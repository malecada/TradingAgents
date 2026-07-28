# Wide-Universe Trend Following Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pre-registered dev-gate evaluation of a long-flat trend ensemble over the top-N liquid USDT-M perps (spec: `docs/superpowers/specs/2026-07-28-trend-wide-design.md`).

**Architecture:** Frozen 4-rule vote (verbatim from §44 metalabel primary) → daily vol-targeted long-flat weights over a monthly-refreshed PIT top-N universe → vectorized daily portfolio with t+1 accrual and 10 bps/side turnover costs → 6-config grid gated by `trend_wide_t1` (net SR, ΔSR vs EW B&H benchmark, weight-shift placebo, DSR).

**Tech Stack:** Python 3.13 (`uv sync --all-extras --python 3.13.13`), pandas/numpy, pytest. Repo: `/home/malecada/master_thesis/TradingAgents`, branch `feature/xs-momentum`.

## Global Constraints

- Dev window: 2021-01-01 → 2025-03-31. Holdout ≥ 2025-04-01 LOCKED (`tradingagents/rebuild/ledger.assert_dev_window` enforces; never pass `allow_holdout=True` in this plan).
- Costs: 10 bps per side × Σ|Δw|, charged on the first accrual day after the weight change.
- Execution: decision at close t → weights apply to bar t+1's return. The decision bar never accrues the return that produced it.
- Grid frozen: N ∈ {10, 20} × vol_target ∈ {0.20, 0.30, 0.40}. No axes added after seeing results.
- Every full-window config evaluation logged via `log_trial("trend_wide_t1", ...)` BEFORE its result is read.
- Frozen primary parameters: MA pairs (5,20),(10,40),(20,60); Donchian 20-entry/10-exit; warmup 60; vote threshold 0.5. No re-tuning.
- Missing kline for a held coin: contributes 0 that day, weight NOT redistributed.
- SR convention: `mean/std*sqrt(365)`, 0.0 on zero variance (reuse `tradingagents.xsect.portfolio.sr`).
- σ rule (frozen): std of daily log-returns whose dates lie in [t−29d, t], computed on the symbol's series reindexed to the full daily calendar with `rolling(30, min_periods=30).std()` — any gap in the 30-day window ⇒ NaN ⇒ weight 0 (mirrors house gapless convention).

---

### Task 1: Frozen trend votes module (`trend_signal.py`) + parity fixture

**Files:**
- Create: `tradingagents/xsect/trend_signal.py`
- Create: `tests/fixtures/trend_votes_btc.csv` (generated, committed)
- Test: `tests/test_xsect_trend_signal.py`

**Interfaces:**
- Produces: `compute_votes(close: pd.Series) -> pd.Series` — input daily close indexed by tz-aware DatetimeIndex; output float votes in [0,1], NaN for first 59 bars. `MA_PAIRS`, `DONCHIAN_ENTRY`, `DONCHIAN_EXIT`, `WARMUP` module constants.
- Consumes: nothing.

- [ ] **Step 1: Generate parity fixture from the metalabel worktree (source of truth)**

```bash
cd /home/malecada/master_thesis/TradingAgents-metalabel && python - <<'EOF'
import pandas as pd, sys
sys.path.insert(0, ".")
from tradingagents.metalabel.primary import compute_votes
df = pd.read_parquet("/home/malecada/master_thesis/TradingAgents/data/xsect/klines/BTCUSDT.parquet")
sl = df.loc["2020-06-01":"2022-06-01"]
ohlcv = pd.DataFrame({"Date": sl.index, "Close": sl["close"].values})
votes = compute_votes(ohlcv)
out = pd.DataFrame({"date": votes.index, "vote": votes.values})
out.to_csv("/home/malecada/master_thesis/TradingAgents/tests/fixtures/trend_votes_btc.csv", index=False)
print(len(out), "rows")
EOF
```

Expected: `732 rows` (± a few; verify non-empty and file created).

- [ ] **Step 2: Write the failing parity test**

`tests/test_xsect_trend_signal.py`:

```python
"""Parity + shape tests for the frozen trend vote (verbatim from metalabel primary)."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.trend_signal import WARMUP, compute_votes

FIXTURE = Path(__file__).parent / "fixtures" / "trend_votes_btc.csv"
KLINES = Path(__file__).parents[1] / "data" / "xsect" / "klines"


def test_parity_with_metalabel_primary():
    fix = pd.read_csv(FIXTURE, parse_dates=["date"])
    close = pd.read_parquet(KLINES / "BTCUSDT.parquet").loc["2020-06-01":"2022-06-01", "close"]
    votes = compute_votes(close)
    assert len(votes) == len(fix)
    np.testing.assert_allclose(
        votes.values, fix["vote"].values, rtol=0, atol=1e-12, equal_nan=True
    )


def test_warmup_is_nan():
    idx = pd.date_range("2021-01-01", periods=120, freq="D", tz="UTC")
    close = pd.Series(np.linspace(100, 200, 120), index=idx)
    votes = compute_votes(close)
    assert votes.iloc[: WARMUP - 1].isna().all()
    assert votes.iloc[WARMUP:].notna().all()


def test_uptrend_votes_high_downtrend_low():
    idx = pd.date_range("2021-01-01", periods=200, freq="D", tz="UTC")
    up = pd.Series(np.linspace(100, 400, 200), index=idx)
    down = pd.Series(np.linspace(400, 100, 200), index=idx)
    assert compute_votes(up).iloc[-1] == 1.0
    assert compute_votes(down).iloc[-1] == 0.0
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_xsect_trend_signal.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tradingagents.xsect.trend_signal'`

- [ ] **Step 4: Write `tradingagents/xsect/trend_signal.py`**

