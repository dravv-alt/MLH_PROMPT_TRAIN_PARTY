"""Explicit loopback-only integration fixture; never imported by main.py."""
import os
if os.getenv('SANCTUARY_BROWSER_FIXTURE') != '1':
    raise RuntimeError('This fixture requires SANCTUARY_BROWSER_FIXTURE=1 and a loopback listener.')

from collections import Counter
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from uuid import uuid4
from app.models.db import Base
from app.services.nlp_service import NLPService
from app.services.session_state import SessionStateStore
from app.services.journal_service import JournalService
import app.api.routes as routes
import app.services.dmrst as dmrst
import app.services.classical_nlp as classical
import app.services.hosted_generation as hosted
from app.services.nlp_engine import parse, vector
from app.services.memory_tools import retrieve_scenes

fixture_dir=Path(__file__).resolve().parents[2]/'.runtime'/'integration-check'
fixture_dir.mkdir(parents=True,exist_ok=True)
fixture_database=fixture_dir/f'browser-{uuid4().hex}.db'
engine=create_engine(f'sqlite:///{fixture_database.as_posix()}',connect_args={'check_same_thread':False})
@event.listens_for(engine,'connect')
def foreign_keys(db,_):db.execute('PRAGMA foreign_keys=ON')
Base.metadata.create_all(engine)
factory=sessionmaker(engine,expire_on_commit=False)
service=NLPService(factory,'browser-fixture-only',lambda _:None)
dmrst.parse_dmrst=lambda _: {'status':'unavailable','reason':'browser_fixture','edus':[],'tree':[]}
classical.discourse_entities=lambda *a: ({'hobbs':{'pronouns':[]},'centering':{'trace':[]}},[])

def enrich(user,analysis,state,**kwargs):
    doc,_,_=parse(analysis['redacted_text'])
    query=vector([t.lemma_.lower() for t in doc if t.is_alpha and not t.is_stop])
    hits=retrieve_scenes(query,state.get('world'))
    results=[]
    for hit in hits:
        scene=next(s for s in state['world']['scenes'] if s['id']==hit['scene_id'])
        results.append({**hit,'excerpt':scene['text'],'source_turn_id':scene.get('turn_id'),'source_session_id':scene.get('session_id'),
                        'lexical_score':hit['similarity'],'semantic_score':None,'fusion_score':round(1/61,6)})
    analysis['memory_retrieval']=results
    analysis['semantic_retrieval']={'status':'ready','method':'lexical_fixture','results':results,'coverage':{'indexed_scenes':0,'eligible_scenes':len(state.get('world',{}).get('scenes',[]))}}
    return {'status':'unavailable','reason':'browser_fixture'},query
service.enrich=enrich
calls=Counter()
def classification(user,turn_id):
    calls[turn_id]+=1
    return {'status':'pending' if calls[turn_id]==1 else 'ready','premise_count':1,'suggestions':[],'labels':[]}
service.neural.classification=classification
routes.get_nlp_service=lambda:service
hosted.hosted_status=lambda:{'configured':True,'provider':'fixture','model':'fixture-no-network','requires_explicit_consent':True}
hosted.generate_hosted=lambda *args:(None,{'reason':'mocked_outage'})
app=FastAPI()
app.state.session_state=SessionStateStore(factory)
app.state.journal_service=JournalService(factory)
app.dependency_overrides[routes.get_current_user_id]=lambda:'browser-fixture-owner'
app.include_router(routes.router)
@app.exception_handler(HTTPException)
async def error(request:Request,exc:HTTPException):
    detail=exc.detail if isinstance(exc.detail,dict) else {'message':str(exc.detail)}
    return JSONResponse({'error':detail},status_code=exc.status_code)
