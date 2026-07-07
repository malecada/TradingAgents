#!/usr/bin/env python
"""Statistical power of the live acceptance gate (audit 2026-07-07 R5).

The §22 gate — "annualized SR over a 90-day window >= threshold" — has a
standard error of roughly sqrt((1 + SR^2/2) * A / n) on the annualized SR
(Lo 2002), which for n=90 daily bars is ~1.7-2.0. This script prints the
pass probability of the gate for a grid of true SRs so the gate's false-pass
and false-fail rates are explicit rather than implied.

Usage:
    python scripts/acceptance_gate_power.py --threshold 2.86 --n-days 90
"""

from __future__ import annotations

import argparse
import math

from scipy.stats import norm


def sr_se(true_sr_ann: float, n: int, ann: float) -> float:
    """SE of the annualized Sharpe estimator over n daily bars (Lo 2002)."""
    sr_daily = true_sr_ann / math.sqrt(ann)
    var_daily = (1 + 0.5 * sr_daily**2) / n
    return math.sqrt(var_daily) * math.sqrt(ann)


def pass_probability(true_sr: float, threshold: float, n: int, ann: float) -> float:
    se = sr_se(true_sr, n, ann)
    return 1 - norm.cdf((threshold - true_sr) / se)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--threshold", type=float, default=2.86)
    p.add_argument("--n-days", type=int, default=90)
    p.add_argument("--annualization", type=float, default=252.0)
    args = p.parse_args()

    print(f"\nGate: 'annualized SR >= {args.threshold}' over {args.n_days} bars "
          f"(A={args.annualization:.0f})")
    print(f"{'true SR':>8} | {'SE(SR_hat)':>10} | {'P(pass)':>8}")
    print("-" * 34)
    for sr in (0.0, 0.5, 1.0, 1.5, 1.9, 2.86, 3.18, 3.97):
        se = sr_se(sr, args.n_days, args.annualization)
        pp = pass_probability(sr, args.threshold, args.n_days, args.annualization)
        print(f"{sr:8.2f} | {se:10.2f} | {pp:8.1%}")
    print(
        "\nReading: the gate cannot separate a mediocre strategy from the\n"
        "backtest headline at this window length. Prefer (a) a paired daily\n"
        "live-vs-replay return regression (removes market noise), or (b) a\n"
        "longer window, and set the threshold from the CAUSAL backtest\n"
        "expectation, not the legacy same-bar one.\n"
    )


if __name__ == "__main__":
    main()
