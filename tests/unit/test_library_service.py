from researchops_mcp.repositories.sqlite import SQLiteRepository
from researchops_mcp.services.library import ConflictError, NotFoundError, ResearchLibraryService, ValidationError
from researchops_mcp.services.openalex import OpenAlexClient, PaperService


class FakePaperService:
    def get_paper(self, paper_id: str) -> dict[str, object]:
        return {
            "paper_id": paper_id,
            "title": f"Paper {paper_id}",
            "authors": ["Jane Doe"],
            "year": 2026,
            "abstract": "Abstract",
            "journal": "Journal",
            "doi": None,
            "openalex_id": f"https://openalex.org/{paper_id}",
            "open_access": True,
            "cited_by_count": 0,
        }


def make_work_payload(paper_id: str) -> dict[str, object]:
    return {
        "id": f"https://openalex.org/{paper_id}",
        "title": f"Paper {paper_id}",
        "authorships": [{"author": {"display_name": "Jane Doe"}}],
        "publication_year": 2026,
        "abstract_inverted_index": {"Research": [0], "Paper": [1]},
        "primary_location": {"source": {"display_name": "Journal"}},
        "open_access": {"is_oa": True},
        "ids": {},
        "cited_by_count": 0,
    }


def test_create_reading_list_is_idempotent(tmp_path) -> None:
    repository = SQLiteRepository(str(tmp_path / "researchops.db"))
    service = ResearchLibraryService(repository, FakePaperService())

    first = service.create_reading_list(name="My List", description="Demo", idempotency_key="create-list-1")
    second = service.create_reading_list(name="Different Name", description="Ignored", idempotency_key="create-list-1")

    assert first == second
    assert first["resource_uri"].startswith("reading-list://")


def test_update_note_rejects_stale_version(tmp_path) -> None:
    repository = SQLiteRepository(str(tmp_path / "researchops.db"))
    service = ResearchLibraryService(repository, FakePaperService())

    created_list = service.create_reading_list(name="My List", description="Demo", idempotency_key="create-list-1")
    service.add_paper_to_list(list_id=created_list["list_id"], paper_id="W1234567890", idempotency_key="add-paper-1")
    note = service.add_note(list_id=created_list["list_id"], paper_id="W1234567890", content="First note", idempotency_key="add-note-1")
    service.update_note(note_id=note["note_id"], content="Updated", expected_version=1, idempotency_key="update-note-1")

    try:
        service.update_note(note_id=note["note_id"], content="Stale", expected_version=1, idempotency_key="update-note-2")
    except ConflictError as exc:
        assert "version" in str(exc)
    else:
        raise AssertionError("Expected ConflictError for stale note version")


def test_add_note_requires_paper_to_be_in_list(tmp_path) -> None:
    repository = SQLiteRepository(str(tmp_path / "researchops.db"))
    service = ResearchLibraryService(repository, FakePaperService())

    created_list = service.create_reading_list(name="My List", description="Demo", idempotency_key="create-list-1")

    try:
        service.add_note(list_id=created_list["list_id"], paper_id="W1234567890", content="No paper yet", idempotency_key="add-note-1")
    except ValidationError as exc:
        assert "already be present" in str(exc)
    else:
        raise AssertionError("Expected ValidationError when note paper is missing from the list")


def test_user_cannot_read_another_users_list(tmp_path) -> None:
    repository = SQLiteRepository(str(tmp_path / "researchops.db"))
    service = ResearchLibraryService(repository, FakePaperService())

    alice_list = service.create_reading_list(
        name="Alice List",
        description="Private",
        idempotency_key="alice-list-1",
        user_id="alice",
    )

    try:
        service.get_reading_list(alice_list["list_id"], user_id="bob")
    except NotFoundError as exc:
        assert alice_list["list_id"] in str(exc)
    else:
        raise AssertionError("Expected NotFoundError for cross-user reading list access")


def test_user_cannot_update_another_users_note(tmp_path) -> None:
    repository = SQLiteRepository(str(tmp_path / "researchops.db"))
    service = ResearchLibraryService(repository, FakePaperService())

    alice_list = service.create_reading_list(
        name="Alice List",
        description="Private",
        idempotency_key="alice-list-1",
        user_id="alice",
    )
    service.add_paper_to_list(
        list_id=alice_list["list_id"],
        paper_id="W1234567890",
        idempotency_key="alice-paper-1",
        user_id="alice",
    )
    note = service.add_note(
        list_id=alice_list["list_id"],
        paper_id="W1234567890",
        content="Alice note",
        idempotency_key="alice-note-1",
        user_id="alice",
    )

    try:
        service.update_note(
            note_id=note["note_id"],
            content="Bob tries update",
            expected_version=1,
            idempotency_key="bob-update-1",
            user_id="bob",
        )
    except NotFoundError as exc:
        assert note["note_id"] in str(exc)
    else:
        raise AssertionError("Expected NotFoundError for cross-user note update")


def test_ensure_demo_data_does_not_lock_database_when_paper_service_caches(tmp_path) -> None:
    repository = SQLiteRepository(str(tmp_path / "researchops.db"))

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        paper_id = url.rsplit("/", 1)[-1].split("?", 1)[0]
        return make_work_payload(paper_id)

    paper_service = PaperService(OpenAlexClient(fetch_json=fetch_json, retry_attempts=0), paper_store=repository)
    service = ResearchLibraryService(repository, paper_service)

    service.ensure_demo_data()

    reading_list = service.get_reading_list("starter-mcp")
    assert len(reading_list["papers"]) == 2
