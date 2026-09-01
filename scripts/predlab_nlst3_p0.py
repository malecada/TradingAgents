"""nlst3 P0 — one-shot moonshot-ranking gates, EVAL SET ONLY (charter-frozen).

T1: Spearman IC(composite, ret7) > 0 on the fresh eval set (per-quarter
    KEEPs #121-180) AND quarter-block bootstrap (>=1000) 5th-pct > 0.
T2: top-quintile by composite: mean net ret7 > 0, NW one-sided p < 0.05,
    ex-top-event mean > 0, top-1 |contrib| <= 50%.
Both must pass; FAIL either => family CLOSED. One-shot (refuses re-run).
Per-feature eval-set ICs + IC_moon reported descriptively either way.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predlab_nlst_lib import ledger_append, nw_tstat, write_result  # noqa: E402
from predlab_nlst3_features import EVENTS3, OUT as FEATS, SIGNS  # noqa: E402

GATES = ROOT / "data" / "predlab" / "gates.json"


def block_bootstrap_ic(df: pd.DataFrame, col: str, n_draws: int = 1000,
                       seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    quarters = df["quarter"].unique()
    out = []
    for _ in range(n_draws):
        pick = rng.choice(quarters, size=len(quarters), replace=True)
        sub = pd.concat([df[df["quarter"] == q] for q in pick])
        out.append(st.spearmanr(sub[col], sub["ret7"])[0])
    return np.asarray(out, dtype=float)


def main() -> None:
    gates = json.loads(GATES.read_text())
    if gates["predlab_nlst3"].get("verdicts"):
        raise SystemExit("REFUSED: predlab_nlst3 verdicts already recorded (one-shot)")
    ev = pd.read_parquet(EVENTS3)
    ft = pd.read_parquet(FEATS)
    df = ev[["ret7", "list_date"]].join(ft, how="inner")
    ev_df = df[df["eval_set"]].dropna(subset=["legit3_score", "ret7"])
    print(f"eval events: {len(ev_df)} (full sample {len(df)})")

    ic, ic_p = st.spearmanr(ev_df["legit3_score"], ev_df["ret7"])
    boot = block_bootstrap_ic(ev_df, "legit3_score")
    p5 = float(np.nanpercentile(boot, 5))
    t1_pass = bool(ic > 0 and p5 > 0)

    q80 = ev_df["legit3_score"].quantile(0.8)
    top = ev_df[ev_df["legit3_score"] >= q80].sort_values("list_date")
    mean, t, p_two = nw_tstat(top["ret7"].to_numpy(), lag=5)
    p_one = p_two / 2 if t > 0 else 1 - p_two / 2
    ex_top = top["ret7"].drop(top["ret7"].abs().idxmax())
    top1_share = float(top["ret7"].abs().max() / top["ret7"].abs().sum())
    t2_pass = bool(mean > 0 and p_one < 0.05 and ex_top.mean() > 0
                   and top1_share <= 0.5)

    moon = (ev_df["ret7"] > 1).astype(int)
    ic_moon = float(st.spearmanr(ev_df["legit3_score"], moon)[0])
    feat_ics = {c: float(st.spearmanr(ev_df[c], ev_df["ret7"],
                                      nan_policy="omit")[0])
                for c in SIGNS}
    res = {
        "n_eval": int(len(ev_df)),
        "T1": {"ic": float(ic), "ic_p": float(ic_p), "boot_p5": p5,
               "pass": t1_pass},
        "T2": {"n_top": int(len(top)), "mean_ret7": mean, "nw_t": t,
               "p_one_sided": p_one, "mean_ex_top": float(ex_top.mean()),
               "median_ret7": float(top["ret7"].median()),
               "top1_share": top1_share, "pass": t2_pass},
        "descriptive": {"ic_moon": ic_moon, "feature_ics_eval": feat_ics,
                        "moon_rate_eval": float(moon.mean()),
                        "moon_rate_top": float((top["ret7"] > 1).mean()),
                        "eval_mean_ret7": float(ev_df["ret7"].mean())},
    }
    verdict = "PASS" if (t1_pass and t2_pass) else "FAIL"
    detail = (f"T1 IC={ic:+.3f} (boot p5 {p5:+.3f}) {'PASS' if t1_pass else 'FAIL'}; "
              f"T2 top-quintile mean ret7={mean:+.3f} p1={p_one:.4f} "
              f"ex-top={ex_top.mean():+.3f} top1={top1_share:.2f} "
              f"{'PASS' if t2_pass else 'FAIL'}")
    gates["predlab_nlst3"]["verdicts"] = {
        "nlst3_moonshot": f"{verdict} at P0 — {detail}" +
        ("" if verdict == "PASS" else "; family CLOSED")}
    GATES.write_text(json.dumps(gates, indent=1))
    ledger_append("predlab_nlst3_moonshot", cell="p0", model="composite_z",
                  config={"features": len(SIGNS), "min_feats": 6,
                          "selection": "top_quintile", "eval": "fresh_only"},
                  metrics={"ic": float(ic), "boot_p5": p5, "ic_moon": ic_moon,
                           "top_mean_ret7": mean, "top_p_one": p_one,
                           "verdict": verdict})
    write_result("nlst3_p0", res)
    print(json.dumps(res, indent=1, default=str))
    print(f"\nVERDICT: {verdict} — {detail}")


if __name__ == "__main__":
    main()
