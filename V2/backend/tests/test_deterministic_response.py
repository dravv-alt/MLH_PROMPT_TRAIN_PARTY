"""Regression coverage for evidence-bound local response adaptation."""
import pytest

from app.services import dmrst
from app.services.deterministic_response import deterministic_response
from app.services.nlp_engine import analyze_turn
from app.services.response_policy import validate_human_tone, validate_reflective_response


CFG={"alias_key":"deterministic-response-test"}


@pytest.fixture(autouse=True)
def no_large_dmrst(monkeypatch):
    monkeypatch.setattr(
        dmrst,
        "parse_dmrst",
        lambda _:{"status":"unavailable","reason":"test_stub","edus":[],"tree":[]},
    )


def turn(text,state=None):
    analysis,next_state,_=analyze_turn(text,state or {},CFG)
    response=deterministic_response(analysis)
    assert validate_reflective_response(response).is_valid
    assert validate_human_tone(response).is_valid
    return analysis,next_state,response


def test_different_initial_narratives_do_not_collapse_to_one_response():
    achievement,_,achievement_response=turn(
        "I completed the internship application. I want to let the achievement settle for a while."
    )
    conflict,_,conflict_response=turn(
        "The deadline moved again. I feel frustrated that the plan keeps changing."
    )
    assert achievement["strategy"]==conflict["strategy"]=="standard"
    assert achievement_response!=conflict_response
    assert "achievement settle" in achievement_response
    assert "plan keeps changing" in conflict_response


def test_new_context_replaces_the_extractively_grounded_working_interpretation():
    _,state,first=turn("I got the internship. I feel tired after the long application process.")
    analysis,state,second=turn(
        "Actually, the internship itself is exciting. The months of preparation are what exhausted me.",
        state,
    )
    assert first!=second
    assert analysis["strategy"]=="correction"
    assert analysis["working_interpretation"]["source_turn"]==2
    assert analysis["working_interpretation"]["supersedes_turn"]==1
    assert "months of preparation" in second


def test_explicit_correction_does_not_repeat_a_superseded_tentative_explanation():
    _,state,_=turn("I got the internship, but I feel tired and I am already thinking about the next goal.")
    _,state,_=turn(
        "I don't think the tiredness is from the internship. I think I am exhausted by having to prove my worth.",
        state,
    )
    analysis,state,response=turn(
        "Actually, I don't think I need to prove that I am worthy. I am excited about the internship. "
        "I am physically exhausted after months of preparation and want to enjoy the achievement first.",
        state,
    )
    assert analysis["strategy"]=="correction"
    assert analysis["strategy_evidence"]["correction"]["supersedes_turn"]==2
    assert "physically exhausted" in response
    assert "prove my worth" not in response


def test_uncertain_or_missing_evidence_does_not_create_an_interpretation():
    analysis,state,response=turn("Maybe.")
    assert analysis["strategy"]=="insufficient"
    assert analysis["working_interpretation"] is None
    assert state["working_interpretation"] is None
    assert response=="There is space for what you have expressed here."

    _,unrelated_state,_=turn("The office project deadline changed after the meeting.")
    unrelated,_,_=turn("I don't think it will rain during the trip.",unrelated_state)
    assert unrelated["strategy"]!="correction"


def test_later_user_statement_is_not_overridden_by_earlier_history_or_nli():
    _,state,_=turn("I was exhausted after preparing for the internship.")
    analysis,state,response=turn("Actually, I slept well and I feel rested today.",state)
    baseline=response
    analysis["classification"]={
        "status":"ready",
        "suggestions":[{"label":"expressing uncertainty","adjusted_score":0.999}],
    }
    assert deterministic_response(analysis)==baseline
    assert "rested" in baseline
    assert "exhausted" not in baseline
    assert state["working_interpretation"]["source_turn"]==2


@pytest.mark.parametrize(
    "first,revision",
    [
        (
            "Maybe I am afraid around my friends.",
            "You keep making this sound like I'm afraid of something. I haven't said that it's fear.",
        ),
        (
            "I want this kept as a permanent memory.",
            "Looking at it again, I don't want this kept as a permanent memory. I'd rather keep it in my journal.",
        ),
        (
            "Maybe I am not capable enough for the assessment.",
            "That changes how I see it. It feels less like I knew nothing and more like I struggled under time pressure.",
        ),
    ],
)
def test_relational_revision_cues_are_detected(first, revision):
    _, state, _ = turn(first)
    analysis, _, _ = turn(revision, state)
    assert analysis["strategy"] == "correction"


def test_fresh_low_similarity_dont_think_is_not_forced_into_correction():
    _, state, _ = turn("The office project deadline changed after the meeting.")
    analysis, _, _ = turn("I don't think it will rain during the trip.", state)
    assert analysis["strategy"] != "correction"
