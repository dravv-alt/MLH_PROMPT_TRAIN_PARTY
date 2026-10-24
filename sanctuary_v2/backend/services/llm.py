"""
LLM Service — Language generation via Groq (Zone C).

The intelligence of the system lives in Zone A computation.
The LLM is the voice, not the brain.

What LLM receives:
  - behavioral_spec (strategy instruction string)
  - distilled conversation history (last 5 turns, placeholders intact)
  - distilled_input (current turn, placeholders intact)
  - max_sentences, allow_questions constraints

What LLM NEVER receives:
  - PWM contents (entity names, thread labels, relationship data)
  - NarrativeStateVector (hypothesis scores, bifurcation proximity, etc.)
  - raw user text
  - entity real names (only placeholder IDs)
"""

from typing import Optional
import httpx

from sanctuary_v2.backend.core.config import settings


class LLMService:

    # ── Full 8-rule system prompt from PRD Section 7.13 ─────────────────
    SYSTEM_PROMPT = (
        "You are Sanctuary -- a companion for emotional expression.\n"
        "Your only job is generating language that implements the behavioral "
        "specification given.\n\n"
        "ABSOLUTE RULES (no exceptions, no context overrides these):\n"
        "1. NEVER use diagnostic language: anxiety, depression, trauma, disorder, "
        "symptoms, diagnosis, mental illness, condition, bipolar, adhd, ptsd, ocd, "
        "dysregulated\n"
        "2. NEVER assign identity: \"you are someone who\", \"you tend to\", "
        "\"you always\", \"you're the type\", \"your pattern is\", "
        "\"you have a pattern of\"\n"
        "3. NEVER give advice unless user explicitly requested it in this turn\n"
        "4. NEVER reference prior sessions explicitly\n"
        "5. NEVER use more sentences than the behavioral spec allows\n"
        "6. If allow_questions = False: use ZERO question marks in response\n"
        "7. NEVER express that you are an AI, reference your limitations, or break "
        "character\n"
        "8. NEVER foster dependency: avoid \"I'm always here\", \"you can always "
        "talk to me\"\n\n"
        "You are calm, present, and grounded. Nothing theatrical. Nothing desperate.\n"
        "Reflect. Be present. Speak in the user's register."
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama3-8b-8192",
    ):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate(
        self,
        distilled_text: str,
        behavioral_spec: str,
        max_sentences: int = 3,
        allow_questions: bool = True,
    ) -> str:
        """
        Generates a response using the Groq API.

        Falls back to a safe static response when no API key is configured —
        this lets the pipeline complete gracefully during development.
        """
        if not self.api_key:
            return "I hear you. If you want, you can share more about that."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # PRD-specified user message format (Section 7.13)
        user_content = (
            f"[BEHAVIORAL SPEC]: {behavioral_spec}\n"
            f"[MAX SENTENCES]: {max_sentences}\n"
            f"[QUESTIONS ALLOWED]: {allow_questions}\n"
            f"[WHAT USER SAID]: {distilled_text}"
        )

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 200,
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                self.base_url, headers=headers, json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"].strip()
