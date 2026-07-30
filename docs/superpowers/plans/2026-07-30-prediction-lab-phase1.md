# Prediction Lab Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Under the Ralph loop (`docs/predlab/RALPH_PROMPT.md`): one task (or split sub-task) per iteration.

**Goal:** Build the forecast-evaluation core (losses, significance tests, purged rolling-origin harness), the 5-minute kline + realized-volatility stores, the Phase-1 registration, and the Tier 0/1 classical battery over the registered cells — producing predictability map v1.

**Architecture:** New `tradingagents/predlab/` package with small single-purpose modules (losses, splits, tests, RV, baselines, tier1 wrappers, registry, runner). Flat CLI scripts `scripts/predlab_*.py`. Own data namespace `data/predlab/`. Registration + append-only ledger mirror the house `rebuild/ledger.py` pattern but live in predlab files. Governing spec: `docs/superpowers/specs/2026-07-30-prediction-lab-charter-design.md`; priors and toolkit rationale: `docs/predlab/RESEARCH.md`.

**Tech Stack:** Python 3.13 (uv venv, source py3.9-compatible), numpy/pandas/pyarrow, statsmodels (ARIMA/ETS/HAC), `arch` (GARCH family; SPA/MCS later), lightgbm (Phase 2), pytest.

## Global Constraints

- Every `.py` starts with `from __future__ import annotations`; no py3.10+-only syntax in `tradingagents/` (house rule).
- Env: `cd /home/malecada/master_thesis/TradingAgents-predlab && uv sync --all-extras --python 3.13.13`; run tests `uv run pytest tests/predlab -q`. Full suite before each battery task: `uv run pytest -q` (3 pre-existing failures outside predlab are known-OK if unchanged).
- Writes ONLY under: `tradingagents/predlab/`, `tests/predlab/`, `scripts/predlab_*.py`, `data/predlab/`, `docs/predlab/`, `docs/superpowers/`, `THESIS_FINDINGS.md` (§54+, append-only), `pyproject.toml`+`uv.lock` (dependency add only).
- Dev window 2021-01-01 → 2025-03-31; **holdout 2025-04-01 → 2026-07-01 sealed**: battery loaders hard-clip frames at `MAX_LOAD_END = 2025-03-31` (fetchers may store full history; evaluation code never reads past the clip in Phase 1–4).
- Data conventions: UTC everywhere; parquet with `ts` int64 ms epoch column (house store convention); canonical cache filenames, tail-append, never embed run date in a filename.
- Ledger `data/predlab/trial_ledger.jsonl` is append-only; every evaluated (cell, model, config) writes a row; `n_trials`-style denominators always computed from the ledger.
- All losses on returns/RV use returns (log) and variance units — never price levels (RESEARCH.md §1 structural warning i).
- Zero-variance/degenerate stats: return `nan` + set a `degenerate` flag; never raise mid-battery.
- Commit after every task with `feat(predlab):` / `test(predlab):` / `exp(predlab):` / `docs(predlab):` prefixes.

---

### Task 1: Package skeleton, dependencies, losses

**Files:**
- Create: `tradingagents/predlab/__init__.py` (empty), `tradingagents/predlab/losses.py`
- Create: `tests/predlab/__init__.py` (empty), `tests/predlab/test_losses.py`
- Modify: `pyproject.toml` (add `arch>=7.0` to `[project.dependencies]`; add `dieboldmariano` to the dev extra)

**Interfaces:**
- Produces (exact signatures, all take/return `np.ndarray` float64, elementwise per-observation losses — the DM/CW tests consume per-observation loss vectors):
  - `se(y_true, y_pred) -> np.ndarray` (squared error), `ae(y_true, y_pred) -> np.ndarray`
  - `qlike(var_forecast, rv) -> np.ndarray` — Patton normalized: `r = rv/var_forecast; r - log(r) - 1`; requires both > 0, else `nan` at that element
  - `mase_scale(y_train, m=1) -> float` — `mean(abs(y_train[m:] - y_train[:-m]))` (train-only scaling)
  - `mase(y_true, y_pred, scale) -> np.ndarray` — `ae/scale`
  - `brier(p_up, y_up) -> np.ndarray` — `(p_up - y_up)**2`

- [ ] **Step 1: deps** — `uv add "arch>=7.0" && uv add --dev dieboldmariano` (in the worktree). Verify `uv run python -c "import arch; print(arch.__version__)"`.
- [ ] **Step 2: failing tests** — `tests/predlab/test_losses.py`:

```python
import numpy as np
from tradingagents.predlab import losses

def test_qlike_zero_at_perfect_forecast():
    rv = np.array([0.5, 1.0, 2.0])
    assert np.allclose(losses.qlike(rv, rv), 0.0)

def test_qlike_known_value():
    # r = 2: 2 - ln 2 - 1 = 0.30685281944
    out = losses.qlike(np.array([1.0]), np.array([2.0]))
    assert np.isclose(out[0], 0.30685281944005469)

def test_qlike_nonpositive_gives_nan():
    out = losses.qlike(np.array([1.0, 0.0]), np.array([0.0, 1.0]))
    assert np.isnan(out).all()

def test_mase_scale_seasonal():
    y = np.array([1.0, 2.0, 3.0, 5.0])
    # m=1 diffs |1,1,2| -> 4/3
    assert np.isclose(losses.mase_scale(y, m=1), 4.0/3.0)
    # m=2 diffs |2,3| -> 2.5
    assert np.isclose(losses.mase_scale(y, m=2), 2.5)

def test_brier_and_se_ae():
    assert np.isclose(losses.brier(np.array([0.8]), np.array([1.0]))[0], 0.04)
    assert np.isclose(losses.se(np.array([1.0]), np.array([3.0]))[0], 4.0)
    assert np.isclose(losses.ae(np.array([1.0]), np.array([3.0]))[0], 2.0)
```

- [ ] **Step 3: run, verify FAIL** — `uv run pytest tests/predlab/test_losses.py -q` → import error.
- [ ] **Step 4: implement `losses.py`** exactly per Interfaces (vectorized numpy; `qlike` masks `var_forecast<=0 | rv<=0` to `nan`).
- [ ] **Step 5: run, verify PASS**, then **commit** `feat(predlab): package skeleton, loss functions, arch dependency`.

