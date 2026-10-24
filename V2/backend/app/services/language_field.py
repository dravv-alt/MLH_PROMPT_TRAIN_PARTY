import re
from statistics import mean

from app.models.schemas import LanguageField


HIGH_ENERGY_TOKENS = {
    "panic",
    "spiraling",
    "explode",
    "snapped",
    "rage",
    "freaking out",
    "overwhelmed",
    "drowning",
    "urgent",
    "now",
}
LOW_ENERGY_TOKENS = {
    "numb",
    "blank",
    "empty",
    "tired",
    "drained",
    "flat",
    "quiet",
    "slow",
    "faded",
}
ABSTRACT_TOKENS = {
    "pattern",
    "meaning",
    "identity",
    "narrative",
    "dynamic",
    "system",
    "autonomy",
    "control",
    "fairness",
    "framework",
}
CONCRETE_TOKENS = {
    "today",
    "yesterday",
    "call",
    "texted",
    "meeting",
    "room",
    "kitchen",
    "desk",
    "voice",
    "body",
}
ANALYTICAL_TOKENS = {
    "because",
    "therefore",
    "however",
    "although",
    "pattern",
    "structure",
    "sequence",
    "interpret",
    "evaluate",
    "analysis",
}
EMOTIONAL_HIGH_TOKENS = {
    "furious",
    "terrified",
    "crushed",
    "shaking",
    "panicked",
    "heart racing",
    "overwhelmed",
    "devastated",
}
EMOTIONAL_LOW_TOKENS = {
    "fine",
    "okay",
    "alright",
    "neutral",
    "calm",
    "steady",
    "flat",
}


def _normalize(text: str) -> str:
    return " ".join(text.lower().split()).strip()


def _tokenize_words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text)


def _split_sentences(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    return parts or [text]


def _contains_token(text: str, token: str) -> bool:
    escaped = re.escape(token)
    return re.search(rf"(?<!\w){escaped}(?!\w)", text) is not None


def _hits(text: str, tokens: set[str]) -> int:
    return sum(1 for token in tokens if _contains_token(text, token))


def derive_language_field(text: str) -> LanguageField:
    normalized = _normalize(text)
    words = _tokenize_words(normalized)
    sentences = _split_sentences(normalized)
    sentence_lengths = [len(_tokenize_words(sentence)) for sentence in sentences if sentence]

    avg_sentence_length = mean(sentence_lengths) if sentence_lengths else float(len(words))
    long_word_ratio = (
        sum(1 for word in words if len(word) >= 7) / max(1, len(words))
    )
    unique_word_ratio = len(set(words)) / max(1, len(words))

    high_energy_hits = _hits(normalized, HIGH_ENERGY_TOKENS)
    low_energy_hits = _hits(normalized, LOW_ENERGY_TOKENS)
    exclamation_weight = normalized.count("!")

    energy_score = (high_energy_hits * 1.2) + (exclamation_weight * 0.8) - (low_energy_hits * 1.1)
    if avg_sentence_length <= 6 and high_energy_hits:
        energy_score += 0.6

    if energy_score >= 2.4:
        energy_level = "high"
    elif energy_score <= -0.5:
        energy_level = "low"
    else:
        energy_level = "medium"

    abstract_hits = _hits(normalized, ABSTRACT_TOKENS)
    concrete_hits = _hits(normalized, CONCRETE_TOKENS)
    if abstract_hits >= concrete_hits + 2:
        abstraction_level = "abstract"
    elif concrete_hits >= abstract_hits + 2:
        abstraction_level = "concrete"
    else:
        abstraction_level = "mixed"

    comma_ratio = normalized.count(",") / max(1, len(sentences))
    if avg_sentence_length <= 8:
        sentence_rhythm = "short"
    elif avg_sentence_length >= 18 or comma_ratio >= 1.2:
        sentence_rhythm = "flowing"
    else:
        sentence_rhythm = "mixed"

    analytical_hits = _hits(normalized, ANALYTICAL_TOKENS)
    if analytical_hits >= 2 or long_word_ratio >= 0.24:
        vocabulary_density = "analytical"
    elif analytical_hits == 0 and long_word_ratio <= 0.12 and unique_word_ratio <= 0.72:
        vocabulary_density = "simple"
    else:
        vocabulary_density = "balanced"

    emotional_high_hits = _hits(normalized, EMOTIONAL_HIGH_TOKENS)
    emotional_low_hits = _hits(normalized, EMOTIONAL_LOW_TOKENS)
    intensity_score = (emotional_high_hits * 1.1) + (exclamation_weight * 0.9) - (emotional_low_hits * 0.9)

    if "!!!" in normalized:
        intensity_score += 1.0

    if intensity_score >= 2.4:
        emotional_intensity = "high"
    elif intensity_score <= -0.2:
        emotional_intensity = "low"
    else:
        emotional_intensity = "medium"

    return LanguageField(
        energy_level=energy_level,
        abstraction_level=abstraction_level,
        sentence_rhythm=sentence_rhythm,
        vocabulary_density=vocabulary_density,
        emotional_intensity=emotional_intensity,
    )
