import os
from typing import Optional


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


class GeminiReflector:
    def __init__(self) -> None:
        self.enabled = False
        self._model = None
        self.model_name: str | None = None
        self._initialize()

    def _resolve_model_name(self, genai, requested_model: str) -> str | None:
        available: set[str] = set()

        try:
            for item in genai.list_models():
                methods = getattr(item, "supported_generation_methods", [])
                if "generateContent" not in methods:
                    continue

                name = getattr(item, "name", "")
                if name.startswith("models/"):
                    name = name.split("/", 1)[1]
                if name:
                    available.add(name)
        except Exception:
            # If listing models fails, trust requested model and let generation validate it.
            return requested_model

        if not available:
            return requested_model

        normalized_requested = requested_model
        if normalized_requested.startswith("models/"):
            normalized_requested = normalized_requested.split("/", 1)[1]
        if normalized_requested in available:
            return normalized_requested

        preferred = [
            "gemini-flash-latest",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-pro-latest",
            "gemini-2.5-pro",
            "gemini-3.1-pro-preview",
            "gemini-3-pro-preview",
        ]
        for candidate in preferred:
            if candidate in available:
                return candidate

        generic = [
            name
            for name in available
            if name.startswith("gemini-")
            and "robotics" not in name
            and "tts" not in name
            and "image" not in name
            and "computer-use" not in name
        ]
        if generic:
            return sorted(generic)[-1]

        return sorted(available)[-1]

    def _initialize(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            return

        try:
            import google.generativeai as genai
        except Exception:
            return

        requested_model = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip() or "gemini-flash-latest"
        temperature = _env_float("GEMINI_TEMPERATURE", 0.4)
        max_tokens = _env_int("GEMINI_MAX_TOKENS", 220)

        try:
            genai.configure(api_key=api_key)

            resolved_model = self._resolve_model_name(genai, requested_model)
            if not resolved_model:
                self._model = None
                self.model_name = None
                self.enabled = False
                return

            self._model = genai.GenerativeModel(
                model_name=resolved_model,
                generation_config={
                    "temperature": temperature,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": max_tokens,
                },
            )
            self.model_name = resolved_model
            self.enabled = True
        except Exception:
            self._model = None
            self.model_name = None
            self.enabled = False

    def generate(self, prompt: str) -> Optional[str]:
        if not self.enabled or self._model is None:
            return None

        try:
            response = self._model.generate_content(prompt)
        except Exception as exc:
            # If a configured model becomes invalid/deprecated, refresh via ListModels once.
            message = str(exc).lower()
            if "not found" in message or "404" in message or "not supported" in message:
                self._initialize()
                if self.enabled and self._model is not None:
                    try:
                        response = self._model.generate_content(prompt)
                    except Exception:
                        return None
                else:
                    return None
            else:
                return None

        text = getattr(response, "text", None)
        if not text:
            return None

        normalized = " ".join(str(text).split()).strip()
        return normalized or None


gemini_reflector = GeminiReflector()