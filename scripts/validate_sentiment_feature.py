#!/usr/bin/env python
"""Sentiment-feature A/B validation — pre-registered acceptance gates (Task 10).

Compares the V2/V5 strategy pipeline run on a "base" prediction route (no
sentiment features) against a "sent" route (same route + PIT sentiment-index
features, see `docs/superpowers/specs/2026-07-03-quant-first-sentiment-and-
model-improvements-design.md`), per coin {bitcoin, ethereum} and per sentiment
engine {llm, bert}.

Reuses the canonical V5 wiring verbatim — `baseline_v5_mix.run_coin` (which in
turn wires `tradingagents.strategies.v2_sizing` primitives with the frozen V5
config: term-structure h7+h14 consensus, confidence_ref 0.05, asymmetric,
kelly 0.5, vol-target 0.10, max leverage 3.0, 7-day min hold, 0.015 early
exit, SMA30 trend filter 1.5x, 3% stop) — so only the predictions directory
differs between arms.

Gate (pre-registered, `gate_verdict`): SHIP iff the bootstrap probability that
the sentiment arm's Sharpe exceeds the base arm's Sharpe is >= 0.90 AND the
sentiment arm's max drawdown is not more than 1 percentage point worse than
the base arm's.

Arms (fixed mapping, per coin):
    bitcoin:  base=base_78f        sent=sent_{engine}_78f
    ethereum: base=base_193f       sent=sent_{engine}_193f
Each arm directory holds `preds_lgb_h7.csv` + `preds_lgb_h14.csv` (same
schema `baseline_v5_mix._load_preds` already consumes).

Usage:
    python scripts/validate_sentiment_feature.py --engine llm
    python scripts/validate_sentiment_feature.py --engine bert --n-boot 5000
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import baseline_v5_mix as bm  # type: ignore  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)

# Annualization: crypto trades every calendar day (365/yr), unlike the
# 252-trading-day equity convention baseline_v5_mix.py uses — this script's
# acceptance gates are pre-registered against 365d-annualized Sharpe.
ANN = np.sqrt(365)

BLOCK_SIZE_DEFAULT = 21  # matches bootstrap_sharpe.py's Politis-Romano default
N_BOOT_DEFAULT = 2000
DSR_N_TRIALS = 8

# Data-quality guards on the aligned (base ∩ sent) index. Fewer overlapping
# days than MIN_OVERLAP_DAYS is not a meaningful A/B (and a zero-length path
# would crash the block bootstrap); more than MAX_NAN_FRAC of NaN days
# signals a broken arm rather than benign missing bars.
MIN_OVERLAP_DAYS = 100
MAX_NAN_FRAC = 0.01

# Wide bounds so `baseline_v5_mix.run_coin` returns the full history present
# in the predictions CSVs; --start/--end are applied afterward to the
# *aligned* (base ∩ sent) index, not to the raw pipeline input (running the
# pipeline over the full history first preserves hold-state/trend-filter
# continuity; slicing the input window would shift them).
_FULL_START = "1900-01-01"
_FULL_END = "2999-12-31"

# Fixed per-coin arm mapping (Task 10 contract).
ARMS = {
    "bitcoin": {"base": "base_78f", "sent": "sent_{engine}_78f"},
    "ethereum": {"base": "base_193f", "sent": "sent_{engine}_193f"},
}
PORTFOLIO_WEIGHTS = {"bitcoin": 0.5, "ethereum": 0.5}


def data_root() -> Path:
    return Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", "data"))


def default_pred_root() -> Path:
    return data_root() / "eval_ab"


def default_out_path(engine: str) -> Path:
    return data_root() / "sentiment_feature_ab" / engine / "summary.json"


def arm_dirs(pred_root: Path, engine: str) -> dict:
    """Resolve {coin: (base_dir, sent_dir)} under `pred_root` for `engine`."""
    out = {}
    for coin, arms in ARMS.items():
        base_dir = pred_root / arms["base"]
        sent_dir = pred_root / arms["sent"].format(engine=engine)
        out[coin] = (base_dir, sent_dir)
    return out


# ── Stats primitives ────────────────────────────────────────────────


def sharpe(returns: np.ndarray) -> float:
    """365d-annualized Sharpe: mean/std with sample std (ddof=1), no
    risk-free subtraction. ddof=1 matches pandas' `Series.std()` default used
    by `baseline_v5_mix._metrics` and this script's `_dsr_for_returns`."""
    r = np.asarray(returns, dtype=float)
    if len(r) < 2:
        return 0.0
    sd = r.std(ddof=1)
    return float(r.mean() / sd * ANN) if sd > 0 else 0.0


