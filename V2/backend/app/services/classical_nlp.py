"""Inspectable simplified Lesk, Hobbs proposal order, and Centering traces."""
import re
import threading
from collections import deque
from functools import lru_cache
from nltk.corpus import wordnet as wn
from nltk.tree import Tree
import nltk
from pathlib import Path

nltk.data.path.insert(0,str(Path(__file__).resolve().parents[2]/'models/nltk'))

_LOCK = threading.RLock()


def words(text):
    return set(re.findall(r"[a-z]+", text.lower())) - {'the','a','an','and','of','to','in','is','be','that','it'}


def lesk(doc):
    results=[]
    try:
        wn.ensure_loaded()
    except LookupError:
        return {'status':'unavailable','reason':'wordnet_missing','senses':[]}
    for token in doc:
        pos={'NOUN':wn.NOUN,'VERB':wn.VERB,'ADJ':wn.ADJ,'ADV':wn.ADV}.get(token.pos_)
        if not pos or not token.is_alpha or token.is_stop:
            continue
        candidates=wn.synsets(token.lemma_.lower(),pos=pos)
        context=words(token.sent.text)-{token.lemma_.lower(),token.lower_}
        scored=[]
        for rank,synset in enumerate(candidates):
            signature=words(synset.definition()+' '+' '.join(synset.examples())+' '+' '.join(synset.lemma_names()))
            overlap=sorted(context & signature)
            ancestors={s.name() for path in synset.hypernym_paths() for s in path}
            scored.append({'sense':synset.name(),'definition':synset.definition(),'score':len(overlap),'overlap':overlap,'wordnet_rank':rank,'animacy':'person' if 'person.n.01' in ancestors else 'animal' if 'animal.n.01' in ancestors else 'unknown'})
        if scored:
            scored.sort(key=lambda s:(-s['score'],s['wordnet_rank'],s['sense']))
            results.append({'span':[token.idx,token.idx+len(token)],'lemma':token.lemma_,'selected':scored[0],'candidates':scored})
    return {'status':'ready','algorithm':'simplified_lesk_set_overlap','tie_break':'WordNet sense order then synset name','senses':results}


@lru_cache(maxsize=1)
def constituency_parser():
    import benepar
    import torch
    torch.set_num_threads(4)
    parser=benepar.Parser('benepar_en3')
    parser._parser.cpu()
    return parser


def proposal_positions(tree, pronoun_leaf, previous=()):
    """Hobbs steps 2–9. Positions are tree coordinates, in proposal order."""
    leaf=tree.leaf_treeposition(pronoun_leaf)
    ancestors=[leaf[:i] for i in range(len(leaf)-1,-1,-1)]
    np=next((p for p in ancestors if isinstance(tree[p],Tree) and tree[p].label()=='NP'),None)
    if np is None:
        return []
    results=[]
    def bfs_left(x,path,require_intermediate=False):
        queue=deque([x])
        while queue:
            p=queue.popleft(); node=tree[p]
            if not isinstance(node,Tree):continue
            if p not in path and node.label()=='NP':
                between=[p[:i] for i in range(len(x)+1,len(p))]
                if not require_intermediate or any(isinstance(tree[q],Tree) and tree[q].label() in {'NP','S'} for q in between):
                    results.append((0,p))
            for i,child in enumerate(node):
                q=p+(i,)
                if isinstance(child,Tree) and (q in path or not any(q>r and len(q)==len(r) for r in path)):
                    queue.append(q)
    x=next((p for p in ancestors if len(p)<len(np) and isinstance(tree[p],Tree) and tree[p].label() in {'NP','S'}),())
    path={leaf[:i] for i in range(len(x),len(leaf))}
    bfs_left(x,path,True)
    while True:
        if x==() or (tree[x].label()=='S' and not any(isinstance(tree[p],Tree) and tree[p].label()=='S' for p in ancestors if len(p)<len(x))):
            for distance,old in enumerate(previous,1):
                queue=deque([()])
                while queue:
                    p=queue.popleft();node=old[p]
                    if not isinstance(node,Tree):continue
                    if node.label()=='NP':results.append((distance,p))
                    queue.extend(p+(i,) for i,c in enumerate(node) if isinstance(c,Tree))
            break
        lower=x
        x=next((p for p in ancestors if len(p)<len(lower) and isinstance(tree[p],Tree) and tree[p].label() in {'NP','S'}),())
        path={leaf[:i] for i in range(len(x),len(leaf))}
        if tree[x].label()=='NP':
            below=x+(lower[len(x)],) if len(lower)>len(x) else lower
            if tree[below].label() not in {'NN','NNS','NNP','NNPS'}:results.append((0,x))
        bfs_left(x,path)
        if tree[x].label()=='S':
            # Right branches: do not descend below any encountered NP or S.
            child_on_path=leaf[len(x)]
            queue=deque(x+(i,) for i in range(child_on_path+1,len(tree[x])))
            while queue:
                p=queue.popleft();node=tree[p]
                if not isinstance(node,Tree):continue
                if node.label()=='NP':results.append((0,p));continue
                if node.label()=='S':continue
                queue.extend(p+(i,) for i,c in enumerate(node) if isinstance(c,Tree))
    return list(dict.fromkeys(results))


