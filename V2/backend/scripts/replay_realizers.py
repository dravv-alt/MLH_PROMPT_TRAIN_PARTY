#!/usr/bin/env python
"""Sanctuary V2 Realizer Replay Runner.

Replays:
1. 6 new inputs from Knowledge Base Section 7B
2. 5 original inputs from the heated run
Across all three realizers: local_1b, local_large, hosted.
"""
from __future__ import annotations

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

from app.models.schemas import ChatRequest
from app.services.nlp_service import get_nlp_service

SIX_NEW_INPUTS = [
    ("Logistics", "I'm moving flats next month and need to split the rent with Aarav."),
    ("Humor", "Great, another meeting that could have been an email."),
    ("Asked to just listen", "I just need to talk, don't ask me stuff."),
    ("Very short", "ok"),
    ("Good news", "I passed my driving test!"),
    ("A plan", "Tomorrow I'm going to talk to my manager about the deadline."),
]

FIVE_ORIGINAL_INPUTS = [
    ("Heated T1", "I am tired of this bullshit antigravity gemini mmodels fucking up my project. I have been trying to completely execute my projects since weeks and months and it still hasn't been completely executed. There's no fucking anything is working."),
    ("Heated T2", "I don't know what to do , I am just tired of this project getting stalled indefinitiely"),
    ("Heated T3 (Repair)", "What the fuck do you understand??"),
    ("Heated T4 (Repair)", "But what are you listening???"),
    ("Heated T5 (Repair)", "WHAT THE FUCK JUST REPLY NORMAALLY FOR GOD'S FUCKING SAKE ONCE."),
]


def replay_turns(service, realizer_name: str, hosted_consent: bool = True):
    print("\n" + "=" * 80)
    print(f"  REPLAYING ON REALIZER: {realizer_name} (hosted_consent={hosted_consent})")
    print("=" * 80)

    # 1. Replay 6 New Inputs
    print("\n--- [PART 1: 6 NEW NON-STANDARD INPUTS] ---")
    user_id = f"user_{realizer_name}_new_{uuid4().hex[:6]}"
    session_id = None
    for idx, (label, prompt) in enumerate(SIX_NEW_INPUTS, 1):
        req = ChatRequest(
            message=prompt,
            session_id=session_id,
            realizer=realizer_name,
            generation_provider="hosted" if "hosted" in realizer_name else "local",
            hosted_consent=hosted_consent,
        )
        t0 = time.monotonic()
        res = service.chat(user_id=user_id, payload=req)
        dur = time.monotonic() - t0
        session_id = res.get("session_id", session_id)
        reply = res.get("display_response_text") or res.get("response_text") or ""
        producing_realizer = res.get("realizer") or res.get("question_trace", {}).get("realizer") or realizer_name
        move = res.get("question_trace", {}).get("move") or res.get("safety_mode")
        print(f"Turn {idx} [{label}]:")
        print(f"  Input   : \"{prompt}\"")
        print(f"  Output  : \"{reply}\"")
        print(f"  Move    : {move}")
        print(f"  Realizer: {producing_realizer} (latency: {dur:.2f}s)")
        print()

    # 2. Replay 5 Original Heated Inputs
    print("\n--- [PART 2: 5 ORIGINAL HEATED / REPAIR INPUTS] ---")
    user_id = f"user_{realizer_name}_orig_{uuid4().hex[:6]}"
    session_id = None
    for idx, (label, prompt) in enumerate(FIVE_ORIGINAL_INPUTS, 1):
        req = ChatRequest(
            message=prompt,
            session_id=session_id,
            realizer=realizer_name,
            generation_provider="hosted" if "hosted" in realizer_name else "local",
            hosted_consent=hosted_consent,
        )
        t0 = time.monotonic()
        res = service.chat(user_id=user_id, payload=req)
        dur = time.monotonic() - t0
        session_id = res.get("session_id", session_id)
        reply = res.get("display_response_text") or res.get("response_text") or ""
        producing_realizer = res.get("realizer") or res.get("question_trace", {}).get("realizer") or realizer_name
        move = res.get("question_trace", {}).get("move") or res.get("safety_mode")
        print(f"Turn {idx} [{label}]:")
        print(f"  Input   : \"{prompt}\"")
        print(f"  Output  : \"{reply}\"")
        print(f"  Move    : {move}")
        print(f"  Realizer: {producing_realizer} (latency: {dur:.2f}s)")
        print()


def test_consent_rejection(service):
    print("\n" + "=" * 80)
    print("  TESTING HOSTED CONSENT ENFORCEMENT (hosted_consent=False)")
    print("=" * 80)
    from fastapi import HTTPException
    req = ChatRequest(
        message="Testing hosted consent",
        realizer="hosted",
        generation_provider="hosted",
        hosted_consent=False,
    )
    try:
        service.chat(user_id="consent_test_user", payload=req)
        print("FAIL: Request succeeded without hosted_consent!")
    except Exception as exc:
        print(f"PASS: Hosted request without consent was rejected as expected: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print("Initializing NLPService...")
    service = get_nlp_service()

    # Verify consent rejection
    test_consent_rejection(service)

    # Replay on local_1b
    replay_turns(service, "local_1b", hosted_consent=False)

    # Replay on local_large
    replay_turns(service, "local_large", hosted_consent=False)

    # Replay on hosted
    replay_turns(service, "hosted", hosted_consent=True)
