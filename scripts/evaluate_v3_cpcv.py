#!/usr/bin/env python
"""V3 CPCV evaluation — runs Combinatorial Purged CV on the V3 backtest.

For each coin:
  1. Generate CPCV splits over the date range
  2. Run V3 backtest on each test fold
  3. Collect per-split Sharpe ratios
  4. Compute Deflated Sharpe Ratio adjusting for n_trials

Outputs:
  data/v3_cpcv/{coin}/sharpe_distribution.parquet
  data/v3_cpcv/{coin}/summary.json

NOTE (Phase-7 simplification): models are NOT retrained per fold. The
pre-trained `data/checkpoints/v3_models_{coin}.pkl` is reused across all
splits. Full per-fold retraining is performed in Task 38 (real eval).

Usage:
    python scripts/evaluate_v3_cpcv.py \\
        --coins bitcoin ethereum \\
        --start 2024-05-01 --end 2026-04-15
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402
from tradingagents.strategies.v3.backtest.cpcv import cpcv_splits  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio,
    expected_max_sharpe,
    variance_of_sr,
)
from tradingagents.strategies.v3.backtest.runner_v3 import run_v3_backtest  # noqa: E402
from tradingagents.strategies.v3.config import V3Config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _load_optional_parquet(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()


def _load_required_pickle(path: Path):
    with open(path, "rb") as f:
        return pickle.load(f)


def _load_ohlcv_for_coin(coin: str, days: int = 2500) -> pd.DataFrame:
    # _load_crypto_ohlcv takes coingecko_id + curr_date (not coin + days)
    # Use end of eval window as curr_date so we get all needed history
    df = _load_crypto_ohlcv(coingecko_id=coin, curr_date="2026-04-15")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    return df


def evaluate_coin_cpcv(
    coin: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    cfg: V3Config,
    microstructure_dir: Path,
    derivatives_dir: Path,
    regime_dir: Path,
    models_dir: Path,
    n_groups: int = 8,
    test_groups: int = 2,
    embargo: int = 14,
    n_trials_for_dsr: int = 12,
) -> dict:
    """Run CPCV evaluation for one coin. Returns dict of per-split metrics + DSR."""
    ohlcv = _load_ohlcv_for_coin(coin)
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    prices = ohlcv["Close"]
    returns = prices.pct_change().fillna(0.0)

    # Slice to evaluation window
    mask = (prices.index >= start) & (prices.index <= end)
    bars = prices.index[mask]
    if len(bars) < n_groups * 2 * embargo:
        raise ValueError(f"Too few bars ({len(bars)}) for CPCV with n_groups={n_groups}")

    micro = _load_optional_parquet(microstructure_dir / f"{coin}.parquet")
    deriv = _load_optional_parquet(derivatives_dir / f"{coin}.parquet")
    regime_bundle = _load_required_pickle(regime_dir / f"regime_hmm_v3_{coin}.pkl")
    mh_bundle = _load_required_pickle(models_dir / f"v3_models_{coin}.pkl")

    splits = list(
        cpcv_splits(
            n_samples=len(bars),
            n_groups=n_groups,
            test_groups=test_groups,
            embargo=embargo,
        )
    )
    logger.info("[%s] %d CPCV splits to evaluate", coin, len(splits))

    per_split_records = []
    for split_idx, split in enumerate(splits):
        if len(split.test_idx) == 0:
            continue
        test_bars = bars[split.test_idx]
        if len(test_bars) < 5:
            continue
        test_start = test_bars[0]
        test_end = test_bars[-1]
        try:
            result = run_v3_backtest(
                coin=coin,
                prices=prices,
                returns=returns,
                microstructure_features=micro,
                derivatives_features=deriv,
                regime_bundle=regime_bundle,
                multi_horizon_bundle=mh_bundle,
                config=cfg,
                start=test_start,
                end=test_end,
                ticker=coin.upper(),
            )
            per_split_records.append({
                "split_idx": split_idx,
                "test_start": test_start,
                "test_end": test_end,
                "n_bars": len(test_bars),
                "sharpe_ratio": float(result.metrics.get("sharpe_ratio", 0.0)),
                "total_return": float(result.metrics.get("total_return", 0.0)),
                "max_drawdown": float(result.metrics.get("max_drawdown", 0.0)),
            })
        except Exception:
            logger.exception("[%s] split %d failed", coin, split_idx)
            continue

    if not per_split_records:
        raise RuntimeError(f"No splits completed for {coin}")

    df = pd.DataFrame(per_split_records)
    sharpes = df["sharpe_ratio"].values

    sr_obs = float(np.mean(sharpes))
    var_sr = variance_of_sr(sharpes)
    sr_exp = expected_max_sharpe(n_trials=n_trials_for_dsr, var_sr=max(var_sr, 1e-9))
    dsr = deflated_sharpe_ratio(
        sr_observed=sr_obs,
        sr_expected_under_null=sr_exp,
        se_sr=float(np.sqrt(max(var_sr, 1e-9))),
    )

    return {
        "splits_df": df,
        "summary": {
            "coin": coin,
            "n_splits": len(per_split_records),
            "sharpe_mean": sr_obs,
            "sharpe_median": float(np.median(sharpes)),
            "sharpe_std": float(np.std(sharpes, ddof=1)),
            "sharpe_min": float(np.min(sharpes)),
            "sharpe_max": float(np.max(sharpes)),
            "var_sr": float(var_sr),
            "sr_expected_under_null": float(sr_exp),
            "dsr": float(dsr),
            "n_trials_for_dsr": n_trials_for_dsr,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--coins", nargs="+", default=["bitcoin", "ethereum"])
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--microstructure-dir", default="data/microstructure")
    parser.add_argument("--derivatives-dir", default="data/derivatives")
    parser.add_argument("--regime-dir", default="data/checkpoints")
    parser.add_argument("--models-dir", default="data/checkpoints")
    parser.add_argument("--out-dir", default="data/v3_cpcv")
    parser.add_argument("--n-groups", type=int, default=8)
    parser.add_argument("--test-groups", type=int, default=2)
    parser.add_argument("--embargo", type=int, default=14)
    parser.add_argument("--n-trials-dsr", type=int, default=12)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = V3Config()
    start_ts = pd.Timestamp(args.start, tz="UTC")
    end_ts = pd.Timestamp(args.end, tz="UTC")

    for coin in args.coins:
        try:
            result = evaluate_coin_cpcv(
                coin=coin,
                start=start_ts,
                end=end_ts,
                cfg=cfg,
                microstructure_dir=Path(args.microstructure_dir),
                derivatives_dir=Path(args.derivatives_dir),
                regime_dir=Path(args.regime_dir),
                models_dir=Path(args.models_dir),
                n_groups=args.n_groups,
                test_groups=args.test_groups,
                embargo=args.embargo,
                n_trials_for_dsr=args.n_trials_dsr,
            )
        except Exception:
            logger.exception("Failed coin %s", coin)
            continue

        coin_dir = out_dir / coin
        coin_dir.mkdir(parents=True, exist_ok=True)
        result["splits_df"].to_parquet(coin_dir / "sharpe_distribution.parquet")
        with open(coin_dir / "summary.json", "w") as f:
            json.dump(result["summary"], f, indent=2, default=str)

        s = result["summary"]
        logger.info(
            "[%s] n_splits=%d sharpe_mean=%.2f median=%.2f std=%.2f DSR=%.3f",
            coin, s["n_splits"], s["sharpe_mean"], s["sharpe_median"],
            s["sharpe_std"], s["dsr"],
        )


if __name__ == "__main__":
    main()
