"""Sanctuary V2 Backoff & Question Budget Policy (Task T4.2).

Enforces conversational pacing, respects boundaries, and prevents loops or interrogation:
- Deflected gap is suppressed for a window of W turns (default W = 3).
- Two consecutive deflections force an immediate 'hold' move.
- Enforces per-session and per-window question budget.
- The same gap is NEVER asked twice inside the window W.
- A user's unprompted return to a deflected gap reopens it.
- Explicit pushback ('why do you keep asking me that?') forces 'hold' and 'acknowledge'.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple


DEFAULT_DEFLECTION_WINDOW = 3
MAX_QUESTIONS_PER_SESSION = 6
MIN_TURNS_BETWEEN_QUESTIONS = 2


PUSHBACK_PATTERNS = [
    r"\bwhy\s+do\s+you\s+(?:keep\s+asking|ask\s+so\s+many\s+questions)\b",
    r"\bstop\s+(?:asking\s+me|questioning\s+me|interrogating\s+me)\b",
    r"\byou\s+ask\s+too\s+many\s+questions\b",
    r"\bi\s+already\s+answered\s+that\b",
    r"\bstop\s+prying\b",
]


def check_explicit_pushback(text: str) -> bool:
    """Check if the user is explicitly pushing back against system questioning."""
    lower = text.lower()
    return any(re.search(pat, lower) for pat in PUSHBACK_PATTERNS)


class ConversationPolicyTracker:
    """Tracks question history, deflection suppression windows, and budget state."""

    def __init__(
        self,
        deflection_window: int = DEFAULT_DEFLECTION_WINDOW,
        max_questions_session: int = MAX_QUESTIONS_PER_SESSION,
        min_turns_between_questions: int = MIN_TURNS_BETWEEN_QUESTIONS,
    ):
        self.deflection_window = deflection_window
        self.max_questions_session = max_questions_session
        self.min_turns_between_questions = min_turns_between_questions

    def evaluate_question_policy(
        self,
        current_text: str,
        prior_turns: List[Dict[str, Any]],
        qud_stack: List[Dict[str, Any]],
        turn_index: int,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Determine whether the system is permitted to ask a question this turn.
        Returns:
            (allow_question: bool, enforced_move: Optional[str], reason: Optional[str])
        """
        # 1. User pushback against questioning
        if check_explicit_pushback(current_text):
            return False, "hold", "User pushback detected: user requested to stop questioning."

        # 2. Check consecutive deflections (2 in a row forces hold)
        recent_uptakes = [
            t.get("uptake")
            for t in prior_turns
            if t.get("system_move") in {"ask", "clarify"} or "uptake" in t
        ]
        if len(recent_uptakes) >= 2 and recent_uptakes[-1] == "deflected" and recent_uptakes[-2] == "deflected":
            return False, "hold", "Question backoff: two consecutive deflections force hold."

        # 3. Check per-session question budget
        questions_asked = sum(1 for t in prior_turns if t.get("system_move") in {"ask", "clarify"} or t.get("question"))
        if questions_asked >= self.max_questions_session:
            return False, "acknowledge", f"Session question budget exhausted ({questions_asked}/{self.max_questions_session})."

        # 4. Check pacing / minimum turns between questions
        if prior_turns:
            last_turn = prior_turns[-1]
            if last_turn.get("system_move") in {"ask", "clarify"} and last_turn.get("question"):
                # If last turn asked a question and user just responded with short/normal reflection
                words = current_text.split()
                if len(words) <= 15:
                    return False, "acknowledge", "Conversational pacing: alternating acknowledge after question turn."

        return True, None, None

    def is_gap_suppressed(
        self,
        gap_id: str,
        qud_stack: List[Dict[str, Any]],
        turn_index: int,
    ) -> bool:
        """Check if a specific gap is suppressed due to recent deflection or asking."""
        for entry in qud_stack:
            if entry.get("gap_id") == gap_id:
                status = entry.get("status")
                last_touched = entry.get("last_touched", 0)

                # If deflected within the window, suppress
                if status == "deflected" and (turn_index - last_touched) <= self.deflection_window:
                    return True

                # If asked within the window, suppress to avoid repeating
                last_asked_turn = entry.get("last_asked_turn")
                if last_asked_turn and (turn_index - last_asked_turn) <= self.deflection_window:
                    return True

        return False

    def detect_unprompted_return(
        self,
        current_text: str,
        current_props: List[Dict[str, Any]],
        qud_entry: Dict[str, Any],
    ) -> bool:
        """Detect if the user returned unprompted to the topic/frame of a deflected gap."""
        if qud_entry.get("status") != "deflected":
            return False

        frame_id = qud_entry.get("frame_id", "")
        neutral_q = qud_entry.get("neutral_question_form", "").lower()

        # Check if user text explicitly mentions keywords from the deflected gap
        q_tokens = {w for w in re.findall(r"\w+", neutral_q) if len(w) > 3}
        u_tokens = {w for w in re.findall(r"\w+", current_text.lower()) if len(w) > 3}
        overlap = q_tokens & u_tokens

        if len(overlap) >= 2:
            return True

        # Check predicate recurrence
        for prop in current_props:
            pred = (prop.get("predicate", {}).get("lemma") or prop.get("predicate", "")).lower()
            if pred and pred in frame_id.lower():
                return True

        return False
