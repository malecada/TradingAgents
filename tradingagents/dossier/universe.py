"""Weekly PIT universe from the card panel (top-N perps by trailing 30-day dollar volume)."""
from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

CARDS = Path("data/llm_rank_xs/cards.parquet")
QUOTE_SUFFIXES = ("USDT", "USDC", "BUSD")


def base_symbol(symbol: str) -> str:
    """BTCUSDT -> BTC; 1000PEPEUSDT -> PEPE; 1000000MOGUSDT -> MOG."""
    s = symbol.upper()
    for q in QUOTE_SUFFIXES:
        if s.endswith(q):
            s = s[: -len(q)]
            break
    # Binance multiplier prefixes: 1000PEPE, 1000000MOG, 1MBABYDOGE -> PEPE, MOG, BABYDOGE
    s = re.sub(r"^1(?:0{3,}|M)(?=[A-Z])", "", s)
    return s


def load_cards(path: Path = CARDS) -> pd.DataFrame:
    cards = pd.read_parquet(path)
    cards["date"] = pd.to_datetime(cards["date"], utc=True)
    return cards


def weekly_top(cards: pd.DataFrame, n: int = 50, start=None, end=None) -> pd.DataFrame:
    """Rows of the top-``n`` symbols per Friday by ``dvol_30d`` (PIT: computed from trailing data)."""
    frame = cards.dropna(subset=["dvol_30d"])
    if start is not None:
        frame = frame[frame["date"] >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        frame = frame[frame["date"] <= pd.Timestamp(end, tz="UTC")]
    ranked = frame.sort_values(["date", "dvol_30d"], ascending=[True, False])
    top = ranked.groupby("date", group_keys=False).head(n).copy()
    top["vol_rank"] = top.groupby("date").cumcount() + 1
    top["base"] = top["symbol"].map(base_symbol)
    return top.reset_index(drop=True)


def universe_members(top: pd.DataFrame) -> list[str]:
    return sorted(top["symbol"].unique())
