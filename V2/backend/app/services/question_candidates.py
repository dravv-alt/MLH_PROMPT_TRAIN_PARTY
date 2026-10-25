"""Sanctuary V2 Candidate Question Generation & Ranking (Tasks T3.2 & T3.4).

Generates candidate questions for structural gaps via:
1. LLM-off deterministic template path (grounded directly in gap span and user tokens).
2. LLM-assisted candidate phrasing under presupposition constraints.
Ranks surviving candidates with explicit, inspectable features:
- Gap salience
- Question openness (penalizes yes/no unless clarifying)
- Presupposition load (fewer unasserted triggers)
- Anchoring to user span
- Novelty against previous questions in session
- Absence of leading tags (", right?", "don't you think")
- Absence of advice / suggestions ("have you considered", "you should")
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.presupposition_filter import filter_candidates
from app.services.gaps import (
    GAP_UNFILLED_ROLE,
    GAP_HEDGED_COMMITMENT,
    GAP_REPORTED_CLAIM,
    GAP_UNRESOLVED_REFERENCE,
    GAP_CORRECTION_LINK,
    GAP_COUNTERFACTUAL_OBLIGATION,
    GAP_CONTRAST_THIN_ARM,
    GAP_RECURRING_TOPIC,
    extract_predicate_lemma,
)

# Template bank for LLM-off path (clean, open, neutral)
GAP_TEMPLATES = {
    GAP_UNFILLED_ROLE: [
        "What was occurring around you when you began to {pred}?",
        "What prompted your decision regarding {pred}?",
        "Could you say more about what was happening when you {pred}?",
    ],
    GAP_HEDGED_COMMITMENT: [
        "What leads you to feel uncertain about that?",
        "How would you describe what was happening in that moment?",
        "Could you say a bit more about what brought that thought to mind?",
    ],
    GAP_REPORTED_CLAIM: [
        "What was your perspective when {agent} mentioned that?",
        "How did you view the situation that was described?",
        "What was occurring when that was said?",
    ],
    GAP_UNRESOLVED_REFERENCE: [
        "Who was involved in that particular moment?",
        "Could you clarify who you were referring to?",
        "Which person was participating in that interaction?",
    ],
    GAP_CORRECTION_LINK: [
        "Could you clarify which part of that you were adjusting?",
        "Which detail did you mean to focus on?",
        "What specific point did you wish to adjust?",
    ],
    GAP_COUNTERFACTUAL_OBLIGATION: [
        "What expectation was in place when that happened?",
        "What was leading you to feel that was expected?",
        "How did that obligation arise in that context?",
    ],
    GAP_CONTRAST_THIN_ARM: [
        "What was occurring on the other side of that contrast?",
        "Could you share what happened next in that situation?",
        "How did the other aspect compare in that instance?",
    ],
    GAP_RECURRING_TOPIC: [
        "How has that matter developed since you first mentioned it?",
        "What has changed regarding that since earlier?",
        "Where does that situation currently stand?",
    ],
}

# Negative markers to detect leading or advice-giving candidates
LEADING_PATTERNS = [
    r",\s*(?:right|isn['’]t it|don['’]t you think|wouldn['’]t you say)\?",
    r"\bdon['’]t you think\b",
    r"\bwouldn['’]t it be better\b",
    r"\bare you sure\b",
]

ADVICE_PATTERNS = [
    r"\bhave you (?:tried|considered|thought about)\b",
    r"\bwhy don['’]t you\b",
    r"\byou (?:should|could|might want to)\b",
    r"\bhave you talked to\b",
]


def generate_template_candidates(gap: Dict[str, Any], user_text: str) -> List[str]:
    """Generate up to 3 deterministic template candidates anchored to user tokens."""
    gap_type = gap.get("type", GAP_UNFILLED_ROLE)
    templates = GAP_TEMPLATES.get(gap_type, GAP_TEMPLATES[GAP_UNFILLED_ROLE])

    raw_pred = gap.get("evidence", {}).get("predicate", "that")
    if raw_pred in {"epistemic_hedge", "hedge", "unspecified", "none", ""}:
        pred = "that"
    else:
        pred = extract_predicate_lemma(raw_pred) or raw_pred
    agent = gap.get("evidence", {}).get("agent", "they")

    candidates = []
    for tpl in templates:
        formatted = tpl.format(pred=pred, agent=agent)
        candidates.append(formatted)

    return candidates


def score_candidate(
    candidate: str,
    gap: Dict[str, Any],
    user_text: str,
    prior_questions: List[str] = None,
) -> float:
    """Score candidate by inspectable features. Higher is better."""
    score = 10.0
    lower = candidate.lower()

    # 1. Openness: Penalize yes/no questions unless clarifying
    is_yes_no = lower.startswith(("is ", "are ", "do ", "did ", "can ", "could ", "would ", "have ", "has "))
    if is_yes_no and gap.get("type") != GAP_UNRESOLVED_REFERENCE:
        score -= 3.0

    # 2. Leading question penalty
    if any(re.search(pat, lower) for pat in LEADING_PATTERNS):
        score -= 6.0

    # 3. Advice penalty
    if any(re.search(pat, lower) for pat in ADVICE_PATTERNS):
        score -= 8.0

    # 4. Anchoring to user words and gap predicate
    user_words = set(re.findall(r"\w+", user_text.lower()))
    cand_words = set(re.findall(r"\w+", lower))
    overlap = len(cand_words & user_words)
    score += min(2.0, overlap * 0.5)

    gap_pred = extract_predicate_lemma(gap.get("evidence", {}).get("predicate", "")) or extract_predicate_lemma(gap.get("predicate", ""))
    if gap_pred and gap_pred.lower() in lower:
        score += 3.0

    # 5. Length penalty: ideal question is 8 to 18 words
    word_count = len(candidate.split())
    if word_count < 5 or word_count > 25:
        score -= 2.0

    # 6. Novelty penalty against earlier questions and stems
    if prior_questions:
        cand_lower = candidate.strip().lower()
        cand_stem = " ".join(candidate.split()[:3]).lower()
        for prior in prior_questions:
            prior_lower = prior.strip().lower()
            if cand_lower == prior_lower:
                score -= 50.0
            elif cand_stem == " ".join(prior.split()[:3]).lower():
                score -= 6.0

    return score


def rank_and_select_candidate(
    candidates: List[str],
    gap: Dict[str, Any],
    user_commitments: List[Dict[str, Any]],
    user_text: str,
    prior_questions: List[str] = None,
) -> Tuple[Optional[str], float, List[Dict[str, Any]]]:
    """Run presupposition filter, score survivors, and select top candidate.
    Returns: (selected_question: Optional[str], score: float, rejection_log: List[Dict])
    """
    surviving, rejections = filter_candidates(candidates, user_commitments, user_text)
    if not surviving:
        return None, 0.0, rejections

    scored = []
    for cand in surviving:
        sc = score_candidate(cand, gap, user_text, prior_questions)
        scored.append((cand, sc))

    # Filter out candidates with non-positive scores (e.g. repeated questions or heavy penalties)
    valid_scored = [item for item in scored if item[1] > 0.0]
    if not valid_scored:
        return None, 0.0, rejections

    # Sort descending by score, ties broken deterministically by string length then alphabetical
    valid_scored.sort(key=lambda item: (-item[1], -len(item[0]), item[0]))
    best_cand, best_score = valid_scored[0]

    return best_cand, best_score, rejections
