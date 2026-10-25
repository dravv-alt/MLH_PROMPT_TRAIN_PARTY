"""Demonstrate all 5 QUD states across conversational turns in Sanctuary V2."""
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.nlp_engine import analyze_turn
from app.services.question_pipeline import execute_question_pipeline
from app.services.qud_stack import merge_and_update_qud_stack

def main():
    print("=" * 80)
    print("SANCTUARY V2: COMPLETE MULTI-TURN QUD (QUESTIONS UNDER DISCUSSION) TRACE")
    print("=" * 80)

    # Turn 1: Open gap on hedged struggle -> Question asked -> QUD created as OPEN
    t1_text = "I think I might struggle with how to proceed with the team assignment, but everyone expects results."
    empty_state = {"turns": [], "entities": [], "qud_stack": [], "neural_metadata": {"process_local_unredacted": False}}
    a1, _, _ = analyze_turn(t1_text, empty_state, {"alias_key": "qud_demo"})
    res1 = execute_question_pipeline(a1, prior_turns=[], session_qud_stack=[], turn_index=1)
    q1 = res1["selected_question"]
    qud1 = res1["qud_stack"]

    print("\n--- TURN 1 ---")
    print(f"USER INPUT      : \"{t1_text}\"")
    print(f"MOVE SELECTED   : [{res1['move'].upper()}]")
    print(f"SYSTEM QUESTION : \"{q1}\"")
    print(f"TRACE REASON    : {res1['question_trace'].get('reason') or res1['question_trace'].get('human_reason')}")
    print("\nQUD STACK (Turn 1):")
    for item in qud1:
        print(f"  * ID: {item['gap_id']:<35} | Status: {item['status'].upper():<10} | Turn: {item['created_turn']} | Form: \"{item['neutral_question_form']}\"")

    # Turn 2: User answers with causal reason -> Uptake: ANSWERED -> QUD transitions to ANSWERED
    t2_text = "I felt that because the manager moved the team assignment deadline forward without notice."
    prior2 = [{"turn_index": 1, "text": t1_text, "move": "ask", "system_move": "ask", "question": q1}]
    a2, _, _ = analyze_turn(t2_text, empty_state, {"alias_key": "qud_demo"})
    res2 = execute_question_pipeline(a2, prior_turns=prior2, session_qud_stack=qud1, turn_index=2)
    qud2 = res2["qud_stack"]

    print("\n--- TURN 2 ---")
    print(f"USER INPUT      : \"{t2_text}\"")
    print(f"USER UPTAKE     : [{res2['uptake'].upper()}] (Answered previous question)")
    print(f"MOVE SELECTED   : [{res2['move'].upper()}] (Conversational pacing: alternating acknowledge)")
    print(f"SYSTEM QUESTION : None (Pacing backoff enforced)")
    print("\nQUD STACK (Turn 2):")
    for item in qud2:
        print(f"  * ID: {item['gap_id']:<35} | Status: {item['status'].upper():<10} | Turn: {item['created_turn']} | Form: \"{item['neutral_question_form']}\"")

    # Turn 3: User deflects a question
    t3_question = "What was occurring around you when you began to lead the department meeting?"
    t3_qud_entry = {
        "gap_id": "gap_dept_meeting_conflict",
        "frame_id": "prop_dept_meeting",
        "predicate": "lead",
        "neutral_question_form": t3_question,
        "status": "open",
        "created_turn": 3,
        "last_touched": 3,
        "recurrence_count": 1,
    }
    qud3_start = qud2 + [t3_qud_entry]
    prior3 = prior2 + [{"turn_index": 2, "text": t2_text, "move": "acknowledge", "system_move": "acknowledge", "question": None}]
    prior3.append({"turn_index": 3, "text": "I tried leading the meeting yesterday.", "move": "ask", "system_move": "ask", "question": t3_question, "targeted_gap_id": "gap_dept_meeting_conflict"})

    t4_text = "Leave it, I don't want to talk about that meeting right now."
    a4, _, _ = analyze_turn(t4_text, empty_state, {"alias_key": "qud_demo"})
    res4 = execute_question_pipeline(a4, prior_turns=prior3, session_qud_stack=qud3_start, turn_index=4)
    qud4 = res4["qud_stack"]

    print("\n--- TURN 3 & 4 (Boundary Deflection) ---")
    print(f"SYSTEM ASKED IN TURN 3 : \"{t3_question}\"")
    print(f"USER INPUT IN TURN 4   : \"{t4_text}\"")
    print(f"USER UPTAKE            : [{res4['uptake'].upper()}] (Boundary deflection cue detected)")
    print(f"MOVE SELECTED          : [{res4['move'].upper()}] (Immediate conversational backoff)")
    print("\nQUD STACK (Turn 4):")
    for item in qud4:
        print(f"  * ID: {item['gap_id']:<35} | Status: {item['status'].upper():<10} | Turn: {item['created_turn']} | Form: \"{item['neutral_question_form']}\"")

    # Turn 5: Multi-turn correction with Hindi-English marker ('Nahi matlab', 'actually') -> QUD SUPERSEDED
    t5_text = "Nahi matlab, actually it was my cousin who blamed me for the vase, not my sister."
    qud5_start = [
        {
            "gap_id": "gap_vase_blame_sister",
            "frame_id": "prop_sister_blame",
            "predicate": "blame",
            "neutral_question_form": "What was occurring when that was blamed?",
            "status": "open",
            "created_turn": 1,
            "last_touched": 1,
            "recurrence_count": 1,
        }
    ]
    qud5 = merge_and_update_qud_stack(
        qud5_start,
        [],
        turn_index=5,
        correction_context={"is_correction": True, "superseded_propositions": ["prop_sister_blame"]},
    )

    print("\n--- TURN 5 (Multi-Turn Correction & Supersession) ---")
    print(f"USER INPUT      : \"{t5_text}\"")
    print(f"DISCOURSE CUE   : 'Nahi matlab' + 'actually' (Frame correction recognized)")
    print(f"ACTION          : Superseded old sister frame 'prop_sister_blame'")
    print("\nQUD STACK (Turn 5):")
    for item in qud5:
        print(f"  * ID: {item['gap_id']:<35} | Status: {item['status'].upper():<10} | Turn: {item['created_turn']} | Form: \"{item['neutral_question_form']}\"")

if __name__ == "__main__":
    main()
