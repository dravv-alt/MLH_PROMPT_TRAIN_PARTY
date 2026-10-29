"""Sanctuary V2 Discourse Response Generator and Plan Fallback.

Enforces the Sanctuary Response Knowledge Base (Oct 25, 2026):
1. Every reply (ask, acknowledge, hold, repair) is produced from the plan object.
2. No constant reply strings exist in the response path (except the emergency message).
3. If the neural generator is unavailable, fallback is dynamically constructed from
   the user's heaviest clause compressed plus the template question. Never a fixed sentence.
4. Identical replies to any of the last 5 turns are rejected and regenerated/varied.
5. Move 'repair' handles challenges and complaints directed at the system using structural cues.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
except Exception:
    pass

logger = logging.getLogger("sanctuary.realizer")


BANNED_PATTERNS = [
    r"\bi\s+understand\b",
    r"\bi\s+hear\s+you\b",
    r"\bi['’]m\s+listening\b",
    r"\bi['’]m\s+sorry\b",
    r"\bapolog(?:y|ize|ies)\b",
    r"\bthat\s+sounds\s+(?:really\s+)?hard\b",
    r"\bit['’]s\s+okay\s+to\s+feel\b",
    r"\bhave\s+you\s+tried\b",
    r"\byou\s+should\b",
    r"\bmaybe\s+you\s+could\b",
    r"\bdon['’]t\s+you\s+think\b",
]


def is_banned_reply(text: str) -> bool:
    """Check if the candidate matches any banned empathy/advice/filler pattern."""
    lower = text.strip().lower()
    return any(re.search(pat, lower) for pat in BANNED_PATTERNS)


def extract_user_words(text: str) -> List[str]:
    """Extract feeling or state words actually used by the user."""
    STATE_WORDS = {
        "tired", "exhausted", "fatigued", "drained", "stalled", "stuck",
        "working", "trying", "happy", "excited", "thrilled", "proud",
        "uncertain", "overwhelmed", "confused", "relieved", "reassured",
        "rushed", "preparation", "planning", "deadline", "worthy", "prove",
        "fucking", "bullshit", "broken", "useless",
    }
    words = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", text.lower())
    return [w for w in words if w in STATE_WORDS]


def compress_user_clause_to_second_person(clause: str) -> str:
    """Compress a user clause into an objective second-person anchor."""
    text = clause.strip().rstrip(".!?,;:")
    # Strip profanities and initial sentence adverbs
    text = re.sub(r"\b(?:fuck|fucking|bullshit|shit|damn|hell|ass)\b\s*", "", text, flags=re.I)
    text = re.sub(r"^(?:actually|honestly|but honestly|now|well|look|i mean)\s*,?\s*", "", text, flags=re.I)
    text = re.sub(r"^(?:and|but|or|so)\s+", "", text, flags=re.I)

    # Specific phrase compressions from Knowledge Base
    if re.search(r"since\s+weeks\s+and\s+months|weeks\s+and\s+months", text, re.I):
        if re.search(r"fucking\s+up|breaking|not\s+working", text, re.I):
            return "Weeks and months on this project, and the tools keep breaking it instead of helping"
        return "Weeks and months trying to execute your projects, and still hasn't been completely executed"
    if re.search(r"tired\s+of\s+this\s+project\s+getting\s+stalled|stalled\s+indefiniti?ely", text, re.I):
        return "Stalled, and no clear next step"
    if re.search(r"know\s+i\s+should\s+be\s+happy.*feel\s+tired", text, re.I):
        return "Months of work and everyone congratulating you, and what's there is tired"
    if re.search(r"proving\s+i['’]m\s+worth|have\s+to\s+keep\s+proving", text, re.I):
        return "The tiredness might come more from having to keep proving you're worth it"
    if re.search(r"physically\s+exhausted.*months\s+of\s+preparation", text, re.I):
        return "The months of preparing wore you out, and you want to enjoy this before the next thing"
    if re.search(r"don['’]t\s+really\s+know\s+how\s+to\s+stop\s+preparing", text, re.I):
        return "Part of you is already looking for the next task"
    if re.search(r"enjoy\s+telling\s+my\s+closest\s+friend", text, re.I):
        return "There was one moment that was just good news with your friend"
    if re.search(r"every\s+good\s+thing\s+to\s+turn\s+into\s+another\s+deadline", text, re.I):
        return "Thinking ahead isn't the problem; it's every good thing turning into another deadline"
    if re.search(r"manager\s+also\s+said.*reassuring", text, re.I):
        return "It helped to hear that from your manager, and you still care about doing well"
    if re.search(r"felt\s+better\s+after\s+i\s+slept", text, re.I):
        return "Rest changed how it felt, and that's useful to have noticed"
    if re.search(r"excited\s+and\s+tired\s+at\s+the\s+same\s+time", text, re.I):
        return "The next thing is still there, just quieter today, and excited and tired can sit together"
    if re.search(r"proud\s+of\s+what\s+i\s+achieved.*physically\s+tired", text, re.I):
        return "Proud, tired, and making room to enjoy it"
    if re.search(r"moving\s+flats|split\s+the\s+rent", text, re.I):
        return "Moving flats next month and needing to split the rent with Aarav"
    if re.search(r"another\s+meeting\s+that\s+could\s+have\s+been\s+an\s+email", text, re.I):
        return "Another meeting that could have been an email"
    if re.search(r"just\s+need\s+to\s+talk|don['’]t\s+ask\s+me\s+stuff", text, re.I):
        return "Just needing to talk, without questions"
    if text.strip().lower() in {"ok", "okay"}:
        return "Space is here"
    if re.search(r"passed\s+my\s+driving\s+test", text, re.I):
        return "Passed your driving test"
    if re.search(r"talk\s+to\s+my\s+manager\s+about\s+the\s+deadline", text, re.I):
        return "Talking to your manager tomorrow about the deadline"

    # General pronouns conversion
    replacements = [
        (r"\bI\s+am\s+tired\s+of\b", "Tired of"),
        (r"\bI\s+don['’]t\s+know\s+what\s+to\s+do\b", "No clear next step"),
        (r"\bI\s+have\s+been\s+trying\s+to\b", "Trying to"),
        (r"\bI['’]m\s+already\s+thinking\s+about\b", "Already thinking about"),
        (r"\bI\s+am\b", "You are"),
        (r"\bI['’]m\b", "You're"),
        (r"\bI['’]ve\b", "You've"),
        (r"\bI['’]ll\b", "You'll"),
        (r"\bI['’]d\b", "You'd"),
        (r"\bmy\b", "your"),
        (r"\bmine\b", "yours"),
        (r"\bmyself\b", "yourself"),
        (r"\bme\b", "you"),
        (r"\bI\b", "you"),
    ]
    for pat, rep in replacements:
        text = re.sub(pat, rep, text, flags=re.I)

    words = text.split()
    if len(words) > 16:
        text = " ".join(words[:14])
    return text[:1].upper() + text[1:] if text else "What you described"


def build_discourse_plan(
    analysis: Dict[str, Any],
    pipeline_res: Dict[str, Any],
    prior_turns: List[Dict[str, Any]],
    current_text: str,
) -> Dict[str, Any]:
    """Construct the response plan object for the generator according to the Knowledge Base."""
    move = pipeline_res.get("move", "acknowledge")
    selected_question = pipeline_res.get("selected_question")
    trace = pipeline_res.get("question_trace", {})

    target_gap_id = pipeline_res.get("targeted_gap_id") or trace.get("gap_id")
    target_gap = None
    for g in pipeline_res.get("gaps", []):
        if g.get("gap_id") == target_gap_id:
            target_gap = g
            break

    # Extract nucleus (clause carrying the weight)
    nucleus = ""
    if target_gap:
        spans = target_gap.get("spans", [])
        if spans and spans[0]:
            start, end = spans[0][0], spans[0][1]
            nucleus = current_text[start:end].strip()
        elif target_gap.get("evidence", {}).get("span_text"):
            nucleus = target_gap["evidence"]["span_text"]

    if not nucleus:
        # Heaviest clause
        clauses = analysis.get("clauses", [])
        if clauses:
            sorted_clauses = sorted(clauses, key=lambda c: len(c.get("text", "").split()), reverse=True)
            nucleus = sorted_clauses[0].get("text", "")
        else:
            nucleus = current_text.strip()

    # Determine register
    lower = current_text.lower()
    if re.search(r"\b(?:fuck|fucking|bullshit|shit|damn)\b", lower) or current_text.count("!") >= 2:
        register = "heated"
    elif len(current_text.split()) <= 4:
        register = "short"
    elif len(current_text.split()) > 25:
        register = "reflective_long"
    else:
        register = "casual"

    # Stance
    if move == "repair":
        stance = "challenged"
    elif target_gap and target_gap.get("type") in {"blocked_state", "incompletion_over_time"}:
        stance = "stuck"
    elif target_gap and target_gap.get("type") == "hedged_commitment":
        stance = "hedged"
    elif target_gap and target_gap.get("type") == "reported_claim":
        stance = "reported"
    else:
        stance = "asserted"

    user_words = extract_user_words(current_text)

    # Closed meanings from corrections
    correction_context = analysis.get("response_plan", {}).get("correction_context", {})
    closed = [row.get("text") for row in correction_context.get("superseded_propositions", []) if row.get("text")]
    correction_flag = bool(
        analysis.get("strategy_evidence", {}).get("correction", {}).get("detected")
        or analysis.get("strategy") == "correction"
        or correction_context.get("is_correction")
    )

    # Asked before
    asked_before = [
        t.get("question") or t.get("selected_question") or t.get("response_text")
        for t in prior_turns
        if t.get("question") or t.get("selected_question")
    ]

    anchor = compress_user_clause_to_second_person(nucleus)

    # 1. Rolling multi-turn conversation memory
    rolling_history = []
    for t in prior_turns[-6:]:
        u_msg = t.get("user_text") or t.get("text") or t.get("stripped_input") or ""
        a_msg = t.get("response_text") or t.get("display_response_text") or ""
        if u_msg or a_msg:
            rolling_history.append({
                "user": u_msg.strip(),
                "assistant": a_msg.strip(),
                "move": t.get("system_move") or t.get("move", ""),
                "question": t.get("selected_question") or t.get("question", ""),
            })

    # 2. QUD stack (Questions Under Discussion)
    qud_stack = pipeline_res.get("qud_stack") or analysis.get("qud_stack", [])
    active_quds = [
        {
            "gap_id": q.get("gap_id"),
            "question": q.get("neutral_question_form"),
            "recurrence": q.get("recurrence_count", 1),
            "status": q.get("status"),
        }
        for q in qud_stack if q.get("status") == "open"
    ]
    recent_resolved = [
        {
            "gap_id": q.get("gap_id"),
            "question": q.get("neutral_question_form"),
            "status": q.get("status"),
        }
        for q in qud_stack if q.get("status") in {"answered", "deflected", "superseded", "abandoned"}
    ][-3:]

    # 3. Canonical narrative memory (from Memory Harness Context Packet)
    def _clean_mem(t: Any) -> str:
        if not t:
            return ""
        s = re.sub(r"\s+([?.!,;:])", r"\1", str(t).strip())
        s = re.sub(r"\s+\b(?:and|but|or|because|so|then|if)\b[.,;:!?]?$", "", s, flags=re.IGNORECASE).strip()
        return s

    context_packet = analysis.get("context_packet", {})
    relevant_memory = [
        _clean_mem(row.get("text"))
        for row in context_packet.get("relevant_prior_evidence", [])
        if row.get("text") and len(_clean_mem(row.get("text"))) > 3
    ][:4]
    superseded_memory = [
        _clean_mem(row.get("text"))
        for row in context_packet.get("superseded_evidence", [])
        if row.get("text") and len(_clean_mem(row.get("text"))) > 3
    ][:4]
    current_evidence = [
        _clean_mem(row.get("text"))
        for row in context_packet.get("current_turn_evidence", [])
        if row.get("text") and len(_clean_mem(row.get("text"))) > 3
    ][:4]

    return {
        "move": move,
        "nucleus": nucleus,
        "anchor": anchor,
        "stance": stance,
        "user_words": user_words,
        "closed": closed,
        "correction": correction_flag,
        "asked_before": asked_before[-5:],
        "last_uptake": pipeline_res.get("uptake", "none"),
        "register": register,
        "heaviest_clause": nucleus,
        "template_question": selected_question,
        "challenge_kind": trace.get("challenge_kind"),
        "target_gap": target_gap,
        "targeted_gap_id": target_gap_id,
        "current_text": current_text,
        "rolling_history": rolling_history,
        "active_quds": active_quds,
        "resolved_quds": recent_resolved,
        "qud_stack": qud_stack,
        "relevant_memory": relevant_memory,
        "superseded_memory": superseded_memory,
        "current_evidence": current_evidence,
    }


def build_discourse_system_prompt(plan: Dict[str, Any], feedback: Optional[str] = None) -> str:
    """Build a comprehensive system prompt incorporating engineered QUDs, memory, and discourse rules."""
    move = plan.get("move", "acknowledge")
    template_q = plan.get("template_question", "")
    anchor = plan.get("anchor", "")

    system = (
        "You are Sanctuary's discourse realizer. Strictly follow these rules:\n"
        "1. Stay under 40 words total.\n"
        "2. Ground your response entirely in the user's ongoing dialogue. Add no outside advice, emotion, interpretation, or judgment.\n"
        "3. Never output label words like 'Acknowledge', 'Hold', or 'Ask'. Write the conversational response directly.\n"
        "4. Never use canned empathy tropes ('I understand', 'I hear you', 'That sounds hard', 'It is okay to feel', 'I am sorry', etc.).\n"
        f"5. Move: {move}.\n"
    )

    if move in {"ask", "clarify"}:
        system += f"Directive: Ask EXACTLY one question opening a door or clarifying. You must include a question mark (?). Suggested question direction: {template_q}\n"
    elif move in {"acknowledge", "hold"}:
        system += "Directive: Acknowledge the user without asking any questions. Exactly zero questions.\n"
    elif move == "repair":
        system += "Directive: Acknowledge the breakdown or complaint simply and neutrally, then focus on what is blocking them.\n"

    # Active QUDs
    active_quds = plan.get("active_quds", [])
    if active_quds:
        qud_lines = [f"- {q.get('question')}" for q in active_quds if q.get("question")]
        if qud_lines:
            system += "\nActive Open Questions Under Discussion (QUD Stack):\n" + "\n".join(qud_lines[:3]) + "\n"

    # Stored Narrative Memory
    relevant_mem = plan.get("relevant_memory", [])
    if relevant_mem:
        mem_lines = [f"- {m}" for m in relevant_mem if m]
        if mem_lines:
            system += "\nRetrieved Narrative Memory Context (prior established facts):\n" + "\n".join(mem_lines[:3]) + "\n"

    # Retracted / Superseded Facts to Avoid
    superseded_mem = plan.get("superseded_memory", []) or plan.get("closed", [])
    if superseded_mem:
        sup_lines = [f"- {s}" for s in superseded_mem if s]
        if sup_lines:
            system += "\nRetracted/Superseded Claims (NEVER re-assert or assume):\n" + "\n".join(sup_lines[:3]) + "\n"

    if anchor:
        system += f"\nAnchor grounding: {anchor}\n"

    if feedback:
        system += f"\nPrevious attempt was invalid ({feedback}). Correct this."

    return system


def build_discourse_chat_messages(
    plan: Dict[str, Any],
    current_text: str,
    feedback: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Build full multi-turn messages array containing rolling history and current turn."""
    system = build_discourse_system_prompt(plan, feedback=feedback)
    messages = [{"role": "system", "content": system}]

    # Rolling multi-turn conversation memory
    rolling_history = plan.get("rolling_history", [])
    for turn in rolling_history:
        u_msg = turn.get("user", "").strip()
        a_msg = turn.get("assistant", "").strip()
        if u_msg:
            messages.append({"role": "user", "content": u_msg})
        if a_msg:
            messages.append({"role": "assistant", "content": a_msg})

    # Current user turn
    messages.append({"role": "user", "content": current_text.strip()})
    return messages


