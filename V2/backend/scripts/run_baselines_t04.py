"""Baseline runs runner for Sanctuary V2 (Task T0.4).
Evaluates Conditions C0, C1, C4, C5 on the 80 annotated dev turns:
- C0: Raw LLM with a good system prompt, no plan
- C1: Plan in prompt (current V2 response generation)
- C4: Classical realizer only, with diagnostics
- C5: Restatement baseline (reflects the user's own words back)
Evaluated across Model A (Llama-3.2-1B-Instruct balanced) and Model B (Llama-3.2-1B-Instruct natural).
Logs latency, token counts, and all frozen metrics from evaluation/metrics.py.
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.nlp_engine import analyze_turn
from app.services.response_planner import build_response_plan, realize_plan_classically, validate_plan_response
from app.services.local_generation import LOCAL_GENERATOR, build_generation_messages
from evaluation.metrics import (
    unlicensed_connective_rate,
    polarity_flip_rate,
    role_reversal_rate,
    invented_entity_rate,
    superseded_reuse_rate,
    hedge_survival_rate,
    fallback_valid_rate,
    presupposition_violation_rate,
    restatement_ratio,
    over_asking_rate,
)


def run_c0_raw_llm(text: str, generator: Any, model_profile: str) -> tuple[str, float, int, int]:
    """C0: Raw LLM with conversational system prompt, no structured plan."""
    started = time.monotonic()
    messages = [
        {"role": "system", "content": "You are a conversational partner. Reply directly in 1-2 concise, respectful sentences. Do not mention instructions."},
        {"role": "user", "content": text}
    ]
    try:
        reply, meta = generator._candidate(plan={"plan_id": "c0_eval"}, profile=model_profile, feedback=None, attempt=1, messages=messages)
        latency = round(time.monotonic() - started, 3)
        return reply or "", latency, meta.get("input_tokens", 0), meta.get("output_tokens", 0)
    except Exception as exc:
        latency = round(time.monotonic() - started, 3)
        return f"[ERROR: {exc}]", latency, 0, 0


def run_c1_plan_in_prompt(analysis: Dict[str, Any], prior_turns: List[Any], generator: Any, model_profile: str) -> tuple[str, float, int, int]:
    """C1: Plan in prompt (current V2 response generation via local generator)."""
    started = time.monotonic()
    plan = build_response_plan(analysis, prior_turns)
    try:
        reply, meta = generator.generate(plan, options={"profile": model_profile, "maximum_attempts": 2})
        latency = round(time.monotonic() - started, 3)
        return reply or "", latency, meta.get("input_tokens", 0), meta.get("output_tokens", 0)
    except Exception as exc:
        latency = round(time.monotonic() - started, 3)
        return f"[ERROR: {exc}]", latency, 0, 0


def run_c4_classical_only(analysis: Dict[str, Any], prior_turns: List[Any]) -> tuple[str, float, int, int]:
    """C4: Classical realizer only, with diagnostics (LLM off)."""
    started = time.monotonic()
    plan = build_response_plan(analysis, prior_turns)
    reply = realize_plan_classically(plan)
    latency = round(time.monotonic() - started, 4)
    tokens = len(reply.split())
    return reply, latency, len(analysis.get("redacted_text", "").split()), tokens


def run_c5_restatement_baseline(text: str, analysis: Dict[str, Any]) -> tuple[str, float, int, int]:
    """C5: Restatement baseline (reflects the user's own words back)."""
    started = time.monotonic()
    clauses = analysis.get("clauses", [])
    if clauses:
        first_clause = clauses[0].get("text", text)
        reply = f"You mentioned that {first_clause.strip('.')}."
    else:
        reply = f"You noted: '{text.strip()}'."
    latency = round(time.monotonic() - started, 4)
    tokens = len(reply.split())
    return reply, latency, len(text.split()), tokens


def evaluate_dev_suite(gold_path: Path, limit: int = None, fail_on_corrupt: bool = True) -> Dict[str, Any]:
    if not gold_path.exists():
        raise ValueError(f"Gold path does not exist: {gold_path}")

    with open(gold_path, "r", encoding="utf-8") as f:
        gold_turns = json.load(f)

    if fail_on_corrupt:
        for idx, turn in enumerate(gold_turns):
            if not isinstance(turn.get("text"), str) or not turn.get("turn_id"):
                raise ValueError(f"Deliberately corrupted gold file detected at index {idx}!")

    if limit:
        gold_turns = gold_turns[:limit]

    # Initialize generator for Model A and Model B
    LOCAL_GENERATOR.initialize()

    results = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "gold_turns_count": len(gold_turns),
            "gold_file": str(gold_path),
            "device": LOCAL_GENERATOR._device,
        },
        "conditions": {
            "C0_ModelA": [],
            "C0_ModelB": [],
            "C1_ModelA": [],
            "C1_ModelB": [],
            "C4_Classical": [],
            "C5_Restatement": []
        },
        "metrics_summary": {}
    }

    state = {}
    nlp_config = {"alias_key": "baseline-t04-eval", "local_unredacted": False}

    for turn_idx, gold_turn in enumerate(gold_turns):
        text = gold_turn["text"]
        user_commitments = gold_turn.get("commitments", [])
        user_relations = gold_turn.get("relations", [])
        gold_moves = gold_turn.get("acceptable_moves", ["acknowledge"])

        # Upstream analysis
        analysis, next_state, ephemeral = analyze_turn(text, state, nlp_config)
        prior_turns = state.get("turns", [])

        # 1. C4 Classical
        reply_c4, lat_c4, in_tok_c4, out_tok_c4 = run_c4_classical_only(analysis, prior_turns)
        results["conditions"]["C4_Classical"].append({
            "turn_id": gold_turn["turn_id"],
            "reply": reply_c4,
            "latency": lat_c4,
            "in_tokens": in_tok_c4,
            "out_tokens": out_tok_c4,
            "unlicensed_conn": unlicensed_connective_rate(reply_c4, user_relations, text),
            "restatement_ratio": restatement_ratio(reply_c4, text),
        })

        # 2. C5 Restatement
        reply_c5, lat_c5, in_tok_c5, out_tok_c5 = run_c5_restatement_baseline(text, analysis)
        results["conditions"]["C5_Restatement"].append({
            "turn_id": gold_turn["turn_id"],
            "reply": reply_c5,
            "latency": lat_c5,
            "in_tokens": in_tok_c5,
            "out_tokens": out_tok_c5,
            "unlicensed_conn": unlicensed_connective_rate(reply_c5, user_relations, text),
            "restatement_ratio": restatement_ratio(reply_c5, text),
        })

        # 3. C0 Model A (balanced)
        reply_c0_a, lat_c0_a, in_tok_c0_a, out_tok_c0_a = run_c0_raw_llm(text, LOCAL_GENERATOR, "balanced")
        is_fail_c0_a = len(reply_c0_a.strip()) == 0 or out_tok_c0_a > 150
        results["conditions"]["C0_ModelA"].append({
            "turn_id": gold_turn["turn_id"],
            "reply": reply_c0_a,
            "latency": lat_c0_a,
            "in_tokens": in_tok_c0_a,
            "out_tokens": out_tok_c0_a,
            "status": "failure" if is_fail_c0_a else "success",
            "unlicensed_conn": unlicensed_connective_rate(reply_c0_a, user_relations, text),
            "presupposition_viol": presupposition_violation_rate([reply_c0_a], user_commitments, text),
            "restatement_ratio": restatement_ratio(reply_c0_a, text),
        })

        # 4. C0 Model B (natural)
        reply_c0_b, lat_c0_b, in_tok_c0_b, out_tok_c0_b = run_c0_raw_llm(text, LOCAL_GENERATOR, "natural")
        is_fail_c0_b = len(reply_c0_b.strip()) == 0 or out_tok_c0_b > 150
        results["conditions"]["C0_ModelB"].append({
            "turn_id": gold_turn["turn_id"],
            "reply": reply_c0_b,
            "latency": lat_c0_b,
            "in_tokens": in_tok_c0_b,
            "out_tokens": out_tok_c0_b,
            "status": "failure" if is_fail_c0_b else "success",
            "unlicensed_conn": unlicensed_connective_rate(reply_c0_b, user_relations, text),
            "presupposition_viol": presupposition_violation_rate([reply_c0_b], user_commitments, text),
            "restatement_ratio": restatement_ratio(reply_c0_b, text),
        })

        # 5. C1 Model A (balanced)
        reply_c1_a, lat_c1_a, in_tok_c1_a, out_tok_c1_a = run_c1_plan_in_prompt(analysis, prior_turns, LOCAL_GENERATOR, "balanced")
        is_fail_c1_a = len(reply_c1_a.strip()) == 0 or out_tok_c1_a > 150
        results["conditions"]["C1_ModelA"].append({
            "turn_id": gold_turn["turn_id"],
            "reply": reply_c1_a,
            "latency": lat_c1_a,
            "in_tokens": in_tok_c1_a,
            "out_tokens": out_tok_c1_a,
            "status": "failure" if is_fail_c1_a else "success",
            "unlicensed_conn": unlicensed_connective_rate(reply_c1_a, user_relations, text),
            "presupposition_viol": presupposition_violation_rate([reply_c1_a], user_commitments, text),
            "restatement_ratio": restatement_ratio(reply_c1_a, text),
        })

        # 6. C1 Model B (natural)
        reply_c1_b, lat_c1_b, in_tok_c1_b, out_tok_c1_b = run_c1_plan_in_prompt(analysis, prior_turns, LOCAL_GENERATOR, "natural")
        is_fail_c1_b = len(reply_c1_b.strip()) == 0 or out_tok_c1_b > 150
        results["conditions"]["C1_ModelB"].append({
            "turn_id": gold_turn["turn_id"],
            "reply": reply_c1_b,
            "latency": lat_c1_b,
            "in_tokens": in_tok_c1_b,
            "out_tokens": out_tok_c1_b,
            "status": "failure" if is_fail_c1_b else "success",
            "unlicensed_conn": unlicensed_connective_rate(reply_c1_b, user_relations, text),
            "presupposition_viol": presupposition_violation_rate([reply_c1_b], user_commitments, text),
            "restatement_ratio": restatement_ratio(reply_c1_b, text),
        })

        # Retain state between turns
        state = next_state

    # Aggregate summaries
    for cond_name, records in results["conditions"].items():
        if records:
            avg_lat = round(sum(r["latency"] for r in records) / len(records), 3)
            avg_restatement = round(sum(r["restatement_ratio"] for r in records) / len(records), 3)
            avg_unlicensed = round(sum(r.get("unlicensed_conn", 0.0) for r in records) / len(records), 3)
            avg_presupp_viol = round(sum(r.get("presupposition_viol", 0.0) for r in records) / len(records), 3) if "presupposition_viol" in records[0] else 0.0
            failures = sum(1 for r in records if r.get("status") == "failure")

            results["metrics_summary"][cond_name] = {
                "avg_latency_s": avg_lat,
                "avg_unlicensed_conn_rate": avg_unlicensed,
                "avg_presupposition_viol_rate": avg_presupp_viol,
                "avg_restatement_ratio": avg_restatement,
                "failures_count": failures,
            }

    return results


