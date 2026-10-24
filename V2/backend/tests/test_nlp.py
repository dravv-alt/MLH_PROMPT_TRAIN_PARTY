import copy
import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import numpy as np
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event, select, func
from sqlalchemy.orm import sessionmaker

from app.models.db import Base
from app.models.orm import ChatTurn, NLPRecord, NLPState, NLPTopic
from app.models.schemas import ChatRequest
from app.services.nlp_engine import analyze_turn, cosine, vector, filtered, FEATURES, FALLBACKS, STRATEGIES, parse
from app.services.nlp_service import NLPService
from app.services.response_policy import validate_reflective_response
from app.services.session_state import SessionStateStore

CFG = {"alias_key": "test-key"}


@pytest.fixture
def service(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread":False})
    @event.listens_for(engine, "connect")
    def enable(db, _):
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=5000")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    return NLPService(factory, "test-key", lambda _: None)


def test_purity_repeat_and_spans():
    state = {}
    before = copy.deepcopy(state)
    text = "Priya Sharma spoke, but Priya stayed quiet because the meeting felt tense."
    a, delta, ephemeral = analyze_turn(text, state, CFG)
    assert state == before
    b, _, _ = analyze_turn(text, state, CFG)
    assert json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(b, sort_keys=True, allow_nan=False)
    assert len(delta['entities']) == 1
    assert 'Priya' not in json.dumps(a)
    assert ephemeral['offset_map']
    for span in [m['span'] for m in a['mentions']] + [s for c in a['clauses'] for s in c['spans']] + [e['cue_span'] for e in a['relations']]:
        assert 0 <= span[0] < span[1] <= len(a['redacted_text'])
    assert {e['relation'] for e in a['relations']} >= {'cause', 'contrast'}
    doc, _, _ = parse(a['redacted_text'])
    assert all(t.pos_ == 'PROPN' for t in doc if t.text.startswith('[entity_'))


def test_ambiguity_and_missing():
    a, _, _ = analyze_turn("I am wondering if the team will call. I am so tired and angry.", {}, CFG)
    assert not a['relations']
    assert a['features']['entity_continuity'] is None
    assert a['features']['topic_novelty'] is None
    assert a['topic_entropy'] is None
    b, _, _ = analyze_turn('ok', {}, CFG)
    assert b['topic_id'] is None
    assert b['strategy'] == 'insufficient'


def test_vector_and_kalman_properties():
    rng = np.random.default_rng(1234)
    posterior = None
    for _ in range(100):
        words = [f'word{int(i)}' for i in rng.integers(0,30,20)]
        v = vector(words)
        assert 0 <= cosine(v, vector(words[::-1])) <= 1
        obs = [None if rng.random() < .3 else float(rng.random()) for _ in range(4)]
        posterior = filtered(obs, [3, 5, 60, 20], posterior)
        p = np.array(posterior['P'])
        assert np.allclose(p, p.T)
        assert np.linalg.eigvalsh(p).min() >= -1e-12
    a, _, _ = analyze_turn('office meeting report project [entity_e000001]', {}, CFG)
    b, _, _ = analyze_turn('office meeting report project [entity_e000099]', {}, CFG)
    assert a['features'] == b['features']


def test_filterpy_crosscheck():
    filterpy = pytest.importorskip("filterpy.kalman", reason="optional independent FilterPy cross-check is not installed")
    KalmanFilter = filterpy.KalmanFilter
    prior = {'x':[.2,.3,.02,.4], 'P':np.diag([.3,.2,.1,.2]).tolist(), 'initialized':[True]*4}
    z = [.4, None, .05, .6]
    actual = filtered(z, [3,5,60,20], prior)
    k = KalmanFilter(dim_x=4, dim_z=3)
    k.x=np.array(prior['x']); k.P=np.array(prior['P']);k.F=np.eye(4)
    k.Q=np.diag([.01,.01,.0001,.01]);k.H=np.eye(4)[[0,2,3]]
    k.R=np.diag([.4*.6/3+1e-4,.05*.95/60+1e-4,1/20+1e-4])
    k.predict();k.update(np.array([.4,.05,.6]))
    assert np.allclose(k.x, actual['x'])
    assert np.allclose(k.P, actual['P'])


def test_templates():
    for text in [*FALLBACKS.values(), *STRATEGIES.values()]:
        assert validate_reflective_response(text).is_valid


def test_preview_idempotency_restart_isolation_delete(service):
    preview = service.preview('alice', 'The office meeting report felt difficult.')
    assert preview['status']=='preview'
    with service.factory() as db:
        assert db.scalar(select(func.count()).select_from(ChatTurn)) == 0
    payload=ChatRequest(message='The office meeting report felt difficult.', request_id=uuid4())
    result=service.chat('alice', payload)
    assert result['safety_mode']=='deterministic_outage'
    assert service.chat('alice',payload)==result
    restarted=NLPService(service.factory,'test-key',lambda _:None)
    assert restarted.load('alice',result['session_id'])[1]==1
    with pytest.raises(HTTPException) as exc:
        service.preview('bob','test',result['session_id'])
    assert exc.value.status_code==404
    SessionStateStore(service.factory).delete_session('alice',result['session_id'])
    with service.factory() as db:
        for model in [ChatTurn,NLPRecord,NLPState,NLPTopic]:
            assert db.scalar(select(func.count()).select_from(model))==0


def test_atomic_conflict_and_provider_failure(service):
    initial=service.chat('a',ChatRequest(message='office report meeting project'))
    sid=initial['session_id']
    snapshot, rev=service.load('a',sid)
    a,d,_=analyze_turn('office report meeting project',snapshot,CFG)
    def commit():
        return service.commit('a',sid,rev,str(uuid4()),'digest',a,d,FALLBACKS['standard'],'deterministic_outage')
    with ThreadPoolExecutor(2) as pool:
        futures=[pool.submit(commit) for _ in range(2)]
    outcomes=[]
    for f in futures:
        try: outcomes.append(f.result()['revision'])
        except HTTPException as e: outcomes.append(e.status_code)
    assert sorted(outcomes)==[2,409]
    with service.factory() as db:
        assert db.scalar(select(func.count()).select_from(ChatTurn))==2
    service.generator=lambda _: (_ for _ in ()).throw(RuntimeError('provider failed'))
    result=service.chat('a',ChatRequest(message='another project discussion report',session_id=sid))
    assert result['safety_mode']=='deterministic_outage'


def test_invalid_write_rolls_back(service):
    a,d,_=analyze_turn('project meeting office report',{},CFG)
    with pytest.raises(HTTPException):
        service.commit('a','unknown',0,str(uuid4()),'digest',a,d,'text','test')
    with service.factory() as db:
        assert db.scalar(select(func.count()).select_from(ChatTurn))==0


def test_api_contract_body_limit_and_auth(service, monkeypatch):
    from fastapi.testclient import TestClient
    import app.services.nlp_service as module
    from app.api.routes import get_current_user_id
    from main import app
    monkeypatch.setattr(module, 'service', service)
    client=TestClient(app)
    assert client.post('/nlp/analyze',json={'text':'test'}).status_code==401
    app.dependency_overrides[get_current_user_id]=lambda:'alice'
    try:
        preview=client.post('/nlp/analyze',json={'text':'office project report meeting'})
        assert preview.status_code==200 and preview.json()['status']=='preview'
        assert client.post('/nlp/analyze',content='x'*32769).status_code==413
        assert client.post('/nlp/analyze',json={'text':'x'*2001}).status_code==422
        payload={'message':'office report project meeting','request_id':str(uuid4())}
        result=client.post('/chat',json=payload)
        assert result.status_code==200
        assert client.post('/chat',json=payload).json()==result.json()
        sid=result.json()['session_id']
        app.dependency_overrides[get_current_user_id]=lambda:'bob'
        assert client.get(f'/sessions/{sid}/analysis').status_code==404
        assert client.post('/chat',json={**payload,'session_id':sid,'request_id':str(uuid4())}).status_code==404
    finally:
        app.dependency_overrides.clear()


def test_cross_session_world_review_and_source_deletion(service):
    first=service.chat('alice',ChatRequest(message='Priya Sharma discussed the office project report.'))
    second=service.chat('alice',ChatRequest(message='Priya discussed the office project report again...'))
    memory=service.world('alice')
    assert len(memory['scenes'])==2
    assert second['nlp_analysis']['memory_retrieval']
    assert second['nlp_analysis']['memory_retrieval'][0]['source_session_id']==first['session_id']
    assert service.world('bob')['scenes']==[]
    unresolved=memory['unresolved'][0]
    service.review_unresolved('alice',unresolved['id'],'dismissed',memory['revision'])
    assert service.world('alice')['unresolved'][0]['status']=='dismissed'
    with pytest.raises(HTTPException) as exc:
        service.review_unresolved('alice',unresolved['id'],'open',memory['revision'])
    assert exc.value.status_code==409
    assert service.delete_session('alice',first['session_id'])
    surviving=service.world('alice')
    assert len(surviving['scenes'])==1
    assert surviving['scenes'][0]['session_id']==second['session_id']
