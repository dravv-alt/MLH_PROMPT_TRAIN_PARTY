"""Sanctuary V2 End-to-End Discourse Question Selection Pipeline.

Implements the Smallest Demonstrable Slice (T2.1, T2.3, T3.2, T3.3, T3.4):
1. Detects structural gaps from user text (open-vocabulary, no emotion lexicon)
2. Updates persistent QUD stack in session state
3. Selects dialogue move (ask, clarify, acknowledge, hold)
4. Generates candidate questions (template path for LLM-off mode)
5. Filters candidates through presupposition budget
6. Ranks and selects surviving candidate with inspectable scoring
7. Produces an end-to-end question trace
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.gaps import (
    detect_structural_gaps,
    extract_predicate_lemma,
    GAP_UNFILLED_ROLE,
    GAP_HEDGED_COMMITMENT,
    GAP_REPORTED_CLAIM,
    GAP_UNRESOLVED_REFERENCE,
    GAP_CORRECTION_LINK,
    GAP_COUNTERFACTUAL_OBLIGATION,
    GAP_CONTRAST_THIN_ARM,
    GAP_RECURRING_TOPIC,
)
from app.services.qud_stack import (
    merge_and_update_qud_stack,
    get_active_quds,
    STATUS_OPEN,
)
from app.services.question_candidates import (
    generate_template_candidates,
    rank_and_select_candidate,
)

# Safety interrupt patterns (recall-first, bypasses question generation to standard safety resources)
SAFETY_INTERRUPT_PATTERNS = [
    r"\b(?:kill|end)\s+(?:myself|my\s+life)\b",
    r"\b(?:commit\s+)?suicide\b",
    r"\bwant\s+to\s+die\b",
    r"\bhurt\s+myself\b",
]

# Explicit user signals requesting silence or vent without questioning
EXPLICIT_HOLD_PATTERNS = [
    r"\bjust\s+let\s+me\s+talk\b",
    r"\bdon['’]t\s+ask\s+(?:me\s+)?(?:any\s+)?questions\b",
    r"\bstop\s+(?:asking|talking)\b",
    r"\bno\s+questions\b",
]


def check_safety_interrupt(text: str) -> bool:
    """Safety interrupt check: language indicating imminent harm routes to crisis resources."""
    lower = text.lower()
    return any(re.search(pat, lower) for pat in SAFETY_INTERRUPT_PATTERNS)


def check_explicit_hold_signal(text: str) -> bool:
    """Check if the user explicitly requested to talk without being questioned."""
    lower = text.lower()
    return any(re.search(pat, lower) for pat in EXPLICIT_HOLD_PATTERNS)


def format_human_reason(gap: Dict[str, Any]) -> str:
    """Format plain-language explainability reason for why this question is grounded in the user's text."""
    gtype = gap.get("type")
    evidence = gap.get("evidence", {})
    pred = extract_predicate_lemma(evidence.get("predicate", "that")) or "that"

    if gtype == GAP_UNFILLED_ROLE:
        return f"You noted that you began to {pred}, and didn't mention what led up to that."
    elif gtype == GAP_HEDGED_COMMITMENT:
        return f"You expressed uncertainty about {pred} without saying more about what brought that to mind."
    elif gtype == GAP_REPORTED_CLAIM:
        agent = evidence.get("agent", "someone")
        return f"You mentioned what {agent} stated, but didn't share your own take on it."
    elif gtype == GAP_UNRESOLVED_REFERENCE:
        return "You mentioned someone in that moment, but it wasn't clear who was involved."
    elif gtype == GAP_CORRECTION_LINK:
        return "You clarified a prior detail, and we want to ensure we focus on the right point."
    elif gtype == GAP_COUNTERFACTUAL_OBLIGATION:
        return f"You noted an expectation about {pred} that seemed unresolved."
    elif gtype == GAP_CONTRAST_THIN_ARM:
        return "You brought up a contrast, but only described one side of it."
    elif gtype == GAP_RECURRING_TOPIC:
        return f"This topic has come up across multiple moments in our conversation."
    return "You touched upon this point and left room to explore it further."


