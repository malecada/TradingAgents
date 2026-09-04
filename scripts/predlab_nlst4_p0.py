"""nlst4 P0 — one-shot T1/T2 on the NEW pools only (charter 2026-09-04).

  python scripts/predlab_nlst4_p0.py

Refuses to run if gates.json["predlab_nlst4"]["verdicts"] exists. Gates:
T1 Spearman IC(composite, ret7) > 0 with quarter-block bootstrap 5th pct > 0;
T2 top-quintile mean net ret7 > 0 with NW one-sided p < 0.05 AND ex-top mean
> 0 AND top-1 share <= 0.25 AND $5k stress keeps the sign; median disclosed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from predlab_nlst3_features import SIGNS  # noqa: E402
from predlab_nlst3_p0 import block_bootstrap_ic  # noqa: E402
from predlab_nlst_lib import ledger_append, nw_tstat, write_result  # noqa: E402

NL = ROOT / "data" / "predlab" / "nlst"
GATES = ROOT / "data" / "predlab" / "gates.json"
KEY = "predlab_nlst4"
TOP1_MAX = 0.25


def main() -> None:
    gates = json.loads(GATES.read_text())
    if gates[KEY].get("verdicts"):
        raise SystemExit("REFUSED: predlab_nlst4 verdicts already recorded (one-shot)")
    ev = pd.read_parquet(NL / "nlst4_events.parquet")
    ft = pd.read_parquet(NL / "nlst4_features.parquet")
    df = ev[["ret7", "ret7_s5000", "list_date"]].join(ft, how="inner")
    new = df[df["new_set"]].dropna(subset=["legit3_score", "ret7"])
    new["quarter"] = new["quarter"].astype(str)
    print(f"new-set events: {len(new)} (full sample {len(df)})")
    ic, ic_p = st.spearmanr(new["legit3_score"], new["ret7"])
    boot = block_bootstrap_ic(new, "legit3_score")
    p5 = float(np.nanpercentile(boot, 5))
    t1_pass = bool(ic > 0 and p5 > 0)
    q80 = new["legit3_score"].quantile(0.8)
    top = new[new["legit3_score"] >= q80].sort_values("list_date")
    mean, t, p_two = nw_tstat(top["ret7"].to_numpy(), lag=5)
    p_one = p_two / 2 if t > 0 else 1 - p_two / 2
    ex_top = top["ret7"].drop(top["ret7"].abs().idxmax())
    top1_share = float(top["ret7"].abs().max() / top["ret7"].abs().sum())
    stress_mean = float(top["ret7_s5000"].mean())
    t2_pass = bool(mean > 0 and p_one < 0.05 and ex_top.mean() > 0 and top1_share <= TOP1_MAX
                   and np.sign(stress_mean) == np.sign(mean))
    moon = (new["ret7"] > 1).astype(int)
    res = {"n_new": int(len(new)), "n_quarters": int(new["quarter"].nunique()),
           "T1": {"ic": float(ic), "ic_p": float(ic_p), "boot_p5": p5, "pass": t1_pass},
           "T2": {"n_top": int(len(top)), "mean_ret7": mean, "nw_t": t, "p_one_sided": p_one,
                  "mean_ex_top": float(ex_top.mean()), "median_ret7": float(top["ret7"].median()),
                  "top1_share": top1_share, "mean_ret7_s5000": stress_mean, "pass": t2_pass},
           "descriptive": {"ic_moon": float(st.spearmanr(new["legit3_score"], moon)[0]),
                           "feature_ics_new": {c: float(st.spearmanr(new[c], new["ret7"], nan_policy="omit")[0]) for c in SIGNS},
                           "moon_rate_new": float(moon.mean()), "moon_rate_top": float((top["ret7"] > 1).mean()),
                           "new_mean_ret7": float(new["ret7"].mean()), "per_quarter_n": new["quarter"].value_counts().to_dict()}}
    verdict = "PASS" if (t1_pass and t2_pass) else "FAIL"
    detail = (f"T1 IC={ic:+.3f} (boot p5 {p5:+.3f}) {'PASS' if t1_pass else 'FAIL'}; "
              f"T2 top-quintile mean ret7={mean:+.3f} p1={p_one:.4f} ex-top={ex_top.mean():+.3f} "
              f"top1={top1_share:.2f} s5k={stress_mean:+.3f} {'PASS' if t2_pass else 'FAIL'}")
    gates[KEY]["verdicts"] = {"nlst4_p0": f"{verdict} at P0 — {detail}" + ("" if verdict == "PASS" else "; family CLOSED (final)")}
    GATES.write_text(json.dumps(gates, indent=1))
    ledger_append(KEY, cell="p0", model="composite_z_frozen",
                  config={"features": len(SIGNS), "min_feats": 6, "selection": "top_quintile", "eval": "new_set_only", "top1_max": TOP1_MAX},
                  metrics={"ic": float(ic), "boot_p5": p5, "top_mean_ret7": mean, "top_p_one": p_one, "top1_share": top1_share, "verdict": verdict})
    write_result("nlst4_p0", res)
    print(json.dumps(res, indent=1, default=str))
    print(f"\nVERDICT: {verdict} — {detail}")


if __name__ == "__main__":
    main()
