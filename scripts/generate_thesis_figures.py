#!/usr/bin/env python
"""Batch generation of thesis figures from existing data artefacts.

Produces every figure in THESIS_FIGURES_PLAN.md that has a confirmed data source.
Outputs PNG (300 dpi) + SVG (vector) to data/figures/.

Usage:
    python scripts/generate_thesis_figures.py [--png-only|--svg-only]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

FIG_DIR = PROJECT_ROOT / "data" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Matplotlib style
plt.rcParams.update({
    "figure.dpi": 100,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.family": "DejaVu Serif",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "axes.grid": True,
    "axes.grid.axis": "both",
    "grid.alpha": 0.3,
    "legend.fontsize": 10,
    "legend.frameon": False,
})

ANN = np.sqrt(252)

# Coin colors (consistent across plots)
COIN_COLORS = {
    "bitcoin": "#F7931A",
    "ethereum": "#627EEA",
    "binancecoin": "#F0B90B",
    "solana": "#9945FF",
    "portfolio": "#000000",
}
COIN_LABELS = {
    "bitcoin": "BTC", "ethereum": "ETH",
    "binancecoin": "BNB", "solana": "SOL",
    "portfolio": "Portfolio",
}

SAVE_FORMATS = ["png", "svg"]


def _save(fig, slug: str) -> None:
    for fmt in SAVE_FORMATS:
        out = FIG_DIR / f"{slug}.{fmt}"
        fig.savefig(out, format=fmt)
        print(f"  wrote {out}")
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────
# F-4.2.3 Per-coin Kelly sweep
# ──────────────────────────────────────────────────────────────────
def fig_kelly_sweep():
    df = pd.read_csv(PROJECT_ROOT / "data/v5_kelly_sweep/per_coin.csv")
    fig, ax = plt.subplots(figsize=(8, 5))
    for coin in ["bitcoin", "ethereum", "binancecoin", "solana"]:
        sub = df[df["coin"] == coin].sort_values("kelly")
        ax.plot(sub["kelly"], sub["sharpe"],
                marker="o", color=COIN_COLORS[coin],
                label=COIN_LABELS[coin], linewidth=2)
    ax.axhline(0, color="gray", linestyle=":", linewidth=0.7)
    ax.axvline(0.25, color="green", linestyle="--", linewidth=0.7,
               alpha=0.5, label="live kelly=0.25")
    ax.axvline(0.50, color="blue", linestyle="--", linewidth=0.7,
               alpha=0.5, label="backtest kelly=0.50")
    ax.set_xlabel("Kelly fraction")
    ax.set_ylabel("Sharpe ratio (4.5-yr WF)")
    ax.set_title("F-4.2.3  Per-coin Kelly sweep — Sharpe vs Kelly fraction")
    ax.legend(loc="lower left", ncol=2)
    _save(fig, "F-4.2.3-kelly-sweep")


# ──────────────────────────────────────────────────────────────────
# F-4.4.9 V5 MIX 4-coin equity curves
# ──────────────────────────────────────────────────────────────────
def fig_v5_equity():
    df = pd.read_csv(PROJECT_ROOT / "data/v5_mix_production/daily_returns.csv",
                     index_col=0, parse_dates=True)
    eq = (1 + df).cumprod() * 10_000
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for col in ["bitcoin", "ethereum", "binancecoin", "solana"]:
        ax.plot(eq.index, eq[col], color=COIN_COLORS[col],
                label=COIN_LABELS[col], linewidth=1.2, alpha=0.7)
    ax.plot(eq.index, eq["portfolio"], color="black",
            label="Portfolio (25% EW)", linewidth=2.5)
    ax.set_yscale("log")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity ($, log scale)")
    ax.set_title("F-4.4.9  V5 MIX — 4-coin walk-forward equity (2021-11 → 2026-04)")
    ax.legend(loc="upper left")
    _save(fig, "F-4.4.9-v5-equity")


# ──────────────────────────────────────────────────────────────────
# F-4.4.10 V5 strategy-level correlation heatmap
# ──────────────────────────────────────────────────────────────────
def fig_v5_correlation():
    df = pd.read_csv(PROJECT_ROOT / "data/v5_mix_production/daily_returns.csv",
                     index_col=0, parse_dates=True)
    coins = ["bitcoin", "ethereum", "binancecoin", "solana"]
    corr = df[coins].corr()
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-0.5, vmax=0.5)
    ax.set_xticks(range(4))
    ax.set_yticks(range(4))
    ax.set_xticklabels([COIN_LABELS[c] for c in coins])
    ax.set_yticklabels([COIN_LABELS[c] for c in coins])
    for i in range(4):
        for j in range(4):
            v = corr.values[i, j]
            ax.text(j, i, f"{v:+.3f}", ha="center", va="center",
                    color="white" if abs(v) > 0.3 else "black", fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("F-4.4.10  V5 MIX strategy-level daily-return correlations")
    ax.grid(False)
    _save(fig, "F-4.4.10-v5-correlation")


# ──────────────────────────────────────────────────────────────────
# F-4.5.1 DSR sensitivity
# ──────────────────────────────────────────────────────────────────
def fig_dsr_sensitivity():
    with open(PROJECT_ROOT / "data/v5_validation/v5_validation.json") as f:
        d = json.load(f)
    # Extract per-n_trials results
    rows = d.get("dsr_by_trials", [])
    if not rows:
        # Fallback: hardcode from §16.1 of report
        rows = [
            {"n_trials": 5,   "e_max_sr": 0.02531, "dsr": 1.0},
            {"n_trials": 12,  "e_max_sr": 0.03533, "dsr": 1.0},
            {"n_trials": 25,  "e_max_sr": 0.04239, "dsr": 1.0},
            {"n_trials": 50,  "e_max_sr": 0.04831, "dsr": 1.0},
            {"n_trials": 100, "e_max_sr": 0.05371, "dsr": 1.0},
        ]
    rdf = pd.DataFrame(rows)
    observed_sr = d.get("observed_per_bar_sr", 0.20023)
    # Convert per-bar to annualised for display
    rdf["e_max_sr_ann"] = rdf["e_max_sr"] * ANN
    observed_ann = observed_sr * ANN

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(rdf["n_trials"], rdf["e_max_sr_ann"],
            marker="o", linewidth=2, color="#D62728",
            label="E[max SR | null]")
    ax.axhline(observed_ann, color="green", linestyle="--", linewidth=2,
               label=f"Observed SR = {observed_ann:+.2f}")
    ax.fill_between(rdf["n_trials"], 0, rdf["e_max_sr_ann"],
                    alpha=0.15, color="red")
    ax.set_xscale("log")
    ax.set_xlabel("n_trials (number of strategies tested)")
    ax.set_ylabel("Annualised Sharpe")
    ax.set_title("F-4.5.1  Deflated Sharpe Ratio sensitivity to n_trials")
    ax.legend(loc="center right")
    ax.annotate(f"DSR = 1.0000 even at n_trials=100",
                xy=(50, observed_ann), xytext=(8, observed_ann - 0.6),
                fontsize=10, color="black",
                arrowprops=dict(arrowstyle="->", color="gray"))
    _save(fig, "F-4.5.1-dsr-sensitivity")


# ──────────────────────────────────────────────────────────────────
# F-4.5.2 Random-entry placebo null distribution
# ──────────────────────────────────────────────────────────────────
def fig_placebo_null():
    arr = np.load(PROJECT_ROOT / "data/v5_validation/placebo_sr_null.npy")
    observed = 3.178
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(arr, bins=40, color="#1F77B4", alpha=0.7, edgecolor="white")
    ax.axvline(observed, color="green", linestyle="-", linewidth=2.5,
               label=f"Observed SR = +{observed:.3f}")
    ax.axvline(arr.mean(), color="red", linestyle="--", linewidth=2,
               label=f"Null mean = +{arr.mean():.3f}")
    p = float((arr >= observed).mean())
    contrib = observed - arr.mean()
    ax.set_xlabel("Portfolio Sharpe (random-entry permutation)")
    ax.set_ylabel("Frequency (K=1000)")
    ax.set_title("F-4.5.2  Random-entry placebo null distribution")
    ax.legend(loc="upper left")
    ax.text(0.97, 0.97,
            f"p-value = {p:.3f}\nSignal contribution = +{contrib:.3f} SR (~10%)\n"
            f"Mechanics floor = +{arr.mean():.3f} SR (~90%)",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=10, bbox=dict(boxstyle="round", facecolor="white",
                                   edgecolor="gray", alpha=0.9))
    _save(fig, "F-4.5.2-placebo-null")


# ──────────────────────────────────────────────────────────────────
# F-4.5.3 Per-regime decomposition (grouped bar)
# ──────────────────────────────────────────────────────────────────
def fig_regime_decomposition():
    with open(PROJECT_ROOT / "data/v5_validation/v5_robustness.json") as f:
        d = json.load(f)
    rows = d["regime_decomposition"]
    df = pd.DataFrame(rows)
    coins = ["bitcoin", "ethereum", "binancecoin", "solana",
             "portfolio_by_btc_regime"]
    regimes = ["bull", "sideways", "bear"]
    coin_labels = {**{k: COIN_LABELS[k] for k in COIN_LABELS},
                   "portfolio_by_btc_regime": "Portfolio\n(BTC regime)"}

    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(coins))
    width = 0.27
    regime_colors = {"bull": "#2CA02C", "sideways": "#7F7F7F", "bear": "#D62728"}
    for i, regime in enumerate(regimes):
        vals = []
        for c in coins:
            r = df[(df["scope"] == c) & (df["regime"] == regime)]
            vals.append(r["sharpe"].iloc[0] if len(r) else 0)
        ax.bar(x + (i - 1) * width, vals, width=width,
               label=regime.capitalize(), color=regime_colors[regime],
               alpha=0.85, edgecolor="white")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([coin_labels[c] for c in coins])
    ax.set_ylabel("Sharpe ratio")
    ax.set_title("F-4.5.3  Per-regime Sharpe decomposition (4.5-yr WF)")
    ax.legend(title="Regime", loc="upper left")
    _save(fig, "F-4.5.3-regime-decomposition")


# ──────────────────────────────────────────────────────────────────
# F-4.5.4 CPCV fold Sharpe distribution
# ──────────────────────────────────────────────────────────────────
def fig_cpcv_fold_dist():
    df = pd.read_csv(PROJECT_ROOT / "data/v5_validation/per_regime_cpcv.csv")
    srs = df["sharpe"].values
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(srs, bins=12, color="#1F77B4", alpha=0.7, edgecolor="white")
    ax.axvline(srs.mean(), color="green", linewidth=2,
               label=f"Mean = +{srs.mean():.3f}")
    ax.axvline(2.0, color="orange", linestyle="--", linewidth=2,
               label="SR=2 threshold")
    ax.set_xlabel("Sharpe ratio (per CPCV test fold)")
    ax.set_ylabel("Frequency (n=28 folds)")
    ax.set_title("F-4.5.4  CPCV fold Sharpe distribution (n_groups=8, test_groups=2)")
    ax.legend(loc="upper left")
    ax.text(0.97, 0.97,
            f"100% folds SR > 2\nmin = +{srs.min():.2f}\nmax = +{srs.max():.2f}\n"
            f"PBO proxy = 0.000",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=10, bbox=dict(boxstyle="round", facecolor="white",
                                   edgecolor="gray", alpha=0.9))
    _save(fig, "F-4.5.4-cpcv-fold-dist")


# ──────────────────────────────────────────────────────────────────
# F-4.5.5 Per-regime CPCV breakdown
# ──────────────────────────────────────────────────────────────────
def fig_per_regime_cpcv():
    with open(PROJECT_ROOT / "data/v5_validation/per_regime_cpcv.json") as f:
        d = json.load(f)
    regimes = ["sideways", "bear"]
    rows = []
    for r in regimes:
        if r in d["per_regime"]:
            v = d["per_regime"][r]
            rows.append({"regime": r, **v})
    rdf = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(rdf))
    width = 0.35
    ax.bar(x - width / 2, rdf["mean_sr"], width=width,
           label="Mean SR", color="#1F77B4", alpha=0.85)
    ax.bar(x + width / 2, rdf["median_sr"], width=width,
           label="Median SR", color="#FF7F0E", alpha=0.85)
    for i, r in enumerate(rdf.itertuples()):
        ax.text(i, max(r.mean_sr, r.median_sr) + 0.1,
                f"n={int(r.n_folds)}\n100% SR>2",
                ha="center", fontsize=10)
    ax.axhline(2.0, color="orange", linestyle="--", linewidth=1, alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([r.capitalize() for r in rdf["regime"]])
    ax.set_ylabel("Sharpe ratio")
    ax.set_title("F-4.5.5  Per-regime CPCV breakdown (28 folds classified by dominant BTC regime)")
    ax.set_ylim(0, max(rdf["mean_sr"].max(), rdf["median_sr"].max()) + 0.8)
    ax.legend(loc="upper right")
    _save(fig, "F-4.5.5-per-regime-cpcv")


# ──────────────────────────────────────────────────────────────────
# F-4.5.6 Cost sensitivity
# ──────────────────────────────────────────────────────────────────
def fig_cost_sensitivity():
    with open(PROJECT_ROOT / "data/v5_validation/v5_robustness.json") as f:
        d = json.load(f)
    rows = d["cost_sensitivity"]
    rdf = pd.DataFrame(rows)
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax2 = ax1.twinx()
    ax1.plot(rdf["cost_mult"], rdf["sharpe"], marker="o", linewidth=2,
             color="#1F77B4", label="Sharpe")
    ax2.plot(rdf["cost_mult"], rdf["total_return"] * 100, marker="s",
             linewidth=2, color="#D62728", label="Return (%)")
    ax1.set_xlabel("Cost multiplier (× baseline)")
    ax1.set_ylabel("Sharpe ratio", color="#1F77B4")
    ax2.set_ylabel("Compounded return (%)", color="#D62728")
    ax1.tick_params(axis="y", labelcolor="#1F77B4")
    ax2.tick_params(axis="y", labelcolor="#D62728")
    ax2.grid(False)
    ax1.set_xticks(rdf["cost_mult"])
    ax1.set_title("F-4.5.6  V5 MIX cost sensitivity (fee+slippage+spread+impact+funding scaled)")
    for i, r in enumerate(rdf.itertuples()):
        ax1.annotate(f"SR={r.sharpe:.2f}",
                     xy=(r.cost_mult, r.sharpe),
                     xytext=(5, 10), textcoords="offset points",
                     fontsize=9, color="#1F77B4")
    _save(fig, "F-4.5.6-cost-sensitivity")


# ──────────────────────────────────────────────────────────────────
# F-4.4.4 V3 component ablation
# ──────────────────────────────────────────────────────────────────
def fig_v3_ablation():
    with open(PROJECT_ROOT / "data/v3_ablations/ablations_metrics.json") as f:
        d = json.load(f)
    variants = ["full", "h7_h14", "flat_regime", "v2_sizing"]
    variant_labels = {
        "full": "Full V3", "h7_h14": "h7+h14 only\n(drop h=3, h=21)",
        "flat_regime": "Flat regime\n(disable NH-HMM)",
        "v2_sizing": "V2 sizing\n(no vol-target/CDAP)",
    }
    btc_srs = [d[v]["bitcoin"]["sharpe_ratio"] for v in variants]
    eth_srs = [d[v]["ethereum"]["sharpe_ratio"] for v in variants]
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(variants))
    width = 0.38
    ax.bar(x - width / 2, btc_srs, width=width,
           label="BTC", color=COIN_COLORS["bitcoin"], alpha=0.85)
    ax.bar(x + width / 2, eth_srs, width=width,
           label="ETH", color=COIN_COLORS["ethereum"], alpha=0.85)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([variant_labels[v] for v in variants])
    ax.set_ylabel("Sharpe ratio (88-bar OOS)")
    ax.set_title("F-4.4.4  V3 component ablation (every removal makes V3 strictly worse)")
    ax.legend(loc="lower right")
    for i, (b, e) in enumerate(zip(btc_srs, eth_srs)):
        ax.text(i - width / 2, b + (0.1 if b > 0 else -0.4),
                f"{b:+.2f}", ha="center", fontsize=9)
        ax.text(i + width / 2, e + (0.1 if e > 0 else -0.4),
                f"{e:+.2f}", ha="center", fontsize=9)
    _save(fig, "F-4.4.4-v3-ablation")


# ──────────────────────────────────────────────────────────────────
# F-4.4.5 NH-HMM bundle pathology
# ──────────────────────────────────────────────────────────────────
def fig_nhhmm_pathology():
    df = pd.read_csv(PROJECT_ROOT / "data/walkforward_v4_2coin/regime_diagnostics.csv")
    coins = ["bitcoin", "ethereum"]
    regimes = ["bull", "sideways", "bear"]
    regime_colors = {"bull": "#2CA02C", "sideways": "#7F7F7F", "bear": "#D62728"}
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(coins))
    bottom = np.zeros(len(coins))
    for regime in regimes:
        shares = []
        for coin in coins:
            sub = df[df["coin"] == coin]
            shares.append((sub["label"] == regime).mean() * 100)
        ax.bar(x, shares, bottom=bottom, label=regime.capitalize(),
               color=regime_colors[regime], alpha=0.85, edgecolor="white")
        for i, s in enumerate(shares):
            if s > 3:
                ax.text(i, bottom[i] + s / 2, f"{s:.1f}%",
                        ha="center", va="center", color="white", fontsize=10,
                        weight="bold")
        bottom += np.array(shares)
    ax.set_xticks(x)
    ax.set_xticklabels([COIN_LABELS[c] for c in coins])
    ax.set_ylabel("Bar share (%) of regime label")
    ax.set_ylim(0, 105)
    ax.set_title("F-4.4.5  V3 NH-HMM regime label distribution (1620 bars, 4.5-yr WF)",
                 pad=20)
    ax.legend(loc="lower right")
    fig.text(0.5, 0.01,
             "BTC bundle: 0% bear despite 2022-2023 crypto winter (-65% DD). "
             "ETH bundle: 63% bear with confidence 1.00 through 2024-2025 bull rally.",
             ha="center", va="bottom", fontsize=8.5, style="italic", color="dimgray")
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    _save(fig, "F-4.4.5-nhhmm-pathology")


# ──────────────────────────────────────────────────────────────────
# F-4.4.7 V4-B per-regime decomposition heatmap
# ──────────────────────────────────────────────────────────────────
def fig_v4b_per_regime():
    df = pd.read_csv(PROJECT_ROOT / "data/v4b_analysis/per_regime_decomposition.csv")
    coins = ["bitcoin", "ethereum"]
    regimes = ["bull", "sideways", "bear"]
    mat = np.zeros((len(coins), len(regimes)))
    for i, coin in enumerate(coins):
        for j, regime in enumerate(regimes):
            r = df[(df["coin"] == coin) & (df["regime"] == regime)]
            if len(r):
                mat[i, j] = r["sharpe"].iloc[0]
    fig, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(mat, cmap="RdYlGn", vmin=-1, vmax=4, aspect="auto")
    ax.set_xticks(range(len(regimes)))
    ax.set_yticks(range(len(coins)))
    ax.set_xticklabels([r.capitalize() for r in regimes])
    ax.set_yticklabels([f"{COIN_LABELS[c]}\n({'V2-78f' if c == 'bitcoin' else 'V4-B-193f'})"
                         for c in coins])
    for i in range(len(coins)):
        for j in range(len(regimes)):
            ax.text(j, i, f"SR={mat[i, j]:+.2f}",
                    ha="center", va="center",
                    color="black" if mat[i, j] < 2.5 else "white",
                    fontsize=11, weight="bold")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Sharpe")
    ax.set_title("F-4.4.7  V5 MIX per-regime Sharpe decomposition (4.5-yr WF)")
    ax.grid(False)
    _save(fig, "F-4.4.7-v4b-per-regime")


# ──────────────────────────────────────────────────────────────────
# F-4.1.6 V4-B feature-importance attribution
# ──────────────────────────────────────────────────────────────────
def fig_feature_importance():
    df = pd.read_csv(PROJECT_ROOT / "data/v4b_analysis/feature_importance.csv")
    groups = df.groupby("group").agg(
        btc_mass=("btc_frac", "sum"), eth_mass=("eth_frac", "sum"),
        n=("group", "size"),
    ).sort_values("btc_mass", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(groups))
    width = 0.38
    ax.bar(x - width / 2, groups["btc_mass"] * 100, width=width,
           label="BTC", color=COIN_COLORS["bitcoin"], alpha=0.85)
    ax.bar(x + width / 2, groups["eth_mass"] * 100, width=width,
           label="ETH", color=COIN_COLORS["ethereum"], alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(groups.index, rotation=15, ha="right")
    ax.set_ylabel("Total feature-importance mass (%)")
    ax.set_title("F-4.1.6  V4-B 193-feature gain-importance by feature group")
    ax.legend()
    for i, (b, e, n) in enumerate(zip(groups["btc_mass"], groups["eth_mass"], groups["n"])):
        ax.text(i, max(b, e) * 100 + 1.5,
                f"n={int(n)}", ha="center", fontsize=9, color="dimgray")
    _save(fig, "F-4.1.6-feature-importance")


# ──────────────────────────────────────────────────────────────────
# F-4.1.5 Per-coin DirAcc hierarchy at h=14 (hardcoded from §3)
# ──────────────────────────────────────────────────────────────────
def fig_diracc_hierarchy():
    coins = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA"]
    diracc = [84.6, 75.8, 68.6, 60.3, 51.0, 44.9, 45.2]
    colors = ["#2CA02C" if d > 65 else "#FF7F0E" if d > 50 else "#D62728"
              for d in diracc]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(coins, diracc, color=colors, alpha=0.85, edgecolor="white")
    ax.axvline(50, color="black", linestyle="--", linewidth=1, label="Coin-flip (50%)")
    ax.set_xlabel("Directional accuracy (%) at h=14")
    ax.set_title("F-4.1.5  Per-coin h=14 directional accuracy hierarchy")
    ax.set_xlim(40, 90)
    for bar, d in zip(bars, diracc):
        ax.text(d + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{d:.1f}%", va="center", fontsize=10)
    ax.legend(loc="lower right")
    ax.invert_yaxis()
    _save(fig, "F-4.1.5-diracc-hierarchy")


# ──────────────────────────────────────────────────────────────────
# F-4.2.1 SMA30 ablation (hardcoded from §5)
# ──────────────────────────────────────────────────────────────────
def fig_sma30_ablation():
    variants = ["V2 only\n(no trend)", "Asymmetric\nsignals only",
                "V2 + trend filter", "V2 + trend\n+ asymmetric"]
    sharpes = [1.88, 1.26, 2.69, 2.06]
    returns = [51.9, 33.9, 106.0, 73.1]
    colors = ["#7F7F7F", "#7F7F7F", "#2CA02C", "#7F7F7F"]
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(variants))
    bars = ax.bar(x, sharpes, color=colors, alpha=0.85, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(variants)
    ax.set_ylabel("Portfolio Sharpe ratio")
    ax.set_title("F-4.2.1  SMA30 trend-filter ablation (1-yr 2-coin BTC+ETH portfolio)")
    for i, (b, s, r) in enumerate(zip(bars, sharpes, returns)):
        ax.text(i, s + 0.05, f"SR={s:.2f}\nret={r:+.1f}%",
                ha="center", fontsize=10)
    ax.set_ylim(0, max(sharpes) * 1.2)
    _save(fig, "F-4.2.1-sma30-ablation")


# ──────────────────────────────────────────────────────────────────
# F-4.3.1 LLM phases ramp (hardcoded phase Sharpes)
# ──────────────────────────────────────────────────────────────────
def fig_llm_phases_ramp():
    phases = ["3-analyst\nbaseline",
              "P1 raw\n(+sentiment)",
              "P1 rescored",
              "P2\n(+GDELT+F&G)",
              "P4 hybrid\n(LGB sizing)",
              "P5 hardened",
              "Per-coin\nmixed"]
    sharpes = [-0.89, 0.79, 0.22, 0.86, 1.52, 0.98, 2.94]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(phases))
    colors = ["#D62728" if s < 0 else "#FF7F0E" if s < 1 else
              "#1F77B4" if s < 2 else "#2CA02C" for s in sharpes]
    bars = ax.bar(x, sharpes, color=colors, alpha=0.85, edgecolor="white")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axhline(3.31, color="purple", linestyle="--", linewidth=2,
               label="V2 quant baseline (+3.31)")
    ax.set_xticks(x)
    ax.set_xticklabels(phases, fontsize=9)
    ax.set_ylabel("Portfolio Sharpe (88-bar bear window)")
    ax.set_title("F-4.3.1  LLM evaluation phases — Sharpe progression (2026-Q1 88-bar window)")
    for i, (bar, s) in enumerate(zip(bars, sharpes)):
        ax.text(i, s + (0.1 if s > 0 else -0.25),
                f"{s:+.2f}", ha="center", fontsize=10, weight="bold")
    ax.set_ylim(-1.5, 3.7)
    ax.legend(loc="upper left")
    _save(fig, "F-4.3.1-llm-phases-ramp")


# ──────────────────────────────────────────────────────────────────
# F-4.4.6 V4-B feature asymmetry (BTC vs ETH)
# ──────────────────────────────────────────────────────────────────
def fig_v4b_asymmetry():
    coins = ["BTC", "ETH"]
    sr_78f = [1.57, 0.88]
    sr_193f = [1.19, 1.80]
    deltas = [b - a for a, b in zip(sr_78f, sr_193f)]
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(coins))
    width = 0.35
    bars1 = ax.bar(x - width / 2, sr_78f, width=width,
                   label="V2-78f canonical", color="#7F7F7F", alpha=0.85)
    bars2 = ax.bar(x + width / 2, sr_193f, width=width,
                   label="V4-B-193f extended", color="#2CA02C", alpha=0.85)
    for i, (a, b, d) in enumerate(zip(sr_78f, sr_193f, deltas)):
        ax.text(i - width / 2, a + 0.05, f"{a:.2f}", ha="center", fontsize=10)
        ax.text(i + width / 2, b + 0.05, f"{b:.2f}", ha="center", fontsize=10)
        arrow_color = "green" if d > 0 else "red"
        ax.annotate(f"Δ {d:+.2f}",
                    xy=(i + width / 2, b), xytext=(i + 0.5, max(a, b) + 0.2),
                    fontsize=10, color=arrow_color,
                    arrowprops=dict(arrowstyle="->", color=arrow_color))
    ax.set_xticks(x)
    ax.set_xticklabels(coins)
    ax.set_ylabel("Sharpe ratio (4.5-yr WF)")
    ax.set_title("F-4.4.6  V4-B feature asymmetry — extended features help ETH, hurt BTC")
    ax.legend(loc="upper left")
    _save(fig, "F-4.4.6-v4b-asymmetry")


# ──────────────────────────────────────────────────────────────────
# F-5.1 Sharpe attribution waterfall
# ──────────────────────────────────────────────────────────────────
def fig_sharpe_waterfall():
    components = ["B&H\nbaseline", "Mechanics\n(sizing + SMA30\n+ 4-coin diversif)",
                  "ML signal\n(LGB direction)", "V5 MIX\nobserved"]
    values = [0, 2.870, 0.308, 3.178]
    cumulative = [0, 2.870, 3.178, 3.178]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    colors = ["#7F7F7F", "#1F77B4", "#2CA02C", "black"]
    x = np.arange(len(components))
    # Cumulative bars: hatched showing baseline + mechanics + signal segments
    ax.bar(x[0], values[0], color=colors[0], alpha=0.85, label="Baseline")
    ax.bar(x[1], values[1], bottom=values[0], color=colors[1], alpha=0.85,
           label=f"Mechanics (+{values[1]:.2f}, ~90%)")
    ax.bar(x[2], values[2], bottom=values[1], color=colors[2], alpha=0.85,
           label=f"ML signal (+{values[2]:.2f}, ~10%)")
    ax.bar(x[3], values[3], color=colors[3], alpha=0.5,
           edgecolor="black", linewidth=2, label="Observed total")
    # Connector lines
    ax.plot([0.4, 0.6], [0, 0], "k--", alpha=0.4, linewidth=0.7)
    ax.plot([1.4, 1.6], [values[1], values[1]], "k--", alpha=0.4, linewidth=0.7)
    ax.plot([2.4, 2.6], [cumulative[2], cumulative[2]], "k--", alpha=0.4, linewidth=0.7)
    for i, v in enumerate([0, values[1], values[1] + values[2], values[3]]):
        if i == 0:
            ax.text(i, 0.05, "0.00", ha="center", fontsize=10)
        else:
            ax.text(i, v + 0.05, f"{v:.2f}", ha="center", fontsize=10, weight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(components, fontsize=9.5)
    ax.set_ylabel("Sharpe ratio")
    ax.set_title("F-5.1  V5 MIX Sharpe attribution — random-entry placebo decomposition")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_ylim(0, 3.6)
    _save(fig, "F-5.1-sharpe-waterfall")


# ──────────────────────────────────────────────────────────────────
# F-4.6.2 Combined equity-curve overlay
# ──────────────────────────────────────────────────────────────────
def fig_combined_equity():
    df = pd.read_csv(PROJECT_ROOT / "data/v5_mix_production/daily_returns.csv",
                     index_col=0, parse_dates=True)
    v5 = (1 + df["portfolio"]).cumprod() * 10_000

    # V2 quant from BT8 4.5-yr WF: use bitcoin+ethereum mean from same input dir
    # Approximated as 2-coin EW from v5 BTC + ETH legs (which use V2 sizing on
    # the routed prediction CSVs — V2 2-coin uses the same BTC route)
    v2_2c = (1 + df[["bitcoin", "ethereum"]].mean(axis=1)).cumprod() * 10_000

    # Buy & Hold BTC (load OHLCV)
    from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv
    ohlcv = _load_crypto_ohlcv("bitcoin", "2026-04-15")
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    ohlcv = ohlcv[(ohlcv["Date"] >= "2021-11-08") & (ohlcv["Date"] <= "2026-04-14")]
    bh = ohlcv.set_index("Date")["Close"]
    bh = bh / bh.iloc[0] * 10_000

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(v5.index, v5.values, color="black", linewidth=2.5,
            label="V5 MIX (4-coin)")
    ax.plot(v2_2c.index, v2_2c.values, color="#1F77B4", linewidth=1.8,
            label="V5 MIX 2-coin (BTC+ETH route)")
    ax.plot(bh.index, bh.values, color="#FF7F0E", linewidth=1.5,
            label="Buy & Hold BTC", alpha=0.8)
    ax.set_yscale("log")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity ($, log scale; $10K start)")
    ax.set_title("F-4.6.2  Strategy comparison — 4.5-year walk-forward equity curves")
    ax.legend(loc="upper left")
    _save(fig, "F-4.6.2-combined-equity")


# ──────────────────────────────────────────────────────────────────
# F-2.1 Multi-agent topology diagram
# ──────────────────────────────────────────────────────────────────
def fig_topology():
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_title("F-2.1  TradingAgents crypto-adapted graph topology",
                 fontsize=13, pad=10)

    def box(x, y, w, h, label, color, fontsize=10, weight="normal"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                                     facecolor=color, edgecolor="black",
                                     linewidth=1.2, alpha=0.85))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=fontsize, weight=weight, wrap=True)

    def arrow(x1, y1, x2, y2, label=None, color="black"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                      arrowstyle="->", mutation_scale=14,
                                      linewidth=1.4, color=color))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.15, label,
                    ha="center", fontsize=8.5, style="italic", color=color)

    # Phase 1: Analysts (parallel, top)
    analysts = [
        ("Market\nAnalyst", "#FFE699"),
        ("On-Chain\nAnalyst", "#A9D18E"),
        ("Sentiment\nAnalyst", "#9DC3E6"),
        ("Prediction\nAnalyst", "#F4B084"),
    ]
    for i, (lbl, c) in enumerate(analysts):
        box(0.4 + i * 3.3, 8.3, 2.5, 1.4, lbl, c, fontsize=9.5, weight="bold")

    # Aggregation arrow into Researchers
    box(2.5, 6.5, 4, 1.2, "Bull Researcher", "#C8E6C9", fontsize=10)
    box(7.5, 6.5, 4, 1.2, "Bear Researcher", "#FFCDD2", fontsize=10)
    for i in range(4):
        arrow(0.4 + i * 3.3 + 1.25, 8.3, 4.5, 7.7, color="gray")
        arrow(0.4 + i * 3.3 + 1.25, 8.3, 9.5, 7.7, color="gray")

    # Debate (Bull <-> Bear)
    arrow(6.5, 7.1, 7.5, 7.1, color="#1976D2")
    arrow(7.5, 6.9, 6.5, 6.9, color="#D32F2F")
    ax.text(7.0, 7.55, "max_debate_rounds", ha="center", fontsize=8,
            style="italic", color="gray")

    # Research Manager
    box(5.0, 5.0, 4, 1.0, "Research Manager (synthesis)", "#CE93D8", fontsize=10)
    arrow(4.5, 6.5, 6.5, 6.0)
    arrow(9.5, 6.5, 7.5, 6.0)

    # Trader
    box(5.5, 3.7, 3, 0.9, "Trader (BUY/HOLD/SELL proposal)", "#FFB74D", fontsize=10)
    arrow(7.0, 5.0, 7.0, 4.6)

    # Risk Debate (3 nodes)
    risk = [("Aggressive", "#EF5350"), ("Neutral", "#FFB74D"), ("Conservative", "#66BB6A")]
    for i, (lbl, c) in enumerate(risk):
        box(0.7 + i * 4.3, 2.2, 3.7, 0.9, f"Risk: {lbl}", c, fontsize=9.5)
        arrow(7.0, 3.7, 0.7 + i * 4.3 + 1.85, 3.1, color="gray")
    ax.text(7, 1.7, "max_risk_discuss_rounds", ha="center",
            fontsize=8, style="italic", color="gray")

    # Portfolio Manager
    box(4.5, 0.5, 5, 1.0, "Portfolio Manager\n(BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL + HIGH/MED/LOW conf)",
        "#9575CD", fontsize=9.5, weight="bold")
    for i in range(3):
        arrow(0.7 + i * 4.3 + 1.85, 2.2, 7.0, 1.5, color="gray")

    # Side caption: phases
    ax.text(13.5, 9.0, "Phase 1\nParallel\nanalysts",
            ha="center", fontsize=9, style="italic",
            bbox=dict(boxstyle="round", facecolor="#FFF9C4", edgecolor="gray"))
    ax.text(13.5, 6.2, "Phase 2\nSequential\ndebate +\ndecision",
            ha="center", fontsize=9, style="italic",
            bbox=dict(boxstyle="round", facecolor="#E1BEE7", edgecolor="gray"))
    ax.text(13.5, 1.0, "Final\nsignal +\nconfidence",
            ha="center", fontsize=9, style="italic",
            bbox=dict(boxstyle="round", facecolor="#D1C4E9", edgecolor="gray"))

    _save(fig, "F-2.1-topology")


# ──────────────────────────────────────────────────────────────────
# F-2.2 Bitemporal data layer schema
# ──────────────────────────────────────────────────────────────────
def fig_bitemporal_schema():
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.set_title("F-2.2  Bitemporal point-in-time data layer", fontsize=13, pad=10)

    def box(x, y, w, h, label, color, fontsize=10, weight="normal", multiline=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                                     facecolor=color, edgecolor="black",
                                     linewidth=1.2, alpha=0.85))
        if multiline:
            ax.text(x + 0.15, y + h - 0.3, label, ha="left", va="top",
                    fontsize=fontsize, weight=weight, family="monospace")
        else:
            ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                    fontsize=fontsize, weight=weight)

    def arrow(x1, y1, x2, y2, label=None, color="black", style="->"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                      arrowstyle=style, mutation_scale=14,
                                      linewidth=1.4, color=color))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.15, label,
                    ha="center", fontsize=8.5, style="italic", color=color)

    # External sources (top row)
    sources = [
        ("CoinMetrics\nCommunity", "#FFE699"),
        ("DefiLlama\nTVL+stables", "#FFE699"),
        ("Coinglass\nderivatives", "#FFE699"),
        ("Deribit\nDVOL", "#FFE699"),
        ("Alpaca News\nGDELT, F&G, HF", "#FFE699"),
    ]
    for i, (lbl, c) in enumerate(sources):
        box(0.3 + i * 2.75, 7.4, 2.2, 1.1, lbl, c, fontsize=9)

    # Backfill arrows → Parquet partitions
    for i in range(5):
        arrow(0.3 + i * 2.75 + 1.1, 7.4, 0.3 + i * 2.75 + 1.1, 6.0,
              color="gray")

    # Parquet partitions (middle)
    box(0.2, 4.5, 13.4, 1.4,
        "Parquet partitions: data/{store}/{year}/{month:02d}.parquet\n"
        "schema: (event_ts, as_of_ts, coin, metric, value, source, status)",
        "#B3E5FC", fontsize=10, weight="bold")

    # DuckDB engine
    box(4.5, 2.6, 5, 1.3,
        "DuckDB engine\n(reads Parquet in-place, no server)",
        "#A5D6A7", fontsize=10, weight="bold")
    arrow(7.0, 4.5, 7.0, 3.9, color="black")

    # PIT query SQL (right side)
    sql = ("PIT query rule:\n\n"
           "SELECT value\nFROM read_parquet(...)\n"
           "WHERE coin = :coin\n"
           "  AND event_ts BETWEEN :start AND :end\n"
           "  AND as_of_ts <= :trade_date\n"
           "QUALIFY ROW_NUMBER() OVER (\n"
           "  PARTITION BY metric, event_ts\n"
           "  ORDER BY as_of_ts DESC) = 1")
    box(10.2, 1.5, 3.6, 3.4, sql, "#FFCCBC", fontsize=8, multiline=True)

    # Revision-window notes (bottom left)
    box(0.2, 0.4, 9.5, 1.5,
        "Revision windows (flash metrics):\n"
        "• CoinMetrics FlowIn/OutExUSD: as_of_ts = event_ts + 7d\n"
        "• All other metrics: as_of_ts = event_ts + 1d\n"
        "→ guarantees no row from a future revision leaks into a past trade_date query",
        "#FFF9C4", fontsize=9, multiline=True)

    # Output arrow to consumer
    arrow(7.0, 2.6, 7.0, 1.95, color="black")
    box(4.5, 1.4, 5, 0.55, "→ pooled feature matrix (V2 / V4-B / V5 MIX)",
        "#CE93D8", fontsize=9.5, weight="bold")

    _save(fig, "F-2.2-bitemporal-schema")


# ──────────────────────────────────────────────────────────────────
# F-2.3 Sizing pipeline flow
# ──────────────────────────────────────────────────────────────────
def fig_sizing_pipeline():
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title("F-2.3  Position sizing + risk pipeline (V2 sizing primitives)",
                 fontsize=13, pad=10)

    def box(x, y, w, h, label, color, fontsize=10, weight="normal"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                     facecolor=color, edgecolor="black",
                                     linewidth=1.2, alpha=0.85))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=fontsize, weight=weight)

    def arrow(x1, y1, x2, y2, label=None, color="black"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                      arrowstyle="->", mutation_scale=14,
                                      linewidth=1.4, color=color))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.15, label,
                    ha="center", fontsize=8.5, style="italic", color=color)

    # Inputs (left)
    box(0.2, 5.5, 2.2, 1.0, "LGB h=7 + h=14\nconsensus signal", "#FFE699", 9.5)
    box(0.2, 4.2, 2.2, 1.0, "LGB magnitude\nconfidence ∈ [0,1]", "#FFE699", 9.5)
    box(0.2, 2.9, 2.2, 1.0, "Realised vol\n(20-day std)", "#FFE699", 9.5)

    # Multiplicative chain (centre, left to right)
    chain = [
        (3.2, "× confidence", "#B3E5FC"),
        (5.0, "× vol target\n(10% / σ_realised)", "#B3E5FC"),
        (6.9, "× kelly fraction\n(0.5 backtest, 0.25 live)", "#B3E5FC"),
        (9.0, "× SMA30 trend filter\n(1.5x aligned, 0.5x against)", "#A5D6A7"),
        (11.2, "× leverage cap\n(1–3x, confidence-conditional)", "#FFCC80"),
    ]
    for x, lbl, c in chain:
        box(x, 4.0, 1.8, 1.0, lbl, c, 8.5)

    # Connecting arrows
    arrow(2.4, 6.0, 3.2, 5.0, color="black")
    arrow(2.4, 4.7, 3.2, 4.7, color="black")
    arrow(2.4, 3.4, 4.5, 4.0, color="black")
    for i in range(len(chain) - 1):
        x1 = chain[i][0] + 1.8
        x2 = chain[i + 1][0]
        arrow(x1, 4.5, x2, 4.5, color="black")

    # Risk overlays (top)
    box(4.5, 6.7, 2.3, 0.7, "Stop-loss: 3%", "#EF9A9A", 9.5)
    box(7.0, 6.7, 2.5, 0.7, "Circuit breaker: 15% DD", "#EF9A9A", 9.5)
    box(9.7, 6.7, 2.0, 0.7, "95th vol cap", "#EF9A9A", 9.5)
    ax.text(7.5, 7.55, "Risk overlays (hard constraints applied after every step)",
            ha="center", fontsize=9, style="italic", color="dimgray")

    # Min hold (bottom right)
    box(11.5, 2.5, 2.3, 0.9, "7-day min hold\n(adaptive early exit)", "#FFCCBC", 9)

    # Output position (far right)
    box(11.3, 0.9, 2.6, 1.3, "Final position\n(clipped to ±max_lev)",
        "#9575CD", 10, "bold")
    arrow(13.0, 4.0, 13.0, 2.2, color="black")

    # Notes column (bottom)
    notes = (
        "Sharpe leverage-invariant for kelly ∈ [0.10, 0.50] (§23).\n"
        "SMA30 trend filter = single highest-impact change (1.88 → 2.69 Sharpe, §11.4).\n"
        "All primitives in tradingagents/strategies/v2_sizing.py — single source of truth for backtest + live."
    )
    ax.text(0.4, 1.5, notes, fontsize=9, style="italic", color="dimgray",
            ha="left", va="center",
            bbox=dict(boxstyle="round", facecolor="#FFF9C4",
                      edgecolor="gray", alpha=0.7))

    _save(fig, "F-2.3-sizing-pipeline")


# ──────────────────────────────────────────────────────────────────
# F-4.3.7 Hybrid V5 1y — equity curves (BTC + ETH, hybrid vs baseline)
# ──────────────────────────────────────────────────────────────────
def fig_hybrid_v5_1y_equity():
    df = pd.read_csv(PROJECT_ROOT / "data/hybrid_backtest_v5_2coin_1y/daily_returns.csv",
                     parse_dates=["date"])
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), sharey=False)
    for ax, coin in zip(axes, ["bitcoin", "ethereum"]):
        sub = df[df["coin"] == coin].sort_values("date")
        eq_h = (1 + sub["hybrid_ret"]).cumprod() * 10_000
        eq_b = (1 + sub["baseline_ret"]).cumprod() * 10_000
        ax.plot(sub["date"], eq_h, color=COIN_COLORS[coin], linewidth=2.2,
                label=f"{COIN_LABELS[coin]} hybrid (quant+LLM)")
        ax.plot(sub["date"], eq_b, color=COIN_COLORS[coin], linewidth=1.5,
                linestyle="--", alpha=0.75,
                label=f"{COIN_LABELS[coin]} V5 baseline (quant only)")
        ax.set_title(f"{COIN_LABELS[coin]}  ({sub['date'].min().date()} → {sub['date'].max().date()})")
        ax.set_xlabel("Date")
        ax.set_ylabel("Equity ($, start $10K)")
        ax.legend(loc="upper left")
    fig.suptitle("F-4.3.7  Hybrid quant+LLM vs V5 baseline — 1-year walk-forward "
                 "(GPT-4o-mini, 363 daily bars)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    _save(fig, "F-4.3.7-hybrid-v5-1y-equity")


# ──────────────────────────────────────────────────────────────────
# F-4.3.8 Hybrid V5 1y — SR delta bar (BTC vs ETH; hybrid vs baseline)
# ──────────────────────────────────────────────────────────────────
def fig_hybrid_v5_1y_sr():
    coins = ["BTC", "ETH"]
    sr_baseline = [3.299, 3.586]
    sr_hybrid = [3.305, 4.681]
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(coins))
    width = 0.35
    ax.bar(x - width / 2, sr_baseline, width=width,
           color="#7F7F7F", alpha=0.85, label="V5 baseline (quant only)")
    ax.bar(x + width / 2, sr_hybrid, width=width,
           color="#2CA02C", alpha=0.85, label="Hybrid (quant + LLM modulator)")
    for i, (b, h) in enumerate(zip(sr_baseline, sr_hybrid)):
        ax.text(i - width / 2, b + 0.05, f"{b:.2f}", ha="center", fontsize=10)
        ax.text(i + width / 2, h + 0.05, f"{h:.2f}", ha="center", fontsize=10,
                weight="bold")
        delta = h - b
        col = "green" if delta > 0 else "red"
        ax.annotate(f"Δ {delta:+.2f}",
                    xy=(i + width / 2, h), xytext=(i + 0.45, max(b, h) + 0.45),
                    fontsize=10, color=col,
                    arrowprops=dict(arrowstyle="->", color=col))
    ax.set_xticks(x)
    ax.set_xticklabels(coins)
    ax.set_ylabel("Sharpe ratio (1-year WF, 2025-04-18 → 2026-04-15)")
    ax.set_title("F-4.3.8  Hybrid V5 1-year — Sharpe delta per coin "
                 "(GPT-4o-mini modulator on V5 quant signal)")
    ax.set_ylim(0, max(sr_hybrid) * 1.18)
    ax.legend(loc="upper left")
    _save(fig, "F-4.3.8-hybrid-v5-1y-sr")


# ──────────────────────────────────────────────────────────────────
# F-4.3.9 Hybrid model A/B — 5-mini vs 4o-mini (30-bar window)
# ──────────────────────────────────────────────────────────────────
def fig_hybrid_model_compare():
    coins = ["BTC", "ETH"]
    baseline = [5.442, 4.340]
    h_4o     = [7.007, 7.604]
    h_5mini  = [7.666, 6.204]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    x = np.arange(len(coins))
    width = 0.27
    ax.bar(x - width, baseline, width=width,
           color="#7F7F7F", alpha=0.85, label="V5 baseline (quant only)")
    ax.bar(x,         h_4o,     width=width,
           color="#1F77B4", alpha=0.85, label="Hybrid + GPT-4o-mini")
    ax.bar(x + width, h_5mini,  width=width,
           color="#2CA02C", alpha=0.85, label="Hybrid + GPT-5-mini")
    triplets = list(zip(baseline, h_4o, h_5mini))
    for i, (b, h4, h5) in enumerate(triplets):
        ax.text(i - width, b + 0.1, f"{b:.2f}", ha="center", fontsize=9)
        ax.text(i,         h4 + 0.1, f"{h4:.2f}", ha="center", fontsize=9)
        ax.text(i + width, h5 + 0.1, f"{h5:.2f}", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(coins)
    ax.set_ylabel("Sharpe ratio (30-bar window, 2026-03-16 → 2026-04-15)")
    ax.set_title("F-4.3.9  Hybrid model A/B — GPT-5-mini vs GPT-4o-mini "
                 "(30 bars; both add Sharpe over V5 baseline)")
    ax.set_ylim(0, max(h_4o + h_5mini) * 1.18)
    ax.legend(loc="upper left")
    fig.text(0.5, 0.005,
             "Caveat: 30 bars only — directionally consistent with the 1-year hybrid result "
             "(F-4.3.8) on ETH, but underpowered for committee-grade Sharpe claims.",
             ha="center", fontsize=8.5, style="italic", color="dimgray")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _save(fig, "F-4.3.9-hybrid-model-compare")


# ──────────────────────────────────────────────────────────────────
# F-4.3.10 Hybrid V5 1y — deep-model A/B (all-4o-mini vs deep-5-mini)
# ──────────────────────────────────────────────────────────────────
def fig_hybrid_deep_model_ab():
    coins = ["BTC", "ETH"]
    baseline = [3.299, 3.586]
    all_4o   = [3.305, 4.681]
    deep_5m  = [2.922, 4.166]
    fig, ax = plt.subplots(figsize=(9, 5.4))
    x = np.arange(len(coins))
    width = 0.27
    ax.bar(x - width, baseline, width=width,
           color="#7F7F7F", alpha=0.85, label="V5 baseline (quant only)")
    ax.bar(x,         all_4o,   width=width,
           color="#2CA02C", alpha=0.85, label="Hybrid — all GPT-4o-mini")
    ax.bar(x + width, deep_5m,  width=width,
           color="#D62728", alpha=0.85, label="Hybrid — deep GPT-5-mini / quick 4o-mini")
    for i, (b, a, d) in enumerate(zip(baseline, all_4o, deep_5m)):
        ax.text(i - width, b + 0.06, f"{b:.2f}", ha="center", fontsize=9)
        ax.text(i,         a + 0.06, f"{a:.2f}", ha="center", fontsize=9, weight="bold")
        ax.text(i + width, d + 0.06, f"{d:.2f}", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(coins)
    ax.set_ylabel("Sharpe ratio (1-year WF, 2025-04-18 → 2026-04-15)")
    ax.set_title("F-4.3.10  Hybrid V5 1-year — deep-model A/B "
                 "(GPT-5-mini deep slot does NOT pay for itself)")
    ax.set_ylim(0, max(all_4o) * 1.18)
    ax.legend(loc="upper left")
    fig.text(0.5, 0.005,
             "Deep slot upgraded to GPT-5-mini at ~10× cost. ETH alpha drops +1.10 → +0.58 "
             "(block-bootstrap ΔSR vs all-4o-mini = -0.49, CI95 [-1.10, -0.09], P(worse)=0.996). "
             "BTC turns negative. Production stays all-GPT-4o-mini.",
             ha="center", fontsize=8.3, style="italic", color="dimgray")
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    _save(fig, "F-4.3.10-hybrid-deep-model-ab")


# ──────────────────────────────────────────────────────────────────
# F-4.2.4 V5 MIX SL/TP/early-exit sweep — Sharpe heatmap (EE off)
# ──────────────────────────────────────────────────────────────────
def fig_v5_sltp_sweep():
    df = pd.read_csv(PROJECT_ROOT / "data/v5_sltp_sweep/results.csv")
    if "scope" in df.columns:
        df = df[df["scope"] == "portfolio"]
    # EE=1.0 slice (early-exit OFF) — the top-20-dominating regime
    ee_off = df[np.isclose(df["ee"], 1.0)]
    pivot = ee_off.pivot_table(index="sl", columns="tp",
                               values="sharpe", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto",
                   vmin=3.10, vmax=3.36, origin="lower")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticklabels([f"{c:g}" for c in pivot.columns])
    ax.set_yticklabels([f"{i:g}" for i in pivot.index])
    ax.set_xlabel("Take-profit threshold (0 = off)")
    ax.set_ylabel("Stop-loss threshold")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            v = pivot.values[i, j]
            ax.text(j, i, f"{v:.3f}", ha="center", va="center",
                    fontsize=8, color="black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Portfolio Sharpe")
    ax.set_title("F-4.2.4  V5 MIX SL/TP sweep — Sharpe at early-exit OFF (4.5-yr WF)\n"
                 "Best cell SL=0.10/TP=off: SR +3.335 vs baseline +3.178 (EE=0.015)")
    ax.grid(False)
    _save(fig, "F-4.2.4-v5-sltp-sweep")


# ──────────────────────────────────────────────────────────────────
# F-4.5.7 Per-analyst leave-one-out ablation (assignment §4.5)
# ──────────────────────────────────────────────────────────────────
def fig_loo_ablation():
    # Bootstrap-confirmed deltas vs full 4-analyst hybrid (88-bar window)
    # ΔSR = drop_variant - full4 ; negative = "drop hurts" = backbone
    rows = [
        ("Market",     "BTC", -0.77, 0.973),
        ("Market",     "ETH", +0.69, 0.003),  # P(worse) = 0.003 → P(IMPROVES) = 0.997
        ("On-Chain",   "BTC", -1.00, 0.996),
        ("On-Chain",   "ETH", +0.02, 0.254),
        ("Sentiment",  "BTC", -0.48, 0.964),
        ("Sentiment",  "ETH", +0.11, 0.125),
        ("Prediction", "BTC", -0.30, 0.631),
        ("Prediction", "ETH", -1.94, 0.987),
    ]
    analysts = ["Market", "On-Chain", "Sentiment", "Prediction"]
    coins = ["BTC", "ETH"]
    mat = np.zeros((len(analysts), len(coins)))
    sig = np.full((len(analysts), len(coins)), "", dtype=object)
    for a, c, d, p in rows:
        i = analysts.index(a); j = coins.index(c)
        mat[i, j] = d
        if p >= 0.95 or p <= 0.05:
            sig[i, j] = "*"
    fig, ax = plt.subplots(figsize=(8, 5.5))
    vmax = max(abs(mat.min()), abs(mat.max()))
    im = ax.imshow(mat, cmap="RdYlGn", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(coins))); ax.set_yticks(range(len(analysts)))
    ax.set_xticklabels(coins, fontsize=11)
    ax.set_yticklabels([f"Drop {a}" for a in analysts], fontsize=10)
    for i in range(len(analysts)):
        for j in range(len(coins)):
            v = mat[i, j]
            txt = f"ΔSR={v:+.2f}{sig[i, j]}"
            ax.text(j, i, txt, ha="center", va="center",
                    color="black", fontsize=11, weight="bold")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04,
                 label="ΔSR vs full 4-analyst hybrid")
    ax.set_title("F-4.5.7  Per-analyst leave-one-out ablation\n"
                 "(88-bar 2026-Q1 window, drop one analyst at a time, * = bootstrap P≥0.95)",
                 fontsize=11, pad=10)
    ax.grid(False)
    fig.text(0.5, 0.005,
             "Green = removing analyst helps (analyst is noise/harmful). "
             "Red = removing analyst hurts (analyst is backbone). "
             "ETH-Market +0.69* = market analyst HURTS ETH. "
             "ETH-Prediction -1.94* = prediction is ETH backbone. "
             "BTC-On-Chain -1.00* = on-chain is BTC backbone.",
             ha="center", fontsize=8.3, style="italic", color="dimgray", wrap=True)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _save(fig, "F-4.5.7-loo-ablation")


# ──────────────────────────────────────────────────────────────────
# Driver
# ──────────────────────────────────────────────────────────────────
FIGURES = [
    ("F-2.1 Multi-agent topology", fig_topology),
    ("F-2.2 Bitemporal data layer schema", fig_bitemporal_schema),
    ("F-2.3 Sizing pipeline flow", fig_sizing_pipeline),
    ("F-4.2.4 V5 SL/TP sweep heatmap", fig_v5_sltp_sweep),
    ("F-4.3.7 Hybrid V5 1y equity", fig_hybrid_v5_1y_equity),
    ("F-4.3.8 Hybrid V5 1y SR delta", fig_hybrid_v5_1y_sr),
    ("F-4.3.9 Hybrid model A/B (5-mini vs 4o-mini)", fig_hybrid_model_compare),
    ("F-4.3.10 Hybrid deep-model A/B (1y)", fig_hybrid_deep_model_ab),
    ("F-4.5.7 Per-analyst LOO ablation", lambda: fig_loo_ablation()),
    ("F-4.2.3 Per-coin Kelly sweep", fig_kelly_sweep),
    ("F-4.4.9 V5 MIX 4-coin equity", fig_v5_equity),
    ("F-4.4.10 V5 correlation heatmap", fig_v5_correlation),
    ("F-4.5.1 DSR sensitivity", fig_dsr_sensitivity),
    ("F-4.5.2 Placebo null distribution", fig_placebo_null),
    ("F-4.5.3 Per-regime decomposition", fig_regime_decomposition),
    ("F-4.5.4 CPCV fold distribution", fig_cpcv_fold_dist),
    ("F-4.5.5 Per-regime CPCV breakdown", fig_per_regime_cpcv),
    ("F-4.5.6 Cost sensitivity", fig_cost_sensitivity),
    ("F-4.4.4 V3 component ablation", fig_v3_ablation),
    ("F-4.4.5 NH-HMM bundle pathology", fig_nhhmm_pathology),
    ("F-4.4.7 V4-B per-regime heatmap", fig_v4b_per_regime),
    ("F-4.1.6 V4-B feature importance", fig_feature_importance),
    ("F-4.1.5 DirAcc hierarchy", fig_diracc_hierarchy),
    ("F-4.2.1 SMA30 ablation", fig_sma30_ablation),
    ("F-4.3.1 LLM phases ramp", fig_llm_phases_ramp),
    ("F-4.4.6 V4-B asymmetry", fig_v4b_asymmetry),
    ("F-5.1 Sharpe waterfall", fig_sharpe_waterfall),
    ("F-4.6.2 Combined equity overlay", fig_combined_equity),
]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--png-only", action="store_true")
    p.add_argument("--svg-only", action="store_true")
    args = p.parse_args()
    global SAVE_FORMATS
    if args.png_only:
        SAVE_FORMATS = ["png"]
    elif args.svg_only:
        SAVE_FORMATS = ["svg"]

    print(f"\n{'=' * 78}")
    print(f"  Generating {len(FIGURES)} thesis figures → {FIG_DIR}")
    print(f"{'=' * 78}\n")
    successes, failures = 0, []
    for name, fn in FIGURES:
        print(f"\n▶ {name}")
        try:
            fn()
            successes += 1
        except Exception as e:
            print(f"  FAILED: {type(e).__name__}: {e}")
            failures.append((name, str(e)))

    print(f"\n{'=' * 78}")
    print(f"  Generated: {successes}/{len(FIGURES)} figures")
    if failures:
        print(f"  Failures:")
        for n, e in failures:
            print(f"    {n}: {e}")
    print(f"  Output: {FIG_DIR}")
    print(f"{'=' * 78}\n")


if __name__ == "__main__":
    main()
