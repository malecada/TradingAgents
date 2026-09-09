# liq_fade_i1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pre-registered dev-gate test of intraday (1h) liquidation-cascade long-fade on a top-50 PIT universe, using a free Binance 1h kline proxy detector (spec: `docs/superpowers/specs/2026-07-28-liq-fade-intraday-design.md`).

**Architecture:** New pure-function module `tradingagents/xsect/liq_fade.py` (triggers → event weights → hourly P&L aggregated to daily), a 1h kline fetcher following `fetch_xsect_klines.py` patterns, and a dev runner `scripts/liq_fade_dev.py` that executes gating probes P0–P2 before any strategy P&L, then the 6-config grid + dual-family placebo + DSR + ledger.

**Tech Stack:** Python 3.13 (`.venv/bin/python`, uv-managed), pandas/numpy, pytest. Binance FAPI + data.binance.vision. No new dependencies.

## Global Constraints

- Registration key `liq_fade_i1`; gates.json entry MUST be committed before the first dev-grid run.
- Long-fade only. Grid: `thr ∈ {2.5, 3.5}` × `H ∈ {6, 24, 48}` hours. Nothing else searched.
- Rolling stats: window 2160 hourly bars, min_periods 1440, ddof=1, data ≤ t only.
- Sizing: 1/10 per active event, gross cap 1.0 (max 10 concurrent, arrival order).
- Costs 10 bps/side on |ΔW|; rf flat 4.5%/yr on full capital daily; funding EXCLUDED.
- SR on daily-aggregated (UTC) net returns, ×√365.
- Dev window 2021-01-01 → 2025-03-31. Holdout 2025-04-01 → 2026-07-01 SEALED.
- Probes P1/P2 are STOP gates: failure → NEGATIVE-at-probe, no grid run, holdout untouched.
- Branch `feature/xs-momentum`. Do not touch unrelated P5 WIP modifications present in the worktree (`scripts/parity_refetch_and_replay.py`, `tradingagents/agents/**`, `tradingagents/dataflows/coingecko_binance.py`, `uv.lock`) — stage files explicitly, never `git add -A`.
- All long-running fetches/runs: `nohup .venv/bin/python ... &` with idempotent caches (house resilience rule).

---

### Task 1: 1h kline fetcher

**Files:**
- Create: `scripts/fetch_xsect_klines_1h.py`
- Test: `tests/xsect/test_klines_1h_merge.py`

**Interfaces:**
- Produces: parquet per symbol at `data/xsect/klines_1h/{SYMBOL}.parquet`, UTC `DatetimeIndex` named `ts` (bar OPEN time), columns `open, high, low, close, volume, quote_volume, taker_buy_quote_volume` (float64), 1h frequency, plus `data/xsect/klines_1h_manifest.json` (`{symbol: {"first": iso, "last": iso, "rows": int}}`).
- Produces: pure function `merge_tail(existing: pd.DataFrame | None, new: pd.DataFrame) -> pd.DataFrame` (dedup on index, keep-last, sorted) importable from the script.

- [ ] **Step 1: Write the failing merge test**

```python
# tests/xsect/test_klines_1h_merge.py
import pandas as pd
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "fetch1h", Path(__file__).parents[2] / "scripts" / "fetch_xsect_klines_1h.py")
fetch1h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch1h)


def _df(hours, val):
    idx = pd.date_range("2024-01-01", periods=hours, freq="1h", tz="UTC", name="ts")
    return pd.DataFrame({c: float(val) for c in
        ["open", "high", "low", "close", "volume", "quote_volume",
         "taker_buy_quote_volume"]}, index=idx)


def test_merge_tail_dedups_keep_last_sorted():
    old = _df(48, 1.0)
    new = _df(24, 2.0).shift(freq="36h")  # overlaps last 12 bars of old
    out = fetch1h.merge_tail(old, new)
    assert out.index.is_monotonic_increasing and out.index.is_unique
    assert len(out) == 60
    assert out.loc["2024-01-02 12:00", "close"].item() == 2.0  # new wins overlap


def test_merge_tail_none_existing():
    new = _df(5, 3.0)
    assert fetch1h.merge_tail(None, new).equals(new)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/xsect/test_klines_1h_merge.py -v`
Expected: FAIL (file `scripts/fetch_xsect_klines_1h.py` not found).

- [ ] **Step 3: Implement the fetcher**

Copy the structure of `scripts/fetch_xsect_klines.py` (read it first) with these changes:

