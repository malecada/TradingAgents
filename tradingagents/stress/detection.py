"""Detection metrics + block-shuffle placebo for the stress EWS."""
import numpy as np
import pandas as pd


def _warn_clusters(warn: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    clusters = []
    start = prev = None
    for ts, on in warn.items():
        if on:
            if start is None:
                start = ts
            prev = ts
        elif start is not None:
            clusters.append((start, prev))
            start = None
    if start is not None:
        clusters.append((start, prev))
    return clusters


def detection_metrics(warn: pd.Series, episodes: pd.DataFrame, window: int = 20) -> dict:
    warn = warn.astype(bool)
    leads, hits = [], 0
    for _, ep in episodes.iterrows():
        lo, hi = ep["start"] - pd.Timedelta(days=window), ep["start"] - pd.Timedelta(days=1)
        w = warn.loc[lo:hi]
        if w.any():
            hits += 1
            leads.append((ep["start"] - w[w].index[0]).days)
    clusters = _warn_clusters(warn)
    fa = 0
    for cs, _ in clusters:
        ok = any(
            cs <= ep_start <= cs + pd.Timedelta(days=window)
            for ep_start in episodes["start"]
        )
        if not ok:
            fa += 1
    years = max((warn.index[-1] - warn.index[0]).days / 365.25, 1e-9)
    n_ep = len(episodes)
    return {
        "hit_rate": hits / n_ep if n_ep else float("nan"),
        "n_episodes": n_ep,
        "n_hits": hits,
        "median_lead_days": float(np.median(leads)) if leads else float("nan"),
        "false_alarm_clusters_per_year": fa / years,
        "n_warn_clusters": len(clusters),
    }


def _block_shuffle(values: np.ndarray, block: int, rng: np.random.Generator) -> np.ndarray:
    n = len(values)
    out = np.empty(n, dtype=values.dtype)
    i = 0
    while i < n:
        length = min(rng.geometric(1.0 / block), n - i)
        start = rng.integers(0, n)
        idx = (start + np.arange(length)) % n
        out[i : i + length] = values[idx]
        i += length
    return out


def placebo_pvalue(
    warn: pd.Series, episodes: pd.DataFrame,
    n: int = 500, block: int = 21, seed: int = 0, window: int = 20,
) -> dict:
    real = detection_metrics(warn, episodes, window)["hit_rate"]
    rng = np.random.default_rng(seed)
    vals = warn.astype(bool).to_numpy()
    placebo = []
    for _ in range(n):
        fake = pd.Series(_block_shuffle(vals, block, rng), index=warn.index)
        placebo.append(detection_metrics(fake, episodes, window)["hit_rate"])
    placebo = np.array(placebo)
    ge = int(np.sum(placebo >= real)) if not np.isnan(real) else n
    return {"p_hit_rate": (1 + ge) / (n + 1), "placebo_hit_rates": placebo.tolist()}
