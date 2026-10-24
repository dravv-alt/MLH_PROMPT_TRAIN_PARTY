import os
import uuid
from typing import Optional
import httpx

from sanctuary_v2.backend.core.config import settings


class TTSService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None,
        output_dir: str = "tmp",
    ):
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        self.voice_id = voice_id or settings.ELEVENLABS_VOICE_ID
        self.output_dir = output_dir
        self.base_url = "https://api.elevenlabs.io/v1/text-to-speech"

    async def synthesize(self, text: str) -> str:
        if not self.api_key or not self.voice_id:
            raise RuntimeError("ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID are required.")

        os.makedirs(self.output_dir, exist_ok=True)
        url = f"{self.base_url}/{self.voice_id}"

        headers = {
            "xi-api-key": self.api_key,
            "accept": "audio/mpeg",
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        filename = f"tts_{uuid.uuid4().hex}.mp3"
        path = os.path.join(self.output_dir, filename)
        with open(path, "wb") as audio_file:
            audio_file.write(response.content)

        return path
