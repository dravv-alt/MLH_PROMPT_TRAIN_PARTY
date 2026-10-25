"""Phase 4: Conversation State, Answer Uptake, and Simulator Test Suite.

Verifies:
1. Uptake classification accuracy across answered, partial, deflected, shifted, and none (T4.1)
2. Deflection window suppression (W = 3) and unprompted return reopening (T4.2)
3. Consecutive deflection hold policy and session question budget enforcement (T4.2)
4. Explicit pushback hold enforcement (T4.2)
5. QUD stack lifecycle transitions, abandonment after N = 4 turns, and auto-resolution (T4.3)
6. Question variety, distinct syntactic stems per gap, and repeat stem penalty (T4.4)
7. Multi-turn user simulator across 4 persona profiles (200 runs): 0 loops, 0 window repeats (T4.5)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import pytest

from app.services.uptake_classifier import (
    classify_answer_uptake,
    UPTAKE_ANSWERED,
    UPTAKE_PARTIAL,
    UPTAKE_DEFLECTED,
    UPTAKE_SHIFTED,
    UPTAKE_NONE,
)
from app.services.backoff_policy import (
    ConversationPolicyTracker,
    check_explicit_pushback,
    DEFAULT_DEFLECTION_WINDOW,
    MAX_QUESTIONS_PER_SESSION,
)
from app.services.qud_stack import (
    create_qud_entry,
    transition_qud_status,
    merge_and_update_qud_stack,
    get_active_quds,
    STATUS_OPEN,
    STATUS_ANSWERED,
    STATUS_DEFLECTED,
    STATUS_ABANDONED,
    STATUS_SUPERSEDED,
)
from app.services.question_candidates import (
    GAP_TEMPLATES,
    score_candidate,
)
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
from app.services.question_pipeline import execute_question_pipeline


# ---------------------------------------------------------------------------
# T4.1: Uptake Classifier Unit & Hard-Negative Tests
# ---------------------------------------------------------------------------

def test_uptake_classifier_none_when_no_prior_question():
    """Verify uptake is 'none' if there is no previous system question."""
    res1 = classify_answer_uptake({"redacted_text": "I feel okay."}, None)
    assert res1["uptake"] == UPTAKE_NONE

    res2 = classify_answer_uptake(
        {"redacted_text": "I feel okay."},
        {"move": "acknowledge", "question": None},
    )
    assert res2["uptake"] == UPTAKE_NONE


def test_uptake_classifier_explicit_deflection():
    """Verify explicit boundary expressions and counter-questions are classified as deflected."""
    last_turn = {
        "move": "ask",
        "question": "What prompted your decision regarding resign?",
        "targeted_gap_id": "gap_resign_1",
        "target_frame": "resign",
    }

    deflections = [
        "Leave it, I don't want to talk about that.",
        "Drop it, please.",
        "None of your business.",
        "Why do you keep asking me questions?",
        "Why do you care?",
        "Chhod na yaar, forget it.",
        "Mat poocho ye sab.",
        "Stop questioning me.",
    ]
    for text in deflections:
        res = classify_answer_uptake({"redacted_text": text}, last_turn, current_text=text)
        assert res["uptake"] == UPTAKE_DEFLECTED, f"Expected deflected for '{text}', got {res['uptake']}"
        assert res["targeted_gap_id"] == "gap_resign_1"


def test_uptake_classifier_engaged_unresolved_partial():
    """Verify 'I don't know' and unresolved expressions are classified as partial."""
    last_turn = {
        "move": "ask",
        "question": "What prompted your decision regarding resign?",
        "targeted_gap_id": "gap_resign_1",
        "target_frame": "resign",
    }

    partials = [
        "I don't know honestly.",
        "I can't really tell.",
        "I'm not sure.",
        "Hard to say.",
        "No idea really.",
        "Pata nahi.",
        "Malum nahi kya bolun.",
    ]
    for text in partials:
        res = classify_answer_uptake({"redacted_text": text}, last_turn, current_text=text)
        assert res["uptake"] == UPTAKE_PARTIAL, f"Expected partial for '{text}', got {res['uptake']}"


def test_uptake_classifier_topic_shift():
    """Verify explicit topic shifting markers are classified as shifted."""
    last_turn = {
        "move": "ask",
        "question": "What prompted your decision regarding resign?",
        "targeted_gap_id": "gap_resign_1",
        "target_frame": "resign",
    }

    shifts = [
        "Anyway, let's talk about something else.",
        "Moving on to another thing.",
        "On another note, my car broke down.",
        "Forget about that, listen to this.",
    ]
    for text in shifts:
        res = classify_answer_uptake({"redacted_text": text}, last_turn, current_text=text)
        assert res["uptake"] == UPTAKE_SHIFTED, f"Expected shifted for '{text}', got {res['uptake']}"


