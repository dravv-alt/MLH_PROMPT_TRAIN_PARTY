import re
from dataclasses import dataclass
from statistics import mean

from app.models.schemas import NarrativeStructure
from app.services.language_field import derive_language_field


STAGE_ORDER = ("event", "reaction", "mismatch", "pattern", "buildup", "system")

ENERGY_RANK = {"low": 0, "medium": 1, "high": 2}
ABSTRACTION_RANK = {"concrete": 0, "mixed": 1, "abstract": 2}
INTENSITY_RANK = {"low": 0, "medium": 1, "high": 2}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "him",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "she",
    "that",
    "the",
    "their",
    "them",
    "there",
    "they",
    "this",
    "to",
    "was",
    "we",
    "were",
    "with",
    "you",
    "your",
}

COMMON_WORDS = {
    "about",
    "again",
    "all",
    "also",
    "always",
    "any",
    "back",
    "because",
    "been",
    "before",
    "between",
    "both",
    "can",
    "clear",
    "cost",
    "could",
    "day",
    "down",
    "each",
    "even",
    "feel",
    "feels",
    "feeling",
    "felt",
    "first",
    "focus",
    "forward",
    "going",
    "good",
    "hard",
    "having",
    "here",
    "into",
    "just",
    "keep",
    "keeps",
    "kind",
    "know",
    "last",
    "life",
    "line",
    "little",
    "long",
    "lot",
    "made",
    "make",
    "makes",
    "many",
    "moment",
    "more",
    "most",
    "much",
    "need",
    "next",
    "now",
    "one",
    "only",
    "other",
    "over",
    "part",
    "pattern",
    "real",
    "really",
    "right",
    "same",
    "sense",
    "shared",
    "shift",
    "small",
    "some",
    "still",
    "take",
    "than",
    "then",
    "thing",
    "think",
    "time",
    "times",
    "today",
    "under",
    "understand",
    "very",
    "want",
    "way",
    "weight",
    "what",
    "when",
    "where",
    "while",
    "work",
}

CONTINUITY_CUES = (
    "still",
    "again",
    "this time",
    "that pattern",
    "keeps",
    "keeps repeating",
    "from that",
)

SHIFT_MARKERS = (
    "now",
    "shift",
    "moves from",
    "which means",
    "so the",
    "the focus",
    "thread",
)

PROGRESSION_CUES = (
    "which shows",
    "which points to",
    "which reveals",
    "naming",
    "clarity",
    "next step",
    "signals",
    "suggests",
)

FORMALIZATION_TOKENS = (
    "therefore",
    "characterized",
    "dynamic",
    "framework",
    "narrative",
    "systemic",
    "analytical",
    "evaluate",
)

GENERIC_RESPONSE_RE = re.compile(
    r"\b(?:that sounds hard|your feelings are valid|you are not alone|that makes sense|"
    r"thank you for sharing|i hear you)\b",
    flags=re.IGNORECASE,
)

PARAPHRASE_LEAD_RE = re.compile(r"^(?:you(?:'re| are| feel| felt| were| keep| kept)|your\b)", flags=re.IGNORECASE)


@dataclass(frozen=True)
class GenerationScoreResult:
    narrative_progression_score: float
    language_alignment_score: float
    coherence_continuity_score: float
    final_score: float
    passed: bool
    violations: list[str]
    narrative_breakdown: dict[str, float]
    language_breakdown: dict[str, float]
    coherence_breakdown: dict[str, float]


