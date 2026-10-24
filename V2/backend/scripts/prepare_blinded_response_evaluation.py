"""Create a blinded A/B response-rating package with a separate answer key."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import random


BACKEND = Path(__file__).resolve().parents[1]


def records(path: Path) -> dict[tuple[str, int], dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(row["topic_id"], int(row["turn_id"])): row for row in data["records"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system-a", type=Path, required=True)
    parser.add_argument("--system-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=BACKEND / "evaluation" / "blinded_response_ratings.csv")
    parser.add_argument("--key", type=Path, default=BACKEND / "evaluation" / "blinded_response_key.json")
    args = parser.parse_args()
    left, right = records(args.system_a), records(args.system_b)
    identities = sorted(set(left).intersection(right))
    rng = random.Random(1701)
    rows, key = [], []
    for identity in identities:
        a, b = left[identity], right[identity]
        swap = bool(rng.getrandbits(1))
        response_a, response_b = (b["response_text"], a["response_text"]) if swap else (a["response_text"], b["response_text"])
        item_id = hashlib.sha256(f"{identity[0]}:{identity[1]}".encode()).hexdigest()[:12]
        rows.append({
            "item_id": item_id,
            "topic_id": identity[0],
            "turn_id": identity[1],
            "user_prompt": b["user_prompt"],
            "response_a": response_a,
            "response_b": response_b,
            "naturalness_a_1_to_5": "",
            "naturalness_b_1_to_5": "",
            "fidelity_a_1_to_5": "",
            "fidelity_b_1_to_5": "",
            "context_use_a_1_to_5": "",
            "context_use_b_1_to_5": "",
            "preferred_a_b_tie": "",
            "unsupported_claim_a_yes_no": "",
            "unsupported_claim_b_yes_no": "",
            "rater_notes": "",
        })
        key.append({
            "item_id": item_id,
            "response_a_source": "system_b" if swap else "system_a",
            "response_b_source": "system_a" if swap else "system_b",
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        writer.writeheader();writer.writerows(rows)
    args.key.write_text(json.dumps({
        "system_a": str(args.system_a.resolve()),
        "system_b": str(args.system_b.resolve()),
        "items": key,
        "status": "awaiting_independent_human_ratings",
        "minimum_required_raters": 2,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"items": len(rows), "ratings": str(args.output.resolve()), "key": str(args.key.resolve()), "status": "awaiting_independent_human_ratings"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
