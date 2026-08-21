import json

from researchops_mcp.services.context import (
    MAX_ABSTRACT_CHARS,
    ReadingListService,
    build_paper_resource_document,
    build_reading_list_resource_document,
)


class FakePaperService:
    def get_paper(self, paper_id: str) -> dict[str, object]:
        return {
            "paper_id": paper_id,
            "title": "Test Paper",
            "authors": ["Jane Doe"],
            "year": 2026,
            "abstract": "x" * (MAX_ABSTRACT_CHARS + 50),
            "journal": "Journal of MCP Tests",
            "doi": None,
            "openalex_id": f"https://openalex.org/{paper_id}",
            "open_access": True,
            "cited_by_count": 3,
        }


def test_build_paper_resource_document_truncates_abstract() -> None:
    payload = json.loads(build_paper_resource_document(FakePaperService(), "W1234567890"))

    assert payload["resource_type"] == "paper"
    assert payload["paper"]["paper_id"] == "W1234567890"
    assert payload["abstract_truncated"] is True
    assert payload["paper"]["abstract"].endswith("...")


def test_build_reading_list_resource_document_exposes_paper_resource_refs() -> None:
    service = ReadingListService()

    payload = json.loads(build_reading_list_resource_document(service, "starter-mcp"))

    assert payload["resource_type"] == "reading_list"
    assert payload["list_id"] == "starter-mcp"
    assert payload["paper_count"] >= 1
    assert all(uri.startswith("paper://W") for uri in payload["paper_resources"])
