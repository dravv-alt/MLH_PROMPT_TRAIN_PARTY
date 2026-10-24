"""Train a tiny development MaxEnt model from evaluator annotations.

The held-out canonical topic is never used for fitting. This artifact is useful
for integration experiments, not for independent accuracy claims. It must not
be evaluated on any training topic as though it were unseen data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline


BACKEND = Path(__file__).resolve().parents[1]
WORKSPACE = BACKEND.parents[1]
CLASSES = ["correction", "uncertainty", "preference_revision"]
HELD_OUT = "achievement_exhaustion_and_the_meaning_of_success"


def labels(expected: list[str]) -> list[int]:
    value = " ".join(expected).casefold()
    return [
        int(any(term in value for term in ("`corrected`", "`superseded`", "explicit correction", "rejected"))),
        int(any(term in value for term in ("`tentative`", "`unresolved`", "uncertain", "qualified wording"))),
        int(any(term in value for term in ("`preference`", "refine the user's preference", "changing preference", "revised preference"))),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=WORKSPACE / "sanctuary_v2_evaluation_dataset.json")
    parser.add_argument("--output", type=Path, default=BACKEND / "models" / "revision_maxent.joblib")
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    texts, targets, groups = [], [], []
    held_texts, held_targets = [], []
    for topic in dataset["topics"]:
        previous = ""
        for turn in topic["turns"]:
            item = f"{previous} [TURN] {turn['user_prompt']}"
            target = labels(turn["expected_state"])
            if topic["topic_id"] == HELD_OUT:
                held_texts.append(item);held_targets.append(target)
            else:
                texts.append(item);targets.append(target);groups.append(topic["topic_id"])
            previous = turn["user_prompt"]
    matrix = np.asarray(targets, dtype=np.int64)
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), analyzer="word", min_df=1, max_features=4096, sublinear_tf=True)),
        ("classifier", MultiOutputClassifier(LogisticRegression(max_iter=1000, class_weight="balanced", random_state=17))),
    ])
    pipeline.fit(texts, matrix)
    held_matrix = np.asarray(held_targets, dtype=np.int64)
    held_predictions = pipeline.predict(held_texts)
    precision, recall, f1, support = precision_recall_fscore_support(
        held_matrix,
        held_predictions,
        average=None,
        zero_division=0,
    )
    held_out_metrics = {
        name: {"precision": round(float(precision[i]), 4), "recall": round(float(recall[i]), 4), "f1": round(float(f1[i]), 4), "positives": int(support[i])}
        for i, name in enumerate(CLASSES)
    }
    artifact = {
        "version": "revision-maxent.dev.v1",
        "classes": CLASSES,
        "pipeline": pipeline,
        "training_scope": {
            "source": str(args.dataset.resolve()),
            "topics": sorted(set(groups)),
            "held_out_topic": HELD_OUT,
            "examples": len(texts),
            "label_source": "free-text evaluator annotations mapped by documented development heuristics",
            "independent_human_validation": False,
            "held_out_development_metrics": held_out_metrics,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, args.output, compress=3)
    print(json.dumps({"output": str(args.output.resolve()), "examples": len(texts), "positives": dict(zip(CLASSES, matrix.sum(axis=0).tolist())), "held_out": HELD_OUT, "held_out_metrics": held_out_metrics}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
