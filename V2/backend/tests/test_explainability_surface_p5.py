"""Phase 5: Explainability Surface Test Suite.

Verifies:
1. T5.1: question_trace in /chat and /nlp/analyze responses with human-readable reason
2. T5.2: Diagnostic map view endpoint (stateless POST and session GET) with LLM off (Invariant 2)
3. T5.3: Open-threads panel route, thread dismissal, and thread prioritization
4. T5.4: Rejected-candidates view aggregating filter rejections with trigger tags
5. T5.5: User correction route (PATCH /nlp/analysis/correction) applying supersession to QUD stack
"""
from __future__ import annotations

import json
from uuid import uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import router, get_current_user_id
from app.models.db import Base
from app.models.orm import ChatTurn, NLPRecord
from app.services.nlp_service import NLPService
from app.services.session_state import SessionStateStore
from app.services.journal_service import JournalService


@pytest.fixture
def explainability_app(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    @event.listens_for(engine, 'connect')
    def foreign_keys(db, _): db.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)

    service = NLPService(sessionmaker(engine, expire_on_commit=False), 'test-alias-key', lambda _: None)
    monkeypatch.setattr('app.api.routes.get_nlp_service', lambda: service)
    monkeypatch.setattr('app.services.dmrst.parse_dmrst', lambda _: {'status': 'unavailable', 'reason': 'mock', 'edus': [], 'tree': []})
    monkeypatch.setattr('app.services.classical_nlp.discourse_entities', lambda *a: ({'hobbs': {'pronouns': []}, 'centering': {'trace': []}}, []))

    def enrich(user, analysis, state, **kwargs):
        analysis['semantic_retrieval'] = {'status': 'unavailable', 'reason': 'mock', 'results': []}
        analysis['memory_retrieval'] = []
        return {'status': 'unavailable', 'reason': 'mock'}, {}

    monkeypatch.setattr(service, 'enrich', enrich)

    app = FastAPI()
    app.include_router(router)
    app.state.session_state = SessionStateStore(service.factory)
    app.state.journal_service = JournalService(service.factory)
    app.dependency_overrides[get_current_user_id] = lambda: 'test-user-explainability'

    with TestClient(app) as client:
        yield client, service, app

    engine.dispose()


# ---------------------------------------------------------------------------
# T5.1: Question Trace Surface in /chat and /nlp/analyze
# ---------------------------------------------------------------------------

def test_question_trace_in_chat_payload(explainability_app):
    """Verify /chat response includes complete question_trace with human-readable reason."""
    client, _, _ = explainability_app
    req = {
        'message': 'I think I might hesitate to take the new assignment, but everyone expects results.',
        'request_id': str(uuid4()),
    }
    resp = client.post('/chat', json=req)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert 'question_trace' in data
    trace = data['question_trace']
    assert trace is not None
    assert 'move' in trace
    assert 'reason' in trace or 'human_reason' in trace
    assert 'presuppositions_checked' in trace
    assert 'score' in trace
    assert 'spans' in trace


def test_question_trace_in_preview_analyze_payload(explainability_app):
    """Verify /nlp/analyze preview returns question_trace alongside gaps and qud_stack."""
    client, _, _ = explainability_app
    req = {
        'text': 'I think I might hesitate to take the new assignment, but everyone expects results.',
    }
    resp = client.post('/nlp/analyze', json=req)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data['status'] == 'preview'
    assert 'gaps' in data
    assert 'qud_stack' in data
    assert 'question_trace' in data
    assert data['question_trace'] is not None


# ---------------------------------------------------------------------------
# T5.2: Diagnostic Map View Endpoint (Stateless POST & Session GET)
# ---------------------------------------------------------------------------

def test_diagnostic_map_stateless_preview_llm_off(explainability_app):
    """Verify POST /nlp/diagnostic_map works deterministically with LLM off (Invariant 2)."""
    client, _, _ = explainability_app
    req = {
        'text': 'I think I might struggle with how to proceed with the team assignment, but everyone expects results.',
    }
    resp = client.post('/nlp/diagnostic_map', json=req)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data['diagnostics_status'] == 'ok'
    assert len(data['turns']) == 1
    turn = data['turns'][0]
    assert turn['turn_index'] == 1
    assert 'clauses' in turn
    assert 'relations' in turn
    assert 'gaps' in turn
    assert 'move' in turn
    assert 'question_trace' in turn


def test_diagnostic_map_session_history(explainability_app):
    """Verify GET /nlp/sessions/{session_id}/diagnostic_map surfaces multi-turn annotations."""
    client, _, _ = explainability_app
    # Turn 1
    t1 = client.post('/chat', json={'message': 'I think I might hesitate with the new assignment, but my team expects it.', 'request_id': str(uuid4())}).json()
    sid = t1['session_id']

    # Turn 2
    client.post('/chat', json={'session_id': sid, 'message': 'I felt that because the deadline was moved without warning.', 'request_id': str(uuid4())})

    resp = client.get(f'/nlp/sessions/{sid}/diagnostic_map')
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data['session_id'] == sid
    assert len(data['turns']) == 2
    assert data['turns'][0]['turn_index'] == 1
    assert data['turns'][1]['turn_index'] == 2


