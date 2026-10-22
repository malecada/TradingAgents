# B7 Feature and Target Engineering — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-engineer the 54 hourly on-chain series of B4 and B6 into multi-scale, deseasonalised features with event-time and interaction terms, add jump and largest-move targets, and compare the new sets against B4's transforms and a price/range/option-market baseline with ridge, early-stopped trees and B4's fixed trees on two tracks.

**Architecture:** New package `tradingagents/research/onchain_b7/` importing B2 (`fit_predict`, `folds`, `row_loss`), B4 (`zscore`, `price_features`, `hourly_targets`, `interval`, `hourmarket`), B5 (`px_features`) primitives. `features7` (seasonal profile, multi-scale, event-time, interactions), `targets7` (range features, J and M targets), `models7` (families incl. time-ordered early stopping), `forecast7` (samples, predictions, comparisons, criteria, tables), `cli` (features, forecast, report; the forecast stage is resumable per track and target).

**Tech Stack:** Python 3.13, numpy, pandas, pyarrow, scikit-learn 1.7 (HistGradientBoosting `staged_predict`), pytest; systemd user unit for the forecast stage.

**Spec:** `docs/superpowers/specs/2026-10-22-onchain-b7-feature-target-engineering-design.md`

## Global Constraints

- Exploratory with a pre-declared plan: `research/onchain-b7-2026-10-22/PLAN.md` committed before any B7 table is built; every comparison reported.
- No new chain data; inputs are the B4/B6 hourly tables, B6 large-transfer records, B4 hourly bars, B6 1-minute ETH closes and B6's option-market columns.
- New-engineering columns are named `n_<series>__<ex1|z1|s6z|s24z|s168z|burst>`; event-time `ev_since_10m`, `ev_since_50m`; interactions `ix_*`; range `rg_range1`, `rg_range24`.
- Sets by prefix: base `h0_`, `px_`, `rg_` (+ `mk_` in track B); X1 = + `eth_`, `stable_`; X1a = + `eth_`, `stable_`, `act_`; Y1 = + `n_eth_`, `n_stable_`, `n_act_`, `ev_`, `ix_`; Y2 = Y1 + `n_gs_`, `n_tk_`, `n_cl_`, `n_is_`.
- Targets V6, V24 (B4), J6, J24 (3·σ̂·√k, σ̂ from the previous 720 h, min 480), M6, M24 (largest absolute 5-minute log return in the next k hours, ≥ 95 % of the window present, floor 1e-6).
- Models: ridge/logistic via B2 alpha search (inner 8,760, fallback 100); trees_es lr 0.05, 15 leaves, min leaf 50, l2 1.0, seed 11, ≤ 600 iterations, iteration count from the time-ordered last 10 % of training (min 20), refit; trees_fixed = B4 settings (sklearn's default `early_stopping='auto'` applies for n > 10,000, as in B4 and B6).
- Tracks A′ 2019-04-01 → 2024-12-31 (test years 2020–2024; criterion upper < 0 and ≥ 3/5 years), B 2021-04-01 → 2026-10-12 (test years 2022–2026; groups 2022–24, 2025–26; upper < 0 in 2022–24 and mean < 0 in 2025–26). Bootstrap block 168, 2,000 draws, seed 20261022; min_train 2,000; purge = horizon.
- `onchain_b` … `onchain_b6` imported, not edited. Docs impersonal. Commits end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Package test command: `.venv/bin/python -m pytest tests/research/onchain_b7 -q`.

## Review Focus

1. The seasonal profile must use only earlier weeks: changing any later value leaves the feature at h unchanged, and fewer than 4 earlier occurrences give NaN (Task 2 `test_seasonal_excess_is_causal_and_needs_four_occurrences`).
2. An hour with fewer than 30 minute closes (exchange outage) gives a NaN range, never 0 or inf; an M window with more than 5 % missing returns is NaN (Task 3 `test_range_features_require_minutes`, `test_mmax_alignment_and_missing`).
3. J targets are NaN, not 0, while σ̂ is unavailable (first 480 hours) and at the tail where the future return is unknown (Task 3 `test_jump_targets_threshold_and_warmup`).
4. trees_es must not crash when the training head or the whole training window holds a single class (Task 4 `test_fit_predict7_single_class_fallback`).
5. A forecast stage killed mid-way resumes by skipping finished (track, target) units and rebuilds `results.json` from the unit files (Task 6 `test_forecast_stage_resumes_per_unit`).

---

### Task 1: Skeleton, configuration, registration

**Files:**
- Create: `tradingagents/research/onchain_b7/__init__.py` (empty), `tradingagents/research/onchain_b7/config.py`
- Create: `research/onchain-b7-2026-10-22/config/b7.json`, `CHARTER.md`, `PLAN.md`, `STATE.md`
- Modify: `.gitignore` (add `/research_artifacts/onchain-b7/`)
- Test: `tests/research/onchain_b7/__init__.py` (empty), `tests/research/onchain_b7/test_config.py`

**Interfaces:**
- Produces: `config.ROOT/STUDY/ARTIFACTS/B4_ARTIFACTS/B6_ARTIFACTS`; `config.load() -> dict`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b7/test_config.py
from tradingagents.research.onchain_b7 import config


def test_config_series_sets_tracks_and_targets():
    c = config.load()
    assert len(c['series']['b4']) == 15 and len(c['series']['b6']) == 39
    assert c['sets'] == {'X0': [], 'X1': ['F'], 'X1a': ['FA'], 'Y1': ['N4'], 'Y2': ['N4', 'N6']}
    assert c['set_comparisons'] == [['Y1', 'X1'], ['Y1', 'X1a'], ['Y2', 'Y1'], ['X1', 'X0'], ['Y2', 'X0']]
    assert c['cross_comparisons'] == [[['trees_es', 'Y2'], ['trees_fixed', 'Y2']]]
    assert c['tracks']['A']['test_years'] == [2020, 2021, 2022, 2023, 2024] and c['tracks']['A']['min_year_wins'] == 3
    assert c['tracks']['B']['groups'] == {'2022-24': [2022, 2023, 2024], '2025-26': [2025, 2026]}
    assert set(c['targets']) == {'V6', 'V24', 'J6', 'J24', 'M6', 'M24'} and c['targets']['J6']['task'] == 'classification'
    assert c['models']['trees_es']['max_iter'] == 600 and c['gate']['seed'] == 20261022


def test_registration_files_exist():
    for name in ('CHARTER.md', 'PLAN.md', 'STATE.md'):
        assert (config.STUDY / name).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_config.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.research.onchain_b7'`

- [ ] **Step 3: Write config module, config file, study docs, gitignore**

```python
# tradingagents/research/onchain_b7/config.py
"""Frozen B7 configuration (research/onchain-b7-2026-10-22/config/b7.json)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b7-2026-10-22'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b7'
B4_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b4'
B6_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b6'


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b7.json').read_text())
```

`research/onchain-b7-2026-10-22/config/b7.json`:

```json
{
 "series": {
  "b4": ["eth_in_val", "eth_out_val", "eth_in_cnt", "eth_out_cnt", "eth_big_in",
         "stable_in_val", "stable_out_val", "stable_in_cnt", "stable_out_cnt", "stable_big_in",
         "act_gas_price", "act_gas_used", "act_tx_count", "act_eth_transfers", "act_eth_value"],
  "b6": ["gs_active", "gs_new_share", "gs_edges", "gs_edges_per_node", "gs_value_gini", "gs_top10_share",
         "gs_core2_share", "gs_giant_share", "gs_ex_cp", "gs_ex_cp_new_share", "gs_cex_cex_usd",
         "tk_usdt_in", "tk_usdt_out", "tk_usdc_in", "tk_usdc_out", "tk_dai_in", "tk_dai_out",
         "cl_dex_stable_in", "cl_dex_stable_out", "cl_dex_eth_in", "cl_dex_eth_out",
         "cl_bridge_stable_in", "cl_bridge_stable_out", "cl_bridge_eth_in", "cl_bridge_eth_out",
         "cl_mev_stable_in", "cl_mev_stable_out", "cl_mev_eth_in", "cl_mev_eth_out",
         "cl_funds_stable_in", "cl_funds_stable_out", "cl_funds_eth_in", "cl_funds_eth_out",
         "is_usdc_mint", "is_usdc_burn", "is_dai_mint", "is_dai_burn", "is_usdt_treasury_out", "is_usdt_treasury_in"]},
 "engineering": {"profile_weeks": 8, "profile_min": 4, "z1_window": 168, "z1_min": 120,
                 "s6_window": 720, "s6_min": 480, "s24_window": 720, "s24_min": 480,
                 "s168_window": 2160, "s168_min": 1440, "burst_window": 24, "clip": 10.0},
 "events": {"thresholds": {"10m": 10000000.0, "50m": 50000000.0}, "cap_hours": 168},
 "interactions": [["ix_stable_val_rv6", "n_stable_in_val__ex1", "px_rv6"],
                  ["ix_stable_cnt_rv24", "n_stable_in_cnt__ex1", "h0_rv24"],
                  ["ix_eth_val_rv6", "n_eth_in_val__ex1", "px_rv6"]],
 "range": {"min_minutes": 30, "window24": 24},
 "jump": {"sigma_window": 720, "sigma_min": 480, "mult": 3.0},
 "mmax": {"spacing_min": 5, "min_share": 0.95, "floor": 1e-6},
 "targets": {"V6": {"h": 6, "task": "regression"}, "V24": {"h": 24, "task": "regression"},
             "J6": {"h": 6, "task": "classification"}, "J24": {"h": 24, "task": "classification"},
             "M6": {"h": 6, "task": "regression"}, "M24": {"h": 24, "task": "regression"}},
 "blocks": {"base": ["h0_", "px_", "rg_"], "F": ["eth_", "stable_"], "FA": ["eth_", "stable_", "act_"],
            "N4": ["n_eth_", "n_stable_", "n_act_", "ev_", "ix_"], "N6": ["n_gs_", "n_tk_", "n_cl_", "n_is_"]},
 "sets": {"X0": [], "X1": ["F"], "X1a": ["FA"], "Y1": ["N4"], "Y2": ["N4", "N6"]},
 "families": ["ridge", "trees_es"],
 "extra_fits": [["trees_fixed", "Y2"]],
 "set_comparisons": [["Y1", "X1"], ["Y1", "X1a"], ["Y2", "Y1"], ["X1", "X0"], ["Y2", "X0"]],
 "cross_comparisons": [[["trees_es", "Y2"], ["trees_fixed", "Y2"]]],
 "tracks": {
  "A": {"start": "2019-04-01", "end": "2024-12-31", "test_years": [2020, 2021, 2022, 2023, 2024],
        "groups": {"2020-24": [2020, 2021, 2022, 2023, 2024]}, "base_extra": [], "criterion": "years", "min_year_wins": 3},
  "B": {"start": "2021-04-01", "end": "2026-10-12", "test_years": [2022, 2023, 2024, 2025, 2026],
        "groups": {"2022-24": [2022, 2023, 2024], "2025-26": [2025, 2026]}, "base_extra": ["mk_"], "criterion": "groups"}},
 "folds": {"inner_len": 8760, "min_train": 2000},
 "models": {"alphas": [0.1, 1, 10, 100, 1000, 10000, 100000], "fallback_alpha": 100.0,
            "trees": {"max_iter": 100, "learning_rate": 0.05, "max_leaf_nodes": 7, "min_samples_leaf": 30,
                      "l2_regularization": 1.0, "random_state": 11},
            "trees_es": {"max_iter": 600, "learning_rate": 0.05, "max_leaf_nodes": 15, "min_samples_leaf": 50,
                         "l2_regularization": 1.0, "random_state": 11, "tail_frac": 0.1, "min_iter": 20}},
 "gate": {"draws": 2000, "seed": 20261022, "block": 168, "chunk": 100}
}
```

`research/onchain-b7-2026-10-22/CHARTER.md`:

```markdown
# B7 charter — feature and target engineering on the hourly on-chain tables

Registered 2026-10-22 before any B7 table is built. Spec:
`docs/superpowers/specs/2026-10-22-onchain-b7-feature-target-engineering-design.md`.

## Questions

Q1 Do multi-scale, deseasonalised features of the same hourly series (plus event-time and
interaction terms) carry more volatility information than B4's two transforms, and does an
early-stopped, larger tree model beat B4's fixed trees? Q2 Do on-chain features forecast
tail moves (|return| > 3σ̂√k) and the size of the largest 5-minute move, beyond what price
history, intraday range and the option market give?

## Framing

Exploratory with a pre-declared plan (`PLAN.md`). The ETH 2025–26 window was opened in
B4–B6; nothing here is a sealed test. Targets are volatility-type only (levels, tails,
largest move); no direction or return targets.

## Disclosures

- Inputs are B4's and B6's hourly tables and B6's large-transfer records, so the label
  disclosures of B4 and B6 (2026 label snapshot, day-after activation, identity look-ahead)
  carry over.
- Binance 1-minute closes stand in for the market; the 4,111 missing minutes make the
  affected hours' range features and M targets missing.
- Minute closes start 2019-01-01, so track A′ starts 2019-04-01 (shorter than B6's track A).
- The 2025–26 group of track B is read with a sign-only criterion and labelled as such.
```

`research/onchain-b7-2026-10-22/PLAN.md`:

```markdown
# B7 pre-declared analysis plan (committed before any B7 table is built)

All items run once; `RESULTS.md` reports every row, including negatives.

## Comparisons

Tracks A′ (2019-04-01 → 2024-12-31; test years 2020–2024; group 2020–24) and B
(2021-04-01 → 2026-10-12; test years 2022–2026; groups 2022–24 and 2025–26). Targets V6,
V24 (log realised volatility of hourly returns, next 6 / 24 h), J6, J24 (1 if |log return
over the next 6 / 24 h| > 3·σ̂·√k, σ̂² = mean squared hourly return over the previous 720
hours; log loss), M6, M24 (log of the largest absolute 5-minute log return in the next 6 /
24 h; squared error). Sets X0 = price (`h0_`), intraday (`px_`), range (`rg_`), plus DVOL
and near-expiry implied volatility (`mk_`) in track B; X1 = X0 + B4's 22 flow columns;
X1a = X0 + B4's transforms of all 15 series; Y1 = X0 + the new engineering of the 15 B4
series + event-time + interactions; Y2 = Y1 + the new engineering of the 39 B6 series.
Families ridge (logistic for J) and trees_es; trees_fixed on Y2 only.

Per track, target and family: Y1 vs X1, Y1 vs X1a, Y2 vs Y1, X1 vs X0, Y2 vs X0; plus
trees_es(Y2) vs trees_fixed(Y2): 11 comparisons × 6 targets × 2 tracks = 132 (track B
rows per group). Statistics: mean per-row loss difference, 95 % circular block-bootstrap
interval (block 168 rows, 2,000 draws, seed 20261022), per-year differences, the loss of
a constant forecast (training mean or base rate) for every row.

Positive reading: A′ — upper end < 0 and better in ≥ 3 of 5 years; B — upper end < 0 in
2022–24 and mean difference < 0 in 2025–26 (the 2025–26 row alone is sign-only and is
labelled so). With 132 comparisons about 7 interval passes are expected by chance; a
result counts as a finding only if it holds in both families or both tracks.

Reading guide: Q1 — Y1 vs X1, Y1 vs X1a, Y2 vs Y1 and trees_es vs trees_fixed on V6/V24;
Q2 — X1 vs X0 and Y2 vs X0 on J and M targets, with V6/V24 as the reference.

## Reporting

`TABLES.md` (generated) holds every row with chosen alphas and iteration counts per fold;
`RESULTS.md` reads them. Post hoc additions are labelled.
```

`research/onchain-b7-2026-10-22/STATE.md`:

```markdown
# Branch B7 state

2026-10-22 — Registered (charter, config, pre-declared plan). No B7 table built yet.
```

Append to `.gitignore` after the `onchain-b6` entry:

```
# B7 artifacts (hourly tables, predictions)
/research_artifacts/onchain-b7/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_config.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b7/__init__.py tradingagents/research/onchain_b7/config.py research/onchain-b7-2026-10-22 tests/research/onchain_b7/__init__.py tests/research/onchain_b7/test_config.py .gitignore
git commit -m "feat(onchain-b7): skeleton, configuration and registration"
```

---

### Task 2: features7 — seasonal excess, multi-scale, event-time, interactions

**Files:**
- Create: `tradingagents/research/onchain_b7/features7.py`
- Test: `tests/research/onchain_b7/test_features7.py`

**Interfaces:**
- Consumes: `onchain_b4.dataset4.zscore(x, window, min_periods, clip)`.
- Produces: `seasonal_excess(x: Series, weeks, min_occ) -> Series`; `multiscale(raw: DataFrame, c) -> DataFrame` (6 columns per series, `n_<name>__<kind>`); `event_hours(large: DataFrame[ts, token, amount, direction], index, thresholds: dict, cap) -> DataFrame[ev_since_<name>]`; `interactions(table, spec) -> DataFrame`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b7/test_features7.py
import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b7 import config, features7 as F

CFG = config.load()


def _weekly(n_weeks, rng):
    idx = pd.date_range('2024-01-01', periods=168 * n_weeks, freq='h')
    slot = idx.dayofweek * 24 + idx.hour
    return pd.Series(100.0 + 5.0 * slot + rng.normal(0, 0.1, len(idx)), index=idx)


def test_seasonal_excess_is_causal_and_needs_four_occurrences():
    rng = np.random.default_rng(1)
    x = _weekly(12, rng)
    a = F.seasonal_excess(x, 8, 4)
    assert a.iloc[:4 * 168].isna().all() and a.iloc[4 * 168:].notna().all()
    assert np.abs(a.iloc[4 * 168:]).max() < 0.01                             # the profile removes the weekly pattern
    y = x.copy()
    y.iloc[10 * 168 + 5] = 1e6                                               # one spike in week 10
    b = F.seasonal_excess(y, 8, 4)
    pd.testing.assert_series_equal(a.iloc[:10 * 168 + 5], b.iloc[:10 * 168 + 5])   # nothing earlier changes
    assert b.iloc[10 * 168 + 5] > 5                                          # the spike hour is far above its profile
    assert np.isclose(b.iloc[11 * 168 + 5], a.iloc[11 * 168 + 5], atol=0.05)   # median profile ignores one spike
    with pytest.raises(ValueError):
        F.seasonal_excess(x.iloc[[0, 1, 5]], 8, 4)


def test_multiscale_columns_windows_end_at_h():
    rng = np.random.default_rng(2)
    idx = pd.date_range('2023-01-01', periods=3000, freq='h')
    raw = pd.DataFrame({'eth_in_val': rng.gamma(2, 3, 3000), 'gs_active': rng.gamma(2, 3, 3000)}, index=idx)
    a = F.multiscale(raw, CFG['engineering'])
    kinds = {'ex1', 'z1', 's6z', 's24z', 's168z', 'burst'}
    assert set(a.columns) == {f'n_{s}__{k}' for s in raw.columns for k in kinds}
    b = F.multiscale(raw.assign(eth_in_val=raw['eth_in_val'].where(raw.index < idx[2500], 999.0)), CFG['engineering'])
    pd.testing.assert_frame_equal(a.iloc[:2500], b.iloc[:2500])              # future values never leak backwards
    assert b['n_eth_in_val__burst'].iloc[2500] > a['n_eth_in_val__burst'].iloc[2500]   # the hour's own value counts
    assert a['n_eth_in_val__s168z'].iloc[2400:].notna().all() and a['n_eth_in_val__s168z'].iloc[:1600].isna().all()
    assert a.abs().max().max() <= CFG['engineering']['clip']


def test_event_hours_since_last_large_deposit():
    idx = pd.date_range('2024-03-01', periods=400, freq='h')
    t = lambda s: int(pd.Timestamp(s, tz='UTC').timestamp())
    large = pd.DataFrame({'ts': [t('2024-03-02 10:30'), t('2024-03-02 11:10'), t('2024-03-05 00:00'), t('2024-03-06 03:00')],
                          'token': [1, 0, 2, 1], 'amount': [2e7, 9e3, 6e7, 1.2e7], 'direction': [1, 1, 1, -1]})
    e = F.event_hours(large, idx, CFG['events']['thresholds'], 168)
    h = lambda s: pd.Timestamp(s)
    assert list(e.columns) == ['ev_since_10m', 'ev_since_50m']
    assert e.loc[h('2024-03-02 09:00'), 'ev_since_10m'] == np.log1p(168)     # before the first event: capped
    assert e.loc[h('2024-03-02 10:00'), 'ev_since_10m'] == 0.0               # event inside the hour counts at its end
    assert e.loc[h('2024-03-02 11:00'), 'ev_since_10m'] == np.log1p(1)       # the ETH deposit does not count
    assert e.loc[h('2024-03-05 00:00'), 'ev_since_50m'] == 0.0 and e.loc[h('2024-03-04 23:00'), 'ev_since_50m'] == np.log1p(168)
    assert e.loc[h('2024-03-06 03:00'), 'ev_since_10m'] == np.log1p(27)      # withdrawals do not count
    assert e['ev_since_10m'].max() == np.log1p(168)


def test_interactions_are_products():
    idx = pd.date_range('2024-01-01', periods=3, freq='h')
    t = pd.DataFrame({'a': [1.0, 2.0, np.nan], 'b': [3.0, 0.5, 1.0]}, index=idx)
    out = F.interactions(t, [['ix_ab', 'a', 'b']])
    assert list(out.columns) == ['ix_ab'] and out['ix_ab'].tolist()[:2] == [3.0, 1.0] and np.isnan(out['ix_ab'].iloc[2])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_features7.py -q`
Expected: FAIL with `ImportError: cannot import name 'features7'`

- [ ] **Step 3: Write the module**

```python
# tradingagents/research/onchain_b7/features7.py
"""Multi-scale, deseasonalised features of hourly on-chain series (spec §4.1), event-time
features from the large-transfer records (§4.2) and explicit interactions (§4.2). Every value
at hour h uses data up to the end of hour h only."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b4.dataset4 import zscore

WEEK = 168
HOUR_NS = 3_600_000_000_000


def _regular_hourly(index):
    idx = pd.DatetimeIndex(index)
    if len(idx) > 1 and not (np.diff(idx.asi8) == HOUR_NS).all():
        raise ValueError('a complete hourly index is required')
    return idx


def seasonal_excess(x, weeks, min_occ):
    """log1p(x) − log1p(median of the same weekday-hour slot over the previous `weeks` weeks).
    Slots recur every 168 rows of a complete hourly index, so the profile is the median over
    the values 168, 336, …, 168·weeks rows earlier; NaN until `min_occ` of them exist."""
    _regular_hourly(x.index)
    v = x.clip(lower=0).to_numpy(float)
    n = len(v)
    prev = np.full((weeks, n), np.nan)
    for w in range(1, weeks + 1):
        if w * WEEK < n:
            prev[w - 1, w * WEEK:] = v[:n - w * WEEK]
    ok = np.isfinite(prev).sum(axis=0) >= max(1, min_occ)
    prof = np.full(n, np.nan)
    prof[ok] = np.nanmedian(prev[:, ok], axis=0)
    out = np.log1p(v) - np.log1p(prof)
    out[~ok] = np.nan
    return pd.Series(out, index=x.index)


def multiscale(raw, c):
    """Six features per series: excess over the weekly profile, z-score against the previous
    week, z-scores of the 6-, 24- and 168-hour sums against longer windows, and the burst
    against the previous 24 hours. Windows end at hour h, the hour's own value included."""
    out = {}
    for name in raw.columns:
        x = raw[name].clip(lower=0)
        lx = np.log1p(x)
        out[f'n_{name}__ex1'] = seasonal_excess(x, c['profile_weeks'], c['profile_min']).clip(-c['clip'], c['clip'])
        out[f'n_{name}__z1'] = zscore(lx, c['z1_window'], c['z1_min'], c['clip'])
        for k, key in ((6, 's6'), (24, 's24'), (168, 's168')):
            s = np.log1p(x.rolling(k, min_periods=k).sum())
            out[f'n_{name}__{key}z'] = zscore(s, c[f'{key}_window'], c[f'{key}_min'], c['clip'])
        prev = x.shift(1).rolling(c['burst_window'], min_periods=c['burst_window']).mean()
        out[f'n_{name}__burst'] = (lx - np.log1p(prev)).clip(-c['clip'], c['clip'])
    return pd.DataFrame(out, index=raw.index)


def event_hours(large, index, thresholds, cap):
    """log1p(hours since the last stablecoin exchange deposit of at least the threshold), capped
    at `cap`; an event inside hour h counts at the end of hour h (zero hours since); before the
    first event the value is the cap."""
    idx = _regular_hourly(index)
    dep = large[(large['token'] > 0) & (large['direction'] == 1)]
    pos = np.arange(len(idx), dtype=float)
    out = {}
    for name, thr in thresholds.items():
        hours = pd.to_datetime(dep.loc[dep['amount'] >= thr, 'ts'].to_numpy(), unit='s').floor('h')
        hit = idx.isin(hours)
        last = pd.Series(np.where(hit, pos, np.nan)).ffill().to_numpy()
        since = np.where(np.isnan(last), cap, np.minimum(pos - last, cap))
        out[f'ev_since_{name}'] = np.log1p(since)
    return pd.DataFrame(out, index=idx)


def interactions(table, spec):
    return pd.DataFrame({name: table[a] * table[b] for name, a, b in spec}, index=table.index)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_features7.py -q`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b7/features7.py tests/research/onchain_b7/test_features7.py
git commit -m "feat(onchain-b7): seasonal excess, multi-scale, event-time and interaction features"
```

---

### Task 3: targets7 — range features, jump and largest-move targets

**Files:**
- Create: `tradingagents/research/onchain_b7/targets7.py`
- Test: `tests/research/onchain_b7/test_targets7.py`

**Interfaces:**
- Produces: `range_features(closes: Series[minute], index, c) -> DataFrame[rg_range1, rg_range24]`; `jump_targets(bars: DataFrame[close, qvol], c) -> DataFrame[J6, J24]`; `mmax_targets(closes, index, c) -> DataFrame[M6, M24]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b7/test_targets7.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b7 import config, targets7 as T

CFG = config.load()
H = pd.Timedelta(hours=1)


def _minutes(start, hours, rng, step=0.0):
    idx = pd.date_range(start, periods=60 * hours, freq='min')
    return pd.Series(100.0 * np.exp(np.cumsum(rng.normal(0, 1e-4, len(idx)))), index=idx)


def test_range_features_require_minutes():
    rng = np.random.default_rng(3)
    m = _minutes('2024-01-01', 48, rng)
    h = pd.Timestamp('2024-01-01 05:00')
    m.loc[h:h + pd.Timedelta(minutes=59)] = 100.0
    m.loc[h + pd.Timedelta(minutes=30)] = 110.0                              # one hour with a known 10 % range
    m = m.drop(m.loc[h + 2 * H:h + 2 * H + pd.Timedelta(minutes=40)].index)   # an outage of 41 minutes
    idx = pd.date_range('2024-01-01', periods=48, freq='h')
    f = T.range_features(m, idx, CFG['range'])
    assert np.isclose(f.loc[h, 'rg_range1'], np.log(1.1)) and np.isnan(f.loc[h + 2 * H, 'rg_range1'])
    assert np.isfinite(f['rg_range1'].drop(h + 2 * H)).all() and (f['rg_range1'].dropna() >= 0).all()
    assert f['rg_range24'].iloc[:31].isna().all() and np.isfinite(f.loc[idx[31], 'rg_range24'])   # warm-up, then the outage hour inside the window


def test_jump_targets_threshold_and_warmup():
    rng = np.random.default_rng(4)
    idx = pd.date_range('2023-01-01', periods=2000, freq='h')
    r = 0.01 * np.where(np.arange(len(idx)) % 2 == 0, 1.0, -1.0)            # alternating ±1 %: σ̂ = 1 %, multi-hour moves cancel
    r[1500] = 0.2                                                            # one 20 % hour
    bars = pd.DataFrame({'close': 1000 * np.exp(np.cumsum(r)), 'qvol': 1.0}, index=idx)
    j = T.jump_targets(bars, CFG['jump'])
    assert j['J6'].iloc[:CFG['jump']['sigma_min']].isna().all()               # σ̂ unavailable → NaN, not 0
    assert j['J6'].iloc[1494:1500].eq(1.0).all() and j['J6'].iloc[1500:1510].eq(0.0).all()
    assert j['J24'].iloc[1476:1500].eq(1.0).all() and j['J24'].iloc[1400:1476].eq(0.0).all()
    assert j['J6'].iloc[-6:].isna().all() and j['J24'].iloc[-24:].isna().all()
    assert j['J6'].iloc[600:1400].eq(0.0).all() and j['J24'].iloc[600:1400].eq(0.0).all()


def test_mmax_alignment_and_missing():
    rng = np.random.default_rng(5)
    m = _minutes('2024-01-01', 72, rng)
    jump_min = pd.Timestamp('2024-01-02 03:17')
    m.loc[jump_min:] *= 1.05                                                 # a 5 % step at minute 03:17 of day 2
    idx = pd.date_range('2024-01-01', periods=72, freq='h')
    t = T.mmax_targets(m, idx, CFG['mmax'])
    big = t['M6'] > np.log(0.045)
    first_hour = pd.Timestamp('2024-01-01 21:00')                            # next 6 h = 22:00 … 03:59 of day 2
    last_hour = pd.Timestamp('2024-01-02 02:00')                             # next 6 h = 03:00 … 08:59
    assert big.loc[first_hour] and big.loc[last_hour] and not big.loc[first_hour - H] and not big.loc[last_hour + H]
    assert (t['M24'] > np.log(0.045)).loc[pd.Timestamp('2024-01-01 04:00'):pd.Timestamp('2024-01-02 02:00')].all()
    assert t['M6'].iloc[-6:].isna().all() and np.isfinite(t['M6'].iloc[-7])
    gap = m.drop(m.loc[pd.Timestamp('2024-01-01 10:00'):pd.Timestamp('2024-01-01 10:30')].index)   # 31 missing minutes
    g = T.mmax_targets(gap, idx, CFG['mmax'])
    assert np.isnan(g.loc[pd.Timestamp('2024-01-01 05:00'), 'M6']) and np.isfinite(g.loc[pd.Timestamp('2024-01-01 05:00'), 'M24'])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_targets7.py -q`
Expected: FAIL with `ImportError: cannot import name 'targets7'`

- [ ] **Step 3: Write the module**

```python
# tradingagents/research/onchain_b7/targets7.py
"""Range features from 1-minute closes (spec §4.3) and the jump and largest-move targets
(§5). Hour h is the bar [h, h+1); the close of minute h:59 is the decision-time price, and
the next k hours are the minutes h+1:00 … h+k:59."""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN = pd.Timedelta(minutes=1)
H = pd.Timedelta(hours=1)


def _minutes(closes):
    s = closes.sort_index()
    start, end = s.index.min().floor('h'), (s.index.max() + MIN).ceil('h') - MIN
    return s.reindex(pd.date_range(start, end, freq='min'))


def range_features(closes, index, c):
    m = _minutes(closes)
    g = m.groupby(m.index.floor('h'))
    rng = np.log(g.max() / g.min()).where(g.count() >= c['min_minutes'])
    r = rng.reindex(index)
    f = pd.DataFrame(index=index)
    f['rg_range1'] = r
    f['rg_range24'] = r.rolling(c['window24'], min_periods=c['window24']).mean()
    return f.replace([np.inf, -np.inf], np.nan)


def jump_targets(bars, c):
    b = bars.reindex(pd.date_range(bars.index.min(), bars.index.max(), freq='h'))
    lc = np.log(b['close'])
    r = lc.diff()
    sigma = np.sqrt((r ** 2).rolling(c['sigma_window'], min_periods=c['sigma_min']).mean())
    t = pd.DataFrame(index=b.index)
    for k in (6, 24):
        move = (lc.shift(-k) - lc).abs()
        thr = c['mult'] * sigma * np.sqrt(k)
        t[f'J{k}'] = (move > thr).astype(float).where(move.notna() & thr.notna())
    return t


def mmax_targets(closes, index, c):
    """log of the largest absolute `spacing_min`-minute log return with both ends at or after
    the decision-time close (minute h:59) and inside the next k hours: returns at minutes
    h+1:(spacing−1) … h+k:59, a window of 60k − spacing + 1 values ending at minute h+k:59;
    NaN unless at least `min_share` of the window's returns exist."""
    m = _minutes(closes)
    lc = np.log(m)
    sp = c['spacing_min']
    r = (lc - lc.shift(sp)).abs()
    out = pd.DataFrame(index=index)
    for k in (6, 24):
        w = 60 * k - sp + 1
        mx = r.rolling(w, min_periods=int(np.ceil(c['min_share'] * w))).max()
        val = mx.reindex(pd.DatetimeIndex(index) + (k + 1) * H - MIN).to_numpy(float)
        out[f'M{k}'] = np.log(np.maximum(val, c['floor']))
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_targets7.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b7/targets7.py tests/research/onchain_b7/test_targets7.py
git commit -m "feat(onchain-b7): range features, jump and largest-move targets"
```

---

### Task 4: models7 — families with time-ordered early stopping

**Files:**
- Create: `tradingagents/research/onchain_b7/models7.py`
- Test: `tests/research/onchain_b7/test_models7.py`

**Interfaces:**
- Consumes: `onchain_b2.screen.fit_predict(family, task, Xtr, ytr, Xte, inner_len, cfg, info)`, `row_loss(task, y, pred)`.
- Produces: `choose_iter(task, Xtr, ytr, c) -> (n_iter: int, losses: ndarray)`; `fit_predict7(family, task, Xtr, ytr, Xte, cfg, info=None) -> ndarray` for families `ridge`, `trees_es`, `trees_fixed`; `info` gets `alpha` (ridge) and `n_iter` (trees_es).

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b7/test_models7.py
import numpy as np

from tradingagents.research.onchain_b7 import config, models7 as M

CFG = config.load()
ES = {**CFG['models']['trees_es'], 'max_iter': 80, 'min_iter': 5}


def _data(n, rng, flip_tail=False):
    X = rng.normal(size=(n, 6))
    y = 2.0 * X[:, 0] - X[:, 1] ** 2 + 0.3 * rng.normal(size=n)
    if flip_tail:
        tail = int(0.1 * n)
        y[-tail:] = -y[-tail:]
    return X, y


def test_choose_iter_uses_the_time_ordered_tail():
    rng = np.random.default_rng(7)
    X, y = _data(4000, rng)
    n_iter, losses = M.choose_iter('regression', X, y, ES)
    assert len(losses) == 80 and 5 <= n_iter <= 80 and n_iter > 20                 # signal: keeps boosting
    Xf, yf = _data(4000, rng, flip_tail=True)
    n_flip, _ = M.choose_iter('regression', Xf, yf, ES)
    assert n_flip == 5                                                             # a tail that contradicts the head stops at the minimum
    yc = (y > np.quantile(y, 0.9)).astype(float)
    n_cls, lc = M.choose_iter('classification', X, yc, ES)
    assert 5 <= n_cls <= 80 and len(lc) == 80


def test_fit_predict7_families_and_info():
    rng = np.random.default_rng(8)
    X, y = _data(3000, rng)
    cfg = {**CFG, 'models': {**CFG['models'], 'trees_es': ES}, 'folds': {**CFG['folds'], 'inner_len': 500}}
    base = ((y[:2500] - y[:2500].mean()) ** 2).mean()
    for fam in ('ridge', 'trees_es', 'trees_fixed'):
        info = {}
        p = M.fit_predict7(fam, 'regression', X[:2500], y[:2500], X[2500:], cfg, info)
        assert p.shape == (500,) and np.isfinite(p).all() and ((y[2500:] - p) ** 2).mean() < 0.6 * base
        assert ('n_iter' in info) == (fam == 'trees_es') and info['alpha'] == (None if fam != 'ridge' else info['alpha'])
    yc = (y > np.quantile(y, 0.8)).astype(float)
    p = M.fit_predict7('trees_es', 'classification', X[:2500], yc[:2500], X[2500:], cfg)
    assert p.shape == (500,) and (p >= 0).all() and (p <= 1).all() and p[yc[2500:] == 1].mean() > p[yc[2500:] == 0].mean()


def test_fit_predict7_single_class_fallback():
    rng = np.random.default_rng(9)
    X, y = _data(1000, rng)
    cfg = {**CFG, 'models': {**CFG['models'], 'trees_es': ES}}
    zeros = np.zeros(800)
    assert (M.fit_predict7('trees_es', 'classification', X[:800], zeros, X[800:], cfg) == 0.0).all()
    head_only = zeros.copy()
    head_only[-20:] = 1.0                                                          # positives only in the tail: the head has one class
    p = M.fit_predict7('trees_es', 'classification', X[:800], head_only, X[800:], cfg)
    assert p.shape == (200,) and np.isfinite(p).all()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_models7.py -q`
Expected: FAIL with `ImportError: cannot import name 'models7'`

- [ ] **Step 3: Write the module**

```python
# tradingagents/research/onchain_b7/models7.py
"""Model families (spec §6): ridge / logistic with B2's alpha search, B4's fixed trees, and
trees whose iteration count is chosen on the time-ordered last part of the training window."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

from ..onchain_b2.screen import fit_predict, row_loss

_ES_KEYS = ('tail_frac', 'min_iter')


def _tree(task, params):
    cls = HistGradientBoostingClassifier if task == 'classification' else HistGradientBoostingRegressor
    return cls(**{k: v for k, v in params.items() if k not in _ES_KEYS}, early_stopping=False)


def _predict(model, task, X):
    return model.predict_proba(X)[:, 1] if task == 'classification' else model.predict(X)


def choose_iter(task, Xtr, ytr, c):
    """Fit on the first (1 − tail_frac) rows, score every stage on the last tail_frac rows and
    return the stage count with the smallest tail loss, at least min_iter, with the losses."""
    n = len(Xtr)
    tail = max(1, int(round(c['tail_frac'] * n)))
    head_y = ytr[:-tail]
    if task == 'classification' and len(np.unique(head_y)) < 2:
        return int(c['min_iter']), np.array([])
    m = _tree(task, c).fit(Xtr[:-tail], head_y)
    stages = m.staged_predict_proba(Xtr[-tail:]) if task == 'classification' else m.staged_predict(Xtr[-tail:])
    losses = np.array([row_loss(task, ytr[-tail:], p[:, 1] if task == 'classification' else p).mean() for p in stages])
    lo = min(int(c['min_iter']), len(losses))
    return int(lo + np.argmin(losses[lo - 1:])), losses


def fit_predict7(family, task, Xtr, ytr, Xte, cfg, info=None):
    if family in ('ridge', 'trees_fixed'):
        return fit_predict('linear' if family == 'ridge' else 'trees', task, Xtr, ytr, Xte, cfg['folds']['inner_len'], cfg, info)
    if family != 'trees_es':
        raise ValueError(f'unknown family {family}')
    if info is not None:
        info['alpha'] = None
    if task == 'classification' and len(np.unique(ytr)) < 2:
        return np.full(len(Xte), float(ytr.mean()))
    c = cfg['models']['trees_es']
    n_iter, _ = choose_iter(task, Xtr, ytr, c)
    if info is not None:
        info['n_iter'] = n_iter
    return _predict(_tree(task, {**c, 'max_iter': n_iter}).fit(Xtr, ytr), task, Xte)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_models7.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b7/models7.py tests/research/onchain_b7/test_models7.py
git commit -m "feat(onchain-b7): model families with time-ordered early stopping"
```

---

### Task 5: forecast7 — samples, predictions, comparisons, criteria, tables

**Files:**
- Create: `tradingagents/research/onchain_b7/forecast7.py`
- Test: `tests/research/onchain_b7/test_forecast7.py`

**Interfaces:**
- Consumes: `models7.fit_predict7`, `onchain_b2.screen.folds/row_loss`, `onchain_b4.screen4.interval`.
- Produces: `set_prefixes(name, track, cfg)`, `columns(df, prefixes)`, `fits(cfg) -> list[(family, set)]`, `comparisons(cfg) -> list[((fa, sa), (fb, sb))]`, `samples(track, table, targets, cfg) -> DataFrame`, `predict_all(df, target, track, cfg, log=None) -> (P: DataFrame['fam:set' …, y, const, tested], meta)`, `compare(P, target, track, cfg) -> list[dict]`, `report(results) -> str`, `detail_report(meta_by_unit) -> str`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b7/test_forecast7.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b7 import config, forecast7 as F

CFG = config.load()
SMALL = {**CFG, 'families': ['ridge', 'trees_es'], 'folds': {'inner_len': 400, 'min_train': 200},
         'models': {**CFG['models'], 'trees_es': {**CFG['models']['trees_es'], 'max_iter': 30, 'min_iter': 5}},
         'gate': {**CFG['gate'], 'draws': 200, 'block': 24}}


def _table(start, end, rng):
    idx = pd.date_range(start, end, freq='6h')
    n = len(idx)
    sig = rng.normal(size=n)
    t = pd.DataFrame({'h0_r1': rng.normal(size=n), 'px_rv6': rng.normal(size=n), 'rg_range1': rng.normal(size=n), 'mk_iv': rng.normal(size=n),
                      'eth_in_val__h1z': rng.normal(size=n), 'act_tx_count__h1z': rng.normal(size=n),
                      'n_eth_in_val__ex1': rng.normal(size=n), 'ev_since_10m': rng.normal(size=n), 'ix_eth_val_rv6': rng.normal(size=n),
                      'n_gs_active__ex1': sig, 'lab_eth_in_val__h1z': rng.normal(size=n)}, index=idx)
    y = pd.DataFrame({'V6': 2 * sig + 0.3 * rng.normal(size=n), 'J6': (sig > 1.3).astype(float)}, index=idx)
    return t, y


def test_set_prefixes_fits_and_comparisons():
    assert F.set_prefixes('Y2', 'B', CFG) == ['h0_', 'px_', 'rg_', 'mk_', 'n_eth_', 'n_stable_', 'n_act_', 'ev_', 'ix_', 'n_gs_', 'n_tk_', 'n_cl_', 'n_is_']
    assert F.set_prefixes('X1a', 'A', CFG) == ['h0_', 'px_', 'rg_', 'eth_', 'stable_', 'act_']
    assert len(F.fits(CFG)) == 11 and F.fits(CFG)[-1] == ('trees_fixed', 'Y2')
    comps = F.comparisons(CFG)
    assert len(comps) == 11 and comps[0] == (('ridge', 'Y1'), ('ridge', 'X1')) and comps[-1] == (('trees_es', 'Y2'), ('trees_fixed', 'Y2'))


def test_samples_window_mask_and_finite_rows():
    rng = np.random.default_rng(10)
    t, y = _table('2021-01-01', '2022-03-31', rng)
    t.loc[t.index[300], 'n_gs_active__ex1'] = np.nan                                 # one incomplete row inside the window
    t.loc[t.index[301], 'lab_eth_in_val__h1z'] = np.nan                              # a column no set uses
    cfg = {**SMALL, 'tracks': {**SMALL['tracks'], 'B': {**SMALL['tracks']['B'], 'start': '2021-02-01', 'end': '2022-01-31'}}}
    s = F.samples('B', t, y, cfg)
    assert s.index.min() == pd.Timestamp('2021-02-01') and s.index.max() == pd.Timestamp('2022-01-31 18:00')
    assert t.index[300] not in s.index and t.index[301] in s.index
    assert 'lab_eth_in_val__h1z' not in s.columns and 'mk_iv' in s.columns
    assert np.isnan(s.loc[pd.Timestamp('2022-01-31 18:00'), 'V6']) and np.isfinite(s.loc[pd.Timestamp('2022-01-31 12:00'), 'V6'])
    a = F.samples('A', t.drop(columns=['mk_iv']), y, {**cfg, 'tracks': {**cfg['tracks'], 'A': {**cfg['tracks']['A'], 'start': '2021-02-01', 'end': '2022-01-31'}}})
    assert 'mk_iv' not in a.columns and len(a) == len(s)


def test_predict_compare_criteria_and_report():
    rng = np.random.default_rng(11)
    cfg = {**SMALL, 'targets': {'V6': CFG['targets']['V6'], 'J6': CFG['targets']['J6']},
           'tracks': {'A': {**SMALL['tracks']['A'], 'start': '2019-01-01', 'end': '2024-12-31'},
                      'B': {**SMALL['tracks']['B'], 'start': '2021-04-01', 'end': '2026-10-12'}}}
    ta, ya = _table('2019-01-01', '2024-12-31', rng)
    sa = F.samples('A', ta.drop(columns=['mk_iv']), ya, cfg)
    P, meta = F.predict_all(sa, 'V6', 'A', cfg)
    assert {'ridge:X0', 'trees_es:Y2', 'trees_fixed:Y2', 'y', 'const', 'tested'} <= set(P.columns)
    assert P['tested'].sum() == (sa.index.year >= 2020).sum()                       # every test-year row is tested (last row 2024-12-31 00:00 keeps V6)
    assert set(meta['trees_es:Y2']) == {2020, 2021, 2022, 2023, 2024} and meta['trees_es:Y2'][2022]['n_iter'] >= 5
    res = F.compare(P, 'V6', 'A', cfg)
    assert len(res) == 11
    get = {(r['family'], r['set'], r['comparator']): r for r in res}
    assert get[('ridge', 'Y2', 'Y1')]['passed'] and get[('ridge', 'Y2', 'Y1')]['criterion'] == 'interval+years'
    assert not get[('ridge', 'X1', 'X0')]['passed'] and get[('trees_es|trees_fixed', 'Y2', 'Y2')]['n'] > 0
    assert get[('ridge', 'Y2', 'X0')]['gain_set'] > 0.5 and abs(get[('ridge', 'X1', 'X0')]['gain_set']) < 0.1
    tb, yb = _table('2021-04-01', '2026-10-12', rng)
    sb = F.samples('B', tb, yb, cfg)
    Pb, _ = F.predict_all(sb, 'J6', 'B', cfg)
    rb = F.compare(Pb, 'J6', 'B', cfg)
    assert len(rb) == 22
    gb = {(r['family'], r['set'], r['group']): r for r in rb}
    assert gb[('trees_es', 'Y2', '2022-24')]['criterion'] == 'interval+sign' and gb[('trees_es', 'Y2', '2025-26')]['criterion'] == 'sign'
    assert gb[('trees_es', 'Y2', '2022-24')]['passed'] and gb[('trees_es', 'Y2', '2022-24')]['loss_constant'] > gb[('trees_es', 'Y2', '2022-24')]['loss_set']
    text = F.report(res + rb)
    assert '| A | V6 | ridge | Y2 vs Y1 | 2020-24 |' in text and '| B | J6 | trees_es | Y2 vs Y1 | 2025-26 |' in text
    detail = F.detail_report({'A_V6': meta})
    assert 'trees_es:Y2' in detail and '2022' in detail
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_forecast7.py -q`
Expected: FAIL with `ImportError: cannot import name 'forecast7'`

- [ ] **Step 3: Write the module**

```python
# tradingagents/research/onchain_b7/forecast7.py
"""Samples per track, walk-forward predictions for every (family, set), the pre-declared
comparisons with block-bootstrap intervals and criteria (spec §7), and the tables."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2.screen import folds, row_loss
from ..onchain_b4.screen4 import interval
from .models7 import fit_predict7

H = pd.Timedelta(hours=1)


def set_prefixes(name, track, cfg):
    out = list(cfg['blocks']['base']) + list(cfg['tracks'][track]['base_extra'])
    for b in cfg['sets'][name]:
        out += cfg['blocks'][b]
    return out


def columns(df, prefixes):
    return sorted(c for c in df.columns if c.startswith(tuple(prefixes)))


def fits(cfg):
    return [(f, s) for f in cfg['families'] for s in cfg['sets']] + [tuple(x) for x in cfg['extra_fits']]


def comparisons(cfg):
    out = [((f, a), (f, b)) for f in cfg['families'] for a, b in cfg['set_comparisons']]
    return out + [(tuple(a), tuple(b)) for a, b in cfg['cross_comparisons']]


def samples(track, table, targets, cfg):
    """Rows of the track window whose features (union of every set of the track) are finite;
    a target is NaN when its horizon runs past the window end."""
    tc = cfg['tracks'][track]
    start, end = pd.Timestamp(tc['start']), pd.Timestamp(tc['end']) + pd.Timedelta(days=1)
    pre = sorted({p for s in cfg['sets'] for p in set_prefixes(s, track, cfg)})
    df = table[columns(table, pre)].join(targets, how='left')
    df = df[(df.index >= start) & (df.index < end)]
    feat = [c for c in df.columns if c not in targets.columns]
    df = df[np.isfinite(df[feat].to_numpy(float)).all(axis=1)].copy()
    for name, t in cfg['targets'].items():
        if name in df.columns:
            df.loc[df.index + pd.Timedelta(hours=t['h']) > end - H, name] = np.nan
    return df


def predict_all(df, target, track, cfg, log=None):
    tc, fc = cfg['tracks'][track], cfg['folds']
    task, h = cfg['targets'][target]['task'], cfg['targets'][target]['h']
    d = df[df[target].notna()].sort_index()
    y = d[target].to_numpy(float)
    fl = [(yr, tr, te) for yr, tr, te in folds(d.index, tc['test_years'], h / 24) if te.any() and tr.sum() >= fc['min_train']]
    tested, const = np.zeros(len(d), bool), np.full(len(d), np.nan)
    for _, tr, te in fl:
        tested |= te
        const[te] = y[tr].mean()
    preds, meta = {}, {}
    for fam, s in fits(cfg):
        key = f'{fam}:{s}'
        X = d[columns(d, set_prefixes(s, track, cfg))].to_numpy(float)
        p, meta[key] = np.full(len(d), np.nan), {}
        for yr, tr, te in fl:
            info = {}
            p[te] = fit_predict7(fam, task, X[tr], y[tr], X[te], cfg, info)
            meta[key][int(yr)] = info
            if log is not None:
                log(event='fit', track=track, target=target, fit=key, year=int(yr), n_train=int(tr.sum()), **info)
        preds[key] = p
    P = pd.DataFrame(preds, index=d.index)
    P['y'], P['const'], P['tested'] = y, const, tested
    return P, meta


def _passed(r, tc, rows):
    if tc['criterion'] == 'years':
        return bool(r['hi'] < 0 and r['wins'] >= tc['min_year_wins']), 'interval+years'
    first, second = list(tc['groups'])
    if r['group'] == first:
        other = rows.get(second)
        return bool(r['hi'] < 0 and other is not None and other['mean_diff'] < 0), 'interval+sign'
    return bool(r['mean_diff'] < 0), 'sign'


def _gain(loss, const):
    return float(1 - loss / const) if np.isfinite(loss) and np.isfinite(const) and const > 0 else np.nan


def compare(P, target, track, cfg):
    tc, g = cfg['tracks'][track], cfg['gate']
    task = cfg['targets'][target]['task']
    y, const, tested = P['y'].to_numpy(float), P['const'].to_numpy(float), P['tested'].to_numpy(bool)
    years = P.index.year.to_numpy()
    results = []
    for (fa, sa), (fb, sb) in comparisons(cfg):
        la = row_loss(task, y, P[f'{fa}:{sa}'].to_numpy(float))
        lb = row_loss(task, y, P[f'{fb}:{sb}'].to_numpy(float))
        rows = {}
        for gname, yrs in tc['groups'].items():
            m = tested & np.isin(years, yrs) & np.isfinite(la) & np.isfinite(lb)
            d = (la - lb)[m]
            lo, hi = interval(d, g['block'], g['draws'], g['seed'], g['chunk']) if len(d) >= g['block'] else (np.nan, np.nan)
            per_year = {int(yr): float(d[years[m] == yr].mean()) for yr in yrs if (years[m] == yr).any()}
            lc = float(row_loss(task, y[m], const[m]).mean()) if m.any() else np.nan
            ls, lcomp = (float(la[m].mean()), float(lb[m].mean())) if m.any() else (np.nan, np.nan)
            rows[gname] = {'track': track, 'target': target, 'family': fa if fa == fb else f'{fa}|{fb}', 'set': sa,
                           'comparator': sb, 'group': gname, 'n': int(m.sum()), 'mean_diff': float(d.mean()) if len(d) else np.nan,
                           'lo': lo, 'hi': hi, 'wins': int(sum(v < 0 for v in per_year.values())), 'years': per_year,
                           'loss_set': ls, 'loss_comparator': lcomp, 'loss_constant': lc,
                           'gain_set': _gain(ls, lc), 'gain_comparator': _gain(lcomp, lc)}
        for r in rows.values():
            r['passed'], r['criterion'] = _passed(r, tc, rows)
            results.append(r)
    return results


def report(results):
    lines = ['| track | target | family | comparison | group | n | mean diff | 95 % CI | years better | criterion | pass | gain vs constant (set / comparator) |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in results:
        lines.append(f"| {r['track']} | {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['group']} | {r['n']} | "
                     f"{r['mean_diff']:+.5f} | [{r['lo']:+.5f}, {r['hi']:+.5f}] | {r['wins']}/{len(r['years'])} | {r['criterion']} | "
                     f"{'PASS' if r['passed'] else '—'} | {r['gain_set']:+.4f} / {r['gain_comparator']:+.4f} |")
    return '\n'.join(lines)


def detail_report(meta_by_unit):
    lines = ['| unit | fit | per-year alpha or iterations |', '|---|---|---|']
    for unit, meta in sorted(meta_by_unit.items()):
        for key, years in meta.items():
            vals = []
            for yr, info in sorted(years.items(), key=lambda kv: int(kv[0])):
                v = info.get('n_iter') if info.get('n_iter') is not None else info.get('alpha')
                vals.append(f'{yr} {v if v is not None else "—"}')
            lines.append(f"| {unit} | {key} | {', '.join(vals)} |")
    return '\n'.join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_forecast7.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b7/forecast7.py tests/research/onchain_b7/test_forecast7.py
git commit -m "feat(onchain-b7): walk-forward comparisons, criteria and tables"
```

---

### Task 6: cli — features, forecast (resumable), report

**Files:**
- Create: `tradingagents/research/onchain_b7/cli.py`
- Test: `tests/research/onchain_b7/test_cli7.py`

**Interfaces:**
- Consumes: everything above; `onchain_b.runlog.Log`; `onchain_b4.cli._write_json`; `onchain_b4.hourmarket.load_all`; `onchain_b4.dataset4.price_features/hourly_targets`; `onchain_b5.decisions.px_features`.
- Produces: `load_inputs()`, `build_tables(c, raw4, raw6, flows, mk, bars, minutes, large) -> (table, targets)`, stages `features`, `forecast [--only A:V6,...]`, `report`; files `research_artifacts/onchain-b7/features/{table,targets}.parquet`, `forecast/{A,B}_<target>.json`, `forecast/pred_<track>_<target>.parquet`, `forecast/results.json`, `research/onchain-b7-2026-10-22/TABLES.md`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b7/test_cli7.py
import copy
import json

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b7 import cli, config

T0, T1 = '2020-06-01', '2021-12-31'


def _inputs(tmp_path, monkeypatch):
    rng = np.random.default_rng(12)
    cfg = copy.deepcopy(config.load())
    cfg['tracks'] = {'A': {**cfg['tracks']['A'], 'start': '2020-10-01', 'end': T1, 'test_years': [2021], 'groups': {'2021': [2021]}, 'min_year_wins': 1},
                     'B': {**cfg['tracks']['B'], 'start': '2020-10-01', 'end': T1, 'test_years': [2021], 'groups': {'2021a': [2021], '2021b': [2021]}}}
    cfg['targets'] = {'V6': cfg['targets']['V6'], 'J6': cfg['targets']['J6'], 'M6': cfg['targets']['M6']}
    cfg['folds'] = {'inner_len': 300, 'min_train': 100}
    cfg['models']['trees_es'].update({'max_iter': 20, 'min_iter': 5})
    cfg['gate'].update({'draws': 100, 'block': 24})
    b4, b6, art = tmp_path / 'b4', tmp_path / 'b6', tmp_path / 'b7'
    idx = pd.date_range(T0, pd.Timestamp(T1) + pd.Timedelta(hours=23), freq='h')
    n = len(idx)
    raw4 = pd.DataFrame({s: rng.gamma(2, 5, n) for s in cfg['series']['b4']}, index=idx)
    raw6 = pd.DataFrame({s: rng.gamma(2, 5, n) for s in cfg['series']['b6']}, index=idx)
    flows = pd.DataFrame({c: rng.normal(size=n) for c in ('eth_in_val__h1z', 'stable_in_val__d24z', 'act_tx_count__h1z', 'lab_eth_in_val__h1z', 'eth_net24__z')}, index=idx)
    (b4 / 'features').mkdir(parents=True)
    (b6 / 'features').mkdir(parents=True)
    raw4.to_parquet(b4 / 'features' / 'hourly_raw.parquet')
    raw6.to_parquet(b6 / 'features' / 'hourly_raw.parquet')
    flows.to_parquet(b4 / 'features' / 'hourly.parquet')
    pd.DataFrame({'mk_dvol': rng.normal(size=n), 'mk_dvol_chg24': rng.normal(size=n), 'mk_iv': rng.normal(size=n), 'other': 1.0}, index=idx).to_parquet(b6 / 'features' / 'features_B.parquet')
    close = 1000 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    bars = {t.strftime('%Y-%m-%dT%H'): [float(c), float(rng.gamma(2, 1e6))] for t, c in zip(idx, close)}
    (b4 / 'market').mkdir()
    (b4 / 'sealed').mkdir()
    (b4 / 'market' / 'hourly_dev.json').write_text(json.dumps({k: v for k, v in bars.items() if k < '2021-10-01T00'}))
    (b4 / 'sealed' / 'hourly_sealed.json').write_text(json.dumps({k: v for k, v in bars.items() if k >= '2021-10-01T00'}))
    midx = pd.date_range(T0, pd.Timestamp(T1) + pd.Timedelta(hours=23, minutes=59), freq='min')
    minutes = pd.Series(np.repeat(close, 60) * np.exp(rng.normal(0, 1e-4, len(midx))), index=midx, name='close')
    (b6 / 'market').mkdir()
    minutes.to_frame().to_parquet(b6 / 'market' / 'minutes_ETH.parquet')
    (b6 / 'large').mkdir()
    ts = [int(pd.Timestamp(t, tz='UTC').timestamp()) for t in ('2020-07-01 10:00', '2021-03-03 03:03', '2021-08-08 08:08')]
    pd.DataFrame({'ts': ts, 'token': [1, 2, 1], 'amount': [2e7, 6e7, 3e7], 'direction': [1, 1, 1], 'entity': 0, 'cp_new': False, 'cp': 0}).to_parquet(b6 / 'large' / '2021-01-01.parquet')
    monkeypatch.setattr(cli, 'B4', b4)
    monkeypatch.setattr(cli, 'B6', b6)
    monkeypatch.setattr(cli, 'ARTIFACTS', art)
    monkeypatch.setattr(cli, 'STUDY', tmp_path / 'study')
    (tmp_path / 'study').mkdir()
    monkeypatch.setattr(cli.config, 'load', lambda: cfg)
    return cfg, art


def test_features_stage_writes_table_and_targets(tmp_path, monkeypatch):
    cfg, art = _inputs(tmp_path, monkeypatch)
    cli.main(['features'])
    t = pd.read_parquet(art / 'features' / 'table.parquet')
    y = pd.read_parquet(art / 'features' / 'targets.parquet')
    assert len(t) == len(y) == 24 * 579 and list(y.columns) == ['V6', 'V24', 'J6', 'J24', 'M6', 'M24']
    n_cols = [c for c in t.columns if c.startswith('n_')]
    assert len(n_cols) == 54 * 6 and {'ev_since_10m', 'ev_since_50m', 'ix_stable_val_rv6', 'rg_range1', 'rg_range24', 'mk_iv', 'h0_rv24', 'px_rv6', 'eth_net24__z'} <= set(t.columns)
    assert 'lab_eth_in_val__h1z' not in t.columns and 'other' not in t.columns
    assert np.isclose(t['ix_stable_val_rv6'], t['n_stable_in_val__ex1'] * t['px_rv6'], equal_nan=True).all()
    assert t.loc['2021-06-01':, n_cols].notna().all().all() and y['M6'].loc['2021-06-01':'2021-12-30'].notna().all()


def test_forecast_stage_resumes_per_unit(tmp_path, monkeypatch):
    cfg, art = _inputs(tmp_path, monkeypatch)
    cli.main(['features'])
    cli.main(['forecast', '--only', 'A:V6'])
    first = art / 'forecast' / 'A_V6.json'
    assert first.exists() and (art / 'forecast' / 'pred_A_V6.parquet').exists()
    doc = json.loads(first.read_text())
    assert len(doc['results']) == 11 and all(r['n'] > 0 for r in doc['results'])
    stamp = first.stat().st_mtime_ns
    cli.main(['forecast'])
    assert first.stat().st_mtime_ns == stamp                                        # finished unit untouched
    res = json.loads((art / 'forecast' / 'results.json').read_text())
    assert len(res['results']) == 3 * 11 + 3 * 22 and set(res['meta']) == {'A_V6', 'A_J6', 'A_M6', 'B_V6', 'B_J6', 'B_M6'}
    assert res['n']['A']['J6']['mean'] < 0.2 and res['n']['B']['V6']['n'] > 1000
    cli.main(['report'])
    text = (tmp_path / 'study' / 'TABLES.md').read_text()
    assert '| B | M6 | trees_es|trees_fixed | Y2 vs Y2 | 2021b |' in text and 'A_V6 | trees_es:Y2' in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_cli7.py -q`
Expected: FAIL with `ImportError: cannot import name 'cli'`

- [ ] **Step 3: Write the module**

```python
# tradingagents/research/onchain_b7/cli.py
"""B7 stage runner: feature and target tables, walk-forward forecasts per track and target
(resumable: one file per unit), and the tables."""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd

from ..onchain_b.runlog import Log
from ..onchain_b4 import dataset4, hourmarket
from ..onchain_b4.cli import _write_json
from ..onchain_b5.decisions import px_features
from . import config, features7, forecast7, targets7

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B4 = config.B4_ARTIFACTS
B6 = config.B6_ARTIFACTS
MK = ['mk_dvol', 'mk_dvol_chg24', 'mk_iv']


def load_inputs():
    c = config.load()
    raw4 = pd.read_parquet(B4 / 'features' / 'hourly_raw.parquet')[c['series']['b4']]
    raw6 = pd.read_parquet(B6 / 'features' / 'hourly_raw.parquet')[c['series']['b6']]
    flows = pd.read_parquet(B4 / 'features' / 'hourly.parquet')
    flows = flows[[x for x in flows.columns if x.startswith(tuple(c['blocks']['FA']))]]
    mk = pd.read_parquet(B6 / 'features' / 'features_B.parquet')[MK]
    bars = hourmarket.load_all(B4 / 'market' / 'hourly_dev.json', B4 / 'sealed' / 'hourly_sealed.json')
    minutes = pd.read_parquet(B6 / 'market' / 'minutes_ETH.parquet')['close']
    large = pd.concat([pd.read_parquet(p, columns=['ts', 'token', 'amount', 'direction'])
                       for p in sorted((B6 / 'large').glob('*.parquet'))], ignore_index=True)
    return c, raw4, raw6, flows, mk, bars, minutes, large


def build_tables(c, raw4, raw6, flows, mk, bars, minutes, large):
    raw = raw4.join(raw6, how='outer').sort_index()
    idx = raw.index
    market = dataset4.price_features(bars).join(px_features(bars)).reindex(idx)
    table = (features7.multiscale(raw, c['engineering'])
             .join(flows.reindex(idx)).join(market)
             .join(targets7.range_features(minutes, idx, c['range']))
             .join(features7.event_hours(large, idx, c['events']['thresholds'], c['events']['cap_hours'])))
    table = table.join(features7.interactions(table, c['interactions'])).join(mk.reindex(idx))
    targets = (dataset4.hourly_targets(bars)[['V6', 'V24']].reindex(idx)
               .join(targets7.jump_targets(bars, c['jump']).reindex(idx))
               .join(targets7.mmax_targets(minutes, idx, c['mmax'])))
    return table, targets


def stage_features(args):
    c, *inputs = load_inputs()
    table, targets = build_tables(c, *inputs)
    out = ARTIFACTS / 'features'
    out.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out / 'table.parquet')
    targets.to_parquet(out / 'targets.parquet')
    print(json.dumps({'hours': len(table), 'columns': table.shape[1], 'targets': {t: int(targets[t].notna().sum()) for t in targets.columns},
                      'base_rate': {t: round(float(targets[t].mean()), 4) for t in ('J6', 'J24')}}))


def stage_forecast(args):
    c = config.load()
    only = set(args.only.split(',')) if args.only else None
    table = pd.read_parquet(ARTIFACTS / 'features' / 'table.parquet')
    targets = pd.read_parquet(ARTIFACTS / 'features' / 'targets.parquet')
    out = ARTIFACTS / 'forecast'
    out.mkdir(parents=True, exist_ok=True)
    log = Log(ARTIFACTS / 'logs' / 'forecast.jsonl')
    n = {}
    for track in c['tracks']:
        df = forecast7.samples(track, table, targets, c)
        n[track] = {t: {'n': int(df[t].notna().sum()), 'mean': float(df[t].mean())} for t in c['targets']}
        for target in c['targets']:
            unit = out / f'{track}_{target}.json'
            if (only is not None and f'{track}:{target}' not in only) or unit.exists():
                continue
            t0 = time.time()
            P, meta = forecast7.predict_all(df, target, track, c, log=log.event)
            res = forecast7.compare(P, target, track, c)
            P.to_parquet(out / f'pred_{track}_{target}.parquet')
            _write_json(unit, {'results': res, 'meta': meta, 'seconds': round(time.time() - t0, 1)})
            log.event(event='unit', track=track, target=target, seconds=round(time.time() - t0, 1), passed=sum(r['passed'] for r in res))
    units = sorted(out.glob('[AB]_*.json'))
    docs = {u.stem: json.loads(u.read_text()) for u in units}
    results = [r for d in docs.values() for r in d['results']]
    _write_json(out / 'results.json', {'results': results, 'meta': {k: d['meta'] for k, d in docs.items()}, 'n': n,
                                       'seconds': {k: d['seconds'] for k, d in docs.items()}})
    print(json.dumps({'units': len(units), 'rows': len(results), 'passed': sum(r['passed'] for r in results)}))


def stage_report(args):
    res = json.loads((ARTIFACTS / 'forecast' / 'results.json').read_text())
    lines = ['# B7 tables (generated; interpretation in RESULTS.md)', '', '## Samples', '', '| track | target | rows | mean |', '|---|---|---|---|']
    for track, ts in res['n'].items():
        for t, v in ts.items():
            lines.append(f"| {track} | {t} | {v['n']} | {v['mean']:.4f} |")
    lines += ['', '## Comparisons', '', forecast7.report(res['results']), '', '## Model detail', '', forecast7.detail_report(res['meta'])]
    STUDY.mkdir(parents=True, exist_ok=True)
    (STUDY / 'TABLES.md').write_text('\n'.join(lines) + '\n')
    print(f'{len(lines)} lines')


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b7')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('features').set_defaults(fn=stage_features)
    f = sub.add_parser('forecast')
    f.add_argument('--only', default=None, help='comma-separated track:target units')
    f.set_defaults(fn=stage_forecast)
    sub.add_parser('report').set_defaults(fn=stage_report)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7/test_cli7.py -q`
Expected: `2 passed`

- [ ] **Step 5: Run the whole package suite and commit**

Run: `.venv/bin/python -m pytest tests/research/onchain_b7 -q`
Expected: `17 passed`

```bash
git add tradingagents/research/onchain_b7/cli.py tests/research/onchain_b7/test_cli7.py
git commit -m "feat(onchain-b7): stage runner with resumable forecasts and tables"
```

---

### Task 7: Build, run, report

**Files:**
- Modify: `research/onchain-b7-2026-10-22/STATE.md`; Create: `research/onchain-b7-2026-10-22/TABLES.md` (generated), `RESULTS.md`.

- [ ] **Step 1: Fresh whole-branch review** (executing-plans final review; fix Critical/Important with tests before the run).

- [ ] **Step 2: Build the tables**

Run: `.venv/bin/python -m tradingagents.research.onchain_b7.cli features`
Expected: JSON with `hours: 85704`, `columns` 379 (324 `n_` + 32 flow + 13 market + 2 range + 2 event + 3 interaction + 3 option), target counts, J base rates ≈ 0.01–0.03. Record in STATE.md (B7-CP1).

- [ ] **Step 3: Forecast stage as a systemd user unit**

```bash
P=$PWD; systemd-run --user --unit onchain-b7-forecast -p MemoryMax=8G -p WorkingDirectory=$P $P/.venv/bin/python -m tradingagents.research.onchain_b7.cli forecast
```
Expected: 12 unit files in `research_artifacts/onchain-b7/forecast/`, ≈ 2–3 h; progress in `research_artifacts/onchain-b7/logs/forecast.jsonl`. Relaunch the same command after an interruption (finished units are skipped).

- [ ] **Step 4: Tables and results**

Run: `.venv/bin/python -m tradingagents.research.onchain_b7.cli report`
Expected: `TABLES.md` with 198 comparison rows (A′ 66, B 132). Write `RESULTS.md` (answers Q1, Q2 per the pre-declared reading guide; chance expectation; post hoc items labelled), update STATE.md (B7-CP2, B7-CP3), commit.

```bash
git add research/onchain-b7-2026-10-22
git commit -m "docs(onchain-b7): tables, results and state"
```
