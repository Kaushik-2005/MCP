import json

import pytest
from mcp.client import Client
from starlette.testclient import TestClient

from researchops_mcp.server import create_server, create_streamable_http_app


BASE_HEADERS = {
    "accept": "application/json, text/event-stream",
    "content-type": "application/json",
}


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
async def test_mcp_workflow_covers_read_write_resource_and_prompt_layers(tmp_path) -> None:
    server = create_server(database_path=str(tmp_path / "researchops.db"), paper_service=FakePaperService())

    async with Client(server) as client:
        search = await client.call_tool(
            "search_papers",
            arguments={"query": "Model Context Protocol", "limit": 1, "page": 1, "search_mode": "exact"},
        )
        assert search.is_error is False
        assert search.structured_content["results"][0]["paper_id"] == "W1234567890"

        created = await client.call_tool(
            "create_reading_list",
            arguments={"name": "Day 11 List", "description": "Integration test", "idempotency_key": "day11-list-1"},
        )
        list_id = created.structured_content["list_id"]

        added = await client.call_tool(
            "add_paper_to_list",
            arguments={"list_id": list_id, "paper_id": "W1234567890", "idempotency_key": "day11-paper-1"},
        )
        assert added.structured_content["status"] == "added"

        note = await client.call_tool(
            "add_note",
            arguments={
                "list_id": list_id,
                "paper_id": "W1234567890",
                "content": "Compare evaluation and transport testing notes.",
                "idempotency_key": "day11-note-1",
            },
        )
        note_id = note.structured_content["note_id"]
        assert note.structured_content["version"] == 1

        updated = await client.call_tool(
            "update_note",
            arguments={
                "note_id": note_id,
                "content": "Updated protocol testing note.",
                "expected_version": 1,
                "idempotency_key": "day11-note-update-1",
            },
        )
        assert updated.structured_content["version"] == 2

        resource_result = await client.read_resource(f"reading-list://{list_id}")
        resource_payload = json.loads(resource_result.contents[0].text)
        assert resource_payload["list_id"] == list_id
        assert resource_payload["paper_count"] == 1
        assert resource_payload["note_count"] == 1
        assert resource_payload["notes"][0]["content_preview"] == "Updated protocol testing note."

        prompt_result = await client.get_prompt(
            "compare_papers",
            arguments={
                "paper_id_a": "W1234567890",
                "paper_id_b": "W1234567890",
                "focus": "protocol testing coverage",
            },
        )
        assert "protocol testing coverage" in prompt_result.messages[0].content.text
        assert "Security note:" in prompt_result.messages[0].content.text

        deleted = await client.call_tool(
            "delete_note",
            arguments={
                "note_id": note_id,
                "expected_version": 2,
                "confirm": True,
                "idempotency_key": "day11-note-delete-1",
            },
        )
        assert deleted.structured_content["status"] == "deleted"

        final_resource = await client.read_resource(f"reading-list://{list_id}")
        final_payload = json.loads(final_resource.contents[0].text)
        assert final_payload["note_count"] == 0


def test_streamable_http_returns_tool_errors_as_mcp_results() -> None:
    app = create_streamable_http_app(auth_enabled=False, host="testserver", stateless_http=True)

    with TestClient(app) as client:
        response = client.post(
            "/mcp",
            headers={**BASE_HEADERS, "mcp-method": "tools/call", "mcp-name": "search_papers"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "search_papers", "arguments": {}}},
        )

    assert response.status_code == 200
    assert '"isError":true' in response.text
    assert "Field required" in response.text


def test_streamable_http_returns_unknown_tool_as_error_result() -> None:
    app = create_streamable_http_app(auth_enabled=False, host="testserver", stateless_http=True)

    with TestClient(app) as client:
        response = client.post(
            "/mcp",
            headers={**BASE_HEADERS, "mcp-method": "tools/call", "mcp-name": "missing_tool"},
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "missing_tool", "arguments": {}}},
        )

    assert response.status_code == 200
    assert '"isError":true' in response.text
    assert "Unknown tool: missing_tool" in response.text
