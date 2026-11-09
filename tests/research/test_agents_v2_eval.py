from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.agents_v2.evaluate import evaluate_panel, newey_west_t, weekly_ic  # noqa: E402
from tradingagents.agents_v2.runner import select_debate_candidates  # noqa: E402


def _panel(signal_strength, seed=0, weeks=60, n=50):
    rng = np.random.default_rng(seed)
    rows = []
    for w in range(weeks):
        d = pd.Timestamp("2022-01-07", tz="UTC") + pd.Timedelta(weeks=w)
        vol = rng.uniform(0.3, 1.5, n); mom = rng.normal(0, 0.2, n); size = rng.integers(1, 200, n)
        latent = rng.normal(0, 1, n)
        fwd = 0.02 * latent * signal_strength + 0.05 * rng.normal(0, 1, n) + 0.01 * mom
        p = 0.5 + 0.1 * latent + 0.02 * rng.normal(0, 1, n)
        rows.append(pd.DataFrame({"date": d, "symbol": [f"S{i}" for i in range(n)], "vol_ewma20": vol, "ret_4w": mom,
                                  "size_rank": size, "dvol_30d": size, "fwd_ret": fwd, "p_outperform": np.clip(p, 0, 1)}))
    return pd.concat(rows, ignore_index=True)


def test_evaluation_detects_signal_and_not_noise():
    strong = evaluate_panel(_panel(1.0))
    assert strong["weeks"] == 60 and strong["ic_mean"] > 0.1 and strong["ic_nw_t"] > 3
    assert strong["brier"]["skill"] > 0 and strong["calibration"]["slope"] > 0
    null = evaluate_panel(_panel(0.0, seed=1))
    assert abs(null["ic_mean"]) < 0.08 and abs(null["ic_nw_t"]) < 2.5


def test_newey_west_and_residualization_remove_momentum():
    x = pd.Series([0.1, -0.05, 0.08, 0.02, 0.0, 0.05])
    assert newey_west_t(x) > 0
    panel = _panel(0.0, seed=2)
    rng = np.random.default_rng(3)
    panel["p_outperform"] = np.clip(0.5 + panel["ret_4w"] + 0.02 * rng.normal(size=len(panel)), 0, 1)  # momentum + noise
    panel["fwd_ret"] = 0.03 * panel["ret_4w"] + 0.01 * rng.normal(size=len(panel))                        # momentum + noise
    raw = pd.Series({d: g["p_outperform"].corr(g["fwd_ret"], method="spearman") for d, g in panel.groupby("date")})
    ic = weekly_ic(panel)
    assert raw.mean() > 0.3 and abs(ic.mean()) < 0.1       # residualization strips the shared control


def test_select_debate_candidates_prefers_conviction_and_disagreement():
    runs = {"A": {"m": {"p_outperform_7d": 0.5}, "n": {"p_outperform_7d": 0.5}},
            "B": {"m": {"p_outperform_7d": 0.8}, "n": {"p_outperform_7d": 0.8}},
            "C": {"m": {"p_outperform_7d": 0.2}, "n": {"p_outperform_7d": 0.8}},
            "D": {"m": {"p_outperform_7d": 0.55}, "n": {"p_outperform_7d": 0.45}}}
    assert select_debate_candidates(runs, 2) == ["B", "C"] or select_debate_candidates(runs, 2) == ["C", "B"]
    assert "A" not in select_debate_candidates(runs, 3)
