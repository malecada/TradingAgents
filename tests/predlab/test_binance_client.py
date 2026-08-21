import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
from io import BytesIO
from unittest.mock import MagicMock, patch

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


class TestHTTPTransport:
    """Direct tests of _http() retry logic, error handling, and signing."""

    def test_5xx_retry_then_success(self, client):
        """5xx on first attempt → 2s backoff → 2nd attempt succeeds."""
        call_count = [0]

        def urlopen_side_effect(req, timeout):
            call_count[0] += 1
            if call_count[0] == 1:
                # First attempt: 500 error
                resp = MagicMock()
                resp.read.return_value = b'{"code": 500, "msg": "Service Unavailable"}'
                raise urllib.error.HTTPError(req.full_url, 500, "Server Error", {}, resp)
            else:
                # Second attempt: success
                return MagicMock(__enter__=lambda s: s, __exit__=lambda s, *a: None,
                                read=lambda: json.dumps({"result": "ok"}).encode())

        with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
            with patch("time.sleep") as mock_sleep:
                result = client._http("GET", "/fapi/v1/test", {}, signed=False)
                assert result == {"result": "ok"}
                assert call_count[0] == 2
                mock_sleep.assert_called_once_with(2)

    def test_4xx_no_retry_raises_error(self, client):
        """4xx error → immediate BinanceAPIError, no retry."""
        call_count = [0]

        def urlopen_side_effect(req, timeout):
            call_count[0] += 1
            resp = MagicMock()
            resp.read.return_value = b'{"code": -4164, "msg": "Order notional must be..."}'
            raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {}, resp)

        with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
            with patch("time.sleep") as mock_sleep:
                with pytest.raises(BinanceAPIError) as exc_info:
                    client._http("POST", "/fapi/v1/order", {}, signed=False)
                assert exc_info.value.code == -4164
                assert "Order notional" in exc_info.value.msg
                assert call_count[0] == 1
                mock_sleep.assert_not_called()

    def test_non_dict_json_error_body_raises_error(self, client):
        """Non-dict JSON error (e.g., array) → BinanceAPIError, not AttributeError."""
        def urlopen_side_effect(req, timeout):
            resp = MagicMock()
            # Binance returns valid JSON but not a dict
            resp.read.return_value = b'["error", "details"]'
            raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {}, resp)

        with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
            with pytest.raises(BinanceAPIError) as exc_info:
                client._http("GET", "/fapi/v1/test", {}, signed=False)
            assert exc_info.value.code == 400
            # Should fall back to raw body string when err.get() fails
            assert "error" in exc_info.value.msg

    def test_signed_get_includes_timestamp_recvwindow_signature(self, client):
        """Signed GET request URL contains timestamp, recvWindow=10000, and signature."""
        captured_req = []

        def urlopen_side_effect(req, timeout):
            captured_req.append(req)
            mock_resp = MagicMock(__enter__=lambda s: s, __exit__=lambda s, *a: None)
            mock_resp.read.return_value = b'{"data": "ok"}'
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
            with patch("time.time", return_value=1000.0):  # Fixed timestamp for reproducibility
                client._http("GET", "/fapi/v1/test", {"symbol": "BTCUSDT"}, signed=True)

        assert len(captured_req) == 1
        req = captured_req[0]
        url = req.full_url

        # URL should contain query string with timestamp, recvWindow, and signature
        assert "timestamp=1000000" in url
        assert "recvWindow=10000" in url
        assert "signature=" in url
        assert "symbol=BTCUSDT" in url

    def test_urlerror_retry_then_success(self, client):
        """URLError on first attempt → 2s backoff → 2nd attempt succeeds."""
        call_count = [0]

        def urlopen_side_effect(req, timeout):
            call_count[0] += 1
            if call_count[0] == 1:
                raise urllib.error.URLError("Connection timeout")
            else:
                mock_resp = MagicMock(__enter__=lambda s: s, __exit__=lambda s, *a: None)
                mock_resp.read.return_value = json.dumps({"status": "ok"}).encode()
                return mock_resp

        with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
            with patch("time.sleep") as mock_sleep:
                result = client._http("GET", "/fapi/v1/test", {}, signed=False)
                assert result == {"status": "ok"}
                assert call_count[0] == 2
                mock_sleep.assert_called_once_with(2)

    def test_urlerror_no_retry_on_second_attempt(self, client):
        """URLError on 2nd attempt is not retried."""
        call_count = [0]

        def urlopen_side_effect(req, timeout):
            call_count[0] += 1
            if call_count[0] == 1:
                raise urllib.error.URLError("First timeout")
            else:
                raise urllib.error.URLError("Second timeout")

        with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
            with patch("time.sleep"):
                with pytest.raises(urllib.error.URLError):
                    client._http("GET", "/fapi/v1/test", {}, signed=False)
                assert call_count[0] == 2

    def test_post_request_body_urlencoded(self, client):
        """POST requests send URL-encoded data in body, not query string."""
        captured_req = []

        def urlopen_side_effect(req, timeout):
            captured_req.append(req)
            mock_resp = MagicMock(__enter__=lambda s: s, __exit__=lambda s, *a: None)
            mock_resp.read.return_value = b'{"orderId": 1}'
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
            client._http("POST", "/fapi/v1/order", {"symbol": "BTCUSDT", "side": "BUY"},
                        signed=False)

        req = captured_req[0]
        # POST should have data in body
        assert req.data is not None
        assert b"symbol=BTCUSDT" in req.data
        assert b"side=BUY" in req.data
        # Query string should be in URL
        assert "?" not in req.full_url or req.full_url.endswith("?")

    def test_api_key_header_set_when_present(self, client):
        """X-MBX-APIKEY header is set when api_key is provided."""
        captured_req = []

        def urlopen_side_effect(req, timeout):
            captured_req.append(req)
            mock_resp = MagicMock(__enter__=lambda s: s, __exit__=lambda s, *a: None)
            mock_resp.read.return_value = b'{"data": "ok"}'
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
            client._http("GET", "/fapi/v1/test", {}, signed=False)

        req = captured_req[0]
        # HTTP headers are case-insensitive; urllib normalizes to lowercase
        assert any(k.lower() == "x-mbx-apikey" for k in req.headers)
        assert req.headers.get("X-mbx-apikey") == "k" or req.headers.get("X-MBX-APIKEY") == "k"

    def test_api_key_header_not_set_when_empty(self, client, monkeypatch):
        """X-MBX-APIKEY header is omitted when api_key is empty."""
        monkeypatch.setenv("BINANCE_API_KEY", "")
        monkeypatch.setenv("BINANCE_API_SECRET", "")
        empty_client = FuturesClient(api_key="", api_secret="")

        captured_req = []

        def urlopen_side_effect(req, timeout):
            captured_req.append(req)
            mock_resp = MagicMock(__enter__=lambda s: s, __exit__=lambda s, *a: None)
            mock_resp.read.return_value = b'{"data": "ok"}'
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
            empty_client._http("GET", "/fapi/v1/test", {}, signed=False)

        req = captured_req[0]
        # X-MBX-APIKEY should not be in headers when api_key is empty
        assert "X-MBX-APIKEY" not in req.headers
