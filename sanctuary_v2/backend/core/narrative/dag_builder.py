"""
DAG Builder — Converts distilled text into NarrativeStructure (11-field JSON + DAG edges).

Implements SSM (Situational Structure Model) layers 1-6.
Phase 1: LLM-based extraction (Groq, with structured output prompt).
Phase 4+: Local trained model when sufficient data exists.

IMPORTANT: The LLM receives distilled text with placeholders.
It returns structured JSON. It never sees raw PII.
"""

import json
import logging
from typing import Optional, Dict, Any, List

import httpx

from sanctuary_v2.backend.core.config import settings
from sanctuary_v2.backend.core.privacy.distiller import PlaceholderMap
from sanctuary_v2.backend.schemas.narrative import NarrativeStructure

logger = logging.getLogger(__name__)


# ── JSON schema description sent to the LLM ─────────────────────────────
_EXTRACTION_SCHEMA = """\
Return a single JSON object with exactly these fields:

{
  "trigger_domain": "work | family | romantic | social | internal | ambiguous",
  "primary_actors": ["PERSON_A", "PERSON_B"],
  "action_taken": "what the user did (distilled) or null",
  "action_desired": "what the user wanted to do or null",
  "outcome": "what happened as a result or null",
  "freedom_to_refuse": 0.0-1.0,
  "conflict_cost": 0.0-1.0,
  "relationship_risk": 0.0-1.0,
  "expectation_pressure": 0.0-1.0,
  "agency_score": 0.0-1.0,
  "social_exposure": 0.0-1.0,
  "primary_emotion_label": "hollow | tense | heavy | numb | tight | expansive | scattered | still",
  "body_location": "where user feels it or null",
  "reaction_pattern": "suppress | express | withdraw | confront | freeze",
  "attributed_cause": "what user believes caused this or null",
  "self_narrative": "how user narrates their role or null",
  "first_occurrence": true/false,
  "pattern_descriptor": "e.g. 'always when X' or null",
  "resolution_tried": "what user attempted or null",
  "resolution_outcome": "whether it worked or null",
  "causal_chain": [{"from": "trigger", "to": "reaction", "type": "causes"}]
}

Rules:
- Use ONLY placeholder IDs for actors (PERSON_A, PERSON_B, LOCATION_X, etc.)
- Use structural, non-diagnostic language for all emotion fields
- FORBIDDEN emotion labels: anxious, depressed, traumatized, dysregulated, triggered
- All float fields must be between 0.0 and 1.0
- Return valid JSON only. No commentary. No markdown fences.\
"""


class DAGBuilder:
    """
    Converts distilled text into NarrativeStructure (11-field JSON + DAG edges).
    Uses Groq for structured extraction when GROQ_API_KEY is available.
    Falls back to minimal structure on parse failure or missing API key.
    """

    SYSTEM_PROMPT = (
        "You are a narrative structure extractor. Extract the structure of the user's "
        "experience into the provided JSON schema. Use ONLY the placeholder IDs provided "
        "(PERSON_A, PERSON_B, etc.) for all people mentioned. Use structural, "
        "non-diagnostic language for all emotion fields. Return valid JSON only. "
        "No commentary. No markdown."
    )

    def __init__(self, api_key: Optional[str] = None, model: str = "llama3-8b-8192"):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def extract(
        self,
        distilled_text: str,
        placeholder_map: PlaceholderMap,
    ) -> NarrativeStructure:
        """
        Sends structured extraction request to Groq.
        Validates response against NarrativeStructure schema.
        Falls back to minimal structure on any failure.
        """
        if not self.api_key:
            logger.info("DAGBuilder: no GROQ_API_KEY, returning minimal structure")
            return self._minimal_structure(placeholder_map)

        try:
            raw_json = await self._call_groq(distilled_text)
            data = json.loads(raw_json)
            data = self._sanitize(data, placeholder_map)
            return NarrativeStructure(**data)
        except Exception as exc:
            logger.warning("DAGBuilder: extraction failed (%s), using fallback", exc)
            return self._minimal_structure(placeholder_map)

    async def _call_groq(self, distilled_text: str) -> str:
        """Sends the extraction prompt to Groq and returns the raw response string."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"{_EXTRACTION_SCHEMA}\n\n"
                    f"Text to extract from:\n{distilled_text}"
                ),
            },
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,     # Low temp for structured output
            "max_tokens": 600,
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                self.base_url, headers=headers, json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if the LLM wraps its output
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)

        return content

    def _sanitize(
        self, data: Dict[str, Any], placeholder_map: PlaceholderMap,
    ) -> Dict[str, Any]:
        """Enforce schema constraints on LLM output."""
        # Ensure actors use placeholder IDs only
        actors = data.get("primary_actors") or []
        sanitized_actors: List[str] = []
        for actor in actors:
            if actor in placeholder_map.reverse_map:
                sanitized_actors.append(placeholder_map.reverse_map[actor])
            else:
                sanitized_actors.append(actor)
        data["primary_actors"] = sanitized_actors

        # Reject forbidden emotion labels
        forbidden_labels = {
            "anxious", "depressed", "traumatized", "dysregulated", "triggered",
        }
        if data.get("primary_emotion_label", "").lower() in forbidden_labels:
            data["primary_emotion_label"] = "tense"

        # Clamp float fields to [0, 1]
        float_fields = [
            "freedom_to_refuse", "conflict_cost", "relationship_risk",
            "expectation_pressure", "agency_score", "social_exposure",
        ]
        for field in float_fields:
            if field in data:
                try:
                    data[field] = max(0.0, min(1.0, float(data[field])))
                except (TypeError, ValueError):
                    data[field] = 0.5

        # Ensure causal_chain is a list
        if not isinstance(data.get("causal_chain"), list):
            data["causal_chain"] = []

        return data

    def _minimal_structure(self, placeholder_map: PlaceholderMap) -> NarrativeStructure:
        """Fallback when extraction is unavailable or fails."""
        return NarrativeStructure(
            trigger_domain="ambiguous",
            primary_actors=list(placeholder_map.entity_map.keys()),
            action_taken=None,
            action_desired=None,
            outcome=None,
            freedom_to_refuse=0.5,
            conflict_cost=0.5,
            relationship_risk=0.5,
            expectation_pressure=0.5,
            agency_score=0.5,
            social_exposure=0.5,
            primary_emotion_label="tense",
            body_location=None,
            reaction_pattern="suppress",
            attributed_cause=None,
            self_narrative=None,
            first_occurrence=False,
            pattern_descriptor=None,
            resolution_tried=None,
            resolution_outcome=None,
            causal_chain=[],
        )
