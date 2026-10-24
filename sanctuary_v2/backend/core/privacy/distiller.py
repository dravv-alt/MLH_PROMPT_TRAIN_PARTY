from dataclasses import dataclass, field
from typing import Dict, Optional
import re
import spacy

@dataclass
class PlaceholderMap:
    """
    In-memory ONLY. NEVER persisted, NEVER sent externally.
    Destroyed after placeholder restoration.
    """
    raw_text: str = ""
    distilled_text: str = ""
    
    # {"PERSON_A": "David", "LOCATION_X": "the office"}
    entity_map: Dict[str, str] = field(default_factory=dict)
    
    # {"David": "PERSON_A", "the office": "LOCATION_X"}
    reverse_map: Dict[str, str] = field(default_factory=dict)
    
    # {"PERSON_A": "PERSON", "LOCATION_X": "GPE"}
    entity_types: Dict[str, str] = field(default_factory=dict)


class PrivacyDistiller:
    """
    PII stripping and placeholder mapping.
    Must run BEFORE any other processing.
    """
    PLACEHOLDER_PREFIXES = {
        "PERSON": "PERSON",
        "GPE": "LOCATION",
        "LOC": "LOCATION",
        "ORG": "ORG",
        "DATE": "TIME",
        "TIME": "TIME",
        "EVENT": "EVENT",
    }

    ENTITY_TYPE_MAP = {
        "PERSON": "PERSON",
        "GPE": "LOCATION",
        "LOC": "LOCATION",
        "ORG": "ORGANIZATION",
        "DATE": "TIME",
        "TIME": "TIME",
        "EVENT": "EVENT",
    }

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # We will download it on demand if absent in the environment
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
            self.nlp = spacy.load("en_core_web_sm")
            
        self.email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        self.url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')

    async def distill(self, raw_text: str, user_id: str, db_session) -> PlaceholderMap:
        """
        1. Run spaCy NER.
        2. Assign/Resolve entity placeholders.
        3. Strip regex templates (e-mails, phones, URLs).
        """
        pmap = PlaceholderMap(raw_text=raw_text)
        
        # Regex pass first
        clean_text = self.email_pattern.sub("[EMAIL]", raw_text)
        clean_text = self.phone_pattern.sub("[PHONE]", clean_text)
        clean_text = self.url_pattern.sub("[URL]", clean_text)
        
        # NER pass
        doc = self.nlp(clean_text)
        
        # Keep counters for new entities: e.g., PERSON_A, PERSON_B
        counters = {k: ord('A') for k in self.PLACEHOLDER_PREFIXES.values()}
        
        # To avoid corrupting substring replacements, we replace from back to front
        spans = []
        for ent in doc.ents:
            prefix = self.PLACEHOLDER_PREFIXES.get(ent.label_)
            if not prefix:
                continue
            entity_type = self.ENTITY_TYPE_MAP.get(ent.label_, prefix)
            spans.append((ent.start_char, ent.end_char, prefix, entity_type))
                 
        # Sort entirely by start index descending
        spans.sort(key=lambda x: x[0], reverse=True)
        
        for start, end, prefix, entity_type in spans:
            surface_form = clean_text[start:end]
            
            # TODO in Phase 2: Call CoreferenceResolver to check if map exists in PWM Entity table.
            # For now in Phase 1: local dictionary assignment.
            if surface_form not in pmap.reverse_map:
                placeholder = f"{prefix}_{chr(counters[prefix])}"
                counters[prefix] += 1
                
                pmap.reverse_map[surface_form] = placeholder
                pmap.entity_map[placeholder] = surface_form
                pmap.entity_types[placeholder] = entity_type
            else:
                placeholder = pmap.reverse_map[surface_form]
                
            clean_text = clean_text[:start] + placeholder + clean_text[end:]
            
        pmap.distilled_text = clean_text
        return pmap
