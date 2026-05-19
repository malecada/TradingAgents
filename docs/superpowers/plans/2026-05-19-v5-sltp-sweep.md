# V5 MIX TP/SL Parameter Sensitivity Sweep — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sweep a 378-cell (stop-loss × early-exit × take-profit) grid against the V5 MIX 4-coin equal-weight strategy over the 4.5-year walk-forward window, producing heatmaps + a top-20 table + a THESIS_NARRATIVE.md §24 section. Research-only — no live parameter change.

**Architecture:** Add an optional `take_profit` parameter to the existing `run_coin_backtest` function (close-to-close, mirroring the existing `stop_loss` block); reuse the `baseline_v5_mix.run_coin` portfolio assembly path; build a new sweep harness that varies (SL, EE, TP) per cell. Cache positions per `early_exit_loss` value (EE drives the position builder; SL and TP only drive the engine) so 378 cells require only 6 × 4 = 24 position-builder runs but 378 × 4 = 1512 engine evaluations.

**Tech Stack:** Python 3.10, pandas, numpy, matplotlib, pytest, existing project modules (`scripts/baseline_strategy_v2.py`, `scripts/baseline_v5_mix.py`, `tradingagents.strategies.v2_sizing`).

**Spec:** `docs/superpowers/specs/2026-05-19-v5-sltp-sweep-design.md`

**Branch:** `feature/v5-sltp-sweep` (already created, spec committed at `757eb1c`)

---

## File Map

| Path | Status | Responsibility |
|---|---|---|
| `scripts/baseline_strategy_v2.py` | Modify | Add `take_profit: float = 0.0` kwarg to `run_coin_backtest`; mirror SL block with TP block |
| `scripts/baseline_v5_mix.py` | Modify | Add `take_profit` to `COSTS` dict (default 0.0 keeps current behaviour bit-identical); thread `early_exit_loss` + `take_profit` kwargs through `run_coin` so the sweep can override |
| `scripts/v5_mix_sltp_sweep.py` | Create | Sweep harness — iterate (SL, EE, TP) grid, cache positions per EE, run engine per cell, assemble portfolio, write outputs |
| `scripts/v5_sltp_sweep_report.py` | Create | Post-sweep reporting — read `results.csv`, produce `top20.md` + 12 heatmap PNGs |
| `tests/strategies/test_sltp_sweep.py` | Create | Unit + regression tests for engine TP, TP-disabled bit-identity, baseline reproduction |
| `THESIS_NARRATIVE.md` | Modify | Append §24 with methodology + results figures |
| `data/v5_sltp_sweep/` | Create at runtime | Sweep output dir (gitignored by virtue of `data/` ignore rules) |

---

## Task 1: Add `take_profit` to engine (failing test first)

**Files:**
- Create: `tests/strategies/test_sltp_sweep.py`
- Modify: `scripts/baseline_strategy_v2.py:80-189` (function `run_coin_backtest`)

- [ ] **Step 1.1: Write the failing TP-trigger test**

```python
# tests/strategies/test_sltp_sweep.py
"""Tests for take-profit extension to run_coin_backtest + sweep harness."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402


COSTS_ZERO = dict(
    fee_rate=0.0, slippage=0.0, spread=0.0,
    price_impact=0.0, funding_rate=0.0,
    max_portfolio_dd=1.0,  # disabled
)


def _ramp(start: float, step: float, n: int) -> np.ndarray:
    return np.array([start + i * step for i in range(n)], dtype=float)


def test_take_profit_triggers_and_flattens_next_bar():
    """Long position with monotonically rising price hits TP=5%, exits next bar."""
    # 10 bars; price ramps +1% per bar from 100; positions = full long throughout.
    dates = np.arange(10)
    prices = 100.0 * (1.01 ** np.arange(10))
    positions = np.ones(10)

    equity, _m = run_coin_backtest(
        dates=dates, prices=prices, positions=positions,
        initial_capital=10_000.0,
        stop_loss=1.0,           # SL disabled (would need 100% drawdown)
        take_profit=0.05,        # TP at 5% equity-up from entry
        **COSTS_ZERO,
    )
    eq = np.asarray(equity)

    # Equity rises until bar where cumulative up >= 5%, then flat thereafter.
    # +1%/bar compounded → bar 5 = +5.1% from initial. TP fires, next bar flat.
    rises = np.diff(eq) > 0
    # At least one bar must be flat after a rising prefix.
    assert rises.sum() >= 1, "expected some rising bars before TP"
    assert (np.diff(eq)[-3:] == 0).all(), \
        f"expected flat tail after TP; got eq tail = {eq[-3:]}"
```

- [ ] **Step 1.2: Run the test to confirm it fails on missing kwarg**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/strategies/test_sltp_sweep.py::test_take_profit_triggers_and_flattens_next_bar -xvs`

Expected: `TypeError: run_coin_backtest() got an unexpected keyword argument 'take_profit'` — confirms the test exercises the new code path before it exists.

- [ ] **Step 1.3: Add `take_profit` parameter + mirror block to the engine**

Edit `scripts/baseline_strategy_v2.py`. Add `take_profit: float = 0.0,` to the signature of `run_coin_backtest` (insert directly after the `stop_loss: float,` line at the current line ~90). Then insert the TP block immediately after the existing SL block. The exact diff:

```python
# In the def run_coin_backtest(...) signature, after the line:
#     stop_loss: float,
# add:
    take_profit: float = 0.0,
