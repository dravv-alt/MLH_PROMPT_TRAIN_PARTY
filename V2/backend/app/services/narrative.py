from app.models.schemas import NarrativeStructure
from app.services.groq_client import groq_reflector
from app.services.narrative_engine import NarrativeEngine
from app.services.privacy import restore_identifiers, strip_identifiers, strip_identifiers_with_mapping
from app.services.response_policy import validate_human_tone, validate_language_alignment, validate_reflective_response
from app.services.response_scoring import evaluate_generation_filter
from app.services.session_state import SessionStateStore


class AIResponseUnavailableError(RuntimeError):
    """Raised when the provider cannot produce a policy-valid response."""


VIOLATION_RETRY_GUIDANCE = {
    "score_narrative_progression_below_0_6": "Advance exactly one narrative step beyond restating the user's words.",
    "score_language_alignment_below_0_6": "Match language style more closely to the user's energy, rhythm, and emotional intensity.",
    "score_coherence_continuity_below_0_6": "Make the response specific to this turn so it cannot fit a generic earlier turn.",
    "score_final_below_2_2": "Increase specificity and forward movement while staying concise and grounded.",
    "language_energy_escalation": "Do not raise energy above the user's current intensity.",
    "language_energy_flattening": "Do not flatten emotional energy below the user's current tone.",
    "language_abstraction_escalation": "Do not shift into higher abstraction than the user is using.",
    "language_rhythm_mismatch": "Match sentence rhythm and sentence length to the user's style.",
    "language_vocabulary_escalation": "Use simpler vocabulary that matches the user's wording density.",
    "language_emotional_inflation": "Do not amplify emotional intensity beyond what the user expressed.",
    "language_emotional_flattening": "Do not flatten emotional intensity below what the user expressed.",
    "human_tone_natural": "Use natural reflective language; avoid clinical or report-like phrasing.",
    "no_technical_meta_language": "Avoid technical and metadata words entirely.",
    "no_placeholder_leak": "Do not include placeholder tokens that are not present in the user text.",
    "sentence_count_1_to_2": "Keep output to 1 or 2 sentences.",
    "no_questions": "Do not ask questions.",
    "no_advice": "Do not give advice or instructions.",
    "no_diagnosis": "Do not diagnose or label the user.",
    "no_minimizing": "Do not minimize the user's experience.",
}


def _retry_guidance(violations: list[str]) -> list[str]:
    guidance: list[str] = []
    for violation in violations:
        message = VIOLATION_RETRY_GUIDANCE.get(violation)
        if message and message not in guidance:
            guidance.append(message)
    return guidance


def _build_provider_prompt(
    structure: NarrativeStructure,
    sanitized_input: str,
    casual_mode: bool,
    strict: bool = False,
    humanize: bool = False,
    alignment_violations: list[str] | None = None,
) -> str:
    style = "casual and warm" if casual_mode else "clear and precise"
    strict_clause = "Output exactly 2 sentences." if strict else "Output 1 to 2 sentences."
    language_field = structure.language.language_field

    prompt_lines = [
        "You are Sanctuary's reflective narrative assistant.",
        "Write with natural, human warmth while staying grounded in what the user shared.",
        "Use the distilled structure silently; do not expose internal labels or metadata.",
        strict_clause,
        "Hard constraints:",
        "- No questions.",
        "- No advice or instructions.",
        "- No diagnosis, disorder labels, or pathologizing language.",
        "- No minimizing statements.",
        "- Do not mention field names, scores, or technical terms from the internal structure.",
        "- Keep language non-judgmental and grounded in the present situation.",
        "- Keep to one structural shift at most.",
        "- Preserve the distilled meaning; do not add new causes, actors, or conclusions.",
        "- First sentence anchors the current unresolved point; final sentence advances one step.",
        "- If specific identities are redacted, you may reference them only with the same placeholder tokens from user text.",
        f"- Style: {style}.",
        "User text (identity stripped):",
        sanitized_input,
        "Internal distilled signals (for grounding only, never quote verbatim):",
        f"event_type={structure.event.event_type}; actors={','.join(structure.event.actors)}; action_taken={structure.event.action_taken}; action_desired={structure.event.action_desired}; outcome={structure.event.outcome}",
        "constraints="
        f"freedom_to_refuse:{structure.constraints.freedom_to_refuse}, "
        f"conflict_cost:{structure.constraints.conflict_cost}, "
        f"relationship_risk:{structure.constraints.relationship_risk}, "
        f"expectation_pressure:{structure.constraints.expectation_pressure}, "
        f"power_asymmetry:{structure.constraints.power_asymmetry}, "
        f"emotional_safety:{structure.constraints.emotional_safety}",
        "reaction="
        f"primary:{structure.reaction.primary_reaction}, "
        f"secondary:{structure.reaction.secondary_reaction}, "
        f"after_effects:{','.join(structure.reaction.after_effects)}, "
        f"intensity:{structure.reaction.intensity}, "
        f"duration:{structure.reaction.duration}",
        "meaning="
        f"self_interpretation:{structure.meaning.self_interpretation}, "
        f"perceived_failure:{structure.meaning.perceived_failure}, "
        f"identity_threat:{structure.meaning.identity_threat}, "
        f"control_belief:{structure.meaning.control_belief}, "
        f"fairness_evaluation:{structure.meaning.fairness_evaluation}",
        "temporal="
        f"is_recurring:{structure.temporal.is_recurring}, "
        f"pattern_signature:{structure.temporal.pattern_signature}, "
        f"progression:{structure.temporal.progression}, "
        f"resolution_state:{structure.temporal.resolution_state}",
        "language_field="
        f"energy_level:{language_field.energy_level}, "
        f"abstraction_level:{language_field.abstraction_level}, "
        f"sentence_rhythm:{language_field.sentence_rhythm}, "
        f"vocabulary_density:{language_field.vocabulary_density}, "
        f"emotional_intensity:{language_field.emotional_intensity}",
        "Language alignment constraints (must hold):",
        "- Keep energy within one level of the user's language energy.",
        "- Do not increase abstraction by more than one level from the user's language.",
        "- Keep sentence rhythm within one step of the user's rhythm.",
        "- Do not increase vocabulary density by more than one level.",
        "- Keep emotional intensity within one level of the user's intensity.",
        f"confidence_score={structure.confidence_score}",
        "Return plain text only.",
    ]

    if humanize:
        prompt_lines.extend(
            [
                "Rewrite constraint:",
                "- Use natural conversational reflection, not analytical report style.",
                "- Avoid phrases like 'the situation involves', 'is characterized by', or 'the outcome remains'.",
                "- If referencing a redacted entity, keep placeholder tokens exactly as given in user text.",
            ]
        )

    if alignment_violations:
        guidance = _retry_guidance(alignment_violations)
        prompt_lines.extend(
            [
                "Alignment retry constraints:",
                f"- Previous draft violations: {', '.join(alignment_violations)}.",
                "- Rewrite so all language alignment constraints are satisfied while preserving supportive meaning.",
            ]
        )
        if guidance:
            prompt_lines.append("Targeted retry guidance:")
            prompt_lines.extend(f"- {item}" for item in guidance)

    return "\n".join(prompt_lines)


