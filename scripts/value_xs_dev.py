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
FUND_VINTAGE_FILE = ROOT / "data" / "xsect" / "fundamentals_vintage.json"
KLINES_DIR = ROOT / "data" / "xsect" / "klines"
UNIV_FILE = ROOT / "data" / "xsect" / "value_xs_universe.json"
OUT_DIR = ROOT / "data" / "rebuild" / "value_xs"

# Fix round 1/5 (2026-07-30): the original P0 differenced the last dates of
# two stores fetched to unrelated end bounds (fundamentals capped at the
# sealed-holdout MAX_END; klines fetched to present) and measured 443 days
# of fetch-scope mismatch, not publication lag.
#
# Fix round 2/5 (2026-07-30): round 1's replacement (fetched_utc minus the
# store's own last observation) had the *same* defect -- the store's last
# observation is the deliberate MAX_END truncation, not the vendor's
# frontier, so that diff measured 471 days of the same truncation artifact.
# Publication lag is a vendor property and cannot be derived from a
# deliberately truncated store's endpoint by any arithmetic. The fix:
# capture the vendor's true frontier at fetch time from the catalog
# endpoint (scripts/fetch_xsect_fundamentals.py::_vendor_max_time, not
# subject to --end truncation), persist it in the vintage stamp
# (vendor_max_time), and have P0 read that stamp offline -- never a live
# network call, never a silent fallback to a store-endpoint comparison.
#
# gates.json registers P0 only as "publication-lag and stamp alignment;
# STOP on fail" -- it does not prescribe an implementation, so both
# corrections implement the registration rather than amend it. See
# probes.json for the full disclosure trail (superseded_measurements /
# correction_rationale / live_verification) and task-6-report.md fix
# rounds 1-2.
SUPERSEDED_P0_MEASUREMENTS = [
    {"measured_lag_days": 443,
     "method": ("differenced the last dates of two stores fetched to "
                "different end bounds (fundamentals capped at the "
                "sealed-holdout MAX_END=2025-04-15; klines fetched to "
                "present, 2026-07-02)")},
    {"measured_lag_days": 471,
     "method": ("differenced fetch date against store last observation, "
                "which is the deliberate holdout cap (MAX_END=2025-04-15) "
                "rather than the vendor frontier")},
]
P0_CORRECTION_RATIONALE = ("the store is truncated at MAX_END by design, so "
                            "publication lag cannot be derived from its "
                            "endpoint; the vendor frontier is captured at "
                            "fetch time (catalog endpoint, not subject to "
                            "--end truncation) and compared against the "
                            "fetch date")
P0_LIVE_VERIFICATION = {
    "assets": ["btc", "eth", "ada", "doge"],
    "metrics": ["AdrActCnt", "TxCnt", "CapMrktCurUSD"],
    "max_time_observed": "2026-07-29",
    "observed_lag_days": 1,
    "observed_on": "2026-07-30",
    "note": ("independent live check against CoinMetrics wall clock, run by "
             "the coordinator outside this probe and outside the on-disk "
             "holdout-capped fundamentals store; confirms the registered "
             "t-2 convention is conservative for the true vendor lag"),
}

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


def _tz_utc_ok(idx: pd.DatetimeIndex) -> bool:
    return len(idx) == 0 or (idx.tz is not None and str(idx.tz) == "UTC")


def _midnight_aligned(idx: pd.DatetimeIndex) -> bool:
    return len(idx) == 0 or bool((idx == idx.normalize()).all())


def _overlaps_dev(idx: pd.DatetimeIndex, dev: pd.DatetimeIndex) -> bool:
    return bool(idx.intersection(dev).size)


class VintageStampStale(RuntimeError):
    """Raised when the vintage stamp predates vendor-frontier recording.

    P0 must fail loudly here, not silently fall back to a store-endpoint
    comparison -- that fallback is exactly the defect fix rounds 1 and 2
    both hit (443 days, then 471 days), because a deliberately
    holdout-truncated store's own endpoint can never stand in for the
    vendor's true frontier.
    """