```

```python
# In the body, AFTER the existing block (currently at lines ~135-138):
#     if target_pos != 0 and entry_equity > 0:
#         trade_dd = (entry_equity - new_equity) / entry_equity
#         if trade_dd >= stop_loss:
#             target_pos = 0.0
# add a sibling TP check, indented under the SAME if-statement so it reuses entry_equity:

        trade_up = (new_equity - entry_equity) / entry_equity
        if take_profit > 0 and trade_up >= take_profit:
            target_pos = 0.0
```

Resulting block reads:

```python
        if target_pos != 0 and entry_equity > 0:
            trade_dd = (entry_equity - new_equity) / entry_equity
            if trade_dd >= stop_loss:
                target_pos = 0.0
            trade_up = (new_equity - entry_equity) / entry_equity
            if take_profit > 0 and trade_up >= take_profit:
                target_pos = 0.0
```

- [ ] **Step 1.4: Run the TP-trigger test to verify it passes**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/strategies/test_sltp_sweep.py::test_take_profit_triggers_and_flattens_next_bar -xvs`

Expected: `PASSED`.

- [ ] **Step 1.5: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/baseline_strategy_v2.py tests/strategies/test_sltp_sweep.py
git commit -m "feat(v2-engine): add take_profit param to run_coin_backtest

Mirrors the existing close-to-close stop_loss block. Disabled by default
(take_profit=0.0), so existing callers are bit-identical."
```

---

## Task 2: Regression-guard `take_profit=0` against current engine

**Files:**
- Modify: `tests/strategies/test_sltp_sweep.py` (add tests)

- [ ] **Step 2.1: Write the TP-disabled bit-identity test**

Append to `tests/strategies/test_sltp_sweep.py`:

```python
def test_take_profit_zero_is_bit_identical_to_no_tp_kwarg():
    """take_profit=0 must produce IDENTICAL equity to omitting the kwarg."""
    rng = np.random.default_rng(42)
    n = 200
    dates = np.arange(n)
    # synthetic price walk
    rets = rng.normal(0.0005, 0.02, size=n)
    prices = 100.0 * np.cumprod(1 + rets)
    # positions: mostly +1, occasional flat, occasional -1
    positions = rng.choice([-1.0, 0.0, 1.0], size=n, p=[0.3, 0.2, 0.5])

    common = dict(
        dates=dates, prices=prices, positions=positions,
        initial_capital=10_000.0, stop_loss=0.03,
        fee_rate=0.0004, slippage=0.0005, spread=0.0001,
        price_impact=0.00005, funding_rate=0.0001 / 8,
        max_portfolio_dd=0.15,
    )

    eq_no_kwarg, m_no = run_coin_backtest(**common)
    eq_tp_zero, m_tp = run_coin_backtest(take_profit=0.0, **common)

    np.testing.assert_array_equal(
        np.asarray(eq_no_kwarg), np.asarray(eq_tp_zero),
        err_msg="take_profit=0.0 changed equity vs no-kwarg path"
    )
    assert m_no == m_tp, "metrics dict diverged when take_profit=0.0"
```

- [ ] **Step 2.2: Write the SL-still-fires-with-TP-active test**

Append:

```python
def test_stop_loss_still_fires_when_take_profit_enabled():
    """With both SL and TP set, a falling position still exits via SL."""
    dates = np.arange(10)
    # Price falls 1%/bar from 100. Long position.
    prices = 100.0 * (0.99 ** np.arange(10))
    positions = np.ones(10)

    equity, _m = run_coin_backtest(
        dates=dates, prices=prices, positions=positions,
        initial_capital=10_000.0,
        stop_loss=0.03,       # active
        take_profit=0.05,     # active (irrelevant for a losing trade)
        **COSTS_ZERO,
    )
    eq = np.asarray(equity)
    # Falling equity then must go flat after SL fires.
    assert (np.diff(eq)[-3:] == 0).all(), \
        f"SL did not flatten falling trade; tail = {eq[-3:]}"
```

- [ ] **Step 2.3: Run the new tests**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/strategies/test_sltp_sweep.py -xvs`

Expected: all 3 tests PASS.

