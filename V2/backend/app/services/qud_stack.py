"""Sanctuary V2 Question Under Discussion (QUD) Stack (Tasks T2.3 & T4.3).

Maintains a persistent list of open discourse questions raised by structural gaps.
Stored entirely within the existing session state JSON snapshot (no new tables).
Enforces valid status transitions, frame merging, abandonment after N turns,
supersession updates, and automatic resolution when later frames fill gaps.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Set


STATUS_OPEN = "open"
STATUS_ANSWERED = "answered"
STATUS_DEFLECTED = "deflected"
STATUS_ABANDONED = "abandoned"
STATUS_SUPERSEDED = "superseded"

LEGAL_STATUS_TRANSITIONS = {
    STATUS_OPEN: {STATUS_ANSWERED, STATUS_DEFLECTED, STATUS_ABANDONED, STATUS_SUPERSEDED},
    STATUS_DEFLECTED: {STATUS_OPEN, STATUS_ABANDONED, STATUS_SUPERSEDED},
    STATUS_ANSWERED: {STATUS_SUPERSEDED},  # if answered frame is later retracted
    STATUS_ABANDONED: set(),
    STATUS_SUPERSEDED: set(),
}


def create_qud_entry(
    gap_id: str,
    neutral_question_form: str,
    spans: List[List[int]],
    turn_index: int,
    frame_id: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "gap_id": gap_id,
        "frame_id": frame_id or gap_id,
        "neutral_question_form": neutral_question_form,
        "status": STATUS_OPEN,
        "spans": spans,
        "created_turn": turn_index,
        "last_touched": turn_index,
        "recurrence_count": 1,
    }


def transition_qud_status(entry: Dict[str, Any], new_status: str, current_turn: int) -> bool:
    """Transition a QUD entry's status if legal."""
    curr = entry.get("status", STATUS_OPEN)
    if new_status == curr:
        entry["last_touched"] = current_turn
        return True

    allowed = LEGAL_STATUS_TRANSITIONS.get(curr, set())
    if new_status not in allowed:
        return False

    entry["status"] = new_status
    entry["last_touched"] = current_turn
    return True


def format_qud_question(gap: Dict[str, Any]) -> str:
    """Format a clean, natural question representing the Question Under Discussion."""
    if gap.get("neutral_question_form"):
        return gap["neutral_question_form"]
    gtype = gap.get("type", "")
    evidence = gap.get("evidence", {})
    raw_pred = evidence.get("predicate", "")
    from app.services.gaps import extract_predicate_lemma
    pred = extract_predicate_lemma(raw_pred) or raw_pred
    if pred in {"epistemic_hedge", "hedge", ""}:
        pred = "that"

    if gtype == "unfilled_role":
        return f"What was occurring around you when you began to {pred}?"
    elif gtype == "hedged_commitment":
        return "What leads you to feel uncertain about that?"
    elif gtype == "reported_claim":
        agent = evidence.get("agent", "they")
        return f"What was your perspective when {agent} mentioned that?"
    elif gtype == "unresolved_reference":
        return "Who was involved in that particular moment?"
    elif gtype == "counterfactual_obligation":
        if str(pred).lower() in {"could", "would", "should", "might", "can", "wished", "wish", "if", "that", "must", "may"}:
            return "What expectation was in place when that happened?"
        return f"What expectation was in place regarding {pred}?"
    elif gtype == "contrast_thin_arm":
        return "What was occurring on the other side of that contrast?"
    elif gtype == "correction_link":
        return "Could you clarify which part of that you were adjusting?"
    elif gtype == "recurring_topic":
        return "How has that situation developed since you first mentioned it?"
    return "Could you say more about what was happening in that moment?"


