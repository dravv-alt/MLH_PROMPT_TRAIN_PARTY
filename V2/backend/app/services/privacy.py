import re
from functools import lru_cache
from typing import Any

try:
    import spacy
    from spacy.language import Language
except Exception:  # pragma: no cover - environment dependent
    spacy = None
    Language = Any  # type: ignore[assignment]


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
URL_RE = re.compile(r"https?://\S+|www\.\S+")
DATE_RE = re.compile(
    r"\b(?:today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}/\d{1,2}/\d{2,4})\b",
    flags=re.IGNORECASE,
)

NAME_TOKEN = r"[A-Z][A-Za-z]*(?:\.)?(?:[-'][A-Za-z]+)*"

ORG_SUFFIX_RE = re.compile(
    rf"\b{NAME_TOKEN}(?:\s+{NAME_TOKEN}){{0,4}}\s+"
    r"(?:University|College|School|Institute|Hospital|Clinic|Center|Centre|Bank|Company|Corporation|Corp|LLC|Ltd)\b"
)
NAME_WITH_CUE_RE = re.compile(
    rf"\b(?P<prefix>(?i:(?:with|met|from|to|named|called|texted|emailed|messaged))\s+)"
    rf"(?P<value>(?:(?i:(?:dr|mr|mrs|ms|prof))\.?\s+)?{NAME_TOKEN}(?:\s+{NAME_TOKEN}){{0,1}})\b",
)
LOCATION_WITH_PREP_RE = re.compile(
    rf"\b(?P<prefix>(?i:(?:in|at|from|to|near))\s+)(?P<value>{NAME_TOKEN}(?:\s+{NAME_TOKEN}){{0,2}})\b"
)
TITLE_NAME_RE = re.compile(rf"\b(?i:(?:dr|mr|mrs|ms|prof))\.?\s+{NAME_TOKEN}\b")


ENTITY_LABELS_TO_MASK = {
    "PERSON",
    "ORG",
    "GPE",
    "LOC",
    "FAC",
    "NORP",
    "EVENT",
    "WORK_OF_ART",
}

COMMON_NON_ENTITY_PHRASES = {
    "i",
    "it",
    "this",
    "that",
    "everything",
    "someone",
    "something",
    "part",
    "today",
    "tomorrow",
    "yesterday",
    "then",
    "we",
    "you",
    "he",
    "she",
    "they",
    "what",
    "when",
    "where",
    "why",
    "how",
    "and",
    "but",
    "because",
    "thank",
}

PLACEHOLDER_TOKEN_RE = r"\[[a-z][a-z0-9_]*(?:_\d+)?\]"
RESTORABLE_PLACEHOLDER_RE = re.compile(PLACEHOLDER_TOKEN_RE)

WEEKDAY_TOKENS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}

RELATIVE_DAY_TOKENS = {"today", "tomorrow", "yesterday"}

FRIEND_KEYWORDS = {"friend", "bestie", "buddy", "pal", "roommate"}
FAMILY_KEYWORDS = {
    "mom",
    "mother",
    "dad",
    "father",
    "parent",
    "parents",
    "sister",
    "brother",
    "aunt",
    "uncle",
    "cousin",
    "grandma",
    "grandmother",
    "grandpa",
    "grandfather",
    "son",
    "daughter",
}
ROMANTIC_KEYWORDS = {"partner", "boyfriend", "girlfriend", "husband", "wife", "spouse", "ex"}
AUTHORITY_KEYWORDS = {"boss", "manager", "teacher", "professor", "mentor", "supervisor", "coach"}
PEER_KEYWORDS = {"coworker", "colleague", "classmate", "teammate"}


