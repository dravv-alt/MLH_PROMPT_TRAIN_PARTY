"""Sanctuary V2 Presupposition Filter (Task T3.3).

Enforces that candidate questions take for granted ONLY facts that the user has
explicitly asserted in discourse commitments or spans.
Extracts presupposition triggers (wh-questions, factives, change-of-state verbs,
iteratives, definite descriptions) and verifies licensing.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.services.gaps import extract_predicate_lemma


PRESUPPOSITION_PATTERNS = [
    # Wh-causative / factive / action (matches any subject)
    (r"\bwhy\s+(?:did|does|do|is|are|was|were|has|have|had|would|could|should)\s+([^?]+)", "wh_action"),
    (r"\bwhat\s+((?:made|caused)\s+[^?]+)", "causative_factive"),
    (r"\bwho\s+((?:forced|compelled|pressured|pushed|ordered|told)\s+[^?]+)", "coercive_who"),
    (r"\bhow\s+come\s+([^?]+)", "wh_how_come"),
    # Feeling queries
    (r"\bhow\s+(?:did|do|can|could|would)\s+(?:you\s+)?feel\s*([^?]*)", "feel_query"),
    (r"\bwhy\s+(?:do|did|are)\s+you\s+feel\s+([^?]+)", "wh_feel_state"),
    # Change of state
    (r"\bwhen\s+did\s+you\s+stop\s+([^?]+)", "change_of_state_stop"),
    (r"\bwhen\s+did\s+you\s+start\s+([^?]+)", "change_of_state_start"),
    (r"\bwhen\s+did\s+you\s+(?:quit|begin|resume)\s+([^?]+)", "change_of_state"),
    (r"\bwhy\s+did\s+you\s+(?:stop|start|quit|begin|resume)\s+([^?]+)", "change_of_state"),
    # Iteratives
    (r"\bhow\s+long\s+have\s+you\s+(?:been|felt|noticed|known|had)\s+([^?]+)", "iterative_duration"),
    (r"\b(?:do|did|are|were)\s+you\s+still\s+([^?]+)", "iterative_still"),
    (r"\b(?:are|were|do|did)\s+you\s+again\s+([^?]+)", "iterative_again"),
    # Factives
    (r"\b(?:do|did)\s+you\s+regret\s+([^?]+)", "factive_regret"),
    (r"\bhow\s+did\s+you\s+(?:realize|discover|find\s+out|learn)\s+(?:that\s+)?([^?]+)", "factive_realize"),
    (r"\bhow\s+did\s+you\s+know\s+(?:that\s+)?([^?]+)", "factive_know"),
    # Temporal clauses presupposition
    (r"\bbefore\s+you\s+([^?,]+)", "temporal_clause_before"),
    (r"\bafter\s+you\s+([^?,]+)", "temporal_clause_after"),
    # Cleft constructions
    (r"\b(?:was|is)\s+it\s+([^?]+)\s+who\b", "cleft_who"),
    (r"\b(?:was|is)\s+it\s+([^?]+)\s+that\b", "cleft_that"),
    # Definite evaluations & affect NPs
    (r"\byour\s+(guilt|shame|regret|fear|trauma|anger|depression|anxiety|grief|jealousy|worry|doubt|insecurity|exhaustion|failure)\b", "unlicensed_affect_np"),
    (r"\bthe\s+reason\s+(?:why\s+)?([^?]+)", "definite_reason"),
]

# Stopwords that are strictly closed-class grammar words (function words only)
PERMITTED_GRAMMAR_WORDS = {
    "a", "an", "the", "this", "that", "these", "those", "it", "its", "you", "your",
    "me", "my", "we", "our", "he", "his", "him", "she", "her", "they", "them", "their",
    "be", "is", "are", "was", "were", "been", "being", "have", "has", "had",
    "do", "does", "did", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "up", "about", "into", "over", "after", "before", "between", "out", "through",
    "when", "where", "why", "how", "what", "which", "who", "whom", "could", "would",
    "should", "can", "will", "may", "might", "must", "or", "and", "but", "if", "not",
    "make", "made", "let", "get", "got",
    "so", "as", "than", "there", "then", "just", "more", "also", "such",
}


def extract_candidate_presuppositions(question: str) -> List[Dict[str, str]]:
    """Identify triggered propositions within a candidate question."""
    triggers = []
    seen_spans = set()
    lower = question.lower().strip()

    for pattern, trigger_name in PRESUPPOSITION_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            span_key = (match.start(), match.end(), trigger_name)
            if span_key not in seen_spans:
                seen_spans.add(span_key)
                triggers.append({
                    "trigger_type": trigger_name,
                    "proposition": match.group(1).strip() if match.groups() else match.group(0).strip(),
                    "span": [match.start(), match.end()],
                })

    return triggers


def check_presupposition_licensing(
    question: str,
    user_commitments: List[Dict[str, Any]],
    user_spans_text: str,
) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
    """Verify that every presupposed proposition is licensed by user commitments or text spans.
    Returns: (is_licensed: bool, rejection_reason: Optional[str], triggers_checked: List[Dict])
    """
    triggers = extract_candidate_presuppositions(question)
    user_tokens = set(re.findall(r"\w+", user_spans_text.lower()))
    
    # Extract committed lemmas and arguments
    committed_predicates = {extract_predicate_lemma(c) for c in user_commitments if extract_predicate_lemma(c)}
    committed_patients = {str(c.get("patient", "")).lower() for c in user_commitments if c.get("patient")}
    committed_agents = {str(c.get("agent", "")).lower() for c in user_commitments if c.get("agent")}

    licensed_vocabulary = user_tokens | committed_predicates | committed_patients | committed_agents

    for trig in triggers:
        prop_text = trig["proposition"]
        prop_words = set(re.findall(r"\w+", prop_text.lower()))
        content_words = prop_words - PERMITTED_GRAMMAR_WORDS

        # Check if every content word in the presupposition has user licensing
        unlicensed = [w for w in content_words if w not in licensed_vocabulary and len(w) > 2]
        if unlicensed:
            reason = f"Unlicensed presupposition in '{trig['trigger_type']}': takes for granted {unlicensed} not asserted by user."
            return False, reason, triggers

    return True, None, triggers


def filter_candidates(
    candidates: List[str],
    user_commitments: List[Dict[str, Any]],
    user_spans_text: str,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Filter candidate questions through presupposition budget.
    Returns: (surviving_candidates: List[str], rejection_log: List[Dict[str, Any]])
    """
    surviving = []
    rejections = []

    for cand in candidates:
        is_licensed, reason, triggers = check_presupposition_licensing(cand, user_commitments, user_spans_text)
        if is_licensed:
            surviving.append(cand)
        else:
            rejections.append({
                "candidate": cand,
                "reason": reason,
                "triggers": triggers,
            })

    return surviving, rejections
