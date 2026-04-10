from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_crypto_data(
    symbol: Annotated[str, "CoinGecko ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum', 'solana')"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Retrieve cryptocurrency OHLCV (Open, High, Low, Close, Volume) price data.

    Uses Binance as primary source with CoinGecko fallback.
    Returns daily candle data for technical analysis.
    """
    return route_to_vendor("get_crypto_data", symbol, start_date, end_date)


@tool
def get_crypto_indicators(
    symbol: Annotated[str, "CoinGecko ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum')"],
    indicator: Annotated[str, "Technical indicator to calculate (e.g., 'rsi', 'macd', 'boll', 'atr', 'close_50_sma')"],
    curr_date: Annotated[str, "Current trading date in YYYY-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back for indicator values"],
) -> str:
    """Compute technical indicators for a cryptocurrency.

    Available indicators: close_50_sma, close_200_sma, close_10_ema,
    macd, macds, macdh, rsi, boll, boll_ub, boll_lb, atr, vwma, mfi.

    Uses the same stockstats library as stock analysis, applied to crypto OHLCV data.
    """
    return route_to_vendor("get_crypto_indicators", symbol, indicator, curr_date, look_back_days)