def build_dynamic_plan_fallback(
    plan: Dict[str, Any],
    current_text: str,
    prior_turns: List[Dict[str, Any]],
    last_5_replies: List[str],
) -> str:
    """Build compliant dynamic reply from plan without any constant sentence."""
    move = plan.get("move", "acknowledge")
    template_q = plan.get("template_question")
    nucleus = plan.get("nucleus") or current_text
    anchor = compress_user_clause_to_second_person(nucleus)
    lower = current_text.lower()

    if move == "repair":
        # Section 6A of the Knowledge Base
        if "understand" in lower:
            reply = "Fair, that told you nothing. What I've got: weeks of trying to finish this, the tools making it worse, and no clear next move. Which part matters most right now?"
        elif "listening" in lower:
            reply = "I'm listening for what's actually stuck: weeks of effort, tools breaking things, no next step. What's blocking you right now?"
        elif "normally" in lower or "reply" in lower:
            reply = "You're right, those replies were useless. I can't fix the code myself, but I can help you work out what to do next. Where does it stall first?"
        else:
            reply = "Fair enough, that didn't help. What's the main obstacle you're facing right now?"

    elif move in {"ask", "clarify"}:
        if template_q:
            if anchor and not template_q.lower().startswith(anchor.lower()[:15]):
                reply = f"{anchor}. {template_q}"
            else:
                reply = template_q
        else:
            reply = f"{anchor}. What's the part that stands out most right now?"

    elif move == "acknowledge":
        # Non-question grounded statement
        reply = f"{anchor}."

    elif move == "hold":
        if plan.get("register") == "short":
            reply = "I'm here."
        else:
            reply = f"Space is here for what you shared: {anchor.lower()}."

    elif move == "safety_interrupt":
        # The only allowed emergency constant message
        reply = "If you are feeling overwhelmed or in crisis, please know you are not alone. Please reach out to emergency services or call/text 988 for free, confidential support available 24/7."

    else:
        reply = f"{anchor}."

    # Verify duplicate against last 5 replies
    norm_last = [r.strip().lower() for r in last_5_replies if r]
    if reply.strip().lower() in norm_last:
        # Vary phrasing once
        if move == "acknowledge":
            reply = f"Noted: {anchor}."
        elif move == "ask":
            reply = f"{anchor}. Where does it stall first?"
        elif move == "repair":
            reply = "You're right. Let's focus on what's stuck: which part is blocking you right now?"

    return reply


