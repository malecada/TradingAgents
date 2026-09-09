"""liq_fade_i1 dev runner: probes P0-P2 (Task 8), dev grid (Task 9). Ledger:
liq_fade_i1. Gates: data/rebuild/gates.json["liq_fade_i1"].
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

from tradingagents.rebuild.ledger import DEFAULT_LEDGER, log_trial  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.xsect.liq_fade import (  # noqa: E402
    cascade_triggers, event_weights_hourly, run_hourly_portfolio, sharpe_daily,
)
from tradingagents.xsect.liq_mr import liq_zscore  # noqa: E402
from tradingagents.xsect.portfolio import maxdd, rank_placebo_pvalue  # noqa: E402

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

# ── Task 9: dev grid ─────────────────────────────────────────────────────────
GRID_GATE = {"net_sr_min": 1.0, "placebo_p_max": 0.05, "dsr_min": 0.9}
N_PLACEBO = 500
N_PLACEBO_SMOKE = 20      # --grid-smoke only, never a registered verdict
COST_BPS = 10.0
STRESS_COST_BPS = 20.0    # sr_stress_20bps: reported, NOT gated
RF_ANNUAL = 0.045
W_PER = 0.1
CAP = 1.0
PLACEBO_SHIFT_MIN_OFFSET = 24   # bars, per side


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
    BTCUSDT close pct_change over the 2021-01-01..MAX_LOAD_END overlap.
    Both the 1h and daily series are clamped to [2021-01-01, MAX_LOAD_END]
    BEFORE resampling/pct_change -- the daily store extends to the present
    and the 1h tail keeps advancing, so an unclamped window would pull ~9
    months of sealed holdout data into a probe that is supposed to run
    pre-backtest. `pass: None` means the overlap couldn't be computed yet
    (insufficient 1h history on disk -- expected mid-fetch / under --smoke),
    never a false pass or fail."""
    p1h = KLINES_1H_DIR / "BTCUSDT.parquet"
    pdaily = KLINES_DAILY_DIR / "BTCUSDT.parquet"
    if not p1h.exists() or not pdaily.exists():
        return {"pass": None, "reason": "BTCUSDT store(s) missing", "corr": None,
                "n_overlap_days": 0}
    lo = pd.Timestamp("2021-01-01", tz="UTC")
    cap = pd.Timestamp(MAX_LOAD_END, tz="UTC")  # sealed-holdout guard -- see docstring
    d1h = pd.read_parquet(p1h)
    d1h = d1h.loc[(d1h.index >= lo) & (d1h.index <= cap)]
    daily_from_1h = d1h["close"].resample("1D").last().pct_change(fill_method=None)
    dd = pd.read_parquet(pdaily)
    dd = dd.loc[(dd.index >= lo) & (dd.index <= cap)]
    daily_store_ret = dd["close"].pct_change(fill_method=None)
    a = daily_from_1h[(daily_from_1h.index >= lo) & (daily_from_1h.index <= cap)]
    b = daily_store_ret.reindex(a.index)
    valid = a.notna() & b.notna()
    n = int(valid.sum())
    if n < 2:
        return {"pass": None, "reason": "insufficient overlap (1h fetch incomplete)",
                "corr": None, "n_overlap_days": n}
    corr = float(np.corrcoef(a[valid].to_numpy(), b[valid].to_numpy())[0, 1])
    return {"pass": bool(corr > P0_MIN_CORR), "corr": corr, "n_overlap_days": n,
            "required_corr": P0_MIN_CORR,
            "window": [str(lo.date()), str(cap.date())]}


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
    R = close.pct_change(fill_method=None)
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


