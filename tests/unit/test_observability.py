import json
import logging

import pytest
from mcp.client import Client
from starlette.testclient import TestClient

from researchops_mcp.observability import JsonFormatter, ObservabilityRegistry
from researchops_mcp.server import create_server, create_streamable_http_app
from researchops_mcp.services.openalex import OpenAlexClient, PaperService, PaperServiceError


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
            "resolved_search_mode": search_mode,
            "results": [self.get_paper("W1234567890")],
        }

    def export_bibtex(self, paper_id: str) -> dict[str, str]:
        return {"paper_id": paper_id, "bibtex": "@article{demo2026}"}


class FailingPaperService(FakePaperService):
    def search_papers(self, *, query: str, page: int, limit: int, search_mode: str = "balanced") -> dict[str, object]:
        raise PaperServiceError("forced paper-service failure")


def test_json_logging_redacts_sensitive_fields() -> None:
    record = logging.LogRecord(
        name="researchops_mcp",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="manual_event",
        args=(),
        exc_info=None,
    )
    record.extra_fields = {"authorization": "Bearer secret", "content": "private note", "tool": "add_note"}

    payload = json.loads(JsonFormatter().format(record))

    assert payload["authorization"] == "[REDACTED]"
    assert payload["content"] == "[REDACTED]"
    assert payload["tool"] == "add_note"
    assert payload["message"] == "manual_event"


def test_http_request_id_header_and_metrics_endpoint() -> None:
    registry = ObservabilityRegistry()
    app = create_streamable_http_app(
        auth_enabled=False,
        host="testserver",
        stateless_http=True,
        observability=registry,
    )

    with TestClient(app) as client:
        response = client.get("/healthz", headers={"x-request-id": "test-request-1"})
        metrics = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-request-1"
    assert metrics.status_code == 200
    assert "http./healthz" in metrics.json()["operations"]


@pytest.mark.anyio
async def test_mcp_tool_call_records_operation_metrics(tmp_path) -> None:
    registry = ObservabilityRegistry()
    server = create_server(
        database_path=str(tmp_path / "researchops.db"),
        paper_service=FakePaperService(),
        observability=registry,
    )

    async with Client(server) as client:
        result = await client.call_tool(
            "search_papers",
            arguments={"query": "Model Context Protocol", "limit": 1, "page": 1, "search_mode": "exact"},
        )

    snapshot = registry.snapshot()
    assert result.is_error is False
    assert snapshot["operations"]["tool.search_papers"]["count"] == 1
    assert snapshot["operations"]["tool.search_papers"]["success_count"] == 1
    assert snapshot["operations"]["tool.search_papers"]["p95_latency_ms"] >= 0


@pytest.mark.anyio
async def test_failed_tool_call_records_failure_metrics(tmp_path) -> None:
    registry = ObservabilityRegistry()
    server = create_server(
        database_path=str(tmp_path / "researchops.db"),
        paper_service=FailingPaperService(),
        observability=registry,
    )

    async with Client(server) as client:
        result = await client.call_tool("search_papers", arguments={"query": "Model Context Protocol", "limit": 1})

    snapshot = registry.snapshot()
    assert result.is_error is True
    assert snapshot["operations"]["tool.search_papers"]["failure_count"] == 1


@pytest.mark.anyio
async def test_openalex_dependency_latency_is_recorded_separately(tmp_path) -> None:
    registry = ObservabilityRegistry()

    def work_payload(paper_id: str) -> dict[str, object]:
        return {
            "id": f"https://openalex.org/{paper_id}",
            "title": "Testing MCP Tools",
            "authorships": [{"author": {"display_name": "Jane Doe"}}],
            "publication_year": 2026,
            "abstract_inverted_index": {"Testing": [0]},
            "primary_location": {"source": {"display_name": "Journal"}},
            "open_access": {"is_oa": True},
            "ids": {},
            "cited_by_count": 0,
        }

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        if "/works/W" in url:
            paper_id = url.rsplit("/", 1)[-1]
            return work_payload(paper_id)
        return {"meta": {"count": 1}, "results": [work_payload("W1234567890")]}

    server = create_server(
        database_path=str(tmp_path / "researchops.db"),
        paper_service=PaperService(OpenAlexClient(fetch_json=fetch_json, observability=registry)),
        observability=registry,
    )

    async with Client(server) as client:
        result = await client.call_tool(
            "search_papers",
            arguments={"query": "Model Context Protocol", "limit": 1, "page": 1, "search_mode": "broad"},
        )

    snapshot = registry.snapshot()
    assert result.is_error is False
    assert snapshot["operations"]["tool.search_papers"]["count"] == 1
    assert snapshot["operations"]["dependency.openalex"]["count"] >= 1
