# Intraday (1h) Triple-Barrier SL/TP Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Find the statistically defensible best SL/TP (+trailing) configuration for the 4-coin V5 MIX, using intraday 1h bars to model intrabar barrier fills correctly (removing §29's close-to-close look-ahead bias), and decide via DSR + CPCV/OOS + paired bootstrap whether ANY cell beats the a-priori 3% stop.

**Architecture:** Daily V2 signals/positions are unchanged. We overlay a *triple-barrier* exit model (López de Prado) — SL (lower), TP (upper), trailing, all checked **intrabar** by walking that day's 1h bars in chronological order — onto the existing daily equity loop. Barriers fire on **equity-since-entry** (so leverage is already baked in, matching the current daily stop semantics). The only behavioral difference vs the §29 daily engine is *when within a day* a barrier fills. A new sweep grid (refined SL×TP + trailing, EE fixed off) is evaluated on the intrabar engine; the best cell is then subjected to DSR (over all N cells), an IS/OOS split, and a paired bootstrap against the 3% baseline. Deliverable splits into a thesis §31 section and a staged production-change recommendation.

**Tech Stack:** Python 3.9+, numpy, pandas, requests (Binance public klines), pyarrow (parquet), scipy.stats (in existing DSR), pytest. Reuses: `scripts/baseline_strategy_v2.run_coin_backtest`, `scripts/baseline_v5_mix` (`COSTS`, `DEFAULT_ROUTING`, `_v2_positions`, `_load_preds`), `scripts/v5_mix_sltp_sweep` patterns, `tradingagents/strategies/v3/backtest/dsr.py`, `scripts/bootstrap_hybrid.diff_sharpe_ci`, `scripts/bootstrap_sharpe`.

---

## File Structure

| Path | Responsibility | Create/Modify |
|------|----------------|---------------|
| `tradingagents/dataflows/coingecko_binance.py` | Add `interval`-parameterized kline fetch + `fetch_binance_klines_range()`; existing daily path untouched | Modify (`_binance_klines` ~L101, `_binance_klines_chunked` ~L120) |
| `scripts/fetch_intraday_1h.py` | CLI: download 1h klines for 4 coins → `data/intraday_1h/{coin}.parquet` | Create |
| `scripts/intraday_fills.py` | Intraday bar loader + `run_coin_backtest_intrabar()` triple-barrier engine | Create |
| `scripts/intraday_sltp_sweep.py` | Refined SL×TP + trailing sweep on intrabar engine; daily-vs-intraday bias cross-check | Create |
| `scripts/intraday_sltp_stats.py` | DSR over grid + bootstrap CI on best + paired bootstrap best-vs-3% + IS/OOS split | Create |
| `scripts/intraday_sltp_report.py` | Heatmaps + top-20 + bias figure | Create |
| `tests/strategies/test_intraday_fills.py` | Unit tests for loader + intrabar engine (incl. equivalence to daily engine) | Create |
| `tests/dataflows/test_intraday_fetch.py` | Unit test for kline parsing/interval param (mocked) | Create |
| `data/intraday_1h/{coin}.parquet` | Cached 1h OHLCV per coin | Generated |
| `data/intraday_sltp_sweep/` | results.csv, summary.json, stats.json, figures | Generated |
| `THESIS_FINDINGS.md` | New §31 write-up | Modify |

**Coins (4-coin V5 MIX core):** `bitcoin, ethereum, binancecoin, solana` (= `baseline_v5_mix.CORE_COINS`; the §29 SR +3.178 baseline). Binance perp symbols: `BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT`.

**Window:** `2021-11-07 → 2026-04-15` (canonical 4.5-yr WF). IS/OOS split point for Task 6: IS = start→`2025-04-15`, OOS = `2025-04-15`→end (last ~12 mo held out).

---

## Task 1: Interval-parameterized Binance kline fetch

**Files:**
- Modify: `tradingagents/dataflows/coingecko_binance.py` (`_binance_klines` ~L101-117, add `fetch_binance_klines_range` after `_binance_klines_chunked` ~L134)
- Test: `tests/dataflows/test_intraday_fetch.py`

Background: `_binance_klines` (L101) hardcodes `"interval": "1d"` and `_binance_klines_chunked` (L120) hardcodes a `+86_400_000` (1-day) cursor step. We add an `interval` param + a generic range fetcher. The existing daily callers keep working because `interval` defaults to `"1d"` and the daily step is selected by interval.

- [ ] **Step 1: Write the failing test**

```python
# tests/dataflows/test_intraday_fetch.py
from __future__ import annotations

import pandas as pd
import pytest

from tradingagents.dataflows import coingecko_binance as cgb


def _fake_kline(open_ms: int, o: float, h: float, l: float, c: float) -> list:
    # Binance kline row layout: [openTime, open, high, low, close, volume, closeTime, ...]
    return [open_ms, str(o), str(h), str(l), str(c), "1.0", open_ms + 3_600_000, "0", 0, "0", "0", "0"]


def test_interval_passthrough(monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured.update(params)

        class R:
            def raise_for_status(self):
                pass

            def json(self):
                return [_fake_kline(1_600_000_000_000, 1, 2, 0.5, 1.5)]

        return R()

    monkeypatch.setattr(cgb.requests, "get", fake_get)
    out = cgb._binance_klines("BTCUSDT", 1_600_000_000_000, 1_600_003_600_000, interval="1h")
    assert captured["interval"] == "1h"
    assert len(out) == 1


def test_fetch_klines_range_parses_ohlc(monkeypatch):
    base = 1_600_000_000_000

    def fake_chunked(symbol, from_ms, to_ms, interval="1d", step_ms=None):
        return [_fake_kline(base + i * 3_600_000, 10 + i, 11 + i, 9 + i, 10.5 + i) for i in range(3)]

    monkeypatch.setattr(cgb, "_binance_klines_chunked", fake_chunked)
    df = cgb.fetch_binance_klines_range("BTCUSDT", base, base + 3 * 3_600_000, interval="1h")
    assert list(df.columns) == ["open_time", "open", "high", "low", "close", "volume"]
    assert len(df) == 3
    assert df["high"].iloc[0] == 11.0
    assert df["open_time"].is_monotonic_increasing
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/dataflows/test_intraday_fetch.py -v`
Expected: FAIL — `_binance_klines() got an unexpected keyword argument 'interval'` / `module has no attribute 'fetch_binance_klines_range'`.

- [ ] **Step 3: Modify `_binance_klines` and `_binance_klines_chunked` to accept `interval`/`step_ms`**

Replace `_binance_klines` (L101-117) with:

```python
_INTERVAL_MS = {
    "1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000,
    "4h": 14_400_000, "1d": 86_400_000,
}


def _binance_klines(symbol_usdt: str, from_ms: int, to_ms: int, interval: str = "1d") -> list:
    """Fetch klines from Binance public API at the given interval (default daily)."""
    url = f"{_BINANCE_BASE_URL}/klines"
    params = {
        "symbol": symbol_usdt,
        "interval": interval,
        "startTime": int(from_ms),
        "endTime": int(to_ms),
        "limit": _BINANCE_KLINE_LIMIT,
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"Binance klines error for {symbol_usdt} ({interval}): {e}")
        return []
```

Replace `_binance_klines_chunked` (L120-134) with:

```python
def _binance_klines_chunked(
    symbol_usdt: str, from_ms: int, to_ms: int,
    interval: str = "1d", step_ms: int | None = None,
) -> list:
    """Fetch klines from Binance, paginating across the full range.

    Cursor advances past the last returned bar's open_time so no bar is
    fetched twice. ``step_ms`` defaults to the interval's bar width.
    """
    if step_ms is None:
        step_ms = _INTERVAL_MS.get(interval, 86_400_000)
    all_klines = []
    cursor = int(from_ms)
    while cursor < int(to_ms):
        klines = _binance_klines(symbol_usdt, cursor, to_ms, interval=interval)
        if not klines:
            break
        all_klines.extend(klines)
        last_open_ms = klines[-1][0]
        cursor = last_open_ms + step_ms
        if len(klines) < _BINANCE_KLINE_LIMIT:
            break
        time.sleep(0.5)
    return all_klines
```

