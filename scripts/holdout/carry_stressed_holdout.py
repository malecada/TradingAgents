#!/usr/bin/env python
"""Carry audit pass 2: execution-realism cost waterfall (the stressed sleeve).

Takes the as-built always-on carry sleeve (short 1x perp + long 1x spot, equal
notional both legs, 50/50 BTC/ETH; same construction as pass 1
scripts/carry_audit_timing.py) and applies four explicit cost layers on top,
in a fixed cumulative order:

    as_built -> +turnover -> +rebalance -> +margin_cost -> +boundary_basis = stressed

Every parameter is written to data/rebuild/carry_audit/costs.json alongside the
SR after each cumulative layer. The net stressed daily return series is the
canonical input for downstream tasks (C4 / Phase 3) and lives in
data/rebuild/carry_audit/sleeve_stressed_daily.csv (columns: date, btc, eth,
sleeve; sleeve = 0.5*btc + 0.5*eth).

The published 8.24 (THESIS Section 32) is an upper bound that omits execution
frictions; this pass measures how much survives.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# H2: copy lives in scripts/holdout/ (one level deeper than the original in
# scripts/), so PROJECT_ROOT needs one more .parent to reach the repo root.
# Mechanical path-resolution fix only — no economic/cost parameter changes.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.carry_blend_p4 import fetch_spot_close  # noqa: E402
from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.strategies.carry_sleeve import (  # noqa: E402
    compute_price_pnl,
    fetch_perp_mark,
    funding_daily_income,
)

ANN = np.sqrt(252)  # thesis-canonical annualization (matches pass 1)
# H2 HOLDOUT ONE-SHOT: authorized window edit (START/END -> holdout bounds).
START, END = "2025-04-01", "2026-07-01"
SYMBOLS = ("BTCUSDT", "ETHUSDT")

# ── Cost parameters (binding, from task-C2-brief.md) ────────────────────────
SPOT_TAKER = 0.0010          # spot taker fee, per side
PERP_TAKER = 0.0004          # perp taker fee, per side
SPREAD = 0.0001              # half-spread cost, per side, per leg
# One SIDE (open OR close) touches both legs: spot leg (taker+spread) + perp leg
# (taker+spread). An inception open or a final-exit close is one side each.
OPEN_COST = SPOT_TAKER + SPREAD + PERP_TAKER + SPREAD  # = 0.0016 of notional
# A rebalance re-trades the drift notional round-trip (out and back).
ROUNDTRIP_COST = 2.0 * OPEN_COST                        # = 0.0032 of notional
DRIFT_THRESHOLD = 0.20       # rebalance when |spot_val - perp_val| > 20% target
TARGET_NOTIONAL = 1.0        # per-leg target (returns are quoted per 1.0 notional)
RF_ANNUAL = 0.045            # risk-free opportunity cost on tied-up margin
RF_DAILY = (1.0 + RF_ANNUAL) ** (1.0 / 252.0) - 1.0
MARGIN_FRACTION = 1.0 / 3.0  # leverage <= 3x -> margin >= 1/3 of perp notional


def sr(x: pd.Series) -> float:
    """Annualized Sharpe (mean/std * sqrt(252)); matches pass 1's sr()."""
    x = x.dropna()
    return float(x.mean() / x.std() * ANN) if x.std() > 0 else 0.0


def build_symbol(sym: str) -> dict:
    """Fetch the sleeve legs for one symbol and return as-built + cost inputs.

    Returns a dict with the as-built daily return series (funding + hedge P&L,
    per 1.0 notional) and the per-leg daily returns needed for drift tracking,
    all aligned to the as-built (funding) index.
    """
    # H2 HOLDOUT ONE-SHOT: authorized window edit — this hardcoded pair is the
    # ACTUAL fetch window (module START/END above is metadata/ledger only), so it
    # must also be set to the holdout bounds for the sleeve to run on holdout data.
    start, end = date(2025, 4, 1), date(2026, 7, 1)
    funding = funding_daily_income(sym, start, end)
    spot = fetch_spot_close(sym, start, end)
    perp = fetch_perp_mark(sym, start, end)
    hedge = compute_price_pnl(spot, perp)
    asbuilt = (funding + hedge.reindex(funding.index)).dropna()
    idx = asbuilt.index
    spot_ret = spot.astype(float).pct_change().reindex(idx).fillna(0.0)
    perp_ret = perp.astype(float).pct_change().reindex(idx).fillna(0.0)
    return {
        "asbuilt": asbuilt,
        "idx": idx,
        "spot_ret": spot_ret.to_numpy(dtype=float),
        "perp_ret": perp_ret.to_numpy(dtype=float),
    }