```python
# scripts/fetch_xsect_klines_1h.py  (key parts; mirror existing script's style)
INTERVAL = "1h"
OUT_DIR = PROJECT_ROOT / "data" / "xsect" / "klines_1h"
MANIFEST = PROJECT_ROOT / "data" / "xsect" / "klines_1h_manifest.json"
VISION_URL = ("https://data.binance.vision/data/futures/um/monthly/klines/"
              "{sym}/1h/{sym}-1h-{ym}.zip")
FAPI = "https://fapi.binance.com/fapi/v1/klines"

def merge_tail(existing, new):
    if existing is None or existing.empty:
        return new.sort_index()
    out = pd.concat([existing, new])
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out

def fetch_symbol(sym: str, start: str) -> pd.DataFrame:
    # 1) Vision monthly zips from `start` month to last full month
    #    (skip months already fully present in existing parquet)
    # 2) FAPI paginated tail (limit=1500) from last Vision bar to now
    # columns per Binance kline spec: open_time, open, high, low, close,
    # volume, close_time, quote_volume, n_trades, taker_buy_base,
    # taker_buy_quote, ignore  -> keep the 7 spec columns, ts = open_time UTC
    ...

def main():
    # args: --symbols-file (one symbol per line) --start 2020-06-01
    # per symbol: load existing parquet if any, fetch missing range only
    # (tail-append; canonical filename, NO date in filename), write parquet
    # + update manifest after each symbol (crash-resumable)
    ...
```

Requests: `timeout=30`, 3 retries with sleep 2s, sleep 0.15s between FAPI calls (weight safety; house IP-ban lesson). Vision 404 for a month = symbol not listed yet → skip month silently.

- [ ] **Step 4: Run merge tests**

Run: `.venv/bin/python -m pytest tests/xsect/test_klines_1h_merge.py -v` — Expected: PASS.

- [ ] **Step 5: Smoke fetch one symbol**

Run: `printf 'BTCUSDT\n' > /tmp/sym1.txt && .venv/bin/python scripts/fetch_xsect_klines_1h.py --symbols-file /tmp/sym1.txt --start 2026-06-01`
Expected: `data/xsect/klines_1h/BTCUSDT.parquet` exists; spot-check in python: index tz-aware UTC hourly, 7 columns, last bar within 2h of now. Re-run the same command: completes fast, row count unchanged or +tail only (idempotent).

- [ ] **Step 6: Commit**

```bash
git add scripts/fetch_xsect_klines_1h.py tests/xsect/test_klines_1h_merge.py
git commit -m "feat(liq-fade): 1h kline fetcher — Vision monthly + FAPI tail, idempotent"
```

---

### Task 2: Monthly top-50 PIT universe

**Files:**
- Create: `tradingagents/xsect/liq_fade.py` (first function)
- Test: `tests/xsect/test_liq_fade_universe.py`

**Interfaces:**
- Consumes: daily kline dict from `tradingagents.xsect.universe.load_klines(Path("data/xsect/klines"))` — `{symbol: DataFrame}` with `quote_volume` column, UTC daily index.
- Produces: `monthly_top_n(daily: dict[str, pd.DataFrame], start: str, end: str, n: int = 50, lookback: int = 30, min_age_days: int = 60) -> dict[pd.Timestamp, list[str]]` — key = month start (UTC), value = selected symbols. Selection at month start `m` uses only data strictly before `m`: trailing `lookback`-day median `quote_volume`; symbol eligible if it has ≥ `min_age_days` rows before `m` and a row on the last day before `m`.

- [ ] **Step 1: Write failing tests**

```python
# tests/xsect/test_liq_fade_universe.py
import pandas as pd
from tradingagents.xsect.liq_fade import monthly_top_n


def _daily(sym_vol: dict, start="2020-10-01", days=200):
    idx = pd.date_range(start, periods=days, freq="1D", tz="UTC", name="ts")
    return {s: pd.DataFrame({"close": 1.0, "quote_volume": float(v)}, index=idx)
            for s, v in sym_vol.items()}


def test_ranks_by_trailing_median_dollar_volume():
    d = _daily({"AAA": 100, "BBB": 300, "CCC": 200})
    sel = monthly_top_n(d, "2021-01-01", "2021-02-28", n=2)
    first = sel[pd.Timestamp("2021-01-01", tz="UTC")]
    assert first == ["BBB", "CCC"]


def test_young_symbol_excluded_until_min_age():
    d = _daily({"OLD": 100})
    young = _daily({"NEW": 999}, start="2020-12-20", days=100)
    d.update(young)  # NEW has <60d history before 2021-01-01
    sel = monthly_top_n(d, "2021-01-01", "2021-03-31", n=2)
    assert "NEW" not in sel[pd.Timestamp("2021-01-01", tz="UTC")]
    assert "NEW" in sel[pd.Timestamp("2021-03-01", tz="UTC")]


def test_no_lookahead_selection_ignores_future_volume():
    d = _daily({"AAA": 100, "BBB": 50})
    # BBB volume explodes AFTER Jan-1; Jan selection must not see it
    d["BBB"].loc["2021-01-05":, "quote_volume"] = 10_000.0
    sel = monthly_top_n(d, "2021-01-01", "2021-01-31", n=1)
    assert sel[pd.Timestamp("2021-01-01", tz="UTC")] == ["AAA"]
```

