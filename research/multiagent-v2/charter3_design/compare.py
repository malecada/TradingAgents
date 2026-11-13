"""Charter 3, stage V0: the variants of check 1 and check 2 side by side, on the seeds every variant of a cell has.

    python research/multiagent-v2/charter3_design/compare.py research/multiagent-v2/charter3_design/check1.jsonl \\
        research/multiagent-v2/charter3_design/check2.jsonl

``paired_diff_se`` is the standard error of the difference of the mean weekly partial correlation to the first
design (``base``) over the common seeds."""
import json
import sys

import numpy as np
import pandas as pd

a = pd.DataFrame([json.loads(line) for line in open(sys.argv[1]) if line.strip()])
b = pd.DataFrame([json.loads(line) for line in open(sys.argv[2]) if line.strip()])
b = b[b.variant != "base"]                                                  # the first design is in both files, row for row
f = pd.concat([a, b], ignore_index=True)
for (shape, rho, signal), g in f.groupby(["shape", "rho", "signal"], sort=False):
    common = set.intersection(*[set(v["seed"]) for _, v in g.groupby("variant")])
    if not common:
        continue
    h = g[g.seed.isin(common)]
    t = h.groupby("variant", sort=False).agg(pass_rate=("verdict", lambda v: (v == "PASS").mean()), mean_ic=("mean", "mean"),
                                             t_mean=("t", "mean"), t_sd=("t", "std"), q975=("t", lambda t: np.quantile(t, 0.975)))
    base = h[h.variant == "base"].set_index("seed")["mean"]
    t["paired_diff_se"] = [float((v.set_index("seed")["mean"] - base).std() / np.sqrt(len(common))) for _, v in h.groupby("variant", sort=False)]
    print(shape, rho, signal, "common seeds", len(common))
    print(t.round(4).to_string())
    print()
