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
