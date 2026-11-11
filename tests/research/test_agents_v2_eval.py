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


def test_subperiod_sign_gate_binds_only_with_two_years():
    from tradingagents.agents_v2.evaluate import subperiod_sign_gate

    def ic(values_by_year):
        parts = [pd.Series(v, index=pd.date_range(f"{y}-02-02", periods=len(v), freq="W-FRI", tz="UTC")) for y, v in values_by_year.items()]
        return pd.concat(parts)

    three = subperiod_sign_gate(ic({2022: [0.1, 0.2], 2023: [-0.1, -0.3], 2024: [0.05, 0.01]}))
    assert three["pass"] and not three["binding"] and three["years_present"] == 3 and three["n_positive"] == 2
    assert subperiod_sign_gate(ic({2022: [0.1], 2023: [-0.1], 2024: [-0.2]}))["pass"]        # cannot fail with three years
    split = subperiod_sign_gate(ic({2023: [-0.1, -0.3], 2024: [0.05, 0.01]}))
    assert not split["pass"] and split["binding"] and split["required_same_sign"] == 2
    assert split["weeks_by_year"] == {"2023": 2, "2024": 2} and split["mean_ic_by_year"]["2023"] == -0.2
    agree = subperiod_sign_gate(ic({2023: [-0.1, -0.3], 2024: [-0.05, 0.01]}))
    assert agree["pass"] and agree["binding"] and agree["n_negative"] == 2                   # the registered rule is sign agreement
    one = subperiod_sign_gate(ic({2024: [0.05, np.nan, 0.01]}))
    assert one["pass"] and not one["binding"] and one["weeks_by_year"] == {"2024": 2}
    empty = subperiod_sign_gate(pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC")))
    assert not empty["pass"] and empty["years_present"] == 0


def _flagged_panel(signal_identified, signal_other, seed=0, weeks=60, n=50):
    rng = np.random.default_rng(seed)
    rows = []
    for w in range(weeks):
        d = pd.Timestamp("2023-01-06", tz="UTC") + pd.Timedelta(weeks=w)
        latent, flag = rng.normal(0, 1, n), np.arange(n) % 5 < 2                             # 20 identified, 20 not, 10 unflagged
        strength = np.where(flag, signal_identified, signal_other)
        rows.append(pd.DataFrame({
            "date": d, "symbol": [f"S{i}" for i in range(n)], "vol_ewma20": rng.uniform(0.3, 1.5, n), "ret_4w": rng.normal(0, 0.2, n),
            "dvol_30d": rng.uniform(1, 100, n), "fwd_ret": 0.03 * latent * strength + 0.05 * rng.normal(0, 1, n),
            "p_judge": np.clip(0.5 + 0.1 * latent + 0.02 * rng.normal(0, 1, n), 0, 1), "p_quant": rng.uniform(0, 1, n),
            "identified": pd.array([bool(f) if i % 5 < 4 else None for i, f in enumerate(flag)], dtype="object")}))
    return pd.concat(rows, ignore_index=True)


def test_subset_gaps_detects_signal_confined_to_identified_rows():
    from tradingagents.agents_v2.evaluate import subset_gaps
    out = subset_gaps(_flagged_panel(1.5, 0.0), cols=("p_judge", "p_quant"), n_boot=300, seed=1)
    judge, quant, did = out["columns"]["p_judge"], out["columns"]["p_quant"], out["difference_in_differences"]
    assert out["weeks"] == 60 and judge["n_identified"] == 1200 and judge["n_not_identified"] == 1200   # unflagged rows in neither
    assert judge["ic_identified"] > 0.3 and abs(judge["ic_not_identified"]) < 0.1
    assert judge["gap"] > 0.25 and judge["gap_bootstrap"]["ci95"][0] > 0 and judge["gap_bootstrap"]["p_two_sided"] < 0.05
    assert judge["brier_skill_identified"] > judge["brier_skill_not_identified"]
    assert abs(quant["gap"]) < 0.12 and quant["gap_bootstrap"]["ci95"][0] < 0 < quant["gap_bootstrap"]["ci95"][1]
    assert did["columns"] == ["p_judge", "p_quant"] and did["gap_difference"] > 0.2 and did["ci95"][0] > 0
    assert did["gap_difference"] == judge["gap"] - quant["gap"]


def test_subset_gaps_null_covers_zero_and_small_subsets_return_no_estimate():
    from tradingagents.agents_v2.evaluate import subset_gaps
    null = subset_gaps(_flagged_panel(1.0, 1.0, seed=2), cols=("p_judge", "p_quant"), n_boot=300, seed=1)
    judge = null["columns"]["p_judge"]
    assert judge["ic_identified"] > 0.2 and judge["ic_not_identified"] > 0.2                 # equal skill in both subsets
    assert judge["gap_bootstrap"]["ci95"][0] < 0 < judge["gap_bootstrap"]["ci95"][1]
    assert null["difference_in_differences"]["ci95"][0] < 0 < null["difference_in_differences"]["ci95"][1]
    tiny = subset_gaps(_flagged_panel(1.0, 1.0, weeks=1, n=20), cols=("p_judge", "p_quant"), n_boot=120, seed=1)
    assert np.isnan(tiny["columns"]["p_judge"]["gap"]) and tiny["columns"]["p_judge"]["gap_bootstrap"]["ci95"] is None
