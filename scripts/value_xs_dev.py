"""value_xs_t1 dev runner: probes P0-P2 (STOP semantics) then the frozen grid.

Probes run first and STOP the experiment on failure, so a broken data path
cannot reach a publishable number. Registered in data/rebuild/gates.json
under value_xs_t1; this file must not introduce any config not in that grid.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.fetch_xsect_fundamentals import ASSET_TO_SYMBOL  # noqa: E402
from tradingagents.xsect.ls_common import ls_weights, sharpe_365, zero_funding  # noqa: E402
from tradingagents.xsect.universe import load_klines, weekly_rebalance_dates  # noqa: E402
from tradingagents.xsect.value_xs import (  # noqa: E402
    control_signal, load_fundamentals, membership_mask, simple_returns,
    value_ratio, zscore_signal,
)

ROOT = Path(__file__).resolve().parents[1]
FUND_DIR = ROOT / "data" / "xsect" / "fundamentals"
KLINES_DIR = ROOT / "data" / "xsect" / "klines"
UNIV_FILE = ROOT / "data" / "xsect" / "value_xs_universe.json"
OUT_DIR = ROOT / "data" / "rebuild" / "value_xs"

DEV = ("2021-01-01", "2025-03-31")
WARMUP_START = "2020-06-01"        # 30d rolling windows warm up before DEV[0]
MAX_LOAD_END = "2025-03-31"        # holdout starts 2025-04-01; never load past this
REGISTERED_LAG = 2
MIN_MEDIAN_BREADTH = 20
LEG_FRAC = {"decile": 0.1, "tercile": 1 / 3}
GRID = [("nvt_proxy", "decile"), ("nvt_proxy", "tercile"),
        ("metcalfe_proxy", "decile"), ("metcalfe_proxy", "tercile")]


def measure_lag(fund_last: pd.Timestamp, kline_last: pd.Timestamp) -> int:
    """Publication lag in days between the fundamentals and price stores."""
    return int((kline_last - fund_last).days)


def decile_spread(S: pd.DataFrame, R: pd.DataFrame, valid: pd.DataFrame,
                  leg_frac: float) -> float:
    """Mean daily (cheap leg - expensive leg) return. Gross, no costs."""
    rb = S.index[S.index.dayofweek == 0]
    W = ls_weights(S.index, S, valid, rb, leg_frac)
    Wprev = W.shift(1).fillna(0.0)
    gross = (Wprev * R.fillna(0.0)).sum(axis=1)
    return float(gross.mean())


def verdict_from_probes(p0: dict, p1: dict, p2: dict) -> str:
    return "CONTINUE" if all(p.get("pass") for p in (p0, p1, p2)) else "NEGATIVE-at-probe"


def _load_all():
    days = pd.date_range(WARMUP_START, MAX_LOAD_END, freq="D", tz="UTC")
    klines = load_klines(KLINES_DIR)
    universe = json.loads(UNIV_FILE.read_text())
    symbols = sorted({s for v in universe.values() for s in v})
    klines = {s: d for s, d in klines.items() if s in symbols}
    fund = load_fundamentals(FUND_DIR, ASSET_TO_SYMBOL)
    fund = {s: d for s, d in fund.items() if s in symbols}
    return days, klines, fund, universe, symbols


def probe_p0_lag(days, klines, fund) -> dict:
    fl = max(d.index.max() for d in fund.values())
    kl = max(d.index.max() for d in klines.values())
    lag = measure_lag(fl, kl)
    return {"probe": "P0_publication_lag", "fund_last": str(fl)[:10],
            "kline_last": str(kl)[:10], "measured_lag_days": lag,
            "registered_lag_days": REGISTERED_LAG,
            "pass": bool(lag <= REGISTERED_LAG),
            "note": ("measured lag exceeds the registered t-2 convention; widen "
                     "the lag and log a pre-result amendment before the grid"
                     if lag > REGISTERED_LAG else "within registered lag")}


def probe_p1_breadth(universe, days, symbols, fund) -> dict:
    """Breadth probe. Gated on universe breadth (registered). Also reports the
    honest signal-valid denominator (universe intersect non-NaN nvt_proxy
    ratio at the registered lag) for the write-up -- not gated.
    """
    sizes = {m: len(v) for m, v in universe.items()}
    by_year: dict[str, list[int]] = {}
    for m, n in sizes.items():
        by_year.setdefault(m[:4], []).append(n)
    med = statistics.median(sizes.values())

    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    M = membership_mask(days, symbols, universe)
    S = zscore_signal(value_ratio(fund, "nvt_proxy", days), REGISTERED_LAG)
    signal_valid = (M.loc[dev] & S.loc[dev].notna()).sum(axis=1)

    return {"probe": "P1_breadth", "median_breadth": med,
            "min_breadth": min(sizes.values()),
            "breadth_by_year": {y: statistics.median(v) for y, v in sorted(by_year.items())},
            "median_signal_valid_breadth": float(signal_valid.median()),
            "min_signal_valid_breadth": float(signal_valid.min()),
            "floor": MIN_MEDIAN_BREADTH, "pass": bool(med >= MIN_MEDIAN_BREADTH)}


def probe_p2_monotonicity(days, klines, fund, universe, symbols) -> dict:
    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    R = simple_returns(klines, days, symbols)
    M = membership_mask(days, symbols, universe)
    spreads = {}
    for metric in ("nvt_proxy", "metcalfe_proxy"):
        S = zscore_signal(value_ratio(fund, metric, days), REGISTERED_LAG)
        valid = M & S.notna()
        spreads[metric] = decile_spread(S.loc[dev], R.loc[dev], valid.loc[dev],
                                        LEG_FRAC["decile"])
    return {"probe": "P2_monotonicity", "spread_by_metric": spreads,
            "pass": bool(any(v > 0 for v in spreads.values())),
            "note": "cheap-minus-expensive gross daily spread must be positive "
                    "for at least one metric"}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    days, klines, fund, universe, symbols = _load_all()
    p0 = probe_p0_lag(days, klines, fund)
    p1 = probe_p1_breadth(universe, days, symbols, fund)
    p2 = probe_p2_monotonicity(days, klines, fund, universe, symbols)
    verdict = verdict_from_probes(p0, p1, p2)
    out = {"experiment": "value_xs_t1", "probes": [p0, p1, p2], "verdict": verdict}
    (OUT_DIR / "probes.json").write_text(json.dumps(out, indent=1, default=str))
    for p in (p0, p1, p2):
        print(f"{p['probe']}: {'PASS' if p['pass'] else 'FAIL'}  {p}")
    print(f"VERDICT: {verdict}")
    if verdict != "CONTINUE":
        sys.exit(2)


if __name__ == "__main__":
    main()
