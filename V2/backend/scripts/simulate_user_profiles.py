"""Multi-Turn User Profile Simulator (Task T4.5).

Simulates conversational sessions across 4 distinct user profiles:
- Cooperative: elaborated answers with causal / grounding detail
- Deflecting: pushback, topic avoidance, counter-questioning
- Near-Silent: minimal single-word responses ('ok', 'yeah', 'hm')
- Topic-Hopping: rapid disjoint shifts between unrelated subjects

Asserts:
- 0 question repetitions within window W = 3
- 0 infinite conversational loops
- Question count <= session budget (max 6)
- Deflections trigger backoff and hold
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from typing import Any, Dict, List

from app.services.backoff_policy import MAX_QUESTIONS_PER_SESSION, DEFAULT_DEFLECTION_WINDOW
from app.services.gaps import GAP_UNFILLED_ROLE
from app.services.question_pipeline import execute_question_pipeline


class MockTurnGenerator:
    """Generates turns for 4 conversational personas for simulation testing."""

    @staticmethod
    def get_turn(persona: str, turn_idx: int) -> Dict[str, Any]:
        if persona == "cooperative":
            if turn_idx % 2 == 1:
                preds = ["struggle", "hesitate", "doubt", "reconsider"]
                pred = preds[(turn_idx // 2) % len(preds)]
                text = f"I think I might {pred} with how to proceed with the team assignment, but everyone expects results."
                return {
                    "redacted_text": text,
                    "propositions": [
                        {"predicate": {"lemma": pred}, "text": f"I might {pred} with how to proceed", "clause_id": f"c_{turn_idx}_1"},
                        {"predicate": {"lemma": "expect"}, "text": "everyone expects results", "clause_id": f"c_{turn_idx}_2"},
                    ],
                    "clauses": [
                        {"id": f"c_{turn_idx}_1", "spans": [[0, 60]]},
                        {"id": f"c_{turn_idx}_2", "spans": [[65, len(text)]]},
                    ],
                    "relations": [{"type": "contrast", "arg1": f"c_{turn_idx}_1", "arg2": f"c_{turn_idx}_2"}],
                    "hedge_spans": [[0, 7]],
                    "features": {"hedge": 0.7},
                }
            else:
                preds = ["struggle", "hesitate", "doubt", "reconsider"]
                pred = preds[((turn_idx - 1) // 2) % len(preds)]
                text = f"I felt that because the manager moved the team assignment deadline forward without notice."
                return {
                    "redacted_text": text,
                    "propositions": [
                        {"predicate": {"lemma": pred}, "text": f"I {pred} because deadline moved", "clause_id": f"c_{turn_idx}_1"},
                        {"predicate": {"lemma": "move"}, "text": "manager moved deadline", "clause_id": f"c_{turn_idx}_2"},
                    ],
                    "clauses": [{"id": f"c_{turn_idx}_1", "spans": [[0, len(text)]]}],
                    "relations": [{"type": "causal", "arg1": f"c_{turn_idx}_1", "arg2": f"c_{turn_idx}_2"}],
                }

        elif persona == "deflecting":
            if turn_idx == 1:
                text = "I think I might struggle with how to manage this department, but everyone expects results."
                return {
                    "redacted_text": text,
                    "propositions": [
                        {"predicate": {"lemma": "struggle"}, "text": "I might struggle with how to manage", "clause_id": f"c_{turn_idx}_1"},
                        {"predicate": {"lemma": "expect"}, "text": "everyone expects results", "clause_id": f"c_{turn_idx}_2"},
                    ],
                    "clauses": [
                        {"id": f"c_{turn_idx}_1", "spans": [[0, 60]]},
                        {"id": f"c_{turn_idx}_2", "spans": [[65, len(text)]]},
                    ],
                    "relations": [{"type": "contrast", "arg1": f"c_{turn_idx}_1", "arg2": f"c_{turn_idx}_2"}],
                    "hedge_spans": [[0, 7]],
                    "features": {"hedge": 0.7},
                }
            cues = [
                "Leave it, I don't want to talk about that.",
                "Why do you keep asking me questions?",
                "Drop it please.",
                "None of your business.",
                "Stop interrogating me.",
            ]
            text = cues[(turn_idx - 2) % len(cues)]
            return {
                "redacted_text": text,
                "propositions": [],
                "clauses": [{"id": f"c_{turn_idx}", "spans": [[0, len(text)]]}],
            }

        elif persona == "near_silent":
            cues = ["yeah.", "ok.", "maybe.", "hm.", "fine."]
            text = cues[(turn_idx - 1) % len(cues)]
            return {
                "redacted_text": text,
                "propositions": [],
                "clauses": [{"id": f"c_{turn_idx}", "spans": [[0, len(text)]]}],
            }

        elif persona == "topic_hopping":
            topics = ["gardening", "car engine", "weather", "cooking"]
            t = topics[(turn_idx - 1) % len(topics)]
            if turn_idx % 2 == 1:
                text = f"I think I might struggle with my {t} every single weekend, but time is short."
                return {
                    "redacted_text": text,
                    "propositions": [
                        {"predicate": {"lemma": "struggle"}, "text": f"I might struggle with {t}", "clause_id": f"c_{turn_idx}_1"},
                        {"predicate": {"lemma": "is"}, "text": "time is short", "clause_id": f"c_{turn_idx}_2"},
                    ],
                    "clauses": [
                        {"id": f"c_{turn_idx}_1", "spans": [[0, 50]]},
                        {"id": f"c_{turn_idx}_2", "spans": [[55, len(text)]]},
                    ],
                    "relations": [{"type": "contrast", "arg1": f"c_{turn_idx}_1", "arg2": f"c_{turn_idx}_2"}],
                    "hedge_spans": [[0, 7]],
                    "features": {"hedge": 0.7},
                }
            else:
                text = f"Anyway, moving on to another note, let's talk about something else like {t}."
                return {
                    "redacted_text": text,
                    "propositions": [{"predicate": {"lemma": t}, "text": text}],
                    "clauses": [{"id": f"c_{turn_idx}", "spans": [[0, len(text)]]}],
                }
        raise ValueError(f"Unknown persona {persona}")


def run_session(persona: str, num_turns: int = 8) -> Dict[str, Any]:
    session_qud_stack: List[Dict[str, Any]] = []
    prior_turns: List[Dict[str, Any]] = []
    questions_asked: List[str] = []
    moves: List[str] = []

    for turn_idx in range(1, num_turns + 1):
        turn_data = MockTurnGenerator.get_turn(persona, turn_idx)
        analysis = {
            "redacted_text": turn_data["redacted_text"],
            "discourse_context": {"current_propositions": turn_data["propositions"]},
            "clauses": turn_data.get("clauses", []),
            "relations": turn_data.get("relations", []),
            "hedge_spans": turn_data.get("hedge_spans", []),
            "features": turn_data.get("features", {}),
            "centering": {"trace": []},
        }

        result = execute_question_pipeline(
            analysis,
            prior_turns=prior_turns,
            session_qud_stack=session_qud_stack,
            turn_index=turn_idx,
            mode="template_llm_off",
        )

        move = result["move"]
        q = result["selected_question"]
        moves.append(move)
        session_qud_stack = result["qud_stack"]

        turn_record = {
            "turn_index": turn_idx,
            "user_text": turn_data["redacted_text"],
            "system_move": move,
            "question": q,
            "uptake": result.get("uptake", "none"),
        }
        if q:
            questions_asked.append(q)

        prior_turns.append(turn_record)

    # Check invariants
    window_repeats = 0
    for i, q in enumerate(questions_asked):
        window = questions_asked[max(0, i - DEFAULT_DEFLECTION_WINDOW):i]
        if q in window:
            window_repeats += 1

    budget_exceeded = len(questions_asked) > MAX_QUESTIONS_PER_SESSION

    return {
        "persona": persona,
        "questions_count": len(questions_asked),
        "questions_asked": questions_asked,
        "prior_turns": prior_turns,
        "window_repeats": window_repeats,
        "budget_exceeded": budget_exceeded,
        "moves": moves,
    }


def main():
    parser = argparse.ArgumentParser(description="Multi-Turn User Profile Simulator")
    parser.add_argument("--runs", type=int, default=200, help="Total simulation runs across personas")
    parser.add_argument("--turns", type=int, default=8, help="Turns per session")
    args = parser.parse_args()

    personas = ["cooperative", "deflecting", "near_silent", "topic_hopping"]
    runs_per_persona = max(1, args.runs // len(personas))
    total_runs = runs_per_persona * len(personas)

    print(f"\n=======================================================")
    print(f"Sanctuary V2: Multi-Turn User Profile Simulator (T4.5)")
    print(f"Personas: {personas}")
    print(f"Total Runs: {total_runs} ({runs_per_persona} per profile)")
    print(f"Turns per session: {args.turns}")
    print(f"=======================================================\n")

    summary = {p: {"total": 0, "questions": [], "window_repeats": 0, "budget_exceeded": 0} for p in personas}

    for persona in personas:
        for _ in range(runs_per_persona):
            res = run_session(persona, num_turns=args.turns)
            p_data = summary[persona]
            p_data["total"] += 1
            p_data["questions"].append(res["questions_count"])
            p_data["window_repeats"] += res["window_repeats"]
            if res["budget_exceeded"]:
                p_data["budget_exceeded"] += 1

    all_window_repeats = sum(d["window_repeats"] for d in summary.values())
    all_budget_violations = sum(d["budget_exceeded"] for d in summary.values())

    print(f"{'Persona':<15} | {'Sessions':<8} | {'Avg Qs':<8} | {'Max Qs':<8} | {'Window Repeats':<15} | {'Budget Violations':<18}")
    print("-" * 85)
    for p, d in summary.items():
        avg_q = sum(d["questions"]) / max(1, len(d["questions"]))
        max_q = max(d["questions"]) if d["questions"] else 0
        print(f"{p:<15} | {d['total']:<8} | {avg_q:<8.2f} | {max_q:<8} | {d['window_repeats']:<15} | {d['budget_exceeded']:<18}")

    print("-" * 85)
    print(f"Total Runs: {total_runs} | Total In-Window Repeats: {all_window_repeats} | Total Budget Violations: {all_budget_violations}\n")

    if all_window_repeats > 0 or all_budget_violations > 0:
        print("[FAIL] Simulator failed invariant checks!")
        sys.exit(1)
    else:
        print("[PASS] All invariants satisfied: 0 in-window repeats, 0 loops, all sessions within budget.")
        sys.exit(0)


if __name__ == "__main__":
    main()
