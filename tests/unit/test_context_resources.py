import json

from researchops_mcp.services.context import MAX_ABSTRACT_CHARS, build_paper_resource_document, build_reading_list_resource_document


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


def test_build_reading_list_resource_document_exposes_papers_and_notes() -> None:
    payload = json.loads(
        build_reading_list_resource_document(
            {
                "list_id": "starter-mcp",
                "name": "Starter MCP Papers",
                "description": "Demo",
                "created_at": "2026-08-21T10:00:00+00:00",
                "updated_at": "2026-08-21T10:05:00+00:00",
                "papers": [{"paper_id": "W123", "title": "Test Paper", "year": 2026}],
                "notes": [
                    {
                        "note_id": "note-1",
                        "paper_id": "W123",
                        "content": "y" * 300,
                        "version": 2,
                        "updated_at": "2026-08-21T10:05:00+00:00",
                    }
                ],
            }
        )
    )

    assert payload["resource_type"] == "reading_list"
    assert payload["list_id"] == "starter-mcp"
    assert payload["papers"][0]["resource_uri"] == "paper://W123"
    assert payload["note_count"] == 1
    assert payload["notes_truncated"] is True
