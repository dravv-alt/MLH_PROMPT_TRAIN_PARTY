"""Smallest Demonstrable Slice Tests:
Verifies T2.1, T2.3, T3.2, T3.3, and T3.4 running end-to-end with template candidates and LLM off.
"""
import pytest
from app.services.nlp_engine import analyze_turn
from app.services.question_pipeline import execute_question_pipeline
from app.services.qud_stack import STATUS_OPEN


def test_smallest_slice_end_to_end_experiential_gap():
    """Verify end-to-end pipeline on dev turn with experiential gap (tiredness)."""
    text = "I got the internship today, but honestly I just feel tired."
    analysis, next_state, _ = analyze_turn(text, config={"alias_key": "slice-test-key"})

    pipeline_result = execute_question_pipeline(analysis, turn_index=1, mode="template_llm_off")

    assert pipeline_result["move"] in {"ask", "clarify"}
    assert pipeline_result["selected_question"] is not None
    assert "?" in pipeline_result["selected_question"]

    # Verify structural gaps
    assert len(pipeline_result["gaps"]) >= 1
    # Verify QUD stack populated
    assert len(pipeline_result["qud_stack"]) >= 1
    assert any(q["status"] == STATUS_OPEN for q in pipeline_result["qud_stack"])

    # Verify question trace (Task T5.1 preview)
    trace = pipeline_result["question_trace"]
    assert "gap_id" in trace
    assert "spans" in trace
    assert "human_reason" in trace
    assert "score" in trace
    assert trace["generation_mode"] == "template_llm_off"


def test_smallest_slice_hold_on_explicit_signal():
    """Verify that when a user asks not to be questioned, move is hold and question is None."""
    text = "I just needed to say all that out loud, please don't ask me any questions about it."
    analysis, _, _ = analyze_turn(text, config={"alias_key": "slice-test-key"})

    pipeline_result = execute_question_pipeline(analysis, turn_index=1)
    assert pipeline_result["move"] == "hold"
    assert pipeline_result["selected_question"] is None
    assert "brief or user explicitly requested" in pipeline_result["question_trace"]["reason"]


def test_smallest_slice_hold_on_short_turn():
    """Verify that on very short turns ('ok'), move is hold and question is None."""
    text = "ok"
    analysis, _, _ = analyze_turn(text, config={"alias_key": "slice-test-key"})

    pipeline_result = execute_question_pipeline(analysis, turn_index=1)
    assert pipeline_result["move"] == "hold"
    assert pipeline_result["selected_question"] is None


def test_smallest_slice_safety_interrupt():
    """Verify that language indicating self-harm triggers safety interrupt immediately."""
    text = "I feel like I want to hurt myself tonight."
    analysis, _, _ = analyze_turn(text, config={"alias_key": "slice-test-key"})

    pipeline_result = execute_question_pipeline(analysis, turn_index=1)
    assert pipeline_result["move"] == "safety_interrupt"
    assert pipeline_result["selected_question"] is None
    assert pipeline_result["diagnostics_status"] == "safety_override"


def test_smallest_slice_determinism():
    """Verify that running identical input produces identical questions and scores."""
    text = "I left the team meeting because no one was listening."
    analysis1, _, _ = analyze_turn(text, config={"alias_key": "slice-test-key"})
    analysis2, _, _ = analyze_turn(text, config={"alias_key": "slice-test-key"})

    res1 = execute_question_pipeline(analysis1, turn_index=1)
    res2 = execute_question_pipeline(analysis2, turn_index=1)

    assert res1["move"] == res2["move"]
    assert res1["selected_question"] == res2["selected_question"]
    assert res1["question_trace"]["score"] == res2["question_trace"]["score"]
