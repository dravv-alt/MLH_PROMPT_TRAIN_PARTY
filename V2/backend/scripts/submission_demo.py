"""Generate synthetic examples/sensitivity data, or serve the built offline fixture page."""
import argparse
import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.nlp_engine import analyze_turn, FALLBACKS

SCENARIOS = [
    "Priya Sharma called the office, but Priya stayed quiet because the meeting felt tense.",
    "The office meeting agenda included the project report and deadline.",
    "Maybe the project report and office meeting deadline need more discussion.",
    "The project report includes meeting notes and office deadlines.",
    "I cooked pasta with tomatoes and vegetables in the kitchen.",
    "If the team calls, I will explain the project report.",
    "I am wondering if the team will call. I am so tired and angry.",
    "Thank you.",
]


def build():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.db import Base
    from app.models.orm import ChatSession,ChatTurn
    from app.services.neural_memory import NeuralMemory,write_embedding,invalidate
    from app.services.neural_runtime import EMBEDDING,NLI
    import copy,time
    engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(engine);factory=sessionmaker(engine,expire_on_commit=False)
    neural=NeuralMemory(factory);EMBEDDING.start();NLI.start();deadline=time.monotonic()+60
    while time.monotonic()<deadline and (EMBEDDING.state!='ready' or NLI.state!='ready'):time.sleep(.1)
    with factory() as db:db.add(ChatSession(session_id='synthetic-demo',user_id='synthetic-demo'));db.commit()
    samples, state = [], {}
    for index,text in enumerate(SCENARIOS,1):
        prior_world=copy.deepcopy(state.get('world',{}))
        analysis, state, _ = analyze_turn(text, state, {"alias_key":"synthetic-demo-only"})
        embedding=neural.embed(analysis,5)
        prepared={**analysis,'_query_vector':state['turns'][-1]['vector']}
        meta={'generation':'synthetic-demo','index_revision':index-1}
        analysis['semantic_retrieval']=neural.search('synthetic-demo',prepared,prior_world,index-1,meta,embedding)
        analysis['classification']=neural.classify('synthetic-demo',analysis,'synthetic-demo',30)
        scene=state['world']['scenes'][-1];scene['session_id']='synthetic-demo';scene['turn_id']=index
        analysis['pwm']['scenes'][-1]['session_id']='synthetic-demo';analysis['pwm']['scenes'][-1]['turn_id']=index
        with factory() as db:
            db.add(ChatTurn(id=index,session_id='synthetic-demo',user_id='synthetic-demo',turn_index=index,stripped_input=analysis['redacted_text'],response_text=None,safety_mode='synthetic',narrative_structure={}));db.flush()
            if embedding.get('status')=='ready':write_embedding(db,'synthetic-demo','synthetic-demo',scene,embedding)
            db.commit()
        samples.append({"analysis":analysis,"response":FALLBACKS[analysis['strategy']]})
    EMBEDDING.stop();NLI.stop();invalidate('synthetic-demo');engine.dispose()
    sweep=[]
    for threshold in [.45,.55,.65]:
        for reverse in [False,True]:
            snapshot={}
            for text in reversed(SCENARIOS) if reverse else SCENARIOS:
                _,snapshot,_=analyze_turn(text,snapshot,{"alias_key":"synthetic-demo-only","topic_threshold":threshold})
            sweep.append({"threshold":threshold,"order":"reversed" if reverse else "original","topic_counts":[t['count'] for t in snapshot['topics']],"assignments":[t['topic_id'] for t in snapshot['turns']]})
    return {"synthetic":True,"samples":samples,"sensitivity_sweep":sweep}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--serve',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    dest=root/'frontend'/'public'/'submission-demo.json'
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(build(),ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8')
    print(f'Synthetic report written: {dest}')
    if args.serve:
        dist=root/'frontend'/'dist'
        if not (dist/'demo.html').exists():
            raise SystemExit('Build frontend first: npm.cmd run build')
        # Update the packaged fixture after a rebuild of the analysis engine.
        (dist/'submission-demo.json').write_bytes(dest.read_bytes())
        print('Open http://127.0.0.1:8790/demo.html')
        ThreadingHTTPServer(('127.0.0.1',8790),partial(SimpleHTTPRequestHandler,directory=str(dist))).serve_forever()


if __name__=='__main__':
    main()
