# V5 MIX TP/SL Intrabar OHLC Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-run the §29 close-only 378-cell SL/EE/TP sweep with intrabar OHLC fill rules (low ≤ SL price; high ≥ TP price; SL-first on same-bar collision) and report whether the §29 finding (best cell ΔSR ≥ +0.15 vs baseline, EE-disabled dominates) survives intrabar wick risk. Output drives a confirm/reject verdict for the §29 result.

**Architecture:** Add an opt-in `intrabar: bool = False` plus `highs` / `lows` arrays to `run_coin_backtest`. When enabled, on each bar check intrabar fills before applying the close-to-close return; truncate the bar's gross return at the fill price; same-bar collision is SL-first pessimistic. Position-builder is unchanged (EE stays close-only by spec). New sweep harness mirrors `v5_mix_sltp_sweep.py` with the OHLC inputs and adds `n_intrabar_sl` / `n_intrabar_tp` diagnostic columns.

**Tech Stack:** Python 3.10, pandas, numpy, matplotlib, pytest, existing project modules (`scripts/baseline_strategy_v2.py`, `scripts/baseline_v5_mix.py`, `scripts/v5_mix_sltp_sweep.py`, `tradingagents.dataflows.coingecko_binance`).

**Spec:** `docs/superpowers/specs/2026-05-19-v5-sltp-intrabar-design.md`

**Branch:** `feature/v5-sltp-sweep-intrabar` (already created, spec committed at `3235836`)

---

## File Map