# ---------------------------------------------------------------------------
# T5.3: Open Threads Panel & Thread Actions
# ---------------------------------------------------------------------------

def test_open_threads_panel_and_actions(explainability_app):
    """Verify GET threads, thread dismissal (deflected), and thread prioritization (open)."""
    client, _, _ = explainability_app
    t1 = client.post('/chat', json={'message': 'I think I might hesitate with the project, but everyone expects it.', 'request_id': str(uuid4())}).json()
    sid = t1['session_id']

    threads_resp = client.get(f'/nlp/sessions/{sid}/threads')
    assert threads_resp.status_code == 200, threads_resp.text
    threads_data = threads_resp.json()
    assert threads_data['session_id'] == sid
    assert len(threads_data['all_threads']) >= 1

    target_gap_id = threads_data['all_threads'][0]['gap_id']

    # Dismiss thread
    dismiss_resp = client.post(f'/nlp/sessions/{sid}/threads/{target_gap_id}/dismiss')
    assert dismiss_resp.status_code == 200, dismiss_resp.text
    d_data = dismiss_resp.json()
    assert d_data['action'] == 'dismiss'
    assert d_data['status'] == 'deflected'

    # Check threads updated
    threads_after_dismiss = client.get(f'/nlp/sessions/{sid}/threads').json()
    dismissed_entry = next(t for t in threads_after_dismiss['all_threads'] if t['gap_id'] == target_gap_id)
    assert dismissed_entry['status'] == 'deflected'

    # Prioritize thread
    prio_resp = client.post(f'/nlp/sessions/{sid}/threads/{target_gap_id}/prioritize')
    assert prio_resp.status_code == 200, prio_resp.text
    p_data = prio_resp.json()
    assert p_data['action'] == 'prioritize'
    assert p_data['status'] == 'open'

    threads_after_prio = client.get(f'/nlp/sessions/{sid}/threads').json()
    prio_entry = next(t for t in threads_after_prio['all_threads'] if t['gap_id'] == target_gap_id)
    assert prio_entry['status'] == 'open'
    assert prio_entry['recurrence_count'] >= 2


# ---------------------------------------------------------------------------
# T5.4: Rejected Candidates View
# ---------------------------------------------------------------------------

def test_rejected_candidates_endpoint(explainability_app):
    """Verify rejected candidates endpoint returns 200 with structured rejections."""
    client, _, _ = explainability_app
    t1 = client.post('/chat', json={'message': 'I think I might hesitate with the project, but everyone expects it.', 'request_id': str(uuid4())}).json()
    sid = t1['session_id']
    tid = t1['turn_id']

    # Session level
    resp_sess = client.get(f'/nlp/sessions/{sid}/rejected_candidates')
    assert resp_sess.status_code == 200, resp_sess.text
    data_sess = resp_sess.json()
    assert data_sess['session_id'] == sid
    assert 'rejected_candidates' in data_sess
    assert 'total_rejected' in data_sess

    # Turn level
    resp_turn = client.get(f'/nlp/turns/{tid}/rejected_candidates')
    assert resp_turn.status_code == 200, resp_turn.text
    data_turn = resp_turn.json()
    assert data_turn['turn_id'] == tid
    assert 'rejected_candidates' in data_turn


# ---------------------------------------------------------------------------
# T5.5: User Correction Route (PATCH /nlp/analysis/correction)
# ---------------------------------------------------------------------------

def test_user_correction_applies_supersession(explainability_app):
    """Verify user correction updates QUD stack and applies supersession."""
    client, _, _ = explainability_app
    t1 = client.post('/chat', json={'message': 'I think I might hesitate with the project, but everyone expects it.', 'request_id': str(uuid4())}).json()
    sid = t1['session_id']
    tid = t1['turn_id']

    threads = client.get(f'/nlp/sessions/{sid}/threads').json()['all_threads']
    assert len(threads) >= 1
    target_gap_id = threads[0]['gap_id']

    correction_payload = {
        'session_id': sid,
        'turn_id': tid,
        'gap_id': target_gap_id,
        'correction_type': 'retract',
        'user_note': 'Actually, I was never hesitating about the project itself.',
    }
    resp = client.patch('/nlp/analysis/correction', json=correction_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data['session_id'] == sid
    assert data['status'] == 'corrected'
    assert target_gap_id in data['applied_supersessions']

    # Verify QUD stack reflects superseded status
    corrected_threads = client.get(f'/nlp/sessions/{sid}/threads').json()['all_threads']
    entry = next(t for t in corrected_threads if t['gap_id'] == target_gap_id)
    assert entry['status'] == 'superseded'
