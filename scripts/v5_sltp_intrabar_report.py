#!/usr/bin/env python
"""Reporting for V5 MIX TP/SL intrabar sweep — top-20 + 12 heatmaps + §29 comparison."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BASELINE = dict(sl=0.03, ee=0.015, tp=0.0)


def _heatmap(pivot: pd.DataFrame, title: str, cbar_label: str,
             out: Path, baseline: tuple[float, float] | None = None) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    arr = pivot.values
    im = ax.imshow(arr, aspect="auto", origin="lower", cmap="RdYlGn")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"{c:g}" for c in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([f"{r:g}" for r in pivot.index])
    ax.set_xlabel(pivot.columns.name)
    ax.set_ylabel(pivot.index.name)
    ax.set_title(title)
    plt.colorbar(im, ax=ax, label=cbar_label)

    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            ax.text(j, i, f"{arr[i, j]:.2f}",
                    ha="center", va="center", fontsize=7, color="black")

    if baseline is not None:
        sl_b, tp_b = baseline
        if sl_b in pivot.index and tp_b in pivot.columns:
            yi = list(pivot.index).index(sl_b)
            xi = list(pivot.columns).index(tp_b)
            ax.plot(xi, yi, marker="x", markersize=18, mew=3, color="blue",
                    label="V5 baseline")
            ax.legend(loc="upper right")

    plt.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="data/v5_sltp_sweep_intrabar")
    p.add_argument("--close-only-dir", default="data/v5_sltp_sweep",
                   help="§29 close-only sweep results for the comparison table")
    args = p.parse_args()

    in_dir = PROJECT_ROOT / args.input_dir
    co_dir = PROJECT_ROOT / args.close_only_dir
    df = pd.read_csv(in_dir / "results.csv")
    port = df[df["scope"] == "portfolio"].copy()

    # ── top-20 ────────────────────────────────────────────────────────
    top = port.sort_values("sharpe", ascending=False).head(20).copy()
    baseline_rows = port[(port["sl"] == 0.03) & (port["ee"] == 0.015) & (port["tp"] == 0.0)]
    baseline_sr = float(baseline_rows["sharpe"].iloc[0]) if len(baseline_rows) else float("nan")
    lines = [
        "# V5 MIX TP/SL Intrabar Sweep — Top 20 Cells (by portfolio Sharpe)",
        "",
        f"Source: `{in_dir / 'results.csv'}` ({len(port)} portfolio cells, intrabar OHLC)",
        "",
        f"Intrabar baseline V5 cell: SL=0.03, EE=0.015, TP=off → SR = {baseline_sr:+.3f}",
        "(Compare §29 close-only baseline = +3.178.)",
        "",
        "| Rank | SL | EE | TP | Sharpe | Total Ret | Max DD | Calmar | Win % | PF | n_SL | n_TP |",
        "|------|-----|-----|-----|--------|-----------|--------|--------|-------|-----|------|------|",
    ]
    for rank, (_, r) in enumerate(top.iterrows(), start=1):
        is_baseline = (r["sl"] == 0.03 and r["ee"] == 0.015 and r["tp"] == 0.0)
        marker = " ← **baseline**" if is_baseline else ""
        lines.append(
            f"| {rank} | {r['sl']:g} | {r['ee']:g} | {r['tp']:g} | "
            f"{r['sharpe']:+.3f}{marker} | {r['total_return']:+.1%} | "
            f"{r['max_drawdown']:.1%} | {r['calmar']:+.2f} | "
            f"{r['win_rate']:.1%} | {r['profit_factor']:.2f} | "
            f"{int(r['n_intrabar_sl'])} | {int(r['n_intrabar_tp'])} |"
        )
    (in_dir / "top20.md").write_text("\n".join(lines) + "\n")
    print(f"  Wrote: {in_dir / 'top20.md'}")

    # ── heatmaps ─────────────────────────────────────────────────────
    heat_dir = in_dir / "heatmaps"
    heat_dir.mkdir(exist_ok=True)
    n = 0
    for ee in sorted(port["ee"].unique()):
        sub = port[port["ee"] == ee]
        for metric, label in [
            ("sharpe", "Portfolio Sharpe (intrabar)"),
            ("max_drawdown", "Max Drawdown (intrabar)"),
        ]:
            pivot = sub.pivot(index="sl", columns="tp", values=metric)
            pivot.index.name = "stop_loss"
            pivot.columns.name = "take_profit"
            title = f"V5 MIX {label}  (early_exit_loss = {ee:g})"
            out = heat_dir / f"{metric}_sl_x_tp__ee_{ee:g}.png"
            baseline = (BASELINE["sl"], BASELINE["tp"]) if ee == BASELINE["ee"] else None
            _heatmap(pivot, title, label, out, baseline=baseline)
            n += 1
    print(f"  Wrote: {n} heatmaps to {heat_dir}")

    # ── comparison.md: §29 top-5 cells under both engines ────────────
    co_path = co_dir / "results.csv"
    if not co_path.exists():
        print(f"  WARNING: {co_path} not found; skipping comparison.md")
        return

    co = pd.read_csv(co_path)
    co_port = co[co["scope"] == "portfolio"]
    top5_co = co_port.sort_values("sharpe", ascending=False).head(5).reset_index(drop=True)

    rows = []
    for _, c in top5_co.iterrows():
        ib_rows = port[
            (port["sl"] == c["sl"]) & (port["ee"] == c["ee"]) & (port["tp"] == c["tp"])
        ]
        if len(ib_rows) == 0:
            continue
        ib = ib_rows.iloc[0]
        rows.append(dict(
            sl=c["sl"], ee=c["ee"], tp=c["tp"],
            co_sr=c["sharpe"], ib_sr=ib["sharpe"], delta=ib["sharpe"] - c["sharpe"],
            co_dd=c["max_drawdown"], ib_dd=ib["max_drawdown"],
            n_sl=int(ib["n_intrabar_sl"]), n_tp=int(ib["n_intrabar_tp"]),
        ))

    comp_lines = [
        "# V5 MIX TP/SL Sweep — §29 vs §30 (close-only vs intrabar)",
        "",
        f"Top-5 cells by close-only Sharpe (§29) re-scored under intrabar (§30).",
        "",
        "| SL | EE | TP | CO SR | IB SR | ΔSR | CO DD | IB DD | n_SL | n_TP |",
        "|----|----|----|-------|-------|-----|-------|-------|------|------|",
    ]
    for r in rows:
        comp_lines.append(
            f"| {r['sl']:g} | {r['ee']:g} | {r['tp']:g} | "
            f"{r['co_sr']:+.3f} | {r['ib_sr']:+.3f} | {r['delta']:+.3f} | "
            f"{r['co_dd']:.1%} | {r['ib_dd']:.1%} | "
            f"{r['n_sl']} | {r['n_tp']} |"
        )
    (in_dir / "comparison.md").write_text("\n".join(comp_lines) + "\n")
    print(f"  Wrote: {in_dir / 'comparison.md'}")


if __name__ == "__main__":
    main()
