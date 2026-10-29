"""Evidence-linked narrative memory update and retrieval harness.

This module is intentionally pure: it reads an analysis and state snapshot and
returns a proposed canonical state. Database revision checks and the final
commit remain owned by :mod:`nlp_service`.

Embeddings, lexical scenes, summaries, and mathematical ledgers are candidate
finders only. ``canonical_memory.assertions`` and their revision lineage are
the authority used by the response boundary.
"""
from __future__ import annotations

import copy
import hashlib
import math
import re
from collections import defaultdict
from typing import Any


SCHEMA_VERSION = "sanctuary.memory-harness.v1"
RETRIEVAL_VERSION = "sanctuary.memory-retrieval.v1"
POLICY_VERSION = "sanctuary.memory-policy.v1"
ACTIVE = {"active", "unresolved"}
INELIGIBLE = {"superseded", "rejected", "deleted"}
TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?", re.I)
STOP = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by", "do", "does",
    "did", "for", "from", "had", "has", "have", "he", "her", "hers", "him", "his", "i", "if",
    "in", "is", "it", "its", "me", "my", "of", "on", "or", "our", "ours", "she", "so", "that",
    "the", "their", "theirs", "them", "they", "this", "to", "was", "we", "were", "with", "you",
    "your", "actually", "honestly", "instead", "rather", "think", "thought", "feel", "felt", "feeling",
    "not", "never", "no", "don't", "didn't", "wasn't", "isn't", "aren't", "haven't", "hasn't",
    "about", "what", "when", "where", "why", "how", "i'm", "i've", "i'd", "i'll",
}
REACTION = re.compile(
    r"\b(?:feel|felt|feeling|excited|happy|sad|angry|annoyed|frustrated|worried|anxious|tired|exhausted|"
    r"relieved|disappointed|overwhelmed|calm|afraid|proud|upset)\b", re.I
)
MEANING = re.compile(r"\b(?:think|believe|mean|realize|understand|interpret|want|prefer|hope|expect|need)\b", re.I)
CONSTRAINT = re.compile(r"\b(?:because|due to|after|before|deadline|time|money|resource|limit|require|months?|years?)\b", re.I)
TEMPORAL = re.compile(r"\b(?:now|then|before|after|yesterday|today|tomorrow|again|still|already|months?|years?|next)\b", re.I)
HYPOTHETICAL = re.compile(r"\b(?:if i|imagine|suppose|hypothetical|someone|my friend|they might)\b", re.I)
REFINEMENT_CUE = re.compile(
    r"\b(?:now i see|i (?:now )?(?:realize|realised|understand)|more specifically|to clarify|"
    r"what i mean|looking back|a bigger part|rather than|refine|the whole thing now)\b",
    re.I,
)


def _stable(prefix: str, *parts: Any) -> str:
    value = "|".join(str(part) for part in parts)
    return f"{prefix}_" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _stem(token: str) -> str:
    value = token.casefold().strip("'")
    aliases = {"worthy": "worth", "worthiness": "worth", "exhaustion": "exhaust", "anxiety": "anxious"}
    if value in aliases:
        return aliases[value]
    for suffix in ("ation", "ingly", "edly", "ments", "ment", "ness", "ious", "ing", "ied", "ies", "ed", "ly", "s"):
        if len(value) > len(suffix) + 3 and value.endswith(suffix):
            value = value[:-len(suffix)] + ("y" if suffix in {"ied", "ies"} else "")
            break
    if value in {"prov", "mak", "hav", "mov", "writ"}:
        value += "e"
    return value


def _tokens(value: str) -> set[str]:
    return {_stem(token) for token in TOKEN_RE.findall(value) if _stem(token) not in STOP and len(_stem(token)) > 2}


def _valid_spans(text: str, spans: list[list[int]]) -> list[list[int]]:
    values = []
    for span in spans:
        if isinstance(span, list) and len(span) == 2:
            start, end = int(span[0]), int(span[1])
            if 0 <= start < end <= len(text):
                values.append([start, end])
    return sorted(values)


def _layer_views(value: str, status: str) -> list[str]:
    layers = ["language"]
    if REACTION.search(value):
        layers.append("reaction")
    if MEANING.search(value) or status in {"tentative", "preference"}:
        layers.append("meaning")
    if CONSTRAINT.search(value):
        layers.append("constraints")
    if TEMPORAL.search(value):
        layers.append("temporal")
    if not set(layers) & {"reaction", "meaning", "constraints"}:
        layers.append("event")
    return layers