Rule logic copied verbatim from `tradingagents/metalabel/primary.py` (§44 freeze); only the input adapter differs (close Series instead of ohlcv DataFrame — the rules read close only):

```python
"""Frozen model-free trend vote — verbatim rules from tradingagents/metalabel/primary.py
(§44 registration, branch feature/meta-labeling). Input adapted to a close Series;
parameters MUST NOT change (spec 2026-07-28-trend-wide-design.md).

Vote = mean of 4 binary rules: MA-cross 5/20, 10/40, 20/60 and a stateful
Donchian 20-entry/10-exit channel. Long when vote > 0.5.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MA_PAIRS = ((5, 20), (10, 40), (20, 60))
DONCHIAN_ENTRY = 20
DONCHIAN_EXIT = 10
WARMUP = 60


def compute_votes(close: pd.Series) -> pd.Series:
    rules = []
    for fast, slow in MA_PAIRS:
        rules.append((close.rolling(fast).mean() > close.rolling(slow).mean()).astype(float))

    # Stateful Donchian: 1 after close > prior 20d high, 0 after close < prior 10d low.
    hi = close.shift(1).rolling(DONCHIAN_ENTRY).max()
    lo = close.shift(1).rolling(DONCHIAN_EXIT).min()
    raw = pd.Series(np.nan, index=close.index)
    raw[close > hi] = 1.0
    raw[close < lo] = 0.0
    rules.append(raw.ffill().fillna(0.0))

    votes = pd.concat(rules, axis=1).mean(axis=1)
    votes.iloc[: WARMUP - 1] = np.nan
    votes.name = "vote"
    return votes
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_xsect_trend_signal.py -v`
Expected: 3 PASS. If parity fails: diff first mismatching row; the fixture side builds `close` via `pd.Series(ohlcv["Close"].values, index=DatetimeIndex(ohlcv["Date"]))` — identical values, so any mismatch is a copy error in Step 4, not an adapter issue.

- [ ] **Step 6: Commit**

```bash
git add tradingagents/xsect/trend_signal.py tests/test_xsect_trend_signal.py tests/fixtures/trend_votes_btc.csv
git commit -m "feat(trend-wide): frozen trend vote module + metalabel parity fixture"
```

---

### Task 2: Daily weight construction + portfolio engine (`trend.py`)

**Files:**
- Create: `tradingagents/xsect/trend.py`
- Test: `tests/test_xsect_trend.py`

**Interfaces:**
- Consumes: `compute_votes` (Task 1); `eligibility`, `load_klines` from `tradingagents.xsect.universe`; `sr`, `maxdd` from `tradingagents.xsect.portfolio`.
- Produces:
  - `monthly_refresh_dates(start: str, end: str) -> pd.DatetimeIndex` — first Monday of each calendar month in [start, end], tz='UTC'.
  - `build_matrices(klines: dict, symbols: list[str]) -> tuple[pd.DatetimeIndex, pd.DataFrame, pd.DataFrame, pd.DataFrame]` — returns `(all_days, R, VOTES, SIGMA)`; R = daily log-returns (days × symbols, NaN where missing), VOTES = votes on each symbol's own bars reindexed to all_days and forward-filled ONLY on days the symbol has a kline (NaN otherwise), SIGMA = calendar-window rolling(30, min_periods=30) std of R per symbol (computed on the full-calendar reindex, so any gap ⇒ NaN).
  - `trend_weights(all_days, R, VOTES, SIGMA, members_by_refresh: dict[pd.Timestamp, list[str]], n_slots: int, vol_target: float) -> pd.DataFrame` — daily decision weights W (days × symbols): `W[t,s] = (1/n_slots) * min(1, vol_target/(SIGMA[t,s]*sqrt(365)))` if s is a member of the refresh period covering t AND `VOTES[t,s] > 0.5` AND SIGMA finite, else 0.0. Membership of refresh date d applies to decision days t in [d, next_refresh).
  - `ew_benchmark_weights(all_days, R, members_by_refresh, n_slots) -> pd.DataFrame` — `W[t,s] = 1/n_slots` for members of the covering refresh period (regardless of votes/sigma), else 0.0.
  - `run_daily_portfolio(W: pd.DataFrame, R: pd.DataFrame, cost_bps: float = 10.0) -> pd.Series` — daily log-returns: `ret[t] = Σ_s W[t-1,s] * nan_to_num(R[t,s]) − cost_bps/1e4 * Σ_s |W[t-1,s] − W[t-2,s]|` (W[-1] := 0 rows). First returned bar = second day of W's index.
- Delisting is handled structurally: after a symbol's last kline, VOTES/SIGMA are NaN ⇒ weight 0 at the next decision ⇒ the Δw cost books the exit. No special case.

- [ ] **Step 1: Write failing tests**

`tests/test_xsect_trend.py`:

