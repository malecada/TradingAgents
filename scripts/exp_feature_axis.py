#!/usr/bin/env python
"""Task F5 — Axis 4: feature-set experiment, per coin (honest rebuild, Phase 2).

The old §20 per-coin feature routing (route BTC/BNB to 78f, ETH/SOL to 193f)
was voided along with every other pre-audit finding (contaminated by
same-bar sizing look-ahead + unpurged labels). This script re-decides,
per coin, whether the wider 193-feature LGB model beats the incumbent
78-feature model on purged dev predictions:

  78f  (incumbent) -> data/rebuild/preds/btc_eth_78f   (both coins)
  193f             -> data/rebuild/preds/btc_eth_193f  (both coins)

Unlike F3/F4 (which pick one winner for the whole 2-coin portfolio), this
axis's gate is evaluated *independently per coin* — the routing decision
can differ between bitcoin and ethereum (that's the entire point of
resurrecting §20's question). The h3-only restriction (F3's incumbent
horizon) and the 78f/193f pred dirs are otherwise driven through the exact
same production sizing path as every other axis script:
``scripts.exp_horizon_axis.run_coin_horizons`` (causal convention,
price_stop_pct=0.03, kelly=0.5, target_vol=0.10, max_leverage=3.0,
min_hold=7, SMA30/1.5x trend filter — unchanged since F2/F3's identity
check against ``baseline_v5_mix.run_coin``).

Sentiment arm (amendment, 2026-07-09): the brief's optional third arm
(+sentiment-index, wired only if 193f shows signs of life) is SKIPPED per
explicit instruction. The pre-registered trigger condition ("run sentiment
arm iff 193f portfolio ΔSR > -0.2") is evaluated and recorded below, but
the arm itself is never executed regardless of the outcome — if it passes,
that is noted as deferred to the controller, not acted on here.

Usage:
    python scripts/exp_feature_axis.py
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
    "78f": PROJECT_ROOT / "data" / "rebuild" / "preds" / "btc_eth_78f",
    "193f": PROJECT_ROOT / "data" / "rebuild" / "preds" / "btc_eth_193f",
}
INCUMBENT_ARM = "78f"

# Per-coin anchors: F4 (axis_pool) ran the identical combo (pred_dir=
# btc_eth_78f, horizons=[3]) and recorded per-coin portfolio-path SRs in
# data/rebuild/axis_pool/result.json["configs"]["pool2"]["per_coin"]. F3
# (axis_horizons, the script's own namesake per the brief) only recorded
# the *portfolio* SR for config "3", not per-coin — so the per-coin anchor
# below comes from F4 instead, noted explicitly in the output. The
# portfolio anchor (both-78f) is common to F3 and F4 and reproduced exactly
# by both.
PER_COIN_ANCHOR_SOURCE = "data/rebuild/axis_pool/result.json (F4, configs.pool2.per_coin) " \
    "— F3's axis_horizons/result.json does not record per-coin SRs for config '3'"
PER_COIN_ANCHOR_SR = {
    "bitcoin": 0.3721560244577205,
    "ethereum": 0.1920043111783232,
}
PORTFOLIO_ANCHOR_SR = 0.3763016494366421  # F3 configs["3"].sharpe == F4 pool2 portfolio.sharpe

SENTIMENT_ARM_THRESHOLD = -0.2


def verify_arm(pred_dir: Path, horizons: list[int]) -> dict:
    """Verify a feature-arm pred file: max date in-window, DirAcc sane for
    BTC/ETH rows, prediction/ref_price ratio ~= 1 (sanity against gross
    scale errors)."""
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
            ratio = float((sub["prediction"] / sub["ref_price"]).mean())
            per_coin[coin] = {
                "n": int(len(sub)),
                "dir_acc": dir_acc,
                "dir_acc_sane": bool(0.45 <= dir_acc <= 0.60),
                "pred_ref_ratio_mean": ratio,
                "pred_ref_ratio_sane": bool(0.9 <= ratio <= 1.1),
            }
        entry["per_coin"] = per_coin
        entry["ok"] = entry["max_date_ok"] and all(
            v["dir_acc_sane"] and v["pred_ref_ratio_sane"] for v in per_coin.values()
        )
        out[f"h{h}"] = entry
    return out


def main() -> None:
    out_dir = PROJECT_ROOT / "data" / "rebuild" / "axis_features"
    out_dir.mkdir(parents=True, exist_ok=True)
    concerns: list[str] = []

    # ── Verify both arms (78f already verified repeatedly by F2/F3/F4; the
    # only genuinely new arm here is 193f) ──────────────────────────────
    verification = {
        "78f": verify_arm(ARMS["78f"], HORIZONS),
        "193f": verify_arm(ARMS["193f"], HORIZONS),
    }
    verification_ok = all(v["ok"] for arm in verification.values() for v in arm.values())
    verification["ok"] = verification_ok
    if not verification_ok:
        print("VERIFICATION FAILED — see result.json['verification']")

    # ── Compute per-coin return series for both arms ────────────────────
    coin_series = {arm: {} for arm in ARMS}
    coin_metrics = {arm: {} for arm in ARMS}
    for arm_name, pred_dir in ARMS.items():
        for coin in COINS:
            rets = run_coin_horizons(coin, pred_dir, HORIZONS, START, END)
            coin_series[arm_name][coin] = rets
            m = _metrics(rets)
            coin_metrics[arm_name][coin] = m
            log_trial(
                experiment="axis_features",
                config={"coin": coin, "arm": arm_name, "horizons": HORIZONS,
                        "pred_dir": pred_dir.name},
                window=(START, END),
                metrics=m,
            )
            sr = m["sharpe"]
            print(f"  {coin:9s} {arm_name:5s} SR={sr:+.4f}  ret={m['total_return']:+8.1%}  "
                  f"maxDD={m['max_drawdown']:6.1%}")
            if sr > 2.5:
                concerns.append(
                    f"STOP: {coin}/{arm_name} SR={sr:.3f} > +2.5 — possible look-ahead "
                    f"bug, DONE_WITH_CONCERNS"
                )
                print(f"  {concerns[-1]}")

    # ── Consistency anchors ──────────────────────────────────────────────
    anchor_check = {"per_coin_source": PER_COIN_ANCHOR_SOURCE, "per_coin": {}}
    for coin in COINS:
        recomputed = coin_metrics[INCUMBENT_ARM][coin]["sharpe"]
        expected = PER_COIN_ANCHOR_SR[coin]
        diff = abs(recomputed - expected)
        anchor_check["per_coin"][coin] = {
            "anchor_sr": expected, "recomputed_sr": recomputed,
            "diff": diff, "ok": diff < 1e-9,
        }
    incumbent_portfolio = portfolio_series(coin_series[INCUMBENT_ARM])
    incumbent_portfolio_metrics = _metrics(incumbent_portfolio)
    portfolio_diff = abs(incumbent_portfolio_metrics["sharpe"] - PORTFOLIO_ANCHOR_SR)
    anchor_check["portfolio"] = {
        "anchor_sr": PORTFOLIO_ANCHOR_SR,
        "recomputed_sr": incumbent_portfolio_metrics["sharpe"],
        "diff": portfolio_diff, "ok": portfolio_diff < 1e-9,
    }
    anchors_ok = (
        all(v["ok"] for v in anchor_check["per_coin"].values())
        and anchor_check["portfolio"]["ok"]
    )
    assert anchors_ok, f"anchor check failed: {anchor_check}"

    # ── Per-coin gate: paired_bootstrap(78f, 193f) -> adopt 193f iff
    # delta_sr>0 AND p_pos>=0.85 AND maxDD worsening <=1pp ───────────────
    gates_cfg = json.loads((PROJECT_ROOT / "data" / "rebuild" / "gates.json").read_text())
    axis_gate = gates_cfg["axis_experiments"]

    per_coin_result = {}
    routing_decision = {}
    for coin in COINS:
        a_series, b_series = coin_series["78f"][coin], coin_series["193f"][coin]
        bootstrap = paired_bootstrap(a_series, b_series)
        incumbent_dd = coin_metrics["78f"][coin]["max_drawdown"]
        b_dd = coin_metrics["193f"][coin]["max_drawdown"]
        dd_worsening = abs(min(b_dd, 0.0)) - abs(min(incumbent_dd, 0.0))
        gate_pass = (
            bootstrap["delta_sr"] > 0
            and bootstrap["p_pos"] >= 0.85
            and dd_worsening <= 0.01
        )
        decision = "193f" if gate_pass else "78f"
        routing_decision[coin] = decision
        per_coin_result[coin] = {
            "78f": coin_metrics["78f"][coin],
            "193f": coin_metrics["193f"][coin],
            "bootstrap_193f_vs_78f": bootstrap,
            "gate": {
                "delta_sharpe": bootstrap["delta_sr"],
                "p_pos": bootstrap["p_pos"],
                "max_drawdown_worsening": dd_worsening,
                "rule": axis_gate["adopt_rule"],
                "pass": gate_pass,
            },
            "decision": decision,
        }
        print(f"  [{coin}] 78f SR={coin_metrics['78f'][coin]['sharpe']:+.4f}  "
              f"193f SR={coin_metrics['193f'][coin]['sharpe']:+.4f}  "
              f"delta={bootstrap['delta_sr']:+.4f}  p_pos={bootstrap['p_pos']:.4f}  "
              f"-> {decision}")

    # ── Both EW portfolio combos for the record ─────────────────────────
    both_193f_portfolio = portfolio_series(coin_series["193f"])
    both_193f_metrics = _metrics(both_193f_portfolio)
    routed_series = {coin: coin_series[routing_decision[coin]][coin] for coin in COINS}
    routed_portfolio = portfolio_series(routed_series)
    routed_metrics = _metrics(routed_portfolio)

    portfolio_bootstrap = paired_bootstrap(incumbent_portfolio, both_193f_portfolio)

    for tag, m in (("both_78f_incumbent", incumbent_portfolio_metrics),
                   ("both_193f", both_193f_metrics),
                   ("routed", routed_metrics)):
        sr = m["sharpe"]
        print(f"  portfolio[{tag:18s}] SR={sr:+.4f}  ret={m['total_return']:+8.1%}  "
              f"maxDD={m['max_drawdown']:6.1%}")
        if sr > 2.5:
            concerns.append(
                f"STOP: portfolio[{tag}] SR={sr:.3f} > +2.5 — possible look-ahead bug, "
                f"DONE_WITH_CONCERNS"
            )
            print(f"  {concerns[-1]}")

    # ── Sentiment-arm pre-registered condition (SKIPPED per amendment) ──
    sentiment_delta_sr = portfolio_bootstrap["delta_sr"]
    sentiment_condition_met = sentiment_delta_sr > SENTIMENT_ARM_THRESHOLD
    sentiment_arm = {
        "rule": f"run sentiment arm iff 193f portfolio delta_sr > {SENTIMENT_ARM_THRESHOLD} "
                f"(both-193f vs both-78f incumbent, paired block bootstrap)",
        "delta_sr": sentiment_delta_sr,
        "threshold": SENTIMENT_ARM_THRESHOLD,
        "condition_met": sentiment_condition_met,
        "action": (
            "SKIPPED per task amendment (2026-07-09) — condition met, so the arm is "
            "deferred to the controller for a future run rather than executed here."
            if sentiment_condition_met else
            "SKIPPED per task amendment (2026-07-09) — condition not met either way; "
            "no further action, incumbent (no sentiment) stands."
        ),
    }
    print(f"\n  sentiment-arm condition: delta_sr={sentiment_delta_sr:+.4f} "
          f"vs threshold {SENTIMENT_ARM_THRESHOLD} -> met={sentiment_condition_met} "
          f"-> {sentiment_arm['action']}")

    result = {
        "window": {"start": START, "end": END},
        "coins": list(COINS),
        "horizons": HORIZONS,
        "arms": {k: v.name for k, v in ARMS.items()},
        "incumbent_arm": INCUMBENT_ARM,
        "verification": verification,
        "anchor_check": anchor_check,
        "per_coin": per_coin_result,
        "portfolio": {
            "both_78f_incumbent": incumbent_portfolio_metrics,
            "both_193f": both_193f_metrics,
            "routed": routed_metrics,
            "bootstrap_193f_vs_incumbent": portfolio_bootstrap,
        },
        "routing_decision": routing_decision,
        "sentiment_arm_condition": sentiment_arm,
        "concerns": concerns,
    }
    with open(out_dir / "result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n  routing decision: {routing_decision}")
    print(f"  Wrote: {out_dir / 'result.json'}")


if __name__ == "__main__":
    main()