- [ ] **Step 4: Add `fetch_binance_klines_range` after `_binance_klines_chunked`**

```python
def fetch_binance_klines_range(
    symbol: str, from_ms: int, to_ms: int, interval: str = "1h",
) -> pd.DataFrame:
    """Fetch [from_ms, to_ms) klines at ``interval`` as a tidy DataFrame.

    Columns: open_time (datetime64, UTC-naive), open, high, low, close, volume.
    Deduplicated on open_time, sorted ascending. Empty DataFrame on error.
    """
    if not symbol:
        return pd.DataFrame()
    klines = _binance_klines_chunked(symbol, from_ms, to_ms, interval=interval)
    if not klines:
        return pd.DataFrame()
    rows = [
        {
            "open_time": pd.to_datetime(k[0], unit="ms"),
            "open": float(k[1]), "high": float(k[2]), "low": float(k[3]),
            "close": float(k[4]), "volume": float(k[5]),
        }
        for k in klines
    ]
    df = pd.DataFrame(rows).drop_duplicates(subset="open_time")
    return df.sort_values("open_time").reset_index(drop=True)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/dataflows/test_intraday_fetch.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Verify the daily path still works (regression)**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/ -k "ohlcv or binance or kline" -v`
Expected: PASS (no daily regressions). If no such tests exist, run `python -c "from tradingagents.dataflows.coingecko_binance import _binance_klines; print('ok')"` → prints `ok`.

- [ ] **Step 7: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tradingagents/dataflows/coingecko_binance.py tests/dataflows/test_intraday_fetch.py
git commit -m "feat(data): interval-parameterized Binance kline fetch + range helper"
```

---

## Task 2: Intraday 1h fetch CLI → parquet cache

**Files:**
- Create: `scripts/fetch_intraday_1h.py`
- Test: manual run (network); cache verified by Task 3 loader test using a synthetic parquet.

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python
"""Download 1h OHLCV klines for the 4-coin V5 MIX core and cache to parquet.

One parquet per coin at data/intraday_1h/{coin}.parquet with columns
open_time, open, high, low, close, volume. Incremental: appends only bars
after the last cached open_time. Idempotent.

Usage:
    python scripts/fetch_intraday_1h.py --start 2021-11-07 --end 2026-04-15
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.dataflows.coingecko_binance import fetch_binance_klines_range  # noqa: E402

COIN_SYMBOLS = {
    "bitcoin": "BTCUSDT", "ethereum": "ETHUSDT",
    "binancecoin": "BNBUSDT", "solana": "SOLUSDT",
}


def _to_ms(date_str: str) -> int:
    return int(pd.Timestamp(date_str, tz="UTC").timestamp() * 1000)


def fetch_coin(coin: str, symbol: str, start: str, end: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{coin}.parquet"
    from_ms = _to_ms(start)
    to_ms = _to_ms(end) + 86_400_000  # include the end day's bars

    existing = pd.DataFrame()
    if out_path.exists():
        existing = pd.read_parquet(out_path)
        if not existing.empty:
            last_ms = int(existing["open_time"].max().timestamp() * 1000)
            from_ms = max(from_ms, last_ms + 3_600_000)

    if from_ms >= to_ms:
        print(f"  {coin}: cache up to date ({len(existing)} bars)")
        return out_path

    t0 = time.time()
    fresh = fetch_binance_klines_range(symbol, from_ms, to_ms, interval="1h")
    df = pd.concat([existing, fresh], ignore_index=True) if not existing.empty else fresh
    df = df.drop_duplicates(subset="open_time").sort_values("open_time").reset_index(drop=True)
    df.to_parquet(out_path, index=False)
    print(f"  {coin}: {len(df)} bars (+{len(fresh)} new) in {time.time()-t0:.1f}s → {out_path}")
    return out_path


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", default="2021-11-07")
    p.add_argument("--end", default="2026-04-15")
    p.add_argument("--output-dir", default="data/intraday_1h")
    p.add_argument("--coins", nargs="+", default=list(COIN_SYMBOLS))
    args = p.parse_args()

    out_dir = PROJECT_ROOT / args.output_dir
    for coin in args.coins:
        fetch_coin(coin, COIN_SYMBOLS[coin], args.start, args.end, out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the fetch (network; ~2-4 min for 4 coins)**

Run: `cd /home/malecada/master_thesis/TradingAgents && python scripts/fetch_intraday_1h.py --start 2021-11-07 --end 2026-04-15`
Expected: four lines like `bitcoin: ~39000 bars (+39000 new) in ~30s → data/intraday_1h/bitcoin.parquet`.

- [ ] **Step 3: Verify coverage and gaps**

Run:
```bash
cd /home/malecada/master_thesis/TradingAgents && python -c "
import pandas as pd, glob
for f in sorted(glob.glob('data/intraday_1h/*.parquet')):
    d = pd.read_parquet(f)
    span_h = (d['open_time'].max()-d['open_time'].min()).total_seconds()/3600
    print(f.split('/')[-1], len(d), d['open_time'].min(), d['open_time'].max(),
          'coverage=%.3f' % (len(d)/span_h))
"
```
Expected: each coin ~39000 rows, min ≈ 2021-11-07, max ≈ 2026-04-15, coverage ≈ 0.99-1.00 (near-contiguous hourly bars).

- [ ] **Step 4: Commit (script only; parquet stays untracked/gitignored if large)**

```bash
cd /home/malecada/master_thesis/TradingAgents
echo "data/intraday_1h/" >> .gitignore
git add scripts/fetch_intraday_1h.py .gitignore
git commit -m "feat(data): 1h kline fetch CLI for 4-coin intraday SL/TP sweep"
```

---

## Task 3: Intraday triple-barrier engine

**Files:**
- Create: `scripts/intraday_fills.py`
- Test: `tests/strategies/test_intraday_fills.py`

This is the core. The engine replicates `run_coin_backtest`'s daily equity loop, costs, and stop **semantics** (equity-since-entry from `entry_equity`), but on each held day it walks that day's 1h `(high, low)` bars in order and fires the first barrier touched, capping the day's return at the barrier exit level. When no barrier touches, the day is the exact close-to-close computation of the daily engine — this is enforced by an equivalence test.

**Barrier semantics (per held day i, position `pos`, day-start equity `e0 = equity[i-1]`, prior-close price `p_prev = close[i-1]`):**
- Intraday equity at price `p`: `eq(p) = e0 * (1 + pos * (p - p_prev) / p_prev)`.
- LONG (`pos>0`): adverse extreme = bar `low`, favorable = bar `high`. SHORT (`pos<0`): adverse = `high`, favorable = `low`.
- Walk bars in chronological order. Per bar, in this priority order (most conservative wins ties within a bar): **(1) fixed SL**, **(2) TP**, **(3) trailing**.
  - Fixed SL: `(entry_equity - eq(adverse)) / entry_equity >= stop_loss` → exit equity = `entry_equity*(1-stop_loss)`.
  - TP: `take_profit>0 and (eq(favorable) - entry_equity)/entry_equity >= take_profit` → exit equity = `entry_equity*(1+take_profit)`.
  - Trailing: update running `peak_eq = max(peak_eq, eq(favorable))`; if `trail>0 and (peak_eq - eq(adverse))/peak_eq >= trail` → exit equity = `peak_eq*(1-trail)`.
- First bar that triggers → exit at that bar. Day i realized gross return = `exit_equity/e0 - 1`; then subtract the day's costs (closing-trade fee on `|pos|` + funding on `pos`), flatten for rest of day.
- Re-entry semantics match the daily engine: a barrier only flattens through the end of day i; day i+1 re-reads `positions[i+1]` (re-enters if the signal is still on). This isolates *fill timing* as the sole difference vs §29.

- [ ] **Step 1: Write the failing tests**

```python
# tests/strategies/test_intraday_fills.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.baseline_strategy_v2 import run_coin_backtest
from scripts.intraday_fills import group_intraday_by_day, run_coin_backtest_intrabar