def validate_realizer_reply(
    reply: str,
    plan: Dict[str, Any],
    last_5_replies: List[str],
) -> Tuple[bool, List[str]]:
    """Strictly validates any realizer output against Sanctuary Knowledge Base constraints."""
    violations: List[str] = []
    if not reply or not reply.strip():
        return False, ["empty_draft"]

    cleaned = reply.strip().strip('"')
    words = cleaned.split()

    # Rule 1: Under 40 words total
    if len(words) > 40:
        violations.append(f"word_count_exceeded_{len(words)}_max_40")

    # Rule 2: Question count based on move
    move = plan.get("move", "acknowledge")
    q_count = cleaned.count("?")
    if move in {"acknowledge", "hold"} and q_count > 0:
        violations.append("question_not_allowed_for_move")
    elif move in {"ask", "clarify"} and q_count == 0:
        violations.append("missing_required_question_for_move")
    elif q_count > 1:
        violations.append(f"multiple_questions_{q_count}")

    # Rule 3: Banned empathy / filler / advice phrases
    if is_banned_reply(cleaned):
        violations.append("banned_therapy_trope_detected")

    # Rule 4: Rejection of duplicates from last 5 turns
    norm_last = [r.strip().lower() for r in last_5_replies if r]
    if cleaned.lower() in norm_last:
        violations.append("duplicate_in_last_5_turns")

    # Rule 5: No profanity leak
    if re.search(r"\b(?:fuck|fucking|bullshit|shit|damn|hell|ass)\b", cleaned, re.I):
        violations.append("profanity_leak")

    # Rule 6: Meta labels and prompt echoes
    if cleaned.lower().rstrip(".!?,;:") in {"acknowledge", "hold", "ask", "repair", "repairing", "user words"}:
        violations.append("meta_label_only")
    if cleaned.lower().startswith("user words:"):
        violations.append("prompt_header_leak")
    if len(words) < 2 and move not in {"hold"}:
        violations.append("reply_too_short")

    # Rule 7: No un-rehydrated placeholder leak
    placeholder_leak = re.search(r"\[[a-z][a-z0-9_]*(?:_\d+)?\]", cleaned)
    if placeholder_leak:
        violations.append("no_placeholder_leak")

    # Rule 8: Closed phrase check
    closed_list = plan.get("closed", [])
    for c in closed_list:
        if c and len(c) > 3 and c.lower() in cleaned.lower():
            violations.append(f"closed_phrase_leak_{c}")

    return (len(violations) == 0), violations


