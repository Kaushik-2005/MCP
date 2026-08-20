"""Service helpers for OpenAlex-backed paper retrieval."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.openalex.org"
DEFAULT_MAILTO = "learning-project@example.com"
DEFAULT_TIMEOUT_SECONDS = 10
MAX_RESULTS_PER_PAGE = 10
SEARCH_MODES = {"balanced", "title", "exact", "broad"}
OpenAlexSearchMode = Literal["balanced", "title", "exact", "broad"]
OPENALEX_WORK_ID_PATTERN = re.compile(r"^W[1-9][0-9]*$")


class PaperServiceError(Exception):
    """Base error for ResearchOps paper-service operations."""


class ValidationError(PaperServiceError):
    """Raised when a caller provides invalid input."""


class NotFoundError(PaperServiceError):
    """Raised when a requested paper cannot be found."""


class DependencyError(PaperServiceError):
    """Raised when an upstream dependency cannot satisfy the request."""


@dataclass(slots=True)
class SearchResponse:
    query: str
    page: int
    per_page: int
    total_results: int
    results: list[dict[str, Any]]
    resolved_search_mode: str

    @property
    def has_more(self) -> bool:
        return self.page * self.per_page < self.total_results

    @property
    def next_page(self) -> int | None:
        return self.page + 1 if self.has_more else None


class OpenAlexClient:
    """Small OpenAlex client for the read-only ResearchOps server."""

    def __init__(self, *, mailto: str = DEFAULT_MAILTO, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        self._mailto = mailto
        self._timeout_seconds = timeout_seconds

    def search_works(self, *, query: str, page: int, per_page: int, search_mode: OpenAlexSearchMode) -> SearchResponse:
        if search_mode == "title":
            payload = self._list_works(search=query, page=page, per_page=min(per_page * 5, 25))
            response = self._build_response(payload, query=query, page=page, per_page=per_page, resolved_search_mode="title")
            filtered = [work for work in response.results if title_matches(query, work["title"])]
            response.results = filtered[:per_page]
            response.total_results = len(filtered)
            return response

        if search_mode == "exact":
            payload = self._list_works(search_exact=query, page=page, per_page=per_page)
            return self._build_response(payload, query=query, page=page, per_page=per_page, resolved_search_mode="exact")

        if search_mode == "broad":
            payload = self._list_works(search=query, page=page, per_page=per_page)
            return self._build_response(payload, query=query, page=page, per_page=per_page, resolved_search_mode="broad")

        exact_payload = self._list_works(search_exact=query, page=page, per_page=per_page)
        exact_response = self._build_response(exact_payload, query=query, page=page, per_page=per_page, resolved_search_mode="exact")
        if exact_response.results:
            return exact_response

        broad_payload = self._list_works(search=query, page=page, per_page=per_page)
        return self._build_response(broad_payload, query=query, page=page, per_page=per_page, resolved_search_mode="broad")

    def get_work(self, paper_id: str) -> dict[str, Any]:
        normalized_id = normalize_paper_id(paper_id)
        payload = self._get_json(f"/works/{normalized_id}")
        normalized_work = normalize_work(payload)
        if normalized_work["paper_id"] != normalized_id:
            raise NotFoundError(f"Paper '{paper_id}' was not found in OpenAlex.")
        return normalized_work

    def _list_works(
        self,
        *,
        page: int,
        per_page: int,
        search: str | None = None,
        search_exact: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "page": page,
            "per-page": per_page,
            "mailto": self._mailto,
        }
        if search is not None:
            params["search"] = search
        if search_exact is not None:
            params["search.exact"] = search_exact
        return self._get_json(f"/works?{urlencode(params)}")

    def _build_response(self, payload: dict[str, Any], *, query: str, page: int, per_page: int, resolved_search_mode: str) -> SearchResponse:
        meta = payload.get("meta", {})
        results = [normalize_work(work) for work in payload.get("results", [])]
        return SearchResponse(
            query=query,
            page=page,
            per_page=per_page,
            total_results=int(meta.get("count", 0)),
            results=results,
            resolved_search_mode=resolved_search_mode,
        )

    def _get_json(self, path: str) -> dict[str, Any]:
        request = Request(
            url=f"{BASE_URL}{path}",
            headers={
                "Accept": "application/json",
                "User-Agent": f"researchops-mcp/0.2.0 ({self._mailto})",
            },
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                raise NotFoundError("Paper was not found in OpenAlex.") from exc
            if exc.code == 429:
                raise DependencyError("OpenAlex rate-limited the request. Try again later.") from exc
            if 500 <= exc.code <= 599:
                raise DependencyError(f"OpenAlex is currently unavailable (HTTP {exc.code}).") from exc
            raise DependencyError(f"OpenAlex returned HTTP {exc.code}.") from exc
        except URLError as exc:
            raise DependencyError("OpenAlex could not be reached within the configured timeout.") from exc


class PaperService:
    """Business-facing paper operations used by MCP tools."""

    def __init__(self, client: OpenAlexClient) -> None:
        self._client = client

    def search_papers(self, *, query: str, page: int, limit: int, search_mode: OpenAlexSearchMode = "balanced") -> dict[str, Any]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValidationError("Query must not be empty.")
        if page < 1:
            raise ValidationError("Page must be greater than or equal to 1.")
        if limit < 1 or limit > MAX_RESULTS_PER_PAGE:
            raise ValidationError(f"Limit must be between 1 and {MAX_RESULTS_PER_PAGE}.")
        if search_mode not in SEARCH_MODES:
            allowed = ", ".join(sorted(SEARCH_MODES))
            raise ValidationError(f"search_mode must be one of: {allowed}.")

        result = self._client.search_works(query=normalized_query, page=page, per_page=limit, search_mode=search_mode)
        return {
            "query": normalized_query,
            "page": page,
            "limit": limit,
            "count": len(result.results),
            "total_results": result.total_results,
            "has_more": result.has_more,
            "next_page": result.next_page,
            "search_mode": search_mode,
            "resolved_search_mode": result.resolved_search_mode,
            "results": result.results,
        }

    def get_paper(self, paper_id: str) -> dict[str, Any]:
        return self._client.get_work(paper_id)

    def export_bibtex(self, paper_id: str) -> dict[str, str]:
        work = self.get_paper(paper_id)
        return {
            "paper_id": work["paper_id"],
            "bibtex": to_bibtex_entry(work),
        }


def normalize_paper_id(paper_id: str) -> str:
    stripped = paper_id.strip()
    if not stripped:
        raise ValidationError("paper_id must not be empty.")
    if stripped.startswith("https://openalex.org/"):
        stripped = stripped.rsplit("/", 1)[-1]
    if not OPENALEX_WORK_ID_PATTERN.fullmatch(stripped):
        raise ValidationError("paper_id must be an OpenAlex work identifier like `W1234567890`.")
    return stripped


def normalize_work(work: dict[str, Any]) -> dict[str, Any]:
    authorships = work.get("authorships", [])
    authors = []
    for authorship in authorships:
        author = authorship.get("author") or {}
        display_name = author.get("display_name")
        if display_name:
            authors.append(display_name)

    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    open_access = work.get("open_access") or {}
    ids = work.get("ids") or {}
    publication_year = work.get("publication_year")
    paper_url = work.get("id", "")
    short_id = normalize_paper_id(paper_url) if paper_url else ""

    return {
        "paper_id": short_id,
        "openalex_id": paper_url,
        "title": work.get("title") or work.get("display_name") or "Untitled",
        "authors": authors,
        "year": publication_year,
        "abstract": extract_abstract(work),
        "doi": ids.get("doi") or work.get("doi"),
        "journal": source.get("display_name"),
        "open_access": bool(open_access.get("is_oa")),
        "cited_by_count": work.get("cited_by_count", 0),
    }


def title_matches(query: str, title: str) -> bool:
    normalized_query = query.strip().lower()
    normalized_title = title.strip().lower()
    if not normalized_query or not normalized_title:
        return False
    if normalized_query in normalized_title:
        return True
    query_tokens = [token for token in normalized_query.split() if token]
    return bool(query_tokens) and all(token in normalized_title for token in query_tokens)


def extract_abstract(work: dict[str, Any]) -> str | None:
    inverted = work.get("abstract_inverted_index")
    if not inverted:
        return None
    words: list[tuple[int, str]] = []
    for token, positions in inverted.items():
        for position in positions:
            words.append((position, token))
    words.sort(key=lambda item: item[0])
    return " ".join(token for _, token in words)


def to_bibtex_entry(work: dict[str, Any]) -> str:
    authors = " and ".join(work.get("authors") or ["Unknown Author"])
    year = work.get("year") or "unknown"
    title = sanitize_bibtex_value(work.get("title") or "Untitled")
    journal = sanitize_bibtex_value(work.get("journal") or "Unknown Journal")
    doi = sanitize_bibtex_value(work.get("doi") or "")
    citation_key = f"{slugify_author(authors)}{year}"
    fields = [
        f"  title = {{{title}}}",
        f"  author = {{{sanitize_bibtex_value(authors)}}}",
        f"  year = {{{year}}}",
        f"  journal = {{{journal}}}",
    ]
    if doi:
        fields.append(f"  doi = {{{doi}}}")
    return "@article{" + citation_key + ",\n" + ",\n".join(fields) + "\n}"


def slugify_author(authors: str) -> str:
    first = authors.split(" and ", 1)[0].split()[-1]
    return "".join(character for character in first.lower() if character.isalnum()) or "paper"


def sanitize_bibtex_value(value: str) -> str:
    return value.replace("{", "").replace("}", "")