---

### Task 2: Purged rolling-origin splitter

**Files:**
- Create: `tradingagents/predlab/splits.py`, `tests/predlab/test_splits.py`

**Interfaces:**
- Data convention consumed by everything downstream: aligned arrays indexed by origin `t` where `y[t]` = target realized over `(t, t+h]` (known only at `t+h`); features/forecasts at origin `t` use info ≤ `t`.
- Produces:
  - `@dataclass OriginSplit: origin: int; train_end: int` — usable train origins are `range(0, train_end)` (exclusive), guaranteeing `s + h <= origin - embargo` for every train origin `s`.
  - `rolling_origin(n: int, min_train: int, horizon: int, step: int = 1, embargo: int = 0) -> list[OriginSplit]` — origins `t` from `min_train` to `n-1` inclusive stepping `step`; `train_end = origin - horizon - embargo + 1`, clipped ≥ 0; splits with `train_end < min_train_effective` (= 30) are skipped.

- [ ] **Step 1: failing tests**

```python
from tradingagents.predlab.splits import rolling_origin

def test_no_label_overlap_property():
    for h in (1, 7, 24):
        for emb in (0, 3):
            for sp in rolling_origin(500, min_train=100, horizon=h, embargo=emb):
                # last train origin s = train_end-1; its label covers (s, s+h]
                assert (sp.train_end - 1) + h <= sp.origin - emb

def test_origin_range_and_step():
    sps = rolling_origin(200, min_train=150, horizon=1, step=10)
    assert [s.origin for s in sps] == [150, 160, 170, 180, 190]

def test_short_series_yields_nothing():
    assert rolling_origin(50, min_train=100, horizon=1) == []
```

- [ ] **Step 2: verify FAIL** → **Step 3: implement** → **Step 4: verify PASS** → **Step 5: commit** `feat(predlab): purged rolling-origin splitter`.

---

### Task 3: Mean tests — Newey-West t and stationary bootstrap

**Files:**
- Create: `tradingagents/predlab/meanstats.py`, `tests/predlab/test_meanstats.py`

**Interfaces:**
- `nw_tstat(x: np.ndarray, lag: int) -> float` — t-stat of mean(x)=0 with Bartlett-kernel long-run variance: `lrv = g0 + 2*sum_{k=1..lag} (1-k/(lag+1))*g_k`; returns `nan` if `lrv <= 0` or `len(x) < 8`.
- `stationary_bootstrap_means(x, n_boot=2000, mean_block=21, seed=0) -> np.ndarray` — Politis-Romano resampled means (geometric block lengths, wrap-around indexing; same scheme as `tradingagents/xsect/portfolio.py:_stationary_indices` — reimplement locally, do not import across experiment namespaces).
- `p_pos(x, **kw) -> float` — share of bootstrap means > 0 (house `p_pos` convention).

- [ ] **Step 1: failing tests**

```python
import numpy as np
from statsmodels.regression.linear_model import OLS
from tradingagents.predlab import meanstats

def test_nw_matches_statsmodels_hac():
    rng = np.random.default_rng(7)
    x = rng.normal(0.1, 1.0, 400) + np.r_[0, rng.normal(0, .5, 399)]  # autocorrelated-ish
    lag = 5
    ours = meanstats.nw_tstat(x, lag=lag)
    sm = OLS(x, np.ones_like(x)).fit(cov_type="HAC", cov_kwds={"maxlags": lag}).tvalues[0]
    assert np.isclose(ours, sm, rtol=1e-6)

def test_bootstrap_p_pos_extremes():
    rng = np.random.default_rng(0)
    up = rng.normal(1.0, 0.1, 300)
    dn = rng.normal(-1.0, 0.1, 300)
    assert meanstats.p_pos(up, n_boot=500, seed=1) > 0.99
    assert meanstats.p_pos(dn, n_boot=500, seed=1) < 0.01

def test_bootstrap_deterministic_under_seed():
    x = np.random.default_rng(3).normal(0, 1, 200)
    a = meanstats.stationary_bootstrap_means(x, n_boot=50, seed=42)
    b = meanstats.stationary_bootstrap_means(x, n_boot=50, seed=42)
    assert np.array_equal(a, b)
```

- [ ] **Step 2-5:** FAIL → implement → PASS → commit `feat(predlab): Newey-West t and stationary bootstrap`.

---

### Task 4: Forecast-comparison tests — DM-HLN, Clark-West, Giacomini-White

**Files:**
- Create: `tradingagents/predlab/dm.py`, `tests/predlab/test_dm.py`

**Interfaces:**
- `@dataclass TestResult: stat: float; pvalue: float; degenerate: bool`
- `dm_test(loss_base, loss_model, h=1, alternative="greater") -> TestResult` — `d = loss_base - loss_model` (positive ⇒ model beats base). DM = `mean(d)/sqrt(lrv/T)` with **rectangular** truncation at `h-1` (`lrv = g0 + 2*sum_{k=1..h-1} g_k`; if `lrv<=0` fall back to `g0`). HLN correction: `stat = DM*sqrt((T+1-2h+h*(h-1)/T)/T)`, p from Student-t `df=T-1`. `alternative` ∈ {"greater","two-sided"}. Degenerate if `std(d)==0` or `T<10` → `nan, nan, True`.
- `clark_west(e_small, e_big, yhat_small, yhat_big, h=1) -> TestResult` — `f = e_small**2 - e_big**2 + (yhat_small - yhat_big)**2`; stat = `meanstats.nw_tstat(f, lag=h-1)`; one-sided normal p (`sf`).
- `gw_test(loss_base, loss_model, h=1) -> TestResult` — unconditional Giacomini-White: NW-t on `d` with lag `h-1`, two-sided normal p. (Valid under rolling/finite-memory schemes; documented in docstring.)

- [ ] **Step 1: failing tests**

