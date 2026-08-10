"""llm_c2_veto_ovl P3 — overlay dev gates on D.

Primary series: ANONYMIZED P2 variant severities (pre-result amendment in
gates.json); named variant reported disclosure-only. Multiplier map
2->0.0, 1->0.5, 0->1.0; budget <=10 veto-days/calendar-year in calendar
order; O4 transition costs charged.

Gates (charter §5 P3):
  G1 rel MaxDD reduction >= 0.10
  G2 rel CVaR5 improvement >= 0.05
  G3 dSR >= -0.10 AND stationary block bootstrap (20d, 2000) P(dSR<=-0.30)<0.05
  G4 random-veto placebo: 400 budget-matched draws, real relDD > p95
  G5 post-budget veto days intersect >= 2 frozen episode windows
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from llm_veto_engine import (  # noqa: E402
    DEV_D, VETO_BUDGET_PER_YEAR, apply_budget, book_metrics, load_book,
    o4_scale, overlay_net, seg,
)
from tradingagents.predlab.pp import ann_sr  # noqa: E402

OUTDIR = Path("data/predlab/llm_veto")
OUT = OUTDIR / "p3_overlay.json"
LEDGER = Path("data/predlab/trial_ledger.jsonl")

EPISODES = {
    "2021-05_crash": ("2021-05-10", "2021-05-25"),
    "2022-05_terra": ("2022-05-07", "2022-05-16"),
    "2022-0607_3ac_celsius": ("2022-06-12", "2022-07-05"),
    "2022-11_ftx": ("2022-11-06", "2022-11-15"),
    "2023-03_usdc_svb": ("2023-03-09", "2023-03-15"),
    "2024-08_carry": ("2024-08-02", "2024-08-09"),
    "2025-0203_drawdown": ("2025-02-21", "2025-03-15"),
}


def m_series(index: pd.DatetimeIndex, m_raw_map: dict) -> pd.Series:
    m = pd.Series(1.0, index=index)
    for d, v in m_raw_map.items():
        t = pd.Timestamp(d, tz="UTC")
        if t in m.index:
            m.loc[t] = float(v)
    return apply_budget(m, budget=VETO_BUDGET_PER_YEAR)


def rel_dd_reduction(ovl_d: pd.Series, vet_d: pd.Series) -> float:
    from tradingagents.predlab.pp import max_drawdown
    d0 = max_drawdown(ovl_d.to_numpy())
    d1 = max_drawdown(vet_d.to_numpy())
    return (d0 - d1) / d0


def stationary_bootstrap_dsr(book: pd.Series, veto: pd.Series,
                             n: int = 2000, mean_block: int = 20,
                             seed: int = 7) -> np.ndarray:
    """Paired stationary bootstrap of dSR = SR(veto) - SR(book)."""
    rng = np.random.default_rng(seed)
    b = book.to_numpy()
    v = veto.to_numpy()
    T = len(b)
    p = 1.0 / mean_block
    out = np.empty(n)
    for i in range(n):
        idx = np.empty(T, dtype=int)
        t = rng.integers(T)
        for j in range(T):
            idx[j] = t
            t = rng.integers(T) if rng.random() < p else (t + 1) % T
        out[i] = ann_sr(v[idx]) - ann_sr(b[idx])
    return out


def main() -> int:
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        return 1
    p2 = json.loads((OUTDIR / "p2_classifier.json").read_text())
    if p2["verdict"] != "PASS":
        print("P2 verdict is not PASS — P3 must not run (stop rule)")
        return 1

    book = load_book()
    base, breadth = book["base"], book["breadth"]
    s = o4_scale(base, breadth)
    ovl = overlay_net(base, s)
    ovl_d = seg(ovl, *DEV_D)

    res = {"experiment": "llm_c2_veto_ovl", "probe": "P3_overlay",
           "primary_variant": "anon", "window_D": list(DEV_D), "variants": {}}
    rng = np.random.default_rng(11)

    for variant in ("anon", "named"):
        m = m_series(ovl.index, p2["variants"][variant]["m_raw"])
        vet = overlay_net(base, s * m)
        vet_d = seg(vet, *DEV_D)
        b0, b1 = book_metrics(ovl, *DEV_D), book_metrics(vet, *DEV_D)
        rel_dd = (b0["maxdd"] - b1["maxdd"]) / b0["maxdd"]
        rel_cvar = (b1["cvar5"] - b0["cvar5"]) / abs(b0["cvar5"])
        d_sr = b1["sr"] - b0["sr"]

        veto_days = m[(m < 1.0) & (m.index >= DEV_D[0]) & (m.index <= DEV_D[1])]
        eps_hit = sorted({name for name, (lo, hi) in EPISODES.items()
                          if ((veto_days.index >= pd.Timestamp(lo, tz="UTC")) &
                              (veto_days.index <= pd.Timestamp(hi, tz="UTC"))).any()})

        entry = {"book": b0, "veto": b1, "rel_maxdd_reduction": rel_dd,
                 "rel_cvar5_improvement": rel_cvar, "d_sr": d_sr,
                 "n_veto_days": int(len(veto_days)),
                 "veto_days": {str(d.date()): float(v)
                               for d, v in veto_days.items()},
                 "episodes_hit": eps_hit}

        if variant == "anon":
            boot = stationary_bootstrap_dsr(ovl_d, vet_d)
            p_bad = float((boot <= -0.30).mean())
            counts = veto_days.groupby(veto_days.index.year).size()
            mults = veto_days.to_numpy()
            placebo = np.empty(400)
            for i in range(400):
                m_p = pd.Series(1.0, index=ovl.index)
                k = 0
                for year, cnt in counts.items():
                    yr_idx = ovl_d.index[ovl_d.index.year == year]
                    pick = rng.choice(len(yr_idx), size=int(cnt), replace=False)
                    for j in pick:
                        m_p.loc[yr_idx[j]] = mults[k % len(mults)]
                        k += 1
                vp = overlay_net(base, s * m_p)
                placebo[i] = rel_dd_reduction(ovl_d, seg(vp, *DEV_D))
            p95 = float(np.quantile(placebo, 0.95))
            gates = {
                "G1_relDD": {"value": rel_dd, "min": 0.10, "pass": rel_dd >= 0.10},
                "G2_relCVaR5": {"value": rel_cvar, "min": 0.05,
                                "pass": rel_cvar >= 0.05},
                "G3_dSR": {"point": d_sr, "p_dsr_le_m030": p_bad,
                           "pass": (d_sr >= -0.10) and (p_bad < 0.05)},
                "G4_placebo": {"real": rel_dd, "placebo_p95": p95,
                               "pass": rel_dd > p95},
                "G5_episodes": {"hit": eps_hit, "min": 2,
                                "pass": len(eps_hit) >= 2},
            }
            entry["gates"] = gates
            entry["placebo_dist"] = {"mean": float(placebo.mean()),
                                     "p95": p95,
                                     "max": float(placebo.max())}
        res["variants"][variant] = entry

    g = res["variants"]["anon"]["gates"]
    verdict = "PASS" if all(v["pass"] for v in g.values()) else "FAIL"
    res["verdict"] = verdict
    OUT.write_text(json.dumps(res, indent=1, default=float))

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    a = res["variants"]["anon"]
    for cell, metrics in (
        ("P3_overlay_anon", {"rel_maxdd_reduction": a["rel_maxdd_reduction"],
                             "rel_cvar5_improvement": a["rel_cvar5_improvement"],
                             "d_sr": a["d_sr"],
                             "n_veto_days": a["n_veto_days"]}),
        ("P3_overlay_placebo", {"placebo_p95": res["variants"]["anon"]
                                ["placebo_dist"]["p95"],
                                "real": a["rel_maxdd_reduction"]}),
    ):
        row = {"ts_utc": datetime.now(timezone.utc).isoformat(),
               "experiment": "llm_c2_veto_ovl", "cell": cell,
               "model": "gpt-5.4-mini",
               "config": {"variant": "anon", "budget": VETO_BUDGET_PER_YEAR,
                          "map": {"2": 0.0, "1": 0.5, "0": 1.0}},
               "config_hash": f"p3-{cell}", "git_commit": commit,
               "window": list(DEV_D), "metrics": metrics}
        with LEDGER.open("a") as f:
            f.write(json.dumps(row, default=float) + "\n")

    print(json.dumps({k: {"pass": v["pass"]} for k, v in g.items()}, indent=1))
    print(f"P3 verdict: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