def _normalize_placeholder_label(label: str) -> str:
    normalized = re.sub(r"[^a-z0-9_]+", "_", label.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "redacted"


class _PlaceholderMapper:
    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self.mapping: dict[str, str] = {}

    def token_for(self, kind: str, original_value: str) -> str:
        normalized_kind = kind if kind.endswith("_removed") else f"{kind}_removed"
        next_index = self._counters.get(normalized_kind, 0) + 1
        self._counters[normalized_kind] = next_index

        token = f"[{normalized_kind}_{next_index}]"
        if token not in self.mapping:
            self.mapping[token] = original_value
        return token

    def token_for_label(self, label: str, original_value: str) -> str:
        normalized_label = _normalize_placeholder_label(label)
        next_index = self._counters.get(normalized_label, 0) + 1
        self._counters[normalized_label] = next_index

        token = f"[{normalized_label}_{next_index}]"
        if token not in self.mapping:
            self.mapping[token] = original_value
        return token


def _replace_with_indexed_placeholder(
    text: str,
    pattern: re.Pattern[str],
    mapper: _PlaceholderMapper,
    label_resolver,
) -> str:
    def _replace(match: re.Match[str]) -> str:
        resolved_label = label_resolver(match) if callable(label_resolver) else str(label_resolver)
        return mapper.token_for_label(resolved_label, match.group(0))

    return pattern.sub(_replace, text)


def _contains_any_keyword(text: str, keywords: set[str]) -> bool:
    lowered = text.lower()
    return any(re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", lowered) for keyword in keywords)


def _infer_person_label(context: str) -> str:
    if _contains_any_keyword(context, {"mom", "mother"}):
        return "mother_figure"
    if _contains_any_keyword(context, {"dad", "father"}):
        return "father_figure"
    if _contains_any_keyword(context, FAMILY_KEYWORDS):
        return "family_member"
    if _contains_any_keyword(context, ROMANTIC_KEYWORDS):
        return "romantic_partner"
    if _contains_any_keyword(context, FRIEND_KEYWORDS):
        return "close_friend"
    if _contains_any_keyword(context, AUTHORITY_KEYWORDS):
        return "authority_figure"
    if _contains_any_keyword(context, PEER_KEYWORDS):
        return "peer_contact"
    return "person_reference"


def _entity_placeholder_label(label: str, source_text: str, start: int, end: int) -> str:
    if label == "PERSON":
        left = max(0, start - 48)
        right = min(len(source_text), end + 48)
        context = source_text[left:right]
        return _infer_person_label(context)

    if label in {"GPE", "LOC"}:
        return "city_or_town"
    if label == "ORG":
        return "organization"
    if label == "FAC":
        return "place_reference"
    if label == "NORP":
        return "community_group"
    if label == "EVENT":
        return "event_reference"
    if label == "WORK_OF_ART":
        return "title_reference"

    return "entity_reference"


def _date_placeholder_label(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in RELATIVE_DAY_TOKENS:
        return "recent_day"
    if normalized in WEEKDAY_TOKENS:
        return "weekday_reference"
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}", normalized):
        return "calendar_date"
    return "time_reference"


@lru_cache(maxsize=1)
def _load_nlp_with_mode() -> tuple[Language | None, str]:
    """Load spaCy NER pipeline once; fall back to a lightweight rule-based pipeline."""
    if spacy is None:
        return None, "regex_only_fallback"

    try:
        nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger", "lemmatizer", "textcat"])
        return nlp, "spacy_en_core_web_sm"
    except Exception:
        nlp = spacy.blank("en")
        ruler = nlp.add_pipe("entity_ruler")
        ruler.add_patterns(
            [
                {"label": "PERSON", "pattern": [{"IS_TITLE": True}, {"IS_TITLE": True}]},
                {"label": "PERSON", "pattern": [{"LOWER": {"IN": ["mr", "mrs", "ms", "dr", "prof"]}}, {"IS_TITLE": True}]},
                {
                    "label": "ORG",
                    "pattern": [
                        {"IS_TITLE": True},
                        {"IS_TITLE": True, "OP": "*"},
                        {
                            "LOWER": {
                                "IN": [
                                    "university",
                                    "college",
                                    "school",
                                    "hospital",
                                    "bank",
                                    "institute",
                                    "inc",
                                    "corp",
                                    "llc",
                                    "ltd",
                                ]
                            }
                        },
                    ],
                },
            ]
        )
        return nlp, "entity_ruler_fallback"


def _get_nlp() -> Language | None:
    return _load_nlp_with_mode()[0]


def get_ner_backend_mode() -> str:
    return _load_nlp_with_mode()[1]


def _mask_contextual_identifiers(text: str, mapper: _PlaceholderMapper | None = None) -> str:
    def _entity_token(value: str, label: str = "entity_reference") -> str:
        if mapper is None:
            return "[entity_removed]"
        return mapper.token_for_label(label, value)

    def _cue_replace(match: re.Match[str]) -> str:
        prefix = match.group("prefix").lower()
        if any(token in prefix for token in ("with", "met", "texted", "emailed", "messaged")):
            label = "close_friend"
        else:
            label = "person_reference"
        return f"{match.group('prefix')}{_entity_token(match.group('value'), label=label)}"

    masked = ORG_SUFFIX_RE.sub(lambda match: _entity_token(match.group(0), label="organization"), text)
    masked = TITLE_NAME_RE.sub(lambda match: _entity_token(match.group(0), label="professional_person"), masked)
    masked = NAME_WITH_CUE_RE.sub(_cue_replace, masked)
    masked = LOCATION_WITH_PREP_RE.sub(
        lambda match: f"{match.group('prefix')}{_entity_token(match.group('value'), label='city_or_town')}",
        masked,
    )
    return masked


def _cleanup_placeholder_artifacts(text: str) -> str:
    cleaned = text
    cleaned = re.sub(rf"({PLACEHOLDER_TOKEN_RE})(?:[-'][A-Za-z]+)+", r"\1", cleaned)
    cleaned = re.sub(rf"({PLACEHOLDER_TOKEN_RE})\s*-\s*[A-Za-z]+", r"\1", cleaned)
    cleaned = re.sub(rf"({PLACEHOLDER_TOKEN_RE})(?:\s*[.,;:]\s*\1)+", r"\1", cleaned)
    cleaned = re.sub(rf"({PLACEHOLDER_TOKEN_RE})\s+\1", r"\1", cleaned)
    return cleaned


def _mask_named_entities(text: str, mapper: _PlaceholderMapper | None = None) -> str:
    nlp = _get_nlp()
    if nlp is None:
        return text

    doc = nlp(text)

    spans: list[tuple[int, int, str]] = []
    for ent in doc.ents:
        if ent.label_ not in ENTITY_LABELS_TO_MASK:
            continue

        normalized = ent.text.strip().lower()

        # Preserve pronoun-like/common sentence-starter tokens if fallback rules tag them.
        if normalized in COMMON_NON_ENTITY_PHRASES:
            continue

        spans.append((ent.start_char, ent.end_char, ent.label_))

    if not spans:
        return text

    spans.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    selected: list[tuple[int, int, str]] = []
    for start, end, label in spans:
        if selected and start < selected[-1][1]:
            continue
        selected.append((start, end, label))

    chunks: list[str] = []
    cursor = 0
    for start, end, label in selected:
        chunks.append(text[cursor:start])
        if mapper is None:
            chunks.append("[entity_removed]")
        else:
            placeholder_label = _entity_placeholder_label(label, text, start, end)
            chunks.append(mapper.token_for_label(placeholder_label, text[start:end]))
        cursor = end
    chunks.append(text[cursor:])
    return "".join(chunks)


def strip_identifiers_with_mapping(text: str) -> tuple[str, dict[str, str]]:
    mapper = _PlaceholderMapper()

    cleaned = _replace_with_indexed_placeholder(text, EMAIL_RE, mapper, "email_address")
    cleaned = _replace_with_indexed_placeholder(cleaned, PHONE_RE, mapper, "phone_number")
    cleaned = _replace_with_indexed_placeholder(cleaned, URL_RE, mapper, "web_link")
    cleaned = _replace_with_indexed_placeholder(cleaned, DATE_RE, mapper, lambda match: _date_placeholder_label(match.group(0)))

    cleaned = re.sub(r"@\w+", lambda match: mapper.token_for_label("social_handle", match.group(0)), cleaned)
    cleaned = _mask_contextual_identifiers(cleaned, mapper=mapper)
    cleaned = _mask_named_entities(cleaned, mapper=mapper)
    cleaned = _cleanup_placeholder_artifacts(cleaned)

    return " ".join(cleaned.split()), mapper.mapping


def strip_identifiers(text: str) -> str:
    cleaned = text
    cleaned = EMAIL_RE.sub("[email_removed]", cleaned)
    cleaned = PHONE_RE.sub("[phone_removed]", cleaned)
    cleaned = URL_RE.sub("[link_removed]", cleaned)
    cleaned = DATE_RE.sub("[time_removed]", cleaned)

    # Remove @handles and then apply NER-based masking.
    cleaned = re.sub(r"@\w+", "[handle_removed]", cleaned)
    cleaned = _mask_contextual_identifiers(cleaned)
    cleaned = _mask_named_entities(cleaned)
    cleaned = _cleanup_placeholder_artifacts(cleaned)

    return " ".join(cleaned.split())


def restore_identifiers(text: str, placeholder_mapping: dict[str, str] | None) -> str:
    if not text or not placeholder_mapping:
        return text

    def _restore(match: re.Match[str]) -> str:
        token = match.group(0)
        return placeholder_mapping.get(token, token)

    restored = RESTORABLE_PLACEHOLDER_RE.sub(_restore, text)
    return " ".join(restored.split())
