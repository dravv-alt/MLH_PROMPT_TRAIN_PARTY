"""Versioned neural input coordinates and fixed, non-diagnostic taxonomy."""
import hashlib
import json
import re

PREPROCESS = 'surrogate.v1'
TAXONOMY = 'topics-functions.v1'
LABELS = [
    ('work','topic','The speaker discusses work.'),
    ('education','topic','The speaker discusses education.'),
    ('relationships','topic','The speaker discusses personal relationships.'),
    ('finances','topic','The speaker discusses finances.'),
    ('daily activities','topic','The speaker discusses daily activities.'),
    ('technology','topic','The speaker discusses technology.'),
    ('personal goals','topic','The speaker discusses personal goals.'),
    ('reporting an event','function','The speaker reports an event.'),
    ('explaining a cause','function','The speaker explains why something happened.'),
    ('expressing uncertainty','function','The speaker expresses uncertainty.'),
    ('describing a contrast/conflict','function','The speaker describes a contrast or conflict.'),
    ('stating an intention','function','The speaker states an intention.'),
    ('closing the conversation','function','The speaker closes the conversation.'),
]
NULLS = ['N/A', 'No content provided.', 'This is a message.']


def surrogate(text, mentions):
    replacements = {tuple(m['span']): m['kind'] for m in mentions}
    chunks, segments, cursor, offset = [], [], 0, 0
    for match in re.finditer(r'\[[\w]+\]', text):
        a,b = match.span()
        if a > cursor:
            chunks.append(text[cursor:a]); segments.append(([offset,offset+a-cursor],[cursor,a],False)); offset += a-cursor
        kind = replacements.get((a,b),'OTHER').upper()
        word = ('someone' if kind=='PERSON' else 'an organization' if kind=='ORG' else
                'a place' if kind in {'GPE','LOC','FAC'} else 'contact information' if kind in {'EMAIL','PHONE','URL','CONTACT'} else
                'a time' if kind in {'DATE','TIME'} else 'something')
        chunks.append(word);segments.append(([offset,offset+len(word)],[a,b],True));offset+=len(word);cursor=b
    chunks.append(text[cursor:]);segments.append(([offset,offset+len(text)-cursor],[cursor,len(text)],False))
    return ''.join(chunks),segments


def canonical_spans(segments, start, end):
    spans=[]
    for (a,b),(x,y),replacement in segments:
        lo,hi=max(start,a),min(end,b)
        if lo>=hi:continue
        span=[x,y] if replacement else [x+lo-a,x+hi-a]
        if spans and span[0]<=spans[-1][1]:spans[-1][1]=max(spans[-1][1],span[1])
        else:spans.append(span)
    return spans


def input_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def nli_candidates(analysis):
    # Existing clauses carry sentence IDs. Sentence hull retains connective context.
    sentences={}
    for c in analysis.get('clauses',[]):sentences.setdefault(c['sentence'],[]).append(c)
    text=analysis['redacted_text']
    if not sentences:return [{'spans':[[0,len(text)]],'clauses':[]}]
    result=[]
    for _,clauses in sorted(sentences.items()):
        spans=[s for c in clauses for s in c['spans']]
        result.append({'spans':[[min(s[0] for s in spans),max(s[1] for s in spans)]], 'clauses':[c['spans'] for c in clauses]})
    return result


def aggregate(probabilities, premises, null_scores):
    labels=[]
    for i,(name,group,_) in enumerate(LABELS):
        best=min(range(len(premises)),key=lambda j:(-round(probabilities[j][i][1]-null_scores[i],6),j))
        c,e,n=probabilities[best][i]
        labels.append({'label':name,'group':group,'entailment':round(e,6),'neutral':round(n,6),'contradiction':round(c,6),
                       'adjusted_score':round(e-null_scores[i],6),'spans':premises[best]['spans']})
    suggestions=[]
    for group,limit in [('topic',3),('function',2)]:
        suggestions.extend(sorted((l for l in labels if l['group']==group and l['adjusted_score']>0),key=lambda l:(-l['adjusted_score'],l['label']))[:limit])
    return {'status':'ready','taxonomy_version':TAXONOMY,'premise_count':len(premises),'labels':labels,'suggestions':suggestions,
            'notice':'Experimental, not validated on Sanctuary conversations. Adjusted scores are not calibrated confidence.'}
