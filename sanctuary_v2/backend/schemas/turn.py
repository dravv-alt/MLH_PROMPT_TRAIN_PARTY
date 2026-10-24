from typing import Optional
from pydantic import BaseModel


class TurnRequest(BaseModel):
    session_id: str
    text: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_filename: Optional[str] = "audio.wav"


class TurnResponse(BaseModel):
    turn_id: str
    response_text: str
    response_audio_url: Optional[str] = None
    can_save_to_journal: bool = True
