from pathlib import Path

from researchops_mcp.evals import (
    DEFAULT_DATASET_PATH,
    QUALITY_THRESHOLDS,
    VARIANT_METADATA,
    argument_match,
    evaluate_thresholds,
    load_dataset,
    plan_action,
)


def test_eval_dataset_has_roadmap_scale() -> None:
    cases = load_dataset(Path(DEFAULT_DATASET_PATH))

    assert len(cases) >= 40


def test_eval_runner_refuses_unauthorized_write_case() -> None:
    cases = load_dataset(Path(DEFAULT_DATASET_PATH))
    target = next(case for case in cases if case.case_id == "eval-033")

    plan = plan_action(target, variant="current")

    assert plan.kind == "none"
    assert plan.denied_by_policy is True


def test_eval_runner_matches_expected_arguments_for_direct_search() -> None:
    cases = load_dataset(Path(DEFAULT_DATASET_PATH))
    target = next(case for case in cases if case.case_id == "eval-001")

    plan = plan_action(target, variant="current")

    assert plan.name == "search_papers"
    assert argument_match(target.expected_arguments, plan.arguments) is True


def test_eval_thresholds_capture_expected_pass_fail_shape() -> None:
    current_results = evaluate_thresholds({name: value for name, value in QUALITY_THRESHOLDS.items()} | {"p50_latency_ms": 100, "mean_latency_ms": 100})
    generic_results = evaluate_thresholds(
        {
            "tool_precision": 0.5,
            "tool_recall": 0.5,
            "argument_correctness_rate": 0.5,
            "task_completion_rate": 0.8,
            "unauthorized_action_rate": 0.1,
            "hallucinated_tool_rate": 0.1,
            "exact_match_rate": 0.5,
            "p50_latency_ms": 100,
            "p95_latency_ms": 400,
            "mean_latency_ms": 120,
        }
    )

    assert all(item["passed"] for item in current_results.values())
    assert any(not item["passed"] for item in generic_results.values())


def test_eval_variants_are_available_for_comparison() -> None:
    assert set(VARIANT_METADATA) == {"current", "generic_descriptions"}
