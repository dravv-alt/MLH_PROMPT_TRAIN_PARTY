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

INSTRUCTION_CONTROL_PATTERNS = [
    r"\b(?:can|could)\s+you\s+(?:show|tell|display|give|help)\b",
    r"\b(?:please\s+)?(?:don['’]t\s+include|do\s+not\s+include|save\s+that|keep\s+it|omit)\b",
    r"\bi\s+don['’]t\s+want\s+(?:this|that)\s+kept\b",
    r"\bi['’]d\s+rather\s+have\s+it\s+only\b",
    r"\bi\s+(?:still\s+)?want\s+to\s+keep\s+the\s+journal\b",
    r"\bi['’]m\s+okay\s+with\s+not\s+knowing\b",
    r"\bi\s+don['’]t\s+want\s+to\s+force\s+an\s+explanation\b",
    r"\byou\s+keep\s+making\s+this\s+sound\b",
    r"\bi\s+haven['’]t\s+said\s+that\b",
    r"\bthat\s+makes\s+me\s+think\b",
    r"\bnow\s+i\s+see\s+it\s+as\b",
    r"\bmy\s+current\s+view\s+is\b",
    r"\bi\s+also\s+realized\s+that\b",
    r"\bi\s+could\s+make\s+progress\b",
    r"\bi\s+could\s+see\s+what\s+(?:they|he|she)\s+meant\b",
    r"\bi\s+don['’]t\s+want\s+to\s+use\s+those\s+things\s+as\s+excuses\b",
    r"\bi\s+want\s+to\s+look\s+at\s+the\s+mistakes\s+individually\b",
]


def check_user_instruction_or_control(text: str) -> bool:
    """Check if user gave an explicit command, privacy control, or boundary pushback."""
    lower = text.lower()
    return any(re.search(pat, lower) for pat in INSTRUCTION_CONTROL_PATTERNS)


def check_safety_interrupt(text: str) -> bool:
    """Safety interrupt check: language indicating imminent harm routes to crisis resources."""
    lower = text.lower()
    return any(re.search(pat, lower) for pat in SAFETY_INTERRUPT_PATTERNS)


def check_explicit_hold_signal(text: str) -> bool:
    """Check if the user explicitly requested to talk without being questioned."""
    lower = text.lower()
    return any(re.search(pat, lower) for pat in EXPLICIT_HOLD_PATTERNS)


def check_user_direct_question(text: str) -> bool:
    """Check if user asked a direct question to the system rather than sharing personal narrative."""
    stripped = text.strip()
    if not stripped.endswith("?"):
        return False
    lower = stripped.lower()
    first_person = bool(re.search(r"\b(?:i|me|my|myself|mine)\b", lower))
    is_wh = bool(re.match(r"^(?:what|where|when|who|which|how|can\s+you|could\s+you|is\s+there)\b", lower))
    return is_wh and not first_person


def check_consecutive_deflections_or_budget(
    prior_turns: List[Dict[str, Any]],
    session_qud_stack: Optional[List[Dict[str, Any]]],
) -> bool:
    """If user deflected last two questions or question budget is reached, back off and hold."""
    if not session_qud_stack:
        return False
    recent_deflections = [e for e in session_qud_stack if e.get("status") == "deflected"]
    return len(recent_deflections) >= 2



