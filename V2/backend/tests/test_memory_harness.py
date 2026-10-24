"""Canonical narrative-memory update, revision, and retrieval regressions."""
from __future__ import annotations

from app.services.memory_harness import apply_memory_harness
from app.services.response_planner import build_response_plan


def test_finalize_without_proposed_memory_update_does_not_rebind_prior_memory():
    from copy import deepcopy
    from app.services.memory_harness import finalize_commit
    delta = {'world': {'canonical_memory': {'memory_generation': 'old', 'assertions': [], 'evidence': [], 'episodes': []}}}
    before = deepcopy(delta)
    analysis = {}
    finalize_commit(analysis, delta, turn_id=4, session_id='s', memory_generation='new', recorded_at='now')
    assert delta == before
    assert analysis == {}


def _analysis(text, turn, *, polarity="positive", predicate="report", correction=False, topic="s000001"):
    return {
        "redacted_text": text,
        "topic_id": topic,
        "pwm": {"scenes": [{"id": f"scene_{turn}", "text": text}]},
        "discourse_context": {
            "current_propositions": [{
                "id": f"dp_{turn}", "source_turn": turn, "clause_id": "c1", "text": text,
                "scope_spans": [[0, len(text)]], "predicate": {"lemma": predicate, "span": [0, 1]},
                "actors": [{"role": "agent", "text": "I", "span": [0, 1]}],
                "polarity": polarity, "negation_spans": [], "modality": [], "status": "asserted",
            }],
            "revision_links": [],
        },
        "relations": [],
        "memory_retrieval": [],
        "strategy": "correction" if correction else "standard",
        "strategy_evidence": {
            "correction": {"detected": correction, "supersedes_turn": turn - 1 if correction else None}
        },
        "mathematical_models": {"evidence_belief_revision": {"propositions": [], "current_evidence_ids": []}},
        "clauses": [],
    }


def _turn(state, text, **kwargs):
    turn = len(state.get("turns", [])) + 1
    analysis = _analysis(text, turn, **kwargs)
    delta = {**state, "turns": [*state.get("turns", []), {"turn_index": turn, "text": text}], "world": {
        **state.get("world", {}), "scenes": [*state.get("world", {}).get("scenes", []), analysis["pwm"]["scenes"][0]]
    }}
    apply_memory_harness(
        analysis, delta, state, memory_generation="test-generation", session_id="test-session"
    )
    return analysis, delta


def test_explicit_correction_targets_older_evidence_and_excludes_it_from_retrieval():
    state = {}
    first, state = _turn(state, "I felt anxious about the interview.", predicate="feel")
    target_id = first["memory_update"]["assertion_ids"][0]
    _, state = _turn(state, "I submitted the documents this morning.", predicate="submit", topic="s000002")
    corrected, state = _turn(
        state,
        "Actually, I was not anxious about the interview.",
        polarity="negative",
        predicate="be",
        correction=True,
    )
    operations = corrected["memory_update"]["operations"]
    assert any(row["operation"] == "CORRECT" and row["target_assertion_id"] == target_id for row in operations)
    stored = {row["assertion_id"]: row for row in state["world"]["canonical_memory"]["assertions"]}
    assert stored[target_id]["revision_status"] == "superseded"
    trace = corrected["context_packet"]["retrieval_trace"]
    assert target_id in trace["excluded_superseded_ids"]
    assert target_id not in {row["assertion_id"] for row in corrected["context_packet"]["relevant_prior_evidence"]}


def test_similar_distinct_events_are_not_merged_or_superseded():
    state = {}
    _, state = _turn(state, "I argued with my manager about the travel budget.")
    second, state = _turn(state, "I argued with my friend about the travel budget.")
    assertions = state["world"]["canonical_memory"]["assertions"]
    assert len(assertions) == 2
    assert len({row["episode_id"] for row in assertions}) == 2
    assert all(row["revision_status"] == "active" for row in assertions)
    assert not any(row["operation"] in {"CORRECT", "SUPERSEDE"} for row in second["memory_update"]["operations"])


