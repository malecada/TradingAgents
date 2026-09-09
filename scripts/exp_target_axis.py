#!/usr/bin/env python
"""Task F2 — Axis 1: target-mode experiment (honest rebuild, purged E1 re-run).

The original E1 (THESIS §34) picked "logret" target transform on leaked
labels; its verdict is void (decision review). This script re-derives the
comparison on purged dev predictions using the same V5 sizing pipeline as
F3's horizon-axis experiment (``scripts/exp_horizon_axis.py``), reusing its
``run_coin_horizons`` driver verbatim (identity-checked there against
production ``run_coin``) rather than writing another one.

F3 adopted single-horizon [3] as the incumbent signal (old [7,14] consensus
scored SR -0.90 on purged preds), so the primary A/B arm here runs on
horizons=[3]; [7,14] is carried only as a secondary reference comparison
(no gate).

Arms:
  level  -> data/rebuild/preds/btc_eth_78f          (evaluate_models_multi.py default)
  logret -> data/rebuild/preds/btc_eth_78f_logret   (--target-mode logret)

Usage:
    python scripts/exp_target_axis.py
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

ARMS = {
    "level": PROJECT_ROOT / "data" / "rebuild" / "preds" / "btc_eth_78f",
    "logret": PROJECT_ROOT / "data" / "rebuild" / "preds" / "btc_eth_78f_logret",
}
HORIZON_SETS = {
    "primary": [3],
    "reference": [7, 14],
}


def verify_arm(pred_dir: Path, horizons: list[int]) -> dict:
    """Verify a logret pred file: max date in-window, DirAcc sane, level-space."""
    out = {}
    for h in horizons:
        df = pd.read_csv(pred_dir / f"preds_lgb_h{h}.csv")
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
        dir_acc = float(
            ((df["prediction"] > df["ref_price"]) == (df["actual"] > df["ref_price"])).mean()
        )
        ratio = (df["prediction"] / df["ref_price"])
        out[f"h{h}"] = {
            "max_date": str(df["date"].max().date()),
            "n": int(len(df)),
            "dir_acc": dir_acc,
            "dir_acc_sane": 0.45 <= dir_acc <= 0.60,
            "max_date_ok": df["date"].max() <= pd.Timestamp("2025-03-31"),
            "pred_ref_ratio_mean": float(ratio.mean()),
            "level_space_ok": bool(0.5 < ratio.mean() < 2.0),  # rules out raw logret magnitude
        }
    return out


def eval_arm(pred_dir: Path, horizons: list[int]) -> tuple[pd.Series, dict]:
    coin_rets = {
        coin: run_coin_horizons(coin, pred_dir, horizons, START, END)
        for coin in COINS
    }
    port = portfolio_series(coin_rets)
    metrics = _metrics(port)
    return port, metrics


def main() -> None:
    out_dir = PROJECT_ROOT / "data" / "rebuild" / "axis_target"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Step: verify the just-generated logret preds ───────────────────
    verification = {
        "logret": verify_arm(ARMS["logret"], [3, 7, 14]),
        "level": verify_arm(ARMS["level"], [3, 7, 14]),
    }
    verification_ok = all(
        v["max_date_ok"] and v["dir_acc_sane"] and v["level_space_ok"]
        for arm in verification.values()
        for v in arm.values()
    )
    verification["ok"] = verification_ok
    if not verification_ok:
        print("VERIFICATION FAILED — see result.json['verification']")

    # ── Step: run all 4 arms (2 target modes x 2 horizon sets) ─────────
    portfolios = {}
    results = {}
    concerns = []
    for arm_name, pred_dir in ARMS.items():
        for set_name, horizons in HORIZON_SETS.items():
            key = f"{arm_name}_{set_name}"
            port, metrics = eval_arm(pred_dir, horizons)
            portfolios[key] = port
            results[key] = {
                "target_mode": arm_name, "horizon_set": set_name,
                "horizons": horizons, **metrics,
            }
            log_trial(
                experiment="axis_target",
                config={"target_mode": arm_name, "horizons": horizons,
                        "pred_dir": pred_dir.name},
                window=(START, END),
                metrics=metrics,
            )
            sr = metrics["sharpe"]
            print(f"  {key:18s} SR={sr:+.3f}  ret={metrics['total_return']:+8.1%}  "
                  f"maxDD={metrics['max_drawdown']:6.1%}")
            if sr > 2.5:
                concerns.append(
                    f"STOP: {key} SR={sr:.3f} > +2.5 — possible look-ahead bug, "
                    f"DONE_WITH_CONCERNS"
                )
                print(f"  {concerns[-1]}")

    # ── Primary gate: level[3] vs logret[3] ─────────────────────────────
    primary_bootstrap = paired_bootstrap(portfolios["level_primary"], portfolios["logret_primary"])
    primary_dd_level = results["level_primary"]["max_drawdown"]
    primary_dd_logret = results["logret_primary"]["max_drawdown"]
    primary_dd_worsening = abs(min(primary_dd_logret, 0.0)) - abs(min(primary_dd_level, 0.0))
    gate_pass = (
        primary_bootstrap["delta_sr"] > 0
        and primary_bootstrap["p_pos"] >= 0.85
        and primary_dd_worsening <= 0.01
    )
    gates = json.loads((PROJECT_ROOT / "data" / "rebuild" / "gates.json").read_text())
    axis_gate = gates["axis_experiments"]
    gate_eval = {
        "delta_sharpe": primary_bootstrap["delta_sr"],
        "p_pos": primary_bootstrap["p_pos"],
        "max_drawdown_worsening": primary_dd_worsening,
        "rule": axis_gate["adopt_rule"],
        "pass": gate_pass,
    }

    # ── Reference comparison: level[7,14] vs logret[7,14] (recorded, no gate) ──
    reference_bootstrap = paired_bootstrap(portfolios["level_reference"], portfolios["logret_reference"])

    decision = {
        "adopt_logret": gate_pass,
        "incumbent_after": "logret" if gate_pass else "level",
    }

    result = {
        "window": {"start": START, "end": END},
        "coins": list(COINS),
        "arms": {"level": ARMS["level"].name, "logret": ARMS["logret"].name},
        "horizon_sets": HORIZON_SETS,
        "verification": verification,
        "configs": results,
        "primary_bootstrap_level_vs_logret_h3": primary_bootstrap,
        "reference_bootstrap_level_vs_logret_h7_14": reference_bootstrap,
        "gate": gate_eval,
        "decision": decision,
        "concerns": concerns,
    }
    with open(out_dir / "result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n  primary: level SR={results['level_primary']['sharpe']:+.3f}  "
          f"logret SR={results['logret_primary']['sharpe']:+.3f}  "
          f"p_pos={primary_bootstrap['p_pos']:.4f}  gate_pass={gate_pass}")
    print(f"  reference: level SR={results['level_reference']['sharpe']:+.3f}  "
          f"logret SR={results['logret_reference']['sharpe']:+.3f}  "
          f"p_pos={reference_bootstrap['p_pos']:.4f}")
    print(f"  decision: {decision}")
    print(f"  Wrote: {out_dir / 'result.json'}")


if __name__ == "__main__":
    main()
