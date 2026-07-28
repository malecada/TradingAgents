"""liq_fade_i1 dev runner: probes P0-P2 (Task 8), dev grid (Task 9, not yet
implemented). Ledger: liq_fade_i1. Gates: data/rebuild/gates.json["liq_fade_i1"].
Spec: docs/superpowers/specs/2026-07-28-liq-fade-intraday-design.md.

Probes (all pre-registered, BINDING per gates.json):
  P0 - bar-stamp reconciliation: daily aggregation of BTCUSDT 1h closes must
       correlate > 0.99 with the daily-store BTCUSDT close pct_change on the
       2021-2025 overlap. Sanity check on data plumbing, not a STOP gate.
  P1 - proxy concordance: cascade_triggers (thr=2.5) on the 8 Coinglass-mapped
       majors, aggregated to UTC day (any bar in that coin's day triggers ->
       day flagged), must flag >= 4/5 of the registered benchmark cascade
       dates. FAIL -> STOP (skip Task 9, NEGATIVE-at-probe per THESIS section
       48). A non-gating corroboration diagnostic (p1_liq_zscore_diag) reuses
       liq_zscore on the real daily Coinglass liq/OI data for the same 8
       coins/dates -- independent signal, not part of the P1 verdict.
  P2 - event-study: for each (thr, H) grid cell, mean over all dev-window
       triggers (membership-masked) of the GROSS forward return t+1..t+H must
       exceed +25bp in at least one cell. FAIL -> STOP.

--smoke restricts the symbol universe to whatever is present on disk (the
bulk 1h fetch may still be running) and stamps {"smoke": true} in the output;
a smoke run is NEVER a registered verdict and never exits nonzero.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.xsect.liq_fade import cascade_triggers  # noqa: E402
from tradingagents.xsect.liq_mr import liq_zscore  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYMBOLS_FILE = PROJECT_ROOT / "data" / "xsect" / "liq_fade_symbols.txt"
UNIVERSE_FILE = PROJECT_ROOT / "data" / "xsect" / "liq_fade_universe.json"
KLINES_1H_DIR = PROJECT_ROOT / "data" / "xsect" / "klines_1h"
KLINES_DAILY_DIR = PROJECT_ROOT / "data" / "xsect" / "klines"
DERIV_DIR = PROJECT_ROOT / "data" / "derivatives"
OUT_DIR = PROJECT_ROOT / "data" / "rebuild" / "liq_fade"

DEV = ("2021-01-01", "2025-03-31")          # registered dev window (gates.json)
WARMUP_START = "2020-06-01"                  # 90d/60 z warmup runs ahead of DEV[0]
MAX_LOAD_END = "2025-04-15"                  # holdout starts 2025-04-01; never load past this

GRID = [(thr, H) for thr in (2.5, 3.5) for H in (6, 24, 48)]  # frozen, 6 configs

# Coinglass derivatives slug -> Binance UM symbol; fixed 8 majors (same set as
# liq_mr_t1's COINS, reused here for P0/P1 ground truth only).
COINS = {
    "bitcoin": "BTCUSDT", "ethereum": "ETHUSDT", "binancecoin": "BNBUSDT",
    "solana": "SOLUSDT", "cardano": "ADAUSDT", "dogecoin": "DOGEUSDT",
    "ripple": "XRPUSDT", "tron": "TRXUSDT",
}

BENCHMARK_DATES = ["2021-05-19", "2022-06-13", "2022-11-09", "2024-08-05", "2025-02-03"]

P0_MIN_CORR = 0.99
P1_THR = 2.5
P1_MIN_MATCHES = 4
P2_MIN_RET = 0.0025


def _sanitize(obj):
    if isinstance(obj, float):
        return None if (np.isnan(obj) or np.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize(v) for v in obj]
    return obj


def load_symbols(smoke: bool) -> list[str]:
    """Union symbol list from liq_fade_symbols.txt; --smoke restricts to
    symbols with a parquet already present under data/xsect/klines_1h/."""
    syms = [s.strip() for s in SYMBOLS_FILE.read_text().splitlines() if s.strip()]
    if smoke:
        on_disk = {p.stem for p in KLINES_1H_DIR.glob("*.parquet")}
        syms = [s for s in syms if s in on_disk]
    return syms


def membership_mask_hourly(universe: dict, columns: list[str],
                           index: pd.DatetimeIndex) -> pd.DataFrame:
    """Expand a monthly PIT universe dict to an hourly boolean membership mask.

    `universe` is {month_start (str or Timestamp): [symbols]}. Each entry's
    membership applies from that month start (inclusive) through the bar
    before the NEXT registered month start (exclusive); the last entry's
    membership extends through the end of `index`. Symbols not in `columns`
    are ignored. Pure function -- no I/O, unit-testable on synthetic inputs.
    """
    keys = sorted(universe.keys())
    starts = [pd.Timestamp(k, tz="UTC") for k in keys]
    mask = pd.DataFrame(False, index=index, columns=columns)
    for i, (k, start) in enumerate(zip(keys, starts)):
        end = starts[i + 1] if i + 1 < len(starts) else (
            index[-1] + pd.Timedelta(hours=1) if len(index) else start)
        members = [s for s in universe[k] if s in columns]
        if not members:
            continue
        sel = (index >= start) & (index < end)
        if sel.any():
            mask.loc[sel, members] = True
    return mask


def load_hourly_panel(symbols: list[str], start: str = WARMUP_START,
                      end: str = DEV[1]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load 1h close/quote_volume wide panels for `symbols`, restricted to
    [start, end] (inclusive of end's final hour). Refuses to load past the
    sealed holdout cap (MAX_LOAD_END) regardless of `end`. Missing symbols
    (no parquet on disk) are silently skipped; missing bars within an
    existing symbol's range are left NaN (reindexed onto the shared hourly
    grid, not forward-filled)."""
    lo = pd.Timestamp(start, tz="UTC")
    hi = pd.Timestamp(end, tz="UTC") + pd.Timedelta(hours=23)
    cap = pd.Timestamp(MAX_LOAD_END, tz="UTC")
    if hi > cap:
        raise ValueError(f"refusing to load past sealed holdout cap {MAX_LOAD_END} "
                         f"(requested end {end} -> {hi})")
    idx = pd.date_range(lo, hi, freq="h")
    close, qvol = {}, {}
    for s in symbols:
        p = KLINES_1H_DIR / f"{s}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df.loc[(df.index >= lo) & (df.index <= hi)]
        if df.empty:
            continue
        close[s] = df["close"]
        qvol[s] = df["quote_volume"]
    cols = sorted(close.keys())
    C = pd.DataFrame({s: close[s].reindex(idx) for s in cols}, index=idx, columns=cols)
    Q = pd.DataFrame({s: qvol[s].reindex(idx) for s in cols}, index=idx, columns=cols)
    return C, Q


