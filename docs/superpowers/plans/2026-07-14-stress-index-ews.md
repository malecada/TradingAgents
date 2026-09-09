# Positioning Stress Index / Early-Warning System (D2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and evaluate a positioning-based crash early-warning index (funding + OI + liquidations + optional F&G) with pre-registered detection gates, dev-window selection, and a locked-holdout one-shot — deliverable is detection metrics + de-risk overlay value, thesis-defensible at any sign.

**Architecture:** New `tradingagents/stress/` package (4 small modules: index, episodes, detection, overlay) reading the existing PIT stores (`data/derivatives/{coin}.parquet`, `data/sentiment/fng/fng.parquet`), evaluated by two runner scripts that log every config to the existing rebuild trial ledger. House methodology: gates registered in `data/rebuild/gates.json` BEFORE any experiment; dev window bounded by `assert_dev_window`; holdout touched exactly once.

**Tech Stack:** Python 3.13 (`.venv/bin/python`), pandas, numpy, pytest; existing `tradingagents/rebuild/ledger.py` (log_trial / assert_dev_window / trial_count).

## Global Constraints

- Branch: `feature/stress-index-ews` off `rebuild/honest-2026-07`.
- Causality: every index value dated D uses only data with `ts ≤ D-1` (shift(1) before z-scoring). No same-bar usage — this is the C1 lesson.
- Dev window: **2021-11-01 → 2025-03-31** (funding_rate coverage starts 2021-11-01). Holdout: **2025-04-01 → data end** (≥ 2026-05-10; refresh attempted in Task 6). Same split as the honest rebuild.
- Coins: bitcoin, ethereum (equal-weight portfolio where applicable).
- Pre-registered config grid: exactly 9 configs (3 component sets × 3 thresholds — see Task 0). No config added after Task 5 starts. Every evaluated config → `log_trial(experiment="stress_ews", ...)`.
- Holdout: single execution with `allow_holdout=True`, no re-runs regardless of outcome (`one_shot_rule`).
- Tests run with: `.venv/bin/python -m pytest tests/<file> -v` from repo root `/home/malecada/master_thesis/TradingAgents`.
- All commits on the feature branch; conventional-commit messages.

---

### Task 0: Pre-registration — gates, grid, episode definition (NO experiment code yet)

**Files:**
- Modify: `data/rebuild/gates.json` (add `stress_ews` key)
- Create: `docs/superpowers/specs/2026-07-14-stress-ews-prereg.md`

**Interfaces:**
- Produces: the frozen constants every later task must import/copy verbatim: episode rule, WARN rule, grid, gate thresholds.

- [ ] **Step 1: Create branch**

```bash
cd /home/malecada/master_thesis/TradingAgents
git checkout rebuild/honest-2026-07
git checkout -b feature/stress-index-ews
```

- [ ] **Step 2: Add `stress_ews` gate to `data/rebuild/gates.json`**

Add this key to the existing top-level JSON object (do not touch other keys):

```json
"stress_ews": {
  "registered": "2026-07-14",
  "dev_window": ["2021-11-01", "2025-03-31"],
  "holdout_window_start": "2025-04-01",
  "episode_rule": "crash day t: 10-day forward log-return of EW BTC+ETH close <= log(0.85); episode = maximal run of crash days, episodes separated by <10 non-crash days are merged; episode_start = first crash day",
  "warn_rule": "composite = mean(component z-scores, all lagged 1 day, z over trailing 365d window with min 180d); WARN active while composite >= k, released below k-0.25; components and k from grid",
  "grid": {
    "component_sets": [["z_fund", "z_oi"], ["z_fund", "z_oi", "z_liq"], ["z_fund", "z_oi", "z_liq", "z_fg"]],
    "k": [1.0, 1.5, 2.0]
  },
  "detection_window_days": 20,
  "dev_select": {
    "hit_rate_min": 0.5,
    "false_alarms_per_year_max": 6,
    "placebo_p_max": 0.05,
    "overlay_delta_maxdd_max": 0.0,
    "overlay_delta_sr_min": -0.10,
    "tiebreak": "lowest placebo_p, then most negative overlay_delta_maxdd"
  },
  "holdout_deploy": {
    "hit_rate_min": 0.5,
    "false_alarms_per_year_max": 6,
    "placebo_p_max": 0.05,
    "overlay_delta_maxdd_max": 0.0,
    "overlay_delta_sr_min": -0.10,
    "one_shot": true
  }
}
```

- [ ] **Step 3: Write the pre-registration spec doc**

Create `docs/superpowers/specs/2026-07-14-stress-ews-prereg.md` containing, verbatim: the gate JSON above; component definitions (below); the statement "Grid is closed at 9 configs; any config evaluated outside this grid voids the experiment"; and the evidence basis (BIS WP 1087 carry→sell-liquidation asymmetry; SENTIMENT_EARLY_WARNING_RESEARCH_2026-07-14.md D2).

Component definitions (frozen):

| component | formula (daily, per coin, then EW-averaged across BTC+ETH) |
|---|---|
| `z_fund` | z365(funding_rate_ma7) |
| `z_oi`   | z365(oi_close / oi_close.shift(30) − 1) |
| `z_liq`  | z365(liq_total_usd / oi_close) |
| `z_fg`   | z365(abs(fng_value − 50)) — portfolio-level, not per coin |