```python
import numpy as np
from dieboldmariano import dm_test as ref_dm
from tradingagents.predlab import dm

def test_dm_matches_reference_package_h1():
    rng = np.random.default_rng(11)
    actual = rng.normal(0, 1, 300)
    p1 = actual + rng.normal(0, 1.0, 300)   # worse
    p2 = actual + rng.normal(0, 0.6, 300)   # better
    ours = dm.dm_test((actual - p1) ** 2, (actual - p2) ** 2, h=1, alternative="two-sided")
    ref_stat, ref_p = ref_dm(actual, p1, p2, one_sided=False)  # dieboldmariano API: V1 vs V2, MSE default, HLN on
    assert np.isclose(ours.stat, ref_stat, rtol=1e-4)
    assert np.isclose(ours.pvalue, ref_p, rtol=1e-3)

def test_dm_sign_convention_model_better_positive():
    base = np.full(200, 2.0); model = np.full(200, 1.0)
    base = base + np.random.default_rng(1).normal(0, .01, 200)
    r = dm.dm_test(base, model, h=1)
    assert r.stat > 0 and r.pvalue < 0.01

def test_dm_degenerate_identical_losses():
    l = np.ones(100)
    r = dm.dm_test(l, l.copy(), h=1)
    assert r.degenerate and np.isnan(r.stat)

def test_clark_west_nested_null_not_rejected_and_alt_rejected():
    rng = np.random.default_rng(5)
    y = rng.normal(0, 1, 800)                  # truly unpredictable
    yh_small = np.zeros(800)                   # RW/zero forecast (true model)
    yh_big = yh_small + rng.normal(0, 0.3, 800)  # nested bigger model = noise added
    r_null = dm.clark_west(y - yh_small, y - yh_big, yh_small, yh_big, h=1)
    assert r_null.pvalue > 0.01               # should NOT strongly reject under null
    x = rng.normal(0, 1, 800); y2 = 0.6 * x + rng.normal(0, 1, 800)
    r_alt = dm.clark_west(y2 - 0.0, y2 - 0.6 * x, np.zeros(800), 0.6 * x, h=1)
    assert r_alt.pvalue < 0.01                # genuine nested improvement detected

def test_gw_equals_nw_on_loss_diff():
    rng = np.random.default_rng(9)
    a, b = rng.normal(1, .2, 300), rng.normal(.8, .2, 300)
    from tradingagents.predlab import meanstats
    assert np.isclose(dm.gw_test(a, b, h=3).stat, meanstats.nw_tstat(a - b, lag=2), rtol=1e-9)
```

- [ ] **Step 2: verify FAIL.** If the `dieboldmariano` API differs from the sketch (check its signature first: `from dieboldmariano import dm_test; help(dm_test)`), adapt the *test wrapper* — the reference values, not our API.
- [ ] **Step 3-5:** implement → PASS → commit `feat(predlab): DM-HLN, Clark-West, Giacomini-White forecast tests`.

---

### Task 5: Direction tests — Pesaran-Timmermann + calibration

**Files:**
- Create: `tradingagents/predlab/direction.py`, `tests/predlab/test_direction.py`

**Interfaces:**
- `pt_test(y_sign: np.ndarray, x_sign: np.ndarray) -> TestResult` (bool/± arrays accepted; internally `y = (y>0)`, `x = (x>0)`), Pesaran-Timmermann 1992:
  - `py=mean(y); px=mean(x); phat=mean(y==x); pstar=py*px+(1-py)*(1-px)`
  - `v_p=pstar*(1-pstar)/n`
  - `v_ps=((2*py-1)**2*px*(1-px) + (2*px-1)**2*py*(1-py) + 4*py*px*(1-py)*(1-px)/n)/n`
  - `stat=(phat-pstar)/sqrt(v_p-v_ps)`, one-sided normal p. Degenerate (flag, nan) if `px in {0,1}` or `py in {0,1}` or `v_p-v_ps<=0` — constant-sign forecasts are NOT scoreable by PT (RESEARCH.md §2).
- `hit_rate_vs_base(y_sign, x_sign) -> dict` — `{"acc": phat, "base_rate": max(py, 1-py), "edge_pp": (phat - max(py,1-py))*100}` (gate is vs class base rate, never 0.5).
- `brier_skill(p_up, y_up, p_clim) -> float` — `1 - brier(p_up,y_up).mean()/brier(p_clim,y_up).mean()` (positive = beats climatology; climatology = expanding base rate supplied by caller).

- [ ] **Step 1: failing tests**

```python
import numpy as np
from tradingagents.predlab import direction

def test_pt_size_under_independence():
    rng = np.random.default_rng(2)
    rejections = 0
    for i in range(400):
        y = rng.normal(size=250) > 0
        x = rng.normal(size=250) > 0
        r = direction.pt_test(y, x)
        if (not r.degenerate) and r.pvalue < 0.05:
            rejections += 1
    assert 0.02 < rejections / 400 < 0.09   # ~5% size under the null

def test_pt_power_on_informative_signal():
    rng = np.random.default_rng(3)
    lat = rng.normal(size=2000)
    y = (lat + rng.normal(0, 1.2, 2000)) > 0
    x = lat > 0
    r = direction.pt_test(y, x)
    assert r.pvalue < 1e-6 and r.stat > 5

def test_pt_degenerate_constant_forecast():
    y = np.random.default_rng(4).normal(size=100) > 0
    r = direction.pt_test(y, np.ones(100, dtype=bool))
    assert r.degenerate

def test_hit_rate_base_rate_guard():
    y = np.array([1, 1, 1, 1, -1])   # base rate 0.8
    x = np.ones(5)
    out = direction.hit_rate_vs_base(y, x)
    assert np.isclose(out["acc"], 0.8) and np.isclose(out["base_rate"], 0.8) and np.isclose(out["edge_pp"], 0.0)
```

- [ ] **Step 2-5:** FAIL → implement → PASS → commit `feat(predlab): Pesaran-Timmermann and direction/calibration metrics`.

---

### Task 6: 5-minute kline fetcher + fetch run

**Files:**
- Create: `scripts/predlab_fetch_klines_5m.py` (adapted copy of `scripts/fetch_xsect_klines_1h.py` — same Vision-monthly-zip + FAPI-tail + `merge_tail` idempotent structure)
- Create: `tests/predlab/test_fetch_5m.py`
- Output data: `data/predlab/klines_5m/{SYMBOL}.parquet`, manifest `data/predlab/klines_5m_manifest.json`

