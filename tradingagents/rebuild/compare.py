"""Paired stationary-block-bootstrap SR comparison (shared index path)."""
from __future__ import annotations

import numpy as np
import pandas as pd

ANN = np.sqrt(252)


def _sr(x: np.ndarray) -> float:
    sd = x.std(ddof=1)
    return float(x.mean() / sd * ANN) if sd > 0 else 0.0


def paired_bootstrap(
    a: pd.Series, b: pd.Series, block: int = 21, n: int = 2000, seed: int = 7,
) -> dict:
    ab = pd.concat({"a": a, "b": b}, axis=1).dropna()
    xa, xb = ab["a"].values, ab["b"].values
    T = len(xa)
    rng = np.random.default_rng(seed)
    deltas = np.empty(n)
    for k in range(n):
        idx = []
        while len(idx) < T:
            start = rng.integers(0, T)
            length = rng.geometric(1.0 / block)
            idx.extend(((start + np.arange(length)) % T).tolist())
        idx = np.array(idx[:T])
        deltas[k] = _sr(xb[idx]) - _sr(xa[idx])
    return {
        "sr_a": _sr(xa), "sr_b": _sr(xb), "delta_sr": _sr(xb) - _sr(xa),
        "p_pos": float((deltas > 0).mean()),
        "ci_low": float(np.percentile(deltas, 2.5)),
        "ci_high": float(np.percentile(deltas, 97.5)),
    }
