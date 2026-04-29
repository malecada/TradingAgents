from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest


def _fake_transformed_df():
    """Pretend output of build_pooled_dataset + _transform_pooled — has prices_h7/h14."""
    n = 300
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "coin_id": (["BTC"] * 100) + (["ETH"] * 100) + (["BNB"] * 100),
        "ref_price": list(rng.uniform(50, 70000, n)),
        "feature_a": rng.normal(0, 1, n),
        "feature_b": rng.normal(0, 1, n),
        "prices_h7": list(rng.uniform(50, 70000, n)),
        "prices_h14": list(rng.uniform(50, 70000, n)),
    })


def test_retrain_writes_per_horizon_bundles(tmp_path):
    from tradingagents.execution.live import retrain

    fake_df = _fake_transformed_df()

    with patch.object(retrain, "build_pooled_dataset", return_value=fake_df), \
         patch.object(retrain, "_transform_pooled", return_value=fake_df), \
         patch.object(retrain, "fit_pooled_full") as mock_fit:
        # Return distinct bundles per horizon so we can verify both were called
        mock_fit.side_effect = lambda df, horizon, **kw: {
            "booster": object(),
            "feature_names": ["feature_a", "feature_b"],
            "horizon": horizon,
            "target_col": f"prices_h{horizon}",
            "n_train_rows": 300,
        }
        artifact = retrain.run_retrain(
            coins=["BTC", "ETH", "BNB"],
            horizons=[7, 14],
            asof="2026-05-11",
            checkpoint_dir=tmp_path,
        )
    assert artifact.model_path.exists()
    assert artifact.train_rows == 300
    assert len(artifact.sha256) == 64
    # Both horizons fit
    assert mock_fit.call_count == 2

    # Loaded checkpoint is a dict keyed by horizon, each value a bundle
    import joblib
    loaded = joblib.load(artifact.model_path)
    assert set(loaded.keys()) == {7, 14}
    assert loaded[7]["target_col"] == "prices_h7"
    assert loaded[14]["target_col"] == "prices_h14"


def test_retrain_falls_back_on_failure(tmp_path):
    from tradingagents.execution.live import retrain

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
    assert artifact.model_path == prev
    assert artifact.is_fallback is True
