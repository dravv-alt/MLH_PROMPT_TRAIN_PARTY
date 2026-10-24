"""Sanctuary V2 Evaluation Metric Harness.
Computes metrics 1 to 14 across dialogue turns, proposition frames, and candidate questions.
Independent causal and contrast detector avoids grading the verifier by its own internal rules.
"""
import re
import math
from typing import List, Dict, Any, Tuple, Optional, Set


# Closed-class connective triggers for independent detection
CAUSAL_CONNECTIVES = {
    "because", "since", "so", "therefore", "thus", "hence", "as a result", "consequently"
}
VERBAL_CAUSATIVES = [
    r"\b(?:made|makes|making)\s+(?:you|me|them|him|her)\s+(\w+)",
    r"\b(?:caused|causes|causing)\s+(?:you|me|them|him|her)\s+to\s+(\w+)",
    r"\b(?:led|leads|leading)\s+to\b",
    r"\b(?:forced|forces|forcing)\s+(?:you|me|them|him|her)\s+to\s+(\w+)",
]
CONTRAST_CONNECTIVES = {
    "but", "however", "although", "even though", "yet", "nevertheless", "on the other hand"
}
HEDGE_WORDS = {
    "maybe", "perhaps", "might", "could", "i think", "i guess", "it seems", "possibly", "kind of", "sort of", "honestly"
}


def extract_quoted_spans(text: str) -> List[Tuple[int, int]]:
    """Extract character ranges of text inside quotes."""
    spans = []
    for match in re.finditer(r"['\"](.*?)['\"]", text):
        spans.append((match.start(), match.end()))
    return spans


def is_in_quotes(start: int, end: int, quote_spans: List[Tuple[int, int]]) -> bool:
    """Check if a token range falls within any quoted span."""
    return any(q_start <= start and end <= q_end for q_start, q_end in quote_spans)


def detect_causal_expressions(text: str, user_text: str = "") -> List[Dict[str, Any]]:
    """Independent detector for causal expressions (lexical connectives and verbal causatives).
    Hard negative rule: connectives inside a direct quote of user words are ignored.
    """
    results = []
    quote_spans = extract_quoted_spans(text)
    lower_text = text.lower()

    # 1. Lexical causal connectives
    for conn in CAUSAL_CONNECTIVES:
        pattern = r"\b" + re.escape(conn) + r"\b"
        for match in re.finditer(pattern, lower_text):
            start, end = match.start(), match.end()
            # If inside quotes and matching user's words, skip
            if is_in_quotes(start, end, quote_spans):
                quoted_content = text[start:end]
                if quoted_content.lower() in user_text.lower():
                    continue
            results.append({
                "type": "lexical_causal",
                "trigger": conn,
                "span": [start, end]
            })

    # 2. Verbal causatives (e.g. "made you feel", "led to")
    for pattern in VERBAL_CAUSATIVES:
        for match in re.finditer(pattern, lower_text):
            start, end = match.start(), match.end()
            if is_in_quotes(start, end, quote_spans):
                continue
            results.append({
                "type": "verbal_causative",
                "trigger": match.group(0),
                "span": [start, end]
            })

    return results


def detect_contrast_expressions(text: str, user_text: str = "") -> List[Dict[str, Any]]:
    """Independent detector for contrast expressions."""
    results = []
    quote_spans = extract_quoted_spans(text)
    lower_text = text.lower()

    for conn in CONTRAST_CONNECTIVES:
        pattern = r"\b" + re.escape(conn) + r"\b"
        for match in re.finditer(pattern, lower_text):
            start, end = match.start(), match.end()
            if is_in_quotes(start, end, quote_spans):
                if text[start:end].lower() in user_text.lower():
                    continue
            results.append({
                "type": "contrast",
                "trigger": conn,
                "span": [start, end]
            })
    return results


# 1. Unlicensed Connective Rate
def unlicensed_connective_rate(reply: str, user_relations: List[Dict[str, Any]], user_text: str = "") -> float:
    """Proportion of causal or contrast expressions in reply that have no licensing edge in user relations."""
    detected = detect_causal_expressions(reply, user_text) + detect_contrast_expressions(reply, user_text)
    if not detected:
        return 0.0

    licensed_types = {r.get("type", "").lower() for r in user_relations}
    unlicensed_count = 0

    for expr in detected:
        expr_type = "causal" if "causal" in expr["type"] else "contrast"
        if expr_type not in licensed_types:
            unlicensed_count += 1

    return unlicensed_count / len(detected)


