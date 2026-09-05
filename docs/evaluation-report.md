# Day 12 Evaluation Report

## Scope

- Date: 2026-09-04
- Dataset: `tests/evals/researchops_eval_dataset.jsonl`
- Case count: 42
- Variants compared:
  - `current`: the current ResearchOps MCP tool names and descriptions
  - `generic_descriptions`: intentionally flattened descriptions to show metadata regression risk

## Categories Covered

- direct tool requests
- indirect tool requests
- resource reads
- prompt retrieval
- no-tool requests
- ambiguous requests
- workflow first-step requests
- unauthorized actions
- prompt-injection attempts
- dependency-failure scenarios

## Thresholds

The current metadata variant must satisfy these minimum thresholds:

- `tool_precision >= 0.95`
- `tool_recall >= 0.95`
- `argument_correctness_rate >= 0.95`
- `task_completion_rate >= 1.0`
- `unauthorized_action_rate <= 0.0`
- `hallucinated_tool_rate <= 0.0`
- `exact_match_rate >= 0.95`
- `p95_latency_ms <= 250`

## Results

### Current Metadata Variant

- `tool_precision`: `1.0`
- `tool_recall`: `1.0`
- `argument_correctness_rate`: `0.971`
- `task_completion_rate`: `1.0`
- `unauthorized_action_rate`: `0.0`
- `hallucinated_tool_rate`: `0.0`
- `exact_match_rate`: `1.0`
- `p50_latency_ms`: `140`
- `p95_latency_ms`: `202`
- `mean_latency_ms`: `126.3`
- Threshold result: `PASS`

### Generic Description Variant

- It is intentionally worse on indirect requests, ambiguous requests, unauthorized-write refusal, and dependency-oriented prompts.
- The report JSON shows why descriptive MCP metadata matters: when descriptions are flattened, the planner confuses tools, prompts, and resources much more often.

### Comparison

- `tool_precision_delta`: `+0.469`
- `tool_recall_delta`: `+0.484`
- `argument_correctness_delta`: `+0.519`
- `exact_match_delta`: `+0.476`

## Interpretation

The Day 12 harness is not trying to benchmark a frontier model. It gives ResearchOps MCP a deterministic regression layer for the part MCP cares about most: whether the model-facing interface still drives the right capability selection and argument shape.

The strongest Day 12 takeaway is that MCP metadata is operational behavior, not only documentation. The current ResearchOps descriptions produce strong selection quality, while generic descriptions materially degrade it.

## Commands Run

```powershell
pytest tests/unit/test_eval_runner.py
python -m researchops_mcp.evals --fail-on-thresholds
```

## Artifacts

- Machine-readable report: `docs/evaluation-report.json`
- Human-readable summary: `docs/evaluation-report.md`
