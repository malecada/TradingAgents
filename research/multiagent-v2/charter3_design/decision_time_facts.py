"""Facts of the Charter 3 regressors at decision time (charter §3.1). No bar after a decision is read: the panel
is the one written by ``scripts/reader_charter3_null_gate.py panel`` and must not carry a forward target.

    PYTHONPATH=.:scripts python research/multiagent-v2/charter3_design/decision_time_facts.py PANEL
"""
import json
import sys

import numpy as np
import pandas as pd

from tradingagents.reader import charter3 as c3

panel = pd.read_parquet(sys.argv[1]).sort_values(["date", "symbol"]).reset_index(drop=True)
assert not any(c in panel.columns for c in c3.TARGET_COLUMNS), "the panel must not carry a forward target"
panel["abs_funding_3d"] = panel["funding_3d"].abs()
dates = c3._dates(panel)
weeks = np.unique(dates)
test = np.isin(dates, weeks[c3.BURN_IN_WEEKS:])
text = [*c3.BLOCK_A, *c3.BLOCK_V]


def coverage(rows):
    part = panel[rows]
    n_weeks = part["date"].nunique()
    return {f: {"nonzero_share": round(float((part[f].fillna(0) != 0).mean()), 4), "missing_share": round(float(part[f].isna().mean()), 4),
                "nonzero_assets_per_week": round(float((part[f].fillna(0) != 0).sum() / n_weeks), 2)} for f in text}


ranks = c3.feature_ranks(panel, c3.BLOCK_V)


def share(part, rows):
    return {f: round(float((part[rows, j] ** 2).sum() / ((ranks[rows, j] - ranks[rows, j].mean()) ** 2).sum()), 3)
            for j, f in enumerate(c3.BLOCK_V)}


everything = np.ones(len(panel), dtype=bool)
left = {}
for label, controls, flexible in (("within_week_hist", c3.HIST, False), ("within_week_hist_attn", c3.HIST + c3.BLOCK_A, False),
                                  ("both_steps_hist_attn", c3.HIST + c3.BLOCK_A, True)):
    X = c3.feature_residuals(panel, c3.BLOCK_V, controls, flexible=flexible)
    left[label] = {"all_weeks": share(X, everything), "test_weeks": share(X, test)}

against = ["attn_7d", "dvol_30d", "rv_7d", "rv_30d"]
other = dict(zip(against, c3.feature_ranks(panel, against).T))
corr = {f: {a: round(float(np.corrcoef(ranks[:, j], other[a])[0, 1]), 3) for a in against} for j, f in enumerate(c3.BLOCK_V)}

print(json.dumps({"rows": int(len(panel)), "weeks": int(len(weeks)), "assets": int(panel["symbol"].nunique()),
                  "test_weeks": int(len(weeks) - c3.BURN_IN_WEEKS), "missing_hist_values": int(panel[c3.HIST].isna().sum().sum()),
                  "coverage_all_weeks": coverage(everything), "coverage_test_weeks": coverage(test),
                  "rank_variance_left": left, "rank_correlation_pooled": corr}, indent=1))
