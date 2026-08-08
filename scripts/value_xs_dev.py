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
from tradingagents.rebuild.ledger import DEFAULT_LEDGER, log_trial  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.xsect.carry_xs import RF_DAILY, run_ls_portfolio  # noqa: E402
from tradingagents.xsect.portfolio import maxdd, rank_placebo_pvalue  # noqa: E402

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

# Fix round 3/5 (2026-07-30) Finding 3: document the vendor-frontier scope
# rather than expanding VENDOR_REFERENCE_ASSETS toward the universe tail.
# xtz/dot/bsv have coverage that genuinely ends in 2022-23 (already
# disclosed for value_xs_t1's six partial/empty names); including them as
# lag references would register multi-hundred-day "lags" that are dead-
# asset artifacts, not publishing delay -- the same conflation that
# already produced the superseded 443- and 471-day measurements.
P0_VENDOR_SCOPE_NOTE = (
    "measured_lag_days / vendor_max_time reflect CoinMetrics' publishing "
    "cadence on actively-covered majors (vendor_reference_assets) -- how "
    "many days behind fetch time the vendor's newest datapoint is for "
    "assets it is actively publishing. This does NOT measure per-asset "
    "coverage termination: several value_xs_t1 candidates (bnb, eos_eth, "
    "trx_eth empty; xtz, dot, bsv truncated in 2022-23) have genuinely "
    "stopped receiving CoinMetrics updates years ago -- a separate, "
    "already-disclosed gap tracked per-asset in "
    "fundamentals_manifest.json's rows/first/last fields, not a "
    "publishing-lag issue. A thin-coverage or delisted-on-CM asset would "
    "register as a large apparent lag for reasons unrelated to publishing "
    "cadence if used as a lag reference, which is exactly why "
    "vendor_reference_assets is restricted to majors with full, "
    "continuous coverage instead of being expanded toward the universe "
    "tail."
)

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
    # Fix round 3/5 Finding 2: klines (data/xsect/klines/) is shared,
    # continuously-updated infra, unlike the fundamentals store, which is
    # deliberately capped at MAX_END. Loading it unbounded read rows deep
    # inside the sealed holdout into memory (a letter-of-the-line breach of
    # "never load data past MAX_LOAD_END", even though no probe outcome
    # depended on that content) and made kline_last -- previously persisted
    # into probes.json -- change on every re-run, which is wrong for a
    # disclosure artifact that is supposed to be stable. Truncate at load
    # time and never surface an unbounded date from this store again.
    days = pd.date_range(WARMUP_START, MAX_LOAD_END, freq="D", tz="UTC")
    universe = json.loads(UNIV_FILE.read_text())
    symbols = sorted({s for v in universe.values() for s in v})
    klines = {s: d.loc[:MAX_LOAD_END] for s, d in load_klines(KLINES_DIR).items()
             if s in symbols}
    max_load_end_ts = pd.Timestamp(MAX_LOAD_END, tz="UTC")
    assert all(d.index.max() <= max_load_end_ts for d in klines.values() if len(d)), (
        "a klines frame exceeds MAX_LOAD_END after truncation -- the sealed "
        "holdout boundary must never be crossed, even in memory"
    )
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

    ``kline_last`` is deliberately not reported (fix round 3, Finding 2):
    klines is a shared, continuously-updated store, so its raw endpoint is
    both irrelevant to the lag arithmetic (unused since fix round 2) and
    non-reproducible in a disclosure artifact that is supposed to be
    stable across re-runs. ``stamp_alignment.dev_overlap_end`` is the
    deterministic witness in its place.
    """
    fl = max(d.index.max() for d in fund.values())

    vintage = json.loads(FUND_VINTAGE_FILE.read_text())
    try:
        lag_result = _lag_from_vintage(vintage)
    except VintageStampStale as e:
        # Fix round 3, Finding 1: fold the loud failure into the normal
        # STOP contract instead of letting it propagate as an uncaught
        # exception -- main() must still exit 2 and write probes.json
        # recording *why*, not die with Python's default exit 1 and no
        # artifact. This is the same bug class that cost two rounds: a
        # failure that is loud in a unit test but not wired into the
        # contract the rest of the pipeline depends on.
        return {"probe": "P0_publication_lag", "fund_last": str(fl)[:10],
                "registered_lag_days": REGISTERED_LAG, "pass": False,
                "error": "vintage_stamp_stale", "note": str(e)}
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
            "fetched_utc": str(lag_result["fetched_utc"])[:10],
            "vendor_max_time": str(lag_result["vendor_max_time"])[:10],
            "vendor_reference_assets": vintage.get("vendor_reference_assets"),
            "vendor_metrics": vintage.get("vendor_metrics"),
            "vendor_max_time_scope": P0_VENDOR_SCOPE_NOTE,
            "measured_lag_days": lag, "registered_lag_days": REGISTERED_LAG,
            "lag_pass": lag_ok,
            "stamp_alignment": {"tz_ok": tz_ok, "midnight_aligned_ok": midnight_ok,
                                "dev_overlap_ok": overlap_ok,
                                "dev_overlap_end": str(dev.max())[:10],
                                "pass": stamp_ok},
            "pass": passed,
            "note": ("within registered lag and stamp-aligned" if passed else
                     "measured lag exceeds registered_lag_days and/or a "
                     "stamp-alignment check failed; widening the lag is a "
                     "pre-result amendment a human must approve"),
            "superseded_measurements": SUPERSEDED_P0_MEASUREMENTS,
            "correction_rationale": P0_CORRECTION_RATIONALE,
            "live_verification": P0_LIVE_VERIFICATION}


def probe_p1_breadth(universe, days, symbols, fund) -> dict:
    """Breadth probe. Gated on universe breadth (registered) -- unchanged by
    fix round 3. Also reports the honest signal-valid denominator (universe
    intersect non-NaN ratio at the registered lag), per metric -- not gated.

    Fix round 3, Finding 4: previously nvt_proxy-only. metcalfe_proxy draws
    on a different denominator (AdrActCnt vs TxCnt) and can have a
    different NaN pattern, so an nvt_proxy-only figure may not describe a
    metcalfe_proxy grid run. Both are reported, keyed by metric name.
    """
    sizes = {m: len(v) for m, v in universe.items()}
    by_year: dict[str, list[int]] = {}
    for m, n in sizes.items():
        by_year.setdefault(m[:4], []).append(n)
    med = statistics.median(sizes.values())

    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    M = membership_mask(days, symbols, universe)
    median_signal_valid, min_signal_valid = {}, {}
    for metric in ("nvt_proxy", "metcalfe_proxy"):
        S = zscore_signal(value_ratio(fund, metric, days), REGISTERED_LAG)
        signal_valid = (M.loc[dev] & S.loc[dev].notna()).sum(axis=1)
        median_signal_valid[metric] = float(signal_valid.median())
        min_signal_valid[metric] = float(signal_valid.min())

    return {"probe": "P1_breadth", "median_breadth": med,
            "min_breadth": min(sizes.values()),
            "breadth_by_year": {y: statistics.median(v) for y, v in sorted(by_year.items())},
            "median_signal_valid_breadth": median_signal_valid,
            "min_signal_valid_breadth": min_signal_valid,
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
    run_grid(days, klines, fund, universe, symbols)


# ---------------------------------------------------------------------------
# Grid half (Task 7): 4 configs, controls, dual-family placebo, DSR, ledger.
# ---------------------------------------------------------------------------

N_PLACEBO = 500
GRID_GATE = {"net_sr_min": 1.0, "placebo_p_max": 0.05, "dsr_min": 0.9,
             "delta_sr_vs_c1_min": 0.0, "delta_sr_vs_c2_min": 0.0}


def run_config(S: pd.DataFrame, R: pd.DataFrame, valid: pd.DataFrame,
               leg_frac: float, cost_bps: float = 10.0) -> pd.Series:
    """Daily net portfolio returns for one signal matrix.

    P&L runs through the frozen section-46 engine with a zero funding leg, so
    cost, lag and rf semantics are byte-identical to carry_xs_t1.
    """
    rb = weekly_rebalance_dates(str(S.index[0])[:10], str(S.index[-1])[:10])
    W = ls_weights(S.index, S, valid, rb, leg_frac)
    F = zero_funding(S.index, S.columns)
    return run_ls_portfolio(W, R.reindex_like(W), F, cost_bps=cost_bps,
                            rf_daily=RF_DAILY)


def circular_shift_columns(S: pd.DataFrame, rng) -> pd.DataFrame:
    """Placebo family A: independent circular shift per symbol."""
    out = S.copy()
    n = len(S)
    for c in S.columns:
        k = int(rng.integers(1, n)) if n > 1 else 0
        out[c] = np.roll(S[c].to_numpy(), k)
    return out


def rank_shuffle_columns(S: pd.DataFrame, rng) -> pd.DataFrame:
    """Placebo family B: permute each row's values across symbols."""
    v = S.to_numpy(copy=True)
    for i in range(v.shape[0]):
        row = v[i]
        idx = np.arange(row.shape[0])
        rng.shuffle(idx)
        v[i] = row[idx]
    return pd.DataFrame(v, index=S.index, columns=S.columns)


