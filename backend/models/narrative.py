"""
Narrative Data Structures
Privacy-preserving representation of conversation narratives
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class NarrativeStructure(BaseModel):
    """
    Privacy-safe narrative representation
    
    Contains ONLY abstract structural information:
    - NO names, places, dates, or identifying details
    - ONLY categorical patterns and emotional structure
    
    This is what gets sent to Gemini (not raw user text)
    """
    
    # Trigger (what started the emotional response)
    trigger_type: Optional[Literal[
        'interpersonal_conflict',
        'loss',
        'failure',
        'rejection',
        'uncertainty',
        'achievement',
        'connection'
    ]] = None
    
    trigger_domain: Optional[Literal[
        'family',
        'work',
        'romantic',
        'friendship',
        'health',
        'academic',
        'financial',
        'existential'
    ]] = None
    
    # Reaction (how person responded)
    reaction_pattern: Optional[Literal[
        'withdrawal',
        'rumination',
        'confrontation',
        'avoidance',
        'seeking_support',
        'problem_solving',
        'emotional_expression'
    ]] = None
    
    # Emotional state
    emotional_valence: Optional[Literal[
        'very_negative',
        'negative',
        'mixed',
        'neutral',
        'positive',
        'very_positive'
    ]] = None
    
    emotional_arousal: Optional[Literal[
        'very_low',   # Numb, detached
        'low',        # Calm, subdued
        'medium',     # Normal energy
        'high',       # Activated, intense
        'very_high'   # Overwhelmed, dysregulated
    ]] = None
    
    # Self-perception
    self_judgment: bool = Field(
        default=False,
        description="Is person being self-critical?"
    )
    
    agency_level: Optional[Literal[
        'very_low',   # "Things happen to me"
        'low',        # Mostly passive
        'medium',     # Mixed
        'high',       # "I made choices"
        'very_high'   # Strong sense of control
    ]] = None
    
    # Narrative coherence indicators
    temporal_clarity: Optional[Literal[
        'unclear',    # Jumping around in time
        'partial',    # Some sequence
        'clear'       # Chronological, ordered
    ]] = None
    
    causal_connections: Optional[Literal[
        'absent',     # No "because" or "so"
        'emerging',   # Starting to connect
        'present'     # Clear cause-effect
    ]] = None
    
    # Resolution state
    resolution_state: Optional[Literal[
        'unresolved',
        'partial',
        'resolved',
        'reframed'    # Meaning made, even if not "fixed"
    ]] = None
    
    # Metadata
    conversation_phase: Optional[Literal[
        'initial_sharing',     # Just starting to tell story
        'elaborating',         # Adding detail
        'meaning_making',      # Connecting dots
        'integrating',         # Seeing bigger picture
        'closing'              # Wrapping up
    ]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "trigger_type": "interpersonal_conflict",
                "trigger_domain": "family",
                "reaction_pattern": "withdrawal",
                "emotional_valence": "negative",
                "emotional_arousal": "high",
                "self_judgment": True,
                "agency_level": "low",
                "temporal_clarity": "partial",
                "causal_connections": "emerging",
                "resolution_state": "unresolved",
                "conversation_phase": "elaborating"
            }
        }


class ConversationTurn(BaseModel):
    """
    Single turn in conversation
    Stored in session, NOT sent to external APIs
    """
    
    turn_id: int
    role: Literal['user', 'sanctuary']
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional metadata
    narrative_structure: Optional[NarrativeStructure] = None
    gen_z_mode: bool = False


class ConversationSession(BaseModel):
    """
    Complete conversation session
    Stored temporarily in memory/cache
    """
    
    session_id: str
    turns: List[ConversationTurn] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_turn(self, role: str, text: str, **kwargs) -> ConversationTurn:
        """Add a new turn to conversation"""
        turn = ConversationTurn(
            turn_id=len(self.turns),
            role=role,
            text=text,
            **kwargs
        )
        self.turns.append(turn)
        self.updated_at = datetime.utcnow()
        return turn
    
    def get_recent_context(self, n_turns: int = 5) -> List[ConversationTurn]:
        """Get last N turns for context"""
        return self.turns[-n_turns:] if self.turns else []