def _assert_data_complete() -> None:
    """Hard guard for non-smoke probe runs, checked BEFORE any probe computes.

    Without this, a premature real run (bulk 1h fetch still in progress)
    would silently write a smoke:false probes.json off a partial universe --
    a file that LOOKS like a registered verdict but isn't backed by the full
    217-symbol universe, and is indistinguishable from a genuine full-data
    run downstream. Requires: every symbol in liq_fade_symbols.txt present
    on disk under data/xsect/klines_1h/, AND BTCUSDT 1h coverage spanning
    <= 2020-06-02 through >= 2025-04-14 (the registered warmup start through
    just short of the sealed holdout). Never bypassed except via --smoke,
    which never claims a registered verdict in the first place.
    """
    required = [s.strip() for s in SYMBOLS_FILE.read_text().splitlines() if s.strip()]
    on_disk = {p.stem for p in KLINES_1H_DIR.glob("*.parquet")}
    missing = sorted(s for s in required if s not in on_disk)
    if missing:
        raise RuntimeError(
            f"data-completeness guard FAILED: {len(missing)}/{len(required)} symbols "
            f"from {SYMBOLS_FILE} missing under {KLINES_1H_DIR} (e.g. {missing[:5]}); "
            "refusing a non-smoke probe run on a partial universe. Use --smoke for a "
            "partial-data sanity check, or wait for the bulk 1h fetch to finish.")
    p = KLINES_1H_DIR / "BTCUSDT.parquet"
    if not p.exists():
        raise RuntimeError(f"data-completeness guard FAILED: {p} missing")
    d = pd.read_parquet(p)
    if d.empty:
        raise RuntimeError(f"data-completeness guard FAILED: {p} is empty")
    first, last = d.index.min(), d.index.max()
    need_first = pd.Timestamp("2020-06-02", tz="UTC")
    need_last = pd.Timestamp("2025-04-14", tz="UTC")
    if first > need_first or last < need_last:
        raise RuntimeError(
            f"data-completeness guard FAILED: BTCUSDT 1h coverage {first.date()} -> "
            f"{last.date()} does not span the required <= {need_first.date()} -> "
            f">= {need_last.date()}; refusing a non-smoke probe run before the fetch "
            "is complete.")


def run_probes(smoke: bool) -> dict:
    if not smoke:
        _assert_data_complete()
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


def _assert_probes_passed(probes_path: Path | None = None) -> dict:
    """Hard guard for a non-smoke grid run: refuses to touch real data unless
    a REGISTERED (smoke=False) probes.json exists with P1 and P2 both passing.
    Checked before _assert_data_complete() so a stale/failing/missing probes
    file is reported first (it is the cheaper, more specific failure mode).
    probes_path is injectable for tests (tmp_path monkeypatch); defaults to
    the real OUT_DIR/probes.json."""
    path = probes_path if probes_path is not None else (OUT_DIR / "probes.json")
    if not path.exists():
        raise RuntimeError(
            f"grid refuses to run: {path} not found -- run "
            "`python scripts/liq_fade_dev.py --probes-only` (no --smoke) first; "
            "P1 and P2 must pass before the dev grid touches real data.")
    payload = json.loads(path.read_text())
    p1 = payload.get("p1", {}) or {}
    p2 = payload.get("p2", {}) or {}
    ok = (payload.get("smoke") is False and p1.get("pass") is True
          and p2.get("pass") is True)
    if not ok:
        raise RuntimeError(
            f"grid refuses to run: {path} is not a passing registered verdict "
            f"(smoke={payload.get('smoke')!r} p1.pass={p1.get('pass')!r} "
            f"p2.pass={p2.get('pass')!r}); re-run --probes-only without --smoke "
            "and confirm P1/P2 pass before running the grid.")
    return payload


def _unique_config_hashes(ledger_path: Path | None = None) -> int:
    path = ledger_path if ledger_path is not None else DEFAULT_LEDGER
    if not Path(path).exists():
        return 0
    seen = set()
    with open(path) as f:
        for line in f:
            if line.strip():
                seen.add(json.loads(line)["config_hash"])
    return len(seen)


