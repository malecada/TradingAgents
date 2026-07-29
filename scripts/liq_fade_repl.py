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
