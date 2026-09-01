from researchops_mcp.repositories.sqlite import SQLiteRepository
from researchops_mcp.services.openalex import (
    CircuitBreakerOpenError,
    DependencyError,
    MAX_RESULTS_PER_PAGE,
    OpenAlexClient,
    PaperService,
    ValidationError,
    normalize_paper_id,
    to_bibtex_entry,
)


def make_work_payload(paper_id: str, title: str = "Testing MCP Tools") -> dict[str, object]:
    return {
        "id": f"https://openalex.org/{paper_id}",
        "title": title,
        "authorships": [{"author": {"display_name": "Jane Doe"}}],
        "publication_year": 2026,
        "abstract_inverted_index": {"Testing": [0], "MCP": [1], "Tools": [2]},
        "primary_location": {"source": {"display_name": "Journal of MCP Studies"}},
        "open_access": {"is_oa": True},
        "ids": {"doi": "https://doi.org/10.1234/example"},
        "cited_by_count": 3,
    }


def test_normalize_paper_id_accepts_full_openalex_url() -> None:
    assert normalize_paper_id("https://openalex.org/W123456789") == "W123456789"


def test_normalize_paper_id_rejects_zero_alias() -> None:
    try:
        normalize_paper_id("W0000000000")
    except ValidationError as exc:
        assert "OpenAlex work identifier" in str(exc)
    else:
        raise AssertionError("Expected ValidationError for zero-only paper id")


def test_search_papers_rejects_invalid_limit() -> None:
    service = PaperService(OpenAlexClient())

    try:
        service.search_papers(query="mcp", page=1, limit=MAX_RESULTS_PER_PAGE + 1)
    except ValidationError as exc:
        assert "Limit must be between" in str(exc)
    else:
        raise AssertionError("Expected ValidationError for invalid limit")


def test_search_papers_rejects_invalid_search_mode() -> None:
    service = PaperService(OpenAlexClient())

    try:
        service.search_papers(query="mcp", page=1, limit=2, search_mode="unsupported")
    except ValidationError as exc:
        assert "search_mode must be one of" in str(exc)
    else:
        raise AssertionError("Expected ValidationError for invalid search mode")


def test_export_bibtex_formats_basic_fields() -> None:
    work = {
        "paper_id": "W123",
        "title": "Testing MCP Tools",
        "authors": ["Jane Doe", "John Smith"],
        "year": 2026,
        "journal": "Journal of MCP Studies",
        "doi": "https://doi.org/10.1234/example",
    }

    bibtex = to_bibtex_entry(work)

    assert "@article{doe2026" in bibtex
    assert "title = {Testing MCP Tools}" in bibtex
    assert "author = {Jane Doe and John Smith}" in bibtex
    assert "year = {2026}" in bibtex


def test_openalex_client_retries_transient_dependency_failure_then_succeeds() -> None:
    attempts: list[str] = []
    slept: list[float] = []

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        attempts.append(url)
        if len(attempts) < 3:
            raise DependencyError("temporary upstream failure")
        return make_work_payload("W1234567890")

    client = OpenAlexClient(
        fetch_json=fetch_json,
        retry_attempts=2,
        retry_backoff_seconds=0.01,
        retry_jitter_seconds=0.0,
        sleep_func=slept.append,
    )

    paper = client.get_work("W1234567890")

    assert paper["paper_id"] == "W1234567890"
    assert len(attempts) == 3
    assert slept == [0.01, 0.02]


def test_openalex_client_opens_circuit_breaker_after_repeated_failures() -> None:
    attempts: list[str] = []
    current_time = {"value": 100.0}

    def now() -> float:
        return current_time["value"]

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        attempts.append(url)
        raise DependencyError("still failing")

    client = OpenAlexClient(
        fetch_json=fetch_json,
        retry_attempts=0,
        circuit_breaker_failure_threshold=2,
        circuit_breaker_reset_seconds=30,
        time_func=now,
    )

    for _ in range(2):
        try:
            client.get_work("W1234567890")
        except DependencyError:
            pass
        else:
            raise AssertionError("Expected dependency failure")

    try:
        client.get_work("W1234567890")
    except CircuitBreakerOpenError as exc:
        assert "circuit breaker is open" in str(exc)
    else:
        raise AssertionError("Expected circuit breaker to fail fast")

    assert len(attempts) == 2


def test_get_paper_returns_stale_cache_when_dependency_is_down(tmp_path) -> None:
    repository = SQLiteRepository(str(tmp_path / "researchops.db"))
    repository.cache_paper(
        {
            "paper_id": "W1234567890",
            "openalex_id": "https://openalex.org/W1234567890",
            "title": "Cached MCP Paper",
            "authors": ["Jane Doe"],
            "year": 2026,
            "abstract": "Cached abstract",
            "doi": None,
            "journal": "Cache Journal",
            "open_access": True,
            "cited_by_count": 1,
        },
        updated_at="2026-08-31T12:00:00+00:00",
    )

    client = OpenAlexClient(fetch_json=lambda url, timeout: (_ for _ in ()).throw(DependencyError("OpenAlex unavailable")), retry_attempts=0)
    service = PaperService(client, paper_store=repository)

    paper = service.get_paper("W1234567890")

    assert paper["cache_status"] == "stale"
    assert paper["cached_at"] == "2026-08-31T12:00:00+00:00"
    assert "Returning cached paper metadata" in paper["dependency_warning"]


def test_get_paper_raises_dependency_error_when_no_cache_exists() -> None:
    client = OpenAlexClient(fetch_json=lambda url, timeout: (_ for _ in ()).throw(DependencyError("OpenAlex unavailable")), retry_attempts=0)
    service = PaperService(client)

    try:
        service.get_paper("W1234567890")
    except DependencyError as exc:
        assert "OpenAlex unavailable" in str(exc)
    else:
        raise AssertionError("Expected dependency error without cache fallback")
