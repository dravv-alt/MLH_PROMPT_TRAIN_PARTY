from typing import Optional
import httpx

from sanctuary_v2.backend.core.config import settings


class STTService:
    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.base_url = "https://api.openai.com/v1/audio/transcriptions"

    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for STT transcription.")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"model": self.model}
        files = {"file": (filename, audio_bytes, "audio/wav")}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, headers=headers, data=data, files=files)
            response.raise_for_status()
            payload = response.json()

        return (payload.get("text") or "").strip()
