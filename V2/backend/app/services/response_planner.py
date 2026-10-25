"""Evidence-bound response planning and local classical realization.

The plan is the authority boundary between NLP/state analysis and language
generation.  A generator may reword approved claims, but it may not promote
retrieval candidates or superseded propositions into current facts.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from app.services.response_policy import validate_human_tone, validate_reflective_response


VERSION = "sanctuary.response-plan.v2"

UNCERTAINTY_RE = re.compile(
    r"\b(?:maybe|perhaps|probably|possibly|might|may|could|i\s+(?:think|guess|suppose|wonder)|"
    r"not\s+sure|uncertain|haven't\s+decided|have\s+not\s+decided|don't\s+(?:know|yet\s+know)|"
    r"do\s+not\s+(?:know|yet\s+know))\b",
    re.I,
)
UNCERTAINTY_OUTPUT_RE = re.compile(
    r"\b(?:maybe|perhaps|probably|possibly|seems?|sounds?\s+like|might|may|could|wonder|guess|"
    r"not\s+sure|uncertain|haven't\s+decided|have\s+not\s+decided|don't\s+know|do\s+not\s+know)\b",
    re.I,
)
META_OUTPUT_RE = re.compile(
    r"(?:^|\n)\s*(?:here\s+is\s+(?:the\s+)?(?:revised\s+)?reflection|"
    r"i\s+will\s+provide\b|approved\s+current\s+meanings?\b|"
    r"it\s+sounds\s+like\s+you(?:'re|\s+are)\s+looking\s+for\b|"
    r"you(?:'re|\s+are)\s+looking\s+for\b|note\s*:|[-*]\s+)",
    re.I,
)

KIND_PATTERNS: tuple[tuple[str, str], ...] = (
    ("physical_exhaustion", r"\b(?:physically exhausted|exhausted|tired|fatigued|drained)\b"),
    ("excitement", r"\b(?:excited|happy|thrilled|looking forward)\b"),
    ("present_enjoyment", r"\b(?:enjoy|savou?r|appreciate|take in|let .* sink in).*(?:achievement|moment|this|it)\b"),
    ("next_orientation", r"\b(?:thinking about|planning|moving (?:on|ahead)|achieve).*(?:next|another goal)\b"),
    ("worth_pressure", r"\b(?:prove|worthy|worth the opportunity|deserve)\b"),
    ("intention", r"\b(?:i want|i intend|i plan|i will|i'd like)\b"),
    ("achievement", r"\b(?:got|earned|completed|finished|achievement|internship|promotion|graduated)\b"),
    ("uncertainty", r"\b(?:maybe|perhaps|possibly|not sure|i think|i guess|i suppose)\b"),
)

NEGATED_CORRECTION_RE = re.compile(
    r"\b(?:actually\s*,?\s*)?i\s+(?:(?:do\s+not|don't|did\s+not|didn't)\s+(?:think|feel|believe|need)|"
    r"(?:am\s+not|was\s+not|wasn't|have\s+not|haven't)\b)",
    re.I,
)


def _kind(text: str) -> str:
    lowered = text.casefold()
    if re.search(r"\b(?:should|supposed to|expected to)\s+(?:be|feel)\s+(?:happy|excited|thrilled)\b", lowered):
        return "expected_emotion"
    return next((name for name, pattern in KIND_PATTERNS if re.search(pattern, lowered)), "user_statement")


def _sentences(text: str) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for match in re.finditer(r"[^.!?]+[.!?]?", text):
        start, end = match.span()
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        value = text[start:end].strip()
        if value:
            values.append({"text": value, "span": [start, end]})
    return values


def _claim_units(text: str) -> list[dict[str, Any]]:
    """Split only explicit first-person coordination while preserving offsets."""
    units: list[dict[str, Any]] = []
    for sentence in _sentences(text):
        value = sentence["text"]
        base = sentence["span"][0]
        cursor = 0
        boundaries = list(re.finditer(r",?\s+(?:and|but)\s+(?=I\b)", value, re.I))
        for boundary in boundaries:
            segment = value[cursor:boundary.start()].strip()
            if segment:
                relative = value.find(segment, cursor, boundary.start())
                units.append({"text": segment, "span": [base + relative, base + relative + len(segment)]})
            cursor = boundary.end()
        segment = value[cursor:].strip()
        if segment:
            relative = value.find(segment, cursor)
            units.append({"text": segment, "span": [base + relative, base + relative + len(segment)]})
    return units


def _claim_priority(claim: dict[str, Any]) -> tuple[int, int]:
    priority = {
        "excitement": 0,
        "physical_exhaustion": 1,
        "present_enjoyment": 2,
        "next_orientation": 3,
        "intention": 4,
        "worth_pressure": 5,
        "achievement": 6,
        "uncertainty": 7,
        "expected_emotion": 8,
        "user_statement": 9,
    }
    return priority.get(claim["kind"], 9), claim["span"][0]


def _clause_text(text: str, clause: dict[str, Any]) -> str:
    """Reconstruct a clause from its canonical ordered span list."""
    values = [text[start:end].strip() for start, end in clause.get("spans", []) if 0 <= start < end <= len(text)]
    return " ".join(value for value in values if value)


def build_response_plan(
    analysis: dict[str, Any],
    prior_turns: list[dict[str, Any]] | None = None,
    *,
    state_revision: int | None = None,
    casual_mode: bool = False,
    include_historical_context: bool = True,
) -> dict[str, Any]:
    """Build a deterministic, serializable plan from current committed evidence."""
    text = analysis.get("redacted_text", "").strip()
    strategy = analysis.get("strategy", "standard")
    turn_index = len(prior_turns or []) + 1
    revision = turn_index - 1 if state_revision is None else int(state_revision)
    claims: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    discourse = analysis.get("discourse_context", {})
    uncertain_spans = []
    for prop in discourse.get("current_propositions", []):
        if prop.get("role_certainty") == "uncertain" or prop.get("status") == "uncertain":
            uncertain_spans.extend(prop.get("scope_spans", []))

    for index, sentence in enumerate(_claim_units(text), start=1):
        value = sentence["text"]
        c_span = sentence["span"]
        claim = {
            "id": f"claim_{index}",
            "text": value,
            "span": c_span,
            "kind": _kind(value),
            "provenance": "direct_user_statement",
            "epistemic_status": "tentative" if UNCERTAINTY_RE.search(value) else "asserted",
            "required": True,
        }

        # Exclude claims with uncertain role mapping
        overlaps_uncertain = any(
            max(c_span[0], u_span[0]) < min(c_span[1], u_span[1])
            for u_span in uncertain_spans
        )

        if overlaps_uncertain:
            claim["epistemic_status"] = "uncertain_role_mapping"
            claim["required"] = False
            rejected.append(claim)
        elif analysis.get("strategy_evidence", {}).get("correction", {}).get("detected") and NEGATED_CORRECTION_RE.search(value):
            claim["epistemic_status"] = "rejected_by_user"
            claim["required"] = False
            rejected.append(claim)
        else:
            claims.append(claim)

    # Keep the plan bounded while preferring explicit reactions, explanations,
    # and intentions.  Text order is restored after selection.
    selected = sorted(sorted(claims, key=_claim_priority)[:3], key=lambda item: item["span"][0])
    if not selected and claims:
        selected = [claims[-1]]

    ledger = analysis.get("mathematical_models", {}).get("evidence_belief_revision", {})
    superseded = [
        {"id": row.get("id"), "text": row.get("claim", ""), "kind": row.get("type", "user_statement")}
        for row in ledger.get("propositions", [])
        if row.get("status") in {"superseded", "disputed"}
    ]
    packet = analysis.get("context_packet", {})
    trace = packet.get("retrieval_trace", {})
    canonical_superseded_ids = set(trace.get("excluded_superseded_ids", []))
    for item in packet.get("corrections_and_supersessions", []):
        if item.get("type") == "supersedes" and item.get("target"):
            canonical_superseded_ids.add(item["target"])
    # Historical evidence is already eligibility-filtered by the memory
    # harness. Provider opt-out is enforced by omitting it from the plan, not
    # by trusting the generator to ignore a field.
    historical_context = []
    if include_historical_context:
        superseded.extend({
            "id": row.get("assertion_id"), "text": row.get("text", ""), "kind": "canonical_assertion"
        } for row in packet.get("superseded_evidence", []) if row.get("text"))
        historical_context = [
            {
                "assertion_id": row.get("assertion_id"),
                "text": row.get("text", ""),
                "source_turn_index": row.get("source_turn_index"),
                "revision_status": row.get("revision_status"),
                "epistemic_status": row.get("epistemic_status"),
                "selection_routes": row.get("selection_routes", []),
                "evidence_refs": row.get("evidence_refs", []),
            }
            for row in packet.get("relevant_prior_evidence", [])[:4]
            if row.get("revision_status") == "active" and row.get("text")
        ]
    prohibited = [
        "Do not diagnose, advise, ask a question, minimize, or invent a cause.",
        "Do not turn a temporary experience into a permanent identity claim.",
        "Do not present retrieval, NLI, filter, or graph scores as facts.",
    ]
    prohibited.extend(f"Do not reassert as current: {row['text']}" for row in superseded[-4:] if row["text"])
    prohibited.extend(f"Do not reverse this explicit rejection: {row['text']}" for row in rejected)
    if canonical_superseded_ids:
        prohibited.append(
            "Do not revive canonical assertions excluded by revision status: "
            + ", ".join(sorted(canonical_superseded_ids))
        )

    clause_text = {row.get("id"): _clause_text(text, row) for row in analysis.get("clauses", [])}
    relation_evidence = []
    for edge in analysis.get("relations", []):
        relation_evidence.append({
            "relation": edge.get("relation"),
            "cue": edge.get("cue"),
            "arg1": clause_text.get(edge.get("arg1"), ""),
            "arg2": clause_text.get(edge.get("arg2"), ""),
            "semantic_source": clause_text.get(edge.get("source"), ""),
            "semantic_target": clause_text.get(edge.get("target"), ""),
            "symmetric": bool(edge.get("symmetric")),
            "origin": "explicit_connective",
        })
    discourse = analysis.get("discourse_context", {})
    proposition_frames = [
        {
            "id": row.get("id"),
            "predicate": row.get("predicate", {}).get("lemma"),
            "actors": [{"role": actor.get("role"), "text": actor.get("text")} for actor in row.get("actors", [])],
            "polarity": row.get("polarity"),
            "voice": row.get("voice", "active"),
            "role_certainty": row.get("role_certainty", "certain"),
            "modality": [item.get("category") for item in row.get("modality", [])],
            "status": row.get("status"),
            "scope_spans": row.get("scope_spans", []),
        }
        for row in discourse.get("current_propositions", [])
    ]

    fingerprint = "|".join([str(revision), strategy, *(claim["text"] for claim in selected)])
    plan_id = "rp_" + hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]
    plan = {
        "schema_version": VERSION,
        "plan_id": plan_id,
        "session_id": None,
        "source_turn_id": turn_index,
        "state_revision": revision,
        "intent": "acknowledge_closure" if strategy == "closure" else "reflect_current_meaning",
        "strategy": strategy,
        "claims_to_communicate": selected,
        "evidence_ids": sorted(set(
            ledger.get("current_evidence_ids", [])
            + [evidence_id for row in packet.get("current_turn_evidence", []) for evidence_id in row.get("evidence_refs", [])]
            + [evidence_id for row in historical_context for evidence_id in row.get("evidence_refs", [])]
        )),
        "relevant_proposition_ids": trace.get("selected_assertion_ids", []) or [
            row.get("id") for row in ledger.get("propositions", [])
            if row.get("status") == "explicitly_stated" and row.get("last_turn") == ledger.get("revision")
        ],
        "relevant_graph_node_ids": trace.get("selected_graph_node_ids", []),
        "relevant_graph_edge_ids": trace.get("selected_edge_ids", []),
        "memory_context": {
            "packet_id": packet.get("packet_id"),
            "task": packet.get("task"),
            "historical_evidence": historical_context,
            "corrections_and_supersessions": packet.get("corrections_and_supersessions", []),
            "unresolved_conflicts": packet.get("unresolved_conflicts", []),
            "abstained_from_history": packet.get("abstained_from_history", True),
            "excluded_superseded_ids": sorted(canonical_superseded_ids),
            "memory_generation": packet.get("memory_generation"),
            "state_revision": packet.get("state_revision"),
        },
        "correction_context": {
            "is_correction": bool(rejected or analysis.get("strategy_evidence", {}).get("correction", {}).get("detected")),
            "rejected_current_claims": rejected,
            "superseded_propositions": superseded[-4:],
        },
        "required_semantic_relations": relation_evidence,
        "proposition_frames": proposition_frames,
        "revision_links": discourse.get("revision_links", []),
        "prohibited_claims": prohibited,
        "uncertainty_constraints": [
            claim["id"] for claim in selected if claim["epistemic_status"] == "tentative"
        ],
        "interaction_policy": {
            "questions": False,
            "advice": False,
            "diagnosis": False,
            "maximum_sentences": 2,
            "maximum_words": 70,
        },
        "style_constraints": {
            "tone": "casual and warm" if casual_mode else "clear, warm, and precise",
            "voice": "second_person_reflection",
        },
        "fallback_policy": "local_evidence_bound_classical",
    }
    # Current-session typed structure, never the transient mirrored phrase list.
    if analysis.get('situational_structure'):
        from app.models.schemas import NarrativeStructure
        plan['situational_structure'] = NarrativeStructure.model_validate(analysis['situational_structure']).model_dump()
        plan['ssm_metadata'] = analysis.get('ssm_metadata', {})
    validate_response_plan(plan)
    return plan


def validate_response_plan(plan: dict[str, Any]) -> None:
    required = {
        "schema_version", "plan_id", "source_turn_id", "state_revision", "intent",
        "claims_to_communicate", "correction_context", "prohibited_claims",
        "interaction_policy", "style_constraints", "fallback_policy",
    }
    missing = sorted(required - set(plan))
    if missing:
        raise ValueError(f"response plan missing fields: {', '.join(missing)}")
    for claim in plan["claims_to_communicate"]:
        if claim.get("provenance") != "direct_user_statement" or not claim.get("text"):
            raise ValueError("response plan contains an ungrounded claim")
        span = claim.get("span")
        if not isinstance(span, list) or len(span) != 2 or span[0] < 0 or span[1] <= span[0]:
            raise ValueError("response plan contains an invalid evidence span")


def _second_person(value: str) -> str:
    text = value.strip().rstrip(".!?")
    text = re.sub(r"^(?:actually|honestly|but honestly|now)\s*,?\s*", "", text, flags=re.I)
    replacements = (
        (r"^I\s+want\s+to\b", "You'd like to"),
        (r"^I\s+would\s+like\s+to\b", "You'd like to"),
        (r"^I\s+finally\s+got\b", "You finally got"),
        (r"^I\s+just\s+feel\b", "You feel"),
        (r"^I(?:'m|\s+am)\b", "You're"),
        (r"^I\s+feel\b", "You feel"),
        (r"^I(?:'ve|\s+have)\b", "You've"),
        (r"^I\s+got\b", "You got"),
        (r"^I\s+completed\b", "You completed"),
        (r"^I\s+think\b", "It sounds like"),
    )
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, count=1, flags=re.I)
    text = re.sub(r"\bI\s+am\b", "you're", text, flags=re.I)
    text = re.sub(r"\bI'm\b", "you're", text, flags=re.I)
    text = re.sub(r"\bI\b", "you", text)
    text = re.sub(r"\bme\b", "you", text, flags=re.I)
    text = re.sub(r"\bmy\b", "your", text, flags=re.I)
    text = re.sub(
        r"^It sounds like you should\s+(.+)$",
        r"It sounds like your preference is to \1",
        text,
        flags=re.I,
    )
    text = re.sub(r"\byou\s+wasn't\b", "you weren't", text, flags=re.I)
    text = re.sub(r"\byou\s+was\b", "you were", text, flags=re.I)
    if re.search(r"\bwant\s+to\s+know\s+whether\b", text, re.I):
        text = re.sub(r"\bwant\s+to\s+know\s+whether\b", "want clarity about whether", text, flags=re.I)
        text = re.sub(r"\byou\s+should\b", "you could", text, flags=re.I)
    text = re.sub(r"\bwhat you need to achieve next\b", "the next goal", text, flags=re.I)
    return text[:1].upper() + text[1:] if text else text


def _safe_reflection(value: str) -> str:
    """Convert requests/questions into a statement without inventing content."""
    text = value.strip().rstrip(".!?")
    text = re.sub(r"\[PERSON(?:_\d+)?\]", "someone", text, flags=re.I)
    text = re.sub(r"\[ORG(?:_\d+)?\]", "an organization", text, flags=re.I)
    text = re.sub(r"\[(?:GPE|LOC|FAC)(?:_\d+)?\]", "a place", text, flags=re.I)
    text = re.sub(r"\[[A-Z]+(?:_\d+)?\]", "something", text, flags=re.I)
    text = re.sub(r"\[ENTITY_[A-Z0-9_]+\]", "a time", text, flags=re.I)
    text = re.sub(r"^(?:okay|actually|honestly)\s*,?\s*", "", text, flags=re.I)
    request = re.match(r"can\s+you\s+show\s+me\s+(.+)", text, re.I)
    if request:
        return "You want to see " + request.group(1)
    request = re.match(r"(?:please\s+)?don't\s+include\s+(.+)", text, re.I)
    if request:
        return "You don't want " + request.group(1) + " included"
    request = re.match(r"save\s+(.+)", text, re.I)
    if request:
        return "You want " + request.group(1) + " saved"
    return _second_person(text)


def realize_plan_classically(plan: dict[str, Any]) -> str:
    """Natural local fallback that realizes only approved current-turn claims."""
    claims = plan.get("claims_to_communicate", [])
    if plan.get("intent") == "acknowledge_closure":
        return "We can leave it here for now."
    if not claims:
        return "There is space for what you have expressed here."
    parts = [_safe_reflection(claim["text"]) for claim in claims if claim.get("text")]
    if len(parts) == 1:
        response = parts[0].rstrip(".") + "."
    elif len(parts) == 2:
        response = parts[0].rstrip(".") + ", and " + parts[1][:1].lower() + parts[1][1:].rstrip(".") + "."
    else:
        response = parts[0].rstrip(".") + ", and " + parts[1][:1].lower() + parts[1][1:].rstrip(".") + ". " + parts[2].rstrip(".") + "."
    if len(response.split()) > plan.get("interaction_policy", {}).get("maximum_words", 70):
        response = " ".join(response.split()[:70]).rstrip(" ,;:") + "."
    # Never erase supported content merely because the first rendering is
    # stylistically imperfect. The independent plan validator remains the
    # final authority and the local provider records its result.
    return response


def validate_plan_response(plan: dict[str, Any], response: str) -> dict[str, Any]:
    """Independent hard checks; scores are diagnostics, never truth estimates."""
    violations = [
        *validate_reflective_response(response).violations,
        *validate_human_tone(response).violations,
    ]
    if len(response.split()) > plan.get("interaction_policy", {}).get("maximum_words", 70):
        violations.append("maximum_words")
    lowered = response.casefold()
    if META_OUTPUT_RE.search(response):
        violations.append("no_generation_meta_preface")
    if plan.get("claims_to_communicate") and not re.search(r"\b(?:you|your|you're|you've|you'd)\b", lowered):
        violations.append("second_person_reflective_voice")
    coverage: dict[str, bool] = {}
    semantic_patterns = {
        "physical_exhaustion": r"\b(?:exhausted|exhaustion|tired|fatigued|drained)\b",
        "excitement": r"\b(?:excited|excitement|happy|thrilled|looking forward)\b",
        "present_enjoyment": r"\b(?:enjoy|savou?r|appreciate|take in|sink in)\b",
        "worth_pressure": r"\b(?:prove|worthy|worth|deserve)\b",
        "achievement": r"\b(?:achievement|internship|completed|earned|accomplishment)\b",
        "intention": r"\b(?:want|would like|you'd like|plan|intend)\b",
        "next_orientation": r"\b(?:next|another goal|moving (?:on|ahead)|planning|thinking about)\b",
        "uncertainty": r"\b(?:maybe|perhaps|seems|sounds like|might|uncertain)\b",
    }
    for claim in plan.get("claims_to_communicate", []):
        kind = claim.get("kind", "user_statement")
        if kind in semantic_patterns:
            present = bool(re.search(semantic_patterns[kind], lowered, re.I))
        else:
            tokens = {token for token in re.findall(r"[a-z]+", claim.get("text", "").casefold()) if len(token) > 3}
            present = bool(tokens & set(re.findall(r"[a-z]+", lowered)))
        coverage[claim["id"]] = present
        if claim.get("epistemic_status") == "tentative" and not UNCERTAINTY_OUTPUT_RE.search(lowered):
            violations.append(f"tentative_claim_unqualified:{claim['id']}")
    for rejected in plan.get("correction_context", {}).get("rejected_current_claims", []):
        if rejected.get("kind") == "worth_pressure" and re.search(r"\b(?:need|have) to prove\b.*\b(?:worth|worthy|deserve)\b", lowered):
            violations.append("reintroduced_rejected_worth_claim")
        rejected_tokens = {
            token for token in re.findall(r"[a-z]+", rejected.get("text", "").casefold())
            if len(token) > 3 and token not in {
                "actually", "with", "that", "this", "have", "been", "were", "wasn", "didn", "don", "haven",
            }
        }
        overlap = rejected_tokens.intersection(re.findall(r"[a-z]+", lowered))
        rejected_text = rejected.get("text", "")
        rejected_had_negation = "n't" in rejected_text.casefold() or bool(
            re.search(r"\b(?:not|never|less)\b", rejected_text, re.I)
        )
        if rejected_had_negation and len(overlap) >= 2:
            anchors = [token for token in rejected_tokens if token in lowered]
            for anchor in anchors:
                location = lowered.find(anchor)
                local_prefix = lowered[max(0, location - 28):location]
                if not re.search(r"(?:\bnot\b|n't|\bnever\b|\bless\b)", local_prefix, re.I):
                    violations.append("reintroduced_rejected_claim_without_negation")
                    break
    pattern_details: dict[str, str] = {
        "second_person_reflective_voice": r"\\b(?:you|your|you're|you've|you'd)\\b",
        "no_generation_meta_preface": META_OUTPUT_RE.pattern,
        "sentence_count_1_to_2": "1 <= sentence_count <= 2",
        "maximum_words": f"word_count <= {plan.get('interaction_policy', {}).get('maximum_words', 70)}",
    }
    for violation in violations:
        if violation.startswith("tentative_claim_unqualified:"):
            pattern_details[violation] = UNCERTAINTY_OUTPUT_RE.pattern
    return {
        "is_valid": not violations,
        "violations": sorted(set(violations)),
        "failure_patterns": {key: pattern_details[key] for key in sorted(set(violations)) if key in pattern_details},
        "required_claim_coverage": coverage,
    }


def realize_plan_fallback(plan: dict[str, Any]) -> str:
    """Generate a guaranteed compliant fallback response matching the validator contract."""
    strategy = plan.get("strategy", "standard")
    claims = plan.get("claims_to_communicate", [])
    uncertainty_ids = set(plan.get("uncertainty_constraints", []))

    # Check if ANY claim in plan is tentative or constrained by uncertainty
    has_any_tentative = any(
        c.get("epistemic_status") == "tentative" or c.get("id") in uncertainty_ids
        for c in claims
    )

    # Check for closure strategy
    if strategy == "closure":
        if has_any_tentative:
            return "Perhaps you have reached a place to pause for now."
        return "You have reached a place to pause for now."

    eligible_claims = [c for c in claims if c.get("epistemic_status") != "rejected_by_user"]
    if not eligible_claims:
        if has_any_tentative:
            return "Perhaps you are reflecting on what you just shared."
        return "You have shared what you are currently experiencing."

    target_claim = eligible_claims[0]
    raw_text = target_claim.get("text", "").strip(".!? ")
    words = raw_text.split()
    if len(words) > 18:
        raw_text = " ".join(words[:16])

    if has_any_tentative:
        candidate = f"Perhaps you are considering that {raw_text}."
    else:
        candidate = f"You noted that {raw_text}."

    validation = validate_plan_response(plan, candidate)
    if validation["is_valid"]:
        return candidate

    # Fail closed with safe verified second-person reflection
    if has_any_tentative:
        return "Perhaps you are reflecting on what you just shared."
    return "You have shared what you are currently experiencing."
