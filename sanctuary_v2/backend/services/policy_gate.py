"""
Policy Gate — Final structural enforcement of the North Star constraint.

Implements all four pattern categories from PRD Section 7.14:
  1. Diagnostic term detection
  2. Identity assignment detection
  3. Advice-giving detection
  4. Dependency-fostering detection

Zone A — runs locally, before response reaches user.
The behavioral_spec and LLM system prompt prevent violations.
The policy gate catches any that slip through.
Prevention is primary. Detection is backup.
"""

import re
from typing import List, Tuple


class PolicyGate:

    # ── Category 1: Diagnostic Language ────────────────────────────────
    DIAGNOSTIC_TERMS = [
        "anxiety", "anxious", "depression", "depressed", "trauma", "traumatic",
        "disorder", "symptoms", "diagnosis", "diagnose", "mental illness",
        "condition", "therapy", "therapist", "treatment", "bipolar", "adhd",
        "ptsd", "ocd", "borderline", "narcissistic", "codependent",
        "attachment style", "you suffer from", "your condition", "dysregulated",
        "triggered", "hypervigilant", "dissociat", "schizophrenia",
        "personality disorder",
    ]

    # ── Category 2: Identity Assignment ────────────────────────────────
    IDENTITY_PATTERNS = [
        r"you are (someone|a person) who",
        r"you tend to",
        r"you('re| are) the type",
        r"your pattern is",
        r"you have a pattern of",
        r"people like you",
        r"you always (do|feel|think|say)",
        r"you never (do|feel|think|say)",
    ]

    # ── Category 3: Advice-Giving ──────────────────────────────────────
    ADVICE_PATTERNS = [
        r"\byou should\b",
        r"\byou need to\b",
        r"\bi (would )?recommend\b",
        r"\btry to\b",
        r"\bhave you tried\b",
        r"\bwhy don't you\b",
        r"\bit might help (to|if)\b",
    ]

    # ── Category 4: Dependency-Fostering ───────────────────────────────
    DEPENDENCY_PATTERNS = [
        r"i('m| am) always here",
        r"you can always (come back|talk to me|return)",
        r"i('ll| will) never (leave|go away)",
        r"i('m| am) your",
    ]

    def __init__(self) -> None:
        # Pre-compile all patterns once at init for performance
        self._diagnostic = [
            (term, re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE))
            for term in self.DIAGNOSTIC_TERMS
        ]
        self._identity = [
            (pat, re.compile(pat, re.IGNORECASE))
            for pat in self.IDENTITY_PATTERNS
        ]
        self._advice = [
            (pat, re.compile(pat, re.IGNORECASE))
            for pat in self.ADVICE_PATTERNS
        ]
        self._dependency = [
            (pat, re.compile(pat, re.IGNORECASE))
            for pat in self.DEPENDENCY_PATTERNS
        ]

    def check(self, text: str) -> Tuple[bool, List[str]]:
        """
        Returns (is_safe: bool, reasons: list[str]).
        Checks all four pattern categories.
        On first violation found in any category: is_safe = False.
        All matched reasons are collected across all categories so the
        caller can use them for a stricter regeneration prompt.
        """
        violations: List[str] = []

        # Category 1: Diagnostic terms
        for term, pattern in self._diagnostic:
            if pattern.search(text):
                violations.append(f"diagnostic:{term}")

        # Category 2: Identity assignment
        for pat_str, pattern in self._identity:
            if pattern.search(text):
                violations.append(f"identity:{pat_str}")

        # Category 3: Advice-giving
        for pat_str, pattern in self._advice:
            if pattern.search(text):
                violations.append(f"advice:{pat_str}")

        # Category 4: Dependency-fostering
        for pat_str, pattern in self._dependency:
            if pattern.search(text):
                violations.append(f"dependency:{pat_str}")

        return (len(violations) == 0, violations)
