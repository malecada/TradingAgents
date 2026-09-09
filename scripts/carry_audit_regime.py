#!/usr/bin/env python
"""Carry audit pass 4: regime & persistence stress on the canonical stressed sleeve.

Runs entirely on the CANONICAL stressed daily series from pass 2
(``data/rebuild/carry_audit/sleeve_stressed_daily.csv``, columns date/btc/eth/
sleeve, sleeve = 0.5*btc + 0.5*eth) -- no sleeve rebuild happens here. The only
extra fetch is the raw per-1.0-notional funding-income series per leg (needed
for the funding-sign share and the funding-only haircut curve), via
``tradingagents.strategies.carry_sleeve.funding_daily_income`` -- the same
fetch C1/C2/C3 already exercised (should hit the disk/network cache).

Analyses (all on the stressed series):
  (a) rolling 30d funding-sign share per leg (share of trailing-30d days with
      positive funding income)
  (b) worst-90d compounded return of the sleeve column
  (c) per-year Sharpe table (calendar years, sqrt(252), matches C2's sr())
  (d) haircut curve: SR of a modified sleeve where FUNDING INCOME ONLY is
      scaled by h in {1.00, 0.75, 0.50, 0.25}:
          haircut_series = stressed_sleeve - (1 - h) * 0.5 * (funding_btc + funding_eth)
      (each leg contributes half the book; h=1.00 is the identity -- no haircut)
  (e) longest drawdown duration in days (peak-to-recovery on cumprod equity;
      an unresolved drawdown at series end is reported as "still open")

Plus three named stress-episode windows (LUNA, FTX, worst sustained
negative-funding stretch) and an explicit gate check: is the sleeve's raw
worst-90d loss, scaled by the sleeve's intended 20-50% book allocation, within
the audit's 5% bound?
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.strategies.carry_sleeve import funding_daily_income  # noqa: E402

ANN = np.sqrt(252)  # thesis-canonical annualization (matches C1/C2)
START, END = "2021-11-08", "2025-03-31"  # funding fetch window (end exclusive, matches C2)
SYMBOLS = {"btc": "BTCUSDT", "eth": "ETHUSDT"}
HAIRCUTS = [1.00, 0.75, 0.50, 0.25]
ROLL_FUNDING = 30
ROLL_90 = 90
GATE_BOUND = 0.05        # audit's at-allocation worst-90d loss bound
ALLOC_RANGE = (0.20, 0.50)  # sleeve's intended book allocation range

STRESSED_CSV = PROJECT_ROOT / "data/rebuild/carry_audit/sleeve_stressed_daily.csv"
OUTDIR = PROJECT_ROOT / "data/rebuild/carry_audit"


def sr(x: pd.Series) -> float:
    """Annualized Sharpe (mean/std * sqrt(252)); matches C1/C2's sr()."""
    x = x.dropna()
    return float(x.mean() / x.std() * ANN) if x.std() > 0 else 0.0


def max_drawdown(returns: pd.Series) -> float:
    """Max peak-to-trough drawdown (negative fraction) on cumprod equity."""
    equity = (1.0 + returns).cumprod()
    running_peak = equity.cummax()
    dd = equity / running_peak - 1.0
    return float(dd.min())


def load_stressed() -> pd.DataFrame:
    df = pd.read_csv(STRESSED_CSV)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.set_index("date").sort_index()
    return df


def load_funding_aligned(idx) -> dict[str, pd.Series]:
    """Per-1.0-notional daily funding income per leg, reindexed to ``idx``."""
    start, end = date(2021, 11, 8), date(2025, 3, 31)
    out = {}
    for leg, sym in SYMBOLS.items():
        f = funding_daily_income(sym, start, end)
        out[leg] = f.reindex(idx).fillna(0.0)
    return out


def rolling_funding_sign_share(funding: pd.Series, window: int = ROLL_FUNDING) -> pd.Series:
    """Trailing-``window`` share of days with positive funding income."""
    return (funding > 0).rolling(window).mean()


