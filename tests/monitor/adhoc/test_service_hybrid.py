from __future__ import annotations

import types

import pandas as pd
import pytest

from tradingagents.monitor.adhoc import service


class _FakeGraph:
    def __init__(self, **kw):
        self.kw = kw

    def propagate_with_modulator(self, coin, date):
        final_state = {
            "market_report": "MKT report text",
            "onchain_report": "ONCHAIN report text",
            "prediction_report": "PRED report text",
            "investment_debate_state": {
                "bull_history": "bull says buy",
                "bear_history": "bear says sell",
                "judge_decision": "manager: lean buy"},
            "trader_investment_plan": "trader: BUY 0.5",
            "risk_debate_state": {"judge_decision": "risk: ok"},
            "final_trade_decision": "OVERWEIGHT",
            "modulated_position": {"llm_multiplier": 1.2, "effective_weight": 0.3,
                                   "llm_confidence": 0.8, "regime": "bull"},
            "modulator_narrative": "scaled up on bull regime",
        }
        mp = final_state["modulated_position"]
        return final_state, mp, {"direction": "long"}, "scaled up on bull regime"


@pytest.fixture
def patched(tmp_path, monkeypatch):
    cfg = types.SimpleNamespace(
        coin_universe=["bitcoin"], routing={"bitcoin": {"pool": ["bitcoin"]}},
        horizons=[7, 14], data_root=str(tmp_path))
    monkeypatch.setattr("tradingagents.execution.live.config.load_config", lambda: cfg)
    (tmp_path / "checkpoints").mkdir()
    (tmp_path / "checkpoints" / "composite_x.pkl").write_text("x")
    df = pd.DataFrame([
        {"coin": "bitcoin", "horizon": 7, "prediction": 0.01, "ref_price": 60000.0},
        {"coin": "bitcoin", "horizon": 14, "prediction": 0.02, "ref_price": 60000.0}])
    monkeypatch.setattr("tradingagents.execution.live.predict.run_predict",
                        lambda **kw: df)
    monkeypatch.setattr(
        "tradingagents.execution.live.hybrid_compose.stage_quant_preds",
        lambda rows, *, date, out_dir: tmp_path / "staged")
    monkeypatch.setattr(
        "tradingagents.execution.live.hybrid_compose.build_hybrid_config",
        lambda *, quant_pred_dir: {"deep_think_llm": "gpt-4o-mini",
                                   "quick_think_llm": "gpt-4o-mini"})
    monkeypatch.setattr("tradingagents.graph.trading_graph.TradingAgentsGraph",
                        _FakeGraph)
    return cfg


def test_run_hybrid_emits_all_partials(patched):
    outs = list(service.run_hybrid(coin="bitcoin", date="2026-05-01",
                                   analysts=["market", "onchain", "prediction"],
                                   model="gpt-4o-mini", run_id="r1"))
    keys = [k for (k, _l, _kind, _c) in outs]
    for expected in ["market_report", "onchain_report", "prediction_report",
                     "bull", "bear", "research_manager", "trader", "risk_debate",
                     "modulator", "pm_decision", "final"]:
        assert expected in keys, expected
    final = [c for (k, _l, _kind, c) in outs if k == "final"][0]
    assert final["pm"] == "OVERWEIGHT"
    assert final["multiplier"] == 1.2


def test_run_hybrid_applies_model_override(patched, monkeypatch):
    captured = {}
    orig = _FakeGraph

    class _Capture(_FakeGraph):
        def __init__(self, **kw):
            captured.update(kw)
            super().__init__(**kw)

    monkeypatch.setattr("tradingagents.graph.trading_graph.TradingAgentsGraph",
                        _Capture)
    list(service.run_hybrid(coin="bitcoin", date="2026-05-01",
                            analysts=["market"], model="gpt-4o", run_id="r1"))
    assert captured["config"]["deep_think_llm"] == "gpt-4o"
    assert captured["config"]["quick_think_llm"] == "gpt-4o"
    assert captured["selected_analysts"] == ["market"]
