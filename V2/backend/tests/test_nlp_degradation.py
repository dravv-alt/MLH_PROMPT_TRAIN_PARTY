"""Tests for graceful degradation and hard negatives under environment/input perturbations."""
import pytest
import spacy
from app.services import nlp_engine


def test_missing_spacy_model_degrades_gracefully(monkeypatch):
    """Hard negative: when the spaCy model is missing, the system must degrade with an explicit status, not crash."""
    def mock_spacy_load(*args, **kwargs):
        raise OSError("Model 'en_core_web_sm' not found. Download it or run fallback.")

    monkeypatch.setattr(spacy, "load", mock_spacy_load)
    nlp_engine.pipeline.cache_clear()
    try:
        nlp, model_name, status = nlp_engine.pipeline()
        assert model_name == "sentence_fallback"
        assert status == "dependency_model_unavailable"
        
        # Test turn analysis under degraded pipeline
        analysis, delta, ephemeral = nlp_engine.analyze_turn(
            "I felt worried because my exam was delayed.",
            config={"alias_key": "test-degrade-key"}
        )
        assert analysis is not None
        assert analysis.get("model_version") == "sentence_fallback"
        assert analysis.get("parser_fallback") == "dependency_model_unavailable"
        assert len(analysis.get("clauses", [])) >= 1
    finally:
        nlp_engine.pipeline.cache_clear()


def test_path_and_input_with_spaces_and_non_ascii():
    """Verify analysis handles non-ASCII characters, Hindi-English code-mixing, and spaces cleanly."""
    text = "Arre yaar, I was at Café Mondegar in Colaba; ghar pe everyone was stressed."
    analysis, delta, ephemeral = nlp_engine.analyze_turn(
        text,
        config={"alias_key": "test-spaces-key"}
    )
    assert analysis is not None
    assert len(analysis.get("clauses", [])) >= 1
    assert "offset_map" in ephemeral
    # Confirm entity redaction handled accented entity without failure
    assert any("Mondegar" in surface for surface in ephemeral.get("mapping", {}).values())
