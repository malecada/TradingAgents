"""Agent graph v2.4: information partition, symmetric order-swapped debate, hybrid mixing, symbol-keyed book."""
from __future__ import annotations

from pathlib import Path
import pytest
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.agents_v2 import schemas  # noqa: E402
from tradingagents.agents_v2.graph import (analyst_view, citation_report, config_sha, hybrid_probability,  # noqa: E402
                                           rule_weights, run_asset, run_portfolio, validate_portfolio, without_quant)

DOSSIER = """# Dossier for Asset_A

## Numeric profile (relative to this week's universe)
[n1] Profile: upper half by market cap; volume rank pct 83, higher than 83% of the universe; listed over a year; category: DeFi.
[n2] Returns: 4w 12.0% (pct 60, higher than 60% of the universe), 12w 30.0% (pct 70, higher than 70% of the universe); distance to 26w high -5.0%.
[n3] Volatility: EWMA20 80.0% ann (pct 40, higher than 40% of the universe); vol-of-vol pct 50, higher than 50% of the universe.
[n4] Funding (annualized): 3d 10.0%, 30d 8.0% (pct 55, higher than 55% of the universe).
[n5] On-chain 30d change: active addresses 5.0%, transactions 3.0% (pct 45, higher than 45% of the universe).
[n6] Supply schedule: unlock data unavailable for this asset.
[n7] Price path, weekly, indexed to 100 at decision: [90.0, 95.0, 100.0]
[n8] Weekly returns % (oldest first): [5.6, 5.3]; 90d drawdown -8.0%; realized vol 20d 75.0% ann.

## Scheduled events (known in advance)
- No US central-bank rate decision in the next two weeks.

## News and discussion, last 30 days
Items retrieved: 3; events 1, analysis 1, price recaps 0 (omitted), promotional/unrelated 1 (omitted); shown: 2.

- [t1] [3 days ago, news, event, new_information] The protocol launched a new product with 2 partners.
- [t2] [5 days ago, community post, analysis_opinion, none] A user argues the token is undervalued.
## Quant forecast
Quant forecast: a cross-sectional ridge model ranks this asset at percentile 80 of the universe for expected 7-day return; over the last 26 weeks its rank correlation averaged +0.090.
"""


class StubClient:
    """Returns schema-shaped answers; records prompts so order swapping can be asserted."""
    def __init__(self, p_bull_first=0.7, p_bear_first=0.6, p_nd=0.5, weight=0.2):
        self.prompts, self.p = [], {"bull_first": p_bull_first, "bear_first": p_bear_first, "none": p_nd}
        self.weight = weight

    def call(self, prompt, schema, name="answer", system=None, reasoning_effort=None, reasoning=None, max_tokens=None):
        self.prompts.append((name, prompt))
        self.efforts = getattr(self, "efforts", []) + [("none" if (reasoning or {}).get("enabled") is False else (reasoning or {}).get("effort"))]
        meta = {"cost": 0.001, "latency_s": 0.1, "model": "m", "provider": "p"}
        if schema is schemas.ANALYST:
            return {"p_outperform_7d": 0.55, "confidence": 0.4, "key_facts": ["4w return 12.0% [n2]"], "bullish_evidence": ["b [n1]"],
                    "bearish_evidence": [], "risks": ["r"], "cited_items": ["n1", "t9"], "data_quality": "adequate"}, meta
        if schema is schemas.FORECAST_INTERPRETER:
            return {"weight_on_quant_forecast": self.weight, "rationale": "weak record", "p_outperform_7d": 0.52}, meta
        if schema is schemas.DEBATE_TURN:
            return {"argument": "a", "strongest_points": ["s"], "concessions": [], "cited_items": ["n1"]}, meta
        if schema is schemas.JUDGE:
            order = "bull_first" if name.endswith("bull_first") else ("bear_first" if name.endswith("bear_first") else "none")
            return {"p_outperform_7d": self.p.get(order, 0.5), "confidence": 0.5, "abstain": False,
                    "decisive_evidence": ["d"], "invalidation_conditions": ["i"], "cited_items": ["n1"]}, meta
        if schema is schemas.PORTFOLIO:
            return {"positions": [{"alias": "C01", "weight": 0.3, "reason": "x"}], "gross_exposure": 0.3, "notes": ""}, meta
        raise AssertionError("unknown schema")


def test_analyst_views_are_partitioned_and_quant_free():
    m, f, n = (analyst_view(r, DOSSIER) for r in ("market", "fundamental", "news"))
    assert "[n2]" in m and "[n7]" in m and "[n1]" not in m and "[t1]" not in m and "central-bank" in m
    assert "[n1]" in f and "[n5]" in f and "[n2]" not in f and "[t1]" in f and "[t2]" not in f     # event-typed items only
    assert "[t1]" in n and "[t2]" in n and "[n1]" not in n and "central-bank" in n
    for v in (m, f, n):
        assert "Quant forecast" not in v and "ridge" not in v
    assert "ridge" not in without_quant(DOSSIER) and "[t2]" in without_quant(DOSSIER)


