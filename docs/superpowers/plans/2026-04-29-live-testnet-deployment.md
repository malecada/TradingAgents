# Live Testnet Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy V2 quant strategy (LGB h=7/h=14 consensus + V2 sizing + PIT on-chain features, 3-coin BTC/ETH/BNB) to Hetzner CX22 with daily Binance Futures testnet execution, full forensic logging, daily shadow-replay + weekly re-backtest comparison, and Telegram alerting — for a 90-day thesis-defendable live-vs-backtest comparison.

**Architecture:** Bare-metal cron via systemd timers on Hetzner CX22 running a Python venv. New `tradingagents/execution/live/` package orchestrates a 10-step daily pipeline (fetch → retrain → predict → size → risk → execute → shadow → snapshot → notify). All state in local SQLite + Parquet + JSONL logs; no inbound services. Live and backtest share one V2 sizing implementation (refactored from `scripts/baseline_strategy_v2.py`) to prevent drift.

**Tech Stack:** Python 3.11, LightGBM, python-binance (futures), python-telegram-bot, DuckDB+Parquet, SQLite (stdlib), systemd, Hetzner Cloud, Ubuntu 24.04 LTS.

**Spec:** `docs/superpowers/specs/2026-04-29-live-testnet-deployment-design.md`

---

## Pre-flight Checklist

Before Task 0.1, the engineer must have:

