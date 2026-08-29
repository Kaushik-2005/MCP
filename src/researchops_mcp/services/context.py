"""Resource and prompt context helpers for ResearchOps MCP."""

from __future__ import annotations

import json
from typing import Any

from researchops_mcp.security import MAX_FOCUS_CHARS, MAX_OBJECTIVE_CHARS, MAX_TOPIC_CHARS, UNTRUSTED_CONTENT_WARNING
from researchops_mcp.services.openalex import PaperService, normalize_paper_id

MAX_ABSTRACT_CHARS = 1200
MAX_NOTE_PREVIEW_CHARS = 240


def truncate_text(text: str | None, *, limit: int) -> tuple[str | None, bool]:
    if text is None:
        return None, False
    if len(text) <= limit:
        return text, False
    return text[: limit - 3].rstrip() + "...", True


def build_paper_resource_document(paper_service: PaperService, paper_id: str) -> str:
    paper = paper_service.get_paper(paper_id)
    abstract, abstract_truncated = truncate_text(paper.get("abstract"), limit=MAX_ABSTRACT_CHARS)
    payload = {
        "resource_type": "paper",
        "uri": f"paper://{paper['paper_id']}",
        "paper": {
            **paper,
            "abstract": abstract,
        },
        "abstract_truncated": abstract_truncated,
        "content_trust": "untrusted_external_data",
        "security_warning": UNTRUSTED_CONTENT_WARNING,
        "recommended_next_actions": {
            "lookup_tool": "get_paper",
            "citation_tool": "export_bibtex",
            "related_prompt": "compare_papers",
        },
    }
    return json.dumps(payload, indent=2)


def build_reading_list_resource_document(reading_list: dict[str, Any]) -> str:
    notes = []
    notes_truncated = False
    for note in reading_list.get("notes", []):
        preview, was_truncated = truncate_text(note.get("content"), limit=MAX_NOTE_PREVIEW_CHARS)
        if was_truncated:
            notes_truncated = True
        notes.append(
            {
                "note_id": note["note_id"],
                "paper_id": note["paper_id"],
                "content_preview": preview,
                "version": note["version"],
                "updated_at": note["updated_at"],
                "content_trust": "untrusted_user_input",
            }
        )

    payload = {
        "resource_type": "reading_list",
        "uri": f"reading-list://{reading_list['list_id']}",
        "list_id": reading_list["list_id"],
        "name": reading_list["name"],
        "description": reading_list["description"],
        "created_at": reading_list["created_at"],
        "updated_at": reading_list["updated_at"],
        "paper_count": len(reading_list.get("papers", [])),
        "papers": [
            {
                "paper_id": paper["paper_id"],
                "title": paper["title"],
                "year": paper.get("year"),
                "resource_uri": f"paper://{paper['paper_id']}",
            }
            for paper in reading_list.get("papers", [])
        ],
        "note_count": len(notes),
        "notes": notes,
        "notes_truncated": notes_truncated,
        "security_warning": UNTRUSTED_CONTENT_WARNING,
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
    normalized_focus = (focus.strip() or "overall contribution")[:MAX_FOCUS_CHARS]
    return (
        "Compare the following two research papers using the provided resource URIs.\n\n"
        f"Paper A resource: paper://{normalized_a}\n"
        f"Paper B resource: paper://{normalized_b}\n"
        f"Comparison focus: {normalized_focus}\n\n"
        f"Security note: {UNTRUSTED_CONTENT_WARNING}\n\n"
        "Structure the answer with: (1) one-sentence summary of each paper, "
        "(2) direct comparison on the requested focus, (3) strengths and weaknesses, "
        "and (4) when someone should prefer one paper over the other.\n"
        "If a needed detail is missing, say so explicitly instead of inventing it."
    )


def build_literature_review_prompt(topic: str, paper_ids: str, objective: str) -> str:
    normalized_topic = topic.strip()
    if not normalized_topic:
        raise ValueError("topic must not be empty.")
    normalized_topic = normalized_topic[:MAX_TOPIC_CHARS]
    normalized_objective = (objective.strip() or "summary")[:MAX_OBJECTIVE_CHARS]
    normalized_paper_ids = normalize_prompt_paper_ids(paper_ids)
    paper_resources = "\n".join(f"- paper://{paper_id}" for paper_id in normalized_paper_ids)
    return (
        f"Draft a literature review about: {normalized_topic}\n"
        f"Objective: {normalized_objective}\n\n"
        "Use these paper resources as the evidence base:\n"
        f"{paper_resources}\n\n"
        f"Security note: {UNTRUSTED_CONTENT_WARNING}\n\n"
        "Produce: (1) a short overview of the topic, (2) key themes across the papers, "
        "(3) disagreements or methodological differences, (4) major gaps, and (5) "
        "a concise conclusion. Cite papers by their paper_id when referring to evidence."
    )
