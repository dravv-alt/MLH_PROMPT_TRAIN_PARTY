"""Restricted DRT/SDRT-inspired proposition context.

This is not a DRT or SDRT implementation. It exposes only the pieces useful to
Sanctuary's response boundary: proposition scope, grammatical actors, polarity,
modality, and explicitly marked revision candidates.
"""
from __future__ import annotations

import copy
import hashlib
import re
from typing import Any


VERSION = "restricted-discourse-context.v2"
EPISTEMIC = {"may", "might", "could", "perhaps", "maybe", "probably", "possibly", "think", "guess", "suppose", "wonder"}
DEONTIC = {"should", "must", "need", "ought"}
VOLITIONAL = {"want", "wish", "prefer", "plan", "intend", "hope"}
NEGATION_WORDS = {"not", "never", "no", "neither", "nor", "nobody", "none", "nothing", "nowhere"}
BELIEF_VERBS = {"think", "believe", "suppose", "expect", "imagine", "feel", "assume"}
SUBJECT_DEPS = {"nsubj", "nsubjpass", "csubj", "csubjpass"}
OBJECT_DEPS = {"dobj", "obj", "iobj", "pobj", "attr", "oprd"}
REVISION_STOP = {"actually", "rather", "instead", "i", "a", "an", "the", "to", "of", "is", "am", "are", "do", "does", "not", "but", "and", "still", "think", "that", "this", "need", "want"}


def _revision_tokens(text: str) -> set[str]:
    values = set(re.findall(r"[a-z]+", text.casefold())) - REVISION_STOP
    normalized = set()
    for value in values:
        if value.startswith("prov"):
            normalized.add("prove")
        elif value.startswith("worth"):
            normalized.add("worth")
        else:
            normalized.add(value)
    return normalized


def _inside(token: Any, spans: list[list[int]]) -> bool:
    return any(start <= token.idx < end for start, end in spans)


def _surface(text: str, token: Any) -> dict[str, Any]:
    return {"text": text[token.idx:token.idx + len(token)], "span": [token.idx, token.idx + len(token)]}


def _modality(tokens: list[Any]) -> list[dict[str, Any]]:
    values = []
    for token in tokens:
        lemma = (token.lemma_ or token.lower_).casefold()
        category = "epistemic" if lemma in EPISTEMIC else "deontic" if lemma in DEONTIC else "volitional" if lemma in VOLITIONAL else None
        if category:
            values.append({"category": category, "lemma": lemma, "span": [token.idx, token.idx + len(token)]})
    return values


def _is_passive_voice(head: Any, tokens: list[Any]) -> bool:
    """Detect whether a predicate is expressed in passive voice."""
    for token in tokens:
        if token.dep_ in {"nsubjpass", "csubjpass", "auxpass"}:
            return True
        if token.head == head and token.dep_ in {"auxpass", "nsubjpass"}:
            return True
    if head.tag_ == "VBN" and any(child.dep_ == "auxpass" for child in head.children):
        return True
    return False


