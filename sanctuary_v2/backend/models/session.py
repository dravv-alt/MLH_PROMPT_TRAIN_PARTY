from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sanctuary_v2.backend.core.database import Base
from datetime import datetime
import uuid

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="active")              # active | ended
    tone_mode = Column(String, default="standard")         # standard | casual
    turn_count = Column(Integer, default=0)
    max_depth_reached = Column(Integer, default=1)
    session_entropy_avg = Column(Float, nullable=True)
    companion_fade_triggered = Column(Boolean, default=False)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
