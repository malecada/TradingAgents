"""Structured sentiment pipeline (v3).

See docs/superpowers/specs/2026-05-23-sentiment-analyst-v3-design.md.
"""
from tradingagents.sentiment.snapshot import (
    CryptoEventType,
    EventFlag,
    SentimentSnapshot,
)

__all__ = ["CryptoEventType", "EventFlag", "SentimentSnapshot"]
