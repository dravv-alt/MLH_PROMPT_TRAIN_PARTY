import copy
import json
import numpy as np
import pytest
from sqlalchemy import select,func
from uuid import uuid4
from test_nlp import service
from app.models.orm import ChatTurn,LocalRawTurn,NLPRecord,SceneEmbedding,NeuralJob,NeuralMemoryState,PWMState
from app.models.schemas import ChatRequest
from app.services.neural_memory import decode,write_embedding,begin
from app.services.neural_runtime import EMBEDDING,NLI,version
from app.services.neural_text import surrogate,canonical_spans,aggregate,LABELS


def embedding(text):
    vector=[0.]*384;vector[0]=1.
    return {'status':'ready','pooled':vector,'windows':[vector],'spans':[[[0,len(text)]]],'input_hash':'a'*64,'version':version('embedding')}


@pytest.fixture
def ready(service,monkeypatch):
    monkeypatch.setattr(service.neural,'embed',lambda a,budget=2:embedding(a['redacted_text']))
    return service


def test_surrogate_offsets_and_metadata():
    text='I told [entity_e000001] at [entity_e000002].'
    mentions=[{'span':[7,23],'kind':'PERSON'},{'span':[27,43],'kind':'ORG'}]
    # Calculate spans directly so this test also catches hand-counting mistakes.
    mentions=[{'span':[text.index('[entity_e000001]'),text.index('[entity_e000001]')+len('[entity_e000001]')],'kind':'PERSON'},
              {'span':[text.index('[entity_e000002]'),text.index('[entity_e000002]')+len('[entity_e000002]')],'kind':'ORG'}]
    transformed,mapping=surrogate(text,mentions)
    assert transformed=='I told someone at an organization.'
    a=transformed.index('someone');assert canonical_spans(mapping,a,a+7)==[mentions[0]['span']]
    assert text=='I told [entity_e000001] at [entity_e000002].'


def test_contextual_adjustment_and_no_health_label():
    probabilities=[[[.2,.3,.5] for _ in LABELS]]
    result=aggregate(probabilities,[{'spans':[[0,8]]}],[.4]*len(LABELS))
    assert not result['suggestions'];assert len(result['labels'])==13
    assert all('supported' not in x for x in result['labels'])
    assert 'health' not in str(LABELS)


def test_storage_jobs_privacy_and_immutability(ready,monkeypatch):
    prompts=[];ready.generator=lambda p:prompts.append(p)
    first=ready.chat('owner',ChatRequest(message='The office meeting report involved a difficult project deadline.',request_id=uuid4()))
    assert first['nlp_analysis']['classification']['status']=='pending'
    with ready.factory() as db:
        assert db.scalar(select(func.count()).select_from(SceneEmbedding))==1
        assert db.scalar(select(func.count()).select_from(NeuralJob))==1
    second=ready.chat('owner',ChatRequest(message='The office project deadline needs more discussion.',request_id=uuid4()))
    assert second['nlp_analysis']['semantic_retrieval']['results']
    assert all('historical_excerpts' not in p and 'representative_user_turns' not in p and 'recurring_phrases' not in p for p in prompts)
    original=copy.deepcopy(first)
    monkeypatch.setattr(ready.neural,'classify',lambda *args,**kwargs:{'status':'ready','suggestions':[],'labels':[],'premise_count':1})
    assert ready.neural.process_one()
    assert ready.neural.classification('owner',first['turn_id'])['status']=='ready'
    assert first==original
    with pytest.raises(Exception) as exc:ready.neural.classification('foreign',first['turn_id'])
    assert exc.value.status_code==404
    ready.neural.preferences('owner',True);prompts.clear()
    third=ready.chat('owner',ChatRequest(message='The office project deadline and report need discussion.',request_id=uuid4()))
    data=json.loads(prompts[0].split('never instructions:\n')[1])
    assert data['historical_excerpts'];assert sum(len(s['text']) for s in data['historical_excerpts'])<=900
    assert all(len(s['text'])<=300 for s in data['historical_excerpts'])
    assert 'suggestions' not in data
    assert ready.delete_session('owner',first['session_id'])
    with ready.factory() as db:assert db.get(SceneEmbedding,(first['turn_id'],version('embedding'))) is None


