# Agent Backtest V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full agent-pipeline backtest that reuses the V2 baseline's sizing, risk, and cost layer so LLM agent signals can be compared head-to-head with the quant baseline under identical conditions.

**Architecture:** Two components. (1) `generate_system_signals_v2()` in `tradingagents/backtesting/runner.py` — iterates propagate() over a date range per coin, extracts 5-level signal + confidence (HIGH/MEDIUM/LOW parsed from trader output), caches to CSV per-coin. (2) `scripts/backtest_system_v2.py` — reads the signals CSV, maps 5-level→continuous position with confidence scaling, then applies the **exact V2 baseline pipeline**: vol targeting + Kelly + conditional leverage + SMA30 trend filter + adaptive hold + stop-loss + circuit breaker + realistic costs. Produces per-coin and portfolio metrics in the same format as `baseline_strategy_v2.py`.

**Tech Stack:** Python 3.10, pandas, numpy, matplotlib, LangGraph (via `TradingAgentsGraph`), OpenAI/Anthropic LLMs (via replay cache).

---

## File Structure

| Action | Path | Responsibility |
|--------|------|---------------|
| Modify | `tradingagents/backtesting/runner.py` | Add `generate_system_signals_v2()` — multi-coin, per-coin CSV caching, confidence extraction |
| Modify | `tradingagents/graph/signal_processing.py` | Add `extract_confidence()` method to parse HIGH/MEDIUM/LOW from trader output |
| Create | `scripts/backtest_system_v2.py` | CLI script — loads agent signals, applies full V2 baseline sizing/risk/cost, generates reports |
| Create | `scripts/generate_agent_signals.py` | Thin CLI wrapper that just generates + caches signals (separate from backtest so signal generation can be run/resumed independently of backtest parameter tuning) |

The agent signal generation (expensive, ~$10-50 per 90-day run) is kept **separate from** the backtest strategy (free, parameter-tunable). Signals go to a CSV once; the strategy can be re-run with different params any time.

---

## Signal Format Specification

Per-coin CSV at `data/agent_signals/{coin}_{start}_{end}.csv`:

```
date,signal,confidence,trader_text
2024-05-01,BUY,HIGH,"Based on LGB h=7/h=14 consensus..."
2024-05-02,HOLD,LOW,"Horizons disagree..."
...
```

- `signal` ∈ {BUY, OVERWEIGHT, HOLD, UNDERWEIGHT, SELL}
- `confidence` ∈ {HIGH, MEDIUM, LOW, UNKNOWN}
- `trader_text` kept for audit/debugging (truncated to 500 chars)

---

## Position Mapping: Signal + Confidence → Continuous Position

Initial position comes from 5-level signal map (same as V1): BUY=+1.0, OVERWEIGHT=+0.5, HOLD=0, UNDERWEIGHT=-0.5, SELL=-1.0.

Confidence acts as a **multiplier** fed into the Kelly sizing pipeline as the `confidence` parameter (which `vol_targeted_size` already expects):
- HIGH → 1.0
- MEDIUM → 0.5
- LOW → 0.1 (small positions still allowed; can be zeroed via `--min-confidence`)
- UNKNOWN → 0.3 (default to medium-low for legacy cached signals without confidence)

Then the **exact V2 pipeline** runs: `vol_targeted_size` → `apply_leverage` → `build_positions_with_hold` (reusing existing functions by import) → `apply_trend_filter` → `run_coin_backtest`.

This means the agent backtest is strictly comparable to baseline V2: same vol target, same Kelly fraction, same max leverage, same trend filter, same costs.

---

### Task 1: Add `extract_confidence()` to SignalProcessor

