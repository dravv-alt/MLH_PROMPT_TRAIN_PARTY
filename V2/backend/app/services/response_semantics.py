"""Model-based grounding checks and comparative scoring for local NLG drafts.

This module deliberately contains no domain noun blacklist and no response
templates.  It compares generated text with the evidence in a ResponsePlan by
using the already provisioned local NLI worker.  NLI values are uncalibrated;
they are used only to reject direct contradictions and rank otherwise valid
drafts, never as probabilities of human truth.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from app.services.neural_runtime import NLI


VERSION = "sanctuary.response-semantics.v1"


def warm_semantic_worker() -> None:
    """Start loading the existing local NLI resource without waiting for it."""
    NLI.start()


def _pair(pair_id: str, premise: str, hypothesis: str, purpose: str) -> dict[str, str]:
    return {
        "id": pair_id,
        "premise": premise.strip(),
        "hypothesis": hypothesis.strip(),
        "purpose": purpose,
    }


def _copy_similarity(plan: dict[str, Any], response: str) -> float:
    """Return a diagnostic near-copy measure; it is not a validity rule."""
    claims = [row.get("text", "") for row in plan.get("claims_to_communicate", []) if row.get("text")]
    if not claims or not response.strip():
        return 0.0
    return max(SequenceMatcher(None, claim.casefold(), response.casefold()).ratio() for claim in claims)


def evaluate_candidates(
    plan: dict[str, Any],
    candidates: list[str],
    *,
    budget: float = 5.0,
) -> list[dict[str, Any]]:
    """Compare drafts with current evidence in one bounded local NLI request.

    Direct contradiction is the only semantic hard failure.  Entailment and
    novelty contribute to comparative ranking so the realizer can prefer a
    grounded synthesis over a near-copy without treating NLI as calibrated.
    """
    approved = [row for row in plan.get("claims_to_communicate", []) if row.get("text")]
    rejected = [
        row for row in plan.get("correction_context", {}).get("rejected_current_claims", [])
        if row.get("text")
    ]
    historical = [
        row for row in plan.get("memory_context", {}).get("historical_evidence", [])
        if row.get("text") and row.get("revision_status") == "active"
    ]
    evidence = " ".join([*(row["text"] for row in approved), *(row["text"] for row in historical)]).strip()
    pairs: list[dict[str, str]] = []
    for candidate_index, response in enumerate(candidates):
        prefix = f"candidate_{candidate_index}"
        if evidence:
            pairs.append(_pair(f"{prefix}:support", evidence, response, "evidence_support"))
        for claim_index, claim in enumerate(approved):
            pairs.append(_pair(f"{prefix}:claim:{claim_index}", response, claim["text"], "claim_coverage"))
        for rejected_index, claim in enumerate(rejected):
            pairs.append(_pair(f"{prefix}:correction:{rejected_index}", claim["text"], response, "correction_consistency"))

    base = [
        {
            "status": "unavailable",
            "reason": "no_semantic_pairs",
            "is_valid": False,
            "score": 1.0 - _copy_similarity(plan, response),
            "copy_similarity": round(_copy_similarity(plan, response), 6),
            "violations": [],
            "pairs": [],
            "version": VERSION,
        }
        for response in candidates
    ]
    if not pairs:
        return base

    result = NLI.request({"task": "semantic_validation", "pairs": pairs}, budget)
    if result.get("status") != "ready":
        for row in base:
            row["reason"] = result.get("reason", "semantic_worker_unavailable")
        return base

    grouped: dict[int, list[dict[str, Any]]] = {index: [] for index in range(len(candidates))}
    for row in result.get("pairs", []):
        try:
            index = int(row["id"].split(":", 1)[0].split("_")[-1])
        except (KeyError, ValueError):
            continue
        if index in grouped:
            grouped[index].append(row)

    evaluated: list[dict[str, Any]] = []
    for index, response in enumerate(candidates):
        rows = grouped[index]
        violations: list[str] = []
        support_scores: list[float] = []
        coverage_scores: list[float] = []
        for row in rows:
            scores = row["scores"]
            strongest = max(scores, key=scores.get)
            if row["purpose"] == "evidence_support":
                support_scores.append(scores["entailment"] - scores["contradiction"])
                if strongest == "contradiction":
                    violations.append("semantic_grounding_contradiction")
                elif strongest == "neutral":
                    violations.append("semantic_response_not_supported")
            elif row["purpose"] == "claim_coverage":
                coverage_scores.append(scores["entailment"] - scores["contradiction"])
                if strongest == "contradiction":
                    violations.append("semantic_claim_contradiction")
            elif row["purpose"] == "correction_consistency" and strongest == "contradiction":
                violations.append("semantic_correction_contradiction")

        copy_similarity = _copy_similarity(plan, response)
        semantic_components = support_scores + coverage_scores
        semantic_score = sum(semantic_components) / len(semantic_components) if semantic_components else 0.0
        # Novel wording is a soft preference only. Semantic consistency remains
        # the gate, preventing novelty from rewarding unsupported invention.
        comparative_score = semantic_score + (1.0 - copy_similarity) * 0.15
        evaluated.append(
            {
                "status": "ready",
                "is_valid": not violations,
                "score": round(comparative_score, 6),
                "semantic_score": round(semantic_score, 6),
                "copy_similarity": round(copy_similarity, 6),
                "violations": sorted(set(violations)),
                "pairs": rows,
                "version": result.get("version", VERSION),
                "notice": "NLI scores are uncalibrated comparative signals, not probabilities of truth.",
            }
        )
    return evaluated
