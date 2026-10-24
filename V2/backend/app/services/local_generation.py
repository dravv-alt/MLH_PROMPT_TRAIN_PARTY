"""Offline local Transformer realization for Sanctuary response plans.

The provider never downloads resources and never owns narrative state.  It is
lazy so analysis-only endpoints and tests do not pay the model-loading cost.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable

from app.services.response_planner import realize_plan_classically, validate_plan_response
from app.services.response_semantics import evaluate_candidates, warm_semantic_worker
from app.services.reflection_style import REFLECTION_STYLE


MODEL_ID = "meta-llama/Llama-3.2-1B-Instruct"
MODEL_REVISION = "22e9fdbe3473c7affd8596fdc248e67e3a004da1"
PROVIDER_VERSION = "local-llama3.2-1b.response-plan.v2"
FEW_SHOT_TARGETS = (
    "You left the conversation carrying disappointment, even though you said what you needed to say.",
    "It sounds like the uncertainty may still be present, rather than settled.",
    "You no longer see the delay as proof that you failed; the concern has shifted.",
)


def repair_second_person_voice(text: str) -> str:
    """Mechanical post-processing before strict voice validation.

    This applies only to the local model's own draft, never to source evidence
    or the response plan. It deliberately has no semantic interpretation.
    """
    repaired = text
    replacements = (
        (r"\bI\s+am\b", "You are"),
        (r"\bI['’]m\b", "You're"),
        (r"\bI['’]ve\b", "You've"),
        (r"\bI['’]ll\b", "You'll"),
        (r"\bI['’]d\b", "You'd"),
        (r"\bmyself\b", "yourself"),
        (r"\bmine\b", "yours"),
        (r"\bmy\b", "your"),
        (r"\bme\b", "you"),
        (r"\bI\b", "You"),
    )
    for pattern, replacement in replacements:
        repaired = re.sub(pattern, replacement, repaired)
    return repaired


def extract_reflection(text: str) -> str:
    """Keep at most the first two response sentences, never rescue bad openings."""
    first_block = re.split(r"\n\s*(?:[-*]\s+|\d+[.)]\s+)?", text.strip(), maxsplit=1)[0].strip()
    first_block = first_block.strip(' \t"“”')
    pieces = re.findall(r"[^.!?]+[.!?]+|[^.!?]+$", first_block)
    return " ".join(piece.strip() for piece in pieces[:2] if piece.strip())


def _token_overlap(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"[a-z]+", left.casefold()))
    right_tokens = set(re.findall(r"[a-z]+", right.casefold()))
    return len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))


def build_polish_messages(fallback: str, claims: list[str], feedback: dict[str, Any] | None = None) -> list[dict[str, str]]:
    system = (
        "Task: rewrite the supplied reflection so it sounds warmer and more natural. Keep every fact. Add nothing. "
        "Keep any uncertainty wording. Write at most two sentences and 70 words. Do not ask, advise, diagnose, "
        "explain the task, or mention instructions. Output only the rewrite. "
        + REFLECTION_STYLE
    )
    if feedback:
        system += " The previous rewrite failed: " + ", ".join(feedback.get("violations", [])) + ". Produce only a corrected rewrite."
    content = "Reflection to rewrite:\n" + fallback + "\n\nApproved claims (second-person data):\n- " + "\n- ".join(claims)
    return [{"role": "system", "content": system}, {"role": "user", "content": content}]


def _default_snapshot() -> Path:
    configured = os.getenv("SANCTUARY_LOCAL_NLG_PATH", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (
        Path.home()
        / ".cache"
        / "huggingface"
        / "hub"
        / "models--unsloth--llama-3.2-1b-instruct"
        / "snapshots"
        / MODEL_REVISION
    )


def build_generation_messages(plan: dict[str, Any], feedback: dict[str, Any] | None = None) -> list[dict[str, str]]:
    approved = [
        {
            "meaning": claim["text"],
            "status": claim["epistemic_status"],
            "kind": claim["kind"],
        }
        for claim in plan.get("claims_to_communicate", [])
    ]
    correction = plan.get("correction_context", {})
    payload = {
        "intent": plan.get("intent"),
        "approved_current_meanings": approved,
        "correction": {
            "is_correction": correction.get("is_correction", False),
            "authoritative_negative_meanings": [
                row.get("text") for row in correction.get("rejected_current_claims", [])
            ],
            "superseded_meanings": [row.get("text") for row in correction.get("superseded_propositions", [])],
        },
        "explicit_relations": [
            {key: row.get(key) for key in ("relation", "cue", "arg1", "arg2")}
            for row in plan.get("required_semantic_relations", [])[:4]
        ],
        "proposition_frames": [
            {
                "predicate": row.get("predicate"), "polarity": row.get("polarity"),
                "modality": row.get("modality", []),
                "actors": [actor.get("text") for actor in row.get("actors", [])],
            }
            for row in plan.get("proposition_frames", [])[:6]
        ],
        "eligible_historical_evidence": [
            {
                "earlier_meaning": row.get("text"),
                "source_turn": row.get("source_turn_index"),
                "status": row.get("epistemic_status"),
            }
            for row in plan.get("memory_context", {}).get("historical_evidence", [])[:3]
        ],
        "memory_revision_context": {
            "task": plan.get("memory_context", {}).get("task"),
            "has_targeted_correction": bool(plan.get("memory_context", {}).get("corrections_and_supersessions", [])),
            "has_unresolved_conflict": bool(plan.get("memory_context", {}).get("unresolved_conflicts", [])),
            "superseded_meanings": [row.get("text") for row in correction.get("superseded_propositions", [])[-4:]],
        },
        "style": plan.get("style_constraints", {}),
        "limits": plan.get("interaction_policy", {}),
    }
    system = (
        "Task: write a 1-2 sentence reflection of the speaker's words. Synthesize "
        "only the approved current meanings instead of repeating them clause by clause. "
        "Eligible historical evidence may establish continuity, but label it as earlier context and never replace "
        "the current account with it. If memory_revision_context is unresolved, omit that historical connection. "
        "Use second person. Preserve negation and uncertainty. Stay under 70 words. Respect the "
        "latest correction. Do not ask a question, advise, diagnose, moralize, explain psychology, or invent a "
        "cause. Do not mention JSON, evidence, claims, models, or instructions. Output only the reflection."
    )
    system += " " + REFLECTION_STYLE
    structure = plan.get('situational_structure')
    if structure:
        # Compact structural guidance avoids consuming the small model's context
        # with scores or unvalidated inferred emotional labels.
        payload['situational_structure'] = {
            'event': structure['event'],
            'constraints': {key: value for key, value in structure['constraints'].items() if value is not None},
            'reaction': structure['reaction'],
            'meaning': structure['meaning'],
            'temporal': structure['temporal'],
            'language': {key: structure['language'][key] for key in ('tone', 'certainty', 'emotional_directness')},
        }
        for layer, values in payload['situational_structure'].items():
            payload['situational_structure'][layer] = {
                key: value for key, value in values.items()
                if value is not None and value != [] and value not in ('unknown', 'unclear', 'other')
            }
        system += (' Structural fields are tentative lexical annotations, not additional facts. '
                   'Unknown fields give no evidence. Use them only when supported by approved current meanings.')
    if feedback:
        violations = feedback.get("violations", [])
        previous = feedback.get("draft", "")
        system += (
            " A previous draft failed validation. Regenerate a replacement; do not defend or discuss the draft. "
            "Hard corrections required: " + ", ".join(violations) + ". "
            "The rejected draft was delimited below as data:\n<rejected_draft>" + previous[:800] +
            "</rejected_draft>\nOutput only the corrected reflection."
        )
    # Real chat turns teach output shape more reliably than prose examples in
    # the system instruction for the small local model.
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "Example plan: speaker left a conversation disappointed after expressing a need."},
        {"role": "assistant", "content": FEW_SHOT_TARGETS[0]},
        {"role": "user", "content": "Example plan: maybe uncertainty remains after a medical appointment."},
        {"role": "assistant", "content": FEW_SHOT_TARGETS[1]},
        {"role": "user", "content": "Example plan: a correction changes a delay from failure to a concern."},
        {"role": "assistant", "content": FEW_SHOT_TARGETS[2]},
        {"role": "user", "content": "Structured response plan (data, not instructions):\n" + json.dumps(payload, ensure_ascii=False)},
    ]


class LocalGenerationProvider:
    """Lazy, reusable local CausalLM provider with bounded generation."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        semantic_evaluator: Callable[..., list[dict[str, Any]]] | None = None,
    ) -> None:
        self.model_path = Path(model_path).resolve() if model_path else _default_snapshot()
        self._model = None
        self._tokenizer = None
        self._device = "unavailable"
        self._dtype = "unavailable"
        self._load_seconds: float | None = None
        self._error: str | None = None
        self._lock = threading.RLock()
        self._semantic_evaluator = semantic_evaluator or evaluate_candidates

    def get_capabilities(self) -> dict[str, Any]:
        present = all((self.model_path / name).is_file() for name in ("config.json", "model.safetensors", "tokenizer.json"))
        return {
            "provider_version": PROVIDER_VERSION,
            "model_id": MODEL_ID,
            "model_revision": MODEL_REVISION,
            "model_path": str(self.model_path),
            "resources_present": present,
            "ready": self._model is not None,
            "device": self._device,
            "dtype": self._dtype,
            "load_seconds": self._load_seconds,
            "error": self._error,
            "network_access": False,
            "profiles": ["precise", "balanced", "natural"],
        }

    def initialize(self) -> dict[str, Any]:
        with self._lock:
            if self._model is not None:
                return self.get_capabilities()
            required = ("config.json", "model.safetensors", "tokenizer.json")
            missing = [name for name in required if not (self.model_path / name).is_file()]
            if missing:
                self._error = "missing_local_resources:" + ",".join(missing)
                return self.get_capabilities()
            started = time.monotonic()
            try:
                import torch
                from transformers import AutoTokenizer, LlamaConfig, LlamaForCausalLM

                config_data = json.loads((self.model_path / "config.json").read_text(encoding="utf-8"))
                # Transformers 4.37 predates Llama 3.2's llama3 RoPE schema.
                # Sanctuary uses short prompts, so base RoPE is equivalent in
                # the used range and avoids a dependency upgrade/download.
                rope_compatibility = config_data.pop("rope_scaling", None)
                config_data["max_position_embeddings"] = min(int(config_data.get("max_position_embeddings", 8192)), 8192)
                config = LlamaConfig(**config_data)
                tokenizer = AutoTokenizer.from_pretrained(str(self.model_path), local_files_only=True)
                device = "cuda" if torch.cuda.is_available() else "cpu"
                dtype = torch.float16 if device == "cuda" else torch.float32
                model = LlamaForCausalLM.from_pretrained(
                    str(self.model_path), config=config, local_files_only=True, torch_dtype=dtype
                ).to(device).eval()
                model.generation_config.temperature = 1.0
                model.generation_config.top_p = 1.0
                self._model, self._tokenizer = model, tokenizer
                self._device, self._dtype = device, str(dtype).replace("torch.", "")
                self._load_seconds = round(time.monotonic() - started, 3)
                self._error = None
                self._rope_compatibility = bool(rope_compatibility)
            except Exception as exc:  # safe local fallback owns failure recovery
                self._error = f"initialization_failed:{type(exc).__name__}:{exc}"
                self._model = self._tokenizer = None
            return self.get_capabilities()

    def _candidate(self, plan: dict[str, Any], profile: str, feedback: dict[str, Any] | None, attempt: int, *, messages: list[dict[str, str]] | None = None) -> tuple[str | None, dict[str, Any]]:
        import torch
        from transformers import StoppingCriteria, StoppingCriteriaList

        messages = messages or build_generation_messages(plan, feedback)
        inputs = self._tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(self._device)
        # This seed is appended after the assistant header created by
        # apply_chat_template(add_generation_prompt=True), never in system/user data.
        assistant_prefill = "You"
        seed = self._tokenizer(assistant_prefill, add_special_tokens=False, return_tensors="pt").input_ids.to(self._device)
        inputs = torch.cat((inputs, seed), dim=1)
        if inputs.shape[1] > 1024:
            return None, {"reason": "response_plan_too_long", "input_tokens": int(inputs.shape[1])}
        options: dict[str, Any] = {
            "max_new_tokens": 90,
            "pad_token_id": self._tokenizer.eos_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
            "use_cache": True,
        }
        newline_ids = self._tokenizer("\n", add_special_tokens=False).input_ids
        start_length = int(inputs.shape[1])

        class _StopAtNewline(StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                generated_ids = input_ids[0, start_length:].tolist()
                return bool(newline_ids and len(generated_ids) >= len(newline_ids)
                            and generated_ids[-len(newline_ids):] == newline_ids)

        options["stopping_criteria"] = StoppingCriteriaList([_StopAtNewline()])
        if profile == "natural":
            seed = int(plan["plan_id"].split("_")[-1][:8], 16) + attempt
            torch.manual_seed(seed)
            if self._device == "cuda":
                torch.cuda.manual_seed_all(seed)
            options.update(do_sample=True, temperature=.35, top_p=.82, repetition_penalty=1.10)
        elif profile == "balanced":
            options.update(do_sample=False, repetition_penalty=1.08)
        elif profile == "precise":
            options.update(do_sample=False, repetition_penalty=1.12, max_new_tokens=72)
        else:
            return None, {"reason": "unknown_generation_profile"}
        started = time.monotonic()
        with torch.inference_mode():
            generated = self._model.generate(inputs, **options)
        continuation = self._tokenizer.decode(generated[0, inputs.shape[1]:], skip_special_tokens=True).strip()
        raw_value = (assistant_prefill + " " + continuation).strip()
        raw_value = re.sub(r"^(?:reflection|response)\s*:\s*", "", raw_value, flags=re.I).strip().strip('"')
        extracted = extract_reflection(raw_value)
        value = repair_second_person_voice(extracted)
        return value or None, {
            "input_tokens": int(inputs.shape[1]),
            "output_tokens": int(generated.shape[1] - inputs.shape[1]),
            "generation_seconds": round(time.monotonic() - started, 3),
            "assistant_prefill": assistant_prefill,
            "raw_draft": raw_value,
            "extracted_draft": extracted,
            "extraction_changed": extracted != raw_value,
            "repair_applied": value != extracted,
        }

    def generate(self, plan: dict[str, Any], options: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
        options = options or {}
        profile = options.get("profile", "balanced")
        maximum_attempts = max(1, min(3, int(options.get("maximum_attempts", 3))))
        capabilities = self.initialize()
        if not capabilities["ready"]:
            fallback = realize_plan_classically(plan)
            return fallback, {
                "status": "fallback",
                "mode": "classical_local_fallback",
                "reason": capabilities.get("error") or "local_model_unavailable",
                "attempts": [],
                "capabilities": capabilities,
            }
        if self._semantic_evaluator is evaluate_candidates:
            # Warm NLI while the CausalLM produces bounded drafts. If it is
            # still cold at verification time, Transformer drafts fail closed.
            warm_semantic_worker()
        attempts: list[dict[str, Any]] = []
        feedback: dict[str, Any] | None = None
        viable: list[tuple[str, int]] = []
        with self._lock:
            for attempt in range(maximum_attempts):
                candidate_profile = profile if attempt == 0 else "precise"
                try:
                    candidate, timing = self._candidate(plan, candidate_profile, feedback, attempt)
                except Exception as exc:
                    attempts.append({"attempt": attempt + 1, "status": "error", "reason": f"{type(exc).__name__}:{exc}"})
                    break
                validation = validate_plan_response(plan, candidate or "")
                attempt_record = {
                    "attempt": attempt + 1,
                    "profile": candidate_profile,
                    "status": "structurally_valid" if validation["is_valid"] else "rejected",
                    "validation": validation,
                    **timing,
                }
                if not validation["is_valid"]:
                    # Diagnostics are persisted only in the caller's existing
                    # redacted analysis record; source input is never added.
                    attempt_record["rejected_draft"] = candidate or ""
                    attempt_record["failed_validator_patterns"] = validation["failure_patterns"]
                attempts.append(attempt_record)
                if candidate and validation["is_valid"]:
                    viable.append((candidate, len(attempts) - 1))
                    feedback = None
                else:
                    feedback = {"violations": validation["violations"], "draft": candidate or ""}

        if viable:
            semantic_rows = self._semantic_evaluator(
                plan,
                [candidate for candidate, _ in viable],
                budget=float(options.get("semantic_budget", 5.0)),
            )
            ranked: list[tuple[float, int, str, dict[str, Any]]] = []
            for (candidate, attempt_index), semantic in zip(viable, semantic_rows):
                attempts[attempt_index]["semantic_validation"] = semantic
                if not semantic.get("is_valid", True):
                    attempts[attempt_index]["status"] = "semantic_rejected"
                    continue
                attempts[attempt_index]["status"] = "accepted_candidate"
                ranked.append((float(semantic.get("score", 0.0)), -attempt_index, candidate, semantic))
            if ranked:
                _, neg_attempt_index, candidate, selected_semantic = max(ranked, key=lambda row: (row[0], row[1]))
                selected_attempt = -neg_attempt_index
                attempts[selected_attempt]["status"] = "selected"
                return candidate, {
                    "status": "ready",
                    "mode": "local_transformer",
                    "profile": profile,
                    "selection": "semantic_grounding_then_comparative_synthesis",
                    "selected_attempt": selected_attempt + 1,
                    "semantic_validation": selected_semantic,
                    "attempts": attempts,
                    "capabilities": capabilities,
                }
        fallback = realize_plan_classically(plan)
        fallback_validation = validate_plan_response(plan, fallback)
        if not fallback_validation["is_valid"]:
            # Fail closed: return the grounded classical rendering, but make
            # the failure explicit instead of presenting it as a safe success.
            # Callers and evaluations can now distinguish this state.
            fallback_status = "invalid_fallback"
        else:
            fallback_status = "fallback"
        return fallback, {
            "status": fallback_status,
            "mode": "classical_local_fallback",
            "reason": "no_transformer_candidate_passed",
            "profile": profile,
            "attempts": attempts,
            "fallback_validation": fallback_validation,
            "capabilities": capabilities,
        }

    def generate_polish(self, plan: dict[str, Any], options: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
        """Use the valid classical realization as the sole semantic source.

        A rejected rewrite never replaces the fallback. The returned Transformer
        string is exactly the string structurally and semantically validated.
        """
        options = options or {}
        fallback = realize_plan_classically(plan)
        capabilities = self.initialize()
        if not capabilities["ready"]:
            return fallback, {"status": "fallback", "mode": "classical_local_fallback",
                              "reason": capabilities.get("error") or "local_model_unavailable", "attempts": [],
                              "fallback_text": fallback, "capabilities": capabilities}
        if self._semantic_evaluator is evaluate_candidates:
            warm_semantic_worker()
        claims = [repair_second_person_voice(row.get("text", "")) for row in plan.get("claims_to_communicate", []) if row.get("text")]
        attempts: list[dict[str, Any]] = []
        viable: list[tuple[str, int]] = []
        feedback: dict[str, Any] | None = None
        with self._lock:
            for attempt in range(max(1, min(3, int(options.get("maximum_attempts", 3))))):
                profile = "natural" if attempt == 0 else "precise"
                message_set = build_polish_messages(fallback, claims, feedback)
                try:
                    candidate, timing = self._candidate(plan, profile, feedback, attempt, messages=message_set)
                except Exception as exc:
                    attempts.append({"attempt": attempt + 1, "status": "error", "reason": f"{type(exc).__name__}:{exc}"})
                    break
                validation = validate_plan_response(plan, candidate or "")
                reasons = list(validation["violations"])
                no_op = bool(candidate and candidate.casefold().strip() == fallback.casefold().strip())
                copied_target = max((_token_overlap(candidate or "", target) for target in FEW_SHOT_TARGETS), default=0.0) > .60
                if no_op:
                    reasons.append("polish_noop")
                if copied_target:
                    reasons.append("few_shot_copy_overlap_gt_60pct")
                record = {"attempt": attempt + 1, "profile": profile, "status": "structurally_valid" if not reasons else "rejected",
                          "validation": validation, "final_violations": sorted(set(reasons)), **timing}
                if reasons:
                    record["rejected_draft"] = candidate or ""
                    record["failed_validator_patterns"] = validation.get("failure_patterns", {})
                    feedback = {"violations": record["final_violations"], "draft": candidate or ""}
                else:
                    viable.append((candidate, len(attempts)))
                    feedback = None
                attempts.append(record)
        if viable:
            semantic_rows = self._semantic_evaluator(plan, [candidate for candidate, _ in viable], budget=float(options.get("semantic_budget", 5.0)))
            ranked = []
            for (candidate, index), semantic in zip(viable, semantic_rows):
                attempts[index]["grounding"] = semantic
                if not semantic.get("is_valid", True):
                    attempts[index]["status"] = "semantic_rejected"
                    continue
                attempts[index]["status"] = "selected"
                ranked.append((float(semantic.get("score", 0.0)), -index, candidate, semantic))
            if ranked:
                _, neg_index, candidate, semantic = max(ranked, key=lambda row: (row[0], row[1]))
                return candidate, {"status": "ready", "mode": "local_transformer_polish", "fallback_text": fallback,
                                   "selected_attempt": -neg_index + 1, "attempts": attempts,
                                   "semantic_validation": semantic, "capabilities": capabilities}
        return fallback, {"status": "fallback", "mode": "classical_local_fallback", "reason": "no_polish_candidate_passed",
                          "fallback_text": fallback, "attempts": attempts,
                          "fallback_validation": validate_plan_response(plan, fallback), "capabilities": capabilities}

    def cancel(self, request_id: str) -> dict[str, Any]:
        return {"request_id": request_id, "cancelled": False, "reason": "generation_is_synchronous_and_bounded"}

    def dispose(self) -> None:
        with self._lock:
            self._model = self._tokenizer = None
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
            self._device = self._dtype = "unavailable"


LOCAL_GENERATOR = LocalGenerationProvider()
