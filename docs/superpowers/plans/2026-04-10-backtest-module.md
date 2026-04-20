# Backtest Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a complete backtest module supporting individual model walk-forward evaluation and full multi-agent system backtesting, with CLI scripts, strategy comparison, and result reporting.

**Architecture:** Two runners orchestrate existing components — `evaluate_models()` bridges `model_run()` functions that wrap existing `prepare_data()` + `walk_forward_evaluate()` in each model; `run_system_backtest()` loops `propagate()` over a date range with signal caching, then feeds to the existing `run_backtest()` engine. A separate reporting module handles tables, plots, and JSON export.

**Tech Stack:** Python 3.10+, matplotlib (already dep), pandas/numpy (already dep), prettytable (new dep)

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Modify | `tradingagents/models/rf_model.py` | Add `model_run()` bridge function |
| Modify | `tradingagents/models/arima_model.py` | Add `model_run()` bridge function |
| Modify | `tradingagents/models/onchain_model.py` | Add `model_run()` bridge function |
| Create | `tradingagents/backtesting/runner.py` | `evaluate_models()`, `generate_system_signals()`, `run_system_backtest()` |
| Create | `tradingagents/backtesting/reporting.py` | Summary table, equity curve plots, predictions plot, JSON export |
| Modify | `tradingagents/backtesting/__init__.py` | Export new modules |
| Create | `scripts/evaluate_models.py` | CLI for individual model evaluation |
| Create | `scripts/backtest_system.py` | CLI for full system backtest |

---

### Task 1: Add `model_run()` to RF model

**Files:**
- Modify: `tradingagents/models/rf_model.py` (append after line 320, after `walk_forward_evaluate`)

- [ ] **Step 1: Add `model_run()` function**

```python
def model_run(
    df_all: pd.DataFrame,
    min_train_window: int | None = None,
    save_checkpoint_flag: bool = False,
) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Orchestrate prepare -> walk-forward evaluate -> metrics for RF.

    Args:
        df_all: Date-indexed model DataFrame (output of ohlcv_to_model_df).
        min_train_window: Override for walk-forward training window.
        save_checkpoint_flag: Save model checkpoint after full retrain.

    Returns:
        (df_forecast, metrics, result_df) where:
        - df_forecast: full DataFrame with forecast row appended
        - metrics: {r2, mae, rmse, mape}
        - result_df: date-indexed DataFrame with 'prediction' and 'actual'
    """
    reframed_lags, df_final, first_day_future = prepare_data(df_all)

    predictions, actuals, window_start = walk_forward_evaluate(
        reframed_lags, min_train_window=min_train_window,
    )

    metrics = mu.compute_metrics(actuals, predictions)

    eval_dates = df_final.index[window_start: window_start + len(predictions)]
    result_df = pd.DataFrame(
        {"prediction": predictions, "actual": actuals},
        index=eval_dates,
    )
    result_df.index.name = "date"

    # Full retrain + one-step-ahead forecast
    prediction_obj = _forecast_from_df(df_all, save_checkpoint_flag=save_checkpoint_flag)
    df_forecast = df_final.copy()
    df_forecast.loc[df_forecast.index[-1], "prices"] = prediction_obj.value

    return df_forecast, metrics, result_df
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "import ast; ast.parse(open('tradingagents/models/rf_model.py').read()); print('OK')"`

---

### Task 2: Add `model_run()` to ARIMA model

**Files:**
- Modify: `tradingagents/models/arima_model.py` (append after line 348, after `walk_forward_evaluate`)

- [ ] **Step 1: Add `model_run()` function**

```python
def model_run(
    df_all: pd.DataFrame,
    min_train_window: int | None = None,
    save_checkpoint_flag: bool = False,
) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Orchestrate prepare -> walk-forward evaluate -> metrics for ARIMA.

    Returns:
        (df_forecast, metrics, result_df) — same contract as rf_model.model_run.
    """
    df_with_date, reframed_lags, df_final, first_day_future = prepare_data(df_all)

    predictions, actuals, window_start = walk_forward_evaluate(
        df_with_date, min_train_window=min_train_window,
    )

    metrics = mu.compute_metrics(actuals, predictions)

    eval_dates = df_with_date.index[window_start: window_start + len(predictions)]
    result_df = pd.DataFrame(
        {"prediction": predictions, "actual": actuals},
        index=eval_dates,
    )
    result_df.index.name = "date"

    prediction_obj = _forecast_from_df(df_all, save_checkpoint_flag=save_checkpoint_flag)
    df_forecast = df_final.copy()
    df_forecast.loc[df_forecast.index[-1], "prices"] = prediction_obj.value

    return df_forecast, metrics, result_df
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "import ast; ast.parse(open('tradingagents/models/arima_model.py').read()); print('OK')"`

