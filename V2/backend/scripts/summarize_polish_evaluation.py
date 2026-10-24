"""Create the polish-mode gate report from a completed evaluator JSON."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    records = payload["records"]
    accepted = [row for row in records if row.get("response_mode") == "reflective_local_transformer"]
    edits = [1.0 - SequenceMatcher(None, row["response_text"].casefold(), row["generation"]["fallback_text"].casefold()).ratio() for row in accepted]
    histogram = Counter()
    for row in records:
        for attempt in row.get("generation", {}).get("attempts", []):
            histogram.update(attempt.get("final_violations") or attempt.get("validation", {}).get("violations", []))
    result = {
        "turns": len(records), "transformer_accepted_turns": len(accepted),
        "transformer_accepted_rate": len(accepted) / len(records) if records else 0.0,
        "mean_edit_distance_from_fallback": sum(edits) / len(edits) if edits else None,
        "violation_histogram": dict(histogram),
        "accepted_outputs": [{"topic_id": row.get("topic_id"), "user_prompt": row.get("user_prompt"),
                              "output": row.get("response_text"), "fallback": row["generation"].get("fallback_text")} for row in accepted],
    }
    result["gate_verdict"] = "keep_local_polish" if result["transformer_accepted_rate"] >= .5 and (result["mean_edit_distance_from_fallback"] or 0) > .05 else "implement_optional_hosted_default_off"
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Local polish evaluation gate", "", f"- Accepted rate: {result['transformer_accepted_rate']:.2%} ({len(accepted)}/{len(records)})",
             f"- Mean edit distance from fallback: {result['mean_edit_distance_from_fallback']}", f"- Verdict: `{result['gate_verdict']}`", "", "## Violation histogram", ""]
    lines += [f"- `{key}`: {value}" for key, value in histogram.most_common()]
    args.output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
