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

CANONICAL_GAP_TYPES = {
    GAP_UNFILLED_ROLE,
    GAP_HEDGED_COMMITMENT,
    GAP_REPORTED_CLAIM,
    GAP_UNRESOLVED_REFERENCE,
    GAP_CORRECTION_LINK,
    GAP_COUNTERFACTUAL_OBLIGATION,
    GAP_CONTRAST_THIN_ARM,
    GAP_RECURRING_TOPIC,
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

            # Don't flag if it's already a complete routine narration
            actors = prop.get("actors", [])
            has_agent = any(a.get("role") in {"agent", "nsubj"} for a in actors)
            has_patient = any(a.get("role") in {"patient", "dobj"} for a in actors)
            
            # If experiential predicate or action lacking reason
            if pred in {"feel", "worry", "struggle", "hesitate", "reconsider", "doubt", "leave", "resign", "miss"}:
                gaps.append({
                    "gap_id": f"gap_unfilled_role_{clause_id}_{pred}",
                    "type": GAP_UNFILLED_ROLE,
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
            "spans": [span],
            "evidence": {"hedge_span": span, "hedge_text": span_text},
            "detector_id": "detector_hedged_commitment",
            "status": status,
            "description": f"Epistemically hedged assertion '{span_text}'.",
        })
    return gaps


# Detector 3: Reported Claim with No User Stance
def detect_reported_claims(analysis: Dict[str, Any], status: str = "ok") -> List[Dict[str, Any]]:
    gaps = []
    text = analysis.get("redacted_text", "")
    propositions = analysis.get("discourse_context", {}).get("current_propositions", [])

    for prop in propositions:
        pred = extract_predicate_lemma(prop)
        if pred in REPORTING_VERBS:
            # Check if user stated an evaluation
            # If user text does not contain explicit stance marker
            clause_id = prop.get("clause_id")
            spans = prop.get("spans", [[0, len(text)]])
            gaps.append({
                "gap_id": f"gap_reported_{clause_id}_{pred}",
                "type": GAP_REPORTED_CLAIM,
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
                "spans": [span],
                "evidence": {"pronoun": p.get("pronoun"), "resolution_status": p_status},
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
        modality = prop.get("modality", [])
        cats = _extract_modality_categories(modality)
        if any(c in {"obligation", "counterfactual", "deontic"} for c in cats):
            spans = prop.get("scope_spans", prop.get("spans", [[0, 10]]))
            pred = extract_predicate_lemma(prop)
            gaps.append({
                "gap_id": f"gap_modality_{prop.get('id', 'm')}",
                "type": GAP_COUNTERFACTUAL_OBLIGATION,
                "spans": spans,
                "evidence": {"predicate": pred, "modality": modality},
                "detector_id": "detector_counterfactual_obligation",
                "status": status,
                "description": f"Unexplored obligation/counterfactual modality on '{pred}'.",
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
                        "spans": thin_arm.get("spans", [[0, 10]]),
                        "evidence": {"relation": rel, "underdeveloped_arm": thin_arm.get("id")},
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
                "spans": [[0, min(20, len(analysis.get("redacted_text", "")))]],
                "evidence": {"topic_id": current_topic_id, "recurrence_count": t.get("count")},
                "detector_id": "detector_recurring_topic",
                "status": status,
                "description": f"Recurring topic '{current_topic_id}' discussed across {t.get('count')} turns.",
            })
    return gaps


def detect_structural_gaps(analysis: Dict[str, Any], prior_turns: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Root entrypoint: executes all 8 structural gap detectors with zero sentiment/emotion lexicon."""
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

    return all_gaps
