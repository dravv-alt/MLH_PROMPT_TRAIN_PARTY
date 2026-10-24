"""Stable MiniLM topic assignment layered over the pure lexical analyzer.

The embedding is supplied by the caller; this module performs no model or
database access. Hashed topics remain in state for backward compatibility,
while ``semantic_topics`` becomes the authoritative user-visible assignment
when a version-compatible 384-dimensional embedding is available.
"""
from __future__ import annotations

import copy
import math
from typing import Any


VERSION = "minilm384.leader-exemplar.v2"
DEFAULT_THRESHOLD = 0.45
MAX_EXEMPLARS = 4


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    denominator = math.sqrt(sum(value * value for value in left) * sum(value * value for value in right))
    if not denominator:
        return 0.0
    # Dense semantic cosine is allowed to be negative.
    return max(-1.0, min(1.0, sum(a * b for a, b in zip(left, right)) / denominator))


def _centroid(topic: dict[str, Any]) -> list[float]:
    count = max(1, int(topic.get("count", 0)))
    return [float(value) / count for value in topic.get("sum", [])]


def _topic_similarity(vector: list[float], topic: dict[str, Any]) -> tuple[float, str]:
    values = [(_cosine(vector, _centroid(topic)), "centroid")]
    values.extend((_cosine(vector, exemplar), "exemplar") for exemplar in topic.get("exemplars", []))
    return max(values, key=lambda item: item[0])


def apply_semantic_topic_assignment(
    analysis: dict[str, Any],
    delta: dict[str, Any],
    state_snapshot: dict[str, Any],
    embedding: dict[str, Any] | None,
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """Mutate proposed analysis/delta with a deterministic semantic topic.

    Returns a small diagnostic object. The operation remains safe to repeat on
    a fresh delta because the caller owns the uncommitted snapshot.
    """
    if not embedding or embedding.get("status") != "ready":
        diagnostic = {
            "status": "fallback",
            "method": "hashed_term_frequency",
            "reason": (embedding or {}).get("reason", "embedding_unavailable"),
        }
        analysis["topic_assignment"] = diagnostic
        return diagnostic

    vector = [float(value) for value in embedding.get("pooled", [])]
    if len(vector) != 384 or not all(math.isfinite(value) for value in vector):
        diagnostic = {"status": "fallback", "method": "hashed_term_frequency", "reason": "invalid_embedding"}
        analysis["topic_assignment"] = diagnostic
        return diagnostic

    content_count = int(analysis.get("strategy_evidence", {}).get("content_tokens", 0))
    if content_count < 4:
        analysis["topic_id"] = None
        diagnostic = {"status": "unassigned", "method": VERSION, "reason": "insufficient_content"}
        analysis["topic_assignment"] = diagnostic
        return diagnostic

    topics = copy.deepcopy(state_snapshot.get("semantic_topics", []))
    compatible = [row for row in topics if row.get("version") == embedding.get("version") and len(row.get("sum", [])) == 384]
    scored = sorted(
        ((*_topic_similarity(vector, row), row) for row in compatible),
        key=lambda item: (-item[0], item[2]["id"]),
    )
    best_score, similarity_basis, best = scored[0] if scored else (None, None, None)
    prior_count = 0
    if best is not None and best_score is not None and best_score >= threshold:
        topic_id = best["id"]
        prior_count = int(best["count"])
        best["sum"] = [left + right for left, right in zip(best["sum"], vector)]
        best["count"] = prior_count + 1
        best["exemplars"] = [*best.get("exemplars", []), vector][-MAX_EXEMPLARS:]
        # Replace the corresponding copied entry, retaining incompatible
        # historical versions without comparing across vector spaces.
        topics = [best if row.get("id") == topic_id else row for row in topics]
        decision = "joined"
    else:
        numeric = [int(row["id"][1:]) for row in topics if str(row.get("id", "")).startswith("s") and str(row["id"])[1:].isdigit()]
        topic_id = f"s{max(numeric, default=0) + 1:06d}"
        topics.append({
            "id": topic_id,
            "sum": vector,
            "count": 1,
            "version": embedding.get("version"),
            "exemplars": [vector],
        })
        decision = "created"

    analysis["topic_id"] = topic_id
    analysis["topics"] = [{"id": row["id"], "count": row["count"]} for row in topics if row.get("version") == embedding.get("version")]
    analysis["vectorizer_version"] = embedding.get("version")
    analysis["strategy_evidence"]["prior_topic_turns"] = prior_count
    current_strategy = analysis.get("strategy")
    if current_strategy == "standard" and prior_count >= 2:
        analysis["strategy"] = "recurring"
    if delta.get("turns"):
        delta["turns"][-1]["topic_id"] = topic_id
        delta["turns"][-1]["topic_method"] = VERSION
    delta["semantic_topics"] = topics
    diagnostic = {
        "status": "ready",
        "method": VERSION,
        "decision": decision,
        "topic_id": topic_id,
        "similarity": round(best_score, 6) if best_score is not None else None,
        "similarity_basis": similarity_basis,
        "threshold": threshold,
        "prior_topic_turns": prior_count,
        "embedding_version": embedding.get("version"),
        "order_sensitive": True,
    }
    analysis["topic_assignment"] = diagnostic
    return diagnostic
