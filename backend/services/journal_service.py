"""
Journal Service
Handles saving user-selected conversation moments
"""

from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from backend.models.narrative import ConversationTurn
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class JournalEntry(BaseModel):
    """
    User-curated journal entry
    Contains ONLY what user selected + their reflection
    """
    
    entry_id: str
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # User-selected moments
    selected_turns: List[Dict[str, str]]  # [{"role": "user", "text": "..."}]
    
    # User's added reflection
    user_reflection: Optional[str] = None
    
    # Metadata
    total_turns_in_session: int
    selected_count: int


class JournalService:
    """
    Manages journal entries
    
    Philosophy:
    - User chooses what to save (agency)
    - No auto-saving (explicit opt-in)
    - Minimal data storage (privacy)
    - User can edit before saving (control)
    """
    
    def __init__(self):
        # In-memory storage for MVP
        # In production: use database (PostgreSQL, MongoDB)
        self.entries: Dict[str, JournalEntry] = {}
        
        logger.info("Journal service initialized")
    
    def create_entry(
        self,
        session_id: str,
        selected_turn_ids: List[int],
        all_turns: List[ConversationTurn],
        user_reflection: Optional[str] = None
    ) -> JournalEntry:
        """
        Create a journal entry from selected turns
        
        Args:
            session_id: Session identifier
            selected_turn_ids: Turn IDs user selected
            all_turns: Complete conversation turns
            user_reflection: User's added reflection
        
        Returns:
            Created JournalEntry
        """
        
        # Extract selected turns
        selected_turns = []
        for turn_id in selected_turn_ids:
            if turn_id < len(all_turns):
                turn = all_turns[turn_id]
                selected_turns.append({
                    "role": turn.role,
                    "text": turn.text,
                    "timestamp": turn.timestamp.isoformat()
                })
        
        # Create entry
        entry_id = f"entry_{session_id}_{int(datetime.utcnow().timestamp())}"
        
        entry = JournalEntry(
            entry_id=entry_id,
            session_id=session_id,
            selected_turns=selected_turns,
            user_reflection=user_reflection,
            total_turns_in_session=len(all_turns),
            selected_count=len(selected_turns)
        )
        
        # Save
        self.entries[entry_id] = entry
        
        logger.info(f"Journal entry created: {entry_id} ({len(selected_turns)} turns)")
        return entry
    
    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Get journal entry by ID"""
        return self.entries.get(entry_id)
    
    def get_entries_by_session(self, session_id: str) -> List[JournalEntry]:
        """Get all journal entries for a session"""
        return [
            entry for entry in self.entries.values()
            if entry.session_id == session_id
        ]
    
    def update_reflection(self, entry_id: str, reflection: str) -> bool:
        """
        Update user reflection on existing entry
        
        Returns:
            True if updated, False if entry not found
        """
        
        if entry_id in self.entries:
            self.entries[entry_id].user_reflection = reflection
            logger.info(f"Updated reflection for entry: {entry_id}")
            return True
        
        return False
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete a journal entry
        
        Returns:
            True if deleted, False if not found
        """
        
        if entry_id in self.entries:
            del self.entries[entry_id]
            logger.info(f"Deleted journal entry: {entry_id}")
            return True
        
        return False
    
    def suggest_key_moments(
        self,
        turns: List[ConversationTurn],
        max_suggestions: int = 3
    ) -> List[int]:
        """
        AI-suggested key moments for journaling
        
        Args:
            turns: All conversation turns
            max_suggestions: Max number to suggest
        
        Returns:
            List of turn IDs that seem important
        
        Suggestion criteria:
        - User turns (not Sanctuary)
        - High coherence improvement (if tracked)
        - Contains insight language
        - Emotional shift detected
        """
        
        suggestions = []
        
        # Insight keywords
        insight_markers = [
            'oh', 'wow', 'i see', 'makes sense', 'i never',
            'realized', 'that explains', 'interesting'
        ]
        
        for i, turn in enumerate(turns):
            if turn.role != 'user':
                continue
            
            text_lower = turn.text.lower()
            
            # Check for insight language
            has_insight = any(marker in text_lower for marker in insight_markers)
            
            # Check for emotional words (might indicate key moment)
            emotional_words = [
                'feel', 'felt', 'feeling', 'emotion',
                'realized', 'understood', 'clarity'
            ]
            has_emotional_language = any(word in text_lower for word in emotional_words)
            
            # Score this turn
            score = 0
            if has_insight:
                score += 2
            if has_emotional_language:
                score += 1
            if turn.narrative_structure and turn.narrative_structure.causal_connections == 'present':
                score += 2
            
            if score >= 2:
                suggestions.append((i, score))
        
        # Sort by score and return top N
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [turn_id for turn_id, _ in suggestions[:max_suggestions]]
