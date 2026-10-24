"""Terminal-only smoke test and ephemeral conversation for Sanctuary's NLP stack.

The command never writes conversation data to the application database. It
uses the cached local Transformer by default and has no hosted fallback.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import sys
import threading
import time
from pathlib import Path
from typing import Any

import numpy as np
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env", override=False)

from app.services import dmrst  # noqa: E402
from app.services.dmrst import parse_dmrst  # noqa: E402
from app.services.neural_runtime import EMBEDDING, NLI, manifest, version  # noqa: E402
from app.services.neural_text import nli_candidates  # noqa: E402
from app.services.nlp_engine import analyze_turn, clause_graph, parse, redact  # noqa: E402
from app.services.deterministic_response import deterministic_response  # noqa: E402
from app.services.nlp_service import NLPService  # noqa: E402
from app.services.memory_harness import apply_memory_harness  # noqa: E402


@contextlib.contextmanager
def processing_animation(label: str, enabled: bool = True):
    """Small dependency-free TUI spinner; never contaminates JSON output."""
    if not enabled:
        yield
        return
    stopped = threading.Event()
    started = time.monotonic()

    def animate() -> None:
        frames = ("|", "/", "-", "\\")
        index = 0
        while not stopped.wait(0.12):
            elapsed = time.monotonic() - started
            print(f"\r{frames[index % len(frames)]} {label}  {elapsed:5.1f}s", end="", flush=True)
            index += 1

    thread = threading.Thread(target=animate, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stopped.set()
        thread.join(timeout=0.5)
        elapsed = time.monotonic() - started
        print(f"\r[done] {label}  {elapsed:5.1f}s".ljust(72), flush=True)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Sanctuary's encoder and output decoders locally, without the API or frontend."
    )
    parser.add_argument("--text", help="Text to inspect. Omit it to enter text without storing it in shell history.")
    parser.add_argument("--compare", help="Optional second text for semantic-similarity testing.")
    parser.add_argument(
        "--mode",
        choices=("embedding", "nli", "dmrst", "math", "all"),
        default="all",
        help="Component to run (default: all).",
    )
    privacy = parser.add_mutually_exclusive_group()
    privacy.add_argument(
        "--raw",
        action="store_true",
        help="Opt in to transient, unredacted local inference. Nothing is persisted by this command.",
    )
    privacy.add_argument("--redacted", action="store_true", help="Use privacy-safe redacted input (default).")
    parser.add_argument(
        "--generator",
        choices=("local", "classical"),
        default="local",
        help="Response realizer: cached local Transformer with validated fallback, or classical only.",
    )
    parser.add_argument("--provider", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--no-reply",
        action="store_true",
        help="Run component diagnostics only, without producing a Sanctuary response.",
    )
    parser.add_argument("--json", action="store_true", help="Emit one machine-readable JSON result.")
    parser.add_argument("--warmup-timeout", type=float, default=90.0, help="Maximum model warm-up seconds.")
    parser.add_argument(
        "--math-profile",
        choices=("low_resource", "balanced", "high_fidelity", "responsive", "stable"),
        default="balanced",
        help="Mathematical-model CPU/memory/noise profile (default: balanced).",
    )
    return parser.parse_args()


def prepare_text(text: str, raw: bool) -> dict[str, Any]:
    if raw:
        model_text, mentions = text, []
    else:
        model_text, _, mentions, _ = redact(text, [], "terminal-local-test-only")
    doc, parser_backend, fallback_reason = parse(model_text)
    clauses, _ = clause_graph(doc, fallback_reason is not None)
    return {
        "text": model_text,
        "mentions": mentions,
        "clauses": clauses,
        "parser_backend": parser_backend,
        "parser_fallback": fallback_reason,
        "redaction_count": len(mentions),
    }


def wait_until_ready(worker: Any, timeout: float) -> dict[str, Any]:
    started = time.monotonic()
    worker.start()
    while time.monotonic() - started < timeout:
        if worker.state == "ready":
            return {
                "status": "ready",
                "warmup_seconds": round(time.monotonic() - started, 3),
                "threads": worker.effective_threads,
                "thread_fallback": worker.thread_fallback,
            }
        if worker.state in {"restart_limit"}:
            break
        time.sleep(0.1)
    return {"status": "unavailable", "reason": worker.state, "warmup_seconds": round(time.monotonic() - started, 3)}


def vector_decode(vector: list[float]) -> dict[str, Any]:
    """Validate the exact persisted <f4 representation; this is not text reconstruction."""
    encoded = np.asarray(vector, dtype="<f4").tobytes(order="C")
    decoded = np.frombuffer(encoded, dtype="<f4")
    original = np.asarray(vector, dtype=np.float64)
    finite = bool(np.isfinite(decoded).all())
    return {
        "status": "ready" if finite and decoded.size == original.size else "unavailable",
        "format": "little-endian float32 (<f4)",
        "byte_length": len(encoded),
        "dimension": int(decoded.size),
        "finite": finite,
        "norm": round(float(np.linalg.norm(decoded)), 8),
        "max_roundtrip_error": round(float(np.max(np.abs(original - decoded))), 10),
        "text_reconstruction": "not_supported_by_sentence_embeddings",
    }


def encode(prepared: dict[str, Any], budget: float = 20.0) -> dict[str, Any]:
    return EMBEDDING.request(
        {"text": prepared["text"], "mentions": prepared["mentions"]},
        budget,
    )


def similarity(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    a = np.asarray(first["windows"], dtype=np.float64)
    b = np.asarray(second["windows"], dtype=np.float64)
    scores = a @ b.T
    flat_index = int(np.argmax(scores))
    left, right = np.unravel_index(flat_index, scores.shape)
    pooled = float(np.dot(np.asarray(first["pooled"]), np.asarray(second["pooled"])))
    return {
        "max_window_cosine": round(float(scores[left, right]), 6),
        "pooled_cosine_diagnostic": round(pooled, 6),
        "winning_window_pair": [int(left), int(right)],
        "first_canonical_spans": first["spans"][left],
        "second_canonical_spans": second["spans"][right],
    }


def embedding_test(primary: dict[str, Any], comparison: dict[str, Any] | None, timeout: float) -> dict[str, Any]:
    ready = wait_until_ready(EMBEDDING, timeout)
    result: dict[str, Any] = {"worker": ready, "model_version": version("embedding")}
    if ready["status"] != "ready":
        result["status"] = "unavailable"
        return result
    first = encode(primary)
    result["status"] = first.get("status")
    if first.get("status") != "ready":
        result["reason"] = first.get("reason", "embedding_failed")
        return result
    pooled = np.asarray(first["pooled"], dtype=np.float64)
    result.update(
        {
            "dimension": int(pooled.size),
            "window_count": len(first["windows"]),
            "pooled_norm": round(float(np.linalg.norm(pooled)), 8),
            "input_hash": first["input_hash"],
            "canonical_window_spans": first["spans"],
            "vector_preview": [round(float(value), 6) for value in pooled[:8]],
            "binary_decode": vector_decode(first["pooled"]),
        }
    )
    if comparison is not None:
        second = encode(comparison)
        result["comparison_status"] = second.get("status")
        if second.get("status") == "ready":
            result["similarity"] = similarity(first, second)
        else:
            result["comparison_reason"] = second.get("reason", "embedding_failed")
    return result


def nli_test(prepared: dict[str, Any], timeout: float) -> dict[str, Any]:
    ready = wait_until_ready(NLI, timeout)
    result: dict[str, Any] = {"worker": ready, "model_version": version("nli")}
    if ready["status"] != "ready":
        result["status"] = "unavailable"
        return result
    analysis = {"redacted_text": prepared["text"], "clauses": prepared["clauses"]}
    inference = NLI.request(
        {
            "text": prepared["text"],
            "mentions": prepared["mentions"],
            "candidates": nli_candidates(analysis),
            "user": "terminal-ephemeral",
            "generation": "terminal-ephemeral",
        },
        min(60.0, timeout),
    )
    result.update(inference)
    return result


def dmrst_test(prepared: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    result = parse_dmrst(prepared["text"])
    return {**result, "inference_seconds": round(time.monotonic() - started, 3)}


def conversation_turn(
    text: str,
    state: dict[str, Any],
    raw: bool,
    generation_mode: str,
    responder: NLPService,
    mathematical_profile: str = "balanced",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Analyze one turn and produce a response while keeping state in memory only."""
    started = time.monotonic()
    analysis, next_state, _ = analyze_turn(
        text,
        state,
        {"alias_key": "terminal-local-test-only", "local_unredacted": raw, "mathematical_profile": mathematical_profile},
    )
    apply_memory_harness(
        analysis,
        next_state,
        state,
        memory_generation="terminal-ephemeral",
        session_id="terminal-ephemeral",
    )
    if generation_mode == "local":
        response, response_mode = responder.generate(
            analysis,
            prior_turns=state.get("turns", []),
            share_history=False,
            user_id=None,
        )
    else:
        response = deterministic_response(analysis)
        response_mode = "deterministic_local"
    analysis["memory_update"]["status"] = "transient_session"
    return {
        "response_text": response,
        "response_mode": response_mode,
        "strategy": analysis["strategy"],
        "topic_id": analysis.get("topic_id"),
        "turn_index": len(next_state.get("turns", [])),
        "dmrst": analysis.get("dmrst", {}),
        "mathematical_models": analysis.get("mathematical_models", {}),
        "response_plan": analysis.get("response_plan"),
        "situational_structure": analysis.get("situational_structure"),
        "ssm_metadata": analysis.get("ssm_metadata"),
        "generation": analysis.get("generation"),
        "memory_update": analysis.get("memory_update"),
        "context_packet": analysis.get("context_packet"),
        "core_pipeline_seconds": round(time.monotonic() - started, 3),
    }, next_state


