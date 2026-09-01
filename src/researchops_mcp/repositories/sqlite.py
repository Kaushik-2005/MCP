"""SQLite repository for Day 5 persistence in ResearchOps MCP."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DEFAULT_USER_ID = "local-user"


class RepositoryError(Exception):
    """Base error for repository failures."""


class RepositoryNotFoundError(RepositoryError):
    """Raised when a requested record does not exist."""


class RepositoryConflictError(RepositoryError):
    """Raised when optimistic concurrency or uniqueness checks fail."""


class SQLiteRepository:
    """Small SQLite repository for durable state."""

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @property
    def db_path(self) -> str:
        return str(self._db_path)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.transaction() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS papers (
                    paper_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    year INTEGER,
                    data_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reading_lists (
                    list_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS reading_list_papers (
                    list_id TEXT NOT NULL,
                    paper_id TEXT NOT NULL,
                    added_at TEXT NOT NULL,
                    PRIMARY KEY (list_id, paper_id),
                    FOREIGN KEY(list_id) REFERENCES reading_lists(list_id),
                    FOREIGN KEY(paper_id) REFERENCES papers(paper_id)
                );

                CREATE TABLE IF NOT EXISTS notes (
                    note_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    list_id TEXT NOT NULL,
                    paper_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    deleted_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    FOREIGN KEY(list_id) REFERENCES reading_lists(list_id),
                    FOREIGN KEY(paper_id) REFERENCES papers(paper_id)
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    operation TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    idempotency_key TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS idempotency_records (
                    operation TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (operation, idempotency_key)
                );
                """
            )
            self.ensure_user(conn, user_id=DEFAULT_USER_ID, display_name="Local Learner")

    def ensure_user(self, conn: sqlite3.Connection, *, user_id: str, display_name: str) -> None:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, display_name) VALUES (?, ?)",
            (user_id, display_name),
        )

    def get_idempotency_result(self, conn: sqlite3.Connection, operation: str, idempotency_key: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT response_json FROM idempotency_records WHERE operation = ? AND idempotency_key = ?",
            (operation, idempotency_key),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["response_json"])

    def store_idempotency_result(
        self,
        conn: sqlite3.Connection,
        *,
        operation: str,
        idempotency_key: str,
        response: dict[str, Any],
        created_at: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO idempotency_records (operation, idempotency_key, response_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (operation, idempotency_key, json.dumps(response), created_at),
        )

    def create_reading_list(
        self,
        conn: sqlite3.Connection,
        *,
        list_id: str,
        user_id: str,
        name: str,
        description: str,
        created_at: str,
    ) -> dict[str, Any]:
        conn.execute(
            """
            INSERT INTO reading_lists (list_id, user_id, name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (list_id, user_id, name, description, created_at, created_at),
        )
        return {
            "list_id": list_id,
            "name": name,
            "description": description,
            "created_at": created_at,
            "updated_at": created_at,
        }

    def has_reading_list(self, conn: sqlite3.Connection, list_id: str, *, user_id: str = DEFAULT_USER_ID) -> bool:
        row = conn.execute(
            "SELECT 1 FROM reading_lists WHERE list_id = ? AND user_id = ?",
            (list_id, user_id),
        ).fetchone()
        return row is not None

    def save_paper(self, conn: sqlite3.Connection, paper: dict[str, Any], *, updated_at: str) -> None:
        conn.execute(
            """
            INSERT INTO papers (paper_id, title, year, data_json, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(paper_id) DO UPDATE SET
                title = excluded.title,
                year = excluded.year,
                data_json = excluded.data_json,
                updated_at = excluded.updated_at
            """,
            (
                paper["paper_id"],
                paper.get("title") or "Untitled",
                paper.get("year"),
                json.dumps(paper),
                updated_at,
            ),
        )

    def cache_paper(self, paper: dict[str, Any], *, updated_at: str) -> None:
        with self.transaction() as conn:
            self.save_paper(conn, paper, updated_at=updated_at)

    def get_cached_paper(self, paper_id: str) -> dict[str, Any] | None:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT data_json, updated_at FROM papers WHERE paper_id = ?",
                (paper_id,),
            ).fetchone()
            if row is None:
                return None
            return {
                "paper": json.loads(row["data_json"]),
                "updated_at": row["updated_at"],
            }

    def add_paper_to_list(
        self,
        conn: sqlite3.Connection,
        *,
        list_id: str,
        paper_id: str,
        user_id: str,
        added_at: str,
    ) -> bool:
        if not self.has_reading_list(conn, list_id, user_id=user_id):
            raise RepositoryNotFoundError(f"Reading list '{list_id}' was not found.")
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO reading_list_papers (list_id, paper_id, added_at)
            VALUES (?, ?, ?)
            """,
            (list_id, paper_id, added_at),
        )
        if cursor.rowcount:
            conn.execute(
                "UPDATE reading_lists SET updated_at = ? WHERE list_id = ? AND user_id = ?",
                (added_at, list_id, user_id),
            )
        return bool(cursor.rowcount)

    def reading_list_contains_paper(self, conn: sqlite3.Connection, *, list_id: str, paper_id: str, user_id: str) -> bool:
        if not self.has_reading_list(conn, list_id, user_id=user_id):
            return False
        row = conn.execute(
            "SELECT 1 FROM reading_list_papers WHERE list_id = ? AND paper_id = ?",
            (list_id, paper_id),
        ).fetchone()
        return row is not None

    def create_note(
        self,
        conn: sqlite3.Connection,
        *,
        note_id: str,
        user_id: str,
        list_id: str,
        paper_id: str,
        content: str,
        created_at: str,
    ) -> dict[str, Any]:
        conn.execute(
            """
            INSERT INTO notes (note_id, user_id, list_id, paper_id, content, version, created_at, updated_at, deleted_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, NULL)
            """,
            (note_id, user_id, list_id, paper_id, content, created_at, created_at),
        )
        conn.execute(
            "UPDATE reading_lists SET updated_at = ? WHERE list_id = ? AND user_id = ?",
            (created_at, list_id, user_id),
        )
        return {
            "note_id": note_id,
            "list_id": list_id,
            "paper_id": paper_id,
            "content": content,
            "version": 1,
            "created_at": created_at,
            "updated_at": created_at,
        }

    def update_note(
        self,
        conn: sqlite3.Connection,
        *,
        note_id: str,
        user_id: str,
        content: str,
        expected_version: int,
        updated_at: str,
    ) -> dict[str, Any]:
        cursor = conn.execute(
            """
            UPDATE notes
            SET content = ?, version = version + 1, updated_at = ?
            WHERE note_id = ? AND user_id = ? AND version = ? AND deleted_at IS NULL
            """,
            (content, updated_at, note_id, user_id, expected_version),
        )
        if cursor.rowcount == 0:
            row = conn.execute(
                "SELECT version, deleted_at FROM notes WHERE note_id = ? AND user_id = ?",
                (note_id, user_id),
            ).fetchone()
            if row is None or row["deleted_at"] is not None:
                raise RepositoryNotFoundError(f"Note '{note_id}' was not found.")
            raise RepositoryConflictError(f"Note '{note_id}' is at version {row['version']}, not {expected_version}.")
        row = conn.execute(
            "SELECT list_id, paper_id, version FROM notes WHERE note_id = ? AND user_id = ?",
            (note_id, user_id),
        ).fetchone()
        assert row is not None
        conn.execute(
            "UPDATE reading_lists SET updated_at = ? WHERE list_id = ? AND user_id = ?",
            (updated_at, row["list_id"], user_id),
        )
        return {
            "note_id": note_id,
            "list_id": row["list_id"],
            "paper_id": row["paper_id"],
            "content": content,
            "version": row["version"],
            "updated_at": updated_at,
        }

    def delete_note(
        self,
        conn: sqlite3.Connection,
        *,
        note_id: str,
        user_id: str,
        expected_version: int,
        deleted_at: str,
    ) -> dict[str, Any]:
        cursor = conn.execute(
            """
            UPDATE notes
            SET deleted_at = ?, updated_at = ?, version = version + 1
            WHERE note_id = ? AND user_id = ? AND version = ? AND deleted_at IS NULL
            """,
            (deleted_at, deleted_at, note_id, user_id, expected_version),
        )
        if cursor.rowcount == 0:
            row = conn.execute(
                "SELECT version, deleted_at FROM notes WHERE note_id = ? AND user_id = ?",
                (note_id, user_id),
            ).fetchone()
            if row is None or row["deleted_at"] is not None:
                raise RepositoryNotFoundError(f"Note '{note_id}' was not found.")
            raise RepositoryConflictError(f"Note '{note_id}' is at version {row['version']}, not {expected_version}.")
        row = conn.execute(
            "SELECT list_id, paper_id, version FROM notes WHERE note_id = ? AND user_id = ?",
            (note_id, user_id),
        ).fetchone()
        assert row is not None
        conn.execute(
            "UPDATE reading_lists SET updated_at = ? WHERE list_id = ? AND user_id = ?",
            (deleted_at, row["list_id"], user_id),
        )
        return {
            "note_id": note_id,
            "list_id": row["list_id"],
            "paper_id": row["paper_id"],
            "deleted": True,
            "version": row["version"],
            "deleted_at": deleted_at,
        }

    def append_audit_event(
        self,
        conn: sqlite3.Connection,
        *,
        event_id: str,
        operation: str,
        target_type: str,
        target_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
        created_at: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO audit_events (event_id, operation, target_type, target_id, idempotency_key, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, operation, target_type, target_id, idempotency_key, json.dumps(payload), created_at),
        )

    def get_reading_list(self, list_id: str, *, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        with self.transaction() as conn:
            row = conn.execute(
                """
                SELECT list_id, name, description, created_at, updated_at
                FROM reading_lists
                WHERE list_id = ? AND user_id = ?
                """,
                (list_id, user_id),
            ).fetchone()
            if row is None:
                raise RepositoryNotFoundError(f"Reading list '{list_id}' was not found.")

            paper_rows = conn.execute(
                """
                SELECT p.paper_id, p.title, p.year
                FROM reading_list_papers rlp
                JOIN papers p ON p.paper_id = rlp.paper_id
                WHERE rlp.list_id = ?
                ORDER BY rlp.added_at ASC
                """,
                (list_id,),
            ).fetchall()
            note_rows = conn.execute(
                """
                SELECT note_id, paper_id, content, version, created_at, updated_at
                FROM notes
                WHERE list_id = ? AND user_id = ? AND deleted_at IS NULL
                ORDER BY created_at ASC
                """,
                (list_id, user_id),
            ).fetchall()

            return {
                "list_id": row["list_id"],
                "name": row["name"],
                "description": row["description"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "papers": [dict(paper_row) for paper_row in paper_rows],
                "notes": [dict(note_row) for note_row in note_rows],
            }


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