def test_run_asset_order_swap_symmetric_debate_and_hybrid():
    c = StubClient(0.7, 0.6, weight=0.2)
    run = run_asset(DOSSIER, "Asset_A", c, quant_rank_pct=0.8)
    assert run.p_judge == pytest.approx(0.65) and run.abstain is False
    assert run.p_hybrid == pytest.approx(hybrid_probability(0.65, 0.8, 0.2)) and run.p_hybrid > run.p_judge
    names = [n for n, _ in c.prompts]
    assert names[:4] == ["analyst_market", "analyst_fundamental", "analyst_news", "forecast"]
    assert names[4:] == ["bull_open", "bear_reply", "judge_bull_first", "bear_open", "bull_reply", "judge_bear_first"]
    assert len(run.meta) == 4 + 2 * 3 and run.config_sha == config_sha()
    for name, prompt in c.prompts:
        assert "Asset_A" in prompt and "Bitcoin" not in prompt
        if name != "forecast":
            assert "ridge" not in prompt                                            # only the interpreter sees the quant line
    assert set(c.efforts) == {"none", "medium"} and c.efforts[-1] == "medium"
    run2 = run_asset(DOSSIER, "Asset_A", StubClient(), analysts=run.analysts, forecast=run.forecast, quant_rank_pct=0.8)
    assert len(run2.meta) == 2 * 3                                                  # analysts + interpreter not re-run
    assert run.citations["analyst_market"]["cite_exist_rate"] == 0.0               # n1, t9 are not in the market view
    assert run.citations["analyst_fundamental"]["cite_exist_rate"] == 0.5          # n1 yes, t9 no
    assert run.citations["analyst_market"]["number_grounded_rate"] == 1.0          # "12.0" occurs in the market view


def test_run_asset_without_debate_single_judge_and_abstain_maps_to_half():
    c = StubClient(p_nd=0.3)
    run = run_asset(DOSSIER, "Asset_A", c, debate=False, with_forecast=False)
    assert "none" in run.debates and run.forecast == {} and len(run.meta) == 3 + 1
    assert run.p_judge == pytest.approx(0.3) and run.p_hybrid == pytest.approx(0.3)   # no weight -> no mixing

    class Abstainer(StubClient):
        def call(self, prompt, schema, name="answer", **kw):
            out, meta = super().call(prompt, schema, name, **kw)
            if schema is schemas.JUDGE:
                out = {**out, "abstain": True, "p_outperform_7d": 0.9}
            return out, meta
    run = run_asset(DOSSIER, "Asset_A", Abstainer(), debate=False, with_forecast=False)
    assert run.abstain and run.p_judge == 0.5


def test_hybrid_mixing_bounds():
    assert hybrid_probability(0.5, 0.5, 0.5) == pytest.approx(0.5)
    assert hybrid_probability(0.6, None, 0.5) == 0.6 and hybrid_probability(0.6, 0.9, None) == 0.6
    assert hybrid_probability(0.5, 0.99, 1.0) == pytest.approx(0.98)            # clipped quant percentile
    assert hybrid_probability(0.4, 0.9, 0.0) == pytest.approx(0.4)


def test_rule_weights_keyed_by_symbol_without_confidence():
    cands = [{"symbol": "AAA", "p_outperform_7d": 0.7, "confidence": 0.8, "abstain": False, "vol_ann": 0.5},
             {"symbol": "BBB", "p_outperform_7d": 0.3, "confidence": 0.5, "abstain": False, "vol_ann": 1.0},
             {"symbol": "CCC", "p_outperform_7d": 0.9, "confidence": 0.9, "abstain": True, "vol_ann": 0.5},
             {"symbol": "DDD", "p_outperform_7d": 0.5, "confidence": 0.1, "abstain": False, "vol_ann": 0.5}]
    w = rule_weights(cands)
    assert set(w) == {"AAA", "BBB", "CCC", "DDD"} and w["AAA"] > 0 > w["BBB"]
    assert abs(sum(w.values())) < 1e-9 and max(abs(v) for v in w.values()) <= 0.10 + 1e-9
    wc = rule_weights(cands, use_confidence=True, max_weight=1.0)
    assert wc != rule_weights(cands, max_weight=1.0) and abs(sum(wc.values())) < 1e-9   # confidence changes the variant only
    assert w["CCC"] == 0.0                                                          # abstention is flat


def test_portfolio_manager_uses_week_unique_ids_and_falls_back():
    cands = [{"symbol": "AAA", "p_outperform_7d": 0.7, "confidence": 0.8, "abstain": False, "vol_ann": 0.5},
             {"symbol": "BBB", "p_outperform_7d": 0.3, "confidence": 0.5, "abstain": False, "vol_ann": 1.0}]
    c = StubClient()
    out = run_portfolio(cands, c)
    assert "C01" in c.prompts[-1][1] and "AAA" not in c.prompts[-1][1]
    assert "weight beyond cap" in out["problems"] and out["weights"] == rule_weights(cands)
    ok = {"positions": [{"alias": "C01", "weight": 0.1, "reason": ""}, {"alias": "C02", "weight": -0.1, "reason": ""}],
          "gross_exposure": 0.2, "notes": ""}
    shown = [{"id": "C01", "abstain": False}, {"id": "C02", "abstain": False}]
    assert validate_portfolio(ok, shown) == []
    dup = {"positions": [{"alias": "C01", "weight": 0.05, "reason": ""}, {"alias": "C01", "weight": -0.05, "reason": ""}],
           "gross_exposure": 0.1, "notes": ""}
    assert "duplicate id in positions" in validate_portfolio(dup, shown)


def test_citation_report_mechanics():
    rep = citation_report({"cited_items": ["n1", "[t1]", "n9"], "key_facts": ["return 12.0% and 99 partners"]}, DOSSIER)
    assert rep["n_cited"] == 3 and rep["cite_exist_rate"] == pytest.approx(2 / 3)
    assert rep["n_numbers"] == 2 and rep["number_grounded_rate"] == 0.5
