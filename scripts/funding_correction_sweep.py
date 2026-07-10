"""Re-publish V5 MIX absolute returns with corrected funding (THESIS §32).

The V5 backtest cost model understated funding ~14x (`COSTS['funding_rate'] =
0.0001/8 ≈ 0.46 %/yr` vs measured ~6.6 %/yr).

ADAPTED 2026-07-08 (post-audit rebuild, branch rebuild/honest-2026-07): the
original version of this script (imported from `exp/carry-go-nogo` @ 9af1cc1)
called `run_coin(..., use_real_funding=real)` and passed `--real-funding` to
`baseline_strategy_v2.py`. Both were signed, per-date real-funding-series
knobs that were never merged into `scripts/baseline_v5_mix.py` /
`scripts/baseline_strategy_v2.py` — they were superseded during audit
remediation (2026-07-07) by a flat-rate cost convention:
`COSTS["funding_rate"] = 0.0001/8` (legacy, understated) vs
`FUNDING_RATE_DAILY_CAUSAL = 0.0001 * 3` (audit-corrected flat rate), selected
via `costs_for_coin(coin, convention="legacy"|"causal")`. This script now
approximates "real funding" with that flat audit-corrected rate instead of a
signed per-date series. `run_coin`'s own (unrelated) `convention` parameter —
which toggles same-day-close vs point-in-time sizing, not funding — is pinned
to "legacy" in both arms so only the funding cost varies (apples-to-apples
with how the original §32 numbers were produced). The V2 subprocess driver
gets `--funding-rate 0.0003` for the "real" arm instead of the removed
`--real-funding` flag (default is 0.0001, i.e. the legacy rate, for the
"flat" arm).

Historical §32 numbers in THESIS_FINDINGS.md were produced by the
exp/carry-go-nogo version of this script (signed real funding), not this one.

Usage:
    python scripts/funding_correction_sweep.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from scripts.baseline_v5_mix import (
    DEFAULT_ROUTING,
    PORTFOLIO_WEIGHTS,
    PROJECT_ROOT,
    _metrics,
    costs_for_coin,
    portfolio_return,
    run_coin,
)

START, END = "2021-11-07", "2026-04-15"


def _run(coin: str, real: bool) -> pd.Series:
    """Run V2 sizing for one coin under the flat-buggy or audit-corrected funding rate.

    `convention="legacy"` is pinned for the sizing engine in both arms (not
    swept) so this isolates the funding cost change only; the funding rate
    itself is swept via `costs_for_coin(..., convention=...)`.
    """
    return run_coin(
        coin, PROJECT_ROOT / DEFAULT_ROUTING[coin], START, END,
        kelly_fraction=0.5, early_exit_loss=0.015,
        costs_override=costs_for_coin(coin, convention=("causal" if real else "legacy")),
        convention="legacy",
    )


def _v2_portfolio(pred_dir: str, real: bool) -> tuple[float, float]:
    """Run the V2 baseline driver (exact pipeline) and parse portfolio SR + return."""
    cmd = [sys.executable, "scripts/baseline_strategy_v2.py",
           "--pred-dir", pred_dir, "--symmetric"]
    if real:
        cmd.extend(["--funding-rate", "0.0003"])
    out = subprocess.run(cmd, capture_output=True, text=True,
                         cwd=str(PROJECT_ROOT), env={"PYTHONPATH": str(PROJECT_ROOT), **__import__("os").environ}).stdout
    block = out.split("Equal-Weight Portfolio", 1)[-1]
    sr = float(re.search(r"Sharpe\s*:\s*([-\d.]+)", block).group(1))
    ret = float(re.search(r"Return\s*:\s*([+\-\d.]+)%", block).group(1))
    return sr, ret


def _sweep_v2() -> None:
    print("\n=== V2 baseline (flat-buggy → real signed funding) ===")
    print(f"{'config':>26} | {'SR flat':>7} {'SR real':>7} {'ΔSR':>6} | {'ret flat':>8} {'ret real':>8}")
    for name, pdir in [("V2 2-coin (BTC/ETH)", "data/multi_2coins_v2"),
                       ("V2 3-coin (+BNB)", "data/multi_3coins_bnb")]:
        sf, rf = _v2_portfolio(pdir, False)
        sr_, rr = _v2_portfolio(pdir, True)
        print(f"{name:>26} | {sf:>7.2f} {sr_:>7.2f} {sr_-sf:>+6.2f} | "
              f"{rf:>7.1f}% {rr:>7.1f}%")


def main() -> None:
    coins = list(DEFAULT_ROUTING.keys())

    # cache both funding variants once per coin
    flat = {c: _run(c, False) for c in coins}
    real = {c: _run(c, True) for c in coins}

    print("\n=== Per-coin standalone (flat-buggy → real signed funding) ===")
    print(f"{'coin':>12} | {'SR flat':>7} {'SR real':>7} {'ΔSR':>6} | "
          f"{'ret flat':>8} {'ret real':>8} {'Δret':>7}")
    for c in coins:
        bf, br = _metrics(flat[c]), _metrics(real[c])
        print(f"{c:>12} | {bf['sharpe']:>7.2f} {br['sharpe']:>7.2f} "
              f"{br['sharpe']-bf['sharpe']:>+6.2f} | "
              f"{bf['total_return']*100:>7.0f}% {br['total_return']*100:>7.0f}% "
              f"{(br['total_return']-bf['total_return'])*100:>+6.0f}pp")

    print("\n=== Portfolios (flat-buggy → real signed funding) ===")
    print(f"{'portfolio':>22} | {'SR flat':>7} {'SR real':>7} {'ΔSR':>6} | "
          f"{'ret flat':>8} {'ret real':>8} | {'DD flat':>7} {'DD real':>7}")
    groups = {
        "4-coin (canonical)": ["bitcoin", "ethereum", "binancecoin", "solana"],
        "8-coin": coins,
        "BTC/ETH (2-coin)": ["bitcoin", "ethereum"],
    }
    for name, cs in groups.items():
        pf_flat = _metrics(portfolio_return(pd.DataFrame({c: flat[c] for c in cs}).dropna(), PORTFOLIO_WEIGHTS))
        pf_real = _metrics(portfolio_return(pd.DataFrame({c: real[c] for c in cs}).dropna(), PORTFOLIO_WEIGHTS))
        print(f"{name:>22} | {pf_flat['sharpe']:>7.3f} {pf_real['sharpe']:>7.3f} "
              f"{pf_real['sharpe']-pf_flat['sharpe']:>+6.3f} | "
              f"{pf_flat['total_return']*100:>7.0f}% {pf_real['total_return']*100:>7.0f}% | "
              f"{pf_flat['max_drawdown']*100:>6.1f}% {pf_real['max_drawdown']*100:>6.1f}%")

    _sweep_v2()


if __name__ == "__main__":
    main()
