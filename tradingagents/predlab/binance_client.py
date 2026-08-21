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


class BinanceAPIError(Exception):
    def __init__(self, code: int, msg: str):
        super().__init__(f"binance error {code}: {msg}")
        self.code = code
        self.msg = msg


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
        if signed:
            params = dict(params, timestamp=int(time.time() * 1000),
                          recvWindow=10000)
            params = self._sign(params)
        query = urllib.parse.urlencode(params)
        url = f"{self.base}{path}"
        data = None
        if method == "GET":
            url = f"{url}?{query}" if query else url
        else:
            data = query.encode()
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={"X-MBX-APIKEY": self.api_key} if self.api_key else {})
        for attempt in (1, 2):
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")
                if 500 <= e.code < 600 and attempt == 1:
                    time.sleep(2)
                    continue
                try:
                    err = json.loads(body)
                    raise BinanceAPIError(err.get("code", e.code),
                                          err.get("msg", body)) from None
                except (ValueError, KeyError):
                    raise BinanceAPIError(e.code, body) from None
            except urllib.error.URLError:
                if attempt == 1:
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

    def market_order(self, symbol: str, side: str, qty: float,
                     reduce_only: bool) -> dict:
        params = {"symbol": symbol, "side": side, "type": "MARKET",
                  "quantity": _fmt(qty), "newOrderRespType": "RESULT"}
        if reduce_only:
            params["reduceOnly"] = "true"
        return self._http("POST", "/fapi/v1/order", params, signed=True)

    def user_trades(self, symbol: str, order_id: int) -> "list[dict]":
        return self._http("GET", "/fapi/v1/userTrades",
                          {"symbol": symbol, "orderId": order_id}, signed=True)