def probe_p0() -> dict:
    """Daily-aggregation reconciliation on BTCUSDT: resample('1D').last() of
    1h closes, pct_change, must correlate > 0.99 with the daily-store
    BTCUSDT close pct_change over the 2021-2025 overlap. `pass: None` means
    the overlap couldn't be computed yet (insufficient 1h history on disk --
    expected mid-fetch / under --smoke), never a false pass or fail."""
    p1h = KLINES_1H_DIR / "BTCUSDT.parquet"
    pdaily = KLINES_DAILY_DIR / "BTCUSDT.parquet"
    if not p1h.exists() or not pdaily.exists():
        return {"pass": None, "reason": "BTCUSDT store(s) missing", "corr": None,
                "n_overlap_days": 0}
    d1h = pd.read_parquet(p1h)
    daily_from_1h = d1h["close"].resample("1D").last().pct_change()
    dd = pd.read_parquet(pdaily)
    daily_store_ret = dd["close"].pct_change()
    lo, hi = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp("2025-12-31", tz="UTC")
    a = daily_from_1h[(daily_from_1h.index >= lo) & (daily_from_1h.index <= hi)]
    b = daily_store_ret.reindex(a.index)
    valid = a.notna() & b.notna()
    n = int(valid.sum())
    if n < 2:
        return {"pass": None, "reason": "insufficient overlap (1h fetch incomplete)",
                "corr": None, "n_overlap_days": n}
    corr = float(np.corrcoef(a[valid].to_numpy(), b[valid].to_numpy())[0, 1])
    return {"pass": bool(corr > P0_MIN_CORR), "corr": corr, "n_overlap_days": n,
            "required_corr": P0_MIN_CORR}