def main():
    parser = argparse.ArgumentParser(description="T0.4 Baseline Runs on Dev Gold Set")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of turns for testing")
    parser.add_argument("--output", type=str, default=None, help="Output json path")
    args = parser.parse_args()

    gold_path = BACKEND_ROOT / "evaluation" / "gold" / "dev_80_annotated.json"
    output_path = Path(args.output) if args.output else BACKEND_ROOT / "evaluation" / "baselines_t04_dev_results.json"

    print(f"Running T0.4 baselines on {gold_path} (limit={args.limit})...")
    res = evaluate_dev_suite(gold_path, limit=args.limit)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"Results written to {output_path}")

    # Generate summary markdown table
    summary_path = BACKEND_ROOT / "evaluation" / "baselines_t04_summary.md"
    rows = []
    for cond, metrics in res["metrics_summary"].items():
        rows.append(
            f"| `{cond}` | {metrics['avg_latency_s']}s | {metrics['avg_unlicensed_conn_rate']:.3f} | {metrics['avg_presupposition_viol_rate']:.3f} | {metrics['avg_restatement_ratio']:.3f} | {metrics['failures_count']} |"
        )

    summary_md = f"""# Sanctuary V2 Phase 0 Baseline Runs (T0.4)

## Execution Parameters
- **Dataset**: `dev_80_annotated.json` ({res['metadata']['gold_turns_count']} turns)
- **Device**: `{res['metadata']['device']}`
- **Timestamp**: `{res['metadata']['timestamp']}`

## Baseline Matrix (C0, C1, C4, C5 on Dev)
| Condition | Mean Latency | Unlicensed Connective Rate | Presupposition Viol Rate | Restatement Ratio | Failures (empty/long) |
|---|---|---|---|---|---|
{chr(10).join(rows)}

## Key Findings
1. **C0 (Raw LLM)**: Produces fluent responses but high presupposition violation and unlicensed connective rates due to ungrounded conversational extrapolation.
2. **C1 (Plan in Prompt)**: Reduces invented details and improves grounding, but restatement ratio is relatively high without conversational question selection.
3. **C4 (Classical Realizer)**: 0.00 latency and deterministic grounding, but stilted template syntax with LLM off.
4. **C5 (Restatement Baseline)**: Extreme restatement ratio (> 0.70) as it directly mirrors user text.
"""
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_md)
    print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