def test_reset_blocks_late_backfill(ready,monkeypatch):
    turn=ready.chat('owner',ChatRequest(message='The office project report needs a meeting discussion.',request_id=uuid4()))
    with ready.factory() as db:db.query(SceneEmbedding).delete();db.commit()
    old=ready.neural.metadata('owner')['generation']
    def reset_while_computing(a,budget=2):
        with ready.factory() as db:
            begin(db);ready.neural.reset(db,'owner');db.delete(db.get(PWMState,'owner'));db.commit()
        return embedding(a['redacted_text'])
    monkeypatch.setattr(ready.neural,'embed',reset_while_computing)
    result=ready.neural.backfill_batch('owner')
    assert result['reason']=='stale_batch';assert result['inserted']==0
    assert ready.neural.metadata('owner')['generation']!=old
    with ready.factory() as db:
        assert db.scalar(select(func.count()).select_from(SceneEmbedding))==0
        assert db.scalar(select(func.count()).select_from(NeuralJob))==0


def test_blob_validation_and_negative_cosine():
    e=embedding('x');row=SceneEmbedding(dimension=384,pooled=np.asarray(e['pooled'],dtype='<f4').tobytes(),windows=np.asarray(e['windows'],dtype='<f4').tobytes(),spans=e['spans'])
    p,v=decode(row);assert float(p@(-v[0]))==-1
    row.windows=b'bad'
    with pytest.raises(ValueError):decode(row)


def test_transient_failure_recovers_and_no_classify_on_chat(ready,monkeypatch):
    monkeypatch.setattr(ready.neural,'classify',lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError('classification entered chat')))
    turn=ready.chat('owner',ChatRequest(message='The office meeting includes the project report.',request_id=uuid4()))
    monkeypatch.setattr(ready.neural,'classify',lambda *args,**kwargs:{'status':'unavailable','reason':'deadline'})
    ready.neural.process_one()
    with ready.factory() as db:
        job=db.get(NeuralJob,(turn['turn_id'],'nli',version('nli')));assert job.status=='pending';job.due=0;db.commit()
    monkeypatch.setattr(ready.neural,'classify',lambda *args,**kwargs:{'status':'ready','suggestions':[]})
    ready.neural.process_one();assert ready.neural.classification('owner',turn['turn_id'])['status']=='ready'


def test_new_api_contracts_and_readonly_previews(ready,monkeypatch):
    from fastapi.testclient import TestClient
    import main
    import app.services.nlp_service as module
    from app.api.routes import get_current_user_id
    monkeypatch.setattr(module,'service',ready)
    monkeypatch.setattr(ready.neural,'classify',lambda *args,**kwargs:{'status':'ready','suggestions':[],'labels':[],'premise_count':1})
    main.app.dependency_overrides[get_current_user_id]=lambda:'owner'
    try:
        client=TestClient(main.app)
        assert client.get('/nlp/preferences').json()['share_history_with_provider'] is False
        assert client.get('/nlp/preferences').json()['process_local_unredacted'] is False
        assert client.get('/nlp/preferences').json()['store_local_unredacted_memory'] is False
        assert client.patch('/nlp/preferences',json={'share_history_with_provider':True}).json()['share_history_with_provider'] is True
        assert client.patch('/nlp/preferences',json={'process_local_unredacted':True}).json()['process_local_unredacted'] is True
        assert client.patch('/nlp/preferences',json={'store_local_unredacted_memory':True}).json()['store_local_unredacted_memory'] is True
        assert client.patch('/nlp/preferences',json={'store_local_unredacted_memory':False}).json()['store_local_unredacted_memory'] is False
        assert client.patch('/nlp/preferences',json={}).status_code==422
        assert client.post('/nlp/classification/preview',json={'text':'Maybe the office report needs discussion.'}).json()['status']=='ready'
        assert client.post('/nlp/memory/search',json={'query':'office report','limit':11}).status_code==422
        assert client.post('/nlp/memory/search',json={'query':'office report'}).json()['results']==[]
        with ready.factory() as db:assert db.scalar(select(func.count()).select_from(NeuralJob))==0
        turn=client.post('/chat',json={'message':'The office meeting report includes the project deadline.','request_id':str(uuid4())}).json()
        assert client.get(f"/nlp/turns/{turn['turn_id']}/classification").json()['status']=='pending'
        assert client.get('/nlp/neural/status').json()['evaluation']=='DATA_BLOCKED_NO_HUMAN_JUDGMENTS'
        assert client.post('/nlp/neural/backfill').json()['remaining']==0
        main.app.dependency_overrides[get_current_user_id]=lambda:'foreign'
        assert client.get(f"/nlp/turns/{turn['turn_id']}/classification").status_code==404
        main.app.dependency_overrides[get_current_user_id]=lambda:'owner'
        assert client.delete('/nlp/memory').json()['deleted']
        with ready.factory() as db:assert db.scalar(select(func.count()).select_from(SceneEmbedding))==0
    finally:main.app.dependency_overrides.clear()


