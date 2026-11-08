from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.agents_v2 import schemas  # noqa: E402
from tradingagents.agents_v2.graph import config_sha, rule_weights, run_asset, run_portfolio, validate_portfolio  # noqa: E402


class StubClient:
    """Returns schema-shaped answers; records prompts so order swapping can be asserted."""
    def __init__(self, p_bull_first=0.7, p_bear_first=0.6):
        self.prompts, self.p = [], {"bull_first": p_bull_first, "bear_first": p_bear_first}

    def call(self, prompt, schema, name="answer", system=None):
        self.prompts.append((name, prompt))
        meta = {"cost": 0.001, "latency_s": 0.1, "model": "m", "provider": "p"}
        if schema is schemas.ANALYST:
            return {"p_outperform_7d": 0.55, "confidence": 0.4, "key_facts": ["f"], "bullish_evidence": ["b [n1]"],
                    "bearish_evidence": [], "risks": ["r"], "cited_items": ["n1"], "data_quality": "adequate"}, meta
        if schema is schemas.FORECAST_INTERPRETER:
            return {"weight_on_quant_forecast": 0.2, "rationale": "weak record", "p_outperform_7d": 0.52}, meta
        if schema is schemas.DEBATE_TURN:
            return {"argument": "a", "strongest_points": ["s"], "concessions": [], "cited_items": ["n1"]}, meta
        if schema is schemas.JUDGE:
            order = "bull_first" if name.endswith("bull_first") else ("bear_first" if name.endswith("bear_first") else "none")
            return {"p_outperform_7d": self.p.get(order, 0.5), "confidence": 0.5, "abstain": False,
                    "decisive_evidence": ["d"], "invalidation_conditions": ["i"], "cited_items": ["n1"]}, meta
        if schema is schemas.PORTFOLIO:
            return {"positions": [{"alias": "Asset_A", "weight": 0.3, "reason": "x"}], "gross_exposure": 0.3, "notes": ""}, meta
        raise AssertionError("unknown schema")


def test_run_asset_order_swap_and_averaging():
    c = StubClient(0.7, 0.6)
    run = run_asset("# Dossier for Asset_A\n...", "Asset_A", c)
    assert run.p_outperform == 0.65 and run.abstain is False
    names = [n for n, _ in c.prompts]
    assert names[:4] == ["analyst_market", "analyst_fundamental", "analyst_news", "forecast"]
    assert "bull_open" in names and "bear_open" in names and names.count("bear_rebut") == 2 and names.count("bull_rebut") == 2
    assert len(run.meta) == 4 + 2 * 4 and run.config_sha == config_sha()
    for _, prompt in c.prompts:
        assert "Asset_A" in prompt and "Bitcoin" not in prompt


def test_run_asset_without_debate_single_judge():
    c = StubClient()
    run = run_asset("d", "Asset_A", c, debate=False, with_forecast=False)
    assert "none" in run.debates and run.forecast == {} and len(run.meta) == 3 + 1


def test_portfolio_validation_falls_back_to_rule():
    cands = [{"alias": "Asset_A", "p_outperform_7d": 0.7, "confidence": 0.8, "abstain": False, "vol_ann": 0.5},
             {"alias": "Asset_B", "p_outperform_7d": 0.3, "confidence": 0.5, "abstain": False, "vol_ann": 1.0},
             {"alias": "Asset_C", "p_outperform_7d": 0.9, "confidence": 0.9, "abstain": True, "vol_ann": 0.5}]
    out = run_portfolio(cands, StubClient())
    assert "weight beyond cap" in out["problems"] and out["weights"] == rule_weights(cands)
    w = rule_weights(cands)
    assert w["Asset_C"] == 0.0 and w["Asset_A"] > 0 > w["Asset_B"] and max(abs(v) for v in w.values()) <= 0.10
    ok = {"positions": [{"alias": "Asset_A", "weight": 0.1, "reason": ""}, {"alias": "Asset_B", "weight": -0.1, "reason": ""}],
          "gross_exposure": 0.2, "notes": ""}
    assert validate_portfolio(ok, cands) == []