- [ ] **Step 2.4: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tests/strategies/test_sltp_sweep.py
git commit -m "test(v2-engine): regression-guard take_profit=0 + SL+TP interaction"
```

---

## Task 3: Thread `early_exit_loss` + `take_profit` through baseline_v5_mix

**Files:**
- Modify: `scripts/baseline_v5_mix.py:62-67, 89-99, 115-135`

- [ ] **Step 3.1: Add `take_profit` to `COSTS` dict (engine pass-through)**

Edit the `COSTS` dict declaration in `scripts/baseline_v5_mix.py` (currently lines 63-67). Add `take_profit=0.0`:

```python
COSTS = dict(
    fee_rate=0.0004, slippage=0.0005, spread=0.0001,
    price_impact=0.00005, funding_rate=0.0001 / 8,
    stop_loss=0.03, take_profit=0.0, max_portfolio_dd=0.15,
)
```

- [ ] **Step 3.2: Make `_v2_positions` accept `early_exit_loss` override**

Replace the current `_v2_positions` function (currently lines 89-99) with:

```python
def _v2_positions(
    merged: pd.DataFrame,
    kelly_fraction: float = 0.5,
    early_exit_loss: float = 0.015,
) -> np.ndarray:
    sig, conf = generate_term_structure_signals(merged, [7, 14], 0.05, asymmetric=True)
    px = merged["Close"].astype(float).values
    rv = compute_realized_vol(px, lookback=20)
    mask = vol_regime_mask(rv, percentile_cap=0.95)
    pos = build_positions_with_hold(
        signals=sig, vol_ok=mask, confidence=conf, realized_vol=rv, prices=px,
        target_vol=0.10, kelly_fraction=kelly_fraction, max_leverage=3.0,
        min_hold=7, early_exit_loss=early_exit_loss,
    )
    return apply_trend_filter(pos, px, sma_period=30, multiplier=1.5)
```

- [ ] **Step 3.3: Make `run_coin` accept `early_exit_loss` + `costs_override`**

Replace the `run_coin` function (currently lines 115-135) with:

```python
def run_coin(
    coin: str,
    pred_dir: Path,
    start: str,
    end: str,
    kelly_fraction: float = 0.5,
    early_exit_loss: float = 0.015,
    costs_override: dict | None = None,
) -> pd.Series:
    """Run V2 sizing on one coin's routed predictions → daily return series.

    early_exit_loss is forwarded to the position builder.
    costs_override (if supplied) replaces the COSTS dict passed to the engine —
    callers can override stop_loss and take_profit per-call.
    """
    preds = _load_preds(pred_dir, coin)
    preds = preds[(preds["date"] >= start) & (preds["date"] <= end)]
    if preds.empty:
        raise ValueError(f"{coin}: no predictions in [{start}, {end}] under {pred_dir}")
    ohlcv = _load_crypto_ohlcv(coin, end)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    merged = preds.merge(ohlcv[["Date", "Close"]], left_on="date", right_on="Date")
    merged = merged.dropna(subset=["Close"]).reset_index(drop=True)
    merged["ref_price"] = merged["Close"]

    pos = _v2_positions(
        merged, kelly_fraction=kelly_fraction, early_exit_loss=early_exit_loss,
    )
    costs = dict(COSTS if costs_override is None else costs_override)
    equity, _m = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=pos, initial_capital=10_000.0, **costs,
    )
    eq = np.asarray(equity, dtype=float)
    rets = eq[1:] / eq[:-1] - 1.0
    return pd.Series(rets, index=pd.to_datetime(merged["date"].values[1:]), name=coin)
```

- [ ] **Step 3.4: Run a quick smoke to confirm the no-override path still works**

Run: `cd /home/malecada/master_thesis/TradingAgents && python scripts/baseline_v5_mix.py --start 2024-01-01 --end 2024-06-30 --output-dir /tmp/v5_smoke_check`

Expected: prints per-coin SR lines + portfolio summary; no exception; output files written to `/tmp/v5_smoke_check/`. (Short window so this finishes in <60 s.)

- [ ] **Step 3.5: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/baseline_v5_mix.py
git commit -m "refactor(v5-mix): expose early_exit_loss + costs_override for sweep

run_coin and _v2_positions now accept overrides without changing default
behaviour. Existing CLI path is bit-identical (defaults match prior
hard-coded values)."
```

---

## Task 4: V5 baseline reproduction test

**Files:**
- Modify: `tests/strategies/test_sltp_sweep.py` (add integration test)

- [ ] **Step 4.1: Add the baseline-reproduction test**

Append to `tests/strategies/test_sltp_sweep.py`:

```python
@pytest.mark.slow
def test_v5_baseline_reproduces_published_sharpe():
    """Sweep cell (SL=0.03, EE=0.015, TP=0.0) must reproduce V5 MIX SR 3.25 ± 0.05.

    Slow test (~30s wall clock). Run with: pytest -m slow.
    """
    from scripts.baseline_v5_mix import (  # noqa: E402
        COSTS, DEFAULT_ROUTING, run_coin,
    )

    start, end = "2021-11-07", "2026-04-15"
    coin_rets = {}
    for coin, pdir in DEFAULT_ROUTING.items():
        coin_rets[coin] = run_coin(
            coin, PROJECT_ROOT / pdir, start, end,
            kelly_fraction=0.5,
            early_exit_loss=0.015,
            costs_override=dict(COSTS),  # baseline: take_profit=0.0
        )

    import pandas as pd
    df = pd.DataFrame(coin_rets).dropna()
    port = df.mean(axis=1)
    ann = np.sqrt(252)
    sr = float(port.mean() / port.std() * ann)

    assert abs(sr - 3.25) < 0.05, (
        f"V5 baseline reproduction drifted: got SR={sr:.3f}, expected 3.25 ± 0.05"
    )
```

