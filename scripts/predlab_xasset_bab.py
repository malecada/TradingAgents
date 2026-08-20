"""xasset_equity_bab — beta-neutral construction cycle (registered 2026-08-20).

Subcommands:
  dev      Run the 3 registered cells on DEV ONLY (2017-01-03..2023-12-31;
           the loop never reads a bar past dev end). Dev gates + shift
           placebos for cells passing the SR floor. Writes
           data/predlab/xasset_bab_dev.json + one ledger row per cell.
           Refuses if the dev file exists.
  holdout  One-shot spend for the single dev champion. Refuses unless the
           dev file names a champion; refuses if the verdict file exists.

Engine: a slim replica of opt.run_ls's daily loop (cadence 1, smooth 1,
no buffer — the champion path) extended with beta handling. Parity guard:
mode="plain" must match opt.run_ls net series to atol 1e-12 before any
cell runs (registered engine_parity_guard).
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
from predlab_xasset_r1 import (  # noqa: E402
    ANN_EQ, STORE, OUTDIR, TAKER_BP, BORROW_MAIN, overlay_o4, equity_inputs,
)

DEV = ("2017-01-03", "2023-12-31")
HOLDOUT = ("2024-01-01", "2026-08-14")
DEV_OUT = OUTDIR / "xasset_bab_dev.json"
HOLD_OUT = OUTDIR / "xasset_bab_holdout.json"

BETA_WIN, BETA_MIN, SHRINK = 252, 120, 0.6


# ------------------------------------------------------------------ beta

def spy_logret() -> pd.Series:
    spy = pd.read_parquet(STORE / "market" / "SPY.parquet").set_index("date")
    spy.index = pd.DatetimeIndex(spy.index).tz_localize("UTC")
    return np.log(spy["close"]).diff()


def build_beta(ret: pd.DataFrame, rm: pd.Series) -> pd.DataFrame:
    """Registered estimator: rolling 252d OLS slope vs SPY (min 120 obs),
    Vasicek shrink 0.6*beta + 0.4*1, shift(1). NaN (young names) -> handled
    as beta=1.0 at use sites (fully shrunk prior)."""
    rm_al = rm.reindex(ret.index)
    cov = ret.rolling(BETA_WIN, min_periods=BETA_MIN).cov(rm_al)
    var = rm_al.rolling(BETA_WIN, min_periods=BETA_MIN).var()
    beta = cov.div(var, axis=0)
    return (SHRINK * beta + (1 - SHRINK) * 1.0).shift(1)


# ------------------------------------------------------------------ engine

def run_ls_beta(sig, ret, uni, mode: str, beta=None, rm=None,
                taker_bp: float = TAKER_BP, window=DEV,
                q_frac: float = 0.2) -> pd.DataFrame:
    """Slim replica of opt.run_ls (champion path) + beta handling.
    mode: plain | leg_scale | hedge. Returns df with
    gross/net/turnover/cost/short_gross columns."""
    lo_ts = pd.Timestamp(window[0], tz="UTC")
    hi_ts = pd.Timestamp(window[1], tz="UTC")
    sig = sig.where(uni)
    days = [d for d in ret.index if lo_ts <= d <= hi_ts]
    prev_w = pd.Series(dtype=np.float64)
    prev_spy = 0.0
    out = []
    for d in days:
        if d not in sig.index:
            continue
        w = opt.leg_weights(sig.loc[d], q_frac, "eq")
        if len(w) == 0:
            continue
        w_spy = 0.0
        if mode != "plain":
            b_row = beta.loc[d].reindex(w.index).fillna(1.0) if d in beta.index \
                else pd.Series(1.0, index=w.index)
            if mode == "leg_scale":
                bl = float((w[w > 0] * b_row[w > 0]).sum())      # legs sum to 1
                bh = float((-w[w < 0] * b_row[w < 0]).sum())
                bl, bh = np.clip(bl, 0.3, 3.0), np.clip(bh, 0.3, 3.0)
                w = w.copy()
                w[w > 0] /= bl
                w[w < 0] /= bh
            elif mode == "hedge":
                w_spy = -float((w * b_row).sum())
            else:
                raise ValueError(mode)
        r_row = ret.loc[d].reindex(w.index)
        contrib = (w * r_row).fillna(0.0)
        gross = float(contrib.sum())
        if mode == "hedge":
            r_spy = rm.get(d, np.nan)
            gross += w_spy * (0.0 if pd.isna(r_spy) else float(r_spy))
        both = w.index.union(prev_w.index)
        turn = float((w.reindex(both, fill_value=0.0)
                      - prev_w.reindex(both, fill_value=0.0)).abs().sum())
        turn += abs(w_spy - prev_spy)
        cost = taker_bp / 1e4 * turn
        short_gross = float(-w[w < 0].sum()) + max(0.0, -w_spy)
        out.append({"date": d, "gross": gross, "net": gross - cost,
                    "turnover": turn, "cost": cost, "carry": 0.0,
                    "short_gross": short_gross})
        prev_w, prev_spy = w, w_spy
    return pd.DataFrame(out).set_index("date")


def cell_pipeline(sig, ret, uni, mode, beta, rm, window,
                  borrow=BORROW_MAIN, taker_bp=TAKER_BP):
    base = run_ls_beta(sig, ret, uni, mode, beta, rm,
                       taker_bp=taker_bp, window=window)
    breadth = (~sig.where(uni).isna()).sum(axis=1).reindex(base.index)
    ovl, scale = overlay_o4(base, breadth, 0.15)
    net_b = ovl - (borrow / ANN_EQ) * scale * base["short_gross"]
    return base, ovl, scale, net_b


def seg_sr(net: pd.Series, lo: str, hi: str):
    seg = net[(net.index >= lo) & (net.index <= hi)].dropna()
    if len(seg) < 20:
        return None, int(len(seg))
    return ann_sr(seg.to_numpy(), periods_per_year=ANN_EQ), int(len(seg))


def realized_beta(net: pd.Series, rm: pd.Series) -> float:
    al = pd.concat([net, rm], axis=1, join="inner").dropna()
    x, y = al.iloc[:, 1].to_numpy(), al.iloc[:, 0].to_numpy()
    return float(np.cov(y, x)[0, 1] / np.var(x))


def parity_guard(sig, ret, uni) -> None:
    """mode=plain must equal opt.run_ls net exactly (registered guard)."""
    slim = run_ls_beta(sig, ret, uni, "plain", window=("2018-01-01", "2019-12-31"))
    ref = opt.run_ls(sig, ret, uni, None, opt.OptConfig(),
                     "2018-01-01", "2019-12-31")["rets"]
    if not np.allclose(slim["net"].to_numpy(), ref["net"].to_numpy(), atol=1e-12):
        raise RuntimeError("engine parity guard FAILED — slim loop != opt.run_ls")
    print("engine parity guard PASS (slim == run_ls, atol 1e-12)")


def dev_quarters():
    days = pd.date_range(*DEV)
    cuts = [days[min(int(len(days) * i / 4), len(days) - 1)] for i in range(5)]
    return [(f"D{i+1}", str(cuts[i].date()), str(cuts[i + 1].date()))
            for i in range(4)]


# ------------------------------------------------------------------ dev

def cmd_dev(n_draws: int = 400, seed: int = 20260820) -> int:
    if DEV_OUT.exists():
        print(f"{DEV_OUT} exists — refusing to redo")
        return 1
    close, park, ret, uni = equity_inputs()
    sig = opt.build_signal(park, close, "ewma_20")
    rm = spy_logret()
    beta = build_beta(ret, rm)
    parity_guard(sig, ret, uni)

    # B1 uses leg_scale too (amendment 2026-08-20 pre-result, declared in
    # gates.json): champion-verbatim construction would carry the same
    # static -0.6 beta tilt and auto-fail the registered beta gate.
    cells = {"A1_leg_scale": ("leg_scale", sig),
             "A2_market_hedge": ("hedge", sig),
             "B1_beta_signal": ("leg_scale", beta)}
    res = {}
    for name, (mode, s_) in cells.items():
        base, ovl, scale, net_b = cell_pipeline(s_, ret, uni, mode, beta, rm, DEV)
        sr, nd = seg_sr(net_b, *DEV)
        nb3 = ovl - (0.03 / ANN_EQ) * scale * base["short_gross"]
        sr3, _ = seg_sr(nb3, *DEV)
        subs = {}
        for label, lo, hi in dev_quarters():
            subs[label], _ = seg_sr(net_b, lo, hi)
        n_pos = sum(1 for v in subs.values() if (v or 0) > 0)
        rb = realized_beta(base["net"], rm)
        row = {"mode": mode, "ovl_sr_dev": sr, "n_days": nd,
               "maxdd": max_drawdown(net_b.dropna().to_numpy()),
               "sr_borrow3": sr3, "subperiods": subs,
               "subperiods_positive": n_pos, "realized_beta": rb,
               "avg_turnover": float(base["turnover"].mean()),
               "avg_scale": float(scale.mean()),
               "sr_floor_pass": bool(sr is not None and sr >= 0.75),
               "beta_pass": bool(abs(rb) < 0.15)}
        res[name] = row
        print(f"{name}: dev ovl SR {sr:+.3f} | beta_realized {rb:+.3f} | "
              f"subs {n_pos}/4 | stress3 {sr3:+.3f}", flush=True)
        registry.log_trial("xasset_equity_bab", name, "beta_neutral",
                           {"mode": mode, "signal": "beta" if name == "B1_beta_signal"
                            else "ewma_20", "beta_est": "ols252_shrink0.6"},
                           DEV, {"ovl_sr_dev": sr, "realized_beta": rb})

    rng = np.random.default_rng(seed)
    for name, row in res.items():
        if not (row["sr_floor_pass"] and row["beta_pass"]):
            row["placebo"] = "not run (failed SR floor or beta gate)"
            continue
        mode = row["mode"]
        s_ = beta if name == "B1_beta_signal" else sig
        real = row["ovl_sr_dev"]
        n = len(s_.index)
        draws = []
        for i in range(n_draws):
            k = int(rng.integers(30, n - 30))
            s_shift = pd.DataFrame(np.roll(s_.to_numpy(), k, axis=0),
                                   index=s_.index, columns=s_.columns)
            _, _, _, nb_ = cell_pipeline(s_shift, ret, uni, mode, beta, rm, DEV)
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
    out = {"experiment": "xasset_equity_bab", "dev_window": list(DEV),
           "cells": res, "passing_cells": sorted(passing),
           "champion": champion}
    DEV_OUT.write_text(json.dumps(out, indent=1, default=float))
    print("champion:", champion)
    return 0


# ---------------------------------------------------------------- holdout

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
    beta = build_beta(ret, rm)
    mode = dev["cells"][champ]["mode"]
    s_ = beta if champ == "B1_beta_signal" else sig
    # full-window book so the overlay's 20d warmup uses late-dev history,
    # then metrics on the sealed slice only
    base, ovl, scale, net_b = cell_pipeline(s_, ret, uni, mode, beta, rm,
                                            (DEV[0], HOLDOUT[1]))
    sr_h, nd = seg_sr(net_b, *HOLDOUT)
    dev_sr = dev["cells"][champ]["ovl_sr_dev"]
    floor = max(0.5 * dev_sr, 0.0)
    verdict = bool(sr_h is not None and sr_h >= floor and sr_h > 0)
    seg = net_b[(net_b.index >= HOLDOUT[0]) & (net_b.index <= HOLDOUT[1])].dropna()
    out = {"champion": champ, "mode": mode, "holdout_window": list(HOLDOUT),
           "ovl_sr_holdout": sr_h, "n_days": nd,
           "maxdd_holdout": max_drawdown(seg.to_numpy()),
           "realized_beta_holdout": realized_beta(
               base["net"][base.index >= HOLDOUT[0]], rm),
           "dev_sr": dev_sr, "floor": floor, "PASS": verdict}
    HOLD_OUT.write_text(json.dumps(out, indent=1, default=float))
    registry.log_trial("xasset_equity_bab", f"holdout_{champ}", "one_shot",
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