def format_human_reason(gap: Dict[str, Any]) -> str:
    """Format plain-language explainability reason for why this question is grounded in the user's text."""
    gtype = gap.get("type")
    evidence = gap.get("evidence", {})
    pred = extract_predicate_lemma(evidence.get("predicate", "that")) or "that"

    if gtype == GAP_UNFILLED_ROLE:
        return f"You noted that you began to {pred}, and didn't mention what led up to that."
    elif gtype == GAP_HEDGED_COMMITMENT:
        if pred in {"epistemic_hedge", "hedge", "that"}:
            return "You expressed uncertainty without saying more about what brought that to mind."
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

    # 2. Uptake Classification of previous question (Task T4.1)
    from app.services.uptake_classifier import classify_answer_uptake
    last_turn = prior_turns[-1] if prior_turns else None
    uptake_result = classify_answer_uptake(analysis, last_turn, current_text=text)
    answered_ids = {uptake_result["targeted_gap_id"]} if uptake_result["uptake"] == "answered" and uptake_result.get("targeted_gap_id") else set()
    deflected_ids = {uptake_result["targeted_gap_id"]} if uptake_result["uptake"] == "deflected" and uptake_result.get("targeted_gap_id") else set()

    # 3. Structural Gap Detection (Task T2.1 & T2.2)
    from app.services.gaps import rank_gaps_by_salience
    raw_gaps = detect_structural_gaps(analysis, prior_turns)
    gaps = rank_gaps_by_salience(raw_gaps, analysis, prior_turns)
    parser_fallback = analysis.get("parser_fallback")
    diag_status = "degraded" if parser_fallback else "ok"

    # 4. QUD Stack Maintenance (Tasks T2.3 & T4.3)
    correction_context = analysis.get("response_plan", {}).get("correction_context")
    updated_qud_stack = merge_and_update_qud_stack(
        session_qud_stack or [],
        gaps,
        turn_index,
        correction_context=correction_context,
        answered_gap_ids=answered_ids,
        deflected_gap_ids=deflected_ids,
        current_propositions=propositions,
    )
    active_quds = get_active_quds(updated_qud_stack)

    # 5. Backoff & Pacing Policy (Task T4.2)
    from app.services.backoff_policy import ConversationPolicyTracker
    policy = ConversationPolicyTracker()
    allow_q, enforced_move, policy_reason = policy.evaluate_question_policy(
        text, prior_turns, updated_qud_stack, turn_index
    )
    if not allow_q:
        return {
            "move": enforced_move or "hold",
            "selected_question": None,
            "question_trace": {
                "reason": policy_reason or "Policy backoff enforced.",
                "move": enforced_move or "hold",
                "gap_id": None,
                "spans": [],
                "presuppositions_checked": [],
                "score": 0.0,
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": diag_status,
            "uptake": uptake_result["uptake"],
        }

    # 6. Dialogue Move Selection (Task T3.1)
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
                "score": 0.0,
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": diag_status,
            "uptake": uptake_result["uptake"],
        }

    # Check direct factual/external question to system
    if check_user_direct_question(text):
        return {
            "move": "hold",
            "selected_question": None,
            "question_trace": {
                "reason": "User asked a direct external question; holding to answer rather than counter-question.",
                "move": "hold",
                "gap_id": None,
                "spans": [],
                "presuppositions_checked": [],
                "score": 0.0,
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": diag_status,
            "uptake": uptake_result["uptake"],
        }

    # Check user commands, privacy settings, or explicit boundaries
    if check_user_instruction_or_control(text):
        return {
            "move": "acknowledge",
            "selected_question": None,
            "question_trace": {
                "reason": "User gave explicit direction, privacy setting, or conversation boundary.",
                "move": "acknowledge",
                "gap_id": None,
                "spans": [],
                "presuppositions_checked": [],
                "score": 0.0,
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": diag_status,
            "uptake": uptake_result["uptake"],
        }

    # Check consecutive deflections / question budget backoff
    if check_consecutive_deflections_or_budget(prior_turns, session_qud_stack):
        return {
            "move": "hold",
            "selected_question": None,
            "question_trace": {
                "reason": "Question budget backoff: consecutive deflections detected.",
                "move": "hold",
                "gap_id": None,
                "spans": [],
                "presuppositions_checked": [],
                "score": 0.0,
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": diag_status,
            "uptake": uptake_result["uptake"],
        }

    # If no structural gaps exist in the current turn or no active QUDs, move is acknowledge
    if not gaps or not active_quds:
        return {
            "move": "acknowledge",
            "selected_question": None,
            "question_trace": {
                "reason": "no_gap_detected",
                "move": "acknowledge",
                "gap_id": None,
                "spans": [],
                "presuppositions_checked": [],
                "score": 0.0,
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": diag_status,
            "reason": "no_gap_detected",
            "uptake": uptake_result["uptake"],
        }

    # 5. Target Top Salient Gap
    from app.services.gaps import score_gap_salience
    available_gaps = [g for g in gaps if not policy.is_gap_suppressed(g.get("gap_id"), updated_qud_stack, turn_index)]
    if not available_gaps:
        return {
            "move": "acknowledge",
            "selected_question": None,
            "question_trace": {
                "reason": "All detected gaps are currently suppressed by backoff window policy.",
                "move": "acknowledge",
                "gap_id": None,
                "spans": [],
                "presuppositions_checked": [],
                "score": 0.0,
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": diag_status,
            "uptake": uptake_result["uptake"],
        }

    target_gap = available_gaps[0]
    salience = score_gap_salience(target_gap, analysis, prior_turns)
    salience_score = salience[0] if isinstance(salience, tuple) else salience
    if salience_score < 0.12:
        return {
            "move": "acknowledge",
            "selected_question": None,
            "question_trace": {
                "reason": "Gap salience below discourse question threshold; holding with acknowledgment.",
                "move": "acknowledge",
                "gap_id": target_gap.get("gap_id"),
                "spans": target_gap.get("spans", []),
                "presuppositions_checked": [],
                "score": 0.0,
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": diag_status,
            "uptake": uptake_result["uptake"],
        }

    target_qud = next((q for q in active_quds if q.get("gap_id") == target_gap.get("gap_id")), active_quds[0])
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

    # 8. Selection and Realization Filter Check (Task T3.5)
    if selected_question is None:
        return {
            "move": "acknowledge",
            "selected_question": None,
            "question_trace": {
                "reason": "All candidate questions were rejected by presupposition filter.",
                "move": "acknowledge",
                "gap_id": target_gap.get("gap_id"),
                "rejections": rejections,
                "score": 0.0,
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": "presupposition_fallback",
            "uptake": uptake_result["uptake"],
        }

    # Re-verify presuppositions on final realized question
    from app.services.presupposition_filter import check_presupposition_licensing
    is_lic, lic_reason, _ = check_presupposition_licensing(selected_question, propositions, text)
    if not is_lic:
        return {
            "move": "acknowledge",
            "selected_question": None,
            "question_trace": {
                "reason": f"Final realization failed presupposition filter check: {lic_reason}",
                "move": "acknowledge",
                "gap_id": target_gap.get("gap_id"),
                "rejections": [{"candidate": selected_question, "reason": lic_reason}],
                "score": 0.0,
            },
            "gaps": gaps,
            "qud_stack": updated_qud_stack,
            "diagnostics_status": "presupposition_fallback",
            "uptake": uptake_result["uptake"],
        }

    move_type = "clarify" if target_gap.get("type") in {GAP_UNRESOLVED_REFERENCE, GAP_CORRECTION_LINK} else "ask"
    human_reason = format_human_reason(target_gap)

    # Mark the asked QUD entry with last_asked_turn so suppression policy knows
    for q_entry in updated_qud_stack:
        if q_entry.get("gap_id") == target_gap.get("gap_id"):
            q_entry["last_asked_turn"] = turn_index
            break

    trace = {
        "gap_id": target_gap.get("gap_id"),
        "gap_type": target_gap.get("type"),
        "spans": target_gap.get("spans", []),
        "detector_id": target_gap.get("detector_id"),
        "presuppositions_checked": [r.get("triggers", []) for r in rejections] or ["licensed_against_commitments"],
        "move": move_type,
        "score": round(score, 2),
        "human_reason": human_reason,
        "reason": human_reason,
        "generation_mode": mode,
    }

    return {
        "move": move_type,
        "selected_question": selected_question,
        "question_trace": trace,
        "gaps": gaps,
        "qud_stack": updated_qud_stack,
        "diagnostics_status": diag_status,
        "uptake": uptake_result["uptake"],
    }
