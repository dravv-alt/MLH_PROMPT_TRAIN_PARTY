"""Optional small MaxEnt classifier for discourse-revision suggestions."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any


ARTIFACT = Path(__file__).resolve().parents[2] / "models" / "revision_maxent.joblib"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any] | None:
    if not ARTIFACT.is_file():
        return None
    try:
        import joblib
        value = joblib.load(ARTIFACT)
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def classify_revision(text: str, previous_text: str | None = None) -> dict[str, Any]:
    artifact = _load()
    if not artifact:
        return {"status": "unavailable", "reason": "artifact_missing", "labels": []}
    model = artifact["pipeline"]
    model_input = f"{previous_text or ''} [TURN] {text}"
    probabilities = model.predict_proba([model_input])
    labels = []
    for index, name in enumerate(artifact["classes"]):
        estimator = model.named_steps["classifier"].estimators_[index]
        positive_index = list(estimator.classes_).index(1)
        score = float(probabilities[index][0][positive_index])
        labels.append({"label": name, "score": round(score, 6), "suggested": score >= .5})
    return {
        "status": "ready",
        "model": "tfidf-logistic-maxent",
        "version": artifact["version"],
        "labels": labels,
        "training_scope": artifact["training_scope"],
        "notice": "Advisory development classifier; scores are not calibrated truth probabilities and do not override explicit rules.",
    }


def clear_revision_classifier_cache() -> None:
    _load.cache_clear()
