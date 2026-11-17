"""Robustness of the trend-multiplier lead: per-year + per-half SR, tm in
{1.5 (baseline), 1.7, 2.0} at production tv=0.10. Also reports max effective
gross leverage per setting (trend filter applies AFTER the 3x cap)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402
from scripts.baseline_v5_mix import (COSTS, DEFAULT_ROUTING, _load_crypto_ohlcv,  # noqa: E402
                                     _load_preds, ANN)
from tradingagents.strategies.v2_sizing import (apply_leverage, apply_trend_filter,  # noqa: E402
    build_positions_with_hold, compute_realized_vol, generate_term_structure_signals,
    vol_regime_mask)

CORE = ["bitcoin", "ethereum", "binancecoin", "solana"]
START, END = "2021-11-07", "2026-04-14"


def coin_series(coin, tm, tv=0.10):
    preds = _load_preds(Path(DEFAULT_ROUTING[coin]), coin)
    preds = preds[(preds["date"] >= START) & (preds["date"] <= END)]
    oh = _load_crypto_ohlcv(coin, END)
    oh["Date"] = pd.to_datetime(oh["Date"]).dt.tz_localize(None).dt.normalize()
    m = preds.merge(oh[["Date", "Close"]], left_on="date", right_on="Date").dropna(subset=["Close"]).reset_index(drop=True)
    sig, conf = generate_term_structure_signals(m, [7, 14], 0.05, asymmetric=True)
    px = m["Close"].astype(float).values
    rv = compute_realized_vol(px, lookback=20)
    mask = vol_regime_mask(rv, percentile_cap=0.95)
    pos = build_positions_with_hold(signals=sig, vol_ok=mask, confidence=conf,
        realized_vol=rv, prices=px, target_vol=tv, kelly_fraction=0.5,
        max_leverage=3.0, min_hold=7, early_exit_loss=0.015)
    pos = apply_trend_filter(pos, px, sma_period=30, multiplier=tm)
    max_gross = float(np.abs(pos).max())
    eq, _ = run_coin_backtest(dates=m["date"].values, prices=m["Close"].values,
        positions=pos, initial_capital=10_000.0, **dict(COSTS))
    eq = np.asarray(eq, float)
    return pd.Series(eq[1:] / eq[:-1] - 1.0, index=pd.to_datetime(m["date"].values[1:])), max_gross


def sr(r):
    sd = r.std()
    return float(r.mean() / sd * ANN) if sd > 0 else 0.0


def main():
    print("per-year portfolio SR (EW 4-coin), tv=0.10\n")
    ports = {}
    grosses = {}
    for tm in [1.5, 1.7, 2.0]:
        series = []
        gmax = 0.0
        for c in CORE:
            s, g = coin_series(c, tm)
            series.append(s)
            gmax = max(gmax, g)
        port = pd.concat(series, axis=1).mean(axis=1).dropna()
        ports[tm] = port
        grosses[tm] = gmax

    years = sorted({d.year for d in ports[1.5].index})
    hdr = "year   " + "".join(f"tm={tm:<6}" for tm in [1.5, 1.7, 2.0])
    print(hdr)
    for y in years:
        row = f"{y}   "
        for tm in [1.5, 1.7, 2.0]:
            yr = ports[tm][[d.year == y for d in ports[tm].index]]
            row += f"{sr(yr):<8.2f}"
        print(row)
    print("-" * len(hdr))
    # halves
    mid = ports[1.5].index[len(ports[1.5]) // 2]
    for lbl, msk in [("H1", lambda idx: idx < mid), ("H2", lambda idx: idx >= mid)]:
        row = f"{lbl}     "
        for tm in [1.5, 1.7, 2.0]:
            seg = ports[tm][[msk(d) for d in ports[tm].index]]
            row += f"{sr(seg):<8.2f}"
        print(row)
    print("-" * len(hdr))
    row = "FULL   "
    for tm in [1.5, 1.7, 2.0]:
        row += f"{sr(ports[tm]):<8.2f}"
    print(row)
    print("\nmax effective gross leverage (per-coin, abs position):")
    for tm in [1.5, 1.7, 2.0]:
        print(f"  tm={tm}: {grosses[tm]:.2f}x")


if __name__ == "__main__":
    main()
