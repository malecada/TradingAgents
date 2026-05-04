"""Binance Futures (USDT-M) client wrapper with testnet default and retry logic.

Ported from Krypto-v0's ``src_live/exchange.py`` and adapted for TradingAgents.
Reads configuration from ``get_config().get("execution", {})``, and API
credentials from environment variables ``BINANCE_API_KEY`` / ``BINANCE_API_SECRET``.
"""

from __future__ import annotations

import math
import os
import time
import logging
from typing import Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException

from tradingagents.dataflows.config import get_config

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAY_S = 2  # exponential backoff base


class ExchangeClient:
    """Thin wrapper around ``python-binance`` for USDT-M Futures trading.

    By default connects to the Binance **testnet** so that no real funds
    are at risk.  Set ``execution.live_mode: True`` in config (and supply
    real API keys) to trade with real money.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        testnet: bool | None = None,
        base_url: str | None = None,
    ):
        cfg = get_config().get("execution", {})

        self._api_key = api_key or os.environ.get("BINANCE_API_KEY", "")
        self._api_secret = api_secret or os.environ.get("BINANCE_API_SECRET", "")

        # Testnet unless explicitly opted into live mode
        if testnet is None:
            self.testnet = not cfg.get("live_mode", False)
        else:
            self.testnet = testnet

        self._client = Client(self._api_key, self._api_secret, testnet=self.testnet)

        # Configure Futures endpoint
        if base_url:
            self._client.FUTURES_URL = base_url.rstrip("/") + "/fapi"
        elif self.testnet:
            self._client.FUTURES_URL = "https://testnet.binancefuture.com/fapi"

        self._symbol_info_cache: dict = {}

    # -- Account ---------------------------------------------------------------

    def get_balances(self) -> dict[str, float]:
        """Return ``{asset: available_balance}`` for all futures wallet assets."""
        account = self._retry(self._client.futures_account)
        return {
            a["asset"]: float(a["availableBalance"])
            for a in account["assets"]
            if float(a["walletBalance"]) > 0 or float(a["availableBalance"]) > 0
        }

    def get_usdt_balance(self) -> float:
        """Return available USDT balance in futures wallet."""
        balances = self.get_balances()
        return balances.get("USDT", 0.0)

    def get_current_position(self, symbol: str) -> float:
        """Return net position size for *symbol*.

        Positive = long, negative = short, 0 = flat.
        """
        positions = self._retry(
            self._client.futures_position_information, symbol=symbol,
        )
        for pos in positions:
            if pos["symbol"] == symbol:
                return float(pos["positionAmt"])
        return 0.0

    def get_position_value(self, symbol: str) -> float:
        """Return absolute USDT value of current position for *symbol*."""
        pos_amt = self.get_current_position(symbol)
        if pos_amt == 0:
            return 0.0
        price = self.get_ticker_price(symbol)
        return abs(pos_amt) * price

    def get_total_portfolio_value(self) -> float:
        """Total futures wallet value (wallet balance + unrealised PnL)."""
        account = self._retry(self._client.futures_account)
        return float(account.get("totalMarginBalance", 0.0))

    def get_open_position_count(self) -> int:
        """Count symbols with non-zero futures positions."""
        positions = self._retry(self._client.futures_position_information)
        return sum(1 for p in positions if float(p["positionAmt"]) != 0)

    # -- Leverage --------------------------------------------------------------

    def set_leverage(self, symbol: str, leverage: int) -> dict:
        """Set leverage for *symbol*."""
        logger.info("Setting leverage for %s to %dx", symbol, leverage)
        return self._retry(
            self._client.futures_change_leverage,
            symbol=symbol,
            leverage=leverage,
        )

    # -- Orders ----------------------------------------------------------------

    def place_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        """Place a futures MARKET order.  *side* is ``'BUY'`` or ``'SELL'``."""
        quantity = self.round_quantity(symbol, quantity)
        logger.info("FUTURES MARKET %s %s qty=%.8f", side, symbol, quantity)
        return self._retry(
            self._client.futures_create_order,
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity,
        )

    def place_stop_loss(
        self,
        symbol: str,
        quantity: float,
        stop_price: float,
        side: str = "SELL",
    ) -> dict:
        """Place a futures STOP_MARKET order that reduces the position.

        *side* should be ``'SELL'`` for long positions and ``'BUY'`` for shorts.
        Uses ``reduceOnly=true`` + explicit quantity instead of
        ``closePosition=true`` so partial-position stops work and the order
        avoids the TIF GTE position-presence check that ``closePosition``
        triggers on testnet (APIError -4509).
        """
        stop_price = self.round_price(symbol, stop_price)
        quantity = self.round_quantity(symbol, quantity)
        logger.info(
            "FUTURES STOP_MARKET %s %s qty=%.8f stop=%.2f",
            symbol, side, quantity, stop_price,
        )
        return self._retry(
            self._client.futures_create_order,
            symbol=symbol,
            side=side,
            type="STOP_MARKET",
            stopPrice=str(stop_price),
            quantity=quantity,
            reduceOnly="true",
        )

    def cancel_all_orders(self, symbol: str) -> list[dict]:
        """Cancel all open futures orders for *symbol*."""
        open_orders = self._retry(
            self._client.futures_get_open_orders, symbol=symbol,
        )
        results = []
        for order in open_orders:
            try:
                r = self._retry(
                    self._client.futures_cancel_order,
                    symbol=symbol,
                    orderId=order["orderId"],
                )
                results.append(r)
            except BinanceAPIException as e:
                logger.warning(
                    "Failed to cancel order %s: %s", order["orderId"], e,
                )
        return results

    # -- Market data -----------------------------------------------------------

    def get_ticker_price(self, symbol: str) -> float:
        """Current futures mark price."""
        data = self._retry(self._client.futures_symbol_ticker, symbol=symbol)
        return float(data["price"])

    def get_symbol_info(self, symbol: str) -> dict:
        """Trading rules for *symbol* (cached from futures exchange info)."""
        if symbol not in self._symbol_info_cache:
            info = self._retry(self._client.futures_exchange_info)
            for s in info["symbols"]:
                self._symbol_info_cache[s["symbol"]] = s
        if symbol not in self._symbol_info_cache:
            raise ValueError(f"Symbol {symbol} not found in futures exchange info")
        return self._symbol_info_cache[symbol]

    # -- Rounding helpers ------------------------------------------------------

    def round_quantity(self, symbol: str, quantity: float) -> float:
        """Round *quantity* down to the symbol's LOT_SIZE step."""
        info = self.get_symbol_info(symbol)
        for f in info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                step = float(f["stepSize"])
                precision = int(round(-math.log10(step)))
                return math.floor(quantity * 10**precision) / 10**precision
        return quantity

    def round_price(self, symbol: str, price: float) -> float:
        """Round *price* to the symbol's PRICE_FILTER tick size."""
        info = self.get_symbol_info(symbol)
        for f in info["filters"]:
            if f["filterType"] == "PRICE_FILTER":
                tick = float(f["tickSize"])
                precision = int(round(-math.log10(tick)))
                return round(price, precision)
        return price

    # -- Retry logic -----------------------------------------------------------

    @staticmethod
    def _retry(func, *args, max_retries: int = _MAX_RETRIES, **kwargs):
        """Call *func* with exponential backoff on retryable errors."""
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except BinanceAPIException as e:
                if e.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    delay = _RETRY_DELAY_S * (2 ** attempt)
                    logger.warning(
                        "Binance %d -- retrying in %ds (attempt %d/%d)",
                        e.status_code, delay, attempt + 1, max_retries,
                    )
                    time.sleep(delay)
                else:
                    raise