**Files:**
- Modify: `tradingagents/graph/signal_processing.py`
- Test: `tests/graph/test_signal_processing_confidence.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/graph/test_signal_processing_confidence.py
from unittest.mock import MagicMock
from tradingagents.graph.signal_processing import SignalProcessor


def test_extract_confidence_high():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "HIGH"
    sp = SignalProcessor(mock_llm)
    assert sp.extract_confidence("FINAL TRANSACTION PROPOSAL: **BUY**\nConfidence: HIGH") == "HIGH"


def test_extract_confidence_unknown_when_not_mentioned():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "UNKNOWN"
    sp = SignalProcessor(mock_llm)
    assert sp.extract_confidence("Some text without confidence") == "UNKNOWN"


def test_extract_confidence_normalizes_whitespace_case():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "  medium  "
    sp = SignalProcessor(mock_llm)
    assert sp.extract_confidence("Some text ... Confidence: Medium ...") == "MEDIUM"


def test_extract_confidence_defaults_unknown_on_bad_llm_output():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "definitely not a valid label"
    sp = SignalProcessor(mock_llm)
    assert sp.extract_confidence("...") == "UNKNOWN"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/graph/test_signal_processing_confidence.py -v`
Expected: FAIL with `AttributeError: 'SignalProcessor' object has no attribute 'extract_confidence'`

- [ ] **Step 3: Implement `extract_confidence()`**

Append to `tradingagents/graph/signal_processing.py` (inside the `SignalProcessor` class):

```python
    def extract_confidence(self, full_signal: str) -> str:
        """Extract confidence label (HIGH/MEDIUM/LOW) from trader output.

        The trader prompt instructs the LLM to state confidence as HIGH /
        MEDIUM / LOW alongside its decision. This method uses the quick LLM
        to parse that label, returning 'UNKNOWN' when it cannot be found.

        Args:
            full_signal: Trader/portfolio-manager text that may contain a
                confidence label.

        Returns:
            One of {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}.
        """
        messages = [
            (
                "system",
                "You are an efficient assistant that extracts the confidence "
                "level from a trading decision text. The text may contain a "
                "label such as 'Confidence: HIGH' or 'HIGH confidence'. "
                "Return exactly one of: HIGH, MEDIUM, LOW, UNKNOWN. "
                "Return UNKNOWN if no confidence is mentioned or it is unclear. "
                "Output only the single word, nothing else.",
            ),
            ("human", full_signal),
        ]

        raw = self.quick_thinking_llm.invoke(messages).content
        cleaned = (raw or "").strip().upper()
        if cleaned in {"HIGH", "MEDIUM", "LOW"}:
            return cleaned
        return "UNKNOWN"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/graph/test_signal_processing_confidence.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tradingagents/graph/signal_processing.py tests/graph/test_signal_processing_confidence.py
git commit -m "feat: add extract_confidence() to SignalProcessor"
```

---

### Task 2: Expose confidence from `TradingAgentsGraph.propagate()`

**Files:**
- Modify: `tradingagents/graph/trading_graph.py`

- [ ] **Step 1: Inspect the current `propagate()` return**

Run: `grep -n "def propagate\|return .*signal\|process_signal" /home/malecada/master_thesis/TradingAgents/tradingagents/graph/trading_graph.py | head -20`
Expected: shows the `propagate()` method signature and where `process_signal()` is called.

- [ ] **Step 2: Add a new `propagate_with_confidence()` method**

Locate the existing `propagate()` method (around line 211) and add this method **directly after** it (do NOT modify the existing `propagate` — keeping it backward-compatible):

```python
    def propagate_with_confidence(self, company_name, trade_date):
        """Like `propagate()` but also returns a confidence label.

        Returns:
            (final_state, signal, confidence, trader_text) tuple where
            signal ∈ {BUY, OVERWEIGHT, HOLD, UNDERWEIGHT, SELL}
            confidence ∈ {HIGH, MEDIUM, LOW, UNKNOWN}
            trader_text is the raw final_trade_decision string for audit.
        """
        final_state, signal = self.propagate(company_name, trade_date)
        trader_text = final_state.get("final_trade_decision", "") or ""
        try:
            confidence = self.signal_processor.extract_confidence(trader_text)
        except Exception:
            confidence = "UNKNOWN"
        return final_state, signal, confidence, trader_text
```

- [ ] **Step 3: Syntax check**

Run: `python -c "import ast; ast.parse(open('tradingagents/graph/trading_graph.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tradingagents/graph/trading_graph.py
git commit -m "feat: add propagate_with_confidence() to TradingAgentsGraph"
```

