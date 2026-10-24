"""
Conversation Models
Request/response models for the conversation API
"""

from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    """Request for chat endpoint"""
    session_id: str
    user_message: str
    gen_z_mode: bool = False


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    sanctuary_response: str
    session_id: str
    turn_id: int


class TranscriptionResponse(BaseModel):
    """Response from voice transcription"""
    text: str
    session_id: Optional[str] = None


class JournalCreateRequest(BaseModel):
    """Request to create journal entry"""
    session_id: str
    selected_turn_ids: List[int]
    user_reflection: Optional[str] = None


class JournalSuggestResponse(BaseModel):
    """Suggested key moments for journaling"""
    session_id: str
    suggested_turn_ids: List[int]
    total_turns: int