def print_reply(conversation: dict[str, Any]) -> None:
    print("\n[SANCTUARY RESPONSE]")
    print(conversation["response_text"])
    structure = conversation.get('situational_structure')
    if structure:
        print('\n[SSM — current session; experimental extraction]')
        for layer in ('event', 'constraints', 'reaction', 'meaning', 'temporal', 'language'):
            print(f'{layer}: {json.dumps(structure[layer], ensure_ascii=True)}')
    print(
        f"\n[turn={conversation['turn_index']} | mode={conversation['response_mode']} | "
        f"strategy={conversation['strategy']} | topic={conversation.get('topic_id') or 'unassigned'}]"
    )
    generation = conversation.get("generation") or {}
    if generation:
        attempts = generation.get("attempts", [])
        print(
            f"Generator: {generation.get('mode', conversation['response_mode'])} | "
            f"status={generation.get('status', 'unknown')} | attempts={len(attempts)}"
        )
        if generation.get("selected_attempt"):
            semantic = generation.get("semantic_validation", {})
            print(
                f"Selected draft: {generation['selected_attempt']} | "
                f"semantic={semantic.get('semantic_score', 'unavailable')} | "
                f"near-copy={semantic.get('copy_similarity', 'unavailable')}"
            )
        for item in attempts:
            structural = item.get("validation", {}).get("violations", [])
            semantic = item.get("semantic_validation", {}).get("violations", [])
            if structural or semantic:
                print(
                    f"Draft {item.get('attempt', '?')}: {item.get('status', 'unknown')} | "
                    + ", ".join([*structural, *semantic])
                )
        rejected = [item for item in attempts if item.get("status") in {"rejected", "semantic_rejected"}]
        if rejected:
            last = rejected[-1]
            violations = [
                *last.get("validation", {}).get("violations", []),
                *last.get("semantic_validation", {}).get("violations", []),
            ]
            print("Validation rejected: " + ", ".join(violations))
    memory = conversation.get("memory_update") or {}
    packet = conversation.get("context_packet") or {}
    if memory:
        operation_counts: dict[str, int] = {}
        for item in memory.get("operations", []):
            operation = item.get("operation", "UNKNOWN")
            operation_counts[operation] = operation_counts.get(operation, 0) + 1
        compact = ", ".join(f"{key}={value}" for key, value in sorted(operation_counts.items())) or "NO_OP"
        print(
            f"Memory: revision={memory.get('memory_revision')} | {compact} | "
            f"history={len(packet.get('relevant_prior_evidence', []))} | "
            f"abstained={packet.get('abstained_from_history', True)}"
        )
        trace = packet.get("retrieval_trace", {})
        if trace.get("excluded_superseded_ids"):
            print("Memory guard: excluded superseded " + ", ".join(trace["excluded_superseded_ids"]))
        if trace.get("unresolved_assertion_ids"):
            print("Memory guard: unresolved " + ", ".join(trace["unresolved_assertion_ids"]))


