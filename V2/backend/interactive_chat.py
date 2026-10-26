#!/usr/bin/env python
"""Sanctuary V2 Interactive Terminal Chat Runner.

Run:
    python interactive_chat.py
    python interactive_chat.py --simple
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scripts.interactive_chat import parse_args, run_interactive_terminal

if __name__ == "__main__":
    args = parse_args()
    run_interactive_terminal(simple=args.simple, realizer=args.realizer, hosted_consent=args.hosted_consent)