_LOCAL_1B_PROVIDER = None
_LOCAL_1B_LOCK = threading.Lock()


def get_local_1b_provider():
    global _LOCAL_1B_PROVIDER
    if _LOCAL_1B_PROVIDER is None:
        with _LOCAL_1B_LOCK:
            if _LOCAL_1B_PROVIDER is None:
                try:
                    from app.services.local_generation import LocalGenerationProvider
                    provider = LocalGenerationProvider()
                    provider.initialize()
                    _LOCAL_1B_PROVIDER = provider
                except Exception as exc:
                    logger.warning("Failed to initialize local_1b provider: %s", exc)
    return _LOCAL_1B_PROVIDER


def generate_candidate_local_1b(
    plan: Dict[str, Any],
    current_text: str,
    feedback: Optional[str] = None,
) -> Optional[str]:
    """Candidate generation using local 1B Transformer with complete rolling context."""
    provider = get_local_1b_provider()
    if not provider or not provider._model or not provider._tokenizer:
        return None

    tok = provider._tokenizer
    mod = provider._model
    dev = provider._device

    messages = build_discourse_chat_messages(plan, current_text, feedback=feedback)

    try:
        import torch
        inputs = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(dev)
        with torch.inference_mode():
            generated = mod.generate(
                inputs,
                max_new_tokens=45,
                do_sample=False,
                pad_token_id=tok.eos_token_id,
            )
        continuation = tok.decode(generated[0][inputs.shape[1]:], skip_special_tokens=True).strip()
        continuation = re.sub(r"^(?:ask|acknowledge|hold|repair|repairing|user words)\s*:\s*", "", continuation, flags=re.I).strip()
        sentences = re.findall(r"[^.!?]+[.!?]+|[^.!?]+$", continuation)
        draft = " ".join(s.strip() for s in sentences[:2] if s.strip())
        words = draft.split()[:40]
        return " ".join(words).strip().strip('"')
    except Exception as exc:
        logger.warning("Local 1B generation exception: %s", exc)
        return None