z365(x) = (x − rolling_mean(x, 365)) / rolling_std(x, 365), min_periods=180. Every input series is `.shift(1)` FIRST (value dated D is computed from data ≤ D−1).

- [ ] **Step 4: Commit (pre-registration timestamped before any experiment)**

```bash
git add data/rebuild/gates.json docs/superpowers/specs/2026-07-14-stress-ews-prereg.md
git commit -m "prereg(stress-ews): gates, 9-config grid, episode+warn rules frozen before experiments"
```

---

### Task 1: Component z-scores + composite index (`tradingagents/stress/index.py`)

**Files:**
- Create: `tradingagents/stress/__init__.py` (empty)
- Create: `tradingagents/stress/index.py`
- Test: `tests/test_stress_index.py`

**Interfaces:**
- Consumes: `data/derivatives/{coin}.parquet` (DatetimeIndex `ts`, cols `funding_rate_ma7`, `oi_close`, `liq_total_usd`), `data/sentiment/fng/fng.parquet` (cols `event_ts`, `value`).
- Produces:
  - `zscore_365(s: pd.Series) -> pd.Series` — rolling z, window 365, min_periods 180, input NOT shifted (caller shifts).
  - `build_components(coins: list[str], deriv_dir: Path, fng_path: Path) -> pd.DataFrame` — daily DatetimeIndex, columns exactly `["z_fund","z_oi","z_liq","z_fg"]`, each already causal (built from shift(1) inputs), per-coin components EW-averaged.
  - `composite_warn(components: pd.DataFrame, component_set: list[str], k: float) -> pd.DataFrame` — columns `composite` (mean of selected z cols, rows with any NaN in set → NaN) and `warn` (bool, hysteresis: turns on at composite ≥ k, stays on until composite < k−0.25).

- [ ] **Step 1: Write failing tests**

```python
# tests/test_stress_index.py
import numpy as np
import pandas as pd
import pytest
from tradingagents.stress.index import zscore_365, composite_warn


def _series(vals):
    idx = pd.date_range("2020-01-01", periods=len(vals), freq="D", tz="UTC")
    return pd.Series(vals, index=idx, dtype=float)


def test_zscore_needs_180_obs():
    s = _series(np.random.default_rng(0).normal(size=400))
    z = zscore_365(s)
    assert z.iloc[:179].isna().all()
    assert z.iloc[200:].notna().all()


def test_zscore_detects_shift():
    vals = [0.0] * 300 + [5.0] * 5
    z = zscore_365(_series(vals))
    assert z.iloc[-1] > 3  # 5-sigma-ish jump vs flat history


def test_composite_warn_hysteresis():
    idx = pd.date_range("2021-01-01", periods=6, freq="D", tz="UTC")
    comp = pd.DataFrame(
        {"z_fund": [0.0, 1.6, 1.4, 1.3, 1.1, 0.5],
         "z_oi":   [0.0, 1.6, 1.4, 1.3, 1.1, 0.5]},
        index=idx,
    )
    out = composite_warn(comp, ["z_fund", "z_oi"], k=1.5)
    # on at 1.6, stays on at 1.4 and 1.3 (>= k-0.25=1.25), off at 1.1
    assert out["warn"].tolist() == [False, True, True, True, False, False]


def test_composite_nan_when_component_missing():
    idx = pd.date_range("2021-01-01", periods=2, freq="D", tz="UTC")
    comp = pd.DataFrame({"z_fund": [1.0, np.nan], "z_oi": [1.0, 2.0]}, index=idx)
    out = composite_warn(comp, ["z_fund", "z_oi"], k=0.5)
    assert np.isnan(out["composite"].iloc[1])
    assert not out["warn"].iloc[1]
```

- [ ] **Step 2: Run tests, expect import failure**

Run: `.venv/bin/python -m pytest tests/test_stress_index.py -v`
Expected: FAIL / ERROR "No module named 'tradingagents.stress'"

- [ ] **Step 3: Implement**

