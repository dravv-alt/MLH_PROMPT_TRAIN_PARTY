"""
Narrative Distillation Service
Converts raw user text into privacy-safe narrative structures
"""

from typing import List, Dict, Optional
import re
from backend.models.narrative import NarrativeStructure, ConversationTurn
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class NarrativeDistiller:
    """
    Extracts narrative structure from user text
    
    Key Principle: Extract PATTERN, not CONTENT
    - Identifies emotional/relational structures
    - Removes all identifying information
    - Preserves therapeutic utility
    
    This is the privacy layer before Gemini API call
    """
    
    def __init__(self):
        # Keyword dictionaries for pattern detection
        self._load_pattern_keywords()
    
    def _load_pattern_keywords(self):
        """Load keyword patterns for structure detection"""
        
        # Trigger detection
        self.conflict_keywords = [
            'fight', 'argument', 'yelled', 'angry', 'mad', 'upset at',
            'disagreement', 'clash', 'confrontation', 'tension', 'hostile'
        ]
        
        self.loss_keywords = [
            'lost', 'died', 'death', 'gone', 'passed away', 'ended',
            'broke up', 'separation', 'divorce', 'goodbye', 'miss'
        ]
        
        self.failure_keywords = [
            'failed', 'failure', 'didn\'t get', 'rejected', 'didn\'t make',
            'messed up', 'screwed up', 'mistake', 'wrong', 'disappointed'
        ]
        
        self.rejection_keywords = [
            'rejected', 'ignored', 'excluded', 'left out', 'dismissed',
            'unwanted', 'abandoned', 'ghosted', 'blocked'
        ]
        
        # Reaction patterns
        self.withdrawal_keywords = [
            'alone', 'isolated', 'locked', 'avoided', 'hide', 'stay away',
            'withdrew', 'distance', 'shut down', 'closed off'
        ]
        
        self.rumination_keywords = [
            'keep thinking', 'can\'t stop', 'over and over', 'replaying',
            'obsessing', 'stuck on', 'won\'t leave my mind', 'constantly'
        ]
        
        self.seeking_support_keywords = [
            'talked to', 'called', 'reached out', 'shared with', 'told',
            'opened up', 'confided', 'vented to'
        ]
        
        # Self-judgment indicators
        self.self_criticism_keywords = [
            'failure', 'stupid', 'idiot', 'lazy', 'worthless', 'useless',
            'should have', 'shouldn\'t have', 'my fault', 'i\'m the problem',
            'weak', 'pathetic', 'terrible', 'awful', 'disaster'
        ]
        
        # Causal language (coherence indicator)
        self.causal_markers = [
            'because', 'so', 'therefore', 'since', 'as a result',
            'that\'s why', 'led to', 'caused', 'made me', 'which meant'
        ]
        
        # Temporal markers (coherence indicator)
        self.temporal_markers = [
            'then', 'after', 'before', 'next', 'later', 'first',
            'finally', 'meanwhile', 'eventually', 'when', 'while'
        ]
    
    def distill(
        self,
        user_text: str,
        conversation_history: List[ConversationTurn]
    ) -> NarrativeStructure:
        """
        Main distillation method
        
        Args:
            user_text: Current user message (raw text)
            conversation_history: Previous turns (for context)
        
        Returns:
            NarrativeStructure (privacy-safe, no identifying info)
        """
        
        text_lower = user_text.lower()
        
        # Detect trigger type
        trigger_type = self._detect_trigger_type(text_lower)
        
        # Detect trigger domain
        trigger_domain = self._detect_trigger_domain(text_lower)
        
        # Detect reaction pattern
        reaction_pattern = self._detect_reaction_pattern(text_lower)
        
        # Assess emotional state
        emotional_valence = self._assess_emotional_valence(text_lower)
        emotional_arousal = self._assess_emotional_arousal(text_lower, user_text)
        
        # Self-perception
        self_judgment = self._detect_self_judgment(text_lower)
        agency_level = self._assess_agency(text_lower)
        
        # Coherence indicators
        temporal_clarity = self._assess_temporal_clarity(text_lower)
        causal_connections = self._assess_causal_connections(text_lower)
        
        # Determine conversation phase
        conversation_phase = self._determine_phase(
            len(conversation_history),
            trigger_type,
            causal_connections
        )
        
        # Resolution state (based on emotional trajectory)
        resolution_state = self._assess_resolution(
            conversation_history,
            emotional_valence
        )
        
        structure = NarrativeStructure(
            trigger_type=trigger_type,
            trigger_domain=trigger_domain,
            reaction_pattern=reaction_pattern,
            emotional_valence=emotional_valence,
            emotional_arousal=emotional_arousal,
            self_judgment=self_judgment,
            agency_level=agency_level,
            temporal_clarity=temporal_clarity,
            causal_connections=causal_connections,
            resolution_state=resolution_state,
            conversation_phase=conversation_phase
        )
        
        logger.info(f"Distilled narrative structure: {structure.model_dump()}")
        return structure
    
    def _detect_trigger_type(self, text: str) -> Optional[str]:
        """Identify what initiated the emotional response"""
        
        if any(word in text for word in self.conflict_keywords):
            return 'interpersonal_conflict'
        elif any(word in text for word in self.loss_keywords):
            return 'loss'
        elif any(word in text for word in self.failure_keywords):
            return 'failure'
        elif any(word in text for word in self.rejection_keywords):
            return 'rejection'
        elif any(word in text for word in ['anxious', 'worried', 'unsure', 'don\'t know']):
            return 'uncertainty'
        elif any(word in text for word in ['achieved', 'succeeded', 'got', 'accomplished']):
            return 'achievement'
        elif any(word in text for word in ['connected', 'close', 'together', 'bonded']):
            return 'connection'
        
        return None
    
    def _detect_trigger_domain(self, text: str) -> Optional[str]:
        """Identify life domain of trigger"""
        
        domain_keywords = {
            'family': ['mom', 'dad', 'mother', 'father', 'parent', 'sibling', 'family'],
            'work': ['work', 'job', 'boss', 'colleague', 'career', 'office', 'manager'],
            'romantic': ['boyfriend', 'girlfriend', 'partner', 'spouse', 'husband', 'wife', 'relationship', 'dating'],
            'friendship': ['friend', 'buddy', 'pal', 'crew', 'squad'],
            'health': ['sick', 'illness', 'doctor', 'hospital', 'pain', 'diagnosis', 'treatment'],
            'academic': ['school', 'class', 'professor', 'grade', 'exam', 'studying', 'college', 'university'],
            'financial': ['money', 'debt', 'bills', 'rent', 'financial', 'expensive', 'afford'],
            'existential': ['meaning', 'purpose', 'point', 'why', 'existence', 'life', 'future']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(word in text for word in keywords):
                return domain
        
        return None
    
    def _detect_reaction_pattern(self, text: str) -> Optional[str]:
        """Identify how person responded to trigger"""
        
        if any(word in text for word in self.withdrawal_keywords):
            return 'withdrawal'
        elif any(word in text for word in self.rumination_keywords):
            return 'rumination'
        elif any(word in text for word in ['confronted', 'told them', 'fought back', 'argued']):
            return 'confrontation'
        elif any(word in text for word in ['avoided', 'ignored', 'pretended', 'distracted']):
            return 'avoidance'
        elif any(word in text for word in self.seeking_support_keywords):
            return 'seeking_support'
        elif any(word in text for word in ['tried to fix', 'problem solve', 'figured out', 'worked on']):
            return 'problem_solving'
        elif any(word in text for word in ['cried', 'screamed', 'yelled', 'expressed', 'let out']):
            return 'emotional_expression'
        
        return None
    
    def _assess_emotional_valence(self, text: str) -> Optional[str]:
        """Assess positive/negative emotional tone"""
        
        very_negative_words = [
            'awful', 'terrible', 'horrible', 'worst', 'devastating',
            'unbearable', 'hopeless', 'miserable', 'hate', 'despise'
        ]
        
        negative_words = [
            'sad', 'upset', 'angry', 'frustrated', 'hurt', 'disappointed',
            'anxious', 'worried', 'scared', 'lonely', 'guilty', 'ashamed',
            'failure', 'messed up', 'screwed up', 'worthless', 'pathetic'
        ]
        
        positive_words = [
            'good', 'better', 'happy', 'glad', 'relieved', 'okay',
            'proud', 'hopeful', 'grateful', 'calm', 'peaceful'
        ]
        
        very_positive_words = [
            'amazing', 'wonderful', 'excellent', 'fantastic', 'joyful',
            'ecstatic', 'thrilled', 'love', 'adore', 'blessed'
        ]
        
        very_neg_count = sum(1 for word in very_negative_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        pos_count = sum(1 for word in positive_words if word in text)
        very_pos_count = sum(1 for word in very_positive_words if word in text)
        
        if very_neg_count > 0 or neg_count >= 3:
            return 'very_negative' if very_neg_count > 0 else 'negative'
        elif very_pos_count > 0 or pos_count >= 3:
            return 'very_positive' if very_pos_count > 0 else 'positive'
        elif pos_count > 0 and neg_count > 0:
            return 'mixed'
        elif pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        
        return 'neutral'
    
    def _assess_emotional_arousal(self, text: str, original_text: str) -> Optional[str]:
        """Assess energy/activation level"""
        
        # High arousal indicators
        high_arousal_words = [
            'intense', 'overwhelming', 'can\'t handle', 'too much',
            'exploded', 'panic', 'freaking out', 'losing it'
        ]
        
        # Check capitalization (YELLING indicates high arousal)
        caps_ratio = sum(1 for c in original_text if c.isupper()) / max(len(original_text), 1)
        has_caps = caps_ratio > 0.3
        
        # Check punctuation (!!!, ???)
        excessive_punct = '!!' in original_text or '??' in original_text
        
        if any(word in text for word in high_arousal_words) or has_caps or excessive_punct:
            return 'very_high'
        elif any(word in text for word in ['anxious', 'nervous', 'agitated', 'restless']):
            return 'high'
        elif any(word in text for word in ['numb', 'empty', 'flat', 'detached', 'dissociated']):
            return 'very_low'
        elif any(word in text for word in ['tired', 'drained', 'exhausted', 'low energy']):
            return 'low'
        
        return 'medium'
    
    def _detect_self_judgment(self, text: str) -> bool:
        """Check if person is being self-critical"""
        return any(word in text for word in self.self_criticism_keywords)
    
    def _assess_agency(self, text: str) -> Optional[str]:
        """Assess sense of personal agency vs. external forces"""
        
        # High agency: "I decided", "I chose", "I made"
        high_agency_phrases = [
            'i decided', 'i chose', 'i made', 'i did', 'i took control',
            'i handled', 'i managed', 'my choice'
        ]
        
        # Low agency: "it happened", "they made me", passive voice
        low_agency_phrases = [
            'it happened', 'things happened', 'they made me', 'i had to',
            'i couldn\'t help', 'no choice', 'forced to', 'couldn\'t control'
        ]
        
        # Count first-person active vs passive constructions
        i_count = text.count(' i ') + text.count('i ')
        they_it_count = text.count('they ') + text.count(' it ')
        
        has_high_agency = any(phrase in text for phrase in high_agency_phrases)
        has_low_agency = any(phrase in text for phrase in low_agency_phrases)
        
        if has_high_agency or i_count > they_it_count * 2:
            return 'high'
        elif has_low_agency or they_it_count > i_count * 2:
            return 'low'
        
        return 'medium'
    
    def _assess_temporal_clarity(self, text: str) -> Optional[str]:
        """Assess how clear the time sequence is"""
        
        marker_count = sum(1 for marker in self.temporal_markers if marker in text)
        
        # Check for time confusion
        confusion_phrases = [
            'i don\'t know when', 'not sure when', 'can\'t remember',
            'everything\'s a blur', 'all mixed up'
        ]
        has_confusion = any(phrase in text for phrase in confusion_phrases)
        
        if has_confusion:
            return 'unclear'
        elif marker_count >= 3:
            return 'clear'
        elif marker_count >= 1:
            return 'partial'
        
        return 'unclear'
    
    def _assess_causal_connections(self, text: str) -> Optional[str]:
        """Assess presence of cause-effect reasoning"""
        
        causal_count = sum(1 for marker in self.causal_markers if marker in text)
        
        if causal_count >= 3:
            return 'present'
        elif causal_count >= 1:
            return 'emerging'
        
        return 'absent'
    
    def _determine_phase(
        self,
        turn_count: int,
        trigger_type: Optional[str],
        causal_connections: Optional[str]
    ) -> Optional[str]:
        """Determine conversation phase"""
        
        if turn_count == 0:
            return 'initial_sharing'
        elif turn_count <= 3:
            return 'elaborating'
        elif causal_connections in ['emerging', 'present']:
            return 'meaning_making'
        elif turn_count >= 8:
            return 'closing'
        
        return 'elaborating'
    
    def _assess_resolution(
        self,
        conversation_history: List[ConversationTurn],
        current_valence: Optional[str]
    ) -> Optional[str]:
        """Assess if emotional issue is resolving"""
        
        if not conversation_history:
            return 'unresolved'
        
        # Check trajectory of emotional valence
        if len(conversation_history) >= 2:
            recent_turns = conversation_history[-2:]
            
            # If moving from negative to positive/mixed
            if (current_valence in ['positive', 'mixed'] and
                any('negative' in str(t.narrative_structure.emotional_valence) 
                    for t in recent_turns if t.narrative_structure)):
                return 'partial'
        
        # Check for resolution language
        if len(conversation_history) > 0:
            last_user_text = conversation_history[-1].text.lower()
            resolution_phrases = [
                'makes sense', 'i see', 'i understand', 'that helps',
                'i feel better', 'clearer', 'realized', 'figured out'
            ]
            
            if any(phrase in last_user_text for phrase in resolution_phrases):
                return 'partial'
        
        return 'unresolved'
    
    def to_gemini_context(
        self,
        structure: NarrativeStructure,
        user_text: str,
        gen_z_mode: bool = False
    ) -> str:
        """
        Create Gemini system prompt from narrative structure
        
        Args:
            structure: Distilled narrative structure
            user_text: Original user text (for reflection)
            gen_z_mode: Whether to use Gen-Z tone
        
        Returns:
            Complete prompt for Gemini
        """
        
        # Build context description
        context_parts = []
        
        if structure.trigger_type:
            context_parts.append(f"trigger: {structure.trigger_type}")
        
        if structure.trigger_domain:
            context_parts.append(f"domain: {structure.trigger_domain}")
        
        if structure.reaction_pattern:
            context_parts.append(f"reaction: {structure.reaction_pattern}")
        
        if structure.emotional_valence:
            context_parts.append(f"feeling: {structure.emotional_valence}")
        
        if structure.self_judgment:
            context_parts.append("self-critical thoughts present")
        
        if structure.agency_level:
            context_parts.append(f"agency: {structure.agency_level}")
        
        if structure.causal_connections:
            context_parts.append(f"causal understanding: {structure.causal_connections}")
        
        context_summary = ", ".join(context_parts) if context_parts else "sharing experience"
        
        # Determine conversation goals based on phase
        goals = self._get_phase_goals(structure.conversation_phase)
        
        # Build prompt
        tone_instruction = ""
        if gen_z_mode:
            tone_instruction = """
TONE: Gen-Z Mode (culturally fluent, not meme-driven)
- Observational, not prescriptive
- Wisdom > slang
- Use "lowkey", "gng", "track" naturally
- Never mock or trivialize distress
- Example: "Lowkey sounds like when life stacks up like that, a lotta people..."
"""
        
        prompt = f"""You are Sanctuary, a reflective companion that helps people understand their experiences through narrative.

CONVERSATION CONTEXT:
{context_summary}

CURRENT PHASE: {structure.conversation_phase}
GOALS FOR THIS TURN:
{goals}

USER'S WORDS (reflect their language, don't paraphrase):
"{user_text}"

CORE DESIGN RULE (CRITICAL):
Sanctuary NEVER asks users to explain themselves. Reflect what’s already there until the user feels understood — then gently move forward. No open-ended questions like "How does that make you feel?" or "What does that feel like?". If you must ask a question, it should only be an optional action.

CONVERSATION FLOW:
The story naturally moves from: reaction → pattern → cause → meaning → relief.
The user responds to your reflections by correcting or deepening, not inventing.

STRICT CONSTRAINTS:
- NO open-ended questions ("How does that make you feel?", "What is causing this?")
- NO advice or coping techniques
- NO labeling emotions they haven't named
- NO diagnosis or clinical language
- NO "you should" statements
- NO pressure to share more. "If I read this while emotionally raw, would I feel compelled to keep talking?" -> Ensure the answer is no. This prevents nudging the user uncomfortably.

WHAT TO DO:
- Make causal connections explicit ("It makes sense that X led to Y")
- Validate without fixing
- Use their EXACT words when reflecting back
- Keep responses EXTREMELY CONCISE. 2-4 sentences MAXIMUM. Avoid repetitive explanations.

{tone_instruction}

Respond with exactly ONE extremely concise paragraph (2 to 4 sentences) that reflects on the user's expression."""

        return prompt
    
    def _get_phase_goals(self, phase: Optional[str]) -> str:
        """Get conversation goals for current phase"""
        
        phase_goals = {
            'initial_sharing': "Help them tell what happened. Reflect structure, not details.",
            'elaborating': "Encourage adding context. Notice patterns emerging.",
            'meaning_making': "Help connect dots. Externalize self-criticism. Build coherence.",
            'integrating': "Support bigger-picture understanding. Normalize experience.",
            'closing': "Acknowledge progress. Offer to save reflection if appropriate."
        }
        
        return phase_goals.get(phase, "Support narrative exploration")
