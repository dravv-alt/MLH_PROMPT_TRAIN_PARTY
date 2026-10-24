from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sanctuary_v2.backend.core.database import Base
from datetime import datetime
import uuid

class UnsaidNode(Base):
    __tablename__ = "unsaid_nodes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    turn_index = Column(Integer, nullable=False)

    signal_type = Column(String, nullable=False)
    # abandoned_sentence | rapid_topic_pivot | low_volume_marker |
    # incomplete_clause | deflection_detected

    structural_description = Column(String, nullable=False)
    # Structural only — no raw content.

    structure_embedding = Column(JSON, nullable=True)  # EmbeddingGemma 256-dim

    thread_id = Column(String, ForeignKey("threads.id"), nullable=True)

    surfaced = Column(String, default="no")
    # no | offered | accepted | declined

    created_at = Column(DateTime, default=datetime.utcnow)
