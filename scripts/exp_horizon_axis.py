#!/usr/bin/env python
"""Task F3 — Axis 2: horizon-set experiment (honest rebuild, Phase 2).

The old h7+h14 term-structure consensus was selected on leaked labels (audit
§33: the DirAcc ladder tracked leaked-row count exactly). This script
re-derives the horizon choice on purged dev predictions
(``data/rebuild/preds/btc_eth_78f``, DirAcc h1 .498 / h3 .502 / h7 .506 /
h14 .527) by running the V5 sizing pipeline through 7 candidate horizon
configs and comparing portfolio Sharpe with a paired block-bootstrap against
the incumbent [7, 14].

This is a *driver*, not a fork of ``baseline_v5_mix.py``: every sizing
primitive, cost convention, and backtest engine call is imported unchanged
from ``scripts/baseline_v5_mix``, ``scripts/baseline_strategy_v2``, and
``tradingagents/strategies/v2_sizing``. The only new code is
``_load_preds_horizons`` (an N-horizon-generic replacement for
``baseline_v5_mix._load_preds``, which hardcodes h7/h14) and
``run_coin_horizons`` (an N-horizon-generic replacement for
``baseline_v5_mix.run_coin``, same reason). Both are thin wrappers that
delegate everything else to the imported functions.

Usage:
    python scripts/exp_horizon_axis.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_strategy_v2 import (  # noqa: E402
    load_horizon_predictions, run_coin_backtest,
)
from scripts.baseline_v5_mix import (  # noqa: E402
    COSTS, EARLY_EXIT_DEFAULT, V5_ASYMMETRIC, V5_CONFIDENCE_REF, _metrics,
    costs_for_coin, run_coin,
)
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402
from tradingagents.rebuild.compare import paired_bootstrap  # noqa: E402
from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.strategies.v2_sizing import (  # noqa: E402
    apply_trend_filter, build_positions_with_hold, compute_realized_vol,
    generate_term_structure_signals, sizing_price_series, vol_regime_mask,
)

START = "2021-11-07"
END = "2025-03-31"
PRED_DIR_NAME = "btc_eth_78f"
PRED_DIR = PROJECT_ROOT / "data" / "rebuild" / "preds" / PRED_DIR_NAME
COINS = ("bitcoin", "ethereum")
INCUMBENT = [7, 14]

CONFIGS: list[list[int]] = [
    [3], [7], [14],
    [3, 7], [7, 14], [3, 14],
    [3, 7, 14],
]


# ── Adapted loader (N-horizon-generic; baseline_v5_mix._load_preds hardcodes
# h7/h14). Delegates the actual multi-file merge to
# baseline_strategy_v2.load_horizon_predictions (already horizon-list-generic
# and shared with the production V2 script), then applies the same
# tz-normalization + per-coin filter that baseline_v5_mix._load_preds does —
# required so the tz-aware CSV dates line up with the tz-naive OHLCV frame
# merged in later. ────────────────────────────────────────────────────
def _load_preds_horizons(pred_dir: Path, coin: str, horizons: list[int]) -> pd.DataFrame:
    merged = load_horizon_predictions(pred_dir, horizons)
    merged["date"] = pd.to_datetime(merged["date"]).dt.tz_localize(None).dt.normalize()
    merged = merged[merged["coin_id"] == coin].sort_values("date").reset_index(drop=True)
    return merged


# ── Adapted sizing (mirrors baseline_v5_mix._v2_positions, generalized to an
# arbitrary horizon list instead of the hardcoded [7, 14]). Every primitive
# call below is imported verbatim from v2_sizing; only the horizons argument
# to generate_term_structure_signals differs from the production call. ────
def _positions_for_horizons(
    merged: pd.DataFrame,
    horizons: list[int],
    kelly_fraction: float = 0.5,
    early_exit_loss: float = EARLY_EXIT_DEFAULT,
    convention: str = "causal",
) -> np.ndarray:
    sig, conf = generate_term_structure_signals(
        merged, horizons, V5_CONFIDENCE_REF, asymmetric=V5_ASYMMETRIC,
    )
    px = merged["Close"].astype(float).values
    px_sizing = sizing_price_series(px, convention=convention)
    rv = compute_realized_vol(px_sizing, lookback=20)
    mask = vol_regime_mask(rv, percentile_cap=0.95)
    pos = build_positions_with_hold(
        signals=sig, vol_ok=mask, confidence=conf, realized_vol=rv,
        prices=px_sizing,
        target_vol=0.10, kelly_fraction=kelly_fraction, max_leverage=3.0,
        min_hold=7, early_exit_loss=early_exit_loss,
    )
    return apply_trend_filter(pos, px_sizing, sma_period=30, multiplier=1.5)


def run_coin_horizons(
    coin: str,
    pred_dir: Path,
    horizons: list[int],
    start: str,
    end: str,
    kelly_fraction: float = 0.5,
    early_exit_loss: float = EARLY_EXIT_DEFAULT,
    convention: str = "causal",
    price_stop_pct: float = 0.03,
) -> pd.Series:
    """N-horizon-generic sibling of ``baseline_v5_mix.run_coin``.

    Mirrors ``run_coin`` exactly: same causal convention, same sizing
    constants (kelly=0.5, target_vol=0.10, max_leverage=3.0, min_hold=7,
    trend SMA30/1.5x), ``costs_for_coin(coin, convention="causal")``,
    ``price_stop_pct=0.03`` with ``costs["stop_loss"] = 1.0`` (price-axis
    stop replaces the equity-axis proxy), and the same High/Low merge —
    except the signal horizons are a driver parameter instead of the
    hardcoded [7, 14].
    """
    preds = _load_preds_horizons(pred_dir, coin, horizons)
    preds = preds[(preds["date"] >= start) & (preds["date"] <= end)]
    if preds.empty:
        raise ValueError(f"{coin}: no predictions in [{start}, {end}] under {pred_dir}")
    ohlcv = _load_crypto_ohlcv(coin, end)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    cols = ["Date", "Close"] + (["High", "Low"] if price_stop_pct > 0 else [])
    merged = preds.merge(ohlcv[cols], left_on="date", right_on="Date")
    merged = merged.dropna(subset=["Close"]).reset_index(drop=True)
    if convention == "legacy":
        merged["ref_price"] = merged["Close"]
    # causal: keep the CSV ref_price (= close(D-1), verified PIT-correct)

    pos = _positions_for_horizons(
        merged, horizons, kelly_fraction=kelly_fraction,
        early_exit_loss=early_exit_loss, convention=convention,
    )
    costs = dict(costs_for_coin(coin, convention=convention))
    stop_kwargs = {}
    if price_stop_pct > 0:
        costs["stop_loss"] = 1.0  # price-axis stop replaces the equity-axis proxy
        stop_kwargs = dict(highs=merged["High"].values, lows=merged["Low"].values,
                           price_stop_pct=price_stop_pct)
    equity, _m = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=pos, initial_capital=10_000.0, **costs, **stop_kwargs,
    )
    eq = np.asarray(equity, dtype=float)
    rets = eq[1:] / eq[:-1] - 1.0
    return pd.Series(rets, index=pd.to_datetime(merged["date"].values[1:]), name=coin)


def portfolio_series(coin_rets: dict[str, pd.Series]) -> pd.Series:
    """Equal-weight BTC+ETH portfolio: align dates, mean across coins."""
    df = pd.DataFrame(coin_rets).dropna()
    return df.mean(axis=1)


def eval_config(horizons: list[int]) -> tuple[pd.Series, dict]:
    coin_rets = {
        coin: run_coin_horizons(coin, PRED_DIR, horizons, START, END)
        for coin in COINS
    }
    port = portfolio_series(coin_rets)
    metrics = _metrics(port)
    return port, metrics


def main() -> None:
    out_dir = PROJECT_ROOT / "data" / "rebuild" / "axis_horizons"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Identity check: run_coin_horizons([7, 14]) must reproduce
    # run_coin's numbers on the same inputs (proves the driver mirrors the
    # production path). run_coin defaults price_stop_pct=0.0, so the
    # production-equivalent call must pass price_stop_pct=0.03 + causal
    # costs_for_coin explicitly (as F2's brief does for the same reason). ──
    identity_report = {}
    for coin in COINS:
        r_prod = run_coin(
            coin, PRED_DIR, START, END,
            costs_override=costs_for_coin(coin, convention="causal"),
            convention="causal", price_stop_pct=0.03,
        )
        r_driver = run_coin_horizons(coin, PRED_DIR, INCUMBENT, START, END)
        diff = float((r_prod - r_driver).abs().max())
        identity_report[coin] = diff
        assert diff < 1e-9, f"{coin}: driver diverges from run_coin by {diff}"

    prod_port = portfolio_series({
        coin: run_coin(coin, PRED_DIR, START, END,
                        costs_override=costs_for_coin(coin, convention="causal"),
                        convention="causal", price_stop_pct=0.03)
        for coin in COINS
    })
    driver_port, _ = eval_config(INCUMBENT)
    port_diff = float((prod_port - driver_port).abs().max())
    identity_report["portfolio_sr_prod"] = _metrics(prod_port)["sharpe"]
    identity_report["portfolio_sr_driver"] = _metrics(driver_port)["sharpe"]
    identity_report["portfolio_max_abs_diff"] = port_diff
    identity_ok = port_diff < 1e-9
    assert identity_ok, f"portfolio identity check failed: max abs diff {port_diff}"

    # ── Run all 7 configs ──────────────────────────────────────────────
    results = {}
    portfolios = {}
    for horizons in CONFIGS:
        key = "_".join(str(h) for h in horizons)
        port, metrics = eval_config(horizons)
        portfolios[key] = port
        results[key] = {"horizons": horizons, **metrics}
        log_trial(
            experiment="axis_horizons",
            config={"horizons": horizons, "pred_dir": PRED_DIR_NAME},
            window=(START, END),
            metrics=metrics,
        )
        print(f"  horizons={horizons!s:12s} SR={metrics['sharpe']:+.3f}  "
              f"ret={metrics['total_return']:+8.1%}  maxDD={metrics['max_drawdown']:6.1%}")

        sr = metrics["sharpe"]
        if sr > 2.5:
            print(f"  STOP: horizons={horizons} SR={sr:.3f} > +2.5 — possible look-ahead "
                  f"bug in driver, investigate before proceeding (DONE_WITH_CONCERNS)")

    incumbent_key = "_".join(str(h) for h in INCUMBENT)
    best_key = max(results, key=lambda k: results[k]["sharpe"])
    best_horizons = results[best_key]["horizons"]
    incumbent_port = portfolios[incumbent_key]
    best_port = portfolios[best_key]

    gates = json.loads((PROJECT_ROOT / "data" / "rebuild" / "gates.json").read_text())
    axis_gate = gates["axis_experiments"]

    if best_key == incumbent_key:
        bootstrap = None
        gate_eval = {"note": "best config IS the incumbent — no bootstrap needed, "
                              "incumbent retained trivially"}
        adopted = False
    else:
        bootstrap = paired_bootstrap(incumbent_port, best_port)
        incumbent_dd = results[incumbent_key]["max_drawdown"]
        best_dd = results[best_key]["max_drawdown"]
        dd_worsening = abs(min(best_dd, 0.0)) - abs(min(incumbent_dd, 0.0))
        gate_pass = (
            bootstrap["delta_sr"] > 0
            and bootstrap["p_pos"] >= 0.85
            and dd_worsening <= 0.01
        )
        gate_eval = {
            "delta_sharpe": bootstrap["delta_sr"],
            "p_pos": bootstrap["p_pos"],
            "max_drawdown_worsening": dd_worsening,
            "rule": axis_gate["adopt_rule"],
            "pass": gate_pass,
        }
        adopted = gate_pass

    decision = {
        "winner": best_horizons,
        "adopted": adopted,
        "incumbent": INCUMBENT,
    }

    result = {
        "window": {"start": START, "end": END},
        "pred_dir": PRED_DIR_NAME,
        "coins": list(COINS),
        "configs": results,
        "identity_check": {
            "per_coin_max_abs_diff": identity_report,
            "ok": identity_ok,
        },
        "bootstrap_vs_incumbent": bootstrap,
        "gate": gate_eval,
        "decision": decision,
    }
    with open(out_dir / "result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n  incumbent [{incumbent_key.replace('_', ',')}] SR="
          f"{results[incumbent_key]['sharpe']:+.3f}")
    print(f"  best      [{best_key.replace('_', ',')}] SR={results[best_key]['sharpe']:+.3f}")
    print(f"  adopted: {adopted}")
    print(f"  Wrote: {out_dir / 'result.json'}")


if __name__ == "__main__":
    main()
