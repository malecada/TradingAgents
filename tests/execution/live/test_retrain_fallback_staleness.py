"""Fallback-checkpoint staleness must be surfaced, not silent.

Audit 2026-07-07 R4: run_retrain_with_fallback falls back to the newest
existing composite on ANY retrain failure with only a warning — a persistent
data outage would freeze the model indefinitely and invisibly.
"""

from __future__ import annotations

import logging

import joblib
import pytest

from tradingagents.execution.live import retrain

ROUTING = {"bitcoin": {"pool": ["bitcoin"], "feature_set": "78f"}}


def _plant_checkpoint(ckpt_dir, asof: str) -> None:
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"bitcoin_78f": {7: {}}}, ckpt_dir / f"lgb_v5_mix_{asof}.pkl")


def _boom(*a, **k):
    raise RuntimeError("data outage")


def test_stale_fallback_logs_error(tmp_path, monkeypatch, caplog):
    _plant_checkpoint(tmp_path, "2026-06-09")  # 10 days before asof
    monkeypatch.setattr(retrain, "run_retrain", _boom)
    with caplog.at_level(logging.WARNING):
        art = retrain.run_retrain_with_fallback(
            routing=ROUTING, horizons=[7], asof="2026-06-19",
            checkpoint_dir=tmp_path,
        )
    assert art.path.name == "lgb_v5_mix_2026-06-09.pkl"
    stale_records = [r for r in caplog.records
                     if r.levelno >= logging.ERROR and "stale" in r.message.lower()]
    assert stale_records, "10-day-old fallback must log an ERROR mentioning staleness"
    assert "10" in stale_records[0].message


def test_fresh_fallback_stays_warning(tmp_path, monkeypatch, caplog):
    _plant_checkpoint(tmp_path, "2026-06-18")  # 1 day before asof
    monkeypatch.setattr(retrain, "run_retrain", _boom)
    with caplog.at_level(logging.WARNING):
        retrain.run_retrain_with_fallback(
            routing=ROUTING, horizons=[7], asof="2026-06-19",
            checkpoint_dir=tmp_path,
        )
    assert not [r for r in caplog.records
                if r.levelno >= logging.ERROR and "stale" in r.message.lower()]
