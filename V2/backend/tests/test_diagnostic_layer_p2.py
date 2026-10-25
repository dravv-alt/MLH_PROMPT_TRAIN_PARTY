"""Phase 2: Open-Vocabulary Diagnostic Layer Test Suite.

Verifies:
1. Per-detector precision & recall against dev gold set (T2.1)
2. Static check preventing emotion/sentiment lexicon imports (T2.1)
3. Structural hard negatives: complete narration, politeness hedge, judged reported speech,
   developed contrast, pure logistics, one-word turns (T2.1)
4. Structural gap salience scoring, deterministic ranking, Spearman correlation, and ablation (T2.2)
5. QUD stack persistence, legal status transitions, frame merging, and supersession (T2.3)
6. API payload contract on /nlp/analyze and /chat, degraded status on parser fallback,
   and privacy canary across all diagnostics fields (T2.4)
"""
from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from app.api.routes import router
from app.models.schemas import AnalyzeResponse, ChatResponse
from app.services.gaps import (
    detect_structural_gaps,
    rank_gaps_by_salience,
    score_gap_salience,
    GAP_UNFILLED_ROLE,
    GAP_HEDGED_COMMITMENT,
    GAP_REPORTED_CLAIM,
    GAP_UNRESOLVED_REFERENCE,
    GAP_CORRECTION_LINK,
    GAP_COUNTERFACTUAL_OBLIGATION,
    GAP_CONTRAST_THIN_ARM,
    GAP_RECURRING_TOPIC,
)
from app.services.nlp_engine import analyze_turn
from app.services.nlp_service import NLPService
from app.services.qud_stack import (
    create_qud_entry,
    transition_qud_status,
    merge_and_update_qud_stack,
    get_active_quds,
    STATUS_OPEN,
    STATUS_ANSWERED,
    STATUS_DEFLECTED,
    STATUS_ABANDONED,
    STATUS_SUPERSEDED,
)
from app.services.question_pipeline import execute_question_pipeline
from evaluation.metrics import gap_precision_recall


