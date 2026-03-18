"""
Unit tests for Sanctuary services
Run with: pytest tests/test_services.py
"""

import pytest
from backend.services.narrative_distiller import NarrativeDistiller
from backend.models.narrative import ConversationTurn


@pytest.fixture
def distiller():
    return NarrativeDistiller()


def test_conflict_detection(distiller):
    """Test detection of interpersonal conflict"""
    
    text = "I got into a huge fight with my mom yesterday"
    structure = distiller.distill(text, [])
    
    assert structure.trigger_type == "interpersonal_conflict"
    assert structure.trigger_domain == "family"


def test_self_judgment_detection(distiller):
    """Test detection of self-critical language"""
    
    text = "I'm such a failure and I messed everything up"
    structure = distiller.distill(text, [])
    
    assert structure.self_judgment is True
    assert structure.emotional_valence in ["negative", "very_negative"]


def test_causal_language_detection(distiller):
    """Test detection of cause-effect reasoning"""
    
    text = "I was exhausted because I hadn't slept, so I snapped at them"
    structure = distiller.distill(text, [])
    
    assert structure.causal_connections in ["emerging", "present"]


def test_temporal_clarity_detection(distiller):
    """Test detection of time sequencing"""
    
    text = "First I tried to talk to them, then they got angry, and after that I left"
    structure = distiller.distill(text, [])
    
    assert structure.temporal_clarity in ["partial", "clear"]


def test_privacy_preservation(distiller):
    """Test that distillation removes identifying info"""
    
    text = "My mom Sarah said I'll never get into Stanford like my brother John did"
    structure = distiller.distill(text, [])
    
    # Structure should not contain names or specific places
    assert structure.trigger_domain == "family"
    # The actual names shouldn't be in the structure
    structure_dict = structure.model_dump()
    assert "Sarah" not in str(structure_dict)
    assert "John" not in str(structure_dict)
    assert "Stanford" not in str(structure_dict)


def test_loss_detection(distiller):
    """Test detection of loss trigger"""
    
    text = "My grandfather passed away last month and I miss him so much"
    structure = distiller.distill(text, [])
    
    assert structure.trigger_type == "loss"
    assert structure.trigger_domain == "family"


def test_rejection_detection(distiller):
    """Test detection of rejection trigger"""
    
    text = "My friend ghosted me after I opened up to them"
    structure = distiller.distill(text, [])
    
    assert structure.trigger_type == "rejection"
    assert structure.trigger_domain == "friendship"


def test_high_arousal_detection(distiller):
    """Test detection of high emotional arousal via caps and punctuation"""
    
    text = "I AM SO DONE WITH EVERYTHING!!!"
    structure = distiller.distill(text, [])
    
    assert structure.emotional_arousal == "very_high"


def test_initial_sharing_phase(distiller):
    """Test that first message is classified as initial_sharing"""
    
    text = "Something happened at work today"
    structure = distiller.distill(text, [])
    
    assert structure.conversation_phase == "initial_sharing"


def test_neutral_valence(distiller):
    """Test neutral emotional detection"""
    
    text = "I went to the store and bought groceries"
    structure = distiller.distill(text, [])
    
    assert structure.emotional_valence == "neutral"

