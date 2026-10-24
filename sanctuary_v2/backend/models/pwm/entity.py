from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sanctuary_v2.backend.core.database import Base
from datetime import datetime
import uuid

class Entity(Base):
    __tablename__ = "entities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    placeholder_id = Column(String, nullable=False)
    # Consistent anonymous ID: "PERSON_A", "PERSON_B", "LOCATION_X"

    entity_type = Column(String, nullable=False)
    # PERSON | LOCATION | ORGANIZATION | TIME | EVENT

    role_tag = Column(String, default="unknown")
    # work | family | romantic | friendship | self | ambiguous | unknown

    emotional_valence_avg = Column(Float, default=0.0)   # -1.0 to +1.0
    emotional_valence_variance = Column(Float, default=0.0)

    mention_frequency = Column(Integer, default=0)
    last_seen = Column(DateTime, default=datetime.utcnow)
    session_appearances = Column(JSON, default=list)  # session_id list

    surface_forms = Column(JSON, default=list)
    # All names/pronouns this entity has appeared as.

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