def _lag_from_vintage(vintage: dict, registered_lag: int = REGISTERED_LAG) -> dict:
    """Pure: the P0 lag gate from an in-memory vintage-stamp dict.

    Lag is the vendor's true frontier (``vendor_max_time``, captured from
    the catalog endpoint at fetch time -- not subject to MAX_END
    truncation) staleness relative to the stamp's own fetch time
    (``fetched_utc``). Raises ``VintageStampStale`` if ``vendor_max_time``
    is absent, rather than returning a (silently wrong) pass/fail dict.
    """
    if "vendor_max_time" not in vintage:
        raise VintageStampStale(
            "vintage stamp has no 'vendor_max_time' field -- this stamp "
            "predates vendor-frontier recording (fix round 2) and must be "
            "refreshed via `uv run --no-sync python "
            "scripts/fetch_xsect_fundamentals.py --vintage-only` before P0 "
            "can run."
        )
    fetched_utc = pd.Timestamp(vintage["fetched_utc"]).tz_convert("UTC").normalize()
    vendor_max_time = pd.Timestamp(vintage["vendor_max_time"], tz="UTC")
    lag = measure_lag(vendor_max_time, fetched_utc)
    return {"lag": lag, "fetched_utc": fetched_utc,
            "vendor_max_time": vendor_max_time,
            "pass": bool(lag <= registered_lag)}


def probe_p0_lag(days, klines, fund) -> dict:
    """P0 = publication-lag AND stamp alignment (gates.json: 'publication-lag
    and stamp alignment; STOP on fail'). Lag reads the vendor frontier
    persisted in the vintage stamp (see ``_lag_from_vintage``) -- it never
    diffs two stores' raw endpoints and never makes a live network call at
    run time. See the superseded_* / live_verification fields below.
    """
    fl = max(d.index.max() for d in fund.values())
    kl = max(d.index.max() for d in klines.values())

    vintage = json.loads(FUND_VINTAGE_FILE.read_text())
    lag_result = _lag_from_vintage(vintage)
    lag, lag_ok = lag_result["lag"], lag_result["pass"]

    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    tz_ok = (all(_tz_utc_ok(d.index) for d in fund.values())
             and all(_tz_utc_ok(d.index) for d in klines.values()))
    midnight_ok = (all(_midnight_aligned(d.index) for d in fund.values())
                   and all(_midnight_aligned(d.index) for d in klines.values()))
    overlap_ok = (any(_overlaps_dev(d.index, dev) for d in fund.values())
                  and any(_overlaps_dev(d.index, dev) for d in klines.values()))
    stamp_ok = bool(tz_ok and midnight_ok and overlap_ok)

    passed = bool(lag_ok and stamp_ok)
    return {"probe": "P0_publication_lag", "fund_last": str(fl)[:10],
            "kline_last": str(kl)[:10],
            "fetched_utc": str(lag_result["fetched_utc"])[:10],
            "vendor_max_time": str(lag_result["vendor_max_time"])[:10],
            "vendor_reference_assets": vintage.get("vendor_reference_assets"),
            "vendor_metrics": vintage.get("vendor_metrics"),
            "measured_lag_days": lag, "registered_lag_days": REGISTERED_LAG,
            "lag_pass": lag_ok,
            "stamp_alignment": {"tz_ok": tz_ok, "midnight_aligned_ok": midnight_ok,
                                "dev_overlap_ok": overlap_ok, "pass": stamp_ok},
            "pass": passed,
            "note": ("within registered lag and stamp-aligned" if passed else
                     "measured lag exceeds registered_lag_days and/or a "
                     "stamp-alignment check failed; widening the lag is a "
                     "pre-result amendment a human must approve"),
            "superseded_measurements": SUPERSEDED_P0_MEASUREMENTS,
            "correction_rationale": P0_CORRECTION_RATIONALE,
            "live_verification": P0_LIVE_VERIFICATION}


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
