"""Bounded, read-only adapters for existing context experiments.

Inputs must already be canonical redacted text. No generator, training on gold
data, persistent writes, network calls or resource downloads are performed.
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
from nltk.stem import PorterStemmer
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from scripts.context_algorithm_lab import (
    NGramModel, fst_morphology, neighbours, ppmi_matrix, regex_tokens, vsa_vectors,
)


@lru_cache(maxsize=1)
def local_tokenizer():
    from transformers import AutoTokenizer
    path = Path(__file__).resolve().parents[2] / 'models/neural/embedding'
    return AutoTokenizer.from_pretrained(str(path), local_files_only=True)


def compare_algorithms(text, previous=()):
    from app.services.nlp_engine import parse
    documents = list(previous)[-19:] + [text]
    tokens = regex_tokens(text)
    porter = PorterStemmer()
    doc, backend, fallback = parse(text)
    result = {
        'schema_version': 'algorithm-lab.v1', 'status': 'preview',
        'redacted_text': text, 'document_count': len(documents),
        'persisted': False, 'affects_generation': False,
        'boundary': 'Descriptive local experiments, not evidence of relevance or language quality. At most 19 earlier turns from the selected session.',
        'tokenization': {
            'regex': {'status': 'ready', 'tokens': tokens},
            'spacy': {'status': 'ready', 'backend': backend, 'fallback': fallback,
                      'tokens': [{'text': t.text, 'lemma': t.lemma_, 'pos': t.pos_, 'dependency': t.dep_,
                                  'span': [t.idx, t.idx + len(t)]} for t in doc]},
            'porter': {'status': 'ready', 'tokens': [{'text': t, 'stem': porter.stem(t)} for t in tokens]},
            'suffix_fst': {'status': 'ready', 'scope': 'restricted suffix rules, not a full English morphological analyzer',
                           'tokens': [fst_morphology(t) for t in tokens]},
        },
        'retrieval': {},
    }
    try:
        result['tokenization']['minilm_wordpiece'] = {'status': 'ready', 'tokens': local_tokenizer().tokenize(text)}
    except (OSError, ImportError, ValueError):
        result['tokenization']['minilm_wordpiece'] = {'status': 'unavailable', 'reason': 'local_tokenizer_unavailable'}
    if len(documents) < 2 or not any(regex_tokens(item) for item in documents[:-1]):
        result['language_models'] = {'status': 'unavailable', 'reason': 'requires_prior_session_turns'}
        result['retrieval'] = {'status': 'unavailable', 'reason': 'requires_prior_session_turns'}
        return result
    train = [regex_tokens(item) for item in documents[:-1]]
    result['language_models'] = {
        'status': 'ready', 'train_turns': len(train), 'test_turns': 1,
        'notice': 'Earlier turns train counts; current turn is held out. Tiny-corpus perplexity is not reflective quality. Good–Turing is an explicitly approximate normalized variant.',
        'perplexity': {f'{n}gram_{smoothing}': round(NGramModel(n, smoothing).fit(train).perplexity([tokens]), 6)
                       for n in (1, 2, 3) for smoothing in ('laplace', 'good_turing')},
    }
    try:
        # Fit representations on earlier documents only, never on evaluator fields.
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=4096)
        prior = vectorizer.fit_transform(documents[:-1])
        query = vectorizer.transform([text])
        from scipy.sparse import vstack
        matrix = vstack([prior, query])
        ids = list(range(1, len(documents) + 1))
        result['retrieval']['tfidf'] = {'status': 'ready', 'neighbours': neighbours(matrix.toarray(), ids)}
        components = min(5, prior.shape[0], prior.shape[1] - 1)
        if components >= 1 and prior.shape[1] >= 2 and len(set(documents[:-1])) >= 2:
            svd = TruncatedSVD(n_components=components, random_state=17)
            vectors = svd.fit_transform(prior)
            result['retrieval']['lsa_svd'] = {'status': 'ready', 'dimensions': components,
                'neighbours': neighbours(np.vstack([vectors, svd.transform(query)]), ids)}
        else:
            result['retrieval']['lsa_svd'] = {'status': 'unavailable', 'reason': 'insufficient_document_variation_or_vocabulary'}
        result['retrieval']['ppmi'] = {'status': 'ready', 'scope': 'document co-occurrence diagnostic, not pretrained word embeddings',
                                      'neighbours': neighbours(ppmi_matrix(documents), ids)}
        result['retrieval']['vsa'] = {'status': 'ready', 'scope': 'deterministic token superposition, no relational binding',
                                     'neighbours': neighbours(vsa_vectors(documents), ids)}
    except ValueError:
        result['retrieval'] = {'status': 'unavailable', 'reason': 'insufficient_vocabulary'}
    return result
