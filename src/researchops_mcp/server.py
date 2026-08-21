"""Day 4 local MCP server for the ResearchOps learning project."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from researchops_mcp.services.context import (
    ReadingListError,
    ReadingListService,
    build_compare_papers_prompt,
    build_literature_review_prompt,
    build_paper_resource_document,
    build_reading_list_resource_document,
)
from researchops_mcp.services.openalex import OpenAlexClient, PaperService, PaperServiceError

server = MCPServer(
    name="researchops-mcp",
    version="0.3.0",
    instructions=(
        "ResearchOps MCP exposes read-only paper search tools backed by OpenAlex, "
        "stable paper and reading-list resources, and reusable prompts for comparison "
        "and literature-review workflows. Use tools for active operations, resources "
        "for stable context, and prompts for reusable reasoning scaffolding."
    ),
)

paper_service = PaperService(OpenAlexClient())
reading_list_service = ReadingListService()


@server.tool()
def health_check() -> dict[str, str]:
    """Check whether the local ResearchOps MCP server is reachable."""
    return {"status": "ok", "server": "researchops-mcp", "paper_source": "OpenAlex"}


@server.tool()
def search_papers(query: str, limit: int = 5, page: int = 1, search_mode: str = "balanced") -> dict[str, Any]:
    """
    Search OpenAlex papers by keyword.

    Args:
        query: Free-text paper search query.
        limit: Maximum number of results to return per page. Must be between 1 and 10.
        page: 1-based page number for pagination.
        search_mode: Search strategy. Use `balanced` for title-first fallback behavior, `title` for title-only matching, `exact` for exact text search, or `broad` for OpenAlex broad search.
    """
    try:
        return paper_service.search_papers(query=query, page=page, limit=limit, search_mode=search_mode)
    except PaperServiceError as exc:
        raise ValueError(str(exc)) from exc


@server.tool()
def get_paper(paper_id: str) -> dict[str, Any]:
    """
    Retrieve one OpenAlex paper by stable identifier.

    Args:
        paper_id: OpenAlex work identifier, such as `W1234567890`.
    """
    try:
        return paper_service.get_paper(paper_id)
    except PaperServiceError as exc:
        raise ValueError(str(exc)) from exc


@server.tool()
def export_bibtex(paper_id: str) -> dict[str, str]:
    """
    Export a single paper citation in BibTeX format.

    Args:
        paper_id: OpenAlex work identifier, such as `W1234567890`.
    """
    try:
        return paper_service.export_bibtex(paper_id)
    except PaperServiceError as exc:
        raise ValueError(str(exc)) from exc


@server.resource(
    "paper://{paper_id}",
    name="paper_resource",
    title="Paper Resource",
    description="Stable paper context for one OpenAlex paper identifier.",
    mime_type="application/json",
)
def paper_resource(paper_id: str) -> str:
    """Read one paper as a stable MCP resource."""
    try:
        return build_paper_resource_document(paper_service, paper_id)
    except PaperServiceError as exc:
        raise ValueError(str(exc)) from exc


@server.resource(
    "reading-list://{list_id}",
    name="reading_list_resource",
    title="Reading List Resource",
    description="Stable reading-list context with paper resource references.",
    mime_type="application/json",
)
def reading_list_resource(list_id: str) -> str:
    """Read one temporary Day 4 reading list as a stable MCP resource."""
    try:
        return build_reading_list_resource_document(reading_list_service, list_id)
    except ReadingListError as exc:
        raise ValueError(str(exc)) from exc


@server.prompt()
def compare_papers(paper_id_a: str, paper_id_b: str, focus: str = "overall contribution") -> str:
    """Reusable prompt for comparing two paper resources."""
    return build_compare_papers_prompt(paper_id_a=paper_id_a, paper_id_b=paper_id_b, focus=focus)


@server.prompt()
def generate_literature_review(topic: str, paper_ids: str, objective: str = "summary") -> str:
    """Reusable prompt for drafting a literature review from selected paper resources."""
    return build_literature_review_prompt(topic=topic, paper_ids=paper_ids, objective=objective)



def main() -> None:
    """Run the local MCP server over stdio."""
    server.run()


if __name__ == "__main__":
    main()