---

### Task 3: Add `generate_system_signals_v2()` to runner

**Files:**
- Modify: `tradingagents/backtesting/runner.py`

- [ ] **Step 1: Add the new function**

Append this function to `tradingagents/backtesting/runner.py` (after the existing `generate_system_signals()`):

```python
def generate_system_signals_v2(
    coins: list[str],
    start_date: str,
    end_date: str,
    config: dict,
    selected_analysts: list[str] | None = None,
    output_dir: Path | str = Path("data/agent_signals"),
    force_rerun: bool = False,
) -> dict[str, pd.DataFrame]:
    """Generate per-coin agent signals with confidence over a date range.

    One CSV per coin at {output_dir}/{coin}_{start}_{end}.csv with columns:
    date, signal, confidence, trader_text.

    Loads from cache when the CSV exists and covers the requested range
    (unless force_rerun=True). Cache granularity is per coin, so adding a
    new coin only generates signals for that coin.

    Returns a dict mapping coin -> DataFrame.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Force the LLM replay cache — mandatory for determinism and cost control.
    config = config.copy()
    config["replay_cache"] = True

    from tradingagents.graph.trading_graph import TradingAgentsGraph
    analysts = selected_analysts or config.get(
        "selected_analysts", ["market", "onchain", "prediction"],
    )

    ta = TradingAgentsGraph(
        selected_analysts=analysts, debug=False, config=config,
    )

    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    results: dict[str, pd.DataFrame] = {}

    for coin in coins:
        csv_path = output_dir / f"{coin}_{start_date}_{end_date}.csv"

        # Try cache first
        if csv_path.exists() and not force_rerun:
            cached = pd.read_csv(csv_path, parse_dates=["date"])
            if len(cached) >= len(dates):
                logger.info(f"{coin}: loaded {len(cached)} cached signals from {csv_path}")
                results[coin] = cached
                continue

        logger.info(f"{coin}: generating signals for {len(dates)} dates")
        records = []
        for i, dt in enumerate(dates):
            date_str = dt.strftime("%Y-%m-%d")
            try:
                _, signal, confidence, trader_text = ta.propagate_with_confidence(
                    coin, date_str,
                )
            except Exception as e:
                logger.error(f"{coin} @ {date_str}: propagate failed: {e}")
                signal, confidence, trader_text = "HOLD", "UNKNOWN", f"ERROR: {e}"

            records.append({
                "date": dt,
                "signal": signal,
                "confidence": confidence,
                "trader_text": (trader_text or "")[:500],
            })

            # Checkpoint every 10 dates so a crash doesn't lose all progress
            if (i + 1) % 10 == 0 or (i + 1) == len(dates):
                pd.DataFrame(records).to_csv(csv_path, index=False)
                logger.info(f"{coin}: checkpoint {i + 1}/{len(dates)} -> {csv_path}")

        df = pd.DataFrame(records)
        df.to_csv(csv_path, index=False)
        logger.info(f"{coin}: saved {len(df)} signals to {csv_path}")
        results[coin] = df

    return results
```

- [ ] **Step 2: Syntax check**

Run: `python -c "import ast; ast.parse(open('tradingagents/backtesting/runner.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tradingagents/backtesting/runner.py
git commit -m "feat: add generate_system_signals_v2 for multi-coin agent backtest"
```

---

### Task 4: Create `scripts/generate_agent_signals.py` CLI

**Files:**
- Create: `scripts/generate_agent_signals.py`

- [ ] **Step 1: Create the script**

