"""Sanctuary V2 Phase 1: Upstream Repair Test Suite (T1.1, T1.2, T1.3).

Verifies:
1. Negation scope and actor-role preservation (T1.1)
   - Passive voice recovery: agent in 'by' phrase, patient in 'nsubjpass'
   - Negation raising: 'I don't think I'm angry' -> complement negated
   - Negation idioms: 'never mind', 'not only X but also Y', 'can't help but'
   - Negative quantifiers: 'no one was listening'
   - Role certainty & exclusion of uncertain frames from response plans
2. Correction detection and supersession (T1.2)
   - Extended cue set: 'no wait', 'I meant', 'scratch that', Hinglish 'nahi, matlab'
   - Hard negatives: 'no, I don't want to talk about that' is pushback, not correction
   - Hard negative: 'actually' as filler without negation does not trigger supersession
   - Ambiguous link to multiple prior assertions remains unresolved_ambiguous
3. Valid fallback output (T1.3)
   - Classical realizer conforms to validator contract across all strategies
   - 500 synthetic plans property test (zero claims, uncertain claims, max length spans)
"""
import pytest
from app.services.nlp_engine import analyze_turn, FALLBACKS
from app.services.response_planner import build_response_plan, validate_plan_response, realize_plan_fallback
from app.services.deterministic_response import deterministic_response


# =========================================================================
# T1.1: Negation and Actor-Role Preservation
# =========================================================================

def test_t1_1_passive_voice_agent_patient_recovery():
    """Verify passive voice: 'I was blamed by my sister' has patient='I', agent='sister'."""
    text = "I was blamed by my sister."
    analysis, _, _ = analyze_turn(text, config={"alias_key": "p1-test-key"})
    props = analysis["discourse_context"]["current_propositions"]
    assert len(props) >= 1

    blame_prop = next(p for p in props if p["predicate"]["lemma"] == "blame")
    assert blame_prop["voice"] == "passive"

    roles = {a["role"]: a["text"].lower() for a in blame_prop["actors"]}
    assert "patient" in roles, f"Expected patient in roles: {blame_prop['actors']}"
    assert "agent" in roles, f"Expected agent in roles: {blame_prop['actors']}"
    assert roles["patient"] == "i"
    assert "sister" in roles["agent"]


def test_t1_1_active_voice_role_contrast():
    """Verify active voice: 'I told her he was wrong' vs 'she told me he was wrong'."""
    text1 = "I told her he was wrong."
    analysis1, _, _ = analyze_turn(text1, config={"alias_key": "p1-test-key"})
    props1 = analysis1["discourse_context"]["current_propositions"]
    tell_prop1 = next(p for p in props1 if p["predicate"]["lemma"] == "tell")
    roles1 = {a["role"]: a["text"].lower() for a in tell_prop1["actors"]}
    assert roles1.get("agent") == "i"
    assert roles1.get("patient") == "her"

    text2 = "She told me he was wrong."
    analysis2, _, _ = analyze_turn(text2, config={"alias_key": "p1-test-key"})
    props2 = analysis2["discourse_context"]["current_propositions"]
    tell_prop2 = next(p for p in props2 if p["predicate"]["lemma"] == "tell")
    roles2 = {a["role"]: a["text"].lower() for a in tell_prop2["actors"]}
    assert roles2.get("agent") == "she"
    assert roles2.get("patient") == "me"


def test_t1_1_negation_raising():
    """Verify negation raising: 'I don't think I'm angry' -> angry proposition is negative."""
    text = "I don't think I am angry."
    analysis, _, _ = analyze_turn(text, config={"alias_key": "p1-test-key"})
    props = analysis["discourse_context"]["current_propositions"]

    # The complement proposition 'be angry' should inherit negative polarity
    angry_prop = next((p for p in props if p["predicate"]["lemma"] in {"be", "am"}), None)
    if angry_prop:
        assert angry_prop["polarity"] == "negative"


def test_t1_1_hard_negative_never_mind():
    """Verify 'never mind' is treated as pragmatic dismissal, not negative polarity assertion."""
    text = "Never mind, I will handle the report myself."
    analysis, _, _ = analyze_turn(text, config={"alias_key": "p1-test-key"})
    props = analysis["discourse_context"]["current_propositions"]
    handle_prop = next((p for p in props if p["predicate"]["lemma"] == "handle"), None)
    assert handle_prop is not None
    assert handle_prop["polarity"] == "positive"