**Interfaces:**
- Constants: `INTERVAL = "5m"`, `SYMBOLS = ["BTCUSDT", "ETHUSDT"]`, `START_MONTH = "2020-01"`, `OUT_DIR = data/predlab/klines_5m` (respect `TRADINGAGENTS_DATA_ROOT`).
- Persisted columns (superset of the 1h store — keep taker + trade count): `open, high, low, close, volume, quote_volume, taker_buy_quote_volume, n_trades, ts` (`ts` int64 ms, bar OPEN time, UTC).
- Produces for Task 7: `load_5m(symbol) -> pd.DataFrame` helper in the script importable via `scripts` path (Task 7 re-reads the parquet directly; only the file format is the contract).

- [ ] **Step 1: failing unit tests** (pure functions only; network behind the house `online` marker):

```python
import pandas as pd
from predlab_fetch_klines_5m import month_zip_url, merge_tail  # sys.path scripts/ pattern used by existing tests

def test_month_zip_url():
    assert month_zip_url("BTCUSDT", "2021-03") == (
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        "BTCUSDT/5m/BTCUSDT-5m-2021-03.zip")

def test_merge_tail_idempotent_and_sorted():
    old = pd.DataFrame({"ts": [0, 300000], "close": [1.0, 2.0]})
    new = pd.DataFrame({"ts": [300000, 600000], "close": [2.5, 3.0]})
    out = merge_tail(old, new)
    assert list(out["ts"]) == [0, 300000, 600000]
    assert out.loc[out.ts == 300000, "close"].item() == 2.5   # new wins on overlap
    again = merge_tail(out, new)
    assert len(again) == 3
```

- [ ] **Step 2: verify FAIL**, **Step 3: implement** (copy template, change constants, keep `n_trades` in `OUT_COLUMNS`, keep µs/ms epoch normalization + `trim_trailing_zero_volume`), **Step 4: PASS + commit** `feat(predlab): 5m kline fetcher (Vision bulk + FAPI tail)`.
- [ ] **Step 5: run the fetch in background** — `uv run python scripts/predlab_fetch_klines_5m.py` (≈ 79 months × 2 symbols of monthly zips; expect ~600–700k rows/symbol). While it runs, the loop may proceed to Task 8 (registry) which needs no data; Task 7 waits for completion. Verify afterwards: manifest rows ≥ 650,000 per symbol, first ts ≤ 2020-01-02, last ts ≥ 2026-07-01, no duplicate `ts`, gaps report printed (months with < 95% expected bars listed with honest denominators).

---

### Task 7: Realized-volatility store builder

**Files:**
- Create: `tradingagents/predlab/rv.py`, `tests/predlab/test_rv.py`, `scripts/predlab_build_rv.py`
- Output data: `data/predlab/rv_1h/{SYMBOL}.parquet`, `data/predlab/rv_1d/{SYMBOL}.parquet`

**Interfaces:**
- `aggregate_rv(df_5m: pd.DataFrame, freq: str) -> pd.DataFrame` with `freq in {"1h","1d"}`; input needs `ts, open, high, low, close, quote_volume, taker_buy_quote_volume, n_trades`. Per period (UTC boundaries, labeled by period START, containing only bars whose open time falls inside the period):
  - `r_i = log(close_i) - log(close_{i-1})` computed within period from the 5m closes plus the previous bar's close as the seed (first period of a symbol drops)
  - `rv = sum(r_i**2)`; `bv = (pi/2) * sum(abs(r_i)*abs(r_{i-1}))` (within period); `rq = (n/3) * sum(r_i**4)`
  - `n_bars` (honest denominator; expected 12 per 1h, 288 per 1d), `quote_volume` sum, `taker_buy_quote_volume` sum, `n_trades` sum, `park = (log(high_period/low_period))**2 / (4*log(2))` from period-aggregated H/L, `ret = log(close_last/close_first_seed)` (the period log-return, becomes T1/T2 target series)
  - completeness rule: rows with `n_bars < 0.8 * expected` get `rv = nan` (kept, flagged via `n_bars`)
- CLI `scripts/predlab_build_rv.py --symbols BTCUSDT ETHUSDT` reads the 5m store, writes both frequencies, prints coverage: total periods, nan-RV periods, first/last date.

**Sanity/forensics inside tests (charter §5):**

- [ ] **Step 1: failing tests**

```python
import numpy as np, pandas as pd
from tradingagents.predlab import rv

def _synth_5m(n_days=30, sigma_daily=0.02, seed=0):
    rng = np.random.default_rng(seed)
    n = n_days * 288
    r = rng.normal(0, sigma_daily / np.sqrt(288), n)
    close = 100 * np.exp(np.cumsum(r))
    ts = (pd.date_range("2024-01-01", periods=n, freq="5min", tz="UTC").view("int64") // 10**6)
    return pd.DataFrame({"ts": ts, "open": close, "high": close * 1.0001, "low": close * 0.9999,
                         "close": close, "quote_volume": 1.0, "taker_buy_quote_volume": 0.5,
                         "n_trades": 10})

def test_rv_recovers_known_daily_variance():
    df = rv.aggregate_rv(_synth_5m(200, sigma_daily=0.02), "1d")
    est = np.nanmedian(df["rv"])
    assert 0.7 * 0.02**2 < est < 1.3 * 0.02**2

def test_constant_price_zero_rv():
    d = _synth_5m(5); d["close"] = 100.0; d["open"] = 100.0
    out = rv.aggregate_rv(d, "1d")
    assert np.allclose(out["rv"].dropna(), 0.0)

def test_period_isolation_no_lookahead():
    # mutate the LAST day only; all earlier daily rows must be bit-identical
    a = _synth_5m(10, seed=1); b = a.copy()
    b.loc[b.index[-288:], "close"] *= 1.5
    ra, rb = rv.aggregate_rv(a, "1d"), rv.aggregate_rv(b, "1d")
    pd.testing.assert_frame_equal(ra.iloc[:-1], rb.iloc[:-1])

def test_incomplete_period_flagged():
    d = _synth_5m(3).iloc[:-200]          # last day incomplete
    out = rv.aggregate_rv(d, "1d")
    assert np.isnan(out["rv"].iloc[-1]) and out["n_bars"].iloc[-1] < 230
```

