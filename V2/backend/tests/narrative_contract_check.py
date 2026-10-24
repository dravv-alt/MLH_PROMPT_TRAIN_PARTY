from fastapi.testclient import TestClient

from app.api.routes import get_current_user_id
from app.models.schemas import LanguageField, NarrativeStructure
from app.services import narrative as narrative_service
from app.services.response_policy import validate_human_tone, validate_language_alignment, validate_reflective_response
from app.services.response_scoring import evaluate_generation_filter
from main import app


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(f"FAILED: {label}")
    print(f"PASS: {label}")


def post_chat(client: TestClient, message: str, session_id: str | None, casual_mode: bool = False) -> dict:
    response = client.post(
        "/chat",
        json={"message": message, "session_id": session_id, "casual_mode": casual_mode},
    )
    if response.status_code != 200:
        raise AssertionError(f"FAILED: /chat status {response.status_code} body={response.text}")
    return response.json()


def run_contract_checks() -> None:
    app.dependency_overrides[get_current_user_id] = lambda: "usr_contract"
    client = TestClient(app)

    original_groq_generate = narrative_service.groq_reflector.generate

    def _mock_groq_generate(prompt: str) -> str:
        is_casual = "Style: casual and warm." in prompt
        is_strict = "Output exactly 2 sentences." in prompt

        if is_casual:
            return (
                "You are carrying a lot right now, and that tension sounds exhausting. "
                "The replay loop shows how much this moment is still sitting in your body."
            )

        if is_strict:
            return (
                "That conflict still feels active inside you, and the replaying fits with how tense this landed. "
                "You are naming the reaction clearly instead of disappearing inside it."
            )

        return (
            "That conflict still feels active inside you, and the replaying makes sense after a hard moment. "
            "You are naming the reaction directly, which creates a small step of clarity."
        )

    narrative_service.groq_reflector.generate = _mock_groq_generate

    try:
        # 1) Nested 6-layer contract validity + allowed values
        contract_turn = post_chat(client, "I had a fight with my mom at Brooklyn University yesterday and I feel terrible.", None)
        structure = contract_turn["narrative_structure"]
        check(
            set(structure.keys()) == {"event", "constraints", "reaction", "meaning", "temporal", "language", "confidence_score"},
            "NarrativeStructure has canonical 6-layer top-level shape",
        )

        allowed_event_type = {
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
        }
        allowed_actor_roles = {
            "authority_figure",
            "peer",
            "romantic_partner",
            "institutional_system",
            "self",
        }
        allowed_actions = {
            "compliance",
            "refusal",
            "avoidance",
            "confrontation",
            "withdrawal",
        }
        allowed_outcomes = {"internal_distress", "external_conflict", "relief", "unresolved"}
        allowed_primary_reaction = {
            "inhibition",
            "rumination",
            "anger",
            "sadness",
            "fear",
            "numbness",
            "relief",
        }
        allowed_after_effects = {
            "guilt",
            "self_disappointment",
            "resentment",
            "anxiety",
            "relief",
            "shame",
        }
        allowed_self_interpretation = {
            "I_should_have_done_better",
            "they_were_unfair",
            "this_is_just_how_it_is",
            "I_had_no_choice",
            "I_made_the_right_call",
        }
        allowed_identity_threat = {"competence", "moral_standing", "belonging", "autonomy", "none"}
        allowed_control_belief = {"had_choice_but_failed", "had_no_choice", "unclear"}
        allowed_fairness = {"self_blame", "external_blame", "shared", "unclear"}
        allowed_progression = {"improving", "stable", "worsening"}
        allowed_resolution = {"unresolved", "emerging_clarity", "partial_resolution", "integrated", "reopened"}
        allowed_tone = {"self-critical", "neutral", "analytical", "overwhelmed", "resigned", "hopeful"}
        allowed_lmh = {"low", "medium", "high"}
        allowed_abstraction = {"concrete", "mixed", "abstract"}
        allowed_rhythm = {"short", "mixed", "flowing"}
        allowed_vocabulary = {"simple", "balanced", "analytical"}

        event = structure["event"]
        constraints = structure["constraints"]
        reaction = structure["reaction"]
        meaning = structure["meaning"]
        temporal = structure["temporal"]
        language = structure["language"]

        check(event["event_type"] in allowed_event_type, "event.event_type allowed value")
        check(all(actor in allowed_actor_roles for actor in event["actors"]), "event.actors allowed values")
        check(event["action_taken"] in allowed_actions, "event.action_taken allowed value")
        check(event["action_desired"] in allowed_actions, "event.action_desired allowed value")
        check(event["outcome"] in allowed_outcomes, "event.outcome allowed value")

        for field in [
            "freedom_to_refuse",
            "conflict_cost",
            "relationship_risk",
            "expectation_pressure",
            "power_asymmetry",
            "emotional_safety",
        ]:
            check(0.0 <= constraints[field] <= 1.0, f"constraints.{field} bounded [0,1]")

        check(reaction["primary_reaction"] in allowed_primary_reaction, "reaction.primary_reaction allowed value")
        if reaction["secondary_reaction"] is not None:
            check(reaction["secondary_reaction"] in allowed_primary_reaction, "reaction.secondary_reaction allowed value")
        check(all(effect in allowed_after_effects for effect in reaction["after_effects"]), "reaction.after_effects allowed values")
        check(0.0 <= reaction["intensity"] <= 1.0, "reaction.intensity bounded [0,1]")
        check(reaction["duration"] in {"immediate", "lingering", "chronic"}, "reaction.duration allowed value")

        check(meaning["self_interpretation"] in allowed_self_interpretation, "meaning.self_interpretation allowed value")
        check(isinstance(meaning["perceived_failure"], bool), "meaning.perceived_failure is bool")
        check(meaning["identity_threat"] in allowed_identity_threat, "meaning.identity_threat allowed value")
        check(meaning["control_belief"] in allowed_control_belief, "meaning.control_belief allowed value")
        check(meaning["fairness_evaluation"] in allowed_fairness, "meaning.fairness_evaluation allowed value")

        check(isinstance(temporal["is_recurring"], bool), "temporal.is_recurring is bool")
        check(temporal["progression"] in allowed_progression, "temporal.progression allowed value")
        check(temporal["resolution_state"] in allowed_resolution, "temporal.resolution_state allowed value")

        check(language["tone"] in allowed_tone, "language.tone allowed value")
        check(language["certainty"] in allowed_lmh, "language.certainty allowed value")
        check(language["emotional_directness"] in allowed_lmh, "language.emotional_directness allowed value")
        check(isinstance(language["key_phrases_mirrored"], list), "language.key_phrases_mirrored is list")
        check(isinstance(language["language_field"], dict), "language.language_field is object")
        check(language["language_field"]["energy_level"] in allowed_lmh, "language.language_field.energy_level allowed value")
        check(
            language["language_field"]["abstraction_level"] in allowed_abstraction,
            "language.language_field.abstraction_level allowed value",
        )
        check(language["language_field"]["sentence_rhythm"] in allowed_rhythm, "language.language_field.sentence_rhythm allowed value")
        check(
            language["language_field"]["vocabulary_density"] in allowed_vocabulary,
            "language.language_field.vocabulary_density allowed value",
        )
        check(
            language["language_field"]["emotional_intensity"] in allowed_lmh,
            "language.language_field.emotional_intensity allowed value",
        )

        check(0.0 <= structure["confidence_score"] <= 1.0, "confidence_score bounded [0,1]")

        # 2) PII stripping and signature privacy
        stripped = contract_turn["identity_stripped_input"].lower()
        signature = temporal["pattern_signature"].lower()
        check("brooklyn" not in stripped and "yesterday" not in stripped, "PII/time markers stripped from input")
        check("brooklyn" not in signature and "university" not in signature, "pattern_signature excludes direct identifiers")

        # 2b) Global language field must be sent for alignment, while mirrored phrases remain excluded
        captured_prompt: dict[str, str] = {"value": ""}
        active_groq_generate = narrative_service.groq_reflector.generate
        try:
            def _capture_prompt(prompt: str) -> str:
                captured_prompt["value"] = prompt
                return "I can hold this with you. The weight you are naming is real and understandable."

            narrative_service.groq_reflector.generate = _capture_prompt
            _ = post_chat(client, "I let myself down again in that conversation.", None)
            prompt_lower = captured_prompt["value"].lower()
            check("language_field=" in prompt_lower, "provider prompt includes global language alignment block")
            check("key_phrases_mirrored" not in prompt_lower, "provider prompt excludes key phrase mirroring data")
        finally:
            narrative_service.groq_reflector.generate = active_groq_generate

        ner_turn = post_chat(
            client,
            "I spoke with Alice in Paris at Redwood University yesterday and feel conflicted.",
            None,
        )
        ner_stripped = ner_turn["identity_stripped_input"].lower()
        check("alice" not in ner_stripped, "spaCy masking removes person-like entities")
        check("paris" not in ner_stripped, "spaCy masking removes location-like entities")
        check("redwood" not in ner_stripped and "university" not in ner_stripped, "spaCy masking removes organization-like entities")

        edge_turn = post_chat(
            client,
            "I met Jean-Luc and texted O'Connor from San Francisco after calling Dr. Patel at St. Mary's Hospital yesterday.",
            None,
        )
        edge_stripped = edge_turn["identity_stripped_input"].lower()
        check("jean" not in edge_stripped and "luc" not in edge_stripped, "context masking handles hyphenated names")
        check("connor" not in edge_stripped, "context masking handles apostrophe names")
        check("francisco" not in edge_stripped and "patel" not in edge_stripped, "context masking handles location and titled names")
        check("hospital" not in edge_stripped, "context masking handles organization suffix edge cases")

        # 3) Resolution progression behaves across a synthetic arc
        t1 = post_chat(client, "I had a fight with my mom and it hurt.", None)
        session_phase = t1["session_id"]
        t2 = post_chat(client, "Then it happened again because she ignored what I said.", session_phase)
        t3 = post_chat(client, "It means I keep doubting myself when conflict starts.", session_phase)
        t4 = post_chat(client, "I decided I can set a boundary without attacking anyone.", session_phase)
        t5 = post_chat(client, "Thank you, we can pause here for now.", session_phase)

        resolutions = [
            t1["narrative_structure"]["temporal"]["resolution_state"],
            t2["narrative_structure"]["temporal"]["resolution_state"],
            t3["narrative_structure"]["temporal"]["resolution_state"],
            t4["narrative_structure"]["temporal"]["resolution_state"],
            t5["narrative_structure"]["temporal"]["resolution_state"],
        ]
        check(resolutions[0] == "unresolved", "resolution starts unresolved")
        check("emerging_clarity" in resolutions[2:4], "resolution shows emerging clarity during meaning/integrating")
        check(resolutions[-1] in {"integrated", "partial_resolution"}, "closing turn reaches a stabilized resolution state")

        # 5) Response constraints + casual mode policy safety
        default_mode = post_chat(client, "Work pressure is heavy and I keep overthinking this.", None, casual_mode=False)
        casual_mode = post_chat(client, "Work pressure is heavy and I keep overthinking this.", None, casual_mode=True)
        check(default_mode["response_text"] != casual_mode["response_text"], "casual mode changes response style")
        check(validate_reflective_response(default_mode["response_text"]).is_valid, "default mode response passes policy validator")
        check(validate_reflective_response(casual_mode["response_text"]).is_valid, "casual mode response passes policy validator")

        # 6) Low-confidence still goes through provider path (no conservative mode)
        low_conf = post_chat(client, "ok", None)
        check(low_conf["narrative_structure"]["confidence_score"] < 0.50, "low-confidence turn scored below threshold")
        check(low_conf["safety_mode"] != "conservative", "low-confidence path no longer uses conservative safety mode")
        check(validate_reflective_response(low_conf["response_text"]).is_valid, "low-confidence response still satisfies policy constraints")

        # 7) Groq is the primary provider path
        groq_turn = post_chat(client, "I feel stuck after that conflict and keep replaying it.", None)
        check(groq_turn["safety_mode"] == "reflective_groq", "groq path is the primary runtime response path")
        check(validate_reflective_response(groq_turn["response_text"]).is_valid, "groq response passes policy validator")
        check(validate_human_tone(groq_turn["response_text"]).is_valid, "groq response passes human-tone validator")

        source_language = groq_turn["narrative_structure"]["language"]["language_field"]
        alignment_result = validate_language_alignment(
            source=LanguageField(**source_language),
            response_text=groq_turn["response_text"],
        )
        check(alignment_result.is_valid, "groq response passes language alignment validator")

        scoring_result = evaluate_generation_filter(
            previous=[],
            current=NarrativeStructure(**groq_turn["narrative_structure"]),
            user_text=groq_turn["identity_stripped_input"],
            response_text=groq_turn["response_text"],
        )
        check(scoring_result.passed, "groq response passes generation scoring gate")

        generic_scoring = evaluate_generation_filter(
            previous=[NarrativeStructure(**groq_turn["narrative_structure"])],
            current=NarrativeStructure(**groq_turn["narrative_structure"]),
            user_text=groq_turn["identity_stripped_input"],
            response_text="That sounds hard. Your feelings are valid.",
        )
        check(not generic_scoring.passed, "generic response fails generation scoring gate")

        # 8) Robotic response triggers humanized rewrite retry
        active_groq_generate = narrative_service.groq_reflector.generate
        try:
            state = {"count": 0}

            def _robotic_then_human(prompt: str) -> str:
                state["count"] += 1
                if state["count"] == 1:
                    return (
                        "The situation involves recurring interpersonal strain and the outcome remains unresolved. "
                        "This experience is characterized by anxiety."
                    )
                return (
                    "That tension still feels active in your body, and it fits with how heavy this has been. "
                    "You are naming the reaction more clearly instead of getting pulled under it."
                )

            narrative_service.groq_reflector.generate = _robotic_then_human
            rewritten = post_chat(client, "I still feel tense after all of this.", None)
            check(state["count"] >= 2, "robotic response path triggers model rewrite retry")
            check(validate_reflective_response(rewritten["response_text"]).is_valid, "rewritten response passes policy validator")
            check(validate_human_tone(rewritten["response_text"]).is_valid, "rewritten response passes human-tone validator")
        finally:
            narrative_service.groq_reflector.generate = active_groq_generate

        # 9) If scoring cannot pass after retries, best policy-valid candidate returns with explicit flag
        active_groq_generate = narrative_service.groq_reflector.generate
        try:
            def _always_generic(_: str) -> str:
                return "That sounds hard. Your feelings are valid."

            narrative_service.groq_reflector.generate = _always_generic
            best_effort = post_chat(client, "I still feel tense and this keeps happening.", None)
            check(best_effort["safety_mode"] == "reflective_groq_best_effort", "best-effort mode returned when score threshold is not met")
            check(validate_reflective_response(best_effort["response_text"]).is_valid, "best-effort response still passes policy validator")
        finally:
            narrative_service.groq_reflector.generate = active_groq_generate

        print("ALL SECTION 3 SUB-PART CHECKS PASSED")
    finally:
        narrative_service.groq_reflector.generate = original_groq_generate


if __name__ == "__main__":
    run_contract_checks()