def terminal_report(result: dict[str, Any]) -> None:
    print("\nSANCTUARY LOCAL MODEL TEST")
    print("=" * 29)
    print(f"Privacy mode : {result['privacy_mode']}")
    print(f"Persistence  : disabled (no database writes)")
    print(f"Provider/API : {result['provider_mode']}")
    print(f"Parser       : {result['input']['parser_backend']}")
    print(f"Redactions   : {result['input']['redaction_count']}")
    if result["input"].get("parser_fallback"):
        print(f"Parser note  : {result['input']['parser_fallback']}")

    embedding = result.get("embedding")
    if embedding:
        print("\n[ENCODER + VECTOR DECODE]")
        print(f"Status       : {embedding.get('status')}")
        if embedding.get("status") == "ready":
            print(f"Dimension    : {embedding['dimension']}")
            print(f"Windows      : {embedding['window_count']}")
            print(f"Vector norm  : {embedding['pooled_norm']}")
            print(f"Preview      : {embedding['vector_preview']}")
            decoded = embedding["binary_decode"]
            print(f"Decode check : {decoded['status']}, {decoded['byte_length']} bytes, max error {decoded['max_roundtrip_error']}")
            print("Text decode  : impossible by design; sentence embeddings are one-way representations")
            if embedding.get("similarity"):
                score = embedding["similarity"]
                print(f"Max cosine   : {score['max_window_cosine']}")
                print(f"Pooled cosine: {score['pooled_cosine_diagnostic']} (diagnostic only)")
        else:
            print(f"Reason       : {embedding.get('reason') or embedding.get('worker', {}).get('reason')}")

    classification = result.get("nli")
    if classification:
        print("\n[NLI OUTPUT HEAD]")
        print(f"Status       : {classification.get('status')}")
        if classification.get("status") == "ready":
            print(f"Premises     : {classification['premise_count']}")
            suggestions = classification.get("suggestions", [])
            if not suggestions:
                print("Suggestions  : none (all adjusted scores are non-positive)")
            for suggestion in suggestions:
                print(
                    f"- {suggestion['group']}: {suggestion['label']} | "
                    f"adjusted={suggestion['adjusted_score']:.6f}, entailment={suggestion['entailment']:.6f}, "
                    f"spans={suggestion['spans']}"
                )
            print(f"Notice       : {classification['notice']}")
        else:
            print(f"Reason       : {classification.get('reason') or classification.get('worker', {}).get('reason')}")

    discourse = result.get("dmrst")
    if discourse:
        print("\n[DMRST STRUCTURAL DECODER]")
        print(f"Status       : {discourse.get('status')}")
        if discourse.get("status") == "ready":
            print(f"EDUs         : {len(discourse.get('edus', []))}")
            for edu in discourse.get("edus", []):
                print(f"- EDU {edu['id']} {edu['span']}: {edu['text']}")
            print(f"Relations    : {len(discourse.get('tree', []))}")
            for edge in discourse.get("tree", []):
                print(
                    f"- {edge['left']} {edge['left_nuclearity']} -> {edge['right']} "
                    f"{edge['right_nuclearity']} | {edge['relation']}"
                )
        else:
            print(f"Reason       : {discourse.get('reason')}")
        print(f"Runtime      : {discourse['inference_seconds']}s")

    mathematical = result.get("mathematical_models") or result.get("conversation", {}).get("mathematical_models")
    if mathematical:
        print("\n[MATHEMATICAL STATE LAB]")
        print(f"Profile      : {mathematical['profile']}")
        print(f"Dimensions   : {', '.join(mathematical['dimensions'])}")
        for name, model in mathematical["filters"].items():
            estimates = ", ".join("n/a" if not ready else f"{value:.3f}" for value, ready in zip(model["estimate"], model["initialized"]))
            suffix = f", ESS={model['effective_sample_size']:.1f}" if name == "particle_filter" else ""
            print(f"- {name:<16} [{estimates}]{suffix}")
        hmm = mathematical["hmm"]
        print(f"HMM phase    : {hmm['current_state']} | path={' -> '.join(hmm['viterbi_path'])}")
        labels = mathematical["crf"].get("labels", [])
        label_summary = ", ".join(f"{row['clause_id']}={row['label']}" for row in labels) or "unavailable"
        print(f"CRF clauses  : {label_summary}")
        ledger = mathematical["evidence_belief_revision"]
        active = [p for p in ledger["propositions"] if p["status"] != "superseded"]
        print(f"Belief ledger: {len(ledger['propositions'])} proposition(s), {len(ledger['revisions'])} revision(s)")
        for proposition in active[-4:]:
            mass = proposition["mass"]
            print(f"  {proposition['type']}: {proposition['status']} | beta-mean={proposition['bayesian_mean']:.3f} | DS true={mass['true']:.3f}, unknown={mass['unknown']:.3f}")
        graph = mathematical["temporal_narrative_graph"]
        print(f"Narrative graph: {len(graph['nodes'])} node(s), {len(graph['edges'])} edge(s), revision {graph['revision']}")
        print("Boundary     : experimental hypotheses; not calibrated truth and not used to select the reply")


