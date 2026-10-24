"""Compare MiniLM leader clustering thresholds on one multi-turn topic."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


BACKEND = Path(__file__).resolve().parents[1]
WORKSPACE = BACKEND.parents[1]
sys.path.insert(0, str(BACKEND))
from app.services.neural_runtime import EMBEDDING  # noqa: E402
from app.services.semantic_topics import apply_semantic_topic_assignment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=WORKSPACE / "sanctuary_v2_evaluation_dataset.json")
    parser.add_argument("--topic", default="achievement_exhaustion_and_the_meaning_of_success")
    parser.add_argument("--output", type=Path, default=BACKEND / "evaluation" / "semantic_topic_sweep.json")
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    topic = next(row for row in dataset["topics"] if row["topic_id"] == args.topic)
    EMBEDDING.start()
    try:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline and EMBEDDING.state != "ready":
            time.sleep(.2)
        if EMBEDDING.state != "ready":
            raise RuntimeError(f"embedding worker unavailable: {EMBEDDING.state}")
        embeddings = []
        for turn in topic["turns"]:
            value = EMBEDDING.request({"text": turn["user_prompt"], "mentions": []}, 10)
            if value.get("status") != "ready":
                raise RuntimeError(str(value))
            embeddings.append(value)
    finally:
        EMBEDDING.stop()

    sweeps = {}
    for threshold in (.40, .45, .52, .60, .68):
        state = {"semantic_topics": []}
        rows = []
        for turn, embedding in zip(topic["turns"], embeddings):
            analysis = {"strategy": "standard", "strategy_evidence": {"content_tokens": 12}}
            delta = {"turns": [{"turn_index": turn["turn_id"]}]}
            diagnostic = apply_semantic_topic_assignment(analysis, delta, state, embedding, threshold=threshold)
            state["semantic_topics"] = delta["semantic_topics"]
            rows.append({"turn_id": turn["turn_id"], **diagnostic})
        sweeps[str(threshold)] = {
            "unique_topics": len({row["topic_id"] for row in rows}),
            "recurring_turns": sum(row["prior_topic_turns"] >= 2 for row in rows),
            "assignments": rows,
        }
    report = {
        "schema_version": "sanctuary.semantic-topic-sweep.v1",
        "topic": args.topic,
        "turns": len(topic["turns"]),
        "embedding_version": embeddings[0]["version"],
        "sweeps": sweeps,
        "boundary": "Descriptive sensitivity result on one authored conversation; not a tuned production-quality estimate.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: {"unique_topics": value["unique_topics"], "recurring_turns": value["recurring_turns"]} for key, value in sweeps.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
