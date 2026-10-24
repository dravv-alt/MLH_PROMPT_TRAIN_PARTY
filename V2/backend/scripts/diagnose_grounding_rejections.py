"""Audit semantic rejections without changing the evaluator or model inputs."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


SYNONYMS = (
    {"tired", "exhausted", "exhaustion", "worn", "drained", "fatigued"},
    {"achievement", "achieved", "internship", "opportunity", "completed", "task"},
    {"pressure", "expectation", "expectations", "prove", "worthy", "worth"},
    {"excited", "excitement", "happy", "proud"},
    {"enjoy", "enjoyment", "settle", "moment"},
)
STOP = {"the", "and", "that", "this", "with", "from", "have", "been", "were", "your", "you", "are", "after", "about", "into", "than", "more", "feel", "feels"}
GENERIC = {"important", "effort", "experience", "task", "event", "thing", "situation"}


def tokens(value: str) -> set[str]:
    return {word for word in re.findall(r"[a-z]+", value.casefold()) if len(word) > 2 and word not in STOP}


def related_overlap(draft: str, claims: list[str]) -> set[str]:
    draft_tokens = tokens(draft)
    claim_tokens = set().union(*(tokens(claim) for claim in claims)) if claims else set()
    overlap = draft_tokens & claim_tokens
    for group in SYNONYMS:
        if draft_tokens & group and claim_tokens & group:
            overlap.add("/".join(sorted(group & (draft_tokens | claim_tokens))))
    return overlap


def classify(attempt: dict[str, Any], claims: list[str]) -> tuple[str, str]:
    semantic = attempt["semantic_validation"]
    violations = set(semantic.get("violations", []))
    draft = attempt.get("rejected_draft") or attempt.get("raw_draft", "")
    overlap = related_overlap(draft, claims)
    if "semantic_claim_contradiction" in violations:
        return "a", "NLI reports a contradiction to an approved claim; retain rejection pending manual review."
    if "semantic_response_not_supported" in violations and overlap and not (tokens(draft) & GENERIC):
        return "b", "NLI support pair was neutral despite shared content/synonym evidence; candidate paraphrase needs a claim-level entailment route."
    if "semantic_response_not_supported" in violations and (tokens(draft) & GENERIC):
        return "c", "Draft is generic and harmless but does not identify enough approved content."
    return "a", "No claim-level paraphrase evidence; treat as unsupported rather than relaxing the gate."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    rows = []
    for record in source["records"]:
        plan = record.get("response_plan", {})
        claims = [row.get("text", "") for row in plan.get("claims_to_communicate", [])]
        for attempt in record.get("generation", {}).get("attempts", []):
            semantic = attempt.get("semantic_validation")
            if attempt.get("status") != "semantic_rejected" or not semantic:
                continue
            classification, reason = classify(attempt, claims)
            failed = []
            for pair in semantic.get("pairs", []):
                scores = pair.get("scores", {})
                strongest = max(scores, key=scores.get) if scores else "unavailable"
                if strongest in {"neutral", "contradiction"}:
                    failed.append({
                        "pair_id": pair.get("id"), "purpose": pair.get("purpose"),
                        "premise": pair.get("premise"), "hypothesis": pair.get("hypothesis"),
                        "scores": scores, "strongest": strongest,
                        "threshold": "argmax class must not be neutral or contradiction",
                        "method": "local NLI three-class argmax",
                    })
            rows.append({
                "topic_id": record.get("topic_id"), "turn": record.get("turn_index"),
                "attempt": attempt.get("attempt"), "draft": attempt.get("rejected_draft") or attempt.get("raw_draft"),
                "approved_claims": claims, "semantic_score": semantic.get("semantic_score"),
                "classification": classification, "classification_reason": reason,
                "content_overlap": sorted(related_overlap(attempt.get("rejected_draft") or attempt.get("raw_draft", ""), claims)),
                "failed_checks": failed,
            })
    counts = Counter(row["classification"] for row in rows)
    result = {"source": str(args.input), "rejections": len(rows), "classification_counts": dict(counts), "records": rows,
              "method_notice": "Original production gate used local NLI only; no lexical-overlap or embedding threshold was used for rejection."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown = ["# Semantic-grounding rejection diagnosis", "", f"- Source: `{args.input.name}`", f"- Rejections: {len(rows)}",
                f"- (a) genuinely unsupported / contradiction: {counts['a']}", f"- (b) likely paraphrase penalized by NLI: {counts['b']}",
                f"- (c) generic but harmless: {counts['c']}", "", "## Method", "", result["method_notice"],
                "Each JSON record includes the rejected draft, failed NLI pair, three scores, argmax threshold and method."]
    args.output.with_suffix(".md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("rejections", "classification_counts")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