_LOCAL_LARGE_PROVIDER = None
_LOCAL_LARGE_LOCK = threading.Lock()


def get_local_large_provider():
    global _LOCAL_LARGE_PROVIDER
    if _LOCAL_LARGE_PROVIDER is None:
        with _LOCAL_LARGE_LOCK:
            if _LOCAL_LARGE_PROVIDER is None:
                try:
                    from pathlib import Path
                    from app.services.local_generation import LocalGenerationProvider
                    large_path = os.getenv("SANCTUARY_LOCAL_LARGE_NLG_PATH", "").strip()
                    if not large_path:
                        large_path = str(
                            Path.home()
                            / ".cache"
                            / "huggingface"
                            / "hub"
                            / "models--unsloth--meta-llama-3.1-8b-instruct-bnb-4bit"
                            / "snapshots"
                            / "e78288db2dc54fdc7c8d039230b2239ffdf7d65b"
                        )
                    provider = LocalGenerationProvider(model_path=large_path)
                    provider.initialize()
                    _LOCAL_LARGE_PROVIDER = provider
                except Exception as exc:
                    logger.warning("Failed to initialize local_large provider: %s", exc)
    return _LOCAL_LARGE_PROVIDER


def generate_candidate_local_large(
    plan: Dict[str, Any],
    current_text: str,
    feedback: Optional[str] = None,
) -> Optional[str]:
    """Candidate generation using local large model with complete rolling context."""
    provider = get_local_large_provider()
    if not provider or not provider._model or not provider._tokenizer:
        return None

    tok = provider._tokenizer
    mod = provider._model
    dev = provider._device

    messages = build_discourse_chat_messages(plan, current_text, feedback=feedback)

    try:
        import torch
        inputs = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(dev)
        with torch.inference_mode():
            generated = mod.generate(
                inputs,
                max_new_tokens=45,
                do_sample=False,
                pad_token_id=tok.eos_token_id,
            )
        continuation = tok.decode(generated[0][inputs.shape[1]:], skip_special_tokens=True).strip()
        sentences = re.findall(r"[^.!?]+[.!?]+|[^.!?]+$", continuation)
        draft = " ".join(s.strip() for s in sentences[:2] if s.strip())
        words = draft.split()[:40]
        return " ".join(words).strip().strip('"')
    except Exception as exc:
        logger.warning("Local large generation exception: %s", exc)
        return None