COSTS = dict(
    fee_rate=0.0004, slippage=0.0005, spread=0.0001, price_impact=0.00005,
    funding_rate=0.0001 / 8, stop_loss=0.03, max_portfolio_dd=0.15, take_profit=0.0,
)


def _flat_day_bars(prices, n_bars=4):
    """Synthetic intraday: each day's bars all sit exactly at that day's close
    (no intraday excursion) → barriers can only fire on close-to-close moves,
    so the intrabar engine MUST match the daily engine."""
    day_map = {}
    for i, p in enumerate(prices):
        day_map[i] = np.array([[p, p]] * n_bars, dtype=float)  # (high, low)
    return day_map


def test_equivalence_when_no_intraday_excursion():
    # When intraday high==low==close every bar, intrabar == daily engine.
    dates = np.array([np.datetime64("2024-01-0%d" % d) for d in range(1, 9)])
    prices = np.array([100, 101, 99, 103, 97, 105, 104, 106], dtype=float)
    positions = np.array([0, 1, 1, 1, 1, 1, 1, 0], dtype=float)
    day_map = _flat_day_bars(prices)

    eq_daily, _ = run_coin_backtest(
        dates=dates, prices=prices, positions=positions, initial_capital=10_000.0,
        trailing_stop=0.0 if False else 0.0, **COSTS,
    ) if False else run_coin_backtest(
        dates=dates, prices=prices, positions=positions, initial_capital=10_000.0, **COSTS,
    )
    eq_intra, _ = run_coin_backtest_intrabar(
        dates=dates, prices=prices, positions=positions, intraday=day_map,
        initial_capital=10_000.0, trailing_stop=0.0, **COSTS,
    )
    np.testing.assert_allclose(eq_intra, eq_daily, rtol=1e-9, atol=1e-6)


def test_long_stop_fires_intrabar_even_when_close_is_up():
    # Day 1: enter long at 100. Day 2 close=101 (UP) but intraday low=90 (-10%).
    # Daily engine would NOT stop (close-to-close +1%); intrabar MUST stop at -3%.
    dates = np.array([np.datetime64("2024-01-01"), np.datetime64("2024-01-02")])
    prices = np.array([100.0, 101.0], dtype=float)
    positions = np.array([1.0, 1.0], dtype=float)
    day_map = {0: np.array([[100.0, 100.0]]), 1: np.array([[101.0, 90.0]])}  # day1 low pierces stop

    costs = dict(COSTS); costs["stop_loss"] = 0.03
    eq, _ = run_coin_backtest_intrabar(
        dates=dates, prices=prices, positions=positions, intraday=day_map,
        initial_capital=10_000.0, trailing_stop=0.0, **costs,
    )
    # Stopped at -3% equity from entry (entry_equity == 10_000 at day-0 close).
    # Day-1 gross return capped at -3%; equity ≈ 10_000*(1-0.03) minus a closing fee.
    assert eq[-1] < 10_000.0 * 0.975  # well below the +1% the daily engine would book
    assert eq[-1] > 10_000.0 * 0.95   # not worse than the stop + one fee


def test_long_tp_fires_intrabar():
    dates = np.array([np.datetime64("2024-01-01"), np.datetime64("2024-01-02")])
    prices = np.array([100.0, 100.5], dtype=float)
    positions = np.array([1.0, 1.0], dtype=float)
    day_map = {0: np.array([[100.0, 100.0]]), 1: np.array([[112.0, 100.0]])}  # +12% intraday high
    costs = dict(COSTS); costs["stop_loss"] = 0.50; costs["take_profit"] = 0.05
    eq, _ = run_coin_backtest_intrabar(
        dates=dates, prices=prices, positions=positions, intraday=day_map,
        initial_capital=10_000.0, trailing_stop=0.0, **costs,
    )
    assert eq[-1] > 10_000.0 * 1.045  # booked ~+5% TP, not the +0.5% close


def test_sl_wins_when_both_touched_earlier_bar():
    # Day 1 bar0 low pierces stop; bar1 high pierces TP. SL is in the EARLIER bar → SL wins.
    dates = np.array([np.datetime64("2024-01-01"), np.datetime64("2024-01-02")])
    prices = np.array([100.0, 101.0], dtype=float)
    positions = np.array([1.0, 1.0], dtype=float)
    day_map = {0: np.array([[100.0, 100.0]]),
               1: np.array([[101.0, 90.0], [120.0, 101.0]])}  # bar0 stop, bar1 TP
    costs = dict(COSTS); costs["stop_loss"] = 0.03; costs["take_profit"] = 0.05
    eq, _ = run_coin_backtest_intrabar(
        dates=dates, prices=prices, positions=positions, intraday=day_map,
        initial_capital=10_000.0, trailing_stop=0.0, **costs,
    )
    assert eq[-1] < 10_000.0 * 0.975  # exited via stop, not TP


def test_trailing_stop_ratchets():
    # Enter long at 100. Day 1 runs up to 120 (high) then pulls back; low=108.
    # trail=0.08 → trail level = peak*(1-0.08). peak equity at +20%; 8% off peak
    # equity ≈ +10.4% from entry, and low (108 → +8%) breaches it → trailing exit.
    dates = np.array([np.datetime64("2024-01-01"), np.datetime64("2024-01-02")])
    prices = np.array([100.0, 110.0], dtype=float)
    positions = np.array([1.0, 1.0], dtype=float)
    day_map = {0: np.array([[100.0, 100.0]]), 1: np.array([[120.0, 108.0]])}
    costs = dict(COSTS); costs["stop_loss"] = 0.50; costs["take_profit"] = 0.0
    eq, _ = run_coin_backtest_intrabar(
        dates=dates, prices=prices, positions=positions, intraday=day_map,
        initial_capital=10_000.0, trailing_stop=0.08, **costs,
    )
    # Trailing exit equity = peak*(1-0.08) = 1.20*0.92 = 1.104 → ~+10.4% minus fee.
    assert 10_000.0 * 1.08 < eq[-1] < 10_000.0 * 1.12


def test_group_intraday_by_day_maps_calendar_days():
    df = pd.DataFrame({
        "open_time": pd.to_datetime([
            "2024-01-01 00:00", "2024-01-01 12:00", "2024-01-02 00:00",
        ]),
        "high": [2.0, 3.0, 5.0], "low": [1.0, 1.5, 4.0],
        "open": [1, 2, 4], "close": [1.5, 2.5, 4.5], "volume": [1, 1, 1],
    })
    days = np.array([np.datetime64("2024-01-01"), np.datetime64("2024-01-02")])
    m = group_intraday_by_day(df, days)
    assert m[0].shape == (2, 2)  # two bars on Jan-01
    assert m[1].shape == (1, 2)  # one bar on Jan-02
    assert m[0][1, 0] == 3.0     # bar1 high
```

> Note: the `if False else` clause in the equivalence test is only to keep a single `run_coin_backtest` call after dropping a draft branch — simplify it to a plain call when implementing:
> `eq_daily, _ = run_coin_backtest(dates=dates, prices=prices, positions=positions, initial_capital=10_000.0, **COSTS)`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/strategies/test_intraday_fills.py -v`
Expected: FAIL — `cannot import name 'run_coin_backtest_intrabar' from 'scripts.intraday_fills'`.

- [ ] **Step 3: Implement `scripts/intraday_fills.py`**