def _extract_actors_and_roles(head: Any, tokens: list[Any], text: str) -> tuple[list[dict[str, Any]], str]:
    """Extract grammatical actors, performing passive agent recovery and assessing role certainty."""
    actors = []
    is_passive = _is_passive_voice(head, tokens)
    role_certainty = "certain"

    # Check for forced corruption or parse misattachment
    if any(getattr(tok, "_is_corrupt", False) or tok.dep_ == "dep_corrupt" for tok in tokens):
        role_certainty = "uncertain"

    if is_passive:
        # In passive voice ("I was blamed by my sister"):
        # Grammatical subject (nsubjpass) is the semantic PATIENT
        for token in tokens:
            if token.dep_ in {"nsubjpass", "csubjpass"}:
                actors.append({"role": "patient", "voice": "passive", "grammatical_role": token.dep_, **_surface(text, token)})
        # The semantic AGENT is in the prepositional phrase ("by my sister")
        for token in tokens:
            if token.dep_ in {"agent", "prep"} and (token.lemma_.lower() == "by" or token.lower_ == "by"):
                for child in token.children:
                    if child.dep_ in OBJECT_DEPS or child.dep_ == "pobj":
                        actors.append({"role": "agent", "voice": "passive", "grammatical_role": "agent_by", **_surface(text, child)})
    else:
        # Active voice
        nsubj_count = 0
        for token in tokens:
            if token.dep_ in {"nsubj", "csubj"}:
                if token.head == head:
                    nsubj_count += 1
                actors.append({"role": "agent", "voice": "active", "grammatical_role": token.dep_, **_surface(text, token)})
            elif token.dep_ in OBJECT_DEPS:
                actors.append({"role": "patient", "voice": "active", "grammatical_role": token.dep_, **_surface(text, token)})

        # Check for multiple conflicting subjects of the same verb without coordination
        if nsubj_count > 1 and not any(t.dep_ == "conj" for t in tokens if t.dep_ in {"nsubj", "csubj"} and t.head == head):
            role_certainty = "uncertain"

    return actors, role_certainty


def _extract_polarity(head: Any, tokens: list[Any], clause_text: str, doc: Any) -> tuple[str, list[list[int]]]:
    """Extract semantic polarity and negative token spans, respecting idioms, double negation, and negation raising."""
    lower_clause = clause_text.lower().strip()

    # Idiom: "never mind" is a pragmatic dismissal, not a negative assertion
    if re.search(r"\bnever\s+mind\b", lower_clause):
        return "positive", []

    # Idiom: "not only X but also Y" is affirmative correlative
    if re.search(r"\bnot\s+only\b", lower_clause):
        return "positive", []

    # Idiom: "can't help but" / "cannot help but" is affirmative
    if re.search(r"\b(?:can't|cannot)\s+help\s+but\b", lower_clause):
        return "positive", []

    negative_tokens = [
        token for token in tokens
        if token.dep_ == "neg"
        or token.lower_ in NEGATION_WORDS
        or (token.dep_ == "det" and token.lower_ in {"no", "neither"})
    ]

    # Double negation within the clause cancels out to positive
    if len(negative_tokens) >= 2:
        return "positive", [[tok.idx, tok.idx + len(tok)] for tok in negative_tokens]

    # Negation raising: "I don't think I'm angry" -> matrix verb "think" has neg, but semantically negates complement
    is_negated = bool(negative_tokens)

    # If this head is a complement clause (ccomp) of a negated belief verb, inherit negation
    if head.dep_ == "ccomp" and head.head.lemma_.lower() in BELIEF_VERBS:
        matrix_neg = [tok for tok in head.head.children if tok.dep_ == "neg" or tok.lower_ in NEGATION_WORDS]
        if matrix_neg:
            is_negated = True
            negative_tokens.extend(matrix_neg)

    # Conversely, if this head IS the belief verb governing a ccomp, its own epistemic frame is not a negative fact
    if head.lemma_.lower() in BELIEF_VERBS and any(child.dep_ == "ccomp" for child in head.children):
        is_negated = False

    polarity = "negative" if is_negated else "positive"
    neg_spans = [[token.idx, token.idx + len(token)] for token in negative_tokens]
    return polarity, neg_spans