```python
"""Engine tests: refresh dates, weights, t+1 accrual, costs, no-look-ahead, delisting."""
import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.trend import (
    build_matrices, ew_benchmark_weights, monthly_refresh_dates,
    run_daily_portfolio, trend_weights,
)

UTC = "UTC"


def _mk_klines(prices: dict[str, pd.Series]) -> dict:
    return {s: pd.DataFrame({"close": p, "quote_volume": 1e9}, index=p.index)
            for s, p in prices.items()}


def _idx(start, periods):
    return pd.date_range(start, periods=periods, freq="D", tz=UTC)


def test_monthly_refresh_dates_first_mondays():
    d = monthly_refresh_dates("2021-01-01", "2021-04-30")
    assert list(d.strftime("%Y-%m-%d")) == ["2021-01-04", "2021-02-01", "2021-03-01", "2021-04-05"]
    assert (d.dayofweek == 0).all()


def test_run_daily_portfolio_t_plus_1_and_costs():
    days = _idx("2021-01-01", 4)
    # symbol A: log-returns [nan, 0.10, 0.20, -0.05]
    R = pd.DataFrame({"A": [np.nan, 0.10, 0.20, -0.05]}, index=days)
    # decision weights: 0, 1, 1, 0  (enter at close of day1, exit at close of day3)
    W = pd.DataFrame({"A": [0.0, 1.0, 1.0, 0.0]}, index=days)
    port = run_daily_portfolio(W, R, cost_bps=10.0)
    # day2: W[day1]=1 -> ret 0.20, cost of |1-0| = 0.001 charged day2 (first accrual after change)
    # day3: W[day2]=1 -> ret -0.05, no change day2->day1? W[day2]-W[day1]=0 -> no cost
    # day1 not in output? output starts at days[1]
    assert port.index[0] == days[1]
    # day1 accrual: W[day0]=0 -> 0.0, cost |W[day0]-W[-1]|=0
    assert port.loc[days[1]] == pytest.approx(0.0)
    assert port.loc[days[2]] == pytest.approx(0.20 - 0.001)
    assert port.loc[days[3]] == pytest.approx(-0.05)


def test_exit_cost_charged_after_flatten():
    days = _idx("2021-01-01", 4)
    R = pd.DataFrame({"A": [np.nan, 0.0, 0.0, 0.0]}, index=days)
    W = pd.DataFrame({"A": [1.0, 0.0, 0.0, 0.0]}, index=days)
    port = run_daily_portfolio(W, R, cost_bps=10.0)
    # entry cost on days[1] (first accrual after day0 change); exit Δ|0-1| on days[2]
    assert port.loc[days[1]] == pytest.approx(-0.001)
    assert port.loc[days[2]] == pytest.approx(-0.001)


def test_missing_kline_contributes_zero_not_redistributed():
    days = _idx("2021-01-01", 3)
    R = pd.DataFrame({"A": [np.nan, np.nan, 0.10], "B": [np.nan, 0.02, 0.02]}, index=days)
    W = pd.DataFrame({"A": [0.5, 0.5, 0.5], "B": [0.5, 0.5, 0.5]}, index=days)
    port = run_daily_portfolio(W, R, cost_bps=0.0)
    assert port.loc[days[1]] == pytest.approx(0.5 * 0.02)  # A missing -> 0, no redistribution


def test_trend_weights_no_look_ahead():
    """Mutate the last close; weights strictly before the mutated bar must not change."""
    rng = np.random.default_rng(0)
    idx = _idx("2020-10-01", 300)
    px = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.002, 0.03, 300))), index=idx)
    klines = _mk_klines({"A": px})
    refresh = monthly_refresh_dates("2021-01-01", "2021-07-31")
    members = {d: ["A"] for d in refresh}

    def weights_for(kl):
        all_days, R, V, S = build_matrices(kl, ["A"])
        return trend_weights(all_days, R, V, S, members, n_slots=1, vol_target=0.30)

    w1 = weights_for(klines)
    px2 = px.copy()
    px2.iloc[-1] *= 3.0
    w2 = weights_for(_mk_klines({"A": px2}))
    cut = idx[-1]
    pd.testing.assert_frame_equal(w1.loc[w1.index < cut], w2.loc[w2.index < cut])


def test_trend_weights_flat_when_vote_low_and_capped_by_vol_target():
    rng = np.random.default_rng(1)
    idx = _idx("2020-10-01", 300)
    up = pd.Series(100 * np.exp(np.cumsum(np.full(300, 0.01) + rng.normal(0, 0.001, 300))), index=idx)
    down = pd.Series(100 * np.exp(np.cumsum(np.full(300, -0.01) + rng.normal(0, 0.001, 300))), index=idx)
    klines = _mk_klines({"UP": up, "DOWN": down})
    refresh = monthly_refresh_dates("2021-01-01", "2021-07-31")
    members = {d: ["UP", "DOWN"] for d in refresh}
    all_days, R, V, S = build_matrices(klines, ["UP", "DOWN"])
    W = trend_weights(all_days, R, V, S, members, n_slots=2, vol_target=0.30)
    last = W.iloc[-1]
    assert last["DOWN"] == 0.0
    ann_vol = float(S["UP"].iloc[-1]) * np.sqrt(365)
    expected = 0.5 * min(1.0, 0.30 / ann_vol)
    assert last["UP"] == pytest.approx(expected)


def test_delisted_symbol_weight_zero_after_last_bar():
    idx_a = _idx("2020-10-01", 200)  # dies 2021-04-18
    idx_b = _idx("2020-10-01", 300)
    up_a = pd.Series(100 * np.exp(np.cumsum(np.full(200, 0.01))), index=idx_a)
    up_b = pd.Series(100 * np.exp(np.cumsum(np.full(300, 0.01))), index=idx_b)
    klines = _mk_klines({"A": up_a, "B": up_b})
    refresh = monthly_refresh_dates("2021-01-01", "2021-07-31")
    members = {d: ["A", "B"] for d in refresh}
    all_days, R, V, S = build_matrices(klines, ["A", "B"])
    W = trend_weights(all_days, R, V, S, members, n_slots=2, vol_target=0.30)
    after = W.loc[W.index > idx_a[-1], "A"]
    assert (after == 0.0).all()
    assert W.loc[idx_a[-1], "A"] > 0.0  # in-trend while alive


def test_ew_benchmark_constant_within_month():
    idx = _idx("2020-10-01", 300)
    px = pd.Series(np.linspace(100, 200, 300), index=idx)
    klines = _mk_klines({"A": px, "B": px * 2})
    refresh = monthly_refresh_dates("2021-01-01", "2021-05-31")
    members = {d: ["A", "B"] for d in refresh}
    all_days, R, V, S = build_matrices(klines, ["A", "B"])
    W = ew_benchmark_weights(all_days, R, members, n_slots=2)
    feb = W.loc["2021-02-01":"2021-02-28"]
    assert (feb["A"] == 0.5).all() and (feb["B"] == 0.5).all()
    assert (W.loc[W.index < refresh[0]] == 0.0).all().all()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_xsect_trend.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tradingagents.xsect.trend'`

