from researchops_mcp.services.openalex import (
    MAX_RESULTS_PER_PAGE,
    OpenAlexClient,
    PaperService,
    ValidationError,
    normalize_paper_id,
    to_bibtex_entry,
)


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