---

### Task 3: Add `model_run()` to on-chain GBR model

**Files:**
- Modify: `tradingagents/models/onchain_model.py` (append after `walk_forward_evaluate`, before the end of file)

- [ ] **Step 1: Add `model_run()` function**

```python
def model_run(
    df_all: pd.DataFrame,
    min_train_window: int | None = None,
    save_checkpoint_flag: bool = False,
    symbol: str = "bitcoin",
    lookback_days: int = 300,
) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Orchestrate prepare -> walk-forward evaluate -> metrics for GBR.

    Optionally enriches with on-chain data before evaluation.

    Returns:
        (df_forecast, metrics, result_df) — same contract as rf_model.model_run.
    """
    # Enrich with on-chain features (degrades gracefully if unavailable)
    df_enriched = _enrich_with_onchain_data(df_all.copy(), symbol, lookback_days)

    reframed_lags, df_final, first_day_future = prepare_data(df_enriched)

    predictions, actuals, window_start = walk_forward_evaluate(
        reframed_lags, min_train_window=min_train_window,
    )

    metrics = mu.compute_metrics(actuals, predictions)

    eval_dates = df_final.index[window_start: window_start + len(predictions)]
    result_df = pd.DataFrame(
        {"prediction": predictions, "actual": actuals},
        index=eval_dates,
    )
    result_df.index.name = "date"

    prediction_obj = _forecast_from_df(df_enriched, save_checkpoint_flag=save_checkpoint_flag)
    df_forecast = df_final.copy()
    df_forecast.loc[df_forecast.index[-1], "prices"] = prediction_obj.value

    return df_forecast, metrics, result_df
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "import ast; ast.parse(open('tradingagents/models/onchain_model.py').read()); print('OK')"`

- [ ] **Step 3: Commit model_run additions**

```bash
git add tradingagents/models/rf_model.py tradingagents/models/arima_model.py tradingagents/models/onchain_model.py
git commit -m "feat: add model_run() bridge functions for walk-forward evaluation"
```

---

### Task 4: Create backtesting runner

**Files:**
- Create: `tradingagents/backtesting/runner.py`

- [ ] **Step 1: Create runner.py with `ModelEvalResult` and `evaluate_models()`**

