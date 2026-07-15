# Meta-Labeled Trend System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the meta-labeled trend system from `docs/superpowers/specs/2026-07-15-meta-labeling-design.md`: frozen model-free trend primary → triple-barrier labels → LightGBM meta-classifier on positioning/on-chain features → filter/shrink decision layer, evaluated under pre-registered gates G1–G3.

**Architecture:** New package `tradingagents/metalabel/` with five focused modules (primary, labeler, features, wf, model, backtest) + two scripts. Reuses `tradingagents/rebuild/ledger.py` (trial ledger + holdout guard), `tradingagents/rebuild/compare.py:paired_bootstrap`, `tradingagents/dataflows/onchain_features.py:build_pit_onchain_features`, `tradingagents/dataflows/fng_store.py:query_fng`, `tradingagents/dataflows/coingecko_binance.py:_load_crypto_ohlcv`.

**Tech Stack:** Python 3.13 (`uv sync --all-extras --python 3.13.13`), pandas, numpy, lightgbm, scikit-learn (roc_auc_score, brier_score_loss, IsotonicRegression, LogisticRegression), pytest.

## Global Constraints

- Coins (coingecko ids): `("bitcoin", "ethereum", "binancecoin", "solana", "ripple", "dogecoin", "cardano", "tron")` — the live 8-coin universe.
- Dev window: 2021-07-01 … 2025-03-31. Locked holdout: 2025-04-01 … 2026-06-30 (aligned with `tradingagents/rebuild/ledger.py:HOLDOUT_START = "2025-04-01"`; the spec's 2025-07 boundary is amended to the existing house lock — stricter, ledger unmodified).
- Frozen a priori (never tuned): MA pairs (5/20, 10/40, 20/60), Donchian 20-entry/10-exit, barrier constants pt=2.0σ / sl=1.5σ / vertical=15 trading bars, σ = EWMA(span=20) of daily log returns, τ grid {0.45, 0.50, 0.55, 0.60}, cost = 10 bps round trip (5 bps/side on turnover), vol target 30% annualized, LGB grid of 8 combos (Task 6).
- Causality: signals from close of bar t execute at open of bar t+1; features strictly ≤ close of t; same-bar barrier ambiguity resolved SL-before-PT.
- Every dev experiment logged via `log_trial(...)`; `gates.json` + `freeze.json` committed BEFORE the first model fit (Task 1). Holdout touched only by `scripts/metalabel_holdout.py` with `allow_holdout=True`, run at most once.
- Zero-variance return windows → SR := 0.
- Run tests with `uv run pytest tests/metalabel/ -v` from the worktree root `/home/malecada/master_thesis/TradingAgents-metalabel`.

---

### Task 1: Pre-registration artifacts (gates.json, freeze.json, spec amendment)

**Files:**
- Create: `experiments/metalabel/gates.json`
- Create: `experiments/metalabel/freeze.json`
- Modify: `docs/superpowers/specs/2026-07-15-meta-labeling-design.md` (holdout boundary amendment)
- Test: `tests/metalabel/test_prereg.py`

**Interfaces:**
- Produces: `experiments/metalabel/gates.json` and `freeze.json` consumed read-only by Tasks 8–10; `tests/metalabel/__init__.py` package marker.

- [ ] **Step 1: Write the failing test**

```python
# tests/metalabel/test_prereg.py
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    return json.loads((ROOT / "experiments" / "metalabel" / name).read_text())


def test_gates_json_complete():
    g = _load("gates.json")
    assert g["G1"]["auc_ci_excludes"] == 0.5
    assert g["G1"]["must_beat"] == ["constant_base_rate", "logistic"]
    assert g["G2"]["delta_sr_p_pos_min"] == 0.90
    assert g["G2"]["max_dd_ratio_max"] == 1.1
    assert g["G3"]["one_shot"] is True
    assert g["holdout_start"] == "2025-04-01"


def test_freeze_json_pins_all_frozen_params():
    f = _load("freeze.json")
    assert f["ma_pairs"] == [[5, 20], [10, 40], [20, 60]]
    assert f["donchian"] == {"entry": 20, "exit": 10}
    assert f["barriers"] == {"pt_mult": 2.0, "sl_mult": 1.5, "vertical_bars": 15}
    assert f["sigma_span"] == 20
    assert f["tau_grid"] == [0.45, 0.50, 0.55, 0.60]
    assert f["cost_bps_round_trip"] == 10
    assert f["vol_target_ann"] == 0.30
    assert f["coins"] == [
        "bitcoin", "ethereum", "binancecoin", "solana",
        "ripple", "dogecoin", "cardano", "tron",
    ]
    assert f["dev_window"] == ["2021-07-01", "2025-03-31"]
    assert f["holdout_window"] == ["2025-04-01", "2026-06-30"]


def test_holdout_guard_blocks_dev_run_into_holdout():
    from tradingagents.rebuild.ledger import assert_dev_window
    with pytest.raises(ValueError):
        assert_dev_window("2025-04-01")
    assert_dev_window("2025-03-31")  # must not raise
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/metalabel/test_prereg.py -v`
Expected: FAIL (FileNotFoundError on gates.json). Create empty `tests/metalabel/__init__.py` first if pytest can't collect.

- [ ] **Step 3: Write the artifacts**

```json
// experiments/metalabel/gates.json
{
  "experiment": "metalabel-2026-07",
  "registered": "2026-07-15",
  "holdout_start": "2025-04-01",
  "G1": {
    "description": "Model quality on pooled dev OOS predictions",
    "auc_ci_excludes": 0.5,
    "auc_ci_level": 0.95,
    "bootstrap_n": 2000,
    "must_beat": ["constant_base_rate", "logistic"],
    "brier_vs": "constant_base_rate"
  },
  "G2": {
    "description": "Economic do-no-harm on dev walk-forward",
    "meta_sr_gte_primary": true,
    "delta_sr_p_pos_min": 0.90,
    "max_dd_ratio_max": 1.1
  },
  "G3": {
    "description": "Holdout one-shot with frozen pipeline",
    "one_shot": true,
    "criteria": "delta_sr > 0 AND (meta_sr_holdout > 0 OR meta_sr_holdout > primary_sr_holdout)"
  }
}
```

```json
// experiments/metalabel/freeze.json
{
  "frozen": "2026-07-15",
  "ma_pairs": [[5, 20], [10, 40], [20, 60]],
  "donchian": {"entry": 20, "exit": 10},
  "barriers": {"pt_mult": 2.0, "sl_mult": 1.5, "vertical_bars": 15},
  "sigma_span": 20,
  "tau_grid": [0.45, 0.50, 0.55, 0.60],
  "cost_bps_round_trip": 10,
  "vol_target_ann": 0.30,
  "coins": ["bitcoin", "ethereum", "binancecoin", "solana", "ripple", "dogecoin", "cardano", "tron"],
  "dev_window": ["2021-07-01", "2025-03-31"],
  "holdout_window": ["2025-04-01", "2026-06-30"],
  "wf": {"retrain_every_days": 90, "embargo_bars": 15, "min_train_events": 150},
  "lgb_grid": {
    "num_leaves": [15, 31],
    "min_child_samples": [20, 50],
    "feature_fraction": [0.7, 1.0],
    "learning_rate": 0.05,
    "n_estimators": 300
  },
  "size_mult": "clip((p - tau) / (0.7 - tau), 0.25, 1.0)"
}
```

In the spec file, replace the sentence defining dev/holdout (§3, "dev = 2021-07 … 2025-06; **locked holdout = 2025-07 … 2026-06** (last 12 months)") with: "dev = 2021-07-01 … 2025-03-31; **locked holdout = 2025-04-01 … 2026-06-30** — aligned with the pre-existing house lock `HOLDOUT_START = 2025-04-01` in `tradingagents/rebuild/ledger.py` (stricter than the originally drafted 2025-07 boundary; guard code unmodified)."

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/metalabel/test_prereg.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add experiments/metalabel/ tests/metalabel/ docs/superpowers/specs/2026-07-15-meta-labeling-design.md
git commit -m "prereg(metalabel): gates.json + freeze.json before any experiment; holdout aligned to house lock"
```

---

### Task 2: Trend primary — votes and events (`primary.py`)

**Files:**
- Create: `tradingagents/metalabel/__init__.py` (empty)
- Create: `tradingagents/metalabel/primary.py`
- Test: `tests/metalabel/test_primary.py`

**Interfaces:**
- Consumes: OHLCV DataFrame with columns `Date, Open, High, Low, Close, Volume` (the `_load_crypto_ohlcv` format), Date ascending, tz-naive.
- Produces:
  - `compute_votes(ohlcv: pd.DataFrame) -> pd.Series` — float in {0, .25, .5, .75, 1}, indexed by Date (DatetimeIndex), NaN for warm-up (< 60 bars).
  - `extract_events(votes: pd.Series) -> pd.DatetimeIndex` — dates where vote crosses from ≤ 0.5 to > 0.5.
  - `primary_positions(votes: pd.Series) -> pd.Series` — 0/1, 1 while vote > 0.5.

- [ ] **Step 1: Write the failing test**

```python
# tests/metalabel/test_primary.py
import numpy as np
import pandas as pd
import pytest

from tradingagents.metalabel.primary import (
    compute_votes, extract_events, primary_positions,
)


def _ohlcv(closes):
    idx = pd.date_range("2023-01-01", periods=len(closes), freq="D")
    c = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({
        "Date": idx, "Open": c.values, "High": c.values * 1.01,
        "Low": c.values * 0.99, "Close": c.values, "Volume": 1.0,
    })


def test_votes_uptrend_reach_one_downtrend_zero():
    up = _ohlcv(np.linspace(100, 400, 150))
    v = compute_votes(up)
    assert v.iloc[-1] == 1.0
    down = _ohlcv(np.linspace(400, 100, 150))
    assert compute_votes(down).iloc[-1] == 0.0


def test_votes_warmup_nan():
    v = compute_votes(_ohlcv(np.linspace(100, 200, 150)))
    assert v.iloc[:59].isna().all()


def test_event_on_upcross_only():
    # 80 bars down (vote 0), then strong reversal up -> exactly one entry event
    closes = np.concatenate([np.linspace(200, 100, 80), np.linspace(100, 300, 70)])
    df = _ohlcv(closes)
    v = compute_votes(df)
    ev = extract_events(v)
    assert len(ev) == 1
    assert v.loc[ev[0]] > 0.5
    prev = v.shift(1).loc[ev[0]]
    assert prev <= 0.5


def test_positions_match_votes():
    closes = np.concatenate([np.linspace(200, 100, 80), np.linspace(100, 300, 70)])
    v = compute_votes(_ohlcv(closes))
    pos = primary_positions(v)
    assert set(pos.dropna().unique()) <= {0.0, 1.0}
    assert (pos[v > 0.5] == 1.0).all()
    assert (pos[(v <= 0.5) & v.notna()] == 0.0).all()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/metalabel/test_primary.py -v`
Expected: FAIL with `ModuleNotFoundError: tradingagents.metalabel`

- [ ] **Step 3: Write the implementation**

```python
# tradingagents/metalabel/primary.py
"""Frozen model-free trend primary. Parameters pinned in experiments/metalabel/freeze.json.

Vote = mean of 4 binary rules: MA-cross 5/20, 10/40, 20/60 and a stateful
Donchian 20-entry/10-exit channel. Entry event = vote crossing above 0.5.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MA_PAIRS = ((5, 20), (10, 40), (20, 60))
DONCHIAN_ENTRY = 20
DONCHIAN_EXIT = 10
WARMUP = 60


def compute_votes(ohlcv: pd.DataFrame) -> pd.Series:
    close = pd.Series(ohlcv["Close"].values, index=pd.DatetimeIndex(ohlcv["Date"]))
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
    votes.iloc[:WARMUP - 1] = np.nan
    votes.name = "vote"
    return votes


def extract_events(votes: pd.Series) -> pd.DatetimeIndex:
    prev = votes.shift(1)
    cross = (votes > 0.5) & (prev <= 0.5) & prev.notna()
    return pd.DatetimeIndex(votes.index[cross])


def primary_positions(votes: pd.Series) -> pd.Series:
    pos = (votes > 0.5).astype(float)
    pos[votes.isna()] = np.nan
    pos.name = "position"
    return pos
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/metalabel/test_primary.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add tradingagents/metalabel/ tests/metalabel/test_primary.py
git commit -m "feat(metalabel): frozen trend primary — ensemble votes, entry events, positions"
```

---

### Task 3: Triple-barrier labeler + uniqueness weights (`labeler.py`)

**Files:**
- Create: `tradingagents/metalabel/labeler.py`
- Test: `tests/metalabel/test_labeler.py`

**Interfaces:**
- Consumes: OHLCV frame (Task 2 format), `events: pd.DatetimeIndex` from `extract_events`.
- Produces:
  - `triple_barrier_labels(ohlcv, events, pt_mult=2.0, sl_mult=1.5, vertical_bars=15, sigma_span=20) -> pd.DataFrame` indexed by event entry-signal date, columns: `entry_exec_date` (bar t+1), `entry_px` (Open of t+1), `sigma` (EWMA σ at t), `pt_px`, `sl_px`, `touch_date`, `touch_type` ("pt"|"sl"|"vertical"), `label` (int 0/1), `ret` (net log return entry→touch, pre-cost). Events whose t+1 bar or full vertical window is off the end of data are DROPPED.
  - `uniqueness_weights(labels: pd.DataFrame, bar_index: pd.DatetimeIndex) -> pd.Series` — average-uniqueness weight per event (AFML §4.5), same index as `labels`.

- [ ] **Step 1: Write the failing test**

```python
# tests/metalabel/test_labeler.py
import numpy as np
import pandas as pd
import pytest

from tradingagents.metalabel.labeler import triple_barrier_labels, uniqueness_weights


def _flat_ohlcv(n=60, px=100.0):
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "Date": idx, "Open": px, "High": px, "Low": px,
        "Close": px, "Volume": 1.0,
    }), idx


def test_pt_touch_labels_one():
    df, idx = _flat_ohlcv()
    ev = pd.DatetimeIndex([idx[30]])
    # entry exec at bar 31 open=100; force sigma with tiny noise then a +25% spike at bar 33
    df.loc[:30, "Close"] = 100 + np.sin(np.arange(31))  # nonzero sigma
    df.loc[33, "High"] = 130.0
    out = triple_barrier_labels(df, ev)
    assert len(out) == 1
    r = out.iloc[0]
    assert r["touch_type"] == "pt"
    assert r["label"] == 1
    assert r["touch_date"] == idx[33]
    assert r["entry_px"] == 100.0


def test_same_bar_pt_and_sl_resolves_sl_first():
    df, idx = _flat_ohlcv()
    df.loc[:30, "Close"] = 100 + np.sin(np.arange(31))
    ev = pd.DatetimeIndex([idx[30]])
    df.loc[32, "High"] = 200.0   # PT touched
    df.loc[32, "Low"] = 50.0     # SL touched same bar -> SL wins
    out = triple_barrier_labels(df, ev)
    assert out.iloc[0]["touch_type"] == "sl"
    assert out.iloc[0]["label"] == 0


def test_vertical_sign_of_return():
    df, idx = _flat_ohlcv()
    df.loc[:30, "Close"] = 100 + np.sin(np.arange(31))
    # drift +0.1/day, never touching 2-sigma barriers
    for i in range(31, 60):
        for col in ("Open", "High", "Low", "Close"):
            df.loc[i, col] = 100 + 0.01 * (i - 31)
    ev = pd.DatetimeIndex([idx[30]])
    out = triple_barrier_labels(df, ev)
    r = out.iloc[0]
    assert r["touch_type"] == "vertical"
    assert r["touch_date"] == idx[31 + 15]
    assert r["label"] == 1  # positive drift at vertical


def test_event_too_close_to_end_dropped():
    df, idx = _flat_ohlcv(n=35)
    df.loc[:30, "Close"] = 100 + np.sin(np.arange(31))
    ev = pd.DatetimeIndex([idx[33]])  # no t+1 vertical window
    out = triple_barrier_labels(df, ev)
    assert len(out) == 0


def test_sigma_uses_only_past_data():
    df, idx = _flat_ohlcv()
    df.loc[:30, "Close"] = 100 + np.sin(np.arange(31))
    ev = pd.DatetimeIndex([idx[30]])
    base = triple_barrier_labels(df, ev).iloc[0]["sigma"]
    df2 = df.copy()
    df2.loc[45:, "Close"] = 500.0  # future changes must not move sigma at t=30
    assert triple_barrier_labels(df2, ev).iloc[0]["sigma"] == pytest.approx(base)


def test_uniqueness_weights_overlap():
    df, idx = _flat_ohlcv(n=80)
    df["Close"] = 100 + np.sin(np.arange(80))
    ev = pd.DatetimeIndex([idx[30], idx[32]])  # heavy overlap
    labels = triple_barrier_labels(df, ev)
    w = uniqueness_weights(labels, pd.DatetimeIndex(df["Date"]))
    assert len(w) == len(labels)
    assert (w > 0).all() and (w <= 1).all()
    assert w.iloc[0] < 1.0  # overlapping events are down-weighted
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/metalabel/test_labeler.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write the implementation**

```python
# tradingagents/metalabel/labeler.py
"""Triple-barrier labels (AFML ch.3) + average-uniqueness weights (AFML §4.5).

Causality: sigma from closes <= entry-signal bar t; entry executes at Open
of bar t+1; barriers scanned from bar t+1 onward with SL-before-PT on
same-bar double touches (conservative, matches live STOP_MARKET behavior).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PT_MULT = 2.0
SL_MULT = 1.5
VERTICAL_BARS = 15
SIGMA_SPAN = 20


def triple_barrier_labels(
    ohlcv: pd.DataFrame,
    events: pd.DatetimeIndex,
    pt_mult: float = PT_MULT,
    sl_mult: float = SL_MULT,
    vertical_bars: int = VERTICAL_BARS,
    sigma_span: int = SIGMA_SPAN,
) -> pd.DataFrame:
    df = ohlcv.set_index(pd.DatetimeIndex(ohlcv["Date"]))
    close = df["Close"].astype(float)
    sigma_series = np.log(close).diff().ewm(span=sigma_span).std()

    rows = []
    positions = {d: i for i, d in enumerate(df.index)}
    for t in events:
        i = positions.get(t)
        if i is None or i + 1 >= len(df):
            continue
        j_entry = i + 1
        j_vert = j_entry + vertical_bars
        if j_vert >= len(df):
            continue  # vertical window off the end of data
        sigma = float(sigma_series.iloc[i])
        if not np.isfinite(sigma) or sigma <= 0:
            continue
        entry_px = float(df["Open"].iloc[j_entry])
        pt_px = entry_px * (1.0 + pt_mult * sigma)
        sl_px = entry_px * (1.0 - sl_mult * sigma)

        touch_type, j_touch = "vertical", j_vert
        for j in range(j_entry, j_vert + 1):
            lo, hi = float(df["Low"].iloc[j]), float(df["High"].iloc[j])
            if lo <= sl_px:          # SL checked first (conservative)
                touch_type, j_touch = "sl", j
                break
            if hi >= pt_px:
                touch_type, j_touch = "pt", j
                break

        if touch_type == "pt":
            exit_px, label = pt_px, 1
        elif touch_type == "sl":
            exit_px, label = sl_px, 0
        else:
            exit_px = float(df["Close"].iloc[j_vert])
            label = int(exit_px > entry_px)

        rows.append({
            "event_date": t,
            "entry_exec_date": df.index[j_entry],
            "entry_px": entry_px,
            "sigma": sigma,
            "pt_px": pt_px,
            "sl_px": sl_px,
            "touch_date": df.index[j_touch],
            "touch_type": touch_type,
            "label": label,
            "ret": float(np.log(exit_px / entry_px)),
        })

    out = pd.DataFrame(rows)
    if len(out):
        out = out.set_index("event_date")
    return out


def uniqueness_weights(
    labels: pd.DataFrame, bar_index: pd.DatetimeIndex
) -> pd.Series:
    """Average uniqueness: weight_i = mean over lifespan bars of 1/concurrency."""
    if not len(labels):
        return pd.Series(dtype=float)
    conc = pd.Series(0.0, index=bar_index)
    spans = {}
    for ev, row in labels.iterrows():
        mask = (bar_index >= row["entry_exec_date"]) & (bar_index <= row["touch_date"])
        conc[mask] += 1.0
        spans[ev] = mask
    w = {}
    for ev, mask in spans.items():
        w[ev] = float((1.0 / conc[mask]).mean()) if mask.any() else 1.0
    return pd.Series(w, name="weight").reindex(labels.index)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/metalabel/test_labeler.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add tradingagents/metalabel/labeler.py tests/metalabel/test_labeler.py
git commit -m "feat(metalabel): triple-barrier labeler + uniqueness weights, leak-tested"
```

---

### Task 4: Event feature assembly (`features.py`)

**Files:**
- Create: `tradingagents/metalabel/features.py`
- Test: `tests/metalabel/test_features.py`

**Interfaces:**
- Consumes: `compute_votes`, `triple_barrier_labels` outputs; `build_pit_onchain_features(coin, dates, root=...)` (returns wide `oc_*` frame indexed by date); `query_fng(trade_date, lookback_days, root=...)` (returns rows with `value`); OHLCV frames.
- Produces:
  - `price_trend_features(ohlcv, votes, event_dates) -> pd.DataFrame` — indexed by event date, columns `f_vote, f_trend_age, f_dist_20d_high, f_ret_20d, f_ret_60d, f_sigma_level, f_sigma_pctl_60d, f_volvol`.
  - `assemble_dataset(per_coin: dict[str, dict]) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]` = (X, y, w, meta). `per_coin[coin]` = `{"ohlcv": df, "votes": series, "labels": df, "weights": series, "onchain": df|None, "fng": series|None}`. X columns: price/trend features + fixed `OC_FEATURES` subset (NaN where missing) + `f_fng` + `f_breadth` + `coin_<id>` one-hots. y = labels. w = uniqueness weights. meta columns: `coin, event_date, entry_exec_date, touch_date, ret, sigma`.
  - Constant `OC_FEATURES: list[str]` — the exact Coinglass/on-chain column names used.

- [ ] **Step 1: Write the failing test**

```python
# tests/metalabel/test_features.py
import numpy as np
import pandas as pd

