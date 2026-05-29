"""C1 fix — LiveConfig must carry renormalized portfolio weights for the
active universe so the runner can weight per-coin sizing."""
import math


def _set_min_env(monkeypatch, universe="bitcoin,ethereum,binancecoin,solana"):
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_API_SECRET", "s")
    monkeypatch.setenv("COINGLASS_API_KEY", "c")
    monkeypatch.setenv("COIN_UNIVERSE", universe)


def test_load_config_max_portfolio_dd_default(monkeypatch):
    """L1: drawdown-from-peak halt threshold, default 0.15 (matches the
    backtest portfolio circuit breaker)."""
    _set_min_env(monkeypatch)
    from tradingagents.execution.live.config import load_config
    assert load_config().max_portfolio_dd == 0.15
    monkeypatch.setenv("MAX_PORTFOLIO_DD", "0.10")
    assert load_config().max_portfolio_dd == 0.10


def test_load_config_populates_renormalized_weights(monkeypatch):
    _set_min_env(monkeypatch)
    from tradingagents.execution.live.config import (
        load_config, compute_portfolio_weights,
    )
    cfg = load_config()
    assert cfg.portfolio_weights == compute_portfolio_weights(cfg.coin_universe)
    for coin in cfg.coin_universe:
        assert math.isclose(cfg.portfolio_weights[coin], 0.25, rel_tol=1e-9)
    assert math.isclose(sum(cfg.portfolio_weights.values()), 1.0, rel_tol=1e-9)