def evaluate_generation_filter(
    previous: list[NarrativeStructure],
    current: NarrativeStructure,
    user_text: str,
    response_text: str,
) -> GenerationScoreResult:
    current_stage = _infer_stage_from_structure(current)
    response_stage = _infer_stage_from_text(response_text)

    anchor_match = _score_anchor_match(previous, response_text)
    single_insight = _score_single_insight(current_stage, response_stage, response_text)
    forward_shift = _score_forward_shift(previous, current_stage, response_stage, response_text)
    narrative_progression = _mean_score(anchor_match, single_insight, forward_shift)

    response_language = derive_language_field(response_text)
    source_language = current.language.language_field

    energy_match = 1.0 if abs(ENERGY_RANK[response_language.energy_level] - ENERGY_RANK[source_language.energy_level]) <= 1 else 0.0
    abstraction_match = (
        1.0
        if ABSTRACTION_RANK[response_language.abstraction_level] - ABSTRACTION_RANK[source_language.abstraction_level] <= 1
        else 0.0
    )
    rhythm_match = _score_rhythm_match(user_text, response_text)
    vocabulary_match = _score_vocabulary_match(user_text, response_text)
    emotional_match = (
        1.0
        if abs(INTENSITY_RANK[response_language.emotional_intensity] - INTENSITY_RANK[source_language.emotional_intensity]) <= 1
        else 0.0
    )
    language_alignment = _mean_score(energy_match, abstraction_match, rhythm_match, vocabulary_match, emotional_match)

    context_reference = _score_context_reference(previous, current, response_text)
    non_repeat = _score_non_repeat(user_text, response_text)
    irreplaceability = _score_irreplaceability(previous, current, response_text, context_reference)
    coherence_continuity = _mean_score(context_reference, non_repeat, irreplaceability)

    final_score = round(narrative_progression + language_alignment + coherence_continuity, 2)

    violations: list[str] = []
    if narrative_progression < 0.60:
        violations.append("score_narrative_progression_below_0_6")
    if language_alignment < 0.60:
        violations.append("score_language_alignment_below_0_6")
    if coherence_continuity < 0.60:
        violations.append("score_coherence_continuity_below_0_6")
    if final_score < 2.20:
        violations.append("score_final_below_2_2")

    return GenerationScoreResult(
        narrative_progression_score=narrative_progression,
        language_alignment_score=language_alignment,
        coherence_continuity_score=coherence_continuity,
        final_score=final_score,
        passed=not violations,
        violations=violations,
        narrative_breakdown={
            "anchor_match": anchor_match,
            "single_insight": single_insight,
            "forward_shift": forward_shift,
        },
        language_breakdown={
            "energy_match": energy_match,
            "abstraction_match": abstraction_match,
            "rhythm_match": rhythm_match,
            "vocabulary_match": vocabulary_match,
            "emotional_match": emotional_match,
        },
        coherence_breakdown={
            "context_reference": context_reference,
            "non_repeat": non_repeat,
            "irreplaceability": irreplaceability,
        },
    )


def _normalize(text: str) -> str:
    return " ".join(text.lower().split()).strip()


def _tokenize_words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text)


def _significant_tokens(text: str) -> list[str]:
    return [word for word in _tokenize_words(_normalize(text)) if len(word) > 2 and word not in STOPWORDS]


def _sentence_lengths(text: str) -> list[int]:
    parts = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    if not parts:
        return []
    return [len(_tokenize_words(part)) for part in parts]


def _avg_sentence_length(text: str) -> float:
    lengths = _sentence_lengths(text)
    if lengths:
        return mean(lengths)
    return float(len(_tokenize_words(text)))


def _count_sentences(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])


def _contains_token(text: str, token: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(token)}(?!\w)", text) is not None


def _infer_stage_from_structure(structure: NarrativeStructure) -> int:
    if structure.temporal.resolution_state == "integrated":
        return 5
    if structure.temporal.resolution_state == "partial_resolution":
        return 4
    if structure.temporal.is_recurring or structure.temporal.resolution_state == "emerging_clarity":
        return 3
    if structure.meaning.fairness_evaluation != "unclear" or structure.meaning.identity_threat not in {"none", "unknown"}:
        return 2
    if structure.reaction.primary_reaction not in {"rumination", "unknown"} or (structure.reaction.intensity or 0) >= 0.45:
        return 1
    return 0


def _infer_stage_from_text(text: str) -> int:
    normalized = _normalize(text)

    stage_tokens = {
        5: ("system", "nervous system", "protective", "survival"),
        4: ("building", "buildup", "stacking", "accumulating", "clearer", "thread", "emerge"),
        3: ("pattern", "cycle", "repeating", "again and again", "keeps repeating"),
        2: ("torn", "split", "conflict between", "cost", "mismatch", "part of you"),
        1: ("feel", "felt", "holding", "anxious", "angry", "hurt", "tense"),
        0: ("happened", "moment", "what happened", "conversation"),
    }

    for stage in range(5, -1, -1):
        if any(_contains_token(normalized, token) for token in stage_tokens[stage]):
            return stage

    return 1


