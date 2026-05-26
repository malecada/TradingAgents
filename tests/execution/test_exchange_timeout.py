"""Unit tests for Binance -1007 reconciliation in place_market_order / place_stop_loss.

-1007 = "Timeout waiting for response from backend server; execution status
unknown." We CAN'T blind-retry — risks double-fill. The reconcile path queries
userTrades + openOrders to determine actual state, then:
- filled → success (synth envelope)
- open   → cancel + raise (don't double up)
- not    → retry once; second -1007 → raise BinanceOrderTimeoutUnknown
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest


def _make_api_exc(message: str, code: int = -1007, status_code: int = 504):
    """Construct a BinanceAPIException without hitting the network."""
    from binance.exceptions import BinanceAPIException

    exc = BinanceAPIException.__new__(BinanceAPIException)
    exc.status_code = status_code
    exc.code = code
    exc.message = message
    exc.response = None
    exc.request = None
    return exc


@pytest.fixture
def ex(monkeypatch):
    """ExchangeClient with the underlying python-binance client fully mocked."""
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_API_SECRET", "s")
    monkeypatch.setattr("tradingagents.execution.exchange.time.sleep",
                        lambda *_: None)  # skip the 3s reconcile sleep
    from tradingagents.execution.exchange import ExchangeClient

    client = ExchangeClient(api_key="k", api_secret="s", testnet=True)
    client._client = MagicMock()
    # Default: symbol info lookup is a no-op (we pass already-rounded qtys).
    client._symbol_info_cache["BTCUSDT"] = {
        "symbol": "BTCUSDT",
        "filters": [
            {"filterType": "LOT_SIZE", "stepSize": "0.00001"},
            {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
        ],
    }
    return client


def test_timeout_then_fill_found_returns_synthesized_envelope(ex):
    """-1007 raised, but Binance actually filled the order → treat as success."""
    timeout = _make_api_exc("APIError(code=-1007): Timeout waiting for backend")
    ex._client.futures_create_order.side_effect = timeout
    ex._client.futures_account_trades.return_value = [
        {"orderId": 999, "side": "SELL", "qty": "0.0168", "price": "77000.0",
         "time": int(time.time() * 1000)},
    ]
    ex._client.futures_get_open_orders.return_value = []

    result = ex.place_market_order("BTCUSDT", "SELL", 0.0168)
    assert result["status"] == "FILLED"
    assert result["orderId"] == 999
    assert result["_reconciled"] is True
    # Critical: only ONE create_order attempt — we did NOT retry after fill.
    assert ex._client.futures_create_order.call_count == 1


def test_timeout_then_open_order_cancels_and_raises(ex):
    """-1007 raised, order resting on book → cancel + raise (don't double up)."""
    from tradingagents.execution.exchange import BinanceOrderTimeoutUnknown

    timeout = _make_api_exc("APIError(code=-1007): timeout")
    ex._client.futures_create_order.side_effect = timeout
    ex._client.futures_account_trades.return_value = []
    ex._client.futures_get_open_orders.return_value = [
        {"orderId": 1234, "side": "SELL", "type": "MARKET",
         "origQty": "0.0168"},
    ]

    with pytest.raises(BinanceOrderTimeoutUnknown) as exc_info:
        ex.place_market_order("BTCUSDT", "SELL", 0.0168)

    assert exc_info.value.state == "open_order_canceled"
    ex._client.futures_cancel_order.assert_called_once()
    cancel_kwargs = ex._client.futures_cancel_order.call_args.kwargs
    assert cancel_kwargs["orderId"] == 1234


def test_timeout_not_placed_retries_once_and_succeeds(ex):
    """-1007 once + reconcile = not_placed → retry succeeds → return real order."""
    timeout = _make_api_exc("APIError(code=-1007): timeout")
    success = {"orderId": 5555, "symbol": "BTCUSDT", "status": "FILLED",
               "side": "SELL", "origQty": "0.0168", "avgPrice": "77100"}
    ex._client.futures_create_order.side_effect = [timeout, success]
    ex._client.futures_account_trades.return_value = []
    ex._client.futures_get_open_orders.return_value = []

    result = ex.place_market_order("BTCUSDT", "SELL", 0.0168)
    assert result["orderId"] == 5555
    assert ex._client.futures_create_order.call_count == 2


def test_double_1007_raises_BinanceOrderTimeoutUnknown(ex):
    """Two consecutive -1007s with no reconciled state → raise to runner."""
    from tradingagents.execution.exchange import BinanceOrderTimeoutUnknown

    timeout = _make_api_exc("APIError(code=-1007): timeout")
    ex._client.futures_create_order.side_effect = [timeout, timeout]
    ex._client.futures_account_trades.return_value = []
    ex._client.futures_get_open_orders.return_value = []

    with pytest.raises(BinanceOrderTimeoutUnknown) as exc_info:
        ex.place_market_order("BTCUSDT", "SELL", 0.0168)

    assert exc_info.value.state == "unknown"
    assert exc_info.value.symbol == "BTCUSDT"
    assert exc_info.value.side == "SELL"
    assert ex._client.futures_create_order.call_count == 2


def test_non_1007_error_does_not_trigger_reconcile(ex):
    """A regular Binance error (e.g. -2010 insufficient balance) must NOT
    consult userTrades/openOrders — reconcile is -1007-specific."""
    err = _make_api_exc("APIError(code=-2010): insufficient balance",
                        code=-2010, status_code=400)
    ex._client.futures_create_order.side_effect = err

    from binance.exceptions import BinanceAPIException
    with pytest.raises(BinanceAPIException):
        ex.place_market_order("BTCUSDT", "SELL", 0.0168)

    ex._client.futures_account_trades.assert_not_called()
    ex._client.futures_get_open_orders.assert_not_called()


def test_place_stop_loss_timeout_with_resting_order_is_success(ex):
    """For STOP_MARKET, an already-resting open order IS the desired end state."""
    timeout = _make_api_exc("APIError(code=-1007): timeout")
    ex._client.futures_create_order.side_effect = timeout
    ex._client.futures_account_trades.return_value = []
    ex._client.futures_get_open_orders.return_value = [
        {"orderId": 7777, "side": "SELL", "type": "STOP_MARKET",
         "origQty": "0.0168"},
    ]

    result = ex.place_stop_loss("BTCUSDT", 0.0168, stop_price=75000, side="SELL")
    assert result["orderId"] == 7777
    # Critical: do NOT cancel the resting stop — that would leave the position unprotected.
    ex._client.futures_cancel_order.assert_not_called()