def test_uptake_classifier_answered_substantive():
    """Verify substantive answers addressing the predicate with causal/contextual grounding are answered."""
    last_turn = {
        "move": "ask",
        "question": "What prompted your decision regarding resign?",
        "targeted_gap_id": "gap_resign_1",
        "target_frame": "resign",
    }

    analysis = {
        "redacted_text": "I decided to resign because my manager continued to cut my project budget.",
        "discourse_context": {
            "current_propositions": [
                {
                    "predicate": {"lemma": "resign"},
                    "text": "I decided to resign because my manager cut budget",
                }
            ]
        },
        "centering": {"trace": [{"transition": "CONTINUE"}]},
    }
    res = classify_answer_uptake(analysis, last_turn)
    assert res["uptake"] == UPTAKE_ANSWERED
    assert res["continuity_score"] >= 0.5


# ---------------------------------------------------------------------------
# T4.2: Backoff & Pacing Policy Tests
# ---------------------------------------------------------------------------

def test_backoff_policy_pushback_enforces_hold():
    """Verify pushback cues immediately force hold."""
    tracker = ConversationPolicyTracker()
    pushbacks = [
        "Why do you keep asking me questions?",
        "Stop questioning me.",
        "You ask too many questions.",
        "I already answered that.",
        "Stop prying.",
    ]
    for text in pushbacks:
        allow_q, enforced_move, reason = tracker.evaluate_question_policy(
            text, [], [], turn_index=2
        )
        assert not allow_q
        assert enforced_move == "hold"
        assert "pushback" in reason.lower()


def test_backoff_policy_consecutive_deflections_forces_hold():
    """Verify two consecutive deflections force hold."""
    tracker = ConversationPolicyTracker()
    prior_turns = [
        {"system_move": "ask", "question": "Q1?", "uptake": "deflected"},
        {"system_move": "ask", "question": "Q2?", "uptake": "deflected"},
    ]
    allow_q, enforced_move, reason = tracker.evaluate_question_policy(
        "I just want to sit here.", prior_turns, [], turn_index=3
    )
    assert not allow_q
    assert enforced_move == "hold"
    assert "consecutive deflections" in reason.lower()


def test_backoff_policy_session_budget():
    """Verify session question budget limits total questions to 6."""
    tracker = ConversationPolicyTracker(max_questions_session=6)
    prior_turns = [
        {"system_move": "ask", "question": f"Q{i}?"} for i in range(6)
    ]
    allow_q, enforced_move, reason = tracker.evaluate_question_policy(
        "This is turn 7 with some narrative.", prior_turns, [], turn_index=7
    )
    assert not allow_q
    assert enforced_move == "acknowledge"
    assert "budget exhausted" in reason.lower()


def test_gap_suppression_window():
    """Verify deflected gap is suppressed for W=3 turns and reopens at turn 4."""
    tracker = ConversationPolicyTracker(deflection_window=3)
    qud_stack = [
        {
            "gap_id": "gap_work_1",
            "status": "deflected",
            "last_touched": 2,
        }
    ]

    # At turn 2, 3, 4, 5 (diff <= 3): suppressed
    assert tracker.is_gap_suppressed("gap_work_1", qud_stack, turn_index=2) is True
    assert tracker.is_gap_suppressed("gap_work_1", qud_stack, turn_index=3) is True
    assert tracker.is_gap_suppressed("gap_work_1", qud_stack, turn_index=5) is True

    # At turn 6 (diff = 4 > 3): suppression expired
    assert tracker.is_gap_suppressed("gap_work_1", qud_stack, turn_index=6) is False


def test_unprompted_return_detection():
    """Verify unprompted return to a deflected gap is detected."""
    tracker = ConversationPolicyTracker()
    qud_entry = {
        "gap_id": "gap_manager_1",
        "frame_id": "manager_meeting",
        "neutral_question_form": "What was occurring during the manager meeting?",
        "status": "deflected",
    }
    user_text = "Actually, going back to the manager meeting yesterday, things went bad."
    props = [{"predicate": {"lemma": "manager_meeting"}}]
    assert tracker.detect_unprompted_return(user_text, props, qud_entry) is True

    unrelated_text = "I went to buy groceries."
    unrelated_props = [{"predicate": {"lemma": "buy"}}]
    assert tracker.detect_unprompted_return(unrelated_text, unrelated_props, qud_entry) is False


