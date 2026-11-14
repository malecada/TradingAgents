"""Power of candidate gate scores on synthetic targets (rule in README.md, written before these draws).

Fitted candidates: the walk-forward ridge on a subset of the residual reader features. Fixed-direction score:
the residual of ``tone_1d`` itself, on the test days and on all days. Synthetic targets on the real
decision-time regressors only; no real return enters. ``<features.npy>`` holds the residuals of the six block-R
ranks, as ``charter4.feature_residuals(panel, BLOCK_R, CONTROLS, True)`` gives them.

    PYTHONPATH=.:scripts python research/multiagent-v2/charter4_design/gate_score_power.py draws <panel> <features.npy> <job> <out.jsonl>
    PYTHONPATH=.:scripts python research/multiagent-v2/charter4_design/gate_score_power.py summary <draws.jsonl>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import reader_charter4_null_gate as ng
from tradingagents.reader import charter3 as c3, charter4 as c4

CANDIDATES = {"BLOCK_R": list(c4.BLOCK_R), "FRESH": list(c4.FRESH), "TONE": ["tone_1d", "tone_prev6"]}
JOBS = {"noise": ("factor", 0.0, "fresh", 400), "fresh05": ("factor", 0.05, "fresh", 200), "fresh10": ("factor", 0.10, "fresh", 200),
        "week03": ("factor", 0.03, "week", 200), "week06": ("factor", 0.06, "week", 200)}
FIRST_SEED = 5000
TEST_BEGINS = pd.Timestamp("2023-01-07", tz="UTC")


def fixed_rows(days: np.ndarray, series: np.ndarray, years_needed) -> list[dict]:
    """Gate rule on a daily series with the years in ``years_needed`` positive."""
    years = c3._years(pd.DatetimeIndex([c4._stamp(d) for d in days]))
    t, out = c4.nw_t(series), []
    for j in range(series.shape[1]):
        col = series[:, j]
        have = np.isfinite(col)
        by_year = [col[have & (years == y)].mean() for y in years_needed]
        ok = bool(np.isfinite(t[j]) and t[j] >= c4.GATE_T and col[have].mean() > 0 and all(v > 0 for v in by_year))
        out.append({"t": float(t[j]), "mean": float(col[have].mean()), "verdict": "PASS" if ok else "FAIL"})
    return out


def draws(panel: str, features: str, job: str, out: str) -> None:
    cell, kappa, plant, n = JOBS[job]
    fixed = ng.Fixed(pd.read_parquet(panel), gate=False)
    X = np.load(features)
    if X.shape != (len(fixed.frame), len(c4.BLOCK_R)):
        raise SystemExit("the feature file does not hold the six block-R residuals of the panel")
    index = {name: [c4.BLOCK_R.index(f) for f in feats] for name, feats in CANDIDATES.items()}
    stamps = pd.DatetimeIndex([c4._stamp(d) for d in fixed.days])
    test = (stamps >= TEST_BEGINS)[:, None]
    tone = X[:, c4.BLOCK_R.index("tone_1d")]
    with open(out, "a") as sink:
        for start in range(0, n, ng.BATCH):
            seeds = list(range(FIRST_SEED + start, FIRST_SEED + start + ng.BATCH))
            Y = fixed.targets(seeds, cell, kappa, plant)
            E = c4.residuals(c4.past_surface(Y, fixed.controls, fixed.dates), fixed.controls, fixed.dates)
            rows = {}
            for name, cols in index.items():
                score, _ = c4.walk_forward(X[:, cols], E, fixed.dates)
                days, corr, _ = c4.daily_stats(fixed.dates, score, E)
                rows[name] = ng.form_rows(days, corr)
            days, corr, _ = c4.daily_stats(fixed.dates, np.repeat(tone[:, None], E.shape[1], axis=1), E)
            rows["DIRECT_test"] = fixed_rows(days, np.where(test, corr, np.nan), c4.GATE_YEARS)
            rows["DIRECT_all"] = fixed_rows(days, corr, (2022, *c4.GATE_YEARS))
            for j, seed in enumerate(seeds):
                sink.write(json.dumps({"job": job, "cell": cell, "plant": plant if kappa else None, "kappa": kappa, "seed": seed,
                                       **{f"{k}_{name}": r[j][k] for name, r in rows.items() for k in ("t", "mean", "verdict")}}) + "\n")
            sink.flush()


def summary(path: str) -> dict:
    frame = pd.read_json(path, lines=True)
    names = [*CANDIDATES, "DIRECT_test", "DIRECT_all"]
    out = {"candidates": CANDIDATES, "jobs": {}}
    for job, part in frame.groupby("job"):
        cell = {"draws": int(len(part))}
        for name in names:
            passes = int((part[f"verdict_{name}"] == "PASS").sum())
            p = passes / len(part)
            half = 1.96 * (p * (1 - p) / len(part)) ** 0.5
            cell[name] = {"passes": passes, "pass_rate": p, "pass_rate_95": [p - half, p + half], "t_mean": float(part[f"t_{name}"].mean()),
                          "t_sd": float(part[f"t_{name}"].std())}
        out["jobs"][job] = cell
    planted = [j for j in out["jobs"] if j != "noise"]
    out["planted_passes"] = {name: int(sum(out["jobs"][j][name]["passes"] for j in planted)) for name in names}
    return out


if __name__ == "__main__":
    if sys.argv[1] == "draws":
        draws(*sys.argv[2:6])
    else:
        print(json.dumps(summary(sys.argv[2]), indent=1))