Register the `slow` marker in `pytest.ini` if not already present. Check first:

Run: `grep -n "slow" /home/malecada/master_thesis/TradingAgents/pytest.ini 2>&1 || echo "no slow marker"`

If missing, edit `pytest.ini`:

```ini
[pytest]
markers =
    slow: marks tests that take >5s (deselect with -m "not slow")
```

(Preserve any existing `markers` entries — append to the list.)

- [ ] **Step 4.2: Run the baseline-reproduction test**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/strategies/test_sltp_sweep.py -m slow -xvs`

Expected: PASS with `sr ≈ 3.25`. If it fails by >0.05, STOP — the refactor in Task 3 has changed behaviour and must be diagnosed before proceeding.

- [ ] **Step 4.3: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tests/strategies/test_sltp_sweep.py pytest.ini
git commit -m "test(v5-mix): baseline-reproduction guard for sweep refactor

Asserts the (SL=0.03, EE=0.015, TP=off) cell still produces SR 3.25 ± 0.05
on the canonical 4.5-yr window. Marked slow."
```

---

## Task 5: Sweep harness

**Files:**
- Create: `scripts/v5_mix_sltp_sweep.py`

- [ ] **Step 5.1: Write the sweep script**

Create `scripts/v5_mix_sltp_sweep.py`:

