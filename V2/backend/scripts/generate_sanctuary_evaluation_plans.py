"""Realize frozen evaluation ResponsePlans with the local Transformer.

This second evaluation stage intentionally runs in a fresh process so DMRST
and the local generator do not need to reside in memory together. Although the
source result contains evaluator-only gold for later comparison, only the
``response_plan`` value is passed to ``LocalGenerationProvider.generate``.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.local_generation import LOCAL_GENERATOR  # noqa: E402
from app.services.response_planner import validate_plan_response  # noqa: E402
from app.services.response_policy import validate_human_tone, validate_reflective_response  # noqa: E402


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate responses from leakage-safe frozen ResponsePlans.")
    parser.add_argument(
        "--input",
        type=Path,
        default=BACKEND_ROOT / "evaluation" / "sanctuary_v2_dataset_classical_results.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_ROOT / "evaluation" / "sanctuary_v2_dataset_local_results.json",
    )
    parser.add_argument("--profile", choices=("precise", "balanced", "natural"), default="balanced")
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def generate(plan: dict[str, Any], profile: str) -> dict[str, Any]:
    started = time.monotonic()
    response, diagnostics = LOCAL_GENERATOR.generate(
        plan,
        {"profile": profile, "maximum_attempts": 2},
    )
    plan_validation = validate_plan_response(plan, response)
    reflective = validate_reflective_response(response)
    human_tone = validate_human_tone(response)
    return {
        "response_text": response,
        "response_mode": "reflective_local_transformer"
        if diagnostics.get("mode") == "local_transformer"
        else "classical_local_fallback",
        "generation": diagnostics,
        "generation_latency_seconds": round(time.monotonic() - started, 4),
        "policy": {
            "plan_response_valid": plan_validation["is_valid"],
            "plan_violations": plan_validation["violations"],
            "reflective_valid": reflective.is_valid,
            "reflective_violations": list(reflective.violations),
            "human_tone_valid": human_tone.is_valid,
            "human_tone_violations": list(human_tone.violations),
        },
    }


def report(result: dict[str, Any], output: Path) -> str:
    summary = result["summary"]
    lines = [
        "# Sanctuary V2 Local Transformer Dataset Evaluation",
        "",
        f"- Turns generated: {summary['turns_generated']}",
        f"- Accepted local Transformer responses: {summary['local_transformer_responses']}",
        f"- Classical fallbacks: {summary['classical_fallbacks']}",
        f"- Policy-valid final responses: {summary['policy_valid']}/{summary['turns_generated']}",
        f"- Rejected Transformer candidates: {summary['rejected_candidates']}",
        f"- Mean generation latency: {summary['mean_generation_latency_seconds']} seconds",
        f"- Median generation latency: {summary['median_generation_latency_seconds']} seconds",
        f"- Total runtime: {summary['total_runtime_seconds']} seconds",
        "",
        "## Leakage boundary",
        "",
        "Generation received only each frozen `response_plan`. `expected_state`, topic metadata and acceptance annotations "
        "were not supplied to the local model or generation prompt.",
        "",
        "## Interpretation boundary",
        "",
        "These counts establish execution and validator behavior, not semantic-state accuracy or human-rated naturalness.",
        "",
        f"Machine-readable results: [{output.name}]({output.name})",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = arguments()
    source = json.loads(args.input.resolve().read_text(encoding="utf-8"))
    records = source["records"][: args.limit] if args.limit else source["records"]
    output_records = []
    started = time.monotonic()
    for source_record in records:
        # This is the complete model-facing object. Never pass source_record.
        plan = source_record["response_plan"]
        generated = generate(plan, args.profile)
        output_records.append({
            "topic_id": source_record["topic_id"],
            "topic_title": source_record.get("topic_title"),
            "turn_id": source_record["turn_id"],
            "user_prompt": source_record["user_prompt"],
            "response_plan": plan,
            **generated,
            # Copied only after generation for evaluator-side inspection.
            "evaluator_only": source_record["evaluator_only"],
        })

    latencies = [row["generation_latency_seconds"] for row in output_records]
    modes = Counter(row["response_mode"] for row in output_records)
    attempts = [attempt for row in output_records for attempt in (row["generation"] or {}).get("attempts", [])]
    result = {
        "schema_version": "sanctuary.dataset-local-generation.v1",
        "source_analysis": str(args.input.resolve()),
        "dataset": source["dataset"],
        "inference_contract": {
            "model_visible_fields": ["response_plan"],
            "evaluator_only_fields": ["expected_state", "expected_labels", "topic metadata", "acceptance gates"],
            "gold_leakage_prevented_by": "LocalGenerationProvider.generate receives plan, never the source record",
            "hosted_provider": False,
            "persistent_application_writes": False,
        },
        "configuration": {"profile": args.profile, "limit": args.limit},
        "summary": {
            "turns_generated": len(output_records),
            "local_transformer_responses": modes["reflective_local_transformer"],
            "classical_fallbacks": modes["classical_local_fallback"],
            "policy_valid": sum(row["policy"]["plan_response_valid"] for row in output_records),
            "rejected_candidates": sum(attempt.get("status") == "rejected" for attempt in attempts),
            "generation_errors": sum(attempt.get("status") == "error" for attempt in attempts),
            "mean_generation_latency_seconds": round(statistics.mean(latencies), 4) if latencies else None,
            "median_generation_latency_seconds": round(statistics.median(latencies), 4) if latencies else None,
            "total_runtime_seconds": round(time.monotonic() - started, 4),
            "semantic_state_accuracy": None,
            "semantic_state_accuracy_reason": "requires human review or a frozen machine-readable rubric",
        },
        "records": output_records,
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output.with_suffix(".jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in output_records),
        encoding="utf-8",
    )
    output.with_suffix(".md").write_text(report(result, output), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"Results: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
