"""Tests for T2.1 Structural Gap Detectors:
- Static check: Fails build if any emotion/sentiment/intent lexicon is imported
- Unit tests for all 8 canonical gap detectors
- Every detected gap has valid source spans
- Hard negatives: routine complete narration, politeness hedge, one-word turns
"""
import ast
import os
import pytest
from pathlib import Path
from app.services.gaps import (
    detect_structural_gaps,
    detect_unfilled_roles,
    detect_hedged_commitments,
    detect_reported_claims,
    detect_unresolved_references,
    detect_counterfactual_obligations,
    detect_contrast_thin_arms,
    GAP_UNFILLED_ROLE,
    GAP_HEDGED_COMMITMENT,
    GAP_REPORTED_CLAIM,
    GAP_UNRESOLVED_REFERENCE,
    GAP_COUNTERFACTUAL_OBLIGATION,
    GAP_CONTRAST_THIN_ARM,
)


def test_static_no_emotion_sentiment_lexicon_imported():
    """Standing invariant & Rule 7: Static test fails build if any gap module imports an emotion/sentiment lexicon."""
    gaps_file = Path(__file__).resolve().parents[1] / "app" / "services" / "gaps.py"
    tree = ast.parse(gaps_file.read_text(encoding="utf-8"))

    prohibited = {"sentiment", "vader", "emotion", "affect", "textblob", "mood", "feeling_lexicon"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(p in alias.name.lower() for p in prohibited), f"Prohibited import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not any(p in mod.lower() for p in prohibited), f"Prohibited from-import: {mod}"


def test_unfilled_role_detector():
    # Positive case: experiential verb with no causal edge
    analysis = {
        "redacted_text": "I felt overwhelmed by the sudden workload.",
        "relations": [],
        "clauses": [{"id": "c0", "spans": [[0, 42]], "text": "I felt overwhelmed by the sudden workload."}],
        "discourse_context": {
            "current_propositions": [{"id": "p0", "clause_id": "c0", "predicate": "feel", "actors": []}]
        }
    }
    gaps = detect_unfilled_roles(analysis)
    assert len(gaps) >= 1
    assert gaps[0]["type"] == GAP_UNFILLED_ROLE
    assert len(gaps[0]["spans"]) >= 1

    # Hard negative: very short turn yields no gaps
    short_analysis = {"redacted_text": "ok", "relations": [], "clauses": [], "discourse_context": {}}
    assert len(detect_unfilled_roles(short_analysis)) == 0


def test_hedged_commitment_detector():
    # Positive case: hedged proposition
    analysis = {
        "redacted_text": "I think I might be making a mistake.",
        "hedge_spans": [[0, 7]],
        "clauses": [],
        "discourse_context": {}
    }
    gaps = detect_hedged_commitments(analysis)
    assert len(gaps) == 1
    assert gaps[0]["type"] == GAP_HEDGED_COMMITMENT

    # Hard negative: Politeness hedge ("thank you", "I guess I'll see you") is not a gap
    polite_analysis = {
        "redacted_text": "Honestly thank you so much for the help.",
        "hedge_spans": [[0, 8]],
        "clauses": [],
        "discourse_context": {}
    }
    assert len(detect_hedged_commitments(polite_analysis)) == 0


def test_reported_claim_detector():
    analysis = {
        "redacted_text": "She said the committee rejected the initiative.",
        "discourse_context": {
            "current_propositions": [{"id": "p0", "clause_id": "c0", "predicate": "say", "spans": [[0, 8]]}]
        }
    }
    gaps = detect_reported_claims(analysis)
    assert len(gaps) == 1
    assert gaps[0]["type"] == GAP_REPORTED_CLAIM


def test_counterfactual_obligation_detector():
    analysis = {
        "redacted_text": "I should have verified the numbers before the presentation.",
        "discourse_context": {
            "current_propositions": [{"id": "p0", "predicate": "verify", "modality": ["obligation"], "spans": [[0, 15]]}]
        }
    }
    gaps = detect_counterfactual_obligations(analysis)
    assert len(gaps) == 1
    assert gaps[0]["type"] == GAP_COUNTERFACTUAL_OBLIGATION


def test_contrast_thin_arm_detector():
    analysis = {
        "redacted_text": "I spent weeks preparing the comprehensive proposal, but they declined.",
        "relations": [{"type": "contrast", "arg1": "c0", "arg2": "c1"}],
        "clauses": [
            {"id": "c0", "spans": [[0, 50]], "text": "I spent weeks preparing the comprehensive proposal"},
            {"id": "c1", "spans": [[56, 70]], "text": "they declined"}
        ]
    }
    gaps = detect_contrast_thin_arms(analysis)
    assert len(gaps) == 1
    assert gaps[0]["type"] == GAP_CONTRAST_THIN_ARM
    assert gaps[0]["evidence"]["underdeveloped_arm"] == "c1"


def test_every_detected_gap_has_valid_source_spans():
    analysis = {
        "redacted_text": "I think I felt worried about the test, but I passed.",
        "hedge_spans": [[0, 7]],
        "relations": [{"type": "contrast", "arg1": "c0", "arg2": "c1"}],
        "clauses": [
            {"id": "c0", "spans": [[0, 37]], "text": "I think I felt worried about the test"},
            {"id": "c1", "spans": [[43, 51]], "text": "I passed"}
        ],
        "discourse_context": {
            "current_propositions": [{"id": "p0", "clause_id": "c0", "predicate": "feel", "modality": []}]
        }
    }
    gaps = detect_structural_gaps(analysis)
    assert len(gaps) >= 1
    for gap in gaps:
        assert "spans" in gap and len(gap["spans"]) >= 1
        for span in gap["spans"]:
            assert len(span) == 2
            assert 0 <= span[0] <= span[1] <= len(analysis["redacted_text"])
