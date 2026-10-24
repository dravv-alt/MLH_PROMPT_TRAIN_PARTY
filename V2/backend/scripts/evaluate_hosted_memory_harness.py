"""Run the 80-turn dataset against an explicitly enabled hosted provider.

This is an evaluation harness, not an application request path.  It never
writes application state, never sends gold annotations to a provider, and
never substitutes the deterministic fallback as a test result.  The fallback
is only a grounded source text for the provider's rewrite task.

Only redacted current text and active, bounded excerpts selected by the memory
harness leave the process.  Identifier mappings live in memory for one topic
only so a provider response can be restored for interactive display; the JSON
report deliberately stores only redacted provider input/output.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = BACKEND_ROOT.parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env", override=False)

from app.services.groq_client import groq_reflector  # noqa: E402
from app.services.local_generation import repair_second_person_voice  # noqa: E402
from app.services.memory_harness import apply_memory_harness  # noqa: E402
from app.services.nlp_engine import analyze_turn  # noqa: E402
from app.services.privacy import restore_identifiers  # noqa: E402
from app.services.response_planner import (  # noqa: E402
    build_response_plan,
    realize_plan_classically,
    validate_plan_response,
)
from app.services.response_semantics import evaluate_candidates  # noqa: E402
from app.services.response_semantics import warm_semantic_worker  # noqa: E402
from app.services.neural_runtime import NLI  # noqa: E402


DEFAULT_DATASET = WORKSPACE_ROOT / "sanctuary_v2_evaluation_dataset.json"
DEFAULT_OUTPUT = BACKEND_ROOT / "evaluation" / "hosted_memory_harness_80.json"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Redacted hosted evaluation through Sanctuary's memory harness.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-interval-seconds", type=float, default=1.25)
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def load_dataset(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value.get("topics"), list):
        raise ValueError("Dataset must contain topics")
    return value


def provider_prompt(fallback: str, claims: list[str], historical: list[dict[str, Any]]) -> str:
    """Build the *only* text supplied to Groq: all fields are redacted."""
    excerpts = [str(row.get("text", ""))[:300] for row in historical[:3] if row.get("text")]
    lines = [
        "Task: rewrite the supplied reflection so it sounds warmer and more natural.",
        "Keep every current fact. Add nothing. Preserve uncertainty wording.",
        "Use relevant prior context only to avoid contradicting it; do not introduce a new fact from it.",
        "At most 2 sentences and 70 words. Output only the reflection.",
        "Do not ask, advise, diagnose, explain the task, or mention instructions.",
        "",
        "Grounded current reflection:",
        fallback,
        "",
        "Approved current claims (second-person wording):",
        *[f"- {item}" for item in claims],
    ]
    if excerpts:
        lines.extend(["", "Relevant earlier context selected by the local memory harness:"])
        lines.extend(f"- {item}" for item in excerpts)
    return "\n".join(lines)


def call_rate_limited(prompt: str, *, last_call: list[float], interval: float, max_attempts: int) -> tuple[str | None, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    for attempt in range(1, max_attempts + 1):
        wait = max(0.0, interval - (time.monotonic() - last_call[0]))
        if wait:
            time.sleep(wait)
        started = time.monotonic()
        response = groq_reflector.generate(prompt)
        last_call[0] = time.monotonic()
        attempts.append({"attempt": attempt, "received": bool(response), "latency_seconds": round(last_call[0] - started, 4)})
        if response:
            return response, attempts
        if attempt < max_attempts:
            time.sleep(min(12.0, 1.0 * (2 ** (attempt - 1))))
    return None, attempts


def inference_turn(prompt: str, state: dict[str, Any], entity_mapping: dict[str, str], last_call: list[float], args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    # This function has deliberately no gold/evaluator parameter.
    analysis, delta, ephemeral = analyze_turn(prompt, state, {
        "alias_key": "hosted-evaluation-ephemeral-only",
        "local_unredacted": False,
        "mathematical_profile": "balanced",
    })
    entity_mapping.update(ephemeral.get("mapping", {}))
    apply_memory_harness(analysis, delta, state, memory_generation="hosted-evaluation-ephemeral", session_id="hosted-evaluation-ephemeral")
    plan = build_response_plan(analysis, state.get("turns", []), include_historical_context=True)
    analysis["response_plan"] = plan
    fallback = realize_plan_classically(plan)
    claims = [repair_second_person_voice(row.get("text", "")) for row in plan.get("claims_to_communicate", []) if row.get("text")]
    historical = list(plan.get("memory_context", {}).get("historical_evidence", []))
    outgoing = provider_prompt(fallback, claims, historical)
    # Fail before sending any surface that our redactor identified locally.
    leaked = [token for token, surface in entity_mapping.items()
              if surface and re.search(r"(?<!\w)" + re.escape(surface) + r"(?!\w)", outgoing, re.I)]
    if leaked:
        raise RuntimeError("Provider privacy boundary failed: detected surface remains in prompt")
    raw, attempts = call_rate_limited(outgoing, last_call=last_call, interval=args.min_interval_seconds, max_attempts=args.max_attempts)

    # Never send original text, mappings, or expected_state.  Never ship F as a
    # replacement result: a failed provider turn stays an explicit failure.
    if not raw:
        return {
            "redacted_input": analysis["redacted_text"],
            "provider_prompt": outgoing,
            "provider_response_redacted": None,
            "display_response_restored": None,
            "status": "provider_unavailable_after_retries",
            "attempts": attempts,
            "memory": {"historical_evidence_count": len(historical), "retrieval_trace": analysis.get("context_packet", {}).get("retrieval_trace", {})},
            "policy": None,
        }, delta

    validation = validate_plan_response(plan, raw)
    semantic_rows = evaluate_candidates(plan, [raw]) if validation["is_valid"] else []
    semantic = semantic_rows[0] if semantic_rows else {"status": "not_run", "is_valid": False, "violations": []}
    accepted = bool(validation["is_valid"] and semantic.get("is_valid"))
    # Restored text is returned only in the in-process result for an interactive
    # caller.  The persisted evaluation record below intentionally omits it.
    restored = restore_identifiers(raw, entity_mapping)
    return {
        "redacted_input": analysis["redacted_text"],
        "provider_prompt": outgoing,
        "provider_response_redacted": raw,
        "display_response_restored": restored,
        "status": "accepted" if accepted else "rejected_by_local_validators",
        "attempts": attempts,
        "memory": {
            "historical_evidence_count": len(historical),
            "historical_excerpt_count_sent": min(3, len([r for r in historical if r.get("text")])),
            "retrieval_trace": analysis.get("context_packet", {}).get("retrieval_trace", {}),
        },
        "privacy": {"detected_surface_leak_count": len(leaked),
                    "restored_placeholder_count": sum(raw.count(token) for token in entity_mapping),
                    "unresolved_placeholders": sorted(set(re.findall(r"\[entity_e\d+\]", restored)))},
        "policy": {"plan": validation, "semantic": semantic},
    }, delta


def sanitize_record(value: dict[str, Any]) -> dict[str, Any]:
    """Do not write restored text or raw identity mappings to disk."""
    copy_value = copy.deepcopy(value)
    copy_value.pop("display_response_restored", None)
    return copy_value


def run(dataset: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if not groq_reflector.enabled:
        raise RuntimeError("Groq is not enabled. Configure GROQ_API_KEY; no request was made.")
    # A cold semantic worker would turn every otherwise-valid hosted draft into
    # a false rejection.  Warm it before the first external request, but keep a
    # bounded failure mode rather than silently accepting unvalidated text.
    warm_semantic_worker()
    warm_deadline = time.monotonic() + 55.0
    while NLI.state == "warming" and time.monotonic() < warm_deadline:
        time.sleep(0.25)
    if NLI.state != "ready":
        raise RuntimeError(f"Local semantic validator unavailable after warm-up: {NLI.state}")
    records: list[dict[str, Any]] = []
    last_call = [0.0]
    remaining = args.limit
    started = time.monotonic()
    for topic in dataset["topics"]:
        state: dict[str, Any] = {}
        entity_mapping: dict[str, str] = {}
        for source_turn in topic["turns"]:
            if remaining is not None and remaining <= 0:
                break
            # Gold annotations intentionally stay outside inference_turn.
            observed, state = inference_turn(str(source_turn["user_prompt"]), state, entity_mapping, last_call, args)
            records.append({"topic_id": topic["topic_id"], "turn_id": int(source_turn["turn_id"]), **sanitize_record(observed)})
            print(f"{len(records)}/80 {topic['topic_id']}:{source_turn['turn_id']} {observed['status']} history={observed['memory'].get('historical_excerpt_count_sent', 0)}", flush=True)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.with_suffix('.progress.json').write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding='utf-8')
            if remaining is not None:
                remaining -= 1
        if remaining is not None and remaining <= 0:
            break
    latencies = [attempt["latency_seconds"] for row in records for attempt in row["attempts"]]
    return {
        "schema_version": "sanctuary.hosted-memory-evaluation.v1",
        "dataset_sha256": hashlib.sha256(json.dumps(dataset, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "contract": {
            "hosted_provider": "groq",
            "hosted_model": groq_reflector.model_name,
            "persistent_application_writes": False,
            "fallback_as_result": False,
            "provider_receives": "redacted current fallback, approved current claims, and up to three redacted memory-harness excerpts",
            "provider_never_receives": ["raw user text", "identifier mappings", "expected_state", "gold annotations"],
            "report_excludes": ["raw user text", "restored output", "identifier mappings"],
        },
        "configuration": {"min_interval_seconds": args.min_interval_seconds, "max_attempts": args.max_attempts, "limit": args.limit},
        "summary": {
            "turns": len(records),
            "accepted": sum(row["status"] == "accepted" for row in records),
            "validator_rejected": sum(row["status"] == "rejected_by_local_validators" for row in records),
            "provider_unavailable": sum(row["status"] == "provider_unavailable_after_retries" for row in records),
            "mean_provider_call_seconds": round(statistics.mean(latencies), 4) if latencies else None,
            "runtime_seconds": round(time.monotonic() - started, 4),
        },
        "records": records,
    }


def main() -> int:
    args = arguments()
    result = run(load_dataset(args.dataset), args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"Wrote redacted report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
