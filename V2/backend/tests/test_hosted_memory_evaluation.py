"""Provider boundary checks using real analysis and memory, mocked transport."""
from argparse import Namespace
from scripts import evaluate_hosted_memory_harness as harness
import pytest


@pytest.fixture(autouse=True)
def omit_unrelated_neural_parsers(monkeypatch):
    # These parsers do not feed the provider boundary being tested. Their own
    # tests cover them; avoid loading two large models for an integration check.
    monkeypatch.setattr('app.services.dmrst.parse_dmrst', lambda text: {'status': 'unavailable', 'edus': [], 'tree': []})
    monkeypatch.setattr('app.services.classical_nlp.discourse_entities', lambda *a: ({'centering': {'trace': []}, 'hobbs': {'pronouns': []}}, []))


def test_history_and_identity_roundtrip(monkeypatch):
    sent = []
    def transport(prompt, **kwargs):
        sent.append(prompt)
        return 'You mentioned [entity_e000001].', []
    monkeypatch.setattr(harness, 'call_rate_limited', transport)
    monkeypatch.setattr(harness, 'evaluate_candidates', lambda *a: [])
    args = Namespace(min_interval_seconds=0, max_attempts=1)
    mapping = {}
    first, state = harness.inference_turn('I met Priya Sharma and felt tired after work.', {}, mapping, [0], args)
    second, _ = harness.inference_turn('I still feel tired after work, but I enjoyed meeting Priya Sharma.', state, mapping, [0], args)
    assert mapping, 'The real redactor must identify the synthetic person'
    assert all('Priya' not in prompt and 'Sharma' not in prompt for prompt in sent)
    assert second['memory']['historical_excerpt_count_sent'] > 0
    assert 'Relevant earlier context' in sent[1]
    assert 'Priya Sharma' in second['display_response_restored']
    assert 'display_response_restored' not in harness.sanitize_record(second)
    assert second['privacy']['unresolved_placeholders'] == []


def test_failure_never_substitutes_fallback(monkeypatch):
    monkeypatch.setattr(harness, 'call_rate_limited', lambda *a, **k: (None, []))
    args = Namespace(min_interval_seconds=0, max_attempts=1)
    result, _ = harness.inference_turn('I feel tired after a long week at work.', {}, {}, [0], args)
    assert result['status'] == 'provider_unavailable_after_retries'
    assert result['provider_response_redacted'] is None


def test_provider_retry_and_spacing(monkeypatch):
    responses = iter([None, None, 'You feel tired.'])
    calls = []
    waits = []
    monkeypatch.setattr(harness.groq_reflector, 'generate', lambda prompt: (calls.append(prompt), next(responses))[1])
    monkeypatch.setattr(harness.time, 'sleep', waits.append)
    monkeypatch.setattr(harness.time, 'monotonic', lambda: 10.0)
    text, attempts = harness.call_rate_limited('redacted', last_call=[9.0], interval=1.5, max_attempts=5)
    assert text == 'You feel tired.'
    assert len(calls) == len(attempts) == 3
    assert waits == [0.5, 1.0, 1.5, 2.0, 1.5]


def test_prompt_bounds_and_no_gold():
    history = [{'text': 'a' * 500} for _ in range(5)]
    prompt = harness.provider_prompt('You feel tired.', ['You feel tired.'], history)
    assert prompt.count('a' * 300) == 3
    assert 'a' * 301 not in prompt
    assert 'expected_state' not in prompt
