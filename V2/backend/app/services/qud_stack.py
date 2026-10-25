"""Sanctuary V2 Question Under Discussion (QUD) Stack (Task T2.3).

Maintains a persistent list of open discourse questions raised by structural gaps.
Stored entirely within the existing session state JSON snapshot (no new tables).
Enforces valid status transitions, frame merging, and supersession updates.
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


def merge_and_update_qud_stack(
    qud_stack: List[Dict[str, Any]],
    new_gaps: List[Dict[str, Any]],
    turn_index: int,
    correction_context: Optional[Dict[str, Any]] = None,
    answered_gap_ids: Optional[Set[str]] = None,
    deflected_gap_ids: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """Update the QUD stack across turns:
    1. Mark answered or deflected gaps from uptake classifier
    2. Mark superseded gaps if correction retracted the base frame
    3. Merge new gaps targeting existing active frames
    4. Append newly raised gaps
    """
    stack = copy.deepcopy(qud_stack or [])
    answered_ids = answered_gap_ids or set()
    deflected_ids = deflected_gap_ids or set()

    # 1. Apply uptake updates to existing stack
    for entry in stack:
        gid = entry.get("gap_id")
        if gid in answered_ids:
            transition_qud_status(entry, STATUS_ANSWERED, turn_index)
        elif gid in deflected_ids:
            transition_qud_status(entry, STATUS_DEFLECTED, turn_index)

    # 2. Check for supersession from correction context
    if correction_context and correction_context.get("is_correction"):
        superseded_propositions = set(correction_context.get("superseded_propositions", []))
        for entry in stack:
            fid = entry.get("frame_id")
            if fid in superseded_propositions:
                transition_qud_status(entry, STATUS_SUPERSEDED, turn_index)

    # 3. Merge new gaps pointing at same frame or append new
    existing_by_frame = {e.get("frame_id"): e for e in stack if e.get("status") == STATUS_OPEN}
    existing_by_gap = {e.get("gap_id"): e for e in stack}

    for gap in new_gaps:
        gid = gap.get("gap_id")
        fid = gap.get("evidence", {}).get("clause_id") or gap.get("evidence", {}).get("predicate") or gid
        question_form = gap.get("neutral_question_form") or f"Could you share more about {gap.get('description', 'that')}?"
        spans = gap.get("spans", [])

        # Hard negative check: Merge gaps pointing at same frame
        if fid in existing_by_frame:
            existing_entry = existing_by_frame[fid]
            existing_entry["last_touched"] = turn_index
            # Combine spans without duplicates
            for s in spans:
                if s not in existing_entry.get("spans", []):
                    existing_entry["spans"].append(s)
        elif gid in existing_by_gap:
            existing_entry = existing_by_gap[gid]
            if existing_entry.get("status") == STATUS_DEFLECTED:
                # User unprompted return reopens deflected gap
                transition_qud_status(existing_entry, STATUS_OPEN, turn_index)
            existing_entry["last_touched"] = turn_index
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