def max_drawdown(returns: np.ndarray) -> float:
    """Max drawdown as a positive fraction (e.g. 0.06 == 6% drawdown)."""
    r = np.asarray(returns, dtype=float)
    if len(r) == 0:
        return 0.0
    eq = (1.0 + r).cumprod()
    dd = eq / np.maximum.accumulate(eq) - 1.0
    return float(-dd.min())


def _stationary_block_indices(n: int, block_size: int, rng: np.random.Generator) -> np.ndarray:
    """Politis-Romano stationary-bootstrap index path (wraps around).

    Same algorithm as `scripts/bootstrap_sharpe.stationary_bootstrap_sample`
    (and `scripts/bootstrap_hybrid.diff_sharpe_ci`'s inline copy), but returns
    the resampled *index* path rather than resampled values so the same path
    can be applied to two paired series (base + sent) for a paired ΔSR
    bootstrap.
    """
    idx = np.empty(n, dtype=int)
    p = 1.0 / block_size
    i = int(rng.integers(0, n))
    for t in range(n):
        idx[t] = i % n
        if rng.random() < p:
            i = int(rng.integers(0, n))
        else:
            i += 1
    return idx


def bootstrap_delta_sr(
    base: np.ndarray, sent: np.ndarray, n_boot: int,
    block_size: int = BLOCK_SIZE_DEFAULT, seed: int = 42,
) -> dict:
    """Paired stationary block bootstrap of ΔSR = SR(sent) − SR(base).

    ΔSR is not a linear statistic of the paired return difference, so each
    replicate resamples a *day-index* path (shared between both series) and
    recomputes both Sharpes on that resampled path before differencing —
    not a bootstrap of the pre-computed daily diff.
    """
    base = np.asarray(base, dtype=float)
    sent = np.asarray(sent, dtype=float)
    n = min(len(base), len(sent))
    if n < 2:
        raise ValueError(f"bootstrap_delta_sr: need >= 2 paired days, got {n}")
    base, sent = base[:n], sent[:n]
    rng = np.random.default_rng(seed)
    delta_samples = np.empty(n_boot)
    for k in range(n_boot):
        idx = _stationary_block_indices(n, block_size, rng)
        delta_samples[k] = sharpe(sent[idx]) - sharpe(base[idx])
    ci_low = float(np.quantile(delta_samples, 0.025))
    ci_high = float(np.quantile(delta_samples, 0.975))
    p_pos = float((delta_samples > 0).mean())
    return {"ci_low": ci_low, "ci_high": ci_high, "p_pos": p_pos, "samples": delta_samples}


def gate_verdict(p_pos: float, maxdd_base: float, maxdd_sent: float) -> str:
    """Pre-registered acceptance gate.

    SHIP iff the bootstrap probability that the sentiment arm's Sharpe beats
    the base arm's is >= 0.90 AND the sentiment arm's max drawdown (positive
    fraction) is not more than 1 percentage point worse than the base arm's.
    """
    dd_worse = maxdd_sent - maxdd_base
    if p_pos >= 0.90 and dd_worse <= 0.01:
        return "SHIP"
    return "NO"


# ── Per-coin / portfolio A/B ─────────────────────────────────────────


def ab_metrics(
    base: np.ndarray, sent: np.ndarray, n_boot: int = N_BOOT_DEFAULT,
    block_size: int = BLOCK_SIZE_DEFAULT, seed: int = 42,
) -> dict:
    """Compute the full metrics dict for one paired (base, sent) return series."""
    sr_base = sharpe(base)
    sr_sent = sharpe(sent)
    maxdd_base = max_drawdown(base)
    maxdd_sent = max_drawdown(sent)
    boot = bootstrap_delta_sr(base, sent, n_boot, block_size, seed)
    verdict = gate_verdict(boot["p_pos"], maxdd_base, maxdd_sent)
    return {
        "n_bars": int(min(len(base), len(sent))),
        "sr_base": sr_base,
        "sr_sent": sr_sent,
        "delta_sr": sr_sent - sr_base,
        "ci_low": boot["ci_low"],
        "ci_high": boot["ci_high"],
        "p_pos": boot["p_pos"],
        "maxdd_base": maxdd_base,
        "maxdd_sent": maxdd_sent,
        "verdict": verdict,
    }