```python
#!/usr/bin/env python
"""Generate and cache agent signals for a coin list over a date range.

This is the expensive step (LLM calls). Runs separately from the backtest
so strategy parameters can be tuned without re-paying for signal generation.

Usage:
    # BTC+ETH, 90 days
    python scripts/generate_agent_signals.py \\
        --coins bitcoin ethereum \\
        --start 2024-05-01 --end 2024-08-01

    # Force regenerate (ignore cache)
    python scripts/generate_agent_signals.py \\
        --coins bitcoin --start 2024-05-01 --end 2024-05-10 --force
"""
from __future__ import annotations

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
        description="Generate agent signals over a date range (caches to CSV per coin).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--coins", nargs="+", required=True,
                    help="CoinGecko IDs (e.g. bitcoin ethereum binancecoin).")
    p.add_argument("--start", required=True, help="Start date YYYY-MM-DD.")
    p.add_argument("--end", required=True, help="End date YYYY-MM-DD.")
    p.add_argument("--analysts", nargs="+",
                    default=["market", "onchain", "prediction"],
                    help="Analyst types to include.")
    p.add_argument("--llm-provider", default="openai")
    p.add_argument("--deep-think", default="gpt-4o")
    p.add_argument("--quick-think", default="gpt-4o-mini")
    p.add_argument("--output-dir", default="data/agent_signals")
    p.add_argument("--force", action="store_true",
                    help="Ignore cached CSVs and regenerate.")
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    t0 = time.time()

    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.backtesting.runner import generate_system_signals_v2

    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = args.llm_provider
    config["deep_think_llm"] = args.deep_think
    config["quick_think_llm"] = args.quick_think
    config["asset_class"] = "crypto"
    config["replay_cache"] = True

    print(f"\n{'=' * 60}")
    print(f"  Agent Signal Generation")
    print(f"{'=' * 60}")
    print(f"  Coins     : {', '.join(args.coins)}")
    print(f"  Period    : {args.start} -> {args.end}")
    print(f"  Analysts  : {', '.join(args.analysts)}")
    print(f"  LLM       : {args.deep_think} / {args.quick_think}")
    print(f"  Force run : {args.force}")
    print(f"  Output    : {args.output_dir}")
    print()

    results = generate_system_signals_v2(
        coins=args.coins,
        start_date=args.start,
        end_date=args.end,
        config=config,
        selected_analysts=args.analysts,
        output_dir=Path(args.output_dir),
        force_rerun=args.force,
    )

    print(f"\n{'=' * 60}")
    print(f"  Summary")
    print(f"{'=' * 60}")
    for coin, df in results.items():
        sig_counts = df["signal"].value_counts().to_dict()
        conf_counts = df["confidence"].value_counts().to_dict()
        print(f"  {coin}: {len(df)} signals  signals={sig_counts}  conf={conf_counts}")

    print(f"\n  Runtime: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Syntax check**

Run: `python -c "import ast; ast.parse(open('scripts/generate_agent_signals.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/generate_agent_signals.py
git commit -m "feat: add CLI to generate & cache agent signals per coin"
```

---

### Task 5: Create `scripts/backtest_system_v2.py` CLI

**Files:**
- Create: `scripts/backtest_system_v2.py`

This script **reuses the baseline V2 pipeline** by importing its functions directly. The only difference is that signals come from agent CSVs instead of LGB predictions.

- [ ] **Step 1: Create the script**

```python
#!/usr/bin/env python
"""Agent Pipeline Backtest V2 — compares LLM agent signals against the V2 quant baseline.

Reuses the exact V2 sizing/risk/cost pipeline from baseline_strategy_v2:
- Vol targeting + half-Kelly + conditional leverage (1-3x)
- SMA30 trend filter (1.5x aligned / 0.5x against)
- 7-day min hold with adaptive early exit
- 3% per-trade stop-loss, 15% portfolio circuit breaker
- Realistic costs (fee, slippage, spread, price impact, funding)

Signals come from agent CSVs produced by `scripts/generate_agent_signals.py`.
The 5-level signal is mapped to +1/+0.5/0/-0.5/-1 and combined with the
confidence label (HIGH/MEDIUM/LOW) as the confidence input to Kelly sizing.

Usage:
    python scripts/backtest_system_v2.py \\
        --signals-dir data/agent_signals \\
        --coins bitcoin ethereum \\
        --start 2024-05-01 --end 2024-08-01
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Reuse V2 baseline components directly — DRY, same pipeline as our best quant baseline.
from scripts.baseline_strategy_v2 import (  # type: ignore
    compute_realized_vol,
    vol_regime_mask,
    build_positions_with_hold,
    apply_trend_filter,
    run_coin_backtest,
)

# Map 5-level signal string to base position weight (before Kelly/vol scaling).
SIGNAL_BASE_POSITION = {
    "BUY": 1.0,
    "OVERWEIGHT": 0.5,
    "HOLD": 0.0,
    "UNDERWEIGHT": -0.5,
    "SELL": -1.0,
}

# Map confidence label to [0, 1] multiplier used as the `confidence` parameter
# into vol_targeted_size (higher confidence -> larger vol-targeted position).
CONFIDENCE_MULTIPLIER = {
    "HIGH": 1.0,
    "MEDIUM": 0.5,
    "LOW": 0.1,
    "UNKNOWN": 0.3,
}


def load_signal_csv(signals_dir: Path, coin: str, start: str, end: str) -> pd.DataFrame:
    """Load the per-coin agent signal CSV produced by generate_agent_signals.py."""
    path = signals_dir / f"{coin}_{start}_{end}.csv"
    if not path.exists():
        # Try to find a compatible CSV (different date range that still covers ours)
        candidates = list(signals_dir.glob(f"{coin}_*.csv"))
        raise FileNotFoundError(
            f"Signals CSV not found: {path}\n"
            f"Available for {coin}: {[c.name for c in candidates]}\n"
            f"Generate with: python scripts/generate_agent_signals.py --coins {coin} "
            f"--start {start} --end {end}"
        )
    df = pd.read_csv(path, parse_dates=["date"])
    for col in ("signal", "confidence"):
        if col not in df.columns:
            raise ValueError(f"{path} missing column '{col}'")
    df = df.sort_values("date").reset_index(drop=True)
    return df


def signals_to_positions_v2(
    signals_df: pd.DataFrame,
    prices: np.ndarray,
    realized_vol: np.ndarray,
    vol_ok: np.ndarray,
    args,
) -> np.ndarray:
    """Convert 5-level agent signals + confidence to continuous positions.

    Produces raw signals (+1/0/-1) and per-bar confidence ∈ [0, 1], then
    feeds both into the V2 baseline's build_positions_with_hold (for min
    hold, adaptive exit) and apply_trend_filter (for SMA30 scaling).
    """
    n = len(signals_df)
    raw_signals = np.zeros(n)
    confidence = np.zeros(n)

    for i in range(n):
        sig_str = str(signals_df["signal"].iloc[i]).strip().upper()
        conf_str = str(signals_df["confidence"].iloc[i]).strip().upper()
        base_pos = SIGNAL_BASE_POSITION.get(sig_str, 0.0)
        conf_mult = CONFIDENCE_MULTIPLIER.get(conf_str, CONFIDENCE_MULTIPLIER["UNKNOWN"])

        # Respect --min-confidence filter
        if conf_str == "LOW" and args.drop_low_confidence:
            raw_signals[i] = 0.0
            confidence[i] = 0.0
            continue

        # raw_signals is a direction in {+1, 0, -1}; magnitude handled by conf*kelly*vol
        if base_pos > 0:
            raw_signals[i] = 1.0
        elif base_pos < 0:
            raw_signals[i] = -1.0
        else:
            raw_signals[i] = 0.0

        # OVERWEIGHT/UNDERWEIGHT halve the confidence to mirror their half-position intent
        if sig_str in ("OVERWEIGHT", "UNDERWEIGHT"):
            conf_mult *= 0.5

        confidence[i] = conf_mult

    positions = build_positions_with_hold(
        raw_signals, vol_ok, confidence, realized_vol, prices,
        target_vol=args.target_vol,
        kelly_fraction=args.kelly_fraction,
        max_leverage=args.max_leverage,
        min_hold=args.min_hold,
        early_exit_loss=args.early_exit_loss,
    )

    if args.trend_sma > 0:
        positions = apply_trend_filter(
            positions, prices, args.trend_sma, args.trend_multiplier,
        )

    return positions


def fetch_prices(coin: str, start: str, end: str) -> pd.DataFrame:
    """Fetch OHLCV via the cached vendor and return date-aligned close prices."""
    from tradingagents.models.model_utils import fetch_ohlcv_for_model
    lookback = (pd.to_datetime(end) - pd.to_datetime(start)).days + 30
    df = fetch_ohlcv_for_model(coin, lookback, trade_date=end)
    if df.empty:
        raise RuntimeError(f"No price data for {coin}")
    df = df.reset_index().rename(columns={"index": "date"})
    df["date"] = pd.to_datetime(df["date"])
    mask = (df["date"] >= pd.to_datetime(start)) & (df["date"] <= pd.to_datetime(end))
    return df.loc[mask, ["date", "prices"]].reset_index(drop=True)


def parse_args():
    p = argparse.ArgumentParser(
        description="Agent Pipeline Backtest V2 — same risk/cost pipeline as baseline V2.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--signals-dir", default="data/agent_signals",
                    help="Directory containing per-coin agent signal CSVs.")
    p.add_argument("--coins", nargs="+", required=True)
    p.add_argument("--start", required=True, help="Start date YYYY-MM-DD.")
    p.add_argument("--end", required=True, help="End date YYYY-MM-DD.")
    p.add_argument("--initial-capital", type=float, default=10_000.0)
    p.add_argument("--drop-low-confidence", action="store_true",
                    help="Zero out LOW-confidence signals (default keeps them at 0.1x).")

    # V2 pipeline params — IDENTICAL to baseline defaults for fair comparison
    p.add_argument("--min-hold", type=int, default=7)
    p.add_argument("--target-vol", type=float, default=0.10)
    p.add_argument("--vol-lookback", type=int, default=20)
    p.add_argument("--kelly-fraction", type=float, default=0.5)
    p.add_argument("--max-leverage", type=float, default=3.0)
    p.add_argument("--stop-loss", type=float, default=0.03)
    p.add_argument("--max-portfolio-dd", type=float, default=0.15)
    p.add_argument("--vol-cap-pct", type=float, default=0.95)
    p.add_argument("--early-exit-loss", type=float, default=0.015)
    p.add_argument("--trend-sma", type=int, default=30)
    p.add_argument("--trend-multiplier", type=float, default=1.5)

    # Cost params — IDENTICAL to baseline defaults
    p.add_argument("--fee-rate", type=float, default=0.001)
    p.add_argument("--slippage", type=float, default=0.001)
    p.add_argument("--spread", type=float, default=0.0005)
    p.add_argument("--price-impact", type=float, default=0.001)
    p.add_argument("--funding-rate", type=float, default=0.0001)

    p.add_argument("--output-dir", default="data/agent_backtest_v2")
    return p.parse_args()


def main():
    args = parse_args()
    t0 = time.time()
    signals_dir = Path(args.signals_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cost_kwargs = dict(
        fee_rate=args.fee_rate, slippage=args.slippage, spread=args.spread,
        price_impact=args.price_impact, funding_rate=args.funding_rate,
        stop_loss=args.stop_loss, max_portfolio_dd=args.max_portfolio_dd,
    )

    print(f"\n{'=' * 70}")
    print(f"  Agent Pipeline Backtest V2")
    print(f"{'=' * 70}")
    print(f"  Signals dir : {signals_dir}")
    print(f"  Coins       : {', '.join(args.coins)}")
    print(f"  Period      : {args.start} -> {args.end}")
    print(f"  Min hold    : {args.min_hold} days")
    print(f"  Trend SMA   : {args.trend_sma}d (x{args.trend_multiplier})")
    print(f"  Max lev     : {args.max_leverage}x")
    print(f"  Drop LOW    : {args.drop_low_confidence}")

    all_results = {}
    all_equity = {}
    all_bh = {}

    for coin in args.coins:
        # 1. Load signals
        signals_df = load_signal_csv(signals_dir, coin, args.start, args.end)

        # 2. Load prices and align
        prices_df = fetch_prices(coin, args.start, args.end)
        merged = signals_df.merge(prices_df, on="date", how="inner").sort_values("date")
        if len(merged) < 30:
            print(f"\n  {coin}: skipped (only {len(merged)} aligned rows)")
            continue

        dates = merged["date"].values
        prices = merged["prices"].values.astype(float)

        # 3. Volatility + regime
        realized_vol = compute_realized_vol(prices, args.vol_lookback)
        vol_ok = vol_regime_mask(realized_vol, args.vol_cap_pct)

        # 4. Signals -> positions via full V2 pipeline
        positions = signals_to_positions_v2(merged, prices, realized_vol, vol_ok, args)

        # 5. Backtest (reuses baseline's run_coin_backtest)
        equity, metrics = run_coin_backtest(
            dates, prices, positions,
            initial_capital=args.initial_capital,
            **cost_kwargs,
        )

        bh_ret = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
        all_results[coin] = metrics
        all_equity[coin] = equity
        all_bh[coin] = bh_ret

        sig_counts = merged["signal"].value_counts().to_dict()
        conf_counts = merged["confidence"].value_counts().to_dict()
        print(f"\n  {coin}: n={len(merged)}  sig={sig_counts}  conf={conf_counts}")
        print(f"    return={metrics['total_return']:+.2%}  sharpe={metrics['sharpe_ratio']:.2f}  "
              f"maxDD={metrics['max_drawdown']:.2%}  trades={metrics['n_trades']}  "
              f"B&H={bh_ret:+.2%}")

    # Per-coin table
    print(f"\n{'=' * 70}")
    print(f"  Per-Coin Results")
    print(f"{'=' * 70}")
    header = (f"{'Coin':<12s} {'Return':>10s} {'Ann.Ret':>10s} {'Sharpe':>8s} "
              f"{'MaxDD':>8s} {'WinRate':>8s} {'#Trades':>8s} {'vs B&H':>10s}")
    print(f"  {'-' * len(header)}")
    print(f"  {header}")
    print(f"  {'-' * len(header)}")
    for coin in args.coins:
        if coin not in all_results:
            continue
        m = all_results[coin]
        bh = all_bh[coin]
        print(f"  {coin:<12s} {m['total_return']:>+10.2%} {m['annualized_return']:>+10.2%} "
              f"{m['sharpe_ratio']:>8.2f} {m['max_drawdown']:>8.2%} "
              f"{m['win_rate']:>8.1%} {m['n_trades']:>8d} "
              f"{m['total_return'] - bh:>+10.2%}")

    # Portfolio
    if len(all_equity) > 1:
        min_len = min(len(eq) for eq in all_equity.values())
        port_equity = np.zeros(min_len)
        for eq in all_equity.values():
            port_equity += np.array(eq[:min_len])
        port_equity /= len(all_equity)
        port_return = (port_equity[-1] - args.initial_capital) / args.initial_capital
        port_daily = np.diff(port_equity) / port_equity[:-1]
        port_daily = port_daily[~np.isnan(port_daily)]
        daily_rf = (1 + 0.045) ** (1 / 252) - 1
        std_ex = np.std(port_daily - daily_rf, ddof=1) if len(port_daily) > 1 else 0
        port_sharpe = (float(np.mean(port_daily - daily_rf) / std_ex * np.sqrt(252))
                      if std_ex > 0 else 0)
        rm = np.maximum.accumulate(port_equity)
        port_dd = float(np.max(np.where(rm > 0, (rm - port_equity) / rm, 0)))
        print(f"\n  Portfolio ({len(all_equity)} coins): "
              f"return={port_return:+.2%}  sharpe={port_sharpe:.2f}  maxDD={port_dd:.2%}")

    # Plot + JSON
    plot_path = output_dir / f"agent_v2_equity_{args.start}_{args.end}.png"
    fig, ax = plt.subplots(figsize=(14, 7))
    for coin in args.coins:
        if coin not in all_equity:
            continue
        eq = all_equity[coin]
        dates_pd = pd.to_datetime(
            load_signal_csv(signals_dir, coin, args.start, args.end)["date"].values
        )
        n_plot = min(len(eq) - 1, len(dates_pd))
        ax.plot(dates_pd[:n_plot], eq[1:n_plot + 1], linewidth=1.4,
                label=f"{coin} ({all_results[coin]['total_return']:+.1%})")
    ax.axhline(y=args.initial_capital, color="gray", linestyle="--", alpha=0.5)
    ax.set_title("Agent Pipeline V2 — Equity Curves (per coin)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity (USD)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(str(plot_path), dpi=150)
    plt.close(fig)
    print(f"\n  Equity plot -> {plot_path}")

    json_path = output_dir / f"agent_v2_metrics_{args.start}_{args.end}.json"
    with open(json_path, "w") as f:
        json.dump({
            "coins": list(all_results.keys()),
            "period": {"start": args.start, "end": args.end},
            "metrics": {c: m for c, m in all_results.items()},
            "bh_returns": all_bh,
        }, f, indent=2, default=str)
    print(f"  Metrics JSON -> {json_path}")
    print(f"\n  Total runtime: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Syntax check**

Run: `python -c "import ast; ast.parse(open('scripts/backtest_system_v2.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/backtest_system_v2.py
git commit -m "feat: add backtest_system_v2 reusing baseline V2 pipeline with agent signals"
```

---

### Task 6: Smoke test end-to-end on 10-day BTC window

Uses a very short window so we can verify the full pipeline works without burning significant LLM cost. ~10 propagate() calls.

**Files:** none created/modified (verification only).

- [ ] **Step 1: Generate signals for 10 days**

Run:
```bash
cd /home/malecada/master_thesis/TradingAgents
python scripts/generate_agent_signals.py \
    --coins bitcoin \
    --start 2024-05-01 --end 2024-05-10
```
Expected:
- Creates `data/agent_signals/bitcoin_2024-05-01_2024-05-10.csv` with 10 rows.
- Each row has non-empty `signal` (one of BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL) and `confidence` (one of HIGH/MEDIUM/LOW/UNKNOWN).
- Summary prints signal+confidence counts.

- [ ] **Step 2: Verify CSV content**

Run: `head -3 data/agent_signals/bitcoin_2024-05-01_2024-05-10.csv`
Expected: header line + 2 data rows with columns `date,signal,confidence,trader_text`.

- [ ] **Step 3: Run backtest on the cached signals**

Run:
```bash
python scripts/backtest_system_v2.py \
    --coins bitcoin \
    --start 2024-05-01 --end 2024-05-10
```
Expected:
- Completes in under 30 seconds (no LLM calls — just loads CSV and runs the V2 pipeline).
- Prints per-coin results table and an equity plot path.
- Creates `data/agent_backtest_v2/agent_v2_equity_2024-05-01_2024-05-10.png`.
- Metrics JSON saved to `data/agent_backtest_v2/agent_v2_metrics_2024-05-01_2024-05-10.json`.

- [ ] **Step 4: Rerun backtest to confirm cache hit on signals**

Run the same `scripts/backtest_system_v2.py` command again.
Expected: identical output, still <30s (signals come from CSV, no LLM calls).

- [ ] **Step 5: Rerun signal generation to confirm LLM replay cache hit**

Run the same `scripts/generate_agent_signals.py` command again.
Expected:
- Log says "loaded N cached signals from data/agent_signals/bitcoin_..." (coverage cache hit) OR
- If running with `--force`, LLM replay cache provides identical signals free.

---

## Verification Summary

After all tasks:

1. **Unit tests pass**: `pytest tests/graph/test_signal_processing_confidence.py` — 4/4 passing.
2. **Syntax**: all modified/created files parse with `ast.parse`.
3. **Smoke run (10 days BTC)**: produces signals CSV + backtest output + equity plot in <2 minutes total (first run), <30s on warm caches.
4. **Comparable to baseline V2**: when run on the same BTC+ETH window, metrics (return, Sharpe, MaxDD) appear in the same format as `baseline_strategy_v2.py` output, enabling direct LLM-vs-baseline comparison for the thesis.

## Out of scope (future work)

- Full 12-month 2-coin BTC+ETH system backtest (expensive — estimate ~$30-50 of API calls; run once after verification passes).
- Hyperparameter tuning specifically for agent signals (min-hold, trend_sma may behave differently with 5-level agent signals vs LGB predictions).
- LLM-specific ablations (e.g. disable sentiment analyst, compare claude vs gpt-4o).