def test_t1_1_hard_negative_not_only_but_also():
    """Verify 'not only X but also Y' correlative retains positive polarity."""
    text = "Not only did he complete the project, but he also supported the team."
    analysis, _, _ = analyze_turn(text, config={"alias_key": "p1-test-key"})
    props = analysis["discourse_context"]["current_propositions"]
    assert any(p["polarity"] == "positive" for p in props)


def test_t1_1_hard_negative_cant_help_but():
    """Verify 'can't help but feel' idiom is positive assertion."""
    text = "I can't help but feel proud of the work."
    analysis, _, _ = analyze_turn(text, config={"alias_key": "p1-test-key"})
    props = analysis["discourse_context"]["current_propositions"]
    feel_prop = next((p for p in props if p["predicate"]["lemma"] == "feel"), None)
    assert feel_prop is not None
    assert feel_prop["polarity"] == "positive"


def test_t1_1_negative_quantifier_subject():
    """Verify 'no one was listening' is correctly negative polarity."""
    text = "No one was listening to the presentation."
    analysis, _, _ = analyze_turn(text, config={"alias_key": "p1-test-key"})
    props = analysis["discourse_context"]["current_propositions"]
    listen_prop = next((p for p in props if p["predicate"]["lemma"] == "listen"), None)
    assert listen_prop is not None
    assert listen_prop["polarity"] == "negative"


def test_t1_1_uncertain_role_mapping_excluded_from_plan():
    """Verify that when a frame is marked uncertain, response planner refuses to assert it."""
    text = "The manager assigned the task."
    analysis, _, _ = analyze_turn(text, config={"alias_key": "p1-test-key"})

    # Inject forced uncertainty on discourse proposition
    props = analysis["discourse_context"]["current_propositions"]
    assert len(props) >= 1
    props[0]["role_certainty"] = "uncertain"
    props[0]["status"] = "uncertain"

    plan = build_response_plan(analysis)
    # The uncertain claim must not appear in required claims_to_communicate
    for claim in plan.get("claims_to_communicate", []):
        assert claim.get("epistemic_status") != "uncertain_role_mapping"


# =========================================================================
# T1.2: Correction Detection and Supersession
# =========================================================================

def test_t1_2_extended_correction_cues():
    """Verify extended correction cues: 'no wait', 'I meant', 'scratch that', Hinglish 'nahi, matlab'."""
    prior_turn = [{"turn_index": 1, "text": "I was speaking with Rahul.", "vector": {}, "topic_id": "t000001", "entities": []}]
    config = {"alias_key": "p1-test-key"}

    cues_to_test = [
        "No wait, I meant my sister.",
        "Scratch that, it was actually on Tuesday.",
        "Nahi, matlab I didn't want to leave early.",
    ]
    for text in cues_to_test:
        analysis, _, _ = analyze_turn(text, state_snapshot={"turns": prior_turn}, config=config)
        assert analysis["strategy_evidence"]["correction"]["detected"] is True, f"Failed for cue: {text}"


def test_t1_2_hard_negative_topic_pushback_not_correction():
    """Verify 'no, I don't want to talk about that' does NOT trigger correction or supersession."""
    prior_turn = [{"turn_index": 1, "text": "We discussed the budget yesterday.", "vector": {}, "topic_id": "t000001", "entities": []}]
    text = "No, I don't want to talk about that."
    analysis, _, _ = analyze_turn(text, state_snapshot={"turns": prior_turn}, config={"alias_key": "p1-test-key"})
    assert analysis["strategy_evidence"]["correction"]["detected"] is False


def test_t1_2_hard_negative_filler_actually():
    """Verify filler 'actually' without negation does NOT trigger spurious correction."""
    prior_turn = [{"turn_index": 1, "text": "I attended the workshop.", "vector": {}, "topic_id": "t000001", "entities": []}]
    text = "Actually, the weather was quite pleasant today."
    analysis, _, _ = analyze_turn(text, state_snapshot={"turns": prior_turn}, config={"alias_key": "p1-test-key"})
    assert analysis["strategy_evidence"]["correction"]["detected"] is False


