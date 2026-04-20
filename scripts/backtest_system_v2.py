#!/usr/bin/env python
"""Agent Pipeline Backtest V2 — compares LLM agent signals against the V2 quant baseline.

Reuses the exact V2 sizing/risk/cost pipeline from baseline_strategy_v2:
- Vol targeting + half-Kelly + conditional leverage (1-3x)
- SMA30 trend filter (1.5x aligned / 0.5x against)
- 7-day min hold with adaptive early exit
- 3% per-trade stop-loss, 15% portfolio circuit breaker
- Realistic costs (fee, slippage, spread, price impact, funding)

Signals come from agent CSVs produced by `scripts/generate_agent_signals.py`.
The 5-level signal is mapped to +1/+0.5/0/-0.5/-1 and combined with the
confidence label (HIGH/MEDIUM/LOW) as the confidence input to Kelly sizing.

Usage:
    python scripts/backtest_system_v2.py \\
        --signals-dir data/agent_signals \\
        --coins bitcoin ethereum \\
        --start 2024-05-01 --end 2024-08-01
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Reuse V2 baseline components directly — DRY, same pipeline as our best quant baseline.
from scripts.baseline_strategy_v2 import (  # type: ignore
    compute_realized_vol,
    vol_regime_mask,
    build_positions_with_hold,
    apply_trend_filter,
    run_coin_backtest,
)

# Map 5-level signal string to base position weight (before Kelly/vol scaling).
SIGNAL_BASE_POSITION = {
    "BUY": 1.0,
    "OVERWEIGHT": 0.5,
    "HOLD": 0.0,
    "UNDERWEIGHT": -0.5,
    "SELL": -1.0,
}

# Map confidence label to [0, 1] multiplier used as the `confidence` parameter
# into vol_targeted_size (higher confidence -> larger vol-targeted position).
CONFIDENCE_MULTIPLIER = {
    "HIGH": 1.0,
    "MEDIUM": 0.5,
    "LOW": 0.1,
    "UNKNOWN": 0.3,
}


def load_signal_csv(signals_dir: Path, coin: str, start: str, end: str) -> pd.DataFrame:
    """Load the per-coin agent signal CSV produced by generate_agent_signals.py."""
    path = signals_dir / f"{coin}_{start}_{end}.csv"
    if not path.exists():
        # Try to find a compatible CSV (different date range that still covers ours)
        candidates = list(signals_dir.glob(f"{coin}_*.csv"))
        raise FileNotFoundError(
            f"Signals CSV not found: {path}\n"
            f"Available for {coin}: {[c.name for c in candidates]}\n"
            f"Generate with: python scripts/generate_agent_signals.py --coins {coin} "
            f"--start {start} --end {end}"
        )
    df = pd.read_csv(path, parse_dates=["date"])
    for col in ("signal", "confidence"):
        if col not in df.columns:
            raise ValueError(f"{path} missing column '{col}'")
    df = df.sort_values("date").reset_index(drop=True)
    return df


def signals_to_positions_v2(
    signals_df: pd.DataFrame,
    prices: np.ndarray,
    realized_vol: np.ndarray,
    vol_ok: np.ndarray,
    args,
) -> np.ndarray:
    """Convert 5-level agent signals + confidence to continuous positions.

    Produces raw signals (+1/0/-1) and per-bar confidence ∈ [0, 1], then
    feeds both into the V2 baseline's build_positions_with_hold (for min
    hold, adaptive exit) and apply_trend_filter (for SMA30 scaling).
    """
    n = len(signals_df)
    raw_signals = np.zeros(n)
    confidence = np.zeros(n)

    for i in range(n):
        sig_str = str(signals_df["signal"].iloc[i]).strip().upper()
        conf_str = str(signals_df["confidence"].iloc[i]).strip().upper()
        base_pos = SIGNAL_BASE_POSITION.get(sig_str, 0.0)
        conf_mult = CONFIDENCE_MULTIPLIER.get(conf_str, CONFIDENCE_MULTIPLIER["UNKNOWN"])

        # Respect --drop-low-confidence filter
        if conf_str == "LOW" and args.drop_low_confidence:
            raw_signals[i] = 0.0
            confidence[i] = 0.0
            continue

        # raw_signals is a direction in {+1, 0, -1}; magnitude handled by conf*kelly*vol
        if base_pos > 0:
            raw_signals[i] = 1.0
        elif base_pos < 0:
            raw_signals[i] = -1.0
        else:
            raw_signals[i] = 0.0

        # OVERWEIGHT/UNDERWEIGHT halve the confidence to mirror their half-position intent
        if sig_str in ("OVERWEIGHT", "UNDERWEIGHT"):
            conf_mult *= 0.5

        confidence[i] = conf_mult

    positions = build_positions_with_hold(
        raw_signals, vol_ok, confidence, realized_vol, prices,
        target_vol=args.target_vol,
        kelly_fraction=args.kelly_fraction,
        max_leverage=args.max_leverage,
        min_hold=args.min_hold,
        early_exit_loss=args.early_exit_loss,
    )

    if args.trend_sma > 0:
        positions = apply_trend_filter(
            positions, prices, args.trend_sma, args.trend_multiplier,
        )

    return positions


def fetch_prices(coin: str, start: str, end: str) -> pd.DataFrame:
    """Fetch OHLCV via the cached vendor and return date-aligned close prices."""
    from tradingagents.models.model_utils import fetch_ohlcv_for_model
    lookback = (pd.to_datetime(end) - pd.to_datetime(start)).days + 30
    df = fetch_ohlcv_for_model(coin, lookback, trade_date=end)
    if df.empty:
        raise RuntimeError(f"No price data for {coin}")
    df = df.reset_index()
    # fetch_ohlcv_for_model returns a DatetimeIndex (name may be "Date" or
    # "date" depending on caching path); normalise to a "date" column.
    if "date" not in df.columns:
        for cand in ("Date", "index"):
            if cand in df.columns:
                df = df.rename(columns={cand: "date"})
                break
    df["date"] = pd.to_datetime(df["date"])
    mask = (df["date"] >= pd.to_datetime(start)) & (df["date"] <= pd.to_datetime(end))
    return df.loc[mask, ["date", "prices"]].reset_index(drop=True)


def parse_args():
    p = argparse.ArgumentParser(
        description="Agent Pipeline Backtest V2 — same risk/cost pipeline as baseline V2.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--signals-dir", default="data/agent_signals",
                    help="Directory containing per-coin agent signal CSVs.")
    p.add_argument("--coins", nargs="+", required=True)
    p.add_argument("--start", required=True, help="Start date YYYY-MM-DD.")
    p.add_argument("--end", required=True, help="End date YYYY-MM-DD.")
    p.add_argument("--initial-capital", type=float, default=10_000.0)
    p.add_argument("--drop-low-confidence", action="store_true",
                    help="Zero out LOW-confidence signals (default keeps them at 0.1x).")

    # V2 pipeline params — IDENTICAL to baseline defaults for fair comparison
    p.add_argument("--min-hold", type=int, default=7)
    p.add_argument("--target-vol", type=float, default=0.10)
    p.add_argument("--vol-lookback", type=int, default=20)
    p.add_argument("--kelly-fraction", type=float, default=0.5)
    p.add_argument("--max-leverage", type=float, default=3.0)
    p.add_argument("--stop-loss", type=float, default=0.03)
    p.add_argument("--max-portfolio-dd", type=float, default=0.15)
    p.add_argument("--vol-cap-pct", type=float, default=0.95)
    p.add_argument("--early-exit-loss", type=float, default=0.015)
    p.add_argument("--trend-sma", type=int, default=30)
    p.add_argument("--trend-multiplier", type=float, default=1.5)

    # Cost params — IDENTICAL to baseline defaults
    p.add_argument("--fee-rate", type=float, default=0.001)
    p.add_argument("--slippage", type=float, default=0.001)
    p.add_argument("--spread", type=float, default=0.0005)
    p.add_argument("--price-impact", type=float, default=0.001)
    p.add_argument("--funding-rate", type=float, default=0.0001)

    p.add_argument("--output-dir", default="data/agent_backtest_v2")
    return p.parse_args()


def main():
    args = parse_args()
    t0 = time.time()
    signals_dir = Path(args.signals_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cost_kwargs = dict(
        fee_rate=args.fee_rate, slippage=args.slippage, spread=args.spread,
        price_impact=args.price_impact, funding_rate=args.funding_rate,
        stop_loss=args.stop_loss, max_portfolio_dd=args.max_portfolio_dd,
    )

    print(f"\n{'=' * 70}")
    print(f"  Agent Pipeline Backtest V2")
    print(f"{'=' * 70}")
    print(f"  Signals dir : {signals_dir}")
    print(f"  Coins       : {', '.join(args.coins)}")
    print(f"  Period      : {args.start} -> {args.end}")
    print(f"  Min hold    : {args.min_hold} days")
    print(f"  Trend SMA   : {args.trend_sma}d (x{args.trend_multiplier})")
    print(f"  Max lev     : {args.max_leverage}x")
    print(f"  Drop LOW    : {args.drop_low_confidence}")

    all_results = {}
    all_equity = {}
    all_bh = {}

    for coin in args.coins:
        # 1. Load signals
        signals_df = load_signal_csv(signals_dir, coin, args.start, args.end)

        # 2. Load prices and align
        prices_df = fetch_prices(coin, args.start, args.end)
        merged = signals_df.merge(prices_df, on="date", how="inner").sort_values("date")
        if len(merged) < 30:
            print(f"\n  {coin}: skipped (only {len(merged)} aligned rows)")
            continue

        dates = merged["date"].values
        prices = merged["prices"].values.astype(float)

        # 3. Volatility + regime
        realized_vol = compute_realized_vol(prices, args.vol_lookback)
        vol_ok = vol_regime_mask(realized_vol, args.vol_cap_pct)

        # 4. Signals -> positions via full V2 pipeline
        positions = signals_to_positions_v2(merged, prices, realized_vol, vol_ok, args)

        # 5. Backtest (reuses baseline's run_coin_backtest)
        equity, metrics = run_coin_backtest(
            dates, prices, positions,
            initial_capital=args.initial_capital,
            **cost_kwargs,
        )

        bh_ret = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
        all_results[coin] = metrics
        all_equity[coin] = equity
        all_bh[coin] = bh_ret

        sig_counts = merged["signal"].value_counts().to_dict()
        conf_counts = merged["confidence"].value_counts().to_dict()
        print(f"\n  {coin}: n={len(merged)}  sig={sig_counts}  conf={conf_counts}")
        print(f"    return={metrics['total_return']:+.2%}  sharpe={metrics['sharpe_ratio']:.2f}  "
              f"maxDD={metrics['max_drawdown']:.2%}  trades={metrics['n_trades']}  "
              f"B&H={bh_ret:+.2%}")

    # Per-coin table
    print(f"\n{'=' * 70}")
    print(f"  Per-Coin Results")
    print(f"{'=' * 70}")
    header = (f"{'Coin':<12s} {'Return':>10s} {'Ann.Ret':>10s} {'Sharpe':>8s} "
              f"{'MaxDD':>8s} {'WinRate':>8s} {'#Trades':>8s} {'vs B&H':>10s}")
    print(f"  {'-' * len(header)}")
    print(f"  {header}")
    print(f"  {'-' * len(header)}")
    for coin in args.coins:
        if coin not in all_results:
            continue
        m = all_results[coin]
        bh = all_bh[coin]
        print(f"  {coin:<12s} {m['total_return']:>+10.2%} {m['annualized_return']:>+10.2%} "
              f"{m['sharpe_ratio']:>8.2f} {m['max_drawdown']:>8.2%} "
              f"{m['win_rate']:>8.1%} {m['n_trades']:>8d} "
              f"{m['total_return'] - bh:>+10.2%}")

    # Portfolio
    if len(all_equity) > 1:
        min_len = min(len(eq) for eq in all_equity.values())
        port_equity = np.zeros(min_len)
        for eq in all_equity.values():
            port_equity += np.array(eq[:min_len])
        port_equity /= len(all_equity)
        port_return = (port_equity[-1] - args.initial_capital) / args.initial_capital
        port_daily = np.diff(port_equity) / port_equity[:-1]
        port_daily = port_daily[~np.isnan(port_daily)]
        daily_rf = (1 + 0.045) ** (1 / 252) - 1
        std_ex = np.std(port_daily - daily_rf, ddof=1) if len(port_daily) > 1 else 0
        port_sharpe = (float(np.mean(port_daily - daily_rf) / std_ex * np.sqrt(252))
                      if std_ex > 0 else 0)
        rm = np.maximum.accumulate(port_equity)
        port_dd = float(np.max(np.where(rm > 0, (rm - port_equity) / rm, 0)))
        print(f"\n  Portfolio ({len(all_equity)} coins): "
              f"return={port_return:+.2%}  sharpe={port_sharpe:.2f}  maxDD={port_dd:.2%}")

    # Plot + JSON
    plot_path = output_dir / f"agent_v2_equity_{args.start}_{args.end}.png"
    fig, ax = plt.subplots(figsize=(14, 7))
    for coin in args.coins:
        if coin not in all_equity:
            continue
        eq = all_equity[coin]
        dates_pd = pd.to_datetime(
            load_signal_csv(signals_dir, coin, args.start, args.end)["date"].values
        )
        n_plot = min(len(eq) - 1, len(dates_pd))
        ax.plot(dates_pd[:n_plot], eq[1:n_plot + 1], linewidth=1.4,
                label=f"{coin} ({all_results[coin]['total_return']:+.1%})")
    ax.axhline(y=args.initial_capital, color="gray", linestyle="--", alpha=0.5)
    ax.set_title("Agent Pipeline V2 — Equity Curves (per coin)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity (USD)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(str(plot_path), dpi=150)
    plt.close(fig)
    print(f"\n  Equity plot -> {plot_path}")

    json_path = output_dir / f"agent_v2_metrics_{args.start}_{args.end}.json"
    with open(json_path, "w") as f:
        json.dump({
            "coins": list(all_results.keys()),
            "period": {"start": args.start, "end": args.end},
            "metrics": {c: m for c, m in all_results.items()},
            "bh_returns": all_bh,
        }, f, indent=2, default=str)
    print(f"  Metrics JSON -> {json_path}")
    print(f"\n  Total runtime: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