```python
#!/usr/bin/env python
"""Intraday (1h) triple-barrier fill engine for the SL/TP sweep.

Overlays SL / TP / trailing barriers on the daily V2 equity loop, checked
intrabar by walking each day's 1h (high, low) bars in chronological order.
Barriers fire on equity-since-entry (matching baseline_strategy_v2's daily
stop semantics; leverage is already baked into the position size). When no
barrier touches within a day, the day reduces to the exact close-to-close
computation of run_coin_backtest (see tests/strategies/test_intraday_fills.py
::test_equivalence_when_no_intraday_excursion).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def group_intraday_by_day(
    intraday_df: pd.DataFrame, daily_dates: np.ndarray,
) -> dict[int, np.ndarray]:
    """Map daily index i → ndarray of (high, low) 1h bars on that calendar day.

    daily_dates are UTC-naive midnight-normalized (as produced by
    _load_crypto_ohlcv + .dt.normalize()). intraday_df.open_time is UTC-naive.
    Days with no intraday bars map to an empty (0, 2) array.
    """
    df = intraday_df.copy()
    df["day"] = pd.to_datetime(df["open_time"]).dt.normalize()
    grouped = {d: g[["high", "low"]].to_numpy(dtype=float)
               for d, g in df.groupby("day", sort=False)}
    out: dict[int, np.ndarray] = {}
    for i, d in enumerate(daily_dates):
        key = pd.Timestamp(d).normalize()
        out[i] = grouped.get(key, np.empty((0, 2), dtype=float))
    return out


def _barrier_exit_equity(
    bars: np.ndarray, e0: float, p_prev: float, pos: float,
    entry_equity: float, peak_eq: float,
    stop_loss: float, take_profit: float, trailing_stop: float,
) -> tuple[float | None, float]:
    """Walk a day's (high, low) bars; return (exit_equity or None, updated_peak).

    exit_equity is None when no barrier fires that day. Priority within a bar:
    fixed SL > TP > trailing (most conservative wins ties).
    """
    if pos == 0.0 or p_prev <= 0.0 or bars.shape[0] == 0:
        return None, peak_eq

    def eq_at(price: float) -> float:
        return e0 * (1.0 + pos * (price - p_prev) / p_prev)

    for hi, lo in bars:
        adverse = lo if pos > 0 else hi
        favorable = hi if pos > 0 else lo
        eq_adv = eq_at(adverse)
        eq_fav = eq_at(favorable)

        # (1) fixed stop-loss
        if entry_equity > 0 and (entry_equity - eq_adv) / entry_equity >= stop_loss:
            return entry_equity * (1.0 - stop_loss), peak_eq
        # (2) take-profit
        if take_profit > 0 and entry_equity > 0 and \
                (eq_fav - entry_equity) / entry_equity >= take_profit:
            return entry_equity * (1.0 + take_profit), peak_eq
        # (3) trailing stop (peak updated by this bar's favorable extreme first)
        peak_eq = max(peak_eq, eq_fav)
        if trailing_stop > 0 and peak_eq > 0 and \
                (peak_eq - eq_adv) / peak_eq >= trailing_stop:
            return peak_eq * (1.0 - trailing_stop), peak_eq

    return None, peak_eq


def run_coin_backtest_intrabar(
    dates: np.ndarray,
    prices: np.ndarray,
    positions: np.ndarray,
    intraday: dict[int, np.ndarray],
    initial_capital: float,
    fee_rate: float,
    slippage: float,
    spread: float,
    price_impact: float,
    funding_rate: float,
    stop_loss: float,
    max_portfolio_dd: float,
    take_profit: float = 0.0,
    trailing_stop: float = 0.0,
    funding_series: np.ndarray | None = None,
) -> tuple[list, dict]:
    """Intraday-fill twin of baseline_strategy_v2.run_coin_backtest.

    Identical cost model, funding, portfolio circuit breaker, metrics. The only
    difference: SL/TP/trailing are evaluated intrabar (per-day 1h bars in
    ``intraday[i]``) instead of on the day's close.
    """
    equity = [initial_capital]
    daily_returns: list[float] = []
    prev_pos = 0.0
    entry_equity = initial_capital
    peak_equity = initial_capital
    peak_eq_since_entry = initial_capital
    halted = False

    for i in range(1, len(dates)):
        p_prev = prices[i - 1]
        p_curr = prices[i]

        if np.isnan(p_prev) or np.isnan(p_curr) or p_prev == 0:
            daily_returns.append(0.0); equity.append(equity[-1]); continue
        if halted:
            daily_returns.append(0.0); equity.append(equity[-1]); prev_pos = 0.0; continue

        target_pos = positions[i]
        trade_notional = abs(target_pos - prev_pos)

        # entry_equity reset on open or close, identical to the daily engine.
        if target_pos != prev_pos and target_pos != 0:
            entry_equity = equity[-1]
            peak_eq_since_entry = equity[-1]
        if target_pos == 0 and prev_pos != 0:
            entry_equity = equity[-1]

        e0 = equity[-1]
        bars = intraday.get(i, np.empty((0, 2), dtype=float))
        exit_eq, peak_eq_since_entry = _barrier_exit_equity(
            bars, e0=e0, p_prev=p_prev, pos=target_pos,
            entry_equity=entry_equity, peak_eq=peak_eq_since_entry,
            stop_loss=stop_loss, take_profit=take_profit, trailing_stop=trailing_stop,
        )

        # Costs (same components as the daily engine).
        fee_cost = (2 * fee_rate + slippage + 2 * spread) * trade_notional
        impact_cost = price_impact * trade_notional * trade_notional
        if funding_series is None:
            holding_cost = funding_rate * abs(target_pos)
        else:
            holding_cost = funding_series[i] * target_pos

        if exit_eq is not None:
            # Barrier filled intrabar: cap the day's gross return at the barrier,
            # add a closing-trade fee on the flattened notional.
            gross_ret = exit_eq / e0 - 1.0
            close_fee = (2 * fee_rate + slippage + 2 * spread) * abs(target_pos)
            net_ret = gross_ret - (fee_cost + impact_cost + holding_cost + close_fee)
            new_equity = e0 * (1 + net_ret)
            filled_pos = 0.0  # flat for the rest of the day
        else:
            price_return = (p_curr - p_prev) / p_prev
            gross_ret = target_pos * price_return
            net_ret = gross_ret - (fee_cost + impact_cost + holding_cost)
            new_equity = e0 * (1 + net_ret)
            filled_pos = target_pos
            # track favorable peak from the day's close move too
            peak_eq_since_entry = max(peak_eq_since_entry, new_equity)

        daily_returns.append(net_ret)
        equity.append(new_equity)
        prev_pos = filled_pos

        peak_equity = max(peak_equity, new_equity)
        dd_from_peak = (peak_equity - new_equity) / peak_equity if peak_equity > 0 else 0
        if dd_from_peak >= max_portfolio_dd:
            halted = True

    # ── Metrics (identical formulas to run_coin_backtest) ──
    returns = np.array(daily_returns)
    total_return = (equity[-1] - initial_capital) / initial_capital
    n_days = len(returns)
    ann_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0
    daily_rf = (1 + 0.045) ** (1 / 252) - 1
    traded_mask = np.abs(np.array([positions[i] for i in range(1, len(dates))])) > 1e-9
    traded_returns = returns[traded_mask]
    if len(traded_returns) > 1:
        excess = traded_returns - daily_rf
        std_ex = np.std(excess, ddof=1)
        sharpe = float(np.mean(excess) / std_ex * np.sqrt(252)) if std_ex > 0 else 0
    else:
        sharpe = 0
    eq = np.array(equity)
    running_max = np.maximum.accumulate(eq)
    dd = np.where(running_max > 0, (running_max - eq) / running_max, 0)
    max_dd = float(np.max(dd))
    n_trades = int(np.sum(np.abs(np.diff(positions)) > 1e-9))
    wins = int(np.sum(traded_returns > 0))
    win_rate = wins / len(traded_returns) if len(traded_returns) > 0 else 0
    gross_profit = float(np.sum(traded_returns[traded_returns > 0]))
    gross_loss = float(np.abs(np.sum(traded_returns[traded_returns < 0])))
    pf = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0)
    metrics = {
        "total_return": total_return, "annualized_return": ann_return,
        "sharpe_ratio": sharpe, "max_drawdown": max_dd, "win_rate": win_rate,
        "n_trades": n_trades, "profit_factor": pf, "halted": halted,
    }
    return equity, metrics
```