```python
"""Backtest runners for individual models and full multi-agent system."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from tradingagents.backtesting.engine import BacktestResult, run_backtest
from tradingagents.backtesting.strategies import (
    FiveLevelSignal,
    ModelConsensus,
    ThresholdSignal,
)
from tradingagents.models import model_utils as mu

logger = logging.getLogger(__name__)


@dataclass
class ModelEvalResult:
    """Result container for a single model's walk-forward evaluation."""

    model_name: str
    metrics: dict
    result_df: pd.DataFrame
    forecast_df: Optional[pd.DataFrame] = None


def evaluate_models(
    coin: str,
    lookback_days: int = 730,
    trade_date: Optional[str] = None,
    min_train_window: Optional[int] = None,
    models: list[str] | tuple[str, ...] = ("rf", "arima"),
    output_dir: Path | str = Path("data"),
) -> dict[str, ModelEvalResult]:
    """Run walk-forward evaluation for specified prediction models.

    Args:
        coin: CoinGecko ID (e.g. "bitcoin").
        lookback_days: Historical data window.
        trade_date: Upper date bound (YYYY-MM-DD). None = today.
        min_train_window: Min training rows for walk-forward.
        models: Which models to evaluate ("rf", "arima", "gbr").
        output_dir: Where to save predictions CSV.

    Returns:
        Dict mapping model name to ModelEvalResult.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df_model = mu.fetch_ohlcv_for_model(coin, lookback_days, trade_date=trade_date)
    if df_model.empty:
        logger.error(f"No OHLCV data for {coin}")
        return {}

    logger.info(f"Fetched {len(df_model)} rows for {coin} (lookback={lookback_days})")

    results: dict[str, ModelEvalResult] = {}

    if "rf" in models:
        logger.info("Evaluating Random Forest...")
        from tradingagents.models.rf_model import model_run as rf_run

        df_fc, metrics, result_df = rf_run(df_model, min_train_window=min_train_window)
        results["rf"] = ModelEvalResult("RandomForest", metrics, result_df, df_fc)
        logger.info(f"RF: R²={metrics['r2']:.4f}  MAE={metrics['mae']:.2f}")

    if "arima" in models:
        logger.info("Evaluating ARIMA...")
        from tradingagents.models.arima_model import model_run as arima_run

        df_fc, metrics, result_df = arima_run(df_model, min_train_window=min_train_window)
        results["arima"] = ModelEvalResult("ARIMA", metrics, result_df, df_fc)
        logger.info(f"ARIMA: R²={metrics['r2']:.4f}  MAE={metrics['mae']:.2f}")

    if "gbr" in models:
        logger.info("Evaluating On-Chain GBR...")
        from tradingagents.models.onchain_model import model_run as gbr_run

        df_fc, metrics, result_df = gbr_run(
            df_model, min_train_window=min_train_window,
            symbol=coin, lookback_days=lookback_days,
        )
        results["gbr"] = ModelEvalResult("OnChainGBR", metrics, result_df, df_fc)
        logger.info(f"GBR: R²={metrics['r2']:.4f}  MAE={metrics['mae']:.2f}")

    # Save merged predictions CSV
    if results:
        frames = []
        for key, res in results.items():
            frame = res.result_df.rename(columns={
                "prediction": f"{key}_prediction",
                "actual": f"{key}_actual",
            })
            if hasattr(frame.index, "tz") and frame.index.tz is not None:
                frame.index = frame.index.tz_localize(None)
            frames.append(frame)

        df_out = frames[0]
        for f in frames[1:]:
            df_out = df_out.join(f, how="outer")

        csv_path = output_dir / "eval_predictions.csv"
        df_out.to_csv(csv_path)
        logger.info(f"Predictions saved -> {csv_path}")

    return results


def generate_system_signals(
    coin: str,
    start_date: str,
    end_date: str,
    config: dict,
    selected_analysts: list[str] | None = None,
    signals_csv: Optional[Path] = None,
) -> pd.DataFrame:
    """Generate agent signals for each date in range via propagate().

    If signals_csv exists and covers the requested range, loads from
    disk (saves $10-50 in LLM costs).

    Returns:
        DataFrame with columns: date, signal.
    """
    # Check for cached signals
    if signals_csv and Path(signals_csv).exists():
        df_cached = pd.read_csv(signals_csv, parse_dates=["date"])
        cached_start = df_cached["date"].min().strftime("%Y-%m-%d")
        cached_end = df_cached["date"].max().strftime("%Y-%m-%d")
        if cached_start <= start_date and cached_end >= end_date:
            logger.info(f"Loaded cached signals from {signals_csv}")
            mask = (df_cached["date"] >= start_date) & (df_cached["date"] <= end_date)
            return df_cached[mask].reset_index(drop=True)
        logger.info(f"Cache {signals_csv} doesn't cover requested range, regenerating")

    # Force replay cache for determinism and cost savings
    config = config.copy()
    config["replay_cache"] = True

    from tradingagents.graph.trading_graph import TradingAgentsGraph

    analysts = selected_analysts or config.get(
        "selected_analysts", ["market", "onchain", "prediction"]
    )

    ta = TradingAgentsGraph(
        selected_analysts=analysts,
        debug=False,
        config=config,
    )

    # Generate daily dates (calendar days — crypto trades 24/7)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    records = []
    for i, dt in enumerate(dates):
        date_str = dt.strftime("%Y-%m-%d")
        logger.info(f"[{i + 1}/{len(dates)}] Propagating {coin} @ {date_str}")
        try:
            _, signal = ta.propagate(coin, date_str)
            records.append({"date": dt, "signal": signal})
        except Exception as e:
            logger.error(f"propagate() failed for {date_str}: {e}")
            records.append({"date": dt, "signal": "HOLD"})

    df_signals = pd.DataFrame(records)

    # Save for reuse
    if signals_csv is None:
        signals_csv = Path("data") / f"system_signals_{coin}.csv"
    Path(signals_csv).parent.mkdir(parents=True, exist_ok=True)
    df_signals.to_csv(signals_csv, index=False)
    logger.info(f"Signals saved -> {signals_csv}")

    return df_signals


def run_system_backtest(
    coin: str,
    start_date: str,
    end_date: str,
    config: dict,
    selected_analysts: list[str] | None = None,
    signals_csv: Optional[Path] = None,
    initial_capital: float = 10_000.0,
    fee_rate: float = 0.001,
    slippage: float = 0.0005,
    short_cost: float = 0.0003,
    output_dir: Path | str = Path("data"),
) -> list[BacktestResult]:
    """Run full system backtest: generate signals, then evaluate strategies.

    Returns:
        List of BacktestResult (one per strategy).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Get signals
    df_signals = generate_system_signals(
        coin, start_date, end_date, config,
        selected_analysts=selected_analysts,
        signals_csv=signals_csv,
    )

    # Step 2: Get price data for the same range
    lookback = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 30
    df_prices = mu.fetch_ohlcv_for_model(coin, lookback, trade_date=end_date)
    if df_prices.empty:
        logger.error("No price data available")
        return []

    # Build price series aligned to signal dates
    price_df = pd.DataFrame({
        "date": df_prices.index,
        "close": df_prices["prices"].values,
    })
    price_df["date"] = pd.to_datetime(price_df["date"])

    df_signals["date"] = pd.to_datetime(df_signals["date"])
    merged = pd.merge(df_signals, price_df, on="date", how="inner").sort_values("date")

    if len(merged) < 2:
        logger.error(f"Only {len(merged)} dates after merge — need at least 2")
        return []

    dates = merged["date"]
    actuals = merged["close"].values
    signals = merged["signal"].tolist()

    # Step 3: Run each strategy
    strategies = [
        FiveLevelSignal(),
        ThresholdSignal(),
    ]

    results = []
    for strategy in strategies:
        result = run_backtest(
            dates=dates,
            actuals=actuals,
            agent_signals=signals,
            strategy=strategy,
            ticker=coin,
            initial_capital=initial_capital,
            fee_rate=fee_rate,
            slippage=slippage,
            short_cost=short_cost,
        )
        results.append(result)
        logger.info(
            f"{strategy.name}: return={result.metrics['total_return']:+.2%}  "
            f"sharpe={result.metrics['sharpe_ratio']:.2f}"
        )

    return results
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "import ast; ast.parse(open('tradingagents/backtesting/runner.py').read()); print('OK')"`

