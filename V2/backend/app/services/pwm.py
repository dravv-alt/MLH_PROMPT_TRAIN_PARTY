"""User-owned explicit world memory; no inferred mental state or hidden intent."""
import copy
import re
from collections import Counter
from itertools import combinations

from app.services.nlp_engine import cosine


def update_world(doc, analysis, delta, prior=None):
    world=copy.deepcopy(prior or {'entities':[],'relationships':[],'scenes':[],'threads':[],'unresolved':[],'private_language':[]})
    world['entities']=copy.deepcopy(delta['entities'])
    scene_id=f"scene{max((int(s['id'][5:]) for s in world['scenes']),default=0)+1:06d}"
    ids=sorted({m['entity_id'] for m in analysis['mentions']})
    v=delta['turns'][-1]['vector']
    thread=None
    if analysis['topic_id'] and v:
        best=min(world['threads'],key=lambda t:(-cosine(v,t['centroid_sum']),t['id'])) if world['threads'] else None
        if best and cosine(v,best['centroid_sum'])>=.55:
            thread=best
            for k,value in v.items():thread['centroid_sum'][k]=thread['centroid_sum'].get(k,0.)+value
            thread['count']+=1
        else:
            next_id=max((int(t['id'][6:]) for t in world['threads']),default=0)+1
            thread={'id':f"thread{next_id:06d}",'centroid_sum':dict(v),'count':1,'scene_ids':[],'entity_ids':[],'activation':.3}
            world['threads'].append(thread)
        thread['scene_ids'].append(scene_id)
        thread['entity_ids']=sorted(set(thread['entity_ids']+ids))
        thread['activation']=min(1.,thread['activation']+.15)
    for other in world['threads']:
        if other is not thread:other['activation']*=.95
    scene={'id':scene_id,'entity_ids':ids,'thread_id':thread['id'] if thread else None,'text':analysis['redacted_text'],'vector':v,'relation_ids':[r['id'] for r in analysis['relations']]}
    world['scenes'].append(scene)
    for left,right in combinations(ids,2):
        existing=next((r for r in world['relationships'] if r['entity_ids']==[left,right] and r['type']=='co_mentioned'),None)
        if not existing:
            existing={'entity_ids':[left,right],'type':'co_mentioned','scene_ids':[]}
            world['relationships'].append(existing)
        existing['scene_ids'].append(scene_id)
    for pronoun in analysis['hobbs']['pronouns']:
        if not pronoun['antecedent']:
            next_id=max((int(u['id'][1:]) for u in world['unresolved']),default=0)+1
            world['unresolved'].append({'id':f"u{next_id:06d}",'scene_id':scene_id,'type':'unresolved_reference','span':pronoun['span'],'status':'open'})
    # Explicit unfinished markers; no claim that a user is avoiding or hiding something.
    if analysis['redacted_text'].rstrip().endswith(('...','…','—')):
        next_id=max((int(u['id'][1:]) for u in world['unresolved']),default=0)+1
        world['unresolved'].append({'id':f"u{next_id:06d}",'scene_id':scene_id,'type':'unfinished_expression','status':'open'})
    content=[t.lemma_.lower() or t.lower_ for t in doc if t.is_alpha and not t.is_stop]
    phrases=set(' '.join(content[i:i+3]) for i in range(max(0,len(content)-2)))
    quoted=re.findall(r'["“]([^"”]{3,100})["”]',analysis['redacted_text'])
    phrases.update(quoted)
    for phrase in sorted(phrases):
        if '[entity_' in phrase:continue
        entry=next((p for p in world['private_language'] if p['phrase']==phrase),None)
        if entry:entry['count']+=1;entry['scene_ids'].append(scene_id)
        else:world['private_language'].append({'phrase':phrase,'count':1,'scene_ids':[scene_id],'explicit_quote':phrase in quoted})
    public={
        'schema_version':'pwm.v1',
        'entities':[{'id':e['id'],'kind':e['kind']} for e in world['entities']],
        'relationships':world['relationships'],
        'scenes':[{k:v for k,v in s.items() if k!='vector'} for s in world['scenes']],
        'threads':[{k:v for k,v in t.items() if k!='centroid_sum'} for t in world['threads']],
        'unresolved':world['unresolved'],
        'private_language':[p for p in world['private_language'] if p['count']>=2 or p['explicit_quote']],
        'interpretation':'Relationships are explicit co-mentions; recurring phrases are lexical recurrence, not personality or intent.'
    }
    return public,world