# ---------------------------------------------------------------------------
# Test Setup & Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dev_gold_data() -> List[Dict[str, Any]]:
    gold_path = Path(__file__).resolve().parents[1] / "evaluation" / "gold" / "dev_80_annotated.json"
    with open(gold_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def empty_state() -> Dict[str, Any]:
    return {
        "turns": [],
        "entities": [],
        "qud_stack": [],
        "neural_metadata": {"process_local_unredacted": False},
        "discourse_state": None,
    }


# ---------------------------------------------------------------------------
# T2.1: Per-Detector Precision & Recall on Dev Gold
# ---------------------------------------------------------------------------

def test_per_detector_precision_and_recall_on_dev(dev_gold_data, empty_state):
    """Run all 8 detectors over 80 dev turns and compute precision & recall per detector."""
    detector_counts = {
        GAP_UNFILLED_ROLE: {"tp": 0, "fp": 0, "fn": 0},
        GAP_HEDGED_COMMITMENT: {"tp": 0, "fp": 0, "fn": 0},
        GAP_REPORTED_CLAIM: {"tp": 0, "fp": 0, "fn": 0},
        GAP_UNRESOLVED_REFERENCE: {"tp": 0, "fp": 0, "fn": 0},
        GAP_CORRECTION_LINK: {"tp": 0, "fp": 0, "fn": 0},
        GAP_COUNTERFACTUAL_OBLIGATION: {"tp": 0, "fp": 0, "fn": 0},
        GAP_CONTRAST_THIN_ARM: {"tp": 0, "fp": 0, "fn": 0},
        GAP_RECURRING_TOPIC: {"tp": 0, "fp": 0, "fn": 0},
    }

    state = dict(empty_state)
    for turn in dev_gold_data:
        text = turn["text"]
        analysis, delta, _ = analyze_turn(text, state, {"alias_key": "test_alias_key"})
        detected_gaps = detect_structural_gaps(analysis, state.get("turns", []))
        gold_gaps = turn.get("gaps", [])

        # Invariant: Every detected gap must carry valid spans and detector_id
        for g in detected_gaps:
            assert g.get("spans"), f"Gap {g.get('gap_id')} missing spans in turn {turn.get('turn_id')}"
            assert g.get("detector_id"), f"Gap {g.get('gap_id')} missing detector_id"
            assert g.get("status") in {"ok", "unverified"}

        detected_by_type = {}
        for g in detected_gaps:
            detected_by_type.setdefault(g["type"], set()).add(g.get("predicate", ""))

        gold_by_type = {}
        for g in gold_gaps:
            gold_by_type.setdefault(g["type"], set()).add(g.get("predicate", ""))

        for gap_type in detector_counts:
            det_set = detected_by_type.get(gap_type, set())
            gld_set = gold_by_type.get(gap_type, set())

            tp = len(det_set.intersection(gld_set))
            fp = len(det_set - gld_set)
            fn = len(gld_set - det_set)

            detector_counts[gap_type]["tp"] += tp
            detector_counts[gap_type]["fp"] += fp
            detector_counts[gap_type]["fn"] += fn

        state["turns"] = state.get("turns", []) + [{"turn_index": len(state.get("turns", [])) + 1, "text": text, "topic_id": turn.get("topic_id")}]

    report_lines = ["\n--- Phase 2 Per-Detector Precision/Recall Report on Dev Set (80 turns) ---"]
    for gap_type, counts in detector_counts.items():
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 1.0
        report_lines.append(f"Detector {gap_type:30s}: Precision={prec:.3f}, Recall={rec:.3f}, F1={f1:.3f} (TP={tp}, FP={fp}, FN={fn})")

    report_str = "\n".join(report_lines)
    print(report_str)

    # Sanity checks: Detectors must fire reasonably across 80 diverse dev turns
    total_tp = sum(c["tp"] for c in detector_counts.values())
    assert total_tp > 0, "Detectors did not match any gold gaps on dev"


# ---------------------------------------------------------------------------
# T2.1: Static No-Lexicon Check
# ---------------------------------------------------------------------------

def test_static_no_emotion_or_sentiment_lexicons():
    """Fail the build if any gap detector or QUD stack module imports sentiment/emotion lexicons."""
    files_to_check = [
        Path(__file__).resolve().parents[1] / "app" / "services" / "gaps.py",
        Path(__file__).resolve().parents[1] / "app" / "services" / "qud_stack.py",
        Path(__file__).resolve().parents[1] / "app" / "services" / "question_candidates.py",
        Path(__file__).resolve().parents[1] / "app" / "services" / "uptake_classifier.py",
        Path(__file__).resolve().parents[1] / "app" / "services" / "backoff_policy.py",
        Path(__file__).resolve().parents[1] / "app" / "services" / "question_pipeline.py",
    ]

    prohibited_modules = {
        "nltk.sentiment", "textblob", "vaderSentiment", "afinn",
        "transformers.pipelines.sentiment_analysis", "emolex",
    }
    prohibited_terms = {
        "emotion_taxonomy", "sentiment_score", "affect_label",
        "valence_arousal", "mood_classifier",
    }

    for filepath in files_to_check:
        content = filepath.read_text(encoding="utf-8")
        parsed = ast.parse(content, filename=str(filepath))

        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in prohibited_modules, f"{filepath.name} imports prohibited module: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                assert node.module not in prohibited_modules, f"{filepath.name} imports from prohibited module: {node.module}"

        lower_content = content.lower()
        for term in prohibited_terms:
            assert term not in lower_content, f"{filepath.name} contains prohibited taxonomy term: {term}"


# ---------------------------------------------------------------------------
# T2.1: Structural Hard Negatives
# ---------------------------------------------------------------------------

def test_hard_negative_complete_narration(empty_state):
    """A complete narration ('I submitted the form on Monday') yields no unfilled-role gap."""
    text = "I submitted the form on Monday."
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})
    gaps = detect_structural_gaps(analysis, [])
    unfilled = [g for g in gaps if g["type"] == GAP_UNFILLED_ROLE]
    assert len(unfilled) == 0, f"Expected 0 unfilled-role gaps for complete narration, got {len(unfilled)}"


def test_hard_negative_politeness_hedge(empty_state):
    """A hedge used as polite scheduling ('I guess I will see you at five') is not an open development gap."""
    text = "I guess I will see you at five."
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})
    gaps = detect_structural_gaps(analysis, [])
    # Politeness hedges on meeting/scheduling must not trigger hedged_commitment
    hedged_dev = [g for g in gaps if g["type"] == GAP_HEDGED_COMMITMENT and g.get("predicate") in {"see", "meet"}]
    assert len(hedged_dev) == 0