```python
#!/usr/bin/env python
"""V5 MIX TP/SL parameter sensitivity sweep.

Iterates a 9 × 6 × 7 grid of (stop_loss, early_exit_loss, take_profit) cells
against the V5 MIX 4-coin equal-weight portfolio over the canonical 4.5-yr
walk-forward window. Caches positions per early_exit_loss value to avoid
redundant position-builder runs (EE drives positions; SL and TP only drive
the engine).

Outputs to data/v5_sltp_sweep/:
  results.csv  — one row per (sl, ee, tp) × scope (portfolio + 4 coins)
  summary.json — grid + V5 baseline reproduction + best cell + git SHA

Reporting (top20.md + heatmaps) is generated by scripts/v5_sltp_sweep_report.py.
"""
from __future__ import annotations

import argparse
import itertools
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
    COSTS, DEFAULT_ROUTING, _load_preds, _v2_positions,
)
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402

ANN = float(np.sqrt(252))

SL_GRID = [0.0, 0.005, 0.01, 0.015, 0.02, 0.03, 0.05, 0.07, 0.10]   # 0.0 = disabled
EE_GRID = [1.0, 0.005, 0.01, 0.015, 0.02, 0.03]                     # 1.0 = effectively disabled (loss > 100%)
TP_GRID = [0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12]                 # 0.0 = disabled

# Smaller grids for smoke
SMOKE_SL = [0.0, 0.03]
SMOKE_EE = [0.015]
SMOKE_TP = [0.0, 0.05]


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT
        ).decode().strip()
    except Exception:
        return "unknown"


def _metrics(rets: np.ndarray) -> dict:
    if len(rets) == 0:
        return dict(sharpe=0.0, total_return=0.0, max_drawdown=0.0,
                    calmar=0.0, win_rate=0.0, profit_factor=0.0, n_bars=0)
    eq = np.cumprod(1.0 + rets)
    sd = float(rets.std(ddof=1)) if len(rets) > 1 else 0.0
    sr = float(rets.mean() / sd * ANN) if sd > 0 else 0.0
    total = float(eq[-1] - 1.0)
    n_yr = len(rets) / 252.0
    ann_ret = (1.0 + total) ** (1.0 / n_yr) - 1.0 if n_yr > 0 else 0.0
    running_max = np.maximum.accumulate(eq)
    dd = float(np.max((running_max - eq) / running_max)) if len(eq) else 0.0
    calmar = float(ann_ret / dd) if dd > 0 else 0.0
    wins = int((rets > 0).sum())
    losses_n = int((rets < 0).sum())
    n_traded = wins + losses_n
    win_rate = float(wins / n_traded) if n_traded > 0 else 0.0
    gp = float(rets[rets > 0].sum())
    gl = float(np.abs(rets[rets < 0].sum()))
    pf = float(gp / gl) if gl > 0 else (float("inf") if gp > 0 else 0.0)
    return dict(
        sharpe=sr, total_return=total, max_drawdown=dd, calmar=calmar,
        win_rate=win_rate, profit_factor=pf, n_bars=int(len(rets)),
    )


def _load_coin_data(coin: str, pred_dir: Path, start: str, end: str) -> pd.DataFrame:
    """Load + merge preds with OHLCV. Same path baseline_v5_mix.run_coin uses."""
    preds = _load_preds(pred_dir, coin)
    preds = preds[(preds["date"] >= start) & (preds["date"] <= end)]
    if preds.empty:
        raise ValueError(f"{coin}: no predictions in [{start}, {end}] under {pred_dir}")
    ohlcv = _load_crypto_ohlcv(coin, end)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    merged = preds.merge(ohlcv[["Date", "Close"]], left_on="date", right_on="Date")
    merged = merged.dropna(subset=["Close"]).reset_index(drop=True)
    merged["ref_price"] = merged["Close"]
    return merged


def _engine_returns(merged: pd.DataFrame, positions: np.ndarray,
                    sl: float, tp: float) -> pd.Series:
    costs = dict(COSTS)
    costs["stop_loss"] = sl
    costs["take_profit"] = tp
    equity, _m = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=positions, initial_capital=10_000.0, **costs,
    )
    eq = np.asarray(equity, dtype=float)
    rets = eq[1:] / eq[:-1] - 1.0
    return pd.Series(rets, index=pd.to_datetime(merged["date"].values[1:]))


def run_sweep(
    sl_grid: list[float], ee_grid: list[float], tp_grid: list[float],
    start: str, end: str, kelly_fraction: float, out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    coin_data: dict[str, pd.DataFrame] = {}
    for coin, pdir in DEFAULT_ROUTING.items():
        coin_data[coin] = _load_coin_data(coin, PROJECT_ROOT / pdir, start, end)
    print(f"  Loaded {len(coin_data)} coins in {time.time() - t0:.1f}s")

    rows: list[dict] = []
    n_cells = len(sl_grid) * len(ee_grid) * len(tp_grid)
    cell_i = 0
    baseline_port_sr = None

    for ee in ee_grid:
        # Build positions once per EE (cached across SL × TP inner loop).
        position_cache: dict[str, np.ndarray] = {}
        for coin, merged in coin_data.items():
            position_cache[coin] = _v2_positions(
                merged, kelly_fraction=kelly_fraction, early_exit_loss=ee,
            )
        for sl in sl_grid:
            for tp in tp_grid:
                cell_i += 1
                coin_rets: dict[str, pd.Series] = {}
                for coin, merged in coin_data.items():
                    coin_rets[coin] = _engine_returns(
                        merged, position_cache[coin], sl=sl, tp=tp,
                    )
                df = pd.DataFrame(coin_rets).dropna()
                port = df.mean(axis=1)
                pm = _metrics(port.values)

                rows.append(dict(
                    sl=sl, ee=ee, tp=tp, scope="portfolio", **pm,
                ))
                for coin, r in coin_rets.items():
                    cm = _metrics(r.values)
                    rows.append(dict(
                        sl=sl, ee=ee, tp=tp, scope=coin, **cm,
                    ))

                if sl == 0.03 and ee == 0.015 and tp == 0.0:
                    baseline_port_sr = pm["sharpe"]

                if cell_i % 20 == 0 or cell_i == n_cells:
                    elapsed = time.time() - t0
                    eta = elapsed / cell_i * (n_cells - cell_i)
                    print(f"  cell {cell_i}/{n_cells}  "
                          f"SL={sl:.3f} EE={ee:.3f} TP={tp:.3f}  "
                          f"port SR={pm['sharpe']:+.2f}  "
                          f"elapsed={elapsed:.0f}s  eta={eta:.0f}s")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_dir / "results.csv", index=False)

    port_only = df_out[df_out["scope"] == "portfolio"].copy()
    best = port_only.sort_values("sharpe", ascending=False).iloc[0]

    summary = dict(
        grid=dict(sl=sl_grid, ee=ee_grid, tp=tp_grid),
        window=dict(start=start, end=end),
        kelly_fraction=kelly_fraction,
        baseline_cell=dict(sl=0.03, ee=0.015, tp=0.0,
                           portfolio_sharpe=baseline_port_sr),
        best_cell=dict(
            sl=float(best["sl"]), ee=float(best["ee"]), tp=float(best["tp"]),
            portfolio_sharpe=float(best["sharpe"]),
            total_return=float(best["total_return"]),
            max_drawdown=float(best["max_drawdown"]),
            calmar=float(best["calmar"]),
        ),
        n_cells=n_cells,
        wall_clock_sec=time.time() - t0,
        git_sha=_git_sha(),
    )
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n  Wrote: {out_dir / 'results.csv'}  ({len(df_out)} rows)")
    print(f"  Wrote: {out_dir / 'summary.json'}")
    if baseline_port_sr is not None:
        print(f"  Baseline cell SR = {baseline_port_sr:+.3f} "
              f"(published V5 MIX = +3.25)")
    print(f"  Best cell: SL={best['sl']} EE={best['ee']} TP={best['tp']}  "
          f"SR={best['sharpe']:+.3f}  DD={best['max_drawdown']:.1%}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", default="2021-11-07")
    p.add_argument("--end", default="2026-04-15")
    p.add_argument("--output-dir", default="data/v5_sltp_sweep")
    p.add_argument("--kelly", type=float, default=0.5)
    p.add_argument("--smoke", action="store_true",
                   help="Smoke run on tiny grid (2×1×2=4 cells)")
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
    print(f"\n  V5 MIX TP/SL sweep")
    print(f"  window : {args.start} → {args.end}")
    print(f"  grid   : SL={len(sl)} EE={len(ee)} TP={len(tp)} = {len(sl) * len(ee) * len(tp)} cells")
    print(f"  output : {out_dir}\n")

    run_sweep(sl, ee, tp, args.start, args.end, args.kelly, out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5.2: Run the smoke (4 cells, ~2 min)**

Run: `cd /home/malecada/master_thesis/TradingAgents && python scripts/v5_mix_sltp_sweep.py --smoke --output-dir /tmp/v5_sltp_smoke`

Expected: 4 cells complete, `results.csv` has 4 × 5 = 20 rows, `summary.json` written. The smoke grid intentionally **does** include the baseline cell `(SL=0.03, EE=0.015, TP=0.0)` so the printed baseline SR should be a real number ≈ 3.25 (short-window noise tolerated). If it is `None` or wildly off, the baseline-cell detection in `run_sweep` is broken — investigate.

- [ ] **Step 5.3: Verify the smoke output shape**

Run: `python -c "import pandas as pd; df = pd.read_csv('/tmp/v5_sltp_smoke/results.csv'); print(df.shape); print(df.head(10)); print(df['scope'].value_counts())"`

Expected: `(20, 10)`; 5 scopes (portfolio, bitcoin, ethereum, binancecoin, solana) × 4 cells = 20 rows; each scope appears exactly 4 times.

- [ ] **Step 5.4: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/v5_mix_sltp_sweep.py
git commit -m "feat(sweep): V5 MIX TP/SL sensitivity sweep harness

378-cell grid, per-EE position cache, portfolio + per-coin metrics.
Smoke mode with 4-cell grid for fast iteration."
```