from tradingagents.metalabel.primary import compute_votes, extract_events
from tradingagents.metalabel.labeler import triple_barrier_labels, uniqueness_weights
from tradingagents.metalabel.features import (
    OC_FEATURES, price_trend_features, assemble_dataset,
)


def _trendy_ohlcv(n=200, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    ret = rng.normal(0.002, 0.03, n)
    c = 100 * np.exp(np.cumsum(ret))
    return pd.DataFrame({
        "Date": idx, "Open": c, "High": c * 1.02, "Low": c * 0.98,
        "Close": c, "Volume": 1.0,
    })


def _coin_blob(seed):
    ohlcv = _trendy_ohlcv(seed=seed)
    votes = compute_votes(ohlcv)
    events = extract_events(votes)
    labels = triple_barrier_labels(ohlcv, events)
    weights = uniqueness_weights(labels, pd.DatetimeIndex(ohlcv["Date"]))
    return {"ohlcv": ohlcv, "votes": votes, "labels": labels,
            "weights": weights, "onchain": None, "fng": None}


def test_price_trend_features_causal_and_complete():
    blob = _coin_blob(1)
    ev = blob["labels"].index
    f = price_trend_features(blob["ohlcv"], blob["votes"], ev)
    assert list(f.index) == list(ev)
    for col in ("f_vote", "f_trend_age", "f_dist_20d_high", "f_ret_20d",
                "f_ret_60d", "f_sigma_level", "f_sigma_pctl_60d", "f_volvol"):
        assert col in f.columns
    # causality: mutate bars after the first event -> its features unchanged
    first = ev[0]
    base = f.loc[first].copy()
    df2 = blob["ohlcv"].copy()
    df2.loc[df2["Date"] > first, "Close"] = 9999.0
    f2 = price_trend_features(df2, blob["votes"], ev[:1])
    pd.testing.assert_series_equal(f2.loc[first], base, check_names=False)


def test_assemble_dataset_shapes_and_onehots():
    per_coin = {"bitcoin": _coin_blob(1), "ethereum": _coin_blob(2)}
    X, y, w, meta = assemble_dataset(per_coin)
    assert len(X) == len(y) == len(w) == len(meta)
    assert len(X) == len(per_coin["bitcoin"]["labels"]) + len(per_coin["ethereum"]["labels"])
    assert "coin_bitcoin" in X.columns and "coin_ethereum" in X.columns
    assert set(y.unique()) <= {0, 1}
    # missing onchain/fng -> NaN columns present (LGB-native handling), not dropped
    for c in OC_FEATURES + ["f_fng"]:
        assert c in X.columns
        assert X[c].isna().all()
    assert "f_breadth" in X.columns
    assert X["f_breadth"].between(0, 1).all()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/metalabel/test_features.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write the implementation**

```python
# tradingagents/metalabel/features.py
"""Event-bar feature assembly. Every feature uses data <= close of the
event-signal bar t (PIT). On-chain/derivatives come from the PIT store
(build_pit_onchain_features is PIT by construction); missing coverage
stays NaN — never zero-filled (CPI zero-fill lesson)."""
from __future__ import annotations

import numpy as np
import pandas as pd

# Exact PIT-store columns consumed (all causal, oc_-prefixed by the loader).
OC_FEATURES = [
    "oc_funding_rate", "oc_funding_z_30d", "oc_funding_oiw_z_30d",
    "oc_oi_chg_7d", "oc_oi_z_30d", "oc_oi_to_mcap",
    "oc_liq_asym_z_30d", "oc_liq_total_z_30d",
    "oc_smart_money_z_30d", "oc_taker_asym_z_30d", "oc_basis_z_30d",
    "oc_AdrActCnt_z", "oc_flow_net_z", "oc_mvrv_z",
]


def price_trend_features(
    ohlcv: pd.DataFrame, votes: pd.Series, event_dates: pd.DatetimeIndex
) -> pd.DataFrame:
    df = ohlcv.set_index(pd.DatetimeIndex(ohlcv["Date"]))
    close = df["Close"].astype(float)
    logret = np.log(close).diff()
    sigma = logret.ewm(span=20).std()

    above = (votes > 0.5).astype(int)
    grp = (above != above.shift(1)).cumsum()
    trend_age = above.groupby(grp).cumcount().where(votes.notna())

    feats = pd.DataFrame({
        "f_vote": votes,
        "f_trend_age": trend_age,
        "f_dist_20d_high": close / close.rolling(20).max() - 1.0,
        "f_ret_20d": close.pct_change(20),
        "f_ret_60d": close.pct_change(60),
        "f_sigma_level": sigma,
        "f_sigma_pctl_60d": sigma.rolling(60).rank(pct=True),
        "f_volvol": sigma.pct_change().rolling(20).std(),
    })
    return feats.reindex(event_dates)


def assemble_dataset(per_coin: dict) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]:
    coins = sorted(per_coin)

    # Cross-coin breadth: fraction of coins with vote > 0.5 per bar.
    all_votes = pd.concat(
        {c: per_coin[c]["votes"] for c in coins}, axis=1
    )
    breadth = (all_votes > 0.5).sum(axis=1) / all_votes.notna().sum(axis=1).clip(lower=1)

    xs, ys, ws, metas = [], [], [], []
    for coin in coins:
        blob = per_coin[coin]
        labels = blob["labels"]
        if not len(labels):
            continue
        ev = pd.DatetimeIndex(labels.index)
        x = price_trend_features(blob["ohlcv"], blob["votes"], ev)

        oc = blob.get("onchain")
        for col in OC_FEATURES:
            x[col] = oc[col].reindex(ev) if oc is not None and col in oc.columns else np.nan

        fng = blob.get("fng")
        x["f_fng"] = fng.reindex(ev) if fng is not None else np.nan
        x["f_breadth"] = breadth.reindex(ev)
        for c2 in coins:
            x[f"coin_{c2}"] = float(c2 == coin)

        xs.append(x)
        ys.append(labels["label"])
        ws.append(blob["weights"])
        m = labels[["entry_exec_date", "touch_date", "ret", "sigma"]].copy()
        m["coin"] = coin
        m["event_date"] = ev
        metas.append(m)

    X = pd.concat(xs, ignore_index=True)
    y = pd.concat(ys, ignore_index=True).astype(int)
    w = pd.concat(ws, ignore_index=True)
    meta = pd.concat(metas, ignore_index=True)
    return X, y, w, meta
```

Note: `oc_AdrActCnt_z`, `oc_flow_net_z`, `oc_mvrv_z` — verify exact derived-column names against `_add_derived` in `tradingagents/dataflows/onchain_features.py` when wiring Task 8 (they are produced there with `oc_` prefix; if the actual names differ, e.g. `oc_aa_z_30d`, update `OC_FEATURES` to the real names in that task and adjust this list — the test only asserts presence-as-NaN so it stays green).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/metalabel/test_features.py -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add tradingagents/metalabel/features.py tests/metalabel/test_features.py
git commit -m "feat(metalabel): PIT event-feature assembly with pooled coin dataset"
```

---

### Task 5: Purged walk-forward splitter (`wf.py`)

**Files:**
- Create: `tradingagents/metalabel/wf.py`
- Test: `tests/metalabel/test_wf.py`

**Interfaces:**
- Consumes: `meta` frame from `assemble_dataset` (needs `event_date`, `touch_date`).
- Produces: `purged_walk_forward(meta, dev_start, dev_end, retrain_every_days=90, embargo_bars=15, min_train_events=150) -> list[tuple[np.ndarray, np.ndarray]]` — list of (train_positions, test_positions) integer index arrays into `meta`. Expanding train; test blocks of `retrain_every_days` calendar days; train events must satisfy `touch_date < test_start − embargo_days` where embargo_days = embargo_bars converted 1:1 to calendar days × 1.4 (15 bars ≈ 21 calendar days, constant `EMBARGO_CAL_DAYS = 21`). Folds with fewer than `min_train_events` train events are skipped (logged via `warnings.warn`).

- [ ] **Step 1: Write the failing test**

```python
# tests/metalabel/test_wf.py
import numpy as np
import pandas as pd
import warnings

from tradingagents.metalabel.wf import EMBARGO_CAL_DAYS, purged_walk_forward


def _meta(n=400, start="2021-07-01"):
    ev = pd.date_range(start, periods=n, freq="3D")
    return pd.DataFrame({
        "event_date": ev,
        "touch_date": ev + pd.Timedelta(days=10),
        "coin": "bitcoin",
    })


def test_no_train_event_touches_into_test():
    meta = _meta()
    folds = purged_walk_forward(meta, "2021-07-01", "2025-03-31")
    assert len(folds) > 3
    for tr, te in folds:
        test_start = meta.iloc[te]["event_date"].min()
        assert (meta.iloc[tr]["touch_date"]
                < test_start - pd.Timedelta(days=EMBARGO_CAL_DAYS)).all()
        # no index overlap, train strictly before test
        assert set(tr).isdisjoint(set(te))


def test_expanding_and_contiguous_test_blocks():
    meta = _meta()
    folds = purged_walk_forward(meta, "2021-07-01", "2025-03-31")
    sizes = [len(tr) for tr, _ in folds]
    assert sizes == sorted(sizes)  # expanding
    covered = np.concatenate([te for _, te in folds])
    assert len(covered) == len(set(covered))  # each test event exactly once


def test_min_train_events_skips_early_folds():
    meta = _meta(n=60)  # tiny -> early folds under 150 train events
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        folds = purged_walk_forward(meta, "2021-07-01", "2022-06-30")
    assert all(len(tr) >= 150 for tr, _ in folds) or len(folds) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/metalabel/test_wf.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write the implementation**

```python
# tradingagents/metalabel/wf.py
"""Purged expanding walk-forward over event space (AFML ch.7 adapted).

Purge rule: a train event is admissible for a test block starting at S
iff its label window has fully resolved before S minus the embargo:
touch_date < S - EMBARGO_CAL_DAYS.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

EMBARGO_CAL_DAYS = 21  # 15 trading bars ~ 21 calendar days


def purged_walk_forward(
    meta: pd.DataFrame,
    dev_start: str,
    dev_end: str,
    retrain_every_days: int = 90,
    embargo_bars: int = 15,
    min_train_events: int = 150,
) -> list[tuple[np.ndarray, np.ndarray]]:
    ev = pd.to_datetime(meta["event_date"])
    touch = pd.to_datetime(meta["touch_date"])
    start, end = pd.Timestamp(dev_start), pd.Timestamp(dev_end)

    folds = []
    block_start = start + pd.Timedelta(days=365)  # first year is train-only
    while block_start < end:
        block_end = min(block_start + pd.Timedelta(days=retrain_every_days), end)
        te = np.where((ev >= block_start) & (ev < block_end))[0]
        tr = np.where(
            (ev >= start)
            & (touch < block_start - pd.Timedelta(days=EMBARGO_CAL_DAYS))
        )[0]
        if len(te):
            if len(tr) >= min_train_events:
                folds.append((tr, te))
            else:
                warnings.warn(
                    f"fold at {block_start.date()} skipped: "
                    f"{len(tr)} < {min_train_events} train events"
                )
        block_start = block_end
    return folds
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/metalabel/test_wf.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add tradingagents/metalabel/wf.py tests/metalabel/test_wf.py
git commit -m "feat(metalabel): purged expanding walk-forward splitter with embargo"
```

---

### Task 6: Meta-model — baselines, LGB, calibration, G1 evaluation (`model.py`)

**Files:**
- Create: `tradingagents/metalabel/model.py`
- Test: `tests/metalabel/test_model.py`

**Interfaces:**
- Consumes: X/y/w frames (Task 4), folds (Task 5).
- Produces:
  - `fit_predict_fold(X_tr, y_tr, w_tr, X_te, model_type) -> np.ndarray` — calibrated P(y=1) for test rows. `model_type` ∈ {"constant", "logit", "lgb"}. LGB: inner chronological purged 3-fold CV over the 8-combo grid from freeze.json (num_leaves {15,31} × min_child_samples {20,50} × feature_fraction {0.7,1.0}; lr 0.05, n_estimators 300), best combo refit on first 80% of train (time-ordered), isotonic calibration fit on the last 20%. Logit: median-impute NaN + standardize + L2 `LogisticRegression(max_iter=1000)`, same 80/20 isotonic. Constant: train base rate everywhere.
  - `run_walk_forward(X, y, w, meta, folds, model_type) -> pd.DataFrame` — one row per OOS event: columns `p`, `y`, `w`, plus meta columns.
  - `evaluate_g1(preds_by_model: dict[str, pd.DataFrame], n_boot=2000, seed=7) -> dict` — pooled weighted AUC + Brier per model, event-bootstrap 95% CI on LGB AUC, and boolean `g1_pass` implementing gates.json: CI excludes 0.5 AND lgb_auc > logit_auc AND lgb_brier ≤ constant_brier.

- [ ] **Step 1: Write the failing test**

```python
# tests/metalabel/test_model.py
import numpy as np
import pandas as pd

from tradingagents.metalabel.model import (
    evaluate_g1, fit_predict_fold, run_walk_forward,
)


def _learnable(n=800, seed=3):
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.normal(size=(n, 5)), columns=[f"f{i}" for i in range(5)])
    logit = 1.5 * X["f0"] - 1.0 * X["f1"]
    y = pd.Series((rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int))
    w = pd.Series(np.ones(n))
    return X, y, w


def test_constant_baseline_predicts_base_rate():
    X, y, w = _learnable()
    p = fit_predict_fold(X[:600], y[:600], w[:600], X[600:], "constant")
    assert np.allclose(p, y[:600].mean())


def test_lgb_beats_chance_on_learnable_data():
    X, y, w = _learnable()
    from sklearn.metrics import roc_auc_score
    p = fit_predict_fold(X[:600], y[:600], w[:600], X[600:], "lgb")
    assert roc_auc_score(y[600:], p) > 0.65
    assert (p >= 0).all() and (p <= 1).all()


def test_lgb_handles_nan_features():
    X, y, w = _learnable()
    X.loc[::3, "f2"] = np.nan
    p = fit_predict_fold(X[:600], y[:600], w[:600], X[600:], "lgb")
    assert np.isfinite(p).all()


def test_run_walk_forward_and_g1():
    X, y, w = _learnable()
    ev = pd.date_range("2021-07-01", periods=len(X), freq="D")
    meta = pd.DataFrame({"event_date": ev, "touch_date": ev + pd.Timedelta(days=10),
                         "coin": "bitcoin"})
    folds = [(np.arange(0, 500), np.arange(500, 650)),
             (np.arange(0, 620), np.arange(650, 800))]
    preds = {m: run_walk_forward(X, y, w, meta, folds, m)
             for m in ("constant", "logit", "lgb")}
    g1 = evaluate_g1(preds, n_boot=200)
    assert {"lgb_auc", "auc_ci_low", "auc_ci_high", "logit_auc",
            "constant_brier", "lgb_brier", "g1_pass"} <= set(g1)
    assert g1["g1_pass"] in (True, False)
    assert g1["lgb_auc"] > 0.6  # learnable synthetic


def test_g1_fails_on_noise():
    rng = np.random.default_rng(0)
    n = 600
    X = pd.DataFrame(rng.normal(size=(n, 5)), columns=[f"f{i}" for i in range(5)])
    y = pd.Series(rng.integers(0, 2, n))
    w = pd.Series(np.ones(n))
    ev = pd.date_range("2021-07-01", periods=n, freq="D")
    meta = pd.DataFrame({"event_date": ev, "touch_date": ev + pd.Timedelta(days=10),
                         "coin": "bitcoin"})
    folds = [(np.arange(0, 400), np.arange(400, 600))]
    preds = {m: run_walk_forward(X, y, w, meta, folds, m)
             for m in ("constant", "logit", "lgb")}
    assert evaluate_g1(preds, n_boot=200)["g1_pass"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/metalabel/test_model.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write the implementation**

```python
# tradingagents/metalabel/model.py
"""Meta-model layer: constant / logistic baselines + LightGBM with inner
purged chronological CV over the frozen 8-combo grid, isotonic calibration
on the last 20% of train (time-ordered). G1 evaluation per gates.json."""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

LGB_GRID = {
    "num_leaves": [15, 31],
    "min_child_samples": [20, 50],
    "feature_fraction": [0.7, 1.0],
}
LGB_FIXED = {"learning_rate": 0.05, "n_estimators": 300, "objective": "binary",
             "verbosity": -1, "seed": 7}


def _fit_lgb(X, y, w, params):
    import lightgbm as lgb
    model = lgb.LGBMClassifier(**LGB_FIXED, **params)
    model.fit(X, y, sample_weight=w)
    return model


def _inner_cv_select(X, y, w):
    """Chronological 3-fold on train (row order = time order within events)."""
    n = len(X)
    edges = [0, n // 3, 2 * n // 3, n]
    best, best_auc = None, -np.inf
    for combo in itertools.product(*LGB_GRID.values()):
        params = dict(zip(LGB_GRID.keys(), combo))
        aucs = []
        for k in (1, 2):  # expanding: train [0:e_k), validate [e_k:e_{k+1})
            tr = slice(0, edges[k])
            va = slice(edges[k], edges[k + 1])
            if len(set(y.iloc[va])) < 2 or len(set(y.iloc[tr])) < 2:
                continue
            m = _fit_lgb(X.iloc[tr], y.iloc[tr], w.iloc[tr], params)
            aucs.append(roc_auc_score(y.iloc[va], m.predict_proba(X.iloc[va])[:, 1],
                                      sample_weight=w.iloc[va]))
        score = np.mean(aucs) if aucs else -np.inf
        if score > best_auc:
            best, best_auc = params, score
    return best or {k: v[0] for k, v in LGB_GRID.items()}


def _calibrated(raw_fit, X_tr, y_tr, w_tr, X_te):
    """Fit on first 80% (time order), isotonic on last 20%, predict test."""
    n = len(X_tr)
    cut = int(n * 0.8)
    model = raw_fit(X_tr.iloc[:cut], y_tr.iloc[:cut], w_tr.iloc[:cut])
    p_cal = model(X_tr.iloc[cut:])
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    if len(set(y_tr.iloc[cut:])) < 2:
        return np.clip(model(X_te), 0.0, 1.0)  # cannot calibrate; raw probs
    iso.fit(p_cal, y_tr.iloc[cut:], sample_weight=w_tr.iloc[cut:])
    return iso.predict(model(X_te))


def fit_predict_fold(X_tr, y_tr, w_tr, X_te, model_type: str) -> np.ndarray:
    if model_type == "constant":
        return np.full(len(X_te), float(np.average(y_tr, weights=w_tr)))

    if model_type == "logit":
        med = X_tr.median()
        mu, sd = X_tr.mean(), X_tr.std().replace(0, 1)

        def _fit(Xa, ya, wa):
            Z = ((Xa.fillna(med) - mu) / sd).fillna(0.0)
            clf = LogisticRegression(max_iter=1000)
            clf.fit(Z, ya, sample_weight=wa)
            return lambda Xb: clf.predict_proba(
                ((Xb.fillna(med) - mu) / sd).fillna(0.0))[:, 1]

        return _calibrated(_fit, X_tr, y_tr, w_tr, X_te)

    if model_type == "lgb":
        params = _inner_cv_select(X_tr, y_tr, w_tr)

        def _fit(Xa, ya, wa):
            m = _fit_lgb(Xa, ya, wa, params)
            return lambda Xb: m.predict_proba(Xb)[:, 1]

        return _calibrated(_fit, X_tr, y_tr, w_tr, X_te)

    raise ValueError(f"unknown model_type {model_type!r}")


def run_walk_forward(X, y, w, meta, folds, model_type: str) -> pd.DataFrame:
    rows = []
    for tr, te in folds:
        # time-order train rows for chronological inner CV / calib split
        order = np.argsort(meta.iloc[tr]["event_date"].values)
        tr_sorted = np.asarray(tr)[order]
        p = fit_predict_fold(
            X.iloc[tr_sorted], y.iloc[tr_sorted], w.iloc[tr_sorted],
            X.iloc[te], model_type,
        )
        block = meta.iloc[te].copy()
        block["p"], block["y"], block["w"] = p, y.iloc[te].values, w.iloc[te].values
        rows.append(block)
    return pd.concat(rows, ignore_index=True)


def evaluate_g1(preds_by_model: dict, n_boot: int = 2000, seed: int = 7) -> dict:
    lgb_df = preds_by_model["lgb"]
    out = {}
    for name, df in preds_by_model.items():
        out[f"{name}_auc"] = (
            roc_auc_score(df["y"], df["p"], sample_weight=df["w"])
            if len(set(df["y"])) > 1 and df["p"].nunique() > 1 else 0.5
        )
        out[f"{name}_brier"] = brier_score_loss(df["y"], df["p"], sample_weight=df["w"])

    rng = np.random.default_rng(seed)
    n = len(lgb_df)
    aucs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        s = lgb_df.iloc[idx]
        if len(set(s["y"])) < 2 or s["p"].nunique() < 2:
            continue
        aucs.append(roc_auc_score(s["y"], s["p"], sample_weight=s["w"]))
    lo, hi = (np.percentile(aucs, [2.5, 97.5]) if aucs else (0.0, 1.0))
    out["auc_ci_low"], out["auc_ci_high"] = float(lo), float(hi)
    out["n_events"] = n
    out["g1_pass"] = bool(
        lo > 0.5
        and out["lgb_auc"] > out["logit_auc"]
        and out["lgb_brier"] <= out["constant_brier"]
    )
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/metalabel/test_model.py -v`
Expected: 5 PASS (lgb tests may take ~1 min: 8-combo grid × 2 inner folds)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/metalabel/model.py tests/metalabel/test_model.py
git commit -m "feat(metalabel): baselines + LGB with inner CV, isotonic calibration, G1 eval"
```

---

### Task 7: Meta-filtered backtest + G2 (`backtest.py`)

**Files:**
- Create: `tradingagents/metalabel/backtest.py`
- Test: `tests/metalabel/test_backtest.py`

**Interfaces:**
- Consumes: OHLCV, votes, labels (Tasks 2–3), OOS predictions frame (Task 6), `paired_bootstrap` from `tradingagents/rebuild/compare.py`.
- Produces:
  - `size_multiplier(p: float, tau: float) -> float` — 0.0 if p < tau else `clip((p − tau)/(0.7 − tau), 0.25, 1.0)`.
  - `replay_coin(ohlcv, votes, labels, event_p: pd.Series | None, tau, cost_bps_rt=10.0, vol_target=0.30) -> pd.Series` — daily net log-return series for one coin. `event_p=None` → primary arm (every event multiplier 1.0). Trade lifecycle: enter at Open of event+1 bar with weight `mult × min(1, vol_target/(sigma·√365))`; exit at barrier touch (PT/SL at barrier price, vertical at close) or when vote ≤ 0.5, whichever first; cost = `cost_bps_rt/2` bps × weight change on entry and exit. Bars outside trades earn 0.
  - `portfolio_returns(per_coin_rets: dict[str, pd.Series]) -> pd.Series` — equal-weight mean across coins (NaN → 0 contribution), same rule both arms.
  - `sharpe(rets: pd.Series) -> float` — annualized √365, **SR := 0 if zero variance**.
  - `max_drawdown(rets: pd.Series) -> float` — on cumulative-sum log-equity.
  - `evaluate_g2(primary: pd.Series, meta: pd.Series) -> dict` — SRs, ΔSR, `p_pos` from `paired_bootstrap(meta, primary)`, MaxDDs, boolean `g2_pass` per gates.json (`meta_sr ≥ primary_sr` AND `p_pos ≥ 0.90` AND `meta_dd ≤ 1.1 × primary_dd`).

- [ ] **Step 1: Write the failing test**

```python
# tests/metalabel/test_backtest.py
import numpy as np
import pandas as pd
import pytest

from tradingagents.metalabel.primary import compute_votes, extract_events
from tradingagents.metalabel.labeler import triple_barrier_labels
from tradingagents.metalabel.backtest import (
    evaluate_g2, max_drawdown, portfolio_returns, replay_coin, sharpe,
    size_multiplier,
)


def _trendy(n=300, seed=5):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    c = 100 * np.exp(np.cumsum(rng.normal(0.001, 0.03, n)))
    return pd.DataFrame({"Date": idx, "Open": c, "High": c * 1.02,
                         "Low": c * 0.98, "Close": c, "Volume": 1.0})


def test_size_multiplier_contract():
    assert size_multiplier(0.40, 0.50) == 0.0
    assert size_multiplier(0.50, 0.50) == pytest.approx(0.25)  # clip floor
    assert size_multiplier(0.70, 0.50) == pytest.approx(1.0)
    assert size_multiplier(0.95, 0.50) == 1.0


def test_replay_skip_all_equals_zero_returns():
    df = _trendy()
    votes = compute_votes(df)
    labels = triple_barrier_labels(df, extract_events(votes))
    p = pd.Series(0.0, index=labels.index)  # meta rejects everything
    rets = replay_coin(df, votes, labels, p, tau=0.5)
    assert (rets.fillna(0) == 0).all()


def test_replay_meta_all_ones_equals_primary():
    df = _trendy()
    votes = compute_votes(df)
    labels = triple_barrier_labels(df, extract_events(votes))
    prim = replay_coin(df, votes, labels, None, tau=0.5)
    p = pd.Series(1.0, index=labels.index)  # mult -> 1.0 for every event
    meta = replay_coin(df, votes, labels, p, tau=0.5)
    pd.testing.assert_series_equal(prim, meta)


def test_costs_reduce_returns():
    df = _trendy()
    votes = compute_votes(df)
    labels = triple_barrier_labels(df, extract_events(votes))
    free = replay_coin(df, votes, labels, None, tau=0.5, cost_bps_rt=0.0)
    paid = replay_coin(df, votes, labels, None, tau=0.5, cost_bps_rt=10.0)
    assert paid.sum() < free.sum()


def test_sharpe_zero_variance_is_zero():
    assert sharpe(pd.Series([0.0] * 100)) == 0.0


def test_max_drawdown_positive_fraction():
    rets = pd.Series([0.1, -0.2, 0.05, -0.1])
    dd = max_drawdown(rets)
    assert 0 < dd < 1


def test_g2_pass_on_improvement():
    rng = np.random.default_rng(1)
    idx = pd.date_range("2022-01-01", periods=400, freq="D")
    prim = pd.Series(rng.normal(0.0005, 0.02, 400), index=idx)
    meta = prim + 0.002  # strictly better
    g2 = evaluate_g2(prim, meta)
    assert g2["g2_pass"] is True
    assert g2["delta_sr"] > 0


def test_portfolio_equal_weight():
    idx = pd.date_range("2022-01-01", periods=10, freq="D")
    a = pd.Series(0.02, index=idx)
    b = pd.Series(0.00, index=idx)
    port = portfolio_returns({"a": a, "b": b})
    assert np.allclose(port.values, 0.01)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/metalabel/test_backtest.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write the implementation**

```python
# tradingagents/metalabel/backtest.py
"""Meta-filtered replay of the trend primary. Both arms share every
convention (execution t+1 open, barrier exits, vol targeting, costs);
the ONLY difference is the per-event size multiplier from p-hat."""
from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.rebuild.compare import paired_bootstrap

ANN = 365.0


def size_multiplier(p: float, tau: float) -> float:
    if p < tau:
        return 0.0
    return float(np.clip((p - tau) / (0.7 - tau), 0.25, 1.0))


def replay_coin(
    ohlcv: pd.DataFrame,
    votes: pd.Series,
    labels: pd.DataFrame,
    event_p: pd.Series | None,
    tau: float,
    cost_bps_rt: float = 10.0,
    vol_target: float = 0.30,
) -> pd.Series:
    df = ohlcv.set_index(pd.DatetimeIndex(ohlcv["Date"]))
    close = df["Close"].astype(float)
    logret = np.log(close).diff()
    rets = pd.Series(0.0, index=df.index)
    half_cost = cost_bps_rt / 2.0 / 1e4

    for ev, row in labels.iterrows():
        mult = 1.0 if event_p is None else size_multiplier(float(event_p.loc[ev]), tau)
        if mult == 0.0:
            continue
        weight = mult * min(1.0, vol_target / (row["sigma"] * np.sqrt(ANN)))
        entry, touch = row["entry_exec_date"], row["touch_date"]

        # earliest exit: barrier touch OR first bar with vote <= 0.5 after entry
        window = votes.loc[entry:touch]
        weak = window[window <= 0.5]
        exit_date = min(touch, weak.index[0]) if len(weak) else touch

        span = df.loc[entry:exit_date]
        if not len(span):
            continue
        # entry bar: open -> close
        rets.loc[entry] += weight * float(
            np.log(df["Close"].loc[entry] / df["Open"].loc[entry])
        )
        # subsequent bars: close -> close
        mid = span.index[1:]
        if len(mid):
            rets.loc[mid] += weight * logret.loc[mid].fillna(0.0).values
        # barrier exits realize at barrier price, not close: adjust final bar
        if exit_date == touch and row["touch_type"] in ("pt", "sl"):
            bar_px = "pt_px" if row["touch_type"] == "pt" else "sl_px"
            prev = df["Close"].shift(1).loc[exit_date] if exit_date != entry else df["Open"].loc[entry]
            rets.loc[exit_date] += weight * (
                float(np.log(row[bar_px] / prev))
                - (float(logret.loc[exit_date]) if exit_date != entry
                   else float(np.log(df["Close"].loc[entry] / df["Open"].loc[entry])))
            )
        rets.loc[entry] -= half_cost * weight       # entry cost
        rets.loc[exit_date] -= half_cost * weight   # exit cost
    return rets


def portfolio_returns(per_coin_rets: dict) -> pd.Series:
    frame = pd.concat(per_coin_rets, axis=1).fillna(0.0)
    return frame.mean(axis=1)


def sharpe(rets: pd.Series) -> float:
    x = rets.dropna()
    if len(x) < 2 or float(x.std()) == 0.0:
        return 0.0
    return float(x.mean() / x.std() * np.sqrt(ANN))


def max_drawdown(rets: pd.Series) -> float:
    eq = rets.fillna(0.0).cumsum()
    dd = eq - eq.cummax()
    return float(-(np.exp(dd.min()) - 1.0))


def evaluate_g2(primary: pd.Series, meta: pd.Series) -> dict:
    boot = paired_bootstrap(meta, primary)
    p_sr, m_sr = sharpe(primary), sharpe(meta)
    p_dd, m_dd = max_drawdown(primary), max_drawdown(meta)
    out = {
        "primary_sr": p_sr, "meta_sr": m_sr, "delta_sr": m_sr - p_sr,
        "primary_dd": p_dd, "meta_dd": m_dd,
        "p_pos": float(boot.get("p_pos", boot.get("p_positive", np.nan))),
    }
    out["g2_pass"] = bool(
        m_sr >= p_sr and out["p_pos"] >= 0.90 and m_dd <= 1.1 * p_dd
    )
    return out
```

Note for implementer: check `paired_bootstrap`'s actual return keys in `tradingagents/rebuild/compare.py` (it returns a dict; use its ΔSR-positive-probability key — adjust the `p_pos` lookup to the real key name and delete the fallback).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/metalabel/test_backtest.py -v`
Expected: 8 PASS

- [ ] **Step 5: Commit**

```bash
git add tradingagents/metalabel/backtest.py tests/metalabel/test_backtest.py
git commit -m "feat(metalabel): meta-filtered replay, portfolio metrics, G2 evaluation"
```

---

### Task 8: Dev orchestration script (`scripts/metalabel_run.py`)

**Files:**
- Create: `scripts/metalabel_run.py`
- Test: `tests/metalabel/test_run_script.py` (unit-level on the pure helpers; the full run is executed manually in Task 9)

**Interfaces:**
- Consumes: everything above + `_load_crypto_ohlcv(coin, end_date)`, `build_pit_onchain_features(coin, dates)`, `query_fng(trade_date, lookback_days)`, `log_trial`, `assert_dev_window`.
- Produces: `data/metalabel/dev_results.json` (G1 + per-τ G2 + chosen τ), `data/metalabel/oos_predictions.csv`, ledger rows. Function `load_coin_blob(coin: str, end_date: str) -> dict` (the `per_coin` entry shape from Task 4) and `main(end_date: str = "2025-03-31") -> dict`.

- [ ] **Step 1: Write the failing test**

```python
# tests/metalabel/test_run_script.py
import pandas as pd
import pytest

import scripts.metalabel_run as run


def test_dev_end_inside_dev_window():
    from tradingagents.rebuild.ledger import assert_dev_window
    assert_dev_window(run.DEV_END)  # must not raise


def test_tau_selection_prefers_passing_then_delta_sr():
    rows = [
        {"tau": 0.45, "g2_pass": False, "delta_sr": 0.9},
        {"tau": 0.50, "g2_pass": True, "delta_sr": 0.3},
        {"tau": 0.55, "g2_pass": True, "delta_sr": 0.5},
    ]
    assert run.select_tau(rows) == 0.55


def test_tau_selection_none_pass_returns_none():
    rows = [{"tau": 0.45, "g2_pass": False, "delta_sr": 0.1}]
    assert run.select_tau(rows) is None


def test_fng_series_shape(monkeypatch):
    # query_fng wrapper must return a date-indexed float series
    calls = {}
    def fake_query(trade_date, lookback_days=7, **kw):
        calls["hit"] = True
        return pd.DataFrame({"value": [55]})
    monkeypatch.setattr(run, "query_fng", fake_query)
    s = run.fng_series(pd.date_range("2023-01-01", periods=3, freq="D"))
    assert isinstance(s, pd.Series) and len(s) == 3 and calls["hit"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/metalabel/test_run_script.py -v`
Expected: FAIL with ImportError/AttributeError

- [ ] **Step 3: Write the implementation**

```python
# scripts/metalabel_run.py
"""Dev walk-forward for the meta-labeled trend system (G1 + G2).

Usage: uv run python scripts/metalabel_run.py
Never reaches into the holdout: assert_dev_window(DEV_END) guards every run.
Every invocation logs one ledger row per (model, tau) evaluated.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv
from tradingagents.dataflows.fng_store import query_fng
from tradingagents.dataflows.onchain_features import build_pit_onchain_features
from tradingagents.metalabel.backtest import (
    evaluate_g2, portfolio_returns, replay_coin,
)
from tradingagents.metalabel.features import assemble_dataset
from tradingagents.metalabel.labeler import triple_barrier_labels, uniqueness_weights
from tradingagents.metalabel.model import evaluate_g1, run_walk_forward
from tradingagents.metalabel.primary import compute_votes, extract_events
from tradingagents.metalabel.wf import purged_walk_forward
from tradingagents.rebuild.ledger import assert_dev_window, log_trial

FREEZE = json.loads(
    (Path(__file__).resolve().parents[1] / "experiments/metalabel/freeze.json").read_text()
)
COINS = FREEZE["coins"]
DEV_START, DEV_END = FREEZE["dev_window"]
TAU_GRID = FREEZE["tau_grid"]
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "metalabel"


def fng_series(dates: pd.DatetimeIndex) -> pd.Series:
    vals = {}
    for d in dates:
        try:
            df = query_fng(d.to_pydatetime(), lookback_days=7)
            vals[d] = float(df["value"].iloc[-1]) if len(df) else np.nan
        except Exception:
            vals[d] = np.nan
    return pd.Series(vals)


def load_coin_blob(coin: str, end_date: str) -> dict:
    ohlcv = _load_crypto_ohlcv(coin, end_date)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    ohlcv = ohlcv[ohlcv["Date"] >= pd.Timestamp(DEV_START) - pd.Timedelta(days=120)]
    ohlcv = ohlcv.reset_index(drop=True)
    votes = compute_votes(ohlcv)
    events = extract_events(votes)
    events = events[(events >= DEV_START) & (events <= end_date)]
    labels = triple_barrier_labels(ohlcv, events)
    weights = (uniqueness_weights(labels, pd.DatetimeIndex(ohlcv["Date"]))
               if len(labels) else pd.Series(dtype=float))
    ev_idx = pd.DatetimeIndex(labels.index) if len(labels) else pd.DatetimeIndex([])
    try:
        onchain = build_pit_onchain_features(coin, ev_idx) if len(ev_idx) else None
    except Exception as exc:  # missing store coverage -> NaN features, logged
        print(f"[warn] onchain features unavailable for {coin}: {exc}")
        onchain = None
    return {
        "ohlcv": ohlcv, "votes": votes, "labels": labels, "weights": weights,
        "onchain": onchain, "fng": fng_series(ev_idx) if len(ev_idx) else None,
    }


def select_tau(rows: list[dict]) -> float | None:
    passing = [r for r in rows if r["g2_pass"]]
    if not passing:
        return None
    return max(passing, key=lambda r: r["delta_sr"])["tau"]


def coverage_report(X: pd.DataFrame) -> dict:
    return {c: round(1.0 - float(X[c].isna().mean()), 3) for c in X.columns}


def main(end_date: str = DEV_END) -> dict:
    assert_dev_window(end_date)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    per_coin = {c: load_coin_blob(c, end_date) for c in COINS}
    X, y, w, meta = assemble_dataset(per_coin)
    print(f"events: {len(X)} | coverage: {json.dumps(coverage_report(X))}")

    folds = purged_walk_forward(
        meta, DEV_START, end_date,
        retrain_every_days=FREEZE["wf"]["retrain_every_days"],
        min_train_events=FREEZE["wf"]["min_train_events"],
    )
    preds = {m: run_walk_forward(X, y, w, meta, folds, m)
             for m in ("constant", "logit", "lgb")}
    g1 = evaluate_g1(preds)
    log_trial("metalabel-g1", {"models": list(preds)}, (DEV_START, end_date), g1)
    print(f"G1: {json.dumps(g1, default=float)}")

    results = {"g1": g1, "g2": [], "chosen_tau": None}
    if g1["g1_pass"]:
        lgb_preds = preds["lgb"].set_index(["coin", "event_date"])["p"]
        prim_port = portfolio_returns({
            c: replay_coin(b["ohlcv"], b["votes"], b["labels"], None, tau=0.5)
            for c, b in per_coin.items() if len(b["labels"])
        })
        for tau in TAU_GRID:
            meta_port = portfolio_returns({
                c: replay_coin(
                    b["ohlcv"], b["votes"], b["labels"],
                    lgb_preds.loc[c] if c in lgb_preds.index.get_level_values(0) else None,
                    tau=tau,
                )
                for c, b in per_coin.items() if len(b["labels"])
            })
            g2 = evaluate_g2(prim_port, meta_port) | {"tau": tau}
            log_trial("metalabel-g2", {"tau": tau}, (DEV_START, end_date), g2)
            results["g2"].append(g2)
            print(f"G2 tau={tau}: {json.dumps(g2, default=float)}")
        results["chosen_tau"] = select_tau(results["g2"])

    preds["lgb"].to_csv(OUT_DIR / "oos_predictions.csv", index=False)
    (OUT_DIR / "dev_results.json").write_text(json.dumps(results, indent=2, default=float))
    print(f"chosen_tau: {results['chosen_tau']}")
    return results


if __name__ == "__main__":
    main()
```

**Important:** G2 as coded replays only OOS-covered events; events before the first test block have no p̂. The implementer must restrict BOTH arms to events with OOS predictions (filter `labels` to `meta` rows present in `preds["lgb"]` for each coin) so the comparison is apples-to-apples. Add this filter inside `main` before building `prim_port`/`meta_port` (join `labels` on `lgb_preds` index per coin) — the test suite for Task 8 covers helpers only; correctness here is verified by the Task 9 smoke checks.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/metalabel/test_run_script.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/metalabel_run.py tests/metalabel/test_run_script.py
git commit -m "feat(metalabel): dev walk-forward orchestration with ledger logging"
```

---

### Task 9: Full-suite green + dev smoke verification

**Files:**
- Modify: whatever the smoke run reveals (fix-forward)
- Test: full suite + manual smoke checks

- [ ] **Step 1: Run the entire test suite**

Run: `uv run pytest -q`
Expected: all metalabel tests pass; pre-existing suite stays green (487+ baseline; 2 known pre-existing failures in `test_parity_script.py` are acceptable — do not fix, they predate this branch).

- [ ] **Step 2: OC_FEATURES name reconciliation**

Run: `uv run python -c "
from tradingagents.dataflows.onchain_features import build_pit_onchain_features
import pandas as pd
f = build_pit_onchain_features('bitcoin', pd.date_range('2024-01-01', periods=5, freq='D'))
print(sorted(c for c in f.columns if 'z' in c or 'funding' in c or 'oi' in c or 'liq' in c or 'smart' in c or 'taker' in c or 'basis' in c or 'mvrv' in c or 'Adr' in c or 'flow' in c))
"`
Compare printed names against `OC_FEATURES` in `tradingagents/metalabel/features.py`; replace any mismatched entries (e.g. active-address / net-flow / MVRV z-score names) with the real column names. Update the Task 4 test only if a listed name has no real counterpart at all.

- [ ] **Step 3: Single-coin smoke run (BTC, short window)**

Run: `uv run python -c "
import scripts.metalabel_run as r
blob = r.load_coin_blob('bitcoin', '2023-12-31')
print('events:', len(blob['labels']))
print('label base rate:', blob['labels']['label'].mean().round(3))
print('touch types:', blob['labels']['touch_type'].value_counts().to_dict())
print('onchain cols:', 0 if blob['onchain'] is None else blob['onchain'].shape[1])
"`
Expected: events ≥ 10, base rate strictly between 0.2 and 0.8, all three touch types present, onchain cols > 0. Investigate before proceeding if any check fails (systematic-debugging skill).

- [ ] **Step 4: Fix anything the smoke run surfaced, re-run suite**

Run: `uv run pytest tests/metalabel/ -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "fix(metalabel): reconcile OC feature names + smoke-run fixes"
```

---

### Task 10: Holdout one-shot script (`scripts/metalabel_holdout.py`) — build only, DO NOT RUN

**Files:**
- Create: `scripts/metalabel_holdout.py`
- Test: `tests/metalabel/test_holdout_script.py`

**Interfaces:**
- Consumes: `data/metalabel/dev_results.json` (`chosen_tau`), freeze.json, all Task 2–7 functions, `log_trial(..., allow_holdout=True)`.
- Produces: `main() -> dict` that refuses to run when `chosen_tau` is None or when a sentinel file `data/metalabel/holdout_spent.flag` exists; on success trains once on full dev, predicts holdout events, replays both arms on 2025-04-01…2026-06-30, writes `data/metalabel/holdout_results.json` + creates the sentinel.

- [ ] **Step 1: Write the failing test**

```python
# tests/metalabel/test_holdout_script.py
import json
import pytest

import scripts.metalabel_holdout as h


def test_refuses_without_chosen_tau(tmp_path, monkeypatch):
    res = tmp_path / "dev_results.json"
    res.write_text(json.dumps({"chosen_tau": None}))
    monkeypatch.setattr(h, "DEV_RESULTS", res)
    with pytest.raises(RuntimeError, match="G2 did not pass"):
        h.main()


def test_refuses_when_already_spent(tmp_path, monkeypatch):
    res = tmp_path / "dev_results.json"
    res.write_text(json.dumps({"chosen_tau": 0.5}))
    flag = tmp_path / "holdout_spent.flag"
    flag.write_text("spent")
    monkeypatch.setattr(h, "DEV_RESULTS", res)
    monkeypatch.setattr(h, "SPENT_FLAG", flag)
    with pytest.raises(RuntimeError, match="already spent"):
        h.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/metalabel/test_holdout_script.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write the implementation**

```python
# scripts/metalabel_holdout.py
"""G3 holdout one-shot. RUN AT MOST ONCE, only after G1+G2 pass on dev.

Trains the frozen pipeline on the full dev window, predicts holdout events,
replays both arms on the locked holdout (2025-04-01..2026-06-30), writes
holdout_results.json and a spent-flag that makes any re-run raise."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.metalabel.backtest import evaluate_g2, portfolio_returns, replay_coin
from tradingagents.metalabel.features import assemble_dataset
from tradingagents.metalabel.model import fit_predict_fold
from tradingagents.rebuild.ledger import log_trial

from scripts.metalabel_run import FREEZE, load_coin_blob

DEV_RESULTS = Path(__file__).resolve().parents[1] / "data/metalabel/dev_results.json"
SPENT_FLAG = Path(__file__).resolve().parents[1] / "data/metalabel/holdout_spent.flag"
HOLDOUT_START, HOLDOUT_END = FREEZE["holdout_window"]
DEV_START, DEV_END = FREEZE["dev_window"]


def main() -> dict:
    dev = json.loads(DEV_RESULTS.read_text())
    tau = dev.get("chosen_tau")
    if tau is None:
        raise RuntimeError("G3 refused: G2 did not pass on dev (chosen_tau is None)")
    if SPENT_FLAG.exists():
        raise RuntimeError("G3 refused: holdout already spent (one-shot)")

    per_coin = {c: load_coin_blob(c, HOLDOUT_END) for c in FREEZE["coins"]}
    X, y, w, meta = assemble_dataset(per_coin)
    is_dev = meta["event_date"] <= pd.Timestamp(DEV_END)
    is_hold = meta["event_date"] >= pd.Timestamp(HOLDOUT_START)

    order = np.argsort(meta[is_dev]["event_date"].values)
    meta_dev_sorted = meta[is_dev].iloc[order][["event_date", "touch_date"]].reset_index(drop=True)
    p_hold = fit_predict_fold(
        X[is_dev].iloc[order], y[is_dev].iloc[order], w[is_dev].iloc[order],
        X[is_hold], "lgb", meta_tr=meta_dev_sorted,
    )
    p_series = pd.Series(p_hold, index=pd.MultiIndex.from_frame(
        meta[is_hold][["coin", "event_date"]]))

    prim, metaarm = {}, {}
    for c, b in per_coin.items():
        labels_h = b["labels"][b["labels"].index >= pd.Timestamp(HOLDOUT_START)]
        if not len(labels_h):
            continue
        prim[c] = replay_coin(b["ohlcv"], b["votes"], labels_h, None, tau=tau)
        pc = p_series.loc[c] if c in p_series.index.get_level_values(0) else None
        metaarm[c] = replay_coin(b["ohlcv"], b["votes"], labels_h, pc, tau=tau)

    span = slice(pd.Timestamp(HOLDOUT_START), pd.Timestamp(HOLDOUT_END))
    prim_port = portfolio_returns(prim).loc[span]
    meta_port = portfolio_returns(metaarm).loc[span]
    g3 = evaluate_g2(prim_port, meta_port) | {"tau": tau, "n_holdout_events": int(is_hold.sum())}
    g3["g3_pass"] = bool(
        g3["delta_sr"] > 0 and (g3["meta_sr"] > 0 or g3["meta_sr"] > g3["primary_sr"])
    )

    log_trial("metalabel-g3", {"tau": tau}, (HOLDOUT_START, HOLDOUT_END), g3,
              allow_holdout=True)
    out = DEV_RESULTS.parent / "holdout_results.json"
    out.write_text(json.dumps(g3, indent=2, default=float))
    SPENT_FLAG.write_text(pd.Timestamp.now().isoformat())
    print(json.dumps(g3, indent=2, default=float))
    return g3


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/metalabel/test_holdout_script.py -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/metalabel_holdout.py tests/metalabel/test_holdout_script.py
git commit -m "feat(metalabel): G3 holdout one-shot script with spent-flag guard"
```

---

## Execution notes (not tasks)

- After Task 10, the DEV RUN itself (`uv run python scripts/metalabel_run.py`) is an experiment, not implementation — run it once, report G1/G2 to the user, and stop for a decision before any holdout action. Expect ~10–60 min depending on OHLCV/feature cache warmth. Disk is tight (~9 GB free): do not download new datasets; all stores exist.
- G1 fail → document negative (THESIS §44 skeleton), no G2/G3.
- G3 execution requires explicit user sign-off even after G2 passes.
