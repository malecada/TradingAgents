"""Live trading configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LiveConfig:
    live_mode: bool
    binance_api_key: str
    binance_api_secret: str
    binance_base_url: str
    coinmetrics_api_key: str
    telegram_bot_token: str
    telegram_chat_id: str
    max_leverage: float
    max_daily_loss_pct: float
    stop_loss_pct: float
    max_open_positions: int
    target_vol: float
    kelly_fraction: float
    vol_lookback: int
    vol_cap_pct: float
    confidence_ref_return: float
    early_exit_loss: float
    min_hold: int
    trend_sma: int
    trend_multiplier: float
    horizons: list[int]
    symmetric: bool
    arima_filter: bool
    initial_capital: float
    coin_universe: list[str]
    signal_threshold: float = 0.0  # not used by V2 (kept for back-compat)


def _required(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise ValueError(f"Required env var {name} is not set")
    return val


def _bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


def _float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    return float(raw) if raw else default


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    return int(raw) if raw else default


def load_config() -> LiveConfig:
    cfg = LiveConfig(
        live_mode=_bool("LIVE_MODE", "false"),
        binance_api_key=_required("BINANCE_API_KEY"),
        binance_api_secret=_required("BINANCE_API_SECRET"),
        binance_base_url=os.environ.get("BINANCE_BASE_URL", "https://testnet.binancefuture.com"),
        coinmetrics_api_key=os.environ.get("COINMETRICS_API_KEY", ""),
        telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
        max_leverage=_float("MAX_LEVERAGE", 3.0),
        max_daily_loss_pct=_float("MAX_DAILY_LOSS_PCT", 0.15),
        stop_loss_pct=_float("STOP_LOSS_PCT", 0.03),
        max_open_positions=_int("MAX_OPEN_POSITIONS", 3),
        target_vol=_float("TARGET_VOL", 0.10),
        kelly_fraction=_float("KELLY_FRACTION", 0.5),
        vol_lookback=_int("VOL_LOOKBACK", 20),
        vol_cap_pct=_float("VOL_CAP_PCT", 0.95),
        confidence_ref_return=_float("CONFIDENCE_REF_RETURN", 0.02),
        early_exit_loss=_float("EARLY_EXIT_LOSS", 0.015),
        min_hold=_int("MIN_HOLD", 7),
        trend_sma=_int("TREND_SMA", 30),
        trend_multiplier=_float("TREND_MULTIPLIER", 1.5),
        horizons=[int(x) for x in os.environ.get("HORIZONS", "7,14").split(",") if x.strip()],
        symmetric=_bool("SYMMETRIC", "true"),
        arima_filter=_bool("ARIMA_FILTER", "false"),
        initial_capital=_float("INITIAL_CAPITAL", 10000.0),
        coin_universe=[c.strip() for c in os.environ.get("COIN_UNIVERSE", "BTC,ETH,BNB").split(",") if c.strip()],
    )
    if cfg.max_leverage <= 0:
        raise ValueError(f"MAX_LEVERAGE must be > 0, got {cfg.max_leverage}")
    if cfg.max_daily_loss_pct <= 0 or cfg.max_daily_loss_pct >= 1:
        raise ValueError(f"MAX_DAILY_LOSS_PCT must be in (0, 1), got {cfg.max_daily_loss_pct}")
    return cfg
