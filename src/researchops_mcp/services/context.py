"""Day 4 resource and prompt context helpers for ResearchOps MCP."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from researchops_mcp.services.openalex import PaperService, PaperServiceError, normalize_paper_id

MAX_ABSTRACT_CHARS = 1200
READING_LIST_ID_PATTERN = re.compile(r"^[a-z0-9-]{3,40}$")


class ReadingListError(Exception):
    """Base error for temporary Day 4 reading-list operations."""


class ReadingListValidationError(ReadingListError):
    """Raised when a reading-list request is malformed."""


class ReadingListNotFoundError(ReadingListError):
    """Raised when a requested reading list does not exist."""


@dataclass(frozen=True, slots=True)
class ReadingListRecord:
    list_id: str
    name: str
    description: str
    paper_ids: tuple[str, ...]


class ReadingListService:
    """Temporary in-memory reading-list service for Day 4 resource work.

    Persistence intentionally waits for Day 5. This service only exposes a
    stable resource shape so the MCP interface can be learned first.
    """

    def __init__(self) -> None:
        self._lists: dict[str, ReadingListRecord] = {
            "starter-mcp": ReadingListRecord(
                list_id="starter-mcp",
                name="Starter MCP Papers",
                description="A small starter list for comparing foundational MCP research papers.",
                paper_ids=("W7129030749", "W4417069007"),
            ),
            "researchops-demo": ReadingListRecord(
                list_id="researchops-demo",
                name="ResearchOps Demo List",
                description="A demo reading list used to exercise the Day 4 reading-list resource.",
                paper_ids=("W7129030749",),
            ),
        }

    def get_reading_list(self, list_id: str) -> ReadingListRecord:
        normalized_id = list_id.strip().lower()
        if not normalized_id:
            raise ReadingListValidationError("list_id must not be empty.")
        if not READING_LIST_ID_PATTERN.fullmatch(normalized_id):
            raise ReadingListValidationError("list_id must contain only lowercase letters, numbers, or hyphens.")
        record = self._lists.get(normalized_id)
        if record is None:
            raise ReadingListNotFoundError(f"Reading list '{list_id}' was not found.")
        return record


def truncate_text(text: str | None, *, limit: int = MAX_ABSTRACT_CHARS) -> tuple[str | None, bool]:
    if text is None:
        return None, False
    if len(text) <= limit:
        return text, False
    return text[: limit - 3].rstrip() + "...", True


def build_paper_resource_document(paper_service: PaperService, paper_id: str) -> str:
    paper = paper_service.get_paper(paper_id)
    abstract, abstract_truncated = truncate_text(paper.get("abstract"))
    payload = {
        "resource_type": "paper",
        "uri": f"paper://{paper['paper_id']}",
        "paper": {
            **paper,
            "abstract": abstract,
        },
        "abstract_truncated": abstract_truncated,
        "recommended_next_actions": {
            "lookup_tool": "get_paper",
            "citation_tool": "export_bibtex",
            "related_prompt": "compare_papers",
        },
    }
    return json.dumps(payload, indent=2)


def build_reading_list_resource_document(reading_list_service: ReadingListService, list_id: str) -> str:
    record = reading_list_service.get_reading_list(list_id)
    payload = {
        "resource_type": "reading_list",
        "uri": f"reading-list://{record.list_id}",
        "list_id": record.list_id,
        "name": record.name,
        "description": record.description,
        "paper_count": len(record.paper_ids),
        "paper_ids": list(record.paper_ids),
        "paper_resources": [f"paper://{paper_id}" for paper_id in record.paper_ids],
        "notes": [
            "This is a temporary in-memory reading list for Day 4.",
            "Persistent reading-list storage is intentionally deferred to Day 5.",
        ],
    }
    return json.dumps(payload, indent=2)


def normalize_prompt_paper_ids(raw_paper_ids: str) -> list[str]:
    paper_ids = [segment.strip() for segment in raw_paper_ids.split(",") if segment.strip()]
    if not paper_ids:
        raise ValueError("At least one paper ID must be provided.")
    return [normalize_paper_id(paper_id) for paper_id in paper_ids]


def build_compare_papers_prompt(paper_id_a: str, paper_id_b: str, focus: str) -> str:
    normalized_a = normalize_paper_id(paper_id_a)
    normalized_b = normalize_paper_id(paper_id_b)
    normalized_focus = focus.strip() or "overall contribution"
    return (
        "Compare the following two research papers using the provided resource URIs.\n\n"
        f"Paper A resource: paper://{normalized_a}\n"
        f"Paper B resource: paper://{normalized_b}\n"
        f"Comparison focus: {normalized_focus}\n\n"
        "Structure the answer with: (1) one-sentence summary of each paper, "
        "(2) direct comparison on the requested focus, (3) strengths and weaknesses, "
        "and (4) when someone should prefer one paper over the other.\n"
        "If a needed detail is missing, say so explicitly instead of inventing it."
    )


def build_literature_review_prompt(topic: str, paper_ids: str, objective: str) -> str:
    normalized_topic = topic.strip()
    if not normalized_topic:
        raise ValueError("topic must not be empty.")
    normalized_objective = objective.strip() or "summary"
    normalized_paper_ids = normalize_prompt_paper_ids(paper_ids)
    paper_resources = "\n".join(f"- paper://{paper_id}" for paper_id in normalized_paper_ids)
    return (
        f"Draft a literature review about: {normalized_topic}\n"
        f"Objective: {normalized_objective}\n\n"
        "Use these paper resources as the evidence base:\n"
        f"{paper_resources}\n\n"
        "Produce: (1) a short overview of the topic, (2) key themes across the papers, "
        "(3) disagreements or methodological differences, (4) major gaps, and (5) "
        "a concise conclusion. Cite papers by their paper_id when referring to evidence."
    )