- [ ] **Step 2: Run to verify failure** — `.venv/bin/python -m pytest tests/xsect/test_liq_fade_universe.py -v` → FAIL (no module attr).

- [ ] **Step 3: Implement**

```python
# tradingagents/xsect/liq_fade.py
"""liq_fade_i1 — intraday liquidation-cascade long-fade (spec 2026-07-28)."""
import numpy as np
import pandas as pd


def monthly_top_n(daily, start, end, n=50, lookback=30, min_age_days=60):
    months = pd.date_range(pd.Timestamp(start, tz="UTC"),
                           pd.Timestamp(end, tz="UTC"), freq="MS")
    out = {}
    for m in months:
        scores = {}
        for sym, df in daily.items():
            hist = df.loc[df.index < m]
            if len(hist) < min_age_days or (m - hist.index[-1]).days > 3:
                continue
            scores[sym] = hist["quote_volume"].iloc[-lookback:].median()
        ranked = sorted(scores, key=lambda s: -scores[s])[:n]
        out[m] = ranked
    return out
```

- [ ] **Step 4: Run tests** — same command → PASS.
- [ ] **Step 5: Commit**

```bash
git add tradingagents/xsect/liq_fade.py tests/xsect/test_liq_fade_universe.py
git commit -m "feat(liq-fade): monthly top-N PIT universe selection"
```

---

### Task 3: Cascade trigger signal

**Files:**
- Modify: `tradingagents/xsect/liq_fade.py`
- Test: `tests/xsect/test_liq_fade_triggers.py`

**Interfaces:**
- Produces: `cascade_triggers(close: pd.DataFrame, qvol: pd.DataFrame, thr: float, window: int = 2160, min_periods: int = 1440) -> pd.DataFrame` — bool, same shape/index as inputs (hourly, symbols as columns). True at bar t iff `z_ret_t ≤ −thr` AND `z_vol_t ≥ thr`, where `z_ret` is the rolling z of 1h log returns and `z_vol` the rolling z of `log1p(qvol)`, both windows inclusive of t, ddof=1.

- [ ] **Step 1: Write failing tests**

```python
# tests/xsect/test_liq_fade_triggers.py
import numpy as np
import pandas as pd
from tradingagents.xsect.liq_fade import cascade_triggers


def _panel(hours=3000, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2021-01-01", periods=hours, freq="1h", tz="UTC")
    ret = rng.normal(0, 0.005, hours)
    close = pd.DataFrame({"AAA": 100 * np.exp(np.cumsum(ret))}, index=idx)
    qvol = pd.DataFrame({"AAA": rng.lognormal(10, 0.3, hours)}, index=idx)
    return close, qvol


def test_crash_with_volume_spike_triggers():
    close, qvol = _panel()
    t = 2500
    close.iloc[t:, 0] *= 0.90          # -10% crash bar at t
    qvol.iloc[t, 0] *= 50              # volume spike at t
    trig = cascade_triggers(close, qvol, thr=2.5)
    assert bool(trig.iloc[t, 0])
    assert trig.iloc[t - 100 : t, 0].sum() == 0


def test_crash_without_volume_does_not_trigger():
    close, qvol = _panel()
    close.iloc[2500:, 0] *= 0.90       # crash, but volume normal
    trig = cascade_triggers(close, qvol, thr=2.5)
    assert not bool(trig.iloc[2500, 0])


def test_causal_future_edit_does_not_change_past():
    close, qvol = _panel()
    close.iloc[2500:, 0] *= 0.90
    qvol.iloc[2500, 0] *= 50
    a = cascade_triggers(close, qvol, thr=2.5).iloc[:2501]
    close.iloc[2700:, 0] *= 0.5        # edit strictly-future data
    qvol.iloc[2700:, 0] *= 100
    b = cascade_triggers(close, qvol, thr=2.5).iloc[:2501]
    assert a.equals(b)


def test_warmup_no_triggers_before_min_periods():
    close, qvol = _panel()
    close.iloc[100:, 0] *= 0.80
    qvol.iloc[100, 0] *= 100
    trig = cascade_triggers(close, qvol, thr=2.5)
    assert trig.iloc[:1440].to_numpy().sum() == 0
```

