from datetime import datetime
from pydantic import BaseModel


class SessionStartResponse(BaseModel):
    session_id: str
    started_at: datetime


class SessionEndRequest(BaseModel):
    session_id: str


class SessionEndResponse(BaseModel):
    session_id: str
    ended_at: datetime
    status: str
