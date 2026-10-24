"""Prompt contracts: no inference, downloads, persistence, or provider calls."""
import json

from app.services.local_generation import build_generation_messages, build_polish_messages
from app.services.hosted_generation import build_hosted_messages
from app.services.reflection_style import REFLECTION_STYLE


def test_every_generation_path_receives_grounded_reflection_guidance():
    plan = {"claims_to_communicate": [], "correction_context": {}}
    for messages in (
        build_generation_messages(plan),
        build_polish_messages("You felt tired.", ["You felt tired."]),
        build_hosted_messages(plan),
    ):
        assert REFLECTION_STYLE in messages[0]["content"]
        assert "rather than restating each clause" in messages[0]["content"]
        assert "negation, correction, and hedge" in messages[0]["content"]
        assert "diagnoses, or questions" in messages[0]["content"]


def test_user_example_is_not_installed_as_a_canned_answer():
    messages = build_polish_messages("You felt tired.", ["You felt tired."])
    assert "cold perimeter" not in str(messages)
    assert "only quiet territory" not in str(messages)


def test_hosted_style_does_not_enable_history_sharing():
    plan = {"claims_to_communicate": [], "memory_context": {"historical_evidence": [
        {"text": "PRIVATE_HISTORY_SENTINEL", "revision_status": "active"}
    ]}}
    messages = build_hosted_messages(plan)
    assert json.loads(messages[-1]["content"])["historical_evidence"] == []
    assert "PRIVATE_HISTORY_SENTINEL" not in str(messages)
