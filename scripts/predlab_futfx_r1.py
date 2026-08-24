"""xasset_futfx_r1 — champion one-shot on the futures+FX universe.

Registered 2026-08-20 (data/predlab/gates.json). Subcommands:
  probes     planted-alpha + return-oracle canary on the futfx panel
  integrity  P1 feasibility gates (breadth>=40 days, coverage, h==l median)
  run        one-shot + shift/xshuffle placebos + taker grid + sub-book
             disclosures. Refuses without passing probes/integrity or if
             the result exists.

Engine: opt.run_ls verbatim (fund=None) + overlay_o4 with breadth floor 40
(registered adaptation). Parkinson NaN on h==l bars; PA/CC/PL excluded
(frozen >20% h==l rule).
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
from predlab_xasset_r1 import ANN_EQ, OUTDIR, TAKER_BP, overlay_o4  # noqa: E402

STORE = PROJECT_ROOT / "data" / "xsect_futfx"
WINDOW = ("2017-01-03", "2026-08-14")
BREADTH_FLOOR = 40
EXCLUDE = {"PA=F", "PL=F", "CC=F"}      # frozen: frac_h_eq_l > 20%

PROBES_OUT = OUTDIR / "futfx_r1_probes.json"
INTEG_OUT = OUTDIR / "futfx_r1_integrity.json"
RESULT_OUT = OUTDIR / "futfx_r1_result.json"


def build_panels():
    closes, parks, counts, kinds = {}, {}, {}, {}
    for fp in sorted((STORE / "bars").glob("*.parquet")):
        sym = fp.stem.replace("_", "=")
        if sym in EXCLUDE:
            continue
        df = pd.read_parquet(fp).set_index("date").sort_index()
        closes[sym] = df["close"]
        park = (np.log(df["high"] / df["low"]) ** 2) / (4 * np.log(2))
        park[df["high"] <= df["low"]] = np.nan     # settlement-only bars
        parks[sym] = park
        counts[sym] = df["close"].notna().astype(float)
        kinds[sym] = "fx" if sym.endswith("=X") else "fut"
    close = pd.DataFrame(closes).sort_index()
    park = pd.DataFrame(parks).sort_index()
    avail = pd.DataFrame(counts).sort_index().fillna(0.0)
    for p in (close, park, avail):
        p.index = pd.DatetimeIndex(p.index).tz_localize("UTC")
    return close, park, avail, kinds


def monthly_mask(avail: pd.DataFrame, min_bars: int = 15) -> pd.DataFrame:
    """Member in month m iff >=15 bars in month m-1 (registered adaptation)."""
    cnt = avail.resample("MS").sum()
    mask = pd.DataFrame(False, index=avail.index, columns=avail.columns)
    months = cnt.index
    for i in range(1, len(months)):
        ok = cnt.iloc[i - 1] >= min_bars
        in_m = (avail.index >= months[i]) & (avail.index < months[i] + pd.offsets.MonthBegin(1))
        mask.loc[in_m, ok[ok].index] = True
    return mask


def inputs():
    close, park, avail, kinds = build_panels()
    # engine_correction_2026-08-24: simple returns — position PnL, never log
    ret = close.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    uni = monthly_mask(avail)
    sig = opt.build_signal(park, close, "ewma_20")
    return close, park, ret, uni, sig, kinds


def pipeline(sig, ret, uni, taker_bp=TAKER_BP, window=WINDOW):
    cfg = opt.OptConfig(taker_bp=taker_bp)
    raw = opt.run_ls(sig, ret, uni, None, cfg, *window)
    base = raw["rets"]
    breadth = (~sig.where(uni).isna()).sum(axis=1).reindex(base.index)
    ovl, scale = overlay_o4(base, breadth, 0.15, breadth_floor=BREADTH_FLOOR)
    return raw, base, breadth, ovl, scale


def sr_of(net, lo, hi):
    seg = net[(net.index >= lo) & (net.index <= hi)].dropna()
    return (ann_sr(seg.to_numpy(), periods_per_year=ANN_EQ)
            if len(seg) >= 20 else None), int(len(seg))


def quarters():
    days = pd.date_range(*WINDOW)
    cuts = [days[min(int(len(days) * i / 4), len(days) - 1)] for i in range(5)]
    return [(f"Q{i+1}", str(cuts[i].date()), str(cuts[i + 1].date()))
            for i in range(4)]


def cmd_probes() -> int:
    if PROBES_OUT.exists():
        print("probes exist — refusing")
        return 1
    close, park, ret, uni, sig, kinds = inputs()
    zs = sig.rank(axis=1, pct=True)
    cases = {
        "real_shifted_RAWONLY": (sig, ret),
        "canary_oracle": (-ret, ret),
        "planted_alpha": (sig, ret + 0.0020 * (1.0 - 2.0 * zs)),
    }
    res = {}
    for name, (s_, r_) in cases.items():
        raw, base, *_ = pipeline(s_, r_, uni)
        res[name] = ann_sr(base["net"].to_numpy(), periods_per_year=ANN_EQ)
        print(name, f"{res[name]:+.3f}", flush=True)
    out = {"equity_probes": res,
           "canary_pass": bool(res["canary_oracle"] > res["real_shifted_RAWONLY"] + 2.0),
           "planted_pass": bool(res["planted_alpha"] > res["real_shifted_RAWONLY"] + 1.0)}
    PROBES_OUT.write_text(json.dumps(out, indent=1, default=float))
    print("canary", out["canary_pass"], "planted", out["planted_pass"])
    return 0


def cmd_integrity() -> int:
    if INTEG_OUT.exists():
        print("integrity exists — refusing")
        return 1
    close, park, ret, uni, sig, kinds = inputs()
    lo = pd.Timestamp(WINDOW[0], tz="UTC")
    hi = pd.Timestamp(WINDOW[1], tz="UTC")
    win = (uni.index >= lo) & (uni.index <= hi)
    breadth = (~sig.where(uni).isna()).sum(axis=1)[win]
    days_ok = int((breadth >= BREADTH_FLOOR).sum())
    n_cov = int((close.notna().sum() >= 2000).sum())
    m = json.loads((STORE / "manifest.json").read_text())
    med_hl = float(np.median([v["frac_h_eq_l"] for k, v in m.items()
                              if k not in EXCLUDE]))
    out = {"breadth_days_ge_40": days_ok, "breadth_pass": bool(days_ok >= 2000),
           "median_breadth": float(breadth.median()),
           "instruments_ge_2000_bars": n_cov, "coverage_pass": bool(n_cov >= 55),
           "median_h_eq_l_included": med_hl, "hl_pass": bool(med_hl < 0.05),
           "n_instruments": int(close.shape[1])}
    ok = out["breadth_pass"] and out["coverage_pass"] and out["hl_pass"]
    out["verdict"] = "FEASIBLE" if ok else "INFEASIBLE"
    INTEG_OUT.write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1))
    return 0 if ok else 1


def cmd_run(n_draws: int = 400, seed: int = 20260820) -> int:
    if RESULT_OUT.exists():
        print("one-shot already spent — refusing")
        return 1
    probes = json.loads(PROBES_OUT.read_text())
    integ = json.loads(INTEG_OUT.read_text())
    if not (probes["canary_pass"] and probes["planted_pass"]):
        print("P0 not passing — refusing")
        return 1
    if integ["verdict"] != "FEASIBLE":
        print("P1 INFEASIBLE — refusing (trial unspent)")
        return 1
    close, park, ret, uni, sig, kinds = inputs()
    raw, base, breadth, ovl, scale = pipeline(sig, ret, uni)
    real_sr = ann_sr(ovl.dropna().to_numpy(), periods_per_year=ANN_EQ)

    subs = {}
    for label, lo, hi in quarters():
        subs[label], _ = sr_of(ovl, lo, hi)
    n_pos = sum(1 for v in subs.values() if (v or 0) > 0)

    grid = {}
    for tk in (2.5, 5.0, 10.0):
        if tk == TAKER_BP:
            grid[f"taker{tk:g}bp"] = real_sr
        else:
            _, _, _, o2, _ = pipeline(sig, ret, uni, taker_bp=tk)
            grid[f"taker{tk:g}bp"] = ann_sr(o2.dropna().to_numpy(),
                                            periods_per_year=ANN_EQ)

    fx_cols = [c for c in sig.columns if kinds.get(c) == "fx"]
    fut_cols = [c for c in sig.columns if kinds.get(c) == "fut"]
    sub_books = {}
    for lbl, cols in (("fx_only", fx_cols), ("fut_only", fut_cols)):
        raw_s = opt.run_ls(sig[cols], ret[cols], uni[cols], None,
                           opt.OptConfig(), *WINDOW)
        sub_books[lbl] = {"raw_net_sr": ann_sr(raw_s["rets"]["net"].to_numpy(),
                                               periods_per_year=ANN_EQ),
                          "note": "raw book, no overlay (disclosure only)"}

    rng = np.random.default_rng(seed)
    fam = {"shift": [], "xshuffle": []}
    n = len(sig.index)
    for i in range(n_draws):
        k = int(rng.integers(30, n - 30))
        s_shift = pd.DataFrame(np.roll(sig.to_numpy(), k, axis=0),
                               index=sig.index, columns=sig.columns)
        _, _, _, o_, _ = pipeline(s_shift, ret, uni)
        fam["shift"].append(ann_sr(o_.dropna().to_numpy(), periods_per_year=ANN_EQ))
        arr = sig.to_numpy().copy()
        for r_i in range(arr.shape[0]):
            row = arr[r_i]
            idx = np.where(~np.isnan(row))[0]
            row[idx] = row[rng.permutation(idx)]
        s_shuf = pd.DataFrame(arr, index=sig.index, columns=sig.columns)
        _, _, _, o_, _ = pipeline(s_shuf, ret, uni)
        fam["xshuffle"].append(ann_sr(o_.dropna().to_numpy(), periods_per_year=ANN_EQ))
        if (i + 1) % 50 == 0:
            print(f"placebo {i+1}/{n_draws}", flush=True)

    p_shift = float(np.mean([x >= real_sr for x in fam["shift"]]))
    p_xshuf = float(np.mean([x >= real_sr for x in fam["xshuffle"]]))
    u2 = bool(real_sr > 0 and p_shift < 0.05 and p_xshuf < 0.05
              and grid["taker10bp"] > 0)
    u1 = bool(u2 and real_sr >= 0.946 and n_pos >= 3)

    full_raw, _ = sr_of(base["net"], *WINDOW)
    res = {"experiment": "xasset_futfx_r1", "window": list(WINDOW),
           "raw_net_sr": full_raw,
           "raw_maxdd": max_drawdown(base["net"].dropna().to_numpy()),
           "ovl_sr": real_sr,
           "ovl_maxdd": max_drawdown(ovl.dropna().to_numpy()),
           "subperiods": subs, "subperiods_positive": f"{n_pos}/4",
           "taker_grid": grid, "sub_books": sub_books,
           "placebos": {"draws": n_draws, "p_shift": p_shift,
                        "p_xshuffle": p_xshuf,
                        "shift_q95": float(np.quantile(fam["shift"], 0.95))},
           "avg_scale": float(scale.mean()),
           "avg_turnover": float(base["turnover"].mean()),
           "median_breadth": float(breadth.median()),
           "max_name_share": float(raw["name_pnl"].abs().max()
                                   / raw["name_pnl"].abs().sum()),
           "max_name": str(raw["name_pnl"].abs().idxmax()),
           "verdicts": {"U1_transfer": u1, "U2_yields_returns": u2}}
    RESULT_OUT.write_text(json.dumps(res, indent=1, default=float))
    registry.log_trial("xasset_futfx_r1", "one_shot", "champion_verbatim_adapted",
                       {"signal": "ewma_20", "breadth_floor": BREADTH_FLOOR,
                        "taker_bp": TAKER_BP}, WINDOW,
                       {"ovl_sr": real_sr, "p_shift": p_shift,
                        "p_xshuffle": p_xshuf, "U1": u1, "U2": u2})
    print(json.dumps({k: res[k] for k in ("raw_net_sr", "ovl_sr",
                      "subperiods_positive", "taker_grid", "sub_books",
                      "placebos", "verdicts")}, indent=1, default=float))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["probes", "integrity", "run"])
    ap.add_argument("--draws", type=int, default=400)
    args = ap.parse_args()
    return {"probes": cmd_probes, "integrity": cmd_integrity,
            "run": lambda: cmd_run(n_draws=args.draws)}[args.cmd]()


if __name__ == "__main__":
    raise SystemExit(main())
