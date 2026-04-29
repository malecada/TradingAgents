from pathlib import Path
from unittest.mock import patch, MagicMock

import joblib
import numpy as np
import pandas as pd
import pytest


def test_predict_loads_bundle_and_returns_per_coin_per_horizon(tmp_path):
    from tradingagents.execution.live import predict

    # Create a fake bundle dict-keyed-by-horizon (matches retrain output).
    # Use plain `object()` sentinels for boosters — predict_pooled is
    # patched, so the boosters are never invoked. MagicMock can't be
    # joblib-pickled in some environments.
    bundle_h7 = {"booster": object(), "feature_names": ["feature_a"],
                  "horizon": 7, "target_col": "prices_h7", "n_train_rows": 100,
                  "scaler": None, "coin_to_int": {"BTC": 0, "ETH": 1, "BNB": 2}}
    bundle_h14 = {"booster": object(), "feature_names": ["feature_a"],
                   "horizon": 14, "target_col": "prices_h14", "n_train_rows": 100,
                   "scaler": None, "coin_to_int": {"BTC": 0, "ETH": 1, "BNB": 2}}
    ckpt = tmp_path / "lgb_3coin_pit_2026-05-11.pkl"
    joblib.dump({7: bundle_h7, 14: bundle_h14}, ckpt)

    fake_features = pd.DataFrame({
        "coin_id": ["BTC", "ETH", "BNB"],
        "feature_a": [1.0, 2.0, 3.0],
        "ref_price": [60000.0, 3000.0, 400.0],
    })

    with patch.object(predict, "build_features_asof", return_value=fake_features), \
         patch("tradingagents.execution.live.predict.predict_pooled") as mock_predict:
        # Return a known sequence — once per (coin, horizon) call
        mock_predict.side_effect = [70000.0, 72000.0,  # BTC h7, h14
                                     3050.0, 3100.0,    # ETH h7, h14
                                     410.0, 420.0]      # BNB h7, h14
        out = predict.run_predict(
            checkpoint_path=ckpt,
            coins=["BTC", "ETH", "BNB"],
            horizons=[7, 14],
            asof="2026-05-11",
        )

    assert set(out.keys()) == {"BTC", "ETH", "BNB"}
    assert out["BTC"]["pred_h7"] == 70000.0
    assert out["BTC"]["pred_h14"] == 72000.0
    assert out["BTC"]["ref_price"] == 60000.0
    assert out["ETH"]["pred_h7"] == 3050.0
    assert out["BNB"]["pred_h14"] == 420.0


def test_predict_skips_coins_without_features(tmp_path):
    from tradingagents.execution.live import predict

    bundle = {"booster": object(), "feature_names": ["feature_a"],
              "horizon": 7, "target_col": "prices_h7", "n_train_rows": 100,
              "scaler": None, "coin_to_int": {"BTC": 0}}
    ckpt = tmp_path / "lgb_1coin_pit_2026-05-11.pkl"
    joblib.dump({7: bundle}, ckpt)

    # Features only for BTC, asked for BTC + ETH
    fake_features = pd.DataFrame({
        "coin_id": ["BTC"],
        "feature_a": [1.0],
        "ref_price": [60000.0],
    })

    with patch.object(predict, "build_features_asof", return_value=fake_features), \
         patch("tradingagents.execution.live.predict.predict_pooled",
               return_value=70000.0):
        out = predict.run_predict(
            checkpoint_path=ckpt,
            coins=["BTC", "ETH"],
            horizons=[7],
            asof="2026-05-11",
        )

    # ETH gets skipped (no features)
    assert "BTC" in out
    assert "ETH" not in out
    assert out["BTC"]["pred_h7"] == 70000.0
