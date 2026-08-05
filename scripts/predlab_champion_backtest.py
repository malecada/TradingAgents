"""Champion comparison backtest — REPORT ONLY (no gates, no ledger rows).

Runs the OLD Phase-P champion (park_5 eq_h1 + vt10_naive20 overlay, pp2
formula) and the NEW Phase-O final champion (ewma_20 eq-quintile-daily
top-200 + vt15_naive20_b100 overlay, O4 formula) over the full stored
history 2021-01-01 -> 2026-07-01.

The daily loop is walk-forward by construction: signal panels are shifted
one day (info through t-1), universe membership is month-(m-1) PIT, and
the vol overlay uses book returns through t-1 only. There are no fitted
parameters, so no refit schedule exists — every position uses only past
data. Yearly segments below are therefore honest out-of-sample folds under
the frozen config (config selection itself used the D window; see the
predlab_opt gates for the D/V discipline and the sealed forward window).

Both overlays reuse each claim's audited formula verbatim (pp2 for vt10,
O4 for vt15_b100) so the headline numbers reproduce the frozen chain.

Outputs (data/predlab/):
  champion_backtest.json          full metrics
  champion_backtest_equity.png    equity curves + drawdown
  champion_backtest_yearly.png    per-year net SR bars
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

# validated dataviz reference palette, light mode
C_NEW, C_OLD = "#2a78d6", "#eb6834"


def overlay_pp2(base: pd.DataFrame, target: float, cap: float = 2.0) -> "tuple[pd.Series, pd.Series]":
    """OLD-champion overlay (pp2 formula): scale applies to pre-fee book."""
    raw_pre_cost = base["gross"] + base["carry"]
    vol = raw_pre_cost.rolling(20).std().shift(1) * np.sqrt(ANN_DAYS)
    s = (target / vol).clip(upper=cap).fillna(0.0)
    ds = s.diff().abs().fillna(s.iloc[0] if len(s) else 0.0)
    cost = TAKER_BP / 1e4 * (s * base["turnover"] + ds * 2.0)
    return s * raw_pre_cost - cost, s


def overlay_o4(base: pd.DataFrame, breadth: pd.Series, target: float,
               cap: float = 2.0, breadth_floor: int = 100) -> "tuple[pd.Series, pd.Series]":
    """NEW-champion overlay (O4 formula): scale applies to net book,
    zeroed while universe breadth < floor (t-1 signal-availability count)."""
    net = base["net"]
    sh = net.rolling(20).std().shift(1) * np.sqrt(ANN_DAYS)
    s = (target / sh).clip(0.0, cap).fillna(0.0)
    s = s.where(breadth >= breadth_floor, 0.0)
    cost = TAKER_BP / 1e4 * (s * base["turnover"] + s.diff().abs().fillna(0.0) * 2.0)
    return s * net - cost, s


def seg_metrics(net: pd.Series, lo: str, hi: str) -> dict:
    seg = net[(net.index >= lo) & (net.index <= hi)].dropna()
    if len(seg) < 20:
        return {"sr": None, "ret": None, "maxdd": None, "n_days": int(len(seg))}
    return {"sr": ann_sr(seg.to_numpy()),
            "ret": float(np.expm1(np.log1p(seg).sum())),
            "maxdd": max_drawdown(seg.to_numpy()),
            "n_days": int(len(seg))}


def yearly(net: pd.Series) -> "dict[str, dict]":
    out = {}
    for y in sorted(set(net.index.year)):
        out[str(y)] = seg_metrics(net, f"{y}-01-01", f"{y}-12-31")
    return out


def main() -> None:
    from predlab_opt_o1 import inputs

    close, park, ret, uni, fund = inputs()
    cfg = opt.OptConfig()
    systems = {}

    for name, sig_kind in (("old", "park_5"), ("new", "ewma_20")):
        sig = opt.build_signal(park, close, sig_kind)
        raw = opt.run_ls(sig, ret, uni, fund, cfg, *FULL)
        base = raw["rets"]
        if name == "old":
            ovl_net, scale = overlay_pp2(base, 0.10)
        else:
            breadth = (~sig.where(uni).isna()).sum(axis=1).reindex(base.index)
            ovl_net, scale = overlay_o4(base, breadth, 0.15)
        systems[name] = {"raw": base, "ovl": ovl_net, "scale": scale}
        print(f"{name} ({sig_kind}): raw SR {raw['sr_net']:+.3f} dd "
              f"{raw['maxdd']:.1%} | ovl SR {ann_sr(ovl_net.to_numpy()):+.3f} "
              f"dd {max_drawdown(ovl_net.dropna().to_numpy()):.1%}", flush=True)

    res = {"window": list(FULL), "note": "report-only rerun of frozen configs; "
           "no new trials", "systems": {}}
    for name, s in systems.items():
        res["systems"][name] = {
            "config": ("park_5 eq_h1 + vt10_naive20 (pp2)" if name == "old"
                       else "ewma_20 eq_h1 top-200 + vt15_naive20_b100 (O4)"),
            "raw": seg_metrics(s["raw"]["net"], *FULL),
            "ovl": seg_metrics(s["ovl"], *FULL),
            "ovl_D": seg_metrics(s["ovl"], *opt.DESIGN_D),
            "ovl_V": seg_metrics(s["ovl"], *opt.VALIDATION_V),
            "avg_scale": float(s["scale"].mean()),
            "yearly_ovl": yearly(s["ovl"]),
            "yearly_raw": yearly(s["raw"]["net"]),
        }
    (OUTDIR / "champion_backtest.json").write_text(
        json.dumps(res, indent=1, default=float))

    # ---------------------------------------------------------------- plots
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid = "#1a1a19", "#5f5e56", "#e8e7e0"
    plt.rcParams.update({"text.color": ink, "axes.edgecolor": grid,
                         "axes.labelcolor": muted, "xtick.color": muted,
                         "ytick.color": muted, "font.size": 10})

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(11, 7), sharex=True,
        gridspec_kw={"height_ratios": [3, 1.2], "hspace": 0.08})
    for name, color, label in (("old", C_OLD, "old champion (park_5 + vt10)"),
                               ("new", C_NEW, "new champion (ewma_20 + vt15_b100)")):
        net = systems[name]["ovl"].dropna()
        eq = (1 + net).cumprod()
        ax1.plot(eq.index, eq, color=color, lw=2, label=label)
        dd = 1 - eq / eq.cummax()
        ax2.plot(dd.index, -dd * 100, color=color, lw=1.5)
    ax1.set_yscale("log")
    ax1.set_ylabel("equity (log, start = 1)")
    ax1.legend(frameon=False, loc="upper left")
    ax1.grid(axis="y", color=grid, lw=0.6)
    ax1.set_title("Champion walk-forward backtest 2021-01 → 2026-07 "
                  "(net of 5bp + funding, vol-target overlays)", loc="left")
    ax2.set_ylabel("drawdown (%)")
    ax2.grid(axis="y", color=grid, lw=0.6)
    for ax in (ax1, ax2):
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    fig.savefig(OUTDIR / "champion_backtest_equity.png", dpi=150,
                bbox_inches="tight")

    years = sorted(set(systems["new"]["ovl"].index.year))
    fig2, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(years))
    for off, (name, color, label) in (
            (-0.2, ("old", C_OLD, "old champion")),
            (+0.2, ("new", C_NEW, "new champion"))):
        srs = [res["systems"][name]["yearly_ovl"][str(y)]["sr"] or 0.0
               for y in years]
        ax.bar(x + off, srs, width=0.38, color=color, label=label, zorder=3)
    ax.axhline(0, color=ink, lw=0.8)
    ax.set_xticks(x, [str(y) for y in years])
    ax.set_ylabel("net Sharpe (overlaid book)")
    ax.set_title("Per-year net SR — walk-forward folds under frozen configs",
                 loc="left")
    ax.legend(frameon=False)
    ax.grid(axis="y", color=grid, lw=0.6, zorder=0)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig2.savefig(OUTDIR / "champion_backtest_yearly.png", dpi=150,
                 bbox_inches="tight")
    print(f"written {OUTDIR}/champion_backtest.json + 2 PNGs")


if __name__ == "__main__":
    main()
