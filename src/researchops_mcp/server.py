"""Day 3 local MCP server for the ResearchOps learning project."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from researchops_mcp.services.openalex import OpenAlexClient, PaperService, PaperServiceError

server = MCPServer(
    name="researchops-mcp",
    version="0.2.1",
    instructions=(
        "ResearchOps MCP exposes read-only paper search tools backed by OpenAlex. "
        "Use `health_check` to verify server status, `search_papers` for bounded paper search, "
        "`get_paper` for a paper lookup by stable identifier, and `export_bibtex` to export one paper citation."
    ),
)

paper_service = PaperService(OpenAlexClient())


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



def main() -> None:
    """Run the local MCP server over stdio."""
    server.run()


if __name__ == "__main__":
    main()