def dsr_or_nan(returns: pd.Series, n_trials: int) -> float:
    """DSR in per-bar units, matching liq_fade_dev.py (THESIS section 49).

    variance_of_sr works in per-bar units, so the observed SR must be per-bar
    too. Passing the sqrt(365)-annualized SR mixes units and saturates Phi()
    to 1.0 for any positive SR, making the gate inoperative (2026-07-30 fix:
    the reported net_sr stays sqrt(365)-annualized per the registration --
    only the DSR internals are per-bar).
    """
    arr = pd.Series(returns).dropna().to_numpy()
    if len(arr) < 2:
        return float("nan")
    sd = float(arr.std(ddof=1))
    if not np.isfinite(sd) or sd == 0.0:
        return float("nan")
    try:
        var_sr = variance_of_sr(arr)
        se = float(np.sqrt(var_sr))
        if se <= 0.0:
            return float("nan")
        sr_perbar = float(arr.mean() / sd)
        return float(deflated_sharpe_ratio(sr_perbar, expected_max_sharpe(n_trials, var_sr), se))
    except ValueError:
        return float("nan")


def gate_config(net_sr: float, placebo_p_worse: float, dsr: float,
                delta_c1: float, delta_c2: float) -> dict:
    checks = {
        "net_sr": net_sr >= GRID_GATE["net_sr_min"],
        "placebo": placebo_p_worse <= GRID_GATE["placebo_p_max"],
        "dsr": bool(dsr >= GRID_GATE["dsr_min"]),   # NaN >= x is False
        "delta_c1": delta_c1 > GRID_GATE["delta_sr_vs_c1_min"],
        "delta_c2": delta_c2 > GRID_GATE["delta_sr_vs_c2_min"],
    }
    return {"checks": checks, "pass": all(checks.values())}


