"""Coin Metrics daily PriceUSD (declared deviation from the paper's Yahoo source)."""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .config import ROOT

DEFAULT = ROOT / ('research_artifacts/onchain-paper-replication-2026-09-24/sources/'
                  'paper-prices-coinmetrics-eth-20260924/capture/'
                  'da30555fdfc60ac1d51a62b598421a339e5ab417bceb9e7f8bf29a4d19630f9e/response.bin')


def load_prices(path: Path = DEFAULT) -> dict[date, float]:
    out = {}
    with open(path, newline='') as fh:
        for row in csv.DictReader(fh):
            v = row.get('PriceUSD', '')
            if v == '':
                continue
            d = date.fromisoformat(row['time'][:10])
            x = float(v)
            if not math.isfinite(x) or x <= 0 or d in out:
                raise ValueError(f'bad price row {row["time"]}')
            out[d] = x
    return out


def target_usd(prices, d: date) -> float:
    return prices[d + timedelta(days=1)]


def direction(prices, d: date) -> int:
    return int(prices[d + timedelta(days=1)] > prices[d])


@dataclass
class Scaler:
    mean: float = 0.0
    std: float = 1.0

    def fit(self, prices, days):
        xs = [prices[t] for t in days]
        n = len(xs)
        self.mean = sum(xs) / n
        var = sum((x - self.mean) ** 2 for x in xs) / n
        self.std = math.sqrt(var) if var > 0 else 1.0
        return self

    def transform(self, x):
        return (x - self.mean) / self.std

    def inverse(self, z):
        return z * self.std + self.mean