def execute_question_pipeline(
    analysis: Dict[str, Any],
    prior_turns: List[Dict[str, Any]] = None,
    session_qud_stack: List[Dict[str, Any]] = None,
    turn_index: int = 1,
    mode: str = "template_llm_off",
) -> Dict[str, Any]:
    """Execute the discourse-grounded question selection pipeline end-to-end."""
    text = analysis.get("redacted_text", "")
    prior_turns = prior_turns or []
    propositions = analysis.get("discourse_context", {}).get("current_propositions", [])

    # 1. Safety Interrupt
    if check_safety_interrupt(text):
        return {
            "move": "safety_interrupt",
            "selected_question": None,
            "question_trace": {
                "reason": "Safety interrupt triggered: routed directly to crisis resources path.",
                "move": "safety_interrupt",
                "gap_id": None,
            },
            "gaps": [],
            "qud_stack": session_qud_stack or [],
            "diagnostics_status": "safety_override",
        }

    # 2. Structural Gap Detection (Task T2.1)
    gaps = detect_structural_gaps(analysis, prior_turns)

    # 3. QUD Stack Maintenance (Task T2.3)
    correction_context = analysis.get("response_plan", {}).get("correction_context")
    updated_qud_stack = merge_and_update_qud_stack(
        session_qud_stack or [],
        gaps,
        turn_index,
        correction_context=correction_context,
    )
    active_quds = get_active_quds(updated_qud_stack)

    # 4. Dialogue Move Selection (Task T3.1)
    # Check explicit hold or very short turn
    if check_explicit_hold_signal(text) or len(text.strip().split()) <= 2:
        return {
            "move": "hold",
            "selected_question": None,
            "question_trace": {
                "reason": "Turn is brief or user explicitly requested to speak without follow-up questions.",
                "move": "hold",
                "gap_id": None,
                "spans": [],
                "presuppositions_checked": [],
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": "ok",
        }

    # If no active structural gaps exist, move is acknowledge
    if not active_quds:
        return {
            "move": "acknowledge",
            "selected_question": None,
            "question_trace": {
                "reason": "No unaddressed structural discourse gaps detected in user utterance.",
                "move": "acknowledge",
                "gap_id": None,
                "spans": [],
                "presuppositions_checked": [],
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": "ok",
        }

    # 5. Target Top Salient Gap
    target_qud = active_quds[0]
    target_gap = next((g for g in gaps if g.get("gap_id") == target_qud.get("gap_id")), None)
    if not target_gap:
        # Reconstruct gap object from QUD entry
        target_gap = {
            "gap_id": target_qud["gap_id"],
            "type": GAP_UNFILLED_ROLE,
            "spans": target_qud.get("spans", [[0, len(text)]]),
            "evidence": {"predicate": target_qud.get("frame_id", "that")},
            "detector_id": "qud_stack_persistent",
        }

    # 6. Candidate Generation (Task T3.2)
    prior_questions = [t.get("question") for t in prior_turns if t.get("question")]
    candidates = generate_template_candidates(target_gap, text)

    # 7. Presupposition Filtering & Ranking (Tasks T3.3 & T3.4)
    selected_question, score, rejections = rank_and_select_candidate(
        candidates=candidates,
        gap=target_gap,
        user_commitments=propositions,
        user_text=text,
        prior_questions=prior_questions,
    )

    # 8. Selection and Realization Trace
    if selected_question is None:
        # Fallback to acknowledge if all candidates took unasserted facts for granted
        return {
            "move": "acknowledge",
            "selected_question": None,
            "question_trace": {
                "reason": "All candidate questions were rejected by presupposition filter.",
                "move": "acknowledge",
                "gap_id": target_gap.get("gap_id"),
                "rejections": rejections,
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": "presupposition_fallback",
        }

    move_type = "clarify" if target_gap.get("type") in {GAP_UNRESOLVED_REFERENCE, GAP_CORRECTION_LINK} else "ask"
    human_reason = format_human_reason(target_gap)

    trace = {
        "gap_id": target_gap.get("gap_id"),
        "gap_type": target_gap.get("type"),
        "spans": target_gap.get("spans", []),
        "detector_id": target_gap.get("detector_id"),
        "presuppositions_checked": [r.get("triggers", []) for r in rejections] or ["licensed_against_commitments"],
        "move": move_type,
        "score": round(score, 2),
        "human_reason": human_reason,
        "generation_mode": mode,
    }

    return {
        "move": move_type,
        "selected_question": selected_question,
        "question_trace": trace,
        "gaps": gaps,
        "qud_stack": updated_qud_stack,
        "diagnostics_status": "ok",
    }
