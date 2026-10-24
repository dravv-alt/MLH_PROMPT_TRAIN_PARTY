"""Local model process; cooperative cancellation between bounded inference units."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import os
import queue
import threading
import time
import hashlib
from collections import OrderedDict, deque
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
from app.services.neural_text import surrogate, canonical_spans, LABELS, NULLS, aggregate, input_hash

kind,root=sys.argv[1],Path(sys.argv[2])
torch.set_num_threads(int(os.getenv('SANCTUARY_NEURAL_THREADS','2')))
torch.set_num_interop_threads(1)
torch.backends.mkldnn.enabled=False
torch.use_deterministic_algorithms(True)
torch.manual_seed(1234)
folder=root/('embedding' if kind=='embedding' else 'nli')
if '--calibrate' not in sys.argv:
    resource_manifest=json.loads((root/'manifest.json').read_text())
    for name,expected in resource_manifest['sha256'].items():
        normalized=name.replace('\\','/')
        if not (normalized.startswith(kind+'/') or (kind=='nli' and normalized=='null_scores.json')):continue
        digest=hashlib.sha256()
        with (root/name).open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
        if digest.hexdigest()!=expected:raise ValueError('resource_checksum_mismatch')
tokenizer=AutoTokenizer.from_pretrained(folder,local_files_only=True,from_slow=(kind=='nli'))
model=(AutoModel if kind=='embedding' else AutoModelForSequenceClassification).from_pretrained(folder,local_files_only=True,attn_implementation='eager').cpu().eval()
if kind=='nli':
    assert [model.config.id2label[i].lower() for i in range(3)]==['contradiction','entailment','neutral']


def repeatable():
    text='I may finish the project tomorrow, but the meeting needs further discussion.'
    enc=tokenizer(text,return_tensors='pt') if kind=='embedding' else tokenizer([text]*len(LABELS),[l[2] for l in LABELS],padding=True,return_tensors='pt')
    def run():
        torch.manual_seed(1234)
        with torch.inference_mode():
            out=model(**enc)
            return (out.last_hidden_state if kind=='embedding' else out.logits).clone()
    a=run();return torch.allclose(a,run(),atol=1e-6,rtol=1e-6) and torch.allclose(a,run(),atol=1e-6,rtol=1e-6)


thread_fallback=False
if not repeatable():
    torch.set_num_threads(1);thread_fallback=True
    if not repeatable():raise ValueError('repeatability_self_check_failed')


def emit(value):print(json.dumps(value,separators=(',',':')),flush=True)


def nli_batch(premise):
    torch.manual_seed(1234);model.eval()
    enc=tokenizer([premise]*len(LABELS),[l[2] for l in LABELS],padding=True,return_tensors='pt',truncation=False)
    if enc['input_ids'].shape[1]>512:raise ValueError('input_too_long')
    with torch.inference_mode():return torch.softmax(model(**enc).logits,dim=-1).tolist()


def nli_pair(premise,hypothesis):
    """Score one arbitrary grounding pair with the pinned three-way NLI head."""
    torch.manual_seed(1234);model.eval()
    enc=tokenizer(premise,hypothesis,return_tensors='pt',truncation=False)
    if enc['input_ids'].shape[1]>512:raise ValueError('input_too_long')
    with torch.inference_mode():
        values=torch.softmax(model(**enc).logits,dim=-1)[0].tolist()
    return {'contradiction':values[0],'entailment':values[1],'neutral':values[2]}


if '--calibrate' in sys.argv:
    scores=np.mean([nli_batch(p) for p in NULLS],axis=0)[:,1].tolist()
    (root/'null_scores.json').write_text(json.dumps({'premises':NULLS,'scores':scores}),encoding='utf-8')
    sys.exit(0)
null_scores=json.loads((root/'null_scores.json').read_text())['scores'] if kind=='nli' else None
incoming=queue.Queue(); cancelled=set(); cache=OrderedDict()


def reader():
    for line in sys.stdin:
        request=json.loads(line)
        if request.get('cancel'):cancelled.add(request['id'])
        elif request.get('clear_user'):
            for key in list(cache):
                if key[0]==request['clear_user']:cache.pop(key,None)
        else:incoming.put(request)


threading.Thread(target=reader,daemon=True).start()
emit({'status':'ready','threads':torch.get_num_threads(),'thread_fallback':thread_fallback})
jobs=deque()


def mapped_text(text,mentions,spans):
    parts=[];mapping=[];offset=0
    for i,(a,b) in enumerate(spans):
        if i:parts.append(' … ');offset+=3
        local=[{**m,'span':[m['span'][0]-a,m['span'][1]-a]} for m in mentions if a<=m['span'][0] and m['span'][1]<=b]
        transformed,segments=surrogate(text[a:b],local)
        parts.append(transformed)
        mapping.extend(([x+offset,y+offset],[c+a,d+a],r) for (x,y),(c,d),r in segments)
        offset+=len(transformed)
    return ''.join(parts),mapping


def windows(text,mapping,size,overlap):
    encoded=tokenizer(text,add_special_tokens=False,return_offsets_mapping=True)
    ids,offsets=encoded['input_ids'],encoded['offset_mapping']
    result=[];start=0
    while start<len(ids):
        end=min(start+size,len(ids)); a,b=offsets[start][0],offsets[end-1][1]
        result.append({'ids':ids[start:end],'text':text[a:b],'spans':canonical_spans(mapping,a,b),'weight':end-start if start==0 else end-start-overlap})
        if end==len(ids):break
        start=end-overlap
    return result


def prepare(req):
    if kind=='nli' and req.get('task')=='semantic_validation':
        pairs=req.get('pairs',[])
        if not 1<=len(pairs)<=32:raise ValueError('invalid_pair_count')
        units=[]
        for pair in pairs:
            premise=str(pair.get('premise','')).strip();hypothesis=str(pair.get('hypothesis','')).strip()
            if not premise or not hypothesis:raise ValueError('empty_pair_text')
            units.append({'id':str(pair.get('id','')),'premise':premise,'hypothesis':hypothesis,'purpose':str(pair.get('purpose',''))})
        return {'req':req,'units':units,'values':[],'i':0,'task':'semantic_validation'}
    text=req['text'];mentions=req.get('mentions',[])
    if kind=='embedding':
        transformed,mapping=surrogate(text,mentions)
        units=windows(transformed,mapping,req.get('window_size',128),32)
        if not units:raise ValueError('empty_input')
        if len(units)>8:raise ValueError('input_too_long')
        return {'req':req,'units':units,'values':[],'hash':input_hash(transformed),'i':0}
    units=[]
    for candidate in req['candidates']:
        transformed,mapping=mapped_text(text,mentions,candidate['spans'])
        if len(tokenizer(transformed,add_special_tokens=False)['input_ids'])<=128:
            units.extend(windows(transformed,mapping,128,16))
        else:
            for spans in candidate.get('clauses') or [candidate['spans']]:
                t,m=mapped_text(text,mentions,spans);units.extend(windows(t,m,128,16))
    if not units:raise ValueError('empty_input')
    if len(units)>32:raise ValueError('input_too_long')
    return {'req':req,'units':units,'values':[],'i':0}


while True:
    if not jobs:
        jobs.append(incoming.get())
    while not incoming.empty():jobs.append(incoming.get())
    live_index=next((i for i,j in enumerate(jobs) if not j.get('req',j).get('background')),0)
    jobs.rotate(-live_index)
    job=jobs.popleft();req=job.get('req',job)
    jobs.rotate(live_index)
    if req['id'] in cancelled or time.time()>req['deadline']:
        cancelled.discard(req['id']);emit({'id':req['id'],'epoch':req['epoch'],'result':{'status':'unavailable','reason':'deadline'}});continue
    try:
        if 'units' not in job:job=prepare(req)
        unit=job['units'][job['i']]
        if kind=='embedding':
            torch.manual_seed(1234);model.eval()
            enc=tokenizer.prepare_for_model(unit['ids'],return_tensors='pt')
            enc={k:v.unsqueeze(0) for k,v in enc.items()}
            with torch.inference_mode():
                hidden=model(**enc).last_hidden_state;mask=enc['attention_mask'].unsqueeze(-1)
                vector=torch.nn.functional.normalize((hidden*mask).sum(1)/mask.sum(1),p=2,dim=1)[0].tolist()
            job['values'].append(vector)
        else:
            if job.get('task')=='semantic_validation':
                pair_hash=input_hash(unit['premise']+'\x00'+unit['hypothesis'])
                key=(req.get('user',''),req.get('generation',''),pair_hash,req['version'],'semantic_validation')
                scores=cache.pop(key,None)
                if scores is None:scores=nli_pair(unit['premise'],unit['hypothesis'])
                values={'id':unit['id'],'purpose':unit['purpose'],'scores':scores}
            else:
                key=(req.get('user',''),req.get('generation',''),input_hash(unit['text']),req['version'])
                values=cache.pop(key,None)
                if values is None:values=nli_batch(unit['text'])
            if req['id'] not in cancelled:cache[key]=scores if job.get('task')=='semantic_validation' else values
            while len(cache)>4096:cache.popitem(last=False)
            job['values'].append(values)
        job['i']+=1
        emit({'progress':req['id'],'epoch':req['epoch']})
        if job['i']<len(job['units']):jobs.append(job);continue
        if kind=='embedding':
            vectors=np.array(job['values'],dtype=np.float32)
            pooled=np.average(vectors,axis=0,weights=[u['weight'] for u in job['units']]);pooled/=np.linalg.norm(pooled)
            result={'status':'ready','input_hash':job['hash'],'pooled':pooled.tolist(),'windows':vectors.tolist(),'spans':[u['spans'] for u in job['units']]}
        elif job.get('task')=='semantic_validation':result={'status':'ready','pairs':job['values']}
        else:result=aggregate(job['values'],job['units'],null_scores)
        result['version']=req['version'];emit({'id':req['id'],'epoch':req['epoch'],'result':result})
    except Exception as exc:
        reason=str(exc) if isinstance(exc,ValueError) else 'inference_failed'
        emit({'id':req['id'],'epoch':req['epoch'],'result':{'status':'unavailable','reason':reason}})
