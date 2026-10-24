from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sanctuary_v2.backend.core.database import Base
from datetime import datetime
import uuid

class Turn(Base):
    __tablename__ = "turns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    turn_index = Column(Integer, nullable=False)

    # PRIVACY RULE: raw_user_text COLUMN DOES NOT EXIST IN THIS TABLE
    # If you add it: critical privacy violation. See test_raw_text_never_stored.

    distilled_input = Column(String, nullable=False)       # Zone A safe
    narrative_structure_json = Column(JSON, nullable=True) # NarrativeStructure

    strategy_used = Column(String, nullable=False)
    winning_hypothesis = Column(String, nullable=False)
    hypothesis_confidence = Column(Float, nullable=False)

    response_text = Column(String, nullable=False)         # Restored (real names)
    response_audio_url = Column(String, nullable=True)

    # Affective State Tracking
    vad_valence = Column(Float, nullable=True)
    vad_arousal = Column(Float, nullable=True)
    vad_dominance = Column(Float, nullable=True)
    depth_layer = Column(Integer, nullable=True)

    user_saved_to_journal = Column(Boolean, default=False)
    depth_label_logged = Column(Boolean, default=False)    # For Phase 3 classifier
    
    # Needs to link to vector when instantiated
    # state_vector_id = Column(String, ForeignKey("narrative_states.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
