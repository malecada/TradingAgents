"""Binance Futures (USDT-M) client wrapper with testnet default and retry logic.

Ported from Krypto-v0's ``src_live/exchange.py`` and adapted for TradingAgents.
Reads configuration from ``get_config().get("execution", {})``, and API
credentials from environment variables ``BINANCE_API_KEY`` / ``BINANCE_API_SECRET``.
"""

from __future__ import annotations

import math
import os
import re
import time
import logging
from typing import Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException

from tradingagents.dataflows.config import get_config

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAY_S = 2  # exponential backoff base

# Match "banned until <ms-timestamp>" anywhere in the -1003 message body.
_BAN_UNTIL_RE = re.compile(r"banned until (\d{10,16})")


class BinanceIPBan(Exception):
    """Raised when Binance returns -1003 (IP banned). Carries ban-expiry epoch (ms).

    The retry loop does NOT retry on this — repeated requests during a ban
    extend the cooldown. Callers (e.g. runner.run_cycle) catch this, alert,
    and exit cleanly so systemd does not enter a restart loop.
    """

    def __init__(self, until_ms: int, raw_message: str = ""):
        self.until_ms = int(until_ms)
        self.raw_message = raw_message
        self.seconds_remaining = max(0.0, self.until_ms / 1000.0 - time.time())
        super().__init__(
            f"Binance IP banned until {self.until_ms} "
            f"(~{self.seconds_remaining:.0f}s remaining): {raw_message}"
        )


