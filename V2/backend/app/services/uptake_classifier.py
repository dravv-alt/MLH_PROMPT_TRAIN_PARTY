"""Sanctuary V2 Uptake Classifier (Task T4.1).

Relates the user's turn to the system's previous question as:
- 'answered': new frames fill the targeted gap role/predicate with discourse continuity.
- 'partial': engaged but unresolved (e.g. 'I don't know', 'hard to say') or partial detail.
- 'deflected': user refuses or avoids the question ('leave it', 'don't want to talk about that', sarcasm).
- 'shifted': user shifts topic ('anyway', 'moving on', or disjoint topic movement).
- 'none': no prior system question was asked (e.g. turn 1 or after acknowledge/hold).

Enforces open-vocabulary principle: uses structural frame overlap, Centering/Hobbs continuity,
closed-class deflection cues, and topic assignment. Zero emotion/sentiment lexicon.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.gaps import extract_predicate_lemma


UPTAKE_ANSWERED = "answered"
UPTAKE_PARTIAL = "partial"
UPTAKE_DEFLECTED = "deflected"
UPTAKE_SHIFTED = "shifted"
UPTAKE_NONE = "none"

# Closed-class deflection cues (pragmatic boundaries, resistance to questioning)
EXPLICIT_DEFLECTION_PATTERNS = [
    r"\b(?:leave\s+it|drop\s+it|skip\s+it|never\s+mind)\b",
    r"\bi\s+don['’]t\s+want\s+to\s+talk\s+about\s+(?:that|it|this)\b",
    r"\bi['’]d\s+rather\s+not\s+(?:say|discuss|talk|answer)\b",
    r"\bnone\s+of\s+your\s+business\b",
    r"\bwhy\s+(?:do\s+you\s+care|are\s+you\s+asking|do\s+you\s+ask|do\s+you\s+keep\s+asking)\b",
    r"\bstop\s+(?:asking|interrogating|questioning)\b",
    r"\b(?:whatever|who\s+cares)\b",
    r"\b(?:chhod\s+na|chodo|nahi\s+baat\s+karni|mat\s+poocho)\b",  # Hindi-English code-mixed deflection
]

# Engaged but unresolved / partial markers (NOT deflection, NOT fully answered)
ENGAGED_UNRESOLVED_PATTERNS = [
    r"\bi\s+(?:don['’]t\s+know|do\s+not\s+know|dunno)\b",
    r"\bi\s+can['’]t\s+(?:really\s+)?tell\b",
    r"\bi['’]m\s+not\s+(?:entirely\s+)?sure\b",
    r"\bhard\s+to\s+(?:say|explain|tell)\b",
    r"\bi\s+haven['’]t\s+thought\s+about\s+(?:that|it)\b",
    r"\bno\s+idea\b",
    r"\b(?:pata\s+nahi|malum\s+nahi)\b",  # Hinglish: I don't know
]

# Explicit topic shift markers
TOPIC_SHIFT_PATTERNS = [
    r"\b(?:anyway|anyways|moving\s+on|on\s+another\s+note|unrelated\s+but|different\s+topic)\b",
    r"\blet['’]s\s+talk\s+about\s+something\s+else\b",
    r"\bforget\s+(?:that|about\s+that)\b",
]


def classify_answer_uptake(
    current_analysis: Dict[str, Any],
    last_system_turn: Optional[Dict[str, Any]],
    current_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Classify the user's uptake of the system's previous question.
    Returns:
    {
        'uptake': 'answered' | 'partial' | 'deflected' | 'shifted' | 'none',
        'targeted_gap_id': Optional[str],
        'continuity_score': float,
        'reason': str,
    }
    """
    text = (current_text or current_analysis.get("redacted_text", "")).strip()
    lower = text.lower()

    # If no prior system question, uptake is none
    if not last_system_turn:
        return {
            "uptake": UPTAKE_NONE,
            "targeted_gap_id": None,
            "continuity_score": 0.0,
            "reason": "No previous system turn.",
        }

    last_move = last_system_turn.get("move")
    last_question = last_system_turn.get("question") or last_system_turn.get("selected_question")
    target_gap_id = last_system_turn.get("targeted_gap_id") or last_system_turn.get("gap_id")

    if last_move not in {"ask", "clarify"} or not last_question:
        return {
            "uptake": UPTAKE_NONE,
            "targeted_gap_id": None,
            "continuity_score": 0.0,
            "reason": f"Previous move '{last_move}' was not a question.",
        }

    # 1. Explicit Deflection Check
    for pat in EXPLICIT_DEFLECTION_PATTERNS:
        if re.search(pat, lower):
            return {
                "uptake": UPTAKE_DEFLECTED,
                "targeted_gap_id": target_gap_id,
                "continuity_score": 0.0,
                "reason": f"Explicit deflection cue detected: '{pat}'.",
            }

    # 2. Counter-Question (user questions the system back without answering)
    if text.endswith("?") and not any(ans in lower for ans in ["because", "since", "well", "actually"]):
        if re.match(r"^(?:why|what|how|who|where|are\s+you|do\s+you)\b", lower):
            return {
                "uptake": UPTAKE_DEFLECTED,
                "targeted_gap_id": target_gap_id,
                "continuity_score": 0.1,
                "reason": "User responded with a counter-question.",
            }

    # 3. Explicit Topic Shift Check
    for pat in TOPIC_SHIFT_PATTERNS:
        if re.search(pat, lower):
            return {
                "uptake": UPTAKE_SHIFTED,
                "targeted_gap_id": target_gap_id,
                "continuity_score": 0.0,
                "reason": f"Explicit topic shift marker detected: '{pat}'.",
            }

    # 4. Engaged but Unresolved ("I don't know") -> Partial Uptake
    for pat in ENGAGED_UNRESOLVED_PATTERNS:
        if re.search(pat, lower):
            # If the user also continues with elaboration, assess further, otherwise partial
            words = text.split()
            if len(words) <= 12:
                return {
                    "uptake": UPTAKE_PARTIAL,
                    "targeted_gap_id": target_gap_id,
                    "continuity_score": 0.5,
                    "reason": "Engaged but unresolved expression (e.g. 'I don't know'); gap remains open.",
                }

    # 5. Structural Frame & Role Continuity
    current_props = current_analysis.get("discourse_context", {}).get("current_propositions", [])
    target_frame = last_system_turn.get("target_frame") or last_system_turn.get("target_predicate")

    q_words = set(re.findall(r"\w+", last_question.lower()))
    u_words = set(re.findall(r"\w+", lower))
    lexical_overlap = len(q_words & u_words)

    # Check Centering / Anaphora Continuity
    centering = current_analysis.get("centering", {})
    trace = centering.get("trace", [])
    has_anaphora_continuity = False
    if trace:
        last_step = trace[-1]
        transition = last_step.get("transition", "")
        if transition in {"CONTINUE", "RETAIN", "SMOOTH-SHIFT"}:
            has_anaphora_continuity = True

    # Check whether new propositions fill the target predicate
    target_pred_filled = False
    if target_frame:
        target_lemma = extract_predicate_lemma(target_frame).lower()
        for p in current_props:
            p_pred = extract_predicate_lemma(p).lower()
            if p_pred == target_lemma or target_lemma in p.get("text", "").lower():
                target_pred_filled = True
                break

    # Check presence of causal/explanatory expansion in response
    has_causal_reason = bool(re.search(r"\b(?:because|since|due\s+to|so\s+that|when|after|so)\b", lower))
    has_substantive_elaboration = len(text.split()) >= 6 and (has_causal_reason or lexical_overlap >= 2 or target_pred_filled)

    # Score continuity
    score = 0.0
    if target_pred_filled:
        score += 0.4
    if lexical_overlap >= 2:
        score += 0.3
    if has_anaphora_continuity:
        score += 0.2
    if has_causal_reason:
        score += 0.2

    score = min(1.0, score)

    # Decision logic
    if target_pred_filled or score >= 0.5 or has_substantive_elaboration:
        return {
            "uptake": UPTAKE_ANSWERED,
            "targeted_gap_id": target_gap_id,
            "continuity_score": round(score, 2),
            "reason": "New proposition frames or substantive elaboration addressed the targeted gap.",
        }
    elif score >= 0.2 or len(text.split()) >= 4:
        return {
            "uptake": UPTAKE_PARTIAL,
            "targeted_gap_id": target_gap_id,
            "continuity_score": round(score, 2),
            "reason": "Partial elaboration; some topical continuity but target gap role remains open.",
        }
    else:
        # Check topic movement from semantic topic assigner if disjoint
        curr_topic = current_analysis.get("semantic_topic")
        prev_topic = last_system_turn.get("semantic_topic")
        if curr_topic and prev_topic and curr_topic != prev_topic:
            return {
                "uptake": UPTAKE_SHIFTED,
                "targeted_gap_id": target_gap_id,
                "continuity_score": round(score, 2),
                "reason": "Semantic topic assignment shifted without answering previous question.",
            }
        return {
            "uptake": UPTAKE_DEFLECTED,
            "targeted_gap_id": target_gap_id,
            "continuity_score": round(score, 2),
            "reason": "Minimal utterance lacking continuity with previous question.",
        }
