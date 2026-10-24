"""ResponsePlan, correction, validation, and local-provider regressions."""
from pathlib import Path

import pytest

from app.services import dmrst
from app.services.local_generation import FEW_SHOT_TARGETS, LocalGenerationProvider, build_generation_messages, build_polish_messages, extract_reflection, repair_second_person_voice
from app.services.nlp_engine import analyze_turn
from app.services.response_planner import build_response_plan, realize_plan_classically, validate_plan_response
from app.services.response_semantics import evaluate_candidates


CFG = {"alias_key": "response-plan-tests", "mathematical_profile": "low_resource"}


@pytest.fixture(autouse=True)
def no_large_dmrst(monkeypatch):
    monkeypatch.setattr(dmrst, "parse_dmrst", lambda _: {"status": "unavailable", "reason": "test_stub", "edus": [], "tree": []})


def analyze(text, state=None):
    return analyze_turn(text, state or {}, CFG)[:2]


def test_canonical_correction_plan_and_classical_realization():
    _, state = analyze(
        "I finally got the internship I've been working toward for months. Everyone is congratulating me, "
        "but honestly, I just feel tired. Now I am already thinking about what I need to achieve next."
    )
    _, state = analyze(
        "I don't think the tiredness is from the internship itself. I think I am exhausted by the feeling "
        "that I have to keep proving I am worth the opportunity.",
        state,
    )
    analysis, state = analyze(
        "Actually, I don't think I need to prove that I am worthy. I am excited about the internship. "
        "I am physically exhausted after months of preparation, and I want to enjoy the achievement "
        "without immediately planning the next thing.",
        state,
    )
    plan = build_response_plan(analysis, state["turns"][:-1])
    assert plan["correction_context"]["is_correction"]
    kinds = {claim["kind"] for claim in plan["claims_to_communicate"]}
    assert {"excitement", "physical_exhaustion", "present_enjoyment"} <= kinds
    assert all("prove" not in claim["text"].casefold() for claim in plan["claims_to_communicate"])
    response = realize_plan_classically(plan)
    assert "excited" in response.casefold()
    assert "exhausted" in response.casefold()
    assert "enjoy" in response.casefold()
    assert "prove" not in response.casefold()
    assert validate_plan_response(plan, response)["is_valid"]


def test_structural_validator_reports_coverage_and_rejects_reintroduced_meaning():
    first, state = analyze("I feel pressure to prove I deserve the internship opportunity.")
    analysis, state = analyze(
        "Actually, I don't think I need to prove that I am worthy. I am excited about the internship.", state
    )
    plan = build_response_plan(analysis, state["turns"][:-1])
    missing = validate_plan_response(plan, "You have put this into words.")
    assert missing["is_valid"]
    assert not all(missing["required_claim_coverage"].values())
    reintroduced = validate_plan_response(plan, "You're excited, but you still need to prove your worth.")
    assert not reintroduced["is_valid"]
    assert "reintroduced_rejected_worth_claim" in reintroduced["violations"]


def test_expected_happiness_is_not_misread_as_reported_happiness_and_tentative_is_preserved():
    analysis, _ = analyze(
        "I finally got the internship. I know I should be happy, but I just feel tired. "
        "I am already thinking about what I need to achieve next."
    )
    plan = build_response_plan(analysis)
    kinds = {claim["kind"] for claim in plan["claims_to_communicate"]}
    assert "excitement" not in kinds
    response = realize_plan_classically(plan)
    assert response.startswith("You finally got")
    assert "tired" in response.casefold() and "next goal" in response.casefold()

    tentative, _ = analyze("I think I am exhausted by the pressure to prove my worth.")
    tentative_plan = build_response_plan(tentative)
    invalid = validate_plan_response(tentative_plan, "You're exhausted by pressure to prove your worth.")
    assert any(code.startswith("tentative_claim_unqualified") for code in invalid["violations"])
    assert "sounds like" in realize_plan_classically(tentative_plan).casefold()


def test_missing_local_model_fails_closed_to_grounded_fallback():
    analysis, state = analyze("I am excited about the internship, but I am physically exhausted.")
    plan = build_response_plan(analysis)
    provider = LocalGenerationProvider(Path("Z:/sanctuary-not-a-model"))
    response, diagnostics = provider.generate(plan)
    assert diagnostics["status"] == "fallback"
    assert diagnostics["mode"] == "classical_local_fallback"
    assert "excited" in response.casefold() and "exhausted" in response.casefold()
    assert provider.get_capabilities()["network_access"] is False


def test_generation_prompt_contains_only_bounded_plan_data():
    analysis, _ = analyze("Maybe I am tired because the project deadline changed.")
    plan = build_response_plan(analysis)
    messages = build_generation_messages(plan)
    serialized = str(messages)
    assert "approved_current_meanings" in serialized
    assert "retrieval" not in serialized.casefold()
    assert "full transcript" not in serialized.casefold()
    assert "revision_links" not in serialized


def test_extraction_keeps_validated_text_and_never_rescues_meta_opening():
    raw = "You are tired after working toward this. You want the achievement to settle.\nExplanation: ignored."
    assert extract_reflection(raw) == "You are tired after working toward this. You want the achievement to settle."
    meta = "It sounds like you're looking for a reflection. You are exhausted."
    assert extract_reflection(meta) == meta


@pytest.mark.parametrize(
    "text",
    [
        "I wonder if the group setting matters.",
        "I might be uncomfortable, but I don't yet know why.",
        "I could probably try it for a month.",
        "I haven't decided whether the timing works.",
    ],
)
def test_extended_uncertainty_forms_remain_tentative(text):
    analysis, _ = analyze(text)
    plan = build_response_plan(analysis)
    assert any(claim["epistemic_status"] == "tentative" for claim in plan["claims_to_communicate"])
    response = realize_plan_classically(plan)
    assert validate_plan_response(plan, response)["is_valid"]


