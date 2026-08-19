"""Day 2 local MCP server for the ResearchOps learning project."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from researchops_mcp.mock_data import MOCK_PAPERS

server = MCPServer(
    name="researchops-mcp",
    version="0.1.0",
    instructions=(
        "ResearchOps MCP exposes read-only mock paper search tools for local learning. "
        "Use `health_check` to verify server status, `search_papers` for keyword search, "
        "and `get_paper` for a paper lookup by stable identifier."
    ),
)


def _normalize_query(query: str) -> str:
    return query.strip().lower()


@server.tool()
def health_check() -> dict[str, str]:
    """Check whether the local ResearchOps MCP server is reachable."""
    return {"status": "ok", "server": "researchops-mcp"}


@server.tool()
def search_papers(query: str, limit: int = 5) -> dict[str, Any]:
    """
    Search mock research papers by keyword.

    Args:
        query: Free-text query to match against titles and abstracts.
        limit: Maximum number of results to return.
    """
    normalized_query = _normalize_query(query)
    if not normalized_query:
        raise ValueError("Query must not be empty.")

    if limit < 1 or limit > 10:
        raise ValueError("Limit must be between 1 and 10.")

    matches = [
        paper
        for paper in MOCK_PAPERS
        if normalized_query in paper["title"].lower()
        or normalized_query in paper["abstract"].lower()
    ]

    return {
        "query": query,
        "count": min(len(matches), limit),
        "results": matches[:limit],
    }


@server.tool()
def get_paper(paper_id: str) -> dict[str, Any]:
    """
    Retrieve one mock paper by stable identifier.

    Args:
        paper_id: Stable paper identifier from a prior search result.
    """
    normalized_paper_id = paper_id.strip()
    if not normalized_paper_id:
        raise ValueError("paper_id must not be empty.")

    for paper in MOCK_PAPERS:
        if paper["paper_id"] == normalized_paper_id:
            return paper

    raise ValueError(f"Paper '{paper_id}' was not found.")


def main() -> None:
    """Run the local MCP server over stdio."""
    server.run()


if __name__ == "__main__":
    main()

