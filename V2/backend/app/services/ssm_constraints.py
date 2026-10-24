"""Explicit first-person constraint cues; ordinal engineering scores, not measurements.

Do not infer constraints from role labels, demographics, or another person's
reported emotion. Conflicting poles abstain. Offsets refer to canonical input.
"""
import re

VERSION = 'ssm-constraint-cues.v1'
RULES = {
    'freedom_to_refuse': ((.1, ("i had no choice", "i couldn't refuse", "i could not refuse")),
                          (.9, ("i was free to refuse", "i could freely say no"))),
    'conflict_cost': ((.9, ("i would lose my job if i refused", "i risked retaliation")),
                     (.1, ("i could disagree without consequences",))),
    'relationship_risk': ((.9, ("i feared losing the relationship", "i was afraid they would leave me")),
                         (.1, ("i knew our relationship was safe",))),
    'expectation_pressure': ((.9, ("i felt pressured", "i felt i had to prove myself")),
                             (.1, ("i felt no pressure",))),
    'power_asymmetry': ((.9, ("i had no say in the decision", "i had no control over the decision")),
                        (.1, ("we had equal say",))),
    'emotional_safety': ((.1, ("i felt unsafe speaking up", "i was afraid to speak up")),
                        (.9, ("i felt safe speaking up", "i felt safe expressing myself"))),
}


def constraint_observations(text):
    values, evidence = {}, {}
    for field, poles in RULES.items():
        label = field.replace('_', '[ _]')
        explicit = re.search(rf'\b{label}\s*[:=]\s*(0(?:\.\d+)?|1(?:\.0+)?)(?![\d.])', text, re.I)
        if explicit:
            values[field] = float(explicit.group(1))
            evidence[field] = {'method': 'explicit_self_rating', 'spans': [list(explicit.span())]}
            continue
        matches = []
        for score, phrases in poles:
            for phrase in phrases:
                for hit in re.finditer(rf'(?<!\w){re.escape(phrase)}(?!\w)', text, re.I):
                    # Reject quoted, hypothetical and negated framing conservatively.
                    prefix = re.split(r'[.!?;]', text[:hit.start()])[-1]
                    if re.search(r'\b(?:if|suppose|imagine|not|said|says|wrote)\b|["“]', prefix, re.I):
                        continue
                    matches.append((score, list(hit.span())))
        scores = {score for score, _ in matches}
        values[field] = next(iter(scores)) if len(scores) == 1 else None
        evidence[field] = {'method': 'ordinal_cue' if len(scores) == 1 else 'conflict' if scores else 'unavailable',
                           'spans': [span for _, span in matches]}
    return values, evidence