- [ ] **Step 3: Commit runner**

```bash
git add tradingagents/backtesting/runner.py
git commit -m "feat: add backtest runner with model eval and system backtest"
```

---

### Task 5: Create backtesting reporting module

**Files:**
- Create: `tradingagents/backtesting/reporting.py`

- [ ] **Step 1: Create reporting.py**

```python
"""Reporting utilities for backtest results: tables, plots, JSON export."""

import json
import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from tradingagents.backtesting.engine import BacktestResult

logger = logging.getLogger(__name__)


def print_model_metrics(model_name: str, metrics: dict) -> None:
    """Print regression metrics for a single model evaluation."""
    print(f"  {model_name:15s}  R²={metrics['r2']:.4f}  MAE={metrics['mae']:.2f}  "
          f"RMSE={metrics['rmse']:.2f}  MAPE={metrics['mape']:.4f}")


def print_summary_table(
    results: list[BacktestResult],
    buy_hold_return: Optional[float] = None,
) -> str:
    """Print a strategy comparison table. Returns the formatted string."""
    header = (
        f"{'Strategy':<20s} {'Tot.Ret.':>10s} {'Ann.Ret.':>10s} {'Sharpe':>8s} "
        f"{'MaxDD':>8s} {'WinRate':>8s} {'#Trades':>8s} {'PF':>8s}"
    )
    sep = "-" * len(header)
    lines = [sep, header, sep]

    for r in results:
        m = r.metrics
        pf = f"{m['profit_factor']:.2f}" if m["profit_factor"] != float("inf") else "inf"
        lines.append(
            f"{r.strategy_name:<20s} {m['total_return']:>+10.2%} "
            f"{m['annualized_return']:>+10.2%} {m['sharpe_ratio']:>8.2f} "
            f"{m['max_drawdown']:>8.2%} {m['win_rate']:>8.1%} "
            f"{m['n_trades']:>8d} {pf:>8s}"
        )

    if buy_hold_return is not None:
        lines.append(
            f"{'Buy & Hold':<20s} {buy_hold_return:>+10.2%} "
            f"{'':>10s} {'':>8s} {'':>8s} {'':>8s} {'':>8s} {'':>8s}"
        )

    lines.append(sep)
    table_str = "\n".join(lines)
    print(table_str)
    return table_str


def plot_equity_curves(
    results: list[BacktestResult],
    output_path: Path | str,
    initial_capital: float = 10_000.0,
) -> None:
    """Plot equity curves for all strategies on one figure."""
    fig, ax = plt.subplots(figsize=(14, 6))

    for r in results:
        dates = pd.to_datetime(r.dates)
        equity = r.equity_curve[1:]  # align with trade dates
        ax.plot(dates, equity, linewidth=1.5, label=r.strategy_name)

    ax.axhline(y=initial_capital, color="gray", linestyle=":", linewidth=1,
               label="Initial Capital")

    ax.set_title("Backtest Equity Curves")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity (USD)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(str(output_path), dpi=150)
    plt.close(fig)
    logger.info(f"Equity curve plot saved -> {output_path}")


def plot_predictions_vs_actuals(
    results: dict,
    output_path: Path | str,
) -> None:
    """Plot model predictions overlaid on actuals.

    Args:
        results: Dict mapping model key to ModelEvalResult.
        output_path: Path to save the plot PNG.
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    actuals_plotted = False

    for key, res in results.items():
        df = res.result_df
        idx = df.index
        if hasattr(idx, "tz") and idx.tz is not None:
            idx = idx.tz_localize(None)

        if not actuals_plotted and "actual" in df.columns:
            ax.plot(idx, df["actual"], color="tab:orange", linewidth=1.5, label="Actual")
            actuals_plotted = True

        ax.plot(idx, df["prediction"], linewidth=1.5, linestyle="--",
                label=f"{res.model_name} prediction")

    ax.set_title("Model Predictions vs Actuals")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    if hasattr(list(results.values())[0].result_df.index[0], "strftime"):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(str(output_path), dpi=150)
    plt.close(fig)
    logger.info(f"Predictions plot saved -> {output_path}")


def save_results_json(
    results: list[BacktestResult],
    output_path: Path | str,
    metadata: Optional[dict] = None,
) -> None:
    """Save backtest results to JSON for reproducibility."""
    data = {
        "metadata": metadata or {},
        "strategies": [],
    }
    for r in results:
        entry = {
            "strategy_name": r.strategy_name,
            "ticker": r.ticker,
            "metrics": r.metrics,
            "n_dates": len(r.dates),
            "date_range": {
                "start": str(r.dates[0]) if r.dates else None,
                "end": str(r.dates[-1]) if r.dates else None,
            },
        }
        data["strategies"].append(entry)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Results JSON saved -> {output_path}")
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "import ast; ast.parse(open('tradingagents/backtesting/reporting.py').read()); print('OK')"`

