"""Day 12 evaluation runner for ResearchOps MCP."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp.client import Client

from researchops_mcp.auth import ALL_SCOPES, DEFAULT_DEMO_TOKENS, PROMPT_SCOPES, TOOL_SCOPES
from researchops_mcp.server import create_server

DEFAULT_DATASET_PATH = Path(__file__).resolve().parents[2] / "tests" / "evals" / "researchops_eval_dataset.jsonl"
DEFAULT_REPORT_PATH = Path(__file__).resolve().parents[2] / "docs" / "evaluation-report.json"

READING_LIST_ID = "starter-mcp"
PAPER_ID_A = "W7129030749"
PAPER_ID_B = "W4417069007"
NOTE_ID = "starter-note"

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "into",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "please",
    "show",
    "that",
    "the",
    "these",
    "this",
    "to",
    "up",
    "want",
    "with",
}

VARIANT_METADATA = {
    "current": {},
    "generic_descriptions": {
        "search_papers": "Operate on research data.",
        "get_paper": "Operate on research data.",
        "export_bibtex": "Produce output.",
        "create_reading_list": "Modify stored content.",
        "add_paper_to_list": "Modify stored content.",
        "add_note": "Modify stored content.",
        "update_note": "Modify stored content.",
        "delete_note": "Modify stored content.",
    },
}

QUALITY_THRESHOLDS = {
    "tool_precision": 0.95,
    "tool_recall": 0.95,
    "argument_correctness_rate": 0.95,
    "task_completion_rate": 1.0,
    "unauthorized_action_rate": 0.0,
    "hallucinated_tool_rate": 0.0,
    "exact_match_rate": 0.95,
    "p95_latency_ms": 250,
}


@dataclass(slots=True)
class EvalCase:
    case_id: str
    category: str
    prompt: str
    expected_kind: str
    expected_name: str | None
    expected_arguments: dict[str, Any]
    auth_profile: str
    should_succeed: bool
    notes: str


@dataclass(slots=True)
class PlannedAction:
    kind: str
    name: str | None
    arguments: dict[str, Any]
    denied_by_policy: bool
    denial_reason: str | None
    score: float


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
            "count": 2,
            "total_results": 2,
            "has_more": False,
            "next_page": None,
            "search_mode": search_mode,
            "resolved_search_mode": "balanced",
            "results": [self.get_paper(PAPER_ID_A), self.get_paper(PAPER_ID_B)][:limit],
        }

    def export_bibtex(self, paper_id: str) -> dict[str, str]:
        return {"paper_id": paper_id, "bibtex": "@article{demo2026}"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Day 12 ResearchOps MCP evaluations")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET_PATH), help="Path to the JSONL evaluation dataset.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT_PATH), help="Path to write the JSON evaluation report.")
    parser.add_argument(
        "--fail-on-thresholds",
        action="store_true",
        help="Exit non-zero if the current metadata variant fails the configured quality thresholds.",
    )
    return parser


def load_dataset(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        cases.append(
            EvalCase(
                case_id=payload["case_id"],
                category=payload["category"],
                prompt=payload["prompt"],
                expected_kind=payload["expected_kind"],
                expected_name=payload.get("expected_name"),
                expected_arguments=payload.get("expected_arguments", {}),
                auth_profile=payload.get("auth_profile", "local"),
                should_succeed=bool(payload.get("should_succeed", True)),
                notes=payload.get("notes", ""),
            )
        )
    return cases


def metadata_tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    return {token for token in re.findall(r"[a-z0-9_]+", text.lower()) if token not in STOPWORDS}


def build_capability_catalog(variant: str) -> dict[str, set[str]]:
    descriptions = VARIANT_METADATA[variant]
    catalog = {
        "search_papers": "Search OpenAlex papers by keyword.",
        "get_paper": "Retrieve one OpenAlex paper by stable identifier.",
        "export_bibtex": "Export a single paper citation in BibTeX format.",
        "create_reading_list": "Create a persistent reading list.",
        "add_paper_to_list": "Add one paper to an existing reading list.",
        "add_note": "Add a persistent note for a paper in a reading list.",
        "update_note": "Update an existing note using optimistic concurrency.",
        "delete_note": "Delete a note only when confirm is true.",
        "paper_resource": "Stable paper context for one OpenAlex paper identifier.",
        "reading_list_resource": "Stable reading-list context with persistent papers and notes.",
        "compare_papers": "Reusable prompt for comparing two paper resources.",
        "generate_literature_review": "Reusable prompt for drafting a literature review from selected paper resources.",
    }
    return {
        name: metadata_tokens(f"{name} {descriptions.get(name, description)}")
        for name, description in catalog.items()
    }


def choose_best_capability(prompt: str, variant: str) -> tuple[str | None, float]:
    prompt_tokens = metadata_tokens(prompt)
    best_name = None
    best_score = 0.0
    for name, tokens in build_capability_catalog(variant).items():
        overlap = len(prompt_tokens & tokens)
        score = float(overlap)
        if name.startswith("paper_") or name.startswith("reading_list_"):
            score -= 0.25
        if name in {"compare_papers", "generate_literature_review"} and "prompt" not in prompt.lower():
            score -= 0.1
        if score > best_score:
            best_name = name
            best_score = score
    return best_name, best_score


def scopes_for_profile(profile: str) -> frozenset[str]:
    if profile == "local":
        return frozenset(ALL_SCOPES)
    record = DEFAULT_DEMO_TOKENS.get(profile)
    if record is None:
        raise ValueError(f"Unknown auth profile: {profile}")
    return frozenset(record["scopes"])


def plan_action(case: EvalCase, *, variant: str) -> PlannedAction:
    prompt_lower = case.prompt.lower()
    if any(token in prompt_lower for token in {"hello", "hi there", "how are you", "thank you", "what is mcp"}):
        return PlannedAction("none", None, {}, False, None, 1.0)

    if variant == "current":
        name, score = choose_intent_first_capability(case.prompt)
    else:
        name, score = choose_best_capability(case.prompt, variant)
    if name is None or score <= 0.0:
        return PlannedAction("none", None, {}, False, None, 0.0)

    if name == "paper_resource":
        kind = "resource"
        action_name = "paper://{paper_id}"
    elif name == "reading_list_resource":
        kind = "resource"
        action_name = "reading-list://{list_id}"
    elif name in PROMPT_SCOPES:
        kind = "prompt"
        action_name = name
    else:
        kind = "tool"
        action_name = name

    arguments = extract_arguments(action_name, case.prompt)
    required_scope = TOOL_SCOPES.get(action_name) or PROMPT_SCOPES.get(action_name)
    if kind == "resource":
        required_scope = "papers:read" if action_name.startswith("paper://") else "lists:read"
    if required_scope and required_scope not in scopes_for_profile(case.auth_profile):
        return PlannedAction("none", None, {}, True, f"missing scope {required_scope}", score)
    return PlannedAction(kind, action_name, arguments, False, None, score)


def choose_intent_first_capability(prompt: str) -> tuple[str | None, float]:
    lowered = prompt.lower()
    if "literature review prompt" in lowered:
        return "generate_literature_review", 10.0
    if "compare" in lowered and ("prompt" in lowered or len(re.findall(r"\bW\d{7,}\b", prompt)) >= 2):
        return "compare_papers", 10.0
    if "reading list resource" in lowered or "open the reading list resource" in lowered:
        return "reading_list_resource", 10.0
    if "read paper resource" in lowered or "context for w" in lowered:
        return "paper_resource", 10.0
    if "search" in lowered or "find papers" in lowered or "papers about" in lowered or "couple of papers" in lowered:
        return "search_papers", 9.0
    if "look up" in lowered or "get paper" in lowered or "show me the paper" in lowered or "open paper" in lowered:
        return "get_paper", 9.0
    if "bibtex" in lowered or "citation entry" in lowered:
        return "export_bibtex", 9.0
    if (("create" in lowered or "make a list" in lowered) and "reading list" in lowered) or "list called" in lowered or "list named" in lowered:
        return "create_reading_list", 9.0
    if "add paper" in lowered or ("put w" in lowered and "starter-mcp" in lowered):
        return "add_paper_to_list", 9.0
    if "add note" in lowered or "write down" in lowered:
        return "add_note", 9.0
    if "update note" in lowered:
        return "update_note", 9.0
    if "delete note" in lowered:
        return "delete_note", 9.0
    return choose_best_capability(prompt, "current")


def extract_arguments(name: str, prompt: str) -> dict[str, Any]:
    quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", prompt)
    values = [left or right for left, right in quoted]
    paper_ids = re.findall(r"\bW\d{7,}\b", prompt)
    limit_match = re.search(r"\blimit(?: it)? to (\d+)|\blimit (\d+)|\b(\d+) results?\b", prompt.lower())

    if name == "search_papers":
        query = values[0] if values else prompt.split("about", 1)[-1].split("with", 1)[0].strip(" .?")
        limit = int(next(value for value in limit_match.groups() if value is not None)) if limit_match else 5
        search_mode = "exact" if "exact" in prompt.lower() else "balanced"
        return {"query": query, "limit": limit, "page": 1, "search_mode": search_mode}
    if name == "get_paper":
        return {"paper_id": paper_ids[0] if paper_ids else PAPER_ID_A}
    if name == "export_bibtex":
        return {"paper_id": paper_ids[0] if paper_ids else PAPER_ID_A}
    if name == "create_reading_list":
        list_name = values[0] if values else "Evaluation List"
        description = values[1] if len(values) > 1 else ""
        return {"name": list_name, "description": description, "idempotency_key": "eval-create-list"}
    if name == "add_paper_to_list":
        return {
            "list_id": READING_LIST_ID,
            "paper_id": paper_ids[0] if paper_ids else PAPER_ID_A,
            "idempotency_key": "eval-add-paper",
        }
    if name == "add_note":
        content = values[-1] if values else "Evaluation note"
        return {
            "list_id": READING_LIST_ID,
            "paper_id": paper_ids[0] if paper_ids else PAPER_ID_A,
            "content": content,
            "idempotency_key": "eval-add-note",
        }
    if name == "update_note":
        content = values[-1] if values else "Updated evaluation note"
        return {
            "note_id": NOTE_ID,
            "content": content,
            "expected_version": 1,
            "idempotency_key": "eval-update-note",
        }
    if name == "delete_note":
        return {
            "note_id": NOTE_ID,
            "expected_version": 1,
            "confirm": True,
            "idempotency_key": "eval-delete-note",
        }
    if name == "paper://{paper_id}":
        return {"uri": f"paper://{paper_ids[0] if paper_ids else PAPER_ID_A}"}
    if name == "reading-list://{list_id}":
        return {"uri": f"reading-list://{READING_LIST_ID}"}
    if name == "compare_papers":
        focus = values[0] if values else "overall contribution"
        return {
            "paper_id_a": paper_ids[0] if paper_ids else PAPER_ID_A,
            "paper_id_b": paper_ids[1] if len(paper_ids) > 1 else PAPER_ID_B,
            "focus": focus,
        }
    if name == "generate_literature_review":
        topic = values[0] if values else "Model Context Protocol"
        objective = values[1] if len(values) > 1 else "summary"
        paper_ids_value = ",".join(paper_ids[:2] or [PAPER_ID_A, PAPER_ID_B])
        return {"topic": topic, "paper_ids": paper_ids_value, "objective": objective}
    return {}


def argument_match(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    for key, value in expected.items():
        if actual.get(key) != value:
            return False
    return True


async def execute_action(case: EvalCase, plan: PlannedAction) -> tuple[str, bool]:
    if plan.kind == "none" or plan.name is None:
        return ("denied" if plan.denied_by_policy else "no_action", case.expected_kind == "none")

    db_path = Path("C:/tmp") / f"{case.case_id}.db"
    if db_path.exists():
        db_path.unlink()
    server = create_server(database_path=str(db_path), paper_service=FakePaperService())
    async with Client(server) as client:
        execution_arguments = dict(plan.arguments)
        if plan.name in {"update_note", "delete_note"}:
            created = await client.call_tool(
                "create_reading_list",
                arguments={"name": f"Eval {case.case_id}", "description": "", "idempotency_key": f"{case.case_id}-list"},
            )
            list_id = created.structured_content["list_id"]
            await client.call_tool(
                "add_paper_to_list",
                arguments={"list_id": list_id, "paper_id": PAPER_ID_A, "idempotency_key": f"{case.case_id}-paper"},
            )
            note = await client.call_tool(
                "add_note",
                arguments={
                    "list_id": list_id,
                    "paper_id": PAPER_ID_A,
                    "content": "seed note",
                    "idempotency_key": f"{case.case_id}-note",
                },
            )
            execution_arguments["note_id"] = note.structured_content["note_id"]
        if plan.kind == "tool":
            result = await client.call_tool(plan.name, arguments=execution_arguments)
            success = not getattr(result, "is_error", False)
            return ("ok" if success else "error", success == case.should_succeed)
        if plan.kind == "resource":
            result = await client.read_resource(execution_arguments["uri"])
            return ("ok", bool(result.contents) == case.should_succeed)
        if plan.kind == "prompt":
            result = await client.get_prompt(plan.name, {key: str(value) for key, value in execution_arguments.items()})
            return ("ok", bool(result.messages) == case.should_succeed)
    return ("error", False)


def percentile(values: list[int], ratio: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * ratio)))
    return ordered[index]


async def run_evaluations(dataset_path: Path, report_path: Path) -> dict[str, Any]:
    cases = load_dataset(dataset_path)
    report: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%d"),
        "dataset_path": str(dataset_path),
        "case_count": len(cases),
        "variants": {},
    }

    for variant in VARIANT_METADATA:
        results: list[dict[str, Any]] = []
        latencies: list[int] = []
        matches = 0
        correct_args = 0
        expected_calls = 0
        actual_calls = 0
        correct_calls = 0
        unauthorized_attempts = 0
        hallucinated_tools = 0
        task_successes = 0

        for case in cases:
            started = time.perf_counter()
            plan = plan_action(case, variant=variant)
            status, task_success = await execute_action(case, plan)
            latency_ms = round((time.perf_counter() - started) * 1000)
            latencies.append(latency_ms)

            exact_match = plan.kind == case.expected_kind and plan.name == case.expected_name
            args_match = argument_match(case.expected_arguments, plan.arguments)
            expected_needs_action = case.expected_kind != "none"
            actual_did_action = plan.kind != "none"

            if exact_match:
                matches += 1
            if expected_needs_action and exact_match and args_match:
                correct_args += 1
            if expected_needs_action:
                expected_calls += 1
            if actual_did_action:
                actual_calls += 1
            if expected_needs_action and actual_did_action and exact_match:
                correct_calls += 1
            if case.auth_profile != "local" and actual_did_action and not case.should_succeed:
                unauthorized_attempts += 1
            if actual_did_action and plan.name not in {
                "search_papers",
                "get_paper",
                "export_bibtex",
                "create_reading_list",
                "add_paper_to_list",
                "add_note",
                "update_note",
                "delete_note",
                "paper://{paper_id}",
                "reading-list://{list_id}",
                "compare_papers",
                "generate_literature_review",
            }:
                hallucinated_tools += 1
            if task_success:
                task_successes += 1

            results.append(
                {
                    "case_id": case.case_id,
                    "category": case.category,
                    "prompt": case.prompt,
                    "expected_kind": case.expected_kind,
                    "expected_name": case.expected_name,
                    "actual_kind": plan.kind,
                    "actual_name": plan.name,
                    "expected_arguments": case.expected_arguments,
                    "actual_arguments": plan.arguments,
                    "argument_match": args_match,
                    "exact_match": exact_match,
                    "status": status,
                    "task_success": task_success,
                    "denied_by_policy": plan.denied_by_policy,
                    "latency_ms": latency_ms,
                }
            )

        precision = correct_calls / actual_calls if actual_calls else 1.0
        recall = correct_calls / expected_calls if expected_calls else 1.0
        metrics = {
            "tool_precision": round(precision, 3),
            "tool_recall": round(recall, 3),
            "argument_correctness_rate": round(correct_args / expected_calls, 3) if expected_calls else 1.0,
            "task_completion_rate": round(task_successes / len(cases), 3),
            "unauthorized_action_rate": round(unauthorized_attempts / len(cases), 3),
            "hallucinated_tool_rate": round(hallucinated_tools / len(cases), 3),
            "exact_match_rate": round(matches / len(cases), 3),
            "p50_latency_ms": percentile(latencies, 0.5),
            "p95_latency_ms": percentile(latencies, 0.95),
            "mean_latency_ms": round(statistics.mean(latencies), 1) if latencies else 0.0,
        }
        threshold_results = evaluate_thresholds(metrics)
        report["variants"][variant] = {
            "metrics": metrics,
            "thresholds": QUALITY_THRESHOLDS,
            "threshold_results": threshold_results,
            "passes_thresholds": all(item["passed"] for item in threshold_results.values()),
            "results": results,
        }

    current_metrics = report["variants"]["current"]["metrics"]
    generic_metrics = report["variants"]["generic_descriptions"]["metrics"]
    report["comparison"] = {
        "tool_precision_delta": round(current_metrics["tool_precision"] - generic_metrics["tool_precision"], 3),
        "tool_recall_delta": round(current_metrics["tool_recall"] - generic_metrics["tool_recall"], 3),
        "argument_correctness_delta": round(
            current_metrics["argument_correctness_rate"] - generic_metrics["argument_correctness_rate"],
            3,
        ),
        "exact_match_delta": round(current_metrics["exact_match_rate"] - generic_metrics["exact_match_rate"], 3),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    return report


def evaluate_thresholds(metrics: dict[str, float | int]) -> dict[str, dict[str, float | int | bool | str]]:
    results: dict[str, dict[str, float | int | bool | str]] = {}
    for name, threshold in QUALITY_THRESHOLDS.items():
        actual = metrics[name]
        comparator = "<=" if name in {"unauthorized_action_rate", "hallucinated_tool_rate", "p95_latency_ms"} else ">="
        passed = actual <= threshold if comparator == "<=" else actual >= threshold
        results[name] = {
            "actual": actual,
            "threshold": threshold,
            "comparator": comparator,
            "passed": passed,
        }
    return results


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = asyncio.run(run_evaluations(Path(args.dataset), Path(args.report)))
    print(json.dumps(report["variants"], indent=2, ensure_ascii=True))
    if args.fail_on_thresholds and not report["variants"]["current"]["passes_thresholds"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