- [ ] **Step 2-4:** FAIL → implement → PASS.
- [ ] **Step 5: build real stores** (requires Task 6 fetch finished): `uv run python scripts/predlab_build_rv.py --symbols BTCUSDT ETHUSDT`. Sanity per charter: median annualized `sqrt(365*rv_1d)` for BTC in 2021 between 0.5 and 1.2; ratio RV-vol / close-to-close-vol (21d windows) between 0.7 and 1.3 for >80% of windows. Record numbers in the task report. Commit `feat(predlab): realized-vol stores (1h/1d) from 5m bars`.

---

### Task 8: Registry — gates, ledger, dev-window guard + Phase-1 registration

**Files:**
- Create: `tradingagents/predlab/registry.py`, `tests/predlab/test_registry.py`, `tests/predlab/test_p1_registration.py`
- Create data: `data/predlab/gates.json` (via a small `scripts/predlab_register_p1.py` writer), empty `data/predlab/trial_ledger.jsonl`

**Interfaces:**
- Constants: `HOLDOUT_START = "2025-04-01"`, `MAX_LOAD_END = "2025-03-31"`, `GATES = data/predlab/gates.json`, `LEDGER = data/predlab/trial_ledger.jsonl` (both under `TRADINGAGENTS_DATA_ROOT` if set).
- `assert_dev_window(end_date: str, allow_holdout: bool = False) -> None` — raises `RuntimeError` if `end_date >= HOLDOUT_START` and not allowed (mirror of `tradingagents/rebuild/ledger.py` semantics, predlab paths).
- `log_trial(experiment: str, cell: str, model: str, config: dict, window: tuple[str, str], metrics: dict) -> dict` — appends one JSON line `{ts_utc, experiment, cell, model, config, config_hash (sha256 of canonical-json config, first 12 hex), git_commit (rev-parse --short HEAD), window, metrics}`; returns the row.
- `trial_count(experiment: str | None = None) -> int` — unique `config_hash` count (ledger-wide when None).
- `load_gates() -> dict`, `get_experiment(key) -> dict`.
- Registration content (`predlab_p1_classical` key) written by `scripts/predlab_register_p1.py`, **frozen before any battery result**:
  - `dev_window: ["2021-01-01","2025-03-31"]`, `holdout_window: ["2025-04-01","2026-07-01"]`, `holdout_status: "sealed"`, `spec: "docs/superpowers/specs/2026-07-30-prediction-lab-charter-design.md"`
  - `cells`: cross of `symbols ["BTCUSDT","ETHUSDT"]` × `horizons ["1h","24h","7d"]` × `targets ["T1_ret","T2_dir","T3_rv","T4_vol"]` plus `["T6_funding@8h","T6_funding@24h"] × symbols` (28 cells), each with `strong_baseline` field: T1→`"rw_zero"`, T2→`"base_rate"`, T3→`"har_rv"`, T4→`"seasonal_naive"`, T6→`"ar1"`.
  - `effect_floors` (charter §5 verbatim): `{"T1_oos_r2": {"1h": 0.002, "24h": 0.005, "7d": 0.01}, "T2_edge_pp": 2.0, "T2_auc_ci_excludes": 0.5, "T3_dqlike": 0.02, "T4_dmase": 0.05, "T6_dmse": 0.05, "T7_ic": 0.02, "T7_nw_t": 3.0}`
  - `tests`: `{"primary": "dm_hln_p<0.05", "nested": "clark_west", "direction": "pesaran_timmermann", "multiplicity_within_cell": "spa_mcs_phase5", "across_cells": "bh_fdr_q0.10"}`
  - `protocol`: `{"scheme": "rolling_origin_expanding", "step": {"1h": 1, "24h": 1, "7d": 1}, "embargo": 0, "purge": "= horizon (built into splitter)", "refit_every": {"cheap": 1, "arima_ets_garch": {"24h": 5, "1h": 24, "7d": 5}}, "min_train": {"24h": 365, "1h": 2160, "7d": 365}, "loss": {"T1": "se", "T2": "brier", "T3": "qlike", "T4": "mase", "T6": "se"}}`
  - `model_grids` (Tier-1, registered): `arima_orders [[1,0,0],[0,0,1],[1,0,1],[2,0,2]] selected by in-train AIC`, `ets ["ANN","AAN"]`, `garch ["garch11","egarch11","gjr11"] dist normal, zero-mean on returns`, `har ["har_levels","log_har","harq"]`, `ewma_lambda 0.94 fixed`, `seasonal_ar volume: m=24 (1h) / m=7 (24h)`, `funding ["ar1","dar1"]`, `t2 ["logit_lags5"]`
  - `stop_rule`: "no post-hoc grid additions; amendments only before the affected cell's first result and declared in this file; NEGATIVE cells close without retry; holdout untouched until Phase-5 champions"
- Registration test `test_p1_registration.py` asserts all of the above fields exist with exactly these values (house pattern `tests/xsect/test_value_unlock_registration.py`).

- [ ] **Step 1: failing tests** for `registry.py` (tmp_path via `TRADINGAGENTS_DATA_ROOT` monkeypatch):

```python
import json, pytest
from tradingagents.predlab import registry

def test_assert_dev_window_blocks_holdout(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path))
    registry.assert_dev_window("2025-03-31")            # ok
    with pytest.raises(RuntimeError):
        registry.assert_dev_window("2025-04-01")
    registry.assert_dev_window("2026-01-01", allow_holdout=True)  # explicit only

def test_log_trial_appends_hash_and_commit(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path))
    row = registry.log_trial("predlab_p1_classical", "BTCUSDT|24h|T3_rv", "har_levels",
                             {"a": 1}, ("2021-01-01", "2025-03-31"), {"qlike": 0.31})
    assert len(row["config_hash"]) == 12 and row["git_commit"]
    row2 = registry.log_trial("predlab_p1_classical", "c", "m", {"a": 2}, ("x", "y"), {})
    assert registry.trial_count() == 2
    assert registry.trial_count("predlab_p1_classical") == 2
```

- [ ] **Step 2-4:** FAIL → implement → PASS.
- [ ] **Step 5: write `scripts/predlab_register_p1.py`, run it**, write `tests/predlab/test_p1_registration.py` asserting the frozen content, all green. Commit `feat(predlab): registry + Phase-1 pre-registration (28 cells, floors, grids frozen)`.

