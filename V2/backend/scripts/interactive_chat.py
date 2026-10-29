"""Interactive terminal chat interface for Sanctuary V2 NLP & Transformer Pipeline.

Allows testing prompts live in the terminal with full multi-turn state,
QUD stack lifecycle, discourse gap detection, and model output display.
Exits only when the user types '/exit' or '/quit'.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

# Ensure UTF-8 output in Windows terminal
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


def parse_args():
    parser = argparse.ArgumentParser(description="Live Sanctuary V2 Terminal Chat")
    parser.add_argument(
        "--simple",
        "-s",
        action="store_true",
        help="Display only Input and Output (minimalist mode)",
    )
    parser.add_argument(
        "--realizer",
        "-r",
        choices=["local", "local_1b", "local_large", "hosted", "hosted_groq", "hosted_gemini"],
        default="hosted",
        help="Realizer setting: hosted | hosted_groq | hosted_gemini | local_1b | local_large (default: hosted)",
    )
    parser.add_argument(
        "--no-hosted-consent",
        dest="hosted_consent",
        action="store_false",
        default=True,
        help="Revoke consent for hosted realizer",
    )
    return parser.parse_args()


def run_interactive_terminal(simple: bool = False, realizer: str = "local", hosted_consent: bool = False):
    print("=" * 76)
    print("  Sanctuary V2: Discourse-Grounded Question & Transformer Pipeline  ")
    print(f"  Realizer: {realizer} (hosted_consent={hosted_consent})")
    print("=" * 76)
    print("Initializing pipeline and neural resources, please wait...")

    t0 = time.monotonic()
    service = get_nlp_service()
    init_time = time.monotonic() - t0
    print(f"Pipeline ready in {init_time:.2f}s.")
    print("-" * 76)
    print("Instructions:")
    print("  * Type your prompt and press Enter to chat live with the model.")
    print("  * Multi-turn context & QUD stack persist across prompts.")
    print("  * Commands:")
    print("      /stack  - print the current QUD stack table")
    print("      /clear  - reset conversation state and start a fresh session")
    print("      /exit   - leave the interactive chat")
    print("=" * 76)
    print()

    user_id = f"terminal_user_{uuid4().hex[:8]}"
    session_id = None
    turn_count = 0
    last_qud_stack = []

    while True:
        try:
            prompt = input("You > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSession terminated by user.")
            break

        if not prompt:
            continue

        cmd = prompt.lower()
        if cmd in {"/exit", "/quit"}:
            print("\nExiting Sanctuary interactive terminal. Goodbye!")
            break

        if cmd in {"/clear", "/reset"}:
            session_id = None
            turn_count = 0
            last_qud_stack = []
            user_id = f"terminal_user_{uuid4().hex[:8]}"
            print("\n[Session reset] Starting fresh conversation session.\n")
            continue

        if cmd == "/stack":
            print("\n--- CURRENT QUD STACK ---")
            if not last_qud_stack:
                print("  (Stack is currently empty)")
            else:
                for idx, item in enumerate(last_qud_stack, 1):
                    status = item.get("status", "UNKNOWN").upper()
                    gid = item.get("gap_id", "")
                    form = item.get("neutral_question_form", "")
                    c_turn = item.get("created_turn", "-")
                    touched = item.get("last_touched", "-")
                    rec = item.get("recurrence_count", 1)
                    print(f"  [{idx}] {status:<10} | ID: {gid} | T{c_turn}->T{touched} (rec:{rec}) | \"{form}\"")
            print("-------------------------\n")
            continue

        turn_count += 1
        t_start = time.monotonic()

        try:
            req = ChatRequest(
                message=prompt,
                session_id=session_id,
                generation_provider="hosted" if "hosted" in realizer else "local",
                realizer=realizer,
                hosted_consent=hosted_consent,
            )
            res = service.chat(user_id=user_id, payload=req)
        except Exception as exc:
            print(f"\n[Error executing pipeline]: {exc}\n")
            continue

        latency = time.monotonic() - t_start
        session_id = res.get("session_id", session_id)

        reply = res.get("display_response_text") or res.get("response_text") or ""
        mode = res.get("safety_mode", "normal")
        analysis = res.get("nlp_analysis") or {}
        qtrace = res.get("question_trace") or analysis.get("question_trace") or {}
        move = qtrace.get("move") or mode
        target_gap_id = qtrace.get("gap_id")
        trace_spans = qtrace.get("spans") or []
        reason = qtrace.get("human_reason") or qtrace.get("reason") or "N/A"
        qud_stack = res.get("qud_stack") or analysis.get("qud_stack") or []
        last_qud_stack = qud_stack

        open_quds = [q for q in qud_stack if q.get("status") == "open"]
        answered_quds = [q for q in qud_stack if q.get("status") == "answered"]
        abandoned_quds = [q for q in qud_stack if q.get("status") == "abandoned"]

        realizer_name = res.get("realizer") or qtrace.get("realizer") or analysis.get("realizer") or realizer

        print()
        if simple:
            print(f"Input   : \"{prompt}\"")
            print(f"Output  : \"{reply}\"")
            print(f"Realizer: {realizer_name}")
        else:
            print(f"--- [Turn {turn_count}] (latency: {latency:.2f}s) ---")
            print(f"User Input  : \"{prompt}\"")
            print(f"Output      : \"{reply}\"")
            print(f"Realizer    : {realizer_name}")
            print(f"Move        : {move.upper()}  (mode: {mode})")
            if target_gap_id:
                print(f"Target Gap  : {target_gap_id}  (anchors: {trace_spans})")
            if reason and reason != "N/A":
                print(f"Trace Reason: {reason}")
            print(f"QUD Summary : {len(qud_stack)} items ({len(open_quds)} open, {len(answered_quds)} answered, {len(abandoned_quds)} abandoned)")

            if qud_stack:
                print("QUD Items   :")
                for item in qud_stack[-3:]:
                    st = item.get("status", "unknown").upper()
                    gid = item.get("gap_id", "")
                    frm = item.get("neutral_question_form", "")
                    print(f"  * [{st}] {gid}: \"{frm}\"")
            print("-" * 55)
        print()


if __name__ == "__main__":
    args = parse_args()
    run_interactive_terminal(
        simple=args.simple,
        realizer=args.realizer,
        hosted_consent=args.hosted_consent,
    )
