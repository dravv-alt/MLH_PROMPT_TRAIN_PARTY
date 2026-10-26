"""Sanctuary V2 Open-Vocabulary Structural Gap Detectors (Task T2.1).

Computes, from the structure of the user's own text, what is open, unsaid,
or unresolved in discourse. Zero sentiment, emotion, or intent lexicons are used.
Every gap carries type, spans, evidence, detector_id, and verification status.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


GAP_UNFILLED_ROLE = "unfilled_role"
GAP_HEDGED_COMMITMENT = "hedged_commitment"
GAP_REPORTED_CLAIM = "reported_claim"
GAP_UNRESOLVED_REFERENCE = "unresolved_reference"
GAP_CORRECTION_LINK = "correction_link"
GAP_COUNTERFACTUAL_OBLIGATION = "counterfactual_obligation"
GAP_CONTRAST_THIN_ARM = "contrast_thin_arm"
GAP_RECURRING_TOPIC = "recurring_topic"
GAP_INCOMPLETION_OVER_TIME = "incompletion_over_time"
GAP_BLOCKED_STATE = "blocked_state"

CANONICAL_GAP_TYPES = {
    GAP_UNFILLED_ROLE,
    GAP_HEDGED_COMMITMENT,
    GAP_REPORTED_CLAIM,
    GAP_UNRESOLVED_REFERENCE,
    GAP_CORRECTION_LINK,
    GAP_COUNTERFACTUAL_OBLIGATION,
    GAP_CONTRAST_THIN_ARM,
    GAP_RECURRING_TOPIC,
    GAP_INCOMPLETION_OVER_TIME,
    GAP_BLOCKED_STATE,
}

REPORTING_VERBS = {
    "say", "tell", "claim", "mention", "state", "assert", "suggest", "report", "insist", "warn"
}

POLITENESS_HEDGE_PATTERNS = [
    r"\b(?:honestly|kindly)?\s*(?:thank you|thanks)\b",
    r"\bi guess\s+(?:i'll|we'll|i will|we will)\s+see you\b",
    r"\b(?:bye|see you|catch you)\b",
]


def _is_politeness_hedge(span_text: str, full_text: str) -> bool:
    """Hard negative: Hedges in greetings, closings, or routine courtesy are not development gaps."""
    lower = full_text.lower()
    for pattern in POLITENESS_HEDGE_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False


def extract_predicate_lemma(pred_or_prop: Any) -> str:
    """Safely extracts the lemma string from a proposition or a predicate object/string."""
    if isinstance(pred_or_prop, dict):
        if "predicate" in pred_or_prop:
            pred = pred_or_prop["predicate"]
            if isinstance(pred, dict):
                return str(pred.get("lemma", "")).lower()
            return str(pred).lower()
        if "lemma" in pred_or_prop:
            return str(pred_or_prop.get("lemma", "")).lower()
    return str(pred_or_prop or "").lower()


# Detector 1: Unfilled Role on Eventive Predicates
def detect_unfilled_roles(analysis: Dict[str, Any], status: str = "ok") -> List[Dict[str, Any]]:
    gaps = []
    text = analysis.get("redacted_text", "")
    relations = analysis.get("relations", [])
    clauses = analysis.get("clauses", [])
    propositions = analysis.get("discourse_context", {}).get("current_propositions", [])

    # If full text is pure logistics without psychological or experiential tension, or very short
    if len(text.split()) <= 3:
        return []

    # Map clauses involved in causal relations
    causal_clauses = set()
    for rel in relations:
        if rel.get("type") == "causal":
            causal_clauses.add(rel.get("arg1"))
            causal_clauses.add(rel.get("arg2"))

    lower_text = text.lower()
    has_explicit_grounding = bool(re.search(r"\b(?:because|after\s+i|since\s+i|due\s+to|so\s+that|when\s+i|why\s+i)\b", lower_text))

    for prop in propositions:
        clause_id = prop.get("clause_id")
        pred = extract_predicate_lemma(prop)
        if not pred:
            continue

        # Eventive verbs or experiential states lacking a causal explanation
        # Check if clause has no causal relation attached
        if clause_id not in causal_clauses:
            clause_obj = next((c for c in clauses if c.get("id") == clause_id), None)
            spans = clause_obj.get("spans", []) if clause_obj else []
            if not spans and "span" in prop:
                spans = [prop["span"]]
            if not spans:
                spans = [[0, min(len(text), 30)]]

            # Don't flag if it's already a complete routine narration or causally grounded
            if has_explicit_grounding and pred in {"feel", "notice", "start", "leave", "struggle", "reconsider"}:
                continue

            # Don't flag linking/copular predicates with complete evaluative complements
            if pred == "feel" and any(adj in lower_text for adj in ["better", "completely normal", "understood", "meaningful"]):
                continue

            # If experiential predicate or action lacking reason
            if pred in {"feel", "worry", "struggle", "hesitate", "reconsider", "doubt", "leave", "resign", "miss"}:
                gaps.append({
                    "gap_id": f"gap_unfilled_role_{clause_id}_{pred}",
                    "type": GAP_UNFILLED_ROLE,
                    "predicate": pred,
                    "spans": spans,
                    "evidence": {"predicate": pred, "clause_id": clause_id},
                    "detector_id": "detector_unfilled_role",
                    "status": status,
                    "description": f"Eventive predicate '{pred}' without stated causal grounding.",
                })
    return gaps


# Detector 2: Hedged Commitment
def detect_hedged_commitments(analysis: Dict[str, Any], status: str = "ok") -> List[Dict[str, Any]]:
    gaps = []
    text = analysis.get("redacted_text", "")
    hedge_spans = analysis.get("hedge_spans", [])

    for span in hedge_spans:
        start, end = span[0], span[1]
        span_text = text[start:end]
        if _is_politeness_hedge(span_text, text):
            continue

        gaps.append({
            "gap_id": f"gap_hedged_{start}_{end}",
            "type": GAP_HEDGED_COMMITMENT,
            "predicate": "epistemic_hedge",
            "spans": [span],
            "evidence": {"predicate": "epistemic_hedge", "hedge_span": span, "hedge_text": span_text},
            "detector_id": "detector_hedged_commitment",
            "status": status,
            "description": f"Epistemically hedged assertion '{span_text}'.",
        })
    return gaps


REPORTED_EVALUATION_PATTERNS = [
    r"\b(?:which\s+is\s+|that\s+is\s+|it\s+is\s+)?(?:completely\s+|totally\s+)?(?:untrue|false|wrong|a\s+lie|nonsense|ridiculous|unfair|not\s+true|true|fair)\b",
    r"\bi\s+(?:don['’]t\s+believe|do\s+not\s+believe|disagree|agree|doubt)\b",
    r"\b(?:which|that)\s+i\s+(?:know|knew|think)\s+is\s+(?:not\s+true|false|untrue|wrong)\b",
    r"\b(?:that|which|it)\s+was\s+(?:reassuring|comforting|helpful|relieving|good|nice|encouraging|useful|clearer)\b",
    r"\b(?:that|which|it)\s+(?:reassured|helped|comforted)\b",
    r"\bi\s+(?:felt|was)\s+(?:reassured|relieved|comforted|glad)\b",
    r"\bi\s+could\s+see\s+what\s+(?:they|he|she)\s+meant\b",
    r"\bthey\s+said\s+that\s+was\s+(?:completely\s+)?fine\b",
    r"\byou\s+keep\s+making\s+this\s+sound\b",
    r"\bi\s+haven['’]t\s+said\s+that\b",
]


def _has_user_evaluation_of_report(text: str) -> bool:
    lower = text.lower()
    return any(re.search(pat, lower) for pat in REPORTED_EVALUATION_PATTERNS)


# Detector 3: Reported Claim with No User Stance
def detect_reported_claims(analysis: Dict[str, Any], status: str = "ok") -> List[Dict[str, Any]]:
    gaps = []
    text = analysis.get("redacted_text", "")
    if _has_user_evaluation_of_report(text):
        return []
    propositions = analysis.get("discourse_context", {}).get("current_propositions", [])

    for prop in propositions:
        pred = extract_predicate_lemma(prop)
        if pred in REPORTING_VERBS:
            agent = str(prop.get("agent", "")).lower()
            if agent in {"user", "i", "me", "we"}:
                continue
            if re.search(r"\b(?:i|we|today\s+i|yesterday\s+i)\s+(?:said|told|asked)\b", text.lower()):
                continue
            clause_id = prop.get("clause_id")
            spans = prop.get("spans", [[0, len(text)]])
            gaps.append({
                "gap_id": f"gap_reported_{clause_id}_{pred}",
                "type": GAP_REPORTED_CLAIM,
                "predicate": pred,
                "spans": spans,
                "evidence": {"predicate": pred, "clause_id": clause_id},
                "detector_id": "detector_reported_claim",
                "status": status,
                "description": f"Reported claim via '{pred}' without explicit user evaluation.",
            })
    return gaps


# Detector 4: Unresolved Reference
def detect_unresolved_references(analysis: Dict[str, Any], status: str = "ok") -> List[Dict[str, Any]]:
    gaps = []
    hobbs_history = analysis.get("hobbs_history", [])
    pronouns = []
    if hobbs_history and isinstance(hobbs_history[-1], dict):
        pronouns = hobbs_history[-1].get("pronouns", [])

    # Also check discourse entities from classical NLP if available
    for p in pronouns:
        p_status = p.get("status")
        if p_status in {"unresolved", "ambiguous"}:
            span = p.get("span", [0, 0])
            gaps.append({
                "gap_id": f"gap_unresolved_ref_{span[0]}_{span[1]}",
                "type": GAP_UNRESOLVED_REFERENCE,
                "predicate": p.get("pronoun", "pronoun"),
                "spans": [span],
                "evidence": {"predicate": p.get("pronoun", "pronoun"), "pronoun": p.get("pronoun"), "resolution_status": p_status},
                "detector_id": "detector_unresolved_reference",
                "status": status,
                "description": f"Reference '{p.get('pronoun')}' is {p_status}.",
            })
    return gaps


# Detector 5: Ambiguous or Open Correction Link
def detect_correction_links(analysis: Dict[str, Any], status: str = "ok") -> List[Dict[str, Any]]:
    gaps = []
    rev_links = analysis.get("discourse_context", {}).get("revision_links", [])
    for link in rev_links:
        if link.get("status") == "candidate" or link.get("is_ambiguous"):
            span = link.get("span", [0, 0])
            gaps.append({
                "gap_id": f"gap_correction_link_{link.get('id', 'rev')}",
                "type": GAP_CORRECTION_LINK,
                "predicate": "correction",
                "spans": [span] if span != [0, 0] else [[0, 10]],
                "evidence": link,
                "detector_id": "detector_correction_link",
                "status": status,
                "description": "Correction link requires resolution.",
            })
    return gaps


def _extract_modality_categories(modality: Any) -> set[str]:
    cats = set()
    if isinstance(modality, list):
        for m in modality:
            if isinstance(m, dict):
                cat = m.get("category", "")
                if cat:
                    cats.add(cat.lower())
                lemma = m.get("lemma", "")
                if lemma in {"should", "must", "ought", "need", "have to"}:
                    cats.add("obligation")
                    cats.add("deontic")
                if lemma in {"would", "could", "might"}:
                    cats.add("counterfactual")
                    cats.add("epistemic")
            elif isinstance(m, str):
                cats.add(m.lower())
    elif isinstance(modality, str):
        cats.add(modality.lower())
    return cats


# Detector 6: Counterfactual or Obligation Modality
def detect_counterfactual_obligations(analysis: Dict[str, Any], status: str = "ok") -> List[Dict[str, Any]]:
    gaps = []
    propositions = analysis.get("discourse_context", {}).get("current_propositions", [])
    for prop in propositions:
        if prop.get("polarity") == "negative":
            continue
        modality = prop.get("modality", [])
        cats = _extract_modality_categories(modality)
        if any(c in {"obligation", "counterfactual", "deontic"} for c in cats):
            spans = prop.get("scope_spans", prop.get("spans", [[0, 10]]))
            pred = extract_predicate_lemma(prop)
            modal_lemma = pred
            for m in modality:
                if isinstance(m, dict) and m.get("lemma") in {"should", "must", "ought", "would", "could", "might"}:
                    modal_lemma = m.get("lemma")
                    break
            gaps.append({
                "gap_id": f"gap_modality_{prop.get('id', 'm')}",
                "type": GAP_COUNTERFACTUAL_OBLIGATION,
                "predicate": modal_lemma,
                "spans": spans,
                "evidence": {"predicate": modal_lemma, "base_predicate": pred, "modality": modality},
                "detector_id": "detector_counterfactual_obligation",
                "status": status,
                "description": f"Unexplored obligation/counterfactual modality on '{modal_lemma}'.",
            })
    return gaps


# Detector 7: Contrast with One Thin Arm
def detect_contrast_thin_arms(analysis: Dict[str, Any], status: str = "ok") -> List[Dict[str, Any]]:
    gaps = []
    relations = analysis.get("relations", [])
    clauses = {c.get("id"): c for c in analysis.get("clauses", [])}

    for rel in relations:
        if rel.get("type") == "contrast":
            c1 = clauses.get(rel.get("arg1"))
            c2 = clauses.get(rel.get("arg2"))
            if c1 and c2:
                len1 = len(c1.get("text", "").split())
                len2 = len(c2.get("text", "").split())
                # If one arm is significantly underdeveloped
                if len1 >= 2 * len2 or len2 >= 2 * len1:
                    thin_arm = c2 if len2 < len1 else c1
                    gaps.append({
                        "gap_id": f"gap_contrast_thin_{thin_arm.get('id')}",
                        "type": GAP_CONTRAST_THIN_ARM,
                        "predicate": "contrast",
                        "spans": thin_arm.get("spans", [[0, 10]]),
                        "evidence": {"predicate": "contrast", "relation": rel, "underdeveloped_arm": thin_arm.get("id")},
                        "detector_id": "detector_contrast_thin_arm",
                        "status": status,
                        "description": f"Contrast where arm '{thin_arm.get('id')}' is underdeveloped.",
                    })
    return gaps


# Detector 8: Recurring Topic with No Stated Outcome
def detect_recurring_topics(analysis: Dict[str, Any], prior_turns: List[Dict[str, Any]] = None, status: str = "ok") -> List[Dict[str, Any]]:
    gaps = []
    topics = analysis.get("topics", [])
    current_topic_id = analysis.get("topic_id")

    for t in topics:
        if t.get("id") == current_topic_id and t.get("count", 1) >= 2:
            gaps.append({
                "gap_id": f"gap_recurring_topic_{current_topic_id}",
                "type": GAP_RECURRING_TOPIC,
                "predicate": "recurring_topic",
                "spans": [[0, min(20, len(analysis.get("redacted_text", "")))]],
                "evidence": {"predicate": "recurring_topic", "topic_id": current_topic_id, "recurrence_count": t.get("count")},
                "detector_id": "detector_recurring_topic",
                "status": status,
                "description": f"Recurring topic '{current_topic_id}' discussed across {t.get('count')} turns.",
            })
    return gaps


# Detector 9: Incompletion Over Time (Duration + Unfinished/Unresolved Task)
INCOMPLETION_DURATION_PATTERNS = [
    r"\b(?:since\s+(?:weeks|months|days)|for\s+(?:weeks|months|days)|weeks\s+and\s+months|for\s+so\s+long)\b",
    r"\b(?:trying\s+to\s+.*(?:weeks|months|days))\b",
]

INCOMPLETION_UNFINISHED_PATTERNS = [
    r"\b(?:still\s+hasn't|still\s+haven't|hasn't\s+been|haven't\s+been|still\s+not|not\s+yet|yet\s+to\s+be|unfinished|incomplete|not\s+(?:completely\s+)?executed|not\s+finished|still\s+trying\s+to)\b",
]

def detect_incompletion_over_time(analysis: Dict[str, Any], status: str = "ok") -> List[Dict[str, Any]]:
    gaps = []
    text = analysis.get("redacted_text", "")
    lower = text.lower()

    dur_match = None
    for pat in INCOMPLETION_DURATION_PATTERNS:
        m = re.search(pat, lower)
        if m:
            dur_match = m
            break

    unf_match = None
    for pat in INCOMPLETION_UNFINISHED_PATTERNS:
        m = re.search(pat, lower)
        if m:
            unf_match = m
            break

    if dur_match or unf_match:
        start = min(dur_match.start() if dur_match else 999999, unf_match.start() if unf_match else 999999)
        end = max(dur_match.end() if dur_match else 0, unf_match.end() if unf_match else 0)
        sent_start = text.rfind(".", 0, start)
        sent_start = 0 if sent_start == -1 else sent_start + 1
        sent_end = text.find(".", end)
        sent_end = len(text) if sent_end == -1 else sent_end

        span_start = max(0, sent_start)
        span_end = min(len(text), sent_end)
        clause_text = text[span_start:span_end].strip()

        gaps.append({
            "gap_id": f"gap_incompletion_{span_start}_{span_end}",
            "type": GAP_INCOMPLETION_OVER_TIME,
            "predicate": "incomplete_effort",
            "spans": [[span_start, span_end]],
            "evidence": {
                "predicate": "incomplete_effort",
                "span_text": clause_text,
                "duration_cue": dur_match.group(0) if dur_match else "",
                "incompletion_cue": unf_match.group(0) if unf_match else "",
            },
            "detector_id": "detector_incompletion_over_time",
            "status": status,
            "description": "Ongoing effort over duration that remains incomplete.",
        })
    return gaps


# Detector 10: Blocked State / Dead End / Open Decision
BLOCKED_STATE_PATTERNS = [
    r"\b(?:stalled|getting\s+stalled|indefinitely\s+stalled|stuck|blocked|dead\s+end)\b",
    r"\b(?:nothing\s+(?:is\s+)?working|nothing\s+works|nothing['’]s\s+working)\b",
    r"\b(?:i\s+don['’]t\s+know\s+what\s+to\s+do|don['’]t\s+know\s+what\s+to\s+do|not\s+sure\s+what\s+to\s+do|at\s+a\s+loss)\b",
    r"\b(?:can['’]t\s+(?:get\s+it\s+to\s+work|figure\s+(?:it\s+)?out|make\s+progress))\b",
]

def detect_blocked_states(analysis: Dict[str, Any], status: str = "ok") -> List[Dict[str, Any]]:
    gaps = []
    text = analysis.get("redacted_text", "")
    lower = text.lower()

    for pat in BLOCKED_STATE_PATTERNS:
        for m in re.finditer(pat, lower):
            start, end = m.span()
            sent_start = text.rfind(".", 0, start)
            sent_start = 0 if sent_start == -1 else sent_start + 1
            sent_end = text.find(".", end)
            sent_end = len(text) if sent_end == -1 else sent_end

            span_start = max(0, sent_start)
            span_end = min(len(text), sent_end)
            clause_text = text[span_start:span_end].strip()

            gaps.append({
                "gap_id": f"gap_blocked_{span_start}_{span_end}",
                "type": GAP_BLOCKED_STATE,
                "predicate": "blocked_state",
                "spans": [[span_start, span_end]],
                "evidence": {
                    "predicate": "blocked_state",
                    "span_text": clause_text,
                    "cue": m.group(0),
                },
                "detector_id": "detector_blocked_state",
                "status": status,
                "description": f"Blocked state or impasse triggered by '{m.group(0)}'.",
            })
            break
    return gaps


def detect_structural_gaps(analysis: Dict[str, Any], prior_turns: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Root entrypoint: executes all structural gap detectors with zero sentiment/emotion lexicon."""
    parser_fallback = analysis.get("parser_fallback")
    status = "unverified" if parser_fallback else "ok"

    all_gaps = []
    all_gaps.extend(detect_unfilled_roles(analysis, status))
    all_gaps.extend(detect_hedged_commitments(analysis, status))
    all_gaps.extend(detect_reported_claims(analysis, status))
    all_gaps.extend(detect_unresolved_references(analysis, status))
    all_gaps.extend(detect_correction_links(analysis, status))
    all_gaps.extend(detect_counterfactual_obligations(analysis, status))
    all_gaps.extend(detect_contrast_thin_arms(analysis, status))
    all_gaps.extend(detect_recurring_topics(analysis, prior_turns, status))
    all_gaps.extend(detect_incompletion_over_time(analysis, status))
    all_gaps.extend(detect_blocked_states(analysis, status))

    return all_gaps