def probe_p1() -> dict:
    """Proxy concordance: cascade_triggers (thr=2.5) on each of the 8 mapped
    majors' 1h data, aggregated to UTC day (any triggering bar flags the
    day), must flag >= 4/5 registered benchmark dates. `pass: None` means no
    mapped-coin 1h data covering the dev window was available (expected
    mid-fetch / under --smoke)."""
    lo = pd.Timestamp(DEV[0], tz="UTC")
    hi = pd.Timestamp(DEV[1], tz="UTC") + pd.Timedelta(hours=23)
    bench = [pd.Timestamp(d, tz="UTC") for d in BENCHMARK_DATES]
    flagged_by: dict[str, set[str]] = {str(b.date()): set() for b in bench}
    coins_used = []
    for _coin, sym in COINS.items():
        p = KLINES_1H_DIR / f"{sym}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df.loc[(df.index >= lo) & (df.index <= hi)]
        if df.empty:
            continue
        close = df[["close"]].rename(columns={"close": sym})
        qvol = df[["quote_volume"]].rename(columns={"quote_volume": sym})
        trig = cascade_triggers(close, qvol, thr=P1_THR)[sym]
        day_trig = trig.groupby(trig.index.normalize()).any()
        coins_used.append(sym)
        for b in bench:
            if b in day_trig.index and bool(day_trig.loc[b]):
                flagged_by[str(b.date())].add(sym)
    matched_dates = {d: sorted(s) for d, s in flagged_by.items()}
    n_matched = sum(1 for s in flagged_by.values() if s)
    result = {"thr": P1_THR, "coins_used": coins_used, "n_coins_used": len(coins_used),
              "benchmark_dates": BENCHMARK_DATES, "matched_dates": matched_dates,
              "n_matched": n_matched, "required": P1_MIN_MATCHES}
    result["pass"] = None if not coins_used else bool(n_matched >= P1_MIN_MATCHES)
    if not coins_used:
        result["reason"] = "no mapped-coin 1h data on disk covering dev window"
    return result


def probe_p1_liq_zscore_diag() -> dict:
    """Non-gating corroboration for P1: does the REAL Coinglass daily liq/OI
    z-score (liq_zscore, reused from tradingagents.xsect.liq_mr) also flag
    the benchmark dates on the 8 majors? Independent of the price/volume
    proxy signal used for the actual P1 gate; reported for forensics only."""
    bench = [pd.Timestamp(d, tz="UTC") for d in BENCHMARK_DATES]
    flagged_by: dict[str, set[str]] = {str(b.date()): set() for b in bench}
    coins_used = []
    for coin, sym in COINS.items():
        p = DERIV_DIR / f"{coin}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(p)
        liq_l = d[["liq_long_usd"]].rename(columns={"liq_long_usd": sym})
        liq_s = d[["liq_short_usd"]].rename(columns={"liq_short_usd": sym})
        oi = d[["oi_close"]].rename(columns={"oi_close": sym})
        z = liq_zscore(liq_l, oi)[sym].combine(liq_zscore(liq_s, oi)[sym], max)
        coins_used.append(sym)
        for b in bench:
            if b in z.index and pd.notna(z.loc[b]) and z.loc[b] >= P1_THR:
                flagged_by[str(b.date())].add(sym)
    matched_dates = {d: sorted(s) for d, s in flagged_by.items()}
    return {"thr": P1_THR, "coins_used": coins_used,
            "matched_dates": matched_dates,
            "n_matched": sum(1 for s in flagged_by.values() if s)}


def event_forward_sum(R: pd.DataFrame, trig: pd.DataFrame, H: int) -> np.ndarray:
    """Gross forward return sum(R[t+1..t+H]) at every triggering (t, symbol)
    cell, flattened. rolling(H).sum() at label t+H equals R[t+1..t+H]
    (window of H rows ending at t+H); shift(-H) realigns it back to row t."""
    fwd = R.rolling(H, min_periods=H).sum().shift(-H)
    vals = fwd.to_numpy()[trig.to_numpy()]
    return vals[~np.isnan(vals)]