class BinanceOrderTimeoutUnknown(Exception):
    """Raised on -1007 when reconciliation can't determine if order landed.

    Binance -1007 "Timeout waiting for response from backend server" carries
    EXPLICITLY unknown execution status — the order may or may not have been
    placed. Blind retry risks double-fill. After this exception is raised,
    a human MUST verify position state before the next cycle places more
    orders for the same symbol; the runner emits a RECONCILE_NEEDED alert.

    `state` ∈ {"unknown", "open_order_canceled"}:
      - "unknown": reconciliation found neither fill nor open order, but
        repeated -1007 prevents safe retry.
      - "open_order_canceled": an order was placed and was still open;
        reconciliation canceled it. Treat as "not filled, do not retry".
    """

    def __init__(self, symbol: str, side: str, qty: float,
                 state: str = "unknown", raw_message: str = ""):
        self.symbol = symbol
        self.side = side
        self.qty = float(qty)
        self.state = state
        self.raw_message = raw_message
        super().__init__(
            f"Binance order timeout ({state}): {side} {symbol} qty={qty} — "
            f"{raw_message}"
        )


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

    def _reconcile_after_timeout(
        self, symbol: str, side: str, qty: float, since_ms: int,
        order_type: str = "MARKET", stop_price: float | None = None,
    ) -> tuple[str, dict | None]:
        """Determine actual order state after a -1007 timeout.

        Returns ``(state, payload)`` where ``state`` ∈
        ``{"filled", "open", "not_placed"}``:

        - ``filled``: a recent fill matches ``side`` + ``qty`` for ``symbol``.
          ``payload`` is a synthesized order envelope carrying the matched
          ``orderId``, ``status="FILLED"``, ``avgPrice``, and ``origQty`` so
          callers can treat the timeout as a successful placement.
        - ``open``: an order is still resting on the book matching ``side`` +
          ``qty``. ``payload`` is the open-order dict (caller may cancel).
        - ``not_placed``: neither fill nor open order found → safe to retry.

        ``since_ms`` filters userTrades + openOrders lookups to the window the
        runner cares about (typically ``timeout - 5min``). A 3s pre-query
        sleep gives the exchange's matching engine time to settle.
        """
        time.sleep(3)
        qty_tol = max(qty * 1e-4, 1e-8)

        # 1. Fills first — if a trade landed, treat as success.
        try:
            trades = self._client.futures_account_trades(
                symbol=symbol, startTime=int(since_ms),
            )
            for t in trades:
                if (t.get("side") == side
                        and abs(float(t.get("qty", 0)) - qty) <= qty_tol):
                    return ("filled", {
                        "orderId": t.get("orderId"),
                        "symbol": symbol,
                        "side": side,
                        "status": "FILLED",
                        "origQty": str(qty),
                        "executedQty": str(t.get("qty")),
                        "avgPrice": str(t.get("price")),
                        "_reconciled": True,
                    })
        except Exception as e:  # noqa: BLE001 — reconciliation must not raise
            logger.warning("Reconcile fills query failed for %s: %s", symbol, e)

        # 2. Open orders — order placed but not yet filled.
        try:
            open_orders = self._client.futures_get_open_orders(symbol=symbol)
            for o in open_orders:
                if (o.get("side") == side
                        and o.get("type") == order_type
                        and abs(float(o.get("origQty", 0)) - qty) <= qty_tol):
                    return ("open", o)
        except Exception as e:  # noqa: BLE001
            logger.warning("Reconcile open-orders query failed for %s: %s",
                           symbol, e)

        return ("not_placed", None)

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reduce_only: bool = False,
    ) -> dict:
        """Place a futures MARKET order.  *side* is ``'BUY'`` or ``'SELL'``.

        When *reduce_only* is True, the order is constrained to reduce or
        close the existing position. Binance allows below-min-notional
        orders only when this flag is set.

        On Binance -1007 (timeout, execution status unknown) this method
        runs :meth:`_reconcile_after_timeout`, treats a matched fill as
        success, retries once if reconciliation confirms "not placed",
        and raises :class:`BinanceOrderTimeoutUnknown` only when state
        cannot be resolved (an open order is canceled in that path so the
        next cycle starts from a known state).
        """
        quantity = self.round_quantity(symbol, quantity)
        logger.info(
            "FUTURES MARKET %s %s qty=%.8f%s",
            side, symbol, quantity, " reduceOnly" if reduce_only else "",
        )
        kwargs = dict(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity,
        )
        if reduce_only:
            kwargs["reduceOnly"] = "true"

        since_ms = int(time.time() * 1000) - 60_000  # 1-min lookback
        for attempt in range(2):
            try:
                return self._retry(self._client.futures_create_order, **kwargs)
            except BinanceAPIException as e:
                if getattr(e, "code", None) != -1007 and "-1007" not in str(e):
                    raise
                logger.warning(
                    "-1007 on %s %s qty=%s (attempt %d/2); reconciling…",
                    side, symbol, quantity, attempt + 1,
                )
                state, payload = self._reconcile_after_timeout(
                    symbol, side, quantity, since_ms, order_type="MARKET",
                )
                if state == "filled":
                    logger.info("Reconcile: %s %s qty=%s already FILLED "
                                "(orderId=%s)", side, symbol, quantity,
                                payload.get("orderId"))
                    return payload
                if state == "open":
                    logger.warning("Reconcile: %s %s qty=%s open on book; "
                                   "canceling for safety", side, symbol, quantity)
                    try:
                        self._client.futures_cancel_order(
                            symbol=symbol, orderId=payload["orderId"],
                        )
                    except Exception as cancel_err:  # noqa: BLE001
                        logger.error("Cancel of stranded order %s failed: %s",
                                     payload.get("orderId"), cancel_err)
                    raise BinanceOrderTimeoutUnknown(
                        symbol=symbol, side=side, qty=quantity,
                        state="open_order_canceled", raw_message=str(e),
                    )
                # state == "not_placed" → safe to retry once.
                if attempt == 0:
                    continue
                raise BinanceOrderTimeoutUnknown(
                    symbol=symbol, side=side, qty=quantity,
                    state="unknown", raw_message=str(e),
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

        Same -1007 reconciliation as :meth:`place_market_order`.
        """
        stop_price = self.round_price(symbol, stop_price)
        quantity = self.round_quantity(symbol, quantity)
        logger.info(
            "FUTURES STOP_MARKET %s %s qty=%.8f stop=%.2f",
            symbol, side, quantity, stop_price,
        )
        kwargs = dict(
            symbol=symbol,
            side=side,
            type="STOP_MARKET",
            stopPrice=str(stop_price),
            quantity=quantity,
            reduceOnly="true",
        )

        since_ms = int(time.time() * 1000) - 60_000
        for attempt in range(2):
            try:
                return self._retry(self._client.futures_create_order, **kwargs)
            except BinanceAPIException as e:
                if getattr(e, "code", None) != -1007 and "-1007" not in str(e):
                    raise
                logger.warning(
                    "-1007 on STOP %s %s qty=%s (attempt %d/2); reconciling…",
                    side, symbol, quantity, attempt + 1,
                )
                state, payload = self._reconcile_after_timeout(
                    symbol, side, quantity, since_ms,
                    order_type="STOP_MARKET", stop_price=stop_price,
                )
                if state == "filled":
                    return payload
                if state == "open":
                    # Stop already on book — that's the intended end state.
                    logger.info("Reconcile: STOP %s %s already resting "
                                "(orderId=%s)", side, symbol,
                                payload.get("orderId"))
                    return payload
                if attempt == 0:
                    continue
                raise BinanceOrderTimeoutUnknown(
                    symbol=symbol, side=side, qty=quantity,
                    state="unknown", raw_message=str(e),
                )

    def get_user_trades(self, symbol: str, order_id) -> list[dict]:
        """Return Binance Futures fills for one order (`/fapi/v1/userTrades`).

        Each fill carries `commission` (with `commissionAsset`) and
        `realizedPnl` which the placement response does NOT include. The
        live runner calls this immediately after a successful
        :meth:`place_market_order` and feeds the summed values into
        ``journal.update_trade_fills`` so `trades.fees` + `trades.pnl`
        stop being NULL.

        `order_id` may be ``str`` (the journal stores it as text) or ``int``.
        """
        return list(self._retry(
            self._client.futures_account_trades,
            symbol=symbol, orderId=int(order_id),
        ))

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
        """Call *func* with exponential backoff on retryable errors.

        On Binance error -1003 (IP banned, HTTP 418/429 + "banned until ..."),
        parse the ban-expiry timestamp and raise BinanceIPBan immediately
        without retrying — additional requests during a ban extend it.
        """
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except BinanceAPIException as e:
                if getattr(e, "code", None) == -1003 or "-1003" in str(e):
                    m = _BAN_UNTIL_RE.search(str(e))
                    if m:
                        raise BinanceIPBan(until_ms=int(m.group(1)), raw_message=str(e))
                    # -1003 without parsable timestamp: still surface as ban.
                    raise BinanceIPBan(until_ms=0, raw_message=str(e))
                # -1007 "execution status unknown" is NOT safely retryable by
                # _retry — bubble it to the caller (place_market_order /
                # place_stop_loss) which runs reconciliation before deciding
                # whether to retry. HTTP 504 alone (without -1007) is safe.
                if getattr(e, "code", None) == -1007 or "-1007" in str(e):
                    raise
                if e.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    delay = _RETRY_DELAY_S * (2 ** attempt)
                    logger.warning(
                        "Binance %d -- retrying in %ds (attempt %d/%d)",
                        e.status_code, delay, attempt + 1, max_retries,
                    )
                    time.sleep(delay)
                else:
                    raise
