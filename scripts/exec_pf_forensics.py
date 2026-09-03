"""exec_pf R2 forensics (reported, not gated): where does passive execution's
PnL difference vs the parent's taker booking come from?

  python scripts/exec_pf_forensics.py

F1 order-level decomposition LTM - taker: filled orders (price improvement
   vs adverse selection: w_new*(close_n/L - 1) - w_new*(close_n/close_b - 1)),
   unfilled orders (missed bar: w_old vs w_new during the bar, then market cost),
   fee difference.
F2 event-conditional 5-minute post-fill drift on R2 entry fills (charter:
   reported) vs the unconditional P1 figure.
F3 through_ticks = 2 sensitivity (fill rate, SR) -- a reported sensitivity,
   NOT a second fill rule (the registered rule stays 1 tick).
F4 per-year SR LTM vs taker; fill rate by year/side.
Writes data/rebuild/exec_pf/forensics_R2.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exec_pf_common as X  # noqa: E402
from tradingagents.xsect.fills import first_cross_minute, passive_overlay  # noqa: E402


def main() -> None:
    run = json.loads((X.OUT / "run_R2.json").read_text())
    orders = pd.read_parquet(X.OUT / "run_R2_ltm_orders.parquet")
    par = X.r2_parent()
    W, C = par["W"], par["close"]
    P = X.load_agg_panel(list(W.columns), W.index)
    spread = X.spread_model()
    srel = {s: spread["per_symbol_s_rel"].get(s, spread["pooled_alt_s_rel"]) for s in W.columns}
    fill = dict(s_rel=srel, through_ticks=run["fill_model"]["through_ticks"], maker_bp=X.FEES["maker_bp"], taker_bp=X.FEES["taker_bp"])

    # ── F1 decomposition ────────────────────────────────────────────────────
    o = orders.copy()
    w_old = []
    for t, s in zip(o["ts_bar"], o["symbol"]):
        i = W.index.get_loc(t)
        w_old.append(float(W.iloc[i - 1][s]) if i > 0 else 0.0)
    o["w_old"] = w_old
    o["w_new"] = o["w_old"] + o["dw"]
    seg_full = np.where(np.isfinite(o["close_n"] / o["close_b"]), o["close_n"] / o["close_b"] - 1, 0.0)
    taker_gross = o["w_new"] * seg_full
    ltm_gross = np.where(o["filled"],
                         o["w_old"] * np.nan_to_num(o["fill_price"] / o["close_b"] - 1) + o["w_new"] * np.nan_to_num(o["close_n"] / o["fill_price"] - 1),
                         o["w_old"] * seg_full)
    o["d_gross"] = ltm_gross - taker_gross
    f, u = o[o["filled"]], o[~o["filled"]]
    half_rel = np.array([max(P["tick"].at[t, s], srel[s] * cn) / 2 / cn if np.isfinite(cn) and cn > 0 else srel[s] / 2
                         for t, s, cn in zip(u["ts_bar"], u["symbol"], u["close_n"])])
    fee_taker_parent = float((o["dw"].abs() * X.R2["cost_bps"] / 1e4).sum())
    fee_ltm = float((f["dw"].abs() * X.FEES["maker_bp"] / 1e4).sum() + (u["dw"].abs() * (X.FEES["taker_bp"] / 1e4 + half_rel)).sum())
    F1 = {"n_orders": int(len(o)), "n_filled": int(len(f)), "n_unfilled": int(len(u)),
          "gross_diff_total": float(o["d_gross"].sum()),
          "gross_diff_filled": float(f["d_gross"].sum()),
          "gross_diff_unfilled_missed_bar": float(u["d_gross"].sum()),
          "fee_parent_taker_total": fee_taker_parent, "fee_ltm_total": fee_ltm, "fee_saved": fee_taker_parent - fee_ltm,
          "net_diff_total": float(o["d_gross"].sum()) + fee_taker_parent - fee_ltm,
          "by_side": {sd: {"n": int(len(g)), "n_filled": int(g["filled"].sum()), "gross_diff": float(g["d_gross"].sum()),
                           "gross_diff_per_order_bp": float(g["d_gross"].mean() / max(g["dw"].abs().mean(), 1e-12) * 1e4)}
                      for sd, g in o.groupby("side")},
          "filled_price_vs_close_b_bp_mean": float(((f["fill_price"] / f["close_b"] - 1).abs()).mean() * 1e4),
          "filled_adverse_close_n_vs_L_bp_mean": float((np.where(f["side"] == "buy", 1, -1) * (f["close_n"] / f["fill_price"] - 1)).mean() * 1e4),
          "note": "d_gross is (LTM - taker) contribution of the order's bar in weight units; fees in weight units; sum over the dev window"}

    # ── F2 event-conditional 5-min drift on entry fills ──────────────────────
    ent = f[f["side"] == "buy"]
    drifts, mins = [], []
    for s_, grp in ent.groupby("symbol"):          # one symbol in memory at a time
        df = X.load_1m(s_, X.DEV_LO - pd.Timedelta(days=1), X.DEV_HI)
        if df is None:
            continue
        for _, r in grp.iterrows():
            t = pd.Timestamp(r["ts_bar"])
            tick = P["tick"].at[t, s_]
            thr = r["fill_price"] - fill["through_ticks"] * tick + 1e-6 * tick
            m = first_cross_minute(df, t, "buy", thr)
            if m is None:
                continue
            c5 = df["close"].get(t + pd.Timedelta(minutes=m + 5), np.nan)
            if np.isfinite(c5):
                drifts.append(c5 / r["fill_price"] - 1)
                mins.append(m)
        del df
    d = np.array(drifts)
    F2 = {"n_entry_fills": int(len(d)), "drift_5m_mean_bp": float(d.mean() * 1e4), "drift_5m_median_bp": float(np.median(d) * 1e4),
          "drift_5m_t": float(d.mean() / d.std(ddof=1) * np.sqrt(len(d))) if len(d) > 1 else None,
          "fill_minute_median": float(np.median(mins)) if mins else None,
          "fill_minute_share_le_5": float(np.mean(np.array(mins) <= 5)) if mins else None,
          "unconditional_P1_drift_5m_bp": json.loads((X.OUT / "p1_adverse_selection.json").read_text())["drift_5m_mean"] * 1e4}

    # ── F3 through=2 sensitivity ────────────────────────────────────────────
    out2 = passive_overlay(W, C, P["minlow_ex0"], P["maxhigh_ex0"], P["tick"], policy="LTM", rf_annual=X.R2["rf_annual"],
                           parent_cost_bp=X.R2["cost_bps"], **{**fill, "through_ticks": 2})
    F3 = {"through_ticks": 2, "net_sr": X.sharpe(out2["daily_net"]), "fill_rate": out2["fill_rate"],
          "note": "reported sensitivity only; registered rule = 1 tick"}

    # ── F4 per-year ─────────────────────────────────────────────────────────
    F4 = {"yearly_sr_LTM": run["LTM"]["yearly_sr"], "yearly_sr_taker": run["taker_simple"]["yearly_sr"],
          "fill_rate_by_year": run["LTM"]["fills"]["fill_rate_by_year"], "fill_rate_by_side": run["LTM"]["fills"]["fill_rate_by_side"]}

    out = {"F1_decomposition": F1, "F2_event_drift": F2, "F3_through2": F3, "F4_yearly": F4,
           "summary": {"sr_taker_parent": run["taker_simple"]["net_sr"], "sr_LTM": run["LTM"]["net_sr"], "sr_LOC": run["LOC"]["net_sr"],
                       "fill_rate_LTM": run["LTM"]["fill_rate"], "placebo_p_worse": run["placebo"]["p_worse"], "verdict": run["verdict"]}}
    (X.OUT / "forensics_R2.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "F1_decomposition"}, indent=1, default=str))
    print(json.dumps({k: v for k, v in F1.items() if k != "by_side"}, indent=1))
    print(json.dumps(F1["by_side"], indent=1))


if __name__ == "__main__":
    main()
