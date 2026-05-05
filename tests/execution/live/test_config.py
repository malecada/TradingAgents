import os
import pytest


@pytest.fixture
def env_vars(monkeypatch):
    monkeypatch.setenv("LIVE_MODE", "false")
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_API_SECRET", "s")
    monkeypatch.setenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("MAX_LEVERAGE", "3.0")
    monkeypatch.setenv("MAX_DAILY_LOSS_PCT", "0.15")
    monkeypatch.setenv("STOP_LOSS_PCT", "0.03")
    monkeypatch.setenv("MAX_OPEN_POSITIONS", "3")
    monkeypatch.setenv("TARGET_VOL", "0.10")
    monkeypatch.setenv("KELLY_FRACTION", "0.5")
    monkeypatch.setenv("VOL_LOOKBACK", "20")
    monkeypatch.setenv("VOL_CAP_PCT", "0.95")
    monkeypatch.setenv("CONFIDENCE_REF_RETURN", "0.02")
    monkeypatch.setenv("EARLY_EXIT_LOSS", "0.015")
    monkeypatch.setenv("MIN_HOLD", "7")
    monkeypatch.setenv("TREND_SMA", "30")
    monkeypatch.setenv("TREND_MULTIPLIER", "1.5")
    monkeypatch.setenv("HORIZONS", "7,14")
    monkeypatch.setenv("SYMMETRIC", "true")
    monkeypatch.setenv("ARIMA_FILTER", "false")
    monkeypatch.setenv("INITIAL_CAPITAL", "10000")
    monkeypatch.setenv("COIN_UNIVERSE", "bitcoin,ethereum,binancecoin")


def test_load_returns_typed_config(env_vars):
    from tradingagents.execution.live.config import load_config

    cfg = load_config()
    assert cfg.live_mode is False
    assert cfg.binance_api_key == "k"
    assert cfg.max_leverage == 3.0
    assert cfg.horizons == [7, 14]
    assert cfg.symmetric is True
    assert cfg.coin_universe == ["bitcoin", "ethereum", "binancecoin"]
    assert cfg.initial_capital == 10000.0


def test_to_binance_symbol_maps_known_coins():
    from tradingagents.execution.live.config import to_binance_symbol
    assert to_binance_symbol("bitcoin") == "BTCUSDT"
    assert to_binance_symbol("ethereum") == "ETHUSDT"
    assert to_binance_symbol("binancecoin") == "BNBUSDT"


def test_to_binance_symbol_falls_back_to_uppercase():
    from tradingagents.execution.live.config import to_binance_symbol
    assert to_binance_symbol("dogecoin") == "DOGECOINUSDT"


def test_missing_required_raises(monkeypatch):
    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_API_SECRET", raising=False)
    from tradingagents.execution.live.config import load_config

    with pytest.raises(ValueError, match="BINANCE_API_KEY"):
        load_config()


def test_validate_rejects_negative_leverage(env_vars, monkeypatch):
    monkeypatch.setenv("MAX_LEVERAGE", "-1")
    from tradingagents.execution.live.config import load_config

    with pytest.raises(ValueError, match="MAX_LEVERAGE"):
        load_config()