- [ ] **Step 3: Implement `tradingagents/xsect/trend.py`**

```python
"""Wide-universe long-flat trend engine — frozen mechanics per gates.json trend_wide_t1.

Spec: docs/superpowers/specs/2026-07-28-trend-wide-design.md. Decision at close t
applies to bar t+1; costs 10 bps/side on |Δw| charged on the first accrual day.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.xsect.trend_signal import compute_votes

ANN = 365.0
VOL_WINDOW = 30


def monthly_refresh_dates(start: str, end: str) -> pd.DatetimeIndex:
    days = pd.date_range(start, end, freq="D", tz="UTC")
    mondays = days[days.dayofweek == 0]
    first = mondays.to_series().groupby([mondays.year, mondays.month]).min()
    return pd.DatetimeIndex(sorted(first.values)).tz_localize("UTC") if first.dt.tz is None \
        else pd.DatetimeIndex(sorted(first.values))


def build_matrices(klines: dict, symbols: list) -> tuple:
    """(all_days, R, VOTES, SIGMA). All frames days x symbols, NaN where undefined.

    VOTES: computed on each symbol's own bars (native index), then reindexed to
    all_days WITHOUT filling — a day with no kline has NaN vote (=> weight 0).
    SIGMA: rolling(30, min_periods=30).std() of R on the full daily calendar,
    so any missing day inside the window yields NaN (gapless house convention).
    """
    all_days = pd.DatetimeIndex(sorted(set().union(*[klines[s].index for s in symbols])))
    R = pd.DataFrame(index=all_days, columns=symbols, dtype=float)
    VOTES = pd.DataFrame(index=all_days, columns=symbols, dtype=float)
    for s in symbols:
        close = klines[s]["close"]
        R[s] = np.log(close).diff().reindex(all_days)
        VOTES[s] = compute_votes(close).reindex(all_days)
    SIGMA = R.rolling(VOL_WINDOW, min_periods=VOL_WINDOW).std()
    return all_days, R, VOTES, SIGMA


def _membership_mask(all_days, columns, members_by_refresh) -> pd.DataFrame:
    mask = pd.DataFrame(False, index=all_days, columns=columns)
    dates = sorted(members_by_refresh)
    for i, d in enumerate(dates):
        end = dates[i + 1] if i + 1 < len(dates) else None
        rows = (all_days >= d) & ((all_days < end) if end is not None else True)
        cols = [s for s in members_by_refresh[d] if s in mask.columns]
        mask.loc[rows, cols] = True
    return mask


def trend_weights(all_days, R, VOTES, SIGMA, members_by_refresh, n_slots: int,
                  vol_target: float) -> pd.DataFrame:
    member = _membership_mask(all_days, R.columns, members_by_refresh)
    scale = (vol_target / (SIGMA * np.sqrt(ANN))).clip(upper=1.0)
    W = (1.0 / n_slots) * scale.where(np.isfinite(scale), 0.0)
    W = W.where((VOTES > 0.5) & member, 0.0)
    return W.fillna(0.0)


def ew_benchmark_weights(all_days, R, members_by_refresh, n_slots: int) -> pd.DataFrame:
    member = _membership_mask(all_days, R.columns, members_by_refresh)
    return member.astype(float) / n_slots


def run_daily_portfolio(W: pd.DataFrame, R: pd.DataFrame, cost_bps: float = 10.0) -> pd.Series:
    Wv = W.to_numpy()
    Rv = np.nan_to_num(R.to_numpy(), nan=0.0)
    Wprev = np.vstack([np.zeros((1, Wv.shape[1])), Wv[:-1]])       # W[t-1]
    Wprev2 = np.vstack([np.zeros((2, Wv.shape[1])), Wv[:-2]])      # W[t-2]
    gross = (Wprev * Rv).sum(axis=1)
    cost = cost_bps / 1e4 * np.abs(Wprev - Wprev2).sum(axis=1)
    port = pd.Series(gross - cost, index=W.index)
    return port.iloc[1:]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_xsect_trend.py tests/test_xsect_trend_signal.py -v`
Expected: all PASS. Known trap in `monthly_refresh_dates`: groupby-min on tz-aware values — if the tz branch is wrong the first assertion fails on dtype; fix inside that function only.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/xsect/trend.py tests/test_xsect_trend.py
git commit -m "feat(trend-wide): daily weight construction + t+1 cost engine"
```

---

### Task 3: Placebo machinery + kill-test

**Files:**
- Modify: `tradingagents/xsect/trend.py` (append two functions)
- Modify: `tests/test_xsect_trend.py` (append tests)

**Interfaces:**
- Produces:
  - `circular_shift_weights(W: pd.DataFrame, rng: np.random.Generator, min_shift: int = 30) -> pd.DataFrame` — each column rolled by an independent random offset in [min_shift, len−min_shift]; costs are NOT baked in (placebo series goes through the same `run_daily_portfolio`).
  - `placebo_srs(W, R, n_placebo: int, cost_bps: float = 10.0) -> list[float]` — SR of `run_daily_portfolio(circular_shift_weights(W, rng seeded p), R)` for p in range(n_placebo); reuses `sr` from `tradingagents.xsect.portfolio`.
- Consumes: Task 2 engine; `sr`, `rank_placebo_pvalue` from `tradingagents.xsect.portfolio`.

- [ ] **Step 1: Write failing tests (append to `tests/test_xsect_trend.py`)**

```python
from tradingagents.xsect.portfolio import rank_placebo_pvalue, sr
from tradingagents.xsect.trend import circular_shift_weights, placebo_srs