def _build_provider_response(
    structure: NarrativeStructure,
    sanitized_input: str,
    casual_mode: bool,
    strict: bool = False,
    humanize: bool = False,
    alignment_violations: list[str] | None = None,
    max_attempts: int = 2,
) -> str | None:
    prompt = _build_provider_prompt(
        structure=structure,
        sanitized_input=sanitized_input,
        casual_mode=casual_mode,
        strict=strict,
        humanize=humanize,
        alignment_violations=alignment_violations,
    )

    for _ in range(max_attempts):
        generated = groq_reflector.generate(prompt)
        if not generated:
            continue

        normalized = " ".join(str(generated).split()).strip()
        if normalized:
            return normalized

    return None


def _is_response_acceptable(response_text: str, structure: NarrativeStructure) -> tuple[bool, list[str]]:
    policy_validation = validate_reflective_response(response_text)
    tone_validation = validate_human_tone(response_text)
    alignment_validation = validate_language_alignment(
        source=structure.language.language_field,
        response_text=response_text,
    )
    violations = [
        *policy_validation.violations,
        *tone_validation.violations,
        *alignment_validation.violations,
    ]
    return not violations, violations


def build_reflection(
    message: str,
    user_id: str,
    requested_session_id: str | None,
    session_store: SessionStateStore,
    casual_mode: bool = False,
) -> tuple[str, str, str, str, NarrativeStructure]:
    sanitized, placeholder_mapping = strip_identifiers_with_mapping(message)
    sanitized_for_model = sanitized if sanitized else "[content_removed_for_privacy]"

    session_id = session_store.resolve_session_id(user_id=user_id, requested_session_id=requested_session_id)
    previous = session_store.get_history(user_id=user_id, session_id=session_id)

    structure = NarrativeEngine().distill_turn(stripped_text=sanitized_for_model, previous=previous)

    low_confidence = structure.confidence_score < 0.50
    response: str | None = None
    mode = "reflective_groq"
    retry_violations: list[str] | None = None

    best_policy_valid_response: str | None = None
    best_policy_valid_score = -1.0
    best_policy_valid_violations: list[str] = []

    for attempt in range(3):
        candidate = _build_provider_response(
            structure=structure,
            sanitized_input=sanitized_for_model,
            casual_mode=casual_mode,
            strict=low_confidence or attempt > 0,
            humanize=attempt > 0,
            alignment_violations=retry_violations,
        )

        if not candidate:
            retry_violations = ["provider_empty_response"]
            continue

        restored_candidate = restore_identifiers(candidate, placeholder_mapping)

        acceptable, validation_violations = _is_response_acceptable(restored_candidate, structure)
        scoring = evaluate_generation_filter(
            previous=previous,
            current=structure,
            user_text=sanitized_for_model,
            response_text=restored_candidate,
        )
        combined_violations = [*validation_violations, *scoring.violations]

        if acceptable and scoring.final_score > best_policy_valid_score:
            best_policy_valid_response = restored_candidate
            best_policy_valid_score = scoring.final_score
            best_policy_valid_violations = combined_violations

        if acceptable and scoring.passed:
            response = restored_candidate
            mode = "reflective_groq"
            break

        retry_violations = combined_violations

    if response is None:
        if best_policy_valid_response:
            response = best_policy_valid_response
            mode = "reflective_groq_best_effort"
        else:
            joined = ",".join(retry_violations or best_policy_valid_violations or ["unknown"])
            raise AIResponseUnavailableError(
                "Groq response failed validation and scoring after 3 attempts "
                f"({joined})."
            )

    response_for_storage = strip_identifiers(response)

    session_store.append_structure(
        user_id=user_id,
        session_id=session_id,
        structure=structure,
        stripped_input=sanitized,
        response_text=response_for_storage,
        safety_mode=mode,
    )

    return session_id, response, sanitized, mode, structure
