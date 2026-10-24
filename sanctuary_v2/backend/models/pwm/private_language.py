from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sanctuary_v2.backend.core.database import Base
from datetime import datetime
import uuid

class PrivateLanguageEntry(Base):
    __tablename__ = "private_language"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    phrase = Column(String, nullable=False)
    # Exact idiosyncratic phrase: "that spinning feeling", "going grey"

    inferred_vad_state = Column(JSON, nullable=False)
    # {"valence": -0.7, "arousal": 0.8, "dominance": 0.2}

    occurrence_count = Column(Integer, default=1)
    associated_thread_ids = Column(JSON, default=list)

    idiosyncrasy_score = Column(Float, default=0.5)

    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