def funding_share_summary(share: pd.Series) -> dict:
    valid = share.dropna()
    return {
        "min": float(valid.min()),
        "median": float(valid.median()),
        "current": float(valid.iloc[-1]),
        "mean": float(valid.mean()),
        "std": float(valid.std()),
        "count": int(valid.shape[0]),
        "min_date": str(valid.idxmin()),
    }


def worst_window_return(returns: pd.Series, window: int) -> tuple[float, object, object]:
    """Worst trailing-``window`` compounded return; returns (ret, start_date, end_date)."""
    roll = (1.0 + returns).rolling(window).apply(lambda x: np.prod(x), raw=True) - 1.0
    end_date = roll.idxmin()
    worst_ret = float(roll.loc[end_date])
    pos = returns.index.get_loc(end_date)
    start_date = returns.index[pos - (window - 1)]
    return worst_ret, start_date, end_date


def compounded_return(returns: pd.Series, start, end) -> float:
    """Compounded return of ``returns`` over the closed date interval [start, end]."""
    sub = returns.loc[(returns.index >= start) & (returns.index <= end)]
    if sub.empty:
        return float("nan")
    return float((1.0 + sub).prod() - 1.0)


def per_year_sr(returns: pd.Series) -> dict:
    years = pd.Series([d.year for d in returns.index], index=returns.index)
    out = {}
    for y, grp in returns.groupby(years):
        out[str(y)] = {"sharpe": sr(grp), "n_days": int(grp.shape[0])}
    return out


def longest_drawdown_days(returns: pd.Series) -> dict:
    """Longest peak-to-(recovery|series-end) duration in calendar days."""
    equity = (1.0 + returns).cumprod()
    dates = list(equity.index)
    running_peak = -np.inf
    peak_date = dates[0]
    longest = -1
    longest_start = dates[0]
    longest_end = dates[0]
    for d, e in zip(dates, equity.to_numpy()):
        if e >= running_peak:
            running_peak = e
            peak_date = d
        else:
            dur = (d - peak_date).days
            if dur > longest:
                longest = dur
                longest_start = peak_date
                longest_end = d
    unresolved = equity.iloc[-1] < running_peak and longest_end == dates[-1]
    return {
        "longest_days": int(max(longest, 0)),
        "peak_date": str(longest_start),
        "trough_or_end_date": str(longest_end),
        "still_open_at_series_end": bool(unresolved),
    }


