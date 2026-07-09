#!/usr/bin/env python
"""H2 HOLDOUT ONE-SHOT — factor sleeve + portfolio combination + gates + placebo.

Executes the frozen portfolio contract (data/rebuild/frozen_portfolio.json,
commit fc33cd5) on the never-touched holdout window 2025-04-01..2026-07-01.
NO parameter is tunable. The carry sleeve is produced separately by
scripts/holdout/carry_stressed_holdout.py (must be run first); this script:

  1. Factor sleeve (macross_10_50_ls) — two-stage per holdout_protocol:
     (a) ma_cross_signal on FULL history (warm-up), (b) fresh-latch engine on
     the holdout-window slice only. Reuses the frozen path in
     scripts/factor_baselines.py verbatim (import, no re-implementation).
  2. Combine factor + carry with the frozen allocation rule (50/50 freeze,
     monthly inverse-vol rebalance on trailing-90-calendar-day vol, carry cap
     0.5, zero-vol guard).
  3. Evaluate gates.json holdout_deploy (SR, maxDD, per-sleeve contribution,
     factor placebo p N=500).
  4. Write data/rebuild/holdout/result.json + ledger rows (allow_holdout=True).

Zero-variance SR := 0.0 everywhere (holdout_protocol.zero_variance_sr_convention).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.factor_baselines import (  # noqa: E402
    COINS,
    _load_windowed,
    _size_and_backtest,
    _window_mask,
    ma_cross_signal,
)
from tradingagents.rebuild.ledger import log_trial  # noqa: E402

ANN = np.sqrt(252)
FULL_START = "2021-11-07"
HOLD_START = "2025-04-01"
HOLD_END = "2026-07-01"
FAST, SLOW = 10, 50
BLOCK = 21          # placebo stationary-bootstrap mean block length (= compare.py)
N_PLACEBO = 500
CARRY_CAP = 0.5
OUT = PROJECT_ROOT / "data" / "rebuild" / "holdout"
CARRY_CSV = OUT / "carry_audit" / "sleeve_stressed_daily.csv"
GATES = PROJECT_ROOT / "data" / "rebuild" / "gates.json"


# ── metric helpers (zero-variance SR := 0) ──────────────────────────────────
def _sr(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    if len(x) < 2:
        return 0.0
    sd = x.std(ddof=1)
    return float(x.mean() / sd * ANN) if sd > 0 else 0.0


def _metrics(series: pd.Series | np.ndarray) -> dict:
    r = np.asarray(series, float)
    if len(r) == 0:
        return {"sharpe": 0.0, "total_return": 0.0, "max_drawdown": 0.0, "n_bars": 0}
    eq = np.cumprod(1.0 + r)
    peak = np.maximum.accumulate(eq)
    dd = float((eq / peak - 1.0).min())
    return {
        "sharpe": _sr(r),
        "total_return": float(eq[-1] - 1.0),
        "max_drawdown": dd,
        "n_bars": int(len(r)),
    }


# ── stage 1+2 factor sleeve (frozen path, fresh-latch on holdout slice) ──────
def factor_sleeve() -> tuple[pd.DataFrame, pd.Series, dict, dict]:
    cols, halts, windowed = {}, {}, {}
    for coin in COINS:
        df = _load_windowed(coin, FULL_START, HOLD_END)          # full history
        sig_full = ma_cross_signal(df["Close"].values, FAST, SLOW)  # warm-up
        m = _window_mask(df["Date"], HOLD_START, HOLD_END)       # holdout slice
        dates = df["Date"].values[m]
        closes = df["Close"].values[m]
        highs = df["High"].values[m]
        lows = df["Low"].values[m]
        sig = sig_full[m].astype(np.int8)
        series, halted = _size_and_backtest(coin, dates, closes, highs, lows, sig)
        cols[coin] = series
        halts[coin] = bool(halted)
        windowed[coin] = {"dates": dates, "closes": closes, "highs": highs,
                          "lows": lows, "sig": sig}
    fac = pd.DataFrame(cols).dropna().sort_index()
    port = fac.mean(axis=1)
    return fac, port, halts, windowed


# ── placebo: stationary-bootstrap block-shuffle of the SIGNAL arrays ─────────
def _boot_idx(rng: np.random.Generator, T: int, block: int) -> np.ndarray:
    """Same stationary-bootstrap index algorithm as compare.paired_bootstrap."""
    idx: list[int] = []
    while len(idx) < T:
        start = rng.integers(0, T)
        length = rng.geometric(1.0 / block)
        idx.extend(((start + np.arange(length)) % T).tolist())
    return np.array(idx[:T])


def placebo(windowed: dict, real_sr: float, n: int = N_PLACEBO,
            block: int = BLOCK) -> dict:
    srs = np.empty(n)
    t0 = time.time()
    for k in range(1, n + 1):
        rng = np.random.default_rng(k)                # one rng per variant
        cols = {}
        for coin in COINS:                            # [bitcoin, ethereum] order
            wd = windowed[coin]
            T = len(wd["sig"])
            bidx = _boot_idx(rng, T, block)           # draws consumed in order
            shuf = wd["sig"][bidx].astype(np.int8)
            series, _ = _size_and_backtest(
                coin, wd["dates"], wd["closes"], wd["highs"], wd["lows"], shuf)
            cols[coin] = series
        pdf = pd.DataFrame(cols).dropna().sort_index()
        srs[k - 1] = _sr(pdf.mean(axis=1).values)
    ge = int((srs >= real_sr).sum())
    p = (1 + ge) / (n + 1)
    return {
        "n": n, "block_mean": block, "real_factor_sr": real_sr,
        "n_ge_real": ge, "p_value": p,
        "placebo_sr_mean": float(srs.mean()), "placebo_sr_std": float(srs.std(ddof=1)),
        "placebo_sr_min": float(srs.min()), "placebo_sr_max": float(srs.max()),
        "placebo_sr_p95": float(np.percentile(srs, 95)),
        "runtime_sec": round(time.time() - t0, 1),
        "srs": srs.tolist(),
    }


# ── allocation rule (frozen) ─────────────────────────────────────────────────
def _inverse_vol_weights(vc: float, vf: float) -> tuple[float, float]:
    """Frozen formula + zero-vol guard (guard takes precedence)."""
    if vc == 0.0 and vf == 0.0:
        return 0.0, 0.0                       # 100% cash
    if vc == 0.0:
        return 0.0, 1.0                       # carry dead -> factor 1.0 (no cap)
    if vf == 0.0:
        return 0.5, 0.0                       # factor dead -> carry cap 0.5, rest cash
    wc_raw = (1.0 / vc) / (1.0 / vc + 1.0 / vf)
    if wc_raw > CARRY_CAP:
        return CARRY_CAP, 1.0 - CARRY_CAP     # cap binds -> 0.5 / 0.5
    return wc_raw, 1.0 - wc_raw


def _trailing_vol(df: pd.DataFrame, col: str, dt: pd.Timestamp) -> float:
    lo = dt - pd.Timedelta(days=90)
    win = df.loc[(df.index >= lo) & (df.index < dt), col]  # strictly before dt
    return float(win.std(ddof=1) * ANN) if len(win) > 1 else 0.0


def combine(factor_port: pd.Series, carry_sleeve: pd.Series) -> tuple[pd.Series, list]:
    df = pd.concat({"factor": factor_port, "carry": carry_sleeve}, axis=1)
    df = df.dropna().sort_index()
    dates = df.index
    w_carry, w_factor = CARRY_CAP, 1.0 - CARRY_CAP   # 50/50 freeze on first bar
    cur_month = (dates[0].year, dates[0].month)
    schedule = [{"date": dates[0].strftime("%Y-%m-%d"), "w_carry": w_carry,
                 "w_factor": w_factor, "w_cash": round(1 - w_carry - w_factor, 12),
                 "kind": "initial_freeze_50_50"}]
    port = np.empty(len(dates))
    for i, dt in enumerate(dates):
        ym = (dt.year, dt.month)
        if i > 0 and ym != cur_month:                # calendar-month start
            vc = _trailing_vol(df, "carry", dt)
            vf = _trailing_vol(df, "factor", dt)
            w_carry, w_factor = _inverse_vol_weights(vc, vf)
            schedule.append({
                "date": dt.strftime("%Y-%m-%d"), "w_carry": round(w_carry, 6),
                "w_factor": round(w_factor, 6),
                "w_cash": round(1 - w_carry - w_factor, 12),
                "vol_carry_ann": round(vc, 6), "vol_factor_ann": round(vf, 6),
                "kind": "monthly_rebalance"})
            cur_month = ym
        port[i] = w_carry * df["carry"].iloc[i] + w_factor * df["factor"].iloc[i]
    return pd.Series(port, index=dates, name="portfolio"), schedule


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gates = json.loads(GATES.read_text())["holdout_deploy"]

    print("=" * 78)
    print("  H2 HOLDOUT ONE-SHOT — frozen_portfolio.json fc33cd5")
    print(f"  window: {HOLD_START} .. {HOLD_END}")
    print("=" * 78)

    # ── carry sleeve (produced by carry_stressed_holdout.py) ────────────────
    if not CARRY_CSV.exists():
        raise SystemExit(f"missing {CARRY_CSV} — run carry_stressed_holdout.py first")
    cdf = pd.read_csv(CARRY_CSV, parse_dates=["date"]).set_index("date").sort_index()
    carry_sleeve = cdf["sleeve"]
    carry_m = _metrics(carry_sleeve)
    print(f"\n[carry]  SR={carry_m['sharpe']:+.3f}  ret={carry_m['total_return']:+.2%}  "
          f"maxDD={carry_m['max_drawdown']:.2%}  ({carry_m['n_bars']} bars)")

    # ── factor sleeve ───────────────────────────────────────────────────────
    fac, factor_port, halts, windowed = factor_sleeve()
    factor_m = _metrics(factor_port)
    btc_m = _metrics(fac["bitcoin"])
    eth_m = _metrics(fac["ethereum"])
    print(f"[factor] SR={factor_m['sharpe']:+.3f}  ret={factor_m['total_return']:+.2%}  "
          f"maxDD={factor_m['max_drawdown']:.2%}  ({factor_m['n_bars']} bars)  "
          f"halts={halts}")
    print(f"         per-coin: BTC SR={btc_m['sharpe']:+.3f}  ETH SR={eth_m['sharpe']:+.3f}")

    # ── portfolio combination ───────────────────────────────────────────────
    port, schedule = combine(factor_port, carry_sleeve)
    port_m = _metrics(port)
    print(f"[port]   SR={port_m['sharpe']:+.3f}  ret={port_m['total_return']:+.2%}  "
          f"maxDD={port_m['max_drawdown']:.2%}  ({port_m['n_bars']} bars)")
    print(f"         rebalances: {len(schedule)} (incl. initial freeze)")

    # ── placebo (factor sleeve only) ────────────────────────────────────────
    print(f"\n[placebo] running N={N_PLACEBO} (this may take several minutes)...")
    pb = placebo(windowed, factor_m["sharpe"])
    print(f"[placebo] p={pb['p_value']:.4f}  (#>=real {pb['n_ge_real']}/{N_PLACEBO})  "
          f"placebo SR mean={pb['placebo_sr_mean']:+.3f} p95={pb['placebo_sr_p95']:+.3f}  "
          f"[{pb['runtime_sec']}s]")

    # ── gate evaluation ─────────────────────────────────────────────────────
    carry_contrib = carry_m["total_return"]
    factor_contrib = factor_m["total_return"]
    g_sr = port_m["sharpe"] >= gates["portfolio_net_sharpe_min"]
    g_dd = abs(port_m["max_drawdown"]) <= gates["max_drawdown_max"]
    g_carry_contrib = carry_contrib >= gates["sleeve_contribution_min"]
    g_factor_contrib = factor_contrib >= gates["sleeve_contribution_min"]
    g_placebo = pb["p_value"] < gates["placebo_p_max"]

    gate_table = [
        {"criterion": "portfolio_net_sharpe_min", "scope": "portfolio",
         "threshold": gates["portfolio_net_sharpe_min"],
         "measured": round(port_m["sharpe"], 4), "pass": bool(g_sr)},
        {"criterion": "max_drawdown_max", "scope": "portfolio",
         "threshold": gates["max_drawdown_max"],
         "measured": round(abs(port_m["max_drawdown"]), 4), "pass": bool(g_dd)},
        {"criterion": "sleeve_contribution_min[carry]", "scope": "sleeve:carry",
         "threshold": gates["sleeve_contribution_min"],
         "measured": round(carry_contrib, 6), "pass": bool(g_carry_contrib)},
        {"criterion": "sleeve_contribution_min[factor]", "scope": "sleeve:factor",
         "threshold": gates["sleeve_contribution_min"],
         "measured": round(factor_contrib, 6), "pass": bool(g_factor_contrib)},
        {"criterion": "placebo_p_max", "scope": "sleeve:factor",
         "threshold": gates["placebo_p_max"],
         "measured": round(pb["p_value"], 4), "pass": bool(g_placebo)},
    ]

    # Deploy composition: portfolio-level gates (SR, DD) are a global precondition;
    # each sleeve is retained iff its own sleeve-level criteria also pass.
    portfolio_precondition = bool(g_sr and g_dd)
    carry_deploy = bool(portfolio_precondition and g_carry_contrib)  # placebo N/A
    factor_deploy = bool(portfolio_precondition and g_factor_contrib and g_placebo)
    deploy = [s for s, ok in (("carry", carry_deploy), ("factor", factor_deploy)) if ok]

    result = {
        "task": "H2_holdout_oneshot",
        "contract": "data/rebuild/frozen_portfolio.json",
        "contract_commit": "fc33cd5",
        "window": [HOLD_START, HOLD_END],
        "one_shot": True,
        "zero_variance_sr_convention": "SR:=0.0 (0/0), never NaN",
        "sleeves": {
            "factor": {
                "config": "macross_10_50_ls", "kelly_fraction": 0.5,
                "portfolio": factor_m, "bitcoin": btc_m, "ethereum": eth_m,
                "halts": halts,
                "contribution_standalone_cumret": factor_contrib,
                "dev_window_sr_reference": 0.6322181732492197,
            },
            "carry": {
                "construction": "always-on 50/50 BTC/ETH short-perp+long-spot, stressed",
                "portfolio": carry_m,
                "contribution_standalone_cumret": carry_contrib,
                "dev_window_stressed_sr_reference": 3.7503661753112434,
                "dev_range_context": [3.75, 5.9],
            },
        },
        "allocation": {
            "rule": "50/50 freeze on first bar; monthly inverse-vol on trailing-90d "
                    "vol; carry cap 0.5; zero-vol guard",
            "frozen_dev_weights": {"carry": 0.5, "factor": 0.5},
            "weight_schedule": schedule,
        },
        "portfolio": port_m,
        "placebo": {k: v for k, v in pb.items() if k != "srs"},
        "gate_table": gate_table,
        "deploy_composition_rule": (
            "portfolio SR & maxDD are a global precondition; a sleeve deploys iff "
            "precondition holds AND its contribution>=0 AND (factor also: placebo p<0.05)"
        ),
        "portfolio_precondition_pass": portfolio_precondition,
        "verdict": {
            "deploy": deploy,
            "carry_deploy": carry_deploy,
            "factor_deploy": factor_deploy,
            "all_gates_pass": bool(g_sr and g_dd and g_carry_contrib
                                   and g_factor_contrib and g_placebo),
        },
    }

    # placebo distribution saved separately (large array kept out of result.json)
    (OUT / "placebo_distribution.json").write_text(json.dumps(
        {"real_factor_sr": pb["real_factor_sr"], "p_value": pb["p_value"],
         "srs": pb["srs"]}, indent=2))
    (OUT / "result.json").write_text(json.dumps(result, indent=2))

    # daily series for the record
    fac_out = fac.copy()
    fac_out["factor_portfolio"] = factor_port
    fac_out.index.name = "date"
    (OUT / "factor_floor").mkdir(parents=True, exist_ok=True)
    fac_out.reset_index().to_csv(OUT / "factor_floor" / "daily_returns.csv", index=False)
    port.rename("portfolio").rename_axis("date").reset_index().to_csv(
        OUT / "portfolio_daily_returns.csv", index=False)

    # ── ledger rows (allow_holdout=True) ────────────────────────────────────
    log_trial(allow_holdout=True, experiment="holdout_oneshot",
              config={"sleeve": "factor", "config_name": "macross_10_50_ls",
                      "kelly_fraction": 0.5},
              window=(HOLD_START, HOLD_END),
              metrics={**factor_m, "contribution": factor_contrib,
                       "bitcoin_sr": btc_m["sharpe"], "ethereum_sr": eth_m["sharpe"],
                       "halts": halts})
    log_trial(allow_holdout=True, experiment="holdout_oneshot",
              config={"kind": "portfolio", "allocation": "inverse_vol_carry_cap_0.5"},
              window=(HOLD_START, HOLD_END),
              metrics={**port_m, "deploy": deploy,
                       "all_gates_pass": result["verdict"]["all_gates_pass"]})
    log_trial(allow_holdout=True, experiment="holdout_oneshot",
              config={"kind": "placebo_factor", "n": N_PLACEBO, "block_mean": BLOCK},
              window=(HOLD_START, HOLD_END),
              metrics={"p_value": pb["p_value"], "n_ge_real": pb["n_ge_real"],
                       "real_factor_sr": pb["real_factor_sr"],
                       "placebo_sr_mean": pb["placebo_sr_mean"],
                       "placebo_sr_p95": pb["placebo_sr_p95"]})

    print("\n" + "=" * 78)
    print("  GATE TABLE")
    for g in gate_table:
        print(f"    {g['criterion']:34s} thr={g['threshold']:<7} "
              f"meas={g['measured']:<10} {'PASS' if g['pass'] else 'FAIL'}")
    print(f"\n  portfolio precondition (SR & DD): "
          f"{'PASS' if portfolio_precondition else 'FAIL'}")
    print(f"  VERDICT deploy = {deploy}   (all_gates_pass="
          f"{result['verdict']['all_gates_pass']})")
    print(f"  -> {OUT / 'result.json'}")
    print("=" * 78)


if __name__ == "__main__":
    main()
