from app.services.memory_tools import retrieve_scenes,memory_graph


def test_retrieval_and_evidence_graph():
    world={'entities':[{'id':'e000001','kind':'PERSON'}],'threads':[{'id':'thread000001','count':2}], 'relationships':[], 'scenes':[{'id':'scene000001','entity_ids':['e000001'],'thread_id':'thread000001','text':'office project report','vector':{'1':1.},'session_id':'old','turn_id':1},{'id':'scene000002','entity_ids':['e000001'],'thread_id':'thread000001','text':'office meeting report','vector':{'1':1.},'session_id':'old','turn_id':2}]}
    results=retrieve_scenes({'1':1.},world)
    assert [r['scene_id'] for r in results]==['scene000002','scene000001']
    assert results[0]['source_turn_id']==2
    assert retrieve_scenes({},world)==[]
    graph=memory_graph(world)
    nodes={n['id'] for n in graph['nodes']}
    assert all(e['source'] in nodes and e['target'] in nodes for e in graph['edges'])
    assert all(e['evidence_scene_id'] in {'scene000001','scene000002'} for e in graph['edges'])
