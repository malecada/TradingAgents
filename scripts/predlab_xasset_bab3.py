"""xasset_equity_bab3 — final equity cycle (registered 2026-08-20).

Single cell C2f_book_hedge: bab2's C2 with the clip bound widened to
[-1.5, +1.5] (the book needs a +0.83 SPY hedge; the old +0.5 cap was a
mechanical bound error). Shift placebo runs REGARDLESS of the SR floor
this cycle (registered disclosure policy); it remains a championship gate.
Equity program closes after this cycle either way.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import opt, registry  # noqa: E402
from tradingagents.predlab.pp import ann_sr, max_drawdown  # noqa: E402
from predlab_xasset_r1 import ANN_EQ, OUTDIR, TAKER_BP, BORROW_MAIN, overlay_o4, equity_inputs  # noqa: E402
from predlab_xasset_bab import (  # noqa: E402
    DEV, HOLDOUT, spy_logret, run_ls_beta, seg_sr, realized_beta,
    parity_guard, dev_quarters,
)

DEV_OUT = OUTDIR / "xasset_bab3_dev.json"
HOLD_OUT = OUTDIR / "xasset_bab3_holdout.json"
BOOK_WIN, BOOK_MIN, CLIP = 126, 60, 1.5


def book_hedge_v2(base_plain: pd.DataFrame, rm: pd.Series,
                  taker_bp: float = TAKER_BP) -> pd.DataFrame:
    net0 = base_plain["net"]
    rm_al = rm.reindex(net0.index)
    cov = net0.rolling(BOOK_WIN, min_periods=BOOK_MIN).cov(rm_al)
    var = rm_al.rolling(BOOK_WIN, min_periods=BOOK_MIN).var()
    w_spy = (-(cov / var)).clip(-CLIP, CLIP).shift(1).fillna(0.0)
    dcost = taker_bp / 1e4 * w_spy.diff().abs().fillna(w_spy.abs())
    out = base_plain.copy()
    out["net"] = net0 + w_spy * rm_al.fillna(0.0) - dcost
    out["gross"] = base_plain["gross"] + w_spy * rm_al.fillna(0.0)
    out["turnover"] = base_plain["turnover"] + w_spy.diff().abs().fillna(w_spy.abs())
    out["short_gross"] = base_plain["short_gross"] + (-w_spy).clip(lower=0.0)
    return out


def cell(sig, ret, uni, rm, window, borrow=BORROW_MAIN):
    base = book_hedge_v2(run_ls_beta(sig, ret, uni, "plain", window=window), rm)
    breadth = (~sig.where(uni).isna()).sum(axis=1).reindex(base.index)
    ovl, scale = overlay_o4(base, breadth, 0.15)
    net_b = ovl - (borrow / ANN_EQ) * scale * base["short_gross"]
    return base, ovl, scale, net_b


def cmd_dev(n_draws: int = 400, seed: int = 20260820) -> int:
    if DEV_OUT.exists():
        print(f"{DEV_OUT} exists — refusing to redo")
        return 1
    close, park, ret, uni = equity_inputs()
    sig = opt.build_signal(park, close, "ewma_20")
    rm = spy_logret()
    parity_guard(sig, ret, uni)

    base, ovl, scale, net_b = cell(sig, ret, uni, rm, DEV)
    sr, nd = seg_sr(net_b, *DEV)
    nb3 = ovl - (0.03 / ANN_EQ) * scale * base["short_gross"]
    sr3, _ = seg_sr(nb3, *DEV)
    subs = {}
    for label, lo, hi in dev_quarters():
        subs[label], _ = seg_sr(net_b, lo, hi)
    n_pos = sum(1 for v in subs.values() if (v or 0) > 0)
    rb = realized_beta(base["net"], rm)
    row = {"mode": "book_hedge_v2_clip1.5", "ovl_sr_dev": sr, "n_days": nd,
           "maxdd": max_drawdown(net_b.dropna().to_numpy()),
           "sr_borrow3": sr3, "subperiods": subs, "subperiods_positive": n_pos,
           "realized_beta": rb, "avg_turnover": float(base["turnover"].mean()),
           "avg_scale": float(scale.mean()),
           "sr_floor_pass": bool(sr is not None and sr >= 0.75),
           "beta_pass": bool(abs(rb) < 0.15)}
    print(f"C2f: dev ovl SR {sr:+.3f} | beta {rb:+.3f} | subs {n_pos}/4 | "
          f"stress3 {sr3:+.3f}", flush=True)
    registry.log_trial("xasset_equity_bab3", "C2f_book_hedge", "beta_neutral_v3",
                       {"mode": "book_hedge", "clip": CLIP}, DEV,
                       {"ovl_sr_dev": sr, "realized_beta": rb})

    # placebo runs regardless (registered disclosure policy)
    rng = np.random.default_rng(seed)
    n = len(sig.index)
    draws = []
    for i in range(n_draws):
        k = int(rng.integers(30, n - 30))
        s_shift = pd.DataFrame(np.roll(sig.to_numpy(), k, axis=0),
                               index=sig.index, columns=sig.columns)
        _, _, _, nb_ = cell(s_shift, ret, uni, rm, DEV)
        v, _ = seg_sr(nb_, *DEV)
        draws.append(v if v is not None else 0.0)
        if (i + 1) % 50 == 0:
            print(f"placebo {i+1}/{n_draws}", flush=True)
    p = float(np.mean([x >= (sr or 0.0) for x in draws]))
    row["placebo"] = {"p_shift": p, "draws": n_draws,
                      "q95": float(np.quantile(draws, 0.95)),
                      "q50": float(np.quantile(draws, 0.50))}
    row["placebo_pass"] = bool(p < 0.05)

    champion = "C2f_book_hedge" if (
        row["sr_floor_pass"] and row["beta_pass"] and n_pos >= 3
        and (sr3 or 0) > 0 and row["placebo_pass"]) else None
    DEV_OUT.write_text(json.dumps(
        {"experiment": "xasset_equity_bab3", "dev_window": list(DEV),
         "cells": {"C2f_book_hedge": row}, "champion": champion},
        indent=1, default=float))
    print("champion:", champion)
    return 0


def cmd_holdout() -> int:
    if HOLD_OUT.exists():
        print(f"{HOLD_OUT} exists — one-shot already spent, refusing")
        return 1
    dev = json.loads(DEV_OUT.read_text())
    champ = dev.get("champion")
    if not champ:
        print("no dev champion — cycle dead, refusing holdout spend")
        return 1
    close, park, ret, uni = equity_inputs()
    sig = opt.build_signal(park, close, "ewma_20")
    rm = spy_logret()
    base, ovl, scale, net_b = cell(sig, ret, uni, rm, (DEV[0], HOLDOUT[1]))
    sr_h, nd = seg_sr(net_b, *HOLDOUT)
    dev_sr = dev["cells"][champ]["ovl_sr_dev"]
    floor = max(0.5 * dev_sr, 0.0)
    verdict = bool(sr_h is not None and sr_h >= floor and sr_h > 0)
    seg = net_b[(net_b.index >= HOLDOUT[0]) & (net_b.index <= HOLDOUT[1])].dropna()
    out = {"champion": champ, "holdout_window": list(HOLDOUT),
           "ovl_sr_holdout": sr_h, "n_days": nd,
           "maxdd_holdout": max_drawdown(seg.to_numpy()),
           "realized_beta_holdout": realized_beta(
               base["net"][base.index >= HOLDOUT[0]], rm),
           "dev_sr": dev_sr, "floor": floor, "PASS": verdict}
    HOLD_OUT.write_text(json.dumps(out, indent=1, default=float))
    registry.log_trial("xasset_equity_bab3", f"holdout_{champ}", "one_shot",
                       {"clip": CLIP}, HOLDOUT,
                       {"ovl_sr_holdout": sr_h, "floor": floor, "PASS": verdict})
    print(json.dumps(out, indent=1, default=float))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["dev", "holdout"])
    ap.add_argument("--draws", type=int, default=400)
    args = ap.parse_args()
    return cmd_dev(n_draws=args.draws) if args.cmd == "dev" else cmd_holdout()


if __name__ == "__main__":
    raise SystemExit(main())
