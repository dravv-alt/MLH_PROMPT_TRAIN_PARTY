"""Generate comparison-arm predictions; labels remain external human inputs."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse
import json
import time
import numpy as np
from app.services.neural_runtime import EMBEDDING,NLI,manifest
from app.services.neural_text import nli_candidates
from app.services.nlp_engine import parse,clause_graph,vector,cosine


def analysis(text):
    doc,_,reason=parse(text);clauses,_=clause_graph(doc,reason is not None)
    return {'redacted_text':text,'mentions':[],'clauses':clauses},vector([t.lemma_.lower() or t.lower_ for t in doc if t.is_alpha and not t.is_stop and t.pos_ not in {'DET','PRON','AUX','PART'}])


def generate(data):
    EMBEDDING.start();NLI.start();deadline=time.monotonic()+60
    while time.monotonic()<deadline and (EMBEDDING.state!='ready' or NLI.state!='ready'):time.sleep(.2)
    if EMBEDDING.state!='ready' or NLI.state!='ready':raise RuntimeError('models_unavailable')
    classification={}
    for turn in data['turns']:
        a,_=analysis(turn['text'])
        result=NLI.request({'text':a['redacted_text'],'mentions':[],'candidates':nli_candidates(a),'user':'synthetic-evaluation','generation':'evaluation','background':True},120)
        if result['status']!='ready':raise RuntimeError(result)
        classification[turn['id']]=[l['label'] for l in result['suggestions']]
    arms={'hashed':{'classification':classification,'retrieval':{}}}
    for size in [128,224]:
        for kind in ['semantic_pooled','semantic_max_window','rrf']:
            arms[f'{kind}_{size}']={'classification':classification,'retrieval':{}}
    for item in data['queries']:
        _,qhash=analysis(item['query']);shashes=[analysis(s['text'])[1] for s in item['scenes']]
        lex=sorted([(i,round(cosine(qhash,s),6)) for i,s in enumerate(shashes)],key=lambda p:(-p[1],p[0]));lex=[x for x in lex if x[1]>=.25]
        arms['hashed']['retrieval'][item['id']]=[item['scenes'][i]['id'] for i,_ in lex[:3]]
        for size in [128,224]:
            encoded=[]
            for text in [item['query']]+[s['text'] for s in item['scenes']]:
                result=EMBEDDING.request({'text':text,'mentions':[],'window_size':size,'background':True},120)
                if result['status']!='ready':raise RuntimeError(result)
                encoded.append(result)
            query=encoded[0];semantic=None
            for kind in ['semantic_pooled','semantic_max_window']:
                scores=[]
                for i,s in enumerate(encoded[1:]):
                    score=float(np.asarray(query['pooled'])@np.asarray(s['pooled'])) if kind=='semantic_pooled' else float((np.asarray(query['windows'])@np.asarray(s['windows']).T).max())
                    scores.append((i,round(score,6)))
                ranked=sorted((p for p in scores if p[1]>0),key=lambda p:(-p[1],p[0]))
                arms[f'{kind}_{size}']['retrieval'][item['id']]=[item['scenes'][i]['id'] for i,_ in ranked[:3]]
                if kind=='semantic_max_window':semantic=ranked
            fusion={}
            for ranked in [lex,semantic]:
                for rank,(i,_) in enumerate(ranked,1):fusion[i]=fusion.get(i,0)+1/(60+rank)
            ranked=sorted(fusion,key=lambda i:(-round(fusion[i],6),i))
            arms[f'rrf_{size}']['retrieval'][item['id']]=[item['scenes'][i]['id'] for i in ranked[:3]]
    return {'versions':manifest()['versions'],'exploratory_suggestions':True,'arms':arms}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    try:args.output.write_text(json.dumps(generate(json.loads(args.dataset.read_text())),indent=2),encoding='utf-8')
    finally:EMBEDDING.stop();NLI.stop()
