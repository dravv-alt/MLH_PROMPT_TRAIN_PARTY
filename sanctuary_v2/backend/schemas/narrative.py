from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class NarrativeStructure(BaseModel):
    """
    11-field structured representation of user input.
    Implements the Situational Structure Model (SSM).
    Built from distilled text — never contains raw PII.
    """
    # SSM Layer 1: Event Structure
    trigger_domain: str
    primary_actors: List[str] = Field(default_factory=list)
    action_taken: Optional[str] = None
    action_desired: Optional[str] = None
    outcome: Optional[str] = None

    # SSM Layer 2: Constraint Field
    freedom_to_refuse: float
    conflict_cost: float
    relationship_risk: float
    expectation_pressure: float
    agency_score: float
    social_exposure: float

    # SSM Layer 3: Internal Reaction
    primary_emotion_label: str
    body_location: Optional[str] = None
    reaction_pattern: str

    # SSM Layer 4: Meaning-Making
    attributed_cause: Optional[str] = None
    self_narrative: Optional[str] = None

    # SSM Layer 5: Temporal Pattern
    first_occurrence: bool
    pattern_descriptor: Optional[str] = None

    # SSM Layer 6: Resolution Attempt
    resolution_tried: Optional[str] = None
    resolution_outcome: Optional[str] = None

    # DAG edges (causal links between fields)
    causal_chain: List[Dict[str, Any]] = Field(default_factory=list)