- [ ] **Step 2: Run to verify failure** → FAIL.
- [ ] **Step 3: Implement**

```python
def _roll_z(x: pd.DataFrame, window: int, min_periods: int) -> pd.DataFrame:
    mu = x.rolling(window, min_periods=min_periods).mean()
    sd = x.rolling(window, min_periods=min_periods).std(ddof=1)
    return (x - mu) / sd


def cascade_triggers(close, qvol, thr, window=2160, min_periods=1440):
    r = np.log(close).diff()
    z_ret = _roll_z(r, window, min_periods)
    z_vol = _roll_z(np.log1p(qvol), window, min_periods)
    return (z_ret <= -thr) & (z_vol >= thr)
```

- [ ] **Step 4: Run tests** → PASS.
- [ ] **Step 5: Commit** — `git add ... && git commit -m "feat(liq-fade): 1h cascade trigger (return-z x volume-z proxy)"`

---

### Task 4: Event weights (hold H, retrigger reset, gross cap)

**Files:**
- Modify: `tradingagents/xsect/liq_fade.py`
- Test: `tests/xsect/test_liq_fade_weights.py`

**Interfaces:**
- Produces: `event_weights_hourly(trig: pd.DataFrame, H: int, w_per: float = 0.1, cap: float = 1.0) -> pd.DataFrame` — float weights, W.iloc[i] is the position held DURING bar i (decided from triggers ≤ bar i−1). A trigger at bar t opens weight `w_per` for bars t+1…t+H; retrigger during the hold resets the timer; a new event that would push `W.sum(axis=1)` above `cap` at its entry bar is ignored entirely (arrival order = column order for same-bar ties).

- [ ] **Step 1: Write failing tests**

```python
# tests/xsect/test_liq_fade_weights.py
import pandas as pd
from tradingagents.xsect.liq_fade import event_weights_hourly


def _trig(events: dict, hours=50, syms=("A", "B")):
    idx = pd.date_range("2021-01-01", periods=hours, freq="1h", tz="UTC")
    t = pd.DataFrame(False, index=idx, columns=list(syms))
    for s, bars in events.items():
        t.iloc[bars, t.columns.get_loc(s)] = True
    return t


def test_hold_window_t_plus_1_to_t_plus_H():
    W = event_weights_hourly(_trig({"A": [10]}), H=3)
    col = W["A"].to_numpy()
    assert col[10] == 0.0                       # trigger bar itself: flat
    assert list(col[11:14]) == [0.1, 0.1, 0.1]  # t+1..t+3
    assert col[14] == 0.0


def test_retrigger_resets_timer():
    W = event_weights_hourly(_trig({"A": [10, 12]}), H=3)
    assert list(W["A"].to_numpy()[11:16]) == [0.1, 0.1, 0.1, 0.1, 0.1]  # 11..15
    assert W["A"].iloc[16] == 0.0


def test_gross_cap_ignores_excess_event():
    trig = _trig({s: [10] for s in "ABCDEFGHIJK"}, syms=tuple("ABCDEFGHIJK"))
    W = event_weights_hourly(trig, H=3)
    assert W.iloc[11].sum() == 1.0              # 10 events × 0.1, 11th ignored
    assert W["K"].iloc[11] == 0.0               # last column dropped


def test_no_shorts_and_no_negative_weights():
    W = event_weights_hourly(_trig({"A": [10]}), H=3)
    assert (W.to_numpy() >= 0).all()
```

- [ ] **Step 2: Run to verify failure** → FAIL.
- [ ] **Step 3: Implement**

Loop over bars (numpy int state per symbol: `bars_left`), single pass:

```python
def event_weights_hourly(trig, H, w_per=0.1, cap=1.0):
    T = trig.to_numpy()
    n, k = T.shape
    left = np.zeros(k, dtype=np.int64)
    W = np.zeros((n, k))
    max_slots = int(round(cap / w_per))
    for i in range(n):
        if i > 0:
            # events triggered at bar i-1 activate for bar i
            for j in range(k):
                if T[i - 1, j]:
                    active = int((left > 0).sum())
                    if left[j] > 0 or active < max_slots:
                        left[j] = H          # open or reset timer
        W[i] = np.where(left > 0, w_per, 0.0)
        left = np.maximum(left - 1, 0)
    return pd.DataFrame(W, index=trig.index, columns=trig.columns)
```

