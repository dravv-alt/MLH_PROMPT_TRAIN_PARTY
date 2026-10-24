"""Deterministic retrieval and evidence graph over the user's explicit world memory."""
from app.services.nlp_engine import cosine


def retrieve_scenes(query_vector, world, limit=3, minimum_similarity=.25):
    if not query_vector:
        return []
    candidates=[]
    for scene in (world or {}).get('scenes',[]):
        score=cosine(query_vector,scene.get('vector',{}))
        if score>=minimum_similarity:
            candidates.append({'scene_id':scene['id'],'text':scene['text'],'similarity':score,'entity_ids':scene['entity_ids'],'thread_id':scene['thread_id'],'source_session_id':scene.get('session_id'),'source_turn_id':scene.get('turn_id')})
    # Equal scores prefer recent scenes; scene IDs are monotonic within retained memory.
    candidates.sort(key=lambda c:(-c['similarity'],-int(c['scene_id'][5:])))
    return candidates[:limit]


def memory_graph(world):
    world=world or {}
    nodes=[];edges=[]
    for entity in world.get('entities',[]):
        nodes.append({'id':entity['id'],'type':'entity','label':f"{entity['kind']} {entity['id']}"})
    for thread in world.get('threads',[]):
        nodes.append({'id':thread['id'],'type':'thread','label':thread['id'],'count':thread['count']})
    for scene in world.get('scenes',[]):
        nodes.append({'id':scene['id'],'type':'scene','label':scene['id'],'text':scene['text'],'source_session_id':scene.get('session_id'),'source_turn_id':scene.get('turn_id')})
        for entity in scene['entity_ids']:
            edges.append({'source':entity,'target':scene['id'],'type':'mentioned_in','evidence_scene_id':scene['id']})
        if scene['thread_id']:
            edges.append({'source':scene['id'],'target':scene['thread_id'],'type':'member_of','evidence_scene_id':scene['id']})
    for relationship in world.get('relationships',[]):
        left,right=relationship['entity_ids']
        edges.append({'source':left,'target':right,'type':'co_mentioned','evidence_scene_ids':relationship['scene_ids']})
    canonical=world.get('canonical_memory',{})
    assertions={row['assertion_id']:row for row in canonical.get('assertions',[])}
    evidence={row['evidence_id']:row for row in canonical.get('evidence',[])}
    for node in canonical.get('graph',{}).get('nodes',[]):
        item={**node,'type':'narrative_'+node.get('type','node')}
        if node['id'] in assertions:item['label']=assertions[node['id']]['content']['text']
        elif node['id'] in evidence:item['label']=evidence[node['id']]['text']
        else:item['label']=node['id']
        nodes.append(item)
    for edge in canonical.get('graph',{}).get('edges',[]):
        edges.append({**edge,'canonical':True})
    valid={node['id'] for node in nodes}
    edges=[edge for edge in edges if edge['source'] in valid and edge['target'] in valid]
    return {'schema_version':'pwm-and-narrative.graph.v2','memory_revision':canonical.get('revision',0),'nodes':sorted(nodes,key=lambda n:(n['type'],n['id'])),'edges':sorted(edges,key=lambda e:(e['source'],e['target'],e['type']))}