---

## Task 6: Full sweep run

**Files:**
- Runtime output only: `data/v5_sltp_sweep/results.csv`, `data/v5_sltp_sweep/summary.json`

- [ ] **Step 6.1: Launch the full 378-cell sweep**

Run: `cd /home/malecada/master_thesis/TradingAgents && python scripts/v5_mix_sltp_sweep.py --output-dir data/v5_sltp_sweep 2>&1 | tee data/v5_sltp_sweep/sweep.log`

Expected runtime: ~3 hours wall clock (engine evaluation ~30s × 378 cells, amortised by per-EE position cache → realistically 1.5-2h). Progress prints every 20 cells.

If wall clock exceeds 6h, kill and add `joblib.Parallel(n_jobs=-1)` over the inner SL×TP loop per EE.

- [ ] **Step 6.2: Verify baseline reproduction**

Run: `python -c "import json; s = json.load(open('data/v5_sltp_sweep/summary.json')); print('baseline:', s['baseline_cell']); print('best:', s['best_cell'])"`

Expected: `baseline_cell.portfolio_sharpe` within 0.05 of 3.25. If not, the sweep is suspect — investigate before proceeding to reporting.

- [ ] **Step 6.3: Sanity-check the output**

Run: `python -c "import pandas as pd; df = pd.read_csv('data/v5_sltp_sweep/results.csv'); print(df.shape); print('cells:', df.drop_duplicates(['sl','ee','tp']).shape[0]); print(df['scope'].value_counts())"`

Expected: `(1890, 10)`, 378 unique cells, 378 rows per scope × 5 scopes.

- [ ] **Step 6.4: Commit the results files**

```bash
cd /home/malecada/master_thesis/TradingAgents
# results dir likely gitignored under data/; force-add if so:
git add -f data/v5_sltp_sweep/results.csv data/v5_sltp_sweep/summary.json
git commit -m "results(sweep): V5 MIX TP/SL full 378-cell sweep output

Baseline cell reproduces published V5 MIX SR 3.25 ± tolerance.
See summary.json for best cell + grid metadata."
```

---

## Task 7: Reporting — top-20 + heatmaps

**Files:**
- Create: `scripts/v5_sltp_sweep_report.py`

- [ ] **Step 7.1: Write the reporting script**

Create `scripts/v5_sltp_sweep_report.py`:

```python
#!/usr/bin/env python
"""Generate top-20 markdown + 12 heatmap PNGs from V5 MIX TP/SL sweep results."""
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

    # Annotate each cell with value
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
    p.add_argument("--input-dir", default="data/v5_sltp_sweep")
    args = p.parse_args()

    in_dir = PROJECT_ROOT / args.input_dir
    df = pd.read_csv(in_dir / "results.csv")
    port = df[df["scope"] == "portfolio"].copy()

    # ── Top-20 markdown ────────────────────────────────────────────────
    top = port.sort_values("sharpe", ascending=False).head(20).copy()
    lines = [
        "# V5 MIX TP/SL Sweep — Top 20 Cells (by portfolio Sharpe)",
        "",
        f"Source: `{in_dir / 'results.csv'}` ({len(port)} portfolio cells)",
        "",
        "Baseline V5 cell: SL=0.03, EE=0.015, TP=off "
        f"→ SR = {port[(port['sl'] == 0.03) & (port['ee'] == 0.015) & (port['tp'] == 0.0)]['sharpe'].iloc[0]:+.3f}",
        "",
        "| Rank | SL | EE | TP | Sharpe | Total Ret | Max DD | Calmar | Win % | PF |",
        "|------|-----|-----|-----|--------|-----------|--------|--------|-------|-----|",
    ]
    for rank, (_, r) in enumerate(top.iterrows(), start=1):
        is_baseline = (r["sl"] == 0.03 and r["ee"] == 0.015 and r["tp"] == 0.0)
        marker = " ← **baseline**" if is_baseline else ""
        lines.append(
            f"| {rank} | {r['sl']:g} | {r['ee']:g} | {r['tp']:g} | "
            f"{r['sharpe']:+.3f}{marker} | {r['total_return']:+.1%} | "
            f"{r['max_drawdown']:.1%} | {r['calmar']:+.2f} | "
            f"{r['win_rate']:.1%} | {r['profit_factor']:.2f} |"
        )
    (in_dir / "top20.md").write_text("\n".join(lines) + "\n")
    print(f"  Wrote: {in_dir / 'top20.md'}")

    # ── Heatmaps: per EE, SR(SL × TP) + DD(SL × TP) ────────────────────
    heat_dir = in_dir / "heatmaps"
    heat_dir.mkdir(exist_ok=True)
    n = 0
    for ee in sorted(port["ee"].unique()):
        sub = port[port["ee"] == ee]
        for metric, label, cmap_inv in [
            ("sharpe", "Portfolio Sharpe", False),
            ("max_drawdown", "Max Drawdown", True),
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


if __name__ == "__main__":
    main()
```

- [ ] **Step 7.2: Run reporting on sweep output**

Run: `cd /home/malecada/master_thesis/TradingAgents && python scripts/v5_sltp_sweep_report.py --input-dir data/v5_sltp_sweep`

Expected: `top20.md` written + 12 PNGs (6 EE × 2 metrics) under `data/v5_sltp_sweep/heatmaps/`. Confirm:

Run: `ls data/v5_sltp_sweep/heatmaps/*.png | wc -l && head -30 data/v5_sltp_sweep/top20.md`

Expected: `12` PNGs; top-20 table shows highest-SR cells with the baseline marked.

- [ ] **Step 7.3: Commit script + reports**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/v5_sltp_sweep_report.py
git add -f data/v5_sltp_sweep/top20.md data/v5_sltp_sweep/heatmaps/
git commit -m "report(sweep): top-20 markdown + 12 SR/DD heatmaps

One heatmap per (metric × early_exit_loss). Baseline V5 cell marked
on the EE=0.015 panels."
```

---

## Task 8: THESIS_NARRATIVE.md §24

**Files:**
- Modify: `THESIS_NARRATIVE.md` (append new section)

- [ ] **Step 8.1: Determine the correct section anchor**

Run: `grep -n "^## §2[0-9]" /home/malecada/master_thesis/TradingAgents/THESIS_NARRATIVE.md | tail -10`

Use the highest existing § number + 1 as the new section ID. If the latest section is §23, use §24. If a higher number already exists, use the next available.

- [ ] **Step 8.2: Append §24 (or next available) to THESIS_NARRATIVE.md**

Append the following section. **Before writing, substitute the live numbers** from `data/v5_sltp_sweep/summary.json` (baseline SR, best cell parameters, best SR, best DD, best Calmar) into the placeholders marked `<<...>>`:

```markdown

## §24 TP/SL Parameter Sensitivity Sweep

**Goal.** Quantify whether the V5 MIX portfolio is sensitive to its risk-management
parameters: the close-to-close equity stop-loss (SL), the early-exit-on-signal-flip
loss threshold (EE), and a new take-profit (TP) leg. Framed as a sensitivity
analysis — output is a SR/DD landscape, not a tuned recommendation.

**Method.** The existing V2 engine (`scripts/baseline_strategy_v2.py:run_coin_backtest`)
already implements an equity-drawdown-from-entry stop-loss (default 3 %) and an
early-exit-on-loss-and-signal-flip rule (default 1.5 %). A `take_profit`
parameter was added as a sibling of the stop-loss check (`take_profit = 0` is
bit-identical to the prior engine; regression-tested). A 9 × 6 × 7 grid was
swept against the canonical 4-coin V5 MIX portfolio over the 4.5-year
walk-forward window (2021-11-07 → 2026-04-15), reusing the per-coin
prediction routing of §20:

| Parameter | Values |
|---|---|
| stop_loss | off, 0.5 %, 1 %, 1.5 %, 2 %, **3 %** (V5), 5 %, 7 %, 10 % |
| early_exit_loss | off, 0.5 %, 1 %, **1.5 %** (V5), 2 %, 3 % |
| take_profit | **off** (V5), 1 %, 2 %, 3 %, 5 %, 8 %, 12 % |

378 cells × 4 coins × ~1100 daily bars. Positions are cached per `early_exit_loss`
value (positions depend on EE but not on SL or TP).