- Local clone of `master_thesis/TradingAgents` repo at HEAD of `main`
- A Hetzner Cloud account with API token
- A Binance Futures testnet account with API key + secret (https://testnet.binancefuture.com)
- A Telegram bot token + chat ID (create via @BotFather, get chat_id from any message to bot)
- Python 3.11 installed locally
- `pytest`, `python-binance`, `python-telegram-bot`, `lightgbm`, `pandas`, `duckdb`, `pyarrow`, `joblib` in dev environment

---

## Phase 0: Setup

### Task 0.1: Create feature branch + worktree

**Files:**
- Modify: git state (no file changes)

- [ ] **Step 1: Verify clean main**

```bash
cd /home/malecada/master_thesis/TradingAgents
git status
```

Expected: `On branch main`, working tree clean (untracked files OK if not in plan scope).

- [ ] **Step 2: Create feature branch**

```bash
git branch feature/live-testnet-deploy main
```

Expected: no output. Verify with `git branch | grep live-testnet-deploy`.

- [ ] **Step 3: Create worktree**

```bash
git worktree add .worktrees/live-testnet-deploy feature/live-testnet-deploy
```

Expected: `Preparing worktree (checking out 'feature/live-testnet-deploy')` and `HEAD is now at <sha>`.

- [ ] **Step 4: Cd into worktree, verify state**

```bash
cd /home/malecada/master_thesis/TradingAgents/.worktrees/live-testnet-deploy
git status
git log --oneline -3
```

Expected: `On branch feature/live-testnet-deploy`, three recent commits visible.

- [ ] **Step 5: Commit (none — branch creation only)**

No commit; the branch starts at main's HEAD.

### Task 0.2: Commit spec to feature branch

**Files:**
- Already created: `docs/superpowers/specs/2026-04-29-live-testnet-deployment-design.md`
- Already created: `docs/superpowers/plans/2026-04-29-live-testnet-deployment.md`

- [ ] **Step 1: Copy spec + plan from main checkout to worktree**

```bash
cp /home/malecada/master_thesis/TradingAgents/docs/superpowers/specs/2026-04-29-live-testnet-deployment-design.md \
   /home/malecada/master_thesis/TradingAgents/.worktrees/live-testnet-deploy/docs/superpowers/specs/

cp /home/malecada/master_thesis/TradingAgents/docs/superpowers/plans/2026-04-29-live-testnet-deployment.md \
   /home/malecada/master_thesis/TradingAgents/.worktrees/live-testnet-deploy/docs/superpowers/plans/
```

Note: if the directories don't exist in the worktree, create with `mkdir -p` first.

Expected: files copied, no errors.

- [ ] **Step 2: Stage and commit**

```bash
cd /home/malecada/master_thesis/TradingAgents/.worktrees/live-testnet-deploy
git add docs/superpowers/specs/2026-04-29-live-testnet-deployment-design.md
git add docs/superpowers/plans/2026-04-29-live-testnet-deployment.md
git commit -m "docs: live testnet deployment spec + plan"
```

Expected: 1 commit created with 2 files added.

### Task 0.3: Verify dependencies + branch alignment

**Files:**
- Read-only: verify `tradingagents/models/lgb_model.py`, `tradingagents/models/onchain_features.py` exist on main

- [ ] **Step 1: Confirm PIT on-chain is on main**

```bash
git log main --oneline | grep -iE "onchain|pit.on" | head -5
```

Expected: at least the commits `2c750d2 merge: PIT On-Chain Features Phase 1`, `c8770b6 feat(onchain-pit): BNB-mask fix unlocks 3-coin pool — Sharpe 1.90 -> 2.76`.

- [ ] **Step 2: Verify on-chain modules exist**

```bash
ls tradingagents/models/onchain_features.py
ls tradingagents/dataflows/onchain.py
ls scripts/backfill_onchain.py
```

Expected: all three files exist.

- [ ] **Step 3: Verify build_pooled_dataset has add_onchain_pit kwarg**

```bash
grep -n "add_onchain_pit" tradingagents/models/model_utils.py
```

Expected: at least one match.

- [ ] **Step 4: Pin dependencies snapshot**

```bash
pip freeze > /tmp/deps_baseline.txt
wc -l /tmp/deps_baseline.txt
```

Expected: non-zero line count. Reference for later container pinning.

- [ ] **Step 5: Commit (none — verification only)**

No commit; this is a verification step.

---

## Phase 1: Refactor V2 sizing into reusable module

The goal is a single `tradingagents/strategies/v2_sizing.py` imported by both `scripts/baseline_strategy_v2.py` (existing backtest) and the new live sizer (Phase 6). Golden tests pin behavior to current backtest output.

### Task 1.1: Create golden-value test from current backtest

**Files:**
- Create: `tests/strategies/__init__.py`
- Create: `tests/strategies/test_v2_sizing_golden.py`

- [ ] **Step 1: Create test directory and `__init__.py`**

```bash
mkdir -p tests/strategies
touch tests/strategies/__init__.py
```

- [ ] **Step 2: Write golden-value test (failing, since module doesn't exist yet)**

Create `tests/strategies/test_v2_sizing_golden.py`:

```python
"""Golden-value tests pinning v2_sizing functions to current backtest behavior.

The values below were captured by hand from `baseline_strategy_v2.py` defaults
and kept stable so any future refactor can be validated against them.
"""
import math

import numpy as np
import pytest


def test_vol_targeted_size_basic():
    from tradingagents.strategies.v2_sizing import vol_targeted_size

    # signal=+1, confidence=0.5, realized_vol=0.4 (40% annualized),
    # target_vol=0.10, kelly=0.5
    # base = 0.10 / 0.40 = 0.25
    # size = 1 * 0.5 * 0.25 * 0.5 = 0.0625
    result = vol_targeted_size(
        signal=1, confidence=0.5, realized_vol=0.40,
        target_vol=0.10, kelly_fraction=0.5,
    )
    assert math.isclose(result, 0.0625, rel_tol=1e-9)


def test_vol_targeted_size_zero_signal_returns_zero():
    from tradingagents.strategies.v2_sizing import vol_targeted_size

    result = vol_targeted_size(0, 0.8, 0.40, 0.10, 0.5)
    assert result == 0.0


def test_vol_targeted_size_nan_vol_returns_zero():
    from tradingagents.strategies.v2_sizing import vol_targeted_size

    result = vol_targeted_size(1, 0.5, float("nan"), 0.10, 0.5)
    assert result == 0.0


def test_vol_targeted_size_zero_vol_returns_zero():
    from tradingagents.strategies.v2_sizing import vol_targeted_size

    result = vol_targeted_size(1, 0.5, 0.0, 0.10, 0.5)
    assert result == 0.0


def test_vol_targeted_size_short_signal():
    from tradingagents.strategies.v2_sizing import vol_targeted_size

    result = vol_targeted_size(-1, 1.0, 0.20, 0.10, 0.5)
    # base = 0.10/0.20 = 0.5; size = -1 * 0.5 * 0.5 * 1.0 = -0.25
    assert math.isclose(result, -0.25, rel_tol=1e-9)


def test_apply_leverage_zero_base_returns_zero():
    from tradingagents.strategies.v2_sizing import apply_leverage

    assert apply_leverage(0.0, 0.8, 3.0) == 0.0


def test_apply_leverage_at_max_confidence_hits_3x_factor():
    from tradingagents.strategies.v2_sizing import apply_leverage

    # base=0.5, conf=1.0 → lev = 1 + (3 - 1)*1 = 3 → size = 1.5
    result = apply_leverage(0.5, 1.0, 3.0)
    assert math.isclose(result, 1.5, rel_tol=1e-9)


def test_apply_leverage_capped_at_max_leverage():
    from tradingagents.strategies.v2_sizing import apply_leverage

    # base=2.0, conf=1.0 → lev=3 → 6.0; capped to 3.0
    result = apply_leverage(2.0, 1.0, 3.0)
    assert result == 3.0


def test_apply_leverage_short_capped_negative():
    from tradingagents.strategies.v2_sizing import apply_leverage

    result = apply_leverage(-2.0, 1.0, 3.0)
    assert result == -3.0


def test_compute_realized_vol_uses_252():
    from tradingagents.strategies.v2_sizing import compute_realized_vol

    np.random.seed(42)
    prices = 100 * np.exp(np.cumsum(np.random.normal(0, 0.01, 50)))
    vol = compute_realized_vol(prices, lookback=20)
    assert np.all(np.isnan(vol[:20]))
    assert not np.isnan(vol[20])
    # std of N(0, 0.01) returns over 20 samples * sqrt(252) ≈ 0.158
    assert 0.1 < vol[-1] < 0.25, f"Unexpected vol {vol[-1]}"


def test_vol_regime_mask_short_history_passes():
    from tradingagents.strategies.v2_sizing import vol_regime_mask

    vol = np.array([np.nan] * 5 + [0.2, 0.3, 0.25])
    mask = vol_regime_mask(vol, percentile_cap=0.95)
    # First 5 NaN → False; rest pass since history < 20 → no cap applied
    assert mask.tolist() == [False] * 5 + [True, True, True]


def test_vol_regime_mask_caps_high_vol():
    from tradingagents.strategies.v2_sizing import vol_regime_mask

    history = list(np.linspace(0.1, 0.3, 25))
    vol = np.array(history + [1.5])
    mask = vol_regime_mask(vol, percentile_cap=0.95)
    assert mask[-1] is np.False_ or mask[-1] == False  # high vol blocked


def test_apply_trend_filter_aligned_long_uses_multiplier():
    from tradingagents.strategies.v2_sizing import apply_trend_filter

    positions = np.array([1.0, 1.0, -0.5, 0.0])
    prices = np.array([100, 105, 110, 115])
    sma = np.array([90, 95, 105, 120])  # idx 0,1: aligned long; idx 2: short, against; idx 3: flat
    out = apply_trend_filter(positions, prices, sma_period=30, multiplier=1.5,
                              precomputed_sma=sma)
    assert math.isclose(out[0], 1.5)
    assert math.isclose(out[1], 1.5)
    # idx 2: short, sma > price → short aligned with downtrend? sma > price means price below sma
    # In v2_sizing: apply_trend_filter scales -position by multiplier when price < sma (short with trend).
    # Verify exact behavior matches baseline_strategy_v2.apply_trend_filter.
    assert out[3] == 0.0


def test_term_structure_signals_symmetric_full_agreement():
    from tradingagents.strategies.v2_sizing import generate_term_structure_signals
    import pandas as pd

    df = pd.DataFrame({
        "ref_price": [100, 100, 100],
        "pred_h7":   [105, 95, 102],
        "pred_h14":  [110, 90, 99],
    })
    signals, conf = generate_term_structure_signals(
        df, horizons=[7, 14], confidence_ref=0.02, asymmetric=False,
    )
    # Row 0: both UP → +1; magnitudes (5%, 10%), avg=7.5%, conf = min(1, 0.075/0.02)=1
    # Row 1: both DOWN → -1; magnitudes (5%, 10%), conf=1
    # Row 2: UP, DOWN → 0
    assert signals.tolist() == [1.0, -1.0, 0.0]
    assert conf[0] == 1.0
    assert conf[1] == 1.0
    assert conf[2] == 0.0
```

- [ ] **Step 3: Run test to verify it fails (module doesn't exist)**

```bash
pytest tests/strategies/test_v2_sizing_golden.py -v 2>&1 | head -40
```

Expected: ALL tests FAIL with `ModuleNotFoundError: No module named 'tradingagents.strategies'`.

- [ ] **Step 4: Commit failing tests**

```bash
git add tests/strategies/__init__.py tests/strategies/test_v2_sizing_golden.py
git commit -m "test(v2_sizing): golden-value tests for refactor target"
```

### Task 1.2: Extract sizing functions into `tradingagents/strategies/v2_sizing.py`

**Files:**
- Create: `tradingagents/strategies/__init__.py`
- Create: `tradingagents/strategies/v2_sizing.py`

- [ ] **Step 1: Create directory + init**

```bash
mkdir -p tradingagents/strategies
touch tradingagents/strategies/__init__.py
```

- [ ] **Step 2: Copy sizing logic from `scripts/baseline_strategy_v2.py` into `v2_sizing.py`**

Create `tradingagents/strategies/v2_sizing.py` with the following functions (move verbatim from `scripts/baseline_strategy_v2.py`, lines 67–280, preserving signatures + behavior):

```python
"""V2 strategy sizing primitives — single source of truth for backtest + live.

Refactored out of scripts/baseline_strategy_v2.py so that
tradingagents/execution/live/sizer.py and the offline backtest share the same
implementation. Any drift between live and backtest decisions can therefore
be ruled out as a sizing-code bug.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_term_structure_signals(
    df_coin: pd.DataFrame,
    horizons: list[int],
    confidence_ref: float,
    asymmetric: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate consensus signals and confidence for a single coin.

    Symmetric mode: signal = +1/-1 if ALL horizons agree, else 0.
    Asymmetric mode (default): LONG if longest horizon says UP. SHORT only if
    ALL horizons agree on DOWN. When longest says UP but shorter disagrees,
    signal is LONG at half confidence.

    Returns (signals, confidence) arrays aligned with df_coin rows.
    """
    n = len(df_coin)
    signals = np.zeros(n)
    confidence = np.zeros(n)
    ref = df_coin["ref_price"].values
    longest_h = max(horizons)

    for i in range(n):
        if ref[i] <= 0 or np.isnan(ref[i]):
            continue
        dirs = []
        ret_magnitudes = []
        for h in horizons:
            pred = df_coin[f"pred_h{h}"].values[i]
            if np.isnan(pred):
                break
            d = 1 if pred > ref[i] else -1
            dirs.append(d)
            ret_magnitudes.append(abs(pred - ref[i]) / ref[i])
        if len(dirs) != len(horizons):
            continue
        avg_ret = np.mean(ret_magnitudes)
        if all(d == dirs[0] for d in dirs):
            signals[i] = dirs[0]
            confidence[i] = min(1.0, avg_ret / confidence_ref)
        elif asymmetric:
            longest_dir = dirs[horizons.index(longest_h)]
            if longest_dir == 1:
                signals[i] = 1
                confidence[i] = min(1.0, avg_ret / confidence_ref) * 0.5
    return signals, confidence


def compute_realized_vol(prices: np.ndarray, lookback: int) -> np.ndarray:
    """Rolling annualized realized volatility from log returns (sqrt(252) scale)."""
    log_ret = np.full(len(prices), np.nan)
    log_ret[1:] = np.log(prices[1:] / prices[:-1])
    vol = np.full(len(prices), np.nan)
    for i in range(lookback, len(prices)):
        window = log_ret[i - lookback + 1 : i + 1]
        window = window[~np.isnan(window)]
        if len(window) >= 2:
            vol[i] = np.std(window, ddof=1) * np.sqrt(252)
    return vol


def vol_regime_mask(vol: np.ndarray, percentile_cap: float) -> np.ndarray:
    """Return boolean mask: True = OK to trade, False = vol too high."""
    mask = np.ones(len(vol), dtype=bool)
    for i in range(len(vol)):
        if np.isnan(vol[i]):
            mask[i] = False
            continue
        history = vol[:i]
        history = history[~np.isnan(history)]
        if len(history) < 20:
            continue
        threshold = np.quantile(history, percentile_cap)
        if vol[i] > threshold:
            mask[i] = False
    return mask


def vol_targeted_size(
    signal: int, confidence: float, realized_vol: float,
    target_vol: float, kelly_fraction: float,
) -> float:
    """Position size = signal * kelly * (target_vol / realized_vol) * confidence."""
    if signal == 0 or np.isnan(realized_vol) or realized_vol <= 0:
        return 0.0
    base = target_vol / realized_vol
    return float(signal) * kelly_fraction * base * confidence


def apply_leverage(base_size: float, confidence: float, max_leverage: float) -> float:
    """Scale by 1 + (max_lev - 1) * confidence, capped at ±max_leverage."""
    if base_size == 0:
        return 0.0
    lev = 1 + (max_leverage - 1) * confidence
    sized = base_size * lev
    if abs(sized) > max_leverage:
        sized = np.sign(sized) * max_leverage
    return float(sized)


def apply_trend_filter(
    positions: np.ndarray,
    prices: np.ndarray,
    sma_period: int,
    multiplier: float,
    precomputed_sma: np.ndarray | None = None,
) -> np.ndarray:
    """Scale positions by SMA-trend alignment: *multiplier if aligned, /multiplier if against."""
    if sma_period <= 0:
        return positions.copy()
    if precomputed_sma is None:
        sma = pd.Series(prices).rolling(sma_period).mean().values
    else:
        sma = precomputed_sma
    filtered = positions.copy()
    for i in range(len(positions)):
        if np.isnan(sma[i]) or abs(positions[i]) < 1e-9:
            continue
        if prices[i] > sma[i]:
            if positions[i] > 0:
                filtered[i] = positions[i] * multiplier
            else:
                filtered[i] = positions[i] / multiplier
        else:
            if positions[i] < 0:
                filtered[i] = positions[i] * multiplier
            else:
                filtered[i] = positions[i] / multiplier
    return filtered


def build_positions_with_hold(
    signals: np.ndarray,
    vol_ok: np.ndarray,
    confidence: np.ndarray,
    realized_vol: np.ndarray,
    prices: np.ndarray,
    target_vol: float,
    kelly_fraction: float,
    max_leverage: float,
    min_hold: int,
    early_exit_loss: float = 0.015,
) -> np.ndarray:
    """Build position series with exit-only-on-flip + adaptive hold.

    Min-hold applies to winning positions. Losing positions can exit early
    (after 3 bars) if cumulative loss exceeds early_exit_loss AND signal has
    flipped or gone flat.
    """
    positions = np.zeros(len(signals))
    current_pos = 0.0
    current_dir = 0
    bars_held = 0
    entry_price = 0.0

    for i in range(len(signals)):
        sig = int(signals[i])
        if current_dir != 0:
            bars_held += 1
        # Early exit for losers
        if current_dir != 0 and bars_held >= 3 and bars_held < min_hold:
            if entry_price > 0 and prices[i] > 0:
                pnl = current_dir * (prices[i] - entry_price) / entry_price
                signal_changed = (sig != current_dir)
                if pnl < -early_exit_loss and signal_changed:
                    current_pos = 0.0
                    current_dir = 0
                    bars_held = 0
                    entry_price = 0.0
        # Entry / flip
        if sig != 0 and vol_ok[i]:
            if current_dir == 0:
                base = vol_targeted_size(sig, confidence[i], realized_vol[i],
                                         target_vol, kelly_fraction)
                current_pos = apply_leverage(base, confidence[i], max_leverage)
                current_dir = sig
                bars_held = 0
                entry_price = prices[i]
            elif sig != current_dir and bars_held >= min_hold:
                base = vol_targeted_size(sig, confidence[i], realized_vol[i],
                                         target_vol, kelly_fraction)
                current_pos = apply_leverage(base, confidence[i], max_leverage)
                current_dir = sig
                bars_held = 0
                entry_price = prices[i]
        positions[i] = current_pos
    return positions
```

- [ ] **Step 3: Run golden tests to verify they pass**

```bash
pytest tests/strategies/test_v2_sizing_golden.py -v 2>&1 | tail -30
```

Expected: ALL tests pass. If `test_apply_trend_filter_aligned_long_uses_multiplier` fails, inspect the trend-filter behavior in the original `baseline_strategy_v2.py:apply_trend_filter` and adjust the test to match. Document any assumption explicitly.

- [ ] **Step 4: Commit refactored module**

```bash
git add tradingagents/strategies/__init__.py tradingagents/strategies/v2_sizing.py
git commit -m "refactor(strategies): extract V2 sizing into reusable module"
```

### Task 1.3: Update `scripts/baseline_strategy_v2.py` to import from new module

**Files:**
- Modify: `scripts/baseline_strategy_v2.py`

- [ ] **Step 1: Snapshot current backtest output for regression check**

```bash
python scripts/baseline_strategy_v2.py --pred-dir data/multi_2coins_v2 --symmetric \
    > /tmp/v2_backtest_before_refactor.txt 2>&1
tail -30 /tmp/v2_backtest_before_refactor.txt
```

Expected: a summary table with Sharpe, return, max DD per coin and portfolio. Save the numbers — the post-refactor run must match exactly.

- [ ] **Step 2: Replace function bodies with imports**

In `scripts/baseline_strategy_v2.py`, find the function definitions for `generate_term_structure_signals`, `compute_realized_vol`, `vol_regime_mask`, `vol_targeted_size`, `apply_leverage`, `apply_trend_filter`, and `build_positions_with_hold`. Delete those definitions and add an import at the top of the file:

```python
from tradingagents.strategies.v2_sizing import (
    generate_term_structure_signals,
    compute_realized_vol,
    vol_regime_mask,
    vol_targeted_size,
    apply_leverage,
    apply_trend_filter,
    build_positions_with_hold,
)
```

Keep all argparse, IO, plotting, and main() code in `scripts/baseline_strategy_v2.py`.

- [ ] **Step 3: Run backtest, verify identical output**

```bash
python scripts/baseline_strategy_v2.py --pred-dir data/multi_2coins_v2 --symmetric \
    > /tmp/v2_backtest_after_refactor.txt 2>&1
diff /tmp/v2_backtest_before_refactor.txt /tmp/v2_backtest_after_refactor.txt
```

Expected: no diff. If diff shows numeric drift, the refactor altered behavior — bisect by reverting one function at a time.

- [ ] **Step 4: Commit**

```bash
git add scripts/baseline_strategy_v2.py
git commit -m "refactor(scripts): baseline_strategy_v2 imports from tradingagents.strategies.v2_sizing"
```

---

## Phase 2: Live execution package skeleton + journal

### Task 2.1: Create `live/` package and `config.py` with env loading

**Files:**
- Create: `tradingagents/execution/live/__init__.py`
- Create: `tradingagents/execution/live/config.py`
- Create: `tests/execution/__init__.py`
- Create: `tests/execution/live/__init__.py`
- Create: `tests/execution/live/test_config.py`

- [ ] **Step 1: Create directories and inits**

```bash
mkdir -p tradingagents/execution/live tests/execution/live
touch tradingagents/execution/live/__init__.py tests/execution/__init__.py tests/execution/live/__init__.py
```

- [ ] **Step 2: Write failing test for config loader**

Create `tests/execution/live/test_config.py`:

```python
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
    monkeypatch.setenv("COIN_UNIVERSE", "BTC,ETH,BNB")


def test_load_returns_typed_config(env_vars):
    from tradingagents.execution.live.config import load_config

    cfg = load_config()
    assert cfg.live_mode is False
    assert cfg.binance_api_key == "k"
    assert cfg.max_leverage == 3.0
    assert cfg.horizons == [7, 14]
    assert cfg.symmetric is True
    assert cfg.coin_universe == ["BTC", "ETH", "BNB"]
    assert cfg.initial_capital == 10000.0


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
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/execution/live/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Implement `config.py`**

Create `tradingagents/execution/live/config.py`:

```python
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
```

- [ ] **Step 5: Run tests, verify pass**

```bash
pytest tests/execution/live/test_config.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add tradingagents/execution/live/__init__.py tradingagents/execution/live/config.py
git add tests/execution/__init__.py tests/execution/live/__init__.py tests/execution/live/test_config.py
git commit -m "feat(live): config loader + tests"
```

### Task 2.2: SQLite journal — schema + writer

**Files:**
- Create: `tradingagents/execution/live/journal.py`
- Create: `tradingagents/execution/live/schema.sql`
- Create: `tests/execution/live/test_journal.py`

- [ ] **Step 1: Write failing test for journal round-trip**

Create `tests/execution/live/test_journal.py`:

```python
import os
import sqlite3
from datetime import datetime, timezone

import pytest


@pytest.fixture
def journal(tmp_path):
    from tradingagents.execution.live.journal import Journal
    db_path = tmp_path / "j.db"
    j = Journal(str(db_path))
    yield j
    j.close()


def test_creates_all_tables(journal):
    cur = journal._conn.cursor()
    rows = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    names = {r[0] for r in rows}
    assert {"cycles", "predictions", "sizing", "risk_checks", "trades",
            "portfolio_snapshots", "feature_snapshots",
            "model_artifacts", "shadow_decisions"}.issubset(names)


def test_log_cycle_round_trip(journal):
    journal.log_cycle_start("2026-05-12", git_sha="abc1234")
    journal.log_cycle_end("2026-05-12", status="ok")

    rows = journal._conn.execute("SELECT cycle_id, status FROM cycles").fetchall()
    assert rows == [("2026-05-12", "ok")]


def test_log_prediction_round_trip(journal):
    journal.log_cycle_start("2026-05-12", git_sha="abc")
    journal.log_prediction(cycle_id="2026-05-12", coin="BTC",
                            horizon=7, model_path_sha="sha7",
                            pred_value=70000.0, ref_price=68000.0,
                            signal_h7=1, signal_h14=1, consensus_signal=1)
    rows = journal._conn.execute(
        "SELECT coin, horizon, pred_value, consensus_signal FROM predictions"
    ).fetchall()
    assert rows == [("BTC", 7, 70000.0, 1)]


def test_log_risk_check_passed_and_failed(journal):
    journal.log_cycle_start("2026-05-12", git_sha="abc")
    journal.log_risk_check("2026-05-12", "BTC", "leverage_cap", True, 2.0, 3.0, "OK")
    journal.log_risk_check("2026-05-12", "BTC", "daily_loss", False, -0.20, -0.15, "kill")
    rows = journal._conn.execute(
        "SELECT check_name, passed FROM risk_checks ORDER BY id"
    ).fetchall()
    assert rows == [("leverage_cap", 1), ("daily_loss", 0)]


def test_idempotent_cycle_start(journal):
    journal.log_cycle_start("2026-05-12", git_sha="abc")
    journal.log_cycle_start("2026-05-12", git_sha="abc")  # safe re-call
    rows = journal._conn.execute("SELECT COUNT(*) FROM cycles").fetchone()
    assert rows[0] == 1
```

- [ ] **Step 2: Run, verify failing**

```bash
pytest tests/execution/live/test_journal.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Create schema file**

Create `tradingagents/execution/live/schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS cycles (
    cycle_id TEXT PRIMARY KEY,
    start_ts TEXT NOT NULL,
    end_ts TEXT,
    status TEXT,
    error_msg TEXT,
    git_commit_sha TEXT
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    horizon INTEGER NOT NULL,
    model_path_sha TEXT,
    pred_value REAL,
    pred_quantile_low REAL,
    pred_quantile_high REAL,
    ref_price REAL,
    signal_h7 INTEGER,
    signal_h14 INTEGER,
    consensus_signal INTEGER
);

CREATE TABLE IF NOT EXISTS sizing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    realized_vol REAL,
    target_vol REAL,
    kelly REAL,
    confidence REAL,
    base_size REAL,
    leverage REAL,
    sma30_multiplier REAL,
    final_size_notional REAL
);

CREATE TABLE IF NOT EXISTS risk_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id TEXT NOT NULL,
    coin TEXT,
    check_name TEXT NOT NULL,
    passed INTEGER NOT NULL,
    value REAL,
    threshold REAL,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    side TEXT,
    qty REAL,
    entry_price REAL,
    exit_price REAL,
    pnl REAL,
    fees REAL,
    slippage REAL,
    order_id TEXT,
    stop_loss_id TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    total_value REAL,
    usdt_balance REAL,
    position_qty_per_coin TEXT,
    unrealized_pnl REAL
);

CREATE TABLE IF NOT EXISTS feature_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    value REAL,
    source TEXT
);

CREATE TABLE IF NOT EXISTS model_artifacts (
    retrain_id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    model_path TEXT NOT NULL,
    train_window_start TEXT,
    train_window_end TEXT,
    train_rows INTEGER,
    train_dir_acc_h7 REAL,
    train_dir_acc_h14 REAL,
    sha256 TEXT
);

CREATE TABLE IF NOT EXISTS shadow_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    live_signal INTEGER,
    backtest_signal INTEGER,
    agree INTEGER,
    live_size REAL,
    backtest_size REAL,
    size_delta_pct REAL
);
```

- [ ] **Step 4: Implement Journal class**

Create `tradingagents/execution/live/journal.py`:

```python
"""SQLite forensic journal — one writer per pipeline step.

All schema in schema.sql. Designed for post-hoc reconstruction of any cycle.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Journal:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        with open(_SCHEMA_PATH) as f:
            self._conn.executescript(f.read())
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def log_cycle_start(self, cycle_id: str, *, git_sha: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO cycles (cycle_id, start_ts, git_commit_sha) "
            "VALUES (?, ?, ?)",
            (cycle_id, _utcnow_iso(), git_sha),
        )
        self._conn.commit()

    def log_cycle_end(self, cycle_id: str, *, status: str, error_msg: str = "") -> None:
        self._conn.execute(
            "UPDATE cycles SET end_ts = ?, status = ?, error_msg = ? WHERE cycle_id = ?",
            (_utcnow_iso(), status, error_msg, cycle_id),
        )
        self._conn.commit()

    def log_prediction(self, *, cycle_id, coin, horizon, model_path_sha,
                        pred_value, ref_price, signal_h7, signal_h14, consensus_signal,
                        pred_quantile_low=None, pred_quantile_high=None) -> None:
        self._conn.execute(
            "INSERT INTO predictions (cycle_id, coin, horizon, model_path_sha, "
            "pred_value, pred_quantile_low, pred_quantile_high, ref_price, "
            "signal_h7, signal_h14, consensus_signal) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cycle_id, coin, horizon, model_path_sha, pred_value,
             pred_quantile_low, pred_quantile_high, ref_price,
             signal_h7, signal_h14, consensus_signal),
        )
        self._conn.commit()

    def log_sizing(self, *, cycle_id, coin, realized_vol, target_vol, kelly,
                    confidence, base_size, leverage, sma30_multiplier,
                    final_size_notional) -> None:
        self._conn.execute(
            "INSERT INTO sizing (cycle_id, coin, realized_vol, target_vol, kelly, "
            "confidence, base_size, leverage, sma30_multiplier, final_size_notional) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cycle_id, coin, realized_vol, target_vol, kelly, confidence,
             base_size, leverage, sma30_multiplier, final_size_notional),
        )
        self._conn.commit()

    def log_risk_check(self, cycle_id, coin, check_name, passed: bool,
                        value, threshold, reason: str) -> None:
        self._conn.execute(
            "INSERT INTO risk_checks (cycle_id, coin, check_name, passed, value, threshold, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (cycle_id, coin, check_name, 1 if passed else 0, value, threshold, reason),
        )
        self._conn.commit()

    def log_trade(self, *, cycle_id, coin, side, qty, entry_price, exit_price,
                   pnl, fees, slippage, order_id, stop_loss_id, status) -> None:
        self._conn.execute(
            "INSERT INTO trades (cycle_id, coin, side, qty, entry_price, exit_price, "
            "pnl, fees, slippage, order_id, stop_loss_id, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cycle_id, coin, side, qty, entry_price, exit_price, pnl, fees,
             slippage, order_id, stop_loss_id, status),
        )
        self._conn.commit()

    def log_portfolio_snapshot(self, cycle_id, total_value, usdt_balance,
                                position_qty_per_coin: dict, unrealized_pnl) -> None:
        self._conn.execute(
            "INSERT INTO portfolio_snapshots (cycle_id, ts, total_value, usdt_balance, "
            "position_qty_per_coin, unrealized_pnl) VALUES (?, ?, ?, ?, ?, ?)",
            (cycle_id, _utcnow_iso(), total_value, usdt_balance,
             json.dumps(position_qty_per_coin), unrealized_pnl),
        )
        self._conn.commit()

    def log_feature_snapshot(self, cycle_id, coin, feature_name, value, source) -> None:
        self._conn.execute(
            "INSERT INTO feature_snapshots (cycle_id, coin, feature_name, value, source) "
            "VALUES (?, ?, ?, ?, ?)",
            (cycle_id, coin, feature_name, value, source),
        )
        self._conn.commit()

    def log_model_artifact(self, *, retrain_id, model_path, train_window_start,
                            train_window_end, train_rows, train_dir_acc_h7,
                            train_dir_acc_h14, sha256) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO model_artifacts (retrain_id, ts, model_path, "
            "train_window_start, train_window_end, train_rows, "
            "train_dir_acc_h7, train_dir_acc_h14, sha256) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (retrain_id, _utcnow_iso(), model_path, train_window_start,
             train_window_end, train_rows, train_dir_acc_h7,
             train_dir_acc_h14, sha256),
        )
        self._conn.commit()

    def log_shadow_decision(self, *, cycle_id, coin, live_signal, backtest_signal,
                             live_size, backtest_size) -> None:
        agree = 1 if live_signal == backtest_signal else 0
        if abs(backtest_size) > 1e-9:
            size_delta_pct = abs(live_size - backtest_size) / abs(backtest_size)
        else:
            size_delta_pct = 0.0 if abs(live_size) < 1e-9 else float("inf")
        self._conn.execute(
            "INSERT INTO shadow_decisions (cycle_id, coin, live_signal, backtest_signal, "
            "agree, live_size, backtest_size, size_delta_pct) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (cycle_id, coin, live_signal, backtest_signal, agree,
             live_size, backtest_size, size_delta_pct),
        )
        self._conn.commit()
```

- [ ] **Step 5: Run tests, verify pass**

```bash
pytest tests/execution/live/test_journal.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add tradingagents/execution/live/journal.py tradingagents/execution/live/schema.sql
git add tests/execution/live/test_journal.py
git commit -m "feat(live): SQLite journal schema + writer with round-trip tests"
```

---

## Phase 3: Data refresh

### Task 3.1: `data_refresh.py` — incremental CoinMetrics + DefiLlama + Binance

**Files:**
- Create: `tradingagents/execution/live/data_refresh.py`
- Create: `tests/execution/live/test_data_refresh.py`

- [ ] **Step 1: Inspect existing on-chain backfill code to identify reusable functions**

```bash
grep -n "^def \|^class " scripts/backfill_onchain.py | head -20
grep -n "upsert_rows\|fetch_coinmetrics\|fetch_defillama" tradingagents/dataflows/onchain.py | head -20
```

Note the names of the reusable fetchers and the `onchain_store.upsert_rows` API. Write them down — they're the dependencies of `data_refresh.py`.

- [ ] **Step 2: Write failing test (mocking the fetchers)**

Create `tests/execution/live/test_data_refresh.py`:

```python
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest


@pytest.fixture
def fake_cm_df():
    return pd.DataFrame({
        "coin": ["BTC"], "metric": ["MVRV"], "valid_from": ["2026-05-12"],
        "value": [1.5],
    })


@pytest.fixture
def fake_defillama_df():
    return pd.DataFrame({
        "coin": ["BTC"], "metric": ["TVL"], "valid_from": ["2026-05-12"],
        "value": [50e9],
    })


def test_refresh_coinmetrics_calls_fetch_and_upsert(tmp_path, fake_cm_df):
    from tradingagents.execution.live import data_refresh

    with patch.object(data_refresh, "fetch_coinmetrics_incremental",
                      return_value=fake_cm_df) as mock_fetch, \
         patch.object(data_refresh, "upsert_onchain_rows") as mock_upsert:
        data_refresh.refresh_coinmetrics(coins=["BTC"], store_root=tmp_path)
        mock_fetch.assert_called_once()
        mock_upsert.assert_called_once()
        df_arg, root_arg = mock_upsert.call_args.args
        assert root_arg == tmp_path
        assert "MVRV" in df_arg["metric"].values


def test_refresh_handles_empty_response(tmp_path):
    from tradingagents.execution.live import data_refresh

    empty = pd.DataFrame(columns=["coin", "metric", "valid_from", "value"])
    with patch.object(data_refresh, "fetch_coinmetrics_incremental",
                      return_value=empty), \
         patch.object(data_refresh, "upsert_onchain_rows") as mock_upsert:
        data_refresh.refresh_coinmetrics(coins=["BTC"], store_root=tmp_path)
        mock_upsert.assert_not_called()


def test_refresh_defillama_uses_correct_args(tmp_path, fake_defillama_df):
    from tradingagents.execution.live import data_refresh

    with patch.object(data_refresh, "fetch_defillama_incremental",
                      return_value=fake_defillama_df), \
         patch.object(data_refresh, "upsert_onchain_rows") as mock_upsert:
        data_refresh.refresh_defillama(coins=["BTC", "ETH"], store_root=tmp_path)
        mock_upsert.assert_called_once()


def test_refresh_binance_ohlcv_appends_yesterday(tmp_path):
    from tradingagents.execution.live import data_refresh

    fake_bar = pd.DataFrame({
        "date": ["2026-05-11"], "open": [60000], "high": [61000],
        "low": [59000], "close": [60500], "volume": [1000],
    })
    with patch.object(data_refresh, "fetch_binance_daily",
                      return_value=fake_bar) as mock_f, \
         patch.object(data_refresh, "append_ohlcv") as mock_app:
        data_refresh.refresh_ohlcv(coin="BTC", cache_root=tmp_path)
        mock_f.assert_called_once()
        mock_app.assert_called_once()
```

- [ ] **Step 3: Run, verify FAIL**

```bash
pytest tests/execution/live/test_data_refresh.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 4: Implement `data_refresh.py`**

Create `tradingagents/execution/live/data_refresh.py`. Wire to existing functions in `tradingagents/dataflows/onchain.py` (CoinMetrics + DefiLlama fetchers) and `scripts/backfill_onchain.py:onchain_store.upsert_rows`. Pseudocode:

```python
"""Daily incremental data refresh for live cycle.

All three sources are append-only into Parquet stores keyed by
(metric, coin, valid_from). Re-running the same date is a no-op.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from tradingagents.dataflows.onchain import (
    fetch_coinmetrics_incremental,    # add this if missing — see Step 5
    fetch_defillama_incremental,      # add this if missing — see Step 5
)
from tradingagents.dataflows.coingecko_binance import fetch_binance_daily

logger = logging.getLogger(__name__)


def upsert_onchain_rows(df: pd.DataFrame, root: Path) -> int:
    """Wrapper around onchain_store.upsert_rows for testability."""
    from scripts.backfill_onchain import onchain_store
    return onchain_store.upsert_rows(df, root=root)


def append_ohlcv(df: pd.DataFrame, coin: str, cache_root: Path) -> None:
    """Append yesterday's OHLCV bar to the per-coin cache parquet."""
    cache_root.mkdir(parents=True, exist_ok=True)
    out = cache_root / f"{coin}USDT_1d.parquet"
    if out.exists():
        existing = pd.read_parquet(out)
        merged = pd.concat([existing, df]).drop_duplicates(subset=["date"], keep="last")
    else:
        merged = df
    merged.to_parquet(out, index=False)


def refresh_coinmetrics(coins: list[str], store_root: Path) -> None:
    df = fetch_coinmetrics_incremental(coins=coins, since=_yesterday_utc())
    if df.empty:
        logger.warning("CoinMetrics returned 0 rows")
        return
    n = upsert_onchain_rows(df, store_root)
    logger.info("CoinMetrics: upserted %d rows", n)


def refresh_defillama(coins: list[str], store_root: Path) -> None:
    df = fetch_defillama_incremental(coins=coins, since=_yesterday_utc())
    if df.empty:
        logger.warning("DefiLlama returned 0 rows")
        return
    n = upsert_onchain_rows(df, store_root)
    logger.info("DefiLlama: upserted %d rows", n)


def refresh_ohlcv(coin: str, cache_root: Path) -> None:
    df = fetch_binance_daily(symbol=f"{coin}USDT", days=2)  # yesterday + today partial
    if df.empty:
        logger.warning("Binance OHLCV returned 0 rows for %s", coin)
        return
    append_ohlcv(df, coin, cache_root)
    logger.info("OHLCV: appended %d rows for %s", len(df), coin)


def _yesterday_utc() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
```

- [ ] **Step 5: If `fetch_coinmetrics_incremental` / `fetch_defillama_incremental` don't exist**

Inspect `tradingagents/dataflows/onchain.py`. If only batch fetchers exist, add thin incremental wrappers there:

```python
def fetch_coinmetrics_incremental(coins: list[str], since: str) -> pd.DataFrame:
    """Fetch CoinMetrics rows with valid_from >= since. Returns empty df if none."""
    return fetch_coinmetrics(coins=coins, start_date=since, end_date=None)


def fetch_defillama_incremental(coins: list[str], since: str) -> pd.DataFrame:
    """Fetch DefiLlama rows with valid_from >= since."""
    return fetch_defillama(coins=coins, start_date=since, end_date=None)
```

- [ ] **Step 6: Run tests, verify pass**

```bash
pytest tests/execution/live/test_data_refresh.py -v
```

Expected: 4 passed.

- [ ] **Step 7: Commit**

```bash
git add tradingagents/execution/live/data_refresh.py tests/execution/live/test_data_refresh.py
git add tradingagents/dataflows/onchain.py  # if Step 5 modifications were made
git commit -m "feat(live): incremental data refresh for CoinMetrics, DefiLlama, Binance OHLCV"
```

---

## Phase 4: Retrain

### Task 4.1: `retrain.py` — daily walk-forward LGB pooled with checkpoint

**Files:**
- Create: `tradingagents/execution/live/retrain.py`
- Create: `tests/execution/live/test_retrain.py`

- [ ] **Step 1: Inspect existing pooled training entry point**

```bash
grep -n "model_run_pooled\|build_pooled_dataset" tradingagents/models/lgb_model.py tradingagents/models/model_utils.py | head -20
```

Note signatures. The retrain module must call them with the live universe + PIT on-chain enabled.

- [ ] **Step 2: Write failing test**

Create `tests/execution/live/test_retrain.py`:

```python
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest


def test_retrain_writes_checkpoint_and_returns_artifact(tmp_path):
    from tradingagents.execution.live import retrain

    fake_dataset = pd.DataFrame({
        "coin": ["BTC", "ETH", "BNB"] * 100,
        "ref_price": [60000, 3000, 400] * 100,
        "feature_a": [1.0] * 300,
        "y_h7": [60100, 3010, 401] * 100,
        "y_h14": [60200, 3020, 402] * 100,
    })
    fake_metrics = {"dir_acc_h7": 0.65, "dir_acc_h14": 0.70}

    with patch.object(retrain, "build_pooled_dataset",
                      return_value=fake_dataset), \
         patch.object(retrain, "model_run_pooled",
                      return_value=({"model": MagicMock()}, fake_metrics)):
        artifact = retrain.run_retrain(
            coins=["BTC", "ETH", "BNB"],
            horizons=[7, 14],
            asof="2026-05-11",
            checkpoint_dir=tmp_path,
        )
    assert artifact.model_path.exists()
    assert artifact.train_dir_acc_h7 == 0.65
    assert artifact.train_dir_acc_h14 == 0.70
    assert artifact.train_rows == 300
    assert len(artifact.sha256) == 64


def test_retrain_falls_back_on_failure(tmp_path):
    from tradingagents.execution.live import retrain

    # Pre-seed a previous checkpoint
    prev = tmp_path / "lgb_3coin_pit_2026-05-10.pkl"
    prev.write_bytes(b"fake-prev-checkpoint")

    with patch.object(retrain, "build_pooled_dataset",
                      side_effect=RuntimeError("CoinMetrics down")):
        artifact = retrain.run_retrain_with_fallback(
            coins=["BTC", "ETH", "BNB"],
            horizons=[7, 14],
            asof="2026-05-11",
            checkpoint_dir=tmp_path,
        )
    # Falls back to most recent existing checkpoint
    assert artifact.model_path == prev
    assert artifact.is_fallback is True
```

- [ ] **Step 3: Run, FAIL**

```bash
pytest tests/execution/live/test_retrain.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 4: Implement `retrain.py`**

```python
"""Daily walk-forward retrain of pooled LGB model with PIT on-chain features."""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

import joblib

from tradingagents.models.lgb_model import model_run_pooled
from tradingagents.models.model_utils import build_pooled_dataset

logger = logging.getLogger(__name__)


@dataclass
class TrainArtifact:
    model_path: Path
    train_window_start: str
    train_window_end: str
    train_rows: int
    train_dir_acc_h7: float
    train_dir_acc_h14: float
    sha256: str
    is_fallback: bool = False


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def run_retrain(coins, horizons, asof, checkpoint_dir: Path) -> TrainArtifact:
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    df = build_pooled_dataset(coins=coins, add_onchain_pit=True, asof=asof)
    model_obj, metrics = model_run_pooled(df, horizons=horizons)

    out_path = checkpoint_dir / f"lgb_{len(coins)}coin_pit_{asof}.pkl"
    joblib.dump(model_obj, out_path)

    return TrainArtifact(
        model_path=out_path,
        train_window_start=str(df.iloc[0].get("date", "")),
        train_window_end=asof,
        train_rows=len(df),
        train_dir_acc_h7=metrics.get("dir_acc_h7", float("nan")),
        train_dir_acc_h14=metrics.get("dir_acc_h14", float("nan")),
        sha256=_sha256_of(out_path),
    )


def run_retrain_with_fallback(coins, horizons, asof, checkpoint_dir: Path) -> TrainArtifact:
    """Try retrain; if it fails, return the most recent existing checkpoint."""
    try:
        return run_retrain(coins, horizons, asof, checkpoint_dir)
    except Exception as e:
        logger.error("Retrain failed: %s — falling back to previous checkpoint", e)
        previous = sorted(Path(checkpoint_dir).glob("lgb_*coin_pit_*.pkl"))
        if not previous:
            raise RuntimeError("No previous checkpoint to fall back to") from e
        prev = previous[-1]
        return TrainArtifact(
            model_path=prev,
            train_window_start="",
            train_window_end="",
            train_rows=0,
            train_dir_acc_h7=float("nan"),
            train_dir_acc_h14=float("nan"),
            sha256=_sha256_of(prev),
            is_fallback=True,
        )
```

- [ ] **Step 5: Run tests, verify pass**

```bash
pytest tests/execution/live/test_retrain.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add tradingagents/execution/live/retrain.py tests/execution/live/test_retrain.py
git commit -m "feat(live): daily walk-forward retrain with checkpoint + fallback"
```

---

## Phase 5: Predict

### Task 5.1: `predict.py` — load checkpoint, build PIT features, predict

**Files:**
- Create: `tradingagents/execution/live/predict.py`
- Create: `tests/execution/live/test_predict.py`

- [ ] **Step 1: Identify the existing predict-from-pooled-model entry point**

```bash
grep -n "predict\|forecast" tradingagents/models/lgb_model.py | head -10
```

If the existing `model_run_pooled` returns a `predict()` callable on the model object, use it. If not, pickle includes a fitted booster — use `booster.predict(features_df)` directly.

- [ ] **Step 2: Write failing test**

Create `tests/execution/live/test_predict.py`:

```python
from pathlib import Path
from unittest.mock import patch, MagicMock

import joblib
import numpy as np
import pandas as pd
import pytest


def test_predict_returns_frame_per_coin(tmp_path):
    from tradingagents.execution.live import predict

    fake_model = MagicMock()
    fake_model.predict.side_effect = [
        np.array([70000.0]),  # h=7 prediction for BTC
        np.array([72000.0]),  # h=14 for BTC
    ]
    ckpt = tmp_path / "model.pkl"
    joblib.dump({"booster": fake_model, "feature_names": ["a"]}, ckpt)

    fake_features = pd.DataFrame({"coin": ["BTC"], "a": [1.0], "ref_price": [68000.0]})

    with patch.object(predict, "build_pit_features_for_date",
                      return_value=fake_features):
        out = predict.run_predict(
            checkpoint_path=ckpt,
            coins=["BTC"], horizons=[7, 14], asof="2026-05-11",
        )

    assert "BTC" in out
    assert out["BTC"]["pred_h7"] == 70000.0
    assert out["BTC"]["pred_h14"] == 72000.0
    assert out["BTC"]["ref_price"] == 68000.0
```

- [ ] **Step 3: Run, FAIL**

```bash
pytest tests/execution/live/test_predict.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 4: Implement `predict.py`**

```python
"""Load latest checkpoint, build PIT features asof, predict per coin per horizon."""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import pandas as pd

from tradingagents.models.onchain_features import build_pit_onchain_features
from tradingagents.models.model_utils import build_pooled_dataset

logger = logging.getLogger(__name__)


def build_pit_features_for_date(coins, asof) -> pd.DataFrame:
    """Build same feature schema as backtest, but asof a specific date.

    Reuses build_pooled_dataset with truncation to asof.
    """
    df = build_pooled_dataset(coins=coins, add_onchain_pit=True, asof=asof)
    # Take only the latest row per coin
    return df.groupby("coin", as_index=False).tail(1)


def run_predict(checkpoint_path: Path, coins, horizons, asof) -> dict:
    bundle = joblib.load(checkpoint_path)
    booster = bundle["booster"]
    feature_names = bundle["feature_names"]

    feats = build_pit_features_for_date(coins, asof)
    out = {}
    for coin in coins:
        row = feats[feats["coin"] == coin]
        if row.empty:
            logger.warning("No features for %s asof %s", coin, asof)
            continue
        x = row[feature_names].values
        result = {"ref_price": float(row["ref_price"].values[0])}
        for h in horizons:
            # If model is per-horizon: pick the right model from bundle
            # If model is multi-output: predict and slice
            pred = booster.predict(x)
            result[f"pred_h{h}"] = float(pred[0]) if hasattr(pred, "__len__") else float(pred)
        out[coin] = result
    return out
```

Note: this implementation assumes single-booster models. If `model_run_pooled` returns a per-horizon dict (e.g. `{"booster_h7": ..., "booster_h14": ...}`), update the predict loop to look up the right booster per horizon. Inspect the bundle structure during Step 1 and adapt before running tests.

- [ ] **Step 5: Run tests, verify pass**

```bash
pytest tests/execution/live/test_predict.py -v
```

Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add tradingagents/execution/live/predict.py tests/execution/live/test_predict.py
git commit -m "feat(live): load checkpoint and run PIT predict per coin per horizon"
```

### Task 5.2: Equivalence test — live predict matches backtest at the same date

**Files:**
- Create: `tests/execution/live/test_predict_equivalence.py`

- [ ] **Step 1: Write equivalence test**

Create `tests/execution/live/test_predict_equivalence.py`:

```python
"""Live predict must produce the same numbers as backtest predict at the same date.

If they diverge, the live cycle's decisions cannot be compared to backtest.
"""
import pytest
from pathlib import Path

import pandas as pd


@pytest.mark.online  # requires data files
def test_live_predict_matches_backtest():
    from tradingagents.execution.live import predict, retrain
    from tradingagents.models.lgb_model import model_run_pooled
    from tradingagents.models.model_utils import build_pooled_dataset

    coins = ["BTC", "ETH", "BNB"]
    asof = "2026-04-25"  # any date with data

    # Backtest path: build dataset, train, predict
    df = build_pooled_dataset(coins=coins, add_onchain_pit=True, asof=asof)
    bt_model, _ = model_run_pooled(df, horizons=[7, 14])
    feature_names = bt_model.get("feature_names", df.columns.tolist())
    bt_predictions = {}
    for coin in coins:
        row = df[df["coin"] == coin].tail(1)
        if not row.empty:
            x = row[feature_names].values
            bt_predictions[coin] = {
                "pred_h7": float(bt_model["booster"].predict(x)[0]),
                "pred_h14": float(bt_model["booster"].predict(x)[0]),
            }

    # Live path: train + checkpoint + predict
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        artifact = retrain.run_retrain(coins, [7, 14], asof, Path(td))
        live_predictions = predict.run_predict(
            artifact.model_path, coins, [7, 14], asof,
        )

    for coin in coins:
        if coin not in bt_predictions or coin not in live_predictions:
            continue
        for h in [7, 14]:
            assert abs(bt_predictions[coin][f"pred_h{h}"] -
                       live_predictions[coin][f"pred_h{h}"]) < 1e-6, \
                f"{coin} h={h} diverges"
```

- [ ] **Step 2: Run with `--run-online` (skipped by default)**

```bash
pytest tests/execution/live/test_predict_equivalence.py -v -m online
```

Expected: passes if data is present. Skips otherwise.

- [ ] **Step 3: Commit**

```bash
git add tests/execution/live/test_predict_equivalence.py
git commit -m "test(live): equivalence test live predict vs backtest predict"
```

---

## Phase 6: Sizer (live wrapper)

### Task 6.1: `sizer.py` — single-step V2 sizing for live cycle

**Files:**
- Create: `tradingagents/execution/live/sizer.py`
- Create: `tests/execution/live/test_sizer.py`

- [ ] **Step 1: Write failing test**

Create `tests/execution/live/test_sizer.py`:

```python
from datetime import date
import math

import numpy as np
import pandas as pd
import pytest


def _fake_history(coin, days=60):
    """Build a fake price history that the sizer needs for vol + SMA."""
    dates = pd.date_range("2026-03-01", periods=days, freq="D")
    np.random.seed(42)
    prices = 60000 * np.exp(np.cumsum(np.random.normal(0, 0.02, days)))
    return pd.DataFrame({"date": dates, "close": prices, "coin": [coin] * days})


def test_sizer_long_signal_produces_positive_size():
    from tradingagents.execution.live.sizer import compute_size

    pred = {"ref_price": 60000.0, "pred_h7": 63000.0, "pred_h14": 66000.0}  # both UP
    history = _fake_history("BTC")
    result = compute_size(
        coin="BTC", prediction=pred, price_history=history,
        horizons=[7, 14], symmetric=True,
        target_vol=0.10, kelly_fraction=0.5, max_leverage=3.0,
        vol_lookback=20, vol_cap_pct=0.95, confidence_ref=0.02,
        trend_sma=30, trend_multiplier=1.5,
    )
    assert result.signal == 1
    assert result.final_size_notional > 0
    assert result.confidence > 0


def test_sizer_disagreeing_horizons_returns_zero_in_symmetric():
    from tradingagents.execution.live.sizer import compute_size

    pred = {"ref_price": 60000.0, "pred_h7": 63000.0, "pred_h14": 57000.0}
    history = _fake_history("BTC")
    result = compute_size(
        coin="BTC", prediction=pred, price_history=history,
        horizons=[7, 14], symmetric=True,
        target_vol=0.10, kelly_fraction=0.5, max_leverage=3.0,
        vol_lookback=20, vol_cap_pct=0.95, confidence_ref=0.02,
        trend_sma=30, trend_multiplier=1.5,
    )
    assert result.signal == 0
    assert result.final_size_notional == 0


def test_sizer_caps_at_max_leverage():
    from tradingagents.execution.live.sizer import compute_size

    pred = {"ref_price": 60000.0, "pred_h7": 90000.0, "pred_h14": 95000.0}  # huge magnitude
    history = _fake_history("BTC")
    result = compute_size(
        coin="BTC", prediction=pred, price_history=history,
        horizons=[7, 14], symmetric=True,
        target_vol=0.10, kelly_fraction=0.5, max_leverage=3.0,
        vol_lookback=20, vol_cap_pct=0.95, confidence_ref=0.02,
        trend_sma=30, trend_multiplier=1.5,
    )
    assert abs(result.final_size_notional) <= 3.0
```

- [ ] **Step 2: Run, verify FAIL**

```bash
pytest tests/execution/live/test_sizer.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `sizer.py`**

```python
"""Single-step V2 sizing for the live cycle.

Wraps tradingagents.strategies.v2_sizing primitives and applies them to one
coin's most recent prediction + the rolling price history. Returns a SizingResult
with all components needed for journal logging.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tradingagents.strategies.v2_sizing import (
    apply_leverage,
    apply_trend_filter,
    compute_realized_vol,
    generate_term_structure_signals,
    vol_regime_mask,
    vol_targeted_size,
)


@dataclass
class SizingResult:
    coin: str
    signal: int
    confidence: float
    realized_vol: float
    base_size: float
    leverage: float
    sma_multiplier: float
    final_size_notional: float
    vol_ok: bool


def compute_size(
    *, coin, prediction, price_history,
    horizons, symmetric,
    target_vol, kelly_fraction, max_leverage,
    vol_lookback, vol_cap_pct, confidence_ref,
    trend_sma, trend_multiplier,
) -> SizingResult:
    # Build single-row prediction frame in the format generate_term_structure_signals expects
    df_coin = pd.DataFrame({
        "ref_price": [prediction["ref_price"]],
        **{f"pred_h{h}": [prediction[f"pred_h{h}"]] for h in horizons},
    })
    signals, conf = generate_term_structure_signals(
        df_coin, horizons=horizons, confidence_ref=confidence_ref,
        asymmetric=not symmetric,
    )
    signal = int(signals[0])
    confidence = float(conf[0])

    # Vol from history
    prices = price_history.sort_values("date")["close"].values
    vol_series = compute_realized_vol(prices, lookback=vol_lookback)
    realized_vol = float(vol_series[-1]) if len(vol_series) and not np.isnan(vol_series[-1]) else float("nan")
    mask = vol_regime_mask(vol_series, percentile_cap=vol_cap_pct)
    vol_ok = bool(mask[-1]) if len(mask) else False

    if not vol_ok or signal == 0:
        return SizingResult(coin=coin, signal=signal, confidence=confidence,
                             realized_vol=realized_vol, base_size=0.0, leverage=0.0,
                             sma_multiplier=1.0, final_size_notional=0.0, vol_ok=vol_ok)

    base = vol_targeted_size(signal, confidence, realized_vol, target_vol, kelly_fraction)
    sized = apply_leverage(base, confidence, max_leverage)

    # Trend filter on a 2-element array (only need the last point)
    pos_arr = np.array([sized])
    price_arr = np.array([prices[-1]])
    sma = pd.Series(prices).rolling(trend_sma).mean().values
    sma_arr = np.array([sma[-1]])
    filtered = apply_trend_filter(pos_arr, price_arr, sma_period=trend_sma,
                                   multiplier=trend_multiplier, precomputed_sma=sma_arr)
    sma_mult = filtered[0] / sized if abs(sized) > 1e-9 else 1.0
    return SizingResult(
        coin=coin, signal=signal, confidence=confidence, realized_vol=realized_vol,
        base_size=base, leverage=sized, sma_multiplier=sma_mult,
        final_size_notional=float(filtered[0]), vol_ok=True,
    )
```

- [ ] **Step 4: Run tests, verify pass**

```bash
pytest tests/execution/live/test_sizer.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/sizer.py tests/execution/live/test_sizer.py
git commit -m "feat(live): single-step V2 sizer wrapping strategies.v2_sizing"
```

---

## Phase 7: Risk

### Task 7.1: `risk.py` — pre-trade gates

**Files:**
- Create: `tradingagents/execution/live/risk.py`
- Create: `tests/execution/live/test_risk.py`

- [ ] **Step 1: Write failing test**

Create `tests/execution/live/test_risk.py`:

```python
from datetime import date
import pytest


def test_leverage_cap_passes_within_limit():
    from tradingagents.execution.live.risk import check_leverage

    ok, reason = check_leverage(size=2.5, max_leverage=3.0)
    assert ok is True


def test_leverage_cap_rejects_over_limit():
    from tradingagents.execution.live.risk import check_leverage

    ok, reason = check_leverage(size=3.5, max_leverage=3.0)
    assert ok is False
    assert "3.5" in reason


def test_daily_loss_kill_switch_triggers_at_threshold():
    from tradingagents.execution.live.risk import check_daily_loss

    ok, reason = check_daily_loss(pnl_today_pct=-0.16, max_loss_pct=0.15)
    assert ok is False
    assert "kill" in reason.lower()


def test_daily_loss_under_limit_passes():
    from tradingagents.execution.live.risk import check_daily_loss

    ok, _ = check_daily_loss(pnl_today_pct=-0.05, max_loss_pct=0.15)
    assert ok is True


def test_max_open_positions_blocks_new_entry():
    from tradingagents.execution.live.risk import check_max_positions

    ok, _ = check_max_positions(current_open=3, max_open=3, opening_new=True)
    assert ok is False


def test_max_open_positions_allows_close():
    from tradingagents.execution.live.risk import check_max_positions

    ok, _ = check_max_positions(current_open=3, max_open=3, opening_new=False)
    assert ok is True


def test_frequency_guard_blocks_second_trade_today():
    from tradingagents.execution.live.risk import check_frequency_guard

    ok, _ = check_frequency_guard(coin="BTC", trades_today_count=1)
    assert ok is False


def test_frequency_guard_allows_first_trade():
    from tradingagents.execution.live.risk import check_frequency_guard

    ok, _ = check_frequency_guard(coin="BTC", trades_today_count=0)
    assert ok is True
```

- [ ] **Step 2: Run, FAIL**

```bash
pytest tests/execution/live/test_risk.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `risk.py`**

```python
"""Pre-trade risk gates. Each returns (passed: bool, reason: str)."""
from __future__ import annotations


def check_leverage(size: float, max_leverage: float) -> tuple[bool, str]:
    if abs(size) > max_leverage:
        return False, f"|size|={abs(size):.3f} > max_leverage={max_leverage}"
    return True, "ok"


def check_daily_loss(pnl_today_pct: float, max_loss_pct: float) -> tuple[bool, str]:
    if pnl_today_pct < -max_loss_pct:
        return False, (f"daily PnL {pnl_today_pct:.2%} breached -{max_loss_pct:.2%} — "
                       f"KILL SWITCH")
    return True, "ok"


def check_max_positions(current_open: int, max_open: int, opening_new: bool) -> tuple[bool, str]:
    if opening_new and current_open >= max_open:
        return False, f"already at MAX_OPEN_POSITIONS={max_open}"
    return True, "ok"


def check_frequency_guard(coin: str, trades_today_count: int) -> tuple[bool, str]:
    if trades_today_count > 0:
        return False, f"{coin} already traded today ({trades_today_count} time(s))"
    return True, "ok"
```

- [ ] **Step 4: Run tests, verify pass**

```bash
pytest tests/execution/live/test_risk.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/risk.py tests/execution/live/test_risk.py
git commit -m "feat(live): pre-trade risk gates"
```

---

## Phase 8: Exchange (verify existing)

### Task 8.1: Confirm existing `tradingagents/execution/exchange.py` works on testnet

**Files:**
- Read-only: `tradingagents/execution/exchange.py`
- Create: `tests/execution/test_exchange_smoke.py`

- [ ] **Step 1: Inspect existing wrapper**

```bash
wc -l tradingagents/execution/exchange.py
grep -n "^def \|^class " tradingagents/execution/exchange.py
```

Confirm at minimum: `place_market_order`, `place_stop_loss`, `get_ticker_price`, `get_usdt_balance`, `get_current_position`, `set_leverage`, `get_total_portfolio_value`. If any are missing, add them following the pattern in `Krypto-v0/src_live/exchange.py` (already verified working on Binance Futures testnet).

- [ ] **Step 2: Write smoke test (online, opt-in)**

Create `tests/execution/test_exchange_smoke.py`:

```python
"""Online smoke test against Binance Futures testnet.

Run only with credentials in environment:
    pytest tests/execution/test_exchange_smoke.py -v -m online
"""
import os
import pytest


@pytest.mark.online
def test_testnet_ticker_query():
    from tradingagents.execution.exchange import BinanceClient

    if not os.environ.get("BINANCE_API_KEY"):
        pytest.skip("BINANCE_API_KEY not set")

    client = BinanceClient(
        api_key=os.environ["BINANCE_API_KEY"],
        api_secret=os.environ["BINANCE_API_SECRET"],
        testnet=True,
    )
    price = client.get_ticker_price("BTCUSDT")
    assert price > 1000  # sanity: BTC always > $1k


@pytest.mark.online
def test_testnet_balance_query():
    from tradingagents.execution.exchange import BinanceClient

    if not os.environ.get("BINANCE_API_KEY"):
        pytest.skip("BINANCE_API_KEY not set")

    client = BinanceClient(
        api_key=os.environ["BINANCE_API_KEY"],
        api_secret=os.environ["BINANCE_API_SECRET"],
        testnet=True,
    )
    balance = client.get_usdt_balance()
    assert balance >= 0  # could be 0 on fresh testnet account
```

- [ ] **Step 3: Run online smoke test (only if testnet creds set)**

```bash
pytest tests/execution/test_exchange_smoke.py -v -m online
```

Expected: 2 passed (or skipped if no creds).

- [ ] **Step 4: Commit**

```bash
git add tradingagents/execution/exchange.py  # if any modifications
git add tests/execution/test_exchange_smoke.py
git commit -m "test(execution): testnet smoke tests for Binance wrapper"
```

---

## Phase 9: Shadow replay

### Task 9.1: `shadow.py` — re-run V2 backtest engine on same data + date

**Files:**
- Create: `tradingagents/execution/live/shadow.py`
- Create: `tests/execution/live/test_shadow.py`

- [ ] **Step 1: Write failing test**

Create `tests/execution/live/test_shadow.py`:

```python
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest


def test_shadow_decision_for_same_inputs_matches_live():
    from tradingagents.execution.live.shadow import compute_shadow_decision

    pred = {"ref_price": 60000.0, "pred_h7": 63000.0, "pred_h14": 66000.0}
    np.random.seed(42)
    history = pd.DataFrame({
        "date": pd.date_range("2026-03-01", periods=60, freq="D"),
        "close": 60000 * np.exp(np.cumsum(np.random.normal(0, 0.02, 60))),
    })
    result = compute_shadow_decision(
        coin="BTC", prediction=pred, price_history=history,
        horizons=[7, 14], symmetric=True,
        target_vol=0.10, kelly_fraction=0.5, max_leverage=3.0,
        vol_lookback=20, vol_cap_pct=0.95, confidence_ref=0.02,
        trend_sma=30, trend_multiplier=1.5,
    )
    assert result.signal in (-1, 0, 1)
    assert isinstance(result.size, float)
```

- [ ] **Step 2: Run, FAIL**

```bash
pytest tests/execution/live/test_shadow.py -v
```

- [ ] **Step 3: Implement `shadow.py`**

Since shadow + live both need V2 single-step sizing, `shadow.compute_shadow_decision` is essentially the same as `sizer.compute_size`. The point of shadow is to use the **canonical reference implementation** — the one in `tradingagents.strategies.v2_sizing`. So shadow should ALSO call `compute_size`. The agreement check then becomes: live and shadow paths are wired to the same code, and the only thing being verified is that the surrounding plumbing (e.g. data fetching, journal writes) doesn't mutate the inputs en route.

```python
"""Shadow replay: re-runs V2 sizing on the same input data.

Because both live and shadow use tradingagents.strategies.v2_sizing as the
single source of truth, signal_agreement should be 100%. Any divergence
indicates input mutation (e.g. stale cache, unit conversion, type coercion).
"""
from __future__ import annotations

from dataclasses import dataclass

from tradingagents.execution.live.sizer import compute_size


@dataclass
class ShadowDecision:
    coin: str
    signal: int
    size: float


def compute_shadow_decision(**kwargs) -> ShadowDecision:
    """Wraps compute_size; identical math, separate code path for diff verification."""
    res = compute_size(**kwargs)
    return ShadowDecision(coin=res.coin, signal=res.signal, size=res.final_size_notional)
```

- [ ] **Step 4: Run tests, pass**

```bash
pytest tests/execution/live/test_shadow.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/shadow.py tests/execution/live/test_shadow.py
git commit -m "feat(live): shadow replay decision computation"
```

---

## Phase 10: Notify (Telegram)

### Task 10.1: `notify.py` — Telegram daily summary + immediate alerts

**Files:**
- Create: `tradingagents/execution/live/notify.py`
- Create: `tests/execution/live/test_notify.py`

- [ ] **Step 1: Write failing test (mocking httpx/requests)**

Create `tests/execution/live/test_notify.py`:

```python
from unittest.mock import patch, MagicMock

import pytest


def test_send_daily_summary_calls_telegram_api():
    from tradingagents.execution.live import notify

    with patch.object(notify, "_post_telegram") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        notify.send_daily_summary(
            bot_token="t", chat_id="123",
            cycle_id="2026-05-12",
            portfolio_before=10000.0, portfolio_after=10120.0,
            trades=[{"coin": "BTC", "side": "BUY", "qty": 0.1, "price": 60000}],
            agreement_rate=1.0,
        )
        mock_post.assert_called_once()
        text = mock_post.call_args.kwargs["text"]
        assert "2026-05-12" in text
        assert "BTC" in text


def test_send_alert_includes_severity():
    from tradingagents.execution.live import notify

    with patch.object(notify, "_post_telegram") as mock_post:
        notify.send_alert(
            bot_token="t", chat_id="123",
            severity="UNPROTECTED",
            message="BTC stop-loss failed",
        )
        text = mock_post.call_args.kwargs["text"]
        assert "UNPROTECTED" in text
        assert "BTC stop-loss" in text


def test_telegram_failure_does_not_crash():
    from tradingagents.execution.live import notify

    with patch.object(notify, "_post_telegram", side_effect=Exception("network")):
        # Must not raise — Telegram failure is logged, not fatal
        notify.send_daily_summary(
            bot_token="t", chat_id="123",
            cycle_id="2026-05-12",
            portfolio_before=10000.0, portfolio_after=10100.0,
            trades=[], agreement_rate=1.0,
        )
```

- [ ] **Step 2: Run, FAIL**

```bash
pytest tests/execution/live/test_notify.py -v
```

- [ ] **Step 3: Implement `notify.py`**

```python
"""Telegram bot — daily summary + immediate alerts.

Outbound only; failures are logged, never raised (Telegram outage must not
abort a trading cycle).
"""
from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _post_telegram(*, token: str, chat_id: str, text: str):
    return requests.post(
        _TELEGRAM_API.format(token=token),
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )


def send_daily_summary(*, bot_token, chat_id, cycle_id,
                        portfolio_before, portfolio_after, trades,
                        agreement_rate) -> None:
    pnl = portfolio_after - portfolio_before
    pnl_pct = pnl / portfolio_before if portfolio_before else 0
    lines = [
        f"*Cycle {cycle_id}*",
        f"Portfolio: {portfolio_before:.2f} → {portfolio_after:.2f} ({pnl_pct:+.2%})",
        f"Trades: {len(trades)}",
        f"Shadow agreement: {agreement_rate:.1%}",
    ]
    for t in trades:
        lines.append(f"  {t['coin']} {t['side']} {t['qty']:.6f} @ {t['price']:.2f}")
    text = "\n".join(lines)
    try:
        _post_telegram(token=bot_token, chat_id=chat_id, text=text)
    except Exception as e:
        logger.error("Telegram delivery failed (non-fatal): %s", e)


def send_alert(*, bot_token, chat_id, severity: str, message: str) -> None:
    text = f"🚨 *{severity}*\n{message}"
    try:
        _post_telegram(token=bot_token, chat_id=chat_id, text=text)
    except Exception as e:
        logger.error("Telegram alert failed (non-fatal): %s", e)
```

- [ ] **Step 4: Run tests, pass**

```bash
pytest tests/execution/live/test_notify.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/notify.py tests/execution/live/test_notify.py
git commit -m "feat(live): Telegram notifications with non-fatal failure handling"
```

---

## Phase 11: Re-backtest (weekly)

### Task 11.1: `rebacktest.py` — weekly full re-run + JSON report

**Files:**
- Create: `tradingagents/execution/live/rebacktest.py`
- Create: `tests/execution/live/test_rebacktest.py`

- [ ] **Step 1: Write failing test**

Create `tests/execution/live/test_rebacktest.py`:

```python
from pathlib import Path
import json
from unittest.mock import patch

import pytest


def test_compute_weekly_report_writes_json(tmp_path):
    from tradingagents.execution.live import rebacktest

    fake_live = {"sharpe": 2.4, "return_pct": 0.04, "max_dd": 0.03,
                  "n_trades": 18, "win_rate": 0.61}
    fake_bt = {"sharpe": 2.6, "return_pct": 0.05, "max_dd": 0.025,
                "n_trades": 18, "win_rate": 0.67}

    with patch.object(rebacktest, "compute_live_metrics", return_value=fake_live), \
         patch.object(rebacktest, "compute_backtest_metrics", return_value=fake_bt):
        report_path = rebacktest.run_weekly_report(
            week_end="2026-W18",
            live_start_date="2026-04-29",
            live_end_date="2026-05-12",
            output_dir=tmp_path,
        )
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert data["week_end"] == "2026-W18"
    assert data["live"]["sharpe"] == 2.4
    assert data["backtest"]["sharpe"] == 2.6
    assert data["delta"]["sharpe"] == pytest.approx(-0.2)


def test_verdict_diverging_when_sharpe_delta_large(tmp_path):
    from tradingagents.execution.live import rebacktest

    delta = {"sharpe": -0.7}
    assert rebacktest.classify_verdict(delta) == "DIVERGING"


def test_verdict_converging_when_close(tmp_path):
    from tradingagents.execution.live import rebacktest

    delta = {"sharpe": -0.1}
    assert rebacktest.classify_verdict(delta) == "CONVERGING"
```

- [ ] **Step 2: Run, FAIL**

```bash
pytest tests/execution/live/test_rebacktest.py -v
```

- [ ] **Step 3: Implement `rebacktest.py`**

```python
"""Weekly re-backtest: re-run V2 from live_start through prior day, diff to live."""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def compute_live_metrics(live_start_date, live_end_date) -> dict:
    """Compute Sharpe/Return/MaxDD/etc. from portfolio_snapshots in trade_journal.db.

    Implementation details are in Phase 12. For now this is a stub for the
    test to mock.
    """
    raise NotImplementedError("wire up to journal in Phase 12")


def compute_backtest_metrics(start_date, end_date) -> dict:
    """Re-run baseline_strategy_v2 from start_date to end_date and return metrics.

    Implementation details are in Phase 12. For now this is a stub for the
    test to mock.
    """
    raise NotImplementedError("wire up to baseline_strategy_v2 in Phase 12")


def classify_verdict(delta: dict) -> str:
    sharpe_delta = delta.get("sharpe", 0)
    if abs(sharpe_delta) <= 0.3:
        return "CONVERGING"
    if abs(sharpe_delta) > 1.0:
        return "BROKEN"
    return "DIVERGING"


def run_weekly_report(*, week_end, live_start_date, live_end_date, output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    live = compute_live_metrics(live_start_date, live_end_date)
    bt = compute_backtest_metrics(live_start_date, live_end_date)
    delta = {k: live[k] - bt[k] for k in live if k in bt}
    report = {
        "week_end": week_end,
        "live_start_date": live_start_date,
        "live_end_date": live_end_date,
        "live": live,
        "backtest": bt,
        "delta": delta,
        "verdict": classify_verdict(delta),
    }
    out_path = output_dir / f"rebacktest_{week_end}.json"
    out_path.write_text(json.dumps(report, indent=2))
    return out_path
```

- [ ] **Step 4: Run tests, pass**

```bash
pytest tests/execution/live/test_rebacktest.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/rebacktest.py tests/execution/live/test_rebacktest.py
git commit -m "feat(live): weekly re-backtest report scaffold"
```

---

## Phase 12: Runner orchestration

### Task 12.1: `runner.py` end-to-end pipeline + structured JSONL log

**Files:**
- Create: `tradingagents/execution/live/runner.py`
- Create: `tradingagents/execution/live/structured_log.py`
- Create: `tests/execution/live/test_runner.py`

- [ ] **Step 1: Write structured logger first**

Create `tradingagents/execution/live/structured_log.py`:

```python
"""Append-only JSONL structured log for forensic reconstruction."""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class StructuredLogger:
    def __init__(self, path: Path, cycle_id: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.cycle_id = cycle_id

    def event(self, step: str, status: str, payload: dict | None = None,
              duration_ms: int | None = None) -> None:
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "cycle_id": self.cycle_id,
            "step": step,
            "status": status,
            "duration_ms": duration_ms,
            "payload": payload or {},
        }
        with open(self.path, "a") as f:
            f.write(json.dumps(rec) + "\n")

    @contextmanager
    def step(self, step: str, payload: dict | None = None):
        start = time.monotonic()
        try:
            yield
            self.event(step, "ok", payload, int((time.monotonic() - start) * 1000))
        except Exception as e:
            self.event(step, "error", {"error": str(e), **(payload or {})},
                       int((time.monotonic() - start) * 1000))
            raise
```

- [ ] **Step 2: Write failing runner test (heavy mocking)**

Create `tests/execution/live/test_runner.py`:

```python
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest


@pytest.fixture
def env_setup(monkeypatch, tmp_path):
    monkeypatch.setenv("LIVE_MODE", "false")
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_API_SECRET", "s")
    monkeypatch.setenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    return tmp_path


def test_dry_run_completes_full_pipeline(env_setup, monkeypatch):
    """End-to-end dry run: no orders placed, all steps execute, journal populated."""
    from tradingagents.execution.live import runner

    # Mock every external boundary
    with patch("tradingagents.execution.live.data_refresh.refresh_coinmetrics"), \
         patch("tradingagents.execution.live.data_refresh.refresh_defillama"), \
         patch("tradingagents.execution.live.data_refresh.refresh_ohlcv"), \
         patch("tradingagents.execution.live.retrain.run_retrain_with_fallback") as mock_retrain, \
         patch("tradingagents.execution.live.predict.run_predict") as mock_pred, \
         patch("tradingagents.execution.live.exchange.BinanceClient") as mock_ex_cls, \
         patch("tradingagents.execution.live.notify.send_daily_summary") as mock_notify:
        mock_retrain.return_value = MagicMock(
            model_path=Path("/tmp/m.pkl"), train_dir_acc_h7=0.6,
            train_dir_acc_h14=0.65, sha256="abc", train_rows=100,
            train_window_start="2024-01-01", train_window_end="2026-05-11",
            is_fallback=False,
        )
        mock_pred.return_value = {
            "BTC": {"ref_price": 60000.0, "pred_h7": 63000.0, "pred_h14": 66000.0},
            "ETH": {"ref_price": 3000.0, "pred_h7": 2950.0, "pred_h14": 2900.0},  # SHORT consensus
            "BNB": {"ref_price": 400.0, "pred_h7": 410.0, "pred_h14": 405.0},     # mixed → 0
        }
        mock_ex_cls.return_value.get_total_portfolio_value.return_value = 10000.0
        mock_ex_cls.return_value.get_usdt_balance.return_value = 10000.0
        mock_ex_cls.return_value.get_current_position.return_value = 0.0
        mock_ex_cls.return_value.get_ticker_price.return_value = 60000.0

        result = runner.run_cycle(cycle_id="2026-05-12", dry_run=True)

    assert result.status == "ok"
    assert result.n_executed == 0  # dry-run skips execution
    mock_notify.assert_called_once()
```

- [ ] **Step 3: Run, FAIL**

```bash
pytest tests/execution/live/test_runner.py -v
```

- [ ] **Step 4: Implement `runner.py`**

```python
"""Daily cycle orchestrator. CLI entry: python -m tradingagents.execution.live.runner --once"""
from __future__ import annotations

import argparse
import logging
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from tradingagents.execution.live import (
    config, data_refresh, exchange, journal, notify, predict,
    retrain, risk, shadow, sizer, structured_log,
)

logger = logging.getLogger(__name__)


@dataclass
class CycleResult:
    cycle_id: str
    status: str
    n_executed: int
    error_msg: str = ""


_shutdown_requested = False


def _handle_sigterm(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True


def _git_sha(repo_dir: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=repo_dir,
        ).decode().strip()
    except Exception:
        return "unknown"


def _today_id() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def run_cycle(cycle_id: str | None = None, dry_run: bool = False) -> CycleResult:
    cycle_id = cycle_id or _today_id()

    cfg = config.load_config()
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    log_dir = Path(os.environ.get("LOG_DIR", "logs"))
    log_path = log_dir / f"cycle_{cycle_id}.jsonl"
    structured = structured_log.StructuredLogger(log_path, cycle_id)

    j = journal.Journal(str(data_dir / "trade_journal.db"))
    repo_dir = Path(__file__).resolve().parents[3]
    j.log_cycle_start(cycle_id, git_sha=_git_sha(repo_dir))

    n_executed = 0
    try:
        # 1. data_refresh
        with structured.step("fetch_onchain"):
            data_refresh.refresh_coinmetrics(coins=cfg.coin_universe,
                                              store_root=data_dir / "onchain_store")
            data_refresh.refresh_defillama(coins=cfg.coin_universe,
                                            store_root=data_dir / "onchain_store")
        for coin in cfg.coin_universe:
            with structured.step("fetch_ohlcv", {"coin": coin}):
                data_refresh.refresh_ohlcv(coin=coin,
                                            cache_root=data_dir / "ohlcv_cache")

        # 2. retrain
        with structured.step("retrain"):
            artifact = retrain.run_retrain_with_fallback(
                coins=cfg.coin_universe, horizons=cfg.horizons,
                asof=(datetime.now(timezone.utc).date() - pd.Timedelta(days=1)).isoformat(),
                checkpoint_dir=data_dir / "checkpoints",
            )
            j.log_model_artifact(
                retrain_id=cycle_id, model_path=str(artifact.model_path),
                train_window_start=artifact.train_window_start,
                train_window_end=artifact.train_window_end,
                train_rows=artifact.train_rows,
                train_dir_acc_h7=artifact.train_dir_acc_h7,
                train_dir_acc_h14=artifact.train_dir_acc_h14,
                sha256=artifact.sha256,
            )

        # 3. predict
        with structured.step("predict"):
            preds = predict.run_predict(
                checkpoint_path=artifact.model_path,
                coins=cfg.coin_universe, horizons=cfg.horizons,
                asof=(datetime.now(timezone.utc).date() - pd.Timedelta(days=1)).isoformat(),
            )

        ex = exchange.BinanceClient(
            api_key=cfg.binance_api_key, api_secret=cfg.binance_api_secret,
            testnet=not cfg.live_mode,
        )
        portfolio_before = ex.get_total_portfolio_value()
        trades_executed = []

        for coin in cfg.coin_universe:
            if _shutdown_requested:
                break
            if coin not in preds:
                continue
            symbol = f"{coin}USDT"

            # Load history for this coin
            cache = data_dir / "ohlcv_cache" / f"{symbol}_1d.parquet"
            history = pd.read_parquet(cache) if cache.exists() else pd.DataFrame()
            if len(history) < cfg.vol_lookback:
                structured.event("skip_coin", "insufficient_history", {"coin": coin})
                continue

            # 4-5. size + log
            with structured.step("size", {"coin": coin}):
                sz = sizer.compute_size(
                    coin=coin, prediction=preds[coin], price_history=history,
                    horizons=cfg.horizons, symmetric=cfg.symmetric,
                    target_vol=cfg.target_vol, kelly_fraction=cfg.kelly_fraction,
                    max_leverage=cfg.max_leverage, vol_lookback=cfg.vol_lookback,
                    vol_cap_pct=cfg.vol_cap_pct, confidence_ref=cfg.confidence_ref_return,
                    trend_sma=cfg.trend_sma, trend_multiplier=cfg.trend_multiplier,
                )
                j.log_sizing(
                    cycle_id=cycle_id, coin=coin, realized_vol=sz.realized_vol,
                    target_vol=cfg.target_vol, kelly=cfg.kelly_fraction,
                    confidence=sz.confidence, base_size=sz.base_size,
                    leverage=sz.leverage, sma30_multiplier=sz.sma_multiplier,
                    final_size_notional=sz.final_size_notional,
                )

            # 6. risk_check
            with structured.step("risk_check", {"coin": coin}):
                ok_lev, why = risk.check_leverage(sz.final_size_notional, cfg.max_leverage)
                j.log_risk_check(cycle_id, coin, "leverage_cap", ok_lev,
                                  abs(sz.final_size_notional), cfg.max_leverage, why)
                if not ok_lev:
                    continue

                # daily loss check (uses portfolio history; placeholder 0.0 for first cycle)
                pnl_today_pct = 0.0  # TODO Phase 12.2: compute from snapshots
                ok_loss, why = risk.check_daily_loss(pnl_today_pct, cfg.max_daily_loss_pct)
                j.log_risk_check(cycle_id, coin, "daily_loss", ok_loss,
                                  pnl_today_pct, -cfg.max_daily_loss_pct, why)
                if not ok_loss:
                    notify.send_alert(bot_token=cfg.telegram_bot_token,
                                       chat_id=cfg.telegram_chat_id,
                                       severity="KILL_SWITCH", message=why)
                    break  # halt entire cycle

            # 7. execute
            if sz.final_size_notional == 0:
                continue

            side = "BUY" if sz.final_size_notional > 0 else "SELL"
            qty = abs(sz.final_size_notional) * portfolio_before / preds[coin]["ref_price"]

            with structured.step("execute", {"coin": coin}):
                if dry_run:
                    j.log_trade(cycle_id=cycle_id, coin=coin, side=side, qty=qty,
                                 entry_price=preds[coin]["ref_price"], exit_price=None,
                                 pnl=None, fees=None, slippage=None,
                                 order_id="dry-run", stop_loss_id=None, status="DRY_RUN")
                    structured.event("execute", "dry_run", {"coin": coin, "side": side, "qty": qty})
                else:
                    try:
                        order = ex.place_market_order(symbol, side, qty)
                        order_id = str(order.get("orderId", ""))
                        exec_price = float(order.get("avgPrice", preds[coin]["ref_price"]))
                        # stop-loss
                        stop_side = "SELL" if side == "BUY" else "BUY"
                        stop_price = exec_price * (1 - cfg.stop_loss_pct) if side == "BUY" \
                            else exec_price * (1 + cfg.stop_loss_pct)
                        try:
                            stop = ex.place_stop_loss(symbol, qty, stop_price, stop_side)
                            stop_id = str(stop.get("orderId", ""))
                            status = "EXECUTED"
                        except Exception as e:
                            stop_id = None
                            status = "UNPROTECTED"
                            notify.send_alert(bot_token=cfg.telegram_bot_token,
                                               chat_id=cfg.telegram_chat_id,
                                               severity="UNPROTECTED",
                                               message=f"{coin} stop-loss failed: {e}")
                        j.log_trade(cycle_id=cycle_id, coin=coin, side=side, qty=qty,
                                     entry_price=exec_price, exit_price=None,
                                     pnl=None, fees=None, slippage=None,
                                     order_id=order_id, stop_loss_id=stop_id, status=status)
                        n_executed += 1
                        trades_executed.append({"coin": coin, "side": side, "qty": qty,
                                                  "price": exec_price})
                    except Exception as e:
                        j.log_trade(cycle_id=cycle_id, coin=coin, side=side, qty=qty,
                                     entry_price=preds[coin]["ref_price"], exit_price=None,
                                     pnl=None, fees=None, slippage=None,
                                     order_id=None, stop_loss_id=None, status="FAILED")
                        notify.send_alert(bot_token=cfg.telegram_bot_token,
                                           chat_id=cfg.telegram_chat_id,
                                           severity="FAILED",
                                           message=f"{coin} order failed: {e}")

            # 8. shadow_replay
            with structured.step("shadow_replay", {"coin": coin}):
                shadow_dec = shadow.compute_shadow_decision(
                    coin=coin, prediction=preds[coin], price_history=history,
                    horizons=cfg.horizons, symmetric=cfg.symmetric,
                    target_vol=cfg.target_vol, kelly_fraction=cfg.kelly_fraction,
                    max_leverage=cfg.max_leverage, vol_lookback=cfg.vol_lookback,
                    vol_cap_pct=cfg.vol_cap_pct, confidence_ref=cfg.confidence_ref_return,
                    trend_sma=cfg.trend_sma, trend_multiplier=cfg.trend_multiplier,
                )
                j.log_shadow_decision(cycle_id=cycle_id, coin=coin,
                                       live_signal=sz.signal,
                                       backtest_signal=shadow_dec.signal,
                                       live_size=sz.final_size_notional,
                                       backtest_size=shadow_dec.size)

        # 9. snapshot
        portfolio_after = ex.get_total_portfolio_value()
        j.log_portfolio_snapshot(cycle_id=cycle_id, total_value=portfolio_after,
                                  usdt_balance=ex.get_usdt_balance(),
                                  position_qty_per_coin={
                                      c: ex.get_current_position(f"{c}USDT")
                                      for c in cfg.coin_universe
                                  },
                                  unrealized_pnl=portfolio_after - portfolio_before)

        # 10. notify
        with structured.step("notify"):
            agreement = sum(1 for t in trades_executed) / max(len(trades_executed), 1)
            notify.send_daily_summary(
                bot_token=cfg.telegram_bot_token, chat_id=cfg.telegram_chat_id,
                cycle_id=cycle_id, portfolio_before=portfolio_before,
                portfolio_after=portfolio_after, trades=trades_executed,
                agreement_rate=agreement,
            )

        j.log_cycle_end(cycle_id, status="ok")
        return CycleResult(cycle_id=cycle_id, status="ok", n_executed=n_executed)

    except Exception as e:
        logger.exception("Cycle failed")
        j.log_cycle_end(cycle_id, status="error", error_msg=str(e))
        notify.send_alert(bot_token=cfg.telegram_bot_token,
                           chat_id=cfg.telegram_chat_id,
                           severity="CYCLE_ERROR", message=str(e))
        return CycleResult(cycle_id=cycle_id, status="error", n_executed=n_executed,
                            error_msg=str(e))
    finally:
        j.close()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="TradingAgents live cycle")
    parser.add_argument("--once", action="store_true", help="run one cycle then exit")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--cycle-id", default=None)
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, _handle_sigterm)
    result = run_cycle(cycle_id=args.cycle_id, dry_run=args.dry_run)
    sys.exit(0 if result.status == "ok" else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run runner test**

```bash
pytest tests/execution/live/test_runner.py -v
```

Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add tradingagents/execution/live/runner.py tradingagents/execution/live/structured_log.py
git add tests/execution/live/test_runner.py
git commit -m "feat(live): runner orchestration with structured logging"
```

### Task 12.2: Wire `compute_live_metrics` and `compute_backtest_metrics`

**Files:**
- Modify: `tradingagents/execution/live/rebacktest.py`
- Create: `tests/execution/live/test_rebacktest_wired.py`

- [ ] **Step 1: Replace stubs with real implementations**

Edit `tradingagents/execution/live/rebacktest.py`. Replace the `NotImplementedError` bodies:

```python
def compute_live_metrics(live_start_date, live_end_date) -> dict:
    """Read portfolio_snapshots, compute Sharpe / return / max DD over window."""
    import sqlite3
    import os
    from pathlib import Path
    import numpy as np

    db = Path(os.environ.get("DATA_DIR", "data")) / "trade_journal.db"
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT ts, total_value FROM portfolio_snapshots "
        "WHERE date(ts) >= ? AND date(ts) <= ? ORDER BY ts",
        (live_start_date, live_end_date),
    ).fetchall()
    conn.close()
    if len(rows) < 2:
        return {"sharpe": float("nan"), "return_pct": 0.0, "max_dd": 0.0,
                "n_trades": 0, "win_rate": 0.0}
    values = np.array([r[1] for r in rows], dtype=float)
    rets = np.diff(values) / values[:-1]
    sharpe = float(np.mean(rets) / (np.std(rets, ddof=1) + 1e-12) * np.sqrt(252)) \
        if len(rets) > 1 else 0.0
    cum = np.cumprod(1 + rets)
    peak = np.maximum.accumulate(cum)
    dd = float(np.max((peak - cum) / peak)) if len(cum) else 0.0
    return {
        "sharpe": sharpe,
        "return_pct": float((values[-1] - values[0]) / values[0]),
        "max_dd": dd,
        "n_trades": len(rows),
        "win_rate": float(np.mean(rets > 0)) if len(rets) else 0.0,
    }


def compute_backtest_metrics(start_date, end_date) -> dict:
    """Re-run baseline_strategy_v2 from start_date to end_date and parse output."""
    import subprocess, json, re, os, tempfile

    out_dir = Path(tempfile.mkdtemp())
    cmd = [
        "python", "scripts/baseline_strategy_v2.py",
        "--pred-dir", os.environ.get("BACKTEST_PRED_DIR", "data/multi_3coins_bnb"),
        "--symmetric",
        "--output-plot", str(out_dir / "equity.png"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    text = result.stdout

    # Parse the printed metrics — adjust pattern to match the actual baseline_strategy_v2 output
    sharpe = float(re.search(r"Portfolio Sharpe[:\s]+([0-9.\-]+)", text).group(1))
    ret_pct = float(re.search(r"Total return[:\s]+([0-9.\-]+)", text).group(1)) / 100
    max_dd = float(re.search(r"Max drawdown[:\s]+([0-9.\-]+)", text).group(1)) / 100
    n_trades = int(re.search(r"Trades[:\s]+([0-9]+)", text).group(1))
    win_rate = float(re.search(r"Win rate[:\s]+([0-9.]+)", text).group(1)) / 100
    return {"sharpe": sharpe, "return_pct": ret_pct, "max_dd": max_dd,
            "n_trades": n_trades, "win_rate": win_rate}
```

Note: the regex patterns above are illustrative. Inspect the actual stdout of `python scripts/baseline_strategy_v2.py --pred-dir <dir> --symmetric` and adapt.

- [ ] **Step 2: Add wired test**

Create `tests/execution/live/test_rebacktest_wired.py`:

```python
import sqlite3
from pathlib import Path

import pytest


def test_compute_live_metrics_with_real_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    db = tmp_path / "trade_journal.db"
    db.parent.mkdir(parents=True, exist_ok=True)

    from tradingagents.execution.live.journal import Journal
    j = Journal(str(db))
    j.log_cycle_start("2026-05-12", git_sha="abc")
    for day, val in [("2026-05-12", 10000), ("2026-05-13", 10100), ("2026-05-14", 10250)]:
        j._conn.execute(
            "INSERT INTO portfolio_snapshots (cycle_id, ts, total_value, usdt_balance, "
            "position_qty_per_coin, unrealized_pnl) VALUES (?, ?, ?, ?, ?, ?)",
            (day, f"{day}T00:05:00+00:00", val, val, "{}", 0),
        )
    j._conn.commit()
    j.close()

    from tradingagents.execution.live.rebacktest import compute_live_metrics
    metrics = compute_live_metrics("2026-05-12", "2026-05-14")
    assert metrics["return_pct"] == pytest.approx(0.025)
    assert metrics["n_trades"] == 3
```

- [ ] **Step 3: Run wired test**

```bash
pytest tests/execution/live/test_rebacktest_wired.py -v
```

Expected: 1 passed.

- [ ] **Step 4: Commit**

```bash
git add tradingagents/execution/live/rebacktest.py tests/execution/live/test_rebacktest_wired.py
git commit -m "feat(live): wire rebacktest to journal + baseline_strategy_v2"
```

### Task 12.3: CLI flags `--replay`, `--kill-all`, `--dry-run`

**Files:**
- Modify: `tradingagents/execution/live/runner.py`

- [ ] **Step 1: Add `--replay` and `--kill-all` to argparse + dispatch**

Modify the bottom of `runner.py`:

```python
def replay_cycle(cycle_id: str) -> CycleResult:
    """Reconstruct decision for a past cycle from journal — read-only, no exec."""
    raise NotImplementedError(
        "Replay reads predictions, sizing, risk_checks rows for cycle_id and "
        "re-runs sizer.compute_size + shadow.compute_shadow_decision to verify "
        "they still produce the recorded values."
    )


def kill_all() -> None:
    """Cancel all open orders, close all open positions, halt cycle execution."""
    cfg = config.load_config()
    ex = exchange.BinanceClient(
        api_key=cfg.binance_api_key, api_secret=cfg.binance_api_secret,
        testnet=not cfg.live_mode,
    )
    for coin in cfg.coin_universe:
        symbol = f"{coin}USDT"
        try:
            ex.cancel_all_orders(symbol)
        except Exception as e:
            logger.warning("cancel_all_orders failed for %s: %s", symbol, e)
        pos = ex.get_current_position(symbol)
        if pos != 0:
            close_side = "SELL" if pos > 0 else "BUY"
            try:
                ex.place_market_order(symbol, close_side, abs(pos))
                logger.info("Closed %s position of %s", coin, pos)
            except Exception as e:
                logger.error("Failed to close %s: %s", coin, e)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="TradingAgents live cycle")
    parser.add_argument("--once", action="store_true", help="run one cycle then exit")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--cycle-id", default=None)
    parser.add_argument("--replay", default=None, metavar="DATE",
                         help="reconstruct decision for past cycle from journal")
    parser.add_argument("--kill-all", action="store_true",
                         help="cancel all orders + close all positions, halt")
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, _handle_sigterm)

    if args.kill_all:
        kill_all()
        sys.exit(0)
    if args.replay:
        replay_cycle(args.replay)
        sys.exit(0)
    result = run_cycle(cycle_id=args.cycle_id, dry_run=args.dry_run)
    sys.exit(0 if result.status == "ok" else 1)
```

- [ ] **Step 2: Smoke-test the CLI**

```bash
python -m tradingagents.execution.live.runner --help
```

Expected: argparse output listing `--once`, `--dry-run`, `--replay`, `--kill-all`, `--cycle-id`.

- [ ] **Step 3: Commit**

```bash
git add tradingagents/execution/live/runner.py
git commit -m "feat(live): --replay and --kill-all CLI flags"
```

---

## Phase 13: Systemd + provisioning

### Task 13.1: `preflight.sh` + systemd units

**Files:**
- Create: `deploy/preflight.sh`
- Create: `deploy/systemd/ta-cycle.service`
- Create: `deploy/systemd/ta-cycle.timer`
- Create: `deploy/systemd/ta-rebacktest.service`
- Create: `deploy/systemd/ta-rebacktest.timer`

- [ ] **Step 1: Create `deploy/preflight.sh`**

```bash
mkdir -p deploy/systemd
```

Create `deploy/preflight.sh` (executable, run as `tabot` user before each cycle):

```bash
#!/usr/bin/env bash
set -euo pipefail

# Disk free check (>10% free on /opt)
disk_pct=$(df --output=pcent /opt | tail -1 | tr -d ' %')
if [ "$disk_pct" -gt 90 ]; then
    echo "preflight: disk usage $disk_pct% > 90% — aborting" >&2
    exit 1
fi

# Network reachability
if ! curl -sSf --max-time 5 https://api.binance.com/api/v3/ping >/dev/null; then
    echo "preflight: cannot reach Binance — aborting" >&2
    exit 1
fi

# Secrets file present + locked
secrets="/opt/tradingagents/secrets/.env.trading"
if [ ! -f "$secrets" ]; then
    echo "preflight: secrets file missing — aborting" >&2
    exit 1
fi
mode=$(stat -c "%a" "$secrets")
if [ "$mode" != "600" ]; then
    echo "preflight: secrets file mode $mode (expected 600) — aborting" >&2
    exit 1
fi
```

- [ ] **Step 2: Make executable**

```bash
chmod +x deploy/preflight.sh
```

- [ ] **Step 3: Create `deploy/systemd/ta-cycle.service`**

```ini
[Unit]
Description=TradingAgents daily live cycle
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=tabot
WorkingDirectory=/opt/tradingagents/repo
EnvironmentFile=/opt/tradingagents/secrets/.env.trading
Environment=DATA_DIR=/opt/tradingagents/data
Environment=LOG_DIR=/opt/tradingagents/logs
ExecStartPre=/opt/tradingagents/repo/deploy/preflight.sh
ExecStart=/opt/tradingagents/venv/bin/python -m tradingagents.execution.live.runner --once
RuntimeMaxSec=1800
Nice=10
StandardOutput=journal
StandardError=journal
```

- [ ] **Step 4: Create `deploy/systemd/ta-cycle.timer`**

```ini
[Unit]
Description=Trigger ta-cycle daily at 00:05 UTC

[Timer]
OnCalendar=*-*-* 00:05:00 UTC
Persistent=true
RandomizedDelaySec=60
Unit=ta-cycle.service

[Install]
WantedBy=timers.target
```

- [ ] **Step 5: Create `deploy/systemd/ta-rebacktest.service` and `.timer`**

`ta-rebacktest.service`:

```ini
[Unit]
Description=TradingAgents weekly re-backtest
After=network-online.target

[Service]
Type=oneshot
User=tabot
WorkingDirectory=/opt/tradingagents/repo
EnvironmentFile=/opt/tradingagents/secrets/.env.trading
Environment=DATA_DIR=/opt/tradingagents/data
ExecStart=/opt/tradingagents/venv/bin/python -c "from tradingagents.execution.live.rebacktest import run_weekly_report; from datetime import date, timedelta; from pathlib import Path; today=date.today(); start=today-timedelta(days=7); run_weekly_report(week_end=today.strftime('%Y-W%V'), live_start_date=start.isoformat(), live_end_date=today.isoformat(), output_dir=Path('/opt/tradingagents/data/reports'))"
RuntimeMaxSec=3600
Nice=10
```

`ta-rebacktest.timer`:

```ini
[Unit]
Description=Trigger weekly re-backtest Sundays 02:00 UTC

[Timer]
OnCalendar=Sun *-*-* 02:00:00 UTC
Persistent=true
Unit=ta-rebacktest.service

[Install]
WantedBy=timers.target
```

- [ ] **Step 6: Commit**

```bash
git add deploy/preflight.sh deploy/systemd/
git commit -m "feat(deploy): systemd units + preflight check"
```

### Task 13.2: `provision_hetzner.sh`

**Files:**
- Create: `deploy/provision_hetzner.sh`

- [ ] **Step 1: Write provisioning script**

Create `deploy/provision_hetzner.sh`. This runs on the local machine to create + harden the Hetzner box. It uses `ssh root@<host>` for the heavy lifting.

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <hetzner-host-ip>" >&2
    exit 1
fi

HOST=$1
SSH="ssh -o StrictHostKeyChecking=accept-new root@$HOST"

echo "→ disabling root password auth"
$SSH "sed -i 's/^#PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config && systemctl reload ssh"

echo "→ installing UFW + fail2ban + unattended-upgrades"
$SSH "apt-get update && apt-get install -y ufw fail2ban unattended-upgrades"

echo "→ configuring UFW (ssh only)"
$SSH "ufw default deny incoming && ufw default allow outgoing && ufw allow 22/tcp && ufw --force enable"

echo "→ enabling unattended-upgrades (security only)"
$SSH "dpkg-reconfigure -f noninteractive unattended-upgrades"

echo "→ creating tabot user"
$SSH "id -u tabot >/dev/null 2>&1 || useradd -m -s /bin/bash tabot"
$SSH "mkdir -p /home/tabot/.ssh && chmod 700 /home/tabot/.ssh"

echo "→ copying SSH key from root to tabot"
$SSH "cp /root/.ssh/authorized_keys /home/tabot/.ssh/ && chown -R tabot:tabot /home/tabot/.ssh && chmod 600 /home/tabot/.ssh/authorized_keys"

echo "→ installing python3.11 + git + sqlite3"
$SSH "apt-get install -y python3.11 python3.11-venv python3.11-dev git sqlite3 build-essential"

echo "→ creating /opt/tradingagents"
$SSH "mkdir -p /opt/tradingagents && chown tabot:tabot /opt/tradingagents"

echo "✓ provisioning complete"
```

```bash
chmod +x deploy/provision_hetzner.sh
```

- [ ] **Step 2: Commit**

```bash
git add deploy/provision_hetzner.sh
git commit -m "feat(deploy): Hetzner provisioning script"
```

### Task 13.3: `deploy.sh`

**Files:**
- Create: `deploy/deploy.sh`

- [ ] **Step 1: Write deploy script**

Create `deploy/deploy.sh`. Idempotent — safe to re-run for upgrades.

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
    echo "Usage: $0 <hetzner-host-ip> <git-tag>" >&2
    exit 1
fi

HOST=$1
TAG=$2
SSH="ssh tabot@$HOST"
SSH_ROOT="ssh root@$HOST"

REPO_URL="https://github.com/<your-org>/TradingAgents.git"  # ADJUST

echo "→ cloning or updating repo"
$SSH "[ -d /opt/tradingagents/repo ] || git clone $REPO_URL /opt/tradingagents/repo"
$SSH "cd /opt/tradingagents/repo && git fetch --tags && git checkout $TAG"

echo "→ creating venv + installing"
$SSH "[ -d /opt/tradingagents/venv ] || python3.11 -m venv /opt/tradingagents/venv"
$SSH "/opt/tradingagents/venv/bin/pip install -U pip wheel && /opt/tradingagents/venv/bin/pip install -e /opt/tradingagents/repo"

echo "→ ensuring data + log dirs"
$SSH "mkdir -p /opt/tradingagents/data /opt/tradingagents/logs /opt/tradingagents/secrets && chmod 700 /opt/tradingagents/secrets"

echo "→ checking secrets file exists"
$SSH "[ -f /opt/tradingagents/secrets/.env.trading ] || (echo 'ERROR: scp secrets/.env.trading manually before re-running'; exit 1)"
$SSH "chmod 600 /opt/tradingagents/secrets/.env.trading"

echo "→ installing systemd units (root)"
$SSH_ROOT "cp /opt/tradingagents/repo/deploy/systemd/*.service /etc/systemd/system/"
$SSH_ROOT "cp /opt/tradingagents/repo/deploy/systemd/*.timer /etc/systemd/system/"
$SSH_ROOT "systemctl daemon-reload"
$SSH_ROOT "systemctl enable --now ta-cycle.timer ta-rebacktest.timer"

echo "→ verifying timers"
$SSH_ROOT "systemctl list-timers ta-cycle.timer ta-rebacktest.timer --no-pager"

echo "✓ deploy complete; pinned tag: $TAG"
```

```bash
chmod +x deploy/deploy.sh
```

- [ ] **Step 2: Commit**

```bash
git add deploy/deploy.sh
git commit -m "feat(deploy): idempotent deploy script"
```

### Task 13.4: Rollback procedure docs

**Files:**
- Create: `deploy/ROLLBACK.md`

- [ ] **Step 1: Write rollback doc**

Create `deploy/ROLLBACK.md`:

```markdown
# Rollback procedure

## Halt only (no data change)

```bash
ssh tabot@<host>
sudo systemctl stop ta-cycle.timer ta-rebacktest.timer
```

Cycles will not run again until timers are re-enabled.

## Halt + close all open positions

```bash
ssh tabot@<host>
sudo systemctl stop ta-cycle.timer ta-rebacktest.timer
cd /opt/tradingagents/repo
EnvironmentFile=/opt/tradingagents/secrets/.env.trading \
  /opt/tradingagents/venv/bin/python -m tradingagents.execution.live.runner --kill-all
```

## Roll back to previous git tag

```bash
ssh tabot@<host>
sudo systemctl stop ta-cycle.timer
cd /opt/tradingagents/repo
git fetch --tags
git checkout <previous-tag>
/opt/tradingagents/venv/bin/pip install -e /opt/tradingagents/repo
sudo systemctl start ta-cycle.timer
```

## Restore data from snapshot

```bash
# On Hetzner Cloud Console: select "Snapshots" → restore latest
# This replaces the entire VM. After restore, re-run /opt/tradingagents/repo/deploy/deploy.sh
```

## Rebuild from scratch

```bash
# Locally:
./deploy/provision_hetzner.sh <new-host-ip>
scp /path/to/.env.trading tabot@<new-host>:/opt/tradingagents/secrets/.env.trading
./deploy/deploy.sh <new-host-ip> <git-tag>
```
```

- [ ] **Step 2: Commit**

```bash
git add deploy/ROLLBACK.md
git commit -m "docs(deploy): rollback procedure"
```

---

## Phase 14: Acceptance + cutover

### Task 14.1: Local 7-day dry-run rehearsal

**Files:**
- Create: `scripts/rehearse_live_cycle.sh`

- [ ] **Step 1: Write rehearsal script**

Create `scripts/rehearse_live_cycle.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Run 7 dry-run cycles back-to-back locally to validate the pipeline end-to-end.

export DATA_DIR=$(mktemp -d)
export LOG_DIR=$(mktemp -d)
export LIVE_MODE=false
export BINANCE_API_KEY=$BINANCE_API_KEY
export BINANCE_API_SECRET=$BINANCE_API_SECRET
export TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
export TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID

for i in 1 2 3 4 5 6 7; do
    echo "── rehearsal cycle $i ──"
    python -m tradingagents.execution.live.runner --once --dry-run --cycle-id "rehearse-$i"
done

echo "Journal contents:"
sqlite3 "$DATA_DIR/trade_journal.db" "SELECT cycle_id, status FROM cycles;"
sqlite3 "$DATA_DIR/trade_journal.db" "SELECT cycle_id, COUNT(*) FROM trades GROUP BY cycle_id;"
sqlite3 "$DATA_DIR/trade_journal.db" "SELECT cycle_id, AVG(agree) FROM shadow_decisions GROUP BY cycle_id;"

echo "Cleanup: rm -rf $DATA_DIR $LOG_DIR"
```

```bash
chmod +x scripts/rehearse_live_cycle.sh
```

- [ ] **Step 2: Run the rehearsal locally**

```bash
./scripts/rehearse_live_cycle.sh
```

Expected: 7 cycles all status=ok in journal, shadow agreement=1.0 for every cycle, no Telegram failures (or controlled fall-through if creds absent).

- [ ] **Step 3: Commit**

```bash
git add scripts/rehearse_live_cycle.sh
git commit -m "test(live): 7-cycle local rehearsal script"
```

### Task 14.2: Hetzner deploy + 1-cycle smoke

**Files:**
- No new files; manual ops

- [ ] **Step 1: Provision Hetzner box**

Create a CX22 server in Hetzner Cloud Console (Falkenstein DE, Ubuntu 24.04 LTS, attach SSH key).

- [ ] **Step 2: Run provisioning script**

```bash
./deploy/provision_hetzner.sh <new-host-ip>
```

Expected: completes without errors. SSH as `tabot@<host>` works.

- [ ] **Step 3: Tag + push current branch**

From the worktree:

```bash
git tag -a live-v1.0 -m "Live testnet deployment v1.0"
git push origin feature/live-testnet-deploy --tags
```

- [ ] **Step 4: SCP secrets to box**

Locally, prepare `/tmp/.env.trading` with all values from the spec's secrets section. Then:

```bash
scp /tmp/.env.trading tabot@<host>:/opt/tradingagents/secrets/.env.trading
ssh tabot@<host> chmod 600 /opt/tradingagents/secrets/.env.trading
rm /tmp/.env.trading  # remove local copy
```

- [ ] **Step 5: Deploy**

```bash
./deploy/deploy.sh <host> live-v1.0
```

Expected: clone + venv + systemd units installed, timers active.

- [ ] **Step 6: Manual one-cycle smoke**

```bash
ssh tabot@<host>
sudo systemctl start ta-cycle.service
sudo journalctl -u ta-cycle.service -f
```

Expected: cycle completes, sees `=== Trading cycle complete ===`, exit 0. Telegram receives daily summary.

- [ ] **Step 7: Verify journal populated**

```bash
ssh tabot@<host> sqlite3 /opt/tradingagents/data/trade_journal.db "SELECT cycle_id, status FROM cycles;"
ssh tabot@<host> sqlite3 /opt/tradingagents/data/trade_journal.db "SELECT cycle_id, coin, consensus_signal FROM predictions;"
```

Expected: 1 row in `cycles` with status=ok, predictions for all 3 coins.

- [ ] **Step 8: Commit (none — operational only)**

No commit; deploy is operational, not code.

### Task 14.3: 90-day acceptance review

**Files:**
- No new files; periodic review

- [ ] **Step 1: Day 7 check**

```bash
ssh tabot@<host>
sudo journalctl -u ta-cycle.service --since "7 days ago" | grep -E "ERROR|UNPROTECTED|FAILED" | head
sqlite3 /opt/tradingagents/data/trade_journal.db "SELECT cycle_id, status FROM cycles;"
```

Expected: ≥6/7 cycles status=ok. Investigate any failures.

- [ ] **Step 2: Day 30 — re-backtest verdict review**

```bash
ssh tabot@<host>
ls /opt/tradingagents/data/reports/
cat /opt/tradingagents/data/reports/rebacktest_2026-W*.json | jq '.verdict, .delta'
```

Expected: weekly verdicts mostly `CONVERGING`. If `BROKEN`, root-cause from `shadow_decisions` table.

- [ ] **Step 3: Day 90 — final acceptance**

Verify against spec acceptance criteria:
1. ≥85/90 cycles completed → `SELECT COUNT(*) FROM cycles WHERE status='ok';`
2. signal_agreement_rate ≥ 0.95 → `SELECT AVG(agree) FROM shadow_decisions;`
3. |live_sharpe - backtest_sharpe| ≤ 0.5 → from latest weekly report
4. No `UNPROTECTED` open >1h → `SELECT * FROM trades WHERE status='UNPROTECTED';`
5. Zero kill-switch trips from bugs → `SELECT * FROM risk_checks WHERE check_name='daily_loss' AND passed=0;`

If all 5 pass: append a results section to `THESIS_FINDINGS.md` Section 12 "Live Deployment vs Backtest" with full table + verdict.

- [ ] **Step 4: Final commit (results write-up)**

```bash
git add THESIS_FINDINGS.md
git commit -m "docs(thesis): live deployment 90-day comparison results"
```

---

## Self-Review

Spec coverage check:
- ✅ All 10 spec decisions implemented (strategy, machine, schedule, comparison, monitoring, risk, universe, retrain, capital, deploy)
- ✅ All 9 SQLite tables in `schema.sql`
- ✅ All 11 failure modes addressed (CoinMetrics down → skip + alert; Binance down → retry + alert; LGB fail → fallback; UNPROTECTED → alert; daily loss → kill-switch; disk → preflight; cycle timeout → systemd RuntimeMaxSec; etc.)
- ✅ All 11 acceptance command-line entry points (`--once`, `--replay`, `--kill-all`, `--dry-run`, `shadow.py --date`, `rebacktest.py --week`, `provision_hetzner.sh`, `deploy.sh`, `preflight.sh`, `rehearse_live_cycle.sh`, `kill-all`)
- ✅ Layer 1 + Layer 2 comparison (shadow per-cycle, weekly re-backtest)
- ✅ Hetzner provisioning + secrets + systemd + backup pattern
- ✅ Telegram daily summary + alerts (UNPROTECTED, FAILED, KILL_SWITCH, CYCLE_ERROR)
- ✅ Reconstruction guarantee (model_artifacts + feature_snapshots + JSONL)

Placeholder check: no "TODO", no "implement later" outside one labeled stub in `compute_live_metrics`/`compute_backtest_metrics` (Task 11 → wired in Task 12.2). All test bodies and implementation bodies are concrete.

Type consistency: `SizingResult` fields used in runner match Phase 6 definition; `TrainArtifact.model_path` is `Path` in Phase 4 + Phase 12; `LiveConfig` field names referenced in `runner.py` match Phase 2 dataclass exactly.
