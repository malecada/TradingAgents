"""Daily examples with 28-step windows; each step carries its latest available week (spec §8, §10)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch

from . import calendar as cal
from . import prices as P
from . import weekly as W


@dataclass
class Example:
    decision: date
    step_days: list
    step_weeks: list
    closes: np.ndarray
    target: float


def examples(split, prices, scaler, task):
    out = []
    for d in cal.decision_dates(split):
        days = cal.window(d)
        weeks = [cal.available_week(t) for t in days]
        if any(w is None for w in weeks):
            continue
        closes = np.array([scaler.transform(prices[t]) for t in days], np.float32)
        if task == 'classification':
            target = float(P.direction(prices, d))
        else:
            target = float(scaler.transform(P.target_usd(prices, d)))
        out.append(Example(d, days, weeks, closes, target))
    return out


class WeekStore:
    """Loads (mcm, edge_index) tensors per week with a small LRU cache."""

    def __init__(self, graph_dir: Path, mcm_dir: Path):
        self.graph_dir, self.mcm_dir = Path(graph_dir), Path(mcm_dir)
        self._tensors = lru_cache(maxsize=16)(self._load)

    def _load(self, week):
        g = W.load(self.graph_dir / week)
        mcm = np.load(self.mcm_dir / f'{week}.npy')
        return torch.from_numpy(mcm.astype(np.float32)), torch.from_numpy(g.edge_index.astype(np.int64))

    def tensors(self, week):
        return self._tensors(week)


@dataclass
class Batch:
    decisions: list
    prices: torch.Tensor
    weeks: list
    targets: torch.Tensor


def batches(examples_, batch_size):
    for s in range(0, len(examples_), batch_size):
        chunk = examples_[s:s + batch_size]
        yield Batch([e.decision for e in chunk],
                    torch.from_numpy(np.stack([e.closes for e in chunk])),
                    [e.step_weeks for e in chunk],
                    torch.tensor([e.target for e in chunk]))
