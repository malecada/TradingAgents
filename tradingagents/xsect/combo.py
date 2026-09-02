"""combo_c1 — multi-sleeve constant-mix combination engine (pure, no I/O).

Registered 2026-09-02 (data/rebuild/gates.json["combo_c1"], charter
docs/superpowers/specs/2026-09-02-combo-c1-charter.md). Four frozen sleeves
(liq_fade_i1 thr3.5/H48, carry_xs_t1 L30/leg0.2, xs_mom_p1 L28/s0/K10,
value_xs_t1 nvt tercile), each producing a DAILY net simple-return series;
this module aligns, weights, combines and scores them.

Conventions (frozen):
  * every sleeve series is a daily NET SIMPLE return after its own costs/rf;
  * alignment: calendar-day index of the window; a day a sleeve does not
    cover is 0.0 (flat) — the book is a constant-mix of fixed capital weights
    on daily sleeve returns, no cross-sleeve rebalancing cost (stated
    deployment contract);
  * W1: w_i proportional to 1/sd_i, sd_i = dev-window daily SD (ddof=1) of the
    ALIGNED sleeve series; sum w = 1; W2: 0.25 each;
  * Sharpe: sqrt(365) * mean/sd (ddof=1), 0.0 on zero variance;
  * drawdown: on compounded simple returns (cumprod), positive magnitude;
  * per-sleeve contribution: w_i * mean_i (sums to the combined mean);
  * top-name share: pooled per-symbol gross PnL across sleeves,
    max|pnl_s| / sum|pnl_s|;
  * placebos on WEIGHT PATHS (costs/rf re-applied by the sleeve engines):
    family A = per-column independent circular shift within every sleeve
    (house circular_shift_weights semantics, min offset 30 days / 720 bars);
    family B = ONE shared offset in days applied to every sleeve and column
    (x24 for the hourly sleeve), preserving cross-sleeve co-activation.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from tradingagents.xsect.ls_common import sharpe_365


class HoldoutAlreadySpent(RuntimeError):
    """The one-shot verdict file exists — the sealed window has been spent."""


def assert_holdout_unspent(verdict_path: Path) -> None:
    p = Path(verdict_path)
    if p.exists():
        try:
            v = json.loads(p.read_text()).get("verdict")
        except Exception:  # noqa: BLE001 — any content means spent
            v = "?"
        raise HoldoutAlreadySpent(f"{p} exists (verdict={v!r}); the holdout is spent — "
                                  "no re-run, no re-weighting, no second look")


def align_sleeves(series_by_id: dict, index: pd.DatetimeIndex) -> pd.DataFrame:
    """Daily sleeve returns on a common calendar index, 0.0 where uncovered."""
    cols = {}
    for sid in sorted(series_by_id):
        s = series_by_id[sid].dropna()
        extra = s.index.difference(index)
        if len(extra):
            raise ValueError(f"sleeve {sid!r} has {len(extra)} days outside the window "
                             f"(first {extra[0]})")
        cols[sid] = s.reindex(index).fillna(0.0).astype(float)
    return pd.DataFrame(cols, index=index)


def inverse_vol_weights(dev: pd.DataFrame) -> dict:
    sd = dev.std(ddof=1)
    if (sd <= 0).any() or sd.isna().any():
        bad = list(sd.index[(sd <= 0) | sd.isna()])
        raise ValueError(f"zero/undefined dev volatility for sleeves {bad}")
    inv = 1.0 / sd
    w = inv / inv.sum()
    return {k: float(v) for k, v in w.items()}


def equal_weights(ids) -> dict:
    ids = list(ids)
    return {k: 1.0 / len(ids) for k in ids}


def _check_weights(df: pd.DataFrame, weights: dict) -> np.ndarray:
    if set(weights) != set(df.columns):
        raise ValueError(f"weights {sorted(weights)} != sleeves {sorted(df.columns)}")
    w = np.array([weights[c] for c in df.columns], dtype=float)
    if not np.isclose(w.sum(), 1.0, atol=1e-12):
        raise ValueError(f"capital weights must sum to 1 (got {w.sum()})")
    return w


def combine(df: pd.DataFrame, weights: dict) -> pd.Series:
    w = _check_weights(df, weights)
    return pd.Series(df.to_numpy() @ w, index=df.index)


def sleeve_contributions(df: pd.DataFrame, weights: dict) -> dict:
    _check_weights(df, weights)
    return {c: float(weights[c] * df[c].mean()) for c in df.columns}


def top_name_share(pnl_by_sleeve: dict) -> tuple:
    pooled: dict = {}
    for _sid, by_name in pnl_by_sleeve.items():
        for name, v in by_name.items():
            pooled[name] = pooled.get(name, 0.0) + float(v)
    if not pooled:
        return None, 0.0
    denom = sum(abs(v) for v in pooled.values())
    if denom == 0:
        return None, 0.0
    name = max(pooled, key=lambda k: abs(pooled[k]))
    return name, abs(pooled[name]) / denom


def maxdd_simple(series: pd.Series) -> float:
    wealth = (1.0 + series.astype(float)).cumprod()
    dd = wealth / wealth.cummax() - 1.0
    return float(-dd.min()) if len(dd) else 0.0


def sharpe(series: pd.Series) -> float:
    return sharpe_365(series)


# ── placebo weight-path shifts ──────────────────────────────────────────────

def indep_shift(W: pd.DataFrame, rng: np.random.Generator, min_shift: int) -> pd.DataFrame:
    """Family A: per-column independent circular roll, offset in [min_shift, n-min_shift)."""
    n = len(W)
    if n <= 2 * min_shift:
        raise ValueError(f"frame too short ({n}) for min_shift {min_shift}")
    out = {}
    for col in W.columns:
        k = int(rng.integers(min_shift, n - min_shift))
        out[col] = np.roll(W[col].to_numpy(), k)
    return pd.DataFrame(out, index=W.index, columns=W.columns)


def shared_shift(W: pd.DataFrame, offset_days: int) -> pd.DataFrame:
    """Family B: one shared offset (in DAYS) for every column; hourly frames roll 24x."""
    step = pd.infer_freq(W.index[:3]) if len(W) >= 3 else "D"
    per_day = 24 if (step is not None and step.lower().startswith("h")) else 1
    k = int(offset_days) * per_day
    return pd.DataFrame(np.roll(W.to_numpy(), k, axis=0), index=W.index, columns=W.columns)


def draw_shared_offset(rng: np.random.Generator, n_days: int, min_shift: int = 30) -> int:
    return int(rng.integers(min_shift, n_days - min_shift))


def rank_placebo_pvalue(real: float, placebo: list) -> float:
    ge = sum(1 for p in placebo if p >= real)
    return (1 + ge) / (len(placebo) + 1)


# ── gates ───────────────────────────────────────────────────────────────────

def gate_verdict(m: dict, g: dict) -> dict:
    """All seven registered checks; every one must hold.

    m: sr_h, sr_dev, placebo_p_worse, min_contrib, maxdd, top_name_share,
       convention_swap_flips.
    g: sr_ratio_min, sr_abs_min, placebo_p_max, sleeve_contribution_min,
       maxdd_max, top_name_share_max.
    """
    checks = {
        "sr_ratio": bool(m["sr_h"] >= g["sr_ratio_min"] * m["sr_dev"]),
        "sr_abs": bool(m["sr_h"] >= g["sr_abs_min"]),
        "same_sign": bool(np.sign(m["sr_h"]) == np.sign(m["sr_dev"]) and m["sr_h"] != 0),
        "placebo": bool(m["placebo_p_worse"] < g["placebo_p_max"]),
        "sleeve_contribution": bool(m["min_contrib"] >= g["sleeve_contribution_min"]),
        "maxdd": bool(m["maxdd"] <= g["maxdd_max"]),
        "concentration": bool(m["top_name_share"] <= g["top_name_share_max"]),
        "convention_swap": bool(not m["convention_swap_flips"]),
    }
    return {"pass": all(checks.values()), "checks": checks}
