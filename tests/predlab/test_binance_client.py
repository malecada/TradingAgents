import hashlib
import hmac
import urllib.parse

import pytest

from tradingagents.predlab.binance_client import BinanceAPIError, FuturesClient


@pytest.fixture
def client():
    return FuturesClient(api_key="k", api_secret="s")


class TestSigning:
    def test_signature_is_hmac_sha256_of_query(self, client):
        params = {"symbol": "BTCUSDT", "timestamp": 1000}
        signed = client._sign(dict(params))
        q = urllib.parse.urlencode(params)
        expected = hmac.new(b"s", q.encode(), hashlib.sha256).hexdigest()
        assert signed["signature"] == expected


class TestEndpoints:
    def test_equity_parses_total_margin_balance(self, client, monkeypatch):
        monkeypatch.setattr(client, "_http",
                            lambda m, p, params, signed: {"totalMarginBalance": "3010.55"})
        assert client.equity() == 3010.55

    def test_positions_nonzero_signed(self, client, monkeypatch):
        rows = [{"symbol": "AAAUSDT", "positionAmt": "50"},
                {"symbol": "BBBUSDT", "positionAmt": "-1.5"},
                {"symbol": "CCCUSDT", "positionAmt": "0"}]
        monkeypatch.setattr(client, "_http", lambda m, p, params, signed: rows)
        assert client.positions() == {"AAAUSDT": 50.0, "BBBUSDT": -1.5}

    def test_market_order_params(self, client, monkeypatch):
        captured = {}

        def fake(method, path, params, signed):
            captured.update(method=method, path=path, params=params, signed=signed)
            return {"orderId": 1, "avgPrice": "2.0",
                    "executedQty": "50", "cumQuote": "100"}

        monkeypatch.setattr(client, "_http", fake)
        r = client.market_order("AAAUSDT", "SELL", 50.0, reduce_only=True)
        assert captured["method"] == "POST"
        assert captured["path"] == "/fapi/v1/order"
        assert captured["params"]["type"] == "MARKET"
        assert captured["params"]["reduceOnly"] == "true"
        assert captured["params"]["quantity"] == "50"
        assert captured["params"]["newOrderRespType"] == "RESULT"
        assert captured["signed"] is True
        assert r["orderId"] == 1

    def test_qty_formatting_no_scientific_notation(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            client, "_http",
            lambda m, p, params, signed: captured.update(params=params) or {})
        client.market_order("BTCUSDT", "BUY", 0.001, reduce_only=False)
        assert captured["params"]["quantity"] == "0.001"

    def test_error_raises(self, client, monkeypatch):
        def boom(m, p, params, signed):
            raise BinanceAPIError(-4164, "Order's notional must be no smaller...")
        monkeypatch.setattr(client, "_http", boom)
        with pytest.raises(BinanceAPIError):
            client.market_order("AAAUSDT", "BUY", 1.0, reduce_only=False)
