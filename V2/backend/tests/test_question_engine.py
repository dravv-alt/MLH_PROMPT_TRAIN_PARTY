"""Tests for Phase 3 Question Engine (Tasks T3.2, T3.3, T3.4):
- Presupposition trigger extraction & licensing check
- Hard negative licensing check: "guilty" allowed only when asserted by user
- Ranking features: openness, leading question detector, advice avoidance
- LLM-off template candidates for all 8 canonical gap types
"""
import pytest
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
from app.services.gaps import CANONICAL_GAP_TYPES, GAP_UNFILLED_ROLE, GAP_REPORTED_CLAIM


def test_presupposition_trigger_extraction():
    q1 = "Why did you resign from the position?"
    trigs1 = extract_candidate_presuppositions(q1)
    assert len(trigs1) == 1
    assert trigs1[0]["trigger_type"] == "wh_action"

    q2 = "When did you stop helping at home?"
    trigs2 = extract_candidate_presuppositions(q2)
    assert any(t["trigger_type"] == "change_of_state_stop" for t in trigs2)

    q3 = "Do you regret submitting the proposal?"
    trigs3 = extract_candidate_presuppositions(q3)
    assert any(t["trigger_type"] == "factive_regret" for t in trigs3)


def test_hard_negative_licensing_guilty():
    """Hard negative: 'Why did that make you feel guilty?' is rejected unless the user used that word."""
    # Negative case: User never asserted guilt
    user_text_unasserted = "I decided not to go to the dinner."
    user_commitments_unasserted = [{"predicate": "decide", "patient": "dinner"}]
    cand = "Why did that make you feel guilty?"
    is_licensed, reason, _ = check_presupposition_licensing(cand, user_commitments_unasserted, user_text_unasserted)
    assert not is_licensed
    assert "guilty" in reason

    # Positive case: User explicitly asserted guilt -> MUST BE ALLOWED!
    user_text_asserted = "I felt so guilty about missing the team dinner."
    user_commitments_asserted = [{"predicate": "feel", "patient": "guilty"}]
    is_licensed_asserted, reason_asserted, _ = check_presupposition_licensing(cand, user_commitments_asserted, user_text_asserted)
    assert is_licensed_asserted, "When user explicitly states guilt, the question is licensed!"
    assert reason_asserted is None


def test_hard_negative_change_of_state_and_reporting():
    # Change of state without basis is rejected
    user_text = "I was busy with assignments."
    user_commitments = [{"predicate": "be_busy"}]
    cand_stop = "When did you stop helping at home?"
    is_lic, reason, _ = check_presupposition_licensing(cand_stop, user_commitments, user_text)
    assert not is_lic
    assert "stop" in reason or "helping" in reason

    # Reported speech allows asking what she meant
    user_text_rep = "She told me the budget was rejected."
    user_commitments_rep = [{"predicate": "tell", "agent": "she"}]
    cand_mean = "What did she mean by that?"
    is_lic_rep, reason_rep, _ = check_presupposition_licensing(cand_mean, user_commitments_rep, user_text_rep)
    assert is_lic_rep


def test_ranking_penalizes_leading_and_advice_questions():
    gap = {"type": GAP_UNFILLED_ROLE, "evidence": {"predicate": "leave"}}
    user_text = "I left the room during the debate."

    good_cand = "What was occurring around you when you decided to leave?"
    leading_cand = "What was occurring, don't you think you overreacted?"
    advice_cand = "Have you considered talking to them about why you left?"

    score_good = score_candidate(good_cand, gap, user_text)
    score_leading = score_candidate(leading_cand, gap, user_text)
    score_advice = score_candidate(advice_cand, gap, user_text)

    assert score_good > score_leading, "Leading questions must be penalized"
    assert score_good > score_advice, "Advice questions must be heavily penalized"


def test_all_candidates_rejected_falls_back_safely():
    gap = {"type": GAP_UNFILLED_ROLE, "evidence": {"predicate": "leave"}}
    user_text = "I left."
    user_commitments = []
    # Both candidates contain completely unasserted entities
    candidates = [
        "Why did that make you feel guilty about the hospital?",
        "When did you stop quarreling with your supervisor?"
    ]
    best_cand, score, rejections = rank_and_select_candidate(candidates, gap, user_commitments, user_text)
    assert best_cand is None, "When all candidates violate presuppositions, selector must return None"
    assert len(rejections) == 2


def test_templates_cover_every_canonical_gap_type():
    user_text = "The manager said the review was finished."
    for gap_type in CANONICAL_GAP_TYPES:
        gap = {"type": gap_type, "evidence": {"predicate": "review", "agent": "manager"}}
        cands = generate_template_candidates(gap, user_text)
        assert len(cands) >= 1
        assert all("?" in c for c in cands)