- [ ] **Step 4: Run tests** → PASS. If the cap test fails on ordering, fix so already-held symbols always reset regardless of cap (they occupy their own slot).
- [ ] **Step 5: Commit** — `git commit -m "feat(liq-fade): event weights — H-bar hold, retrigger reset, gross cap"`

---

### Task 5: Hourly P&L → daily net returns

**Files:**
- Modify: `tradingagents/xsect/liq_fade.py`
- Test: `tests/xsect/test_liq_fade_pnl.py`

**Interfaces:**
- Consumes: `W` from `event_weights_hourly`, hourly simple returns `R = close.pct_change()` (same shape).
- Produces: `run_hourly_portfolio(W: pd.DataFrame, R: pd.DataFrame, cost_bps: float = 10.0, rf_annual: float = 0.045) -> pd.Series` — daily (UTC calendar-day) NET simple returns: hourly gross = `(W * R).sum(axis=1)` minus `cost_bps/1e4 * |W − W.shift()|.sum(axis=1)`, summed per day, minus `rf_daily = 1.045**(1/365) − 1` on EVERY calendar day in the index range (full-capital convention). Missing R for a held symbol contributes 0.
- Produces: `sharpe_daily(net: pd.Series) -> float` — `mean/std(ddof=1) * sqrt(365)`, 0.0 if std is 0 (house zero-variance convention).

- [ ] **Step 1: Write failing tests**

```python
# tests/xsect/test_liq_fade_pnl.py
import numpy as np
import pandas as pd
from tradingagents.xsect.liq_fade import run_hourly_portfolio, sharpe_daily

RF_D = 1.045 ** (1 / 365) - 1


def test_hand_computed_single_event():
    idx = pd.date_range("2021-01-01", periods=48, freq="1h", tz="UTC")
    W = pd.DataFrame(0.0, index=idx, columns=["A"])
    W.iloc[10:13, 0] = 0.1                     # 3-bar hold
    R = pd.DataFrame(0.01, index=idx, columns=["A"])
    net = run_hourly_portfolio(W, R, cost_bps=10.0)
    # gross: 3 bars * 0.1 * 0.01 = 0.003 ; costs: |dW| = 0.1 + 0.1 -> 2e-4
    # all inside day 1; rf on both calendar days
    assert np.isclose(net.iloc[0], 0.003 - 2e-4 - RF_D)
    assert np.isclose(net.iloc[1], -RF_D)


def test_missing_return_contributes_zero():
    idx = pd.date_range("2021-01-01", periods=24, freq="1h", tz="UTC")
    W = pd.DataFrame(0.1, index=idx, columns=["A"])
    R = pd.DataFrame(np.nan, index=idx, columns=["A"])
    net = run_hourly_portfolio(W, R, cost_bps=0.0)
    assert np.isclose(net.iloc[0], -RF_D)


def test_sharpe_zero_variance_is_zero():
    s = pd.Series(0.0, index=pd.date_range("2021-01-01", periods=10, tz="UTC"))
    assert sharpe_daily(s) == 0.0
```

- [ ] **Step 2: Run to verify failure** → FAIL.
- [ ] **Step 3: Implement**

```python
def run_hourly_portfolio(W, R, cost_bps=10.0, rf_annual=0.045):
    gross = (W * R.fillna(0.0)).sum(axis=1)
    turn = (W - W.shift().fillna(0.0)).abs().sum(axis=1)
    hourly = gross - cost_bps / 1e4 * turn
    daily = hourly.groupby(hourly.index.tz_convert("UTC").normalize()).sum()
    daily = daily.asfreq("D", fill_value=0.0)      # rf accrues on gap days too
    rf_d = (1 + rf_annual) ** (1 / 365) - 1
    return daily - rf_d


def sharpe_daily(net):
    sd = net.std(ddof=1)
    if not np.isfinite(sd) or sd == 0:
        return 0.0
    return float(net.mean() / sd * np.sqrt(365))
```

- [ ] **Step 4: Run tests** → PASS. Also run the full module suite: `.venv/bin/python -m pytest tests/xsect/ -v` → all green.
- [ ] **Step 5: Commit** — `git commit -m "feat(liq-fade): hourly P&L with costs + rf, daily aggregation, SR"`

