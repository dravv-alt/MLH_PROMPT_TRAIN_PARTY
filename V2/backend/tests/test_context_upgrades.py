"""Focused tests for semantic topic and restricted discourse context upgrades."""
from app.services.semantic_topics import apply_semantic_topic_assignment
from app.services.revision_classifier import classify_revision
from app.services.nlp_engine import analyze_turn


def embedding(values):
    vector = [0.0] * 384
    for index, value in values.items():
        vector[index] = value
    return {"status": "ready", "pooled": vector, "version": "test-minilm"}


def test_semantic_topic_joins_paraphrases_and_drives_recurring_strategy():
    state = {"semantic_topics": []}
    assignments = []
    for item in (
        embedding({0: 1.0}),
        embedding({0: .98, 1: .02}),
        embedding({0: .96, 1: .04}),
    ):
        analysis = {"strategy": "standard", "strategy_evidence": {"content_tokens": 8}}
        delta = {"turns": [{}]}
        assignments.append(apply_semantic_topic_assignment(analysis, delta, state, item, threshold=.45))
        state["semantic_topics"] = delta["semantic_topics"]
    assert len({row["topic_id"] for row in assignments}) == 1
    assert assignments[-1]["prior_topic_turns"] == 2
    assert analysis["strategy"] == "recurring"


def test_semantic_topic_keeps_unrelated_dense_vector_separate():
    state = {"semantic_topics": []}
    first_analysis = {"strategy": "standard", "strategy_evidence": {"content_tokens": 8}}
    first_delta = {"turns": [{}]}
    apply_semantic_topic_assignment(first_analysis, first_delta, state, embedding({0: 1.0}), threshold=.45)
    state["semantic_topics"] = first_delta["semantic_topics"]
    next_analysis = {"strategy": "standard", "strategy_evidence": {"content_tokens": 8}}
    next_delta = {"turns": [{}]}
    result = apply_semantic_topic_assignment(next_analysis, next_delta, state, embedding({1: 1.0}), threshold=.45)
    assert result["decision"] == "created"
    assert result["topic_id"] != first_analysis["topic_id"]


def test_restricted_discourse_context_preserves_negation_modality_and_roles(monkeypatch):
    from app.services import dmrst
    monkeypatch.setattr(dmrst, "parse_dmrst", lambda _: {"status": "unavailable", "reason": "test", "edus": [], "tree": []})
    analysis, _, _ = analyze_turn(
        "I might not accept the offer because I want more time.",
        {},
        {"alias_key": "context-upgrade-tests", "mathematical_profile": "low_resource"},
    )
    frames = analysis["discourse_context"]["current_propositions"]
    assert any(row["polarity"] == "negative" for row in frames)
    assert any(any(item["category"] == "epistemic" for item in row["modality"]) for row in frames)
    assert any(any(actor["role"] == "agent" for actor in row["actors"]) for row in frames)


def test_maxent_artifact_is_advisory_and_versioned():
    result = classify_revision("Actually, I do not think that explanation fits.", "Maybe that was the reason.")
    assert result["status"] == "ready"
    assert result["model"] == "tfidf-logistic-maxent"
    assert result["training_scope"]["independent_human_validation"] is False
    assert {row["label"] for row in result["labels"]} == {"correction", "uncertainty", "preference_revision"}


def test_correction_scope_does_not_supersede_unrelated_prior_claims(monkeypatch):
    from app.services import dmrst
    monkeypatch.setattr(dmrst, "parse_dmrst", lambda _: {"status": "unavailable", "reason": "test", "edus": [], "tree": []})
    config = {"alias_key": "scope-tests", "mathematical_profile": "low_resource"}
    _, state, _ = analyze_turn(
        "I feel tired, and I am already thinking about what I need to achieve next.", {}, config
    )
    analysis, _, _ = analyze_turn(
        "Actually, I do not need to prove that I am worthy. I am excited about the internship.", state, config
    )
    links = analysis["discourse_context"]["revision_links"]
    # No shared content with the prior tiredness/next-goal claims: no broad
    # supersession link is permitted.
    assert links == []
    revisions = analysis["mathematical_models"]["evidence_belief_revision"]["revisions"]
    assert revisions and revisions[0]["target"] is None
