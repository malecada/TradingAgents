"""P0 data audit for the funding-carry sleeve (docs/CARRY_SLEEVE_BACKTEST_SPEC.md).

Fetches Binance perp funding for BTC/ETH over the V5 MIX backtest window, derives
the daily funding-INCOME series (sum of 8h prints, not the scraper's mean), and
reports coverage + funding statistics. Gate: clean daily history covering the
window with few gaps for both coins.

Usage:
    python scripts/carry_data_audit.py --start 2021-11-07 --end 2026-04-15
    python scripts/carry_data_audit.py --coins BTCUSDT ETHUSDT BNBUSDT SOLUSDT
"""
from __future__ import annotations

import argparse
from datetime import date, datetime

import numpy as np
import pandas as pd

from tradingagents.strategies.carry_sleeve import (
    aggregate_daily_funding_income,
    fetch_funding_raw,
)

# Binance funds perps 3x/day (every 8h). Used to flag days with missing prints.
PERIODS_PER_DAY = 3
GAP_TOLERANCE_PCT = 2.0  # max % of window days missing before the gate fails


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def audit_symbol(symbol: str, start: date, end: date) -> dict:
    raw = fetch_funding_raw(symbol, start, end)
    if raw.empty:
        return {"symbol": symbol, "ok": False, "reason": "no funding data returned"}

    income = aggregate_daily_funding_income(raw)
    raw = raw.copy()
    raw["fundingRate"] = raw["fundingRate"].astype(float)
    raw["date"] = pd.to_datetime(raw["fundingTime"], unit="ms", utc=True).dt.date
    prints_per_day = raw.groupby("date").size()

    covered = pd.DatetimeIndex(pd.to_datetime(list(income.index)))
    full = pd.date_range(start=covered.min(), end=covered.max(), freq="D")
    missing = full.difference(covered)
    gap_pct = 100.0 * len(missing) / max(len(full), 1)

    inc = income.to_numpy(dtype=float)
    ok = (gap_pct <= GAP_TOLERANCE_PCT) and (covered.min().date() <= start)

    return {
        "symbol": symbol,
        "ok": bool(ok),
        "first_day": covered.min().date(),
        "last_day": covered.max().date(),
        "n_days": int(len(income)),
        "n_expected": int(len(full)),
        "gap_days": int(len(missing)),
        "gap_pct": round(gap_pct, 3),
        "days_with_full_3_prints_pct": round(100.0 * (prints_per_day == PERIODS_PER_DAY).mean(), 1),
        "mean_daily_income": float(np.mean(inc)),
        "median_daily_income": float(np.median(inc)),
        "annualized_mean_pct": round(100.0 * np.mean(inc) * 365.0, 2),
        "pct_positive_days": round(100.0 * float(np.mean(inc > 0)), 1),
        "worst_day": float(np.min(inc)),
        "best_day": float(np.max(inc)),
        "income": income,  # kept for optional downstream persistence
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=_parse_date, default=_parse_date("2021-11-07"))
    ap.add_argument("--end", type=_parse_date, default=_parse_date("2026-04-15"))
    ap.add_argument("--coins", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    args = ap.parse_args()

    print(f"\nFunding-carry P0 data audit  window={args.start}..{args.end}\n")
    results = [audit_symbol(sym, args.start, args.end) for sym in args.coins]

    cols = [
        "symbol", "ok", "first_day", "last_day", "n_days", "gap_days", "gap_pct",
        "days_with_full_3_prints_pct", "annualized_mean_pct", "pct_positive_days",
        "median_daily_income", "worst_day", "best_day",
    ]
    table = pd.DataFrame([{k: r.get(k) for k in cols} for r in results])
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(table.to_string(index=False))

    gate = all(r.get("ok") for r in results)
    print(f"\nGATE: {'PASS' if gate else 'FAIL'} "
          f"(need <={GAP_TOLERANCE_PCT}% gaps and coverage from window start, all coins)\n")


if __name__ == "__main__":
    main()