def test_circular_shift_preserves_mass_and_reproducible():
    days = _idx("2021-01-01", 400)
    rng0 = np.random.default_rng(7)
    W = pd.DataFrame({"A": rng0.uniform(0, 1, 400), "B": rng0.uniform(0, 1, 400)}, index=days)
    s1 = circular_shift_weights(W, np.random.default_rng(3))
    s2 = circular_shift_weights(W, np.random.default_rng(3))
    pd.testing.assert_frame_equal(s1, s2)
    assert np.allclose(np.sort(s1["A"].values), np.sort(W["A"].values))
    assert not s1.equals(W)


def test_placebo_kill_test_on_synthetic_trend():
    """Real trend weights must beat ~all circularly-shifted placebos on a
    regime series engineered so trend-following earns (mutation kill-test)."""
    rng = np.random.default_rng(42)
    n = 900
    regime = np.sign(np.sin(np.arange(n) / 60.0))       # ~120d alternating regimes
    r = 0.004 * regime + rng.normal(0, 0.01, n)
    idx = _idx("2020-06-01", n)
    px = pd.Series(100 * np.exp(np.cumsum(r)), index=idx)
    klines = _mk_klines({"A": px})
    refresh = monthly_refresh_dates("2020-09-01", str(idx[-1].date()))
    members = {d: ["A"] for d in refresh}
    all_days, R, V, S = build_matrices(klines, ["A"])
    W = trend_weights(all_days, R, V, S, members, n_slots=1, vol_target=0.40)
    real = sr(run_daily_portfolio(W, R, cost_bps=10.0))
    p_srs = placebo_srs(W, R, n_placebo=99, cost_bps=10.0)
    p = rank_placebo_pvalue(real, p_srs)
    assert real > 0
    assert p <= 0.05
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_xsect_trend.py -v -k "circular or kill"`
Expected: FAIL — `ImportError: cannot import name 'circular_shift_weights'`

- [ ] **Step 3: Implement (append to `tradingagents/xsect/trend.py`)**

```python
def circular_shift_weights(W: pd.DataFrame, rng: np.random.Generator,
                            min_shift: int = 30) -> pd.DataFrame:
    """Per-column random circular roll — preserves each coin's weight
    autocorrelation and vol-scaling structure, destroys alignment with the
    market path. Costs are re-applied downstream by run_daily_portfolio."""
    n = len(W)
    out = {}
    for col in W.columns:
        k = int(rng.integers(min_shift, n - min_shift))
        out[col] = np.roll(W[col].to_numpy(), k)
    return pd.DataFrame(out, index=W.index, columns=W.columns)


def placebo_srs(W: pd.DataFrame, R: pd.DataFrame, n_placebo: int,
                 cost_bps: float = 10.0) -> list:
    from tradingagents.xsect.portfolio import sr as _sr
    out = []
    for p in range(n_placebo):
        rng = np.random.default_rng(seed=p)  # reproducible per placebo index
        shifted = circular_shift_weights(W, rng)
        out.append(_sr(run_daily_portfolio(shifted, R, cost_bps=cost_bps)))
    return out
```

- [ ] **Step 4: Run full test file — all pass**

Run: `python -m pytest tests/test_xsect_trend.py tests/test_xsect_trend_signal.py -v`
Expected: all PASS (kill-test may take ~10-30s for 99 placebos; fine).

- [ ] **Step 5: Commit**

```bash
git add tradingagents/xsect/trend.py tests/test_xsect_trend.py
git commit -m "feat(trend-wide): circular-shift placebo + synthetic kill-test"
```

---

### Task 4: Register `trend_wide_t1` in gates.json (BEFORE any experiment run)

**Files:**
- Modify: `data/rebuild/gates.json` (add one top-level key; do not touch existing keys)

**Interfaces:**
- Produces: gates entry consumed by Task 5's script (`GATE` constants must match it verbatim).

- [ ] **Step 1: Add the entry**

Python one-liner to avoid hand-editing JSON:

```bash
cd /home/malecada/master_thesis/TradingAgents && python - <<'EOF'
import json
p = "data/rebuild/gates.json"
g = json.load(open(p))
assert "trend_wide_t1" not in g
g["trend_wide_t1"] = {
    "registered": "2026-07-28",
    "spec": "docs/superpowers/specs/2026-07-28-trend-wide-design.md",
    "dev_window": ["2021-01-01", "2025-03-31"],
    "holdout_window": ["2025-04-01", "2026-07-01"],
    "signal": "frozen metalabel primary verbatim (MA 5/20,10/40,20/60 + Donchian 20/10, vote>0.5, warmup 60); long-flat",
    "universe_rule": "PIT monthly refresh at first Monday close of each month using data <= that close: USDT-M perp with kline on day D, first kline <= D-30, 30d median quote-volume >= 5000000 USD, rank by 30d median quote-volume, keep top-N; symbol needs >= 90 daily bars at decision; coin leaving universe force-flattened next bar with cost",
    "portfolio_rule": "daily decision close t -> weights apply bar t+1; w = (1/N)*min(1, vol_target/(sigma30*sqrt(365)))*1{vote>0.5}; sigma30 = rolling 30-calendar-day std of daily log-returns, gapless else weight 0; costs 10 bps per side on sum|dW| charged first accrual day; missing kline contributes 0, no redistribution",
    "benchmark": "per-N EW buy-and-hold of same monthly top-N universe, same t+1 and cost mechanics",
    "grid": {"N": [10, 20], "vol_target": [0.20, 0.30, 0.40]},
    "bootstrap": {"block": 21, "n": 2000},
    "placebo": "N=500 per-coin random circular time-shifts (min offset 30d) of the final daily weight series, costs re-applied; p=(1+#{placebo SR >= real SR})/(N+1)",
    "dev_select": {"net_sr_min": 1.0, "delta_sr_vs_benchmark_min": 0.0,
                    "p_pos_min": 0.90, "placebo_p_max": 0.05, "dsr_min": 0.9,
                    "tiebreak": "highest DSR, then lowest placebo p"},
    "holdout_deploy": {"net_sr_min": 0.5, "delta_sr_vs_benchmark_min": 0.0,
                        "p_pos_min": 0.85, "placebo_p_max": 0.05, "one_shot": True},
}
json.dump(g, open(p, "w"), indent=1)
print("registered trend_wide_t1")
EOF
```

- [ ] **Step 2: Verify JSON valid + existing entries untouched**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -c "import json; g=json.load(open('data/rebuild/gates.json')); print(sorted(g)); print(g['trend_wide_t1']['dev_select'])" && git diff --stat data/rebuild/gates.json`
Expected: key list includes `trend_wide_t1` plus all 9 prior keys; diff touches only the new block.

