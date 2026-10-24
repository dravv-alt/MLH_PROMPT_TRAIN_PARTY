"""SSM wiring and privacy regressions; not psychological accuracy tests."""
import json

from app.models.schemas import NarrativeStructure
from app.services.narrative_engine import NarrativeEngine
from app.services.local_generation import build_generation_messages
from app.services.response_planner import build_response_plan


def test_unknown_is_not_an_invented_reaction_or_choice():
    s = NarrativeEngine().distill_turn('The document has three pages.')
    assert s.event.action_taken is None
    assert s.event.action_desired is None
    assert s.reaction.primary_reaction == 'unknown'
    assert s.reaction.after_effects == []
    assert s.reaction.intensity is None
    assert s.meaning.self_interpretation == 'unknown'
    assert all(v is None for v in s.constraints.model_dump().values())


def test_explicit_ratings_include_zero_and_reject_out_of_range():
    s = NarrativeEngine().distill_turn('freedom_to_refuse: 0; expectation pressure: 0.9; emotional_safety: 1.2')
    assert s.constraints.freedom_to_refuse == 0
    assert s.constraints.expectation_pressure == .9
    assert s.constraints.emotional_safety is None


def test_phrases_never_serialize_even_when_nested():
    s = NarrativeEngine().distill_turn('I let myself down. I felt angry.')
    assert s.language.key_phrases_mirrored
    assert 'key_phrases_mirrored' not in s.model_dump()['language']
    assert 'key_phrases_mirrored' not in s.model_dump_json()
    assert NarrativeStructure.model_validate(s.model_dump()).language.key_phrases_mirrored == []


def test_unknown_patterns_do_not_create_recurrence():
    engine = NarrativeEngine()
    first = engine.distill_turn('The document has three pages.')
    second = engine.distill_turn('The screen has four buttons.', [first])
    assert not second.temporal.is_recurring
    assert second.temporal.progression == 'unknown'


def test_negative_reaction_and_distinct_same_event():
    engine = NarrativeEngine()
    assert engine.distill_turn('I am not sad.').reaction.primary_reaction == 'unknown'
    assert engine.distill_turn('I argued with my partner. I feel relieved.').reaction.primary_reaction == 'relief'
    assert engine.distill_turn('I argued with my partner. I feel scared.').reaction.primary_reaction == 'fear'


def test_structure_reaches_generator_without_phrases():
    text = 'I said yes but wanted to say no. I feel guilty.'
    s = NarrativeEngine().distill_turn(text)
    plan = build_response_plan({'redacted_text': text, 'situational_structure': s.model_dump()})
    payload = json.loads(build_generation_messages(plan)[-1]['content'].split('\n', 1)[1])
    assert set(payload['situational_structure']) == {'event', 'constraints', 'reaction', 'meaning', 'temporal', 'language'}
    assert 'key_phrases_mirrored' not in json.dumps(payload)
    assert payload['situational_structure']['event']['action_desired'] == 'refusal'


def test_reaction_mentions_are_ordered_not_invented_as_causal():
    s = NarrativeEngine().distill_turn('I was scared, then angry.')
    assert s.reaction.primary_reaction == 'fear'
    assert s.reaction.secondary_reaction == 'anger'


def test_session_pattern_history_can_be_forgotten():
    engine = NarrativeEngine()
    text = 'Under pressure I said yes. I feel guilty.'
    first = engine.distill_turn(text)
    assert not first.temporal.is_recurring
    assert engine.distill_turn(text, [first]).temporal.is_recurring
    assert not engine.distill_turn(text, []).temporal.is_recurring


def test_constraints_have_grounded_spans_and_conflict_abstention():
    from app.services.ssm_constraints import constraint_observations
    text = 'I felt pressured. I had no choice.'
    values, evidence = constraint_observations(text)
    assert values['freedom_to_refuse'] == .1
    assert values['expectation_pressure'] == .9
    for item in evidence.values():
        for start, end in item['spans']:
            assert 0 <= start < end <= len(text)
    assert constraint_observations('I felt pressured. I felt no pressure.')[0]['expectation_pressure'] is None
    assert constraint_observations('Imagine I felt pressured.')[0]['expectation_pressure'] is None
    assert constraint_observations('My manager spoke.')[0]['power_asymmetry'] is None
