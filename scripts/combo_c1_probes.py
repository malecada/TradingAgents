"""combo_c1 blocking probes P0-P3 (charter docs/superpowers/specs/2026-09-02-combo-c1-charter.md).

Runs AFTER `combo_c1_register.py dev` and BEFORE the holdout spend. Writes
data/rebuild/combo_c1/probes.json. No holdout PnL is computed here: the only
holdout-window reads are coverage/breadth counts (P1).

P0 parity      — from register.json (pins to 1e-6).
P1 coverage    — store spans, PIT eligibility counts on the holdout, S4
                 signal-valid breadth, fundamentals_h1 vs sealed-store
                 restatement on the dev overlap.
P2 leakage     — (a) as registered: each dev sleeve's weight path advanced one
                 bar (W.shift(-1)) must raise its dev SR by >= +1.0;
                 (b) engine-timing oracle (supplementary, see AMENDMENT below):
                 |W| with the sign of the NEXT booked bar's return on the
                 sleeve's own traded names must raise dev SR by >= +1.0.
P3 correlation — dev pairwise |rho| <= 0.6 (disclosed, not blocking).

AMENDMENT (pre-holdout, 2026-09-02): the registered P2 wording ("signal one
bar into the future") is only a leakage detector for price-signal sleeves.
For the long-fade (advancing the trigger puts the book long DURING the crash
bar), the funding-carry (signal is funding, not price) and value (lag 2)
sleeves the literal shift cannot raise SR by construction, so a literal
STOP would block the cycle on a misspecified probe rather than on evidence.
Both (a) and (b) are computed and reported; the blocking criterion is (b)
for every sleeve, (a) for the momentum sleeve. Recorded in gates.json under
combo_c1.amendment_P2 by this script BEFORE any holdout number exists.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.combo_c1_register import (  # noqa: E402
    CM_FUND, CM_UNIV, DEV, FUND, GATES, HOLDOUT, KL, KL1H, OUT, build_dev_sleeves,
)
from tradingagents.xsect.combo import sharpe  # noqa: E402
from tradingagents.xsect.combo_sleeves import (  # noqa: E402
    CFG, SLEEVE_IDS, build_value, load_cm_mapping, sleeve_net,
)
from tradingagents.xsect.trend import monthly_refresh_dates  # noqa: E402
from tradingagents.xsect.universe import eligibility, load_klines, weekly_rebalance_dates  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CM_FUND_H1 = ROOT / "data/xsect/fundamentals_h1"
VAL_UNIV_H1 = ROOT / "data/xsect/value_xs_universe_h1.json"
LIQ_UNIV_H1 = ROOT / "data/xsect/liq_fade_universe_h1.json"
LIQ_SYMS_H1 = ROOT / "data/xsect/liq_fade_symbols_h1.txt"
MIN_BREADTH = 20
LEAK_MIN = 1.0
CORR_MAX = 0.6
WARMUP_VAL_H1 = "2024-09-01"


def _leak_shift(W: pd.DataFrame) -> pd.DataFrame:
    return W.shift(-1).fillna(0.0)


def _oracle(s) -> pd.DataFrame:
    """|W| signed by the next booked bar's return: daily engines book W[t-1]*R[t]
    (so W[t] should carry sign(R[t+1])); the hourly engine books W[i]*R[i]."""
    R = np.nan_to_num(s.R.to_numpy(), nan=0.0)
    nxt = R if s.engine == "hourly" else np.vstack([R[1:], np.zeros((1, R.shape[1]))])
    return pd.DataFrame(np.abs(s.W.to_numpy()) * np.sign(nxt), index=s.W.index, columns=s.W.columns)


def probe_p1(klines: dict) -> dict:
    lo, hi = pd.Timestamp(HOLDOUT[0], tz="UTC"), pd.Timestamp(HOLDOUT[1], tz="UTC")
    out = {"holdout": list(HOLDOUT), "stores": {}, "eligibility": {}, "value": {}, "restatement": {}}
    # store spans
    out["stores"]["klines_daily_end"] = str(max(d.index.max() for d in klines.values()))[:10]
    out["stores"]["klines_daily_n_covering"] = int(sum(d.index.max() >= hi for d in klines.values()))
    liq_syms = [s for s in LIQ_SYMS_H1.read_text().split() if s]
    ends_1h = {}
    for s in liq_syms:
        p = KL1H / f"{s}.parquet"
        if p.exists():
            ends_1h[s] = pd.read_parquet(p, columns=["close"]).index.max()
    out["stores"]["klines_1h_liq_symbols"] = len(liq_syms)
    out["stores"]["klines_1h_present"] = len(ends_1h)
    out["stores"]["klines_1h_covering_holdout_end"] = int(sum(e >= hi + pd.Timedelta(hours=23) for e in ends_1h.values()))
    out["stores"]["klines_1h_missing"] = sorted(set(liq_syms) - set(ends_1h))
    refresh = monthly_refresh_dates(*HOLDOUT)
    carry_members = {d: eligibility(klines, d, top_n=CFG["carry"]["top_n"]) for d in refresh}
    carry_union = sorted(set().union(*[set(v) for v in carry_members.values()]))
    ends_f = {}
    for s in carry_union:
        p = FUND / f"{s}.parquet"
        if p.exists():
            ends_f[s] = pd.read_parquet(p).index.max()
    out["stores"]["funding_carry_union"] = len(carry_union)
    out["stores"]["funding_present"] = len(ends_f)
    out["stores"]["funding_covering_holdout_end"] = int(sum(e >= hi for e in ends_f.values()))
    out["stores"]["funding_end_max"] = str(max(ends_f.values()))[:10] if ends_f else None
    # PIT eligibility counts
    reb = weekly_rebalance_dates(*HOLDOUT)
    mom_n = {str(t.date()): len(eligibility(klines, t, top_n=CFG["momentum"]["top_n"])) for t in reb}
    car_n = {str(d.date()): len(v) for d, v in carry_members.items()}
    liq_u = json.loads(LIQ_UNIV_H1.read_text())
    liq_n = {k: len(v) for k, v in liq_u.items()}
    out["eligibility"] = {"momentum_weekly": mom_n, "momentum_min": min(mom_n.values()),
                          "carry_monthly": car_n, "carry_min": min(car_n.values()),
                          "liq_fade_monthly": liq_n, "liq_fade_min": min(liq_n.values())}
    # value breadth on the holdout (weights only, no PnL)
    if CM_FUND_H1.exists() and any(CM_FUND_H1.glob("*.parquet")):
        mapping = load_cm_mapping(CM_UNIV)
        univ = json.loads(VAL_UNIV_H1.read_text())
        sv = build_value(klines, CM_FUND_H1, mapping, univ, WARMUP_VAL_H1, lo, hi)
        out["value"] = {"present": True, **{k: v for k, v in sv.meta.items() if k != "breadth_weekly"},
                        "breadth_weekly": sv.meta["breadth_weekly"]}
        # fundamentals_h1 coverage per symbol
        last = {}
        for p in sorted(CM_FUND_H1.glob("*.parquet")):
            d = pd.read_parquet(p)
            last[p.stem] = str(d.index.max())[:10] if len(d) else None
        out["value"]["fund_h1_assets"] = len(last)
        out["value"]["fund_h1_covering_2026-06-29"] = int(sum(v is not None and v >= "2026-06-29" for v in last.values()))
        # restatement on the dev overlap vs the sealed store
        rs = {}
        for p in sorted(CM_FUND_H1.glob("*.parquet")):
            q = CM_FUND / p.name
            if not q.exists():
                continue
            a, b = pd.read_parquet(p), pd.read_parquet(q)
            j = a.join(b, how="inner", lsuffix="_h1", rsuffix="_sealed")
            j = j.loc[(j.index >= pd.Timestamp(DEV[0], tz="UTC")) & (j.index <= pd.Timestamp(DEV[1], tz="UTC"))]
            if j.empty:
                continue
            per = {}
            for m in ("AdrActCnt", "TxCnt", "CapMrktCurUSD"):
                x, y = j[f"{m}_h1"], j[f"{m}_sealed"]
                rel = ((x - y).abs() / y.abs().where(y.abs() > 0)).dropna()
                per[m] = {"n": int(len(rel)), "max_rel": float(rel.max()) if len(rel) else 0.0,
                          "frac_gt_1e-6": float((rel > 1e-6).mean()) if len(rel) else 0.0}
            rs[p.stem] = per
        out["restatement"] = {
            "n_assets_compared": len(rs),
            "max_rel_any": max((v[m]["max_rel"] for v in rs.values() for m in v), default=0.0),
            "assets_with_any_change": sorted(a for a, v in rs.items() if any(v[m]["frac_gt_1e-6"] > 0 for m in v)),
            "per_asset": rs,
        }
    else:
        out["value"] = {"present": False}
    ok = (out["stores"]["klines_daily_end"] >= HOLDOUT[1]
          and out["stores"]["klines_1h_covering_holdout_end"] >= MIN_BREADTH
          and out["stores"]["funding_covering_holdout_end"] >= MIN_BREADTH
          and out["eligibility"]["momentum_min"] >= MIN_BREADTH
          and out["eligibility"]["carry_min"] >= MIN_BREADTH
          and out["eligibility"]["liq_fade_min"] >= MIN_BREADTH
          and out["value"].get("present", False)
          and out["value"].get("breadth_median", 0) >= MIN_BREADTH)
    out["pass"] = bool(ok)
    out["verdict"] = "PASS" if ok else "STOP (data)"
    return out


def probe_p2(sleeves: dict) -> dict:
    out = {"registered_rule": "W.shift(-1) raises dev SR by >= +1.0 per sleeve",
           "amended_rule": "oracle |W|*sign(next booked return) raises dev SR by >= +1.0 per sleeve; literal shift additionally required for momentum",
           "sleeves": {}}
    for sid in SLEEVE_IDS:
        s = sleeves[sid]
        base = sharpe(sleeve_net(s))
        lit = sharpe(sleeve_net(s, W=_leak_shift(s.W)))
        ora = sharpe(sleeve_net(s, W=_oracle(s)))
        out["sleeves"][sid] = {"sr_base": base, "sr_literal_shift": lit, "delta_literal": lit - base,
                               "sr_oracle": ora, "delta_oracle": ora - base,
                               "literal_pass": bool(lit - base >= LEAK_MIN),
                               "oracle_pass": bool(ora - base >= LEAK_MIN)}
        print(f"P2 {sid:9s} base {base:+.3f} literal {lit:+.3f} (d {lit-base:+.2f}) oracle {ora:+.3f} (d {ora-base:+.2f})")
    ok = all(v["oracle_pass"] for v in out["sleeves"].values()) and out["sleeves"]["momentum"]["literal_pass"]
    out["literal_pass_all"] = all(v["literal_pass"] for v in out["sleeves"].values())
    out["pass"] = bool(ok)
    out["verdict"] = "PASS" if ok else "STOP (harness)"
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--accept-amendment-p2b", action="store_true",
                    help=("USER DECISION ONLY: adopt amendment P2b — the engine-timing oracle is the "
                          "sole blocking P2 criterion for every sleeve; the literal W.shift(-1) "
                          "numbers stay reported. Recorded in gates.json combo_c1.amendment_P2b."))
    args = ap.parse_args()
    t0 = time.time()
    reg = json.loads((OUT / "register.json").read_text())
    gates = json.loads(GATES.read_text())
    assert "registered_dev" in gates["combo_c1"], "run register dev first"
    if (OUT / "holdout_verdict.json").exists():
        raise SystemExit("holdout already spent; probes are frozen")
    p0 = {"parity": reg["parity"], "pass": bool(reg["p0_pass"]),
          "verdict": "PASS" if reg["p0_pass"] else "STOP (harness)"}
    print(f"P0 {p0['verdict']}")
    klines = load_klines(KL)
    p1 = probe_p1(klines)
    print(f"P1 {p1['verdict']}: mom_min {p1['eligibility']['momentum_min']} carry_min {p1['eligibility']['carry_min']} "
          f"liq_min {p1['eligibility']['liq_fade_min']} value {p1['value']}"[:400])
    sleeves = build_dev_sleeves(t0)
    p2 = probe_p2(sleeves)
    print(f"P2 {p2['verdict']}")
    corr = reg["corr_dev"]
    pairs = {f"{a}|{b}": corr[a][b] for i, a in enumerate(SLEEVE_IDS) for b in SLEEVE_IDS[i + 1:]}
    p3 = {"pairs": pairs, "max_abs": max(abs(v) for v in pairs.values()),
          "pass": bool(all(abs(v) <= CORR_MAX for v in pairs.values()))}
    p3["verdict"] = "PASS" if p3["pass"] else "DISCLOSED (premise weakened; W1 unchanged)"
    print(f"P3 {p3['verdict']}: max |rho| {p3['max_abs']:.3f}")
    if args.accept_amendment_p2b:
        p2["pass_p2b"] = bool(all(v["oracle_pass"] for v in p2["sleeves"].values()))
        p2["verdict"] = ("PASS (amendment P2b: oracle-only)" if p2["pass_p2b"]
                         else "STOP (harness; oracle failed under P2b)")
        p2["blocking_rule"] = "P2b"
        gates["combo_c1"]["amendment_P2b"] = {
            "when": pd.Timestamp.utcnow().isoformat(),
            "decided_by": "user (explicit --accept-amendment-p2b)",
            "rule": "engine-timing oracle >= +1.0 for every sleeve is the sole blocking P2 criterion; literal W.shift(-1) reported not gated",
            "literal_results": {k: v["delta_literal"] for k, v in p2["sleeves"].items()},
            "oracle_results": {k: v["delta_oracle"] for k, v in p2["sleeves"].items()},
            "note": "P2a STOP (momentum literal +0.86 < +1.0) stands on record; no holdout number existed at decision time",
        }
        p2_block = p2["pass_p2b"]
    else:
        p2_block = p2["pass"]
    blocking = p0["pass"] and p1["pass"] and p2_block
    out = {"P0": p0, "P1": p1, "P2": p2, "P3": p3, "blocking_pass": bool(blocking),
           "runtime_sec": time.time() - t0, "computed": pd.Timestamp.utcnow().isoformat()}
    (OUT / "probes.json").write_text(json.dumps(out, indent=1, default=str))
    gates["combo_c1"]["amendment_P2"] = {
        "when": "2026-09-02, after register dev, before any holdout number",
        "why": "registered wording only detects leakage for price-signal sleeves; literal shift lowers SR by construction for long-fade (long during the crash bar), funding carry (signal is funding) and value (lag 2)",
        "rule": "engine-timing oracle |W|*sign(next booked return) must raise dev SR >= +1.0 for every sleeve; literal W.shift(-1) additionally required for momentum; literal numbers reported for all",
        "literal_results": {k: v["delta_literal"] for k, v in p2["sleeves"].items()},
    }
    gates["combo_c1"]["probes"] = {**gates["combo_c1"]["probes"],
                                   "verdicts": {"P0": p0["verdict"], "P1": p1["verdict"],
                                                "P2": p2["verdict"], "P3": p3["verdict"]}}
    GATES.write_text(json.dumps(gates, indent=1))
    print(f"blocking probes {'PASS' if blocking else 'STOP'} ({time.time()-t0:.0f}s)")
    if not blocking:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
