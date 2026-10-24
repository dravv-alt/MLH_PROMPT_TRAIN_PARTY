import re

from app.models.schemas import (
    ConstraintField,
    EventStructure,
    InternalReactionDynamics,
    LanguageExpression,
    MeaningMaking,
    NarrativeStructure,
    TemporalPatterning,
)
from app.services.language_field import derive_language_field


class NarrativeEngine:
    def distill_turn(self, stripped_text: str, previous: list[NarrativeStructure] | None = None) -> NarrativeStructure:
        raw_text = " ".join(stripped_text.split())
        text = self._normalize_text(raw_text)
        previous = previous or []

        event = self._extract_event(text)
        constraints = self._extract_constraints(text, event)
        reaction = self._extract_reaction(text)
        meaning = self._extract_meaning(text, constraints)
        temporal = self._extract_temporal(text, previous, event, reaction, meaning)
        language = self._extract_language(raw_text, text)
        confidence_score = self._compute_confidence(text, event, constraints, reaction, meaning, temporal)

        structure = NarrativeStructure(
            event=event,
            constraints=constraints,
            reaction=reaction,
            meaning=meaning,
            temporal=temporal,
            language=language,
            confidence_score=confidence_score,
        )
        return structure

    def _normalize_text(self, text: str) -> str:
        lowered = text.lower()
        lowered = re.sub(r"\s+", " ", lowered)
        return lowered.strip()

    def _extract_event(self, text: str) -> EventStructure:
        rules = {
            "interpersonal_conflict": [
                "fight",
                "argue",
                "argument",
                "conflict",
                "clash",
                "shouting",
                "set a boundary",
                "staying quiet",
                "people will leave me",
            ],
            "loss": ["lost", "loss", "passed away", "grief", "broke up", "breakup"],
            "uncertainty": ["uncertain", "unsure", "don't know", "confused", "maybe", "anxious", "worried"],
            "pressure": [
                "pressure",
                "overwhelmed",
                "deadline",
                "expectation",
                "too much",
                "said yes again",
                "wanted to say no",
                "betrayed myself",
                "freeze",
                "overthink",
            ],
            "disappointment": ["disappointed", "let down", "failed", "failure", "rejected"],
            "transition": [
                "moved",
                "moving",
                "new job",
                "graduated",
                "change",
                "transition",
                "wrote down",
                "practiced",
                "pause here",
                "clearer than",
            ],
            "isolation": ["alone", "lonely", "isolated", "ignored", "left out"],
            "achievement_strain": ["grade", "promotion", "performance", "achievement", "prove myself"],
            "health_concern": ["sick", "ill", "health", "doctor", "pain", "symptom"],
        }
        event_type = self._match_first(rules, text, "other")


        actors: list[str] = ["self"]
        if self._contains_any(text, ["mom", "dad", "parent", "boss", "manager", "teacher", "professor"]):
            actors.append("authority_figure")
        if self._contains_any(text, ["friend", "coworker", "classmate", "roommate", "colleague"]):
            actors.append("peer")
        if self._contains_any(text, ["partner", "boyfriend", "girlfriend", "husband", "wife", "spouse"]):
            actors.append("romantic_partner")
        if self._contains_any(text, ["school", "hospital", "bank", "government", "company", "system"]):
            actors.append("institutional_system")
        actors = list(dict.fromkeys(actors))

        action_taken = self._detect_action_taken(text)
        action_desired = self._detect_action_desired(text, action_taken)
        outcome = self._detect_outcome(text)

        return EventStructure(
            event_type=event_type,
            actors=actors,
            action_taken=action_taken,
            action_desired=action_desired,
            outcome=outcome,
        )

    def _detect_action_taken(self, text: str) -> str:
        compliance = ["said yes", "went along", "gave in", "agreed"]
        refusal = ["said no", "refused", "declined", "set a boundary", "pushed back"]
        avoidance = ["avoided", "ignored", "dodged", "postponed", "put it off"]
        confrontation = ["argued", "fought", "confronted", "yelled", "snapped"]
        withdrawal = ["withdrew", "shut down", "walked away", "left", "went silent"]

        if self._contains_any(text, refusal):
            return "refusal"
        if self._contains_any(text, confrontation):
            return "confrontation"
        if self._contains_any(text, withdrawal):
            return "withdrawal"
        if self._contains_any(text, avoidance):
            return "avoidance"
        if self._contains_any(text, compliance):
            return "compliance"
        return None

    def _detect_action_desired(self, text: str, action_taken: str) -> str:
        if self._contains_any(text, ["wanted to say no", "wish i said no", "wanted to refuse"]):
            return "refusal"
        if self._contains_any(text, ["wanted to avoid", "wish i avoided"]):
            return "avoidance"
        if self._contains_any(text, ["wanted to confront", "wish i confronted"]):
            return "confrontation"
        if self._contains_any(text, ["wanted to leave", "wanted to walk away"]):
            return "withdrawal"
        if self._contains_any(text, ["wanted to agree", "wanted to comply"]):
            return "compliance"
        return None

    def _detect_outcome(self, text: str) -> str:
        if self._contains_any(text, ["relieved", "better", "lighter", "calmer"]):
            return "relief"
        if self._contains_any(text, ["fight", "argue", "shouting", "drama", "tension"]):
            return "external_conflict"
        if self._contains_any(text, ["terrible", "guilt", "hurt", "anxious", "heavy", "upset"]):
            return "internal_distress"
        return "unresolved"

    def _extract_constraints(self, text: str, event: EventStructure) -> ConstraintField:
        from app.services.ssm_constraints import constraint_observations
        values, _ = constraint_observations(text)
        return ConstraintField(**values)

    def _extract_reaction(self, text: str) -> InternalReactionDynamics:
        primary_map = {
            "inhibition": ["froze", "shut down", "went silent"],
            "rumination": ["overthink", "replay", "loop", "can't stop thinking"],
            "anger": ["angry", "furious", "rage", "snapped"],
            "sadness": ["sad", "hurt", "feeling down", "cry"],
            "fear": ["afraid", "scared", "anxious", "panic"],
            "numbness": ["numb", "empty", "detached"],
            "relief": ["relieved", "lighter"],
        }
        # Textual ordering is evidence of mention order, not proof of causality.
        ordered = sorted(
            (min(text.find(token) for token in tokens if self._contains_token(text, token)), label)
            for label, tokens in primary_map.items() if self._contains_any(text, tokens)
        )
        primary_reaction = ordered[0][1] if ordered else 'unknown'
        secondary_reaction = ordered[1][1] if len(ordered) > 1 else None

        effect_map = {
            "guilt": ["guilt", "guilty"],
            "self_disappointment": ["let myself down", "disappointed in myself", "failed myself"],
            "resentment": ["resent", "resentment", "bitter"],
            "anxiety": ["anxious", "panic", "worried"],
            "relief": ["relieved", "lighter", "calm"],
            "shame": ["shame", "ashamed", "embarrassed"],
        }
        after_effects = [key for key, tokens in effect_map.items() if self._contains_any(text, tokens)]
        match = re.search(r"\bintensity\s*[:=]\s*(0(?:\.\d+)?|1(?:\.0+)?)(?![\d.])", text)
        intensity = float(match.group(1)) if match else None
        duration = "unknown"
        if self._contains_any(text, ["still", "again", "keeps", "lingering", "for days"]):
            duration = "lingering"
        if self._contains_any(text, ["always", "for months", "for years", "chronic"]):
            duration = "chronic"

        return InternalReactionDynamics(
            primary_reaction=primary_reaction,
            secondary_reaction=secondary_reaction,
            after_effects=after_effects,
            intensity=intensity,
            duration=duration,
        )

    def _extract_meaning(self, text: str, constraints: ConstraintField) -> MeaningMaking:
        if self._contains_any(text, ["should have", "let myself down", "failed", "my fault"]):
            self_interpretation = "I_should_have_done_better"
        elif self._contains_any(text, ["unfair", "wrong of them", "they were wrong"]):
            self_interpretation = "they_were_unfair"
        elif self._contains_any(text, ["it is what it is", "just how it is"]):
            self_interpretation = "this_is_just_how_it_is"
        elif self._contains_any(text, ["no choice", "had to", "couldn't"]):
            self_interpretation = "I_had_no_choice"
        else:
            self_interpretation = "I_made_the_right_call" if self._contains_any(text, ["made the right call", "made the right choice"]) else "unknown"

        perceived_failure = True if self._contains_any(text, ["failed", "messed up", "let myself down", "my fault"]) else None

        if self._contains_any(text, ["not good enough", "incompetent", "failed"]):
            identity_threat = "competence"
        elif self._contains_any(text, ["bad person", "i was wrong", "i am selfish", "i'm selfish"]):
            identity_threat = "moral_standing"
        elif self._contains_any(text, ["alone", "excluded", "left out", "rejected"]):
            identity_threat = "belonging"
        elif self._contains_any(text, ["trapped", "no control", "can't choose"]):
            identity_threat = "autonomy"
        else:
            identity_threat = "unknown"

        if self._contains_any(text, ["no choice", "had to", "forced"]):
            control_belief = "had_no_choice"
        elif self._contains_any(text, ["had a choice", "could have refused"]) and perceived_failure:
            control_belief = "had_choice_but_failed"
        else:
            control_belief = "unclear"

        if self._contains_any(text, ["my fault", "i caused", "i ruined"]):
            fairness_evaluation = "self_blame"
        elif self._contains_any(text, ["unfair", "their fault", "they caused"]):
            fairness_evaluation = "external_blame"
        elif self._contains_any(text, ["both", "we both", "shared"]):
            fairness_evaluation = "shared"
        else:
            fairness_evaluation = "unclear"

        return MeaningMaking(
            self_interpretation=self_interpretation,
            perceived_failure=perceived_failure,
            identity_threat=identity_threat,
            control_belief=control_belief,
            fairness_evaluation=fairness_evaluation,
        )

    def _extract_temporal(
        self,
        text: str,
        previous: list[NarrativeStructure],
        event: EventStructure,
        reaction: InternalReactionDynamics,
        meaning: MeaningMaking,
    ) -> TemporalPatterning:
        signature_tail = reaction.after_effects[0] if reaction.after_effects else reaction.primary_reaction
        pattern_signature = f"{event.event_type} -> {event.action_taken} -> {signature_tail}"

        previous_signatures = [item.temporal.pattern_signature for item in previous]
        complete = event.event_type != 'other' and event.action_taken is not None and signature_tail != 'unknown'
        is_recurring = (complete and pattern_signature in previous_signatures) or self._contains_any(text, ["keeps happening", "this happened again"])

        progression = "unknown"
        if previous and reaction.intensity is not None and previous[-1].reaction.intensity is not None and previous[-1].temporal.pattern_signature == pattern_signature:
            progression = "stable"
            last_intensity = previous[-1].reaction.intensity
            if reaction.intensity - last_intensity > 0.08:
                progression = "worsening"
            elif reaction.intensity - last_intensity < -0.08:
                progression = "improving"

        last_resolution = previous[-1].temporal.resolution_state if previous else "unresolved"
        if last_resolution in {"integrated", "partial_resolution"} and self._contains_any(text, ["again", "back here", "still happening"]):
            resolution_state = "reopened"
        elif self._contains_any(text, ["i realize", "it means", "i understand", "makes sense", "this feels clearer"]):
            resolution_state = "emerging_clarity"
        elif self._contains_any(text, ["i decided", "i can", "boundary", "moving forward", "i did set"]):
            resolution_state = "partial_resolution"
        elif self._contains_any(text, ["thank you", "we can pause", "pause here", "i feel better", "lighter now"]):
            resolution_state = "integrated" if last_resolution in {"emerging_clarity", "partial_resolution"} else "partial_resolution"
        else:
            resolution_state = "unresolved"

        return TemporalPatterning(
            is_recurring=is_recurring,
            pattern_signature=pattern_signature,
            progression=progression,
            resolution_state=resolution_state,
        )

    def _extract_language(self, raw_text: str, text: str) -> LanguageExpression:
        if self._contains_any(text, ["let myself down", "my fault", "should have", "i messed up"]):
            tone = "self-critical"
        elif self._contains_any(text, ["overwhelmed", "too much", "can't handle", "terrible"]):
            tone = "overwhelmed"
        elif self._contains_any(text, ["whatever", "it is what it is", "pointless"]):
            tone = "resigned"
        elif self._contains_any(text, ["hopeful", "better", "lighter", "moving forward"]):
            tone = "hopeful"
        elif self._contains_any(text, ["because", "therefore", "which means", "pattern"]):
            tone = "analytical"
        else:
            tone = "neutral"

        if self._contains_any(text, ["definitely", "always", "never", "certain"]):
            certainty = "high"
        elif self._contains_any(text, ["maybe", "not sure", "perhaps", "i guess"]):
            certainty = "low"
        else:
            certainty = "medium"

        if self._contains_any(text, ["i feel", "i am", "i'm", "it hurts", "i'm anxious"]):
            emotional_directness = "high"
        elif self._contains_any(text, ["kind of", "a bit", "somewhat"]):
            emotional_directness = "medium"
        else:
            emotional_directness = "low"

        key_phrases = []
        for match in re.findall(r"\bI\s+[A-Za-z']+\s+[A-Za-z']+(?:\s+[A-Za-z']+)?", raw_text):
            phrase = match.strip()
            if phrase not in key_phrases:
                key_phrases.append(phrase)
            if len(key_phrases) == 3:
                break

        language_field = derive_language_field(raw_text)

        return LanguageExpression(
            tone=tone,
            certainty=certainty,
            emotional_directness=emotional_directness,
            key_phrases_mirrored=key_phrases,
            language_field=language_field,
        )

    def _compute_confidence(
        self,
        text: str,
        event: EventStructure,
        constraints: ConstraintField,
        reaction: InternalReactionDynamics,
        meaning: MeaningMaking,
        temporal: TemporalPatterning,
    ) -> float:
        score = 0.35
        if event.event_type != "other":
            score += 0.18
        if len(event.actors) > 1:
            score += 0.08
        if reaction.secondary_reaction is not None:
            score += 0.12
        if reaction.intensity is not None and reaction.intensity >= 0.55:
            score += 0.08
        if meaning.identity_threat not in {"none", "unknown"}:
            score += 0.06
        if temporal.is_recurring:
            score += 0.05
        if temporal.resolution_state != "unresolved":
            score += 0.02
        if event.action_taken != event.action_desired:
            score += 0.07
        if meaning.perceived_failure:
            score += 0.04
        if (constraints.expectation_pressure or 0) > 0.65 or (constraints.power_asymmetry or 0) > 0.65:
            score += 0.02
        if len(text.split()) > 10:
            score += 0.05

        return round(min(score, 0.95), 2)

    def _token_hits(self, text: str, tokens: list[str]) -> int:
        return sum(1 for token in tokens if self._contains_token(text, token))

    def _clamp(self, value: float, low: float = 0.0, high: float = 1.0) -> float:
        return round(max(low, min(high, value)), 2)

    def _match_first(self, rules: dict[str, list[str]], text: str, default: str) -> str:
        for value, keywords in rules.items():
            if self._contains_any(text, keywords):
                return value
        return default

    def _contains_any(self, text: str, tokens: list[str]) -> bool:
        return any(self._contains_token(text, token) for token in tokens)

    def _contains_token(self, text: str, token: str) -> bool:
        escaped = re.escape(token.lower())
        for match in re.finditer(rf"(?<!\w){escaped}(?!\w)", text):
            prefix = re.split(r'[.!?;,]', text[:match.start()])[-1]
            if re.search(r"(?:\bnot|\bnever|n't|\bno longer)\s+(?:\w+\s+){0,2}$", prefix):
                continue
            return True
        return False
