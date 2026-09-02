import json

import pytest
from mcp.client import Client

from researchops_mcp.server import create_server


class FakePaperService:
    def get_paper(self, paper_id: str) -> dict[str, object]:
        return {
            "paper_id": paper_id,
            "title": f"Paper {paper_id}",
            "authors": ["Jane Doe"],
            "year": 2026,
            "abstract": "Abstract text",
            "journal": "Journal",
            "doi": None,
            "openalex_id": f"https://openalex.org/{paper_id}",
            "open_access": True,
            "cited_by_count": 0,
        }

    def search_papers(self, *, query: str, page: int, limit: int, search_mode: str = "balanced") -> dict[str, object]:
        return {
            "query": query,
            "page": page,
            "limit": limit,
            "count": 1,
            "total_results": 1,
            "has_more": False,
            "next_page": None,
            "search_mode": search_mode,
            "resolved_search_mode": "exact",
            "results": [self.get_paper("W1234567890")],
        }

    def export_bibtex(self, paper_id: str) -> dict[str, str]:
        return {"paper_id": paper_id, "bibtex": "@article{demo2026}"}


@pytest.mark.anyio
async def test_server_persists_reading_list_writes_and_resource_reads(tmp_path) -> None:
    server = create_server(database_path=str(tmp_path / "researchops.db"), paper_service=FakePaperService())

    async with Client(server) as client:
        created = await client.call_tool(
            "create_reading_list",
            arguments={"name": "Persistent List", "description": "Demo", "idempotency_key": "create-list-1"},
        )
        list_id = created.structured_content["list_id"]

        added = await client.call_tool(
            "add_paper_to_list",
            arguments={"list_id": list_id, "paper_id": "W1234567890", "idempotency_key": "add-paper-1"},
        )
        assert added.structured_content["status"] == "added"

        note = await client.call_tool(
            "add_note",
            arguments={
                "list_id": list_id,
                "paper_id": "W1234567890",
                "content": "Important note",
                "idempotency_key": "add-note-1",
            },
        )
        assert note.structured_content["version"] == 1

        resource_result = await client.read_resource(f"reading-list://{list_id}")
        payload = json.loads(resource_result.contents[0].text)
        assert payload["list_id"] == list_id
        assert payload["paper_count"] == 1
        assert payload["note_count"] == 1


@pytest.mark.anyio
async def test_delete_note_requires_confirmation(tmp_path) -> None:
    server = create_server(database_path=str(tmp_path / "researchops.db"), paper_service=FakePaperService())

    async with Client(server) as client:
        created = await client.call_tool(
            "create_reading_list",
            arguments={"name": "Persistent List", "description": "Demo", "idempotency_key": "create-list-1"},
        )
        list_id = created.structured_content["list_id"]
        await client.call_tool(
            "add_paper_to_list",
            arguments={"list_id": list_id, "paper_id": "W1234567890", "idempotency_key": "add-paper-1"},
        )
        note = await client.call_tool(
            "add_note",
            arguments={
                "list_id": list_id,
                "paper_id": "W1234567890",
                "content": "Important note",
                "idempotency_key": "add-note-1",
            },
        )

        failed = await client.call_tool(
            "delete_note",
            arguments={
                "note_id": note.structured_content["note_id"],
                "expected_version": 1,
                "confirm": False,
                "idempotency_key": "delete-note-1",
            },
        )
        assert failed.is_error is True
        assert "confirm must be true" in failed.content[0].text
