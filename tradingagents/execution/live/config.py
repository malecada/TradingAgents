"""Live trading configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


# CoinGecko id → Binance base symbol. The model code uses CoinGecko ids
# (`bitcoin`, `ethereum`, `binancecoin`); the exchange uses Binance bases
# (`BTC`, `ETH`, `BNB`) plus the `USDT` quote suffix.
_COIN_TO_BINANCE_BASE = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "binancecoin": "BNB",
    "solana": "SOL",
}


# V5 MIX per-coin feature-set routing (validated in THESIS_FINDINGS §17/§20).
# BTC and BNB use the canonical 78-feature set; ETH and SOL use the extended
# 193-feature set. The `pool` lists the coins included in each coin's
# training universe (2+1 pattern for altcoins).
_V5_DEFAULT_ROUTING: dict[str, dict[str, object]] = {
    "bitcoin":     {"feature_set": "78f",  "pool": ["bitcoin", "ethereum"]},
    "ethereum":    {"feature_set": "193f", "pool": ["bitcoin", "ethereum"]},
    "binancecoin": {"feature_set": "78f",  "pool": ["bitcoin", "ethereum", "binancecoin"]},
    "solana":      {"feature_set": "193f", "pool": ["bitcoin", "ethereum", "solana"]},
}


def to_binance_symbol(coin_id: str) -> str:
    """Convert a CoinGecko coin id to its Binance Futures USDT-pair symbol.

    Falls back to upper-casing the id if the coin is not in the known map —
    callers passing already-base-cased symbols (e.g. `BTC`) get `BTCUSDT`.
    """
    base = _COIN_TO_BINANCE_BASE.get(coin_id.lower(), coin_id.upper())
    return f"{base}USDT"


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
    # V5 routing fields (Task 3 — V5 MIX live deployment)
    routing: dict[str, dict[str, object]] = field(default_factory=dict)
    coinglass_api_key: str = ""
    data_refresh_critical: set[str] = field(default_factory=set)
    data_root: str = "data"
    signal_threshold: float = 0.0  # not used by V2 (kept for back-compat)

    @classmethod
    def from_env(cls) -> "LiveConfig":
        """Load `LiveConfig` from environment variables (V5-aware).

        Thin alias for `load_config()` — V5 callers (retrain, predict,
        parity_refetch_and_replay) use this name to signal they expect the
        V5 routing/coinglass/data_root fields to be populated.
        """
        return load_config()


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
    coinglass_api_key = os.environ.get("COINGLASS_API_KEY", "").strip()
    if not coinglass_api_key:
        raise RuntimeError(
            "COINGLASS_API_KEY env var required for V5 live deployment "
            "(193f-routed coins depend on Coinglass refresh)"
        )

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
        kelly_fraction=_float("KELLY_FRACTION", 0.25),
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
        coin_universe=[c.strip() for c in os.environ.get(
            "COIN_UNIVERSE", "bitcoin,ethereum,binancecoin,solana").split(",") if c.strip()],
        routing=_V5_DEFAULT_ROUTING,
        coinglass_api_key=coinglass_api_key,
        data_refresh_critical={"ohlcv", "coinmetrics"},
        data_root=os.environ.get("TRADINGAGENTS_DATA_ROOT", "data"),
    )
    if cfg.max_leverage <= 0:
        raise ValueError(f"MAX_LEVERAGE must be > 0, got {cfg.max_leverage}")
    if cfg.max_daily_loss_pct <= 0 or cfg.max_daily_loss_pct >= 1:
        raise ValueError(f"MAX_DAILY_LOSS_PCT must be in (0, 1), got {cfg.max_daily_loss_pct}")
    return cfg
