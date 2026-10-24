"""HTTP contract tests for the integrated UI. Neural generation is mocked."""
import copy
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


@pytest.fixture
def integrated(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    @event.listens_for(engine,'connect')
    def foreign_keys(db,_): db.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    service = NLPService(sessionmaker(engine,expire_on_commit=False), 'integration-key', lambda _:None)
    monkeypatch.setattr('app.api.routes.get_nlp_service',lambda:service)
    monkeypatch.setattr('app.services.dmrst.parse_dmrst',lambda _: {'status':'unavailable','reason':'integration_mock','edus':[],'tree':[]})
    monkeypatch.setattr('app.services.classical_nlp.discourse_entities',lambda *a: ({'hobbs':{'pronouns':[]},'centering':{'trace':[]}},[]))
    def enrich(user,analysis,state,**kwargs):
        analysis['semantic_retrieval']={'status':'unavailable','reason':'integration_mock','results':[]}
        analysis['memory_retrieval']=[]
        return {'status':'unavailable','reason':'integration_mock'},{}
    monkeypatch.setattr(service,'enrich',enrich)
    app=FastAPI();app.include_router(router)
    from app.services.session_state import SessionStateStore
    from app.services.journal_service import JournalService
    app.state.session_state=SessionStateStore(service.factory)
    app.state.journal_service=JournalService(service.factory)
    app.dependency_overrides[get_current_user_id]=lambda:'integration-owner'
    with TestClient(app) as client: yield client,service,app
    engine.dispose()


def test_http_chat_memory_journal_and_deletion(integrated):
    client,service,app=integrated
    assert client.get('/sessions').json()['sessions']==[]
    assert client.post('/nlp/analyze',json={'text':'I feel tired after work.'}).json()['status']=='preview'
    request={'message':'I met Priya Sharma and felt tired after work.','request_id':str(uuid4())}
    result=client.post('/chat',json=request)
    assert result.status_code==200,result.text
    body=result.json(); sid=body['session_id']; tid=body['turn_id']
    assert body['nlp_analysis']['context_packet']
    assert 'Priya' not in json.dumps(body['nlp_analysis'])
    assert client.post('/chat',json=request).json()==body
    assert client.get('/sessions').json()['sessions'][0]['turn_count']==1
    assert client.get(f'/sessions/{sid}/turns').json()['turns'][0]['turn_id']==tid
    assert client.get(f'/sessions/{sid}/analysis').json()['records'][0]['analysis']['mathematical_models']['filters']['unscented_kf']
    assert client.get('/nlp/memory/graph').json()['nodes']
    assert client.patch('/nlp/preferences',json={'share_history_with_provider':True}).json()['share_history_with_provider'] is True
    assert client.get(f'/nlp/turns/{tid}/classification').status_code==200
    entry=client.post('/journal/create',json={'session_id':sid,'selected_turn_ids':[tid],'entry_title':'Work reflection'})
    assert entry.status_code==201,entry.text
    eid=entry.json()['entry_id']
    assert client.patch(f'/journal/{eid}',json={'entry_title':'Updated reflection'}).status_code==200
    assert client.get('/journal').json()['entries'][0]['entry_title']=='Updated reflection'
    app.dependency_overrides[get_current_user_id]=lambda:'another-owner'
    assert client.get('/sessions').json()['sessions']==[]
    assert client.get(f'/sessions/{sid}/analysis').status_code==404
    assert client.get(f'/nlp/turns/{tid}/classification').status_code==404
    app.dependency_overrides[get_current_user_id]=lambda:'integration-owner'
    assert client.delete(f'/journal/{eid}').status_code==200
    assert client.delete(f'/sessions/{sid}').status_code==200
    with service.factory() as db:
        assert db.scalar(select(func.count()).select_from(ChatTurn))==0
        assert db.scalar(select(func.count()).select_from(NLPRecord))==0


def test_hosted_requires_consent_and_failure_does_not_commit(integrated,monkeypatch):
    client,service,_=integrated
    payload={'message':'I feel tired after work.','request_id':str(uuid4()),'generation_provider':'hosted'}
    assert client.post('/chat',json=payload).status_code==422
    monkeypatch.setattr('app.services.hosted_generation.generate_hosted',lambda *a: (None,{'reason':'test outage'}))
    payload['hosted_consent']=True
    assert client.post('/chat',json=payload).status_code==503
    assert client.get('/sessions').json()['total']==0


def test_hosted_context_boundaries():
    from app.services.hosted_generation import build_hosted_messages
    plan={'intent':'reflect_current_meaning','claims_to_communicate':[{'text':'I feel tired.','epistemic_status':'asserted'}],
          'memory_context':{'historical_evidence':[{'text':'historical-private-text-'+'a'*400,'revision_status':'active'} for _ in range(5)]}}
    original=copy.deepcopy(plan)
    off=json.loads(build_hosted_messages(plan,False)[1]['content'])
    on=json.loads(build_hosted_messages(plan,True)[1]['content'])
    assert off['historical_evidence']==[]
    assert len(on['historical_evidence'])==3
    assert sum(len(r['text']) for r in on['historical_evidence'])==900
    assert plan==original


def test_display_restoration_does_not_change_persisted_result():
    record={'response_text':'You felt heard by [entity_e000001].'}
    display=NLPService.display_result(record,{'[entity_e000001]':'Priya Sharma'})
    assert display['display_response_text']=='You felt heard by Priya Sharma.'
    assert 'Priya' not in record['response_text']


def test_untrusted_issuer_rejected_before_network(monkeypatch):
    import jwt
    from app.services.clerk_auth import _derive_jwks_url,ClerkAuthError
    monkeypatch.setenv('CLERK_ISSUER','https://trusted.clerk.accounts.dev')
    token=jwt.encode({'iss':'http://127.0.0.1/private'},'synthetic',algorithm='HS256')
    with pytest.raises(ClerkAuthError):_derive_jwks_url(token)


def test_calendar_journal_crud_redaction_and_owner_scope(integrated):
    client,_,app=integrated
    data={'title':'A calmer day','text':'I met Priya Sharma after work.','mood':{'label':'Calm','emoji':'🌿'},'sleep':7.5,'stress':2}
    response=client.put('/journal/calendar/2026-10-17',json=data)
    assert response.status_code==200,response.text
    assert 'Priya' not in response.json()['entry']['text']
    assert client.get('/journal/calendar').json()['entries']['2026-10-17']['sleep']==7.5
    app.dependency_overrides[get_current_user_id]=lambda:'another-owner'
    assert client.get('/journal/calendar').json()['entries']=={}
    assert client.delete('/journal/calendar/2026-10-17').status_code==404
    app.dependency_overrides[get_current_user_id]=lambda:'integration-owner'
    assert client.delete('/journal/calendar/2026-10-17').status_code==200
    assert client.get('/journal/calendar').json()['entries']=={}


def test_algorithm_lab_is_redacted_read_only_and_owner_checked(integrated):
    client, service, app = integrated
    result = client.post('/chat', json={'message': 'I walked outside after work.', 'request_id': str(uuid4())}).json()
    sid = result['session_id']
    snapshot, revision = service.load('integration-owner', sid)
    before = copy.deepcopy(snapshot)
    response = client.post('/nlp/experiments', json={'text': 'Priya Sharma walked outside.', 'session_id': sid})
    assert response.status_code == 200, response.text
    data = response.json()
    assert 'Priya' not in json.dumps(data)
    assert data['document_count'] == 2
    assert data['language_models']['status'] == 'ready'
    assert data['persisted'] is False
    assert service.load('integration-owner', sid) == (before, revision)
    assert len(client.get(f'/sessions/{sid}/turns').json()['turns']) == 1
    app.dependency_overrides[get_current_user_id] = lambda: 'another-owner'
    assert client.post('/nlp/experiments', json={'text': 'A private query.', 'session_id': sid}).status_code == 404


@pytest.mark.parametrize('profile', ['low_resource', 'balanced', 'high_fidelity', 'responsive', 'stable'])
def test_preview_exposes_each_math_profile_without_committing(integrated, profile):
    client, _, _ = integrated
    response = client.post('/nlp/analyze', json={'text': 'I may rest because work was tiring.', 'mathematical_profile': profile})
    assert response.status_code == 200, response.text
    math = response.json()['nlp_analysis']['mathematical_models']
    assert math['profile'] == profile
    assert set(math['filters']) == {'linear_kf', 'extended_kf', 'unscented_kf', 'ensemble_kf', 'particle_filter'}
    assert client.get('/sessions').json()['sessions'] == []


def test_algorithm_endpoints_reject_unknown_profile_and_oversized_text(integrated):
    client, _, _ = integrated
    assert client.post('/nlp/analyze', json={'text': 'hello', 'mathematical_profile': 'invented'}).status_code == 422
    assert client.post('/nlp/experiments', json={'text': 'a' * 2001}).status_code == 422
