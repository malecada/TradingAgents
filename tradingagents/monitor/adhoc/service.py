# tradingagents/monitor/adhoc/service.py
"""Pure ad-hoc prediction logic. Reproduces the live cycle's predict path for
an arbitrary date, yielding (key, label, kind, content) tuples per stage.

Engine modules are imported lazily and referenced as `module.attr` so tests can
monkeypatch the source symbols. A yield with kind == "progress" is a stage
marker only (the worker updates progress; it is not stored as an output).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Tuple

Output = Tuple[str, str, str, object]   # (key, label, kind, content)


def _staging_root(data_root: str, run_id: str) -> Path:
    return Path(data_root) / "adhoc" / run_id


def _latest_checkpoint(data_root: str) -> Path:
    ckpt_dir = Path(data_root) / "checkpoints"
    cands = sorted(ckpt_dir.glob("composite_*.pkl"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not cands:
        raise FileNotFoundError(
            f"no composite_*.pkl checkpoint in {ckpt_dir}; run a live cycle first")
    return cands[0]


def _compute_and_stage(cfg, coin: str, date: str, run_id: str) -> Path:
    """run_predict for the single coin + stage CSVs the engine can read back."""
    from tradingagents.execution.live import predict
    from tradingagents.execution.live import hybrid_compose

    preds_df = predict.run_predict(
        coin_universe=[coin],
        routing=cfg.routing,
        ckpt_path=_latest_checkpoint(cfg.data_root),
        asof=date,
        store_root=Path(cfg.data_root) / "onchain",
        ohlcv_cache=Path(cfg.data_root) / "cache",
        horizons=cfg.horizons,
    )
    if preds_df is None or len(preds_df) == 0:
        raise RuntimeError(f"no prediction produced for {coin} @ {date}")
    rows = preds_df[["coin", "horizon", "prediction", "ref_price"]].to_dict("records")
    staged = _staging_root(cfg.data_root, run_id) / "cycle_preds" / date
    return hybrid_compose.stage_quant_preds(rows, date=date, out_dir=staged)


def run_quant(*, coin: str, date: str, run_id: str) -> Iterator[Output]:
    from tradingagents.execution.live import config as live_config
    from tradingagents.strategies import quant_engine

    yield ("_p", "Computing quant signal", "progress", "")
    cfg = live_config.load_config()
    staged = _compute_and_stage(cfg, coin, date, run_id)
    sig = quant_engine.get_quant_signal(coin, date, base_dir=str(staged))
    yield ("quant_signal", "Quant signal", "json", sig.model_dump())
    yield ("final", "Final decision", "json", {
        "strategy": "quant", "direction": sig.direction, "magnitude": sig.magnitude,
        "regime": sig.regime})


_REPORT_KEYS = [
    ("market_report", "Market analyst"),
    ("onchain_report", "On-chain analyst"),
    ("prediction_report", "Prediction analyst"),
    ("sentiment_report", "Sentiment analyst"),
]


def run_hybrid(*, coin: str, date: str, analysts, model: str | None,
               run_id: str) -> Iterator[Output]:
    from tradingagents.execution.live import config as live_config
    from tradingagents.execution.live import hybrid_compose
    from tradingagents.graph import trading_graph

    yield ("_p", "Computing quant base", "progress", "")
    cfg = live_config.load_config()
    staged = _compute_and_stage(cfg, coin, date, run_id)

    gcfg = hybrid_compose.build_hybrid_config(quant_pred_dir=str(staged))
    if model:
        gcfg["deep_think_llm"] = model
        gcfg["quick_think_llm"] = model

    yield ("_p", "Running agent graph (~90s)", "progress", "")
    graph = trading_graph.TradingAgentsGraph(
        selected_analysts=list(analysts) if analysts else list(hybrid_compose.HYBRID_ANALYSTS),
        config=gcfg)
    final_state, mp, _qs, narrative = graph.propagate_with_modulator(coin, date)

    for key, label in _REPORT_KEYS:
        text = final_state.get(key)
        if text:
            yield (key, label, "text", text)

    debate = final_state.get("investment_debate_state", {}) or {}
    if debate.get("bull_history"):
        yield ("bull", "Bull researcher", "text", debate["bull_history"])
    if debate.get("bear_history"):
        yield ("bear", "Bear researcher", "text", debate["bear_history"])
    if debate.get("judge_decision"):
        yield ("research_manager", "Research manager", "text", debate["judge_decision"])

    if final_state.get("trader_investment_plan"):
        yield ("trader", "Trader plan", "text", final_state["trader_investment_plan"])

    risk = final_state.get("risk_debate_state", {}) or {}
    if risk.get("judge_decision"):
        yield ("risk_debate", "Risk debate", "text", risk["judge_decision"])

    mult, eff_w = hybrid_compose.extract_modulator_outputs(mp)
    yield ("modulator", "Modulator", "json", {
        "multiplier": mult, "effective_weight": eff_w, "narrative": narrative,
        "modulated_position": mp})

    if final_state.get("final_trade_decision"):
        yield ("pm_decision", "Portfolio manager", "text",
               final_state["final_trade_decision"])

    yield ("final", "Final decision", "json", {
        "strategy": "hybrid", "pm": final_state.get("final_trade_decision"),
        "multiplier": mult, "effective_weight": eff_w, "modulated_position": mp})