def _claim_type(value: str, status: str) -> str:
    if REACTION.search(value):
        return "reported_reaction"
    if status == "preference" or re.search(r"\b(?:want|prefer|intend|plan|hope)\b", value, re.I):
        return "reported_preference"
    if MEANING.search(value):
        return "reported_meaning"
    if CONSTRAINT.search(value):
        return "reported_constraint"
    return "reported_event"


def _empty(generation: str = "") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "memory_generation": generation,
        "revision": 0,
        "assertions": [],
        "evidence": [],
        "revision_links": [],
        "graph": {"nodes": [], "edges": []},
        "episodes": [],
        "unresolved": [],
        "outbox": [],
    }


def _assertion_from_frame(
    frame: dict[str, Any], text: str, turn_index: int, episode_id: str, scene_id: str | None
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    spans = _valid_spans(text, frame.get("scope_spans", []))
    if not spans:
        return None
    value = " ".join(text[start:end].strip() for start, end in spans).strip()
    value = re.sub(r"\s+([?.!,;:])", r"\1", value).strip()
    value = re.sub(r"\s+\b(?:and|but|or|because|so|then|if)\b[.,;:!?]?$", "", value, flags=re.IGNORECASE).strip()
    if not value:
        return None
    assertion_id = _stable("as", turn_index, frame.get("id"), value.casefold())
    evidence_id = _stable("ev", assertion_id, spans)
    modality = [row.get("category") for row in frame.get("modality", []) if row.get("category")]
    status = frame.get("status", "asserted")
    evidence = {
        "evidence_id": evidence_id,
        "source_turn_index": turn_index,
        "source_turn_id": None,
        "source_scene_id": scene_id,
        "speaker": "user",
        "text": value,
        "spans": spans,
        "coordinate_system": "redacted_half_open",
        "retention_scope": "session",
        "sensitivity": "private",
    }
    assertion = {
        "assertion_id": assertion_id,
        "subject_ref": episode_id,
        "episode_id": episode_id,
        "source_turn_index": turn_index,
        "source_turn_id": None,
        "source_scene_id": scene_id,
        "claim_type": _claim_type(value, status),
        "content": {
            "text": value,
            "predicate": frame.get("predicate", {}).get("lemma"),
            "actors": copy.deepcopy(frame.get("actors", [])),
            "polarity": frame.get("polarity", "positive"),
            "modality": modality,
        },
        "ssm_views": _layer_views(value, status),
        "evidence_refs": [evidence_id],
        "epistemic_status": "extracted_with_uncertainty" if status == "tentative" else "explicitly_reported",
        "revision_status": "active",
        "valid_time": {"kind": "turn_relative", "turn": turn_index},
        "recorded_at": None,
        "supersedes": [],
        "sensitivity": "private",
        "retention_scope": "session",
        "autobiographical": not bool(HYPOTHETICAL.search(value)),
    }
    return assertion, evidence


def _similarity(current: dict[str, Any], prior: dict[str, Any]) -> tuple[float, set[str]]:
    left = _tokens(current["content"]["text"])
    right = _tokens(prior["content"]["text"])
    common = left & right
    lexical = len(common) / max(1, len(left | right))
    predicate = current["content"].get("predicate")
    predicate_match = bool(predicate and predicate == prior["content"].get("predicate"))
    actor_left = _tokens(" ".join(row.get("text", "") for row in current["content"].get("actors", [])))
    actor_right = _tokens(" ".join(row.get("text", "") for row in prior["content"].get("actors", [])))
    actor_match = bool(actor_left & actor_right) or not actor_left or not actor_right
    score = lexical + (.12 if predicate_match else 0.0) + (.08 if actor_match else -.12)
    return score, common


def _resolve_correction(
    current: list[dict[str, Any]], memory: dict[str, Any], correction: dict[str, Any], current_text: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    operations: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    if not correction.get("detected"):
        return operations, links, unresolved

    negative = [row for row in current if row["content"].get("polarity") == "negative"]
    scopes = negative or current[:1]
    cue_start = (correction.get("cue_span") or [0])[0]
    correction_sentence = next(
        (match.group(0).strip() for match in re.finditer(r"[^.!?]+[.!?]?", current_text) if match.start() <= cue_start < match.end()),
        " ".join(row["content"]["text"] for row in current),
    )
    prior = [row for row in memory["assertions"] if row.get("revision_status") == "active"]
    for scope in scopes:
        matching_scope = copy.deepcopy(scope)
        # Dependency clause ownership can place a negation on "think" while
        # its corrected content lives in a nested complement. Use the full
        # current evidence only for target discovery; the stored correction
        # still points to the exact negative assertion and its own spans.
        if len(_tokens(scope["content"]["text"])) < 2:
            matching_scope["content"]["text"] = correction_sentence
        correction_terms = _tokens(matching_scope["content"]["text"]) - {"actual", "need", "now", "next", "already"}
        if correction_terms:
            matching_scope["content"]["text"] = " ".join(sorted(correction_terms))
        scored = []
        for candidate in prior:
            score, common = _similarity(matching_scope, candidate)
            if common:
                scored.append((score, candidate.get("source_turn_index", 0), candidate, sorted(common)))
        scored.sort(key=lambda row: (-row[0], -row[1], row[2]["assertion_id"]))
        best = scored[0] if scored else None
        next_score = scored[1][0] if len(scored) > 1 else -1.0
        # The legacy analyzer's ``supersedes_turn`` is only a recency hint; it
        # always names the immediately previous turn and therefore cannot
        # resolve scope when two prior accounts are equally plausible.
        targets: list[tuple[float, int, dict[str, Any], list[str]]] = []
        if best and best[0] >= .24 and best[0] - next_score >= .08:
            targets = [best]
        elif best:
            tied = [row for row in scored if row[0] >= .24 and best[0] - row[0] < .08]
            common_sets = [set(row[3]) for row in tied]
            disjoint_scope = all(
                not left.intersection(right)
                for index, left in enumerate(common_sets)
                for right in common_sets[index + 1:]
            )
            if (
                len(tied) > 1
                and len({row[1] for row in tied}) == 1
                and disjoint_scope
                and len(set().union(*common_sets)) >= 2
            ):
                targets = tied
        if not targets:
            item = {
                "id": _stable("ur", scope["assertion_id"], memory["revision"] + 1),
                "kind": "correction_target",
                "source_assertion_id": scope["assertion_id"],
                "candidate_assertion_ids": [row[2]["assertion_id"] for row in scored[:3]],
                "status": "deferred",
                "reason": "no_unambiguous_evidence_link",
            }
            unresolved.append(item)
            operations.append({"operation": "DEFER", "assertion_id": scope["assertion_id"], "reason": item["reason"]})
            continue
        for resolved in targets:
            target = resolved[2]
            target["revision_status"] = "superseded"
            target["superseded_by"] = scope["assertion_id"]
            scope["supersedes"] = sorted(set(scope.get("supersedes", []) + [target["assertion_id"]]))
            link = {
                "edge_id": _stable("edge", scope["assertion_id"], "supersedes", target["assertion_id"]),
                "source": scope["assertion_id"],
                "target": target["assertion_id"],
                "type": "supersedes",
                "origin": "explicit_correction",
                "status": "active",
                "evidence_terms": resolved[3],
            }
            links.append(link)
            operations.append({
                "operation": "CORRECT",
                "assertion_id": scope["assertion_id"],
                "target_assertion_id": target["assertion_id"],
                "reason": "explicit_correction_with_shared_evidence_scope",
            })
    return operations, links, unresolved


def _detect_conflicts(current: list[dict[str, Any]], memory: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    links, unresolved = [], []
    for source in current:
        for target in memory["assertions"]:
            if target.get("revision_status") != "active":
                continue
            if source["content"].get("polarity") == target["content"].get("polarity"):
                continue
            score, common = _similarity(source, target)
            if score < .32 or not common:
                continue
            edge = {
                "edge_id": _stable("edge", source["assertion_id"], "contradicts", target["assertion_id"]),
                "source": source["assertion_id"], "target": target["assertion_id"],
                "type": "contradicts", "origin": "polarity_conflict", "status": "unresolved",
                "evidence_terms": sorted(common),
            }
            links.append(edge)
            unresolved.append({
                "id": _stable("ur", edge["edge_id"]), "kind": "contradiction",
                "source_assertion_id": source["assertion_id"],
                "candidate_assertion_ids": [target["assertion_id"]],
                "status": "unresolved", "reason": "opposite_polarity_without_explicit_resolution",
            })
    return links, unresolved


def _resolve_refinements(current: list[dict[str, Any]], memory: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    links, operations = [], []
    if not any(REFINEMENT_CUE.search(row["content"]["text"]) for row in current):
        return links, operations
    prior = [row for row in memory["assertions"] if row.get("revision_status") == "active"]
    for source in current:
        if not REFINEMENT_CUE.search(source["content"]["text"]):
            continue
        scored = []
        for target in prior:
            if source["content"].get("polarity") != target["content"].get("polarity"):
                continue
            score, common = _similarity(source, target)
            if common:
                scored.append((score, target.get("source_turn_index", 0), target, sorted(common)))
        scored.sort(key=lambda row: (-row[0], -row[1], row[2]["assertion_id"]))
        if not scored or scored[0][0] < .18:
            continue
        if len(scored) > 1 and scored[0][0] - scored[1][0] < .08:
            continue
        target = scored[0][2]
        edge = {
            "edge_id": _stable("edge", source["assertion_id"], "refines", target["assertion_id"]),
            "source": source["assertion_id"], "target": target["assertion_id"],
            "type": "refines", "origin": "explicit_refinement_cue", "status": "active",
            "evidence_terms": scored[0][3],
        }
        links.append(edge)
        operations.append({
            "operation": "REFINE", "assertion_id": source["assertion_id"],
            "target_assertion_id": target["assertion_id"], "reason": "explicit_refinement_with_shared_scope",
        })
    return links, operations


def _graph_updates(
    analysis: dict[str, Any], current: list[dict[str, Any]], evidence: list[dict[str, Any]], episode_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = [{"id": episode_id, "type": "episode", "status": "active", "origin": "turn_boundary"}]
    nodes.extend({"id": row["evidence_id"], "type": "evidence", "status": "active", "origin": "user_stated"} for row in evidence)
    nodes.extend({
        "id": row["assertion_id"], "type": "assertion", "status": row["revision_status"],
        "origin": "user_stated", "claim_type": row["claim_type"], "source_turn_index": row["source_turn_index"],
    } for row in current)
    edges = []
    by_clause = {}
    for assertion in current:
        edges.append({
            "edge_id": _stable("edge", assertion["evidence_refs"][0], "supports", assertion["assertion_id"]),
            "source": assertion["evidence_refs"][0], "target": assertion["assertion_id"],
            "type": "supports", "origin": "source_evidence", "status": "active",
        })
        edges.append({
            "edge_id": _stable("edge", assertion["assertion_id"], "belongs_to", episode_id),
            "source": assertion["assertion_id"], "target": episode_id,
            "type": "belongs_to", "origin": "turn_boundary", "status": "active",
        })
    frames = analysis.get("discourse_context", {}).get("current_propositions", [])
    for frame, assertion in zip(frames, current):
        by_clause[frame.get("clause_id")] = assertion["assertion_id"]
    relation_types = {
        "cause": "causes", "result": "leads_to", "contrast": "contrasts_with",
        "condition": "condition_for", "temporal": "temporally_related", "example": "elaborates",
    }
    for relation in analysis.get("relations", []):
        source, target = by_clause.get(relation.get("source")), by_clause.get(relation.get("target"))
        if source and target:
            edges.append({
                "edge_id": _stable("edge", source, relation.get("relation"), target, relation.get("id")),
                "source": source, "target": target,
                "type": relation_types.get(relation.get("relation"), relation.get("relation")),
                "origin": "explicit_connective", "status": "active", "relation_id": relation.get("id"),
            })
    return nodes, edges


def propose_update(
    analysis: dict[str, Any], state_snapshot: dict[str, Any], *, memory_generation: str = "", session_id: str | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build and reconcile an idempotent proposed canonical-memory delta."""
    prior_world = state_snapshot.get("world", {})
    memory = copy.deepcopy(prior_world.get("canonical_memory") or _empty(memory_generation))
    if memory_generation and memory.get("memory_generation") not in {"", memory_generation}:
        memory = _empty(memory_generation)
    memory["memory_generation"] = memory_generation or memory.get("memory_generation", "")
    turn_index = len(state_snapshot.get("turns", [])) + 1
    scene = (analysis.get("pwm", {}).get("scenes") or [{}])[-1]
    scene_id = scene.get("id")
    episode_id = _stable("ep", session_id or "pending", turn_index, scene_id or "scene")
    existing_sources = {(row.get("source_turn_index"), row.get("content", {}).get("text")) for row in memory["assertions"]}
    built: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for frame in analysis.get("discourse_context", {}).get("current_propositions", []):
        value = _assertion_from_frame(frame, analysis.get("redacted_text", ""), turn_index, episode_id, scene_id)
        if value and (turn_index, value[0]["content"]["text"]) not in existing_sources:
            built.append(value[0]); evidence.append(value[1])

    operations = [{"operation": "ADD", "assertion_id": row["assertion_id"], "reason": "explicit_user_evidence"} for row in built]
    correction = analysis.get("strategy_evidence", {}).get("correction", {})
    correction_ops, revision_links, unresolved = _resolve_correction(
        built, memory, correction, analysis.get("redacted_text", "")
    )
    operations.extend(correction_ops)
    if not correction.get("detected"):
        conflict_links, conflicts = _detect_conflicts(built, memory)
        revision_links.extend(conflict_links); unresolved.extend(conflicts)
        operations.extend({
            "operation": "CONTRADICT", "assertion_id": row["source"],
            "target_assertion_id": row["target"], "reason": "opposite_polarity_without_explicit_resolution",
        } for row in conflict_links)
        refinement_links, refinement_ops = _resolve_refinements(built, memory)
        revision_links.extend(refinement_links); operations.extend(refinement_ops)

    nodes, edges = _graph_updates(analysis, built, evidence, episode_id)
    edges.extend(revision_links)
    operations.extend({
        "operation": "LINK", "assertion_id": row["source"], "target_assertion_id": row["target"],
        "relation": row["type"], "reason": row["origin"],
    } for row in edges if row.get("origin") == "explicit_connective")
    for operation in list(operations):
        if operation.get("operation") == "CORRECT" and operation.get("target_assertion_id"):
            operations.append({
                "operation": "SUPERSEDE", "assertion_id": operation["target_assertion_id"],
                "target_assertion_id": operation["assertion_id"],
                "reason": "targeted_explicit_correction",
            })
    if not built:
        operations.append({"operation": "NO_OP", "assertion_id": None, "reason": "no_valid_evidence_spans"})
    assertion_status = {row["assertion_id"]: row.get("revision_status", "unresolved") for row in memory["assertions"]}
    for node in memory["graph"]["nodes"]:
        if node.get("id") in assertion_status:
            node["status"] = assertion_status[node["id"]]
    known_nodes = {row["id"] for row in memory["graph"]["nodes"]}
    memory["graph"]["nodes"].extend(row for row in nodes if row["id"] not in known_nodes)
    known_edges = {row["edge_id"] for row in memory["graph"]["edges"]}
    memory["graph"]["edges"].extend(row for row in edges if row["edge_id"] not in known_edges)
    memory["assertions"].extend(built)
    memory["evidence"].extend(evidence)
    memory["revision_links"].extend(revision_links)
    memory["unresolved"].extend(unresolved)
    memory["episodes"].append({
        "episode_id": episode_id, "source_turn_index": turn_index, "source_turn_id": None,
        "source_scene_id": scene_id, "session_id": session_id, "topic_id": analysis.get("topic_id"),
        "status": "active", "assertion_ids": [row["assertion_id"] for row in built],
    })
    memory["revision"] = int(memory.get("revision", 0)) + 1
    event = {
        "event_id": _stable("out", memory["memory_generation"], memory["revision"], turn_index),
        "kind": "refresh_memory_projections", "status": "pending", "source_turn_index": turn_index,
        "memory_generation": memory["memory_generation"], "memory_revision": memory["revision"],
    }
    memory["outbox"].append(event)
    # Bounded canonical session/user state. Source turns remain in the database;
    # this protects local prompt and snapshot sizes without changing authority.
    memory["assertions"] = memory["assertions"][-512:]
    memory["evidence"] = memory["evidence"][-768:]
    memory["revision_links"] = memory["revision_links"][-512:]
    memory["graph"]["nodes"] = memory["graph"]["nodes"][-1024:]
    valid_nodes = {row["id"] for row in memory["graph"]["nodes"]}
    memory["graph"]["edges"] = [
        row for row in memory["graph"]["edges"]
        if row.get("source") in valid_nodes and row.get("target") in valid_nodes
    ][-2048:]
    memory["episodes"] = memory["episodes"][-256:]
    memory["unresolved"] = memory["unresolved"][-256:]
    memory["outbox"] = memory["outbox"][-256:]
    outcome = {
        "schema_version": SCHEMA_VERSION,
        "status": "proposed",
        "memory_revision": memory["revision"],
        "memory_generation": memory["memory_generation"],
        "source_turn_index": turn_index,
        "assertion_ids": [row["assertion_id"] for row in built],
        "evidence_ids": [row["evidence_id"] for row in evidence],
        "operations": operations,
        "revision_link_ids": [row["edge_id"] for row in revision_links],
        "unresolved_ids": [row["id"] for row in unresolved],
        "outbox_event_id": event["event_id"],
    }
    return memory, outcome


def _candidate_routes(analysis: dict[str, Any], memory: dict[str, Any], current_ids: set[str]) -> dict[str, dict[str, float]]:
    routes: dict[str, dict[str, float]] = defaultdict(dict)
    active = [row for row in memory["assertions"] if row["assertion_id"] not in current_ids and row.get("revision_status") == "active"]
    current = [row for row in memory["assertions"] if row["assertion_id"] in current_ids]
    current_tokens = set().union(*(_tokens(row["content"]["text"]) for row in current)) if current else set()
    latest_turn = max((row.get("source_turn_index", 0) for row in memory["assertions"]), default=0)
    for row in active:
        distance = max(1, latest_turn - int(row.get("source_turn_index", 0)))
        if distance <= 2:
            routes[row["assertion_id"]]["rolling"] = 1.0 / distance
        tokens = _tokens(row["content"]["text"])
        overlap = len(tokens & current_tokens) / max(1, len(tokens | current_tokens))
        if overlap > 0:
            routes[row["assertion_id"]]["lexical"] = overlap

    by_scene = defaultdict(list)
    for row in active:
        by_scene[row.get("source_scene_id")].append(row)
    for hit in analysis.get("memory_retrieval", []):
        for row in by_scene.get(hit.get("scene_id"), []):
            routes[row["assertion_id"]]["semantic"] = max(
                routes[row["assertion_id"]].get("semantic", 0.0), float(hit.get("fusion_score") or 0.0)
            )

    neighbor_ids = set()
    for edge in memory["graph"]["edges"]:
        if edge.get("status") not in {"active", "unresolved"}:
            continue
        if edge.get("source") in current_ids:
            neighbor_ids.add(edge.get("target"))
        if edge.get("target") in current_ids:
            neighbor_ids.add(edge.get("source"))
    for assertion_id in neighbor_ids:
        if any(row["assertion_id"] == assertion_id for row in active):
            routes[assertion_id]["graph"] = 1.0

    topics = {row.get("topic_id") for row in memory.get("episodes", []) if current_ids & set(row.get("assertion_ids", []))}
    episode_topic = {row["episode_id"]: row.get("topic_id") for row in memory.get("episodes", [])}
    for row in active:
        if topics and episode_topic.get(row.get("episode_id")) in topics:
            routes[row["assertion_id"]]["temporal_thread"] = 1.0
    return routes


def retrieve(
    analysis: dict[str, Any], memory: dict[str, Any], outcome: dict[str, Any], *, max_evidence_items: int = 8
) -> dict[str, Any]:
    """Retrieve eligible assertion evidence and build a bounded ContextPacket."""
    current_ids = set(outcome.get("assertion_ids", []))
    current = [row for row in memory["assertions"] if row["assertion_id"] in current_ids]
    packet_current = current[:max_evidence_items]
    packet_current_ids = {row["assertion_id"] for row in packet_current}
    routes = _candidate_routes(analysis, memory, current_ids)
    excluded = defaultdict(int)
    candidates = []
    for row in memory["assertions"]:
        if row["assertion_id"] in current_ids:
            continue
        status = row.get("revision_status", "unresolved")
        if status in INELIGIBLE:
            excluded[status] += 1
            continue
        if not row.get("autobiographical", True):
            excluded["non_autobiographical"] += 1
            continue
        route = routes.get(row["assertion_id"], {})
        # Recency by itself is insufficient to manufacture continuity.
        if not set(route) & {"lexical", "semantic", "graph", "temporal_thread"}:
            excluded["no_verified_route"] += 1
            continue
        score = (
            2.0 * route.get("lexical", 0.0)
            + 1.5 * min(1.0, route.get("semantic", 0.0) * 65.0)
            + 1.4 * route.get("graph", 0.0)
            + .8 * route.get("temporal_thread", 0.0)
            + .25 * route.get("rolling", 0.0)
        )
        candidates.append((round(score, 6), row, route))
    candidates.sort(key=lambda item: (-item[0], -int(item[1].get("source_turn_index", 0)), item[1]["assertion_id"]))

    selected, per_turn = [], defaultdict(int)
    historical_limit = max(0, min(4, max_evidence_items - len(packet_current)))
    for score, row, route in candidates:
        if len(selected) >= historical_limit:
            break
        turn = row.get("source_turn_index")
        if per_turn[turn] >= 1:
            excluded["diversity_limit"] += 1
            continue
        per_turn[turn] += 1
        selected.append({
            "assertion_id": row["assertion_id"], "evidence_refs": row.get("evidence_refs", []),
            "text": row["content"]["text"], "claim_type": row["claim_type"],
            "revision_status": row["revision_status"], "epistemic_status": row["epistemic_status"],
            "source_turn_index": turn, "source_turn_id": row.get("source_turn_id"),
            "source_scene_id": row.get("source_scene_id"), "score": score,
            "selection_routes": sorted(route), "selection_reason": "task_conditioned_evidence_match",
        })

    revision_links = [
        row for row in memory.get("revision_links", [])
        if row.get("source") in current_ids or row.get("target") in current_ids
    ]
    superseded_ids = sorted({row.get("target") for row in revision_links if row.get("type") == "supersedes" and row.get("target")})
    superseded_evidence = [
        {
            "assertion_id": row["assertion_id"], "text": row["content"]["text"],
            "source_turn_index": row.get("source_turn_index"), "revision_status": row.get("revision_status"),
            "evidence_refs": row.get("evidence_refs", []),
        }
        for row in memory["assertions"] if row["assertion_id"] in superseded_ids
    ]
    unresolved_ids = [
        row["id"] for row in memory.get("unresolved", [])
        if row.get("source_assertion_id") in current_ids or current_ids.intersection(row.get("candidate_assertion_ids", []))
    ]
    selected_ids = packet_current_ids | {row["assertion_id"] for row in selected}
    graph_edges = [
        row for row in memory["graph"]["edges"]
        if row.get("source") in selected_ids and row.get("target") in selected_ids
    ]
    graph_node_ids = sorted(selected_ids | {row.get("source") for row in graph_edges} | {row.get("target") for row in graph_edges})
    current_items = [{
        "assertion_id": row["assertion_id"], "evidence_refs": row.get("evidence_refs", []),
        "text": row["content"]["text"], "claim_type": row["claim_type"],
        "revision_status": row["revision_status"], "epistemic_status": row["epistemic_status"],
        "source_turn_index": row["source_turn_index"],
    } for row in packet_current]
    task = "reflect_changed_interpretation" if revision_links else "reflect_current_narrative"
    packet = {
        "schema_version": RETRIEVAL_VERSION,
        "packet_id": _stable("ctx", memory["memory_generation"], memory["revision"], task),
        "task": task,
        "source_turn_index": outcome.get("source_turn_index"),
        "state_revision": memory["revision"],
        "memory_generation": memory["memory_generation"],
        "current_turn_evidence": current_items,
        "active_episode": [row for row in memory.get("episodes", []) if current_ids & set(row.get("assertion_ids", []))],
        "relevant_prior_evidence": selected,
        "corrections_and_supersessions": revision_links,
        "superseded_evidence": superseded_evidence,
        "unresolved_conflicts": [row for row in memory.get("unresolved", []) if row["id"] in unresolved_ids],
        "explicit_narrative_relations": graph_edges,
        "interpretation_constraints": [
            "Similarity is candidate evidence, not identity or truth.",
            "Do not present superseded or rejected assertions as current.",
            "If historical scope is ambiguous, respond from the current turn only.",
        ],
        "excluded_candidates_summary": [{"reason": key, "count": value} for key, value in sorted(excluded.items())],
        "evidence_item_limit": max_evidence_items,
        "selected_item_count": len(current_items) + len(selected),
        "abstained_from_history": not bool(selected),
        "retrieval_trace": {
            "selected_assertion_ids": sorted(selected_ids),
            "selected_graph_node_ids": graph_node_ids,
            "selected_edge_ids": [row["edge_id"] for row in graph_edges],
            "excluded_superseded_ids": superseded_ids,
            "unresolved_assertion_ids": unresolved_ids,
            "retrieval_policy_version": RETRIEVAL_VERSION,
        },
    }
    return packet


def apply_memory_harness(
    analysis: dict[str, Any], delta: dict[str, Any], state_snapshot: dict[str, Any], *,
    memory_generation: str = "", session_id: str | None = None, max_evidence_items: int = 8,
) -> dict[str, Any]:
    """Attach a proposed canonical update and retrieval packet to analysis."""
    memory, outcome = propose_update(
        analysis, state_snapshot, memory_generation=memory_generation, session_id=session_id
    )
    packet = retrieve(analysis, memory, outcome, max_evidence_items=max_evidence_items)
    delta.setdefault("world", {})["canonical_memory"] = memory
    analysis["memory_update"] = outcome
    analysis["context_packet"] = packet
    analysis["canonical_memory"] = {
        "schema_version": SCHEMA_VERSION,
        "revision": memory["revision"],
        "active_assertion_count": sum(row.get("revision_status") == "active" for row in memory["assertions"]),
        "superseded_assertion_count": sum(row.get("revision_status") == "superseded" for row in memory["assertions"]),
        "unresolved_count": len(memory["unresolved"]),
    }
    return {"memory_update": outcome, "context_packet": packet}


def finalize_commit(
    analysis: dict[str, Any], delta: dict[str, Any], *, turn_id: int, session_id: str,
    memory_generation: str, recorded_at: str,
) -> None:
    """Bind proposed records to committed database identities inside the writer."""
    memory = delta.get("world", {}).get("canonical_memory")
    if not memory or not analysis.get('memory_update'):
        return
    source_index = analysis.get("memory_update", {}).get("source_turn_index")
    assertion_ids = set(analysis.get("memory_update", {}).get("assertion_ids", []))
    evidence_ids = set(analysis.get("memory_update", {}).get("evidence_ids", []))
    for row in memory["assertions"]:
        if row["assertion_id"] in assertion_ids:
            row["source_turn_id"] = turn_id; row["source_session_id"] = session_id; row["recorded_at"] = recorded_at
    for row in memory["evidence"]:
        if row["evidence_id"] in evidence_ids:
            row["source_turn_id"] = turn_id; row["source_session_id"] = session_id
    for row in memory["episodes"]:
        if row.get("source_turn_index") == source_index and row.get("source_turn_id") is None:
            row["source_turn_id"] = turn_id; row["session_id"] = session_id
    memory["memory_generation"] = memory_generation
    for event in memory.get("outbox", []):
        if event.get("event_id") == analysis.get("memory_update", {}).get("outbox_event_id"):
            event["status"] = "committed"; event["source_turn_id"] = turn_id; event["memory_generation"] = memory_generation
    analysis["memory_update"]["status"] = "committed"
    analysis["memory_update"]["source_turn_id"] = turn_id
    analysis["memory_update"]["memory_generation"] = memory_generation
    analysis["context_packet"]["memory_generation"] = memory_generation
    analysis["context_packet"]["source_turn_id"] = turn_id


def prune_session(memory: dict[str, Any], session_id: str) -> dict[str, Any]:
    """Delete canonical records derived solely from one deleted session."""
    value = copy.deepcopy(memory)
    removed_assertions = {row["assertion_id"] for row in value.get("assertions", []) if row.get("source_session_id") == session_id}
    removed_evidence = {row["evidence_id"] for row in value.get("evidence", []) if row.get("source_session_id") == session_id}
    removed_turn_ids = {
        row.get("source_turn_id") for row in value.get("evidence", [])
        if row.get("source_session_id") == session_id and row.get("source_turn_id") is not None
    }
    removed_episodes = {row["episode_id"] for row in value.get("episodes", []) if row.get("session_id") == session_id}
    value["assertions"] = [row for row in value.get("assertions", []) if row["assertion_id"] not in removed_assertions]
    for row in value["assertions"]:
        row["supersedes"] = [item for item in row.get("supersedes", []) if item not in removed_assertions]
        if row.get("superseded_by") in removed_assertions:
            row["superseded_by"] = None
            row["revision_status"] = "active"
    value["evidence"] = [row for row in value.get("evidence", []) if row["evidence_id"] not in removed_evidence]
    value["episodes"] = [row for row in value.get("episodes", []) if row.get("session_id") != session_id]
    removed_nodes = removed_assertions | removed_evidence | removed_episodes | {
        row["id"] for row in value.get("graph", {}).get("nodes", [])
        if row.get("source_session_id") == session_id
    }
    value.setdefault("graph", {})["nodes"] = [row for row in value.get("graph", {}).get("nodes", []) if row["id"] not in removed_nodes]
    valid = {row["id"] for row in value["graph"]["nodes"]}
    value["graph"]["edges"] = [row for row in value["graph"].get("edges", []) if row.get("source") in valid and row.get("target") in valid]
    value["revision_links"] = [row for row in value.get("revision_links", []) if row.get("source") in valid and row.get("target") in valid]
    value["unresolved"] = [
        row for row in value.get("unresolved", [])
        if row.get("source_assertion_id") not in removed_assertions
        and not removed_assertions.intersection(row.get("candidate_assertion_ids", []))
    ]
    value["outbox"] = [row for row in value.get("outbox", []) if row.get("source_turn_id") not in removed_turn_ids]
    value["revision"] = int(value.get("revision", 0)) + 1
    return value