def turnover_deductions(idx) -> np.ndarray:
    """Inception open + final exit close, one side each (both legs)."""
    d = np.zeros(len(idx))
    if len(idx) == 0:
        return d
    d[0] += OPEN_COST      # inception open
    d[-1] += OPEN_COST     # final exit close
    return d


def rebalance_deductions(
    spot_ret: np.ndarray, perp_ret: np.ndarray, roundtrip_cost: float,
) -> tuple[np.ndarray, int]:
    """Drift-triggered rebalance costs.

    Compound each leg's equity value with its own daily return since the last
    rebalance; when the two legs' values diverge by more than
    DRIFT_THRESHOLD * TARGET_NOTIONAL, charge the round-trip cost on the drift
    notional (|spot_val - perp_val|) that day and reset both legs to target.

    The long-spot leg compounds with +spot_ret; the SHORT-perp leg compounds
    with -perp_ret (a short loses equity as the perp rises). This is the
    drift-generating reading: modelling both legs with the same-sign price
    return leaves spot_val ~= perp_val (perp tracks spot) so drift never
    reaches 20% and the layer is trivially zero. See costs.json "notes".
    """
    n = len(spot_ret)
    d = np.zeros(n)
    spot_val = TARGET_NOTIONAL
    perp_val = TARGET_NOTIONAL
    n_rebal = 0
    for i in range(n):
        spot_val *= (1.0 + spot_ret[i])
        perp_val *= (1.0 - perp_ret[i])
        drift = abs(spot_val - perp_val)
        if drift > DRIFT_THRESHOLD * TARGET_NOTIONAL:
            d[i] += roundtrip_cost * drift
            n_rebal += 1
            spot_val = TARGET_NOTIONAL
            perp_val = TARGET_NOTIONAL
    return d, n_rebal


def margin_deductions(idx, rf_daily: float) -> np.ndarray:
    """Constant daily opportunity cost on the margin fraction of perp notional."""
    return np.full(len(idx), rf_daily * MARGIN_FRACTION * TARGET_NOTIONAL)


def apply_layers(sym_data: dict, params: dict) -> dict:
    """Apply the four cost layers cumulatively to one symbol's as-built series.

    Returns dict of layer_name -> stressed-so-far daily return Series, plus the
    per-symbol rebalance count. ``params`` carries the (possibly zeroed) cost
    magnitudes so the all-zero sanity check can reuse this exact path.
    """
    asbuilt = sym_data["asbuilt"]
    idx = sym_data["idx"]

    turn = turnover_deductions(idx) * params["turnover_on"]
    reb, n_rebal = rebalance_deductions(
        sym_data["spot_ret"], sym_data["perp_ret"], params["roundtrip_cost"],
    )
    marg = margin_deductions(idx, params["rf_daily"])
    boundary = np.zeros(len(idx))  # basis already marked-to-market daily (see notes)

    l_asbuilt = asbuilt.copy()
    l_turn = l_asbuilt - turn
    l_reb = l_turn - reb
    l_marg = l_reb - marg
    l_boundary = l_marg - boundary
    return {
        "as_built": l_asbuilt,
        "plus_turnover": pd.Series(l_turn, index=idx),
        "plus_rebalance": pd.Series(l_reb, index=idx),
        "plus_margin_cost": pd.Series(l_marg, index=idx),
        "plus_boundary_basis": pd.Series(l_boundary, index=idx),
        "n_rebal": n_rebal,
    }


LAYER_ORDER = [
    "as_built", "plus_turnover", "plus_rebalance",
    "plus_margin_cost", "plus_boundary_basis",
]


def blend(per_symbol_layers: dict, layer: str) -> pd.Series:
    """0.5*BTC + 0.5*ETH of a given layer, over the shared date index."""
    btc = per_symbol_layers["BTCUSDT"][layer]
    eth = per_symbol_layers["ETHUSDT"][layer]
    idx = btc.index.intersection(eth.index)
    return (0.5 * btc.loc[idx] + 0.5 * eth.loc[idx]).rename("sleeve")


