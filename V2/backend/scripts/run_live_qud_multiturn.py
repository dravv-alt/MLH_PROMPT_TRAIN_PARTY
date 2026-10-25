"""Execute a real multi-turn conversation and inspect the living QUD stack at every turn."""
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.nlp_engine import analyze_turn
from app.services.question_pipeline import execute_question_pipeline

def run_multiturn_session():
    conversation_turns = [
        # Turn 1: Open gap on hedged struggle -> Question asked -> QUD created as OPEN
        "I think I might struggle with how to manage this department assignment, but everyone expects results.",
        # Turn 2: User answers with causal reason -> Uptake: ANSWERED -> QUD transitions to ANSWERED
        "I feel that struggle because the director moved our quarterly deliverable forward by three weeks without warning.",
        # Turn 3: User brings up new concern with unresolved reference -> Question asked -> QUD created as OPEN
        "Someone in leadership told my manager that our department was lagging behind, and they believed it.",
        # Turn 4: User boundary deflection -> Uptake: DEFLECTED -> QUD transitions to DEFLECTED -> Backoff Hold
        "Leave it, I don't want to talk about that person right now.",
        # Turn 5: User corrects prior frame using Hindi-English discourse marker -> QUD SUPERSEDED
        "Nahi matlab, actually it wasn't leadership that started that rumor, it was an external contractor who misspoke.",
        # Turn 6: User returns unprompted to deliverable -> unprompted reopening / resolution
        "Coming back to the three-week deadline, we held a sprint planning session today and rescheduled the sprints."
    ]

    state = {
        "turns": [],
        "entities": [],
        "qud_stack": [],
        "neural_metadata": {"process_local_unredacted": False}
    }
    prior_turns = []
    qud_stack = []

    print("=" * 80)
    print("SANCTUARY V2: MULTI-TURN CONVERSATION WITH LIVE QUD STACK TRACE")
    print("=" * 80)

    for idx, user_text in enumerate(conversation_turns, start=1):
        print(f"\n================================================================================")
        print(f"TURN {idx}")
        print(f"================================================================================")
        print(f"USER INPUT:")
        print(f"  \"{user_text}\"\n")

        analysis, delta, _ = analyze_turn(user_text, state, {"alias_key": "live_qud_demo"})
        pipeline_res = execute_question_pipeline(
            analysis,
            prior_turns=prior_turns,
            session_qud_stack=qud_stack,
            turn_index=idx,
            mode="template_llm_off"
        )

        move = pipeline_res["move"]
        selected_question = pipeline_res.get("selected_question")
        uptake = pipeline_res.get("uptake")
        trace = pipeline_res.get("question_trace", {})
        qud_stack = pipeline_res.get("qud_stack", [])
        gaps = pipeline_res.get("gaps", [])

        print(f"SYSTEM DECISION & OUTPUT:")
        print(f"  Move Selected   : [{move.upper()}]")
        print(f"  User Uptake     : {uptake}")
        if selected_question:
            print(f"  System Question : \"{selected_question}\"")
        else:
            print(f"  System Action   : No question asked (Acknowledge / Hold backoff enforced)")
        print(f"  Grounding Reason: {trace.get('reason') or trace.get('human_reason')}")
        print()

        print(f"ACTIVE DETECTED GAPS THIS TURN ({len(gaps)}):")
        for g in gaps[:3]:
            print(f"  - [{g.get('type')}] on predicate '{g.get('evidence', {}).get('predicate', 'n/a')}' | Salience: {g.get('salience', 0.0)}")
        print()

        print(f"LIVING QUD STACK (Questions Under Discussion) - Total: {len(qud_stack)} items:")
        for q_idx, q in enumerate(qud_stack, start=1):
            q_id = q.get("gap_id")
            status = q.get("status")
            question_form = q.get("neutral_question_form")
            created = q.get("created_turn")
            last_touch = q.get("last_touched")
            recurr = q.get("recurrence_count", 0)
            print(f"  [{q_idx}] QUD ID: {q_id}")
            print(f"      Status       : {status.upper()}")
            print(f"      QUD Question : \"{question_form}\"")
            print(f"      Lifecycle    : Created Turn {created} | Last Touched Turn {last_touch} | Recurrence: {recurr}")
        print()

        # Update prior turns and state
        prior_turns.append({
            "turn_index": idx,
            "text": user_text,
            "move": move,
            "system_move": move,
            "question": selected_question,
            "uptake": uptake
        })
        state["qud_stack"] = qud_stack

if __name__ == "__main__":
    run_multiturn_session()