---

### Task 9: Baselines, cell runner, leakage canary probe

**Files:**
- Create: `tradingagents/predlab/baselines.py`, `tradingagents/predlab/runner.py`, `tests/predlab/test_runner.py`, `scripts/predlab_probes.py`

**Interfaces:**
- Forecaster protocol (duck-typed, consumed by every tier): `class Forecaster: name: str; def fit(self, y_train: np.ndarray, X_train: np.ndarray | None) -> None; def predict(self, y_hist: np.ndarray, x_now: np.ndarray | None) -> float` — one value per origin: point forecast of `y[t]` (T1/T4/T6: level of target; T3: **variance**; T2: probability of up).
- `baselines.py` classes (all cheap, refit every origin): `RWZero` (0.0), `HistMean` (expanding mean), `Persistence` (last y), `SeasonalNaive(m)` (y[t-m]), `EWMA(lam=0.94)` (variance recursion on the *target* series for T3; on levels for T4), `Climatology` (expanding mean by season bin: hour-of-day for 1h cells, day-of-week for 24h/7d), `BaseRate` (T2: expanding share of up).
- `runner.run_cell(cell: dict, series: pd.DataFrame, models: list[Forecaster], gates_key: str, tier: str, dry: bool = False) -> pd.DataFrame`:
  - `series` indexed by UTC timestamp with columns `y` (target aligned per Task-2 convention: `y[t]` realized over `(t, t+h]`) and optional exog; runner calls `registry.assert_dev_window` on the last timestamp, builds splits via `rolling_origin` with the registered `min_train/step/refit` for the cell, collects per-origin forecasts for every model, computes the registered loss vs `y`, runs `dm_test`/`clark_west`/`pt_test` vs the cell's `strong_baseline` model, writes `data/predlab/forecasts/{gates_key}/{cell}/{model}.parquet` + a result card JSON `data/predlab/cards/{gates_key}/{cell}.json` `{cell, n_origins, per_model: {name: {loss_mean, vs_baseline: {dm_stat, dm_p, cw_p, pt_p}, degenerate}}, sub_periods: {"2021-2022": .., "2023-2024": .., "2025Q1": ..}}`, and one `registry.log_trial` row per model. `dry=True` skips writes (used by tests).
- `scripts/predlab_probes.py` — pre-battery plumbing gates (charter §7): (P0) timestamp reconciliation: recompute 3 sampled days of BTC daily RV directly from raw 5m parquet with an independent 10-line pandas groupby and assert equality to the store within 1e-12; assert `ts` strictly increasing, tz-naive int ms, no bar with open time ≥ period label + period; (P-canary) run `run_cell` on the real BTC|24h|T3 series with a deliberately leaky model (`predict` returns `y[t]` + tiny noise) and assert it beats HAR by DM p < 1e-6 — proving the harness *would* expose leakage; write `data/predlab/probes_p1.json` with both results.

- [ ] **Step 1: failing tests** (synthetic end-to-end):

```python
import numpy as np, pandas as pd
from tradingagents.predlab import baselines, runner

def _cell():
    return {"cell": "SYN|24h|T1_ret", "target": "T1_ret", "horizon_bars": 1,
            "strong_baseline": "rw_zero", "loss": "se",
            "min_train": 100, "step": 1, "refit_every": 1}

def _series(n=600, phi=0.4, seed=0):
    rng = np.random.default_rng(seed)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = phi * y[t - 1] + rng.normal(0, 1)
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    return pd.DataFrame({"y": y}, index=idx)

class _AR1(baselines.Forecaster):
    name = "ar1_true"
    def fit(self, y, X=None): self.phi = 0.4
    def predict(self, y_hist, x_now=None): return self.phi * y_hist[-1]

def test_runner_detects_planted_predictability():
    out = runner.run_cell(_cell(), _series(), [baselines.RWZero(), _AR1()],
                          gates_key="predlab_p1_classical", tier="t0", dry=True)
    ar = out[out.model == "ar1_true"].iloc[0]
    assert ar["dm_p"] < 0.01 and ar["loss_mean"] < out[out.model == "rw_zero"].iloc[0]["loss_mean"]

def test_runner_no_skill_on_white_noise():
    s = _series(phi=0.0, seed=1)
    out = runner.run_cell(_cell(), s, [baselines.RWZero(), baselines.Persistence()],
                          gates_key="predlab_p1_classical", tier="t0", dry=True)
    assert out[out.model == "persistence"].iloc[0]["dm_p"] > 0.05  # persistence must NOT beat RW on white noise

def test_runner_refuses_holdout_dates():
    import pytest
    s = _series(n=1700)  # runs past 2025-04-01 from 2021-01-01 daily
    with pytest.raises(RuntimeError):
        runner.run_cell(_cell(), s, [baselines.RWZero()], gates_key="predlab_p1_classical", tier="t0", dry=True)
```

- [ ] **Step 2-4:** FAIL → implement → PASS (runner returns a tidy DataFrame, one row per model, columns `model, loss_mean, dm_stat, dm_p, cw_p, pt_p, degenerate, n_origins`).
- [ ] **Step 5: run probes** — `uv run python scripts/predlab_probes.py` on the real stores; both must PASS (else STOP per charter §7 and fix plumbing first). Commit `feat(predlab): baselines, cell runner, plumbing+canary probes PASS`.

---

### Task 10: Tier-0 battery run (P1-04)

**Files:**
- Create: `scripts/predlab_run_battery.py` (CLI: `--gates-key predlab_p1_classical --tier t0 --cells all|<pattern>`), `docs/predlab/reports/p1_tier0.md`

**Interfaces:**
- Builds each cell's `series` from the stores: T1/T2 from `rv_1{h,d}` `ret` column (7d = 7-day non-overlapping... **no — registered: 7d uses daily store with h=7 overlapping origins, step 1, HAC lag 6 in tests**); T3 `rv`; T4 `log(quote_volume)`; T6 from `data/xsect/funding/{SYM}.parquet` (8h prints; 24h = rolling sum of 3 prints). All loaders clip at `MAX_LOAD_END`.
- Tier-0 model set per target: T1 {rw_zero, hist_mean, persistence}; T2 {base_rate}; T3 {ewma, persistence, hist_mean}; T4 {seasonal_naive(m), persistence, hist_mean, climatology}; T6 {persistence, hist_mean}.

