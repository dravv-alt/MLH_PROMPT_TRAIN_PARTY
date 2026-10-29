import json
import os
import urllib.error
import urllib.request
from typing import Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - handled by runtime fallback
    OpenAI = None


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class GroqReflector:
    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile"
        self.temperature = _env_float("GROQ_TEMPERATURE", 0.3)
        self.max_tokens = _env_int("GROQ_MAX_TOKENS", 220)
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
        self.enabled = bool(self.api_key)
        self._client = None

        if self.enabled and OpenAI is not None:
            try:
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception:
                self._client = None

    def _generate_via_http(self, prompt: str) -> Optional[str]:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "sanctuary-v2-backend/1.0",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            return None

        try:
            parsed = json.loads(raw)
            choices = parsed.get("choices") or []
            first = choices[0] if choices else {}
            message = first.get("message") if isinstance(first, dict) else {}
            content = message.get("content") if isinstance(message, dict) else None
        except Exception:
            return None

        if not content:
            return None

        normalized = " ".join(str(content).split()).strip()
        return normalized or None

    def generate(self, prompt: str) -> Optional[str]:
        if not self.enabled:
            return None

        if self._client is not None:
            try:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                text = response.choices[0].message.content if response and response.choices else None
                if text:
                    normalized = " ".join(str(text).split()).strip()
                    return normalized or None
            except Exception:
                # Fall through to raw HTTP transport for resiliency.
                pass

        return self._generate_via_http(prompt)

    def chat(self, messages: list[dict[str, str]], system_instruction: Optional[str] = None) -> Optional[str]:
        """Execute multi-turn chat with rolling memory and system instruction."""
        if not self.enabled:
            return None

        payload_messages = []
        if system_instruction:
            payload_messages.append({"role": "system", "content": system_instruction})
        for m in messages:
            if m.get("content"):
                payload_messages.append({"role": m.get("role", "user"), "content": m["content"]})

        if not payload_messages:
            return None

        if self._client is not None:
            try:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=payload_messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                text = response.choices[0].message.content if response and response.choices else None
                if text:
                    return " ".join(str(text).split()).strip() or None
            except Exception:
                pass

        try:
            payload = {
                "model": self.model_name,
                "messages": payload_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            data = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                url=f"{self.base_url}/chat/completions",
                data=data,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "sanctuary-v2-backend/1.0",
                },
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
            parsed = json.loads(raw)
            choices = parsed.get("choices") or []
            first = choices[0] if choices else {}
            message = first.get("message") if isinstance(first, dict) else {}
            content = message.get("content") if isinstance(message, dict) else None
            if content:
                return " ".join(str(content).split()).strip() or None
        except Exception:
            return None

        return None


groq_reflector = GroqReflector()
