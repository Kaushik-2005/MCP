"""Day 5 local MCP server for the ResearchOps learning project."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from researchops_mcp.repositories.sqlite import SQLiteRepository
from researchops_mcp.services.context import (
    build_compare_papers_prompt,
    build_literature_review_prompt,
    build_paper_resource_document,
    build_reading_list_resource_document,
)
from researchops_mcp.services.library import LibraryServiceError, ResearchLibraryService
from researchops_mcp.services.openalex import OpenAlexClient, PaperService, PaperServiceError

DEFAULT_DB_PATH = str(Path(__file__).resolve().parents[2] / "data" / "researchops.db")


def create_server(*, database_path: str | None = None, paper_service: PaperService | None = None) -> MCPServer:
    resolved_paper_service = paper_service or PaperService(OpenAlexClient())
    repository = SQLiteRepository(database_path or DEFAULT_DB_PATH)
    library_service = ResearchLibraryService(repository, resolved_paper_service)
    library_service.ensure_demo_data()

    server = MCPServer(
        name="researchops-mcp",
        version="0.4.0",
        instructions=(
            "ResearchOps MCP exposes OpenAlex-backed paper tools, stable paper and reading-list resources, "
            "reusable prompts, and Day 5 persistent write tools for reading lists and notes. "
            "Use read tools and resources for retrieval, and use write tools for state changes with idempotency keys."
        ),
    )

    @server.tool()
    def health_check() -> dict[str, str]:
        """Check whether the local ResearchOps MCP server is reachable."""
        return {
            "status": "ok",
            "server": "researchops-mcp",
            "paper_source": "OpenAlex",
            "storage": "SQLite",
            "database_path": repository.db_path,
        }

    @server.tool()
    def search_papers(query: str, limit: int = 5, page: int = 1, search_mode: str = "balanced") -> dict[str, Any]:
        """Search OpenAlex papers by keyword."""
        try:
            return resolved_paper_service.search_papers(query=query, page=page, limit=limit, search_mode=search_mode)
        except PaperServiceError as exc:
            raise ValueError(str(exc)) from exc

    @server.tool()
    def get_paper(paper_id: str) -> dict[str, Any]:
        """Retrieve one OpenAlex paper by stable identifier."""
        try:
            return resolved_paper_service.get_paper(paper_id)
        except PaperServiceError as exc:
            raise ValueError(str(exc)) from exc

    @server.tool()
    def export_bibtex(paper_id: str) -> dict[str, str]:
        """Export a single paper citation in BibTeX format."""
        try:
            return resolved_paper_service.export_bibtex(paper_id)
        except PaperServiceError as exc:
            raise ValueError(str(exc)) from exc

    @server.tool()
    def create_reading_list(name: str, idempotency_key: str, description: str = "") -> dict[str, Any]:
        """Create a persistent reading list. This is a write action and must include a stable idempotency key."""
        try:
            return library_service.create_reading_list(name=name, description=description, idempotency_key=idempotency_key)
        except (LibraryServiceError, PaperServiceError) as exc:
            raise ValueError(str(exc)) from exc

    @server.tool()
    def add_paper_to_list(list_id: str, paper_id: str, idempotency_key: str) -> dict[str, Any]:
        """Add one paper to an existing reading list. Use only after the list already exists."""
        try:
            return library_service.add_paper_to_list(list_id=list_id, paper_id=paper_id, idempotency_key=idempotency_key)
        except (LibraryServiceError, PaperServiceError) as exc:
            raise ValueError(str(exc)) from exc

    @server.tool()
    def add_note(list_id: str, paper_id: str, content: str, idempotency_key: str) -> dict[str, Any]:
        """Add a persistent note for a paper that is already in the specified reading list."""
        try:
            return library_service.add_note(list_id=list_id, paper_id=paper_id, content=content, idempotency_key=idempotency_key)
        except (LibraryServiceError, PaperServiceError) as exc:
            raise ValueError(str(exc)) from exc

    @server.tool()
    def update_note(note_id: str, content: str, expected_version: int, idempotency_key: str) -> dict[str, Any]:
        """Update an existing note using optimistic concurrency via expected_version."""
        try:
            return library_service.update_note(note_id=note_id, content=content, expected_version=expected_version, idempotency_key=idempotency_key)
        except (LibraryServiceError, PaperServiceError) as exc:
            raise ValueError(str(exc)) from exc

    @server.tool()
    def delete_note(note_id: str, expected_version: int, confirm: bool, idempotency_key: str) -> dict[str, Any]:
        """Delete a note only when confirm is true and the expected_version still matches."""
        try:
            return library_service.delete_note(note_id=note_id, expected_version=expected_version, confirm=confirm, idempotency_key=idempotency_key)
        except (LibraryServiceError, PaperServiceError) as exc:
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
            return build_paper_resource_document(resolved_paper_service, paper_id)
        except PaperServiceError as exc:
            raise ValueError(str(exc)) from exc

    @server.resource(
        "reading-list://{list_id}",
        name="reading_list_resource",
        title="Reading List Resource",
        description="Stable reading-list context with persistent papers and notes.",
        mime_type="application/json",
    )
    def reading_list_resource(list_id: str) -> str:
        """Read one persistent reading list as a stable MCP resource."""
        try:
            return build_reading_list_resource_document(library_service.get_reading_list(list_id))
        except (LibraryServiceError, PaperServiceError) as exc:
            raise ValueError(str(exc)) from exc

    @server.prompt()
    def compare_papers(paper_id_a: str, paper_id_b: str, focus: str = "overall contribution") -> str:
        """Reusable prompt for comparing two paper resources."""
        return build_compare_papers_prompt(paper_id_a=paper_id_a, paper_id_b=paper_id_b, focus=focus)

    @server.prompt()
    def generate_literature_review(topic: str, paper_ids: str, objective: str = "summary") -> str:
        """Reusable prompt for drafting a literature review from selected paper resources."""
        return build_literature_review_prompt(topic=topic, paper_ids=paper_ids, objective=objective)

    return server


server = create_server()


def main() -> None:
    """Run the local MCP server over stdio."""
    server.run()


if __name__ == "__main__":
    main()