- [ ] **Step 3: Commit reporting**

```bash
git add tradingagents/backtesting/reporting.py
git commit -m "feat: add backtest reporting module with tables, plots, JSON export"
```

---

### Task 6: Update `__init__.py` exports

**Files:**
- Modify: `tradingagents/backtesting/__init__.py`

- [ ] **Step 1: Add new exports after existing ones**

Append after the existing `__all__` list:

```python
from tradingagents.backtesting.runner import (
    ModelEvalResult,
    evaluate_models,
    generate_system_signals,
    run_system_backtest,
)
from tradingagents.backtesting.reporting import (
    print_summary_table,
    plot_equity_curves,
    plot_predictions_vs_actuals,
    print_model_metrics,
    save_results_json,
)

__all__ += [
    # Runner
    "ModelEvalResult",
    "evaluate_models",
    "generate_system_signals",
    "run_system_backtest",
    # Reporting
    "print_summary_table",
    "plot_equity_curves",
    "plot_predictions_vs_actuals",
    "print_model_metrics",
    "save_results_json",
]
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "import ast; ast.parse(open('tradingagents/backtesting/__init__.py').read()); print('OK')"`

---

### Task 7: Create model evaluation CLI script

**Files:**
- Create: `scripts/evaluate_models.py`

- [ ] **Step 1: Create the script**