- [ ] **Step 4: Run tests to verify they pass (remember to simplify the `if False` line per the note in Step 1)**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/strategies/test_intraday_fills.py -v`
Expected: PASS (6 passed). The equivalence test is the load-bearing one — if it fails, the cost/close-to-close path diverges from the daily engine and must be reconciled before proceeding.

- [ ] **Step 5: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/intraday_fills.py tests/strategies/test_intraday_fills.py
git commit -m "feat(backtest): intraday triple-barrier (SL/TP/trailing) fill engine"
```

---

## Task 4: Intraday SL×TP+trailing sweep + daily-vs-intraday bias cross-check

**Files:**
- Create: `scripts/intraday_sltp_sweep.py`
- Test: covered by the smoke run (Step 3) + the bias cross-check assertion (Step 4).

Clone the structure of `scripts/v5_mix_sltp_sweep.py` (the `_load_coin_data`, position caching, portfolio = `df.mean(axis=1)`, `_metrics`, `summary.json` patterns) but: (a) EE fixed off (`EE = 1.0`, single value — §29 settled it); (b) inner sweep is SL × TP × trailing; (c) `_engine_returns` calls `run_coin_backtest_intrabar` with the per-coin intraday day-map; (d) coins = `CORE_COINS` (4-coin). Also emit `bias.json`: the 3% baseline cell run on BOTH the daily engine and the intrabar engine, to quantify the look-ahead bias as the SR/return/DD delta.

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python
"""Intraday triple-barrier SL/TP+trailing sweep for the 4-coin V5 MIX.

Refined SL × TP × trailing grid (EE fixed off — §29 settled that early-exit
deteriorates), evaluated on the intraday-fill engine (scripts/intraday_fills).
Also emits bias.json: the canonical 3% cell on the daily engine vs the intrabar
engine, quantifying §29's close-to-close look-ahead bias.

Outputs to data/intraday_sltp_sweep/:
  results.csv  — one row per (sl, tp, trail) × scope (portfolio + 4 coins)
  summary.json — grid + baseline cell + best cell + git SHA
  bias.json    — daily-vs-intrabar deltas for the 3% baseline cell

Usage:
    python scripts/intraday_sltp_sweep.py --start 2021-11-07 --end 2026-04-15
"""
from __future__ import annotations

import argparse
import json
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
    COSTS, CORE_COINS, DEFAULT_ROUTING, _load_preds, _v2_positions,
)
from scripts.intraday_fills import (  # noqa: E402
    group_intraday_by_day, run_coin_backtest_intrabar,
)
from scripts.v5_mix_sltp_sweep import _metrics  # noqa: E402  (reuse identical metrics)
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402

EE_OFF = 1.0  # §29: early-exit disabled dominates; fixed off here.
SL_GRID = [0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.07, 0.10]   # 0.0 = disabled
TP_GRID = [0.0, 0.02, 0.03, 0.05, 0.08, 0.12]               # 0.0 = disabled
TRAIL_GRID = [0.0, 0.03, 0.05, 0.08]                        # 0.0 = disabled
INTRADAY_DIR = PROJECT_ROOT / "data" / "intraday_1h"

SMOKE_SL = [0.0, 0.03]
SMOKE_TP = [0.0, 0.05]
SMOKE_TRAIL = [0.0]


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT).decode().strip()
    except Exception:
        return "unknown"


def _load_coin_data(coin: str, pred_dir: Path, start: str, end: str) -> pd.DataFrame:
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


def _load_intraday_map(coin: str, daily_dates: np.ndarray) -> dict:
    path = INTRADAY_DIR / f"{coin}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing — run scripts/fetch_intraday_1h.py first")
    return group_intraday_by_day(pd.read_parquet(path), daily_dates)


def _intra_returns(merged, intraday_map, positions, sl, tp, trail) -> pd.Series:
    costs = dict(COSTS); costs["stop_loss"] = sl; costs["take_profit"] = tp
    equity, _m = run_coin_backtest_intrabar(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=positions, intraday=intraday_map, initial_capital=10_000.0,
        trailing_stop=trail, **costs,
    )
    eq = np.asarray(equity, dtype=float)
    return pd.Series(eq[1:] / eq[:-1] - 1.0, index=pd.to_datetime(merged["date"].values[1:]))


def _daily_returns(merged, positions, sl, tp) -> pd.Series:
    costs = dict(COSTS); costs["stop_loss"] = sl; costs["take_profit"] = tp
    equity, _m = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=positions, initial_capital=10_000.0, **costs,
    )
    eq = np.asarray(equity, dtype=float)
    return pd.Series(eq[1:] / eq[:-1] - 1.0, index=pd.to_datetime(merged["date"].values[1:]))


