"""Annotation scaffolds and independently-labelled prediction scoring; no invented gold."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from sklearn.metrics import cohen_kappa_score
from app.services.neural_text import LABELS

KEYWORDS={
    'work':['office','job','meeting','work'], 'education':['class','exam','study','college'],
    'relationships':['friend','partner','family'], 'finances':['money','budget','payment'],
    'daily activities':['cook','walk','shopping'],'technology':['computer','software','phone'],
    'personal goals':['goal','achieve','practice'],'reporting an event':['happened','yesterday'],
    'explaining a cause':['because','therefore'],'expressing uncertainty':['maybe','perhaps','not sure'],
    'describing a contrast/conflict':['but','however','disagree'],'stating an intention':['will','plan to'],
    'closing the conversation':['thank you','stop here'],
}
STRATA=['paraphrase','same_topic_different_event','lexical_false_match','negation','short','long','ambiguous','no_match']


def prepare(folder):
    folder.mkdir(parents=True,exist_ok=True)
    for split,n_turns,n_queries in [('dev',100,40),('test',200,80)]:
        turns=[];queries=[]
        for i in range(n_turns):
            stratum=STRATA[i%len(STRATA)];event=f'{split}-event-{i:04d}'
            samples=['I dread speaking in front of people.','The office meeting was about a different report.',
                     'The meeting room is quiet; I am describing its furniture, not a discussion.',
                     'I am not planning to quit my job.','Maybe.',
                     'I wanted to discuss the report, but stayed quiet. '+('The office project has several deadlines. '*12),
                     'That could mean several things.','A comet crossed the sky.']
            turns.append({'id':event,'conversation_id':event,'stratum':stratum,'text':samples[i%8]+f' Entry {i}.',
                          'annotations':[{'annotator':'A','labels':None},{'annotator':'B','labels':None}],'gold':None})
        for i in range(n_queries):
            event=f'{split}-query-{i:04d}'
            queries.append({'id':event,'conversation_id':event,'stratum':STRATA[i%8],
                'query':'I feel nervous about presenting my report.' if i%8!=7 else 'I remember a comet.',
                'scenes':[{'id':f'{event}-s{j}','text':t} for j,t in enumerate(['I dread speaking in front of people.',
                    'The report discusses furniture purchases.','Another presentation occurred at a different event.',
                    'I am not worried about presenting.','I prepared dinner.','The meeting room contains a table.'])],
                'annotations':[{'annotator':'A','relevant_scene_ids':None},{'annotator':'B','relevant_scene_ids':None}],'gold':None})
        (folder/f'{split}.json').write_text(json.dumps({'synthetic_scaffolds':True,'turns':turns,'queries':queries},indent=2),encoding='utf-8')
    (folder/'protocol.json').write_text(json.dumps({'status':'DATA_BLOCKED_NO_HUMAN_JUDGMENTS','taxonomy':[l[0] for l in LABELS],
        'retrieval_arms':['hashed','semantic_pooled','semantic_max_window','rrf'],
        'window_comparisons':['128/32','224/32'],'requirements':'Replace repeated template text with distinct conversation/event cases; obtain two independent annotations and adjudicated gold before evaluation. Never treat scaffold examples as accuracy evidence.'},indent=2),encoding='utf-8')
    print('Prepared unlabelled scaffolds. DATA_BLOCKED_NO_HUMAN_JUDGMENTS')


def keyword(text):return [label for label,words in KEYWORDS.items() if any(w in text.casefold() for w in words)]


def metrics(turns,queries,predictions):
    tp=fp=fn=covered=0;counts={l[0]:[0,0,0,0] for l in LABELS}
    for item in turns:
        gold=set(item['gold']);pred=set(predictions.get('classification',{}).get(item['id'],[]));covered+=bool(pred)
        tp+=len(gold&pred);fp+=len(pred-gold);fn+=len(gold-pred)
        for label in counts:
            counts[label][0]+=label in gold;counts[label][1]+=label in gold&pred
            counts[label][2]+=label in pred-gold;counts[label][3]+=label in gold-pred
    p=tp/(tp+fp) if tp+fp else 0;r=tp/(tp+fn) if tp+fn else 0
    recalls=[];mrr=[];no_match=[]
    for item in queries:
        gold=set(item['gold']);ranking=predictions.get('retrieval',{}).get(item['id'],[])[:3]
        if not gold:no_match.append(not ranking);continue
        recalls.append(len(gold&set(ranking))/len(gold));mrr.append(next((1/(i+1) for i,s in enumerate(ranking) if s in gold),0))
    return {'micro_precision':p,'micro_recall':r,'micro_f1':2*p*r/(p+r) if p+r else 0,
            'coverage':covered/len(turns) if turns else None,'recall_at_3':float(np.mean(recalls)) if recalls else None,
            'mrr_at_3':float(np.mean(mrr)) if mrr else None,'no_match_abstention':float(np.mean(no_match)) if no_match else None,
            'per_label':{l:{'positive_count':n,'f1':2*a/(2*a+b+c) if n>=10 and 2*a+b+c else None} for l,(n,a,b,c) in counts.items()}}


def evaluate(dataset,predictions):
    items=dataset['turns']+dataset['queries']
    for item in items:
        key='labels' if 'text' in item else 'relevant_scene_ids'
        annotations=item.get('annotations',[])
        if item.get('gold') is None or len(annotations)!=2 or annotations[0]['annotator']==annotations[1]['annotator'] or any(a.get(key) is None for a in annotations):
            return {'status':'DATA_BLOCKED_NO_HUMAN_JUDGMENTS','metrics':None}
    result={'status':'labelled_evaluation','overall':metrics(dataset['turns'],dataset['queries'],predictions),'strata':{}}
    for stratum in STRATA:result['strata'][stratum]=metrics([t for t in dataset['turns'] if t['stratum']==stratum],[q for q in dataset['queries'] if q['stratum']==stratum],predictions)
    result['length_strata']={name:metrics([t for t in dataset['turns'] if (len(t['text'].split())<40)==short],[],predictions) for name,short in [('short',True),('long',False)]}
    pairs=[[],[]]
    for t in dataset['turns']:
        for label,_,_ in LABELS:
            for i,a in enumerate(t['annotations']):pairs[i].append(label in a['labels'])
    retrieval_pairs=[[],[]]
    for q in dataset['queries']:
        for s in q['scenes']:
            for i,a in enumerate(q['annotations']):retrieval_pairs[i].append(s['id'] in a['relevant_scene_ids'])
    def kappa(pair):
        if not pair[0]:return None
        value=float(cohen_kappa_score(*pair))
        return value if np.isfinite(value) else None
    result['kappa']={'classification':kappa(pairs),'retrieval':kappa(retrieval_pairs)}
    groups=sorted({t['conversation_id'] for t in items});rng=np.random.default_rng(1234);boot=[]
    for _ in range(2000):
        sampled=rng.choice(groups,len(groups),replace=True)
        selected=[item for group in sampled for item in items if item['conversation_id']==group]
        boot.append(metrics([t for t in selected if 'text' in t],[q for q in selected if 'query' in q],predictions))
    result['bootstrap_95_ci']={name:[float(np.quantile(values,.025)),float(np.quantile(values,.975))] for name in ['micro_precision','micro_recall','micro_f1','coverage','recall_at_3','mrr_at_3'] if (values:=[b[name] for b in boot if b[name] is not None])}
    result['keyword_baseline']=metrics(dataset['turns'],[],{'classification':{t['id']:keyword(t['text']) for t in dataset['turns']}})
    result['abstain_all']=metrics(dataset['turns'],dataset['queries'],{})
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','evaluate']);p.add_argument('--folder',type=Path,default=Path(__file__).resolve().parents[1]/'evaluation/neural');p.add_argument('--predictions',type=Path);p.add_argument('--split',choices=['dev','test'],default='test');args=p.parse_args()
    if args.action=='prepare':prepare(args.folder)
    else:
        data=json.loads((args.folder/f'{args.split}.json').read_text());pred=json.loads(args.predictions.read_text()) if args.predictions else {}
        report={name:evaluate(data,arm) for name,arm in pred['arms'].items()} if 'arms' in pred else evaluate(data,pred)
        print(json.dumps(report,indent=2,allow_nan=False))
