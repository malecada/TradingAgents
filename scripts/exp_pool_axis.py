#!/usr/bin/env python
"""Task F4 — Axis 3: training-pool-size experiment (honest rebuild, Phase 2).

The old finding "altcoins cost 12-22pp DirAcc" (audit §33 area) was
contaminated by label leakage. This script re-derives whether widening the
LGB *training pool* beyond BTC+ETH helps or hurts the BTC+ETH signal on
purged dev predictions. The traded universe never changes (always
bitcoin+ethereum, EW portfolio) — only the coins the LightGBM models were
*trained* on differ across arms:

  2-pool (incumbent) -> data/rebuild/preds/btc_eth_78f     (bitcoin, ethereum)
  3-pool             -> data/rebuild/preds/pool3_sol        (+ solana)
  5-pool             -> data/rebuild/preds/pool5             (+ solana,
                         binancecoin, ripple)

All three pred dirs were generated with the same purged rolling-730d
protocol (``--purge --train-window-days 730 --trade-date 2025-03-31
--days 1606``). Per F3, the incumbent signal is single-horizon h3, so only
horizons=[3] is evaluated here (no secondary reference set — F4's brief
doesn't ask for one).

This is a *driver*, not a fork: every sizing primitive, cost convention, and
backtest engine call comes from ``scripts.exp_horizon_axis.run_coin_horizons``
(itself a thin N-horizon-generic wrapper around the production
``baseline_v5_mix.run_coin`` path, identity-checked in F3). The only new
code here is the pool-arm loop and the anchor/gate/decision bookkeeping.

Usage:
    python scripts/exp_pool_axis.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_v5_mix import _metrics  # noqa: E402
from scripts.exp_horizon_axis import (  # noqa: E402
    portfolio_series, run_coin_horizons,
)
from tradingagents.rebuild.compare import paired_bootstrap  # noqa: E402
from tradingagents.rebuild.ledger import log_trial  # noqa: E402

START = "2021-11-07"
END = "2025-03-31"
COINS = ("bitcoin", "ethereum")
HORIZONS = [3]

ARMS = {
    "pool2": PROJECT_ROOT / "data" / "rebuild" / "preds" / "btc_eth_78f",
    "pool3": PROJECT_ROOT / "data" / "rebuild" / "preds" / "pool3_sol",
    "pool5": PROJECT_ROOT / "data" / "rebuild" / "preds" / "pool5",
}
INCUMBENT_ARM = "pool2"
ANCHOR_SR = 0.3763016494366421  # F3's [3]-horizon portfolio SR, reproduced exactly here


def verify_arm(pred_dir: Path, horizons: list[int]) -> dict:
    """Verify a pool pred file: max date in-window, DirAcc sane for BTC/ETH rows."""
    out = {}
    for h in horizons:
        df = pd.read_csv(pred_dir / f"preds_lgb_h{h}.csv")
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
        entry = {
            "coin_ids": sorted(df["coin_id"].unique().tolist()),
            "max_date": str(df["date"].max().date()),
            "max_date_ok": bool(df["date"].max() <= pd.Timestamp("2025-03-31")),
        }
        per_coin = {}
        for coin in COINS:
            sub = df[df["coin_id"] == coin]
            dir_acc = float(
                ((sub["prediction"] > sub["ref_price"]) == (sub["actual"] > sub["ref_price"])).mean()
            )
            per_coin[coin] = {
                "n": int(len(sub)),
                "dir_acc": dir_acc,
                "dir_acc_sane": bool(0.45 <= dir_acc <= 0.60),
            }
        entry["per_coin"] = per_coin
        entry["ok"] = entry["max_date_ok"] and all(v["dir_acc_sane"] for v in per_coin.values())
        out[f"h{h}"] = entry
    return out


def eval_arm(pred_dir: Path, horizons: list[int]) -> tuple[pd.Series, dict, dict]:
    coin_rets = {
        coin: run_coin_horizons(coin, pred_dir, horizons, START, END)
        for coin in COINS
    }
    port = portfolio_series(coin_rets)
    metrics = _metrics(port)
    per_coin_metrics = {coin: _metrics(r) for coin, r in coin_rets.items()}
    return port, metrics, per_coin_metrics


def main() -> None:
    out_dir = PROJECT_ROOT / "data" / "rebuild" / "axis_pool"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Verify the two new pool variants (2-pool already verified by F2/F3) ──
    verification = {
        "pool3": verify_arm(ARMS["pool3"], HORIZONS),
        "pool5": verify_arm(ARMS["pool5"], HORIZONS),
    }
    verification_ok = all(v["ok"] for arm in verification.values() for v in arm.values())
    verification["ok"] = verification_ok
    if not verification_ok:
        print("VERIFICATION FAILED — see result.json['verification']")

    # ── Run all 3 pool arms at horizons=[3] ─────────────────────────────
    portfolios = {}
    results = {}
    concerns = []
    for arm_name, pred_dir in ARMS.items():
        port, metrics, per_coin = eval_arm(pred_dir, HORIZONS)
        portfolios[arm_name] = port
        results[arm_name] = {
            "pred_dir": pred_dir.name, "horizons": HORIZONS,
            "portfolio": metrics, "per_coin": per_coin,
        }
        log_trial(
            experiment="axis_pool",
            config={"pool": arm_name, "horizons": HORIZONS, "pred_dir": pred_dir.name},
            window=(START, END),
            metrics=metrics,
        )
        sr = metrics["sharpe"]
        print(f"  {arm_name:6s} SR={sr:+.4f}  ret={metrics['total_return']:+8.1%}  "
              f"maxDD={metrics['max_drawdown']:6.1%}")
        if sr > 2.5:
            concerns.append(
                f"STOP: {arm_name} SR={sr:.3f} > +2.5 — possible look-ahead bug, "
                f"DONE_WITH_CONCERNS"
            )
            print(f"  {concerns[-1]}")

    # ── Consistency anchor: 2-pool arm must reproduce F3's [3] portfolio SR ──
    pool2_sr = results[INCUMBENT_ARM]["portfolio"]["sharpe"]
    anchor_diff = abs(pool2_sr - ANCHOR_SR)
    anchor_ok = anchor_diff < 1e-9
    assert anchor_ok, (
        f"anchor check failed: pool2 SR={pool2_sr!r} vs F3 anchor={ANCHOR_SR!r} "
        f"(diff={anchor_diff})"
    )

    # ── Best arm = max portfolio SR ─────────────────────────────────────
    best_arm = max(results, key=lambda k: results[k]["portfolio"]["sharpe"])

    gates = json.loads((PROJECT_ROOT / "data" / "rebuild" / "gates.json").read_text())
    axis_gate = gates["axis_experiments"]

    if best_arm == INCUMBENT_ARM:
        bootstrap = None
        gate_eval = {"note": "best arm IS the incumbent (2-pool) — no bootstrap needed, "
                              "incumbent retained trivially"}
        adopted = False
    else:
        incumbent_port = portfolios[INCUMBENT_ARM]
        best_port = portfolios[best_arm]
        bootstrap = paired_bootstrap(incumbent_port, best_port)
        incumbent_dd = results[INCUMBENT_ARM]["portfolio"]["max_drawdown"]
        best_dd = results[best_arm]["portfolio"]["max_drawdown"]
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
        "winner": best_arm,
        "adopted": adopted,
        "incumbent": INCUMBENT_ARM,
    }

    result = {
        "window": {"start": START, "end": END},
        "coins": list(COINS),
        "horizons": HORIZONS,
        "arms": {k: v.name for k, v in ARMS.items()},
        "verification": verification,
        "anchor_check": {
            "f3_anchor_sr": ANCHOR_SR,
            "pool2_sr": pool2_sr,
            "diff": anchor_diff,
            "ok": anchor_ok,
        },
        "configs": results,
        "bootstrap_vs_incumbent": bootstrap,
        "gate": gate_eval,
        "decision": decision,
        "concerns": concerns,
    }
    with open(out_dir / "result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n  anchor check: pool2 SR={pool2_sr!r} vs F3 anchor={ANCHOR_SR!r} "
          f"diff={anchor_diff:.2e} ok={anchor_ok}")
    print(f"  best: {best_arm}  SR={results[best_arm]['portfolio']['sharpe']:+.4f}")
    print(f"  decision: {decision}")
    print(f"  Wrote: {out_dir / 'result.json'}")


if __name__ == "__main__":
    main()