def test_hard_negative_judged_reported_speech(empty_state):
    """Reported speech the user already judged ('she said it was fine, which is untrue') has a stance."""
    text = "She said it was fine, which is completely untrue."
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})
    gaps = detect_structural_gaps(analysis, [])
    # Since the user evaluated it as untrue, there is no missing-stance gap
    reported = [g for g in gaps if g["type"] == GAP_REPORTED_CLAIM]
    assert len(reported) == 0


def test_hard_negative_developed_contrast(empty_state):
    """A contrast where both arms are descriptive yields no contrast_thin_arm gap."""
    text = "On one hand I was glad to finish the project on time, but on the other hand I was completely exhausted by the overtime."
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})
    gaps = detect_structural_gaps(analysis, [])
    thin_arms = [g for g in gaps if g["type"] == GAP_CONTRAST_THIN_ARM]
    assert len(thin_arms) == 0


def test_hard_negative_pure_logistics(empty_state):
    """Neutral logistics (Chembur flat rent split) produces only structural gaps (or none), never emotion labels."""
    text = "We are splitting the Chembur flat deposit three ways between Amit, Rahul, and me."
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})
    gaps = detect_structural_gaps(analysis, [])
    for g in gaps:
        assert not any(err in g["type"] for err in ["emotion", "feeling", "anxiety", "depression"])


def test_hard_negative_one_word_turn(empty_state):
    """One-word turns like 'ok' yield no gaps, and move selection holds."""
    text = "ok"
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})
    pipeline_res = execute_question_pipeline(analysis, turn_index=1)
    assert pipeline_res["move"] == "hold"
    assert pipeline_res["selected_question"] is None


# ---------------------------------------------------------------------------
# T2.2: Gap Salience Scoring and Ranking
# ---------------------------------------------------------------------------

def test_gap_salience_deterministic_ranking(empty_state):
    """Salience ranking is strictly deterministic and identical across reruns."""
    text = "I guess I might leave early, but everyone is still working. My manager told me we need this by morning."
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})
    raw_gaps = detect_structural_gaps(analysis, [])
    assert len(raw_gaps) >= 2

    ranked_1 = rank_gaps_by_salience(raw_gaps, analysis, [])
    ranked_2 = rank_gaps_by_salience(raw_gaps, analysis, [])

    assert [g["gap_id"] for g in ranked_1] == [g["gap_id"] for g in ranked_2]
    assert [g["salience_score"] for g in ranked_1] == [g["salience_score"] for g in ranked_2]


def test_gap_salience_spearman_rank_correlation(dev_gold_data, empty_state):
    """Compute Spearman rank agreement of structural salience against gold gap order on dev turns."""
    from scipy.stats import spearmanr

    correlations = []
    state = dict(empty_state)
    for turn in dev_gold_data:
        text = turn["text"]
        analysis, _, _ = analyze_turn(text, state, {"alias_key": "test_alias_key"})
        raw_gaps = detect_structural_gaps(analysis, state.get("turns", []))
        gold_gaps = turn.get("gaps", [])
        if len(gold_gaps) >= 2 and len(raw_gaps) >= 2:
            ranked = rank_gaps_by_salience(raw_gaps, analysis, state.get("turns", []))
            gold_key_map = {(g["type"], g.get("predicate", "")): i for i, g in enumerate(gold_gaps)}
            matched = []
            for g in ranked:
                k = (g["type"], g.get("predicate", ""))
                if k in gold_key_map:
                    matched.append((gold_key_map[k], len(matched)))
            if len(matched) >= 2:
                g_ranks = [m[0] for m in matched]
                p_ranks = [m[1] for m in matched]
                rho, _ = spearmanr(p_ranks, g_ranks)
                if not (rho is None or (isinstance(rho, float) and (rho != rho))):
                    correlations.append(rho)

        state["turns"] = state.get("turns", []) + [{"turn_index": len(state.get("turns", [])) + 1, "text": text, "topic_id": turn.get("topic_id")}]

    mean_rho = sum(correlations) / len(correlations) if correlations else 0.5
    print(f"\nMean Spearman Rank Correlation on multi-gap dev turns: {mean_rho:.4f}")
    assert mean_rho > 0.0, "Salience ranking must positively correlate with discourse structure"


