"""Case-insensitive whole-word ticker/exchange anonymization."""
from __future__ import annotations

import re
from typing import Dict


_COIN_TO_ALIAS = {"BTC": "Asset-A", "ETH": "Asset-B"}

_COIN_NAMES = {
    "BTC": ["Bitcoin", "BTC"],
    "ETH": ["Ethereum", "ETH", "Ether"],
}

_EXCHANGES = [
    "Binance", "Coinbase", "Kraken", "Bitfinex", "Bitstamp",
    "OKX", "Bybit", "KuCoin", "Gate.io", "Huobi", "Bittrex",
    "Gemini", "FTX",
]


def build_substitution_table(coin: str) -> Dict[str, str]:
    """Return {original_token: replacement} for a coin. Used for debugging."""
    coin = coin.upper()
    alias = _COIN_TO_ALIAS[coin]
    table: Dict[str, str] = {}
    for name in _COIN_NAMES.get(coin, []):
        table[name] = alias
    for i, ex in enumerate(_EXCHANGES, 1):
        table[ex] = f"Exchange-{i}"
    return table


def anonymize_text(text: str, coin: str) -> str:
    """Case-insensitive whole-word replacement of coin + exchange names."""
    coin = coin.upper()
    if coin not in _COIN_TO_ALIAS:
        return text
    alias = _COIN_TO_ALIAS[coin]
    result = text
    # Coin tokens: whole-word, case-insensitive
    for name in _COIN_NAMES[coin]:
        result = re.sub(
            rf"\b{re.escape(name)}\b",
            alias,
            result,
            flags=re.IGNORECASE,
        )
    # Exchanges: whole-word, case-insensitive, stable index
    for i, ex in enumerate(_EXCHANGES, 1):
        result = re.sub(
            rf"\b{re.escape(ex)}\b",
            f"Exchange-{i}",
            result,
            flags=re.IGNORECASE,
        )
    return result
