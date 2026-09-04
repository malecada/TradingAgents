"""oflow forensics (negative verification): P0-vs-P1 alignment parity, z-decile monotonicity, leg decomposition."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from predlab_oflow_p1 import build_inputs, book, OptConfig  # noqa: E402
from tradingagents.predlab.xsec import daily_ic  # noqa: E402

sig, ret, uni, fund, idx = build_inputs()
# (1) IC on the P1 panels: sig row d (= z_{d-1}) vs ret row d
ic = daily_ic(sig, ret, min_breadth=25)
print("P1-panel IC mean", float(ic.mean()), "n", int(ic.notna().sum()))
# (2) pooled z-decile mean next-day return (in-universe names)
S = sig.where(uni); R = ret
rows = []
for d in S.index:
    s = S.loc[d].dropna(); r = R.loc[d].reindex(s.index)
    if len(s) < 25: continue
    dec = pd.qcut(s.rank(method="first"), 10, labels=False)
    rows.append(r.groupby(dec).mean())
dec_ret = pd.DataFrame(rows).mean() * 1e4
print("decile mean next-day return bp (0=lowest z):", dec_ret.round(2).to_dict())
# (3) leg decomposition with the registered book
cfg = OptConfig(signal="flow_z30", top_n=200, adv_floor=0.0, q_frac=0.2, weighting="eq", smooth=1, cadence=1, buffer=0.0, taker_bp=5.0)
res = book(sig, ret, uni, fund, cfg)
rets = res["rets"]
print("gross/net/cost/carry ann bp/day:", {c: round(float(rets[c].mean()*1e4), 2) for c in ("gross", "net", "cost", "carry")})
# long-only bottom quintile vs short-only top quintile gross
def leg_only(sign):
    out = []
    for d in S.index:
        s = S.loc[d].dropna()
        if len(s) < 25: continue
        q = max(int(len(s) * 0.2), 1)
        o = s.sort_values()
        names = o.index[:q] if sign > 0 else o.index[-q:]
        out.append((d, float(R.loc[d, names].mean())))
    return pd.Series(dict(out))
lo, hi = leg_only(+1), leg_only(-1)
ew = R.where(uni).mean(axis=1).reindex(lo.index)
print("bottom-z quintile mean bp/day", round(float(lo.mean()*1e4), 2), "top-z quintile", round(float(hi.mean()*1e4), 2), "EW universe", round(float(ew.mean()*1e4), 2))
print("bottom minus top bp/day", round(float((lo - hi).mean()*1e4), 2), "t", round(float((lo-hi).mean()/(lo-hi).std()*np.sqrt(len(lo))), 2))
json.dump({"p1_panel_ic": float(ic.mean()), "decile_ret_bp": dec_ret.round(3).to_dict(), "leg_bp": {"bottom": float(lo.mean()*1e4), "top": float(hi.mean()*1e4), "ew": float(ew.mean()*1e4)},
           "book_bp_day": {c: float(rets[c].mean()*1e4) for c in ("gross", "net", "cost", "carry")}}, open(ROOT / "data/predlab/oflow/forensics.json", "w"), indent=1)
