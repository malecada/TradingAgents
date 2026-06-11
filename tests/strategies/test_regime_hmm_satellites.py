"""All 8 live-universe coins must have a loadable regime HMM checkpoint.

XRP/DOGE/ADA/TRX are pre-trained for the hybrid V5 8-coin live deploy
(Phase 0.1); BTC/ETH/BNB/SOL already shipped with the quant bot.
"""
import pickle
from pathlib import Path

import pytest

LIVE_COINS = ["bitcoin", "ethereum", "binancecoin", "solana",
              "ripple", "dogecoin", "cardano", "tron"]


@pytest.mark.parametrize("coin", LIVE_COINS)
def test_regime_hmm_present_and_loadable(coin):
    path = Path("data/checkpoints") / f"regime_hmm_{coin}.pkl"
    assert path.exists(), f"missing regime HMM for {coin}"
    with open(path, "rb") as f:
        bundle = pickle.load(f)
    # FittedHMM bundle: a fitted GaussianHMM + a 3-state label map
    assert hasattr(bundle, "model")
    assert hasattr(bundle, "state_to_label")
    assert len(set(bundle.state_to_label.values())) >= 2
