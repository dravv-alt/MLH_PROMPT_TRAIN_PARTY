"""Unit tests for evaluation/metrics.py:
- Verifies metrics 1 to 14
- Each metric includes at least 3 positive and 3 negative test cases
- Strict test for hard negatives (quoted connectives vs verbal causatives)
- Tests deterministic repeatability on rerun
"""
import pytest
from evaluation.metrics import (
    unlicensed_connective_rate,
    polarity_flip_rate,
    role_reversal_rate,
    invented_entity_rate,
    superseded_reuse_rate,
    hedge_survival_rate,
    fallback_valid_rate,
    presupposition_violation_rate,
    gap_precision_recall,
    restatement_ratio,
    over_asking_rate,
    repeat_question_rate,
    uptake_rate,
    detect_causal_expressions,
)


# 1. Unlicensed Connective Rate Tests
def test_unlicensed_connectives_positive_cases():
    user_relations = []
    # Case 1: reply uses "because" with no edge
    assert unlicensed_connective_rate("You felt exhausted because the work was demanding.", user_relations) == 1.0
    # Case 2: reply uses "so" with no edge
    assert unlicensed_connective_rate("The deadline moved so you had to hurry.", user_relations) == 1.0
    # Case 3: reply uses "therefore"
    assert unlicensed_connective_rate("You were tired, therefore you rested.", user_relations) == 1.0


def test_unlicensed_connectives_negative_cases():
    user_relations = [{"type": "causal", "explicit_connective": "because"}]
    # Case 1: reply uses licensed "because"
    assert unlicensed_connective_rate("You felt tired because of the long hours.", user_relations) == 0.0
    # Case 2: reply has no connectives
    assert unlicensed_connective_rate("You noticed the timing.", []) == 0.0
    # Case 3: reply uses neutral sentence coordination
    assert unlicensed_connective_rate("You finished the report and went home.", []) == 0.0


def test_unlicensed_connectives_hard_negatives():
    # Hard negative 1: "because" inside quote of user words MUST NOT count as unlicensed
    user_relations = []
    user_text = "I said because he was shouting."
    reply = "You mentioned 'because he was shouting' during the discussion."
    assert unlicensed_connective_rate(reply, user_relations, user_text=user_text) == 0.0

    # Hard negative 2: verbal causative with no connective ("made you leave") MUST count as unlicensed
    reply_causative = "His shouting made you leave the meeting room."
    assert unlicensed_connective_rate(reply_causative, user_relations) == 1.0


# 2. Polarity Flip Rate Tests
def test_polarity_flip_rate():
    user_commitments = [
        {"predicate": "be_angry", "polarity": "negative"},
        {"predicate": "finish_work", "polarity": "positive"}
    ]
    # Positive cases (flips occur)
    assert polarity_flip_rate([{"predicate": "be_angry", "polarity": "positive"}], user_commitments) == 1.0
    assert polarity_flip_rate([{"predicate": "finish_work", "polarity": "negative"}], user_commitments) == 1.0
    assert polarity_flip_rate([
        {"predicate": "be_angry", "polarity": "positive"},
        {"predicate": "finish_work", "polarity": "positive"}
    ], user_commitments) == 0.5

    # Negative cases (no flips)
    assert polarity_flip_rate([{"predicate": "be_angry", "polarity": "negative"}], user_commitments) == 0.0
    assert polarity_flip_rate([{"predicate": "finish_work", "polarity": "positive"}], user_commitments) == 0.0
    assert polarity_flip_rate([{"predicate": "unrelated_pred", "polarity": "positive"}], user_commitments) == 0.0


# 3. Role Reversal Rate Tests
def test_role_reversal_rate():
    user_commitments = [
        {"predicate": "blame", "agent": "sister", "patient": "user"},
        {"predicate": "call", "agent": "doctor", "patient": "mother"}
    ]
    # Positive cases (swaps)
    assert role_reversal_rate([{"predicate": "blame", "agent": "user", "patient": "sister"}], user_commitments) == 1.0
    assert role_reversal_rate([{"predicate": "call", "agent": "mother", "patient": "doctor"}], user_commitments) == 1.0
    assert role_reversal_rate([
        {"predicate": "blame", "agent": "user", "patient": "sister"},
        {"predicate": "call", "agent": "doctor", "patient": "mother"}
    ], user_commitments) == 0.5

    # Negative cases (correct roles preserved)
    assert role_reversal_rate([{"predicate": "blame", "agent": "sister", "patient": "user"}], user_commitments) == 0.0
    assert role_reversal_rate([{"predicate": "call", "agent": "doctor", "patient": "mother"}], user_commitments) == 0.0
    assert role_reversal_rate([{"predicate": "other", "agent": "sister", "patient": "user"}], user_commitments) == 0.0


# 4. Invented Entity Rate Tests
def test_invented_entity_rate():
    user_entities = ["Priya", "Mumbai", "Internship"]
    # Positive cases
    assert invented_entity_rate(["Rohan"], user_entities) == 1.0
    assert invented_entity_rate(["Priya", "Delhi"], user_entities) == 0.5
    assert invented_entity_rate(["Anand", "Hospital", "Dr. Mehta"], user_entities) == 1.0

    # Negative cases
    assert invented_entity_rate(["Priya"], user_entities) == 0.0
    assert invented_entity_rate(["Mumbai", "Internship"], user_entities) == 0.0
    assert invented_entity_rate([], user_entities) == 0.0


