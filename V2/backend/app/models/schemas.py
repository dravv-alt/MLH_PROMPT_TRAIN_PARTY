from datetime import datetime
from typing import Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventStructure(BaseModel):
    event_type: Literal[
        "interpersonal_conflict",
        "loss",
        "uncertainty",
        "pressure",
        "disappointment",
        "transition",
        "isolation",
        "achievement_strain",
        "health_concern",
        "other",
    ]
    actors: list[Literal["authority_figure", "peer", "romantic_partner", "institutional_system", "self"]]
    action_taken: Optional[Literal["compliance", "refusal", "avoidance", "confrontation", "withdrawal"]] = None
    action_desired: Optional[Literal["compliance", "refusal", "avoidance", "confrontation", "withdrawal"]] = None
    outcome: Literal["internal_distress", "external_conflict", "relief", "unresolved"]


class ConstraintField(BaseModel):
    freedom_to_refuse: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    conflict_cost: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    relationship_risk: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    expectation_pressure: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    power_asymmetry: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    emotional_safety: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class InternalReactionDynamics(BaseModel):
    primary_reaction: Literal[
        "inhibition",
        "rumination",
        "anger",
        "sadness",
        "fear",
        "numbness",
        "relief",
        "unknown",
    ]
    secondary_reaction: Optional[
        Literal[
            "inhibition",
            "rumination",
            "anger",
            "sadness",
            "fear",
            "numbness",
            "relief",
        ]
    ] = None
    after_effects: list[Literal["guilt", "self_disappointment", "resentment", "anxiety", "relief", "shame"]]
    intensity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    duration: Literal["immediate", "lingering", "chronic", "unknown"]


class MeaningMaking(BaseModel):
    self_interpretation: Literal[
        "I_should_have_done_better",
        "they_were_unfair",
        "this_is_just_how_it_is",
        "I_had_no_choice",
        "I_made_the_right_call",
        "unknown",
    ]
    perceived_failure: Optional[bool] = None
    identity_threat: Literal["competence", "moral_standing", "belonging", "autonomy", "none", "unknown"]
    control_belief: Literal["had_choice_but_failed", "had_no_choice", "unclear"]
    fairness_evaluation: Literal["self_blame", "external_blame", "shared", "unclear"]


class TemporalPatterning(BaseModel):
    is_recurring: bool
    pattern_signature: str = Field(min_length=3, max_length=200)
    progression: Literal["improving", "stable", "worsening", "unknown"]
    resolution_state: Literal["unresolved", "emerging_clarity", "partial_resolution", "integrated", "reopened"]


class LanguageField(BaseModel):
    energy_level: Literal["low", "medium", "high"]
    abstraction_level: Literal["concrete", "mixed", "abstract"]
    sentence_rhythm: Literal["short", "mixed", "flowing"]
    vocabulary_density: Literal["simple", "balanced", "analytical"]
    emotional_intensity: Literal["low", "medium", "high"]


class LanguageExpression(BaseModel):
    tone: Literal["self-critical", "neutral", "analytical", "overwhelmed", "resigned", "hopeful"]
    certainty: Literal["low", "medium", "high"]
    emotional_directness: Literal["low", "medium", "high"]
    key_phrases_mirrored: list[str] = Field(default_factory=list, exclude=True)
    language_field: LanguageField


class NarrativeStructure(BaseModel):
    event: EventStructure
    constraints: ConstraintField
    reaction: InternalReactionDynamics
    meaning: MeaningMaking
    temporal: TemporalPatterning
    language: LanguageExpression
    confidence_score: float = Field(ge=0.0, le=1.0)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None
    casual_mode: bool = False
    request_id: UUID = Field(default_factory=uuid4)
    generation_provider: Literal['local', 'hosted'] = 'local'
    hosted_consent: bool = False


class ChatResponse(BaseModel):
    session_id: str
    response_text: str
    display_response_text: str | None = None
    identity_stripped_input: str
    safety_mode: str
    narrative_structure: NarrativeStructure
    nlp_analysis: dict | None = None
    turn_id: int | None = None
    revision: int | None = None


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None
    mathematical_profile: Literal['low_resource', 'balanced', 'high_fidelity', 'responsive', 'stable'] = 'balanced'


class CalendarMood(BaseModel):
    label: str = Field(max_length=40)
    emoji: str = Field(default='', max_length=16)
    desc: str | None = Field(default=None, max_length=100)


class CalendarJournalRequest(BaseModel):
    title: str = Field(default='', max_length=200)
    text: str = Field(default='', max_length=10000)
    mood: CalendarMood | None = None
    sleep: float | None = Field(default=None, ge=0, le=24)
    stress: float | None = Field(default=None, ge=0, le=10)


class MemoryReviewRequest(BaseModel):
    status: Literal['open','acknowledged','dismissed']
    expected_revision: int = Field(ge=0)


class MemorySearchRequest(BaseModel):
    query: str = Field(min_length=1,max_length=2000)
    limit: int = Field(default=3,ge=1,le=10)


class NeuralPreferencesRequest(BaseModel):
    share_history_with_provider: bool | None = None
    process_local_unredacted: bool | None = None
    store_local_unredacted_memory: bool | None = None


class EmergencyResource(BaseModel):
    label: str
    region: str
    contact: str
    type: str


class SessionTurn(BaseModel):
    turn_id: int
    turn_index: int
    identity_stripped_input: Optional[str] = None
    response_text: Optional[str] = None
    safety_mode: Optional[str] = None
    narrative_structure: NarrativeStructure
    created_at: datetime


class SessionTurnsResponse(BaseModel):
    session_id: str
    turns: list[SessionTurn]


class SessionDeleteResponse(BaseModel):
    session_id: str
    deleted: bool


class JournalSuggestRequest(BaseModel):
    session_id: str = Field(min_length=4, max_length=64)
    max_suggestions: int = Field(default=5, ge=1, le=20)


class JournalSuggestResponse(BaseModel):
    session_id: str
    suggested_turn_ids: list[int]
    reasoning_labels: list[str]


class JournalCreateRequest(BaseModel):
    session_id: str = Field(min_length=4, max_length=64)
    selected_turn_ids: list[int] = Field(min_length=1)
    entry_title: Optional[str] = Field(default=None, max_length=200)
    user_reflection_text: Optional[str] = Field(default=None, max_length=5000)


class JournalEntryResponse(BaseModel):
    entry_id: int
    session_id: str
    selected_turn_ids: list[int]
    reasoning_labels: list[str]
    entry_title: Optional[str] = None
    user_reflection_text: Optional[str] = None
    summary_snapshot: str
    created_at: datetime
    updated_at: datetime


class JournalListResponse(BaseModel):
    entries: list[JournalEntryResponse]


class JournalUpdateRequest(BaseModel):
    entry_title: Optional[str] = Field(default=None, max_length=200)
    user_reflection_text: Optional[str] = Field(default=None, max_length=5000)


class JournalDeleteResponse(BaseModel):
    entry_id: int
    deleted: bool
