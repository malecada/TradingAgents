from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest


def test_retrain_writes_checkpoint_and_returns_artifact(tmp_path):
    from tradingagents.execution.live import retrain

    fake_dataset = pd.DataFrame({
        "coin": ["BTC", "ETH", "BNB"] * 100,
        "ref_price": [60000, 3000, 400] * 100,
        "feature_a": [1.0] * 300,
        "y_h7": [60100, 3010, 401] * 100,
        "y_h14": [60200, 3020, 402] * 100,
    })
    fake_metrics = {"dir_acc_h7": 0.65, "dir_acc_h14": 0.70}

    with patch.object(retrain, "build_pooled_dataset",
                      return_value=fake_dataset), \
         patch.object(retrain, "model_run_pooled",
                      return_value=({"model": MagicMock()}, fake_metrics)):
        artifact = retrain.run_retrain(
            coins=["BTC", "ETH", "BNB"],
            horizons=[7, 14],
            asof="2026-05-11",
            checkpoint_dir=tmp_path,
        )
    assert artifact.model_path.exists()
    assert artifact.train_dir_acc_h7 == 0.65
    assert artifact.train_dir_acc_h14 == 0.70
    assert artifact.train_rows == 300
    assert len(artifact.sha256) == 64


def test_retrain_falls_back_on_failure(tmp_path):
    from tradingagents.execution.live import retrain

    # Pre-seed a previous checkpoint
    prev = tmp_path / "lgb_3coin_pit_2026-05-10.pkl"
    prev.write_bytes(b"fake-prev-checkpoint")

    with patch.object(retrain, "build_pooled_dataset",
                      side_effect=RuntimeError("CoinMetrics down")):
        artifact = retrain.run_retrain_with_fallback(
            coins=["BTC", "ETH", "BNB"],
            horizons=[7, 14],
            asof="2026-05-11",
            checkpoint_dir=tmp_path,
        )
    # Falls back to most recent existing checkpoint
    assert artifact.model_path == prev
    assert artifact.is_fallback is True