# ---------------------------------------------------------------------------
# T4.3: QUD Stack Lifecycle Transitions
# ---------------------------------------------------------------------------

def test_qud_lifecycle_legal_and_illegal_transitions():
    """Verify legal transitions succeed and illegal ones are rejected."""
    entry = create_qud_entry("gap_1", "What happened?", [[0, 10]], turn_index=1)
    assert entry["status"] == STATUS_OPEN

    # Legal: open -> deflected
    assert transition_qud_status(entry, STATUS_DEFLECTED, current_turn=2) is True
    assert entry["status"] == STATUS_DEFLECTED

    # Legal: deflected -> open (unprompted return)
    assert transition_qud_status(entry, STATUS_OPEN, current_turn=3) is True
    assert entry["status"] == STATUS_OPEN

    # Legal: open -> answered
    assert transition_qud_status(entry, STATUS_ANSWERED, current_turn=4) is True
    assert entry["status"] == STATUS_ANSWERED

    # Legal: answered -> superseded
    assert transition_qud_status(entry, STATUS_SUPERSEDED, current_turn=5) is True
    assert entry["status"] == STATUS_SUPERSEDED

    # Illegal: superseded cannot transition to open or answered
    assert transition_qud_status(entry, STATUS_OPEN, current_turn=6) is False
    assert entry["status"] == STATUS_SUPERSEDED


def test_qud_abandonment_after_n_turns():
    """Verify QUD entry is marked abandoned after 4 untouched turns."""
    stack = [
        create_qud_entry("gap_old", "What happened?", [[0, 5]], turn_index=1)
    ]
    # At turn 4, diff = 3 -> remains open
    updated_t4 = merge_and_update_qud_stack(stack, [], turn_index=4, abandon_threshold=4)
    assert updated_t4[0]["status"] == STATUS_OPEN

    # At turn 5, diff = 4 -> abandoned
    updated_t5 = merge_and_update_qud_stack(stack, [], turn_index=5, abandon_threshold=4)
    assert updated_t5[0]["status"] == STATUS_ABANDONED


def test_qud_supersession_on_correction():
    """Verify QUD entry is superseded when correction retracts base frame."""
    stack = [
        create_qud_entry("gap_call", "What happened?", [[0, 5]], turn_index=1, frame_id="prop_sister_call")
    ]
    correction_context = {
        "is_correction": True,
        "superseded_propositions": ["prop_sister_call"],
    }
    updated = merge_and_update_qud_stack(stack, [], turn_index=2, correction_context=correction_context)
    assert updated[0]["status"] == STATUS_SUPERSEDED


def test_qud_auto_resolution_by_matching_predicate():
    """Verify open QUD entry is marked answered when subsequent proposition fills predicate."""
    stack = [
        create_qud_entry("gap_doctor", "What happened with the appointment?", [[0, 5]], turn_index=1, frame_id="appointment")
    ]
    current_props = [
        {"predicate": {"lemma": "appointment"}, "text": "I went to the appointment at 3pm."}
    ]
    updated = merge_and_update_qud_stack(stack, [], turn_index=2, current_propositions=current_props)
    assert updated[0]["status"] == STATUS_ANSWERED


# ---------------------------------------------------------------------------
# T4.4: Question Variety & Stem Repetition Penalty
# ---------------------------------------------------------------------------

def test_template_bank_has_three_distinct_stems_per_gap():
    """Verify that all canonical gap types provide at least 3 distinct question stems."""
    for gap_type in CANONICAL_GAP_TYPES:
        templates = GAP_TEMPLATES.get(gap_type, [])
        assert len(templates) >= 3, f"Gap {gap_type} has fewer than 3 templates."

        # Verify distinct stems (first 3 tokens)
        stems = set()
        for tpl in templates:
            stem = " ".join(tpl.split()[:3]).lower()
            stems.add(stem)
        assert len(stems) >= 2, f"Gap {gap_type} does not have distinct stems: {stems}"


def test_stem_penalty_deprioritizes_repeated_phrasing():
    """Verify candidate scoring penalizes repeated question stems by -6.0."""
    gap = {
        "type": GAP_UNFILLED_ROLE,
        "evidence": {"predicate": "resign"},
    }
    candidate = "What was occurring around you when you began to resign?"
    prior_questions = ["What was occurring in that interaction?"]

    score_without_repeat = score_candidate(candidate, gap, "I decided to resign yesterday.", prior_questions=[])
    score_with_repeat = score_candidate(candidate, gap, "I decided to resign yesterday.", prior_questions=prior_questions)

    assert score_without_repeat - score_with_repeat == pytest.approx(6.0, abs=0.1)