def merge_and_update_qud_stack(
    qud_stack: List[Dict[str, Any]],
    new_gaps: List[Dict[str, Any]],
    turn_index: int,
    correction_context: Optional[Dict[str, Any]] = None,
    answered_gap_ids: Optional[Set[str]] = None,
    deflected_gap_ids: Optional[Set[str]] = None,
    current_propositions: Optional[List[Dict[str, Any]]] = None,
    abandon_threshold: int = 4,
) -> List[Dict[str, Any]]:
    """Update the QUD stack across turns:
    1. Mark answered or deflected gaps from uptake classifier
    2. Check if current propositions fill open gaps
    3. Mark superseded gaps if correction retracted the base frame
    4. Mark abandoned after abandon_threshold untouched turns
    5. Merge new gaps targeting existing active frames and increment recurrence
    6. Append newly raised gaps
    """
    stack = copy.deepcopy(qud_stack or [])
    answered_ids = set(answered_gap_ids or [])
    deflected_ids = set(deflected_gap_ids or [])

    # 1. Apply uptake updates to existing stack
    for entry in stack:
        gid = entry.get("gap_id")
        if gid in answered_ids:
            transition_qud_status(entry, STATUS_ANSWERED, turn_index)
        elif gid in deflected_ids:
            transition_qud_status(entry, STATUS_DEFLECTED, turn_index)

    # 2. Check if current propositions fill open gaps
    if current_propositions:
        for entry in stack:
            if entry.get("status") == STATUS_OPEN:
                target_frame = str(entry.get("frame_id", "")).lower()
                for prop in current_propositions:
                    pred = str(prop.get("predicate", {}).get("lemma") if isinstance(prop.get("predicate"), dict) else prop.get("predicate", "")).lower()
                    if pred and (pred == target_frame or target_frame in pred):
                        transition_qud_status(entry, STATUS_ANSWERED, turn_index)
                        break

    # 3. Check for supersession from correction context
    if correction_context and correction_context.get("is_correction"):
        superseded_propositions = set(correction_context.get("superseded_propositions", []))
        for entry in stack:
            fid = entry.get("frame_id")
            if fid in superseded_propositions:
                transition_qud_status(entry, STATUS_SUPERSEDED, turn_index)

    # 4. Mark abandoned after untouched threshold
    for entry in stack:
        if entry.get("status") == STATUS_OPEN:
            last_touch = entry.get("last_touched", entry.get("created_turn", turn_index))
            if (turn_index - last_touch) >= abandon_threshold:
                transition_qud_status(entry, STATUS_ABANDONED, turn_index)

    # 5. Merge new gaps pointing at same frame or append new
    existing_by_frame = {e.get("frame_id"): e for e in stack if e.get("status") == STATUS_OPEN}
    existing_by_gap = {e.get("gap_id"): e for e in stack}

    for gap in new_gaps:
        gid = gap.get("gap_id")
        fid = gap.get("evidence", {}).get("clause_id") or gap.get("evidence", {}).get("predicate") or gid
        question_form = format_qud_question(gap)
        spans = gap.get("spans", [])

        # Merge gaps pointing at same frame
        if fid in existing_by_frame:
            existing_entry = existing_by_frame[fid]
            existing_entry["last_touched"] = turn_index
            existing_entry["recurrence_count"] = existing_entry.get("recurrence_count", 1) + 1
            for s in spans:
                if s not in existing_entry.get("spans", []):
                    existing_entry["spans"].append(s)
        elif gid in existing_by_gap:
            existing_entry = existing_by_gap[gid]
            if existing_entry.get("status") == STATUS_DEFLECTED:
                # User unprompted return reopens deflected gap
                transition_qud_status(existing_entry, STATUS_OPEN, turn_index)
                existing_entry.pop("last_asked_turn", None)
            existing_entry["last_touched"] = turn_index
            existing_entry["recurrence_count"] = existing_entry.get("recurrence_count", 1) + 1
        else:
            new_entry = create_qud_entry(
                gap_id=gid,
                neutral_question_form=question_form,
                spans=spans,
                turn_index=turn_index,
                frame_id=fid,
            )
            stack.append(new_entry)
            existing_by_frame[fid] = new_entry
            existing_by_gap[gid] = new_entry

    return stack


def get_active_quds(qud_stack: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return open questions ordered by recency (last_touched desc)."""
    open_entries = [e for e in qud_stack if e.get("status") == STATUS_OPEN]
    return sorted(open_entries, key=lambda e: (-e.get("last_touched", 0), -e.get("created_turn", 0)))