def main() -> None:
    df = load_stressed()
    sleeve = df["sleeve"]
    idx = df.index

    funding = load_funding_aligned(idx)  # {"btc": Series, "eth": Series}, per-1.0-notional

    # ── (a) rolling 30d funding-sign share per leg ──────────────────────────
    funding_share = {leg: rolling_funding_sign_share(f) for leg, f in funding.items()}
    funding_share_stats = {leg: funding_share_summary(s) for leg, s in funding_share.items()}

    # Blended share (0.5*btc + 0.5*eth funding > 0), used to locate the worst
    # sustained negative-funding stretch for the stress-episode section below.
    blended_funding = 0.5 * (funding["btc"] + funding["eth"])
    blended_share = rolling_funding_sign_share(blended_funding)
    worst_share_end = blended_share.idxmin()
    worst_share_pos = idx.get_loc(worst_share_end)
    worst_share_start = idx[worst_share_pos - (ROLL_FUNDING - 1)]
    worst_share_value = float(blended_share.loc[worst_share_end])

    # ── (b) worst-90d compounded return of the sleeve ───────────────────────
    worst_90d_ret, worst_90d_start, worst_90d_end = worst_window_return(sleeve, ROLL_90)

    # ── (c) per-year SR table ────────────────────────────────────────────────
    year_sr = per_year_sr(sleeve)

    # ── (d) haircut curve: funding-income-only scaling ──────────────────────
    haircut_rows = []
    haircut_sr = {}
    for h in HAIRCUTS:
        adj = (1.0 - h) * blended_funding
        haircut_series = sleeve - adj
        s = sr(haircut_series)
        haircut_sr[f"{h:.2f}"] = s
        haircut_rows.append({
            "haircut": h,
            "sharpe": s,
            "total_return": float((1.0 + haircut_series).prod() - 1.0),
            "max_drawdown": max_drawdown(haircut_series),
        })

    # Runtime sanity: h=1.00 is a construction identity (subtract zero) -> must
    # exactly reproduce the CSV's own stressed SR.
    stressed_sr = sr(sleeve)
    h100_sr = haircut_sr["1.00"]
    assert abs(h100_sr - stressed_sr) < 1e-9, (
        f"haircut identity failed: h=1.00 SR {h100_sr} != stressed CSV SR {stressed_sr}"
    )
    print(f"[sanity] h=1.00 haircut SR == stressed CSV SR: PASS ({h100_sr:.6f})")

    haircut_df = pd.DataFrame(haircut_rows)
    haircut_df.to_csv(OUTDIR / "haircut_curve.csv", index=False)

    # ── (e) longest drawdown duration ────────────────────────────────────────
    dd = longest_drawdown_days(sleeve)

    # ── Stress episodes ──────────────────────────────────────────────────────
    luna_ret = compounded_return(sleeve, date(2022, 5, 1), date(2022, 6, 15))
    ftx_ret = compounded_return(sleeve, date(2022, 11, 1), date(2022, 12, 15))
    worst_funding_stretch_ret = compounded_return(sleeve, worst_share_start, worst_share_end)

    stress_episodes = {
        "luna_2022_05": {
            "window": ["2022-05-01", "2022-06-15"],
            "sleeve_compounded_return": luna_ret,
        },
        "ftx_2022_11": {
            "window": ["2022-11-01", "2022-12-15"],
            "sleeve_compounded_return": ftx_ret,
        },
        "worst_funding_stretch": {
            "window": [str(worst_share_start), str(worst_share_end)],
            "blended_30d_funding_sign_share": worst_share_value,
            "sleeve_compounded_return": worst_funding_stretch_ret,
        },
    }

    # ── Gate check ────────────────────────────────────────────────────────────
    # Gate: worst-90d loss AT the sleeve's intended 20-50% book allocation <= 5%.
    raw_loses_5pct_at_full_alloc = worst_90d_ret < -GATE_BOUND
    if worst_90d_ret < 0:
        implied_max_alloc = min(1.0, GATE_BOUND / abs(worst_90d_ret))
    else:
        implied_max_alloc = 1.0
    gate_pass_at_low_alloc = (worst_90d_ret * ALLOC_RANGE[0]) >= -GATE_BOUND
    gate_pass_at_high_alloc = (worst_90d_ret * ALLOC_RANGE[1]) >= -GATE_BOUND

    gate = {
        "bound": GATE_BOUND,
        "sleeve_worst_90d_return_raw": worst_90d_ret,
        "sleeve_raw_loses_more_than_5pct": bool(raw_loses_5pct_at_full_alloc),
        "implied_max_allocation_to_keep_gate": implied_max_alloc,
        "intended_allocation_range": list(ALLOC_RANGE),
        "gate_pass_at_20pct_alloc": bool(gate_pass_at_low_alloc),
        "gate_pass_at_50pct_alloc": bool(gate_pass_at_high_alloc),
        "note": (
            "Gate is defined at-allocation: sleeve_worst_90d_return * allocation "
            "must be >= -5%. The raw (100%-notional) sleeve number is recorded "
            "above; implied_max_allocation_to_keep_gate is the largest "
            "allocation fraction (capped at 1.0) that keeps the -5% floor."
        ),
    }

    # ── Assemble JSON ─────────────────────────────────────────────────────────
    out = {
        "window": [START, END],
        "annualization": "sqrt(252)",
        "source_csv": "data/rebuild/carry_audit/sleeve_stressed_daily.csv",
        "n_days": int(len(idx)),
        "funding_sign_share": {
            "window_days": ROLL_FUNDING,
            "per_leg": funding_share_stats,
            "construction": (
                "share of the trailing 30 calendar days (contiguous daily index, "
                "no gaps) with funding_daily_income(symbol) > 0, per leg, over "
                "the same window as the stressed CSV."
            ),
        },
        "worst_90d": {
            "window_days": ROLL_90,
            "return": worst_90d_ret,
            "start_date": str(worst_90d_start),
            "end_date": str(worst_90d_end),
        },
        "per_year_sharpe": year_sr,
        "haircut_curve": {
            "construction": (
                "haircut_series = stressed_sleeve - (1 - h) * 0.5 * "
                "(funding_btc + funding_eth), where funding_btc/funding_eth are "
                "the per-1.0-notional daily funding-income series from "
                "funding_daily_income(), reindexed to the stressed CSV's date "
                "index (each leg contributes half the book, matching the "
                "sleeve's 50/50 BTC/ETH blend). h=1.00 is the identity "
                "(subtract zero); h=0.00 would remove all funding income. Only "
                "funding income is scaled -- hedge P&L and execution costs "
                "already baked into the stressed CSV are untouched."
            ),
            "haircuts": HAIRCUTS,
            "sharpe_by_haircut": haircut_sr,
            "rows_written_to": "data/rebuild/carry_audit/haircut_curve.csv",
        },
        "sanity_checks": {
            "h1.00_equals_stressed_csv_sr": "PASS",
            "stressed_csv_sr": stressed_sr,
        },
        "longest_drawdown": dd,
        "stress_episodes": stress_episodes,
        "gate": gate,
    }

    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "regime.json").write_text(json.dumps(out, indent=2))

    # ── Ledger ────────────────────────────────────────────────────────────────
    log_trial(
        experiment="carry_audit",
        config={"pass": "regime"},
        window=("2021-11-08", "2025-03-31"),
        metrics={
            "worst_90d": worst_90d_ret,
            "per_year_sr": {y: v["sharpe"] for y, v in year_sr.items()},
            "haircut_sr": haircut_sr,
            "longest_dd_days": dd["longest_days"],
        },
    )

    # ── Report ────────────────────────────────────────────────────────────────
    print("\nFunding-sign share per leg (trailing 30d):")
    for leg, stats in funding_share_stats.items():
        print(f"  {leg}: min={stats['min']:.3f} median={stats['median']:.3f} "
              f"current={stats['current']:.3f}")
    print(f"\nWorst-90d sleeve return: {worst_90d_ret:.4%} "
          f"({worst_90d_start} -> {worst_90d_end})")
    print("\nPer-year Sharpe:")
    for y, v in year_sr.items():
        print(f"  {y}: {v['sharpe']:.3f} (n={v['n_days']})")
    print("\nHaircut curve (funding-only):")
    for row in haircut_rows:
        print(f"  h={row['haircut']:.2f}  SR={row['sharpe']:.3f}  "
              f"total_return={row['total_return']:.2%}  "
              f"maxDD={row['max_drawdown']:.2%}")
    print(f"\nLongest drawdown: {dd['longest_days']}d "
          f"({dd['peak_date']} -> {dd['trough_or_end_date']}) "
          f"still_open={dd['still_open_at_series_end']}")
    print("\nStress episodes:")
    print(f"  LUNA (2022-05-01..2022-06-15): {luna_ret:.4%}")
    print(f"  FTX  (2022-11-01..2022-12-15): {ftx_ret:.4%}")
    print(f"  Worst funding stretch ({worst_share_start}..{worst_share_end}, "
          f"share={worst_share_value:.3f}): {worst_funding_stretch_ret:.4%}")
    print(f"\nGate: worst-90d raw={worst_90d_ret:.4%} | >5% loss raw: "
          f"{raw_loses_5pct_at_full_alloc} | implied max allocation: "
          f"{implied_max_alloc:.3f} | pass@20%: {gate_pass_at_low_alloc} | "
          f"pass@50%: {gate_pass_at_high_alloc}")


if __name__ == "__main__":
    main()