def discourse_entities(doc, mentions, previous_sentences=None, previous_hobbs=None, senses=None):
    previous_sentences=previous_sentences or []
    mention_by_start={m['span'][0]:m['entity_id'] for m in mentions}
    sentences=[];pronouns=[]
    cached=previous_hobbs or []
    tree_history=[Tree.fromstring(h['tree']) for h in cached if h.get('tree')]
    previous_maps=[{'mentions':h['mentions']} for h in cached]
    sense_map={s['span'][0]:s['selected'] for s in (senses or {}).get('senses',[])}
    kind_map={m['span'][0]:m['kind'] for m in mentions}
    try:
        parser=constituency_parser();backend='benepar_en3'
    except (ImportError,LookupError,OSError) as exc:
        parser=None;backend='spacy_dependency_candidate_fallback'
    for si,sentence in enumerate(doc.sents):
        tokens=list(sentence);cluster_map={}; mention_rows=[]
        for i,t in enumerate(tokens):
            if t.pos_=='PRON' and t.lower_ in {'i','me','my','mine','we','us','our','ours','you','your','yours'}:
                cluster_map[i]='speaker:self' if t.lower_ in {'i','me','my','mine'} else 'speaker:group' if t.lower_ in {'we','us','our','ours'} else 'addressee:you'
            if t.pos_ in {'NOUN','PROPN'}:
                cluster=mention_by_start.get(t.idx) or f"nominal:{t.lemma_.lower()}"
                cluster_map[i]=cluster
                animate=kind_map.get(t.idx)=='PERSON' or sense_map.get(t.idx,{}).get('animacy')=='person'
                gender='female' if t.lemma_.lower() in {'mother','sister','woman','girl','wife'} else 'male' if t.lemma_.lower() in {'father','brother','man','boy','husband'} else 'unknown'
                mention_rows.append({'token':i,'entity':cluster,'role':t.dep_,'number':list(t.morph.get('Number')),'kind':'PERSON' if animate else 'nominal','gender':gender})
        tree=None
        if parser:
            import benepar
            with _LOCK:
                tree=parser.parse(benepar.InputSentence(words=[t.text for t in tokens],space_after=[bool(t.whitespace_) for t in tokens]))
        for i,t in enumerate(tokens):
            if t.pos_!='PRON' or t.lower_ not in {'he','him','his','she','her','hers','it','its','they','them','their','theirs'}:
                continue
            candidates=[]
            if tree:
                proposals=proposal_positions(tree,i,list(reversed(tree_history)))
                for distance,p in proposals:
                    target_tree=tree if distance==0 else tree_history[-distance]
                    leaf_positions=[target_tree.leaf_treeposition(k) for k in range(len(target_tree.leaves()))]
                    indices=[k for k,q in enumerate(leaf_positions) if q[:len(p)]==p]
                    rows=mention_rows if distance==0 else previous_maps[-distance]['mentions']
                    for row in reversed(rows):
                        if row['token'] not in indices:continue
                        number='Plur' if t.lower_ in {'they','them','their','theirs'} else 'Sing'
                        pg='female' if t.lower_ in {'she','her','hers'} else 'male' if t.lower_ in {'he','him','his'} else 'unknown'
                        feasible=(not row['number'] or number in row['number']) and (pg=='unknown' or (row['kind']=='PERSON' and row.get('gender','unknown') in {'unknown',pg}))
                        if t.lower_ in {'it','its'} and row['kind']=='PERSON':feasible=False
                        if not any(c['entity']==row['entity'] for c in candidates):
                            candidates.append({'rank':len(candidates)+1,'entity':row['entity'],'sentence_distance':distance,'agreement':feasible,'gender':row.get('gender','unknown'),'tree_position':list(p)})
            else:
                # Resource-safe antecedent fallback.  This is deliberately not
                # labelled Hobbs: it ranks dependency mentions by sentence
                # distance, grammatical role, and recency, then applies the
                # same conservative agreement checks used above.
                role_order={'nsubj':0,'nsubjpass':0,'csubj':0,'dobj':1,'obj':1,'iobj':2,'pobj':3}
                pools=[(0,[row for row in mention_rows if row['token']<i])]
                pools.extend((distance,previous_maps[-distance]['mentions']) for distance in range(1,min(len(previous_maps),3)+1))
                for distance,rows in pools:
                    ranked=sorted(rows,key=lambda row:(role_order.get(row['role'],4),-row['token']))
                    for row in ranked:
                        number='Plur' if t.lower_ in {'they','them','their','theirs'} else 'Sing'
                        pg='female' if t.lower_ in {'she','her','hers'} else 'male' if t.lower_ in {'he','him','his'} else 'unknown'
                        feasible=(not row['number'] or number in row['number']) and (pg=='unknown' or (row['kind']=='PERSON' and row.get('gender','unknown') in {'unknown',pg}))
                        if t.lower_ in {'it','its'} and row['kind']=='PERSON':feasible=False
                        if not any(c['entity']==row['entity'] for c in candidates):
                            candidates.append({'rank':len(candidates)+1,'entity':row['entity'],'sentence_distance':distance,'agreement':feasible,'gender':row.get('gender','unknown'),'dependency_role':row['role']})
            winner=next((c for c in candidates if c['agreement']),None)
            entity=winner['entity'] if winner else None
            if entity:cluster_map[i]=entity
            pronouns.append({'span':[t.idx,t.idx+len(t)],'pronoun':t.text,'antecedent':entity,'candidates':candidates,'status':'resolved' if entity else 'unresolved'})
        role_order={'nsubj':0,'nsubjpass':0,'csubj':0,'dobj':1,'obj':1,'iobj':2,'pobj':3}
        cf=[]
        for i in sorted(cluster_map,key=lambda k:(role_order.get(tokens[k].dep_,4),k)):
            if cluster_map[i] not in cf:cf.append(cluster_map[i])
        prior=(sentences[-1] if sentences else previous_sentences[-1] if previous_sentences else None)
        cb=next((e for e in prior['cf'] if e in cf),None) if prior else None
        cp=cf[0] if cf else None
        if cb is None:transition='NO_CB'
        elif not prior or prior['cb'] is None:transition='INITIAL_CB'
        elif cb==prior['cb']:transition='CONTINUE' if cb==cp else 'RETAIN'
        else:transition='SMOOTH_SHIFT' if cb==cp else 'ROUGH_SHIFT'
        sentences.append({'sentence':si,'cf':cf,'cp':cp,'cb':cb,'transition':transition,'cost':{'CONTINUE':0,'RETAIN':1,'SMOOTH_SHIFT':2,'ROUGH_SHIFT':3,'NO_CB':3,'INITIAL_CB':None}[transition]})
        if tree:
            tree_history.append(tree)
        previous_maps.append({'mentions':mention_rows})
    if parser:
        history=[{'tree':str(t),'mentions':m['mentions']} for t,m in zip(tree_history,previous_maps)]
    else:
        history=[{'tree':None,'mentions':m['mentions']} for m in previous_maps]
    return {'hobbs':{'status':'ready','backend':backend,'algorithm':'hobbs_constituency' if parser else 'dependency_ranked_antecedent_fallback','pronouns':pronouns,'agreement_scope':'number, Lesk/person compatibility, explicit lexical gender; name gender unknown','limitation':None if parser else 'Benepar package unavailable; fallback is not the full Hobbs tree traversal.'},'centering':{'status':'ready','unit':'sentence','role_ranking':'subject > object > indirect object > other','trace':sentences}}, history[-50:]
