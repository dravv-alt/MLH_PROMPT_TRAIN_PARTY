import copy

import numpy as np

from app.services.mathematical_models import (
    CLAUSE_LABELS,
    PHASES,
    configuration,
    crf_decode,
    run_mathematical_suite,
    temperature_scale,
)
from app.services.nlp_engine import analyze_turn


CFG = {"alias_key": "math-test-key", "mathematical_profile": "low_resource"}


def test_all_filter_families_are_deterministic_bounded_and_psd():
    features = {"entity_continuity": .5, "connective_density": .25, "hedge_density": .05, "topic_novelty": .8}
    args = ("I may change the plan because the deadline moved.", [], [], features, [2, 4, 20, 8], {"detected": False}, "explanation")
    first, state = run_mathematical_suite(*args, profile="low_resource")
    second, state_two = run_mathematical_suite(*args, profile="low_resource")
    assert first == second
    assert state == state_two
    assert set(first["filters"]) == {"linear_kf", "extended_kf", "unscented_kf", "ensemble_kf", "particle_filter"}
    for result in first["filters"].values():
        estimate = np.asarray(result["estimate"])
        covariance = np.asarray(result["covariance"])
        assert np.all((0 <= estimate) & (estimate <= 1))
        assert np.allclose(covariance, covariance.T)
        assert np.linalg.eigvalsh(covariance).min() >= -1e-9
    assert first["filters"]["unscented_kf"]["alpha"] == configuration("low_resource").ukf_alpha


def test_missing_measurements_remain_uninitialized_then_update():
    missing = {name: None for name in ("entity_continuity", "connective_density", "hedge_density", "topic_novelty")}
    first, state = run_mathematical_suite("ok", [], [], missing, [0, 0, 0, 0], {"detected": False}, "insufficient", profile="low_resource")
    assert all(not any(item["initialized"]) for item in first["filters"].values())
    observed = {"entity_continuity": 1., "connective_density": 0., "hedge_density": .1, "topic_novelty": .7}
    second, _ = run_mathematical_suite("I now have enough evidence.", [], [], observed, [1, 1, 10, 5], {"detected": False}, "standard", state, "low_resource")
    assert all(all(item["initialized"]) for item in second["filters"].values())


def test_hmm_crf_bayesian_ds_revision_and_temporal_graph():
    clauses = [
        {"id": "c0", "spans": [[0, 34]], "text": "I thought I had to prove my worth."},
        {"id": "c1", "spans": [[35, 70]], "text": "But I am physically exhausted now."},
    ]
    relations = [{"id": "r0", "relation": "contrast", "arg1": "c0", "arg2": "c1", "source": "c0", "target": "c1"}]
    features = {"entity_continuity": None, "connective_density": 1., "hedge_density": .05, "topic_novelty": None}
    first, state = run_mathematical_suite("I thought I had to prove my worth. But I am physically exhausted now.", clauses, relations, features, [0, 2, 14, 10], {"detected": False}, "contrast", profile="low_resource")
    assert first["hmm"]["current_state"] in PHASES
    assert {row["label"] for row in first["crf"]["labels"]} <= set(CLAUSE_LABELS)
    assert any(edge["type"] == "contrasts_with" for edge in first["temporal_narrative_graph"]["edges"])
    assert all(abs(sum(p["mass"][k] for k in ("true", "false", "unknown")) - 1.) < 1e-5 for p in first["evidence_belief_revision"]["propositions"])

    corrected_clauses = [{"id": "c0", "spans": [[0, 91]], "text": "Actually, I do not need to prove my worth; I am excited and physically exhausted."}]
    second, _ = run_mathematical_suite(corrected_clauses[0]["text"], corrected_clauses, [], features, [0, 1, 14, 10],
                                       {"detected": True, "cue_span": [0, 8]}, "correction", state, "low_resource")
    assert second["evidence_belief_revision"]["revisions"]
    assert any(p["status"] == "superseded" for p in second["evidence_belief_revision"]["propositions"])
    assert any(edge["type"] == "supersedes" for edge in second["temporal_narrative_graph"]["edges"])
    node_ids = {node["id"] for node in second["temporal_narrative_graph"]["nodes"]}
    assert all(edge["source"] in node_ids and edge["target"] in node_ids for edge in second["temporal_narrative_graph"]["edges"])


def test_temperature_calibration_requires_labels_and_fits_positive_temperature():
    assert temperature_scale([], [])["status"] == "unavailable"
    result = temperature_scale([[3., 1.], [1., 3.], [2., 1.]], [0, 1, 0], iterations=50)
    assert result["status"] == "ready"
    assert result["temperature"] > 0


def test_partial_and_ambiguous_revision_are_not_forced_full_retractions():
    features = {"entity_continuity": None, "connective_density": 0., "hedge_density": 0., "topic_novelty": None}
    clause = lambda value: [{"id": "c0", "spans": [[0, len(value)]], "text": value}]
    initial = "I feel pressure to prove my worth at work."
    _, state = run_mathematical_suite(initial, clause(initial), [], features, [0, 1, 9, 7], {"detected": False}, "standard", profile="low_resource")
    partial = "Actually, I still feel some pressure, but physical tiredness matters too."
    result, state = run_mathematical_suite(partial, clause(partial), [], features, [0, 1, 12, 9], {"detected": True, "cue_span": [0, 8]}, "correction", state, "low_resource")
    assert result["evidence_belief_revision"]["revisions"][0]["kind"] == "explicit_partial"
    assert any(p["status"] == "disputed" for p in result["evidence_belief_revision"]["propositions"])
    unrelated = "Actually, the weather forecast changed completely."
    result, _ = run_mathematical_suite(unrelated, clause(unrelated), [], features, [0, 1, 8, 6], {"detected": True, "cue_span": [0, 8]}, "correction", state, "low_resource")
    assert result["evidence_belief_revision"]["revisions"][0]["kind"] == "ambiguous"
    assert result["evidence_belief_revision"]["revisions"][0]["target"] is None


def test_profiles_and_analyzer_integration_are_snapshot_pure(monkeypatch):
    from app.services import dmrst
    monkeypatch.setattr(dmrst, "parse_dmrst", lambda text: {"status": "unavailable", "reason": "test", "edus": [], "tree": []})
    for profile in ("low_resource", "balanced", "high_fidelity", "responsive", "stable"):
        assert configuration(profile).profile == profile
    state = {}
    before = copy.deepcopy(state)
    analysis, delta, _ = analyze_turn("I am tired, but I want to enjoy this achievement.", state, CFG)
    assert state == before
    assert analysis["mathematical_models"]["profile"] == "low_resource"
    assert delta["mathematical_state"]["turn"] == 1
    assert analysis["mathematical_models"]["decision_boundary"].startswith("experimental enrichment")