**Reproduction.** The baseline cell (SL = 3 %, EE = 1.5 %, TP = off) reproduces
SR = <<BASELINE_SR>> (published V5 MIX = +3.25; tolerance ± 0.05).

**Result — best cell.** SL = <<BEST_SL>>, EE = <<BEST_EE>>, TP = <<BEST_TP>>
→ Sharpe <<BEST_SR>>, total return <<BEST_RET>>, max DD <<BEST_DD>>,
Calmar <<BEST_CALMAR>>. Delta vs baseline: ΔSR = <<DELTA_SR>>,
ΔDD = <<DELTA_DD>>.

**Landscape.** [Insert heatmaps:
`data/v5_sltp_sweep/heatmaps/sharpe_sl_x_tp__ee_0.015.png` and
`data/v5_sltp_sweep/heatmaps/max_drawdown_sl_x_tp__ee_0.015.png`.] The
landscape is interpreted as **<<FLAT | PEAKED>>** — describe whether the SR
varies by < 0.3 across the grid (flat → V5 robust to parameter choice) or
shows a clear ridge / peak (peaked → SL/TP material; warrants intrabar
validation in a follow-up).

**Limitations.**
1. Close-to-close SL/TP only — intrabar wicks not modelled. Real fills under tight SL would be worse (long wick risk in crypto).
2. Single 4.5-year window — no out-of-sample param validation. Best cell may not generalise.
3. Global tuple — same SL/EE/TP across all 4 coins. Per-coin optimisation deferred (overfit risk).
4. No statistical test — improvements over baseline reported as point estimates only.

**No live deployment recommendation.** Production parameters in
`src_live/config.py` (`STOP_LOSS_PCT = 0.03`) remain unchanged pending
intrabar OHLC validation (approach B in the design spec, conditional on this
landscape being peaked).

**Artifacts.** Top-20 cells: `data/v5_sltp_sweep/top20.md`. Full results:
`data/v5_sltp_sweep/results.csv`. Grid + best-cell metadata + git SHA:
`data/v5_sltp_sweep/summary.json`. Heatmap PNGs:
`data/v5_sltp_sweep/heatmaps/`.

**Spec / plan.**
[`docs/superpowers/specs/2026-05-19-v5-sltp-sweep-design.md`](docs/superpowers/specs/2026-05-19-v5-sltp-sweep-design.md),
[`docs/superpowers/plans/2026-05-19-v5-sltp-sweep.md`](docs/superpowers/plans/2026-05-19-v5-sltp-sweep.md).
```

- [ ] **Step 8.3: Verify substitutions**

Run: `grep -n "<<.*>>" /home/malecada/master_thesis/TradingAgents/THESIS_NARRATIVE.md`

Expected: zero matches. If any `<<...>>` placeholder remains, fix it from `summary.json` and the chosen heatmap interpretation.

- [ ] **Step 8.4: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add THESIS_NARRATIVE.md
git commit -m "docs(thesis): §24 TP/SL parameter sensitivity sweep

V5 MIX 378-cell SL/EE/TP grid over 4.5-yr WF. Reports baseline
reproduction, best cell, landscape interpretation, limitations.
No live parameter change recommended."
```

---

## Task 9: Final verification

**Files:** none modified

- [ ] **Step 9.1: Run the full test suite for the new file**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/strategies/test_sltp_sweep.py -v`

Expected: 3 fast tests PASS. (The slow baseline-reproduction test is excluded by default; run separately with `-m slow` if you want to re-verify.)

- [ ] **Step 9.2: Run the strategies suite for regression**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/strategies/ -v --ignore=tests/strategies/test_sltp_sweep.py`

Expected: all existing strategies tests still PASS. The Task 1 engine edit added a new kwarg with default 0.0 — no existing call site should break.

- [ ] **Step 9.3: Confirm git status is clean**

Run: `cd /home/malecada/master_thesis/TradingAgents && git status --short`

Expected: only previously-untracked WIP files from before this branch (e.g. `LLM_LIMITATIONS_AND_RESEARCH_GAPS.md`, `scripts/generate_thesis_figures.py`). No untracked files from this plan's work — everything committed.

- [ ] **Step 9.4: Confirm the branch state**

Run: `cd /home/malecada/master_thesis/TradingAgents && git log --oneline feature/v5-sltp-sweep ^main`

Expected: 8-9 commits (spec + Tasks 1, 2, 3, 4, 5, 6, 7, 8), in order.

---

## Done

The branch `feature/v5-sltp-sweep` now contains:
- Engine extension with `take_profit` (bit-identical default)
- Sweep harness + reporting tooling
- 378-cell sweep results + 12 heatmaps + top-20 markdown
- THESIS_NARRATIVE.md §24 with baseline reproduction + best-cell delta + landscape interpretation

If the landscape is **peaked**, open a new spec for approach B (intrabar OHLC). If **flat**, the conclusion stands: V5 MIX is robust to SL/EE/TP parameter choice, no live change warranted.
