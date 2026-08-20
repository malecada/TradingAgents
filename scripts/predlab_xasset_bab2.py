"""xasset_equity_bab2 — beta-neutral cycle 2 (registered 2026-08-20).

Fixes the bab-cycle estimator bias: the 0.6-shrunk betas under-hedge ~40%
of the true beta gap. Two cells:
  C1_unshrunk_hedge  name-level hedge sized on UNSHRUNK rolling betas
  C2_book_hedge      book-level self-correcting hedge (rolling 126d OLS of
                     the pre-hedge book net on SPY, shift(1), clip [-1.5,.5])

Reuses the parity-guarded engine from predlab_xasset_bab. Same subcommand
discipline: `dev` (refuses redo) then `holdout` (one-shot, verdict lock).
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
    DEV, HOLDOUT, SHRINK, spy_logret, build_beta, run_ls_beta, seg_sr,
    realized_beta, parity_guard, dev_quarters,
)

DEV_OUT = OUTDIR / "xasset_bab2_dev.json"
HOLD_OUT = OUTDIR / "xasset_bab2_holdout.json"
BOOK_WIN, BOOK_MIN = 126, 60


def book_hedge(base_plain: pd.DataFrame, rm: pd.Series,
               taker_bp: float = TAKER_BP) -> pd.DataFrame:
    """C2: post-process book-level hedge on the plain champion book."""
    net0 = base_plain["net"]
    rm_al = rm.reindex(net0.index)
    cov = net0.rolling(BOOK_WIN, min_periods=BOOK_MIN).cov(rm_al)
    var = rm_al.rolling(BOOK_WIN, min_periods=BOOK_MIN).var()
    w_spy = (-(cov / var)).clip(-1.5, 0.5).shift(1).fillna(0.0)
    dcost = taker_bp / 1e4 * w_spy.diff().abs().fillna(w_spy.abs())
    out = base_plain.copy()
    out["net"] = net0 + w_spy * rm_al.fillna(0.0) - dcost
    out["gross"] = base_plain["gross"] + w_spy * rm_al.fillna(0.0)
    out["turnover"] = base_plain["turnover"] + w_spy.diff().abs().fillna(w_spy.abs())
    out["short_gross"] = base_plain["short_gross"] + (-w_spy).clip(lower=0.0)
    out["w_spy"] = w_spy
    return out


def cell_book(sig, ret, uni, beta_unused, rm, window, mode: str,
              borrow=BORROW_MAIN):
    """Build one bab2 cell book + overlay + borrow."""
    if mode == "book_hedge":
        base_plain = run_ls_beta(sig, ret, uni, "plain", window=window)
        base = book_hedge(base_plain, rm)
    elif mode == "hedge_unshrunk":
        base = run_ls_beta(sig, ret, uni, "hedge", beta_unused, rm, window=window)
    else:
        raise ValueError(mode)
    breadth_src = sig.where(uni)
    breadth = (~breadth_src.isna()).sum(axis=1).reindex(base.index)
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
    beta_shrunk = build_beta(ret, rm)
    beta_u = (beta_shrunk - (1 - SHRINK)) / SHRINK    # invert the shrink
    parity_guard(sig, ret, uni)

    cells = {"C1_unshrunk_hedge": "hedge_unshrunk", "C2_book_hedge": "book_hedge"}
    res = {}
    for name, mode in cells.items():
        base, ovl, scale, net_b = cell_book(sig, ret, uni, beta_u, rm, DEV, mode)
        sr, nd = seg_sr(net_b, *DEV)
        nb3 = ovl - (0.03 / ANN_EQ) * scale * base["short_gross"]
        sr3, _ = seg_sr(nb3, *DEV)
        subs = {}
        for label, lo, hi in dev_quarters():
            subs[label], _ = seg_sr(net_b, lo, hi)
        n_pos = sum(1 for v in subs.values() if (v or 0) > 0)
        rb = realized_beta(base["net"], rm)
        res[name] = {"mode": mode, "ovl_sr_dev": sr, "n_days": nd,
                     "maxdd": max_drawdown(net_b.dropna().to_numpy()),
                     "sr_borrow3": sr3, "subperiods": subs,
                     "subperiods_positive": n_pos, "realized_beta": rb,
                     "avg_turnover": float(base["turnover"].mean()),
                     "avg_scale": float(scale.mean()),
                     "sr_floor_pass": bool(sr is not None and sr >= 0.75),
                     "beta_pass": bool(abs(rb) < 0.15)}
        print(f"{name}: dev ovl SR {sr:+.3f} | beta {rb:+.3f} | subs {n_pos}/4 "
              f"| stress3 {sr3:+.3f}", flush=True)
        registry.log_trial("xasset_equity_bab2", name, "beta_neutral_v2",
                           {"mode": mode}, DEV,
                           {"ovl_sr_dev": sr, "realized_beta": rb})

    rng = np.random.default_rng(seed)
    for name, row in res.items():
        if not (row["sr_floor_pass"] and row["beta_pass"]):
            row["placebo"] = "not run (failed SR floor or beta gate)"
            continue
        real = row["ovl_sr_dev"]
        n = len(sig.index)
        draws = []
        for i in range(n_draws):
            k = int(rng.integers(30, n - 30))
            s_shift = pd.DataFrame(np.roll(sig.to_numpy(), k, axis=0),
                                   index=sig.index, columns=sig.columns)
            _, _, _, nb_ = cell_book(s_shift, ret, uni, beta_u, rm, DEV,
                                     row["mode"])
            v, _ = seg_sr(nb_, *DEV)
            draws.append(v if v is not None else 0.0)
            if (i + 1) % 50 == 0:
                print(f"{name} placebo {i+1}/{n_draws}", flush=True)
        p = float(np.mean([x >= real for x in draws]))
        row["placebo"] = {"p_shift": p, "draws": n_draws,
                          "q95": float(np.quantile(draws, 0.95))}
        row["placebo_pass"] = bool(p < 0.05)

    passing = {k: v for k, v in res.items()
               if v["sr_floor_pass"] and v["beta_pass"]
               and v["subperiods_positive"] >= 3
               and (v.get("sr_borrow3") or 0) > 0
               and v.get("placebo_pass", False)}
    champion = max(passing, key=lambda k: passing[k]["ovl_sr_dev"]) if passing else None
    DEV_OUT.write_text(json.dumps(
        {"experiment": "xasset_equity_bab2", "dev_window": list(DEV),
         "cells": res, "passing_cells": sorted(passing), "champion": champion},
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
    beta_u = (build_beta(ret, rm) - (1 - SHRINK)) / SHRINK
    mode = dev["cells"][champ]["mode"]
    base, ovl, scale, net_b = cell_book(sig, ret, uni, beta_u, rm,
                                        (DEV[0], HOLDOUT[1]), mode)
    sr_h, nd = seg_sr(net_b, *HOLDOUT)
    dev_sr = dev["cells"][champ]["ovl_sr_dev"]
    floor = max(0.5 * dev_sr, 0.0)
    verdict = bool(sr_h is not None and sr_h >= floor and sr_h > 0)
    seg = net_b[(net_b.index >= HOLDOUT[0]) & (net_b.index <= HOLDOUT[1])].dropna()
    hold_beta = realized_beta(base["net"][base.index >= HOLDOUT[0]], rm)
    out = {"champion": champ, "mode": mode, "holdout_window": list(HOLDOUT),
           "ovl_sr_holdout": sr_h, "n_days": nd,
           "maxdd_holdout": max_drawdown(seg.to_numpy()),
           "realized_beta_holdout": hold_beta,
           "dev_sr": dev_sr, "floor": floor, "PASS": verdict}
    HOLD_OUT.write_text(json.dumps(out, indent=1, default=float))
    registry.log_trial("xasset_equity_bab2", f"holdout_{champ}", "one_shot",
                       {"mode": mode}, HOLDOUT,
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
