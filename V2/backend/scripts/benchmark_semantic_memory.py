"""Synthetic infrastructure benchmark: actual adapters/index, not quality or user load."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import tempfile
import time
import os
import subprocess
from uuid import uuid4
import numpy as np
from sqlalchemy import create_engine,event,insert
from sqlalchemy.orm import sessionmaker
from app.models.db import Base
from app.models.orm import ChatSession,ChatTurn,NeuralMemoryState,SceneEmbedding
from app.services.neural_memory import NeuralMemory,invalidate
from app.services.neural_runtime import EMBEDDING,NLI,version
from app.services.neural_text import nli_candidates
from app.services.dmrst import parse_dmrst


def memory_usage():
    ids=[os.getpid()]+[w.proc.pid for w in (EMBEDDING,NLI) if w.proc]
    from app.services import dmrst
    if dmrst._WORKER:ids.append(dmrst._WORKER.pid)
    if os.name!='nt':return {'status':'unavailable','reason':'Windows measurement script'}
    command='Get-Process -Id '+','.join(map(str,ids))+' | Select-Object Id,WorkingSet64,PeakWorkingSet64 | ConvertTo-Json -Compress'
    try:return json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',command],text=True))
    except Exception:return {'status':'unavailable'}


def main():
    report={'synthetic':True,'quality_claims':False,'runs':[]}
    start=time.monotonic();EMBEDDING.start();NLI.start()
    while time.monotonic()-start<60 and (EMBEDDING.state!='ready' or NLI.state!='ready'):time.sleep(.1)
    report['cold_ready_seconds']=round(time.monotonic()-start,4)
    a={'redacted_text':'I felt nervous about presenting my project report.','mentions':[],'clauses':[{'sentence':0,'spans':[[0,49]]}], '_query_vector':{'1':1.}}
    start=time.monotonic();embedding=EMBEDDING.request({'text':a['redacted_text'],'mentions':[]},5);report['warm_embedding_seconds']=round(time.monotonic()-start,4)
    if embedding['status']!='ready':raise RuntimeError(embedding)
    start=time.monotonic();nli=NLI.request({'text':a['redacted_text'],'mentions':[],'candidates':nli_candidates(a),'user':'benchmark','generation':'benchmark'},30);report['warm_nli_seconds']=round(time.monotonic()-start,4);report['nli_status']=nli['status']
    start=time.monotonic();rst=parse_dmrst(a['redacted_text']);report['dmrst_seconds']=round(time.monotonic()-start,4);report['dmrst_status']=rst['status']
    report['memory_with_models']=memory_usage()
    from app.services import dmrst
    report['process_roles']={'host':os.getpid(),'embedding':EMBEDDING.proc.pid,'nli':NLI.proc.pid,'dmrst':dmrst._WORKER.pid if dmrst._WORKER else None}
    with tempfile.TemporaryDirectory(prefix='sanctuary-neural-benchmark-') as folder:
        engine=create_engine('sqlite:///'+(Path(folder)/'benchmark.db').as_posix());factory=sessionmaker(engine,expire_on_commit=False)
        @event.listens_for(engine,'connect')
        def foreign_keys(connection,_):connection.execute('PRAGMA foreign_keys=ON')
        Base.metadata.create_all(engine);neural=NeuralMemory(factory);generation=str(uuid4());user='synthetic-benchmark'
        with factory() as db:db.add(ChatSession(session_id='benchmark',user_id=user));db.add(NeuralMemoryState(user_id=user,generation=generation,index_revision=1,share_history=False,preference_revision=0));db.commit()
        vector=np.asarray(embedding['pooled'],dtype='<f4').tobytes();windows=np.asarray(embedding['windows'],dtype='<f4').tobytes()
        for count in [100,1000,10000]:
            with factory() as db:
                db.query(SceneEmbedding).delete();db.query(ChatTurn).delete()
                db.execute(insert(ChatTurn),[{'id':i,'session_id':'benchmark','user_id':user,'turn_index':i,'stripped_input':a['redacted_text'],'response_text':None,'safety_mode':'benchmark','narrative_structure':{}} for i in range(1,count+1)])
                db.execute(insert(SceneEmbedding),[{'turn_id':i,'version':version('embedding'),'user_id':user,'generation':generation,'scene_id':f'scene{i:06d}','input_hash':embedding['input_hash'],'dimension':384,'pooled':vector,'windows':windows,'spans':embedding['spans']} for i in range(1,count+1)]);db.commit()
            world={'scenes':[{'id':f'scene{i:06d}','turn_id':i,'session_id':'benchmark','text':a['redacted_text'],'vector':{'1':1.}} for i in range(1,count+1)]};meta={'generation':generation,'index_revision':1}
            invalidate(user)
            for mode in ['cold_index','cached_index']:
                start=time.monotonic();result=neural.search(user,a,world,count,meta,embedding,budget=5)
                report['runs'].append({'scenes':count,'mode':mode,'seconds':round(time.monotonic()-start,4),'status':result['status'],'coverage':result['coverage']})
            report[f'memory_{count}']=memory_usage()
        engine.dispose()
    dest=Path(__file__).resolve().parents[1]/'data/neural-benchmark.json';dest.parent.mkdir(exist_ok=True);dest.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))


if __name__=='__main__':
    try:main()
    finally:EMBEDDING.stop();NLI.stop()
