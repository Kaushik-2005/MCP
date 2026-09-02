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
async def test_tool_catalog_metadata_regression(tmp_path) -> None:
    server = create_server(database_path=str(tmp_path / "researchops.db"), paper_service=FakePaperService())

    async with Client(server) as client:
        result = await client.list_tools()

    tools = {tool.name: tool.model_dump() for tool in result.tools}
    assert list(tools) == [
        "health_check",
        "search_papers",
        "get_paper",
        "export_bibtex",
        "create_reading_list",
        "add_paper_to_list",
        "add_note",
        "update_note",
        "delete_note",
    ]

    assert tools["health_check"]["description"] == "Check whether the ResearchOps MCP server is reachable."
    assert tools["search_papers"]["input_schema"]["required"] == ["query"]
    assert tools["search_papers"]["input_schema"]["properties"]["limit"]["default"] == 5
    assert tools["search_papers"]["input_schema"]["properties"]["page"]["default"] == 1
    assert tools["search_papers"]["input_schema"]["properties"]["search_mode"]["default"] == "balanced"
    assert tools["get_paper"]["input_schema"]["required"] == ["paper_id"]
    assert tools["create_reading_list"]["input_schema"]["required"] == ["name", "idempotency_key"]
    assert tools["delete_note"]["input_schema"]["required"] == [
        "note_id",
        "expected_version",
        "confirm",
        "idempotency_key",
    ]


@pytest.mark.anyio
async def test_prompt_catalog_metadata_regression(tmp_path) -> None:
    server = create_server(database_path=str(tmp_path / "researchops.db"), paper_service=FakePaperService())

    async with Client(server) as client:
        result = await client.list_prompts()

    prompts = {prompt.name: prompt.model_dump() for prompt in result.prompts}
    assert list(prompts) == ["compare_papers", "generate_literature_review"]
    assert prompts["compare_papers"]["description"] == "Reusable prompt for comparing two paper resources."
    assert prompts["compare_papers"]["arguments"] == [
        {"name": "paper_id_a", "title": None, "description": None, "required": True},
        {"name": "paper_id_b", "title": None, "description": None, "required": True},
        {"name": "focus", "title": None, "description": None, "required": False},
    ]
    assert prompts["generate_literature_review"]["arguments"] == [
        {"name": "topic", "title": None, "description": None, "required": True},
        {"name": "paper_ids", "title": None, "description": None, "required": True},
        {"name": "objective", "title": None, "description": None, "required": False},
    ]


@pytest.mark.anyio
async def test_resource_template_metadata_regression(tmp_path) -> None:
    server = create_server(database_path=str(tmp_path / "researchops.db"), paper_service=FakePaperService())

    async with Client(server) as client:
        result = await client.list_resource_templates()

    templates = {template.uri_template: template.model_dump() for template in result.resource_templates}
    assert list(templates) == ["paper://{paper_id}", "reading-list://{list_id}"]
    assert templates["paper://{paper_id}"]["name"] == "paper_resource"
    assert templates["paper://{paper_id}"]["title"] == "Paper Resource"
    assert templates["paper://{paper_id}"]["description"] == "Stable paper context for one OpenAlex paper identifier."
    assert templates["paper://{paper_id}"]["mime_type"] == "application/json"
    assert templates["reading-list://{list_id}"]["name"] == "reading_list_resource"
    assert templates["reading-list://{list_id}"]["title"] == "Reading List Resource"
    assert (
        templates["reading-list://{list_id}"]["description"]
        == "Stable reading-list context with persistent papers and notes."
    )
    assert templates["reading-list://{list_id}"]["mime_type"] == "application/json"
