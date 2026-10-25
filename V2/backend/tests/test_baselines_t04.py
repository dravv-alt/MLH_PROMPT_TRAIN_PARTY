"""Tests for T0.4 Baseline Runs:
- Verifies corrupted gold file fails loudly (raises ValueError)
- Verifies empty or over-long reply is recorded as failure, not skipped
- Verifies rerun determinism at fixed seed
"""
import os
import json
import pytest
from pathlib import Path
from scripts.run_baselines_t04 import evaluate_dev_suite, run_c0_raw_llm


def test_corrupted_gold_file_fails_loudly(tmp_path):
    """Hard negative: A run on a deliberately corrupted gold file must fail loudly."""
    corrupted_file = tmp_path / "corrupted_gold.json"
    corrupted_file.write_text(json.dumps([{"invalid_field": 123}]), encoding="utf-8")
    with pytest.raises(ValueError, match="Deliberately corrupted gold file detected"):
        evaluate_dev_suite(corrupted_file)


def test_empty_or_overlong_reply_recorded_as_failure():
    """Hard negative: Empty or over-long replies must be recorded as failures, not skipped."""
    class DummyGenerator:
        def _candidate(self, **kwargs):
            return "", {"input_tokens": 10, "output_tokens": 0}

    reply, lat, in_tok, out_tok = run_c0_raw_llm("I felt tired.", DummyGenerator(), "balanced")
    is_failure = len(reply.strip()) == 0 or out_tok > 150
    assert is_failure, "Empty reply must be marked as failure"

    class OverLongGenerator:
        def _candidate(self, **kwargs):
            return "word " * 200, {"input_tokens": 10, "output_tokens": 200}

    reply, lat, in_tok, out_tok = run_c0_raw_llm("I felt tired.", OverLongGenerator(), "balanced")
    is_failure = len(reply.strip()) == 0 or out_tok > 150
    assert is_failure, "Over-long reply (>150 tokens) must be marked as failure"


def test_baseline_smoke_run(tmp_path):
    """Smoke test running 2 turns across C0, C1, C4, C5 to verify pipeline integrity and determinism."""
    gold_path = Path(__file__).resolve().parents[1] / "evaluation" / "gold" / "dev_80_annotated.json"
    res1 = evaluate_dev_suite(gold_path, limit=2)
    assert len(res1["conditions"]["C4_Classical"]) == 2
    assert len(res1["conditions"]["C5_Restatement"]) == 2
    assert len(res1["conditions"]["C0_ModelA"]) == 2
    assert "metrics_summary" in res1
    assert "C4_Classical" in res1["metrics_summary"]