```python
# tradingagents/stress/index.py
"""Positioning stress index — pre-registered spec docs/superpowers/specs/2026-07-14-stress-ews-prereg.md."""
from pathlib import Path

import numpy as np
import pandas as pd

COMPONENTS = ["z_fund", "z_oi", "z_liq", "z_fg"]


def zscore_365(s: pd.Series) -> pd.Series:
    mean = s.rolling(365, min_periods=180).mean()
    std = s.rolling(365, min_periods=180).std()
    return (s - mean) / std


def _coin_components(deriv_path: Path) -> pd.DataFrame:
    df = pd.read_parquet(deriv_path).sort_index()
    lag = df.shift(1)  # causal: value dated D uses data <= D-1
    out = pd.DataFrame(index=df.index)
    out["z_fund"] = zscore_365(lag["funding_rate_ma7"])
    out["z_oi"] = zscore_365(lag["oi_close"] / lag["oi_close"].shift(30) - 1.0)
    out["z_liq"] = zscore_365(lag["liq_total_usd"] / lag["oi_close"])
    return out


def _fng_component(fng_path: Path) -> pd.Series:
    fng = pd.read_parquet(fng_path)
    s = (
        fng.assign(d=pd.to_datetime(fng["event_ts"], utc=True).dt.normalize())
        .set_index("d")["value"]
        .astype(float)
        .sort_index()
    )
    s = s[~s.index.duplicated(keep="last")].shift(1)
    return zscore_365((s - 50.0).abs())


def build_components(coins: list[str], deriv_dir: Path, fng_path: Path) -> pd.DataFrame:
    per_coin = [_coin_components(Path(deriv_dir) / f"{c}.parquet") for c in coins]
    idx = per_coin[0].index
    for p in per_coin[1:]:
        idx = idx.union(p.index)
    ew = sum(p.reindex(idx) for p in per_coin) / len(per_coin)
    ew["z_fg"] = _fng_component(fng_path).reindex(idx)
    return ew


def composite_warn(components: pd.DataFrame, component_set: list[str], k: float) -> pd.DataFrame:
    sub = components[component_set]
    composite = sub.mean(axis=1).where(~sub.isna().any(axis=1))
    warn = np.zeros(len(composite), dtype=bool)
    active = False
    vals = composite.to_numpy()
    for i, v in enumerate(vals):
        if np.isnan(v):
            active = False
        elif active:
            active = v >= k - 0.25
        else:
            active = v >= k
        warn[i] = active
    return pd.DataFrame({"composite": composite, "warn": warn}, index=components.index)
```

Also create empty `tradingagents/stress/__init__.py`.

- [ ] **Step 4: Run tests, expect pass**

Run: `.venv/bin/python -m pytest tests/test_stress_index.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/stress/ tests/test_stress_index.py
git commit -m "feat(stress-ews): causal component z-scores + hysteresis composite WARN"
```

---

### Task 2: Episode catalog (`tradingagents/stress/episodes.py`)

**Files:**
- Create: `tradingagents/stress/episodes.py`
- Test: `tests/test_stress_episodes.py`

**Interfaces:**
- Consumes: EW BTC+ETH daily close series (caller builds it from the OHLCV cache the backtester already uses — for tests, synthetic).
- Produces: `build_episodes(close: pd.Series, drop: float = 0.15, horizon: int = 10, merge_gap: int = 10) -> pd.DataFrame` — one row per episode, columns `start` (Timestamp of first crash day), `end` (last crash day), `trough_ret` (min 10-day forward log-return inside the episode). Crash day t: `log(close[t+horizon] / close[t]) <= log(1 - drop)` (calendar reindexed to trading index positions).

- [ ] **Step 1: Write failing tests**

```python
# tests/test_stress_episodes.py
import numpy as np
import pandas as pd
from tradingagents.stress.episodes import build_episodes


def _close(vals):
    idx = pd.date_range("2022-01-01", periods=len(vals), freq="D", tz="UTC")
    return pd.Series(vals, index=idx, dtype=float)


def test_flat_series_no_episodes():
    eps = build_episodes(_close([100.0] * 100))
    assert len(eps) == 0


def test_single_crash_detected():
    vals = [100.0] * 30 + list(np.linspace(100, 70, 10)) + [70.0] * 30
    eps = build_episodes(_close(vals))
    assert len(eps) == 1
    # first day whose 10-day-forward return breaches -15% is before the fall completes
    assert eps.iloc[0]["start"] <= pd.Timestamp("2022-01-31", tz="UTC")


def test_nearby_crashes_merged():
    fall1 = list(np.linspace(100, 80, 8))
    fall2 = list(np.linspace(82, 60, 8))
    vals = [100.0] * 30 + fall1 + [80, 81, 82, 82, 82] + fall2 + [60.0] * 30
    eps = build_episodes(_close(vals), merge_gap=10)
    assert len(eps) == 1  # gap of 5 non-crash days < 10 -> merged
```

- [ ] **Step 2: Run tests, expect fail**

Run: `.venv/bin/python -m pytest tests/test_stress_episodes.py -v`
Expected: ERROR "cannot import name 'build_episodes'"

- [ ] **Step 3: Implement**

```python
# tradingagents/stress/episodes.py
"""Mechanical crash-episode catalog — rule frozen in gates.json['stress_ews']['episode_rule']."""
import numpy as np
import pandas as pd


def build_episodes(
    close: pd.Series, drop: float = 0.15, horizon: int = 10, merge_gap: int = 10
) -> pd.DataFrame:
    close = close.dropna().sort_index()
    fwd = np.log(close.shift(-horizon) / close)
    crash = fwd <= np.log(1.0 - drop)
    rows = []
    in_ep = False
    start = end = None
    gap = 0
    for ts, is_crash in crash.items():
        if is_crash:
            if not in_ep:
                in_ep, start = True, ts
            end, gap = ts, 0
        elif in_ep:
            gap += 1
            if gap >= merge_gap:
                rows.append((start, end))
                in_ep = False
    if in_ep:
        rows.append((start, end))
    return pd.DataFrame(
        [
            {"start": s, "end": e, "trough_ret": float(fwd.loc[s:e].min())}
            for s, e in rows
        ]
    )
```

- [ ] **Step 4: Run tests, expect pass**

Run: `.venv/bin/python -m pytest tests/test_stress_episodes.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/stress/episodes.py tests/test_stress_episodes.py
git commit -m "feat(stress-ews): mechanical crash-episode catalog (-15%/10d, merge<10d)"
```