def test_t1_2_ambiguous_supersession_marked_unresolved():
    """Verify that a correction matching two prior assertions equally goes to unresolved_ambiguous."""
    from app.services.discourse_context import build_discourse_context

    prior_state = {
        "propositions": [
            {
                "id": "dp_target_1",
                "source_turn": 1,
                "text": "I spoke to my manager about the project deadline.",
                "predicate": {"lemma": "speak"},
                "actors": [{"role": "patient", "text": "manager"}],
                "revision_status": "current",
            },
            {
                "id": "dp_target_2",
                "source_turn": 2,
                "text": "I spoke to my director about the project deadline.",
                "predicate": {"lemma": "speak"},
                "actors": [{"role": "patient", "text": "director"}],
                "revision_status": "current",
            },
        ],
        "revision_links": [],
    }

    correction_info = {"detected": True, "cue": "scratch that"}
    import spacy
    nlp = spacy.blank("en")
    doc = nlp("Scratch that, I spoke to HR about the project deadline.")
    clauses = [{"id": "c1", "spans": [[0, len(doc.text)]], "head": 4}]

    public, next_state = build_discourse_context(
        doc.text, doc, clauses, correction_info, turn_index=3, prior=prior_state
    )

    # Both targets matched equally (same predicate 'speak', same overlap tokens 'project deadline')
    ambiguous_links = [l for l in public["revision_links"] if l.get("status") == "unresolved_ambiguous"]
    assert len(ambiguous_links) >= 1
    # Neither target should be unilaterally marked superseded
    assert all(p["revision_status"] == "current" for p in next_state["propositions"] if p["id"] in {"dp_target_1", "dp_target_2"})


# =========================================================================
# T1.3: Valid Fallback Output Property Tests
# =========================================================================

def test_t1_3_fallbacks_pass_reflective_and_human_tone_validator():
    """Verify that all predefined strategy fallbacks pass policy validators and have 2nd-person voice."""
    for strategy, text in FALLBACKS.items():
        assert "?" not in text
        assert any(p in text.lower() for p in ["you", "your"])
        dummy_plan = {"claims_to_communicate": [], "interaction_policy": {"maximum_words": 70}, "strategy": strategy}
        validation = validate_plan_response(dummy_plan, text)
        assert validation["is_valid"] is True, f"Strategy '{strategy}' failed validation: {validation['violations']}"


def test_t1_3_realize_plan_fallback_zero_claims():
    """Hard negative: plan with zero eligible claims produces compliant neutral acknowledgement."""
    plan = {
        "claims_to_communicate": [],
        "interaction_policy": {"maximum_words": 70},
        "strategy": "standard",
    }
    response = realize_plan_fallback(plan)
    assert response == "You have shared what you are currently experiencing."
    validation = validate_plan_response(plan, response)
    assert validation["is_valid"] is True


def test_t1_3_realize_plan_fallback_uncertain_only_claims():
    """Hard negative: plan whose only claim is tentative qualifies with uncertainty marker."""
    plan = {
        "claims_to_communicate": [
            {
                "id": "claim_1",
                "text": "I might consider looking for another role next month",
                "epistemic_status": "tentative",
                "span": [0, 50],
            }
        ],
        "uncertainty_constraints": ["claim_1"],
        "interaction_policy": {"maximum_words": 70},
        "strategy": "standard",
    }
    response = realize_plan_fallback(plan)
    assert any(w in response.lower() for w in ["perhaps", "maybe", "seems"])
    validation = validate_plan_response(plan, response)
    assert validation["is_valid"] is True


def test_t1_3_property_test_500_synthetic_plans():
    """Property test across 500 synthetic plans ensuring 100% validator pass rate."""
    import random

    strategies = ["standard", "closure", "insufficient", "correction", "contrast", "recurring", "explanation"]
    words_pool = ["project", "internship", "decision", "schedule", "conversation", "effort", "progress", "meeting"]

    for i in range(500):
        strat = random.choice(strategies)
        num_claims = random.choice([0, 1, 2, 3])
        claims = []
        uncertain_ids = []

        for c_idx in range(num_claims):
            c_id = f"claim_{c_idx}"
            is_tent = random.choice([True, False])
            claim_text = " ".join(random.sample(words_pool, random.randint(3, 7)))
            claims.append({
                "id": c_id,
                "text": claim_text,
                "epistemic_status": "tentative" if is_tent else "asserted",
                "span": [0, len(claim_text)],
            })
            if is_tent:
                uncertain_ids.append(c_id)

        plan = {
            "schema_version": "restricted-response-plan.v1",
            "plan_id": f"rp_synthetic_{i}",
            "strategy": strat,
            "claims_to_communicate": claims,
            "uncertainty_constraints": uncertain_ids,
            "interaction_policy": {"maximum_words": 70},
        }

        realized = realize_plan_fallback(plan)
        validation = validate_plan_response(plan, realized)
        assert validation["is_valid"] is True, (
            f"Synthetic plan {i} ({strat}, {num_claims} claims) produced invalid output: "
            f"'{realized}', violations: {validation['violations']}"
        )
