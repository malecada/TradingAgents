from __future__ import annotations

from tradingagents.strategies.contracts import QuantSignal
from tradingagents.strategies.regime import detect_regime


def get_quant_signal(coin: str, date: str) -> QuantSignal:
    """Return a Layer 1 ``QuantSignal`` for ``(coin, date)``.

    Phase 0 stub — emits a neutral long signal. Phase 1 wires this to
    precomputed LGB CSVs + ``v2_sizing`` primitives + ``detect_regime``.
    """
    regime, regime_conf, hurst = detect_regime(coin, date)
    return QuantSignal(
        coin=coin,
        direction="long",
        magnitude=0.5,
        regime=regime,
        regime_confidence=regime_conf,
        hurst=hurst,
        deterministic_signals={},
        as_of_date=date,
    )