---

### Task 3: Detection metrics + block-shuffle placebo (`tradingagents/stress/detection.py`)

**Files:**
- Create: `tradingagents/stress/detection.py`
- Test: `tests/test_stress_detection.py`

**Interfaces:**
- Consumes: `warn: pd.Series[bool]` (from Task 1), `episodes: pd.DataFrame` (from Task 2).
- Produces:
  - `detection_metrics(warn, episodes, window: int = 20) -> dict` with keys `hit_rate`, `n_episodes`, `n_hits`, `median_lead_days`, `false_alarm_clusters_per_year`, `n_warn_clusters`. Hit: any warn day in `[start-window, start-1]` (calendar days). Warn cluster: maximal run of consecutive warn days; false alarm: cluster with no episode start within `window` days after cluster start.
  - `placebo_pvalue(warn, episodes, n: int = 500, block: int = 21, seed: int = 0, window: int = 20) -> dict` with keys `p_hit_rate`, `placebo_hit_rates` (list). Stationary block bootstrap shuffle of the warn series (geometric block length mean `block`), p = (1 + #placebo hit_rate ≥ real) / (n + 1).

- [ ] **Step 1: Write failing tests**

```python
# tests/test_stress_detection.py
import numpy as np
import pandas as pd
from tradingagents.stress.detection import detection_metrics, placebo_pvalue


def _warn(days_on, n=200, start="2022-01-01"):
    idx = pd.date_range(start, periods=n, freq="D", tz="UTC")
    s = pd.Series(False, index=idx)
    s.iloc[days_on] = True
    return s


def _episodes(starts):
    return pd.DataFrame(
        {"start": [pd.Timestamp(s, tz="UTC") for s in starts],
         "end": [pd.Timestamp(s, tz="UTC") for s in starts],
         "trough_ret": [-0.2] * len(starts)}
    )


def test_perfect_hit():
    warn = _warn([40, 41, 42])  # 2022-02-10..12
    eps = _episodes(["2022-02-20"])  # start 8 days after last warn day
    m = detection_metrics(warn, eps)
    assert m["hit_rate"] == 1.0
    assert m["n_hits"] == 1
    assert m["median_lead_days"] == 10  # first warn 2022-02-10, start 2022-02-20


def test_miss_and_false_alarm():
    warn = _warn([100, 101])  # far from episode
    eps = _episodes(["2022-02-01"])
    m = detection_metrics(warn, eps)
    assert m["hit_rate"] == 0.0
    assert m["n_warn_clusters"] == 1
    assert m["false_alarm_clusters_per_year"] > 0


def test_placebo_p_not_significant_for_random_warn():
    rng = np.random.default_rng(1)
    warn = _warn(list(rng.choice(500, 30, replace=False)), n=520)
    eps = _episodes(["2022-06-01", "2023-01-15"])
    p = placebo_pvalue(warn, eps, n=99, seed=2)
    assert 0.0 < p["p_hit_rate"] <= 1.0
```

- [ ] **Step 2: Run tests, expect fail**

Run: `.venv/bin/python -m pytest tests/test_stress_detection.py -v`
Expected: ERROR "No module named 'tradingagents.stress.detection'"

- [ ] **Step 3: Implement**

```python
# tradingagents/stress/detection.py
"""Detection metrics + block-shuffle placebo for the stress EWS."""
import numpy as np
import pandas as pd


def _warn_clusters(warn: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    clusters = []
    start = prev = None
    for ts, on in warn.items():
        if on:
            if start is None:
                start = ts
            prev = ts
        elif start is not None:
            clusters.append((start, prev))
            start = None
    if start is not None:
        clusters.append((start, prev))
    return clusters


def detection_metrics(warn: pd.Series, episodes: pd.DataFrame, window: int = 20) -> dict:
    warn = warn.astype(bool)
    leads, hits = [], 0
    for _, ep in episodes.iterrows():
        lo, hi = ep["start"] - pd.Timedelta(days=window), ep["start"] - pd.Timedelta(days=1)
        w = warn.loc[lo:hi]
        if w.any():
            hits += 1
            leads.append((ep["start"] - w[w].index[0]).days)
    clusters = _warn_clusters(warn)
    fa = 0
    for cs, _ in clusters:
        ok = any(
            cs <= ep_start <= cs + pd.Timedelta(days=window)
            for ep_start in episodes["start"]
        )
        if not ok:
            fa += 1
    years = max((warn.index[-1] - warn.index[0]).days / 365.25, 1e-9)
    n_ep = len(episodes)
    return {
        "hit_rate": hits / n_ep if n_ep else float("nan"),
        "n_episodes": n_ep,
        "n_hits": hits,
        "median_lead_days": float(np.median(leads)) if leads else float("nan"),
        "false_alarm_clusters_per_year": fa / years,
        "n_warn_clusters": len(clusters),
    }


def _block_shuffle(values: np.ndarray, block: int, rng: np.random.Generator) -> np.ndarray:
    n = len(values)
    out = np.empty(n, dtype=values.dtype)
    i = 0
    while i < n:
        length = min(rng.geometric(1.0 / block), n - i)
        start = rng.integers(0, n)
        idx = (start + np.arange(length)) % n
        out[i : i + length] = values[idx]
        i += length
    return out


def placebo_pvalue(
    warn: pd.Series, episodes: pd.DataFrame,
    n: int = 500, block: int = 21, seed: int = 0, window: int = 20,
) -> dict:
    real = detection_metrics(warn, episodes, window)["hit_rate"]
    rng = np.random.default_rng(seed)
    vals = warn.astype(bool).to_numpy()
    placebo = []
    for _ in range(n):
        fake = pd.Series(_block_shuffle(vals, block, rng), index=warn.index)
        placebo.append(detection_metrics(fake, episodes, window)["hit_rate"])
    placebo = np.array(placebo)
    ge = int(np.sum(placebo >= real)) if not np.isnan(real) else n
    return {"p_hit_rate": (1 + ge) / (n + 1), "placebo_hit_rates": placebo.tolist()}
```

- [ ] **Step 4: Run tests, expect pass**

Run: `.venv/bin/python -m pytest tests/test_stress_detection.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/stress/detection.py tests/test_stress_detection.py
git commit -m "feat(stress-ews): detection metrics (hit/lead/FA-rate) + block-shuffle placebo"
```

---

### Task 4: De-risk overlay (`tradingagents/stress/overlay.py`)

**Files:**
- Create: `tradingagents/stress/overlay.py`
- Test: `tests/test_stress_overlay.py`

**Interfaces:**
- Consumes: `warn` series (Task 1), daily strategy/benchmark log-return series.
- Produces: `apply_overlay(returns: pd.Series, warn: pd.Series, cooldown: int = 5) -> pd.Series` — returns zeroed while warn is active and for `cooldown` days after release (position flat; re-entry lag models execution). `overlay_metrics(returns, warn, cooldown=5) -> dict` with `sr_base`, `sr_overlay`, `delta_sr`, `maxdd_base`, `maxdd_overlay`, `delta_maxdd`, `exposure_frac`. SR = mean/std * sqrt(365) on daily log-returns (SR := 0.0 if std == 0, per house convention). MaxDD on cumulative sum of log-returns (expm1 of cummax gap).

- [ ] **Step 1: Write failing tests**

```python
# tests/test_stress_overlay.py
import numpy as np
import pandas as pd
from tradingagents.stress.overlay import apply_overlay, overlay_metrics


def _idx(n):
    return pd.date_range("2022-01-01", periods=n, freq="D", tz="UTC")


def test_overlay_zeros_warn_and_cooldown():
    idx = _idx(10)
    ret = pd.Series(0.01, index=idx)
    warn = pd.Series([False, True, True, False] + [False] * 6, index=idx)
    out = apply_overlay(ret, warn, cooldown=2)
    # zeroed on warn days 1-2 and cooldown days 3-4
    assert out.iloc[1:5].eq(0.0).all()
    assert out.iloc[0] == 0.01 and out.iloc[5] == 0.01


def test_overlay_avoids_crash_improves_dd():
    idx = _idx(60)
    ret = pd.Series(0.001, index=idx)
    ret.iloc[30:40] = -0.03  # crash
    warn = pd.Series(False, index=idx)
    warn.iloc[28:40] = True  # warned before crash
    m = overlay_metrics(ret, warn, cooldown=2)
    assert m["delta_maxdd"] < 0  # overlay reduces drawdown
    assert m["sr_overlay"] > m["sr_base"]


def test_zero_variance_sr_is_zero():
    idx = _idx(30)
    ret = pd.Series(0.0, index=idx)
    warn = pd.Series(False, index=idx)
    m = overlay_metrics(ret, warn)
    assert m["sr_base"] == 0.0
```

- [ ] **Step 2: Run tests, expect fail**

Run: `.venv/bin/python -m pytest tests/test_stress_overlay.py -v`
Expected: ERROR "No module named 'tradingagents.stress.overlay'"

- [ ] **Step 3: Implement**

```python
# tradingagents/stress/overlay.py
"""Flatten-while-WARN de-risk overlay + paired metrics."""
import numpy as np
import pandas as pd


def apply_overlay(returns: pd.Series, warn: pd.Series, cooldown: int = 5) -> pd.Series:
    warn = warn.reindex(returns.index).fillna(False).astype(bool)
    flat = warn.copy()
    release_count = 0
    out_flags = []
    for on in warn:
        if on:
            release_count = cooldown
            out_flags.append(True)
        elif release_count > 0:
            release_count -= 1
            out_flags.append(True)
        else:
            out_flags.append(False)
    flat = pd.Series(out_flags, index=returns.index)
    return returns.where(~flat, 0.0)


def _sr(returns: pd.Series) -> float:
    sd = returns.std()
    if sd == 0 or np.isnan(sd):
        return 0.0
    return float(returns.mean() / sd * np.sqrt(365))


def _maxdd(returns: pd.Series) -> float:
    cum = returns.cumsum()
    dd = cum - cum.cummax()
    return float(np.expm1(dd.min()))


def overlay_metrics(returns: pd.Series, warn: pd.Series, cooldown: int = 5) -> dict:
    ov = apply_overlay(returns, warn, cooldown)
    flat_frac = float((ov == 0.0).mean())
    return {
        "sr_base": _sr(returns),
        "sr_overlay": _sr(ov),
        "delta_sr": _sr(ov) - _sr(returns),
        "maxdd_base": _maxdd(returns),
        "maxdd_overlay": _maxdd(ov),
        "delta_maxdd": _maxdd(ov) - _maxdd(returns),
        "exposure_frac": 1.0 - flat_frac,
    }
```

- [ ] **Step 4: Run tests, expect pass**

Run: `.venv/bin/python -m pytest tests/test_stress_overlay.py -v`
Expected: 3 passed

- [ ] **Step 5: Full suite regression check**

Run: `.venv/bin/python -m pytest tests/ -q 2>&1 | tail -3`
Expected: no new failures beyond pre-existing ones (compare with `git stash; pytest; git stash pop` if unsure — as of branch base: 2 pre-existing test_parity_script.py failures).

- [ ] **Step 6: Commit**

```bash
git add tradingagents/stress/overlay.py tests/test_stress_overlay.py
git commit -m "feat(stress-ews): flatten-while-WARN overlay + paired SR/maxDD metrics"
```

---

### Task 5: Dev-window runner — 9-config grid, ledgered (`scripts/stress_ews_dev.py`)

**Files:**
- Create: `scripts/stress_ews_dev.py`
- Output: `data/rebuild/stress_ews/dev_results.json`

**Interfaces:**
- Consumes: all Task 1–4 functions; `tradingagents/rebuild/ledger.py:log_trial`; EW BTC+ETH close from the OHLCV cache used by `scripts/baseline_v5_mix.py` (import its loader — find the function that returns per-coin OHLCV DataFrames, reuse verbatim rather than re-implementing; it exists because the rebuild's factor sleeve used full-history closes).
- Produces: `dev_results.json` — one record per config: config dict, detection metrics, placebo p, overlay metrics on (a) EW B&H, (b) factor sleeve daily returns if `data/rebuild/holdout/` has the frozen factor return series for dev — else B&H only (record which); plus `selected` block per the frozen `dev_select` gate.

- [ ] **Step 1: Write the runner**

```python
# scripts/stress_ews_dev.py
"""Dev-window evaluation of the 9 pre-registered stress-EWS configs. Ledger: stress_ews."""
import json
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.rebuild.ledger import log_trial
from tradingagents.stress.detection import detection_metrics, placebo_pvalue
from tradingagents.stress.episodes import build_episodes
from tradingagents.stress.index import build_components, composite_warn
from tradingagents.stress.overlay import overlay_metrics

DEV = ("2021-11-01", "2025-03-31")
GRID_SETS = [["z_fund", "z_oi"], ["z_fund", "z_oi", "z_liq"], ["z_fund", "z_oi", "z_liq", "z_fg"]]
GRID_K = [1.0, 1.5, 2.0]
GATE = {"hit_rate_min": 0.5, "false_alarms_per_year_max": 6,
        "placebo_p_max": 0.05, "overlay_delta_maxdd_max": 0.0, "overlay_delta_sr_min": -0.10}
OUT = Path("data/rebuild/stress_ews")


def load_ew_close() -> pd.Series:
    # Reuse the same close series the rebuild factor sleeve used.
    # baseline_v5_mix exposes the cached OHLCV loader; adapt the import to its actual name:
    from scripts.baseline_v5_mix import load_ohlcv  # verified at implementation time

    closes = []
    for coin in ["bitcoin", "ethereum"]:
        df = load_ohlcv(coin)
        closes.append(np.log(df["close"]).diff())
    ew_logret = sum(c for c in closes) / 2
    return np.exp(ew_logret.cumsum().fillna(0.0))  # synthetic EW price path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lo, hi = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC")
    comps = build_components(["bitcoin", "ethereum"],
                             Path("data/derivatives"), Path("data/sentiment/fng/fng.parquet"))
    close = load_ew_close()
    close_dev = close.loc[lo:hi]
    episodes = build_episodes(close_dev)
    ew_ret = np.log(close_dev / close_dev.shift(1)).dropna()

    results = []
    for cset, k in product(GRID_SETS, GRID_K):
        cw = composite_warn(comps, cset, k).loc[lo:hi]
        det = detection_metrics(cw["warn"], episodes)
        plc = placebo_pvalue(cw["warn"], episodes, n=500, seed=0)
        ovl = overlay_metrics(ew_ret, cw["warn"])
        cfg = {"components": cset, "k": k, "hysteresis": 0.25, "cooldown": 5,
               "episode": "-15pct/10d/merge10", "window": 20}
        metrics = {**det, "p_hit_rate": plc["p_hit_rate"],
                   **{f"ovl_{m}": v for m, v in ovl.items()}}
        log_trial("stress_ews", cfg, DEV, metrics)
        passes = (det["hit_rate"] >= GATE["hit_rate_min"]
                  and det["false_alarm_clusters_per_year"] <= GATE["false_alarms_per_year_max"]
                  and plc["p_hit_rate"] <= GATE["placebo_p_max"]
                  and ovl["delta_maxdd"] <= GATE["overlay_delta_maxdd_max"]
                  and ovl["delta_sr"] >= GATE["overlay_delta_sr_min"])
        results.append({"config": cfg, "metrics": metrics, "gate_pass": bool(passes)})
        print(f"{cset} k={k}: hit={det['hit_rate']:.2f} p={plc['p_hit_rate']:.3f} "
              f"FA/yr={det['false_alarm_clusters_per_year']:.1f} "
              f"dMaxDD={ovl['delta_maxdd']:+.3f} dSR={ovl['delta_sr']:+.2f} pass={passes}")

    passing = [r for r in results if r["gate_pass"]]
    selected = (sorted(passing, key=lambda r: (r["metrics"]["p_hit_rate"],
                                               r["metrics"]["ovl_delta_maxdd"]))[0]
                if passing else None)
    json.dump({"n_episodes_dev": len(episodes),
               "episodes": episodes.assign(start=episodes["start"].astype(str),
                                           end=episodes["end"].astype(str)).to_dict("records") if len(episodes) else [],
               "results": results, "selected": selected},
              open(OUT / "dev_results.json", "w"), indent=1, default=str)
    print("selected:", json.dumps(selected["config"]) if selected else "NONE (all fail gate)")


if __name__ == "__main__":
    main()
```

Note to implementer: `from scripts.baseline_v5_mix import load_ohlcv` — check the actual loader name in `scripts/baseline_v5_mix.py` first (`grep -n "def load" scripts/baseline_v5_mix.py`); reuse whatever function the factor sleeve holdout used (`scripts/holdout/` shows the exact import). Do NOT write a new OHLCV fetcher.

- [ ] **Step 2: Smoke-run on dev window**

Run: `.venv/bin/python scripts/stress_ews_dev.py`
Expected: 9 lines (one per config) + `selected: ...`; `data/rebuild/stress_ews/dev_results.json` written; 9 new rows in the trial ledger (`experiment="stress_ews"`). Sanity: `n_episodes_dev` between 3 and 15 (dev window contains Nov-2022 FTX and Aug-2024 at minimum — if 0 episodes, the close loader is wrong; stop and fix before interpreting).

- [ ] **Step 3: Commit code + results**

```bash
git add scripts/stress_ews_dev.py data/rebuild/stress_ews/dev_results.json
git add -f data/rebuild/trial_ledger.jsonl 2>/dev/null || git add data/rebuild/trial_ledger.jsonl
git commit -m "exp(stress-ews): dev-window 9-config grid, detection+placebo+overlay, ledgered"
```

---

### Task 6: Data refresh attempt (Coinglass/F&G tail to present)

**Files:**
- Modify: none (runs existing backfill scripts)
- Output: refreshed `data/derivatives/*.parquet`, `data/sentiment/fng/fng.parquet`

- [ ] **Step 1: Refresh derivatives + F&G**

Run (each may need the Coinglass API key from `~/master_thesis/keys` — check `scripts/backfill_funding_history.py --help` and the script headers for env var name):

```bash
.venv/bin/python scripts/backfill_funding_history.py 2>&1 | tail -5
.venv/bin/python scripts/backfill_fng.py 2>&1 | tail -5
```

Expected: derivatives columns extend beyond 2026-05-10 toward present. Verify:

```bash
.venv/bin/python -c "
import pandas as pd
df = pd.read_parquet('data/derivatives/bitcoin.parquet')
print(df['funding_rate'].dropna().index.max(), df['oi_close'].dropna().index.max())"
```

- [ ] **Step 2: Decide holdout end (mechanical rule, no discretion)**

Holdout end = min(2026-07-01, last date where ALL selected-config components are non-NaN). Record the value in the Task 7 command line. If refresh fails entirely (API/subscription), holdout end = 2026-05-10 and the failure is noted in the results file — do NOT retry-tune.

- [ ] **Step 3: Commit refreshed stores (if changed)**

```bash
git add data/derivatives/*.parquet data/sentiment/fng/fng.parquet
git commit -m "data(stress-ews): refresh Coinglass derivatives + FnG tail for holdout"
```

---

### Task 7: Holdout one-shot (`scripts/stress_ews_holdout.py`) — ONLY if Task 5 selected a config

**Files:**
- Create: `scripts/stress_ews_holdout.py`
- Output: `data/rebuild/stress_ews/holdout_result.json`
- Modify: `THESIS_FINDINGS.md` (new section)

**Interfaces:**
- Consumes: `dev_results.json["selected"]["config"]` (frozen — script MUST read it from the file, never take config from CLI), Task 1–4 functions, `log_trial(..., allow_holdout=True)`.

- [ ] **Step 1: Gate check — does a selected config exist?**

Run: `.venv/bin/python -c "import json; print(json.load(open('data/rebuild/stress_ews/dev_results.json'))['selected'])"`
If `None`: skip Steps 2–4, go directly to Step 5 and record the honest negative (dev gate failed; holdout stays locked/unspent).

- [ ] **Step 2: Write the one-shot script**

```python
# scripts/stress_ews_holdout.py
"""Stress-EWS holdout one-shot. Config frozen from dev_results.json. Run EXACTLY once."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.rebuild.ledger import log_trial
from tradingagents.stress.detection import detection_metrics, placebo_pvalue
from tradingagents.stress.episodes import build_episodes
from tradingagents.stress.index import build_components, composite_warn
from tradingagents.stress.overlay import overlay_metrics
from scripts.stress_ews_dev import load_ew_close, GATE

HOLDOUT_START = "2025-04-01"
HOLDOUT_END = sys.argv[1]  # from Task 6 Step 2 mechanical rule, e.g. "2026-07-01"
OUT = Path("data/rebuild/stress_ews/holdout_result.json")

assert not OUT.exists(), "one_shot_rule: holdout already executed"
sel = json.load(open("data/rebuild/stress_ews/dev_results.json"))["selected"]
assert sel is not None, "no selected config — holdout must not run"
cfg = sel["config"]

lo, hi = pd.Timestamp(HOLDOUT_START, tz="UTC"), pd.Timestamp(HOLDOUT_END, tz="UTC")
comps = build_components(["bitcoin", "ethereum"],
                         Path("data/derivatives"), Path("data/sentiment/fng/fng.parquet"))
close = load_ew_close().loc[lo:hi]
episodes = build_episodes(close)
ew_ret = np.log(close / close.shift(1)).dropna()

cw = composite_warn(comps, cfg["components"], cfg["k"]).loc[lo:hi]
det = detection_metrics(cw["warn"], episodes)
plc = placebo_pvalue(cw["warn"], episodes, n=500, seed=0)
ovl = overlay_metrics(ew_ret, cw["warn"])
metrics = {**det, "p_hit_rate": plc["p_hit_rate"], **{f"ovl_{m}": v for m, v in ovl.items()}}
log_trial("stress_ews_holdout", cfg, (HOLDOUT_START, HOLDOUT_END), metrics, allow_holdout=True)

verdict = {c: bool(v) for c, v in {
    "hit_rate": det["hit_rate"] >= GATE["hit_rate_min"],
    "fa_per_year": det["false_alarm_clusters_per_year"] <= GATE["false_alarms_per_year_max"],
    "placebo": plc["p_hit_rate"] <= GATE["placebo_p_max"],
    "delta_maxdd": ovl["delta_maxdd"] <= GATE["overlay_delta_maxdd_max"],
    "delta_sr": ovl["delta_sr"] >= GATE["overlay_delta_sr_min"]}.items()}
result = {"config": cfg, "window": [HOLDOUT_START, HOLDOUT_END],
          "n_episodes": len(episodes), "metrics": metrics,
          "gate": verdict, "GO": all(verdict.values())}
json.dump(result, open(OUT, "w"), indent=1, default=str)
print(json.dumps(result, indent=1, default=str))
```

- [ ] **Step 3: Execute ONCE**

Run: `.venv/bin/python scripts/stress_ews_holdout.py 2026-07-01` (end date per Task 6 Step 2)
Expected: JSON verdict printed, `holdout_result.json` written, 1 ledger row with `allow_holdout=True`. Whatever the verdict — it stands.

- [ ] **Step 4: Commit**

```bash
git add scripts/stress_ews_holdout.py data/rebuild/stress_ews/holdout_result.json data/rebuild/trial_ledger.jsonl
git commit -m "exp(stress-ews): holdout one-shot executed — verdict recorded as it fell"
```

- [ ] **Step 5: Write THESIS_FINDINGS.md section**

Append a new `## Section 42: Positioning Stress Early-Warning System (D2)` to `THESIS_FINDINGS.md` containing: motivation (SENTIMENT_EARLY_WARNING_RESEARCH_2026-07-14.md, BIS mechanism), pre-registration reference (gates.json stress_ews, commit hash of Task 0), dev grid table (9 rows: components/k/hit/p/FA/ΔmaxDD/ΔSR/pass), episode catalog table, selected config or "none", holdout verdict table (or "holdout unspent — dev gate failed"), and interpretation caveats (single dev window; hit-rate on small episode count; overlay tested on B&H EW, not the live book). Commit:

```bash
git add THESIS_FINDINGS.md
git commit -m "docs(stress-ews): THESIS section 42 — D2 detection results"
```

---

## Self-Review

- Spec coverage: pre-registration (Task 0) ✓; causal index (T1) ✓; mechanical episodes (T2) ✓; detection+placebo (T3) ✓; overlay economics (T4) ✓; ledgered dev grid (T5) ✓; data refresh + mechanical holdout-end rule (T6) ✓; one-shot + thesis section (T7) ✓. D1 (sentiment-beta sort) and pivot infra intentionally OUT of scope — separate plan.
- Placeholders: one deliberate implementation-time lookup (OHLCV loader name in `baseline_v5_mix.py`) with exact grep command and instruction to reuse the factor-sleeve loader — acceptable as it references existing verified code, not new code to invent.
- Type consistency: `composite_warn` returns DataFrame with `warn` bool column consumed by `detection_metrics(warn: pd.Series)` — callers pass `cw["warn"]` ✓; `build_episodes` returns `start`/`end`/`trough_ret` consumed by detection ✓; GATE dict shared via import in holdout script ✓.

## Known risks (accepted, documented)

- Grid of 9 with 5-condition gate on ~5-12 dev episodes = coarse power; that is the point of the placebo + one-shot discipline.
- `funding_rate` starts 2021-11 → May-2021 crash outside dev window; FTX (Nov-2022) + Aug-2024 inside.
- Overlay is long-only-flat; no short leg (matches evidence: warning, not alpha).
