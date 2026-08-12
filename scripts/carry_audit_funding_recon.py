#!/usr/bin/env python
"""Carry audit pass 3: funding reconciliation vs raw 8h events.

`aggregate_daily_funding_income` (tradingagents/strategies/carry_sleeve.py) is
the function under test: it groups raw Binance 8h funding prints by UTC date
and sums `fundingRate` into a daily funding-income series that a short-perp
leg collects (positive) or pays (negative). This pass verifies that
aggregation is correct by re-deriving the same daily income independently —
via a plain Python accumulation loop over `fetch_funding_raw`'s raw frame,
NOT by calling `aggregate_daily_funding_income` itself — and diffing the two.

Per Binance semantics, a positive fundingRate means longs pay shorts; since
the sleeve is short-perp, income per event = +fundingRate * notional (1.0
notional here, i.e. rate itself). A negative rate means shorts pay longs
(income is negative that day).

Sampled on 3 quarters spanning bear/chop/bull regimes (2022-Q2, 2023-Q4,
2024-Q1) x (BTCUSDT, ETHUSDT), a stratified sample of the full audit window
rather than an exhaustive scan, per task-C3-brief.md.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.strategies.carry_sleeve import (  # noqa: E402
    aggregate_daily_funding_income,
    fetch_funding_raw,
)

FULL_WINDOW = ("2021-11-08", "2025-03-31")
SYMBOLS = ("BTCUSDT", "ETHUSDT")

# (label, start inclusive, end exclusive) — end is the day AFTER the quarter's
# last day, matching fetch_funding_raw's exclusive-end convention.
QUARTERS = [
    ("2022-Q2_bear", date(2022, 4, 1), date(2022, 7, 1)),
    ("2023-Q4_chop", date(2023, 10, 1), date(2024, 1, 1)),
    ("2024-Q1_bull", date(2024, 1, 1), date(2024, 4, 1)),
]


def independent_recompute(raw: pd.DataFrame) -> dict[date, float]:
    """Hand-rolled daily funding income, deliberately NOT reusing
    `aggregate_daily_funding_income` (the function under audit).

    Iterates raw events with a plain accumulation loop (no pandas groupby),
    summing rate * notional (notional = 1.0) per UTC calendar day. Short side
    receives positive rates (income = +rate when rate > 0); a negative rate
    means the short pays (income is negative).
    """
    income: dict[date, float] = {}
    for _, row in raw.iterrows():
        rate = float(row["fundingRate"])
        ts_ms = int(row["fundingTime"])
        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
        day = dt.date()
        notional = 1.0
        income[day] = income.get(day, 0.0) + rate * notional
    return income


def compare_daily_series(recomputed_daily: dict[date, float], module_daily: pd.Series) -> dict:
    """Per-day (not just per-quarter-total) comparison of the two aggregations.

    Totals-only comparison is invariant to how events get bucketed into days —
    a timezone/day-boundary bug in `aggregate_daily_funding_income` (e.g. an
    off-by-one-day shift applied consistently) would still sum to the same
    quarterly total and sail through with rel_diff≈0. Building an explicit
    per-day series and diffing day-by-day (plus cross-checking day *counts*)
    catches that class of bug even when totals agree.
    """
    recomputed_series = pd.Series(recomputed_daily, dtype="float64")
    recomputed_series.index = pd.to_datetime(recomputed_series.index)
    recomputed_series = recomputed_series.sort_index()

    module_series = module_daily.copy()
    module_series.index = pd.to_datetime(module_series.index)
    module_series = module_series.sort_index()

    n_days_recomputed = int(len(recomputed_series))
    n_days_module = int(len(module_series))

    # Union index: a day present on only one side is itself evidence of a
    # day-boundary discrepancy, so treat the missing side as 0.0 rather than
    # dropping the day.
    union_idx = recomputed_series.index.union(module_series.index)
    aligned_recomputed = recomputed_series.reindex(union_idx, fill_value=0.0)
    aligned_module = module_series.reindex(union_idx, fill_value=0.0)
    daily_abs_diff = (aligned_recomputed - aligned_module).abs()
    max_daily_abs_diff = float(daily_abs_diff.max()) if len(daily_abs_diff) > 0 else 0.0

    daily_series_identical = bool(
        n_days_recomputed == n_days_module and max_daily_abs_diff < 1e-12
    )

    return {
        "n_days_recomputed": n_days_recomputed,
        "n_days_module": n_days_module,
        "max_daily_abs_diff": max_daily_abs_diff,
        "daily_series_identical": daily_series_identical,
    }


def analyze_quarter(symbol: str, q_start: date, q_end: date) -> dict:
    raw = fetch_funding_raw(symbol, q_start, q_end)
    n_events = len(raw)

    recomputed_daily = independent_recompute(raw)
    recomputed_income = float(sum(recomputed_daily.values()))
    n_days = len(recomputed_daily)

    module_daily = aggregate_daily_funding_income(raw)
    module_income = float(module_daily.sum()) if not module_daily.empty else 0.0

    denom = abs(module_income) if module_income != 0.0 else abs(recomputed_income)
    rel_diff = abs(recomputed_income - module_income) / denom if denom > 0 else 0.0

    events_per_day = (n_events / n_days) if n_days > 0 else 0.0
    neg_days = sum(1 for v in recomputed_daily.values() if v < 0)
    neg_funding_day_share = (neg_days / n_days) if n_days > 0 else 0.0

    daily_cmp = compare_daily_series(recomputed_daily, module_daily)

    return {
        "n_events": n_events,
        "n_days": n_days,
        "recomputed_income": recomputed_income,
        "module_income": module_income,
        "rel_diff": rel_diff,
        "events_per_day": events_per_day,
        "neg_funding_day_share": neg_funding_day_share,
        **daily_cmp,
    }


def main() -> None:
    out: dict = {"quarters": {}}

    for label, q_start, q_end in QUARTERS:
        out["quarters"][label] = {}
        for sym in SYMBOLS:
            res = analyze_quarter(sym, q_start, q_end)
            out["quarters"][label][sym] = res
            print(
                f"{label} {sym}: recomputed={res['recomputed_income']:.6f} "
                f"module={res['module_income']:.6f} rel_diff={res['rel_diff']:.6%} "
                f"events/day={res['events_per_day']:.2f} "
                f"neg_share={res['neg_funding_day_share']:.2%} "
                f"n_days(recomp/mod)={res['n_days_recomputed']}/{res['n_days_module']} "
                f"max_daily_abs_diff={res['max_daily_abs_diff']:.3e} "
                f"daily_identical={res['daily_series_identical']}"
            )

    max_rel_diff = max(
        res["rel_diff"]
        for sym_map in out["quarters"].values()
        for res in sym_map.values()
    )
    all_daily_identical = all(
        res["daily_series_identical"]
        for sym_map in out["quarters"].values()
        for res in sym_map.values()
    )
    verdict = "PASS" if (max_rel_diff < 0.01 and all_daily_identical) else "INVESTIGATE"
    out["max_rel_diff"] = max_rel_diff
    out["all_daily_series_identical"] = all_daily_identical
    out["verdict"] = verdict
    out["window_sampled"] = [[q_start.isoformat(), q_end.isoformat()] for _, q_start, q_end in QUARTERS]
    out["symbols"] = list(SYMBOLS)

    outdir = PROJECT_ROOT / "data/rebuild/carry_audit"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "funding_recon.json").write_text(json.dumps(out, indent=2))

    # Flat metrics summary for the ledger.
    flat_metrics = {
        f"{label}__{sym}__{k}": v
        for label, sym_map in out["quarters"].items()
        for sym, res in sym_map.items()
        for k, v in res.items()
    }
    flat_metrics["max_rel_diff"] = max_rel_diff
    flat_metrics["verdict"] = verdict

    log_trial(
        experiment="carry_audit",
        config={"pass": "funding_recon"},
        window=FULL_WINDOW,
        metrics=flat_metrics,
    )

    print(f"\nverdict: {verdict} (max rel_diff = {max_rel_diff:.6%})")


if __name__ == "__main__":
    main()
