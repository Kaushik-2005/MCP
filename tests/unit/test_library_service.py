from researchops_mcp.repositories.sqlite import SQLiteRepository
from researchops_mcp.services.library import ConflictError, ResearchLibraryService, ValidationError


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