def align_arm_returns(
    base: pd.Series, sent: pd.Series, coin: str,
    start: str | None = None, end: str | None = None,
) -> tuple[pd.Series, pd.Series, int]:
    """Align two arm return series on their common date intersection
    (optionally restricted to [start, end]) and drop NaN days PAIRWISE.

    Guards (raise ValueError with a clear message):
      - aligned index shorter than MIN_OVERLAP_DAYS — too little overlap for
        a meaningful A/B (and would crash the block bootstrap downstream);
      - more than MAX_NAN_FRAC of the aligned days NaN in either arm — a
        broken arm, not benign missing bars. NaN must never reach `sharpe()`
        silently (nan comparisons are False, which deflates p_pos).

    Returns (base_aligned, sent_aligned, n_dropped_nan).
    """
    common = base.index.intersection(sent.index)
    if start is not None:
        common = common[common >= pd.Timestamp(start)]
    if end is not None:
        common = common[common <= pd.Timestamp(end)]
    common = common.sort_values()
    n = len(common)
    if n < MIN_OVERLAP_DAYS:
        raise ValueError(
            f"insufficient overlapping dates between arms for {coin}: {n} "
            f"(minimum {MIN_OVERLAP_DAYS})"
        )
    b = base.loc[common]
    s = sent.loc[common]
    nan_mask = b.isna() | s.isna()
    n_dropped = int(nan_mask.sum())
    if n_dropped > MAX_NAN_FRAC * n:
        raise ValueError(
            f"{coin}: {n_dropped}/{n} aligned days have NaN returns in at "
            f"least one arm (> {MAX_NAN_FRAC:.0%} tolerance) — arm data looks broken"
        )
    if n_dropped:
        b = b[~nan_mask]
        s = s[~nan_mask]
    return b, s, n_dropped


def _coin_arm_returns(
    coin: str, base_dir: Path, sent_dir: Path,
    start: str | None = None, end: str | None = None,
    kelly_fraction: float = 0.5,
) -> tuple[pd.Series, pd.Series, int]:
    """Run the V2/V5 pipeline for both arms of one coin, then align + clean
    them via `align_arm_returns` (common intersection, pairwise NaN drop,
    overlap/NaN guards)."""
    base_full = bm.run_coin(coin, base_dir, _FULL_START, _FULL_END, kelly_fraction=kelly_fraction)
    sent_full = bm.run_coin(coin, sent_dir, _FULL_START, _FULL_END, kelly_fraction=kelly_fraction)
    return align_arm_returns(base_full, sent_full, coin, start=start, end=end)


def run_coin_ab(
    coin: str, base_dir: Path, sent_dir: Path,
    start: str | None = None, end: str | None = None,
    kelly_fraction: float = 0.5, n_boot: int = N_BOOT_DEFAULT,
    block_size: int = BLOCK_SIZE_DEFAULT, seed: int = 42,
) -> tuple[dict, pd.Series, pd.Series]:
    """Full per-coin A/B: run both arms, align, bootstrap ΔSR, gate.

    Returns (metrics dict, aligned base returns, aligned sent returns) — the
    aligned series are returned so the caller can build the 50/50 portfolio
    row from the same per-coin paths.
    """
    base_aligned, sent_aligned, n_dropped_nan = _coin_arm_returns(
        coin, base_dir, sent_dir, start=start, end=end, kelly_fraction=kelly_fraction,
    )
    metrics = ab_metrics(
        base_aligned.values, sent_aligned.values,
        n_boot=n_boot, block_size=block_size, seed=seed,
    )
    metrics["n_days"] = int(len(base_aligned))
    metrics["n_dropped_nan"] = n_dropped_nan
    return metrics, base_aligned, sent_aligned


def _git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            sha = out.stdout.strip()
            if sha:
                return sha
    except Exception:
        pass
    return "unknown"


def _dsr_for_returns(returns: np.ndarray, n_trials: int = DSR_N_TRIALS) -> dict:
    """Deflated Sharpe Ratio (probability the observed SR survives a
    multiple-testing correction across `n_trials` independent strategies)."""
    r = np.asarray(returns, dtype=float)
    try:
        var_sr = variance_of_sr(r)
        se_sr = float(np.sqrt(var_sr))
        sd = r.std(ddof=1)
        sr_perbar = float(r.mean() / sd) if sd > 0 else 0.0
        e_max_sr = expected_max_sharpe(n_trials, var_sr)
        dsr = deflated_sharpe_ratio(sr_perbar, e_max_sr, se_sr)
    except (ValueError, ZeroDivisionError):
        return {
            "n_trials": n_trials, "dsr": None, "sr_perbar": None,
            "se_sr": None, "var_sr": None, "e_max_sr": None,
        }
    return {
        "n_trials": n_trials, "dsr": dsr, "sr_perbar": sr_perbar,
        "se_sr": se_sr, "var_sr": var_sr, "e_max_sr": e_max_sr,
    }


