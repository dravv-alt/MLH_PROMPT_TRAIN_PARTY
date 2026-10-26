import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.nlp_service import get_nlp_service
from app.models.schemas import ChatRequest

prompts = [
    "I am tired of this bullshit antigravity gemini mmodels fucking up my project. I have been trying to completely execute my projects since weeks and months and it still hasn't been completely executed. There's no fucking anything is working.",
    "I don't know what to do , I am just tired of this project getting stalled indefinitiely",
    "What the fuck do you understand??",
    "But what are you listening???",
    "WHAT THE FUCK JUST REPLY NORMAALLY FOR GOD'S FUCKING SAKE ONCE."
]

service = get_nlp_service()
sid = None
for i, p in enumerate(prompts, 1):
    req = ChatRequest(message=p, session_id=sid, generation_provider="local")
    res = service.chat(user_id="diag_user_5turns", payload=req)
    sid = res["session_id"]
    tr = res.get("question_trace") or {}
    print(f"=== TURN {i} ===")
    print(f"Prompt   : {p}")
    print(f"Reply    : {res.get('response_text')}")
    print(f"Mode     : {res.get('safety_mode')}")
    print(f"Move     : {tr.get('move')}")
    print(f"Target   : {tr.get('gap_id')}")
    print(f"Reason   : {tr.get('reason') or tr.get('human_reason')}")
    print(f"Gaps     : {[g.get('type') for g in res.get('gaps', [])]}")
    print()
