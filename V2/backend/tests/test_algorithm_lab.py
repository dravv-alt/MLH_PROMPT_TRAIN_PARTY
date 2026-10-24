import copy
import math

import pytest

from app.services.algorithm_lab import compare_algorithms
from scripts.context_algorithm_lab import NGramModel


@pytest.mark.parametrize('order', [1, 2, 3])
@pytest.mark.parametrize('smoothing', ['laplace', 'good_turing'])
def test_ngram_probabilities_normalize_and_handle_unseen_words(order, smoothing):
    model = NGramModel(order, smoothing).fit([['rain', 'falls'], ['rain', 'stops']])
    for history in [tuple(['<s>'] * (order - 1)), tuple(['missing'] * (order - 1))]:
        assert sum(model.probability(history + (word,)) for word in model.vocab) == pytest.approx(1)
    value = model.perplexity([['unseen', 'words']])
    assert math.isfinite(value) and value >= 1


def test_lab_without_prior_context_is_explicitly_unavailable(monkeypatch):
    monkeypatch.setattr('app.services.algorithm_lab.local_tokenizer', lambda: (_ for _ in ()).throw(OSError()))
    result = compare_algorithms('I walked past the building.')
    assert not result['persisted'] and not result['affects_generation']
    assert result['language_models']['reason'] == 'requires_prior_session_turns'
    assert result['tokenization']['minilm_wordpiece']['status'] == 'unavailable'
    assert result['tokenization']['porter']['status'] == 'ready'


def test_lab_reuses_algorithms_without_mutating_input(monkeypatch):
    class Tokenizer:
        def tokenize(self, text): return text.split()
    monkeypatch.setattr('app.services.algorithm_lab.local_tokenizer', lambda: Tokenizer())
    previous = ['I walked in cold air.', 'I answered emails after work.']
    original = copy.deepcopy(previous)
    result = compare_algorithms('The cold air felt quiet.', previous)
    assert previous == original
    assert len(result['language_models']['perplexity']) == 6
    assert all(v >= 1 and math.isfinite(v) for v in result['language_models']['perplexity'].values())
    assert set(result['retrieval']) == {'tfidf', 'lsa_svd', 'ppmi', 'vsa'}
    for value in result['retrieval'].values():
        assert value['status'] == 'ready'
        assert all(1 <= row['turn_id'] <= 2 for row in value['neighbours'])


def test_lab_caps_previous_context():
    result = compare_algorithms('I walked home.', ['I walked outside.'] * 30)
    assert result['document_count'] == 20
