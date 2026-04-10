"""Backtesting module for TradingAgents.

Provides a realistic backtesting engine that works with TradingAgents'
5-level signal output (BUY / OVERWEIGHT / HOLD / UNDERWEIGHT / SELL)
and includes transaction costs, slippage, and short borrowing fees.

Example usage::

    from tradingagents.backtesting import (
        run_backtest,
        FiveLevelSignal,
        ThresholdSignal,
        ModelConsensus,
    )

    strategy = FiveLevelSignal()
    result = run_backtest(
        dates=dates_series,
        actuals=price_array,
        agent_signals=signals_list,
        strategy=strategy,
        ticker="BTC",
    )
    print(result.metrics)
"""

from tradingagents.backtesting.engine import (
    BacktestResult,
    TradeRecord,
    compute_metrics,
    run_backtest,
)
from tradingagents.backtesting.strategies import (
    FiveLevelSignal,
    ModelConsensus,
    Signal,
    SignalLevel,
    SIGNAL_POSITION_MAP,
    Strategy,
    ThresholdSignal,
)

__all__ = [
    # Engine
    "BacktestResult",
    "TradeRecord",
    "compute_metrics",
    "run_backtest",
    # Strategies
    "FiveLevelSignal",
    "ModelConsensus",
    "Signal",
    "SignalLevel",
    "SIGNAL_POSITION_MAP",
    "Strategy",
    "ThresholdSignal",
]
