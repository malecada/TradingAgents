#!/usr/bin/env python
"""Backtest the hybrid quant+LLM ModulatedPosition stream.

Reads CSVs produced by ``generate_hybrid_signals.py``, joins with
OHLCV (CoinGecko/Binance cache), and runs the V2 cost+risk pipeline
(``run_coin_backtest`` from ``baseline_strategy_v2``). The hybrid
``position`` field already encodes direction × magnitude × LLM
modulation, so we feed it directly without re-applying Kelly /
SMA30 / vol regime — those are baked into Layer 1.

Compares against the pure-quant V2 baseline equity curve over the
same window.

Usage:
    python scripts/backtest_hybrid.py \\
        --signals-dir data/hybrid_signals_p1 \\
        --coins bitcoin ethereum \\
        --start 2026-01-16 --end 2026-04-15 \\
        --baseline-pred-dir data/multi_2coins_v2
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_strategy_v2 import run_coin_backtest  # type: ignore
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv

# V2 cost / risk defaults — same numbers as baseline_strategy_v2
COSTS = dict(
    fee_rate=0.0004,
    slippage=0.0005,
    spread=0.0001,
    price_impact=0.00005,
    funding_rate=0.0001 / 8,  # daily
    stop_loss=0.03,
    max_portfolio_dd=0.15,
)


def _load_prices(coin: str, end_date: str) -> pd.DataFrame:
    df = _load_crypto_ohlcv(coin, end_date)
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    return df.sort_values("Date").reset_index(drop=True)


def _to_signed_position(row) -> float:
    pos = row["position"]
    if pos is None or pd.isna(pos):
        return 0.0
    direction = row.get("quant_direction", "flat")
    sign = 1 if direction == "long" else (-1 if direction == "short" else 0)
    return float(sign * abs(pos))


def _backtest_coin(coin: str, signals_csv: Path, start: str, end: str) -> dict:
    sig = pd.read_csv(signals_csv, parse_dates=["date"])
    sig["date"] = sig["date"].dt.tz_localize(None).dt.normalize()
    sig = sig[(sig["date"] >= start) & (sig["date"] <= end)]
    if sig.empty:
        return {"coin": coin, "error": "no signals in range"}
    sig = sig.dropna(subset=["position"]).copy()
    sig["signed_pos"] = sig.apply(_to_signed_position, axis=1)

    prices = _load_prices(coin, end)
    merged = sig.merge(prices[["Date", "Close"]], left_on="date", right_on="Date", how="left")
    merged = merged.dropna(subset=["Close"]).reset_index(drop=True)

    dates = merged["date"].values
    px = merged["Close"].astype(float).values
    pos = merged["signed_pos"].astype(float).values

    equity, metrics = run_coin_backtest(
        dates=dates,
        prices=px,
        positions=pos,
        initial_capital=10_000.0,
        **COSTS,
    )
    eq_arr = np.asarray(equity, dtype=float)
    daily_returns = np.zeros_like(eq_arr)
    if len(eq_arr) > 1:
        daily_returns[1:] = eq_arr[1:] / eq_arr[:-1] - 1.0
    return {
        "coin": coin,
        "n_bars": int(len(merged)),
        "equity": equity,
        "dates": dates,
        "metrics": metrics,
        "positions": pos,
        "daily_returns": daily_returns,
    }


def _baseline_coin(coin: str, baseline_pred_dir: Path, start: str, end: str) -> dict:
    """Pure V2 quant baseline using the same LGB CSVs as Layer 1."""
    from tradingagents.strategies.v2_sizing import (
        apply_trend_filter, build_positions_with_hold, compute_realized_vol,
        generate_term_structure_signals, vol_regime_mask,
    )
    p7 = baseline_pred_dir / "preds_lgb_h7.csv"
    p14 = baseline_pred_dir / "preds_lgb_h14.csv"
    df7 = pd.read_csv(p7, parse_dates=["date"])
    df14 = pd.read_csv(p14, parse_dates=["date"])
    df7["date"] = df7["date"].dt.tz_localize(None).dt.normalize()
    df14["date"] = df14["date"].dt.tz_localize(None).dt.normalize()
    df7 = df7[df7["coin_id"] == coin].rename(columns={"prediction": "pred_h7"})
    df14 = df14[df14["coin_id"] == coin].rename(columns={"prediction": "pred_h14"})
    m = df7.merge(df14[["date", "pred_h14"]], on="date")
    m = m[(m["date"] >= start) & (m["date"] <= end)].sort_values("date").reset_index(drop=True)
    if m.empty:
        return {"coin": coin, "error": "no baseline preds"}

    sig, conf = generate_term_structure_signals(m, [7, 14], 0.05, asymmetric=True)
    prices = _load_prices(coin, end)
    merged = m.merge(prices[["Date", "Close"]], left_on="date", right_on="Date", how="left")
    px = merged["Close"].astype(float).values

    rv = compute_realized_vol(px, lookback=20)
    mask = vol_regime_mask(rv, percentile_cap=0.95)
    pos = build_positions_with_hold(
        signals=sig,
        vol_ok=mask,
        confidence=conf,
        realized_vol=rv,
        prices=px,
        target_vol=0.10,
        kelly_fraction=0.5,
        max_leverage=3.0,
        min_hold=7,
        early_exit_loss=0.015,
    )
    pos = apply_trend_filter(pos, px, sma_period=30, multiplier=1.5)

    equity, metrics = run_coin_backtest(
        dates=merged["date"].values, prices=px, positions=pos,
        initial_capital=10_000.0, **COSTS,
    )
    eq_arr = np.asarray(equity, dtype=float)
    daily_returns = np.zeros_like(eq_arr)
    if len(eq_arr) > 1:
        daily_returns[1:] = eq_arr[1:] / eq_arr[:-1] - 1.0
    return {"coin": coin, "n_bars": int(len(m)), "equity": equity,
            "dates": merged["date"].values, "metrics": metrics, "positions": pos,
            "daily_returns": daily_returns}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--signals-dir", required=True)
    p.add_argument("--coins", nargs="+", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--baseline-pred-dir", default="data/multi_2coins_v2")
    p.add_argument("--output-dir", default=None)
    args = p.parse_args()

    out_dir = Path(args.output_dir or f"{args.signals_dir}/backtest")
    out_dir.mkdir(parents=True, exist_ok=True)

    hybrid_results = {}
    baseline_results = {}
    for coin in args.coins:
        sig_csv = Path(args.signals_dir) / f"{coin}_{args.start}_{args.end}.csv"
        if not sig_csv.exists():
            print(f"[skip] {coin}: no hybrid signals at {sig_csv}")
            continue
        hybrid_results[coin] = _backtest_coin(coin, sig_csv, args.start, args.end)
        baseline_results[coin] = _baseline_coin(coin, Path(args.baseline_pred_dir), args.start, args.end)

    # Summary
    print(f"\n{'=' * 80}")
    print(f"  Hybrid vs Pure-Quant V2 Baseline ({args.start} -> {args.end})")
    print(f"{'=' * 80}")
    summary = {}
    for coin in hybrid_results:
        h = hybrid_results[coin]
        b = baseline_results.get(coin) or {}
        if "error" in h:
            print(f"  {coin}: hybrid error: {h['error']}")
            continue
        hm = h.get("metrics", {})
        bm = b.get("metrics", {})
        print(f"\n  {coin} ({h['n_bars']} bars)")
        print(f"    {'metric':<25} {'hybrid':>12} {'baseline':>12}  delta")
        for k in ("sharpe_ratio", "total_return", "ann_return", "max_drawdown", "win_rate"):
            hv = hm.get(k, float("nan"))
            bv = bm.get(k, float("nan"))
            d = hv - bv if not (np.isnan(hv) or np.isnan(bv)) else float("nan")
            print(f"    {k:<25} {hv:>12.4f} {bv:>12.4f}  {d:+.4f}")
        summary[coin] = {"hybrid": hm, "baseline": bm}

    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    # Per-bar daily returns CSV for downstream bootstrap / DSR / ablations
    rows = []
    for coin in hybrid_results:
        h = hybrid_results[coin]
        b = baseline_results.get(coin) or {}
        if "error" in h:
            continue
        n = min(len(h["dates"]), len(h["daily_returns"]))
        b_ret = b.get("daily_returns", np.zeros(n))
        for i in range(n):
            rows.append({
                "date": pd.Timestamp(h["dates"][i]).strftime("%Y-%m-%d"),
                "coin": coin,
                "hybrid_ret": float(h["daily_returns"][i]),
                "baseline_ret": float(b_ret[i] if i < len(b_ret) else 0.0),
                "hybrid_pos": float(h["positions"][i]) if i < len(h["positions"]) else 0.0,
            })
    pd.DataFrame(rows).to_csv(out_dir / "daily_returns.csv", index=False)

    # Plot equity curves
    fig, ax = plt.subplots(figsize=(12, 6))
    for coin in hybrid_results:
        h = hybrid_results[coin]
        b = baseline_results.get(coin) or {}
        if "error" in h:
            continue
        ax.plot(h["dates"], h["equity"], label=f"{coin} hybrid", linewidth=1.6)
        if "equity" in b:
            ax.plot(b["dates"], b["equity"], label=f"{coin} V2 baseline",
                    linestyle="--", alpha=0.7)
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity")
    ax.set_title(f"Hybrid quant+LLM vs V2 baseline ({args.start} → {args.end})")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    plot_path = out_dir / "hybrid_vs_baseline_equity.png"
    fig.savefig(plot_path, dpi=130, bbox_inches="tight")
    print(f"\n  Plot:    {plot_path}")
    print(f"  Summary: {out_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
