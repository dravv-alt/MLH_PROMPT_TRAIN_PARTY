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


VERSION = "restricted-discourse-context.v1"
EPISTEMIC = {"may", "might", "could", "perhaps", "maybe", "probably", "possibly", "think", "guess", "suppose", "wonder"}
DEONTIC = {"should", "must", "need", "ought"}
VOLITIONAL = {"want", "wish", "prefer", "plan", "intend", "hope"}
NEGATION = {"not", "never", "no", "neither", "nor"}
SUBJECT_DEPS = {"nsubj", "nsubjpass", "csubj", "csubjpass"}
OBJECT_DEPS = {"dobj", "obj", "iobj", "pobj", "attr", "oprd"}
REVISION_STOP = {"actually", "rather", "instead", "i", "a", "an", "the", "to", "of", "is", "am", "are", "do", "does", "not", "but", "and", "still", "think", "that", "this"}


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
        actors = []
        for token in tokens:
            if token.dep_ in SUBJECT_DEPS:
                actors.append({"role": "agent", **_surface(text, token)})
            elif token.dep_ in OBJECT_DEPS:
                actors.append({"role": "patient", **_surface(text, token)})
        modality = _modality(tokens)
        negative_tokens = [token for token in tokens if token.dep_ == "neg" or token.lower_ in NEGATION]
        polarity = "negative" if negative_tokens else "positive"
        categories = {row["category"] for row in modality}
        status = "tentative" if "epistemic" in categories else "preference" if "volitional" in categories else "asserted"
        normalized = " ".join(text[start:end].strip() for start, end in spans)
        proposition_id = "dp_" + hashlib.sha256(f"{turn_index}|{clause.get('id')}|{normalized}".encode("utf-8")).hexdigest()[:12]
        current.append({
            "id": proposition_id,
            "source_turn": turn_index,
            "clause_id": clause.get("id"),
            "text": normalized,
            "scope_spans": spans,
            "predicate": {"lemma": (head.lemma_ or head.lower_).casefold(), "span": [head.idx, head.idx + len(head)]},
            "actors": actors,
            "polarity": polarity,
            "negation_spans": [[token.idx, token.idx + len(token)] for token in negative_tokens],
            "modality": modality,
            "status": status,
            "revision_status": "current",
        })

    links = []
    if correction.get("detected") and correction.get("supersedes_turn"):
        target_turn = int(correction["supersedes_turn"])
        targets = [row for row in state["propositions"] if row.get("source_turn") == target_turn and row.get("revision_status") == "current"]
        for source in current:
            # A correction only reaches propositions sharing concrete content
            # with its negated/revised clause. It must not invalidate every
            # proposition from the preceding turn merely because it is newer.
            source_tokens = _revision_tokens(source["text"])
            for target in targets:
                overlap = source_tokens & _revision_tokens(target["text"])
                if len(overlap) < 2:
                    continue
                links.append({
                    "source": source["id"],
                    "target": target["id"],
                    "relation": "supersession_candidate",
                    "status": "scope_resolved_lexical",
                    "reason": "explicit_revision_cue_with_content_overlap",
                    "shared_terms": sorted(overlap),
                })
                target["revision_status"] = "review_for_supersession"

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
            "Dependency-based actor roles are surface grammatical roles, not semantic-role labels.",
            "Supersession links remain candidates until their scope is resolved; they do not erase prior facts.",
        ],
    }
    return public, state
