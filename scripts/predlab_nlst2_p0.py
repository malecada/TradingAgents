"""nlst2 P0 — one-shot legitimacy-classifier gates (charter-frozen).

T1: AUC(legit_score -> rug-within-14d avoided) >= 0.65 AND quarter-block
    bootstrap (>=1000 draws) 5th percentile >= 0.55.
T2: top-half by legit_score (pooled median split, fixed): mean net ret7 > 0,
    NW t one-sided p < 0.05, AND ex-top-event mean > 0.
Both must pass; FAIL either => cycle CLOSED. Verdict written once
(refuses re-run on non-empty verdicts). Event table built fresh for the
extended sample into nlst2_events.parquet (nlst artifacts untouched).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predlab_nlst_lib import ledger_append, nw_tstat, write_result  # noqa: E402
from predlab_nlst_dex_p0 import (  # noqa: E402
    eth_usd_series, load_anchors, pool_event,
)
from predlab_nlst_dex_fetch import RAW  # noqa: E402

GATES = ROOT / "data" / "predlab" / "gates.json"
FEATS = ROOT / "data" / "predlab" / "nlst" / "nlst2_features.parquet"
EVENTS = ROOT / "data" / "predlab" / "nlst" / "nlst2_events.parquet"


def build_events() -> pd.DataFrame:
    if EVENTS.exists():
        return pd.read_parquet(EVENTS)
    ts_of = load_anchors()
    ethusd = eth_usd_series()
    rows = []
    pools = sorted((RAW / "pools").glob("*.json"))
    for i, p in enumerate(pools):
        r = pool_event(json.loads(p.read_text()), ts_of, ethusd)
        if r is not None and not r.get("dead_before_entry"):
            rows.append(r)
        if i % 100 == 0:
            print(f"events: {i}/{len(pools)}", flush=True)
    tab = pd.DataFrame(rows).set_index("pair").sort_values("list_date")
    tab.to_parquet(EVENTS)
    return tab


def auc(score: np.ndarray, label: np.ndarray) -> float:
    """AUC for label=1 (no rug) via Mann-Whitney rank statistic."""
    s = pd.Series(score).rank().to_numpy()
    n1, n0 = int(label.sum()), int((1 - label).sum())
    if n1 == 0 or n0 == 0:
        return np.nan
    return float((s[label == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def quarter_bootstrap_auc(df: pd.DataFrame, n_draws: int = 1000,
                          seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    quarters = df["quarter"].unique()
    out = []
    for _ in range(n_draws):
        pick = rng.choice(quarters, size=len(quarters), replace=True)
        sub = pd.concat([df[df["quarter"] == q] for q in pick])
        out.append(auc(sub["legit_score"].to_numpy(),
                       sub["no_rug"].to_numpy()))
    return np.asarray(out)


def main() -> None:
    gates = json.loads(GATES.read_text())
    if gates["predlab_nlst2"].get("verdicts"):
        raise SystemExit("REFUSED: predlab_nlst2 verdicts already recorded (one-shot)")
    ev = build_events()
    ft = pd.read_parquet(FEATS)
    df = ev.join(ft[["legit_score"]], how="inner").dropna(subset=["legit_score"])
    df["no_rug"] = (~df["rug14"]).astype(int)
    print(f"events with score: {len(df)} (of {len(ev)} entered)")

    # T1 — discrimination
    a = auc(df["legit_score"].to_numpy(), df["no_rug"].to_numpy())
    boot = quarter_bootstrap_auc(df)
    a_p5 = float(np.nanpercentile(boot, 5))
    t1_pass = bool(a >= 0.65 and a_p5 >= 0.55)

    # T2 — economic transfer
    cut = df["legit_score"].median()
    top = df[df["legit_score"] > cut].sort_values("list_date")
    mean, t, p_two = nw_tstat(top["ret7"].to_numpy(), lag=5)
    p_one = p_two / 2 if t > 0 else 1 - p_two / 2
    top_ex = top["ret7"].drop(top["ret7"].abs().idxmax())
    t2_pass = bool(mean > 0 and p_one < 0.05 and top_ex.mean() > 0)

    bot = df[df["legit_score"] <= cut]
    res = {
        "n_scored": int(len(df)),
        "T1": {"auc": a, "boot_p5": a_p5, "pass": t1_pass},
        "T2": {"n_top": int(len(top)), "mean_ret7": mean, "nw_t": t,
               "p_one_sided": p_one, "mean_ex_top": float(top_ex.mean()),
               "median_ret7": float(top["ret7"].median()), "pass": t2_pass},
        "descriptive": {
            "rug14_top_half": float((~top["rug14"].astype(bool)).mean()),
            "rug14_bottom_half": float((~bot["rug14"].astype(bool)).mean()),
            "bottom_mean_ret7": float(bot["ret7"].mean()),
        },
    }
    verdict = "PASS" if (t1_pass and t2_pass) else "FAIL"
    detail = (f"T1 AUC={a:.3f} (boot p5 {a_p5:.3f}) {'PASS' if t1_pass else 'FAIL'}; "
              f"T2 top-half mean ret7={mean:+.3f} p1={p_one:.4f} "
              f"ex-top={top_ex.mean():+.3f} {'PASS' if t2_pass else 'FAIL'}")
    gates["predlab_nlst2"]["verdicts"] = {
        "nlst2_dexlegit": f"{verdict} at P0 — {detail}" +
        ("" if verdict == "PASS" else "; cycle CLOSED")}
    GATES.write_text(json.dumps(gates, indent=1))
    ledger_append("predlab_nlst2_dexlegit", cell="p0", model="composite_z",
                  config={"features": 8, "min_feats": 5, "split": "median",
                          "target": "rug14_avoided"},
                  metrics={"auc": a, "auc_boot_p5": a_p5,
                           "top_mean_ret7": mean, "top_p_one": p_one,
                           "verdict": verdict})
    write_result("nlst2_p0", res)
    print(json.dumps(res, indent=1, default=str))
    print(f"\nVERDICT: {verdict} — {detail}")


if __name__ == "__main__":
    main()
