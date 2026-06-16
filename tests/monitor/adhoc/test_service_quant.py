from __future__ import annotations

import types

import pandas as pd
import pytest

from tradingagents.monitor.adhoc import service


class _FakeSignal:
    def model_dump(self):
        return {"coin": "bitcoin", "direction": "long", "magnitude": 0.42,
                "regime": "bull", "regime_confidence": 0.7, "hurst": 0.55,
                "deterministic_signals": {"lgb_h7": 0.01}, "as_of_date": "2026-05-01"}
    direction = "long"
    magnitude = 0.42
    regime = "bull"


@pytest.fixture
def patched(tmp_path, monkeypatch):
    # fake live config
    cfg = types.SimpleNamespace(
        coin_universe=["bitcoin", "ethereum"],
        routing={"bitcoin": {"feature_set": "78f", "pool": ["bitcoin", "ethereum"]}},
        horizons=[7, 14], data_root=str(tmp_path))
    monkeypatch.setattr("tradingagents.execution.live.config.load_config", lambda: cfg)
    # fake checkpoint
    ckpt_dir = tmp_path / "checkpoints"
    ckpt_dir.mkdir()
    (ckpt_dir / "lgb_v5_mix_2026-05-01.pkl").write_text("x")
    # fake run_predict
    df = pd.DataFrame([
        {"coin": "bitcoin", "horizon": 7, "prediction": 0.011, "ref_price": 60000.0,
         "bundle_route": "78f"},
        {"coin": "bitcoin", "horizon": 14, "prediction": 0.020, "ref_price": 60000.0,
         "bundle_route": "78f"},
    ])
    monkeypatch.setattr("tradingagents.execution.live.predict.run_predict",
                        lambda **kw: df)
    # capture staging + return a dir; bypass real CSV write
    staged_dir = tmp_path / "staged"
    staged_dir.mkdir()
    monkeypatch.setattr(
        "tradingagents.execution.live.hybrid_compose.stage_quant_preds",
        lambda rows, *, date, out_dir: staged_dir)
    monkeypatch.setattr("tradingagents.strategies.quant_engine.get_quant_signal",
                        lambda coin, date, base_dir=None: _FakeSignal())
    return cfg


def test_run_quant_yields_signal_and_final(patched):
    outs = list(service.run_quant(coin="bitcoin", date="2026-05-01", run_id="r1"))
    keys = [k for (k, _l, _kind, _c) in outs]
    assert "quant_signal" in keys
    assert "final" in keys
    final = [c for (k, _l, _kind, c) in outs if k == "final"][0]
    assert final["direction"] == "long"
    assert final["magnitude"] == 0.42


def test_run_quant_errors_on_empty_preds(patched, monkeypatch):
    monkeypatch.setattr("tradingagents.execution.live.predict.run_predict",
                        lambda **kw: __import__("pandas").DataFrame())
    with pytest.raises(RuntimeError, match="no prediction"):
        list(service.run_quant(coin="bitcoin", date="2026-05-01", run_id="r1"))


def test_latest_checkpoint_picks_newest_v5_mix(tmp_path):
    # matches the live retrain artifact name lgb_v5_mix_<asof>.pkl
    ck = tmp_path / "checkpoints"
    ck.mkdir()
    (ck / "lgb_v5_mix_2026-05-01.pkl").write_text("x")
    (ck / "lgb_v5_mix_2026-06-15.pkl").write_text("x")
    (ck / "lgb_3coin_pit_2026-06-20.pkl").write_text("x")  # different model, ignored
    got = service._latest_checkpoint(str(tmp_path))
    assert got.name == "lgb_v5_mix_2026-06-15.pkl"


def test_latest_checkpoint_missing_raises(tmp_path):
    (tmp_path / "checkpoints").mkdir()
    with pytest.raises(FileNotFoundError, match="lgb_v5_mix"):
        service._latest_checkpoint(str(tmp_path))