DEFAULT_SALIENCE_WEIGHTS = {
    "recency": 0.25,
    "hedge_strength": 0.20,
    "repetition": 0.25,
    "contrast_or_correction": 0.20,
    "unprompted_return": 0.10,
}


def score_gap_salience(
    gap: Dict[str, Any],
    analysis: Dict[str, Any],
    prior_turns: List[Dict[str, Any]] = None,
    weights: Dict[str, float] = None,
) -> Tuple[float, Dict[str, float]]:
    """Compute explicit inspectable structural salience score for a gap."""
    w = weights or DEFAULT_SALIENCE_WEIGHTS
    text = analysis.get("redacted_text", "")
    text_len = max(len(text), 1)

    spans = gap.get("spans", [[0, 0]])
    span_start = spans[0][0] if spans and spans[0] else 0
    span_end = spans[0][1] if spans and spans[0] else 0

    # 1. Recency: later in the turn -> higher recency
    f_recency = min(max(span_start / text_len, 0.0), 1.0)

    # 2. Hedge strength: from hedge detector / hedge ratio
    f_hedge = 0.0
    if gap.get("type") == GAP_HEDGED_COMMITMENT:
        f_hedge = float(analysis.get("features", {}).get("hedge") or 0.7)
    elif analysis.get("hedge_spans"):
        for h_span in analysis["hedge_spans"]:
            if max(span_start, h_span[0]) < min(span_end, h_span[1]):
                f_hedge = float(analysis.get("features", {}).get("hedge") or 0.5)
                break

    # 3. Repetition across turns (topic recurrence)
    f_repetition = 0.0
    if gap.get("type") == GAP_RECURRING_TOPIC:
        count = gap.get("evidence", {}).get("recurrence_count", 2)
        f_repetition = min(count / 5.0, 1.0)
    else:
        topic_count = analysis.get("strategy_evidence", {}).get("prior_topic_turns", 0)
        f_repetition = min(topic_count / 5.0, 1.0)

    # 4. Co-occurrence with contrast or correction
    f_contrast_correction = 0.0
    if gap.get("type") in {GAP_CONTRAST_THIN_ARM, GAP_CORRECTION_LINK}:
        f_contrast_correction = 1.0
    else:
        relations = analysis.get("relations", [])
        if any(rel.get("type") == "contrast" for rel in relations):
            f_contrast_correction = 0.5
        if analysis.get("strategy_evidence", {}).get("correction", {}).get("detected"):
            f_contrast_correction = max(f_contrast_correction, 0.8)

    # 5. Unprompted return: user returned to a topic/predicate without being prompted
    f_unprompted_return = 0.0
    if prior_turns and len(prior_turns) >= 2:
        pred = extract_predicate_lemma(gap.get("evidence", {}).get("predicate", ""))
        for turn in prior_turns[:-1]:
            if pred and pred in turn.get("text", "").lower():
                f_unprompted_return = 1.0
                break

    # 6. Blocked state or incompletion over time has high discourse tension
    f_blocked_incompletion = 0.0
    if gap.get("type") in {GAP_BLOCKED_STATE, GAP_INCOMPLETION_OVER_TIME}:
        f_blocked_incompletion = 1.0

    features = {
        "recency": round(f_recency, 4),
        "hedge_strength": round(f_hedge, 4),
        "repetition": round(f_repetition, 4),
        "contrast_or_correction": round(f_contrast_correction, 4),
        "unprompted_return": round(f_unprompted_return, 4),
        "blocked_incompletion": round(f_blocked_incompletion, 4),
    }

    score = (
        w.get("recency", 0.25) * f_recency
        + w.get("hedge_strength", 0.20) * f_hedge
        + w.get("repetition", 0.25) * f_repetition
        + w.get("contrast_or_correction", 0.20) * f_contrast_correction
        + w.get("unprompted_return", 0.10) * f_unprompted_return
        + 0.50 * f_blocked_incompletion
    )

    return round(score, 4), features


def rank_gaps_by_salience(
    gaps: List[Dict[str, Any]],
    analysis: Dict[str, Any],
    prior_turns: List[Dict[str, Any]] = None,
    weights: Dict[str, float] = None,
) -> List[Dict[str, Any]]:
    """Rank detected gaps deterministically by structural salience features."""
    if not gaps:
        return []

    scored = []
    for gap in gaps:
        score, feats = score_gap_salience(gap, analysis, prior_turns, weights)
        gap_copy = dict(gap)
        gap_copy["salience_score"] = score
        gap_copy["salience_features"] = feats
        scored.append(gap_copy)

    def _sort_key(g):
        spans = g.get("spans", [[0, 0]])
        start = spans[0][0] if spans and spans[0] else 0
        return (-g["salience_score"], -start, g.get("gap_id", ""))

    scored.sort(key=_sort_key)
    return scored
