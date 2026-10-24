"""Low-space NLP context experiments for Sanctuary.

This runner does not download resources and does not modify production state.
It executes algorithms that can be evaluated honestly on local conversation
text and records explicit gates for methods lacking data or resources.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
from nltk.stem import PorterStemmer
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer


BACKEND = Path(__file__).resolve().parents[1]
WORKSPACE = BACKEND.parents[1]
sys.path.insert(0, str(BACKEND))
from app.services.nlp_engine import pipeline  # noqa: E402


TOKEN_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


def regex_tokens(text: str) -> list[str]:
    return [item.casefold() for item in TOKEN_RE.findall(text)]


def fst_morphology(token: str) -> dict:
    """Small deterministic English inflection transducer, not a full lexicon."""
    value = token.casefold()
    transitions = (
        ("ies", "y", "plural_or_3sg"),
        ("ing", "", "progressive_or_gerund"),
        ("ed", "", "past_or_participle"),
        ("es", "", "plural_or_3sg"),
        ("s", "", "plural_or_3sg"),
    )
    for suffix, replacement, feature in transitions:
        if len(value) > len(suffix) + 2 and value.endswith(suffix):
            stem = value[:-len(suffix)] + replacement
            if suffix in {"ing", "ed"} and len(stem) > 2 and stem[-1:] == stem[-2:-1]:
                stem = stem[:-1]
            return {"surface": value, "stem": stem, "feature": feature, "accepted": True}
    return {"surface": value, "stem": value, "feature": "unmarked", "accepted": True}


class NGramModel:
    def __init__(self, order: int, smoothing: str):
        self.order = order
        self.smoothing = smoothing
        self.counts: Counter[tuple[str, ...]] = Counter()
        self.contexts: Counter[tuple[str, ...]] = Counter()
        self.vocab: set[str] = set()
        self.count_of_counts: Counter[int] = Counter()
        self._normalizers = {}

    def fit(self, documents: list[list[str]]) -> "NGramModel":
        for tokens in documents:
            sequence = ["<s>"] * (self.order - 1) + tokens + ["</s>"]
            self.vocab.update(tokens + ['</s>', '<unk>'])
            for index in range(self.order - 1, len(sequence)):
                gram = tuple(sequence[index-self.order+1:index+1])
                self.counts[gram] += 1
                self.contexts[gram[:-1]] += 1
        self.count_of_counts = Counter(self.counts.values())
        self._normalizers.clear()
        return self

    def probability(self, gram: tuple[str, ...]) -> float:
        gram = tuple(t if t in self.vocab or t == '<s>' else '<unk>' for t in gram)
        if self.smoothing == 'laplace':
            return (self.counts[gram] + 1) / (self.contexts[gram[:-1]] + max(1, len(self.vocab)))
        # The historical lab used unnormalised Good–Turing-style scores.
        # Normalize its approximate weights per history before reporting PPL.
        # This remains an approximation, not full Simple Good–Turing fitting.
        history = gram[:-1]
        if history not in self._normalizers:
            self._normalizers[history] = sum(self._weight(history + (word,)) for word in sorted(self.vocab))
        return self._weight(gram) / max(1e-300, self._normalizers[history])

    def _weight(self, gram: tuple[str, ...]) -> float:
        count = self.counts[gram]
        context_count = self.contexts[gram[:-1]]
        vocabulary = max(1, len(self.vocab))
        if count:
            nc = self.count_of_counts[count]
            next_nc = self.count_of_counts[count + 1]
            adjusted = (count + 1) * next_nc / nc if nc and next_nc else float(count)
            return max(1e-12, adjusted / max(1, context_count))
        unseen_mass = self.count_of_counts[1] / max(1, sum(self.counts.values()))
        return max(1e-12, unseen_mass / vocabulary)

    def perplexity(self, documents: list[list[str]]) -> float:
        losses, count = 0.0, 0
        for tokens in documents:
            sequence = ["<s>"] * (self.order - 1) + tokens + ["</s>"]
            for index in range(self.order - 1, len(sequence)):
                gram = tuple(sequence[index-self.order+1:index+1])
                losses -= math.log(self.probability(gram))
                count += 1
        return math.exp(losses / max(1, count))


def ppmi_matrix(documents: list[str]) -> np.ndarray:
    counts = CountVectorizer(token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z']+\b").fit_transform(documents).astype(float)
    cooccurrence = (counts @ counts.T).toarray()
    total = cooccurrence.sum()
    rows = cooccurrence.sum(axis=1, keepdims=True)
    cols = cooccurrence.sum(axis=0, keepdims=True)
    expected = rows @ cols / max(total, 1.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.log(np.divide(cooccurrence, expected, out=np.ones_like(cooccurrence), where=expected > 0))
    return np.maximum(pmi, 0.0)


def vsa_vectors(documents: list[str], dimension: int = 1024) -> np.ndarray:
    result = []
    for document in documents:
        vector = np.zeros(dimension, dtype=np.float64)
        for token in regex_tokens(document):
            seed = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "little")
            rng = np.random.default_rng(seed)
            vector += rng.choice([-1.0, 1.0], size=dimension)
        norm = np.linalg.norm(vector)
        result.append(vector / norm if norm else vector)
    return np.asarray(result)


def neighbours(matrix: np.ndarray, turn_ids: list[int]) -> list[dict]:
    similarities = cosine_similarity(matrix[-1:], matrix[:-1])[0]
    order = sorted(range(len(similarities)), key=lambda index: (-similarities[index], turn_ids[index]))[:3]
    return [{"turn_id": turn_ids[index], "score": round(float(similarities[index]), 6)} for index in order]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=WORKSPACE / "sanctuary_v2_evaluation_dataset.json")
    parser.add_argument("--topic", default="achievement_exhaustion_and_the_meaning_of_success")
    parser.add_argument("--output", type=Path, default=BACKEND / "evaluation" / "context_algorithm_lab.json")
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    topic = next(row for row in dataset["topics"] if row["topic_id"] == args.topic)
    documents = [row["user_prompt"] for row in topic["turns"]]
    turn_ids = [int(row["turn_id"]) for row in topic["turns"]]
    tokenized = [regex_tokens(document) for document in documents]

    nlp, _, _ = pipeline()
    porter = PorterStemmer()
    hf = AutoTokenizer.from_pretrained(BACKEND / "models" / "neural" / "embedding", local_files_only=True)
    sample = documents[0]
    regex_sample = regex_tokens(sample)
    spacy_sample = [token.text for token in nlp(sample)]
    hf_sample = hf.tokenize(sample)

    train, test = tokenized[:8], tokenized[8:]
    perplexities = {}
    for order in (1, 2, 3):
        for smoothing in ("laplace", "good_turing"):
            model = NGramModel(order, smoothing).fit(train)
            perplexities[f"{order}gram_{smoothing}"] = round(model.perplexity(test), 6)

    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=1).fit_transform(documents)
    components = min(5, tfidf.shape[0] - 1, tfidf.shape[1] - 1)
    lsa = TruncatedSVD(n_components=max(1, components), random_state=17).fit_transform(tfidf)
    ppmi = ppmi_matrix(documents)
    vsa = vsa_vectors(documents)

    report = {
        "schema_version": "sanctuary.context-algorithm-lab.v1",
        "topic": args.topic,
        "turns": len(documents),
        "production_changes": False,
        "tokenization_and_morphology": {
            "sample": sample,
            "regex": {"count": len(regex_sample), "tokens": regex_sample},
            "spacy": {"count": len(spacy_sample), "tokens": spacy_sample},
            "minilm_wordpiece": {"count": len(hf_sample), "tokens": hf_sample},
            "porter": [{"surface": token, "stem": porter.stem(token)} for token in regex_sample],
            "finite_state_suffix_transducer": [fst_morphology(token) for token in regex_sample],
            "decision": "Keep spaCy lemmas for linguistic features and MiniLM WordPiece only for its model. Porter/FST outputs are diagnostics; replacing lemmas would lose context.",
        },
        "language_models": {
            "train_turns": 8,
            "test_turns": 2,
            "perplexity": perplexities,
            "decision": "Useful as a fluency diagnostic only. Ten conversational turns are far too small for generation or prompt context.",
        },
        "retrieval_representations": {
            "tfidf_last_turn_neighbours": neighbours(tfidf.toarray(), turn_ids),
            "lsa_last_turn_neighbours": neighbours(lsa, turn_ids),
            "ppmi_last_turn_neighbours": neighbours(ppmi, turn_ids),
            "vsa_last_turn_neighbours": neighbours(vsa, turn_ids),
            "decision": "Compare against MiniLM with relevance labels; do not replace semantic retrieval from this demonstration.",
        },
        "gated_experiments": {
            "pcfg_cyk": "Implementation is possible, but no local constituency treebank or domain grammar exists; a toy grammar would not improve Sanctuary context.",
            "grammar_induction_dmv_em": "Blocked from production by missing sentence-level dependency corpus and held-out parsing evaluation.",
            "babelnet": "Unavailable offline: no checked-in BabelNet index or licensed API credentials. No network fallback attempted.",
            "word2vec_glove_fasttext": "No versioned local pretrained artifacts. Training on ten turns would be statistically meaningless.",
            "nce_infonce": "Requires defined positive/negative conversation pairs and a train/test split; no clean pairs currently exist.",
            "hyperbolic_embeddings": "Requires a validated hierarchy objective; topic IDs alone do not establish a hierarchy.",
            "discocat": "Requires a categorial grammar and tensor semantics corpus absent from the repository.",
            "rnn_lstm_gru_cnn_s4_mamba_perceiver": "No architecture experiment is authorized as production context without a shared task, equivalent parameter budget, training data, and held-out metric.",
            "lora": "Deferred until deterministic fidelity failures are fixed and clean response pairs exist.",
        },
        "boundary": "Executed outputs are descriptive on one conversation. They are not evidence of production superiority.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "perplexity": perplexities, "retrieval": report["retrieval_representations"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
