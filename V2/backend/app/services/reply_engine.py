"""reply_engine.py - drop-in reply engine for Sanctuary V2.

Plan in code, phrase with an LLM, verify in code, never restate.

Public API
    choose_move(text, history, pipeline_move=None, correction=False) -> (move, reason)
    pick_nucleus(text) -> str
    generate_reply(user_text, move=..., llm_call=..., ...) -> dict
    check_reply(reply, move, user_text, all_user_text, closed, recent_replies) -> list[str]

Run `python reply_engine.py` to execute the offline self-test (no network, no model).
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Callable, Dict, List, Optional, Sequence, Tuple

Message = Dict[str, str]
LLMCall = Callable[[List[Message]], str]

# --------------------------------------------------------------------------- #
# Small shared helpers
# --------------------------------------------------------------------------- #

STOP = set(
    """a an the and or but if then so to of in on at by for with from as is are was were be been
    being am i me my mine we our you your he she it its they them their this that these those
    there here do does did have has had will would can could should may might must not no yes
    just very really also too than about into out up down over after before again still even
    only more most much many some any all each every what which who whom whose when where why
    how""".split()
)


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9']+", (text or "").lower())


def _content(tokens: Sequence[str]) -> List[str]:
    return [t for t in tokens if len(t) > 2 and t not in STOP]


# --------------------------------------------------------------------------- #
# 1. Nucleus: which clause carries the weight (grammar cues only, no emotion lexicon)
# --------------------------------------------------------------------------- #

CONTRAST_LEAD = re.compile(r"^(but|however|though|although|yet|still)\b", re.I)
UNIVERSAL_NEG = re.compile(r"\b(nothing|never|no one|nobody|none|nowhere|even if|no matter)\b", re.I)
COUNTERFACTUAL = re.compile(
    r"\b(wish(?:ed)?|if only|should have|shouldn't have|could have|would have|go back)\b", re.I
)
VOLITION = re.compile(
    r"\b(want|wanted|wish|wished|gotta|need to|needs to|feel like|feels like|hope|hoping|"
    r"can't|cannot|don't want|do not want|i'd like|would like)\b",
    re.I,
)
UNCERTAIN = re.compile(r"\b(not sure|unsure|uncertain|don't know|do not know|no idea|can't tell)\b", re.I)


def split_clauses(text: str) -> List[str]:
    out: List[str] = []
    for sent in re.split(r"(?<=[.!?])\s+|\n+", (text or "").strip()):
        sent = sent.strip()
        if not sent:
            continue
        for part in re.split(r"[,;]?\s+(?=(?:but|however|though|although|yet)\b)", sent, flags=re.I):
            part = part.strip(" ,;")
            if not part:
                continue
            if len(part.split()) > 18:
                subs = [p.strip(" ,;") for p in re.split(r",\s+", part) if len(p.split()) >= 3]
                out.extend(subs or [part])
            else:
                out.append(part)
    return out


def _bigrams(toks: Sequence[str]):
    return list(zip(toks, toks[1:]))


def nucleus_info(text: str) -> Tuple[str, str]:
    """Return (clause, type). Ties go to the later clause."""
    clauses = split_clauses(text)
    if not clauses:
        return (text or "").strip(), "plain"
    counts = Counter(_bigrams(_content(_tokens(text))))
    best, best_score = clauses[-1], float("-inf")
    for i, c in enumerate(clauses):
        s = 0.0
        if CONTRAST_LEAD.match(c):
            s += 2
        if UNIVERSAL_NEG.search(c):
            s += 1.5
        if COUNTERFACTUAL.search(c):
            s += 2
        if VOLITION.search(c):
            s += 1
        if UNCERTAIN.search(c):
            s += 1
        if any(counts[b] > 1 for b in _bigrams(_content(_tokens(c)))):
            s += 1.5
        if i == len(clauses) - 1:
            s += 0.5
        w = len(c.split())
        if w < 4:
            s -= 2
        if w > 30:
            s -= 1
        if s >= best_score:
            best, best_score = c, s
    return best, nucleus_type(best)


def pick_nucleus(text: str) -> str:
    return nucleus_info(text)[0]


def nucleus_type(c: str) -> str:
    if COUNTERFACTUAL.search(c):
        return "counterfactual"
    if UNIVERSAL_NEG.search(c):
        return "universal"
    if UNCERTAIN.search(c):
        return "uncertain"
    if VOLITION.search(c):
        return "volition"
    return "plain"


# --------------------------------------------------------------------------- #
# 2. Move choice: default is ASK. Acknowledge/hold only on structural settle cues.
# --------------------------------------------------------------------------- #

HOLD_REQ = re.compile(
    r"\b(just let me (talk|vent|speak)|don'?t ask|stop asking|no questions|just listen|let me finish)\b", re.I
)
SUMMARY = re.compile(
    r"\b(if i had to (describe|sum)|to sum up|overall|in the end|looking back|all in all|so basically|the whole thing)\b",
    re.I,
)
MAX_CONSECUTIVE_ASKS = 3
MAX_ASKS_PER_SESSION = 8


def choose_move(
    text: str,
    history: Sequence[Dict],
    pipeline_move: Optional[str] = None,
    correction: bool = False,
) -> Tuple[str, str]:
    """history items: {"move": str, "reply": str, "uptake": Optional[str]}"""
    if pipeline_move == "safety_interrupt":
        return "safety_interrupt", "safety path"
    if HOLD_REQ.search(text or ""):
        return "hold", "user asked not to be questioned"
    if pipeline_move == "repair":
        return "repair", "challenge aimed at the system"
    if len((text or "").split()) < 4:
        return "hold", "very short turn"
    if SUMMARY.search(text or ""):
        return "acknowledge", "user is wrapping up"
    if correction:
        return "acknowledge", "a correction just landed"
    asks = [h for h in history if h.get("move") in ("ask", "clarify")]
    tail = list(history)[-MAX_CONSECUTIVE_ASKS:]
    if len(tail) == MAX_CONSECUTIVE_ASKS and all(h.get("move") in ("ask", "clarify") for h in tail):
        return "acknowledge", "three questions in a row"
    if history and history[-1].get("uptake") == "deflected":
        return "acknowledge", "last question was deflected"
    if len(asks) >= MAX_ASKS_PER_SESSION:
        return "acknowledge", "question budget used"
    if pipeline_move == "clarify":
        return "clarify", "ambiguity blocks understanding"
    return "ask", "default: unsettled turn"


# --------------------------------------------------------------------------- #
# 3. Gate: verify the reply in code before it is shown
# --------------------------------------------------------------------------- #

CANNED = [
    re.compile(p, re.I)
    for p in [
        r"\bi understand\b", r"\bi hear you\b", r"\bthat sounds\b", r"\bit sounds like\b",
        r"\bi'?m sorry\b", r"\bi am sorry\b", r"\btake (all )?(your|the) time\b", r"\bi'?m here\b",
        r"\bi'?m listening\b", r"\bthat'?s valid\b", r"\byou'?re not alone\b", r"\bapolog",
    ]
]
PRESUP = [
    re.compile(p, re.I)
    for p in [
        r"\bbegan to\b", r"\bstarted to\b", r"\bstopped\b", r"\bwhat made you\b", r"\bwhy did\b",
        r"\bwhy are you\b", r"\bin that moment\b", r"\bat that time\b", r"\bhow long have you\b",
        r"\bfeel uncertain\b", r"\bregarding\b", r"\bwhen that happened\b", r"\bwhat expectation\b",
    ]
]
# Output guard only (never used to choose a move): feeling words the reply may not introduce.
AFFECT_GUARD = set(
    """worried anxious scared afraid sad angry upset overwhelmed hurt guilty ashamed lonely hopeless
    nervous frustrated disappointed burned burnt depressed miserable devastated heartbroken terrified
    panicked helpless resentful jealous envious embarrassed insecure unworthy defeated hopeful relieved
    grateful proud excited happy""".split()
)
MAX_WORDS = {"ask": 32, "clarify": 32, "acknowledge": 25, "hold": 10, "repair": 40}
QUESTION_MOVES = ("ask", "clarify", "repair")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", (s or "").lower()).strip()


def _has_run(a: Sequence[str], b: Sequence[str], n: int) -> bool:
    grams = {tuple(b[i : i + n]) for i in range(len(b) - n + 1)}
    return any(tuple(a[i : i + n]) in grams for i in range(len(a) - n + 1))


def check_reply(
    reply: str,
    move: str,
    user_text: str,
    all_user_text: str,
    closed: Sequence[str] = (),
    recent_replies: Sequence[str] = (),
) -> List[str]:
    v: List[str] = []
    r = (reply or "").strip()
    if not r:
        return ["empty reply"]
    q = r.count("?")
    if move in QUESTION_MOVES:
        if q != 1 or not r.endswith("?"):
            v.append("must contain exactly one question, as the last sentence")
    elif q:
        v.append("must not contain a question")
    wc = len(r.split())
    if wc > MAX_WORDS.get(move, 30):
        v.append(f"too long ({wc} words)")
    if any(p.search(r) for p in CANNED):
        v.append("uses a canned empathy phrase")
    for p in PRESUP:
        m = p.search(r)
        if m:
            v.append(f"presupposes something the user did not say ('{m.group(0)}')")
            break
    rt, ut = _tokens(r), _tokens(user_text)
    rc = _content(rt)
    if move != "hold" and len(rc) >= 4:
        ucs = set(_content(ut))
        ratio = sum(t in ucs for t in rc) / len(rc)
        if ratio > 0.6:
            v.append(f"restates the user ({ratio:.0%} of its content words are theirs)")
    if _has_run(rt, ut, 7):
        v.append("copies a long run of the user's words")
    seen = set(_tokens(all_user_text))
    for t in rt:
        if t in AFFECT_GUARD and t not in seen:
            v.append(f"introduces a feeling the user did not name ('{t}')")
            break
    low = r.lower()
    for c in closed:
        if c and c.lower() in low:
            v.append("mentions something the user retracted")
            break
    recent = list(recent_replies)[-5:]
    if any(_norm(p) == _norm(r) for p in recent):
        v.append("identical to a recent reply")
    opener = " ".join(rt[:3])
    if opener and any(" ".join(_tokens(p)[:3]) == opener for p in recent[-2:]):
        v.append("same opener as a recent reply")
    return v


# --------------------------------------------------------------------------- #
# 4. Prompts, exemplars (generic domains; none taken from any test transcript)
# --------------------------------------------------------------------------- #

_COMMON = (
    "- Do NOT restate or summarize what the user said. Reuse at most a few of their words.\n"
    "- Do not name any feeling, cause or event the user did not state. No advice, reassurance, praise or interpretation.\n"
    "- Never use: I understand, I hear you, that sounds, it sounds like, I'm sorry, take your time.\n"
    "- Plain words. Do not repeat an earlier question.\n"
    "Output only the reply, with no label or quotes."
)
SYSTEM = {
    "ask": "You are a quiet, curious listener in a reflective conversation. You write ONE short reply.\n"
    "- Ask exactly ONE open question about the focus phrase, as the last sentence. Under 30 words.\n"
    "- You may add a lead-in of at most 8 words that does not repeat their sentences.\n" + _COMMON,
    "clarify": "You are a quiet listener. You write ONE short reply.\n"
    "- Ask exactly ONE either-or question using the user's own words to resolve what is unclear. Under 30 words.\n" + _COMMON,
    "acknowledge": "You are a quiet listener. You write ONE short reply of one or two sentences, under 22 words, with NO question.\n"
    "- Show you followed by naming what mattered in different words than theirs.\n" + _COMMON,
    "hold": "You are a quiet listener. The user wants space. Write one line of at most 8 words, no question, "
    "that shows you are following.\n" + _COMMON,
    "repair": "The user is frustrated with your earlier replies. Write ONE short reply under 38 words.\n"
    "- First, in one short clause, agree that your earlier replies did not help (no excuses, no apology speech).\n"
    "- Then ask exactly ONE open question about the focus phrase, as the last sentence.\n" + _COMMON,
}
EXAMPLES: Dict[str, List[Dict]] = {
    "ask": [
        {"message": "My flatmate keeps eating my food and when I bring it up he just laughs it off.",
         "focus": "he just laughs it off", "reply": "What happens right after he laughs it off?"},
        {"message": "Our hackathon team has two days left and nobody agrees on what we're even building.",
         "focus": "nobody agrees on what we're even building",
         "reply": "What are the different ideas people have right now?"},
        {"message": "I keep saying I'll start the gym tomorrow and then tomorrow comes and I find another reason.",
         "focus": "I find another reason", "reply": "What's the reason that shows up most often?"},
        {"message": "Dad said I should drop the music course and focus on exams. I said okay but I didn't mean it.",
         "focus": "I said okay but I didn't mean it", "reply": "What would you have said if you'd meant it?"},
    ],
    "clarify": [
        {"message": "My manager and my senior both said I should present, and he thinks I'm not ready.",
         "focus": "he thinks I'm not ready",
         "reply": "When you say he, do you mean your manager or your senior?"},
    ],
    "acknowledge": [
        {"message": "Okay, I finally sent the application. Whatever happens now happens.",
         "focus": "Whatever happens now happens", "reply": "Sent, and the rest is out of your hands."},
        {"message": "Haha my chai spilled on the laptop right before the demo. Typical.",
         "focus": "right before the demo", "reply": "Right before the demo, of all moments."},
    ],
    "hold": [
        {"message": "Honestly I just need to vent for a minute, don't ask me stuff.",
         "focus": "vent for a minute", "reply": "Go ahead, I'm following."},
    ],
    "repair": [
        {"message": "That was useless, you just repeated what I said.",
         "focus": "I keep failing the same viva question",
         "earlier": ["I keep failing the same viva question and nobody tells me what I'm missing."],
         "reply": "You're right, I only echoed you. What happens when that viva question comes up?"},
    ],
}


def _render(message: str, focus: str, earlier: Sequence[str], asked: Sequence[str], closed: Sequence[str]) -> str:
    parts = []
    if earlier:
        parts.append("Earlier messages from the user (context only, never restate):\n" + "\n".join(f"- {e}" for e in earlier))
    parts.append(f'Latest message: "{message}"')
    parts.append(f'Focus phrase: "{focus}"')
    if asked:
        parts.append("Questions already asked (do not repeat):\n" + "\n".join(f"- {a}" for a in asked))
    if closed:
        parts.append("Do not mention: " + "; ".join(closed))
    return "\n".join(parts)


def build_messages(move, user_text, focus, earlier, asked, closed) -> List[Message]:
    msgs: List[Message] = [{"role": "system", "content": SYSTEM[move]}]
    for ex in EXAMPLES.get(move, []):
        msgs.append({"role": "user", "content": _render(ex["message"], ex["focus"], ex.get("earlier", []), [], [])})
        msgs.append({"role": "assistant", "content": ex["reply"]})
    msgs.append({"role": "user", "content": _render(user_text, focus, earlier, asked, closed)})
    return msgs


def clean_output(raw: str) -> str:
    t = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.S | re.I).strip()
    t = re.sub(r"^(reply|response|assistant)\s*:\s*", "", t, flags=re.I).strip()
    if len(t) > 1 and t[0] in "\"\u201c" and t[-1] in "\"\u201d":
        t = t[1:-1].strip()
    return re.sub(r"\s+", " ", t)


# --------------------------------------------------------------------------- #
# 5. Fallback: never a restatement, never one fixed sentence
# --------------------------------------------------------------------------- #

def _short(q: str, n: int = 8) -> str:
    w = q.split()
    return " ".join(w[:n]) + ("..." if len(w) > n else "")


ASK_TEMPLATES = {
    "counterfactual": ["What would that have looked like?", "What is it about that time you would want back?"],
    "universal": ["Is that true every time, or does it feel that way right now?",
                  "Has there been a time it went differently, even a little?"],
    "uncertain": ["What part of it is hardest to pin down?", "What do you know for sure about it so far?"],
    "volition": ["What would that look like for you?", "Which part of that matters most to you?"],
    "plain": ['What stands out to you about "{q}"?', 'Can you say more about "{q}"?'],
}
HOLD_LINES = ["Go ahead.", "Keep going.", "Still following you.", "Go on, I'm following."]


def fallback_reply(move: str, nucleus: str, ntype: str, turn_index: int, recent: Sequence[str]) -> str:
    if move == "hold":
        options = HOLD_LINES
    elif move == "acknowledge":
        options = [f'Got it: "{_short(nucleus, 7)}".', f'Noted, "{_short(nucleus, 7)}".']
    elif move == "repair":
        options = ["You're right, that did not help. " + t for t in ASK_TEMPLATES.get(ntype, ASK_TEMPLATES["plain"])]
    elif move == "clarify":
        options = [f'When you say "{_short(nucleus, 6)}", what exactly do you mean?']
    else:
        options = ASK_TEMPLATES.get(ntype, ASK_TEMPLATES["plain"])
    options = [o.format(q=_short(nucleus, 8)) if "{q}" in o else o for o in options]
    recent_norm = {_norm(r) for r in list(recent)[-5:]}
    ordered = options[turn_index % len(options):] + options[: turn_index % len(options)]
    for o in ordered:
        if _norm(o) not in recent_norm:
            return o
    return ordered[0]


# --------------------------------------------------------------------------- #
# 6. Main entry point
# --------------------------------------------------------------------------- #

def generate_reply(
    user_text: str,
    *,
    move: str,
    llm_call: LLMCall,
    earlier_user_turns: Sequence[str] = (),
    closed: Sequence[str] = (),
    asked_before: Sequence[str] = (),
    recent_replies: Sequence[str] = (),
    turn_index: int = 0,
    max_attempts: int = 3,
) -> Dict:
    """user_text must already be the redacted canonical text. Re-hydrate names after this returns."""
    earlier = list(earlier_user_turns)[-2:]
    if move == "repair" and earlier:
        focus_src = max(earlier, key=lambda s: len(s.split()))
    else:
        focus_src = user_text
    nucleus, ntype = nucleus_info(focus_src)
    all_user_text = " ".join(list(earlier_user_turns) + [user_text])
    result = {"move": move, "nucleus": nucleus, "nucleus_type": ntype, "attempts": 0,
              "violations": [], "source": "fallback", "reply": ""}

    if move == "safety_interrupt":
        raise ValueError("safety_interrupt must be handled by the emergency-resources path, not this engine")

    msgs = build_messages(move, user_text, nucleus, earlier, list(asked_before)[-4:], closed)
    for attempt in range(max_attempts):
        result["attempts"] = attempt + 1
        try:
            raw = llm_call(msgs)
        except Exception as exc:  # network, quota, timeout
            result["violations"].append([f"llm error: {exc}"])
            break
        reply = clean_output(raw)
        v = check_reply(reply, move, user_text, all_user_text, closed, recent_replies)
        if not v:
            result.update(reply=reply, source="llm")
            return result
        result["violations"].append(v)
        msgs = msgs + [
            {"role": "assistant", "content": raw or ""},
            {"role": "user", "content": "Rejected: " + "; ".join(v) + ". Write a new reply that fixes this. Output only the reply."},
        ]
    result["reply"] = fallback_reply(move, nucleus, ntype, turn_index, recent_replies)
    return result


# --------------------------------------------------------------------------- #
# Offline self-test
# --------------------------------------------------------------------------- #

def _selftest() -> None:
    t1 = ("I have been extremely tired because of the college and placement process that is taking place at the "
          "college and it's getting genuinely very draining and tiring. I just feel like going to some place where "
          "I can be unbothered by all these noise.")
    t2 = ("I can't describe the place but something like going on a trek would be extremely relaxing but the "
          "companies are coming for placements and internships I don't want to miss out on it.")
    t3 = ("It is still very uncertain that I will land an internship or get a placement opportunity this week. I have "
          "appeared for 2-3 such opportunities and the preparation behind all of this is very draining and it takes a "
          "lot of peace of mind to be sacrificed and eventually nothing fruitfull comes out of this then, even if you "
          "put in all your efforts nothing fruitful as a result comes out.")
    t5 = ("I am not sure about how all this placement process proceeds and I am really stressed about it. I just want "
          "to go back when I had nothing much to worry about in life. I wished I could go back in time.")
    old = {
        t1: "The college and placement process is draining you, and you want a place where you can be unbothered by the noise.",
        t2: "You want the relaxation of a trek, but you don\u2019t want to miss the companies coming for placements and internships.",
        t3: "You\u2019ve appeared for a few opportunities, but the preparation is draining your peace of mind, and you\u2019re worried nothing fruitful will come out of it.",
    }

    # nucleus picks the weighty clause
    assert "unbothered" in pick_nucleus(t1), pick_nucleus(t1)
    assert "miss out" in pick_nucleus(t2), pick_nucleus(t2)
    assert "even if" in pick_nucleus(t3), pick_nucleus(t3)
    assert "go back" in pick_nucleus(t5), pick_nucleus(t5)

    # the old restating replies are rejected, as ask and as acknowledge
    for text, rep in old.items():
        assert check_reply(rep, "ask", text, text), "old reply should fail as ask"
        assert any("restates" in x or "copies" in x or "introduces" in x
                   for x in check_reply(rep, "acknowledge", text, text)), "old reply should fail as acknowledge"
    # invented feeling is caught even when the rest is fine
    assert any("worried" in x for x in check_reply("What is behind feeling worried about the outcome?", "ask", t3, t3))
    # presupposition guard and canned guard
    assert check_reply("What was occurring around you when you began to worry?", "ask", t5, t5)
    assert check_reply("I understand.", "acknowledge", t5, t5)
    # a good question passes
    assert not check_reply("What was different about that time?", "ask", t5, t5), \
        check_reply("What was different about that time?", "ask", t5, t5)
    # duplicates are caught
    assert check_reply("What was different about that time?", "ask", t5, t5, recent_replies=["What was different about that time?"])

    # move policy
    assert choose_move("ok", [])[0] == "hold"
    assert choose_move("just let me talk for a bit please", [])[0] == "hold"
    assert choose_move("If I had to describe the whole thing now, I am proud and tired", [])[0] == "acknowledge"
    assert choose_move(t3, [])[0] == "ask"
    asks = [{"move": "ask"}] * 3
    assert choose_move(t3, asks)[0] == "acknowledge"
    assert choose_move(t3, [{"move": "ask", "uptake": "deflected"}])[0] == "acknowledge"
    assert choose_move("What do you even understand", [], pipeline_move="repair")[0] == "repair"
    assert choose_move("stop asking me things", [], pipeline_move="repair")[0] == "hold"

    # retry path: bad first reply, good second
    calls = {"n": 0}

    def mock(msgs):
        calls["n"] += 1
        return old[t1] if calls["n"] == 1 else "<think>x</think>Reply: What would that place be like for you?"

    res = generate_reply(t1, move="ask", llm_call=mock)
    assert res["source"] == "llm" and res["attempts"] == 2 and res["reply"].endswith("?"), res

    # fallback path: LLM always bad, or raises
    res = generate_reply(t5, move="ask", llm_call=lambda m: old[t1])
    assert res["source"] == "fallback" and not check_reply(res["reply"], "ask", t5, t5), res

    def boom(m):
        raise TimeoutError("api down")

    res = generate_reply(t3, move="ask", llm_call=boom)
    assert res["source"] == "fallback" and res["reply"].count("?") == 1, res
    for mv in ("acknowledge", "hold", "repair", "clarify"):
        r = generate_reply(t3, move=mv, llm_call=boom, earlier_user_turns=[t1])
        assert not check_reply(r["reply"], mv, t3, t3 + t1) or mv == "acknowledge", (mv, r)

    # payload contains the plan and recent user turns only, never assistant history
    msgs = build_messages("ask", t5, pick_nucleus(t5), [t3], [], [])
    assert msgs[-1]["role"] == "user" and "Earlier messages" in msgs[-1]["content"]
    assert all(old[t1] not in m["content"] for m in msgs)
    print("reply_engine self-test: all checks passed")


if __name__ == "__main__":
    _selftest()