def test_ambiguous_correction_is_deferred_without_overwriting_prior_accounts():
    state = {}
    _, state = _turn(state, "The deadline explanation made the project difficult.")
    _, state = _turn(state, "The deadline explanation made the meeting difficult.")
    current, state = _turn(
        state,
        "Actually, that deadline explanation was not right.",
        polarity="negative",
        correction=True,
    )
    assert any(row["operation"] == "DEFER" for row in current["memory_update"]["operations"])
    historical = state["world"]["canonical_memory"]["assertions"][:-1]
    assert all(row["revision_status"] == "active" for row in historical)
    assert current["context_packet"]["retrieval_trace"]["unresolved_assertion_ids"]


def test_context_packet_is_bounded_and_plan_receives_memory_graph_trace():
    state = {}
    for index in range(10):
        _, state = _turn(state, f"I discussed project deadline detail number {index} with the team.")
    current, state = _turn(state, "I am still thinking about the project deadline with the team.")
    packet = current["context_packet"]
    assert packet["selected_item_count"] <= packet["evidence_item_limit"] == 8
    assert len(packet["relevant_prior_evidence"]) <= 4
    plan = build_response_plan(current, state["turns"][:-1])
    assert plan["relevant_proposition_ids"] == packet["retrieval_trace"]["selected_assertion_ids"]
    assert plan["relevant_graph_node_ids"] == packet["retrieval_trace"]["selected_graph_node_ids"]
    assert plan["memory_context"]["historical_evidence"]


def test_provider_opt_out_removes_historical_text_from_response_plan():
    state = {}
    _, state = _turn(state, "I am tired after the project deadline.")
    current, state = _turn(state, "I am still tired because of the project deadline.")
    local_plan = build_response_plan(current, state["turns"][:-1], include_historical_context=True)
    provider_plan = build_response_plan(current, state["turns"][:-1], include_historical_context=False)
    assert local_plan["memory_context"]["historical_evidence"]
    assert provider_plan["memory_context"]["historical_evidence"] == []


def test_hypothetical_assertions_do_not_become_retrievable_autobiographical_memory():
    state = {}
    _, state = _turn(state, "Suppose my friend felt tired after a deadline.")
    current, _ = _turn(state, "I feel tired after my deadline.")
    assert current["context_packet"]["relevant_prior_evidence"] == []
    assert any(
        row["reason"] == "non_autobiographical"
        for row in current["context_packet"]["excluded_candidates_summary"]
    )


def test_service_commits_memory_atomically_and_session_delete_prunes_sources(monkeypatch):
    from uuid import uuid4
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.models.db import Base
    from app.models.schemas import ChatRequest
    from app.services.nlp_service import NLPService

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    service = NLPService(sessionmaker(engine, expire_on_commit=False), "memory-service-test", lambda _: None)
    metadata = {
        "generation": "", "index_revision": 0, "share_history_with_provider": False,
        "process_local_unredacted": False, "store_local_unredacted_memory": False,
        "preference_revision": 0,
    }
    monkeypatch.setattr(service.neural, "metadata", lambda _user: dict(metadata))
    monkeypatch.setattr(service.neural, "embed", lambda *_args, **_kwargs: {"status": "unavailable", "reason": "test"})
    monkeypatch.setattr(service.neural, "search", lambda *_args, **_kwargs: {
        "status": "lexical_fallback", "reason": "test", "coverage": {}, "results": []
    })

    result = service.chat(
        "alice", ChatRequest(message="I felt anxious about the interview yesterday.", request_id=uuid4())
    )
    assert result["nlp_analysis"]["memory_update"]["status"] == "committed"
    assert result['narrative_structure'] == result['nlp_analysis']['situational_structure']
    assert result['nlp_analysis']['response_plan']['situational_structure'] == result['narrative_structure']
    snapshot = service.load('alice', result['session_id'])[0]
    assert snapshot['ssm_history'][-1] == result['narrative_structure']
    assert service.load('alice', None)[0].get('ssm_history', []) == []
    assert 'key_phrases_mirrored' not in result['narrative_structure']['language']
    memory = service.load("alice", result["session_id"])[0]["world"]["canonical_memory"]
    assert memory["memory_generation"]
    assert all(row["source_turn_id"] == result["turn_id"] for row in memory["assertions"])
    assert service.delete_session("alice", result["session_id"])
    assert service.world("alice")["scenes"] == []
    assert service.load("alice", None)[0]["world"].get("canonical_memory", {}).get("assertions", []) == []
