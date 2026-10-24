"""Leakage-safe evaluation runner for the Sanctuary V2 conversation dataset.

Only ``user_prompt`` and state derived from earlier user prompts are passed to
Sanctuary. Gold annotations are attached to a result *after* inference and are
never added to the ResponsePlan or local generation prompt.

This runner reports structural and policy evidence. The dataset's free-text
``expected_state`` annotations are retained for human/adjudicated review; they
are not converted into invented semantic-accuracy scores.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = BACKEND_ROOT.parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.nlp_engine import analyze_turn  # noqa: E402
from app.services.nlp_service import NLPService  # noqa: E402
from app.services.memory_harness import apply_memory_harness  # noqa: E402
from app.services.response_planner import (  # noqa: E402
    build_response_plan,
    realize_plan_classically,
    validate_plan_response,
)
from app.services.response_policy import (  # noqa: E402
    validate_human_tone,
    validate_reflective_response,
)


DEFAULT_DATASET = WORKSPACE_ROOT / "sanctuary_v2_evaluation_dataset.json"
DEFAULT_OUTPUT = BACKEND_ROOT / "evaluation" / "sanctuary_v2_dataset_results.json"
EXPECTED_LABEL_RE = re.compile(r"`([A-Z_]+)`")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Sanctuary V2 dataset without leaking gold annotations.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mode", choices=("local", "classical"), default="local")
    parser.add_argument("--profile", choices=("low_resource", "balanced", "high_fidelity", "responsive", "stable"), default="balanced")
    parser.add_argument("--topic", help="Run only one topic_id.")
    parser.add_argument("--limit", type=int, help="Maximum total turns, useful for a smoke test.")
    return parser.parse_args()


def load_dataset(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    topics = value.get("topics")
    if not isinstance(topics, list) or not topics:
        raise ValueError("dataset must contain a non-empty topics list")
    identities: set[tuple[str, int]] = set()
    for topic in topics:
        topic_id = topic.get("topic_id")
        turns = topic.get("turns")
        if not isinstance(topic_id, str) or not isinstance(turns, list):
            raise ValueError("each topic requires topic_id and turns")
        for turn in turns:
            identity = (topic_id, int(turn["turn_id"]))
            if identity in identities:
                raise ValueError(f"duplicate topic-turn identity: {identity}")
            identities.add(identity)
            if not isinstance(turn.get("user_prompt"), str) or not turn["user_prompt"].strip():
                raise ValueError(f"missing user_prompt: {identity}")
            if not isinstance(turn.get("expected_state"), list):
                raise ValueError(f"missing expected_state list: {identity}")
    return value


def expected_labels(expected_state: list[str]) -> list[str]:
    labels: list[str] = []
    for annotation in expected_state:
        labels.extend(EXPECTED_LABEL_RE.findall(annotation))
    return sorted(set(labels))


def inference_only(
    prompt: str,
    state: dict[str, Any],
    service: NLPService,
    mode: str,
    profile: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Inference boundary: no annotation/gold argument exists here."""
    started = time.monotonic()
    analysis, next_state, _ = analyze_turn(
        prompt,
        state,
        {
            "alias_key": "sanctuary-dataset-evaluation-only",
            "local_unredacted": False,
            "mathematical_profile": profile,
        },
    )
    apply_memory_harness(
        analysis,
        next_state,
        state,
        memory_generation="evaluation-ephemeral",
        session_id="evaluation-ephemeral",
    )
    if mode == "local":
        response, response_mode = service.generate(
            analysis,
            prior_turns=state.get("turns", []),
            share_history=False,
            user_id=None,
        )
    else:
        plan = build_response_plan(analysis, state.get("turns", []))
        analysis["response_plan"] = plan
        response = realize_plan_classically(plan)
        response_mode = "classical_response_plan"

    plan = analysis["response_plan"]
    plan_validation = validate_plan_response(plan, response)
    reflective = validate_reflective_response(response)
    human_tone = validate_human_tone(response)
    redacted_text = analysis.get("redacted_text", "")
    traceability = []
    for claim in plan.get("claims_to_communicate", []):
        start, end = claim.get("span", [-1, -1])
        traceability.append(
            bool(0 <= start < end <= len(redacted_text) and redacted_text[start:end] == claim.get("text"))
        )

    result = {
        "response_text": response,
        "response_mode": response_mode,
        "latency_seconds": round(time.monotonic() - started, 4),
        "strategy": analysis.get("strategy"),
        "topic_assignment": analysis.get("topic_id"),
        "response_plan": plan,
        "generation": analysis.get("generation"),
        "policy": {
            "plan_response_valid": plan_validation["is_valid"],
            "plan_violations": plan_validation["violations"],
            "reflective_valid": reflective.is_valid,
            "reflective_violations": list(reflective.violations),
            "human_tone_valid": human_tone.is_valid,
            "human_tone_violations": list(human_tone.violations),
            "claim_spans_traceable": all(traceability),
            "claim_count": len(traceability),
        },
        "state_observation": {
            "correction_detected": bool(plan.get("correction_context", {}).get("is_correction")),
            "superseded_count": len(plan.get("correction_context", {}).get("superseded_propositions", [])),
            "tentative_claim_count": sum(
                claim.get("epistemic_status") == "tentative"
                for claim in plan.get("claims_to_communicate", [])
            ),
            "proposition_statuses": dict(Counter(
                item.get("status", "unknown")
                for item in analysis.get("mathematical_models", {})
                .get("evidence_belief_revision", {})
                .get("propositions", [])
            )),
            "graph_nodes": len(
                analysis.get("mathematical_models", {}).get("temporal_narrative_graph", {}).get("nodes", [])
            ),
            "graph_edges": len(
                analysis.get("mathematical_models", {}).get("temporal_narrative_graph", {}).get("edges", [])
            ),
            "canonical_memory": analysis.get("canonical_memory", {}),
            "memory_operations": analysis.get("memory_update", {}).get("operations", []),
            "retrieval_trace": analysis.get("context_packet", {}).get("retrieval_trace", {}),
            "historical_evidence_count": len(
                analysis.get("context_packet", {}).get("relevant_prior_evidence", [])
            ),
            "retrieval_abstained": analysis.get("context_packet", {}).get("abstained_from_history", True),
        },
    }
    return result, next_state


