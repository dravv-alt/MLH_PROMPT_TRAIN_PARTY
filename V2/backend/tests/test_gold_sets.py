"""Tests for T0.2 Gold Annotation Sets:
- Verifies dev set (80 turns) schema completeness
- Verifies held-out test set (40 turns) integrity and SHA-256 hash
- Computes Cohen's kappa for inter-annotator agreement on the 25% subset
- Tests reproducibility of annotation guidelines on 5 turns
"""
import os
import json
import hashlib
import pytest
from sklearn.metrics import cohen_kappa_score


@pytest.fixture
def gold_dir():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "evaluation", "gold")


def test_dev_80_annotated_schema(gold_dir):
    dev_path = os.path.join(gold_dir, "dev_80_annotated.json")
    assert os.path.exists(dev_path), "dev_80_annotated.json missing"
    with open(dev_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 80, f"Expected 80 dev turns, found {len(data)}"
    for item in data:
        assert "turn_id" in item
        assert "text" in item and len(item["text"]) > 0
        assert "commitments" in item
        assert "relations" in item
        assert "corrections" in item
        assert "references" in item
        assert "gaps" in item
        assert "acceptable_moves" in item
        assert set(item["acceptable_moves"]).issubset({"ask", "clarify", "acknowledge", "hold"})


def test_held_out_test_integrity_and_hash(gold_dir):
    test_path = os.path.join(gold_dir, "held_out_test_40.json")
    hash_path = os.path.join(gold_dir, "TEST_HASH.txt")
    assert os.path.exists(test_path), "held_out_test_40.json missing"
    assert os.path.exists(hash_path), "TEST_HASH.txt missing"

    with open(test_path, "rb") as f:
        computed_hash = hashlib.sha256(f.read()).hexdigest()
    with open(hash_path, "r", encoding="utf-8") as f:
        recorded_hash = f.read().strip()
    assert computed_hash == recorded_hash, "Held-out test set hash does not match frozen TEST_HASH.txt!"

    with open(test_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 40, f"Expected 40 test turns, got {len(data)}"
    hard_negatives = [t for t in data if t.get("is_hard_negative")]
    assert len(hard_negatives) >= 20, f"At least 50% must be hard negatives, got {len(hard_negatives)}/40"


def test_inter_annotator_agreement_cohens_kappa(gold_dir):
    dev_path = os.path.join(gold_dir, "dev_80_annotated.json")
    ann2_path = os.path.join(gold_dir, "annotator2_dev20.json")
    with open(dev_path, "r", encoding="utf-8") as f:
        ann1 = json.load(f)[:20]
    with open(ann2_path, "r", encoding="utf-8") as f:
        ann2 = json.load(f)

    assert len(ann1) == 20
    assert len(ann2) == 20

    # 1. Primary Move Agreement
    moves1 = [t["acceptable_moves"][0] for t in ann1]
    moves2 = [t["acceptable_moves"][0] for t in ann2]
    kappa_moves = cohen_kappa_score(moves1, moves2)
    assert kappa_moves >= 0.85, f"Move agreement kappa too low: {kappa_moves}"

    # 2. Primary Gap Type Agreement
    gaps1 = [t["gaps"][0]["type"] if t["gaps"] else "no_gap" for t in ann1]
    gaps2 = [t["gaps"][0]["type"] if t["gaps"] else "no_gap" for t in ann2]
    kappa_gaps = cohen_kappa_score(gaps1, gaps2)
    assert kappa_gaps >= 0.85, f"Gap agreement kappa too low: {kappa_gaps}"

    # 3. Correction Detection Agreement
    corr1 = [1 if t["corrections"] else 0 for t in ann1]
    corr2 = [1 if t["corrections"] else 0 for t in ann2]
    kappa_corr = cohen_kappa_score(corr1, corr2)
    assert kappa_corr >= 0.85, f"Correction detection kappa too low: {kappa_corr}"

    # 4. Relation Presence Agreement
    rel1 = [1 if t["relations"] else 0 for t in ann1]
    rel2 = [1 if t["relations"] else 0 for t in ann2]
    kappa_rel = cohen_kappa_score(rel1, rel2)
    assert kappa_rel >= 0.85, f"Relation presence kappa too low: {kappa_rel}"


def test_guideline_reproduces_labels_on_5_turns(gold_dir):
    """Verify guideline rules deterministically reproduce labels on 5 sample turns."""
    dev_path = os.path.join(gold_dir, "dev_80_annotated.json")
    with open(dev_path, "r", encoding="utf-8") as f:
        turns = json.load(f)[:5]

    for turn in turns:
        # Check rule 1: If text contains 'but', relation must contain contrast
        if " but " in turn["text"].lower():
            assert any(r["type"] == "contrast" for r in turn["relations"])
        # Check rule 2: If text contains 'because', relation must contain causal
        if " because " in turn["text"].lower():
            assert any(r["type"] == "causal" for r in turn["relations"])
        # Check rule 3: Moves must be legitimate
        assert len(turn["acceptable_moves"]) >= 1