---

### Task 6: gates.json registration + ledger note

**Files:**
- Modify: `data/rebuild/gates.json` (add key `liq_fade_i1`)

**Interfaces:**
- Consumes: existing gates.json dict format (see sibling key `liq_mr_t1`).
- Produces: committed registration BEFORE any dev run (house rule).

- [ ] **Step 1: Add entry** (adapt wording, keep structure identical to `liq_mr_t1`):

```json
"liq_fade_i1": {
  "registered": "2026-07-28",
  "spec": "docs/superpowers/specs/2026-07-28-liq-fade-intraday-design.md",
  "dev_window": ["2021-01-01", "2025-03-31"],
  "holdout_window": ["2025-04-01", "2026-07-01"],
  "universe": "top-50 PIT monthly by trailing 30d median quote_volume from 799-symbol survivorship-safe daily store; min_age 60d; Binance UM 1h klines",
  "signal": "per symbol hourly: z_ret = rolling z of 1h log returns, z_vol = rolling z of log1p(quote_volume), window 2160 bars min_periods 1440 ddof=1 inclusive of t; trigger = z_ret <= -thr AND z_vol >= thr; LONG-FADE ONLY (short side pre-excluded per section-47 asymmetry)",
  "portfolio_rule": "trigger at bar t -> long 1/10 for bars t+1..t+H; retrigger resets timer; gross cap 1.0 (max 10 concurrent, arrival order); costs 10 bps per side on |dW|; rf_daily = 1.045^(1/365)-1 on full capital every calendar day; funding EXCLUDED; SR on daily-aggregated UTC net returns x sqrt(365)",
  "grid": { "thr": [2.5, 3.5], "H": [6, 24, 48] },
  "probes": {
    "P0": "1h bars open-stamped; daily aggregation of 1h closes reconciles with daily store (corr > 0.99 on overlapping returns, BTCUSDT)",
    "P1": "proxy triggers (thr=2.5) aggregated daily on 8 Coinglass coins must flag >= 4 of 5 benchmark cascade dates (2021-05-19, 2022-06-13, 2022-11-09, 2024-08-05, 2025-02-03); FAIL -> STOP",
    "P2": "mean cumulative GROSS forward return t+1..t+H over all dev triggers must exceed +25 bps in at least one grid cell; FAIL -> STOP (NEGATIVE-at-probe)"
  },
  "dev_select": {
    "net_sr_min": 1.0,
    "placebo": "dual-family (A: per-symbol circular shift of trigger series; B: count-matched uniform random trigger timestamps), 500 draws each, costs+rf re-applied, p = (1+#{placebo SR >= real SR})/(N+1), gate on WORSE p <= 0.05",
    "dsr_min": 0.9,
    "n_trials": "ledger-cumulative unique config_hash count at evaluation time (+6 from this grid)"
  },
  "one_shot": "holdout spent only if dev gate passes; stress row +10bps slippage reported not gated",
  "thesis_section": "48"
}
```

- [ ] **Step 2: Validate JSON** — `.venv/bin/python -c "import json; json.load(open('data/rebuild/gates.json')); print('ok')"` → `ok`.
- [ ] **Step 3: Commit** — `git add data/rebuild/gates.json && git commit -m "prereg(liq-fade-i1): gate registration — 6-config grid, probes P0-P2, sealed holdout"`

---

### Task 7: Universe resolution + bulk 1h fetch

**Files:**
- Create: `scripts/liq_fade_universe.py` (writes `data/xsect/liq_fade_universe.json` + symbol union list)

