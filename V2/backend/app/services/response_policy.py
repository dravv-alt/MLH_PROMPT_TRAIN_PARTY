import re
from dataclasses import dataclass

from app.models.schemas import LanguageField
from app.services.language_field import derive_language_field


ADVICE_RE = re.compile(r"\b(?:you should|you must|you need to|try this|i recommend|consider doing)\b", flags=re.IGNORECASE)
DIAGNOSIS_RE = re.compile(
    r"\b(?:you (?:have|are)\s+(?:depressed|anxious|bipolar|traumatized)|diagnos(?:e|is)|disorder|ptsd|adhd)\b",
    flags=re.IGNORECASE,
)
MINIMIZING_RE = re.compile(
    r"\b(?:it will be okay|others have it worse|just be positive|just relax|calm down)\b",
    flags=re.IGNORECASE,
)
ROBOTIC_STYLE_RE = re.compile(
    r"\b(?:the situation involves|this situation involves|this (?:experience|event|pattern) (?:is|was) "
    r"(?:characterized by|marked by)|the outcome (?:of this|remains)|the emotional landscape|this dynamic)\b",
    flags=re.IGNORECASE,
)
TECHNICAL_META_RE = re.compile(
    r"\b(?:event_type|confidence_score|resolution_state|action_taken|action_desired|pattern_signature|"
    r"primary_reaction|secondary_reaction|identity_threat|constraint(?:s)?)\b",
    flags=re.IGNORECASE,
)
PLACEHOLDER_LEAK_RE = re.compile(r"\[[a-z][a-z0-9_]*(?:_\d+)?\]")

ENERGY_RANK = {"low": 0, "medium": 1, "high": 2}
ABSTRACTION_RANK = {"concrete": 0, "mixed": 1, "abstract": 2}
RHYTHM_RANK = {"short": 0, "mixed": 1, "flowing": 2}
VOCABULARY_RANK = {"simple": 0, "balanced": 1, "analytical": 2}
INTENSITY_RANK = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True)
class PolicyValidationResult:
    is_valid: bool
    violations: list[str]


def _count_sentences(text: str) -> int:
    fragments = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    return len(fragments)


def validate_reflective_response(text: str) -> PolicyValidationResult:
    violations: list[str] = []

    if "?" in text:
        violations.append("no_questions")

    sentence_count = _count_sentences(text)
    if sentence_count < 1 or sentence_count > 2:
        violations.append("sentence_count_1_to_2")

    if ADVICE_RE.search(text):
        violations.append("no_advice")

    if DIAGNOSIS_RE.search(text):
        violations.append("no_diagnosis")

    if MINIMIZING_RE.search(text):
        violations.append("no_minimizing")

    return PolicyValidationResult(is_valid=not violations, violations=violations)


def validate_human_tone(text: str) -> PolicyValidationResult:
    violations: list[str] = []

    if ROBOTIC_STYLE_RE.search(text):
        violations.append("human_tone_natural")

    if TECHNICAL_META_RE.search(text):
        violations.append("no_technical_meta_language")

    if PLACEHOLDER_LEAK_RE.search(text):
        violations.append("no_placeholder_leak")

    return PolicyValidationResult(is_valid=not violations, violations=violations)


def _is_rhythm_aligned(source: str, response: str) -> bool:
    source_rank = RHYTHM_RANK[source]
    response_rank = RHYTHM_RANK[response]
    return abs(response_rank - source_rank) <= 1


def validate_language_alignment(source: LanguageField, response_text: str) -> PolicyValidationResult:
    response = derive_language_field(response_text)
    violations: list[str] = []

    if ENERGY_RANK[response.energy_level] - ENERGY_RANK[source.energy_level] > 1:
        violations.append("language_energy_escalation")

    if ENERGY_RANK[source.energy_level] - ENERGY_RANK[response.energy_level] > 1:
        violations.append("language_energy_flattening")

    if ABSTRACTION_RANK[response.abstraction_level] - ABSTRACTION_RANK[source.abstraction_level] > 1:
        violations.append("language_abstraction_escalation")

    if not _is_rhythm_aligned(source.sentence_rhythm, response.sentence_rhythm):
        violations.append("language_rhythm_mismatch")

    if VOCABULARY_RANK[response.vocabulary_density] - VOCABULARY_RANK[source.vocabulary_density] > 1:
        violations.append("language_vocabulary_escalation")

    if INTENSITY_RANK[response.emotional_intensity] - INTENSITY_RANK[source.emotional_intensity] > 1:
        violations.append("language_emotional_inflation")

    if INTENSITY_RANK[source.emotional_intensity] - INTENSITY_RANK[response.emotional_intensity] > 1:
        violations.append("language_emotional_flattening")

    return PolicyValidationResult(is_valid=not violations, violations=violations)
