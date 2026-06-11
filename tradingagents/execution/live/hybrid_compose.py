# tradingagents/execution/live/hybrid_compose.py
"""Pure compose primitives for the hybrid (quant base × LLM modulator) path.

The composition mirrors the validated §23 backtest
(scripts/backtest_hybrid.py:118, scripts/ablate_hybrid.py:73):

    final = base * (1 + effective_weight * (multiplier - 1))

where ``base`` is the V5-sized quant position and (multiplier, effective_weight)
come from the modulator graph's ``modulated_position`` (NOT its ``position``,
which composed against the graph's own internal magnitude).
"""
from __future__ import annotations


def compose_final(*, base: float, multiplier: float, effective_weight: float) -> float:
    return float(base * (1.0 + effective_weight * (multiplier - 1.0)))


def extract_modulator_outputs(modulated_position: dict | None) -> tuple[float, float]:
    """Return (multiplier, effective_weight) from a modulated_position dict.

    Degrades to pure quant (1.0, 0.0) when the modulator was skipped or any
    field is missing, so a modulator failure never moves the hybrid position
    away from the quant base. Multiplier clamped to the contract bounds [0,1.5].
    """
    if not modulated_position:
        return (1.0, 0.0)
    mult = modulated_position.get("llm_multiplier")
    eff_w = modulated_position.get("effective_weight")
    if mult is None or eff_w is None:
        return (1.0, 0.0)
    mult = max(0.0, min(1.5, float(mult)))
    eff_w = max(0.0, min(1.0, float(eff_w)))
    return (mult, eff_w)


from pathlib import Path
import pandas as pd


def stage_quant_preds(rows: list[dict], *, date: str, out_dir) -> Path:
    """Write cycle predictions to the quant_engine CSV layout.

    ``rows`` = list of {coin, horizon, prediction, ref_price}. Writes
    preds_lgb_h7.csv and preds_lgb_h14.csv (columns date, coin_id, ref_price,
    prediction) under ``out_dir`` and returns it. Point config["quant_pred_dir"]
    at the returned path.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    for h, fname in [(7, "preds_lgb_h7.csv"), (14, "preds_lgb_h14.csv")]:
        sub = df[df["horizon"] == h].copy()
        sub["date"] = pd.to_datetime(date).normalize()
        sub = sub.rename(columns={"coin": "coin_id"})
        sub[["date", "coin_id", "ref_price", "prediction"]].to_csv(
            out_dir / fname, index=False
        )
    return out_dir
