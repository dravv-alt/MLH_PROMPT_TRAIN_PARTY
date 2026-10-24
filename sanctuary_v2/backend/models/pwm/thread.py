from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sanctuary_v2.backend.core.database import Base
from datetime import datetime
import uuid

class Thread(Base):
    __tablename__ = "threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    internal_label = Column(String, nullable=False)
    # Machine-readable only, NEVER shown to user.

    # EmbeddingGemma 256-dim centroid of all distilled inputs on this thread
    centroid_embedding = Column(JSON, nullable=False)

    activation_score = Column(Float, default=0.0)    # 0.0-1.0 continuous
    status = Column(String, default="emerging")       # emerging|active|dormant|integrated

    session_count = Column(Integer, default=1)
    turn_count = Column(Integer, default=1)

    first_detected = Column(DateTime, default=datetime.utcnow)
    last_activated = Column(DateTime, default=datetime.utcnow)

    associated_entities = Column(JSON, default=list)  # placeholder_id list
    typical_depth_layer = Column(Integer, default=1)

    # Zettelkasten abstract pattern schema (Zone B sync candidate)
    abstract_pattern = Column(JSON, nullable=True)

    # DAG summary from most recent activations
    causal_chain_summary = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