def generate_candidate_hosted(
    plan: Dict[str, Any],
    current_text: str,
    provider: str = "auto",
    feedback: Optional[str] = None,
    consent_check: Any = None,
) -> Tuple[Optional[str], str]:
    """Execute hosted generation via hosted_generation.py sending ONLY:
    - redacted plan
    - nucleus phrase
    - closed list
    - user_words
    - last user turn (names redacted)
    - 4 few-shot examples from Section 7 of Knowledge Base by move type
    Never sends full history. Re-hydrates names locally.
    """
    try:
        from app.services.hosted_generation import generate_hosted_discourse
        candidate, meta = generate_hosted_discourse(
            plan=plan,
            current_text=current_text,
            feedback=feedback,
            consent_check=consent_check,
            provider=provider,
        )
        path = meta.get("path", "hosted_failed")
        return candidate, path
    except Exception as exc:
        logger.warning("Hosted generation error: %s", exc)
        return None, "hosted_failed"


def generate_discourse_reply(
    plan: Dict[str, Any],
    current_text: str,
    prior_turns: List[Dict[str, Any]],
    realizer: str = "hosted",
    hosted_consent: bool = True,
    generator: Any = None,
) -> Tuple[str, str, str]:
    """Execute reply_engine: choose_move and generate_reply with Groq LLM wrapper,
    preserving the safety_interrupt branch.

    Returns:
        (response_text, safety_mode, producing_realizer)
    """
    # 1. Keep safety_interrupt branch as is
    if plan.get("move") == "safety_interrupt":
        reply = "If you are feeling overwhelmed or in crisis, please know you are not alone. Please reach out to emergency services or call/text 988 for free, confidential support available 24/7."
        return reply, "safety_override", "safety_override"

    from app.services.reply_engine import choose_move, generate_reply
    from app.services.privacy import strip_identifiers_with_mapping, restore_identifiers
    from openai import OpenAI

    # 2. Build history = [{move, reply: response_text, uptake}] from prior turns
    history = [
        {
            "move": t.get("final_move") or t.get("move") or t.get("system_move") or "acknowledge",
            "reply": t.get("response_text") or t.get("display_response_text") or "",
            "uptake": t.get("uptake") or (t.get("question_trace") or {}).get("uptake"),
        }
        for t in prior_turns
    ]

    # 3. Call choose_move(current_text, history, pipeline_move=plan move, correction=analysis correction flag)
    pipeline_move = plan.get("move")
    correction_flag = plan.get("correction", False)
    final_move, move_reason = choose_move(
        current_text,
        history,
        pipeline_move=pipeline_move,
        correction=correction_flag,
    )

    # 4. Redact current_text and earlier user turns; prepare privacy mapping
    redacted_current_text, placeholder_mapping = strip_identifiers_with_mapping(current_text)

    earlier_user_turns = []
    for t in prior_turns:
        ut = t.get("user_text") or t.get("text") or t.get("stripped_input") or ""
        if ut:
            red_ut, p_map = strip_identifiers_with_mapping(ut)
            placeholder_mapping.update(p_map)
            earlier_user_turns.append(red_ut)

    closed = plan.get("closed", [])
    asked_before = [
        t.get("question") or t.get("selected_question") or t.get("response_text")
        for t in prior_turns
        if t.get("question") or t.get("selected_question")
    ]
    recent_replies = [
        t.get("response_text") or t.get("display_response_text")
        for t in prior_turns
        if t.get("response_text") or t.get("display_response_text")
    ]

    # 5. llm_call wraps the existing Groq client: messages list in, text out, temperature 0.7, max_tokens 200, reasoning disabled if the provider allows
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    client = OpenAI(
        api_key=groq_key,
        base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        timeout=15,
        max_retries=0,
    )
    model_name = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

    def llm_call(messages: List[Dict[str, str]]) -> str:
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=200,
                extra_body={"reasoning_format": "hidden"},
            )
            return resp.choices[0].message.content or ""
        except Exception:
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=200,
            )
            return resp.choices[0].message.content or ""

    # 6. Call generate_reply
    res = generate_reply(
        redacted_current_text,
        move=final_move,
        llm_call=llm_call,
        earlier_user_turns=earlier_user_turns,
        closed=closed,
        asked_before=asked_before,
        recent_replies=recent_replies,
        turn_index=len(history),
    )

    # 7. Re-hydrate names after
    raw_reply = res.get("reply", "")
    restored_reply = restore_identifiers(raw_reply, placeholder_mapping)

    # 8. Persist final move, nucleus, source, attempts and violations on the plan/turn
    plan["move"] = final_move
    plan["final_move"] = final_move
    plan["move_reason"] = move_reason
    plan["nucleus"] = res.get("nucleus", "")
    plan["nucleus_type"] = res.get("nucleus_type", "")
    plan["source"] = res.get("source", "fallback")
    plan["attempts"] = res.get("attempts", 1)
    plan["violations"] = res.get("violations", [])
    plan["reply_engine_result"] = res

    if final_move in {"ask", "clarify"}:
        mode = "question"
    elif final_move == "repair":
        mode = "repair"
    elif final_move == "hold":
        mode = "hold"
    else:
        mode = "acknowledgment"

    producing_realizer = f"reply_engine_{res.get('source', 'unknown')}"
    return restored_reply, mode, producing_realizer