def stop_workers() -> None:
    EMBEDDING.stop()
    NLI.stop()
    worker = dmrst._WORKER
    if worker is not None and worker.poll() is None:
        worker.terminate()
    dmrst._WORKER = None


def main() -> int:
    args = arguments()
    if not manifest() and args.mode in {"embedding", "nli", "all"}:
        print("Neural resource manifest is missing. Run V2\\SETUP_SEMANTIC_MODELS.bat first.", file=sys.stderr)
        return 2
    text = args.text if args.text is not None else input("Enter text (input is not saved): ").strip()
    if not text:
        print("Input cannot be empty.", file=sys.stderr)
        return 2
    comparison_text = args.compare
    if args.text is None and args.mode in {"embedding", "all"}:
        comparison_text = input("Optional comparison text (press Enter to skip): ").strip() or None

    privacy_mode = "raw transient local inference" if args.raw else "redacted local inference (default)"
    generation_mode = "local" if args.provider else args.generator
    provider_mode = "disabled; cached local Transformer" if generation_mode == "local" else "disabled; classical local realization"
    responder = NLPService(alias_key="terminal-local-test-only")
    conversation_state: dict[str, Any] = {}

    def run_turn(turn_text: str, comparison_value: str | None = None) -> dict[str, Any]:
        nonlocal conversation_state
        primary = prepare_text(turn_text, args.raw)
        comparison = prepare_text(comparison_value, args.raw) if comparison_value else None
        result: dict[str, Any] = {
            "status": "completed",
            "privacy_mode": privacy_mode,
            "provider_mode": provider_mode,
            "input": {
                "character_count": len(turn_text),
                "model_character_count": len(primary["text"]),
                "redaction_count": primary["redaction_count"],
                "parser_backend": primary["parser_backend"],
                "parser_fallback": primary["parser_fallback"],
            },
        }
        if args.mode in {"embedding", "all"}:
            result["embedding"] = embedding_test(primary, comparison, args.warmup_timeout)
        if args.mode in {"nli", "all"}:
            result["nli"] = nli_test(primary, args.warmup_timeout)
        if args.no_reply:
            if args.mode in {"dmrst", "all"}:
                result["dmrst"] = dmrst_test(primary)
            return result

        conversation, conversation_state = conversation_turn(
            turn_text, conversation_state, args.raw, generation_mode, responder, args.math_profile
        )
        result["conversation"] = conversation
        if args.mode in {"math", "all"}:
            result["mathematical_models"] = conversation["mathematical_models"]
        if args.mode in {"dmrst", "all"}:
            result["dmrst"] = {
                **conversation["dmrst"],
                "inference_seconds": conversation["core_pipeline_seconds"],
                "runtime_scope": "complete_core_analysis",
            }
        return result

    try:
        with processing_animation("Processing with Sanctuary's local NLP pipeline", enabled=not args.json):
            result = run_turn(text, comparison_text)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        terminal_report(result)
        if result.get("conversation"):
            print_reply(result["conversation"])

        if args.text is None and not args.no_reply:
            print("\nContinue typing to test session context. Commands: /help, /quit")
            while True:
                try:
                    next_text = input("\nYou > ").strip()
                except EOFError:
                    print("\nSession ended.")
                    break
                if not next_text:
                    continue
                if next_text.casefold() in {"/quit", "/exit"}:
                    print("Session ended; ephemeral context was discarded.")
                    break
                if next_text.casefold() == "/help":
                    print("Enter another message, or type /quit. This session is held in memory only.")
                    continue
                with processing_animation("Processing turn", enabled=True):
                    next_result = run_turn(next_text)
                print_reply(next_result["conversation"])
                nli = next_result.get("nli", {})
                suggestions = nli.get("suggestions", [])
                if suggestions:
                    compact = ", ".join(f"{item['label']} ({item['adjusted_score']:.3f})" for item in suggestions)
                    print(f"NLI suggestions: {compact}")
                embedding = next_result.get("embedding", {})
                if embedding.get("status") == "ready":
                    print(f"Encoder: {embedding['window_count']} window(s), norm={embedding['pooled_norm']}")
                mathematical = next_result.get("mathematical_models", {})
                if mathematical:
                    revisions = mathematical["evidence_belief_revision"]["revisions"]
                    print(f"Math lab: HMM={mathematical['hmm']['current_state']}, graph={len(mathematical['temporal_narrative_graph']['nodes'])} nodes, revisions={len(revisions)}")
    finally:
        stop_workers()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
