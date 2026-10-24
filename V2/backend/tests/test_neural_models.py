"""Real-model functional smoke tests; no semantic-quality claims."""
import time
import numpy as np
from app.services.neural_runtime import EMBEDDING,NLI,manifest
from app.services.neural_text import nli_candidates
from test_nlp import service
from app.models.schemas import ChatRequest
from uuid import uuid4


def test_real_cpu_embedding_and_nli():
    assert manifest(), 'Run scripts/setup_semantic_resources.py before resource smoke tests.'
    EMBEDDING.start();NLI.start()
    try:
        deadline=time.monotonic()+60
        while time.monotonic()<deadline and (EMBEDDING.state!='ready' or NLI.state!='ready'):time.sleep(.2)
        assert EMBEDDING.state=='ready';assert NLI.state=='ready'
        a={'redacted_text':'I may finish the project tomorrow.','mentions':[],'clauses':[{'sentence':0,'spans':[[0,33]]}]}
        e=EMBEDDING.request({'text':a['redacted_text'],'mentions':[]},5)
        assert e['status']=='ready',e
        assert len(e['pooled'])==384;assert np.isclose(np.linalg.norm(e['pooled']),1,atol=1e-5)
        repeated=EMBEDDING.request({'text':a['redacted_text'],'mentions':[]},5)
        assert np.allclose(e['pooled'],repeated['pooled'],atol=1e-6)
        too_long=EMBEDDING.request({'text':'word '*1000,'mentions':[]},5)
        assert too_long['reason']=='input_too_long'
        c=NLI.request({'text':a['redacted_text'],'mentions':[],'candidates':nli_candidates(a),'user':'synthetic','generation':'smoke'},20)
        assert c['status']=='ready',c;assert len(c['labels'])==13;assert c['premise_count']==1
        assert all(0<=l['entailment']<=1 for l in c['labels'])
        grounding=NLI.request({'task':'semantic_validation','pairs':[
            {'id':'supported','purpose':'evidence_support','premise':'The preparation left the speaker exhausted.','hypothesis':'The preparation was exhausting.'},
            {'id':'opposite','purpose':'evidence_support','premise':'The speaker is excited about the internship.','hypothesis':'The speaker hates the internship.'},
        ]},10)
        assert grounding['status']=='ready',grounding
        by_id={row['id']:row['scores'] for row in grounding['pairs']}
        assert by_id['supported']['entailment']>by_id['supported']['contradiction']
        assert by_id['opposite']['contradiction']>by_id['opposite']['entailment']
    finally:EMBEDDING.stop();NLI.stop()


def test_actual_background_classification_persists(service):
    service.neural.start()
    try:
        committed=service.chat('synthetic-owner',ChatRequest(message='Maybe I will finish the project report tomorrow.',request_id=uuid4()))
        assert committed['nlp_analysis']['classification']['status']=='pending'
        deadline=time.monotonic()+40;result={}
        while time.monotonic()<deadline:
            result=service.neural.classification('synthetic-owner',committed['turn_id'])
            if result['status'] not in {'pending','running'}:break
            time.sleep(.2)
        assert result['status']=='ready',result
        assert len(result['labels'])==13
        assert committed['nlp_analysis']['classification']['status']=='pending'
    finally:service.neural.stop()
