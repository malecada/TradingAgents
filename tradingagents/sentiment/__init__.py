"""Structured sentiment pipeline (v3).

See docs/superpowers/specs/2026-05-23-sentiment-analyst-v3-design.md.
"""
from tradingagents.sentiment.snapshot import (
    CryptoEventType,
    EventFlag,
    SentimentSnapshot,
)

__all__ = ["CryptoEventType", "EventFlag", "SentimentSnapshot"]

from tradingagents.sentiment.snapshot import build_snapshot  # noqa: E402
__all__.append("build_snapshot")