```python
#!/usr/bin/env python
"""Evaluate RF / ARIMA / GBR models via walk-forward and save dated predictions.

Usage:
    python scripts/evaluate_models.py --coin bitcoin --days 730
    python scripts/evaluate_models.py --coin bitcoin --days 365 --models rf arima
    python scripts/evaluate_models.py --coin ethereum --min-train 360
"""

import argparse
import logging
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="Maximum Likelihood optimization failed")
try:
    from statsmodels.tools.sm_exceptions import ConvergenceWarning
    warnings.filterwarnings("ignore", category=ConvergenceWarning)
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args():
    p = argparse.ArgumentParser(
        description="Evaluate prediction models via walk-forward backtesting.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--coin", required=True, help="CoinGecko ID, e.g. 'bitcoin'.")
    p.add_argument("--days", type=int, default=730, help="Lookback days for data.")
    p.add_argument("--trade-date", default=None, help="Upper date bound (YYYY-MM-DD).")
    p.add_argument("--models", nargs="+", default=["rf", "arima"],
                    choices=["rf", "arima", "gbr"], help="Models to evaluate.")
    p.add_argument("--min-train", type=int, default=None,
                    help="Min training window for walk-forward eval.")
    p.add_argument("--output-dir", default="data", help="Output directory.")
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    t0 = time.time()

    from tradingagents.backtesting.runner import evaluate_models
    from tradingagents.backtesting.reporting import (
        print_model_metrics,
        plot_predictions_vs_actuals,
    )

    output_dir = Path(args.output_dir)

    print(f"\n{'=' * 60}")
    print(f"  Model Evaluation: {args.coin} ({args.days} days)")
    print(f"{'=' * 60}\n")

    results = evaluate_models(
        coin=args.coin,
        lookback_days=args.days,
        trade_date=args.trade_date,
        min_train_window=args.min_train,
        models=args.models,
        output_dir=output_dir,
    )

    if not results:
        print("ERROR: No models evaluated successfully.")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  Walk-Forward Evaluation Results")
    print(f"{'=' * 60}")
    for key, res in results.items():
        print_model_metrics(res.model_name, res.metrics)

    # Plot predictions vs actuals
    plot_path = output_dir / "eval_predictions_plot.png"
    plot_predictions_vs_actuals(results, plot_path)
    print(f"\nPlot saved -> {plot_path}")

    # Summary
    csv_path = output_dir / "eval_predictions.csv"
    print(f"Predictions CSV -> {csv_path}")
    print(f"\nTotal runtime: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "import ast; ast.parse(open('scripts/evaluate_models.py').read()); print('OK')"`

---

### Task 8: Create system backtest CLI script

**Files:**
- Create: `scripts/backtest_system.py`

- [ ] **Step 1: Create the script**