def _extract_anchor_tokens(structure: NarrativeStructure) -> set[str]:
    tokens: set[str] = set()

    for item in (
        structure.event.event_type,
        structure.event.action_taken,
        structure.event.action_desired,
        structure.reaction.primary_reaction,
        structure.meaning.fairness_evaluation,
        structure.meaning.identity_threat,
        structure.temporal.progression,
        structure.temporal.resolution_state,
    ):
        tokens.update(part for part in item.split("_") if part and part not in STOPWORDS)

    if structure.reaction.secondary_reaction:
        tokens.update(part for part in structure.reaction.secondary_reaction.split("_") if part and part not in STOPWORDS)

    for effect in structure.reaction.after_effects:
        tokens.update(part for part in effect.split("_") if part and part not in STOPWORDS)

    tokens.update(word for word in _tokenize_words(structure.temporal.pattern_signature.lower()) if len(word) > 2 and word not in STOPWORDS)
    return tokens


def _score_anchor_match(previous: list[NarrativeStructure], response_text: str) -> float:
    if not previous:
        return 1.0

    last = previous[-1]
    if last.temporal.resolution_state == "integrated" and not last.temporal.is_recurring:
        return 1.0

    response_tokens = set(_significant_tokens(response_text))
    if _extract_anchor_tokens(last).intersection(response_tokens):
        return 1.0

    normalized = _normalize(response_text)
    if any(cue in normalized for cue in CONTINUITY_CUES):
        return 1.0

    return 0.0


def _score_single_insight(current_stage: int, response_stage: int, response_text: str) -> float:
    sentence_count = _count_sentences(response_text)
    if sentence_count < 1 or sentence_count > 2:
        return 0.0

    delta = response_stage - current_stage
    normalized = _normalize(response_text)
    shift_marker_hits = sum(1 for marker in SHIFT_MARKERS if marker in normalized)
    progression_signal = _has_progression_signal(normalized)

    if shift_marker_hits > 2:
        return 0.0

    if delta == 1 and progression_signal:
        return 1.0

    if delta == 0 and shift_marker_hits == 1 and progression_signal:
        return 1.0

    return 0.0


def _score_forward_shift(previous: list[NarrativeStructure], current_stage: int, response_stage: int, response_text: str) -> float:
    if previous:
        previous_stage = _infer_stage_from_structure(previous[-1])
        base_stage = max(current_stage, previous_stage)
    else:
        base_stage = current_stage

    terminal_stage = len(STAGE_ORDER) - 1
    expected_stage = min(base_stage + 1, terminal_stage)

    if base_stage == terminal_stage and response_stage == terminal_stage:
        return 1.0

    if response_stage == expected_stage:
        return 1.0

    if response_stage == base_stage:
        normalized = _normalize(response_text)
        if _has_progression_signal(normalized):
            return 1.0

    return 0.0


def _score_rhythm_match(user_text: str, response_text: str) -> float:
    user_avg = _avg_sentence_length(user_text)
    response_avg = _avg_sentence_length(response_text)

    if user_avg <= 10:
        threshold = 2.0
    elif user_avg <= 16:
        threshold = 4.0
    else:
        threshold = 6.0

    return 1.0 if abs(response_avg - user_avg) <= threshold else 0.0


def _uncommon_word_ratio(text: str) -> float:
    words = [word.lower() for word in _tokenize_words(text)]
    if not words:
        return 0.0

    uncommon_count = 0
    for word in words:
        if len(word) < 5:
            continue
        if word in COMMON_WORDS:
            continue
        uncommon_count += 1

    return uncommon_count / max(1, len(words))


def _score_vocabulary_match(user_text: str, response_text: str) -> float:
    user_uncommon_ratio = _uncommon_word_ratio(user_text)
    response_uncommon_ratio = _uncommon_word_ratio(response_text)
    allowed_ratio = min(0.35, user_uncommon_ratio + 0.08)

    normalized = _normalize(response_text)
    formal_hits = sum(1 for token in FORMALIZATION_TOKENS if _contains_token(normalized, token))

    if response_uncommon_ratio > allowed_ratio:
        return 0.0

    if formal_hits > 2:
        return 0.0

    return 1.0