def main() -> None:
    # ── Fetch legs once per symbol ──────────────────────────────────────────
    sym_data = {s: build_symbol(s) for s in SYMBOLS}

    real_params = {
        "turnover_on": 1.0,
        "roundtrip_cost": ROUNDTRIP_COST,
        "rf_daily": RF_DAILY,
    }
    zero_params = {"turnover_on": 0.0, "roundtrip_cost": 0.0, "rf_daily": 0.0}

    layers = {s: apply_layers(sym_data[s], real_params) for s in SYMBOLS}

    # ── Sanity check (b): all-zero costs => stressed == as-built ────────────
    for s in SYMBOLS:
        zl = apply_layers(sym_data[s], zero_params)
        pd.testing.assert_series_equal(
            zl["plus_boundary_basis"].rename("asbuilt"),
            sym_data[s]["asbuilt"].rename("asbuilt"),
            check_names=False,
        )
    print("[sanity b] all-zero-cost stressed == as-built: PASS")

    # ── SR waterfall on the blended sleeve ──────────────────────────────────
    waterfall = {}
    blended_series = {}
    for layer in LAYER_ORDER:
        b = blend(layers, layer)
        blended_series[layer] = b
        waterfall[layer] = sr(b)

    # ── Sanity check (a): monotonically non-increasing SR ───────────────────
    prev = None
    for layer in LAYER_ORDER:
        cur = waterfall[layer]
        if prev is not None:
            assert cur <= prev + 1e-6, (
                f"waterfall not non-increasing at {layer}: {cur} > {prev}"
            )
        prev = cur
    print("[sanity a] waterfall SR monotonically non-increasing: PASS")

    # ── Rebalance counts + sanity check (c): plausible (not 0, not every day)
    n_days = {s: len(sym_data[s]["idx"]) for s in SYMBOLS}
    n_rebal = {s: layers[s]["n_rebal"] for s in SYMBOLS}
    total_rebal = sum(n_rebal.values())
    for s in SYMBOLS:
        assert 0 < n_rebal[s] < n_days[s], (
            f"implausible rebalance count for {s}: {n_rebal[s]} of {n_days[s]} days"
        )
    print(f"[sanity c] rebalance counts plausible: {n_rebal} (of {n_days} days)")

    # ── Per-symbol stressed SR ──────────────────────────────────────────────
    per_symbol_stressed_sr = {
        s: sr(layers[s]["plus_boundary_basis"]) for s in SYMBOLS
    }
    per_symbol_asbuilt_sr = {s: sr(layers[s]["as_built"]) for s in SYMBOLS}

    # ── Layer deltas + >2-SR comments ───────────────────────────────────────
    layer_detail = []
    prev_sr = None
    for layer in LAYER_ORDER:
        cur_sr = waterfall[layer]
        delta = None if prev_sr is None else cur_sr - prev_sr
        entry = {"layer": layer, "sr_after": cur_sr, "delta_sr": delta}
        if delta is not None and delta < -2.0:
            entry["comment"] = (
                f"layer '{layer}' alone removes {-delta:.2f} SR (>2): the sleeve's "
                f"edge is thin relative to this friction."
            )
        if layer == "plus_boundary_basis":
            entry["comment"] = (
                "0.0 by construction: compute_price_pnl marks the spot-perp basis "
                "to market every day via spot_ret - perp_ret on actual price "
                "series, so entry/exit basis convergence is already in the hedge "
                "P&L. Charging a separate boundary-basis layer would double-count."
            )
        layer_detail.append(entry)
        prev_sr = cur_sr

    stressed_blended_sr = waterfall["plus_boundary_basis"]

    out = {
        "window": [START, END],
        "annualization": "sqrt(252)",
        "construction": (
            "always-on, short 1x perp + long 1x spot, equal notional both legs, "
            "50/50 BTC/ETH; inception=first day, exit=last day"
        ),
        "cost_parameters": {
            "spot_taker": SPOT_TAKER,
            "perp_taker": PERP_TAKER,
            "spread_per_side": SPREAD,
            "open_cost_both_legs_one_side": OPEN_COST,
            "roundtrip_cost_both_legs": ROUNDTRIP_COST,
            "drift_threshold_frac_of_target": DRIFT_THRESHOLD,
            "target_notional_per_leg": TARGET_NOTIONAL,
            "rf_annual": RF_ANNUAL,
            "rf_daily": RF_DAILY,
            "margin_fraction_of_perp_notional": MARGIN_FRACTION,
        },
        "waterfall_order": LAYER_ORDER,
        "waterfall_sr": waterfall,
        "waterfall_detail": layer_detail,
        "stressed_blended_sr": stressed_blended_sr,
        "per_symbol_asbuilt_sr": per_symbol_asbuilt_sr,
        "per_symbol_stressed_sr": per_symbol_stressed_sr,
        "rebalance_count": n_rebal,
        "rebalance_count_total": total_rebal,
        "n_days": n_days,
        "sanity_checks": {
            "all_zero_cost_equals_asbuilt": "PASS",
            "waterfall_non_increasing": "PASS",
            "rebalance_count_plausible": "PASS",
        },
        "notes": (
            "Turnover 'per side' interpreted as one execution (open OR close) "
            "touching both legs: spot(taker+spread) + perp(taker+spread) = "
            f"{OPEN_COST:.4f}; inception charges one open, final exit one close. "
            "Rebalance charges the full round-trip cost (2x open = "
            f"{ROUNDTRIP_COST:.4f}) on the drift notional per the brief. Drift "
            "tracked by compounding each leg's equity with its own daily return "
            "since the last rebalance (long spot +spot_ret, SHORT perp -perp_ret) "
            "and resetting to target on rebalance. AMBIGUITY RESOLVED: modelling "
            "the short-perp leg with +perp_ret makes it track spot so |drift| "
            "never reaches 20% and rebalance count is 0 (degenerate); -perp_ret "
            "is the drift-generating reading, since a short's equity falls as the "
            "perp rises. Margin cost "
            "is a constant daily rf drag on 1/3 of perp notional (leverage<=3x). "
            "Boundary-basis layer recorded as 0.0 (already marked-to-market)."
        ),
    }

    outdir = PROJECT_ROOT / "data/rebuild/holdout/carry_audit"  # H2 holdout outdir
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "costs.json").write_text(json.dumps(out, indent=2))

    # ── Canonical stressed daily series CSV ─────────────────────────────────
    btc_stressed = layers["BTCUSDT"]["plus_boundary_basis"]
    eth_stressed = layers["ETHUSDT"]["plus_boundary_basis"]
    idx = btc_stressed.index.intersection(eth_stressed.index)
    df = pd.DataFrame({
        "date": [d.isoformat() for d in idx],
        "btc": btc_stressed.loc[idx].to_numpy(),
        "eth": eth_stressed.loc[idx].to_numpy(),
    })
    df["sleeve"] = 0.5 * df["btc"] + 0.5 * df["eth"]
    df.to_csv(outdir / "sleeve_stressed_daily.csv", index=False)

    # ── Ledger ──────────────────────────────────────────────────────────────
    log_trial(
        allow_holdout=True,  # H2 authorized ledger-guard edit (holdout one-shot)
        experiment="holdout_oneshot",
        config={
            "sleeve": "carry",
            "pass": "costs",
            "spot_taker": SPOT_TAKER,
            "perp_taker": PERP_TAKER,
            "spread_per_side": SPREAD,
            "roundtrip_cost": ROUNDTRIP_COST,
            "drift_threshold": DRIFT_THRESHOLD,
            "rf_annual": RF_ANNUAL,
            "margin_fraction": MARGIN_FRACTION,
        },
        window=(START, END),
        metrics={
            "stressed_blended_sr": stressed_blended_sr,
            "asbuilt_blended_sr": waterfall["as_built"],
            "per_symbol_stressed_sr": per_symbol_stressed_sr,
            "waterfall_sr": waterfall,
            "rebalance_count": n_rebal,
        },
    )

    # ── Report ──────────────────────────────────────────────────────────────
    print("\nWaterfall (blended sleeve SR):")
    for layer in LAYER_ORDER:
        d = next(x for x in layer_detail if x["layer"] == layer)
        ds = "" if d["delta_sr"] is None else f"  (Δ {d['delta_sr']:+.3f})"
        print(f"  {layer:22s} SR {waterfall[layer]:7.3f}{ds}")
    print(f"\nstressed blended SR: {stressed_blended_sr:.3f}")
    print(f"per-symbol stressed SR: {per_symbol_stressed_sr}")
    print(f"rebalance count: {n_rebal} (total {total_rebal})")


if __name__ == "__main__":
    main()