```python
#!/usr/bin/env python
"""Run full multi-agent system backtest with strategy comparison.

Usage:
    # First run (expensive — generates signals via LLM calls):
    python scripts/backtest_system.py --coin bitcoin --start 2024-05-01 --end 2025-03-01

    # Reuse cached signals (free):
    python scripts/backtest_system.py --coin bitcoin --start 2024-05-01 --end 2025-03-01 \
        --signals-csv data/system_signals_bitcoin.csv
"""

import argparse
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args():
    p = argparse.ArgumentParser(
        description="Run multi-agent system backtest with strategy comparison.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--coin", required=True, help="CoinGecko ID.")
    p.add_argument("--start", required=True, help="Start date (YYYY-MM-DD).")
    p.add_argument("--end", required=True, help="End date (YYYY-MM-DD).")
    p.add_argument("--signals-csv", default=None, help="Pre-computed signals CSV.")
    p.add_argument("--analysts", nargs="+",
                    default=["market", "onchain", "prediction"],
                    help="Analyst types to include.")
    p.add_argument("--initial-capital", type=float, default=10_000.0)
    p.add_argument("--fee-rate", type=float, default=0.001)
    p.add_argument("--slippage", type=float, default=0.0005)
    p.add_argument("--short-cost", type=float, default=0.0003)
    p.add_argument("--llm-provider", default="openai")
    p.add_argument("--deep-think", default="gpt-4o")
    p.add_argument("--quick-think", default="gpt-4o-mini")
    p.add_argument("--output-dir", default="data")
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    t0 = time.time()

    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.backtesting.runner import run_system_backtest
    from tradingagents.backtesting.reporting import (
        print_summary_table,
        plot_equity_curves,
        save_results_json,
    )
    from tradingagents.models.model_utils import fetch_ohlcv_for_model

    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = args.llm_provider
    config["deep_think_llm"] = args.deep_think
    config["quick_think_llm"] = args.quick_think
    config["asset_class"] = "crypto"
    config["replay_cache"] = True

    output_dir = Path(args.output_dir)
    signals_csv = Path(args.signals_csv) if args.signals_csv else None

    print(f"\n{'=' * 60}")
    print(f"  System Backtest: {args.coin}")
    print(f"  Period: {args.start} -> {args.end}")
    print(f"  Analysts: {', '.join(args.analysts)}")
    print(f"  LLM: {args.deep_think} / {args.quick_think}")
    print(f"{'=' * 60}\n")

    results = run_system_backtest(
        coin=args.coin,
        start_date=args.start,
        end_date=args.end,
        config=config,
        selected_analysts=args.analysts,
        signals_csv=signals_csv,
        initial_capital=args.initial_capital,
        fee_rate=args.fee_rate,
        slippage=args.slippage,
        short_cost=args.short_cost,
        output_dir=output_dir,
    )

    if not results:
        print("ERROR: No backtest results produced.")
        sys.exit(1)

    # Buy & Hold benchmark
    lookback = (
        __import__("pandas").to_datetime(args.end)
        - __import__("pandas").to_datetime(args.start)
    ).days + 30
    df_prices = fetch_ohlcv_for_model(args.coin, lookback, trade_date=args.end)
    if not df_prices.empty:
        prices = df_prices["prices"]
        bh_return = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]
    else:
        bh_return = None

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Strategy Comparison")
    print(f"{'=' * 60}")
    print_summary_table(results, buy_hold_return=bh_return)

    print(f"\nCost assumptions:")
    print(f"  Fee per side   : {args.fee_rate:.2%}")
    print(f"  Slippage       : {args.slippage:.2%}")
    print(f"  Short cost/day : {args.short_cost:.2%}")

    n_days = len(results[0].dates) if results else 0
    if n_days < 100:
        print(f"\n  NOTE: Only {n_days} trading days. Annualized metrics may be unreliable.")

    # Plot
    plot_path = output_dir / f"backtest_equity_{args.coin}.png"
    plot_equity_curves(results, plot_path, args.initial_capital)
    print(f"Equity curve -> {plot_path}")

    # Save JSON
    json_path = output_dir / f"backtest_results_{args.coin}.json"
    save_results_json(results, json_path, metadata={
        "coin": args.coin, "start": args.start, "end": args.end,
        "analysts": args.analysts,
    })
    print(f"Results JSON -> {json_path}")

    print(f"\nTotal runtime: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "import ast; ast.parse(open('scripts/backtest_system.py').read()); print('OK')"`

- [ ] **Step 3: Commit CLI scripts**

```bash
git add scripts/evaluate_models.py scripts/backtest_system.py
git commit -m "feat: add CLI scripts for model evaluation and system backtesting"
```

---

### Task 9: Final commit and verify

- [ ] **Step 1: Commit all remaining changes**

```bash
git add tradingagents/backtesting/__init__.py
git commit -m "feat: export new backtest runner and reporting modules"
```

- [ ] **Step 2: Full syntax check**

```bash
python -c "
import ast
files = [
    'tradingagents/models/rf_model.py',
    'tradingagents/models/arima_model.py',
    'tradingagents/models/onchain_model.py',
    'tradingagents/backtesting/runner.py',
    'tradingagents/backtesting/reporting.py',
    'tradingagents/backtesting/__init__.py',
    'scripts/evaluate_models.py',
    'scripts/backtest_system.py',
]
for f in files:
    ast.parse(open(f).read())
    print(f'OK: {f}')
print('All files pass')
"
```

- [ ] **Step 3: Verify model eval works end-to-end**

Run: `python scripts/evaluate_models.py --coin bitcoin --days 365 --models rf`

Expected: Walk-forward evaluation completes, prints R²/MAE/RMSE/MAPE, saves CSV and plot to `data/`.

---

## Verification

1. **Model eval**: `python scripts/evaluate_models.py --coin bitcoin --days 365 --models rf arima` should produce `data/eval_predictions.csv` and `data/eval_predictions_plot.png`
2. **System backtest**: `python scripts/backtest_system.py --coin bitcoin --start 2024-05-01 --end 2024-06-01 --analysts market prediction` should generate signals, run strategies, print comparison table, save equity curve and JSON
3. **Signal reuse**: Running the system backtest a second time with `--signals-csv data/system_signals_bitcoin.csv` should skip propagate() and reuse cached signals