| Path | Status | Responsibility |
|---|---|---|
| `scripts/baseline_strategy_v2.py` | Modify | Add `intrabar`, `highs`, `lows` kwargs to `run_coin_backtest`. Track `entry_price` when intrabar. Intrabar SL/TP check truncates bar return at fill. |
| `scripts/v5_mix_sltp_sweep_intrabar.py` | Create | Sweep harness with OHLC inputs + per-cell intrabar fill counts |
| `scripts/v5_sltp_intrabar_report.py` | Create | top-20 + 12 heatmaps + `comparison.md` (side-by-side vs §29 top-5) |
| `tests/strategies/test_sltp_intrabar.py` | Create | 7 unit + integration tests covering bit-identity, intrabar SL fire, intrabar TP fire, same-bar collision (SL-first), required-arrays guard, slow baseline reproduction (close-only AND intrabar) |
| `THESIS_FINDINGS.md` | Modify | Append §30 (verdict) + append cross-reference line to §29 |
| `data/v5_sltp_sweep_intrabar/` | Runtime | results.csv, summary.json, top20.md, comparison.md, heatmaps/*.png, sweep.log |

---

## Task 1: Intrabar engine path (TDD red, then green)

**Files:**
- Modify: `scripts/baseline_strategy_v2.py:80-152` (function `run_coin_backtest`)
- Create: `tests/strategies/test_sltp_intrabar.py`

- [ ] **Step 1.1: Write the failing intrabar-SL test**

Create `tests/strategies/test_sltp_intrabar.py`:

```python
# tests/strategies/test_sltp_intrabar.py
"""Tests for the intrabar OHLC SL/TP path in run_coin_backtest."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402


_COSTS_NO = dict(
    fee_rate=0.0, slippage=0.0, spread=0.0,
    price_impact=0.0, funding_rate=0.0,
    max_portfolio_dd=1.0,
)


def test_intrabar_sl_truncates_bar_return_at_sl_price():
    """Long position, price ramps down. On bar where low <= entry*(1-SL),
    bar return must be SL%, not the full close-to-close drop."""
    n = 10
    dates = np.arange(n)
    # Open long at bar 1 at close 100. Subsequent close drops 1%/bar. At bar 5,
    # close = 100*0.96 = 96.06, but we engineer low[5] = 94 (-6% wick).
    closes = np.array([100.0] * n)
    closes[1:] = 100.0 * (0.99 ** np.arange(n - 1))
    highs = closes * 1.001
    lows = closes.copy()
    lows[5] = 93.0  # deep wick below SL=5% from entry close=100
    positions = np.ones(n)

    eq, _ = run_coin_backtest(
        dates=dates, prices=closes, positions=positions,
        initial_capital=10_000.0,
        stop_loss=0.05, take_profit=0.0,
        intrabar=True, highs=highs, lows=lows,
        **_COSTS_NO,
    )
    eq = np.asarray(eq)

    # Bar-5 return must equal SL fill (entry=closes[4], fill=entry*0.95):
    # Bar enters with prev close as entry equity reference. Just check:
    # the bar-5 step lost EXACTLY 5% from its entry_price (the close at bar 4),
    # NOT the close-to-close drop that day (which would be smaller, ~1%).
    # Easiest invariant: equity at bar 5 must be strictly lower than the
    # close-only-no-SL equity at bar 5 — because the wick truncated harder.
    eq_no_intrabar, _ = run_coin_backtest(
        dates=dates, prices=closes, positions=positions,
        initial_capital=10_000.0,
        stop_loss=0.05, take_profit=0.0,
        intrabar=False,
        **_COSTS_NO,
    )
    eq_no_intrabar = np.asarray(eq_no_intrabar)
    assert eq[5] < eq_no_intrabar[5], (
        f"intrabar SL must reduce equity at bar 5 vs close-only path: "
        f"intrabar={eq[5]:.2f} close-only={eq_no_intrabar[5]:.2f}"
    )
```

- [ ] **Step 1.2: Run the test, confirm it fails**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_intrabar.py::test_intrabar_sl_truncates_bar_return_at_sl_price -xvs
```

Expected: `TypeError: run_coin_backtest() got an unexpected keyword argument 'intrabar'`.

- [ ] **Step 1.3: Modify `scripts/baseline_strategy_v2.py:run_coin_backtest`**

Read the function (currently ~lines 80-152). Apply these edits exactly:

**Signature additions** (after `take_profit: float = 0.0,`):
```python
    intrabar: bool = False,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
```

**Validation at function start**, immediately after the docstring:
```python
    if intrabar and (highs is None or lows is None):
        raise ValueError(
            "run_coin_backtest: intrabar=True requires both highs and lows arrays"
        )
```

**Add `entry_price` state** alongside the existing `entry_equity = initial_capital` (~line 97-98):
```python
    entry_price = 0.0
```

**Update entry-price tracking** in the existing block (~line 119-123):
```python
        if target_pos != prev_pos and target_pos != 0:
            entry_equity = equity[-1]
            entry_price = p_prev  # NEW: opened this bar at prev close
        if target_pos == 0 and prev_pos != 0:
            entry_equity = equity[-1]
            entry_price = 0.0     # NEW: closed
```

**Insert intrabar fill check BEFORE the `price_return = ...` line** (currently ~line 124-125). The new block:

```python
        # Intrabar SL/TP — runs before close-to-close return is computed.
        intrabar_fill_price = None
        intrabar_exit_reason = None
        if intrabar and target_pos != 0 and entry_price > 0:
            hi = highs[i]
            lo = lows[i]
            if target_pos > 0:
                sl_price = entry_price * (1 - stop_loss) if stop_loss > 0 else 0.0
                tp_price = entry_price * (1 + take_profit) if take_profit > 0 else float("inf")
                hit_sl = (sl_price > 0 and lo <= sl_price)
                hit_tp = (take_profit > 0 and hi >= tp_price)
            else:  # short
                sl_price = entry_price * (1 + stop_loss) if stop_loss > 0 else float("inf")
                tp_price = entry_price * (1 - take_profit) if take_profit > 0 else 0.0
                hit_sl = (stop_loss > 0 and hi >= sl_price)
                hit_tp = (take_profit > 0 and tp_price > 0 and lo <= tp_price)
            if hit_sl and hit_tp:
                intrabar_fill_price = sl_price  # SL-first pessimistic
                intrabar_exit_reason = "SL"
            elif hit_sl:
                intrabar_fill_price = sl_price
                intrabar_exit_reason = "SL"
            elif hit_tp:
                intrabar_fill_price = tp_price
                intrabar_exit_reason = "TP"
```

**Replace the gross-return computation** to honour intrabar fills. The current line:
```python
        price_return = (p_curr - p_prev) / p_prev
        gross_ret = target_pos * price_return
```
becomes:
```python
        if intrabar_fill_price is not None:
            price_return = (intrabar_fill_price - p_prev) / p_prev
        else:
            price_return = (p_curr - p_prev) / p_prev
        gross_ret = target_pos * price_return
```

**Force target_pos = 0 when an intrabar fill happened** AFTER the existing close-to-close SL/TP block (~lines 136-142). Add at the same indentation as the SL/TP block:
```python
        if intrabar_fill_price is not None:
            target_pos = 0.0
            entry_price = 0.0
```

Resulting bar loop ordering (for clarity):
1. NaN/halted guards (unchanged)
2. Read `target_pos`, set `entry_equity`/`entry_price` on position change (NEW: also reset entry_price)
3. Compute intrabar fill (NEW)
4. Compute gross_ret using intrabar fill price OR close (CHANGED)
5. Costs + new_equity (unchanged)
6. Close-only SL/TP block (unchanged)
7. NEW: if intrabar_fill_price set, also flatten target_pos and clear entry_price
8. Append returns/equity (unchanged)

- [ ] **Step 1.4: Run the intrabar-SL test, confirm PASS**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_intrabar.py::test_intrabar_sl_truncates_bar_return_at_sl_price -xvs
```

Expected: PASSED.

- [ ] **Step 1.5: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/baseline_strategy_v2.py tests/strategies/test_sltp_intrabar.py
git commit -m "feat(v2-engine): add intrabar OHLC SL/TP path

Opt-in via intrabar=True + highs/lows arrays. Same-bar collision is
SL-first pessimistic. Default intrabar=False is bit-identical to the
existing close-only engine. TDD: 1 intrabar-SL test green."
```

---

## Task 2: Bit-identity regression for `intrabar=False`

**Files:**
- Modify: `tests/strategies/test_sltp_intrabar.py` (append)

- [ ] **Step 2.1: Append the bit-identity test**

```python
def test_intrabar_false_is_bit_identical_to_omitted_kwarg():
    """intrabar=False with no highs/lows must produce IDENTICAL equity to
    omitting the kwargs entirely. The most important property to preserve."""
    rng = np.random.default_rng(11)
    n = 200
    dates = np.arange(n)
    rets = rng.normal(0.0005, 0.02, size=n)
    prices = 100.0 * np.cumprod(1 + rets)
    positions = rng.choice([-1.0, 0.0, 1.0], size=n, p=[0.3, 0.2, 0.5])

    common = dict(
        dates=dates, prices=prices, positions=positions,
        initial_capital=10_000.0, stop_loss=0.03, take_profit=0.0,
        fee_rate=0.0004, slippage=0.0005, spread=0.0001,
        price_impact=0.00005, funding_rate=0.0001 / 8,
        max_portfolio_dd=0.15,
    )
    eq_omit, m_omit = run_coin_backtest(**common)
    eq_false, m_false = run_coin_backtest(intrabar=False, **common)

    np.testing.assert_array_equal(
        np.asarray(eq_omit), np.asarray(eq_false),
        err_msg="intrabar=False changed equity vs no-kwarg path"
    )
    assert m_omit == m_false, "metrics diverged with intrabar=False"
```

- [ ] **Step 2.2: Run the test**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_intrabar.py -xvs
```

Expected: 2 PASS.

- [ ] **Step 2.3: Run the full strategies suite**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/ -v 2>&1 | tail -3
```

Expected: 119 PASS + 1 skip + 1 deselected. (117 prior + 2 new intrabar tests = 119.)

- [ ] **Step 2.4: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tests/strategies/test_sltp_intrabar.py
git commit -m "test(v2-engine): regression-guard intrabar=False bit-identity"
```

---

## Task 3: Intrabar TP, same-bar collision, required-arrays tests

**Files:**
- Modify: `tests/strategies/test_sltp_intrabar.py` (append three tests)

- [ ] **Step 3.1: Append the intrabar-TP test**

```python
def test_intrabar_tp_truncates_bar_return_at_tp_price():
    """Long position, price ramps up. On bar where high >= entry*(1+TP),
    bar return must be TP%, not the full close-to-close gain (if smaller)."""
    n = 10
    dates = np.arange(n)
    closes = np.array([100.0] * n)
    closes[1:] = 100.0 * (1.005 ** np.arange(n - 1))  # +0.5%/bar = small
    highs = closes.copy()
    highs[5] = 108.0  # big upward wick (+8%) above TP=5% from entry close=100
    lows = closes * 0.999
    positions = np.ones(n)

    eq_intrabar, _ = run_coin_backtest(
        dates=dates, prices=closes, positions=positions,
        initial_capital=10_000.0,
        stop_loss=1.0, take_profit=0.05,
        intrabar=True, highs=highs, lows=lows,
        **_COSTS_NO,
    )
    eq_no_intrabar, _ = run_coin_backtest(
        dates=dates, prices=closes, positions=positions,
        initial_capital=10_000.0,
        stop_loss=1.0, take_profit=0.05,
        intrabar=False,
        **_COSTS_NO,
    )
    eq_intrabar = np.asarray(eq_intrabar)
    eq_no_intrabar = np.asarray(eq_no_intrabar)

    # Intrabar TP captures the wick; close-only TP cannot (high never reaches
    # close). So intrabar bar-5 equity must be strictly higher than close-only.
    assert eq_intrabar[5] > eq_no_intrabar[5], (
        f"intrabar TP must increase equity at bar 5 via wick capture: "
        f"intrabar={eq_intrabar[5]:.2f} close-only={eq_no_intrabar[5]:.2f}"
    )
```

- [ ] **Step 3.2: Append the same-bar-collision (SL-first pessimistic) test**

```python
def test_intrabar_same_bar_collision_is_sl_first_pessimistic():
    """When low <= SL_price AND high >= TP_price in the same bar, fill at SL."""
    n = 5
    dates = np.arange(n)
    # Entry close at bar 1 = 100. Bar 2 has BOTH SL hit (low=94) AND TP hit
    # (high=110). Close=100 (flat). SL-first pessimistic must pick SL.
    closes = np.array([100.0, 100.0, 100.0, 100.0, 100.0])
    highs = np.array([100.0, 100.0, 110.0, 100.0, 100.0])
    lows = np.array([100.0, 100.0, 94.0, 100.0, 100.0])
    positions = np.ones(n)

    eq, _ = run_coin_backtest(
        dates=dates, prices=closes, positions=positions,
        initial_capital=10_000.0,
        stop_loss=0.05, take_profit=0.08,
        intrabar=True, highs=highs, lows=lows,
        **_COSTS_NO,
    )
    eq = np.asarray(eq)

    # Bar 2: entry_price = closes[1] = 100. SL_price = 95. TP_price = 108.
    # Both lo=94 (≤95) and hi=110 (≥108) triggered. SL-first → fill at 95.
    # Equity at bar 2 = equity[1] * (1 + 1.0 * (95 - 100)/100) = equity[1] * 0.95
    # If TP-first were used (wrong), equity[2] = equity[1] * 1.08 (much higher).
    assert eq[2] < eq[1], (
        f"SL-first should reduce equity on collision bar: "
        f"got eq[1]={eq[1]:.2f}, eq[2]={eq[2]:.2f}"
    )
    # Strong assertion: ratio close to 0.95 (SL fill), not 1.08 (TP fill)
    ratio = eq[2] / eq[1]
    assert 0.94 < ratio < 0.96, (
        f"SL-first fill must produce ~5% loss on bar 2: ratio={ratio:.4f} "
        f"(SL=0.95, TP=1.08); SL-first is the pessimistic choice"
    )
```

- [ ] **Step 3.3: Append the required-arrays guard test**

```python
def test_intrabar_true_without_highs_raises():
    """intrabar=True requires highs and lows; missing arrays must raise."""
    dates = np.arange(5)
    prices = np.array([100.0] * 5)
    positions = np.ones(5)
    common = dict(
        dates=dates, prices=prices, positions=positions,
        initial_capital=10_000.0, stop_loss=0.05, take_profit=0.0,
        **_COSTS_NO,
    )
    with pytest.raises(ValueError, match="intrabar=True requires"):
        run_coin_backtest(intrabar=True, **common)
    with pytest.raises(ValueError, match="intrabar=True requires"):
        run_coin_backtest(intrabar=True, highs=np.zeros(5), **common)
    with pytest.raises(ValueError, match="intrabar=True requires"):
        run_coin_backtest(intrabar=True, lows=np.zeros(5), **common)
```

- [ ] **Step 3.4: Run the 3 new tests + full suite**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_intrabar.py -xvs
python -m pytest tests/strategies/ -v 2>&1 | tail -3
```

Expected: 5 intrabar tests PASS; full suite 122 + 1 skip + 1 deselected.

- [ ] **Step 3.5: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tests/strategies/test_sltp_intrabar.py
git commit -m "test(v2-engine): intrabar TP wick capture + SL-first collision + arg guard"
```

---

## Task 4: Slow baseline reproduction tests

**Files:**
- Modify: `tests/strategies/test_sltp_intrabar.py` (append two slow tests)

- [ ] **Step 4.1: Append both slow tests**

```python
# Slow regression guards: V5 MIX 4.5-yr WF baseline cell under both engine paths.
_CLOSE_ONLY_ANCHOR_SR = 3.18   # Reproduces §29 baseline; matches _V5_ANCHOR_SR.
_CLOSE_ONLY_ANCHOR_TOL = 0.05
# Intrabar baseline: NEW value we're discovering. Wide tolerance because we don't
# yet know what it should be — only that it should be sane.
_INTRABAR_ANCHOR_LOW = 2.5
_INTRABAR_ANCHOR_HIGH = 3.5


def _run_baseline(intrabar: bool) -> float:
    """Run V5 MIX baseline cell (SL=0.03, EE=0.015, TP=off) on the canonical
    4.5-yr WF window. Returns portfolio Sharpe."""
    from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402
    from scripts.baseline_v5_mix import (  # noqa: E402
        COSTS, DEFAULT_ROUTING, _load_preds, _v2_positions,
    )
    from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402

    start, end = "2021-11-07", "2026-04-15"
    coin_rets = {}
    for coin, pdir in DEFAULT_ROUTING.items():
        preds = _load_preds(PROJECT_ROOT / pdir, coin)
        preds = preds[(preds["date"] >= start) & (preds["date"] <= end)]
        ohlcv = _load_crypto_ohlcv(coin, end)
        ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
        merged = preds.merge(
            ohlcv[["Date", "Open", "High", "Low", "Close"]],
            left_on="date", right_on="Date",
        ).dropna(subset=["Close"]).reset_index(drop=True)
        merged["ref_price"] = merged["Close"]

        pos = _v2_positions(merged, kelly_fraction=0.5, early_exit_loss=0.015)
        costs = dict(COSTS)
        if intrabar:
            equity, _m = run_coin_backtest(
                dates=merged["date"].values,
                prices=merged["Close"].values,
                positions=pos, initial_capital=10_000.0,
                intrabar=True,
                highs=merged["High"].values, lows=merged["Low"].values,
                **costs,
            )
        else:
            equity, _m = run_coin_backtest(
                dates=merged["date"].values,
                prices=merged["Close"].values,
                positions=pos, initial_capital=10_000.0,
                **costs,
            )
        eq = np.asarray(equity, dtype=float)
        rets = eq[1:] / eq[:-1] - 1.0
        coin_rets[coin] = pd.Series(
            rets, index=pd.to_datetime(merged["date"].values[1:]),
        )
    df = pd.DataFrame(coin_rets).dropna()
    port = df.mean(axis=1)
    return float(port.mean() / port.std() * np.sqrt(252))


@pytest.mark.slow
def test_close_only_baseline_still_reproduces_under_new_engine():
    """The §29 close-only baseline cell must still reproduce SR ≈ 3.18 ± 0.05
    after the intrabar engine path was added. Bit-identity regression at scale.
    """
    sr = _run_baseline(intrabar=False)
    assert abs(sr - _CLOSE_ONLY_ANCHOR_SR) < _CLOSE_ONLY_ANCHOR_TOL, (
        f"close-only baseline drift after intrabar add: "
        f"got SR={sr:.3f}, expected {_CLOSE_ONLY_ANCHOR_SR} ± {_CLOSE_ONLY_ANCHOR_TOL}"
    )


@pytest.mark.slow
def test_intrabar_baseline_produces_sane_sharpe():
    """The intrabar baseline cell (SL=0.03, EE=0.015, TP=off, intrabar=True) is
    a NEW value we're discovering. Assert it's in a sane range to catch obvious
    bugs (e.g. ValueError-on-None highs, sign flips, etc). The discovered value
    becomes the §30 reference baseline."""
    sr = _run_baseline(intrabar=True)
    assert _INTRABAR_ANCHOR_LOW < sr < _INTRABAR_ANCHOR_HIGH, (
        f"intrabar baseline SR out of sane range: got {sr:.3f}, "
        f"expected ({_INTRABAR_ANCHOR_LOW}, {_INTRABAR_ANCHOR_HIGH})"
    )
    # Print for visibility in slow-test runs — this is the §30 reference.
    print(f"\n[intrabar baseline SR (§30 reference) = {sr:.3f}]")
```

- [ ] **Step 4.2: Run the slow tests (~60 s wall, both must pass)**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_intrabar.py -m slow -xvs
```

Expected: 2 PASS. Close-only stays at SR ≈ 3.178 (±0.05). Intrabar baseline prints its SR (record this number — it's the §30 reference value).

- [ ] **Step 4.3: Confirm default exclusion still works**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_intrabar.py -v 2>&1 | tail -5
```

Expected: 5 PASS + 2 deselected.

- [ ] **Step 4.4: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tests/strategies/test_sltp_intrabar.py
git commit -m "test(v5-mix): slow baseline regression for both close-only + intrabar paths"
```

---

## Task 5: Intrabar sweep harness

**Files:**
- Create: `scripts/v5_mix_sltp_sweep_intrabar.py`

- [ ] **Step 5.1: Create the sweep script**

Create `scripts/v5_mix_sltp_sweep_intrabar.py`:

```python
#!/usr/bin/env python
"""V5 MIX TP/SL intrabar OHLC sensitivity sweep (Approach B).

Same 378-cell grid as scripts/v5_mix_sltp_sweep.py, but with intrabar SL/TP
fills (low <= SL_price, high >= TP_price; SL-first on same-bar collision).
Records n_intrabar_sl / n_intrabar_tp diagnostic counts per cell.

Outputs to data/v5_sltp_sweep_intrabar/:
  results.csv  — one row per (sl, ee, tp) × scope; includes intrabar diagnostics
  summary.json — grid + close-only-§29 baseline + intrabar baseline + best + git SHA
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402
from scripts.baseline_v5_mix import (  # noqa: E402
    COSTS, DEFAULT_ROUTING, EARLY_EXIT_DEFAULT, _load_preds, _v2_positions,
)
from scripts.v5_mix_sltp_sweep import (  # noqa: E402
    SL_GRID, EE_GRID, TP_GRID, SMOKE_SL, SMOKE_EE, SMOKE_TP, _metrics,
)
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402

ANN = float(np.sqrt(252))

_BASELINE_SL = COSTS["stop_loss"]       # 0.03
_BASELINE_EE = EARLY_EXIT_DEFAULT       # 0.015
_BASELINE_TP = COSTS["take_profit"]     # 0.0


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT
        ).decode().strip()
    except Exception:
        return "unknown"


def _load_coin_data(coin: str, pred_dir: Path, start: str, end: str) -> pd.DataFrame:
    """Load + merge preds with full OHLCV (Close + High + Low)."""
    preds = _load_preds(pred_dir, coin)
    preds = preds[(preds["date"] >= start) & (preds["date"] <= end)]
    if preds.empty:
        raise ValueError(f"{coin}: no predictions in [{start}, {end}] under {pred_dir}")
    ohlcv = _load_crypto_ohlcv(coin, end)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    merged = preds.merge(
        ohlcv[["Date", "Open", "High", "Low", "Close"]],
        left_on="date", right_on="Date",
    )
    merged = merged.dropna(subset=["Close", "High", "Low"]).reset_index(drop=True)
    merged["ref_price"] = merged["Close"]
    return merged


def _engine_returns_intrabar(merged: pd.DataFrame, positions: np.ndarray,
                              sl: float, tp: float) -> tuple[pd.Series, int, int]:
    """Run intrabar engine. Returns (returns, n_intrabar_sl, n_intrabar_tp).

    The n_* counts are reconstructed by comparing the intrabar equity to a
    parallel close-only run on the same positions/SL/TP — every bar where the
    paths diverge had an intrabar fill. SL vs TP is inferred from the sign of
    divergence (negative on the diverging bar → SL; positive → TP).
    """
    costs = dict(COSTS)
    costs["stop_loss"] = sl
    costs["take_profit"] = tp

    eq_ib, _ = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=positions, initial_capital=10_000.0,
        intrabar=True,
        highs=merged["High"].values, lows=merged["Low"].values,
        **costs,
    )
    eq_co, _ = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=positions, initial_capital=10_000.0,
        intrabar=False,
        **costs,
    )
    eq_ib = np.asarray(eq_ib, dtype=float)
    eq_co = np.asarray(eq_co, dtype=float)

    # Bar-level divergence: where intrabar return differs from close-only.
    rets_ib = eq_ib[1:] / eq_ib[:-1] - 1.0
    rets_co = eq_co[1:] / eq_co[:-1] - 1.0
    diff = rets_ib - rets_co
    n_sl = int((diff < -1e-9).sum())   # intrabar lost more this bar → SL
    n_tp = int((diff > 1e-9).sum())    # intrabar gained more this bar → TP

    return (
        pd.Series(rets_ib, index=pd.to_datetime(merged["date"].values[1:])),
        n_sl, n_tp,
    )


def run_sweep(
    sl_grid: list[float], ee_grid: list[float], tp_grid: list[float],
    start: str, end: str, kelly_fraction: float, out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    coin_data: dict[str, pd.DataFrame] = {}
    for coin, pdir in DEFAULT_ROUTING.items():
        coin_data[coin] = _load_coin_data(coin, PROJECT_ROOT / pdir, start, end)
    print(f"  Loaded {len(coin_data)} coins (with OHLC) in {time.time() - t0:.1f}s")

    rows: list[dict] = []
    n_cells = len(sl_grid) * len(ee_grid) * len(tp_grid)
    cell_i = 0
    intrabar_baseline_sr = None

    # EE outer: positions are EE-dependent only.
    for ee in ee_grid:
        position_cache: dict[str, np.ndarray] = {}
        for coin, merged in coin_data.items():
            position_cache[coin] = _v2_positions(
                merged, kelly_fraction=kelly_fraction, early_exit_loss=ee,
            )
        for sl in sl_grid:
            for tp in tp_grid:
                cell_i += 1
                coin_rets: dict[str, pd.Series] = {}
                n_sl_total = 0
                n_tp_total = 0
                for coin, merged in coin_data.items():
                    r, n_sl, n_tp = _engine_returns_intrabar(
                        merged, position_cache[coin], sl=sl, tp=tp,
                    )
                    coin_rets[coin] = r
                    n_sl_total += n_sl
                    n_tp_total += n_tp

                df = pd.DataFrame(coin_rets).dropna()
                port = df.mean(axis=1)
                pm = _metrics(port.values)

                rows.append(dict(
                    sl=sl, ee=ee, tp=tp, scope="portfolio",
                    n_intrabar_sl=n_sl_total, n_intrabar_tp=n_tp_total, **pm,
                ))
                for coin, r in coin_rets.items():
                    cm = _metrics(r.values)
                    # Per-coin counts not split here — coarse aggregate only.
                    rows.append(dict(
                        sl=sl, ee=ee, tp=tp, scope=coin,
                        n_intrabar_sl=-1, n_intrabar_tp=-1, **cm,
                    ))

                if sl == _BASELINE_SL and ee == _BASELINE_EE and tp == _BASELINE_TP:
                    intrabar_baseline_sr = pm["sharpe"]

                if cell_i % 20 == 0 or cell_i == n_cells:
                    elapsed = time.time() - t0
                    eta = elapsed / cell_i * (n_cells - cell_i)
                    print(f"  cell {cell_i}/{n_cells}  "
                          f"SL={sl:.3f} EE={ee:.3f} TP={tp:.3f}  "
                          f"port SR={pm['sharpe']:+.2f}  "
                          f"n_sl={n_sl_total} n_tp={n_tp_total}  "
                          f"elapsed={elapsed:.0f}s  eta={eta:.0f}s")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_dir / "results.csv", index=False)

    port_only = df_out[df_out["scope"] == "portfolio"].copy()
    best = port_only.sort_values("sharpe", ascending=False).iloc[0]

    if intrabar_baseline_sr is None:
        print(
            f"  WARNING: baseline cell (SL={_BASELINE_SL}, EE={_BASELINE_EE}, "
            f"TP={_BASELINE_TP}) was NOT in the sweep grid — "
            f"summary.json intrabar_baseline_cell.portfolio_sharpe will be null.",
            file=sys.stderr,
        )

    delta_sr = (
        float(best["sharpe"]) - intrabar_baseline_sr
        if intrabar_baseline_sr is not None else None
    )

    summary = dict(
        grid=dict(sl=sl_grid, ee=ee_grid, tp=tp_grid),
        window=dict(start=start, end=end),
        kelly_fraction=kelly_fraction,
        intrabar_baseline_cell=dict(
            sl=_BASELINE_SL, ee=_BASELINE_EE, tp=_BASELINE_TP,
            portfolio_sharpe=intrabar_baseline_sr,
        ),
        close_only_published_baseline_sharpe=3.178,  # §29 reference for context
        best_cell=dict(
            sl=float(best["sl"]), ee=float(best["ee"]), tp=float(best["tp"]),
            portfolio_sharpe=float(best["sharpe"]),
            total_return=float(best["total_return"]),
            max_drawdown=float(best["max_drawdown"]),
            calmar=float(best["calmar"]),
            n_intrabar_sl=int(best["n_intrabar_sl"]),
            n_intrabar_tp=int(best["n_intrabar_tp"]),
        ),
        delta_sr_best_vs_intrabar_baseline=delta_sr,
        acceptance_threshold=0.15,
        verdict=(
            None if intrabar_baseline_sr is None
            else ("confirm" if delta_sr is not None and delta_sr >= 0.15 else "reject")
        ),
        n_cells=n_cells,
        wall_clock_sec=time.time() - t0,
        git_sha=_git_sha(),
    )
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n  Wrote: {out_dir / 'results.csv'}  ({len(df_out)} rows)")
    print(f"  Wrote: {out_dir / 'summary.json'}")
    if intrabar_baseline_sr is not None:
        print(f"  Intrabar baseline SR = {intrabar_baseline_sr:+.3f} "
              f"(close-only §29 = +3.178)")
        print(f"  Best cell: SL={best['sl']} EE={best['ee']} TP={best['tp']}  "
              f"SR={best['sharpe']:+.3f}  DD={best['max_drawdown']:.1%}  "
              f"ΔSR={delta_sr:+.3f}  verdict={summary['verdict'].upper()}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", default="2021-11-07")
    p.add_argument("--end", default="2026-04-15")
    p.add_argument("--output-dir", default="data/v5_sltp_sweep_intrabar")
    p.add_argument("--kelly", type=float, default=0.5)
    p.add_argument("--smoke", action="store_true",
                   help="Smoke run on tiny grid (2x1x2=4 cells)")
    p.add_argument("--data-root", default=None)
    args = p.parse_args()

    if args.data_root:
        os.environ["TRADINGAGENTS_DATA_ROOT"] = args.data_root

    if args.smoke:
        sl, ee, tp = SMOKE_SL, SMOKE_EE, SMOKE_TP
        print("  SMOKE MODE — small grid")
    else:
        sl, ee, tp = SL_GRID, EE_GRID, TP_GRID

    out_dir = PROJECT_ROOT / args.output_dir
    print(f"\n  V5 MIX TP/SL intrabar sweep (approach B)")
    print(f"  window : {args.start} → {args.end}")
    print(f"  grid   : SL={len(sl)} EE={len(ee)} TP={len(tp)} = {len(sl) * len(ee) * len(tp)} cells")
    print(f"  output : {out_dir}\n")

    run_sweep(sl, ee, tp, args.start, args.end, args.kelly, out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5.2: Run the smoke (4 cells, ~30-60 s)**

```bash
cd /home/malecada/master_thesis/TradingAgents
rm -rf /tmp/v5_intrabar_smoke
python scripts/v5_mix_sltp_sweep_intrabar.py --smoke --output-dir /tmp/v5_intrabar_smoke
```

Expected: 4 cells complete, `results.csv` has 4 × 5 = 20 rows, `summary.json` written, intrabar baseline cell SR printed (will likely be lower than 3.178 — that's the whole point of the sweep).

- [ ] **Step 5.3: Verify output shape**

```bash
python -c "
import pandas as pd, json
df = pd.read_csv('/tmp/v5_intrabar_smoke/results.csv')
s = json.load(open('/tmp/v5_intrabar_smoke/summary.json'))
assert df.shape[0] == 20
assert 'n_intrabar_sl' in df.columns
assert 'n_intrabar_tp' in df.columns
assert s['intrabar_baseline_cell']['portfolio_sharpe'] is not None
assert s['verdict'] in ('confirm', 'reject')
print('OK: smoke shape, columns, verdict all present')
print('  intrabar baseline SR =', s['intrabar_baseline_cell']['portfolio_sharpe'])
print('  best cell SR        =', s['best_cell']['portfolio_sharpe'])
print('  delta               =', s['delta_sr_best_vs_intrabar_baseline'])
print('  verdict             =', s['verdict'])
"
```

- [ ] **Step 5.4: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/v5_mix_sltp_sweep_intrabar.py
git commit -m "feat(sweep): V5 MIX TP/SL intrabar OHLC sweep harness (approach B)

378-cell grid mirror of v5_mix_sltp_sweep.py with intrabar fills + per-cell
n_intrabar_sl / n_intrabar_tp counts. summary.json includes verdict
field (confirm / reject) per the +0.15 ΔSR acceptance threshold."
```

---

## Task 6: Full intrabar sweep run

**Files:** runtime only

- [ ] **Step 6.1: Launch the full 378-cell intrabar sweep**

```bash
cd /home/malecada/master_thesis/TradingAgents
mkdir -p data/v5_sltp_sweep_intrabar
python scripts/v5_mix_sltp_sweep_intrabar.py --output-dir data/v5_sltp_sweep_intrabar 2>&1 | tee data/v5_sltp_sweep_intrabar/sweep.log
```

Expected wall clock: ~30-60 s (intrabar = 2× engine evals per cell vs §29). Progress prints every 20 cells.

If wall clock > 10 min, kill and investigate (e.g., OHLC merge slow).

- [ ] **Step 6.2: Inspect the verdict + baseline reproduction**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -c "
import json
s = json.load(open('data/v5_sltp_sweep_intrabar/summary.json'))
print('intrabar baseline:', s['intrabar_baseline_cell'])
print('best cell        :', s['best_cell'])
print('delta SR         :', s['delta_sr_best_vs_intrabar_baseline'])
print('VERDICT          :', s['verdict'])
print('wall clock       :', s['wall_clock_sec'], 's')
"
```

Record the verdict. The remaining tasks (7+8) execute either branch:
- `confirm` (delta_sr ≥ +0.15): proceed to reporting + §30 = confirm + WF spec.
- `reject` (delta_sr < +0.15): proceed to reporting + §30 = reject + STOP (no WF spec).

- [ ] **Step 6.3: Sanity-check output shape**

```bash
python -c "
import pandas as pd
df = pd.read_csv('data/v5_sltp_sweep_intrabar/results.csv')
print('shape:', df.shape)
print('uniq cells:', df.drop_duplicates(['sl','ee','tp']).shape[0])
print('scope counts:')
print(df['scope'].value_counts())
"
```

Expected: `(1890, 13)` — 378 unique cells × 5 scopes; 13 columns: sl, ee, tp, scope, n_intrabar_sl, n_intrabar_tp, sharpe, total_return, max_drawdown, calmar, win_rate, profit_factor, n_bars.

- [ ] **Step 6.4: Commit results**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add -f data/v5_sltp_sweep_intrabar/results.csv data/v5_sltp_sweep_intrabar/summary.json data/v5_sltp_sweep_intrabar/sweep.log
git commit -m "results(sweep): V5 MIX TP/SL intrabar OHLC 378-cell sweep output

See summary.json for verdict + intrabar baseline + best cell + delta."
```

---

## Task 7: Reporting — top-20 + heatmaps + comparison

**Files:**
- Create: `scripts/v5_sltp_intrabar_report.py`

- [ ] **Step 7.1: Write the reporting script**

Create `scripts/v5_sltp_intrabar_report.py`:

```python
#!/usr/bin/env python
"""Reporting for V5 MIX TP/SL intrabar sweep — top-20 + 12 heatmaps + §29 comparison."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BASELINE = dict(sl=0.03, ee=0.015, tp=0.0)


def _heatmap(pivot: pd.DataFrame, title: str, cbar_label: str,
             out: Path, baseline: tuple[float, float] | None = None) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    arr = pivot.values
    im = ax.imshow(arr, aspect="auto", origin="lower", cmap="RdYlGn")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"{c:g}" for c in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([f"{r:g}" for r in pivot.index])
    ax.set_xlabel(pivot.columns.name)
    ax.set_ylabel(pivot.index.name)
    ax.set_title(title)
    plt.colorbar(im, ax=ax, label=cbar_label)

    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            ax.text(j, i, f"{arr[i, j]:.2f}",
                    ha="center", va="center", fontsize=7, color="black")

    if baseline is not None:
        sl_b, tp_b = baseline
        if sl_b in pivot.index and tp_b in pivot.columns:
            yi = list(pivot.index).index(sl_b)
            xi = list(pivot.columns).index(tp_b)
            ax.plot(xi, yi, marker="x", markersize=18, mew=3, color="blue",
                    label="V5 baseline")
            ax.legend(loc="upper right")

    plt.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="data/v5_sltp_sweep_intrabar")
    p.add_argument("--close-only-dir", default="data/v5_sltp_sweep",
                   help="§29 close-only sweep results for the comparison table")
    args = p.parse_args()

    in_dir = PROJECT_ROOT / args.input_dir
    co_dir = PROJECT_ROOT / args.close_only_dir
    df = pd.read_csv(in_dir / "results.csv")
    port = df[df["scope"] == "portfolio"].copy()

    # ── top-20 ────────────────────────────────────────────────────────
    top = port.sort_values("sharpe", ascending=False).head(20).copy()
    baseline_rows = port[(port["sl"] == 0.03) & (port["ee"] == 0.015) & (port["tp"] == 0.0)]
    baseline_sr = float(baseline_rows["sharpe"].iloc[0]) if len(baseline_rows) else float("nan")
    lines = [
        "# V5 MIX TP/SL Intrabar Sweep — Top 20 Cells (by portfolio Sharpe)",
        "",
        f"Source: `{in_dir / 'results.csv'}` ({len(port)} portfolio cells, intrabar OHLC)",
        "",
        f"Intrabar baseline V5 cell: SL=0.03, EE=0.015, TP=off → SR = {baseline_sr:+.3f}",
        "(Compare §29 close-only baseline = +3.178.)",
        "",
        "| Rank | SL | EE | TP | Sharpe | Total Ret | Max DD | Calmar | Win % | PF | n_SL | n_TP |",
        "|------|-----|-----|-----|--------|-----------|--------|--------|-------|-----|------|------|",
    ]
    for rank, (_, r) in enumerate(top.iterrows(), start=1):
        is_baseline = (r["sl"] == 0.03 and r["ee"] == 0.015 and r["tp"] == 0.0)
        marker = " ← **baseline**" if is_baseline else ""
        lines.append(
            f"| {rank} | {r['sl']:g} | {r['ee']:g} | {r['tp']:g} | "
            f"{r['sharpe']:+.3f}{marker} | {r['total_return']:+.1%} | "
            f"{r['max_drawdown']:.1%} | {r['calmar']:+.2f} | "
            f"{r['win_rate']:.1%} | {r['profit_factor']:.2f} | "
            f"{int(r['n_intrabar_sl'])} | {int(r['n_intrabar_tp'])} |"
        )
    (in_dir / "top20.md").write_text("\n".join(lines) + "\n")
    print(f"  Wrote: {in_dir / 'top20.md'}")

    # ── heatmaps ─────────────────────────────────────────────────────
    heat_dir = in_dir / "heatmaps"
    heat_dir.mkdir(exist_ok=True)
    n = 0
    for ee in sorted(port["ee"].unique()):
        sub = port[port["ee"] == ee]
        for metric, label in [
            ("sharpe", "Portfolio Sharpe (intrabar)"),
            ("max_drawdown", "Max Drawdown (intrabar)"),
        ]:
            pivot = sub.pivot(index="sl", columns="tp", values=metric)
            pivot.index.name = "stop_loss"
            pivot.columns.name = "take_profit"
            title = f"V5 MIX {label}  (early_exit_loss = {ee:g})"
            out = heat_dir / f"{metric}_sl_x_tp__ee_{ee:g}.png"
            baseline = (BASELINE["sl"], BASELINE["tp"]) if ee == BASELINE["ee"] else None
            _heatmap(pivot, title, label, out, baseline=baseline)
            n += 1
    print(f"  Wrote: {n} heatmaps to {heat_dir}")

    # ── comparison.md: §29 top-5 cells under both engines ────────────
    co_path = co_dir / "results.csv"
    if not co_path.exists():
        print(f"  WARNING: {co_path} not found; skipping comparison.md")
        return

    co = pd.read_csv(co_path)
    co_port = co[co["scope"] == "portfolio"]
    top5_co = co_port.sort_values("sharpe", ascending=False).head(5).reset_index(drop=True)

    rows = []
    for _, c in top5_co.iterrows():
        ib_rows = port[
            (port["sl"] == c["sl"]) & (port["ee"] == c["ee"]) & (port["tp"] == c["tp"])
        ]
        if len(ib_rows) == 0:
            continue
        ib = ib_rows.iloc[0]
        rows.append(dict(
            sl=c["sl"], ee=c["ee"], tp=c["tp"],
            co_sr=c["sharpe"], ib_sr=ib["sharpe"], delta=ib["sharpe"] - c["sharpe"],
            co_dd=c["max_drawdown"], ib_dd=ib["max_drawdown"],
            n_sl=int(ib["n_intrabar_sl"]), n_tp=int(ib["n_intrabar_tp"]),
        ))

    comp_lines = [
        "# V5 MIX TP/SL Sweep — §29 vs §30 (close-only vs intrabar)",
        "",
        f"Top-5 cells by close-only Sharpe (§29) re-scored under intrabar (§30).",
        "",
        "| SL | EE | TP | CO SR | IB SR | ΔSR | CO DD | IB DD | n_SL | n_TP |",
        "|----|----|----|-------|-------|-----|-------|-------|------|------|",
    ]
    for r in rows:
        comp_lines.append(
            f"| {r['sl']:g} | {r['ee']:g} | {r['tp']:g} | "
            f"{r['co_sr']:+.3f} | {r['ib_sr']:+.3f} | {r['delta']:+.3f} | "
            f"{r['co_dd']:.1%} | {r['ib_dd']:.1%} | "
            f"{r['n_sl']} | {r['n_tp']} |"
        )
    (in_dir / "comparison.md").write_text("\n".join(comp_lines) + "\n")
    print(f"  Wrote: {in_dir / 'comparison.md'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 7.2: Run reporting**

```bash
cd /home/malecada/master_thesis/TradingAgents
python scripts/v5_sltp_intrabar_report.py --input-dir data/v5_sltp_sweep_intrabar --close-only-dir data/v5_sltp_sweep
ls data/v5_sltp_sweep_intrabar/heatmaps/*.png | wc -l
head -30 data/v5_sltp_sweep_intrabar/top20.md
head -20 data/v5_sltp_sweep_intrabar/comparison.md
```

Expected: 12 PNGs, top-20 table with `n_SL`/`n_TP` columns, comparison.md with 5 rows.

- [ ] **Step 7.3: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/v5_sltp_intrabar_report.py
git add -f data/v5_sltp_sweep_intrabar/top20.md data/v5_sltp_sweep_intrabar/comparison.md data/v5_sltp_sweep_intrabar/heatmaps/
git commit -m "report(sweep): intrabar top-20 + 12 heatmaps + §29 comparison"
```

---

## Task 8: THESIS_FINDINGS.md §30 + §29 cross-reference

**Files:**
- Modify: `THESIS_FINDINGS.md`

- [ ] **Step 8.1: Determine the correct section number**

```bash
grep -n "^## 2[0-9]\|^## 3[0-9]" /home/malecada/master_thesis/TradingAgents/THESIS_FINDINGS.md | tail -5
```

Expected: latest is `## 29.`. New section is `## 30.`. If a higher number already exists, use the next available.

- [ ] **Step 8.2: Read `summary.json` to extract live numbers**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -c "
import json
s = json.load(open('data/v5_sltp_sweep_intrabar/summary.json'))
ib = s['intrabar_baseline_cell']
b = s['best_cell']
print(f'IB_BASELINE_SR={ib[\"portfolio_sharpe\"]:.3f}')
print(f'BEST_SL={b[\"sl\"]}  BEST_EE={b[\"ee\"]}  BEST_TP={b[\"tp\"]}')
print(f'BEST_SR={b[\"portfolio_sharpe\"]:.3f}')
print(f'BEST_TOTAL_RET={b[\"total_return\"]*100:.1f}')
print(f'BEST_DD={b[\"max_drawdown\"]*100:.1f}')
print(f'BEST_CALMAR={b[\"calmar\"]:.2f}')
print(f'BEST_N_SL={b[\"n_intrabar_sl\"]}')
print(f'BEST_N_TP={b[\"n_intrabar_tp\"]}')
print(f'DELTA={s[\"delta_sr_best_vs_intrabar_baseline\"]:.3f}')
print(f'VERDICT={s[\"verdict\"]}')
"
```

Record these values. They MUST substitute every `<<...>>` placeholder in Step 8.3.

- [ ] **Step 8.3: Append the §30 section (substituting actual numbers)**

Append to `THESIS_FINDINGS.md`:

```markdown


## 30. V5 MIX TP/SL Intrabar OHLC Sweep — §29 Wick-Risk Validation (2026-05-19)

**Goal.** §29 (close-only sweep) found best cell SL=0.10, EE=disabled, TP=off → SR
+3.335 / DD 3.6% (vs baseline +3.178 / 4.9%), a +0.157 SR / -1.3 pp DD delta.
The §29 limitations flagged **intrabar wick risk** as the dominant unaddressed
unknown: real fills under tight SL would be worse than close-only logic shows.
This study re-runs the §29 378-cell grid with intrabar OHLC fills and reports
whether the §29 finding survives.

**Method.** Engine extended (`scripts/baseline_strategy_v2.py`) with opt-in
`intrabar: bool = False` + `highs` / `lows` arrays. When enabled, per-bar:
`hit_SL = low ≤ entry × (1 − SL%)`, `hit_TP = high ≥ entry × (1 + TP%)`,
same-bar collision is **SL-first pessimistic**. Bar's gross return truncated
at fill price. Default `intrabar=False` is bit-identical to the §29 engine
(regression-tested in `tests/strategies/test_sltp_intrabar.py`). EE
(close-only by construction) unchanged. Same 378-cell grid as §29:

| Parameter | Values |
|---|---|
| stop_loss | off, 0.5%, 1%, 1.5%, 2%, 3% (V5), 5%, 7%, 10% |
| early_exit_loss | disabled, 0.5%, 1%, 1.5% (V5), 2%, 3% |
| take_profit | off (V5), 1%, 2%, 3%, 5%, 8%, 12% |

Per-cell `n_intrabar_sl` and `n_intrabar_tp` counts capture how often the
intrabar branch fired (diagnostic for collision-rate analysis).

**Intrabar baseline.** (SL=0.03, EE=0.015, TP=off, intrabar=True) →
SR = <<IB_BASELINE_SR>>. (Close-only §29 baseline = +3.178; intrabar drift
reflects wick effects on the production parameters.)

**Best cell — intrabar.** SL = <<BEST_SL>>, EE = <<BEST_EE>>, TP = <<BEST_TP>>
→ Sharpe <<BEST_SR>>, total return <<BEST_TOTAL_RET>>%, max DD <<BEST_DD>>%,
Calmar <<BEST_CALMAR>>, intrabar SL fires = <<BEST_N_SL>>, intrabar TP fires =
<<BEST_N_TP>>. ΔSR vs intrabar baseline = <<DELTA>>.

**Verdict.** <<VERDICT>>.

Acceptance criterion (locked pre-sweep): best cell ΔSR vs intrabar baseline
≥ +0.15. If met → §29 finding is robust to wick risk; follow-up is
walk-forward parameter split (separate spec). If not met → §29 finding is
wick-fragile, no live parameter change motivated, no WF split.

**§29 top-5 re-scored under intrabar.** See
`data/v5_sltp_sweep_intrabar/comparison.md` for the full side-by-side. Brief:
[Insert 2-3 lines summarising the comparison table — which §29 winners survive
under intrabar and which collapse.]

**Limitations carried from §29.**
1. Single 4.5-year window; no out-of-sample.
2. Global tuple (same SL/EE/TP across 4 coins).
3. Fills assumed at the exact trigger price (no slippage beyond the existing
   `slippage` parameter).
4. Same-bar collision logic is one fixed convention (SL-first); a TP-first
   variant would yield an upper bound and is not run here.

**Live deployment.** Still no recommendation. If verdict = confirm, WF param
split is the next gate. If verdict = reject, no further work toward live
change on this parameter family.

**Artifacts.**
- Top-20 cells: `data/v5_sltp_sweep_intrabar/top20.md`
- §29 vs §30 comparison (top-5): `data/v5_sltp_sweep_intrabar/comparison.md`
- Full results: `data/v5_sltp_sweep_intrabar/results.csv`
- Grid + verdict + git SHA: `data/v5_sltp_sweep_intrabar/summary.json`
- 12 heatmaps: `data/v5_sltp_sweep_intrabar/heatmaps/`
- Sweep log: `data/v5_sltp_sweep_intrabar/sweep.log`

**Spec + plan.**
- Spec: `docs/superpowers/specs/2026-05-19-v5-sltp-intrabar-design.md`
- Plan: `docs/superpowers/plans/2026-05-19-v5-sltp-intrabar.md`
- Branch: `feature/v5-sltp-sweep-intrabar`
```

- [ ] **Step 8.4: Append cross-reference line to §29**

Find the §29 section header (`## 29. V5 MIX TP/SL Parameter Sensitivity Sweep`) and append a single line at the end of the §29 section, BEFORE §30 starts. Use the Edit tool:

Find this line near the end of §29 (likely the "Spec + plan" block's last line). Append immediately after it:

```markdown

**Follow-up:** § 30 validates this under intrabar OHLC rules; see verdict there.
```

- [ ] **Step 8.5: Verify no `<<...>>` placeholders remain**

```bash
grep -n "<<.*>>" /home/malecada/master_thesis/TradingAgents/THESIS_FINDINGS.md
```

Expected: no output. If matches remain, substitute them from `summary.json`.

- [ ] **Step 8.6: Confirm §30 anchor + cross-reference**

```bash
grep -n "^## 30\." /home/malecada/master_thesis/TradingAgents/THESIS_FINDINGS.md
grep -n "Follow-up.*intrabar" /home/malecada/master_thesis/TradingAgents/THESIS_FINDINGS.md
```

Expected: §30 anchor present exactly once; cross-reference line present once inside §29.

- [ ] **Step 8.7: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add THESIS_FINDINGS.md
git commit -m "docs(thesis): §30 intrabar OHLC sweep — verdict for §29 finding

Re-runs the 378-cell SL/EE/TP grid with intrabar SL/TP fills (SL-first
pessimistic on same-bar collision). Reports intrabar baseline, best cell,
ΔSR, and confirm/reject verdict against the locked +0.15 threshold.
Cross-reference line added to §29."
```

---

## Task 9: Final verification

**Files:** none modified

- [ ] **Step 9.1: Run the full intrabar test suite**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_intrabar.py -v
```

Expected: 5 fast tests PASS + 2 deselected slow.

- [ ] **Step 9.2: Run the full strategies suite (no regression)**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/ -v 2>&1 | tail -3
```

Expected: 122 PASS + 1 skip + 3 deselected (1 §29 slow + 2 new §30 slow).

- [ ] **Step 9.3: Run both slow baseline guards**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_intrabar.py tests/strategies/test_sltp_sweep.py -m slow -xvs 2>&1 | tail -15
```

Expected: 3 PASS — §29 baseline still SR ≈ 3.178 (close-only path unchanged); §30 close-only baseline still SR ≈ 3.178 (bit-identity guard); §30 intrabar baseline SR within sane range.

- [ ] **Step 9.4: Confirm branch state**

```bash
cd /home/malecada/master_thesis/TradingAgents
git log --oneline feature/v5-sltp-sweep-intrabar ^main
git status --short
```

Expected: 9 commits (spec → plan → Tasks 1-8). Working tree clean (or only pre-existing untracked).

- [ ] **Step 9.5: Report the verdict to the user**

Read `data/v5_sltp_sweep_intrabar/summary.json` and report:

- Intrabar baseline cell SR
- Best cell (SL, EE, TP) + SR + DD + Calmar
- ΔSR
- VERDICT (confirm / reject)
- Top-3 from `comparison.md`
- Next-step recommendation:
  - If `confirm` → say "Ready to design WF param split spec. Want me to proceed?"
  - If `reject` → say "Approach B rejects §29. No WF spec scheduled. §30 committed as controlled negative result. Recommend `superpowers:finishing-a-development-branch`."

---

## Done

The branch `feature/v5-sltp-sweep-intrabar` contains:
- Engine extension with opt-in `intrabar=True` + `highs` / `lows` (bit-identical default)
- 378-cell intrabar sweep harness with collision diagnostic counts
- Reporting (`top20.md` + 12 heatmaps + `comparison.md` vs §29)
- THESIS_FINDINGS.md §30 with locked verdict + §29 cross-reference

If verdict = confirm → next spec: WF parameter split (train 2021-11 → 2024-12, test 2025-01 → 2026-04). If verdict = reject → finish branch, no further follow-up on this parameter family.
