#!/usr/bin/env python
"""V5 MIX per-coin Kelly fraction sweep.

Tests whether each coin's optimal Kelly fraction differs materially from the
uniform 0.25 (live) / 0.50 (backtest canonical) currently used in §22 of
THESIS_FINDINGS.md.

Protocol:
  - Reuse existing walk-forward prediction CSVs (no model retraining, no LLM calls).
  - For each (coin, kelly_fraction) pair on the §20 4-coin V5 MIX routing,
    run the V2 sizing pipeline and record Sharpe + return + max DD.
  - Build a per-coin-optimal portfolio (each coin at its argmax-SR Kelly) and
    compare to the uniform-Kelly portfolios.

Outputs:
  data/v5_kelly_sweep/per_coin.csv           — long-format (coin × kelly × metrics)
  data/v5_kelly_sweep/portfolio_uniform.csv  — per-uniform-kelly portfolio metrics
  data/v5_kelly_sweep/summary.json           — full structured summary
  stdout                                      — formatted tables

Usage:
    python scripts/v5_kelly_sweep.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402
from scripts.baseline_v5_mix import (  # noqa: E402
    ANN, COSTS, DEFAULT_ROUTING, _load_preds, _metrics, _v2_positions,
)
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402

START, END = "2021-11-07", "2026-04-15"

KELLY_GRID = [0.10, 0.20, 0.25, 0.35, 0.50, 0.75, 1.00]


def _coin_merged(coin: str) -> pd.DataFrame:
    preds = _load_preds(PROJECT_ROOT / DEFAULT_ROUTING[coin], coin)
    preds = preds[(preds["date"] >= START) & (preds["date"] <= END)]
    ohlcv = _load_crypto_ohlcv(coin, END)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    merged = preds.merge(ohlcv[["Date", "Close"]], left_on="date", right_on="Date")
    merged = merged.dropna(subset=["Close"]).reset_index(drop=True)
    merged["ref_price"] = merged["Close"]
    return merged


def _coin_returns(merged: pd.DataFrame, kelly_fraction: float) -> pd.Series:
    pos = _v2_positions(merged, kelly_fraction=kelly_fraction)
    equity, _ = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=pos, initial_capital=10_000.0, **COSTS,
    )
    eq = np.asarray(equity, dtype=float)
    return pd.Series(
        eq[1:] / eq[:-1] - 1.0,
        index=pd.to_datetime(merged["date"].values[1:]),
        name="ret",
    )


def main() -> None:
    out_dir = PROJECT_ROOT / "data" / "v5_kelly_sweep"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 84}")
    print(f"  V5 MIX — Per-coin Kelly fraction sweep")
    print(f"  window: {START} → {END}    grid: {KELLY_GRID}")
    print(f"{'=' * 84}\n")

    # Load merged frames once per coin (expensive part of pipeline)
    merged = {c: _coin_merged(c) for c in DEFAULT_ROUTING}

    # ── Per-coin × per-kelly sweep ──
    rows: list[dict] = []
    coin_kelly_rets: dict[tuple[str, float], pd.Series] = {}
    for coin in DEFAULT_ROUTING:
        feat = "193f extended" if "pit" in DEFAULT_ROUTING[coin] else "78f canonical"
        print(f"  {coin}  [{feat}]")
        for k in KELLY_GRID:
            r = _coin_returns(merged[coin], kelly_fraction=k)
            coin_kelly_rets[(coin, k)] = r
            m = _metrics(r)
            rows.append({"coin": coin, "feature_set": feat, "kelly": k, **m})
            print(f"    kelly={k:.2f}  SR={m['sharpe']:+.3f}  "
                  f"ret={m['total_return']:+8.1%}  "
                  f"maxDD={m['max_drawdown']:6.1%}  "
                  f"annVol={m['ann_vol']:5.1%}")
        print()

    per_coin_df = pd.DataFrame(rows)
    per_coin_df.to_csv(out_dir / "per_coin.csv", index=False)

    # ── Per-coin optimal Kelly ──
    print(f"  {'-' * 78}")
    print(f"  Per-coin argmax-SR Kelly:")
    print(f"  {'-' * 78}")
    optimal_per_coin: dict[str, float] = {}
    for coin in DEFAULT_ROUTING:
        sub = per_coin_df[per_coin_df["coin"] == coin]
        best = sub.loc[sub["sharpe"].idxmax()]
        optimal_per_coin[coin] = float(best["kelly"])
        print(f"    {coin:12s}  kelly*={best['kelly']:.2f}  "
              f"SR={best['sharpe']:+.3f}  ret={best['total_return']:+.1%}  "
              f"maxDD={best['max_drawdown']:.1%}")
    print()

    # ── Uniform-kelly portfolios ──
    print(f"  {'-' * 78}")
    print(f"  Uniform-Kelly portfolios (25% EW across 4 coins):")
    print(f"  {'-' * 78}")
    port_rows = []
    for k in KELLY_GRID:
        df = pd.DataFrame({c: coin_kelly_rets[(c, k)] for c in DEFAULT_ROUTING}).dropna()
        port = df.mean(axis=1)
        m = _metrics(port)
        port_rows.append({"kelly": k, **m})
        print(f"    kelly={k:.2f}  SR={m['sharpe']:+.3f}  ret={m['total_return']:+8.1%}  "
              f"maxDD={m['max_drawdown']:6.1%}  annVol={m['ann_vol']:5.1%}")
    pd.DataFrame(port_rows).to_csv(out_dir / "portfolio_uniform.csv", index=False)
    print()

    # ── Per-coin-optimal portfolio ──
    print(f"  {'-' * 78}")
    print(f"  Per-coin-optimal portfolio (each coin at its argmax-SR Kelly):")
    print(f"  {'-' * 78}")
    df_opt = pd.DataFrame({
        c: coin_kelly_rets[(c, optimal_per_coin[c])] for c in DEFAULT_ROUTING
    }).dropna()
    port_opt = df_opt.mean(axis=1)
    m_opt = _metrics(port_opt)
    print(f"    routing: {optimal_per_coin}")
    print(f"    SR={m_opt['sharpe']:+.3f}  ret={m_opt['total_return']:+8.1%}  "
          f"maxDD={m_opt['max_drawdown']:6.1%}  annVol={m_opt['ann_vol']:5.1%}")
    print()

    # ── Comparison vs canonical uniform=0.50 + live uniform=0.25 ──
    uniform_50 = next(r for r in port_rows if r["kelly"] == 0.50)
    uniform_25 = next(r for r in port_rows if r["kelly"] == 0.25)
    print(f"  {'-' * 78}")
    print(f"  Comparison vs canonical Kelly settings:")
    print(f"  {'-' * 78}")
    print(f"    uniform 0.50 (canonical backtest):  SR={uniform_50['sharpe']:+.3f}  "
          f"ret={uniform_50['total_return']:+.1%}  maxDD={uniform_50['max_drawdown']:.1%}")
    print(f"    uniform 0.25 (live deployment):      SR={uniform_25['sharpe']:+.3f}  "
          f"ret={uniform_25['total_return']:+.1%}  maxDD={uniform_25['max_drawdown']:.1%}")
    print(f"    per-coin optimal:                    SR={m_opt['sharpe']:+.3f}  "
          f"ret={m_opt['total_return']:+.1%}  maxDD={m_opt['max_drawdown']:.1%}")
    delta_vs_uniform_50 = m_opt["sharpe"] - uniform_50["sharpe"]
    print(f"\n    ΔSR (per-coin-optimal − uniform 0.50): {delta_vs_uniform_50:+.3f}")
    print()

    summary = {
        "window": {"start": START, "end": END},
        "kelly_grid": KELLY_GRID,
        "routing": DEFAULT_ROUTING,
        "optimal_per_coin": optimal_per_coin,
        "uniform_portfolios": port_rows,
        "per_coin_optimal_portfolio": m_opt,
        "delta_vs_uniform_0.50": delta_vs_uniform_50,
    }
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"  Wrote: {out_dir / 'per_coin.csv'}")
    print(f"  Wrote: {out_dir / 'portfolio_uniform.csv'}")
    print(f"  Wrote: {out_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
