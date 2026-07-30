from __future__ import annotations

import numpy as np

from tradingagents.predlab import rollup


def test_bh_fdr_known_example():
    # classic BH at q=0.10: sorted p (0.001, 0.008, 0.039, 0.041, 0.60);
    # thresholds i/m*q = (0.02, 0.04, 0.06, 0.08, 0.10); largest i with
    # p_i <= thr_i is i=4 (0.041 <= 0.08) -> first four pass
    ps = {"a": 0.039, "b": 0.001, "c": 0.60, "d": 0.008, "e": 0.041}
    passed = rollup.bh_fdr(ps, q=0.10)
    assert passed == {"a": True, "b": True, "c": False, "d": True, "e": True}


def test_bh_fdr_ignores_nan():
    ps = {"a": 0.01, "b": float("nan")}
    passed = rollup.bh_fdr(ps, q=0.10)
    assert passed["a"] is True and passed["b"] is False


def _card(models):
    return {"strong_baseline": "base", "loss": "se",
            "per_model": {name: {"loss_mean": lm, "dm_p": p, "degenerate": name == "base",
                                 "sub_periods": sub}
                          for name, (lm, p, sub) in models.items()}}


def test_champion_and_verdict():
    card = _card({
        "base": (1.0, float("nan"), {}),
        "good": (0.8, 0.001, {"a": 0.1, "b": 0.2, "c": 0.05}),
        "bad": (1.2, 0.99, {}),
    })
    ch = rollup.champion(card)
    assert ch["model"] == "good"
    assert np.isclose(ch["improvement_pct"], 20.0)
    assert ch["subperiod_stable"] is True  # 3/3 positive mean loss-diffs


def test_champion_baseline_wins():
    card = _card({"base": (1.0, float("nan"), {}), "worse": (1.1, 0.9, {})})
    ch = rollup.champion(card)
    assert ch["model"] == "base" and ch["baseline_wins"] is True


def test_verdict_logic():
    assert rollup.verdict(fdr_pass=True, floor_pass=True, stable=True,
                          baseline_wins=False, override=None) == "SKILL-CANDIDATE"
    assert rollup.verdict(True, True, True, baseline_wins=True, override=None) == "BASELINE-WINS"
    assert rollup.verdict(False, True, True, False, None) == "NO-SKILL"
    assert rollup.verdict(True, False, True, False, None) == "NO-SKILL"
    assert rollup.verdict(True, True, True, False,
                          override="PREDICTABLE-VS-WEAK-ONLY") == "PREDICTABLE-VS-WEAK-ONLY"
