"""Champion capacity study — REPORT ONLY (no gates, no ledger rows).

Question: at what AUM does the final champion's net Sharpe die once
market impact is modeled?

Method: rebuild the champion's exact daily weight path (parity-checked
against the Phase-O engine's gross return), then re-price costs per
name-day for a grid of AUM levels:

    trade_$_{t,i}  = AUM * |s_t w_{t,i} - s_{t-1} w_{t-1,i}|
    cost_{t,i}     = trade * (TAKER_BP/1e4)                       (fees)
                   + trade * k * sigma_{t,i} * sqrt(trade/ADV_{t,i})  (impact)

with sigma = trailing 20d close-to-close vol and ADV = trailing 20d
median quote volume (both lagged 1 day). Square-root impact is the
standard Almgren/Grinold institutional model; k=1.0 headline with
k in {0.5, 2.0} sensitivity. Funding carry unchanged. The overlay scale
path s_t is held at its baseline (5bp) trajectory — scale is a function
of realized book vol, which is approximately AUM-invariant.

Assumptions disclosed: close fills (no intraday scheduling), impact fully
paid same-day (no spreading), ADV from daily quote volume (includes both
sides), no crowding/alpha-decay term — this bounds *execution* capacity,
not the capacity of the anomaly itself.

Outputs (data/predlab/): capacity_study.json, capacity_study.png
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import opt  # noqa: E402
from tradingagents.predlab.pp import ANN_DAYS, TAKER_BP, ann_sr, max_drawdown  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
OUTDIR = DATA_ROOT / "predlab"
FULL = ("2021-01-01", "2026-07-01")
AUM_GRID = [1e6, 3e6, 1e7, 3e7, 1e8, 3e8, 1e9]
K_GRID = [0.5, 1.0, 2.0]

C_MAIN, C_SENS = "#2a78d6", "#a8a698"


def weight_path(sig, ret, uni):
    """Exact replication of opt.run_ls weights (eq, q=0.2, smooth 1,
    cadence 1). Returns (W DataFrame days x syms, traded index)."""
    lo, hi = pd.Timestamp(FULL[0], tz="UTC"), pd.Timestamp(FULL[1], tz="UTC")
    sigu = sig.where(uni)
    days = [d for d in ret.index if lo <= d <= hi and d in sigu.index]
    rows, idx = [], []
    for d in days:
        w = opt.leg_weights(sigu.loc[d], 0.2, "eq")
        if len(w) == 0:
            continue
        rows.append(w)
        idx.append(d)
    return pd.DataFrame(rows, index=idx).fillna(0.0)


def main() -> None:
    from predlab_opt_o1 import inputs

    close, park, ret, uni, fund = inputs()
    cfg = opt.OptConfig()
    sig = opt.build_signal(park, close, "ewma_20")

    # engine baseline (for parity + scale path)
    raw = opt.run_ls(sig, ret, uni, fund, cfg, *FULL)
    base = raw["rets"]

    W = weight_path(sig, ret, uni)
    r_al = ret.reindex(index=W.index, columns=W.columns)
    gross_chk = (W * r_al).sum(axis=1)
    par = float((gross_chk - base["gross"]).abs().max())
    assert par < 1e-12, f"weight-path parity FAIL: {par}"
    print(f"parity OK (max |diff| {par:.2e})", flush=True)

    carry = base["carry"]
    breadth = (~sig.where(uni).isna()).sum(axis=1).reindex(base.index)
    net5 = base["net"]
    sh = net5.rolling(20).std().shift(1) * np.sqrt(ANN_DAYS)
    scale = (0.15 / sh).clip(0.0, 2.0).fillna(0.0).where(breadth >= 100, 0.0)

    # scaled weight path + per-name dollar-fraction trades
    SW = W.mul(scale.reindex(W.index), axis=0)
    dW = SW.diff().abs()
    dW.iloc[0] = SW.iloc[0].abs()

    qv = pd.read_parquet if False else None  # placeholder guard (unused)
    # trailing stats, lagged one day
    from predlab_t7 import build_panels
    panels = build_panels()
    qv_panel = panels["qv"]
    adv = qv_panel.rolling(20).median().shift(1).reindex(
        index=W.index, columns=W.columns)
    sigma = (np.log(panels["close"]).diff().rolling(20).std().shift(1)
             .reindex(index=W.index, columns=W.columns))

    ovl_gross = scale.reindex(W.index) * (base["gross"] + carry)

    res = {"assumptions": {
        "impact": "k * sigma20 * sqrt(trade/ADV20), same-day, close fills",
        "taker_bp": TAKER_BP, "aum_grid": AUM_GRID, "k_grid": K_GRID,
        "scale_path": "baseline 5bp trajectory (AUM-invariant approx)"},
        "curves": {}}

    for k in K_GRID:
        curve = {}
        for aum in AUM_GRID:
            trade = dW * aum                       # $ per name-day
            fee_frac = (trade.sum(axis=1) * TAKER_BP / 1e4) / aum
            with np.errstate(divide="ignore", invalid="ignore"):
                imp = trade * k * sigma * np.sqrt(trade / adv)
            imp_frac = imp.sum(axis=1, skipna=True) / aum
            net = ovl_gross - fee_frac - imp_frac
            part = (trade / adv).stack()
            curve[f"{aum:.0e}"] = {
                "sr": ann_sr(net.to_numpy()),
                "maxdd": max_drawdown(net.dropna().to_numpy()),
                "ann_impact_drag_pct": float(imp_frac.mean() * ANN_DAYS * 100),
                "participation_p95_pct": float(part.quantile(0.95) * 100),
                "participation_max_pct": float(part.max() * 100),
            }
        res["curves"][f"k={k}"] = curve
        srs = {a: c["sr"] for a, c in curve.items()}
        print(f"k={k}: " + "  ".join(f"{a}:{s:+.2f}" for a, s in srs.items()),
              flush=True)

    # capacity thresholds on the headline k=1 curve (log-linear interp)
    aums = np.array(AUM_GRID)
    srs = np.array([res["curves"]["k=1.0"][f"{a:.0e}"]["sr"] for a in AUM_GRID])
    thresholds = {}
    for floor in (1.5, 1.0, 0.0):
        below = np.where(srs < floor)[0]
        if len(below) == 0:
            thresholds[f"sr_{floor}"] = f"> {aums[-1]:.0e}"
        elif below[0] == 0:
            thresholds[f"sr_{floor}"] = f"< {aums[0]:.0e}"
        else:
            i = below[0]
            x = np.interp(floor, [srs[i], srs[i - 1]],
                          [np.log10(aums[i]), np.log10(aums[i - 1])])
            thresholds[f"sr_{floor}"] = f"{10 ** x:.2e}"
    res["capacity_thresholds_k1"] = thresholds
    (OUTDIR / "capacity_study.json").write_text(
        json.dumps(res, indent=1, default=float))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid_c = "#1a1a19", "#5f5e56", "#e8e7e0"
    plt.rcParams.update({"text.color": ink, "axes.edgecolor": grid_c,
                         "axes.labelcolor": muted, "xtick.color": muted,
                         "ytick.color": muted, "font.size": 10})
    fig, ax = plt.subplots(figsize=(9, 5))
    for k in K_GRID:
        ys = [res["curves"][f"k={k}"][f"{a:.0e}"]["sr"] for a in AUM_GRID]
        if k == 1.0:
            ax.plot(aums, ys, color=C_MAIN, lw=2.5, marker="o", ms=6,
                    label="k = 1.0 (headline)", zorder=3)
        else:
            ax.plot(aums, ys, color=C_SENS, lw=1.4, ls="--", marker="o",
                    ms=4, label=f"k = {k}", zorder=2)
    ax.axhline(0, color=ink, lw=0.8)
    for floor, ls in ((1.0, ":"),):
        ax.axhline(floor, color=muted, lw=0.8, ls=ls)
    ax.set_xscale("log")
    ax.set_xlabel("AUM (USD)")
    ax.set_ylabel("net Sharpe (overlaid book)")
    ax.set_title("Champion capacity: net SR vs AUM under square-root impact",
                 loc="left")
    ax.legend(frameon=False)
    ax.grid(axis="y", color=grid_c, lw=0.6)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.savefig(OUTDIR / "capacity_study.png", dpi=150, bbox_inches="tight")
    print(f"thresholds (k=1): {thresholds}")
    print(f"written {OUTDIR}/capacity_study.json + png")


if __name__ == "__main__":
    main()