# 2. Polarity-Flip Rate
def polarity_flip_rate(reply_claims: List[Dict[str, Any]], user_commitments: List[Dict[str, Any]]) -> float:
    """Proportion of claims in reply that flip the polarity of the user's committed predicate."""
    if not reply_claims or not user_commitments:
        return 0.0

    user_pred_pol = {c.get("predicate", "").lower(): c.get("polarity", "positive").lower() for c in user_commitments if c.get("predicate")}
    flips = 0
    matched = 0

    for claim in reply_claims:
        pred = claim.get("predicate", "").lower()
        if pred in user_pred_pol:
            matched += 1
            if claim.get("polarity", "positive").lower() != user_pred_pol[pred]:
                flips += 1

    return flips / matched if matched > 0 else 0.0


# 3. Role-Reversal Rate
def role_reversal_rate(reply_claims: List[Dict[str, Any]], user_commitments: List[Dict[str, Any]]) -> float:
    """Proportion of shared predicate claims where agent and patient are swapped."""
    if not reply_claims or not user_commitments:
        return 0.0

    user_roles = {
        c.get("predicate", "").lower(): (str(c.get("agent", "")).lower(), str(c.get("patient", "")).lower())
        for c in user_commitments if c.get("predicate")
    }
    reversals = 0
    matched = 0

    for claim in reply_claims:
        pred = claim.get("predicate", "").lower()
        if pred in user_roles:
            matched += 1
            u_agent, u_patient = user_roles[pred]
            r_agent = str(claim.get("agent", "")).lower()
            r_patient = str(claim.get("patient", "")).lower()
            if u_agent and u_patient:
                # Reversal occurs when reply agent matches user patient and reply patient matches user agent
                if (r_agent in u_patient or u_patient in r_agent) and (r_patient in u_agent or u_agent in r_patient):
                    reversals += 1

    return reversals / matched if matched > 0 else 0.0


# 4. Invented-Entity Rate
def invented_entity_rate(reply_entities: List[str], user_entities: List[str], allowed_plan_entities: Optional[List[str]] = None) -> float:
    """Proportion of entities mentioned in reply that were not in user utterance or allowed plan."""
    if not reply_entities:
        return 0.0

    allowed = {e.lower().strip() for e in user_entities}
    if allowed_plan_entities:
        allowed.update(e.lower().strip() for e in allowed_plan_entities)

    invented = sum(1 for e in reply_entities if e.lower().strip() not in allowed)
    return invented / len(reply_entities)


# 5. Superseded-Reuse Rate
def superseded_reuse_rate(reply_claims: List[Dict[str, Any]], superseded_commitments: List[Dict[str, Any]]) -> float:
    """Proportion of reply claims that assert a superseded proposition."""
    if not reply_claims or not superseded_commitments:
        return 0.0

    superseded_preds = {c.get("predicate", "").lower() for c in superseded_commitments if c.get("predicate")}
    violations = sum(1 for claim in reply_claims if claim.get("predicate", "").lower() in superseded_preds)
    return violations / len(reply_claims)


# 6. Hedge-Survival Rate
def hedge_survival_rate(reply_claims: List[Dict[str, Any]], user_commitments: List[Dict[str, Any]]) -> float:
    """Measures how well hedged user commitments survive as hedged propositions in the reply.
    Returns 1.0 if all hedged commitments remain hedged, and < 1.0 if hedged claims are rendered as firm assertions.
    """
    hedged_user_preds = {c.get("predicate", "").lower() for c in user_commitments if c.get("hedge")}
    if not hedged_user_preds:
        return 1.0  # None were hedged, so survival is vacuously 100%

    matched = 0
    survived = 0
    for claim in reply_claims:
        pred = claim.get("predicate", "").lower()
        if pred in hedged_user_preds:
            matched += 1
            if claim.get("hedge"):
                survived += 1

    return survived / matched if matched > 0 else 1.0


# 7. Fallback-Valid Rate
def fallback_valid_rate(fallback_outputs: List[Dict[str, Any]], validator_func: Any) -> float:
    """Proportion of classical realizer outputs that pass validation."""
    if not fallback_outputs:
        return 0.0
    valid_count = sum(1 for out in fallback_outputs if validator_func(out))
    return valid_count / len(fallback_outputs)


# 9. Presupposition-Violation Rate
PRESUPPOSITION_TRIGGERS = [
    (r"\bwhy did you\s+([^?]+)", "reason_factive"),
    (r"\bwhen did you stop\s+([^?]+)", "change_of_state"),
    (r"\bhow long have you felt\s+([^?]+)", "temporal_factive"),
    (r"\bwhat made you feel\s+([^?]+)", "causative_factive"),
    (r"\bdo you regret\s+([^?]+)", "factive_regret"),
]


def extract_presuppositions(question: str) -> List[Dict[str, str]]:
    """Extract propositions that the question takes for granted."""
    presuppositions = []
    lower_q = question.lower().strip()
    for pattern, trigger_type in PRESUPPOSITION_TRIGGERS:
        match = re.search(pattern, lower_q)
        if match:
            presuppositions.append({
                "trigger": trigger_type,
                "proposition": match.group(1).strip()
            })
    return presuppositions


