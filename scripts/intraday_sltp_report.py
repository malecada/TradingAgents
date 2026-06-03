"""Figure-generation script for intraday SL/TP sweep (THESIS §31).

Generates 3 figures (PNG + SVG each) into <sweep-dir>/figures/:
  F-31.1  SL×TP Sharpe heatmap (intrabar, trail=0)
  F-31.2  Close-to-close look-ahead bias bar chart
  F-31.3  Robustness panel (split-date sensitivity + per-coin attribution)

Usage:
    python scripts/intraday_sltp_report.py --sweep-dir data/intraday_sltp_sweep
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # noqa: E402 — must come before pyplot import

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


def make_heatmap(sweep_dir: Path, figures_dir: Path) -> list[Path]:
    """F-31.1 — SL×TP Sharpe heatmap (intrabar, trail=0)."""
    df = pd.read_csv(sweep_dir / "results.csv")
    sub = df[(df["scope"] == "portfolio") & (df["trail"] == 0.0)].copy()

    pivot = sub.pivot(index="sl", columns="tp", values="sharpe")
    # Sort ascending so origin-lower shows smallest SL at bottom
    pivot = pivot.sort_index(ascending=True)
    pivot = pivot.sort_index(axis=1, ascending=True)

    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(
        pivot.values,
        cmap="viridis",
        origin="lower",
        aspect="auto",
    )

    # Tick labels as percentages
    sl_pcts = [f"{v:.0%}" for v in pivot.index]
    tp_pcts = [f"{v:.0%}" for v in pivot.columns]
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(tp_pcts)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(sl_pcts)

    ax.set_xlabel("Take-Profit", fontsize=12)
    ax.set_ylabel("Stop-Loss", fontsize=12)
    ax.set_title("Portfolio Sharpe — intrabar 1h fills (trail=0)", fontsize=13)

    # Annotate each cell
    for row_idx, sl_val in enumerate(pivot.index):
        for col_idx, tp_val in enumerate(pivot.columns):
            val = pivot.loc[sl_val, tp_val]
            if np.isfinite(val):
                text_color = "white" if val < pivot.values[np.isfinite(pivot.values)].mean() else "black"
                ax.text(
                    col_idx,
                    row_idx,
                    f"{val:.2f}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=text_color,
                )

    # Mark the baseline production cell: SL=3%, TP=0%
    baseline_sl = 0.03
    baseline_tp = 0.0
    if baseline_sl in list(pivot.index) and baseline_tp in list(pivot.columns):
        row_pos = list(pivot.index).index(baseline_sl)
        col_pos = list(pivot.columns).index(baseline_tp)
        ax.add_patch(
            plt.Rectangle(
                (col_pos - 0.5, row_pos - 0.5),
                1.0,
                1.0,
                fill=False,
                edgecolor="red",
                linewidth=2.5,
                label="Production baseline (SL=3%, TP=0%)",
            )
        )
        ax.text(
            col_pos,
            row_pos + 0.42,
            "baseline",
            ha="center",
            va="bottom",
            fontsize=7,
            color="red",
            fontweight="bold",
        )

    fig.colorbar(im, ax=ax, label="Sharpe Ratio")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.8)
    fig.tight_layout()

    out_png = figures_dir / "F-31.1_sltp_heatmap.png"
    out_svg = figures_dir / "F-31.1_sltp_heatmap.svg"
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_svg)
    plt.close(fig)
    return [out_png, out_svg]


def make_bias_chart(sweep_dir: Path, figures_dir: Path) -> list[Path]:
    """F-31.2 — Close-to-close look-ahead bias bar chart."""
    with open(sweep_dir / "bias.json") as fh:
        bias = json.load(fh)

    # Build per-group data
    groups: list[str] = []
    daily_vals: list[float] = []
    intrabar_vals: list[float] = []

    # Per-coin entries first
    for coin, metrics in bias.get("per_coin", {}).items():
        groups.append(coin)
        daily_vals.append(metrics["daily"]["sharpe"])
        intrabar_vals.append(metrics["intrabar"]["sharpe"])

    # Portfolio group last
    groups.append("portfolio")
    daily_vals.append(bias["portfolio"]["daily"]["sharpe"])
    intrabar_vals.append(bias["portfolio"]["intrabar"]["sharpe"])

    x = np.arange(len(groups))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    bars_daily = ax.bar(x - width / 2, daily_vals, width, label="Daily (close-to-close)", color="#2196F3")
    bars_intra = ax.bar(x + width / 2, intrabar_vals, width, label="Intrabar (1h fills)", color="#FF9800")

    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=11)
    ax.set_ylabel("Sharpe", fontsize=12)
    ax.set_title("3% stop: close-to-close look-ahead bias (daily overstates by 0.27 SR)", fontsize=12)
    ax.legend(fontsize=10)
    ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Annotate bar heights
    for bar in bars_daily:
        h = bar.get_height()
        ax.annotate(
            f"{h:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    for bar in bars_intra:
        h = bar.get_height()
        ax.annotate(
            f"{h:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.tight_layout()

    out_png = figures_dir / "F-31.2_close_to_close_bias.png"
    out_svg = figures_dir / "F-31.2_close_to_close_bias.svg"
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_svg)
    plt.close(fig)
    return [out_png, out_svg]


def make_robustness_panel(sweep_dir: Path, figures_dir: Path) -> list[Path]:
    """F-31.3 — Robustness panel (split-date sensitivity + per-coin attribution)."""
    with open(sweep_dir / "robustness.json") as fh:
        rob = json.load(fh)

    check1 = rob["check1_split_sensitivity"]
    check2 = rob["check2_per_coin"]

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(13, 5))

    # ── Left: split-date sensitivity ──────────────────────────────────────────
    splits = [entry["split"] for entry in check1]
    points = [entry["delta_sr_point"] for entry in check1]
    cis = [entry["delta_sr_ci"] for entry in check1]
    ships = [entry["ship"] for entry in check1]
    p_vals = [entry["p_delta_le_0"] for entry in check1]

    x_left = np.arange(len(splits))
    colors = ["green" if s else "red" for s in ships]

    # Asymmetric error bars: [point - lo, hi - point]
    yerr_low = [pt - ci[0] for pt, ci in zip(points, cis)]
    yerr_high = [ci[1] - pt for pt, ci in zip(points, cis)]
    yerr = np.array([yerr_low, yerr_high])

    for i, (xi, pt, color) in enumerate(zip(x_left, points, colors)):
        ax_left.errorbar(
            xi,
            pt,
            yerr=[[yerr_low[i]], [yerr_high[i]]],
            fmt="o",
            color=color,
            capsize=5,
            markersize=8,
            elinewidth=1.5,
        )

    ax_left.axhline(0, color="black", linewidth=1.0, linestyle="--")

    # Annotate p-values above each point
    for i, (xi, pt, p) in enumerate(zip(x_left, points, p_vals)):
        ax_left.annotate(
            f"p={p:.4f}",
            xy=(xi, pt + yerr_high[i] + 0.04),
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax_left.set_xticks(x_left)
    ax_left.set_xticklabels(splits, rotation=15, ha="right", fontsize=9)
    ax_left.set_ylabel("OOS ΔSharpe (best vs 3%)", fontsize=11)
    ax_left.set_title("Split-date sensitivity: SHIP holds 2/4", fontsize=11)
    ax_left.grid(axis="y", linestyle="--", alpha=0.4)

    # Legend proxy for ship color coding
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="green", markersize=9, label="Ship"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="red", markersize=9, label="No-ship"),
    ]
    ax_left.legend(handles=legend_elements, fontsize=9, loc="lower right")

    # ── Right: per-coin attribution (check2) ──────────────────────────────────
    coins = list(check2.keys())
    delta_srs = [check2[c]["delta_sr"] for c in coins]
    bar_colors = ["green" if d > 0 else "red" for d in delta_srs]

    x_right = np.arange(len(coins))
    bars = ax_right.bar(x_right, delta_srs, color=bar_colors, edgecolor="black", linewidth=0.5)

    ax_right.axhline(0, color="black", linewidth=1.0, linestyle="--")
    ax_right.set_xticks(x_right)
    ax_right.set_xticklabels(coins, fontsize=10)
    ax_right.set_ylabel("ΔSharpe (SL4%/TP8% − 3%)", fontsize=11)
    ax_right.set_title("TP benefit concentrated in ETH", fontsize=11)
    ax_right.grid(axis="y", linestyle="--", alpha=0.4)

    for bar, d in zip(bars, delta_srs):
        offset = 0.02 if d >= 0 else -0.04
        ax_right.annotate(
            f"{d:+.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, d + offset),
            ha="center",
            va="bottom" if d >= 0 else "top",
            fontsize=9,
            fontweight="bold",
        )

    fig.tight_layout()

    out_png = figures_dir / "F-31.3_robustness.png"
    out_svg = figures_dir / "F-31.3_robustness.svg"
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_svg)
    plt.close(fig)
    return [out_png, out_svg]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate §31 intraday SL/TP figures")
    parser.add_argument(
        "--sweep-dir",
        default="data/intraday_sltp_sweep",
        help="Directory containing results.csv, bias.json, robustness.json",
    )
    args = parser.parse_args()

    sweep_dir = Path(args.sweep_dir)
    figures_dir = sweep_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    written.extend(make_heatmap(sweep_dir, figures_dir))
    written.extend(make_bias_chart(sweep_dir, figures_dir))
    written.extend(make_robustness_panel(sweep_dir, figures_dir))

    print("Files written:")
    for p in written:
        print(f"  {p}")


if __name__ == "__main__":
    main()
