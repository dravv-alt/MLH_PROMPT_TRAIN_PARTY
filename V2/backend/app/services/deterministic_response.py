"""Evidence-bound deterministic responses for local and outage operation."""
from __future__ import annotations

import re

from app.services.nlp_engine import FALLBACKS
from app.services.response_policy import validate_human_tone, validate_reflective_response


SURROGATES = {
    "PERSON": "someone",
    "ORG": "an organization",
    "GPE": "a place",
    "LOC": "a place",
    "FAC": "a place",
    "EMAIL": "contact information",
    "PHONE": "contact information",
    "URL": "contact information",
    "HANDLE": "contact information",
    "DATE": "a time",
    "TIME": "a time",
}


def _safe_excerpt(analysis: dict) -> str | None:
    evidence=analysis.get("response_evidence") or {}
    span=evidence.get("span")
    text=analysis.get("redacted_text","")
    if not span or len(span)!=2 or not (0<=span[0]<span[1]<=len(text)):
        return None
    excerpt=" ".join(text[span[0]:span[1]].split())
    for mention in analysis.get("mentions",[]):
        a,b=mention.get("span",[0,0])
        if 0<=a<b<=len(text):
            excerpt=excerpt.replace(text[a:b],SURROGATES.get(mention.get("kind",""),"something"))
    excerpt=re.sub(r"\[entity_e\d+\]","something",excerpt)
    excerpt=excerpt.strip(" \t\r\n.!?")
    if len(excerpt)>220:
        excerpt=excerpt[:217].rsplit(" ",1)[0]+"…"
    return excerpt or None


def deterministic_response(analysis: dict) -> str:
    """Produce one conservative reflection using only current user evidence."""
    strategy=analysis.get("strategy","standard")
    if strategy in {"closure","insufficient"}:
        return FALLBACKS[strategy]
    excerpt=_safe_excerpt(analysis)
    if not excerpt:
        return FALLBACKS.get(strategy,FALLBACKS["standard"])
    lead={
        "correction":"You are revising the earlier framing; your current emphasis is",
        "contrast":"The contrast you are emphasizing is",
        "recurring":"This returns to an earlier theme; your current emphasis is",
        "explanation":"The explanation you are offering is",
        "standard":"Your current emphasis is",
    }.get(strategy,"Your current emphasis is")
    candidate=f'{lead}: "{excerpt}."'
    if not validate_reflective_response(candidate).is_valid or not validate_human_tone(candidate).is_valid:
        return FALLBACKS.get(strategy,FALLBACKS["standard"])
    return candidate