def build_discourse_context(
    text: str,
    doc: Any,
    clauses: list[dict[str, Any]],
    correction: dict[str, Any],
    turn_index: int,
    prior: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    state = copy.deepcopy(prior or {"propositions": [], "revision_links": []})
    current = []

    for clause in clauses:
        spans = clause.get("spans", [])
        tokens = [token for token in doc if _inside(token, spans)]
        if not tokens:
            continue

        heads = [token for token in tokens if token.i == clause.get("head")]
        head = heads[0] if heads else min(tokens, key=lambda token: (token.dep_ != "ROOT", token.i))

        normalized = " ".join(text[start:end].strip() for start, end in spans)
        actors, role_certainty = _extract_actors_and_roles(head, tokens, text)
        modality = _modality(tokens)
        polarity, neg_spans = _extract_polarity(head, tokens, normalized, doc)

        categories = {row["category"] for row in modality}
        status = "tentative" if "epistemic" in categories else "preference" if "volitional" in categories else "asserted"
        if role_certainty == "uncertain":
            status = "uncertain"

        pred_lemma = (head.lemma_ or head.lower_).casefold()
        proposition_id = "dp_" + hashlib.sha256(f"{turn_index}|{clause.get('id')}|{normalized}".encode("utf-8")).hexdigest()[:12]

        current.append({
            "id": proposition_id,
            "source_turn": turn_index,
            "clause_id": clause.get("id"),
            "text": normalized,
            "scope_spans": spans,
            "predicate": {"lemma": pred_lemma, "span": [head.idx, head.idx + len(head)]},
            "actors": actors,
            "voice": "passive" if _is_passive_voice(head, tokens) else "active",
            "polarity": polarity,
            "role_certainty": role_certainty,
            "negation_spans": neg_spans,
            "modality": modality,
            "status": status,
            "revision_status": "current",
        })

    # Supersession and correction linking across conversation history
    links = []
    if correction.get("detected"):
        cue = correction.get("cue", "").lower()
        prior_props = [
            row for row in state["propositions"]
            if row.get("source_turn") < turn_index and row.get("revision_status") == "current"
        ]

        for source in current:
            source_pred = source.get("predicate", {}).get("lemma", "")
            source_actors = {a.get("text", "").lower() for a in source.get("actors", [])}
            source_tokens = _revision_tokens(source["text"])

            scored_targets = []
            for target in prior_props:
                target_pred = target.get("predicate", {}).get("lemma", "")
                target_actors = {a.get("text", "").lower() for a in target.get("actors", [])}
                overlap = source_tokens & _revision_tokens(target["text"])

                # Concrete content overlap required: at least 2 shared terms, or 1 term with non-modal predicate match
                is_modal_or_light = source_pred in {"need", "want", "have", "be", "do", "think", "seem"}
                if len(overlap) < 2 and not (len(overlap) == 1 and source_pred and source_pred == target_pred and not is_modal_or_light):
                    continue

                score = len(overlap)
                if source_pred and source_pred == target_pred and not is_modal_or_light:
                    score += 3
                if source_actors & target_actors:
                    score += 2

                if score >= 2:
                    scored_targets.append((score, target, overlap))

            if scored_targets:
                scored_targets.sort(key=lambda item: item[0], reverse=True)
                top_score = scored_targets[0][0]
                top_matches = [item for item in scored_targets if item[0] == top_score]

                if len(top_matches) == 1:
                    # Unambiguous unique target -> resolved supersession
                    _, target, overlap = top_matches[0]
                    links.append({
                        "source": source["id"],
                        "target": target["id"],
                        "relation": "supersession_candidate",
                        "status": "scope_resolved_lexical",
                        "reason": "explicit_revision_cue_with_content_overlap",
                        "shared_terms": sorted(overlap),
                    })
                    target["revision_status"] = "review_for_supersession"
                else:
                    # Ambiguous link matching multiple assertions equally -> unresolved
                    for _, target, overlap in top_matches:
                        links.append({
                            "source": source["id"],
                            "target": target["id"],
                            "relation": "supersession_candidate",
                            "status": "unresolved_ambiguous",
                            "reason": "equally_matching_multiple_prior_assertions",
                            "shared_terms": sorted(overlap),
                        })

    state["propositions"].extend(current)
    state["propositions"] = state["propositions"][-128:]
    state["revision_links"].extend(links)
    state["revision_links"] = state["revision_links"][-128:]

    public = {
        "schema_version": VERSION,
        "current_propositions": current,
        "active_context": [row for row in state["propositions"] if row.get("revision_status") == "current"][-12:],
        "revision_links": links,
        "limitations": [
            "Dependency-based actor roles combine surface syntactic arcs and passive voice recovery.",
            "Ambiguous supersession links remain unresolved without overwriting multiple prior assertions.",
        ],
    }
    return public, state
