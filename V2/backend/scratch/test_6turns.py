import os
import sys
from pathlib import Path
from uuid import uuid4

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(BACKEND_DIR / ".env", override=False)
except Exception:
    pass

from app.models.schemas import ChatRequest
from app.services.nlp_service import get_nlp_service

inputs = [
    "My marks still aren't going up and nobody at home gets it.",
    "Do you even get what I'm saying? You sound like a robot.",
    "Ugh, the landlord won't return my deposit and he's ignoring my calls.",
    "I can't decide whether to take the job in Pune or stay here.",
    "Stop repeating yourself.",
    "My sister called today. We talked for an hour, it was nice."
]

service = get_nlp_service()
user_id = f"test_user_{uuid4().hex[:6]}"
session_id = None

print("=" * 80)
print("REPLAYING 6 INPUTS IN ONE SESSION WITH HOSTED DEFAULT REALIZER")
print("=" * 80)

for idx, user_input in enumerate(inputs, 1):
    req = ChatRequest(
        message=user_input,
        session_id=session_id,
        generation_provider="hosted",
        hosted_consent=True,
        realizer="hosted",
    )
    res = service.chat(user_id, req)
    session_id = res["session_id"]

    raw_output = res.get("response_text")
    producing_path = res.get("realizer")
    move = res.get("nlp_analysis", {}).get("discourse_plan", {}).get("move") or res.get("question_trace", {}).get("move")
    qud = [q.get("qud_text") for q in res.get("qud_stack", [])]

    print(f"\n[Turn {idx}]")
    print(f"User Input:     {user_input}")
    print(f"Move:           {move}")
    print(f"Producing Path: {producing_path}")
    print(f"Raw Output:     {raw_output}")
    print(f"QUD Stack:      {qud}")

print("\n" + "=" * 80)
print("REPLAY COMPLETE")
print("=" * 80)