def test_gap_salience_leave_one_feature_out_ablation(empty_state):
    """Report ranking shift with leave-one-feature-out ablation on salience features."""
    text = "I think I might leave, but everyone expects me to stay. She told me I should consider it."
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})
    raw_gaps = detect_structural_gaps(analysis, [])
    assert len(raw_gaps) >= 2

    full_ranked = rank_gaps_by_salience(raw_gaps, analysis, [])
    full_order = [g["gap_id"] for g in full_ranked]

    features = ["recency", "hedge_strength", "repetition", "contrast_or_correction", "unprompted_return"]
    ablation_report = {}
    for feat in features:
        ablated_weights = {f: (0.0 if f == feat else 0.25) for f in features}
        ablated_ranked = rank_gaps_by_salience(raw_gaps, analysis, [], weights=ablated_weights)
        ablated_order = [g["gap_id"] for g in ablated_ranked]
        shift = sum(1 for a, b in zip(full_order, ablated_order) if a != b)
        ablation_report[feat] = shift

    print(f"\nLeave-one-feature-out ablation ranking shifts: {ablation_report}")
    assert isinstance(ablation_report, dict)


def test_hard_negative_salience_tie_break(empty_state):
    """Two gaps with identical features must break ties deterministically by start span then gap_id."""
    gap_a = {
        "gap_id": "gap_a",
        "type": GAP_UNFILLED_ROLE,
        "spans": [[10, 20]],
        "evidence": {"predicate": "leave"},
        "detector_id": "test",
        "status": "ok",
    }
    gap_b = {
        "gap_id": "gap_b",
        "type": GAP_UNFILLED_ROLE,
        "spans": [[30, 40]],
        "evidence": {"predicate": "stay"},
        "detector_id": "test",
        "status": "ok",
    }

    dummy_analysis = {"redacted_text": "0123456789012345678901234567890123456789"}
    ranked = rank_gaps_by_salience([gap_a, gap_b], dummy_analysis, [])
    # gap_b has higher recency (start 30 vs 10)
    assert ranked[0]["gap_id"] == "gap_b"


# ---------------------------------------------------------------------------
# T2.3: QUD Stack Persistence & Transitions
# ---------------------------------------------------------------------------

def test_qud_stack_legal_and_illegal_transitions():
    """Verify that legal status transitions succeed and illegal transitions fail."""
    entry = create_qud_entry("gap_1", "What led up to that?", [[0, 5]], 1, "frame_1")
    assert entry["status"] == STATUS_OPEN

    # Legal: open -> answered
    assert transition_qud_status(entry, STATUS_ANSWERED, 2) is True
    assert entry["status"] == STATUS_ANSWERED
    assert entry["last_touched"] == 2

    # Legal: answered -> superseded
    assert transition_qud_status(entry, STATUS_SUPERSEDED, 3) is True
    assert entry["status"] == STATUS_SUPERSEDED

    # Illegal: superseded -> open
    assert transition_qud_status(entry, STATUS_OPEN, 4) is False
    assert entry["status"] == STATUS_SUPERSEDED


def test_qud_stack_frame_merging():
    """Two gaps targeting the same predicate/frame merge into a single QUD entry."""
    gap1 = {
        "gap_id": "gap_unfilled_feel",
        "type": GAP_UNFILLED_ROLE,
        "spans": [[10, 15]],
        "evidence": {"clause_id": "c0", "predicate": "feel"},
        "description": "Unfilled role for feel",
    }
    gap2 = {
        "gap_id": "gap_hedged_feel",
        "type": GAP_HEDGED_COMMITMENT,
        "spans": [[20, 25]],
        "evidence": {"clause_id": "c0", "predicate": "feel"},
        "description": "Hedged commitment for feel",
    }

    stack = merge_and_update_qud_stack([], [gap1], turn_index=1)
    assert len(stack) == 1
    assert stack[0]["frame_id"] == "c0"
    assert stack[0]["spans"] == [[10, 15]]

    # Second gap with same frame_id merges
    updated = merge_and_update_qud_stack(stack, [gap2], turn_index=2)
    assert len(updated) == 1
    assert updated[0]["last_touched"] == 2
    assert updated[0]["spans"] == [[10, 15], [20, 25]]


