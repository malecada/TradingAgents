"""The tables of the Charter 3 charter (Appendix B), built from the stored draws. Synthetic targets only.

    PYTHONPATH=.:scripts python research/multiagent-v2/charter3_design/tables.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import reader_charter3_null_gate as ng

BASE = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
SHAPES = {"linear": "linear", "nonlinear": "curved"}
VARIANTS = {
    "base": "first design: within-week linear step only (`s_reader_lin`)",
    "sq": "squares of the 8 bar-history ranks added to the within-week step (`s_reader_sq`)",
    "gbm_weak": "features: trees cross-fitted over 6 blocks of weeks (parameters of Charter 2)",
    "gbm_strong": "features: trees cross-fitted over 6 blocks of weeks (parameters of §3.2)",
    "gbm_strong_sq": "the same, and the squares in the within-week step",
    "quad_feat": "features: quadratic surface fitted on earlier weeks",
    "gbm_past_feat": "features: trees fitted on earlier weeks",
    "quad_both": "features and target: quadratic surface fitted on earlier weeks",
    "gbm_past_feat_quad_target": "**registered:** features: trees on earlier weeks; target: quadratic surface on earlier weeks",
}
CELLS = {("linear", 0.0, 0.0): "linear, noise", ("nonlinear", 0.0, 0.0): "curved, noise",
         ("nonlinear", 0.3, 0.0): "curved, `rho` 0.3, noise", ("linear", 0.0, 0.075): "linear, planted 0.075"}
THRESHOLDS = (2.0, 2.3, 2.5)


def pct(x, d=2):
    return f"{100 * x:.{d}f} %"


def noise_table(path):
    head = ("| Regressors | `rho` | Shape | `noise` | Draws | PASS | Pass rate (95 % interval) | Mean weekly partial correlation | "
            "t: mean, sd, 97.5 % point | G1 alone | PASS with t at lag 12 | Read as visible / thin | "
            "Target-rank variance left by the controls |\n" + "|---" * 13 + "|\n")
    out = []
    for r in ng.summary(path):
        lo, hi = r["pass_rate_95"]
        cell = (f"| real | {r['rho']:.1f} | {SHAPES[r['shape']]} | {r['noise']:.1f} |" if r["kind"] == "real"
                else f"| synthetic panel | {r['rho']:.1f} | | |")
        share = f"{r['residual_share']:.3f}" if r.get("residual_share") is not None and np.isfinite(r["residual_share"]) else ""
        out.append(f"{cell} {r['draws']:,} | {r['passes']} | {pct(r['pass_rate'])} ({pct(lo)} to {pct(hi)}) | {r['mean_ic']:+.4f} | "
                   f"{r['t_mean']:+.2f}, {r['t_sd']:.2f}, {r['t_q975']:.2f} | {r['first_gate_alone']} | {r['pass_long_lag']} | "
                   f"{r['pass_visible']} / {r['pass_thin']} | {share} |")
    return head + "\n".join(out)


def power_table(path):
    head = ("| Planted strength | `rho` | Shape | Draws | PASS | Pass rate (95 % interval) | Mean weekly partial correlation | Mean t | "
            "Read as visible / thin |\n|---|---|---|---|---|---|---|---|---|\n")
    out = []
    for r in ng.summary(path):
        lo, hi = r["pass_rate_95"]
        out.append(f"| {r['signal']:g} | {r['rho']:.1f} | {SHAPES[r['shape']]} | {r['draws']:,} | {r['passes']} | "
                   f"{pct(r['pass_rate'], 1)} ({pct(lo, 1)} to {pct(hi, 1)}) | {r['mean_ic']:+.4f} | {r['t_mean']:.2f} | "
                   f"{r['pass_visible']} / {r['pass_thin']} |")
    return head + "\n".join(out)


def load(path):
    return pd.DataFrame([json.loads(line) for line in open(path) if line.strip()])


def design_table():
    a, b = load(HERE / "check1.jsonl"), load(HERE / "check2.jsonl")
    f = pd.concat([a, b[b.variant != "base"]], ignore_index=True)       # the first design is in both files, row for row
    cols = {}
    for (shape, rho, signal), label in CELLS.items():
        g = f[(f["shape"] == shape) & (f.rho == rho) & (f.signal == signal)]
        counts = g.groupby("variant")["seed"].nunique()
        assert counts.nunique() == 1, counts
        cols[label] = (g.groupby("variant").agg(rate=("verdict", lambda v: (v == "PASS").mean()), mean=("mean", "mean")), int(counts.iloc[0]))
    head = "| Removal of the controls before the walk-forward fit | " + " | ".join(f"{label} ({n} seeds)" for label, (_, n) in cols.items()) + " |\n"
    head += "|---|" + "---|" * len(cols) + "\n"
    rows = ["| " + text + " | " + " | ".join(f"{pct(t.loc[name, 'rate'])}, {t.loc[name, 'mean']:+.4f}" for t, _ in cols.values()) + " |"
            for name, text in VARIANTS.items()]
    return head + "\n".join(rows)


def threshold_table():
    head = "| Draws | " + " | ".join(f"t at least {t:g}" for t in THRESHOLDS) + " | t at least 2 and mean at least 0.07 |\n|---|" + "---|" * (len(THRESHOLDS) + 1) + "\n"
    rows = []
    for name in ("charter3_null_gate.jsonl", "charter3_null_gate_power.jsonl"):
        f = load(BASE / name)
        for (rho, shape, signal, noise), g in f.groupby(["rho", "shape", "signal", "noise"]):
            ok = (g["mean"] > 0) & (g["y2023"] > 0) & (g["y2024"] > 0)
            label = f"{SHAPES[shape]}, `rho` {rho:.1f}, " + (f"planted {signal:g}" if signal else f"noise, scale {noise:.1f}")
            cells = [pct(float(((g["t"] >= t) & ok).mean())) for t in THRESHOLDS]
            cells.append(pct(float(((g["t"] >= 2.0) & ok & (g["mean"] >= 0.07)).mean())))
            rows.append(f"| {label} | " + " | ".join(cells) + " |")
    return head + "\n".join(rows)


TABLES = {
    "NOISE": lambda: noise_table(BASE / "charter3_null_gate.jsonl"),
    "POWER": lambda: power_table(BASE / "charter3_null_gate_power.jsonl"),
    "FIRST_NOISE": lambda: noise_table(BASE / "charter3_null_gate_first_design.jsonl"),
    "FIRST_POWER": lambda: power_table(BASE / "charter3_null_gate_first_design_power.jsonl"),
    "DESIGNS": design_table,
    "THRESHOLDS": threshold_table,
}

if __name__ == "__main__":
    for name, build in TABLES.items():
        print(f"@@{name}@@\n{build()}\n")