- [ ] **Step 3: Commit (registration timestamp = this commit)**

```bash
git add data/rebuild/gates.json
git commit -m "exp(trend-wide): register trend_wide_t1 gates BEFORE any run"
```

---

### Task 5: Dev grid script (`scripts/trend_wide_dev.py`)

**Files:**
- Create: `scripts/trend_wide_dev.py`

**Interfaces:**
- Consumes: everything above; `log_trial`, `DEFAULT_LEDGER` from `tradingagents.rebuild.ledger`; `paired_bootstrap`, `rank_placebo_pvalue`, `sr`, `maxdd` from `tradingagents.xsect.portfolio`; `eligibility`, `load_klines` from `tradingagents.xsect.universe`; DSR trio from `tradingagents.strategies.v3.backtest.dsr`; `_unique_config_hashes` house convention (copy the 12-line helper from `scripts/xs_mom_dev.py:55-67`).
- Produces: `data/rebuild/trend_wide/dev_results.json`, ledger rows `experiment="trend_wide_t1"`, stdout table.

- [ ] **Step 1: Write the script**

```python
"""trend_wide_t1 dev grid: 6 pre-registered configs vs per-N EW B&H benchmark.

Ledger: trend_wide_t1. Gates: data/rebuild/gates.json["trend_wide_t1"].
Mechanics per docs/superpowers/specs/2026-07-28-trend-wide-design.md.
"""
import json
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.rebuild.ledger import DEFAULT_LEDGER, log_trial  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.xsect.portfolio import (  # noqa: E402
    maxdd, paired_bootstrap, rank_placebo_pvalue, sr,
)
from tradingagents.xsect.trend import (  # noqa: E402
    build_matrices, circular_shift_weights, ew_benchmark_weights,
    monthly_refresh_dates, run_daily_portfolio, trend_weights,
)
from tradingagents.xsect.universe import eligibility, load_klines  # noqa: E402

DEV = ("2021-01-01", "2025-03-31")
GRID = list(product([10, 20], [0.20, 0.30, 0.40]))  # N, vol_target — frozen, 6 configs
GATE = {"net_sr_min": 1.0, "delta_sr_vs_benchmark_min": 0.0, "p_pos_min": 0.90,
        "placebo_p_max": 0.05, "dsr_min": 0.9}
OUT = Path("data/rebuild/trend_wide")
N_PLACEBO = 500
COST_BPS = 10.0
MIN_HISTORY_BARS = 90
KLINE_DIR = Path("data/xsect/klines")


def _unique_config_hashes(ledger_path: Path = DEFAULT_LEDGER) -> int:
    """House convention for DSR n_trials (scripts/xs_mom_dev.py)."""
    seen = set()
    with open(ledger_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            seen.add(json.loads(line)["config_hash"])
    return len(seen)


def _sanitize(obj):
    if isinstance(obj, float):
        return None if (np.isnan(obj) or np.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


def _blocked(reason: str, diagnostics: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = _sanitize({"blocked": True, "reason": reason, "diagnostics": diagnostics})
    with open(OUT / "dev_results.json", "w") as f:
        json.dump(payload, f, indent=1, allow_nan=False)
    print(f"\nBLOCKED: {reason}")
    print(json.dumps(_sanitize(diagnostics), indent=1))


def main() -> None:
    t_start = time.time()
    klines = load_klines(KLINE_DIR)
    refresh = monthly_refresh_dates(*DEV)
    hi = pd.Timestamp(DEV[1], tz="UTC")

    # ── Universe per refresh date, per N (eligibility + >=90-bar history) ──
    t0 = time.time()
    members = {N: {} for N, _ in set((n, v) for n, v in GRID)}
    for d in refresh:
        base = eligibility(klines, d, top_n=100)
        aged = [s for s in base
                if len(klines[s].loc[:d]) >= MIN_HISTORY_BARS]
        for N in (10, 20):
            ranked = aged[:N]  # eligibility already volume-ranked
            members[N][d] = ranked
    counts = {N: [len(v) for v in members[N].values()] for N in (10, 20)}
    print(f"[universe] refreshes={len(refresh)} "
          f"N=10 min/med={min(counts[10])}/{int(np.median(counts[10]))} "
          f"N=20 min/med={min(counts[20])}/{int(np.median(counts[20]))} "
          f"({time.time() - t0:.1f}s)")
    if min(counts[20]) < 20:
        short = [(str(d.date()), len(members[20][d])) for d in refresh
                 if len(members[20][d]) < 20]
        # spec: use all eligible, log count — proceed, do not block
        print(f"[universe] WARNING: {len(short)} refreshes with <20 members: {short[:6]}")

    # ── Matrices over the union of all symbols ever selected ──
    t0 = time.time()
    union = sorted(set().union(*[set(v) for N in (10, 20) for v in members[N].values()]))
    all_days, R, VOTES, SIGMA = build_matrices(klines, union)
    print(f"[matrices] union_symbols={len(union)} days={len(all_days)} "
          f"({time.time() - t0:.1f}s)")

    # ── Benchmarks per N ──
    bench = {}
    for N in (10, 20):
        Wb = ew_benchmark_weights(all_days, R, members[N], n_slots=N)
        s = run_daily_portfolio(Wb, R, COST_BPS).loc[:hi]
        s = s.loc[s.index > refresh[0]]
        bench[N] = s
        print(f"[benchmark N={N}] SR={sr(s):+.4f} maxdd={maxdd(s):.4f} n_days={len(s)}")

    # ── Sanity gates (frozen) ──
    problems = []
    for N in (10, 20):
        nd = len(bench[N])
        if not (1450 <= nd <= 1560):
            problems.append(f"benchmark N={N} n_days={nd} outside 1505+/-55")
        if not (-1.5 < sr(bench[N]) < 2.5):
            problems.append(f"benchmark N={N} SR={sr(bench[N]):.4f} outside (-1.5, 2.5)")
    if problems:
        _blocked("; ".join(problems), {f"bench_{N}": sr(bench[N]) for N in (10, 20)})
        return

    # ── Grid: 6 configs; placebos shared per N via identical seeds ──
    results = []
    series_by_cfg = {}
    for N, vt in GRID:
        t_cfg = time.time()
        W = trend_weights(all_days, R, VOTES, SIGMA, members[N], n_slots=N, vol_target=vt)
        real = run_daily_portfolio(W, R, COST_BPS).loc[:hi]
        real = real.loc[real.index > refresh[0]]
        real_sr = sr(real)
        pb = paired_bootstrap(real, bench[N])
        p_srs = []
        for p in range(N_PLACEBO):
            rng = np.random.default_rng(seed=p)
            shifted = circular_shift_weights(W, rng)
            ps = run_daily_portfolio(shifted, R, COST_BPS).loc[:hi]
            ps = ps.loc[ps.index > refresh[0]]
            p_srs.append(sr(ps))
        placebo_p = rank_placebo_pvalue(real_sr, p_srs)
        cfg = {"N": N, "vol_target": vt, "cost_bps": COST_BPS,
               "min_history_bars": MIN_HISTORY_BARS, "refresh": "monthly_first_monday"}
        metrics = {"net_sr": real_sr, "maxdd": maxdd(real),
                   "total_logret": float(real.sum()),
                   "bench_sr": sr(bench[N]), "delta_sr": pb["delta_sr"],
                   "p_pos": pb["p_pos"], "placebo_p": placebo_p, "n_days": len(real)}
        log_trial("trend_wide_t1", cfg, DEV, metrics)
        series_by_cfg[(N, vt)] = real
        results.append({"config": cfg, "metrics": metrics})
        print(f"N={N} vt={vt}: SR={real_sr:+.3f} dSR={pb['delta_sr']:+.3f} "
              f"p_pos={pb['p_pos']:.3f} placebo_p={placebo_p:.3f} "
              f"({time.time() - t_cfg:.1f}s)")

    # ── DSR after all 6 logged (house recipe) ──
    n_trials = _unique_config_hashes()
    for r in results:
        cand = series_by_cfg[(r["config"]["N"], r["config"]["vol_target"])].values
        var_sr = variance_of_sr(cand)
        se_sr = float(np.sqrt(var_sr))
        sr_perbar = float(cand.mean() / cand.std(ddof=1)) if cand.std(ddof=1) > 0 else 0.0
        dsr = deflated_sharpe_ratio(sr_perbar, expected_max_sharpe(n_trials, var_sr), se_sr)
        r["metrics"]["dsr"] = dsr
        r["metrics"]["n_trials_at_eval"] = n_trials
        m = r["metrics"]
        r["gate_pass"] = bool(
            m["net_sr"] >= GATE["net_sr_min"]
            and m["delta_sr"] > GATE["delta_sr_vs_benchmark_min"]
            and m["p_pos"] >= GATE["p_pos_min"]
            and m["placebo_p"] <= GATE["placebo_p_max"]
            and m["dsr"] >= GATE["dsr_min"]
        )

    passing = [r for r in results if r["gate_pass"]]
    selected = (max(passing, key=lambda r: (r["metrics"]["dsr"], -r["metrics"]["placebo_p"]))
                if passing else None)

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"benchmarks": {str(N): {"sr": sr(bench[N]), "maxdd": maxdd(bench[N]),
                                        "n_days": len(bench[N])} for N in (10, 20)},
               "results": results, "selected": selected,
               "n_trials_at_eval": n_trials,
               "total_runtime_sec": time.time() - t_start}
    with open(OUT / "dev_results.json", "w") as f:
        json.dump(_sanitize(payload), f, indent=1, allow_nan=False, default=str)

    print(f"\nselected: {json.dumps(selected['config']) if selected else 'NONE'}")
    print(f"total runtime: {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-run mechanics on a truncated window WITHOUT ledger writes**

Ledger discipline: no full-window evaluation before registration is committed (Task 4 precedes this task, so registration is already in). But a mechanics smoke on a short window must not pollute the ledger — run with a temporary ledger path:

```bash
cd /home/malecada/master_thesis/TradingAgents && python - <<'EOF'
import sys; sys.path.insert(0, ".")
import scripts.trend_wide_dev as m
import tradingagents.rebuild.ledger as L
from pathlib import Path
m.DEV = ("2021-01-01", "2021-12-31")
m.N_PLACEBO = 20
L.DEFAULT_LEDGER = Path("/tmp/claude-1000/-home-malecada-master-thesis/b69c929c-9a7d-44c6-a677-a3e0d43e6c10/scratchpad/smoke_ledger.jsonl")
m.log_trial = lambda *a, **k: L.log_trial(a[0], a[1], a[2], a[3], ledger_path=L.DEFAULT_LEDGER)
m.OUT = Path("/tmp/claude-1000/-home-malecada-master-thesis/b69c929c-9a7d-44c6-a677-a3e0d43e6c10/scratchpad/trend_smoke")
m._unique_config_hashes = lambda ledger_path=None: 6
m.main()
EOF
```

Expected: runs to completion in a few minutes; prints 6 config lines with finite SR/p_pos/placebo_p (sanity gates on benchmark n_days will trip on the short window — if `_blocked` fires with only the n_days complaint, that is EXPECTED on the smoke; relax nothing, just confirm the universe/matrices/benchmark lines printed sane numbers and configs produced finite metrics before the block, by also setting `m.GATE` untouched and reading the blocked diagnostics). If it blocks before printing config lines for a reason OTHER than n_days, fix the engine, not the gates.

- [ ] **Step 3: Commit script**

```bash
git add scripts/trend_wide_dev.py
git commit -m "exp(trend-wide): dev grid script (6 configs, per-N EW benchmark, 500 placebos)"
```

---

### Task 6: Full dev run + results

**Files:**
- Produces: `data/rebuild/trend_wide/dev_results.json`, 6 ledger rows.

- [ ] **Step 1: Full run (foreground bash, long timeout; ~6 configs × 500 placebos)**

```bash
cd /home/malecada/master_thesis/TradingAgents && nohup python scripts/trend_wide_dev.py > data/rebuild/trend_wide/dev_run.log 2>&1 &
```

Poll `data/rebuild/trend_wide/dev_run.log`. Expected runtime: minutes to ~1h (3000 placebo portfolio evals on ~1550×≤60 matrices are cheap; placebo loop is the bulk).

- [ ] **Step 2: Verify integrity**

```bash
cd /home/malecada/master_thesis/TradingAgents && python - <<'EOF'
import json
r = json.load(open("data/rebuild/trend_wide/dev_results.json"))
assert not r.get("blocked"), r.get("reason")
assert len(r["results"]) == 6
rows = sum(1 for l in open("data/rebuild/trial_ledger.jsonl")
           if '"trend_wide_t1"' in l)