def _shift_triggers(trig: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Placebo family A: per symbol, circular-shift the (already
    membership-masked, dev-window-restricted) trigger column by a uniform
    random offset in [24, N-24] bars. Preserves each symbol's exact event
    count (a roll is a permutation) and its temporal clustering structure;
    destroys calendar alignment with the realized market path."""
    n = len(trig)
    lo = PLACEBO_SHIFT_MIN_OFFSET
    hi = n - PLACEBO_SHIFT_MIN_OFFSET
    if hi <= lo:
        raise ValueError(f"trigger panel too short ({n} bars) for a "
                         f"[{lo}, {n - lo}] shift offset")
    out = {}
    for col in trig.columns:
        k = int(rng.integers(lo, hi + 1))   # inclusive of N-24
        out[col] = np.roll(trig[col].to_numpy(), k)
    return pd.DataFrame(out, index=trig.index, columns=trig.columns)


def _redraw_random_triggers(trig: pd.DataFrame, mask: pd.DataFrame,
                            rng: np.random.Generator) -> pd.DataFrame:
    """Placebo family B: per symbol, redraw n_events(symbol) uniform bar
    positions among eligible bars -- bars where the symbol is
    membership-eligible in the dev window (`mask`, same columns/index as
    `trig`). Count-matched per symbol by construction (redraw size ==
    real n_events for that symbol; symbols with 0 real events get an
    all-False placebo column, never gaining spurious events)."""
    T = trig.to_numpy()
    M = mask.to_numpy()
    out = np.zeros_like(T)
    for j, col in enumerate(trig.columns):
        n_ev = int(T[:, j].sum())
        if n_ev == 0:
            continue
        eligible = np.nonzero(M[:, j])[0]
        assert len(eligible) >= n_ev, (
            f"{col}: {n_ev} real events but only {len(eligible)} eligible bars "
            "-- trig-implies-mask invariant violated")
        pick = rng.choice(eligible, size=n_ev, replace=False)
        out[pick, j] = True
    return pd.DataFrame(out, index=trig.index, columns=trig.columns)


def _synthetic_grid_smoke_panel(n_symbols: int = 6, n_bars: int = 24 * 120,
                                seed: int = 7):
    """Tiny fully-synthetic hourly (close, quote_volume, universe) panel for
    --grid-smoke: deterministic, always available regardless of the real 1h
    fetch's progress. Each symbol gets a handful of injected cascade-like
    shocks (sharp negative return + volume spike) so cascade_triggers has
    something to find and the placebo machinery is exercised non-trivially."""
    idx = pd.date_range("2021-01-01", periods=n_bars, freq="1h", tz="UTC")
    rng = np.random.default_rng(seed)
    cols = [f"SMOKE{i}USDT" for i in range(n_symbols)]
    close = pd.DataFrame(index=idx, columns=cols, dtype=float)
    qvol = pd.DataFrame(index=idx, columns=cols, dtype=float)
    for c in cols:
        rets = rng.normal(0.0, 0.003, n_bars)
        vol = rng.lognormal(10.0, 0.3, n_bars)
        n_shocks = max(3, n_bars // 500)
        shock_bars = rng.choice(n_bars, size=n_shocks, replace=False)
        rets[shock_bars] -= rng.uniform(0.02, 0.05, size=n_shocks)
        vol[shock_bars] *= rng.uniform(4.0, 8.0, size=n_shocks)
        close[c] = 100.0 * np.exp(np.cumsum(rets))
        qvol[c] = vol
    universe = {"2021-01-01": cols}
    return close, qvol, universe


def _grid_core(close: pd.DataFrame, qvol: pd.DataFrame, universe: dict,
               dev_lo: pd.Timestamp, dev_hi: pd.Timestamp, n_placebo: int,
               smoke: bool, n_trials_before: int = 0) -> dict:
    """Shared 6-config grid loop used by both the real and --grid-smoke
    paths. Only I/O (ledger append, dev_results.json write) is gated on
    `smoke`; the computation is identical."""
    t_start = time.time()
    R = close.pct_change(fill_method=None)
    mask_full = membership_mask_hourly(universe, close.columns.tolist(), close.index)
    row_sel = (close.index >= dev_lo) & (close.index <= dev_hi)

    rng = np.random.default_rng(48)  # single generator, threaded across the
    # whole grid (all 6 configs x both placebo families) in GRID order, per spec
    results = []
    net_by_cfg = {}
    for cfg_i, (thr, H) in enumerate(GRID):
        t_cfg = time.time()
        trig_raw = cascade_triggers(close, qvol, thr=thr)
        trig_masked = trig_raw & mask_full
        trig_dev = trig_masked.loc[row_sel]
        R_dev = R.loc[row_sel]
        mask_dev = mask_full.loc[row_sel]

        # Perf: restrict to trig-active columns only. Inactive columns are
        # provably zero-contribution to weights/PnL for BOTH the real config
        # AND every placebo draw (family A: rolling an all-False column stays
        # all-False; family B: redrawing 0 events draws nothing) -- so this
        # never changes any reported metric, only speeds up the O(n*k)
        # event_weights_hourly loop, which is the placebo hot path.
        active_cols = trig_dev.columns[trig_dev.to_numpy().any(axis=0)].tolist()
        trig_active = trig_dev[active_cols]
        R_active = R_dev[active_cols]
        mask_active = mask_dev[active_cols]

        n_events = int(trig_active.to_numpy().sum())

        W_real = event_weights_hourly(trig_active, H, w_per=W_PER, cap=CAP)
        net_real = run_hourly_portfolio(W_real, R_active, cost_bps=COST_BPS,
                                        rf_annual=RF_ANNUAL)
        real_sr = sharpe_daily(net_real)
        net_stress = run_hourly_portfolio(W_real, R_active, cost_bps=STRESS_COST_BPS,
                                          rf_annual=RF_ANNUAL)
        sr_stress = sharpe_daily(net_stress)

        t_pb0 = time.time()
        shift_srs, rand_srs = [], []
        for _ in range(n_placebo):
            trig_p = _shift_triggers(trig_active, rng)
            Wp = event_weights_hourly(trig_p, H, w_per=W_PER, cap=CAP)
            netp = run_hourly_portfolio(Wp, R_active, cost_bps=COST_BPS, rf_annual=RF_ANNUAL)
            shift_srs.append(sharpe_daily(netp))
        for _ in range(n_placebo):
            trig_p = _redraw_random_triggers(trig_active, mask_active, rng)
            Wp = event_weights_hourly(trig_p, H, w_per=W_PER, cap=CAP)
            netp = run_hourly_portfolio(Wp, R_active, cost_bps=COST_BPS, rf_annual=RF_ANNUAL)
            rand_srs.append(sharpe_daily(netp))
        pb_elapsed = time.time() - t_pb0
        if cfg_i == 0 and not smoke:
            projected_sec = pb_elapsed * len(GRID)
            if projected_sec > 6 * 3600:
                print(f"[WARN] projected placebo wall-clock {projected_sec / 3600:.1f}h "
                      f"> 6h budget even after active-column reduction "
                      f"({len(active_cols)}/{len(trig_dev.columns)} cols); draws are "
                      "NOT reduced per spec.", file=sys.stderr)

        p_shift = rank_placebo_pvalue(real_sr, shift_srs)
        p_rand = rank_placebo_pvalue(real_sr, rand_srs)
        placebo_p_worse = max(p_shift, p_rand)

        maxdd_v = maxdd(net_real)
        # events_per_coin_month: n_events / total membership coin-months in
        # the dev window (coin-days with any hourly membership, summed across
        # symbols, / 30.44 avg days-per-month) -- normalizes trigger density
        # by exposure, not by raw calendar time.
        coin_days = float(mask_dev.groupby(
            mask_dev.index.tz_convert("UTC").normalize()).any().to_numpy().sum())
        coin_months = coin_days / 30.44
        events_per_coin_month = (n_events / coin_months) if coin_months > 0 else float("nan")
        n_days_dev = max(1, (trig_dev.index[-1] - trig_dev.index[0]).days + 1)
        # annual_turnover: total |delta W| summed over all bars & symbols,
        # annualized by (365 / calendar days spanned), halved because a
        # round-trip (open + close) registers twice in |delta W| -- this
        # reports round-trip position changes per year, not raw weight-change
        # volume.
        dW_abs_sum = float(W_real.diff().fillna(0.0).abs().to_numpy().sum())
        annual_turnover = dW_abs_sum * 365.0 / n_days_dev / 2.0
        active_daily = (W_real.abs().sum(axis=1) > 0).groupby(
            W_real.index.tz_convert("UTC").normalize()).any()
        pct_days_active = float(active_daily.mean()) if len(active_daily) else 0.0
        mean_gross_turnover = float(W_real.diff().fillna(0.0).abs().sum(axis=1).mean())
        boundary_open_events = int((W_real.iloc[-1] > 0).sum()) if len(W_real) else 0
        fade = {}
        for h in (1, 6, 24):
            vals = event_forward_sum(R_active, trig_active, h)
            fade[f"mean_fade_ret_{h}h"] = float(vals.mean()) if len(vals) else float("nan")

        # cfg holds ONLY frozen design constants -- anything runtime-derived
        # (e.g. which columns happened to be active on disk) must NOT enter
        # config_hash, or a rerun with one different active symbol mints a
        # new hash and silently inflates cross-experiment n_trials forever
        # (see tradingagents/rebuild/ledger.py docstring). n_symbols_active
        # is reported in metrics instead.
        cfg = {"thr": thr, "H": H, "w_per": W_PER, "cap": CAP, "cost_bps": COST_BPS,
               "rf_annual": RF_ANNUAL}
        metrics = {"net_sr": real_sr, "maxdd": maxdd_v, "n_events": n_events,
                   "events_per_coin_month": events_per_coin_month,
                   "annual_turnover": annual_turnover,
                   "pct_days_active": pct_days_active,
                   "mean_gross_turnover": mean_gross_turnover,
                   "sr_stress_20bps": sr_stress,
                   "placebo_p_shiftfam": p_shift, "placebo_p_randfam": p_rand,
                   "placebo_p_worse": placebo_p_worse,
                   "boundary_open_events": boundary_open_events,
                   "n_symbols_active": len(active_cols),
                   "n_days": len(net_real), **fade}

        if not smoke:
            log_trial("liq_fade_i1", cfg,
                      (str(dev_lo.date()), str(pd.Timestamp(dev_hi).date())), metrics)

        net_by_cfg[(thr, H)] = net_real
        results.append({"config": cfg, "metrics": metrics,
                        "net_sr_pass": bool(real_sr >= GRID_GATE["net_sr_min"]),
                        "placebo_pass": bool(placebo_p_worse <= GRID_GATE["placebo_p_max"])})
        print(f"thr={thr} H={H}: SR={real_sr:+.3f} p_shift={p_shift:.3f} "
              f"p_rand={p_rand:.3f} ev={n_events} act_cols={len(active_cols)} "
              f"({time.time() - t_cfg:.1f}s)")

    # DSR computed only for the best config by net_sr, per spec (not all 6)
    best = max(results, key=lambda r: r["metrics"]["net_sr"])
    n_trials = n_trials_before + len(GRID)
    cand = net_by_cfg[(best["config"]["thr"], best["config"]["H"])].to_numpy()
    # DSR is best-effort diagnostic, not a hard requirement to land the run:
    # deflated_sharpe_ratio raises ValueError on se_sr<=0 (degenerate/negative
    # variance estimate). If that fires, ledger rows for all 6 configs are
    # already written -- dev_results.json must still land, just with
    # dsr=nan and the gate failing on that config (never silently pass).
    dsr = float("nan")
    if len(cand) >= 2 and cand.std(ddof=1) > 0:
        var_sr = variance_of_sr(cand)
        se_sr = float(np.sqrt(var_sr))
        sr_perbar = float(cand.mean() / cand.std(ddof=1))
        if se_sr > 0.0:
            try:
                dsr = deflated_sharpe_ratio(sr_perbar, expected_max_sharpe(n_trials, var_sr), se_sr)
            except ValueError as e:
                print(f"[WARN] DSR computation failed ({e}); dsr=nan, dsr_pass=False",
                      file=sys.stderr)
                dsr = float("nan")
    dsr_pass = bool(np.isfinite(dsr) and dsr >= GRID_GATE["dsr_min"])
    best["metrics"]["dsr"] = dsr
    best["metrics"]["n_trials_at_eval"] = n_trials
    best["dsr_pass"] = dsr_pass
    best["gate_pass"] = bool(best["net_sr_pass"] and best["placebo_pass"] and dsr_pass)
    selected = best["config"] if best["gate_pass"] else None

    payload = {"smoke": bool(smoke),
               "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
               "dev_window": [str(dev_lo), str(dev_hi)],
               "gate": GRID_GATE, "results": results,
               "best_config": best["config"], "selected": selected,
               "n_trials_at_eval": n_trials,
               "total_runtime_sec": time.time() - t_start}

    if not smoke:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUT_DIR / "dev_results.json", "w") as f:
            json.dump(_sanitize(payload), f, indent=1, allow_nan=False, default=str)
        print(f"\nwrote {OUT_DIR / 'dev_results.json'}")
    print(f"selected: {json.dumps(_sanitize(selected)) if selected else 'NONE'}")
    print(f"total runtime: {time.time() - t_start:.1f}s")
    return payload


def _run_grid_real() -> dict:
    _assert_probes_passed()
    _assert_data_complete()
    n_trials_before = _unique_config_hashes()
    symbols = load_symbols(smoke=False)
    universe = json.loads(UNIVERSE_FILE.read_text())
    close, qvol = load_hourly_panel(symbols)   # WARMUP_START .. DEV[1]
    dev_lo = pd.Timestamp(DEV[0], tz="UTC")
    dev_hi = pd.Timestamp(DEV[1], tz="UTC") + pd.Timedelta(hours=23)
    print(f"[grid] {len(symbols)} symbols loaded, dev window "
          f"{dev_lo.date()}..{dev_hi.date()}, n_trials_before={n_trials_before}")
    return _grid_core(close, qvol, universe, dev_lo, dev_hi, N_PLACEBO,
                      smoke=False, n_trials_before=n_trials_before)


def _run_grid_smoke() -> dict:
    close, qvol, universe = _synthetic_grid_smoke_panel()
    dev_lo = close.index[24 * 30]   # skip a synthetic "warmup" month
    dev_hi = close.index[-1]
    print(f"[grid --grid-smoke] synthetic panel: {len(close.columns)} symbols, "
          f"{len(close)} bars, dev {dev_lo}..{dev_hi} -- NOT a registered verdict")
    return _grid_core(close, qvol, universe, dev_lo, dev_hi, N_PLACEBO_SMOKE,
                      smoke=True, n_trials_before=0)


def run_grid(smoke: bool = False) -> dict:
    if smoke:
        return _run_grid_smoke()
    return _run_grid_real()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--probes-only", action="store_true", help="run probes P0-P2 only")
    mode.add_argument("--grid", action="store_true", help="run the dev grid (Task 9)")
    mode.add_argument("--all", action="store_true", help="probes then grid (Task 9)")
    ap.add_argument("--smoke", action="store_true",
                    help="probes: restrict to symbols present on disk; never a "
                         "registered verdict")
    ap.add_argument("--grid-smoke", action="store_true",
                    help="grid: tiny synthetic panel, never writes ledger rows or "
                         "dev_results.json; for implementation verification only")
    args = ap.parse_args()

    if args.probes_only:
        run_probes(args.smoke)
        return
    if args.all:
        run_probes(args.smoke)
    run_grid(smoke=args.grid_smoke)


if __name__ == "__main__":
    main()
