"""Dev walk-forward for the meta-labeled trend system (G1 + G2).

Usage: uv run python scripts/metalabel_run.py
Never reaches into the holdout: assert_dev_window(DEV_END) guards every run.
Every invocation logs one ledger row per (model, tau) evaluated.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv
from tradingagents.dataflows.fng_store import query_fng
from tradingagents.dataflows.onchain_features import build_pit_onchain_features
from tradingagents.metalabel.backtest import (
    evaluate_g2, portfolio_returns, replay_coin,
)
from tradingagents.metalabel.features import assemble_dataset
from tradingagents.metalabel.labeler import triple_barrier_labels, uniqueness_weights
from tradingagents.metalabel.model import evaluate_g1, run_walk_forward
from tradingagents.metalabel.primary import compute_votes, extract_events
from tradingagents.metalabel.wf import purged_walk_forward
from tradingagents.rebuild.ledger import assert_dev_window, log_trial

FREEZE = json.loads(
    (Path(__file__).resolve().parents[1] / "experiments/metalabel/freeze.json").read_text()
)
COINS = FREEZE["coins"]
DEV_START, DEV_END = FREEZE["dev_window"]
TAU_GRID = FREEZE["tau_grid"]
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "metalabel"


def fng_series(dates: pd.DatetimeIndex) -> pd.Series:
    vals = {}
    for d in dates:
        try:
            df = query_fng(d.to_pydatetime(), lookback_days=7)
            vals[d] = float(df["value"].iloc[-1]) if len(df) else np.nan
        except Exception:
            vals[d] = np.nan
    return pd.Series(vals)


def load_coin_blob(coin: str, end_date: str) -> dict:
    ohlcv = _load_crypto_ohlcv(coin, end_date)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    ohlcv = ohlcv[ohlcv["Date"] >= pd.Timestamp(DEV_START) - pd.Timedelta(days=120)]
    ohlcv = ohlcv.reset_index(drop=True)
    votes = compute_votes(ohlcv)
    events = extract_events(votes)
    events = events[(events >= DEV_START) & (events <= end_date)]
    labels = triple_barrier_labels(ohlcv, events)
    weights = (uniqueness_weights(labels, pd.DatetimeIndex(ohlcv["Date"]))
               if len(labels) else pd.Series(dtype=float))
    ev_idx = pd.DatetimeIndex(labels.index) if len(labels) else pd.DatetimeIndex([])
    try:
        onchain = build_pit_onchain_features(coin, ev_idx) if len(ev_idx) else None
    except Exception as exc:  # missing store coverage -> NaN features, logged
        print(f"[warn] onchain features unavailable for {coin}: {exc}")
        onchain = None
    if onchain is not None and getattr(onchain.index, "tz", None) is not None:
        # build_pit_onchain_features returns a UTC tz-aware index; event dates
        # here are tz-naive midnight UTC, so normalize losslessly before any
        # reindex against tz-naive event dates (else silent all-NaN reindex).
        onchain.index = onchain.index.tz_localize(None)
    return {
        "ohlcv": ohlcv, "votes": votes, "labels": labels, "weights": weights,
        "onchain": onchain, "fng": fng_series(ev_idx) if len(ev_idx) else None,
    }


def select_tau(rows: list[dict]) -> float | None:
    passing = [r for r in rows if r["g2_pass"]]
    if not passing:
        return None
    return max(passing, key=lambda r: r["delta_sr"])["tau"]


def coverage_report(X: pd.DataFrame) -> dict:
    return {c: round(1.0 - float(X[c].isna().mean()), 3) for c in X.columns}


def main(end_date: str = DEV_END) -> dict:
    assert_dev_window(end_date)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    per_coin = {c: load_coin_blob(c, end_date) for c in COINS}
    X, y, w, meta = assemble_dataset(per_coin)
    cov = coverage_report(X)
    print(f"events: {len(X)} | coverage: {json.dumps(cov)}")

    oc_cols = [c for c in X.columns if c.startswith("oc_")]
    if oc_cols and all(cov[c] == 0.0 for c in oc_cols):
        raise RuntimeError(
            "on-chain feature coverage is zero — tz/store wiring broken; "
            "refusing to run gates on a gutted model"
        )

    folds = purged_walk_forward(
        meta, DEV_START, end_date,
        retrain_every_days=FREEZE["wf"]["retrain_every_days"],
        embargo_bars=FREEZE["wf"]["embargo_bars"],
        min_train_events=FREEZE["wf"]["min_train_events"],
    )
    preds = {m: run_walk_forward(X, y, w, meta, folds, m)
             for m in ("constant", "logit", "lgb")}
    g1 = evaluate_g1(preds)
    log_trial("metalabel-g1", {"models": list(preds)}, (DEV_START, end_date), g1)
    print(f"G1: {json.dumps(g1, default=float)}")

    results = {"g1": g1, "g2": [], "chosen_tau": None}
    if g1["g1_pass"]:
        lgb_preds = preds["lgb"].set_index(["coin", "event_date"])["p"]
        oos_coins = set(lgb_preds.index.get_level_values(0))

        # Restrict BOTH arms to events with OOS predictions so the G2
        # primary-vs-meta comparison is apples-to-apples: events before the
        # first test block never got a p-hat, and including them in the
        # primary arm (but not the meta arm) would bias the comparison.
        oos_labels = {}
        for c, b in per_coin.items():
            labels = b["labels"]
            if not len(labels) or c not in oos_coins:
                continue
            covered = lgb_preds.loc[c].index
            filtered = labels[labels.index.isin(covered)]
            if len(filtered):
                oos_labels[c] = filtered
        print(f"G2 OOS-covered events per coin: "
              f"{ {c: len(v) for c, v in oos_labels.items()} }")

        prim_port = portfolio_returns({
            c: replay_coin(per_coin[c]["ohlcv"], per_coin[c]["votes"], labels, None, tau=0.5)
            for c, labels in oos_labels.items()
        })
        for tau in TAU_GRID:
            meta_port = portfolio_returns({
                c: replay_coin(
                    per_coin[c]["ohlcv"], per_coin[c]["votes"], labels,
                    lgb_preds.loc[c], tau=tau,
                )
                for c, labels in oos_labels.items()
            })
            g2 = evaluate_g2(prim_port, meta_port) | {"tau": tau}
            log_trial("metalabel-g2", {"tau": tau}, (DEV_START, end_date), g2)
            results["g2"].append(g2)
            print(f"G2 tau={tau}: {json.dumps(g2, default=float)}")
        results["chosen_tau"] = select_tau(results["g2"])

    preds["lgb"].to_csv(OUT_DIR / "oos_predictions.csv", index=False)
    (OUT_DIR / "dev_results.json").write_text(json.dumps(results, indent=2, default=float))
    print(f"chosen_tau: {results['chosen_tau']}")
    return results


if __name__ == "__main__":
    main()
