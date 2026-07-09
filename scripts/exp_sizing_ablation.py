#!/usr/bin/env python
"""Task F6 — Axis 5: sizing-component ablation + ML survival verdict.

Phase-2 finale of the honest rebuild. Two parts:

  Part 1 — **Sizing ablation.** The incumbent directional config after F2-F5
  is: level target, single horizon [3], 2-coin pool (BTC+ETH), 78-feature
  predictions (``data/rebuild/preds/btc_eth_78f``), portfolio SR +0.3763.
  Its sizing stack is the V2/V5 pipeline (vol-targeted Kelly → conditional
  leverage → SMA30 trend filter → adaptive hold + early exit + price stop).
  Six arms each toggle ONE component off the incumbent; each arm is
  ledger-logged and paired-block-bootstrapped against the incumbent. A
  component is REMOVED (its arm ADOPTED into the composed config) iff its
  removal arm IMPROVES with delta_sr > 0 AND p_pos >= 0.85 (axis gate family).
  The composed config = incumbent minus every removed component, re-run and
  recorded. This causally re-measures the old "trend filter is the biggest
  win" claim, which the audit (§33, finding C1) showed was a same-bar
  look-ahead artifact.

  Part 2 — **ML survival verdict.** The composed directional candidate is
  gated against the factor floor (``data/rebuild/factor_floor/BEST`` =
  macross_10_50_ls, portfolio SR +0.632 full-series). Gate (gates.json
  ``ml_survival``): paired_bootstrap(floor, candidate) delta_sr > 0 AND
  p_pos >= 0.85 AND DSR >= 0.90. DSR is the Bailey-Lopez de Prado deflated
  Sharpe (reused verbatim from tradingagents/strategies/v3/backtest/dsr.py,
  the same implementation scripts/validate_v5_mix.py uses). n_trials is the
  count of UNIQUE config_hash rows in the trial ledger at evaluation time
  (honest dedupe: 62 rows contain 42 unique configs because the factor
  floor's 18 configs were double-appended in a re-run).

The sizing path here is a parameterized copy of ``run_coin_horizons``
(scripts/exp_horizon_axis.py) — MANDATORY identity check: the defaults must
reproduce the incumbent portfolio SR 0.3763016494366421 to 1e-9 before any
ablation runs. ``_build_positions_with_hold_sizing`` is a verbatim fork of
``v2_sizing.build_positions_with_hold`` with a single isolated branch on the
base-size computation (vol-target vs fixed 1.0 pre-leverage); at
``use_vol_target=True`` it is byte-for-byte the imported function, which the
identity assert proves.

Usage:
    python scripts/exp_sizing_ablation.py
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

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402
from scripts.baseline_v5_mix import (  # noqa: E402
    V5_ASYMMETRIC, V5_CONFIDENCE_REF, _metrics, costs_for_coin,
)
from scripts.exp_horizon_axis import (  # noqa: E402
    _load_preds_horizons, portfolio_series,
)
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402
from tradingagents.rebuild.compare import paired_bootstrap  # noqa: E402
from tradingagents.rebuild.ledger import DEFAULT_LEDGER, log_trial  # noqa: E402
# DSR: reused verbatim from the V3 stack — the same implementation
# scripts/validate_v5_mix.py imports (Bailey & Lopez de Prado 2014).
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.strategies.v2_sizing import (  # noqa: E402
    apply_leverage, apply_trend_filter, compute_realized_vol,
    generate_term_structure_signals, sizing_price_series, vol_regime_mask,
    vol_targeted_size,
)

START = "2021-11-07"
END = "2025-03-31"
PRED_DIR_NAME = "btc_eth_78f"
PRED_DIR = PROJECT_ROOT / "data" / "rebuild" / "preds" / PRED_DIR_NAME
COINS = ("bitcoin", "ethereum")
HORIZONS = [3]                      # incumbent after F3
INCUMBENT_SR = 0.3763016494366421  # F4 pool2 anchor / F5 incumbent
FLOOR_CSV = PROJECT_ROOT / "data" / "rebuild" / "factor_floor" / "BEST" / "daily_returns.csv"


# ── Forked position builder (verbatim copy of
# v2_sizing.build_positions_with_hold; the ONLY change is the isolated
# base-size branch driven by ``use_vol_target``). At use_vol_target=True the
# ``_base_size`` call equals ``vol_targeted_size`` exactly, so this function is
# byte-for-byte the imported one — proven by the identity assert in main(). ──
def _base_size(
    signal: int, confidence: float, realized_vol: float,
    target_vol: float, kelly_fraction: float, use_vol_target: bool,
) -> float:
    if use_vol_target:
        return vol_targeted_size(
            signal, confidence, realized_vol, target_vol, kelly_fraction,
        )
    # no_vol_target arm: fixed base size 1.0 pre-leverage (signed by signal).
    # Entry is gated by vol_ok, so realized_vol is always valid here; the nan
    # guard mirrors vol_targeted_size defensively.
    if signal == 0 or np.isnan(realized_vol) or realized_vol <= 0:
        return 0.0
    return float(signal) * 1.0


def _build_positions_with_hold_sizing(
    signals: np.ndarray,
    vol_ok: np.ndarray,
    confidence: np.ndarray,
    realized_vol: np.ndarray,
    prices: np.ndarray,
    target_vol: float,
    kelly_fraction: float,
    max_leverage: float,
    min_hold: int,
    early_exit_loss: float,
    use_vol_target: bool,
) -> np.ndarray:
    positions = np.zeros(len(signals))
    current_pos = 0.0
    current_dir = 0
    bars_held = 0
    entry_price = 0.0

    for i in range(len(signals)):
        sig = int(signals[i])

        if current_dir != 0:
            bars_held += 1

        # Check early exit for losers. NOTE: the condition is
        # `pnl < -early_exit_loss and signal_changed`; early_exit_loss=inf
        # DISABLES the arm (no finite loss can trip it), whereas 0.0 would
        # mean "exit at ANY loss on a signal flip" — the opposite of removal.
        # The no_early_exit arm therefore uses inf (the disabling value the
        # code implies), documented in the result.
        if current_dir != 0 and bars_held >= 3 and bars_held < min_hold:
            if entry_price > 0 and prices[i] > 0:
                pnl = current_dir * (prices[i] - entry_price) / entry_price
                signal_changed = (sig != current_dir)
                if pnl < -early_exit_loss and signal_changed:
                    current_pos = 0.0
                    current_dir = 0
                    bars_held = 0

        # Entry from flat
        if current_dir == 0 and sig != 0 and vol_ok[i]:
            base = _base_size(
                sig, confidence[i], realized_vol[i], target_vol,
                kelly_fraction, use_vol_target,
            )
            current_pos = apply_leverage(base, confidence[i], max_leverage)
            current_dir = sig
            bars_held = 0
            entry_price = prices[i]

        # Flip: only if hold period expired AND signal reversed
        elif (current_dir != 0 and sig != 0 and sig != current_dir
              and bars_held >= min_hold and vol_ok[i]):
            base = _base_size(
                sig, confidence[i], realized_vol[i], target_vol,
                kelly_fraction, use_vol_target,
            )
            current_pos = apply_leverage(base, confidence[i], max_leverage)
            current_dir = sig
            bars_held = 0
            entry_price = prices[i]

        positions[i] = current_pos

    return positions


def _positions_sizing(
    merged: pd.DataFrame,
    horizons: list[int],
    *,
    trend_sma: int,
    trend_multiplier: float,
    use_vol_target: bool,
    kelly_fraction: float,
    min_hold: int,
    early_exit_loss: float,
    convention: str = "causal",
) -> np.ndarray:
    """Sizing pipeline mirroring exp_horizon_axis._positions_for_horizons,
    with every sizing component exposed as a parameter."""
    sig, conf = generate_term_structure_signals(
        merged, horizons, V5_CONFIDENCE_REF, asymmetric=V5_ASYMMETRIC,
    )
    px = merged["Close"].astype(float).values
    px_sizing = sizing_price_series(px, convention=convention)
    rv = compute_realized_vol(px_sizing, lookback=20)
    mask = vol_regime_mask(rv, percentile_cap=0.95)
    pos = _build_positions_with_hold_sizing(
        signals=sig, vol_ok=mask, confidence=conf, realized_vol=rv,
        prices=px_sizing, target_vol=0.10, kelly_fraction=kelly_fraction,
        max_leverage=3.0, min_hold=min_hold, early_exit_loss=early_exit_loss,
        use_vol_target=use_vol_target,
    )
    return apply_trend_filter(
        pos, px_sizing, sma_period=trend_sma, multiplier=trend_multiplier,
    )


def run_coin_sizing(
    coin: str,
    pred_dir: Path,
    horizons: list[int],
    start: str,
    end: str,
    *,
    trend_sma: int = 30,
    trend_multiplier: float = 1.5,
    use_vol_target: bool = True,
    kelly_fraction: float = 0.5,
    min_hold: int = 7,
    early_exit_loss: float = 0.015,
    price_stop_pct: float = 0.03,
    convention: str = "causal",
) -> pd.Series:
    """Parameterized sibling of ``exp_horizon_axis.run_coin_horizons``.

    At the defaults it mirrors the incumbent path exactly (level target,
    horizons=[3], causal convention, SMA30/1.5x trend, vol-target Kelly=0.5,
    min_hold=7, early_exit=0.015, price_stop=3%, causal costs_for_coin) — the
    identity assert in main() proves defaults reproduce SR 0.3763016494366421.
    Each keyword-only argument toggles one sizing component for the ablation.
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

    pos = _positions_sizing(
        merged, horizons, trend_sma=trend_sma, trend_multiplier=trend_multiplier,
        use_vol_target=use_vol_target, kelly_fraction=kelly_fraction,
        min_hold=min_hold, early_exit_loss=early_exit_loss, convention=convention,
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


def eval_config(**kwargs) -> tuple[pd.Series, dict]:
    """Run BTC+ETH with the given sizing kwargs → (EW portfolio series, metrics)."""
    coin_rets = {
        coin: run_coin_sizing(coin, PRED_DIR, HORIZONS, START, END, **kwargs)
        for coin in COINS
    }
    port = portfolio_series(coin_rets)  # equal-weight BTC+ETH
    return port, _metrics(port)


def _unique_config_hashes(ledger_path: Path = DEFAULT_LEDGER) -> int:
    """Count UNIQUE config_hash rows in the ledger (honest DSR n_trials)."""
    seen: set[str] = set()
    with open(ledger_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            seen.add(json.loads(line)["config_hash"])
    return len(seen)


# ── Ablation arms: each toggles ONE component off the incumbent. ──────────
ARMS = [
    ("no_trend_filter", {"trend_sma": 0},
     "trend filter skipped (sma_period<=0 -> apply_trend_filter is a no-op)"),
    ("trend_mult_1", {"trend_multiplier": 1.0},
     "trend filter runs but multiplier=1.0 -> up/down scale by 1.0 or 1/1.0 "
     "(numerically identical to no_trend_filter; verified)"),
    ("no_vol_target", {"use_vol_target": False},
     "vol-targeted Kelly replaced by fixed base size 1.0 pre-leverage"),
    ("kelly_025", {"kelly_fraction": 0.25},
     "half-Kelly (0.5) -> quarter-Kelly (0.25)"),
    ("min_hold_1", {"min_hold": 1},
     "7-day min hold -> 1-day (near-immediate flip allowed)"),
    ("no_early_exit", {"early_exit_loss": float("inf")},
     "adaptive early exit disabled (inf; 0.0 would exit-at-any-loss, not "
     "disable -> inf is the disabling value the code implies)"),
]

# Map each arm to the composed-config override it contributes if adopted.
ARM_TO_OVERRIDE = {
    "no_trend_filter": {"trend_sma": 0},
    "trend_mult_1": {"trend_multiplier": 1.0},
    "no_vol_target": {"use_vol_target": False},
    "kelly_025": {"kelly_fraction": 0.25},
    "min_hold_1": {"min_hold": 1},
    "no_early_exit": {"early_exit_loss": float("inf")},
}


def main() -> None:
    out_dir = PROJECT_ROOT / "data" / "rebuild" / "axis_sizing"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Identity check ──────────────────────────────────────────────────
    incumbent_port, incumbent_metrics = eval_config()
    incumbent_sr = incumbent_metrics["sharpe"]
    id_diff = abs(incumbent_sr - INCUMBENT_SR)
    print(f"  identity: run_coin_sizing defaults SR={incumbent_sr:.16f}  "
          f"anchor={INCUMBENT_SR:.16f}  diff={id_diff:.2e}")
    assert id_diff < 1e-9, (
        f"identity check FAILED: defaults SR {incumbent_sr} != anchor "
        f"{INCUMBENT_SR} (diff {id_diff})"
    )
    per_coin_incumbent = {
        coin: _metrics(run_coin_sizing(coin, PRED_DIR, HORIZONS, START, END))
        for coin in COINS
    }

    concerns: list[str] = []

    # ── Run the 6 arms ──────────────────────────────────────────────────
    arm_rows: dict[str, dict] = {}
    arm_ports: dict[str, pd.Series] = {}
    for name, override, note in ARMS:
        port, metrics = eval_config(**override)
        arm_ports[name] = port
        boot = paired_bootstrap(incumbent_port, port)  # a=incumbent, b=arm
        # removal IMPROVES iff arm beats incumbent: delta_sr>0 and p_pos>=0.85
        improves = bool(boot["delta_sr"] > 0 and boot["p_pos"] >= 0.85)
        dd_worsening = abs(min(metrics["max_drawdown"], 0.0)) - abs(
            min(incumbent_metrics["max_drawdown"], 0.0))
        cfg = {"arm": name, "override": {k: str(v) for k, v in override.items()},
               "horizons": HORIZONS, "pred_dir": PRED_DIR_NAME}
        log_trial(experiment="axis_sizing", config=cfg,
                  window=(START, END), metrics=metrics)
        arm_rows[name] = {
            "note": note,
            "override": {k: (None if v == float("inf") else v)
                         for k, v in override.items()},
            **metrics,
            "bootstrap_vs_incumbent": boot,
            "max_drawdown_worsening": dd_worsening,
            "removal_improves": improves,
        }
        print(f"  {name:16s} SR={metrics['sharpe']:+.4f}  "
              f"dSR={boot['delta_sr']:+.4f}  p_pos={boot['p_pos']:.3f}  "
              f"improves={improves}")
        if metrics["sharpe"] > 2.5:
            concerns.append(f"{name} SR={metrics['sharpe']:.3f} > 2.5 — investigate")

    # Verify arm1 == arm2 numerically (trend multiplier 1.0 == no filter).
    arm12_max_diff = float(
        (arm_ports["no_trend_filter"] - arm_ports["trend_mult_1"]).abs().max())
    arm12_identical = arm12_max_diff < 1e-12
    print(f"  no_trend_filter vs trend_mult_1 max abs diff = {arm12_max_diff:.2e} "
          f"(identical={arm12_identical})")

    # ── Compose final config = incumbent minus every removed component ───
    removed = [name for name, _o, _n in ARMS if arm_rows[name]["removal_improves"]]
    composed_override: dict = {}
    for name in removed:
        composed_override.update(ARM_TO_OVERRIDE[name])
    # If both trend arms passed, trend_sma=0 already dominates; drop the now
    # redundant multiplier override for a clean canonical representation.
    if "trend_sma" in composed_override:
        composed_override.pop("trend_multiplier", None)

    if composed_override:
        composed_port, composed_metrics = eval_config(**composed_override)
        composed_boot = paired_bootstrap(incumbent_port, composed_port)
        composed_cfg = {"arm": "composed",
                        "override": {k: str(v) for k, v in composed_override.items()},
                        "horizons": HORIZONS, "pred_dir": PRED_DIR_NAME}
        log_trial(experiment="axis_sizing", config=composed_cfg,
                  window=(START, END), metrics=composed_metrics)
        candidate_port = composed_port
        candidate_metrics = composed_metrics
        if composed_metrics["sharpe"] > 2.5:
            concerns.append(
                f"composed SR={composed_metrics['sharpe']:.3f} > 2.5 — investigate")
    else:
        composed_boot = None
        candidate_port = incumbent_port
        candidate_metrics = incumbent_metrics

    composed_full = {
        "trend_sma": composed_override.get("trend_sma", 30),
        "trend_multiplier": composed_override.get("trend_multiplier", 1.5),
        "use_vol_target": composed_override.get("use_vol_target", True),
        "kelly_fraction": composed_override.get("kelly_fraction", 0.5),
        "min_hold": composed_override.get("min_hold", 7),
        "early_exit_loss": (None if composed_override.get("early_exit_loss") == float("inf")
                            else composed_override.get("early_exit_loss", 0.015)),
        "price_stop_pct": 0.03,
        "horizons": HORIZONS, "target": "level", "pool": "2-coin",
        "features": "78f", "pred_dir": PRED_DIR_NAME,
    }
    print(f"\n  removed components: {removed or 'NONE'}")
    print(f"  candidate SR={candidate_metrics['sharpe']:+.4f}")

    # ── Write ablation result ───────────────────────────────────────────
    ablation_result = {
        "window": {"start": START, "end": END},
        "pred_dir": PRED_DIR_NAME,
        "coins": list(COINS),
        "horizons": HORIZONS,
        "incumbent": {
            "sharpe": incumbent_sr,
            "portfolio": incumbent_metrics,
            "per_coin": per_coin_incumbent,
            "identity_diff_vs_anchor": id_diff,
            "identity_ok": bool(id_diff < 1e-9),
        },
        "arms": arm_rows,
        "arm1_vs_arm2": {"max_abs_diff": arm12_max_diff, "identical": arm12_identical},
        "removal_rule": "delta_sr > 0 AND p_pos >= 0.85 (paired block bootstrap, "
                        "block=21, n=2000; arm improves over incumbent)",
        "removed_components": removed,
        "composed_config": composed_full,
        "composed_bootstrap_vs_incumbent": composed_boot,
        "composed_metrics": candidate_metrics if composed_override else incumbent_metrics,
        "concerns": concerns,
    }
    with open(out_dir / "result.json", "w") as f:
        json.dump(ablation_result, f, indent=2, default=str)
    print(f"  Wrote: {out_dir / 'result.json'}")

    # ── Part 2: ML survival verdict ─────────────────────────────────────
    floor = pd.read_csv(FLOOR_CSV, parse_dates=["date"]).set_index("date")["portfolio"]
    floor_metrics = _metrics(floor)
    survival_boot = paired_bootstrap(floor, candidate_port)  # a=floor, b=candidate

    # DSR of the candidate (per-bar SR units; same convention as validate_v5_mix).
    cand = candidate_port.values
    var_sr = variance_of_sr(cand)
    se_sr = float(np.sqrt(var_sr))
    sr_perbar = float(cand.mean() / cand.std(ddof=1)) if cand.std(ddof=1) > 0 else 0.0
    n_trials = _unique_config_hashes()  # AFTER logging this experiment's trials
    e_max = expected_max_sharpe(n_trials, var_sr)
    dsr = deflated_sharpe_ratio(sr_perbar, e_max, se_sr)

    gates = json.loads((PROJECT_ROOT / "data" / "rebuild" / "gates.json").read_text())
    ms = gates["ml_survival"]
    gate_pass = bool(
        survival_boot["delta_sr"] > ms["delta_sharpe_min"]
        and survival_boot["p_pos"] >= ms["p_pos_min"]
        and dsr >= ms["dsr_min"]
    )
    sleeve = "lgb" if gate_pass else "factor"

    print(f"\n  {'=' * 68}")
    print(f"  SURVIVAL: candidate SR={candidate_metrics['sharpe']:+.4f}  "
          f"floor SR={floor_metrics['sharpe']:+.4f}")
    print(f"    dSR(floor->cand)={survival_boot['delta_sr']:+.4f}  "
          f"p_pos={survival_boot['p_pos']:.3f}")
    print(f"    DSR={dsr:.4f} (n_trials={n_trials}, e_max_sr={e_max:.5f}, "
          f"se_sr={se_sr:.5f})")
    print(f"    gate: dSR>{ms['delta_sharpe_min']} & p_pos>={ms['p_pos_min']} & "
          f"DSR>={ms['dsr_min']}  ->  {'PASS' if gate_pass else 'FAIL'}")
    print(f"    VERDICT: sleeve = {sleeve.upper()}")
    print(f"  {'=' * 68}")

    verdict = {
        "window": {"start": START, "end": END},
        "candidate": {
            "source": "composed config from F6 sizing ablation"
                      if composed_override else "incumbent (no component removed)",
            "config": composed_full,
            "portfolio": candidate_metrics,
            "sr_annualized": candidate_metrics["sharpe"],
            "sr_per_bar": sr_perbar,
        },
        "floor": {
            "config": "macross_10_50_ls",
            "source": "data/rebuild/factor_floor/BEST/daily_returns.csv",
            "portfolio_full_series": floor_metrics,
            "sr_full_series": floor_metrics["sharpe"],
            "sr_active_note": "floor_table.md reports sr_active +1.016 (halt-latch "
                              "trailing-zero tail excluded); full-series +0.632 is the "
                              "gate metric (identical-engine policy applied to both arms)",
        },
        "bootstrap_floor_vs_candidate": survival_boot,
        "dsr": {
            "sr_observed_per_bar": sr_perbar,
            "var_sr": var_sr,
            "se_sr": se_sr,
            "n_trials": n_trials,
            "n_trials_note": "UNIQUE config_hash count in trial_ledger.jsonl at "
                             "evaluation time (honest dedupe: the factor floor's 18 "
                             "configs were double-appended in a re-run, so raw row "
                             "count overstates the search; unique-hash count is the "
                             "honest multiple-testing n_trials)",
            "expected_max_sr_null": e_max,
            "dsr": dsr,
            "impl": "tradingagents.strategies.v3.backtest.dsr (Bailey & Lopez de "
                    "Prado 2014; same impl as scripts/validate_v5_mix.py)",
        },
        "gate": {
            "thresholds": ms,
            "delta_sharpe": survival_boot["delta_sr"],
            "p_pos": survival_boot["p_pos"],
            "dsr": dsr,
            "pass": gate_pass,
        },
        "sleeve": sleeve,
        "verdict": (
            f"Directional sleeve = {sleeve.upper()}. "
            + ("LGB candidate beats the factor floor at the ml_survival gate."
               if gate_pass else
               "LGB candidate does NOT beat the factor floor at the ml_survival "
               "gate; the model-free factor floor is the honest directional sleeve.")
        ),
        "concerns": concerns,
    }
    with open(out_dir.parent / "directional_verdict.json", "w") as f:
        json.dump(verdict, f, indent=2, default=str)
    print(f"  Wrote: {out_dir.parent / 'directional_verdict.json'}")


if __name__ == "__main__":
    main()