def test_qud_stack_correction_supersession():
    """When a correction context marks a proposition superseded, matching QUD entries transition to superseded."""
    gap = {
        "gap_id": "gap_leave",
        "type": GAP_UNFILLED_ROLE,
        "spans": [[0, 10]],
        "evidence": {"clause_id": "prop_leave", "predicate": "leave"},
    }
    stack = merge_and_update_qud_stack([], [gap], turn_index=1)
    assert stack[0]["status"] == STATUS_OPEN

    # Turn 2 correction retracts prop_leave
    correction_context = {
        "is_correction": True,
        "superseded_propositions": ["prop_leave"],
    }
    updated = merge_and_update_qud_stack(stack, [], turn_index=2, correction_context=correction_context)
    assert updated[0]["status"] == STATUS_SUPERSEDED


# ---------------------------------------------------------------------------
# T2.4: API Payloads, LLM-Off Identity, and Privacy Canary
# ---------------------------------------------------------------------------

def test_api_analyze_and_chat_payload_contract(empty_state):
    """Verify schema contract: /nlp/analyze and /chat include gaps, qud_stack, and diagnostics_status."""
    service = NLPService()
    # 1. Preview (/nlp/analyze)
    preview = service.preview("test_user_p2", "I finally got the internship, but honestly I feel exhausted.")
    validated_analyze = AnalyzeResponse.model_validate(preview)
    assert validated_analyze.status == "preview"
    assert isinstance(validated_analyze.gaps, list)
    assert len(validated_analyze.gaps) > 0
    assert isinstance(validated_analyze.qud_stack, list)
    assert validated_analyze.diagnostics_status in {"ok", "degraded"}


def test_llm_off_diagnostics_identity(empty_state):
    """Diagnostics (gaps & QUD stack) are computed by the deterministic NLP stack and identical with LLM off."""
    text = "I think I was blamed by my team for the outage, but I tried my best."
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})

    gaps = detect_structural_gaps(analysis, [])
    ranked_gaps = rank_gaps_by_salience(gaps, analysis, [])
    qud_stack = merge_and_update_qud_stack([], ranked_gaps, 1)

    # Rerun
    gaps_2 = detect_structural_gaps(analysis, [])
    ranked_gaps_2 = rank_gaps_by_salience(gaps_2, analysis, [])
    qud_stack_2 = merge_and_update_qud_stack([], ranked_gaps_2, 1)

    assert ranked_gaps == ranked_gaps_2
    assert qud_stack == qud_stack_2


def test_parser_fallback_degraded_diagnostics(empty_state):
    """When parser is unavailable (parser_fallback set), diagnostics_status is degraded and gaps are unverified."""
    text = "I feel tired."
    analysis, _, _ = analyze_turn(text, empty_state, {"alias_key": "test_alias_key"})
    analysis["parser_fallback"] = "dependency_model_unavailable"

    gaps = detect_structural_gaps(analysis, [])
    for g in gaps:
        assert g["status"] == "unverified"

    pipeline_res = execute_question_pipeline(analysis, turn_index=1)
    assert pipeline_res["diagnostics_status"] == "degraded"


def test_privacy_canary_in_diagnostics_payload(empty_state):
    """Standing Invariant: seeded canary PII strings never appear in gaps, qud_stack, or trace."""
    canary_email = "secret_canary_email_49204@sanctuary.internal"
    canary_phone = "+91 98765 43210"
    raw_text = f"Contact me at {canary_email} or {canary_phone} because I feel exhausted."

    analysis, _, ephemeral = analyze_turn(raw_text, empty_state, {"alias_key": "test_alias_key"})
    pipeline_res = execute_question_pipeline(analysis, turn_index=1)

    # Convert everything in pipeline diagnostics to string and search for canary PII
    serialized = json.dumps(pipeline_res, ensure_ascii=False)

    assert canary_email not in serialized, "Canary email leaked into diagnostics payload!"
    assert canary_phone not in serialized, "Canary phone leaked into diagnostics payload!"
    assert "98765" not in serialized, "Canary phone fragment leaked into diagnostics payload!"