def test_validator_rejects_meta_voice_invention_and_negation_reversal():
    analysis, state = analyze("I was annoyed with myself after agreeing to help.")
    corrected, state = analyze(
        "Actually, I wasn't annoyed with my friend. I was frustrated that I hadn't been honest about having other plans.",
        state,
    )
    plan = build_response_plan(corrected, state["turns"][:-1])
    assert plan["correction_context"]["is_correction"]
    reversed_meaning = validate_plan_response(
        plan,
        "You were actually feeling annoyed at your friend for not being honest about their plans.",
    )
    assert not reversed_meaning["is_valid"]
    assert "reintroduced_rejected_claim_without_negation" in reversed_meaning["violations"]

    meta = validate_plan_response(plan, "Here is the revised reflection: I was frustrated about a trip.")
    assert not meta["is_valid"]
    assert "no_generation_meta_preface" in meta["violations"]
    assert "second_person_reflective_voice" in meta["violations"]


def test_classical_realizer_preserves_previous_generic_fallback_cases():
    for text in (
        "Although, I did enjoy telling my closest friend about it yesterday. I wasn't thinking about my next goal then.",
        "That reassured me, but I still want to know whether there are things I should improve.",
        "I think I should say no. Taking on less would probably be sensible.",
        "Yesterday I agreed to something and then felt annoyed with myself because I'd planned to rest.",
        "Can you show me exactly what would be saved before anything is stored?",
    ):
        analysis, _ = analyze(text)
        plan = build_response_plan(analysis)
        response = realize_plan_classically(plan)
        assert response != "There is space for what you have expressed here."
        assert validate_plan_response(plan, response)["is_valid"], (text, response, validate_plan_response(plan, response))


def test_semantic_evaluator_rejects_model_detected_contradiction_without_noun_rules(monkeypatch):
    analysis, _ = analyze("I was frustrated with myself, not my friend.")
    plan = build_response_plan(analysis)

    def fake_request(payload, budget):
        assert payload["task"] == "semantic_validation"
        rows = []
        for pair in payload["pairs"]:
            scores = {"contradiction": 0.91, "entailment": 0.04, "neutral": 0.05}
            rows.append({"id": pair["id"], "purpose": pair["purpose"], "scores": scores})
        return {"status": "ready", "version": "test-nli", "pairs": rows}

    monkeypatch.setattr("app.services.response_semantics.NLI.request", fake_request)
    result = evaluate_candidates(plan, ["You were pleased with someone else."])[0]
    assert not result["is_valid"]
    assert "semantic_grounding_contradiction" in result["violations"]


def test_provider_ranks_all_grounded_candidates_instead_of_returning_first(monkeypatch):
    analysis, _ = analyze("I am excited about the internship, but I am physically exhausted.")
    plan = build_response_plan(analysis)
    scores = iter([0.1, 0.9, 0.3])

    def semantic_evaluator(_plan, candidates, **_):
        return [
            {"status": "ready", "is_valid": True, "score": next(scores), "violations": []}
            for _candidate in candidates
        ]

    provider = LocalGenerationProvider(Path("Z:/unused"), semantic_evaluator=semantic_evaluator)
    monkeypatch.setattr(provider, "initialize", lambda: {"ready": True, "network_access": False})
    drafts = iter([
        "You're excited about the internship, while also feeling physically exhausted.",
        "The internship matters to you, yet your excitement is arriving alongside real physical exhaustion.",
        "You're physically exhausted even with the excitement you feel about the internship.",
    ])
    monkeypatch.setattr(provider, "_candidate", lambda *_args, **_kwargs: (next(drafts), {}))
    response, diagnostics = provider.generate(plan, {"maximum_attempts": 3})
    assert response.startswith("The internship matters")
    assert diagnostics["selected_attempt"] == 2
    assert diagnostics["selection"] == "semantic_grounding_then_comparative_synthesis"


def test_mechanical_second_person_repair_preserves_validator_as_gate():
    repaired = repair_second_person_voice("I'm exhausted by my work, but I told myself I could rest.")
    assert repaired == "You're exhausted by your work, but You told yourself You could rest."
    assert "I" not in repaired


def test_polish_mode_rejects_noop_and_keeps_the_valid_classical_fallback(monkeypatch):
    analysis, _ = analyze("I am excited about the internship, but I am physically exhausted.")
    plan = build_response_plan(analysis)
    fallback = realize_plan_classically(plan)
    provider = LocalGenerationProvider(Path("Z:/unused"), semantic_evaluator=lambda *_args, **_kwargs: [])
    monkeypatch.setattr(provider, "initialize", lambda: {"ready": True, "network_access": False})
    monkeypatch.setattr(provider, "_candidate", lambda *_args, **_kwargs: (fallback, {"raw_draft": fallback, "extracted_draft": fallback}))
    response, diagnostics = provider.generate_polish(plan, {"maximum_attempts": 2})
    assert response == fallback
    assert diagnostics["mode"] == "classical_local_fallback"
    assert all("polish_noop" in row["final_violations"] for row in diagnostics["attempts"])


def test_polish_prompt_contains_only_fallback_and_second_person_claims():
    messages = build_polish_messages("You felt tired.", ["You think the pressure may matter."])
    serialized = str(messages)
    assert "Structured response plan" not in serialized
    assert "memory_context" not in serialized
    assert "You think the pressure" in serialized


def test_few_shot_targets_are_not_eval_achievement_wording():
    assert all("internship" not in target.casefold() and "achievement" not in target.casefold() for target in FEW_SHOT_TARGETS)