def run(dataset: dict[str, Any], mode: str, profile: str, topic_filter: str | None, limit: int | None) -> dict[str, Any]:
    service = NLPService(alias_key="sanctuary-dataset-evaluation-only")
    records: list[dict[str, Any]] = []
    remaining = limit
    started = time.monotonic()

    for topic in dataset["topics"]:
        if topic_filter and topic["topic_id"] != topic_filter:
            continue
        state: dict[str, Any] = {}
        for source_turn in topic["turns"]:
            if remaining is not None and remaining <= 0:
                break

            # Deliberately construct the inference input from one scalar. The
            # source record and its expected_state never cross this boundary.
            prompt = str(source_turn["user_prompt"])
            inference, state = inference_only(prompt, state, service, mode, profile)

            # Gold is copied only after the model and validators have finished.
            gold = copy.deepcopy(source_turn["expected_state"])
            labels = expected_labels(gold)
            records.append({
                "topic_id": topic["topic_id"],
                "topic_title": topic.get("title"),
                "turn_id": int(source_turn["turn_id"]),
                "user_prompt": prompt,
                **inference,
                "evaluator_only": {
                    "expected_state": gold,
                    "expected_labels": labels,
                    "semantic_judgment": "not_scored_requires_human_or_machine_readable_rubric",
                    "expects_correction": bool({"CORRECTED", "SUPERSEDED"} & set(labels)),
                    "expects_uncertainty": bool({"TENTATIVE", "UNRESOLVED"} & set(labels)),
                },
            })
            if remaining is not None:
                remaining -= 1
        if remaining is not None and remaining <= 0:
            break

    correction_records = [r for r in records if r["evaluator_only"]["expects_correction"]]
    uncertainty_records = [r for r in records if r["evaluator_only"]["expects_uncertainty"]]
    latencies = [r["latency_seconds"] for r in records]
    topic_summaries = []
    for topic_id in dict.fromkeys(r["topic_id"] for r in records):
        rows = [r for r in records if r["topic_id"] == topic_id]
        topic_summaries.append({
            "topic_id": topic_id,
            "turns": len(rows),
            "policy_valid": sum(r["policy"]["plan_response_valid"] for r in rows),
            "traceable": sum(r["policy"]["claim_spans_traceable"] for r in rows),
            "corrections_expected": sum(r["evaluator_only"]["expects_correction"] for r in rows),
            "corrections_detected": sum(
                r["evaluator_only"]["expects_correction"] and r["state_observation"]["correction_detected"]
                for r in rows
            ),
            "mean_latency_seconds": round(statistics.mean(r["latency_seconds"] for r in rows), 4),
        })

    transformer_accepted = sum(r["response_mode"] == "reflective_local_transformer" for r in records)
    return {
        "schema_version": "sanctuary.dataset-evaluation.v1",
        "dataset": {
            "name": dataset.get("dataset_name"),
            "version": dataset.get("dataset_version"),
            "sha256": hashlib.sha256(json.dumps(dataset, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        },
        "inference_contract": {
            "model_visible_dataset_fields": ["user_prompt"],
            "model_visible_context": "state derived only from prior user_prompt values in the same topic",
            "evaluator_only_fields": ["expected_state", "annotation_labels", "evaluation_dimensions", "acceptance_gates"],
            "gold_leakage_prevented_by": "inference_only(prompt, state, service, mode, profile) has no gold parameter",
            "persistent_application_writes": False,
            "hosted_provider": False,
        },
        "configuration": {"mode": mode, "mathematical_profile": profile, "topic_filter": topic_filter, "limit": limit},
        "summary": {
            "turns_executed": len(records),
            "topics_executed": len({r["topic_id"] for r in records}),
            "policy_valid": sum(r["policy"]["plan_response_valid"] for r in records),
            "traceable_claim_spans": sum(r["policy"]["claim_spans_traceable"] for r in records),
            "expected_correction_turns": len(correction_records),
            "expected_corrections_detected": sum(r["state_observation"]["correction_detected"] for r in correction_records),
            "expected_uncertainty_turns": len(uncertainty_records),
            "expected_uncertainty_with_tentative_plan_claim": sum(
                r["state_observation"]["tentative_claim_count"] > 0 for r in uncertainty_records
            ),
            "generation_modes": dict(Counter(r["response_mode"] for r in records)),
            "transformer_accepted_turns": transformer_accepted,
            "transformer_accepted_rate": round(transformer_accepted / len(records), 6) if records else None,
            "strategies": dict(Counter(r["strategy"] for r in records)),
            "mean_latency_seconds": round(statistics.mean(latencies), 4) if latencies else None,
            "median_latency_seconds": round(statistics.median(latencies), 4) if latencies else None,
            "total_runtime_seconds": round(time.monotonic() - started, 4),
            "semantic_state_accuracy": None,
            "semantic_state_accuracy_reason": "expected_state is free text and has not been independently adjudicated or mapped to a frozen scoring rubric",
        },
        "topic_summaries": topic_summaries,
        "records": records,
    }


def markdown_report(result: dict[str, Any], output: Path) -> str:
    summary = result["summary"]
    lines = [
        "# Sanctuary V2 Dataset Evaluation",
        "",
        f"- Dataset: `{result['dataset']['name']}` v{result['dataset']['version']}",
        f"- Mode: `{result['configuration']['mode']}`",
        f"- Turns executed: {summary['turns_executed']}",
        f"- Topics executed: {summary['topics_executed']}",
        f"- Policy-valid responses: {summary['policy_valid']}/{summary['turns_executed']}",
        f"- Transformer-accepted turns: {summary['transformer_accepted_turns']}/{summary['turns_executed']} "
        f"({summary['transformer_accepted_rate']})",
        f"- Traceable claim spans: {summary['traceable_claim_spans']}/{summary['turns_executed']}",
        f"- Expected correction turns detected: {summary['expected_corrections_detected']}/{summary['expected_correction_turns']}",
        f"- Mean latency: {summary['mean_latency_seconds']} seconds",
        f"- Median latency: {summary['median_latency_seconds']} seconds",
        f"- Total runtime: {summary['total_runtime_seconds']} seconds",
        "",
        "## Leakage boundary",
        "",
        "Only `user_prompt` and state derived from preceding prompts in the same topic were passed to Sanctuary. "
        "`expected_state` and all other gold/evaluation annotations were attached after inference.",
        "",
        "## Interpretation boundary",
        "",
        "Policy, traceability and execution counts are automated evidence. Semantic state accuracy remains unscored because "
        "the gold annotations are free text and have not been mapped to a frozen adjudicated rubric.",
        "",
        "## Per-topic execution",
        "",
        "| Topic | Turns | Policy valid | Traceable | Corrections detected/expected | Mean seconds |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["topic_summaries"]:
        lines.append(
            f"| {row['topic_id']} | {row['turns']} | {row['policy_valid']} | {row['traceable']} | "
            f"{row['corrections_detected']}/{row['corrections_expected']} | {row['mean_latency_seconds']} |"
        )
    lines.extend(["", f"Machine-readable results: [{output.name}]({output.name})", ""])
    return "\n".join(lines)


def main() -> int:
    args = arguments()
    dataset = load_dataset(args.dataset.resolve())
    result = run(dataset, args.mode, args.profile, args.topic, args.limit)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output.with_suffix(".jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in result["records"]),
        encoding="utf-8",
    )
    output.with_suffix(".md").write_text(markdown_report(result, output), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"Results: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