def run_validation(
    pred_root: Path, engine: str,
    start: str | None = None, end: str | None = None,
    kelly_fraction: float = 0.5, n_boot: int = N_BOOT_DEFAULT,
    block_size: int = BLOCK_SIZE_DEFAULT, seed: int = 42,
) -> dict:
    """Run the full A/B validation (both coins + portfolio + DSR) and return
    the summary dict that gets written to `--out`."""
    dirs = arm_dirs(pred_root, engine)

    # Deterministic per-series seed offsets (coin i → seed+i, portfolio →
    # seed+len(dirs)) so bootstraps of equal-length series don't share
    # identical resampled index paths.
    per_coin = {}
    base_series, sent_series = {}, {}
    for i, (coin, (base_dir, sent_dir)) in enumerate(dirs.items()):
        metrics, b, s = run_coin_ab(
            coin, base_dir, sent_dir, start=start, end=end,
            kelly_fraction=kelly_fraction, n_boot=n_boot,
            block_size=block_size, seed=seed + i,
        )
        per_coin[coin] = metrics
        base_series[coin] = b
        sent_series[coin] = s

    base_df = pd.DataFrame(base_series).dropna()
    sent_df = pd.DataFrame(sent_series).dropna()
    common_all = base_df.index.intersection(sent_df.index)
    base_df = base_df.loc[common_all]
    sent_df = sent_df.loc[common_all]

    port_base = bm.portfolio_return(base_df, PORTFOLIO_WEIGHTS)
    port_sent = bm.portfolio_return(sent_df, PORTFOLIO_WEIGHTS)
    portfolio = ab_metrics(
        port_base.values, port_sent.values,
        n_boot=n_boot, block_size=block_size, seed=seed + len(dirs),
    )

    dsr = _dsr_for_returns(port_sent.values, n_trials=DSR_N_TRIALS)

    return {
        "config": {
            "engine": engine,
            "n_boot": n_boot,
            "block_size": block_size,
            "kelly_fraction": kelly_fraction,
            "seed": seed,
            "window": {"start": start, "end": end},
            "pred_root": str(pred_root),
            "git_sha": _git_sha(),
        },
        "per_coin": per_coin,
        "portfolio": portfolio,
        "dsr": dsr,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", choices=["llm", "bert"], required=True,
                   help="Which sentiment-scoring engine's arm to validate.")
    p.add_argument("--pred-root", default=None,
                   help="Root dir holding the arm subdirectories "
                        "(default: {TRADINGAGENTS_DATA_ROOT or 'data'}/eval_ab)")
    p.add_argument("--out", default=None,
                   help="Output summary JSON path "
                        "(default: {DATA_ROOT}/sentiment_feature_ab/{engine}/summary.json)")
    p.add_argument("--n-boot", type=int, default=N_BOOT_DEFAULT)
    p.add_argument("--block-size", type=int, default=BLOCK_SIZE_DEFAULT)
    p.add_argument("--kelly", type=float, default=0.5)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--start", default=None, help="Optional date filter applied to the common index.")
    p.add_argument("--end", default=None, help="Optional date filter applied to the common index.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    pred_root = Path(args.pred_root) if args.pred_root else default_pred_root()
    out_path = Path(args.out) if args.out else default_out_path(args.engine)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 78}")
    print(f"  Sentiment-feature A/B validation — engine={args.engine}")
    print(f"  pred_root: {pred_root}")
    print(f"{'=' * 78}\n")

    summary = run_validation(
        pred_root, args.engine, start=args.start, end=args.end,
        kelly_fraction=args.kelly, n_boot=args.n_boot,
        block_size=args.block_size, seed=args.seed,
    )

    for coin, m in summary["per_coin"].items():
        print(f"  {coin:12s} SR base={m['sr_base']:+.3f} sent={m['sr_sent']:+.3f} "
              f"ΔSR={m['delta_sr']:+.3f}  p_pos={m['p_pos']:.3f}  "
              f"maxDD base={m['maxdd_base']:.1%} sent={m['maxdd_sent']:.1%}  "
              f"→ {m['verdict']}")
    pm = summary["portfolio"]
    print(f"\n  {'portfolio (50/50)':12s} SR base={pm['sr_base']:+.3f} sent={pm['sr_sent']:+.3f} "
          f"ΔSR={pm['delta_sr']:+.3f}  p_pos={pm['p_pos']:.3f}  "
          f"maxDD base={pm['maxdd_base']:.1%} sent={pm['maxdd_sent']:.1%}  "
          f"→ {pm['verdict']}")
    print(f"\n  DSR (n_trials={summary['dsr']['n_trials']}): {summary['dsr']['dsr']}")

    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n  Wrote: {out_path}")


if __name__ == "__main__":
    main()
