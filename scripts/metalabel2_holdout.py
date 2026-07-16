"""G3 holdout one-shot, v2. RUN AT MOST ONCE, only after G1+G2 pass on dev.

Trains the frozen pipeline (dense in-bar events) on the full dev window,
predicts dense holdout events, replays both arms restricted to entry-cross
events on the locked holdout (2025-04-01..2026-06-30) — same tradeable-event
scheme as `metalabel2_run.py`'s G2 — and writes holdout_results.json plus a
spent-flag that makes any re-run raise."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.metalabel.backtest import evaluate_g2, portfolio_returns, replay_coin
from tradingagents.metalabel.features import assemble_dataset
from tradingagents.metalabel.model import fit_predict_fold
from tradingagents.metalabel.wf import EMBARGO_CAL_DAYS
from tradingagents.rebuild.ledger import log_trial

from scripts.metalabel2_run import FREEZE, load_coin_blob

DEV_RESULTS = Path(__file__).resolve().parents[1] / "data/metalabel_v2/dev_results.json"
SPENT_FLAG = Path(__file__).resolve().parents[1] / "data/metalabel_v2/holdout_spent.flag"
HOLDOUT_START, HOLDOUT_END = FREEZE["holdout_window"]
DEV_START, DEV_END = FREEZE["dev_window"]


def g3_train_mask(meta: pd.DataFrame) -> pd.Series:
    """Dev-window train mask for the G3 holdout fit, purged at the holdout
    boundary: an event qualifies only if its event_date falls in the dev
    window AND its label has fully resolved (touch_date) before
    HOLDOUT_START minus the embargo. Without the embargo term, dev-tail
    events would have labels resolved using holdout-window prices —
    training-time leakage across the dev/holdout boundary."""
    purge_cutoff = pd.Timestamp(HOLDOUT_START) - pd.Timedelta(days=EMBARGO_CAL_DAYS)
    return (meta["event_date"] <= pd.Timestamp(DEV_END)) & (
        pd.to_datetime(meta["touch_date"]) < purge_cutoff
    )


def main() -> dict:
    dev = json.loads(DEV_RESULTS.read_text())
    tau = dev.get("chosen_tau")
    if tau is None:
        raise RuntimeError("G3 refused: G2 did not pass on dev (chosen_tau is None)")
    if SPENT_FLAG.exists():
        raise RuntimeError("G3 refused: holdout already spent (one-shot)")

    per_coin = {c: load_coin_blob(c, HOLDOUT_END) for c in FREEZE["coins"]}
    X, y, w, meta = assemble_dataset(per_coin)
    is_dev = g3_train_mask(meta)
    is_hold = meta["event_date"] >= pd.Timestamp(HOLDOUT_START)

    order = np.argsort(meta[is_dev]["event_date"].values)
    meta_dev_sorted = meta[is_dev].iloc[order][["event_date", "touch_date"]].reset_index(drop=True)
    p_hold = fit_predict_fold(
        X[is_dev].iloc[order], y[is_dev].iloc[order], w[is_dev].iloc[order],
        X[is_hold], "lgb", meta_tr=meta_dev_sorted,
    )
    # p_series spans ALL dense holdout events (every in-trend bar); replay
    # below restricts to entry-cross events only, so lookups below narrow
    # this down to the tradeable subset. .loc[c] fails loud if a coin has
    # no dense holdout predictions at all.
    p_series = pd.Series(p_hold, index=pd.MultiIndex.from_frame(
        meta[is_hold][["coin", "event_date"]]))

    prim, metaarm = {}, {}
    for c, b in per_coin.items():
        labels = b["labels"]
        # G2-style restriction: replay only at entry-cross events, not every
        # dense in-bar event — the tradeable event scheme, matching
        # metalabel2_run.py's G2 replay.
        labels_h = labels[(labels.index >= pd.Timestamp(HOLDOUT_START)) &
                           (labels.index.isin(b["entry_dates"]))]
        if not len(labels_h):
            continue
        prim[c] = replay_coin(b["ohlcv"], b["votes"], labels_h, None, tau=tau)
        metaarm[c] = replay_coin(b["ohlcv"], b["votes"], labels_h, p_series.loc[c], tau=tau)

    span = slice(pd.Timestamp(HOLDOUT_START), pd.Timestamp(HOLDOUT_END))
    prim_port = portfolio_returns(prim).loc[span]
    meta_port = portfolio_returns(metaarm).loc[span]
    g3 = evaluate_g2(prim_port, meta_port) | {"tau": tau, "n_holdout_events": int(is_hold.sum())}
    g3["g3_pass"] = bool(
        g3["delta_sr"] > 0 and (g3["meta_sr"] > 0 or g3["meta_sr"] > g3["primary_sr"])
    )

    log_trial("metalabel2-g3", {"tau": tau}, (HOLDOUT_START, HOLDOUT_END), g3,
              allow_holdout=True)
    out = DEV_RESULTS.parent / "holdout_results.json"
    out.write_text(json.dumps(g3, indent=2, default=float))
    SPENT_FLAG.write_text(pd.Timestamp.now().isoformat())
    print(json.dumps(g3, indent=2, default=float))
    return g3


if __name__ == "__main__":
    main()
