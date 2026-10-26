import json
import sys
from pathlib import Path

# Setup paths
BACKEND_DIR = Path(r"c:\Users\bhavv\OneDrive\Desktop\Dravvya(4th Sem)\Projects\MAIN\MAIN\Sanctuary\MLH_PROMPT_TRAIN_PARTY\V2\backend")
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.nlp_service import get_nlp_service
from app.models.schemas import ChatRequest

def run_audit():
    # 1. Read user_prompts only
    jsonl_path = BACKEND_DIR / "evaluation" / "achievement_10turn_reflective_v2.jsonl"
    prompts = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                d = json.loads(line)
                prompts.append((d["turn_id"], d["user_prompt"]))

    print(f"Loaded {len(prompts)} user prompts from {jsonl_path.name}\n")

    service = get_nlp_service()
    user_id = "live_audit_user_001"
    session_id = None

    results = []

    for turn_id, user_prompt in prompts:
        print(f"==================== TURN {turn_id} ====================")
        print(f"USER PROMPT: {user_prompt}\n")

        req = ChatRequest(
            message=user_prompt,
            session_id=session_id,
            generation_provider="local",
        )

        res = service.chat(user_id=user_id, payload=req)
        session_id = res["session_id"]

        reply = res.get("response_text")
        display_reply = res.get("display_response_text")
        analysis = res.get("nlp_analysis") or {}
        qtrace = res.get("question_trace") or analysis.get("question_trace") or {}
        move = qtrace.get("move") or res.get("safety_mode")
        target_gap_id = qtrace.get("gap_id")
        trace_spans = qtrace.get("spans")
        qud_stack = res.get("qud_stack") or []

        print(f"REPLY (Stored response_text): {reply}")
        print(f"DISPLAY REPLY               : {display_reply}")
        print(f"MOVE                        : {move}")
        print(f"TARGET GAP_ID               : {target_gap_id}")
        print(f"TRACE SPANS                 : {trace_spans}")
        print(f"QUESTION TRACE REASON       : {qtrace.get('reason') or qtrace.get('human_reason')}")
        print(f"FULL QUD STACK ({len(qud_stack)} items):")
        for idx, item in enumerate(qud_stack, 1):
            status = item.get("status", "unknown").upper()
            form = item.get("neutral_question_form", "")
            gid = item.get("gap_id", "")
            c_turn = item.get("created_turn", "")
            touched = item.get("last_touched", "")
            rec = item.get("recurrence_count", "")
            print(f"   [{idx}] ID: {gid:<36} | Status: {status:<10} | Created: T{c_turn} | Touched: T{touched} | Rec: {rec} | Form: \"{form}\"")
        print("\n")

        results.append({
            "turn_id": turn_id,
            "user_prompt": user_prompt,
            "reply": reply,
            "display_reply": display_reply,
            "move": move,
            "target_gap_id": target_gap_id,
            "trace_spans": trace_spans,
            "qud_stack": qud_stack,
            "question_trace": qtrace,
        })

    # Save raw audit output to json for report verification
    out_path = BACKEND_DIR / "evaluation" / "live_audit_run_results.json"
    with open(out_path, "w", encoding="utf-8") as out_f:
        json.dump(results, out_f, indent=2)
    print(f"Audit results written to {out_path}")

if __name__ == "__main__":
    run_audit()
