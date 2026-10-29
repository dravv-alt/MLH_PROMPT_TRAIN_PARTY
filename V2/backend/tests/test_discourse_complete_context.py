"""Verification tests for multi-turn rolling memory, QUD, and memory context wiring to model APIs."""
from typing import Any, Dict, List
import pytest

from app.services.discourse_generator import (
    build_discourse_plan,
    build_discourse_system_prompt,
    build_discourse_chat_messages,
)
from app.services.hosted_generation import generate_hosted_discourse


def test_build_discourse_plan_packs_complete_context():
    """Verify that build_discourse_plan packages rolling history, QUD stack, and memory."""
    prior_turns = [
        {
            "turn_index": 1,
            "user_text": "I've been preparing for this internship for months.",
            "response_text": "Months of preparing for the internship. What was that preparation like?",
            "system_move": "ask",
            "selected_question": "What was that preparation like?",
        },
        {
            "turn_index": 2,
            "user_text": "It was exhausting, but I finally got accepted today.",
            "response_text": "Exhausting work, and you got accepted today. Space is here.",
            "system_move": "acknowledge",
            "selected_question": None,
        },
    ]

    analysis = {
        "clauses": [{"text": "Now I just feel tired"}],
        "context_packet": {
            "relevant_prior_evidence": [
                {"text": "Preparing for internship for months"},
                {"text": "Accepted to the internship today"},
            ],
            "superseded_evidence": [
                {"text": "User doubted their qualifications"},
            ],
            "current_turn_evidence": [
                {"text": "Feeling tired after acceptance"},
            ],
        },
        "response_plan": {
            "correction_context": {
                "superseded_propositions": [{"text": "doubted qualifications"}],
            }
        },
    }

    pipeline_res = {
        "move": "ask",
        "selected_question": "What is that tiredness like right now?",
        "targeted_gap_id": "gap_unfilled_role_tired_1",
        "gaps": [
            {
                "gap_id": "gap_unfilled_role_tired_1",
                "type": "unfilled_role",
                "spans": [[0, 21]],
            }
        ],
        "qud_stack": [
            {
                "gap_id": "gap_unfilled_role_tired_1",
                "neutral_question_form": "What is that tiredness like right now?",
                "status": "open",
                "recurrence_count": 1,
            },
            {
                "gap_id": "gap_resolved_earlier",
                "neutral_question_form": "What was that preparation like?",
                "status": "answered",
            },
        ],
        "question_trace": {
            "gap_id": "gap_unfilled_role_tired_1",
        },
    }

    current_text = "Now I just feel tired."
    plan = build_discourse_plan(
        analysis=analysis,
        pipeline_res=pipeline_res,
        prior_turns=prior_turns,
        current_text=current_text,
    )

    # Verify rolling history
    assert len(plan["rolling_history"]) == 2
    assert "preparing for this internship" in plan["rolling_history"][0]["user"]
    assert "What was that preparation like?" in plan["rolling_history"][0]["assistant"]
    assert "exhausting" in plan["rolling_history"][1]["user"]

    # Verify QUD stack
    assert len(plan["active_quds"]) == 1
    assert plan["active_quds"][0]["gap_id"] == "gap_unfilled_role_tired_1"
    assert len(plan["resolved_quds"]) >= 1

    # Verify narrative memory
    assert len(plan["relevant_memory"]) == 2
    assert "Preparing for internship for months" in plan["relevant_memory"]
    assert len(plan["superseded_memory"]) >= 1
    assert "User doubted their qualifications" in plan["superseded_memory"]

    # Verify system prompt construction
    sys_prompt = build_discourse_system_prompt(plan)
    assert "Sanctuary's discourse realizer" in sys_prompt
    assert "Active Open Questions Under Discussion" in sys_prompt
    assert "What is that tiredness like right now?" in sys_prompt
    assert "Retrieved Narrative Memory Context" in sys_prompt
    assert "Preparing for internship for months" in sys_prompt
    assert "Retracted/Superseded Claims" in sys_prompt
    assert "User doubted their qualifications" in sys_prompt

    # Verify multi-turn chat message formatting
    messages = build_discourse_chat_messages(plan, current_text)
    # messages: system, user1, assistant1, user2, assistant2, current_user
    assert len(messages) == 6
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "preparing for this internship" in messages[1]["content"]
    assert messages[2]["role"] == "assistant"
    assert messages[3]["role"] == "user"
    assert messages[4]["role"] == "assistant"
    assert messages[5]["role"] == "user"
    assert messages[5]["content"] == "Now I just feel tired."


def test_multiturn_rolling_memory_in_nlp_service(monkeypatch):
    """Verify that NLPService passes rolling conversation history and QUD across turns."""
    from uuid import uuid4
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.models.db import Base
    from app.models.schemas import ChatRequest
    from app.services.nlp_service import NLPService
    import app.services.discourse_generator as dg

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def foreign_keys(db, _):
        db.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    service = NLPService(sessionmaker(engine, expire_on_commit=False), "test-alias-key")

    monkeypatch.setattr("app.services.dmrst.parse_dmrst", lambda _: {"status": "unavailable", "reason": "test_mock", "edus": [], "tree": []})
    monkeypatch.setattr("app.services.classical_nlp.discourse_entities", lambda *a: ({"hobbs": {"pronouns": []}, "centering": {"trace": []}}, []))

    recorded_plans = []
    original_generate = dg.generate_discourse_reply

    def mock_generate_discourse_reply(plan, current_text, prior_turns, realizer="hosted", hosted_consent=True, generator=None):
        recorded_plans.append(copy.deepcopy(plan))
        return original_generate(plan, current_text, prior_turns, realizer="local_template_fallback", hosted_consent=hosted_consent, generator=generator)

    import copy
    monkeypatch.setattr(dg, "generate_discourse_reply", mock_generate_discourse_reply)

    user_id = f"user_{uuid4().hex[:8]}"

    # Turn 1
    req1 = ChatRequest(message="I've been working on this compiler project for weeks.", realizer="local")
    res1 = service.chat(user_id, req1)
    sid = res1["session_id"]

    assert len(recorded_plans) == 1
    # Turn 1 has 0 prior turns
    assert len(recorded_plans[0]["rolling_history"]) == 0

    # Turn 2
    req2 = ChatRequest(message="And the test suite keeps failing on edge cases.", session_id=sid, realizer="local")
    res2 = service.chat(user_id, req2)

    assert len(recorded_plans) == 2
    # Turn 2 must have 1 prior turn in rolling history
    assert len(recorded_plans[1]["rolling_history"]) == 1
    assert "compiler project" in recorded_plans[1]["rolling_history"][0]["user"]
    assert recorded_plans[1]["rolling_history"][0]["assistant"] != ""

    # Turn 3
    req3 = ChatRequest(message="I managed to fix the parser, but the memory allocator is still stuck.", session_id=sid, realizer="local")
    res3 = service.chat(user_id, req3)

    assert len(recorded_plans) == 3
    # Turn 3 must have 2 prior turns in rolling history
    assert len(recorded_plans[2]["rolling_history"]) == 2
    assert "compiler project" in recorded_plans[2]["rolling_history"][0]["user"]
    assert "failing on edge cases" in recorded_plans[2]["rolling_history"][1]["user"]

    engine.dispose()

