from __future__ import annotations

from tradingagents.strategies.contracts import RegimeLabel


def detect_regime(coin: str, date: str) -> tuple[RegimeLabel, float, float]:
    """Return ``(regime, confidence, hurst)`` for a coin/date.

    Phase 0 stub — always returns a neutral sideways label. Phase 1 replaces
    this with HMM-3 + BOCPD + Hurst ensemble.
    """
    return "sideways", 0.5, 0.5