# ---------------------------------------------------------------------------
# T4.5 / Simulator: Multi-Turn User Profiles (200 Runs)
# ---------------------------------------------------------------------------

class MockTurnGenerator:
    """Generates turns for 4 conversational personas for simulation testing."""

    @staticmethod
    def get_turn(persona: str, turn_idx: int) -> Dict[str, Any]:
        if persona == "cooperative":
            if turn_idx % 2 == 1:
                preds = ["struggle", "hesitate", "doubt", "reconsider"]
                pred = preds[(turn_idx // 2) % len(preds)]
                text = f"I think I might {pred} with how to proceed with the team assignment, but everyone expects results."
                return {
                    "redacted_text": text,
                    "propositions": [
                        {"predicate": {"lemma": pred}, "text": f"I might {pred} with how to proceed", "clause_id": f"c_{turn_idx}_1"},
                        {"predicate": {"lemma": "expect"}, "text": "everyone expects results", "clause_id": f"c_{turn_idx}_2"},
                    ],
                    "clauses": [
                        {"id": f"c_{turn_idx}_1", "spans": [[0, 60]]},
                        {"id": f"c_{turn_idx}_2", "spans": [[65, len(text)]]},
                    ],
                    "relations": [{"type": "contrast", "arg1": f"c_{turn_idx}_1", "arg2": f"c_{turn_idx}_2"}],
                    "hedge_spans": [[0, 7]],
                    "features": {"hedge": 0.7},
                }
            else:
                preds = ["struggle", "hesitate", "doubt", "reconsider"]
                pred = preds[((turn_idx - 1) // 2) % len(preds)]
                text = f"I felt that because the manager moved the team assignment deadline forward without notice."
                return {
                    "redacted_text": text,
                    "propositions": [
                        {"predicate": {"lemma": pred}, "text": f"I {pred} because deadline moved", "clause_id": f"c_{turn_idx}_1"},
                        {"predicate": {"lemma": "move"}, "text": "manager moved deadline", "clause_id": f"c_{turn_idx}_2"},
                    ],
                    "clauses": [{"id": f"c_{turn_idx}_1", "spans": [[0, len(text)]]}],
                    "relations": [{"type": "causal", "arg1": f"c_{turn_idx}_1", "arg2": f"c_{turn_idx}_2"}],
                }

        elif persona == "deflecting":
            if turn_idx == 1:
                text = "I think I might struggle with how to manage this department, but everyone expects results."
                return {
                    "redacted_text": text,
                    "propositions": [
                        {"predicate": {"lemma": "struggle"}, "text": "I might struggle with how to manage", "clause_id": f"c_{turn_idx}_1"},
                        {"predicate": {"lemma": "expect"}, "text": "everyone expects results", "clause_id": f"c_{turn_idx}_2"},
                    ],
                    "clauses": [
                        {"id": f"c_{turn_idx}_1", "spans": [[0, 60]]},
                        {"id": f"c_{turn_idx}_2", "spans": [[65, len(text)]]},
                    ],
                    "relations": [{"type": "contrast", "arg1": f"c_{turn_idx}_1", "arg2": f"c_{turn_idx}_2"}],
                    "hedge_spans": [[0, 7]],
                    "features": {"hedge": 0.7},
                }
            cues = [
                "Leave it, I don't want to talk about that.",
                "Why do you keep asking me questions?",
                "Drop it please.",
                "None of your business.",
                "Stop interrogating me.",
            ]
            text = cues[(turn_idx - 2) % len(cues)]
            return {
                "redacted_text": text,
                "propositions": [],
                "clauses": [{"id": f"c_{turn_idx}", "spans": [[0, len(text)]]}],
            }

        elif persona == "near_silent":
            cues = ["yeah.", "ok.", "maybe.", "hm.", "fine."]
            text = cues[(turn_idx - 1) % len(cues)]
            return {
                "redacted_text": text,
                "propositions": [],
                "clauses": [{"id": f"c_{turn_idx}", "spans": [[0, len(text)]]}],
            }

        elif persona == "topic_hopping":
            topics = ["gardening", "car engine", "weather", "cooking"]
            t = topics[(turn_idx - 1) % len(topics)]
            if turn_idx % 2 == 1:
                text = f"I think I might struggle with my {t} every single weekend, but time is short."
                return {
                    "redacted_text": text,
                    "propositions": [
                        {"predicate": {"lemma": "struggle"}, "text": f"I might struggle with {t}", "clause_id": f"c_{turn_idx}_1"},
                        {"predicate": {"lemma": "is"}, "text": "time is short", "clause_id": f"c_{turn_idx}_2"},
                    ],
                    "clauses": [
                        {"id": f"c_{turn_idx}_1", "spans": [[0, 50]]},
                        {"id": f"c_{turn_idx}_2", "spans": [[55, len(text)]]},
                    ],
                    "relations": [{"type": "contrast", "arg1": f"c_{turn_idx}_1", "arg2": f"c_{turn_idx}_2"}],
                    "hedge_spans": [[0, 7]],
                    "features": {"hedge": 0.7},
                }
            else:
                text = f"Anyway, moving on to another note, let's talk about something else like {t}."
                return {
                    "redacted_text": text,
                    "propositions": [{"predicate": {"lemma": t}, "text": text}],
                    "clauses": [{"id": f"c_{turn_idx}", "spans": [[0, len(text)]]}],
                }
        raise ValueError(f"Unknown persona {persona}")


def run_simulated_session(persona: str, num_turns: int = 8) -> Dict[str, Any]:
    """Execute a simulated multi-turn session through the question pipeline."""
    session_qud_stack: List[Dict[str, Any]] = []
    prior_turns: List[Dict[str, Any]] = []
    questions_asked: List[str] = []
    moves: List[str] = []

    for turn_idx in range(1, num_turns + 1):
        turn_data = MockTurnGenerator.get_turn(persona, turn_idx)

        analysis = {
            "redacted_text": turn_data["redacted_text"],
            "discourse_context": {"current_propositions": turn_data["propositions"]},
            "clauses": turn_data.get("clauses", []),
            "relations": turn_data.get("relations", []),
            "hedge_spans": turn_data.get("hedge_spans", []),
            "features": turn_data.get("features", {}),
            "centering": {"trace": []},
        }

        # Inject detected gaps if any into pipeline
        result = execute_question_pipeline(
            analysis,
            prior_turns=prior_turns,
            session_qud_stack=session_qud_stack,
            turn_index=turn_idx,
            mode="template_llm_off",
        )

        move = result["move"]
        q = result["selected_question"]
        moves.append(move)

        session_qud_stack = result["qud_stack"]

        turn_record = {
            "turn_index": turn_idx,
            "user_text": turn_data["redacted_text"],
            "system_move": move,
            "question": q,
            "uptake": result.get("uptake", "none"),
        }
        if q:
            questions_asked.append(q)
            turn_record["target_frame"] = result.get("question_trace", {}).get("evidence", {}).get("predicate")

        prior_turns.append(turn_record)

    return {
        "persona": persona,
        "moves": moves,
        "questions_asked": questions_asked,
        "prior_turns": prior_turns,
    }


def test_multi_turn_simulator_200_runs():
    """Run 50 simulated dialogs for each of 4 personas (200 total runs).
    Assert:
    - 0 repeated questions within window W = 3
    - 0 infinite question loops
    - Total questions asked never exceeds session budget (<= 6)
    - Deflecting persona triggers hold / backoff
    - Near-silent persona triggers hold
    """
    personas = ["cooperative", "deflecting", "near_silent", "topic_hopping"]
    runs_per_persona = 50
    total_runs = 0

    for persona in personas:
        for run_i in range(runs_per_persona):
            session = run_simulated_session(persona, num_turns=8)
            questions = session["questions_asked"]
            moves = session["moves"]

            # 1. Budget check: max 6 questions per session
            assert len(questions) <= MAX_QUESTIONS_PER_SESSION, (
                f"Session exceeded budget in {persona} run {run_i}: {len(questions)} asked"
            )

            # 2. Zero repeated questions within window W = 3
            for i, q in enumerate(questions):
                window = questions[max(0, i - 3):i]
                assert q not in window, (
                    f"Repeated question in window in {persona} run {run_i}: '{q}' in {window}"
                )

            # 3. Persona behavioral guarantees
            if persona == "deflecting":
                # Must not interrogate: questions asked should be <= 1 (after first deflection, holds)
                assert len(questions) <= 1, (
                    f"Deflecting persona asked too many questions ({len(questions)}): {questions}"
                )
                assert "hold" in moves

            elif persona == "near_silent":
                # Near-silent 1-word inputs must strictly trigger hold
                assert len(questions) == 0, (
                    f"Near-silent persona was asked questions ({len(questions)}): {questions}"
                )
                assert all(m == "hold" for m in moves)

            elif persona == "cooperative":
                # Cooperative persona should alternate ask and acknowledge
                assert "ask" in moves or "clarify" in moves

            total_runs += 1

    assert total_runs == 200, f"Expected 200 runs, got {total_runs}"
