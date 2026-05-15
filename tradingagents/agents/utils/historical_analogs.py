"""Historical analog retrieval over regime-feature tuples (Tier B8).

Indexed on tuples of (regime, hurst, funding_z, drawdown_30d) encoded
as a deterministic string so the existing BM25 retriever can be reused.
The Skeptic-Quant agent queries this for "what did the past 30-day
window with this regime+features look like, and what was the realised
outcome?" — directly attacking FINSABER's "bull-conservative,
bear-aggressive" pathology by grounding the LLM's regime intuition in
historical analogs.

Phase 6 ships a BM25-only path that key-encodes regime features as text.
A dense retriever on top of the existing FAISS index in
``memory._DenseRetriever`` is straightforward to add later — left
out here to keep the new module dependency-free.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from tradingagents.agents.utils.memory import FinancialSituationMemory

logger = logging.getLogger(__name__)


@dataclass
class RegimeWindow:
    """A 30-day window characterized by its regime + numeric features."""

    end_date: str
    regime: str
    hurst: float
    funding_z: float
    drawdown_30d: float
    realised_return: float

    def to_text(self) -> str:
        """Encode features as a stable text query for BM25 indexing."""
        return (
            f"regime_{self.regime} "
            f"hurst_{self._bin(self.hurst, 0.05)} "
            f"funding_{self._bin(self.funding_z, 0.5)} "
            f"drawdown_{self._bin(self.drawdown_30d, 0.05)}"
        )

    @staticmethod
    def _bin(v: float, step: float) -> str:
        return f"{round(v / step) * step:+.2f}"


class HistoricalAnalogRetriever:
    """Wraps FinancialSituationMemory for regime-feature analogy lookups."""

    def __init__(self, name: str = "historical_analogs", config: Optional[dict] = None):
        self._mem = FinancialSituationMemory(name=name, config=config)

    def index(self, windows: List[RegimeWindow]) -> None:
        situations = [w.to_text() for w in windows]
        outcomes = [
            f"end={w.end_date}, regime={w.regime}, "
            f"realised_return={w.realised_return:+.4f}"
            for w in windows
        ]
        self._mem.add_situations(list(zip(situations, outcomes)))

    def retrieve(
        self,
        regime: str,
        hurst: float,
        funding_z: float,
        drawdown_30d: float,
        k: int = 5,
    ) -> List[dict]:
        query = RegimeWindow(
            end_date="now",
            regime=regime,
            hurst=hurst,
            funding_z=funding_z,
            drawdown_30d=drawdown_30d,
            realised_return=0.0,
        ).to_text()
        return self._mem.get_memories(query, n_matches=k)