def run_sweep(sl_grid, tp_grid, trail_grid, start, end, kelly_fraction, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    coin_data, intraday_maps, positions = {}, {}, {}
    for coin in CORE_COINS:
        merged = _load_coin_data(coin, PROJECT_ROOT / DEFAULT_ROUTING[coin], start, end)
        coin_data[coin] = merged
        intraday_maps[coin] = _load_intraday_map(coin, merged["date"].values)
        positions[coin] = _v2_positions(merged, kelly_fraction=kelly_fraction, early_exit_loss=EE_OFF)
    print(f"  Loaded {len(coin_data)} coins + intraday in {time.time()-t0:.1f}s")

    rows = []
    n_cells = len(sl_grid) * len(tp_grid) * len(trail_grid)
    cell_i = 0
    baseline_sr = None
    for sl in sl_grid:
        for tp in tp_grid:
            for trail in trail_grid:
                cell_i += 1
                coin_rets = {c: _intra_returns(coin_data[c], intraday_maps[c], positions[c], sl, tp, trail)
                             for c in CORE_COINS}
                df = pd.DataFrame(coin_rets).dropna()
                pm = _metrics(df.mean(axis=1).values)
                rows.append(dict(sl=sl, tp=tp, trail=trail, scope="portfolio", **pm))
                for c, r in coin_rets.items():
                    rows.append(dict(sl=sl, tp=tp, trail=trail, scope=c, **_metrics(r.values)))
                if sl == COSTS["stop_loss"] and tp == 0.0 and trail == 0.0:
                    baseline_sr = pm["sharpe"]
                if cell_i % 10 == 0 or cell_i == n_cells:
                    el = time.time() - t0
                    print(f"  cell {cell_i}/{n_cells} SL={sl} TP={tp} TR={trail} "
                          f"SR={pm['sharpe']:+.2f} elapsed={el:.0f}s eta={el/cell_i*(n_cells-cell_i):.0f}s")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_dir / "results.csv", index=False)
    port = df_out[df_out["scope"] == "portfolio"].sort_values("sharpe", ascending=False)
    best = port.iloc[0]

    summary = dict(
        engine="intrabar_1h", coins=list(CORE_COINS),
        grid=dict(sl=sl_grid, tp=tp_grid, trail=trail_grid, ee="off"),
        window=dict(start=start, end=end), kelly_fraction=kelly_fraction,
        baseline_cell=dict(sl=COSTS["stop_loss"], tp=0.0, trail=0.0, portfolio_sharpe=baseline_sr),
        best_cell=dict(sl=float(best["sl"]), tp=float(best["tp"]), trail=float(best["trail"]),
                       portfolio_sharpe=float(best["sharpe"]),
                       total_return=float(best["total_return"]),
                       max_drawdown=float(best["max_drawdown"]), calmar=float(best["calmar"])),
        n_cells=n_cells, wall_clock_sec=time.time() - t0, git_sha=_git_sha(),
    )
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    # ── Bias cross-check: 3% cell on daily vs intrabar engine ──
    bias_coin = {}
    for c in CORE_COINS:
        d = _daily_returns(coin_data[c], positions[c], COSTS["stop_loss"], 0.0)
        ii = _intra_returns(coin_data[c], intraday_maps[c], positions[c], COSTS["stop_loss"], 0.0, 0.0)
        bias_coin[c] = dict(daily=_metrics(d.values), intrabar=_metrics(ii.values))
    d_port = pd.DataFrame({c: _daily_returns(coin_data[c], positions[c], COSTS["stop_loss"], 0.0) for c in CORE_COINS}).dropna().mean(axis=1)
    i_port = pd.DataFrame({c: _intra_returns(coin_data[c], intraday_maps[c], positions[c], COSTS["stop_loss"], 0.0, 0.0) for c in CORE_COINS}).dropna().mean(axis=1)
    bias = dict(
        cell=dict(sl=COSTS["stop_loss"], tp=0.0, trail=0.0),
        portfolio=dict(daily=_metrics(d_port.values), intrabar=_metrics(i_port.values)),
        per_coin=bias_coin,
    )
    bias["portfolio"]["sharpe_delta_intrabar_minus_daily"] = (
        bias["portfolio"]["intrabar"]["sharpe"] - bias["portfolio"]["daily"]["sharpe"])
    (out_dir / "bias.json").write_text(json.dumps(bias, indent=2, default=str))

    print(f"\n  Wrote {out_dir/'results.csv'} ({len(df_out)} rows), summary.json, bias.json")
    print(f"  Baseline 3% cell intrabar SR = {baseline_sr:+.3f}")
    print(f"  Best cell: SL={best['sl']} TP={best['tp']} TR={best['trail']} "
          f"SR={best['sharpe']:+.3f} DD={best['max_drawdown']:.1%}")
    print(f"  BIAS (intrabar - daily) portfolio SR delta = "
          f"{bias['portfolio']['sharpe_delta_intrabar_minus_daily']:+.3f}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", default="2021-11-07")
    p.add_argument("--end", default="2026-04-15")
    p.add_argument("--output-dir", default="data/intraday_sltp_sweep")
    p.add_argument("--kelly", type=float, default=0.5)
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    sl, tp, tr = (SMOKE_SL, SMOKE_TP, SMOKE_TRAIL) if args.smoke else (SL_GRID, TP_GRID, TRAIL_GRID)
    out_dir = PROJECT_ROOT / args.output_dir
    print(f"\n  Intraday SL/TP/trailing sweep — {args.start} → {args.end}")
    print(f"  grid: SL={len(sl)} TP={len(tp)} TRAIL={len(tr)} = {len(sl)*len(tp)*len(tr)} cells (EE off)\n")
    run_sweep(sl, tp, tr, args.start, args.end, args.kelly, out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Confirm `CORE_COINS` is importable from `baseline_v5_mix`**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -c "from scripts.baseline_v5_mix import CORE_COINS; print(CORE_COINS)"`
Expected: `('bitcoin', 'ethereum', 'binancecoin', 'solana')`.

- [ ] **Step 3: Smoke run (4 cells)**

Run: `cd /home/malecada/master_thesis/TradingAgents && python scripts/intraday_sltp_sweep.py --smoke --output-dir data/intraday_sltp_sweep_smoke`
Expected: completes; prints a baseline 3% intrabar SR and a `BIAS ... SR delta`; writes results.csv (10 rows = 2×2×1 portfolio+coin scopes... = 4 cells × 5 scopes = 20 rows), summary.json, bias.json.

- [ ] **Step 4: Full run (background — ~10-40 min, 192 cells × 4 coins intrabar)**

Run (background): `cd /home/malecada/master_thesis/TradingAgents && python scripts/intraday_sltp_sweep.py --start 2021-11-07 --end 2026-04-15 --output-dir data/intraday_sltp_sweep`
Expected: `summary.json` with `baseline_cell.portfolio_sharpe` ≈ +3.0–3.2 (intrabar 3% cell; expect it at/below the §29 daily +3.178 because realistic fills can only remove favorable look-ahead, not add it), a `best_cell`, and `bias.json` with the portfolio SR delta (the headline bias number). Sanity gate: `abs(bias.portfolio.daily.sharpe - 3.178) < 0.1` — the daily 3% cell must reproduce §29.

- [ ] **Step 5: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/intraday_sltp_sweep.py
git commit -m "feat(sweep): intraday SL/TP/trailing sweep + daily-vs-intrabar bias check"
```

---

## Task 5: Statistical layer — DSR over grid + paired bootstrap vs 3%

**Files:**
- Create: `scripts/intraday_sltp_stats.py`

Consumes `data/intraday_sltp_sweep/results.csv` (portfolio scope) plus re-runs the engine to recover per-cell daily return series (needed for bootstrap). Applies: (1) DSR to the best cell with `n_trials = n_cells`; (2) bootstrap 95% CI on the best cell's Sharpe; (3) paired bootstrap best-vs-3% (`diff_sharpe_ci`). Writes `stats.json` + a one-line verdict.

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python
"""Statistical adjudication of the intraday SL/TP/trailing sweep.

Reads the sweep's best cell, re-derives the best-cell and 3%-baseline daily
portfolio return series on the intrabar engine, then:
  1. DSR (deflated Sharpe) on the best cell with n_trials = #grid cells.
  2. Block-bootstrap 95% CI for the best cell's Sharpe.
  3. Paired block-bootstrap best-vs-3% (delta_sr_ci, p_delta_le_0).

Verdict: the best cell is a defensible improvement over the a-priori 3% only if
DSR >= 0.95 AND the paired delta_sr_ci excludes 0 (P(best>3%) high). Otherwise
3% is statistically indistinguishable and stays.

Usage:
    python scripts/intraday_sltp_stats.py --sweep-dir data/intraday_sltp_sweep
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_v5_mix import COSTS, CORE_COINS, DEFAULT_ROUTING, _v2_positions  # noqa: E402
from scripts.bootstrap_hybrid import diff_sharpe_ci  # noqa: E402
from scripts.bootstrap_sharpe import bootstrap_sharpe_ci  # noqa: E402
from scripts.intraday_fills import group_intraday_by_day, run_coin_backtest_intrabar  # noqa: E402
from scripts.intraday_sltp_sweep import _load_coin_data, EE_OFF, INTRADAY_DIR  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)


def _portfolio_returns(sl, tp, trail, start, end, kelly=0.5) -> np.ndarray:
    coin_rets = {}
    for c in CORE_COINS:
        merged = _load_coin_data(c, PROJECT_ROOT / DEFAULT_ROUTING[c], start, end)
        imap = group_intraday_by_day(pd.read_parquet(INTRADAY_DIR / f"{c}.parquet"), merged["date"].values)
        pos = _v2_positions(merged, kelly_fraction=kelly, early_exit_loss=EE_OFF)
        costs = dict(COSTS); costs["stop_loss"] = sl; costs["take_profit"] = tp
        eq, _ = run_coin_backtest_intrabar(
            dates=merged["date"].values, prices=merged["Close"].values, positions=pos,
            intraday=imap, initial_capital=10_000.0, trailing_stop=trail, **costs)
        eq = np.asarray(eq, dtype=float)
        coin_rets[c] = pd.Series(eq[1:] / eq[:-1] - 1.0, index=pd.to_datetime(merged["date"].values[1:]))
    return pd.DataFrame(coin_rets).dropna().mean(axis=1).values


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sweep-dir", default="data/intraday_sltp_sweep")
    p.add_argument("--start", default="2021-11-07")
    p.add_argument("--end", default="2026-04-15")
    p.add_argument("--n-iter", type=int, default=5000)
    p.add_argument("--block-size", type=int, default=21)
    args = p.parse_args()

    sdir = PROJECT_ROOT / args.sweep_dir
    summary = json.loads((sdir / "summary.json").read_text())
    best = summary["best_cell"]
    n_cells = summary["n_cells"]

    best_ret = _portfolio_returns(best["sl"], best["tp"], best["trail"], args.start, args.end)
    base_ret = _portfolio_returns(COSTS["stop_loss"], 0.0, 0.0, args.start, args.end)

    # 1. DSR on the best cell.
    var_sr = variance_of_sr(best_ret)
    se_sr = float(np.sqrt(var_sr))
    # observed SR in the SAME (non-annualized) units the DSR variance assumes:
    sr_obs_raw = float(np.mean(best_ret) / np.std(best_ret, ddof=1))
    sr_exp = expected_max_sharpe(n_trials=n_cells, var_sr=var_sr)
    dsr = deflated_sharpe_ratio(sr_obs_raw, sr_exp, se_sr)

    # 2. Bootstrap CI on best cell (annualized SR units).
    pt, lo, hi, _ = bootstrap_sharpe_ci(best_ret, n_iter=args.n_iter, block_size=args.block_size)

    # 3. Paired bootstrap best vs 3%.
    pair = diff_sharpe_ci(best_ret, base_ret, n_iter=args.n_iter, block_size=args.block_size)

    beats_3pct = (dsr >= 0.95) and (pair["delta_sr_ci"][0] > 0)
    out = dict(
        best_cell=best, n_trials=n_cells,
        dsr=dict(value=float(dsr), sr_obs_raw=sr_obs_raw,
                 expected_max_sr_null=float(sr_exp), se_sr=se_sr,
                 significant_at_95=bool(dsr >= 0.95)),
        best_bootstrap=dict(sharpe=pt, ci95=[lo, hi]),
        best_vs_3pct=pair,
        verdict=("Best cell is a statistically defensible improvement over 3%"
                 if beats_3pct else
                 "No cell beats the a-priori 3% after multiple-testing correction — keep 3%"),
    )
    (sdir / "stats.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it (after Task 4 full sweep completes)**

Run: `cd /home/malecada/master_thesis/TradingAgents && python scripts/intraday_sltp_stats.py --sweep-dir data/intraday_sltp_sweep`
Expected: prints + writes `stats.json` with `dsr.value` in [0,1], a bootstrap CI, `best_vs_3pct.delta_sr_ci` + `p_delta_le_0`, and a `verdict` string. Most likely (given §29's loose-stop cluster within <0.001 SR): `delta_sr_ci` straddles 0 and verdict = keep 3%.

- [ ] **Step 3: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/intraday_sltp_stats.py
git commit -m "feat(stats): DSR + paired-bootstrap adjudication of intraday SL/TP sweep"
```

---

## Task 6: IS/OOS validation (production-change arm)

**Files:**
- Modify: `scripts/intraday_sltp_stats.py` (add `--oos` mode)

The "Both" deliverable needs a true holdout for any production change. Pick the best cell on the in-sample window (start→`2025-04-15`), then report its Sharpe + paired bootstrap vs 3% on the held-out OOS window (`2025-04-15`→end). A cell only earns a production-change recommendation if it beats 3% in-sample (DSR ≥ 0.95) AND its OOS `delta_sr_ci` lower bound > 0.

- [ ] **Step 1: Add an `--oos` flag and split logic**

Add to `main()` argparse:
```python
    p.add_argument("--oos", action="store_true", help="IS-select / OOS-validate split mode")
    p.add_argument("--split", default="2025-04-15", help="IS/OOS boundary date")
```

Add this branch at the top of `main()` after parsing args (before the in-sample block), guarded by `if args.oos:`:
```python
    if args.oos:
        sdir = PROJECT_ROOT / args.sweep_dir
        # Re-run the sweep grid on the IS window only, pick best by IS Sharpe.
        from scripts.intraday_sltp_sweep import SL_GRID, TP_GRID, TRAIL_GRID
        best_is, best_sr = None, -1e9
        for sl in SL_GRID:
            for tp in TP_GRID:
                for trail in TRAIL_GRID:
                    r = _portfolio_returns(sl, tp, trail, args.start, args.split)
                    sr = float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(252)) if r.std() > 0 else 0.0
                    if sr > best_sr:
                        best_sr, best_is = sr, dict(sl=sl, tp=tp, trail=trail)
        # OOS validation of the IS-selected cell vs 3%.
        best_oos = _portfolio_returns(best_is["sl"], best_is["tp"], best_is["trail"], args.split, args.end)
        base_oos = _portfolio_returns(COSTS["stop_loss"], 0.0, 0.0, args.split, args.end)
        pair_oos = diff_sharpe_ci(best_oos, base_oos, n_iter=args.n_iter, block_size=args.block_size)
        ship = pair_oos["delta_sr_ci"][0] > 0
        out = dict(
            mode="is_oos", is_window=[args.start, args.split], oos_window=[args.split, args.end],
            is_selected_cell=best_is, is_sharpe=best_sr,
            oos_best_vs_3pct=pair_oos,
            recommendation=("SHIP: IS-selected cell beats 3% out-of-sample"
                            if ship else
                            "DO NOT SHIP: IS-selected cell does not beat 3% out-of-sample — keep 3%"),
        )
        (sdir / "stats_oos.json").write_text(json.dumps(out, indent=2, default=str))
        print(json.dumps(out, indent=2, default=str))
        return
```

- [ ] **Step 2: Run the OOS validation**

Run: `cd /home/malecada/master_thesis/TradingAgents && python scripts/intraday_sltp_stats.py --oos --sweep-dir data/intraday_sltp_sweep`
Expected: writes `stats_oos.json` with `is_selected_cell`, `oos_best_vs_3pct.delta_sr_ci`, and a `recommendation` (SHIP / DO NOT SHIP). This is the production decision artifact.

- [ ] **Step 3: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/intraday_sltp_stats.py
git commit -m "feat(stats): IS-select / OOS-validate mode for production SL/TP decision"
```

---

## Task 7: Figures + THESIS §31 write-up + memory

**Files:**
- Create: `scripts/intraday_sltp_report.py`
- Modify: `THESIS_FINDINGS.md` (append §31), `CLAUDE.md` (one-line pointer)

- [ ] **Step 1: Write the report script (heatmaps + bias figure)**

```python
#!/usr/bin/env python
"""Figures for the intraday SL/TP/trailing sweep (THESIS §31).

  F-31.1  SL×TP Sharpe heatmap at trail=0 (intrabar engine)
  F-31.2  SL×TP Sharpe heatmap at the best trail value
  F-31.3  Daily-vs-intrabar 3% baseline bias bar chart (per-coin + portfolio)

Usage:
    python scripts/intraday_sltp_report.py --sweep-dir data/intraday_sltp_sweep
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def _heatmap(df, trail, out_path):
    sub = df[(df["scope"] == "portfolio") & (df["trail"] == trail)]
    piv = sub.pivot(index="sl", columns="tp", values="sharpe")
    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(piv.values, aspect="auto", cmap="viridis", origin="lower")
    ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels([f"{c:.0%}" for c in piv.columns])
    ax.set_yticks(range(len(piv.index))); ax.set_yticklabels([f"{r:.0%}" for r in piv.index])
    ax.set_xlabel("Take-Profit"); ax.set_ylabel("Stop-Loss")
    ax.set_title(f"Portfolio Sharpe (intrabar 1h, trail={trail:.0%})")
    for i in range(len(piv.index)):
        for j in range(len(piv.columns)):
            ax.text(j, i, f"{piv.values[i, j]:.2f}", ha="center", va="center",
                    color="white", fontsize=7)
    fig.colorbar(im, ax=ax, label="Sharpe")
    fig.tight_layout(); fig.savefig(out_path, dpi=150); fig.savefig(str(out_path).replace(".png", ".svg"))
    plt.close(fig)


def _bias_chart(bias, out_path):
    coins = list(bias["per_coin"]) + ["portfolio"]
    daily = [bias["per_coin"][c]["daily"]["sharpe"] for c in bias["per_coin"]] + [bias["portfolio"]["daily"]["sharpe"]]
    intra = [bias["per_coin"][c]["intrabar"]["sharpe"] for c in bias["per_coin"]] + [bias["portfolio"]["intrabar"]["sharpe"]]
    x = np.arange(len(coins)); w = 0.38
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w / 2, daily, w, label="daily (close-to-close, §29)")
    ax.bar(x + w / 2, intra, w, label="intrabar (1h fills)")
    ax.set_xticks(x); ax.set_xticklabels(coins, rotation=20)
    ax.set_ylabel("Sharpe"); ax.set_title("3% stop: close-to-close look-ahead bias")
    ax.legend(); fig.tight_layout()
    fig.savefig(out_path, dpi=150); fig.savefig(str(out_path).replace(".png", ".svg")); plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sweep-dir", default="data/intraday_sltp_sweep")
    args = p.parse_args()
    sdir = Path(args.sweep_dir)
    fig_dir = sdir / "figures"; fig_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(sdir / "results.csv")
    summary = json.loads((sdir / "summary.json").read_text())
    bias = json.loads((sdir / "bias.json").read_text())
    _heatmap(df, 0.0, fig_dir / "F-31.1_sltp_heatmap_trail0.png")
    _heatmap(df, summary["best_cell"]["trail"], fig_dir / "F-31.2_sltp_heatmap_besttrail.png")
    _bias_chart(bias, fig_dir / "F-31.3_close_to_close_bias.png")
    print(f"  Wrote figures to {fig_dir}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate figures**

Run: `cd /home/malecada/master_thesis/TradingAgents && python scripts/intraday_sltp_report.py --sweep-dir data/intraday_sltp_sweep`
Expected: writes F-31.1/F-31.2/F-31.3 (PNG+SVG) under `data/intraday_sltp_sweep/figures/`.

- [ ] **Step 3: Write THESIS_FINDINGS.md §31**

Append a new `## 31. Intraday Triple-Barrier SL/TP Sweep` section. It MUST contain (fill numbers from `summary.json`, `bias.json`, `stats.json`, `stats_oos.json`):
- **Motivation:** §29 was close-to-close → intrabar look-ahead bias on the stop day. Method: triple-barrier (López de Prado) with SL/TP/trailing checked on 1h bars; barriers on equity-since-entry; only fill *timing* differs from §29.
- **Data:** 1h Binance klines, 4 core coins, 2021-11-07→2026-04-15, ~39k bars/coin. No LLM in the loop → no training-cutoff constraint; full window is fair.
- **Bias quantified:** report `bias.portfolio.sharpe_delta_intrabar_minus_daily` and per-coin deltas; state the §29 daily 3% cell reproduces at +3.178 (sanity gate).
- **Landscape:** the intrabar SL×TP×trailing best cell vs the 3% baseline; reference F-31.1/F-31.2.
- **Statistical verdict:** DSR value + `n_trials`, best-cell bootstrap CI, paired `best_vs_3pct.delta_sr_ci` + P(best>3%); state the `verdict` string.
- **OOS:** `is_selected_cell`, OOS `delta_sr_ci`, the SHIP/DO-NOT-SHIP `recommendation`.
- **Conclusion sentence:** whether 3% remains the defensible production choice (expected) or a specific cell earns a staged change.

- [ ] **Step 4: Add CLAUDE.md pointer**

Add one bullet under the §29-adjacent risk/sweep notes in `CLAUDE.md`:
```
- **Intraday SL/TP (§31)**: 1h triple-barrier sweep corrects §29's close-to-close fill bias. See THESIS_FINDINGS.md §31; reproduce via scripts/fetch_intraday_1h.py → scripts/intraday_sltp_sweep.py → scripts/intraday_sltp_stats.py [--oos].
```

- [ ] **Step 5: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/intraday_sltp_report.py THESIS_FINDINGS.md CLAUDE.md
git commit -m "docs(thesis): §31 intraday triple-barrier SL/TP sweep — figures + write-up"
```

- [ ] **Step 6: Update project memory**

Write a `project_intraday_sltp.md` memory (headline numbers + verdict) and add the MEMORY.md index line.

---

## Self-Review

**Spec coverage:**
- Intraday data (1h, fetched) → Tasks 1-2. ✓
- 4-coin V5 MIX scope → `CORE_COINS` everywhere. ✓
- Refined SL×TP + trailing, EE off → Task 4 grids. ✓
- Intrabar-accurate fills (removes §29 bias) → Task 3 engine + Task 4 bias.json. ✓
- "Both" deliverable: thesis rigor (DSR/CPCV/bootstrap) → Task 5; production change (OOS) → Task 6. ✓ (Note: CPCV is represented by the IS/OOS holdout + DSR; the existing `cpcv_v2.py` operates on V2 daily positions, not the intrabar engine, so a full CPCV port is out of scope — the IS/OOS split + DSR are the multiple-testing/overfit controls.)
- Figures + write-up → Task 7. ✓

**Placeholder scan:** No TBD/"handle edge cases"/"similar to" — engine, fetcher, sweep, stats all have full code. The §31 write-up (Task 7 Step 3) is a content spec (numbers come from generated JSON at execution time), not a code placeholder. ✓

**Type consistency:**
- `run_coin_backtest_intrabar(dates, prices, positions, intraday, initial_capital, fee_rate, slippage, spread, price_impact, funding_rate, stop_loss, max_portfolio_dd, take_profit=0.0, trailing_stop=0.0, funding_series=None)` — same call shape used in tests (Task 3), sweep (Task 4 `_intra_returns`), stats (Task 5 `_portfolio_returns`). ✓
- `group_intraday_by_day(intraday_df, daily_dates) -> dict[int, ndarray(n,2)]` — used in Tasks 3-5 identically. ✓
- `fetch_binance_klines_range(symbol, from_ms, to_ms, interval)` — Task 1 def, Task 2 caller. ✓
- DSR: `variance_of_sr(returns)`, `expected_max_sharpe(n_trials, var_sr)`, `deflated_sharpe_ratio(sr_obs, sr_exp, se_sr)` — match dsr.py exactly. ✓
- `diff_sharpe_ci(hybrid_ret, baseline_ret, n_iter, block_size, seed=7)` returns `delta_sr_ci`, `p_delta_le_0` — used in Tasks 5-6. ✓
- `_metrics(ndarray)` reused from `v5_mix_sltp_sweep` returns `sharpe,total_return,max_drawdown,calmar,win_rate,profit_factor,n_bars`. ✓

**Known approximation (documented, not a gap):** DSR's `variance_of_sr`/`expected_max_sr` work in per-period (non-annualized) SR units, so Task 5 feeds `sr_obs_raw` (un-annualized) consistently. The annualized SR is reported separately via the bootstrap CI. This matches how dsr.py was used in §12.

---

## Execution Risks / Notes
- **Intrabar 3% SR will likely be ≤ §29's +3.178**, not above: correct fills can only *remove* favorable close-to-close luck on stop days. If the intrabar baseline comes out materially *higher*, suspect a bug in the barrier direction/sign and re-check Task 3 tests before trusting the sweep.
- **Trailing is the genuinely new lever** §29 never tested; if any cell beats 3% it is most likely a loose SL + modest trailing combo.
- **1h vs same-bar double-touch** is resolved conservatively (SL-first within a bar). At 3%+ stop widths same-hour double-touches are rare; a 5m robustness re-fetch on BTC/ETH is a cheap optional follow-up if a winning cell hinges on tight stops.