assert rows == 6, rows
print("selected:", r["selected"] and r["selected"]["config"])
for x in r["results"]:
    print(x["config"]["N"], x["config"]["vol_target"], x["metrics"]["net_sr"],
          x["metrics"]["delta_sr"], x["metrics"]["p_pos"],
          x["metrics"]["placebo_p"], x["metrics"].get("dsr"), x["gate_pass"])
EOF
```

Expected: 6 results, 6 ledger rows, selected = config or None.

- [ ] **Step 3: Commit results + ledger**

```bash
git add data/rebuild/trend_wide/dev_results.json data/rebuild/trial_ledger.jsonl
git commit -m "exp(trend-wide): dev grid results, ledgered (6 configs)"
```

---

### Task 7: THESIS section + memory

**Files:**
- Modify: `THESIS_FINDINGS.md` (append §45)
- Modify: memory `project_trend_wide.md` (outcome)

- [ ] **Step 1: Write §45**

Content requirements (either outcome): design provenance (lead #2; lead #1 Guo drop documented in spec), frozen grid table, benchmark SRs, per-config table (net SR, ΔSR, p_pos, placebo p, DSR, gate_pass), verdict. If dev_select passes: state that holdout one-shot is AVAILABLE but NOT yet spent — spending it is a separate user decision. If fail: honest negative, holdout stays sealed, mechanism discussion (beta capture vs no trend edge — compare config SR vs benchmark SR pattern).

- [ ] **Step 2: Commit + update memory**

```bash
git add THESIS_FINDINGS.md
git commit -m "docs(thesis): section 45 — wide-universe trend dev-gate result"
```

Update `~/.claude/.../memory/project_trend_wide.md` status line and MEMORY.md hook with the verdict.

---

## Self-Review (done at write time)

1. Spec coverage: signal ✓(T1), universe+90-bar ✓(T5 members), sizing ✓(T2 trend_weights), execution/costs ✓(T2 run_daily_portfolio), grid ✓(T5 GRID), benchmark ✓(T2+T5), windows ✓(DEV + ledger guard), gates ✓(T4), placebo ✓(T3), error handling ✓(NaN→0 / min_periods / <N members warns), all 6 spec tests ✓(T1: parity; T2: look-ahead, delisting, costs, benchmark; T3: placebo kill), deliverables ✓ (trend.py split into trend_signal.py+trend.py — finer than spec, same surface).
2. Placeholder scan: clean.
3. Type consistency: `build_matrices` → (all_days, R, VOTES, SIGMA) used identically in T2 tests, T3 tests, T5; `members_by_refresh: dict[Timestamp, list[str]]` consistent; gate constants T4 == T5 GATE.
Delisting forced-exit note: structural (NaN votes ⇒ 0 weight next bar + Δw cost) — test in T2 covers it; spec's "exits at last available close" realized as: last accrued return is the last real bar, weight zeroes on the following decision row, cost books then. Documented in T2 interface block.