- [ ] **Step 1:** implement CLI (thin over `runner.run_cell`), run `--tier t0 --cells all` (28 cells; minutes, all closed-form).
- [ ] **Step 2:** verify every cell wrote a card + forecasts parquet + ledger rows; no gate evaluation (baselines ARE the null).
- [ ] **Step 3:** write `docs/predlab/reports/p1_tier0.md` — per-cell baseline loss table (this is the reference table every later tier is compared against), coverage stats, any degenerate flags.
- [ ] **Step 4:** commit `exp(predlab): Tier-0 baseline battery, 28 cells ledgered`.

---

### Task 11: Tier-1 daily battery — T1 returns + T2 direction

**Files:**
- Create: `tradingagents/predlab/tier1.py` (ARIMA/ETS/logit wrappers), `tests/predlab/test_tier1.py`
- Modify: `scripts/predlab_run_battery.py` (add `--tier t1_t1t2_24h`)

**Interfaces:**
- `ArimaForecaster(orders=[(1,0,0),(0,0,1),(1,0,1),(2,0,2)], refit_every=5)` — statsmodels SARIMAX on the y series (returns), order chosen by in-train AIC at each refit, `predict` = 1-step (h-step for 7d cells via `direct` target aggregation — the runner feeds the h-aggregated y, so wrappers stay 1-step. Iterated variant Task 14 only).
- `EtsForecaster(kind="ANN"|"AAN", refit_every=5)` — statsmodels ETSModel.
- `LogitLags(n_lags=5, refit_every=5)` — sklearn LogisticRegression on sign of last 5 y-lags, outputs P(up) (T2 cells; scored by Brier + PT on thresholded 0.5).
- Tests: each wrapper on the Task-9 synthetic AR(1) beats RWZero (DM p < 0.05); wrapper never sees `y[t]` at origin t (mutation test: replacing future y with NaN changes nothing — assert identical forecasts).

- [ ] **Step 1-3:** TDD wrappers (FAIL → implement → PASS).
- [ ] **Step 4:** run daily T1/T2 cells for BTC+ETH (`--tier t1_t1t2_24h`); per registered protocol; cards updated with Tier-1 rows vs Tier-0 baselines; CW used vs nested rw_zero; PT + `hit_rate_vs_base` + Brier-skill for T2.
- [ ] **Step 5:** **forensic pass per charter** (expected result per RESEARCH.md is ≈ no skill: if any T1 model beats RW with DM p < 0.05, run shuffled-target kill-test + train-on-future canary on that cell before recording; if ALL models degenerate, probe harness). Append findings to `docs/predlab/reports/p1_tier1_t1t2.md`. Commit `exp(predlab): Tier-1 daily returns/direction battery`.

---

### Task 12: Tier-1 daily battery — T3 volatility (the high-prior target)

**Files:**
- Create: `tradingagents/predlab/har.py` (HAR family), extend `tier1.py` (GARCH), `tests/predlab/test_har.py`
- Modify: `scripts/predlab_run_battery.py` (add `--tier t1_t3_24h`)

**Interfaces:**
- `HarForecaster(kind="har_levels"|"log_har"|"harq", refit_every=1)` — OLS: `rv[t] ~ rv[t-1] + mean(rv[t-5..t-1]) + mean(rv[t-22..t-1])` (daily); `log_har` on `log(rv)` with smearing-free naive `exp` back-transform (documented bias, secondary variant); `harq` adds `sqrt(rq[t-1])*rv[t-1]` term (Bollerslev-Patton-Quaedvlieg). 1h cells use lags (1, 24, 168).
- `GarchForecaster(kind="garch11"|"egarch11"|"gjr11", refit_every=5)` — `arch` on percent log-returns (`y*100`, zero-mean), forecast next-period **variance** rescaled back (`/100**2`); for h-aggregated cells, sum of per-step variance forecasts (arch `forecast(horizon=h).variance` row-sum).
- All T3 forecasts in variance units; runner scores QLIKE (primary) + MSE-of-log (secondary column in card).
- Tests: HAR on synthetic AR(1)-in-RV recovers coefficients (rtol 0.15) and beats EWMA by QLIKE with DM p < 0.05; GARCH wrapper on simulated GARCH(1,1) data (arch `SimulatedData`) beats HistMean; forecast-at-origin mutation test (future rows NaN’d → identical).

- [ ] **Step 1-3:** TDD (FAIL → implement → PASS).
- [ ] **Step 4:** run daily T3 cells (BTC, ETH): ladder EWMA → GARCH family → HAR family; DM vs **HAR-levels** (the registered strong baseline) AND vs EWMA (weak ref, reported not gated); sub-period table.
- [ ] **Step 5:** forensics: literature says HAR must beat EWMA decisively here — if it does NOT, treat as harness bug and probe before recording (charter §5 inverse rule). Report `docs/predlab/reports/p1_tier1_t3.md`. Commit `exp(predlab): Tier-1 daily volatility battery (GARCH/HAR ladder)`.

---

### Task 13: Tier-1 daily battery — T4 volume + T6 funding

**Files:**
- Extend: `tier1.py` (`SeasonalAR`, `Ar1`, `Dar1`), `tests/predlab/test_tier1_vol_funding.py`
- Modify: `scripts/predlab_run_battery.py` (add `--tier t1_t4t6`)

**Interfaces:**
- `SeasonalAR(m, n_lags=3, refit_every=1)` — OLS of `y[t]` on `y[t-1..t-3]` + `y[t-m]` (T4 on log dollar volume; m=7 daily, m=24 hourly).
- `Ar1(refit_every=1)` — OLS `y[t] ~ y[t-1]`; `Dar1(refit_every=5)` — double-AR: conditional mean AR(1) with AR(1) conditional variance via MLE (statsmodels GenericLikelihoodModel, ~40 LOC; RESEARCH.md T6 prior).
- Funding loader: `data/xsect/funding/{SYM}.parquet` → 8h series aligned to print times; 24h cell = sum of 3 consecutive prints (non-overlapping daily grid); clip at `MAX_LOAD_END`.
- Tests: SeasonalAR beats persistence on synthetic seasonal series (planted m-periodicity, DM p < 0.01); Ar1 recovers phi on AR(1) sim; funding loader alignment test (a print at 08:00 UTC belongs to origin 08:00, target = next print).