def probe_p2(smoke: bool) -> dict:
    """Event-study: for each (thr, H) grid cell, mean GROSS forward return
    t+1..t+H over all dev-window triggers (membership-masked, no costs) must
    exceed P2_MIN_RET in at least one cell. `pass: None` when no dev-window
    triggers exist anywhere in the grid (expected under --smoke with a
    partial symbol set)."""
    symbols = load_symbols(smoke)
    universe = json.loads(UNIVERSE_FILE.read_text())
    close, qvol = load_hourly_panel(symbols)
    R = close.pct_change()
    mask = membership_mask_hourly(universe, close.columns.tolist(), close.index)
    dev_lo = pd.Timestamp(DEV[0], tz="UTC")
    row_sel = np.asarray(close.index >= dev_lo)

    cells = []
    best = float("-inf")
    any_events = False
    for thr, H in GRID:
        trig_raw = cascade_triggers(close, qvol, thr=thr)
        trig = trig_raw & mask  # mask triggers before any downstream weights
        trig_dev = pd.DataFrame(trig.to_numpy() & row_sel[:, None],
                                index=trig.index, columns=trig.columns)
        vals = event_forward_sum(R, trig_dev, H)
        n_events = int(trig_dev.to_numpy().sum())
        mean_ret = float(vals.mean()) if len(vals) else float("nan")
        cells.append({"thr": thr, "H": H, "n_events": n_events,
                      "n_events_with_full_forward_window": len(vals),
                      "mean_fwd_ret": mean_ret})
        if len(vals):
            any_events = True
            best = max(best, mean_ret)

    result = {"grid": cells, "n_symbols_loaded": len(close.columns),
              "required": P2_MIN_RET}
    if not any_events:
        result["pass"] = None
        result["best_mean_fwd_ret"] = None
        result["reason"] = "no dev-window triggers in any grid cell (insufficient data)"
    else:
        result["pass"] = bool(best > P2_MIN_RET)
        result["best_mean_fwd_ret"] = best
    return result


def run_probes(smoke: bool) -> dict:
    t0 = time.time()
    p0 = probe_p0()
    print(f"[P0] pass={p0['pass']} corr={p0['corr']} n_overlap_days={p0['n_overlap_days']} "
          f"({time.time() - t0:.1f}s)")

    t1 = time.time()
    p1 = probe_p1()
    print(f"[P1] pass={p1['pass']} n_matched={p1['n_matched']}/{len(BENCHMARK_DATES)} "
          f"coins_used={p1['n_coins_used']} ({time.time() - t1:.1f}s)")

    t1d = time.time()
    p1_diag = probe_p1_liq_zscore_diag()
    print(f"[P1 liq_zscore diag, non-gating] n_matched={p1_diag['n_matched']}/"
          f"{len(BENCHMARK_DATES)} coins_used={len(p1_diag['coins_used'])} "
          f"({time.time() - t1d:.1f}s)")

    t2 = time.time()
    p2 = probe_p2(smoke)
    best = p2.get("best_mean_fwd_ret")
    print(f"[P2] pass={p2['pass']} best_mean_fwd_ret="
          f"{best if best is None else f'{best:.4f}'} n_symbols={p2['n_symbols_loaded']} "
          f"({time.time() - t2:.1f}s)")

    payload = {
        "smoke": bool(smoke),
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "dev_window": list(DEV),
        "runtime_sec": time.time() - t0,
        "p0": p0, "p1": p1, "p1_liq_zscore_diag": p1_diag, "p2": p2,
    }
    payload["stop"] = bool((p1.get("pass") is False) or (p2.get("pass") is False))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "probes.json", "w") as f:
        json.dump(_sanitize(payload), f, indent=1, allow_nan=False, default=str)
    print(f"\nwrote {OUT_DIR / 'probes.json'} (smoke={smoke})")
    print(f"total runtime: {time.time() - t0:.1f}s")

    if smoke:
        return payload  # never a registered verdict; never exits nonzero
    if payload["stop"]:
        print("STOP: P1 or P2 failed the registered gate -- see probes.json",
              file=sys.stderr)
        sys.exit(1)
    return payload


def run_grid() -> None:
    raise NotImplementedError("dev grid (thr x H, placebos, DSR) is Task 9")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--probes-only", action="store_true", help="run probes P0-P2 only")
    mode.add_argument("--grid", action="store_true", help="run the dev grid (Task 9)")
    mode.add_argument("--all", action="store_true", help="probes then grid (Task 9)")
    ap.add_argument("--smoke", action="store_true",
                    help="restrict to symbols present on disk; never a registered verdict")
    args = ap.parse_args()

    if args.probes_only:
        run_probes(args.smoke)
        return
    # --grid / --all both require the grid runner, not yet implemented (Task 9)
    if args.all:
        run_probes(args.smoke)
    run_grid()


if __name__ == "__main__":
    main()