def presupposition_violation_rate(questions: List[str], user_commitments: List[Dict[str, Any]], user_text: str) -> float:
    """Proportion of questions that presuppose propositions not asserted or licensed by the user."""
    if not questions:
        return 0.0

    violations = 0
    user_words = set(re.findall(r"\w+", user_text.lower()))
    committed_predicates = {c.get("predicate", "").lower() for c in user_commitments}
    committed_patients = {str(c.get("patient", "")).lower() for c in user_commitments}

    for q in questions:
        ps = extract_presuppositions(q)
        q_violated = False
        for p in ps:
            prop_words = set(re.findall(r"\w+", p["proposition"]))
            # If the proposition introduces unasserted content words not in user's text or commitments
            content_words = {w for w in prop_words if len(w) > 3 and w not in {"that", "this", "your", "with", "from", "about"}}
            unlicensed_words = content_words - user_words - committed_predicates - committed_patients
            if unlicensed_words:
                q_violated = True
                break
        if q_violated:
            violations += 1

    return violations / len(questions)


# 10. Gap Precision and Recall
def gap_precision_recall(detected_gaps: List[Dict[str, Any]], gold_gaps: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate precision, recall, and F1 of detected structural gaps against gold gaps."""
    if not detected_gaps and not gold_gaps:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not detected_gaps:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    if not gold_gaps:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    gold_signatures = {(g.get("type"), g.get("predicate", "")) for g in gold_gaps}
    detected_signatures = {(g.get("type"), g.get("predicate", "")) for g in detected_gaps}

    tp = len(gold_signatures.intersection(detected_signatures))
    precision = tp / len(detected_signatures) if detected_signatures else 0.0
    recall = tp / len(gold_signatures) if gold_signatures else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


# 11. Restatement Ratio
def restatement_ratio(reply_text: str, user_text: str) -> float:
    """Share of reply tokens copied directly from user spans."""
    reply_tokens = re.findall(r"\w+", reply_text.lower())
    if not reply_tokens:
        return 0.0
    user_token_set = set(re.findall(r"\w+", user_text.lower()))
    copied_tokens = sum(1 for t in reply_tokens if t in user_token_set and len(t) > 2)
    return copied_tokens / len(reply_tokens)


# 12. Over-Asking Rate
def over_asking_rate(system_moves: List[str], gold_moves: List[List[str]]) -> float:
    """Proportion of turns where the system asks or clarifies when gold move is acknowledge or hold."""
    candidate_turns = 0
    over_asks = 0

    for s_move, g_moves in zip(system_moves, gold_moves):
        g_set = set(g_moves)
        if "ask" not in g_set and "clarify" not in g_set:
            candidate_turns += 1
            if s_move in {"ask", "clarify"}:
                over_asks += 1

    return over_asks / candidate_turns if candidate_turns > 0 else 0.0


# 13. Repeat-Question Rate
def repeat_question_rate(questions_in_session: List[str]) -> float:
    """Share of questions in a session that repeat an earlier question stem or identical target."""
    if len(questions_in_session) <= 1:
        return 0.0

    seen_stems = set()
    repeats = 0

    for q in questions_in_session:
        stem = " ".join(re.findall(r"\w+", q.lower())[:4])
        if stem in seen_stems:
            repeats += 1
        else:
            seen_stems.add(stem)

    return repeats / len(questions_in_session)


# 14. Uptake Rate
def uptake_rate(next_turn_commitments: List[Dict[str, Any]], next_turn_relations: List[Dict[str, Any]], targeted_gap: Dict[str, Any]) -> bool:
    """Determine whether the user's subsequent turn fills the targeted gap.
    Returns True if an argument or relation is attached to the targeted predicate.
    """
    if not targeted_gap:
        return False

    target_pred = targeted_gap.get("predicate", "").lower()
    target_type = targeted_gap.get("type", "")

    # For unfilled causal roles, uptake occurs if new causal relation or explanation is provided
    if target_type == "unfilled_role":
        if any(r.get("type") == "causal" for r in next_turn_relations):
            return True
        if any(c.get("predicate", "").lower() == target_pred and c.get("patient") for c in next_turn_commitments):
            return True

    # For hedged commitments, uptake occurs if user elaborates on the hedged predicate
    if target_type == "hedged_commitment":
        if any(c.get("predicate", "").lower() == target_pred for c in next_turn_commitments):
            return True

    # For unresolved references, uptake occurs if antecedent is named
    if target_type == "unresolved_reference":
        if next_turn_commitments:
            return True

    return False