**Interfaces:**
- Consumes: `monthly_top_n` (Task 2), daily store `data/xsect/klines/`.
- Produces: `data/xsect/liq_fade_universe.json` — `{"YYYY-MM-01": ["BTCUSDT", ...], ...}` for 2020-11-01 → 2025-03-01 (membership needed from 60d before dev start for warmup context is NOT required — warmup uses each symbol's own 1h history; membership starts 2021-01); union symbol list at `data/xsect/liq_fade_symbols.txt`.

- [ ] **Step 1: Write the runner** (thin script, no unit test — it composes tested functions):

```python
# scripts/liq_fade_universe.py
import json
from pathlib import Path
from tradingagents.xsect.universe import load_klines
from tradingagents.xsect.liq_fade import monthly_top_n

ROOT = Path(__file__).parents[1]
daily = load_klines(ROOT / "data/xsect/klines")
sel = monthly_top_n(daily, "2021-01-01", "2025-03-31", n=50)
out = {str(k.date()): v for k, v in sel.items()}
(ROOT / "data/xsect/liq_fade_universe.json").write_text(json.dumps(out, indent=1))
union = sorted({s for v in sel.values() for s in v})
(ROOT / "data/xsect/liq_fade_symbols.txt").write_text("\n".join(union) + "\n")
print(f"months={len(out)} union={len(union)}")
```

- [ ] **Step 2: Run it** — `.venv/bin/python scripts/liq_fade_universe.py`. Expected: 51 months, union roughly 80–200 symbols. Sanity: BTCUSDT and ETHUSDT in every month.
- [ ] **Step 3: Launch bulk 1h fetch in background** (start 2020-06-01 to give ≥90d warmup before 2021-01 for early members):

```bash
nohup .venv/bin/python scripts/fetch_xsect_klines_1h.py \
  --symbols-file data/xsect/liq_fade_symbols.txt --start 2020-06-01 \
  > /tmp/liq_fade_fetch.log 2>&1 &
```

Monitor `tail /tmp/liq_fade_fetch.log`; expect minutes–low hours. On completion check manifest: every union symbol present, BTCUSDT first bar ≤ 2020-06-01, last bar ≥ 2025-04-15 (buffer past dev end; do NOT need holdout data yet). Disk check `du -sh data/xsect/klines_1h` — expect < 1G.

- [ ] **Step 4: Commit** — `git add scripts/liq_fade_universe.py data/xsect/liq_fade_universe.json data/xsect/liq_fade_symbols.txt && git commit -m "feat(liq-fade): universe resolution + 1h data fetched (data not committed)"` (parquets stay untracked like the daily store).

---

### Task 8: Dev runner — probes P0–P2 (STOP gates)

**Files:**
- Create: `scripts/liq_fade_dev.py` (probes section)
- Output: `data/rebuild/liq_fade/probes.json`, `data/rebuild/liq_fade/forensics.md` (appended)

**Interfaces:**
- Consumes: Tasks 2–5 functions; `data/xsect/klines_1h/`; universe json; daily Coinglass parquets `data/derivatives/{bitcoin,ethereum,bnb,solana,cardano,dogecoin,xrp,tron}.parquet` (col `liq_long_usd`, `oi_close` — reuse `liq_zscore` from `tradingagents.xsect.liq_mr` for the ground-truth daily z).
- Produces: `--probes-only` mode writing probes.json with pass/fail booleans; exits nonzero on STOP.

- [ ] **Step 1: Implement probes**

```python
# scripts/liq_fade_dev.py (structure; follow liq_mr_dev.py style — read it first)
# CLI: --probes-only | --grid | --all ; loads 1h panel (close, qvol) for
# union symbols, restricted to dev window + warmup, masked monthly by
# liq_fade_universe.json (weights force-zeroed for non-members).

# P0: bar-stamp reconciliation (BTCUSDT):
#   daily_from_1h = 1h close.resample('1D').last().pct_change()
#   corr with daily-store pct_change on overlap 2021-2025 -> require > 0.99
# P1: concordance (thr=2.5): triggers on the 8 mapped symbols
#   (BTCUSDT..TRXUSDT), any coin triggering any bar of a benchmark UTC date
#   counts as flagging that date; require >= 4/5.
# P2: event-study: for each (thr, H): mean over all dev triggers of
#   sum(R[t+1..t+H]) per event (gross, no costs) -> require max > 0.0025.
#   Also write the full per-H profile to probes.json for forensics.
```

- [ ] **Step 2: Run probes** — `nohup .venv/bin/python scripts/liq_fade_dev.py --probes-only > /tmp/liq_fade_probes.log 2>&1 &`, then inspect `probes.json`.
- [ ] **Step 3: Decision point** — If P0 fails: debug data (bug, not verdict). If P1 or P2 fails: STOP — skip Task 9, go to Task 10 and write NEGATIVE-at-probe verdict (§48). If pass: continue.
- [ ] **Step 4: Commit** — `git add scripts/liq_fade_dev.py data/rebuild/liq_fade/probes.json && git commit -m "feat(liq-fade): dev runner probes P0-P2 + results"`

---

### Task 9: Dev grid + dual-family placebo + DSR + ledger

**Files:**
- Modify: `scripts/liq_fade_dev.py` (grid section)
- Output: `data/rebuild/liq_fade/dev_results.json`, ledger rows in `data/rebuild/trial_ledger.jsonl`

**Interfaces:**
- Consumes: `rank_placebo_pvalue` from `tradingagents.xsect.portfolio`; `deflated_sharpe_ratio` from `tradingagents.strategies.v3.backtest.dsr` (read its signature before use); ledger append format = existing jsonl rows (ts, git_commit, experiment, config, config_hash, window, metrics).
- Produces: per-config metrics incl. `net_sr, placebo_p_shiftfam, placebo_p_randfam, n_events, events_per_coin_month, annual_turnover, sr_stress_20bps, maxdd`; DSR for best config with ledger-cumulative n_trials.

- [ ] **Step 1: Implement grid loop**

For each of the 6 configs: triggers → mask by universe membership months → `event_weights_hourly` → `run_hourly_portfolio` (dev window only) → metrics. Placebos per config, 500 draws each, seeded `rng = np.random.default_rng(48)`:
- Family A (shift): per symbol, circular-shift the masked trigger COLUMN by a uniform random offset in [24h, N−24h]; rebuild weights + P&L identically.
- Family B (random): per symbol, redraw `n_events` uniform bar positions (post-warmup, in-membership bars only); rebuild identically.
- `p = (1 + #{placebo_SR >= real_SR}) / (N + 1)` via `rank_placebo_pvalue`; gate on the WORSE family.
Runtime guard: placebo rebuild is the hot path — vectorize `event_weights_hourly` call per draw (it is already O(n·k) numpy); budget ≈ 6 configs × 1000 draws; if projected > 6h, log a note and reduce panel to membership-active columns only (never reduce draws).

- [ ] **Step 2: Ledger append** — one row per config, format-identical to `liq_mr_t1` rows (experiment `liq_fade_i1`).
- [ ] **Step 3: Run** — `nohup .venv/bin/python scripts/liq_fade_dev.py --grid > /tmp/liq_fade_grid.log 2>&1 &`; on completion verify 6 new ledger rows + dev_results.json.
- [ ] **Step 4: Commit** — `git add scripts/liq_fade_dev.py data/rebuild/liq_fade/dev_results.json data/rebuild/trial_ledger.jsonl && git commit -m "run(liq-fade-i1): dev grid + dual-family placebo + DSR + ledger"`

---

### Task 10: Forensic verification + verdict + THESIS §48 + memory

**Files:**
- Create/append: `data/rebuild/liq_fade/forensics.md`
- Modify: `master_thesis/THESIS_FINDINGS.md` (new §48 — NOTE: lives in `/home/malecada/master_thesis/`, not in the TradingAgents repo)
- Modify: memory `project_untried_leads_jul2026.md` + `MEMORY.md` + new `project_liq_fade_<verdict>.md`

**Interfaces:**
- Consumes: dev_results.json, probes.json, §47 forensics pattern (`data/rebuild/liq_mr/forensics.md`).

- [ ] **Step 1: Forensic pass (house discipline, esp. if 0/6)** — inversion test (short-fade same events must NOT beat long-fade), per-coin SR table, event-count honesty (≥30 events/config or declare underpowered), event-day vol percentile, placebo distribution sanity (real SR percentile plotted), turnover report vs 10bps sensitivity (`sr_stress_20bps` row), P2 profile consistency with grid outcome.
- [ ] **Step 2: Write §48** in THESIS_FINDINGS.md following §47's structure (hypothesis, pre-registration, probes, grid table, forensics, verdict, limitations).
- [ ] **Step 3: Update memories** — untried-leads status line for #4; new project memory file with verdict; MEMORY.md index line.
- [ ] **Step 4: Final commits + push** — thesis file committed in `master_thesis` (its own git), TradingAgents changes pushed on `feature/xs-momentum`.
- [ ] **Step 5: Verify** — `.venv/bin/python -m pytest tests/xsect/ -q` all green; `git status` clean except pre-existing P5 WIP files.

---

## Self-Review Notes

- Spec coverage: data (T1, T7), universe (T2, T7), signal (T3), sizing/holds (T4), P&L conventions (T5), registration (T6), probes (T8), gate+placebo+DSR (T9), forensics+§48 (T10). Slippage stress row: T9 metrics (`sr_stress_20bps`). Turnover report: T9/T10. ✓
- Types consistent: `cascade_triggers` bool DF → `event_weights_hourly` → `run_hourly_portfolio` daily Series → `sharpe_daily`. ✓
- Holdout: never loaded (fetch ends 2025-04-15 buffer for H=48 tail only; dev slice ends 2025-03-31). ✓
