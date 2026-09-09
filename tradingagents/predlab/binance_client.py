"""Minimal signed REST client for Binance USDT-M futures (stdlib only).

Only the six endpoints the S1 live executor needs. All HTTP funnels
through _http() so unit tests can stub the network entirely.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


class BinanceAPIError(Exception):
    def __init__(self, code: int, msg: str, *, execution_unknown: bool = False):
        super().__init__(f"binance error {code}: {msg}")
        self.code = code
        self.msg = msg
        self.execution_unknown = execution_unknown


def _fmt(x: float) -> str:
    """Decimal string without scientific notation or trailing zeros."""
    return f"{x:.10f}".rstrip("0").rstrip(".")


class FuturesClient:
    def __init__(self, api_key: "str | None" = None,
                 api_secret: "str | None" = None,
                 base: str = "https://fapi.binance.com"):
        self.api_key = api_key or os.environ.get("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("BINANCE_API_SECRET", "")
        self.base = base

    # -- transport ---------------------------------------------------------
    def _sign(self, params: dict) -> dict:
        params["signature"] = hmac.new(
            self.api_secret.encode(),
            urllib.parse.urlencode(params).encode(),
            hashlib.sha256).hexdigest()
        return params

    def _http(self, method: str, path: str, params: dict, signed: bool) -> dict:
        for attempt in (1, 2):
            # Rebuild request on each attempt to get fresh timestamps/signatures
            request_params = dict(params)
            if signed:
                request_params = dict(request_params,
                                      timestamp=int(time.time() * 1000),
                                      recvWindow=10000)
                request_params = self._sign(request_params)
            query = urllib.parse.urlencode(request_params)
            url = f"{self.base}{path}"
            data = None
            if method == "GET":
                url = f"{url}?{query}" if query else url
            else:
                data = query.encode()
            req = urllib.request.Request(
                url, data=data, method=method,
                headers={"X-MBX-APIKEY": self.api_key} if self.api_key else {})
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")
                if method == "GET" and 500 <= e.code < 600 and attempt == 1:
                    time.sleep(2)
                    continue
                try:
                    err = json.loads(body)
                    raise BinanceAPIError(err.get("code", e.code),
                                          err.get("msg", body),
                                          execution_unknown=(method != "GET" and (e.code >= 500 or err.get("code") in (-1000, -1001, -1006, -1007)))) from None
                except (ValueError, AttributeError, TypeError):
                    raise BinanceAPIError(e.code, body, execution_unknown=method != "GET" and e.code >= 500) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if method == "GET" and attempt == 1:
                    time.sleep(2)
                    continue
                raise

    # -- endpoints ---------------------------------------------------------
    def exchange_info(self) -> dict:
        return self._http("GET", "/fapi/v1/exchangeInfo", {}, signed=False)

    def equity(self) -> float:
        acct = self._http("GET", "/fapi/v2/account", {}, signed=True)
        return float(acct["totalMarginBalance"])

    def positions(self) -> "dict[str, float]":
        rows = self._http("GET", "/fapi/v2/positionRisk", {}, signed=True)
        return {r["symbol"]: float(r["positionAmt"])
                for r in rows if float(r["positionAmt"]) != 0.0}

    def set_leverage(self, symbol: str, leverage: int) -> None:
        self._http("POST", "/fapi/v1/leverage",
                   {"symbol": symbol, "leverage": leverage}, signed=True)

    def position_mode(self) -> bool:
        """True if the account is in hedge (dual-side position) mode.

        The live executor assumes one-way mode (net position per symbol,
        reduceOnly semantics as used throughout diff_orders); hedge mode
        must be rejected before any order is placed.
        """
        r = self._http("GET", "/fapi/v1/positionSide/dual", {}, signed=True)
        v = r.get("dualSidePosition")
        if isinstance(v, bool):
            return v
        if isinstance(v, str) and v.lower() in ("true", "false"):
            return v.lower() == "true"
        raise ValueError("position mode unavailable or invalid")

    def market_order(self, symbol: str, side: str, qty: float,
                     reduce_only: bool, client_order_id: str | None = None) -> dict:
        params = {"symbol": symbol, "side": side, "type": "MARKET",
                  "quantity": _fmt(qty), "newOrderRespType": "RESULT",
                  "newClientOrderId": client_order_id or "s1-" + uuid.uuid4().hex}
        if reduce_only:
            params["reduceOnly"] = "true"
        return self._http("POST", "/fapi/v1/order", params, signed=True)

    def order_status(self, symbol: str, client_order_id: str) -> dict:
        """Lookup even completed orders by the persisted client intent ID."""
        return self._http("GET", "/fapi/v1/order",
                          {"symbol": symbol, "origClientOrderId": client_order_id}, signed=True)

    def book_ticker(self) -> list[dict]:
        """Best bid/ask with exchange event time; missing time is not fresh."""
        return self._http("GET", "/fapi/v1/ticker/bookTicker", {}, signed=False)

    def user_trades(self, symbol: str, order_id: int) -> "list[dict]":
        return self._http("GET", "/fapi/v1/userTrades",
                          {"symbol": symbol, "orderId": order_id}, signed=True)
