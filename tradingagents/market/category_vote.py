"""Category aggregation, conflict_score, asymmetric default direction.

The 2-vs-3 LONG/SHORT asymmetry implements the FINSABER bear-aggression
correction (arXiv:2505.07078): bear positions require stronger consensus
than bull positions because pretrained LLMs over-allocate on the short
side in down-markets. Asymmetric thresholds also encode the crypto-
specific upward drift.
"""
from __future__ import annotations

from typing import Dict

from tradingagents.market.indicators import INDICATOR_CATEGORY


def aggregate_category_votes(directions: Dict[str, int]) -> Dict[str, int]:
    """Sum per-indicator directions inside each category, return signed votes."""
    sums = {"trend": 0, "momentum": 0, "volatility": 0, "volume": 0}
    for name, d in directions.items():
        cat = INDICATOR_CATEGORY.get(name)
        if cat is None:
            continue
        sums[cat] += int(d)
    return {k: (1 if v > 0 else -1 if v < 0 else 0) for k, v in sums.items()}


def conflict_score(category_votes: Dict[str, int]) -> float:
    """Fraction of non-zero categories disagreeing with the majority sign.

    No non-zero categories => 0 (absence of signal, not conflict).
    """
    nonzero = [v for v in category_votes.values() if v != 0]
    if not nonzero:
        return 0.0
    s = sum(nonzero)
    if s == 0:
        return 0.5
    sign = 1 if s > 0 else -1
    disagree = sum(1 for v in category_votes.values() if v != 0 and v != sign)
    return disagree / 4.0


def asymmetric_default_direction(category_votes: Dict[str, int]) -> str:
    """LONG >= 2 pos & 0 neg; SHORT >= 3 neg & 0 pos; else FLAT."""
    pos = sum(1 for v in category_votes.values() if v == 1)
    neg = sum(1 for v in category_votes.values() if v == -1)
    if pos >= 2 and neg == 0:
        return "LONG"
    if neg >= 3 and pos == 0:
        return "SHORT"
    return "FLAT"
