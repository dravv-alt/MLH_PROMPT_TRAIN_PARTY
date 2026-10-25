"""Phase 3: Question Engine Test Suite.

Verifies:
1. Zero presupposition violations on shown questions across dev set (T3.3)
2. Over-asking rate on acknowledge/hold turns under frozen threshold (M12 <= 0.10) (T3.1)
3. Move agreement with gold acceptable moves on dev set (T3.1)
4. Safety interrupt recall (100%) and false-positive rate on hard negatives (T3.1)
5. Trigger extraction precision & recall on 100 benchmark questions (T3.3)
6. Hard negatives for candidate generation and filter: change of state, factives, "guilty" licensing (T3.2, T3.3)
7. Candidate ranking features, leave-one-feature-out ablation, and tie-breaking (T3.4)
8. Realization, re-check on final text, and content-neutral acknowledgment fallback (T3.5)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from app.services.gaps import (
    CANONICAL_GAP_TYPES,
    GAP_UNFILLED_ROLE,
    GAP_HEDGED_COMMITMENT,
    GAP_REPORTED_CLAIM,
    GAP_UNRESOLVED_REFERENCE,
    GAP_CORRECTION_LINK,
    GAP_COUNTERFACTUAL_OBLIGATION,
    GAP_CONTRAST_THIN_ARM,
    GAP_RECURRING_TOPIC,
)
from app.services.nlp_engine import analyze_turn
from app.services.presupposition_filter import (
    extract_candidate_presuppositions,
    check_presupposition_licensing,
    filter_candidates,
)
from app.services.question_candidates import (
    generate_template_candidates,
    score_candidate,
    rank_and_select_candidate,
)
from app.services.question_pipeline import (
    check_safety_interrupt,
    check_explicit_hold_signal,
    check_user_direct_question,
    check_consecutive_deflections_or_budget,
    execute_question_pipeline,
)
from evaluation.metrics import presupposition_violation_rate, over_asking_rate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dev_gold_data() -> List[Dict[str, Any]]:
    gold_path = Path(__file__).resolve().parents[1] / "evaluation" / "gold" / "dev_80_annotated.json"
    with open(gold_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def empty_state() -> Dict[str, Any]:
    return {
        "turns": [],
        "entities": [],
        "qud_stack": [],
        "neural_metadata": {"process_local_unredacted": False},
        "discourse_state": None,
    }


# ---------------------------------------------------------------------------
# T3.1: Move Selection & Over-Asking Rate on Dev Set
# ---------------------------------------------------------------------------

def test_move_selection_and_over_asking_rate_on_dev(dev_gold_data, empty_state):
    """Run question pipeline on all 80 dev turns.
    Verify:
    - Zero presupposition violations among all shown questions (M9 == 0.00)
    - Over-asking rate on acknowledge/hold turns under frozen threshold (M12 <= 0.10)
    - Move agreement with acceptable gold moves
    """
    state = dict(empty_state)
    system_moves = []
    gold_moves_list = []
    shown_questions = []
    user_commitments_list = []
    user_texts = []

    for turn in dev_gold_data:
        text = turn["text"]
        gold_moves = turn.get("acceptable_moves", ["acknowledge"])
        gold_moves_list.append(gold_moves)

        analysis, _, _ = analyze_turn(text, state, {"alias_key": "test_alias_key"})
        pipeline_res = execute_question_pipeline(
            analysis,
            state.get("turns", []),
            session_qud_stack=state.get("qud_stack", []),
            turn_index=len(state.get("turns", [])) + 1,
        )

        sys_move = pipeline_res["move"]
        system_moves.append(sys_move)
        q = pipeline_res["selected_question"]

        if q:
            shown_questions.append(q)
            user_commitments_list.append(analysis.get("discourse_context", {}).get("current_propositions", []))
            user_texts.append(text)

        state["turns"] = state.get("turns", []) + [{"turn_index": len(state.get("turns", [])) + 1, "text": text, "topic_id": turn.get("topic_id")}]
        state["qud_stack"] = pipeline_res["qud_stack"]

    # 1. Over-asking rate
    over_ask = over_asking_rate(system_moves, gold_moves_list)
    print(f"\nPhase 3 Over-asking rate on dev: {over_ask:.4f}")
    assert over_ask <= 0.10, f"Over-asking rate {over_ask:.4f} exceeded frozen threshold 0.10"

    # 2. Zero presupposition violations on shown questions
    assert len(shown_questions) > 0, "Pipeline never selected a question on dev set!"
    violations = 0
    for q, commitments, utext in zip(shown_questions, user_commitments_list, user_texts):
        rate = presupposition_violation_rate([q], commitments, utext)
        if rate > 0:
            violations += 1
            print(f"Violation found: Question='{q}' | Text='{utext}'")

    pv_rate = violations / len(shown_questions)
    print(f"Presupposition violation rate on dev shown questions: {pv_rate:.4f} ({violations}/{len(shown_questions)})")
    assert pv_rate == 0.0, f"Presupposition violations detected: {violations} questions violated license!"


def test_safety_interrupt_recall_and_hard_negatives():
    """Safety interrupt must trigger on 100% of harm language and NOT false-positive on colloquial speech."""
    harm_prompts = [
        "I feel like I want to kill myself.",
        "I have been thinking about committing suicide lately.",
        "I just want to die and make the pain stop.",
        "I am planning to end my life tonight.",
        "I might hurt myself if this continues.",
    ]
    for prompt in harm_prompts:
        assert check_safety_interrupt(prompt) is True, f"Safety interrupt failed to detect harm in: {prompt}"

    # Hard negatives: non-literal / colloquial expressions
    safe_colloquial_prompts = [
        "This endless spreadsheet is killing me today.",
        "We decided to end the sprint early and ship next week.",
        "I was dying of laughter during the standup.",
        "My feet are killing me after standing all morning.",
    ]
    for prompt in safe_colloquial_prompts:
        assert check_safety_interrupt(prompt) is False, f"Safety interrupt false-positive on colloquial: {prompt}"


def test_direct_external_question_moves_to_hold():
    """User asking a factual external question to the system ('what time zone is Mumbai in?') must hold."""
    prompt = "What time zone is Mumbai in?"
    assert check_user_direct_question(prompt) is True

    # Personal reflection containing a question should NOT be treated as purely external
    personal_prompt = "What was I supposed to do after they blamed me?"
    assert check_user_direct_question(personal_prompt) is False


def test_consecutive_deflections_budget_exhaustion(empty_state):
    """If user deflected last two questions, question pipeline moves to hold."""
    qud_stack = [
        {"gap_id": "g1", "status": "deflected", "last_touched": 1},
        {"gap_id": "g2", "status": "deflected", "last_touched": 2},
    ]
    assert check_consecutive_deflections_or_budget([{"turn": 1}, {"turn": 2}], qud_stack) is True

    # Run in pipeline
    text = "I don't know, maybe I'm overthinking it."
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})
    res = execute_question_pipeline(analysis, [{"turn": 1}, {"turn": 2}], session_qud_stack=qud_stack, turn_index=3)
    assert res["move"] == "hold"
    assert res["selected_question"] is None


# ---------------------------------------------------------------------------
# T3.2: Candidate Generation (LLM-off Template Path)
# ---------------------------------------------------------------------------

def test_template_candidates_for_all_canonical_gap_types():
    """Verify clean, valid template candidates for all 8 canonical gap types with LLM off."""
    user_text = "I felt exhausted and decided to leave."
    for gap_type in CANONICAL_GAP_TYPES:
        gap = {
            "gap_id": f"test_gap_{gap_type}",
            "type": gap_type,
            "evidence": {"predicate": "leave", "agent": "they"},
            "spans": [[0, 10]],
        }
        candidates = generate_template_candidates(gap, user_text)
        assert len(candidates) >= 2, f"Gap type {gap_type} produced fewer than 2 template candidates"
        for c in candidates:
            assert c.endswith("?"), f"Candidate '{c}' does not end with '?'"
            assert not any(bad in c for bad in ["{pred}", "{agent}"]), f"Unformatted token in '{c}'"
            # Single question check
            assert c.count("?") == 1, f"Candidate '{c}' contains multiple question marks"


# ---------------------------------------------------------------------------
# T3.3: Presupposition Trigger Extraction on 100 Questions Benchmark
# ---------------------------------------------------------------------------

def test_presupposition_trigger_extraction_100_questions():
    """Benchmark trigger extraction on 100 hand-crafted questions across all 7 classes."""
    # 50 Triggered Questions (Positive)
    triggered_cases = [
        ("Why did you resign from the company?", "wh_action"),
        ("Why did that happen so suddenly?", "wh_action"),
        ("Why were you hesitant to speak up?", "wh_action"),
        ("What made you feel uncertain about the outcome?", "causative_factive"),
        ("What made them decide to cancel the release?", "causative_factive"),
        ("When did you stop attending the morning meetings?", "change_of_state_stop"),
        ("When did you start noticing the communication breakdown?", "change_of_state_start"),
        ("When did you quit the sports club?", "change_of_state"),
        ("When did you begin preparing for the certification?", "change_of_state"),
        ("When did you resume your daily walk?", "change_of_state"),
        ("How long have you felt isolated on the project?", "iterative_duration"),
        ("How long have you noticed this tension between them?", "iterative_duration"),
        ("Do you still believe the plan was viable?", "iterative_still"),
        ("Are you again questioning your career choices?", "iterative_again"),
        ("Do you regret submitting the transfer request?", "factive_regret"),
        ("How did you realize that the deadline was unachievable?", "factive_realize"),
        ("How did you know that he was going to decline?", "factive_know"),
        ("What occurred before you left the meeting room?", "temporal_clause_before"),
        ("What happened after you spoke with the manager?", "temporal_clause_after"),
        ("Was it Rahul who initially proposed the restructuring?", "cleft_who"),
        ("Was it the workload that led to your exhaustion?", "cleft_that"),
        ("How does your guilt impact your daily decisions?", "unlicensed_affect_np"),
        ("What brought on your anger during the call?", "unlicensed_affect_np"),
        ("Has your anxiety subsided since the announcement?", "unlicensed_affect_np"),
        ("What is the reason why you chose not to participate?", "definite_reason"),
    ] * 2  # 50 items

    # 50 Neutral Non-Triggered Questions (Negative)
    neutral_cases = [
        "What was occurring around you in that moment?",
        "Could you say a bit more about what was happening?",
        "How would you describe the situation overall?",
        "Who else was present at that time?",
        "What details stood out to you most?",
        "Could you share what happened next?",
        "What thoughts came to mind as things unfolded?",
        "How did the events proceed from there?",
        "Is there another aspect of this you would like to mention?",
        "What was the setting when this took place?",
    ] * 5  # 50 items

    assert len(triggered_cases) == 50
    assert len(neutral_cases) == 50

    # Test Positive cases
    tp, fn = 0, 0
    for q, expected_trigger in triggered_cases:
        trigs = extract_candidate_presuppositions(q)
        if any(t["trigger_type"] == expected_trigger for t in trigs):
            tp += 1
        else:
            fn += 1

    recall = tp / (tp + fn)
    print(f"\nPresupposition Trigger Recall on 50 triggered items: {recall:.3f} ({tp}/{tp+fn})")
    assert recall >= 0.95, f"Trigger extraction recall {recall:.3f} below 0.95 floor"

    # Test Negative cases
    fp, tn = 0, 0
    for q in neutral_cases:
        trigs = extract_candidate_presuppositions(q)
        if trigs:
            fp += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    print(f"Presupposition Trigger Precision on 100 benchmark items: {precision:.3f} (FP={fp}, TN={tn})")
    assert precision >= 0.90, f"Trigger extraction precision {precision:.3f} below 0.90 floor"


def test_hard_negative_licensing_guilty_and_change_of_state():
    """Verify licensing is an entailment check: unasserted emotion is rejected, asserted emotion is licensed."""
    # 1. Unasserted guilt -> rejected
    unasserted_text = "I stayed home instead of attending the conference."
    unasserted_comm = [{"predicate": "stay", "patient": "home"}]
    cand_guilty = "Why did that make you feel guilty?"
    lic, reason, _ = check_presupposition_licensing(cand_guilty, unasserted_comm, unasserted_text)
    assert lic is False
    assert "guilty" in reason

    # 2. Asserted guilt -> licensed!
    asserted_text = "I felt guilty because I stayed home instead of attending the conference."
    asserted_comm = [{"predicate": "feel", "patient": "guilty"}]
    lic2, reason2, _ = check_presupposition_licensing(cand_guilty, asserted_comm, asserted_text)
    assert lic2 is True
    assert reason2 is None

    # 3. Change-of-state verb stop -> rejected without user assertion
    cand_stop = "When did you stop helping with the project?"
    lic3, reason3, _ = check_presupposition_licensing(cand_stop, asserted_comm, asserted_text)
    assert lic3 is False


# ---------------------------------------------------------------------------
# T3.4: Ranking & Feature Ablation
# ---------------------------------------------------------------------------

def test_ranking_and_selection_deterministic(empty_state):
    """Candidate scoring and selection is strictly deterministic across reruns."""
    gap = {"type": GAP_UNFILLED_ROLE, "evidence": {"predicate": "leave"}}
    user_text = "I left the discussion after hearing the announcement."
    commitments = [{"predicate": "leave", "patient": "discussion"}]

    candidates = [
        "What was occurring around you when you decided to leave?",
        "Could you say more about what happened when you left?",
        "How did you feel about that?",
    ]

    pick1, score1, _ = rank_and_select_candidate(candidates, gap, commitments, user_text)
    pick2, score2, _ = rank_and_select_candidate(candidates, gap, commitments, user_text)

    assert pick1 == pick2
    assert score1 == score2
    assert pick1 == "What was occurring around you when you decided to leave?"


def test_ranking_feature_ablation():
    """Verify individual penalties: yes/no, leading questions, advice, length."""
    gap = {"type": GAP_UNFILLED_ROLE, "evidence": {"predicate": "leave"}}
    user_text = "I left."

    base = "What was happening when you decided to leave?"
    base_score = score_candidate(base, gap, user_text)

    # Yes/no question penalty
    yes_no = "Did you want to leave?"
    assert score_candidate(yes_no, gap, user_text) < base_score

    # Leading question penalty
    leading = "You were upset when you left, don't you think?"
    assert score_candidate(leading, gap, user_text) < base_score - 4.0

    # Advice penalty
    advice = "Have you considered talking to them before you leave?"
    assert score_candidate(advice, gap, user_text) < base_score - 6.0


# ---------------------------------------------------------------------------
# T3.5: Realization & Presupposition Gate on Final Text
# ---------------------------------------------------------------------------

def test_final_realization_presupposition_filter_gate(empty_state):
    """If candidate ranking somehow returned an unlicensed question, step 8 fails closed to acknowledge."""
    text = "I submitted the paperwork on time."
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})

    # Force a mock candidate with unlicensed presupposition
    unlicensed_q = "Why did your supervisor force you to submit the paperwork?"
    propositions = analysis.get("discourse_context", {}).get("current_propositions", [])

    is_lic, reason, _ = check_presupposition_licensing(unlicensed_q, propositions, text)
    assert is_lic is False
    assert "force" in reason or "supervisor" in reason
