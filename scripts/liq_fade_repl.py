"""liq_fade_r1 -- independent replication of liq_fade_i1 on the band 51-150
universe. Single frozen config, no grid. Gates:
data/rebuild/gates.json["liq_fade_r1"].
Spec: docs/superpowers/specs/2026-07-29-liq-fade-r1-design.md.

Probe order matters: P3 runs FIRST and is blocking. It is the discriminating
control liq_fade_i1 never ran -- long-only on high z_vol WITHOUT the z_ret
crash condition. If the control tracks the primary, the section-49 signal was
generic high-volatility long drift and the lead closes as NEGATIVE-confounded
without the gates ever being evaluated.

The backtest engine tradingagents/xsect/liq_fade.py is imported UNCHANGED --
that is what makes this a replication.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.xsect.liq_fade import (  # noqa: E402
    _roll_z, cascade_triggers, event_weights_hourly, run_hourly_portfolio,
    sharpe_daily,
)

XSECT = PROJECT_ROOT / "data" / "xsect"
SYMBOLS_FILE = XSECT / "liq_fade_r1_symbols.txt"
UNIVERSE_FILE = XSECT / "liq_fade_r1_universe.json"
I1_UNIVERSE_FILE = XSECT / "liq_fade_universe.json"
KLINES_1H_DIR = XSECT / "klines_1h"
KLINES_DAILY_DIR = XSECT / "klines"
OUT_DIR = PROJECT_ROOT / "data" / "rebuild" / "liq_fade_r1"

DEV = ("2021-01-01", "2025-03-31")
WARMUP_START = "2020-06-01"
MAX_LOAD_END = "2025-04-15"          # sealed-holdout guard, identical to i1

# ── frozen primary config (gates.json liq_fade_r1.primary_config) ────────────
THR = 3.5
H = 48
W_PER = 0.1
CAP = 1.0
COST_BPS = 20.0                      # band-appropriate; i1 used 10.0
RF_ANNUAL = 0.045
Z_WINDOW = 2160
Z_MIN_PERIODS = 1440

# ── P3 blocking control ─────────────────────────────────────────────────────
P3_CONTROL_MAX_NET_SR = 0.5
P3_MIN_SEPARATION = 0.75
GATE = {"net_sr_min": 1.0, "placebo_p_max": 0.05, "dsr_min": 0.9}


def _sanitize(obj):
    if isinstance(obj, float):
        return None if (np.isnan(obj) or np.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize(v) for v in obj]
    return obj


def load_symbols_r1() -> list[str]:
    return [s.strip() for s in SYMBOLS_FILE.read_text().splitlines() if s.strip()]


def membership_mask_hourly(universe: dict, columns: list[str],
                           index: pd.DatetimeIndex) -> pd.DataFrame:
    """Expand a monthly PIT universe dict to an hourly boolean membership mask.
    Semantics identical to scripts/liq_fade_dev.membership_mask_hourly: each
    entry applies from its month start (inclusive) to the bar before the next
    registered month start (exclusive); the last entry extends to the end of
    `index`. Duplicated here rather than imported because scripts/ is not a
    package."""
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
    """Load 1h close/quote_volume wide panels, refusing to read past the sealed
    holdout cap. Missing bars are left NaN, never forward-filled."""
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


def vol_only_triggers(qvol: pd.DataFrame, thr: float, window: int = Z_WINDOW,
                      min_periods: int = Z_MIN_PERIODS) -> pd.DataFrame:
    """P3 control signal: the volume half of cascade_triggers, alone.

    cascade_triggers fires on (z_ret <= -thr) AND (z_vol >= thr). This drops the
    return condition and keeps z_vol >= thr, so it fires on every high-volume
    bar regardless of price direction. Uses the engine's own _roll_z and the
    same log1p transform, so the z-scores are bit-identical to the primary's
    volume leg -- the ONLY difference is the missing return condition.
    """
    z_vol = _roll_z(np.log1p(qvol), window, min_periods)
    return z_vol >= thr


def p3_verdict(primary_sr: float, control_sr: float,
               net_sr_min: float = GATE["net_sr_min"],
               control_max: float = P3_CONTROL_MAX_NET_SR,
               min_sep: float = P3_MIN_SEPARATION) -> dict:
    """Pre-registered P3 decision rule (gates.json liq_fade_r1.probes.P3).

    PASS iff control net SR < control_max AND (primary - control) >= min_sep.

    The separation term is only diagnostic of a confound when the primary is
    itself strong. If the primary does not clear net_sr_min, the verdict is
    plain NEGATIVE on G1 and the confounded label is NOT applied -- a signal
    that never cleared the floor cannot be said to be explained away by
    volatility drift.
    """
    sep = primary_sr - control_sr
    ok = bool(control_sr < control_max and sep >= min_sep)
    if ok:
        return {"pass": True, "verdict": "PASS",
                "reason": f"control SR {control_sr:.3f} < {control_max} and "
                          f"separation {sep:.3f} >= {min_sep}"}
    if primary_sr < net_sr_min:
        return {"pass": False, "verdict": "NEGATIVE",
                "reason": f"primary SR {primary_sr:.3f} below the {net_sr_min} "
                          "floor; confounded label not applicable"}
    return {"pass": False, "verdict": "NEGATIVE-confounded",
            "reason": f"primary SR {primary_sr:.3f} clears the floor but "
                      f"control SR {control_sr:.3f} / separation {sep:.3f} "
                      f"fails (needs < {control_max} and >= {min_sep})"}


BENCHMARK_DATES = ["2021-05-19", "2022-06-13", "2022-11-09", "2024-08-05", "2025-02-03"]
P0_MIN_CORR = 0.99
P1_THR = 2.5
P1_MIN_MATCHES = 4
P2_MIN_RET = 0.0025


def event_forward_sum(R: pd.DataFrame, trig: pd.DataFrame, H: int) -> np.ndarray:
    """Gross forward return sum(R[t+1..t+H]) at every triggering (t, symbol)
    cell, flattened, NaNs dropped. rolling(H).sum() labelled at t+H equals
    R[t+1..t+H]; shift(-H) realigns it back to the trigger row t."""
    fwd = R.rolling(H, min_periods=H).sum().shift(-H)
    vals = fwd.to_numpy()[trig.to_numpy()]
    return vals[~np.isnan(vals)]


def assert_band_data_complete() -> None:
    """Refuse a non-smoke probe run on a partial band universe. Without this a
    premature run writes a smoke:false probes.json off an incomplete symbol
    set -- a file indistinguishable downstream from a genuine full-data
    verdict."""
    required = [s.strip() for s in SYMBOLS_FILE.read_text().splitlines() if s.strip()]
    on_disk = {p.stem for p in KLINES_1H_DIR.glob("*.parquet")}
    missing = sorted(s for s in required if s not in on_disk)
    if missing:
        raise RuntimeError(
            f"band data-completeness guard FAILED: {len(missing)}/{len(required)} "
            f"symbols from {SYMBOLS_FILE} missing under {KLINES_1H_DIR} "
            f"(e.g. {missing[:5]}); refusing a non-smoke run on a partial band.")


def probe_p0() -> dict:
    """Bar-stamp reconciliation on BTCUSDT, identical to liq_fade_i1's P0.
    BTCUSDT is not a band member, but this probe tests the STORE's stamping
    convention, which is shared, so it stays on the reference symbol."""
    p1h = KLINES_1H_DIR / "BTCUSDT.parquet"
    pdaily = KLINES_DAILY_DIR / "BTCUSDT.parquet"
    if not p1h.exists() or not pdaily.exists():
        return {"pass": None, "reason": "BTCUSDT store(s) missing", "corr": None,
                "n_overlap_days": 0}
    lo = pd.Timestamp("2021-01-01", tz="UTC")
    cap = pd.Timestamp(MAX_LOAD_END, tz="UTC")
    d1h = pd.read_parquet(p1h)
    d1h = d1h.loc[(d1h.index >= lo) & (d1h.index <= cap)]
    a = d1h["close"].resample("1D").last().pct_change(fill_method=None)
    dd = pd.read_parquet(pdaily)
    dd = dd.loc[(dd.index >= lo) & (dd.index <= cap)]
    b = dd["close"].pct_change(fill_method=None).reindex(a.index)
    valid = a.notna() & b.notna()
    n = int(valid.sum())
    if n < 2:
        return {"pass": None, "reason": "insufficient overlap", "corr": None,
                "n_overlap_days": n}
    corr = float(np.corrcoef(a[valid].to_numpy(), b[valid].to_numpy())[0, 1])
    return {"pass": bool(corr > P0_MIN_CORR), "corr": corr, "n_overlap_days": n,
            "required_corr": P0_MIN_CORR, "window": [str(lo.date()), str(cap.date())]}


def probe_p1(close: pd.DataFrame, qvol: pd.DataFrame) -> dict:
    """Proxy concordance on BAND symbols (liq_fade_i1 used the 8 Coinglass
    majors, all of which are top-50 names and therefore absent here). A
    benchmark date counts as matched if ANY band symbol triggers that UTC day
    at thr=2.5. Registered threshold: >= 4 of 5."""
    trig = cascade_triggers(close, qvol, thr=P1_THR)
    day_any = trig.any(axis=1)
    day_flag = day_any.groupby(day_any.index.normalize()).any()
    matched = {}
    for d in BENCHMARK_DATES:
        ts = pd.Timestamp(d, tz="UTC")
        hit = bool(day_flag.loc[ts]) if ts in day_flag.index else False
        syms = sorted(trig.columns[
            trig.loc[trig.index.normalize() == ts].to_numpy().any(axis=0)
        ].tolist()) if hit else []
        matched[d] = syms
    n_matched = sum(1 for v in matched.values() if v)
    return {"thr": P1_THR, "benchmark_dates": BENCHMARK_DATES,
            "matched_dates": matched, "n_matched": n_matched,
            "required": P1_MIN_MATCHES, "n_symbols": len(trig.columns),
            "pass": bool(n_matched >= P1_MIN_MATCHES)}


def probe_p2(close: pd.DataFrame, qvol: pd.DataFrame, mask: pd.DataFrame) -> dict:
    """Event study at the FROZEN primary config only (no grid to scan). Mean
    gross forward return t+1..t+H over membership-masked dev triggers must
    exceed +25bp."""
    R = close.pct_change(fill_method=None)
    dev_lo = pd.Timestamp(DEV[0], tz="UTC")
    row_sel = np.asarray(close.index >= dev_lo)
    trig = cascade_triggers(close, qvol, thr=THR) & mask
    trig_dev = pd.DataFrame(trig.to_numpy() & row_sel[:, None],
                            index=trig.index, columns=trig.columns)
    vals = event_forward_sum(R, trig_dev, H)
    n_events = int(trig_dev.to_numpy().sum())
    if not len(vals):
        return {"pass": None, "thr": THR, "H": H, "n_events": n_events,
                "mean_fwd_ret": None, "required": P2_MIN_RET,
                "reason": "no dev-window triggers with a full forward window"}
    mean_ret = float(vals.mean())
    return {"pass": bool(mean_ret > P2_MIN_RET), "thr": THR, "H": H,
            "n_events": n_events, "n_events_with_full_forward_window": len(vals),
            "mean_fwd_ret": mean_ret, "required": P2_MIN_RET}


def probe_p3(close: pd.DataFrame, qvol: pd.DataFrame, mask: pd.DataFrame) -> dict:
    """Blocking vol-drift control. Runs the FULL primary config and the
    control through the identical engine path, then applies p3_verdict."""
    R = close.pct_change(fill_method=None)
    dev_lo = pd.Timestamp(DEV[0], tz="UTC")
    dev_hi = pd.Timestamp(DEV[1], tz="UTC") + pd.Timedelta(hours=23)
    row_sel = (close.index >= dev_lo) & (close.index <= dev_hi)

    def _sr(trig_full):
        trig = (trig_full & mask).loc[row_sel]
        R_dev = R.loc[row_sel]
        active = trig.columns[trig.to_numpy().any(axis=0)].tolist()
        if not active:
            return 0.0, 0
        W = event_weights_hourly(trig[active], H, w_per=W_PER, cap=CAP)
        net = run_hourly_portfolio(W, R_dev[active], cost_bps=COST_BPS,
                                   rf_annual=RF_ANNUAL)
        return sharpe_daily(net), int(trig[active].to_numpy().sum())

    primary_sr, n_primary = _sr(cascade_triggers(close, qvol, thr=THR))
    control_sr, n_control = _sr(vol_only_triggers(qvol, thr=THR))
    v = p3_verdict(primary_sr, control_sr)
    return {**v, "primary_net_sr": primary_sr, "control_net_sr": control_sr,
            "separation": primary_sr - control_sr,
            "n_primary_events": n_primary, "n_control_events": n_control,
            "control_max_net_sr": P3_CONTROL_MAX_NET_SR,
            "min_separation": P3_MIN_SEPARATION, "cost_bps": COST_BPS}


def run_probes(smoke: bool) -> dict:
    if not smoke:
        assert_band_data_complete()
    t0 = time.time()
    symbols = load_symbols_r1()
    if smoke:
        on_disk = {p.stem for p in KLINES_1H_DIR.glob("*.parquet")}
        symbols = [s for s in symbols if s in on_disk]
    universe = json.loads(UNIVERSE_FILE.read_text())
    close, qvol = load_hourly_panel(symbols)
    mask = membership_mask_hourly(universe, close.columns.tolist(), close.index)
    print(f"[panel] {len(close.columns)} symbols, {len(close)} bars")

    p3 = probe_p3(close, qvol, mask)
    print(f"[P3] {p3['verdict']} primary={p3['primary_net_sr']:+.3f} "
          f"control={p3['control_net_sr']:+.3f} sep={p3['separation']:+.3f}")
    p0 = probe_p0()
    print(f"[P0] pass={p0['pass']} corr={p0['corr']}")
    p1 = probe_p1(close, qvol)
    print(f"[P1] pass={p1['pass']} n_matched={p1['n_matched']}/{len(BENCHMARK_DATES)}")
    p2 = probe_p2(close, qvol, mask)
    print(f"[P2] pass={p2['pass']} mean_fwd_ret={p2['mean_fwd_ret']}")

    payload = {"smoke": bool(smoke),
               "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
               "dev_window": list(DEV), "n_symbols": len(close.columns),
               "primary_config": {"thr": THR, "H": H, "w_per": W_PER, "cap": CAP,
                                  "cost_bps": COST_BPS, "rf_annual": RF_ANNUAL},
               "p3": p3, "p0": p0, "p1": p1, "p2": p2,
               "runtime_sec": time.time() - t0}
    payload["stop"] = bool(p3.get("pass") is False or p1.get("pass") is False
                           or p2.get("pass") is False)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "probes.json", "w") as f:
        json.dump(_sanitize(payload), f, indent=1, allow_nan=False, default=str)
    print(f"\nwrote {OUT_DIR / 'probes.json'} (smoke={smoke})")

    if smoke:
        return payload
    if payload["stop"]:
        print(f"STOP: probe failure -- verdict {p3['verdict'] if not p3['pass'] else 'P1/P2'}",
              file=sys.stderr)
        sys.exit(1)
    return payload


def assert_probes_passed(path: Path | None = None) -> dict:
    """Entry guard for the primary run: refuses to touch data unless a
    REGISTERED (smoke=False) probes.json exists with P3, P1 and P2 all passing."""
    path = path if path is not None else (OUT_DIR / "probes.json")
    if not path.exists():
        raise RuntimeError(
            f"primary run refuses to start: {path} not found -- run "
            "`uv run python scripts/liq_fade_repl.py --probes-only` first.")
    payload = json.loads(path.read_text())
    ok = (payload.get("smoke") is False
          and (payload.get("p3") or {}).get("pass") is True
          and (payload.get("p1") or {}).get("pass") is True
          and (payload.get("p2") or {}).get("pass") is True)
    if not ok:
        raise RuntimeError(
            f"primary run refuses to start: {path} is not a passing registered "
            f"verdict (smoke={payload.get('smoke')!r} "
            f"p3={(payload.get('p3') or {}).get('pass')!r} "
            f"p1={(payload.get('p1') or {}).get('pass')!r} "
            f"p2={(payload.get('p2') or {}).get('pass')!r})")
    return payload
