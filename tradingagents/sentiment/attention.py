"""Liu-Tsyvinski-style Google Trends attention features."""
from __future__ import annotations

from datetime import datetime
from typing import Dict

import pandas as pd

_COIN_TO_QUERY = {"bitcoin": "bitcoin", "ethereum": "ethereum",
                  "btc": "bitcoin", "eth": "ethereum"}
_COIN_TO_NEG = {"bitcoin": "bitcoin hack", "ethereum": "ethereum hack",
                "btc": "bitcoin hack", "eth": "ethereum hack"}


def compute_attention_features(
    gtrends_df: pd.DataFrame,
    coin: str,
    trade_date: datetime,
) -> Dict[str, float]:
    """Compute Liu-Tsyvinski attention features from gtrends rows."""
    out = {
        "google_search_z": 0.0,
        "google_neg_attention_ratio": 0.0,
        "twitter_volume_z": 0.0,
    }
    if gtrends_df.empty:
        return out
    coin_l = coin.lower()
    pos_q = _COIN_TO_QUERY.get(coin_l, coin_l)
    neg_q = _COIN_TO_NEG.get(coin_l, f"{coin_l} hack")
    df = gtrends_df.copy()
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    df = df.sort_values("event_ts")
    pos = df[df["query"] == pos_q]
    if not pos.empty:
        out["google_search_z"] = float(pos["value_z90"].iloc[-1])
    neg = df[df["query"] == neg_q]
    if not neg.empty and not pos.empty:
        # Liu-Tsyvinski ratio: neg / pos, then z-score-flavoured via stored z90.
        pos_val = float(pos["value"].iloc[-1]) or 1.0
        neg_val = float(neg["value"].iloc[-1])
        out["google_neg_attention_ratio"] = neg_val / pos_val
    return out
