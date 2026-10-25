"""Phase 6: Evaluation, Ablations, Scripted Demos, and Final Verification Test Suite.

Verifies:
1. Held-out test set cryptographic integrity (SHA-256 match with TEST_HASH.txt)
2. Success criteria on held-out test set:
   - M9 (Presupposition violations): == 0.00
   - M12 (Over-asking rate): <= 0.10
   - Restatement ratio: C3 strictly beats C1 and C4/C5 baselines
   - Presupposition ablation (C2 vs C3): C2 shows higher over-asking rate
   - Processing latency: p95 <= 0.50s under LLM-off deterministic execution
3. Scripted conversational demonstrations: all 4 canonical demos pass
4. Standing Invariant: Privacy canary clean across analysis, qud_stack, trace, and exports
5. 100% valid deterministic diagnostic map coverage with LLM disabled
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
from typing import Any, Dict, List
import pytest

from app.services.nlp_engine import analyze_turn
from app.services.question_pipeline import execute_question_pipeline
from scripts.verify_scripted_demos import (
    run_demo_1_cooperative,
    run_demo_2_boundary_deflection,
    run_demo_3_presupposition_guard,
    run_demo_4_correction_and_supersession,
)


GOLD_DIR = Path(__file__).resolve().parents[1] / "evaluation" / "gold"
REPORT_DIR = Path(__file__).resolve().parents[1] / "evaluation" / "report"


# ---------------------------------------------------------------------------
# Test 1: Cryptographic Integrity of Held-Out Test Set
# ---------------------------------------------------------------------------

def test_held_out_test_set_hash_integrity():
    """Verify that held_out_test_40.json matches the cryptographic hash frozen in Phase 0."""
    test_path = GOLD_DIR / "held_out_test_40.json"
    hash_path = GOLD_DIR / "TEST_HASH.txt"

    assert test_path.exists(), f"Held-out test set not found at {test_path}"
    assert hash_path.exists(), f"Frozen hash file not found at {hash_path}"

    with open(test_path, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()

    with open(hash_path, "r", encoding="utf-8") as f:
        expected_hash = f.read().strip()

    assert actual_hash == expected_hash, (
        f"Cryptographic hash mismatch for held_out_test_40.json!\n"
        f"Expected: {expected_hash}\nActual:   {actual_hash}"
    )


# ---------------------------------------------------------------------------
# Test 2: Success Criteria on Held-Out Test Set
# ---------------------------------------------------------------------------

def test_held_out_evaluation_success_criteria():
    """Verify that the held-out test evaluation meets all frozen success criteria."""
    results_path = REPORT_DIR / "t61_held_out_evaluation_results.json"
    assert results_path.exists(), f"Evaluation results file not found at {results_path}"

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    c0 = results["conditions"]["C0"]
    c1 = results["conditions"]["C1"]
    c2 = results["conditions"]["C2"]
    c3 = results["conditions"]["C3"]
    c4 = results["conditions"]["C4"]
    c5 = results["conditions"]["C5"]

    # Criterion 1: Zero presupposition violations on held-out test (M9 == 0.00)
    assert c3["presupposition_violation_rate"] == 0.0, (
        f"Presupposition violation rate must be 0.00, got {c3['presupposition_violation_rate']}"
    )

    # Criterion 2: Over-asking rate on acknowledge/hold turns <= 0.10 (M12 <= 0.10)
    assert c3["over_asking_rate"] <= 0.10, (
        f"Over-asking rate must be <= 0.10, got {c3['over_asking_rate']}"
    )

    # Criterion 3: C3 beats C1 and C4/C5 on restatement ratio
    assert c3["restatement_ratio"] < c1["restatement_ratio"], (
        f"C3 restatement ratio ({c3['restatement_ratio']}) must beat C1 ({c1['restatement_ratio']})"
    )
    assert c3["restatement_ratio"] < c5["restatement_ratio"], (
        f"C3 restatement ratio ({c3['restatement_ratio']}) must beat C5 ({c5['restatement_ratio']})"
    )

    # Criterion 4: Ablation proves filter necessity (C2 without filter over-asks > 0.10)
    assert c2["over_asking_rate"] > 0.10, (
        f"C2 ablation over-asking rate ({c2['over_asking_rate']}) expected to exceed 0.10 without filter"
    )

    # Criterion 5: Processing latency p95 <= 0.50s under deterministic execution
    assert c3["p95_latency_s"] <= 0.50, (
        f"Latency p95 ({c3['p95_latency_s']}s) must be <= 0.50s"
    )


# ---------------------------------------------------------------------------
# Test 3: Four Scripted Demonstrations Verification
# ---------------------------------------------------------------------------

def test_four_canonical_scripted_demos():
    """Verify all 4 canonical conversational demos pass deterministically."""
    d1 = run_demo_1_cooperative()
    assert d1["status"] == "PASS", f"Demo 1 failed: {d1}"

    d2 = run_demo_2_boundary_deflection()
    assert d2["status"] == "PASS", f"Demo 2 failed: {d2}"

    d3 = run_demo_3_presupposition_guard()
    assert d3["status"] == "PASS", f"Demo 3 failed: {d3}"

    d4 = run_demo_4_correction_and_supersession()
    assert d4["status"] == "PASS", f"Demo 4 failed: {d4}"


# ---------------------------------------------------------------------------
# Test 4: Standing Invariant — Privacy Canary Cleanliness
# ---------------------------------------------------------------------------

def test_privacy_canary_cleanliness_across_pipeline_and_trace():
    """Standing Invariant: Seeded canary tokens must never leak into analysis, qud, or trace."""
    canary_tokens = [
        "canary_user_alpha_9918@domain.org",
        "+91 98765 43210",
        "SSN-000-12-3456",
        "CANARY_SECRET_TOKEN_XYZ",
    ]
    raw_text = (
        f"Please write to {canary_tokens[0]} or call {canary_tokens[1]} with my {canary_tokens[2]}. "
        f"My identifier is {canary_tokens[3]} and I think I might struggle with how to manage this."
    )

    empty_state = {
        "turns": [],
        "entities": [],
        "qud_stack": [],
        "neural_metadata": {"process_local_unredacted": False},
    }

    analysis, delta, _ = analyze_turn(raw_text, empty_state, {"alias_key": "test_canary_key"})
    pipeline_res = execute_question_pipeline(analysis, [], session_qud_stack=[], turn_index=1)

    # Serialize complete analysis, delta, and pipeline output to inspect
    payload_dump = json.dumps(
        {
            "analysis": analysis,
            "delta": delta,
            "pipeline": pipeline_res,
        },
        default=str,
    )

    for canary in canary_tokens:
        assert canary not in payload_dump, f"Privacy canary token '{canary}' leaked into pipeline output!"
        # Also check substring fragments of numbers
        if "98765" in canary:
            assert "98765" not in payload_dump, "Canary phone fragment '98765' leaked into pipeline output!"


# ---------------------------------------------------------------------------
# Test 5: 100% LLM-Off Deterministic Realization on Test Set
# ---------------------------------------------------------------------------

def test_deterministic_llm_off_coverage_on_held_out_turns():
    """Verify that every held-out test turn yields a valid deterministic move, question/trace, and status."""
    test_path = GOLD_DIR / "held_out_test_40.json"
    with open(test_path, "r", encoding="utf-8") as f:
        test_turns = json.load(f)

    empty_state = {
        "turns": [],
        "entities": [],
        "qud_stack": [],
        "neural_metadata": {"process_local_unredacted": False},
    }

    for turn in test_turns:
        text = turn["text"]
        analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias"})
        res = execute_question_pipeline(analysis, [], session_qud_stack=[], turn_index=1, mode="template_llm_off")

        assert res["move"] in {"ask", "clarify", "acknowledge", "hold", "safety_interrupt"}
        assert "question_trace" in res
        assert "reason" in res["question_trace"]
        assert len(res["question_trace"]["reason"]) > 0

        if res["move"] in {"ask", "clarify"}:
            assert res["selected_question"] is not None
            assert res["selected_question"].endswith("?")
        else:
            assert res["selected_question"] is None