def unique_config_hashes(ledger_path: Path = DEFAULT_LEDGER) -> int:
    """Distinct config evaluations in the ledger — the DSR denominator source."""
    seen = set()
    if ledger_path.exists():
        for line in ledger_path.read_text().splitlines():
            if line.strip():
                seen.add(json.loads(line)["config_hash"])
    return len(seen)


def run_grid(days, klines, fund, universe, symbols, n_placebo: int = N_PLACEBO,
             log: bool = True) -> dict:
    """Frozen 4-config grid.

    ``log=False`` suppresses ledger writes for smoke runs. A reduced-placebo
    smoke shares config_hash with the real run, so it would not inflate the
    DSR denominator — but it would put rows carrying 5-draw placebo p-values
    into the ledger that every DSR count in the thesis is audited against.
    """
    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    R = simple_returns(klines, days, symbols).loc[dev]
    M = membership_mask(days, symbols, universe).loc[dev]

    controls = {}
    for kind in ("vol", "reversal"):
        C = control_signal(klines, days, symbols, kind).loc[dev]
        controls[kind] = sharpe_365(run_config(C, R, M & C.notna(),
                                               LEG_FRAC["decile"]))

    ledger_before = unique_config_hashes()
    rng = np.random.default_rng(20260730)
    results = []
    for metric, breadth in GRID:
        S = zscore_signal(value_ratio(fund, metric, days), REGISTERED_LAG).loc[dev]
        valid = M & S.notna()
        leg = LEG_FRAC[breadth]
        port = run_config(S, R, valid, leg)
        net_sr = sharpe_365(port)

        srs_a = [sharpe_365(run_config(circular_shift_columns(S, rng), R, valid, leg))
                 for _ in range(n_placebo)]
        srs_b = [sharpe_365(run_config(rank_shuffle_columns(S, rng), R, valid, leg))
                 for _ in range(n_placebo)]
        p_a = rank_placebo_pvalue(net_sr, srs_a)
        p_b = rank_placebo_pvalue(net_sr, srs_b)
        p_worse = max(p_a, p_b)

        dsr_own = dsr_or_nan(port, n_trials=len(GRID))
        dsr_ledger = dsr_or_nan(port, n_trials=ledger_before + len(GRID))
        d_c1 = net_sr - controls["vol"]
        d_c2 = net_sr - controls["reversal"]
        gate = gate_config(net_sr, p_worse, dsr_own, d_c1, d_c2)

        cfg = {"metric": metric, "breadth": breadth, "leg_frac": leg,
               "lag_days": REGISTERED_LAG, "cost_bps": 10.0,
               "rebalance": "weekly_monday", "universe": "value_xs_universe.json",
               "n_symbols": int(len(symbols))}
        metrics = {"net_sr": net_sr, "maxdd": float(maxdd(port)),
                   "n_bars": int(len(port)),
                   "placebo_p_shiftfam": p_a, "placebo_p_randfam": p_b,
                   "placebo_p_worse": p_worse,
                   "dsr_own_n": dsr_own, "dsr_own_n_trials": len(GRID),
                   "dsr_ledger_n": dsr_ledger,
                   "dsr_ledger_n_trials": ledger_before + len(GRID),
                   "sr_control_vol": controls["vol"],
                   "sr_control_reversal": controls["reversal"],
                   "delta_sr_vs_c1": d_c1, "delta_sr_vs_c2": d_c2,
                   **{f"gate_{k}": v for k, v in gate["checks"].items()},
                   "gate_pass": gate["pass"]}
        if log:
            log_trial("value_xs_t1", cfg, DEV, metrics)
        results.append({"config": cfg, "metrics": metrics})
        print(f"{metric}/{breadth}: SR {net_sr:+.3f} p {p_worse:.4f} "
              f"DSR {dsr_own:.3f} dC1 {d_c1:+.3f} dC2 {d_c2:+.3f} "
              f"{'PASS' if gate['pass'] else 'FAIL'}")

    passing = [r for r in results if r["metrics"]["gate_pass"]]
    out = {"experiment": "value_xs_t1", "controls": controls,
           "ledger_unique_hashes_before": ledger_before,
           "results": results, "n_pass": len(passing),
           "verdict": "GO-at-dev" if passing else "NEGATIVE"}
    (OUT_DIR / "grid.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"VERDICT: {out['verdict']} ({len(passing)}/{len(GRID)})")
    return out


if __name__ == "__main__":
    main()