def _score_context_reference(previous: list[NarrativeStructure], current: NarrativeStructure, response_text: str) -> float:
    normalized = _normalize(response_text)
    response_tokens = set(_significant_tokens(response_text))

    if previous:
        if _extract_anchor_tokens(previous[-1]).intersection(response_tokens):
            return 1.0

    if _extract_anchor_tokens(current).intersection(response_tokens):
        return 1.0

    if any(cue in normalized for cue in CONTINUITY_CUES):
        return 1.0

    return 0.0 if previous else 1.0


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = len(left.intersection(right))
    union = len(left.union(right))
    return intersection / max(1, union)


def _has_long_ngram_overlap(user_text: str, response_text: str, n: int = 8) -> bool:
    user_words = _tokenize_words(_normalize(user_text))
    response_words = _tokenize_words(_normalize(response_text))

    if len(user_words) < n or len(response_words) < n:
        return False

    user_ngrams = {" ".join(user_words[index : index + n]) for index in range(0, len(user_words) - n + 1)}
    response_blob = " ".join(response_words)
    return any(ngram in response_blob for ngram in user_ngrams)


def _score_non_repeat(user_text: str, response_text: str) -> float:
    user_tokens = set(_significant_tokens(user_text))
    response_tokens = set(_significant_tokens(response_text))

    similarity = _jaccard_similarity(user_tokens, response_tokens)

    if _is_paraphrase_heavy(user_text, response_text, similarity):
        return 0.0

    if similarity >= 0.75:
        return 0.0

    if _has_long_ngram_overlap(user_text, response_text):
        return 0.0

    return 1.0


def _current_state_markers(current: NarrativeStructure) -> set[str]:
    markers: set[str] = set()

    if current.temporal.is_recurring:
        markers.update({"pattern", "cycle", "repeat", "again", "keeps"})

    if current.temporal.resolution_state in {"emerging_clarity", "partial_resolution", "integrated"}:
        markers.update({"clear", "clarity", "thread", "boundary", "shift"})

    if current.meaning.fairness_evaluation in {"self_blame", "external_blame", "shared"}:
        markers.update({"blame", "fair", "unfair", "cost"})

    markers.update(part for part in current.reaction.primary_reaction.split("_") if part)
    markers.update(part for part in current.event.event_type.split("_") if part)
    return {marker for marker in markers if marker not in STOPWORDS}


def _score_irreplaceability(
    previous: list[NarrativeStructure],
    current: NarrativeStructure,
    response_text: str,
    context_reference_score: float,
) -> float:
    normalized = _normalize(response_text)
    response_tokens = set(_significant_tokens(response_text))

    generic = GENERIC_RESPONSE_RE.search(normalized) is not None
    marker_overlap = bool(_current_state_markers(current).intersection(response_tokens))

    if generic and not marker_overlap:
        return 0.0

    if marker_overlap:
        return 1.0

    current_stage = _infer_stage_from_structure(current)
    response_stage = _infer_stage_from_text(response_text)

    if current_stage >= 3 and response_stage >= current_stage:
        return 1.0

    if previous and context_reference_score >= 1.0:
        return 1.0

    return 0.0


def _mean_score(*values: float) -> float:
    return round(sum(values) / max(1, len(values)), 2)


def _has_progression_signal(normalized_response: str) -> bool:
    return any(marker in normalized_response for marker in SHIFT_MARKERS) or any(
        cue in normalized_response for cue in PROGRESSION_CUES
    )


def _is_paraphrase_heavy(user_text: str, response_text: str, similarity: float) -> bool:
    normalized = _normalize(response_text)
    if PARAPHRASE_LEAD_RE.search(normalized) is None:
        return False

    if _has_progression_signal(normalized):
        return False

    user_tokens = set(_significant_tokens(user_text))
    response_tokens = set(_significant_tokens(response_text))
    coverage = len(user_tokens.intersection(response_tokens)) / max(1, len(user_tokens))

    return similarity >= 0.40 or coverage >= 0.70