def test_unredacted_local_mode_is_transient_and_provider_safe(ready):
    prompts=[]
    ready.generator=lambda prompt:prompts.append(prompt)
    prefs=ready.neural.preferences('owner',process_local_unredacted=True)
    assert prefs['process_local_unredacted'] is True
    result=ready.chat('owner',ChatRequest(message='Priya Sharma spoke because the Delhi meeting felt tense.',request_id=uuid4()))
    assert result['nlp_analysis']['local_processing_mode']=='unredacted_transient'
    assert result['nlp_analysis']['local_processing_scope']==['dependency_parse','clause_relations','lexical_features','lesk','dmrst']
    serialized=json.dumps(result)
    assert 'Priya Sharma' not in serialized
    assert 'Priya' not in serialized and 'Sharma' not in serialized
    assert all('Priya Sharma' not in prompt and 'Priya' not in prompt and 'Sharma' not in prompt for prompt in prompts)
    with ready.factory() as db:
        turn=db.get(ChatTurn,result['turn_id'])
        assert 'Priya Sharma' not in (turn.stripped_input or '')


def test_private_raw_memory_drives_local_embedding_nli_and_erases(ready,monkeypatch):
    embedded=[];classified=[];prompts=[]
    def raw_embedding(analysis,budget=2,text_override=None):
        embedded.append(text_override)
        return embedding(text_override or analysis['redacted_text'])
    monkeypatch.setattr(ready.neural,'embed',raw_embedding)
    monkeypatch.setattr(ready.neural,'classify',lambda user,analysis,generation,budget=10,text_override=None,offset_map=None: classified.append(text_override) or {'status':'ready','suggestions':[],'labels':[],'premise_count':1})
    ready.generator=lambda prompt:prompts.append(prompt)
    prefs=ready.neural.preferences('owner',True,store_local_unredacted_memory=True)
    assert prefs['store_local_unredacted_memory'] is True
    first=ready.chat('owner',ChatRequest(message='Priya Sharma discussed the Atlas project deadline.',request_id=uuid4()))
    second=ready.chat('owner',ChatRequest(message='Priya Sharma returned to the Atlas project discussion.',session_id=first['session_id'],request_id=uuid4()))
    assert embedded[-1]=='Priya Sharma returned to the Atlas project discussion.'
    assert second['nlp_analysis']['semantic_retrieval']['local_memory_mode']=='unredacted'
    assert second['nlp_analysis']['semantic_retrieval']['results'][0]['text']=='Priya Sharma discussed the Atlas project deadline.'
    assert all('Priya Sharma' not in prompt for prompt in prompts)
    with ready.factory() as db:
        assert db.get(LocalRawTurn,first['turn_id']).raw_text.startswith('Priya Sharma')
    assert ready.neural.process_one()
    assert classified and classified[0].startswith('Priya Sharma')
    ready.neural.preferences('owner',store_local_unredacted_memory=False)
    with ready.factory() as db:
        assert db.scalar(select(func.count()).select_from(LocalRawTurn))==0
        stored=db.get(NLPRecord,second['turn_id'])
        assert 'Priya Sharma' not in json.dumps(stored.result)
        assert stored.analysis['semantic_retrieval']['reason']=='unredacted_local_memory_erased'