- [ ] **Step 1-3:** TDD → PASS.
- [ ] **Step 4:** run T4 (24h) + T6 (8h + 24h) cells for BTC/ETH vs registered baselines (T4 vs seasonal-naive by MASE; T6 vs AR(1) by MSE — note for T6 the *strong* baseline is AR(1) so Tier-1 asks whether DAR/richer beats it; persistence/no-change comparison reported from Tier-0).
- [ ] **Step 5:** forensics (volume must show strong seasonality — if seasonal-naive ties hist-mean, probe the loader's UTC alignment). Report `docs/predlab/reports/p1_tier1_t4t6.md`. Commit `exp(predlab): Tier-1 volume + funding battery`.

---

### Task 14: 1h-horizon and 7d-horizon batteries

**Files:**
- Modify: `scripts/predlab_run_battery.py` (add `--tier t1_1h`, `--tier t1_7d`)
- Create: `tests/predlab/test_iterated.py` (iterated-forecast helper test)

**Interfaces:**
- 1h cells: same model sets on hourly stores; `min_train=2160` (90 days), ARIMA/GARCH `refit_every=24`; runner's DM already uses `h`-aware HAC — for 1h step-1 forecasts h=1 in bars.
- 7d cells: **direct** = models on 7-day-aggregated targets built from daily store with step 1 (overlapping): `y7[t] = sum(ret[t+1..t+7])` for T1 (and RV sum for T3, log of 7d dollar volume for T4); DM/CW/GW run with `h=7` (HAC lag 6). **Iterated** (T1 ARIMA only): roll 1-step model 7 times feeding predictions back; helper `iterate_forecast(model, y_hist, h) -> float` with test on deterministic AR(1) (`phi=0.5, y_T=1.0` → iterated 7-step sum forecast = `sum(phi**k for k=1..7)` ≈ 0.9921875).
- Both registered already in gates (`horizons` includes them); no new registration.

- [ ] **Step 1:** TDD `iterate_forecast` (exact expected value above) → PASS.
- [ ] **Step 2:** run `--tier t1_1h` (T1/T2/T3/T4 × BTC/ETH hourly; slowest battery — run with `nohup uv run python ... &` and poll; idempotent per-cell skip via existing card check).
- [ ] **Step 3:** run `--tier t1_7d`.
- [ ] **Step 4:** forensics on any PASS (kill-tests) / suspicious NEGATIVE (probe). Reports `p1_tier1_1h.md`, `p1_tier1_7d.md`. Commit `exp(predlab): Tier-1 1h + 7d batteries`.

---

### Task 15: Phase-1 map, FDR roll-up, thesis section, memory milestone

**Files:**
- Create: `scripts/predlab_p1_rollup.py`, `docs/predlab/reports/phase1_map.md`
- Modify: `THESIS_FINDINGS.md` (append `## Section 54: Prediction Lab Phase 1 — Classical Predictability Map (2026-XX-XX)`), `docs/predlab/STATE.md`, `docs/predlab/BACKLOG.md`
- Memory: `/home/malecada/.claude/projects/-home-malecada-master-thesis/memory/predlab_status.md`

**Interfaces:**
- Roll-up reads all cards for `predlab_p1_classical`: per cell take champion model (best registered loss), collect its DM p vs strong baseline → Benjamini-Hochberg at q=0.10 across the 28 cells → columns `cell, champion, loss_improvement_%, dm_p, fdr_pass, effect_floor_pass, subperiod_stable (≥2/3 right-signed)`. Map table sorted by target then horizon. Explicit verdict line per cell: `SKILL-CANDIDATE` (all dev criteria U1–U3+U5-dev pass; holdout deferred to Phase 5) / `PREDICTABLE-VS-WEAK-ONLY` / `NO-SKILL` / `DEGENERATE`.
- THESIS §54 in house format (`### 54.x` subsections + `### Artifacts` listing gates key, ledger row count, card paths, commit).

- [ ] **Step 1:** implement + run roll-up; verify FDR arithmetic by hand on the top-3 p-values in the report.
- [ ] **Step 2:** write `phase1_map.md` + THESIS §54 (numbers only from cards/ledger — no narrative claims beyond verdict lines).
- [ ] **Step 3:** update STATE.md (Phase 1 → complete; next = P2-01), tick BACKLOG P1 items.
- [ ] **Step 4:** memory milestone — write `predlab_status.md` (map headline: which cells are SKILL-CANDIDATE / counts per verdict) + confirm MEMORY.md pointer intact.
- [ ] **Step 5:** commit `docs(predlab): Phase-1 predictability map + THESIS Section 54`.

---

## Self-review (done at write time)

- **Spec coverage:** charter §3 initial battery = 28 cells → Tasks 8 (registration), 10–14 (runs), 15 (map+FDR). §5 protocol pieces: losses (T1), splitter (T2), NW/bootstrap (T3), DM/CW/GW (T4), PT/calibration (T5), ledger/gates/probes (T8–9), forensic rules embedded in Tasks 9, 11–14 Step-5s. T5-range target intentionally deferred (charter: battery subset excludes T5; park column still built in Task 7 for later). T7 XS is Phase 2 (P2-04) — matches charter initial battery which lists T7 at 24h/7d: **amendment note:** T7 cells registered in Phase-2 registration, not `predlab_p1_classical`; recorded here so the deviation is visible before any result exists.
- **Placeholder scan:** no TBDs; every stats function has formula + reference test; battery tasks name exact model sets, baselines, loaders, clip rule.
- **Type consistency:** `Forecaster.predict(y_hist, x_now) -> float` consumed by runner (T9) and implemented by baselines (T9), tier1 (T11–13), har (T12); `TestResult` produced by dm.py (T4) and direction.py (T5), consumed by runner cards; `rolling_origin` signature identical in T2 tests and T9 runner usage.
