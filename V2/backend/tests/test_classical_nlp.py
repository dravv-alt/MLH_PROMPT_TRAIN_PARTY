from nltk.tree import Tree
from app.services.classical_nlp import proposal_positions,lesk,discourse_entities
from app.services.nlp_engine import analyze_turn,parse
from app.services.dmrst import parse_dmrst


def test_lesk_actual_wordnet():
    doc,_,_=parse('The bank accepted a deposit of money.')
    output=lesk(doc)
    assert output['status']=='ready'
    bank=next(s for s in output['senses'] if s['lemma']=='bank')
    assert bank['candidates']
    assert bank['selected']['score']==max(c['score'] for c in bank['candidates'])


def test_hobbs_previous_sentence_bfs():
    prior=Tree.fromstring('(S (NP (NNP Alice)) (VP (VBD greeted) (NP (NNP Bob))) (. .))')
    current=Tree.fromstring('(S (NP (PRP She)) (VP (VBD smiled)) (. .))')
    proposals=proposal_positions(current,0,[prior])
    assert proposals[:2]==[(1,(0,)),(1,(1,1))]


def test_pronouns_without_nominal_evidence_are_not_fabricated():
    doc, _, _ = parse('He spoke to her. She thanked him.')
    result, _ = discourse_entities(doc, [])
    rows = result['hobbs']['pronouns']
    assert len(rows) == 4
    assert all(row['status'] == 'unresolved' and row['antecedent'] is None for row in rows)
    assert all(not row['candidates'] for row in rows)


def test_gendered_pronouns_never_select_explicitly_incompatible_person():
    doc, _, _ = parse('The father greeted the mother. She smiled. He waved.')
    result, _ = discourse_entities(doc, [], senses=lesk(doc))
    for row in result['hobbs']['pronouns']:
        if row['antecedent']:
            winner = next(c for c in row['candidates'] if c['entity'] == row['antecedent'])
            assert winner['agreement']
            assert winner['gender'] != ('male' if row['pronoun'].lower() == 'she' else 'female')


def test_speaker_centering():
    doc,_,_=parse('I spoke. I waited. I left.')
    result,_=discourse_entities(doc,[])
    trace=result['centering']['trace']
    assert trace[0]['cp']=='speaker:self'
    assert trace[1]['cb']=='speaker:self'
    assert trace[2]['transition']=='CONTINUE'


def test_pwm_and_centering_trace():
    cfg={'alias_key':'test'}
    a,state,_=analyze_turn('Priya Sharma greeted the manager. She called the manager.',{},cfg)
    assert a['lesk']['status']=='ready'
    assert a['hobbs']['status']=='ready'
    assert any(p['antecedent'] for p in a['hobbs']['pronouns'])
    assert a['centering']['trace'][0]['transition']=='NO_CB'
    assert a['pwm']['scenes']
    assert state['world']['entities']
    b,updated,_=analyze_turn('Priya spoke to the manager again.',state,cfg)
    assert len(updated['world']['scenes'])==2
    assert b['pwm']['entities'][0]['id']==a['pwm']['entities'][0]['id']


def test_dmrst_missing_resources_explicit(monkeypatch,tmp_path):
    monkeypatch.setenv('DMRST_MODEL_PATH',str(tmp_path/'missing'))
    result=parse_dmrst('This is a short text.')
    assert result['status']=='unavailable'
    assert result['tree']==[]


def test_dmrst_actual_cpu_inference():
    text='Although the meeting was difficult, I explained the project because the team needed the report.'
    result=parse_dmrst(text)
    assert result['status']=='ready', result
    assert len(result['edus'])>=2
    assert result['tree']
    assert all(text[e['span'][0]:e['span'][1]]==e['text'] for e in result['edus'])
    assert len(result['checkpoint_sha256'])==64