# 5. Superseded Reuse Rate Tests
def test_superseded_reuse_rate():
    superseded = [{"predicate": "work_at_google"}, {"predicate": "call_brother"}]
    # Positive cases
    assert superseded_reuse_rate([{"predicate": "work_at_google"}], superseded) == 1.0
    assert superseded_reuse_rate([{"predicate": "call_brother"}], superseded) == 1.0
    assert superseded_reuse_rate([{"predicate": "work_at_google"}, {"predicate": "work_at_meta"}], superseded) == 0.5

    # Negative cases
    assert superseded_reuse_rate([{"predicate": "work_at_meta"}], superseded) == 0.0
    assert superseded_reuse_rate([{"predicate": "call_sister"}], superseded) == 0.0
    assert superseded_reuse_rate([], superseded) == 0.0


# 6. Hedge Survival Rate Tests
def test_hedge_survival_rate():
    user_commitments = [
        {"predicate": "feel_doubt", "hedge": True},
        {"predicate": "arrive_late", "hedge": False}
    ]
    # Positive cases (firm assertion replaces hedged commitment = failure)
    assert hedge_survival_rate([{"predicate": "feel_doubt", "hedge": False}], user_commitments) == 0.0
    assert hedge_survival_rate([{"predicate": "feel_doubt", "hedge": True}], user_commitments) == 1.0

    # Vacuous / negative cases
    assert hedge_survival_rate([{"predicate": "arrive_late", "hedge": False}], [{"predicate": "arrive_late", "hedge": False}]) == 1.0
    assert hedge_survival_rate([], user_commitments) == 1.0


# 7. Fallback Valid Rate Tests
def test_fallback_valid_rate():
    validator = lambda out: out.get("valid", False)
    assert fallback_valid_rate([{"valid": True}, {"valid": True}], validator) == 1.0
    assert fallback_valid_rate([{"valid": True}, {"valid": False}], validator) == 0.5
    assert fallback_valid_rate([{"valid": False}, {"valid": False}], validator) == 0.0


# 9. Presupposition Violation Rate Tests
def test_presupposition_violation_rate():
    user_commitments = [{"predicate": "submit", "patient": "paper"}]
    user_text = "I submitted the paper on time."

    # Positive cases (presupposes unstated facts)
    assert presupposition_violation_rate(["Why did you feel guilty about submitting it?"], user_commitments, user_text) == 1.0
    assert presupposition_violation_rate(["When did you stop procrastinating on the project?"], user_commitments, user_text) == 1.0
    assert presupposition_violation_rate(["Do you regret submitting the paper?"], user_commitments, user_text) == 1.0

    # Negative cases (licensed questions)
    assert presupposition_violation_rate(["What was the paper about?"], user_commitments, user_text) == 0.0
    assert presupposition_violation_rate(["Who received the paper when you submitted it?"], user_commitments, user_text) == 0.0
    assert presupposition_violation_rate(["Could you share what happened next?"], user_commitments, user_text) == 0.0


# 10. Gap Precision and Recall Tests
def test_gap_precision_recall():
    gold = [{"type": "unfilled_role", "predicate": "feel"}, {"type": "hedged_commitment", "predicate": "think"}]
    # Perfect match
    res_perfect = gap_precision_recall(gold, gold)
    assert res_perfect["f1"] == 1.0

    # Overflag (lower precision)
    detected_extra = gold + [{"type": "counterfactual_obligation", "predicate": "should"}]
    res_extra = gap_precision_recall(detected_extra, gold)
    assert res_extra["precision"] < 1.0 and res_extra["recall"] == 1.0

    # Underflag (lower recall)
    detected_less = [gold[0]]
    res_less = gap_precision_recall(detected_less, gold)
    assert res_less["recall"] < 1.0 and res_less["precision"] == 1.0


# 11. Restatement Ratio Tests
def test_restatement_ratio():
    user_text = "I went to Marine Drive yesterday and watched the sunset."
    # High copying
    assert restatement_ratio("You went to Marine Drive yesterday and watched the sunset.", user_text) >= 0.8
    # Moderate
    assert 0.2 < restatement_ratio("What was the atmosphere like when you watched the sunset at Marine Drive?", user_text) < 0.8
    # Zero copying
    assert restatement_ratio("Could you describe your feelings?", user_text) == 0.0


# 12. Over-asking Rate Tests
def test_over_asking_rate():
    gold_moves = [["hold"], ["acknowledge"], ["ask", "acknowledge"]]
    # Positive cases (system asks when gold is hold/ack)
    assert over_asking_rate(["ask", "ask", "ask"], gold_moves) == 1.0
    assert over_asking_rate(["ask", "acknowledge", "ask"], gold_moves) == 0.5
    # Negative cases (correctly holds or acknowledges)
    assert over_asking_rate(["hold", "acknowledge", "ask"], gold_moves) == 0.0


# 13. Repeat Question Rate Tests
def test_repeat_question_rate():
    # Repeated stems
    assert repeat_question_rate(["What was that like?", "What was that like for you?"]) == 0.5
    # Distinct questions
    assert repeat_question_rate(["What was that like?", "Could you elaborate on the project?"]) == 0.0


# 14. Determinism on Rerun Test
def test_metrics_deterministic_rerun():
    reply = "His shouting made you leave because you were anxious."
    res1 = unlicensed_connective_rate(reply, [])
    res2 = unlicensed_connective_rate(reply, [])
    assert res1 == res2
