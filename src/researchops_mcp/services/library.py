"""Business services for durable reading-list and note persistence."""

from __future__ import annotations

import re
import secrets
from typing import Any

from researchops_mcp.repositories.sqlite import (
    DEFAULT_USER_ID,
    RepositoryConflictError,
    RepositoryNotFoundError,
    SQLiteRepository,
    utc_now,
)
from researchops_mcp.services.openalex import PaperService, normalize_paper_id

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9._:-]{4,120}$")
LIST_ID_PATTERN = re.compile(r"^[a-z0-9-]{3,40}$")


class LibraryServiceError(Exception):
    """Base error for reading-list and note operations."""


class ValidationError(LibraryServiceError):
    """Raised when a caller provides invalid input."""


class NotFoundError(LibraryServiceError):
    """Raised when a requested record cannot be found."""


class ConflictError(LibraryServiceError):
    """Raised when optimistic concurrency or uniqueness checks fail."""


class ResearchLibraryService:
    """Business logic for durable reading lists and notes."""

    def __init__(self, repository: SQLiteRepository, paper_service: PaperService, *, user_id: str = DEFAULT_USER_ID) -> None:
        self._repository = repository
        self._paper_service = paper_service
        self._default_user_id = user_id

    @property
    def repository(self) -> SQLiteRepository:
        return self._repository

    def ensure_demo_data(self) -> None:
        with self._repository.transaction() as conn:
            if self._repository.has_reading_list(conn, "starter-mcp", user_id=self._default_user_id):
                return
        self._seed_demo_list(
            "starter-mcp",
            "Starter MCP Papers",
            "A small starter list for comparing foundational MCP research papers.",
            ["W7129030749", "W4417069007"],
        )
        self._seed_demo_list(
            "researchops-demo",
            "ResearchOps Demo List",
            "A demo reading list used to exercise the Day 5 reading-list resource.",
            ["W7129030749"],
        )

    def _seed_demo_list(self, list_id: str, name: str, description: str, paper_ids: list[str]) -> None:
        now = utc_now()
        with self._repository.transaction() as conn:
            self._repository.ensure_user(conn, user_id=self._default_user_id, display_name="Local Learner")
            if not self._repository.has_reading_list(conn, list_id, user_id=self._default_user_id):
                self._repository.create_reading_list(
                    conn,
                    list_id=list_id,
                    user_id=self._default_user_id,
                    name=name,
                    description=description,
                    created_at=now,
                )
            for paper_id in paper_ids:
                paper = self._paper_service.get_paper(paper_id)
                self._repository.save_paper(conn, paper, updated_at=now)
                self._repository.add_paper_to_list(
                    conn,
                    list_id=list_id,
                    paper_id=paper["paper_id"],
                    user_id=self._default_user_id,
                    added_at=now,
                )

    def create_reading_list(self, *, name: str, description: str, idempotency_key: str, user_id: str | None = None) -> dict[str, Any]:
        effective_user_id = self._effective_user_id(user_id)
        normalized_name = name.strip()
        normalized_description = description.strip()
        if not normalized_name:
            raise ValidationError("name must not be empty.")
        self._validate_idempotency_key(idempotency_key)
        operation = "create_reading_list"
        now = utc_now()
        list_id = self._generate_list_id(normalized_name)
        with self._repository.transaction() as conn:
            self._repository.ensure_user(conn, user_id=effective_user_id, display_name=effective_user_id.title())
            if existing := self._repository.get_idempotency_result(conn, operation, idempotency_key):
                return existing
            created = self._repository.create_reading_list(
                conn,
                list_id=list_id,
                user_id=effective_user_id,
                name=normalized_name,
                description=normalized_description,
                created_at=now,
            )
            response = {**created, "resource_uri": f"reading-list://{list_id}", "status": "created"}
            self._record_write(conn, operation=operation, target_type="reading_list", target_id=list_id, idempotency_key=idempotency_key, payload=response, created_at=now)
            self._repository.store_idempotency_result(conn, operation=operation, idempotency_key=idempotency_key, response=response, created_at=now)
            return response

    def add_paper_to_list(self, *, list_id: str, paper_id: str, idempotency_key: str, user_id: str | None = None) -> dict[str, Any]:
        effective_user_id = self._effective_user_id(user_id)
        normalized_list_id = self._normalize_list_id(list_id)
        normalized_paper_id = normalize_paper_id(paper_id)
        self._validate_idempotency_key(idempotency_key)
        operation = "add_paper_to_list"
        paper = self._paper_service.get_paper(normalized_paper_id)
        now = utc_now()
        with self._repository.transaction() as conn:
            if existing := self._repository.get_idempotency_result(conn, operation, idempotency_key):
                return existing
            self._repository.save_paper(conn, paper, updated_at=now)
            try:
                added = self._repository.add_paper_to_list(
                    conn,
                    list_id=normalized_list_id,
                    paper_id=paper["paper_id"],
                    user_id=effective_user_id,
                    added_at=now,
                )
            except RepositoryNotFoundError as exc:
                raise NotFoundError(str(exc)) from exc
            response = {
                "list_id": normalized_list_id,
                "paper_id": paper["paper_id"],
                "paper_title": paper["title"],
                "resource_uri": f"reading-list://{normalized_list_id}",
                "status": "added" if added else "already_present",
            }
            self._record_write(conn, operation=operation, target_type="reading_list", target_id=normalized_list_id, idempotency_key=idempotency_key, payload=response, created_at=now)
            self._repository.store_idempotency_result(conn, operation=operation, idempotency_key=idempotency_key, response=response, created_at=now)
            return response

    def add_note(self, *, list_id: str, paper_id: str, content: str, idempotency_key: str, user_id: str | None = None) -> dict[str, Any]:
        effective_user_id = self._effective_user_id(user_id)
        normalized_list_id = self._normalize_list_id(list_id)
        normalized_paper_id = normalize_paper_id(paper_id)
        normalized_content = content.strip()
        if not normalized_content:
            raise ValidationError("content must not be empty.")
        self._validate_idempotency_key(idempotency_key)
        operation = "add_note"
        now = utc_now()
        note_id = f"note-{secrets.token_hex(4)}"
        with self._repository.transaction() as conn:
            if existing := self._repository.get_idempotency_result(conn, operation, idempotency_key):
                return existing
            if not self._repository.has_reading_list(conn, normalized_list_id, user_id=effective_user_id):
                raise NotFoundError(f"Reading list '{normalized_list_id}' was not found.")
            if not self._repository.reading_list_contains_paper(
                conn,
                list_id=normalized_list_id,
                paper_id=normalized_paper_id,
                user_id=effective_user_id,
            ):
                raise ValidationError("paper_id must already be present in the reading list before adding a note.")
            created = self._repository.create_note(
                conn,
                note_id=note_id,
                user_id=effective_user_id,
                list_id=normalized_list_id,
                paper_id=normalized_paper_id,
                content=normalized_content,
                created_at=now,
            )
            response = {**created, "status": "created"}
            self._record_write(conn, operation=operation, target_type="note", target_id=note_id, idempotency_key=idempotency_key, payload=response, created_at=now)
            self._repository.store_idempotency_result(conn, operation=operation, idempotency_key=idempotency_key, response=response, created_at=now)
            return response

    def update_note(self, *, note_id: str, content: str, expected_version: int, idempotency_key: str, user_id: str | None = None) -> dict[str, Any]:
        effective_user_id = self._effective_user_id(user_id)
        normalized_note_id = note_id.strip()
        normalized_content = content.strip()
        if not normalized_note_id:
            raise ValidationError("note_id must not be empty.")
        if not normalized_content:
            raise ValidationError("content must not be empty.")
        if expected_version < 1:
            raise ValidationError("expected_version must be greater than or equal to 1.")
        self._validate_idempotency_key(idempotency_key)
        operation = "update_note"
        now = utc_now()
        with self._repository.transaction() as conn:
            if existing := self._repository.get_idempotency_result(conn, operation, idempotency_key):
                return existing
            try:
                updated = self._repository.update_note(
                    conn,
                    note_id=normalized_note_id,
                    user_id=effective_user_id,
                    content=normalized_content,
                    expected_version=expected_version,
                    updated_at=now,
                )
            except RepositoryNotFoundError as exc:
                raise NotFoundError(str(exc)) from exc
            except RepositoryConflictError as exc:
                raise ConflictError(str(exc)) from exc
            response = {**updated, "status": "updated"}
            self._record_write(conn, operation=operation, target_type="note", target_id=normalized_note_id, idempotency_key=idempotency_key, payload=response, created_at=now)
            self._repository.store_idempotency_result(conn, operation=operation, idempotency_key=idempotency_key, response=response, created_at=now)
            return response

    def delete_note(self, *, note_id: str, expected_version: int, confirm: bool, idempotency_key: str, user_id: str | None = None) -> dict[str, Any]:
        effective_user_id = self._effective_user_id(user_id)
        normalized_note_id = note_id.strip()
        if not normalized_note_id:
            raise ValidationError("note_id must not be empty.")
        if expected_version < 1:
            raise ValidationError("expected_version must be greater than or equal to 1.")
        if not confirm:
            raise ValidationError("confirm must be true before deleting a note.")
        self._validate_idempotency_key(idempotency_key)
        operation = "delete_note"
        now = utc_now()
        with self._repository.transaction() as conn:
            if existing := self._repository.get_idempotency_result(conn, operation, idempotency_key):
                return existing
            try:
                deleted = self._repository.delete_note(
                    conn,
                    note_id=normalized_note_id,
                    user_id=effective_user_id,
                    expected_version=expected_version,
                    deleted_at=now,
                )
            except RepositoryNotFoundError as exc:
                raise NotFoundError(str(exc)) from exc
            except RepositoryConflictError as exc:
                raise ConflictError(str(exc)) from exc
            response = {**deleted, "status": "deleted"}
            self._record_write(conn, operation=operation, target_type="note", target_id=normalized_note_id, idempotency_key=idempotency_key, payload=response, created_at=now)
            self._repository.store_idempotency_result(conn, operation=operation, idempotency_key=idempotency_key, response=response, created_at=now)
            return response

    def get_reading_list(self, list_id: str, *, user_id: str | None = None) -> dict[str, Any]:
        effective_user_id = self._effective_user_id(user_id)
        normalized_list_id = self._normalize_list_id(list_id)
        try:
            return self._repository.get_reading_list(normalized_list_id, user_id=effective_user_id)
        except RepositoryNotFoundError as exc:
            raise NotFoundError(str(exc)) from exc

    def _effective_user_id(self, user_id: str | None) -> str:
        normalized = (user_id or self._default_user_id).strip()
        if not normalized:
            raise ValidationError("user_id must not be empty.")
        return normalized

    def _record_write(
        self,
        conn,
        *,
        operation: str,
        target_type: str,
        target_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
        created_at: str,
    ) -> None:
        self._repository.append_audit_event(
            conn,
            event_id=f"evt-{secrets.token_hex(4)}",
            operation=operation,
            target_type=target_type,
            target_id=target_id,
            idempotency_key=idempotency_key,
            payload=payload,
            created_at=created_at,
        )

    def _validate_idempotency_key(self, idempotency_key: str) -> None:
        normalized_key = idempotency_key.strip()
        if not IDEMPOTENCY_KEY_PATTERN.fullmatch(normalized_key):
            raise ValidationError("idempotency_key must be 4-120 characters using letters, numbers, dots, colons, underscores, or hyphens.")

    def _normalize_list_id(self, list_id: str) -> str:
        normalized = list_id.strip().lower()
        if not LIST_ID_PATTERN.fullmatch(normalized):
            raise ValidationError("list_id must contain only lowercase letters, numbers, or hyphens.")
        return normalized

    def _generate_list_id(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-") or "reading-list"
        slug = slug[:28].strip("-") or "reading-list"
        return f"{slug}-{secrets.token_hex(3)}"
