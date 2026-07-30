# Cross-Sectional Value + Token-Unlock Burden — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run two pre-registered cross-sectional experiments — `value_xs_t1` (crypto value factor on free CoinMetrics fundamentals) and `unlock_xs_t1` (token-unlock supply-burden factor on free DefiLlama vesting schedules) — each to a dev-gate verdict, holdout untouched.

**Architecture:** Two new point-in-time stores feed two thin signal engines in `tradingagents/xsect/`. Both engines emit a signal matrix `S` (days × symbols) and a validity mask, hand them to one shared dollar-neutral long-short weight builder, and run P&L through the existing frozen `carry_xs.run_ls_portfolio` path with a zero funding leg. Gating (dual-family placebo, DSR, trial ledger) reuses the `liq_fade_i1` wiring verbatim.

**Tech Stack:** Python 3.13 via `uv`, pandas, numpy, requests, pytest. No new dependencies.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-30-value-unlock-xs-design.md`. It is the authority; this plan implements it and never overrides it.
- Branch: `feature/value-unlock-xs` (already created, off `feature/xs-momentum`).
- Dev window `2021-01-01 → 2025-03-31`. Holdout `2025-04-01 → 2026-07-01` is **sealed** — never loaded, never evaluated. `log_trial` enforces this; do not pass `allow_holdout=True` anywhere in this plan.
- Costs: 10 bps/side on `|ΔW|`. Risk-free `RF_DAILY = 1.045 ** (1/365) - 1` on full capital.
- Return convention: **simple** close-to-close for cross-sectional sorts (trend/carry use log — do not swap).
- Rebalance: **weekly** (Mondays), frozen, never a search axis.
- Liquidity floor: monthly PIT **top-150** by prior-month median quote volume.
- Breadth STOP: median daily breadth < 20 names ⇒ NEGATIVE-at-probe, stop.
- Grids are frozen: `value_xs_t1` = 4 configs, `unlock_xs_t1` = 2 configs. Adding a config requires a written pre-run amendment.
- DSR gated at own-experiment n (4 and 2); ledger-cumulative n computed and reported, gated on nothing.
- Every store carries a **vintage stamp** (fetch date + source URL) in a sidecar JSON.
- Annualization `sqrt(365)`, `ddof=1`, zero-variance SR := 0.
- Run everything with `uv run --no-sync python ...`.
- Never write results into `data/rebuild/*/` before the corresponding `gates.json` entry is committed.

---

## File Structure

**Create:**
- `tradingagents/xsect/ls_common.py` — generic dollar-neutral L/S weight builder, weekly-held. Shared by both engines.
- `tradingagents/xsect/value_xs.py` — value ratios → signal matrix.
- `tradingagents/xsect/unlock_xs.py` — unlock burden → signal matrix.
- `tradingagents/xsect/unlock_schedule.py` — as-of-`t` PIT reconstruction of DefiLlama vesting schedules. Split from `unlock_xs.py` because it is the highest-risk logic in the plan and deserves its own test surface.
- `scripts/fetch_xsect_fundamentals.py` — CoinMetrics community store builder.
- `scripts/fetch_xsect_unlocks.py` — DefiLlama emissions store builder.
- `scripts/value_xs_dev.py` — probes P0–P2 + frozen 4-config grid.
- `scripts/unlock_xs_dev.py` — probes P0–P2 + frozen 2-config grid.
- `scripts/value_xs_forensics.py`, `scripts/unlock_xs_forensics.py`
- `tests/xsect/test_ls_common.py`, `test_value_xs.py`, `test_unlock_schedule.py`, `test_unlock_xs.py`, `test_value_xs_dev.py`, `test_unlock_xs_dev.py`, `test_value_unlock_registration.py`

**Modify:**
- `data/rebuild/gates.json` — add `value_xs_t1` and `unlock_xs_t1` entries.
- `THESIS_FINDINGS.md` — add §51, §52, §53.

**Never modify:** `tradingagents/xsect/carry_xs.py`, `liq_fade.py`, `liq_mr.py`, `portfolio.py`. Their outputs are published (§46, §47, §49, §50). `ls_common.py` is a new generic sibling, not a refactor of `carry_weights`.

---

# Phase A — Shared foundation

### Task 1: Generic dollar-neutral L/S weight builder

`carry_xs.carry_weights` is the right algorithm but hardcodes a funding-validity mask and recomputes daily. This task extracts a signal-agnostic, weekly-held version. `carry_xs.py` is left untouched.

**Files:**
- Create: `tradingagents/xsect/ls_common.py`
- Test: `tests/xsect/test_ls_common.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `ls_weights(all_days: pd.DatetimeIndex, S: pd.DataFrame, valid: pd.DataFrame, rebalance_dates: pd.DatetimeIndex, leg_frac: float) -> pd.DataFrame` — weights indexed `all_days`, columns `S.columns`, rows sum to 0.0, held constant between consecutive `rebalance_dates`.
  - `sharpe_365(x: pd.Series) -> float` — `sqrt(365)` annualized, `ddof=1`, returns `0.0` on zero variance or fewer than 2 points.
  - `zero_funding(index: pd.DatetimeIndex, columns) -> pd.DataFrame` — all-zero frame for the `F` argument of `run_ls_portfolio`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/xsect/test_ls_common.py
import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.ls_common import ls_weights, sharpe_365, zero_funding


def _days(n=21):
    return pd.date_range("2022-01-03", periods=n, freq="D", tz="UTC")


def test_weights_are_dollar_neutral_and_legs_disjoint():
    days = _days()
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    valid = pd.DataFrame(True, index=days, columns=cols)
    rb = days[days.dayofweek == 0]
    W = ls_weights(days, S, valid, rb, leg_frac=0.2)
    row = W.loc[rb[0]]
    assert row.sum() == pytest.approx(0.0, abs=1e-12)
    assert (row > 0).sum() == 2 and (row < 0).sum() == 2
    # highest signal is shorted, lowest is longed
    assert row["S9"] < 0 and row["S0"] > 0
    assert set(row[row > 0].index).isdisjoint(row[row < 0].index)


def test_weights_held_constant_between_rebalances():
    days = _days()
    cols = [f"S{i}" for i in range(10)]
    # signal flips sign every day -- weights must NOT follow it intra-week
    base = np.arange(10.0)
    S = pd.DataFrame([base if i % 2 == 0 else base[::-1] for i in range(len(days))],
                     index=days, columns=cols)
    valid = pd.DataFrame(True, index=days, columns=cols)
    rb = days[days.dayofweek == 0]
    W = ls_weights(days, S, valid, rb, leg_frac=0.2)
    seg = W.loc[rb[0]:rb[1] - pd.Timedelta(days=1)]
    assert (seg.nunique() == 1).all()


def test_all_tied_signal_still_disjoint_legs():
    days = _days()
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(1.0, index=days, columns=cols)
    valid = pd.DataFrame(True, index=days, columns=cols)
    rb = days[days.dayofweek == 0]
    W = ls_weights(days, S, valid, rb, leg_frac=0.2)
    row = W.loc[rb[0]]
    assert set(row[row > 0].index).isdisjoint(row[row < 0].index)
    assert row.sum() == pytest.approx(0.0, abs=1e-12)


def test_flat_when_breadth_below_minimum():
    days = _days()
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    valid = pd.DataFrame(False, index=days, columns=cols)
    valid.iloc[:, :3] = True          # only 3 valid names, below MIN_VALID
    rb = days[days.dayofweek == 0]
    W = ls_weights(days, S, valid, rb, leg_frac=0.2)
    assert (W == 0.0).all().all()


def test_invalid_names_never_get_weight():
    days = _days()
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    valid = pd.DataFrame(True, index=days, columns=cols)
    valid["S9"] = False
    rb = days[days.dayofweek == 0]
    W = ls_weights(days, S, valid, rb, leg_frac=0.2)
    assert (W["S9"] == 0.0).all()


def test_sharpe_365_conventions():
    r = pd.Series([0.01, -0.005, 0.02, 0.0, 0.007])
    expected = r.mean() / r.std(ddof=1) * np.sqrt(365)
    assert sharpe_365(r) == pytest.approx(expected)
    assert sharpe_365(pd.Series([0.01] * 5)) == 0.0     # zero variance -> 0.0
    assert sharpe_365(pd.Series([0.01])) == 0.0          # too short -> 0.0
    assert sharpe_365(pd.Series(dtype=float)) == 0.0


def test_zero_funding_shape():
    days = _days(3)
    F = zero_funding(days, ["A", "B"])
    assert F.shape == (3, 2) and (F == 0.0).all().all()
    assert list(F.columns) == ["A", "B"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-sync python -m pytest tests/xsect/test_ls_common.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tradingagents.xsect.ls_common'`

- [ ] **Step 3: Write the implementation**

```python
# tradingagents/xsect/ls_common.py
"""Signal-agnostic dollar-neutral L/S weights, weekly-held.

Generalises the algorithm in ``carry_xs.carry_weights`` (which hardcodes a
funding-validity mask and recomputes daily) so value and unlock signals can
share it. ``carry_xs`` is deliberately NOT refactored onto this: its results
are published (THESIS section 46) and must stay byte-reproducible.

Tie-break follows carry_xs exactly: two independent sorts, short leg first,
long leg excluding short-leg members. A single desc sort's tail gives
(signal asc, symbol DESC) at tie boundaries, which diverges from the frozen
ascending tie-break; under heavily tied signals both sorts collapse to
symbol-asc, so the long leg must explicitly exclude shorts to keep legs
disjoint and Sum(w) = 0.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_VALID = 5   # fewer valid names than this on a rebalance date => flat


def ls_weights(all_days: pd.DatetimeIndex, S: pd.DataFrame, valid: pd.DataFrame,
               rebalance_dates: pd.DatetimeIndex, leg_frac: float) -> pd.DataFrame:
    """Dollar-neutral L/S weights, recomputed only on ``rebalance_dates``.

    Short the top ``leg_frac`` by signal, long the bottom ``leg_frac``.
    Weights are held constant until the next rebalance date. Rows sum to 0.
    """
    if not 0.0 < leg_frac <= 0.5:
        raise ValueError("leg_frac must be in (0, 0.5]")
    W = pd.DataFrame(0.0, index=all_days, columns=S.columns)
    rbs = [d for d in rebalance_dates if d in set(all_days)]
    for i, t in enumerate(rbs):
        v = valid.loc[t] & S.loc[t].notna()
        names = list(v.index[v])
        hi = rbs[i + 1] if i + 1 < len(rbs) else None
        if len(names) < MIN_VALID:
            continue
        n_leg = max(1, int(round(leg_frac * len(names))))
        shorts = sorted(names, key=lambda s: (-S.loc[t, s], s))[:n_leg]
        shorts_set = set(shorts)
        longs = [s for s in sorted(names, key=lambda s: (S.loc[t, s], s))
                 if s not in shorts_set][:n_leg]
        if not longs:
            continue
        seg = W.loc[t:] if hi is None else W.loc[t:hi - pd.Timedelta(days=1)]
        W.loc[seg.index, shorts] = -0.5 / len(shorts)
        W.loc[seg.index, longs] = +0.5 / len(longs)
    return W


def sharpe_365(x: pd.Series) -> float:
    """sqrt(365)-annualized Sharpe, ddof=1. Zero variance or n<2 -> 0.0."""
    x = pd.Series(x).dropna()
    if len(x) < 2:
        return 0.0
    sd = float(x.std(ddof=1))
    if not np.isfinite(sd) or sd == 0.0:
        return 0.0
    return float(x.mean() / sd * np.sqrt(365))


def zero_funding(index: pd.DatetimeIndex, columns) -> pd.DataFrame:
    """All-zero funding frame for run_ls_portfolio's ``F`` argument."""
    return pd.DataFrame(0.0, index=index, columns=list(columns))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --no-sync python -m pytest tests/xsect/test_ls_common.py -v`
Expected: 7 passed

- [ ] **Step 5: Verify P&L path integrates with the frozen engine**

Run:
```bash
uv run --no-sync python -c "
import pandas as pd, numpy as np
from tradingagents.xsect.ls_common import ls_weights, zero_funding, sharpe_365
from tradingagents.xsect.carry_xs import run_ls_portfolio, RF_DAILY
days = pd.date_range('2022-01-03', periods=60, freq='D', tz='UTC')
cols = [f'S{i}' for i in range(10)]
rng = np.random.default_rng(0)
S = pd.DataFrame(rng.normal(size=(len(days),10)), index=days, columns=cols)
R = pd.DataFrame(rng.normal(scale=0.02,size=(len(days),10)), index=days, columns=cols)
valid = pd.DataFrame(True, index=days, columns=cols)
W = ls_weights(days, S, valid, days[days.dayofweek==0], 0.2)
port = run_ls_portfolio(W, R, zero_funding(days, cols), cost_bps=10.0, rf_daily=RF_DAILY)
print('bars', len(port), 'SR', round(sharpe_365(port),3))
"
```
Expected: prints `bars 59` and a finite SR. No exception. (`run_ls_portfolio` drops the first bar and requires identical index/columns across `W`, `R`, `F`.)

- [ ] **Step 6: Commit**

```bash
git add tradingagents/xsect/ls_common.py tests/xsect/test_ls_common.py
git commit -m "feat(xsect): generic dollar-neutral L/S weights, weekly-held

Signal-agnostic generalisation of carry_weights for value/unlock reuse.
carry_xs.py deliberately untouched (section 46 results must stay
byte-reproducible). Tie-break and disjointness semantics copied exactly.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Register both experiments in gates.json

Registration must land **before** any data work, per the freeze contract. Nothing in Phase B or C may run until this is committed.

**Files:**
- Modify: `data/rebuild/gates.json`
- Test: `tests/xsect/test_value_unlock_registration.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `gates.json` keys `value_xs_t1`, `unlock_xs_t1` with the frozen gate values every later task reads.

- [ ] **Step 1: Write the failing test**

```python
# tests/xsect/test_value_unlock_registration.py
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATES = ROOT / "data" / "rebuild" / "gates.json"


def _entry(name):
    return json.loads(GATES.read_text())[name]


def test_both_experiments_registered():
    g = json.loads(GATES.read_text())
    assert "value_xs_t1" in g and "unlock_xs_t1" in g


def test_windows_frozen():
    for name in ("value_xs_t1", "unlock_xs_t1"):
        e = _entry(name)
        assert e["dev_window"] == ["2021-01-01", "2025-03-31"]
        assert e["holdout_window"] == ["2025-04-01", "2026-07-01"]
        assert e["holdout_status"] == "sealed"


def test_gate_bars_frozen():
    for name in ("value_xs_t1", "unlock_xs_t1"):
        d = _entry(name)["dev_select"]
        assert d["net_sr_min"] == 1.0
        assert d["placebo_p_max"] == 0.05
        assert d["dsr_min"] == 0.9
        assert d["delta_sr_vs_c1_min"] == 0.0
        assert d["delta_sr_vs_c2_min"] == 0.0
        assert d["conventions"].startswith("sqrt(365)")


def test_dsr_denominator_amendment_declared():
    for name, n in (("value_xs_t1", 4), ("unlock_xs_t1", 2)):
        d = _entry(name)["dev_select"]
        assert d["n_trials"] == n
        assert "amendment" in d["n_trials_rationale"].lower()
        assert "reported_not_gated" in _entry(name)


def test_frozen_grid_sizes():
    assert len(_entry("value_xs_t1")["grid"]) == 4
    assert len(_entry("unlock_xs_t1")["grid"]) == 2


def test_universe_and_breadth_frozen():
    for name in ("value_xs_t1", "unlock_xs_t1"):
        e = _entry(name)
        assert e["universe"]["liquidity_floor_rank"] == 150
        assert e["universe"]["min_median_breadth"] == 20
        assert e["rebalance"] == "weekly_monday"
        assert e["costs"]["bps_per_side"] == 10.0
        assert e["costs"]["rf_annual"] == 0.045
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_unlock_registration.py -v`
Expected: FAIL — `KeyError: 'value_xs_t1'`

- [ ] **Step 3: Add both entries to `data/rebuild/gates.json`**

Insert these two top-level keys (keep existing keys untouched, preserve file's 1-space indent style):

```json
"value_xs_t1": {
  "dev_window": ["2021-01-01", "2025-03-31"],
  "holdout_window": ["2025-04-01", "2026-07-01"],
  "holdout_status": "sealed",
  "hypothesis": "Cross-sectional crypto value: coins cheap on market-cap-per-network-activity outperform expensive ones. Long-short, dollar-neutral, weekly.",
  "universe": {
    "source": "CoinMetrics community (AdrActCnt, TxCnt, CapMrktCurUSD) INTERSECT 799-symbol perp store, minus stablecoin/pegged names",
    "n_candidates": 63,
    "liquidity_floor_rank": 150,
    "liquidity_floor_basis": "prior-month median quote_volume rank within the 799-symbol store",
    "min_median_breadth": 20,
    "breadth_stop": "median daily breadth < 20 => NEGATIVE-at-probe, stop before grid"
  },
  "signal": {
    "nvt_proxy": "CapMrktCurUSD / mean(TxCnt, 30d)",
    "metcalfe_proxy": "CapMrktCurUSD / mean(AdrActCnt, 30d)",
    "transform": "log, then cross-sectional z-score per rebalance date",
    "direction": "low ratio = cheap = long leg",
    "lag": "features as of t-2, position effective t+1; widened before the grid if P0 measures a longer publication lag (pre-result amendment, logged)"
  },
  "rebalance": "weekly_monday",
  "returns": "simple close-to-close on the USDT perp from data/xsect/klines/",
  "costs": {"bps_per_side": 10.0, "rf_annual": 0.045, "rf_basis": "full capital"},
  "grid": [
    {"metric": "nvt_proxy", "breadth": "decile"},
    {"metric": "nvt_proxy", "breadth": "tercile"},
    {"metric": "metcalfe_proxy", "breadth": "decile"},
    {"metric": "metcalfe_proxy", "breadth": "tercile"}
  ],
  "controls": {
    "C1": "vol-matched: sort on trailing 30d realized volatility alone, identical pipeline",
    "C2": "reversal: sort on -(past 30d return) alone, identical pipeline",
    "gating": "a config clearing net SR but failing either delta-SR control is NEGATIVE"
  },
  "probes": {
    "P0": "publication-lag and stamp alignment; STOP on fail",
    "P1": "breadth floor >= 20 names median; STOP on fail",
    "P2": "cheap-to-expensive decile spread ordered in expected direction on dev for at least one metric; STOP on fail"
  },
  "dev_select": {
    "net_sr_min": 1.0,
    "delta_sr_vs_c1_min": 0.0,
    "delta_sr_vs_c2_min": 0.0,
    "placebo": "dual-family (A: per-symbol circular shift of the signal series; B: count-matched random re-assignment of cross-sectional ranks among eligible names), 500 draws each, costs+rf re-applied inside every draw, p = (1+#{placebo SR >= real SR})/(N+1), gate on WORSE family",
    "placebo_p_max": 0.05,
    "dsr_min": 0.9,
    "n_trials": 4,
    "n_trials_rationale": "Declared amendment to the ledger-cumulative house convention, made 2026-07-30 BEFORE any data was touched, for a new hypothesis family. Multiplicity correction attaches to the search that produced the candidate; the section 43 momentum grid has no bearing on whether a value factor is real. Precedent: liq_fade_r1's pre-run amendment. Ledger-cumulative denominator is computed and reported (reported_not_gated) so the choice is auditable. This does NOT revisit or relax section 49's DSR failure.",
    "conventions": "sqrt(365) annualization on daily net returns, ddof=1, zero-variance SR := 0",
    "tiebreak": "highest DSR, then lowest placebo p"
  },
  "reported_not_gated": {
    "dsr_alt_denominators": "ledger-cumulative unique config_hash count at evaluation time",
    "breadth_by_year": true,
    "leg_concentration": "HHI and top-5 share per leg"
  },
  "holdout_deploy": {
    "net_sr_min": 0.5,
    "placebo_p_max": 0.05,
    "one_shot": true,
    "latch": "fresh per evaluation window"
  },
  "stop_rule": "No post-hoc exclusions. If a single symbol or period dominates, disclose in forensics and let the verdict stand (precedent: liq_fade_r1 FTT). Any amendment must be declared before the affected result is read."
},
"unlock_xs_t1": {
  "dev_window": ["2021-01-01", "2025-03-31"],
  "holdout_window": ["2025-04-01", "2026-07-01"],
  "holdout_status": "sealed",
  "hypothesis": "Cross-sectional token-unlock burden: coins facing large near-term scheduled supply unlocks underperform those facing none. Long-short, dollar-neutral, weekly.",
  "universe": {
    "source": "DefiLlama emissions (defillama-datasets.llama.fi) INTERSECT 799-symbol perp store",
    "n_candidates": 129,
    "liquidity_floor_rank": 150,
    "liquidity_floor_basis": "prior-month median quote_volume rank within the 799-symbol store",
    "min_median_breadth": 20,
    "breadth_stop": "median daily breadth < 20 => NEGATIVE-at-probe, stop before grid; breadth reported per year, and if the first two dev years fall below the floor the dev window is truncated forward and the truncation logged before the grid runs"
  },
  "signal": {
    "definition": "unlock_burden(t, N) = tokens_unlocking(t, t+N] / circulating_supply(t)",
    "direction": "high burden = short leg, low burden = long leg",
    "pit_reconstruction": "replay metadata.events in timestamp order, applying only events with timestamp <= t, yielding the forward unlock curve as known at t (not today's amended schedule). Linear unlocks stay in scope.",
    "residual_hazard": "DefiLlama may silently correct data without emitting a timestamped event; a single snapshot cannot detect this. P0 quantifies it."
  },
  "rebalance": "weekly_monday",
  "returns": "simple close-to-close on the USDT perp from data/xsect/klines/",
  "costs": {"bps_per_side": 10.0, "rf_annual": 0.045, "rf_basis": "full capital"},
  "grid": [
    {"lookahead_days": 14, "breadth": "decile"},
    {"lookahead_days": 30, "breadth": "decile"}
  ],
  "controls": {
    "C1": "vol-matched: sort on trailing 30d realized volatility alone, identical pipeline",
    "C2": "size: sort on log market cap alone, where market cap = perp close x as-of-t circulating supply from the same reconstruction (NOT CoinMetrics; the 129 unlock names and 132 CoinMetrics names are largely disjoint)",
    "gating": "a config clearing net SR but failing either delta-SR control is NEGATIVE"
  },
  "probes": {
    "P0": "supply reconstruction vs independent series (CoinMetrics SplyCur where covered, CoinGecko circulating otherwise); systematic divergence growing toward the present = silent restatement = STOP",
    "P1": "breadth floor >= 20 names median, reported per year; STOP on fail",
    "P2": "event study: mean forward return t+1..t+14 around cliff unlocks releasing >= 1% of circulating supply must carry the expected negative sign; STOP on fail"
  },
  "dev_select": {
    "net_sr_min": 1.0,
    "delta_sr_vs_c1_min": 0.0,
    "delta_sr_vs_c2_min": 0.0,
    "placebo": "dual-family (A: per-symbol circular shift of the signal series; B: count-matched random re-assignment of cross-sectional ranks among eligible names), 500 draws each, costs+rf re-applied inside every draw, p = (1+#{placebo SR >= real SR})/(N+1), gate on WORSE family",
    "placebo_p_max": 0.05,
    "dsr_min": 0.9,
    "n_trials": 2,
    "n_trials_rationale": "Declared amendment to the ledger-cumulative house convention, made 2026-07-30 BEFORE any data was touched, for a new hypothesis family. Same rationale and precedent as value_xs_t1; ledger-cumulative denominator reported under reported_not_gated.",
    "conventions": "sqrt(365) annualization on daily net returns, ddof=1, zero-variance SR := 0",
    "tiebreak": "highest DSR, then lowest placebo p"
  },
  "reported_not_gated": {
    "dsr_alt_denominators": "ledger-cumulative unique config_hash count at evaluation time",
    "breadth_by_year": true,
    "amendment_exposure": "share of dev-window signal mass attributable to schedule amendments vs original TGE schedule"
  },
  "holdout_deploy": {
    "net_sr_min": 0.5,
    "placebo_p_max": 0.05,
    "one_shot": true,
    "latch": "fresh per evaluation window"
  },
  "stop_rule": "No post-hoc exclusions. If a single symbol or period dominates, disclose in forensics and let the verdict stand (precedent: liq_fade_r1 FTT). Any amendment must be declared before the affected result is read."
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_unlock_registration.py -v`
Expected: 6 passed

- [ ] **Step 5: Verify JSON is still valid and no existing entry was disturbed**

Run:
```bash
uv run --no-sync python -c "
import json
g=json.load(open('data/rebuild/gates.json'))
print('entries:', len(g))
for k in ['liq_fade_i1','liq_fade_r1','carry_xs_t1','liq_mr_t1','trend_wide_t1']:
    assert k in g, k
print('pre-existing entries intact')
"
```
Expected: prints entry count and `pre-existing entries intact`

- [ ] **Step 6: Commit**

```bash
git add data/rebuild/gates.json tests/xsect/test_value_unlock_registration.py
git commit -m "prereg(value/unlock-xs): register value_xs_t1 and unlock_xs_t1

Freeze contract: registration lands before any data work. Grids frozen at
4 and 2 configs; DSR denominator amendment declared pre-run with
ledger-cumulative reported not gated; holdout sealed.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

# Phase B — `value_xs_t1`

### Task 3: CoinMetrics community fundamentals store

**Files:**
- Create: `scripts/fetch_xsect_fundamentals.py`
- Creates at runtime: `data/xsect/fundamentals/{asset}.parquet`, `data/xsect/fundamentals_manifest.json`, `data/xsect/fundamentals_vintage.json`
- Test: `tests/xsect/test_value_xs.py` (fetcher-side tests; signal tests added in Task 5)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `CM_ASSETS: list[str]` — the resolved CoinMetrics asset ids.
  - `ASSET_TO_SYMBOL: dict[str, str]` — CoinMetrics asset id → Binance perp symbol (e.g. `"matic" -> "MATICUSDT"`).
  - `fetch_asset(asset: str, start: str, end: str) -> pd.DataFrame` — UTC-indexed daily frame with columns `AdrActCnt`, `TxCnt`, `CapMrktCurUSD`.
  - `write_vintage(path: Path, source_url: str) -> None`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/xsect/test_value_xs.py
import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.fetch_xsect_fundamentals import (
    ASSET_TO_SYMBOL, CM_ASSETS, STABLE_EXCLUDE, write_vintage,
)

ROOT = Path(__file__).resolve().parents[2]


def test_candidate_count_matches_registration():
    gates = json.loads((ROOT / "data" / "rebuild" / "gates.json").read_text())
    assert len(CM_ASSETS) == gates["value_xs_t1"]["universe"]["n_candidates"]


def test_no_stablecoin_or_pegged_names():
    for bad in STABLE_EXCLUDE:
        assert bad not in CM_ASSETS


def test_every_asset_maps_to_a_perp_symbol():
    for a in CM_ASSETS:
        assert a in ASSET_TO_SYMBOL
        assert ASSET_TO_SYMBOL[a].endswith("USDT")


def test_mapped_symbols_exist_in_the_perp_store():
    kdir = ROOT / "data" / "xsect" / "klines"
    missing = [s for s in ASSET_TO_SYMBOL.values() if not (kdir / f"{s}.parquet").exists()]
    assert missing == [], f"unmapped perp symbols: {missing}"


def test_write_vintage_records_date_and_source(tmp_path):
    p = tmp_path / "v.json"
    write_vintage(p, "https://example.test/x")
    d = json.loads(p.read_text())
    assert d["source_url"] == "https://example.test/x"
    assert len(d["fetched_utc"]) >= 10
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_xs.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.fetch_xsect_fundamentals'`

- [ ] **Step 3: Write the fetcher**

```python
# scripts/fetch_xsect_fundamentals.py
"""CoinMetrics community fundamentals store for value_xs_t1.

Free tier, no API key. Serves AdrActCnt, TxCnt, CapMrktCurUSD from 2017 for
132 assets including delisted names, so the store inherits the survivorship
safety of the 799-symbol perp store.

Coverage discipline follows fetch_xsect_klines_1h.py: per-asset manifest,
interior gaps retried rather than silently skipped, explicit vintage stamp.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "xsect" / "fundamentals"
MANIFEST = PROJECT_ROOT / "data" / "xsect" / "fundamentals_manifest.json"
VINTAGE = PROJECT_ROOT / "data" / "xsect" / "fundamentals_vintage.json"
KLINES_DIR = PROJECT_ROOT / "data" / "xsect" / "klines"

BASE = "https://community-api.coinmetrics.io/v4"
METRICS = ["AdrActCnt", "TxCnt", "CapMrktCurUSD"]

# Stablecoins and pegged assets: excluded because a value ratio on a pegged
# asset is meaningless and the names are not directional trades.
STABLE_EXCLUDE = {"usdc", "frax", "paxg", "xaut", "usdt", "dai", "busd",
                  "gusd", "husd", "tusd", "usdp"}

# CoinMetrics ids carry chain suffixes for bridged/wrapped variants
# (matic_eth, trx_eth, ...). The perp trades the native asset, so the suffix
# is stripped for symbol mapping. Verified against the store in Step 5.
def _cm_base(asset: str) -> str:
    return asset.split("_")[0]


def _catalog_assets() -> list[str]:
    url = (f"{BASE}/catalog-v2/asset-metrics?metrics={','.join(METRICS)}"
           f"&page_size=10000")
    data = requests.get(url, timeout=60).json()["data"]
    need = set(METRICS)
    out = []
    for row in data:
        got = {m["metric"] for m in row["metrics"]
               if any(f.get("community") for f in m["frequencies"])}
        if need <= got:
            out.append(row["asset"].lower())
    return sorted(out)


def _perp_bases() -> set[str]:
    return {p.stem[:-4].lower() for p in KLINES_DIR.glob("*USDT.parquet")}


def _resolve_universe() -> tuple[list[str], dict[str, str]]:
    """Assets with all three metrics, a tradeable perp, and not pegged."""
    bases = _perp_bases()
    assets, mapping = [], {}
    for a in _catalog_assets():
        b = _cm_base(a)
        if b in STABLE_EXCLUDE or a in STABLE_EXCLUDE:
            continue
        if b in bases and b not in {_cm_base(x) for x in assets}:
            assets.append(a)
            mapping[a] = f"{b.upper()}USDT"
    return assets, mapping


CM_ASSETS, ASSET_TO_SYMBOL = _resolve_universe()


def fetch_asset(asset: str, start: str, end: str) -> pd.DataFrame:
    """Daily metrics for one asset, UTC-indexed, paginated."""
    rows, url = [], (
        f"{BASE}/timeseries/asset-metrics?assets={asset}"
        f"&metrics={','.join(METRICS)}&frequency=1d"
        f"&start_time={start}&end_time={end}&page_size=10000"
    )
    while url:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        payload = r.json()
        rows.extend(payload.get("data", []))
        url = payload.get("next_page_url")
        if url:
            time.sleep(0.2)
    if not rows:
        return pd.DataFrame(columns=METRICS)
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], utc=True).dt.normalize()
    df = df.set_index("time").sort_index()
    for m in METRICS:
        df[m] = pd.to_numeric(df.get(m), errors="coerce")
    return df[METRICS]


def write_vintage(path: Path, source_url: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "fetched_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": source_url,
        "note": "vendor may restate; this stamp is what makes restatement detectable",
    }, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-06-01")
    ap.add_argument("--end", default="2025-04-15")  # never past holdout+15d
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    for i, a in enumerate(CM_ASSETS, 1):
        out = OUT_DIR / f"{a}.parquet"
        if out.exists() and manifest.get(a, {}).get("end") == args.end:
            continue
        df = fetch_asset(a, args.start, args.end)
        df.to_parquet(out)
        manifest[a] = {"rows": int(len(df)), "start": args.start, "end": args.end,
                       "symbol": ASSET_TO_SYMBOL[a],
                       "first": str(df.index.min())[:10] if len(df) else None,
                       "last": str(df.index.max())[:10] if len(df) else None}
        MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        print(f"[{i}/{len(CM_ASSETS)}] {a} -> {len(df)} rows")
        time.sleep(0.25)
    write_vintage(VINTAGE, f"{BASE}/timeseries/asset-metrics (community tier)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_xs.py -v`
Expected: 5 passed. If `test_candidate_count_matches_registration` fails because the live catalog resolves to something other than 63, **stop and report the number** — do not silently edit `gates.json` to match. A changed candidate count is a pre-run amendment that must be written down.

- [ ] **Step 5: Build the store**

Run: `uv run --no-sync python scripts/fetch_xsect_fundamentals.py`
Expected: 63 lines of `[i/63] <asset> -> N rows`, then exit 0. Runtime roughly 2–4 minutes.

Verify:
```bash
uv run --no-sync python -c "
import json,glob
m=json.load(open('data/xsect/fundamentals_manifest.json'))
print('assets:',len(m),'files:',len(glob.glob('data/xsect/fundamentals/*.parquet')))
empty=[k for k,v in m.items() if v['rows']==0]
print('empty:',empty)
print('vintage:',json.load(open('data/xsect/fundamentals_vintage.json'))['fetched_utc'][:19])
"
```
Expected: `assets: 63`, `files: 63`, `empty: []`. Any non-empty `empty` list is reported, not ignored.

- [ ] **Step 6: Commit**

```bash
git add scripts/fetch_xsect_fundamentals.py tests/xsect/test_value_xs.py \
        data/xsect/fundamentals_manifest.json data/xsect/fundamentals_vintage.json
git commit -m "data(value-xs): CoinMetrics community fundamentals store, 63 names

Free tier, no key, survivorship-safe (includes delisted). Per-asset
manifest + vintage stamp. Parquets gitignored, manifest tracked.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

If `data/xsect/fundamentals/*.parquet` are not already covered by `.gitignore`, add `data/xsect/fundamentals/` to it in this commit.

---

### Task 4: Monthly PIT universe for the value cross-section

**Files:**
- Create: `scripts/value_xs_universe.py`
- Creates at runtime: `data/xsect/value_xs_universe.json`
- Test: extend `tests/xsect/test_value_xs.py`

**Interfaces:**
- Consumes: `ASSET_TO_SYMBOL` (Task 3).
- Produces: `data/xsect/value_xs_universe.json` — `{month_start_iso: [symbol, ...]}`, the same shape as `data/xsect/liq_fade_universe.json`, restricted to symbols that are both value candidates and inside the monthly top-150 liquidity floor.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/xsect/test_value_xs.py
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UNIV = ROOT / "data" / "xsect" / "value_xs_universe.json"


def test_universe_file_shape():
    u = json.loads(UNIV.read_text())
    assert len(u) >= 48                       # >= 4 years of months
    k = sorted(u)[0]
    assert k == "2021-01-01"
    assert all(s.endswith("USDT") for s in u[k])


def test_universe_is_subset_of_value_candidates():
    from scripts.fetch_xsect_fundamentals import ASSET_TO_SYMBOL
    allowed = set(ASSET_TO_SYMBOL.values())
    u = json.loads(UNIV.read_text())
    for month, syms in u.items():
        assert set(syms) <= allowed, f"{month} leaks non-candidate symbols"


def test_universe_never_reaches_into_holdout():
    u = json.loads(UNIV.read_text())
    assert max(u) < "2025-04-01"


def test_median_breadth_meets_registered_floor():
    u = json.loads(UNIV.read_text())
    import statistics
    med = statistics.median(len(v) for v in u.values())
    assert med >= 20, f"breadth STOP: median {med} < 20"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_xs.py -k universe -v`
Expected: FAIL — file not found

- [ ] **Step 3: Write the universe builder**

```python
# scripts/value_xs_universe.py
"""Monthly PIT universe for value_xs_t1: value candidates INTERSECT top-150 liquidity."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.fetch_xsect_fundamentals import ASSET_TO_SYMBOL  # noqa: E402
from tradingagents.xsect.liq_fade import monthly_top_n  # noqa: E402
from tradingagents.xsect.universe import load_klines  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "xsect" / "value_xs_universe.json"
DEV = ("2021-01-01", "2025-03-31")
FLOOR_RANK = 150   # registered in gates.json


def main() -> None:
    daily = load_klines(ROOT / "data" / "xsect" / "klines")
    liquid = monthly_top_n(daily, DEV[0], DEV[1], n=FLOOR_RANK)
    allowed = set(ASSET_TO_SYMBOL.values())
    out = {month: sorted(set(syms) & allowed) for month, syms in liquid.items()}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    sizes = [len(v) for v in out.values()]
    print(f"months={len(out)} breadth min/median/max="
          f"{min(sizes)}/{sorted(sizes)[len(sizes)//2]}/{max(sizes)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Build it and check the breadth STOP**

Run: `uv run --no-sync python scripts/value_xs_universe.py`
Expected: prints `months=51 breadth min/median/max=...`

**Decision point:** if median breadth < 20, the registered breadth STOP fires. Record the number, write the NEGATIVE-at-probe verdict, and stop Phase B — do not lower the floor.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_xs.py -v`
Expected: 9 passed

- [ ] **Step 6: Commit**

```bash
git add scripts/value_xs_universe.py data/xsect/value_xs_universe.json tests/xsect/test_value_xs.py
git commit -m "data(value-xs): monthly PIT universe, candidates INTERSECT top-150

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Value signal engine

**Files:**
- Create: `tradingagents/xsect/value_xs.py`
- Test: `tests/xsect/test_value_xs_signal.py`

**Interfaces:**
- Consumes: `ls_weights`, `sharpe_365`, `zero_funding` (Task 1); fundamentals store (Task 3); universe JSON (Task 4).
- Produces:
  - `load_fundamentals(fund_dir: Path, asset_to_symbol: dict) -> dict[str, pd.DataFrame]` keyed by **perp symbol**.
  - `value_ratio(fund: dict, metric: str, all_days: pd.DatetimeIndex, window: int = 30) -> pd.DataFrame` — raw ratio matrix; `metric` ∈ `{"nvt_proxy", "metcalfe_proxy"}`.
  - `zscore_signal(ratio: pd.DataFrame, lag_days: int = 2) -> pd.DataFrame` — log → cross-sectional z-score → lag.
  - `membership_mask(all_days, columns, universe: dict) -> pd.DataFrame`.
  - `control_signal(klines: dict, all_days, columns, kind: str) -> pd.DataFrame` — `kind` ∈ `{"vol", "reversal"}`, already z-scored and lagged, sign-oriented so the **short leg is the one the control predicts will underperform**.
  - `simple_returns(klines: dict, all_days, columns) -> pd.DataFrame`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/xsect/test_value_xs_signal.py
import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.value_xs import (
    control_signal, simple_returns, value_ratio, zscore_signal,
)


def _fund(days, tx, adr, mcap):
    return pd.DataFrame({"TxCnt": tx, "AdrActCnt": adr, "CapMrktCurUSD": mcap},
                        index=days)


def test_nvt_proxy_is_mcap_over_mean_txcnt():
    days = pd.date_range("2022-01-01", periods=40, freq="D", tz="UTC")
    f = {"AUSDT": _fund(days, 100.0, 50.0, 1000.0)}
    R = value_ratio(f, "nvt_proxy", days, window=30)
    assert R.loc[days[35], "AUSDT"] == pytest.approx(1000.0 / 100.0)


def test_metcalfe_proxy_is_mcap_over_mean_adractcnt():
    days = pd.date_range("2022-01-01", periods=40, freq="D", tz="UTC")
    f = {"AUSDT": _fund(days, 100.0, 50.0, 1000.0)}
    R = value_ratio(f, "metcalfe_proxy", days, window=30)
    assert R.loc[days[35], "AUSDT"] == pytest.approx(1000.0 / 50.0)


def test_ratio_is_nan_before_window_is_full():
    days = pd.date_range("2022-01-01", periods=40, freq="D", tz="UTC")
    f = {"AUSDT": _fund(days, 100.0, 50.0, 1000.0)}
    R = value_ratio(f, "nvt_proxy", days, window=30)
    assert R.loc[days[10], "AUSDT"] != R.loc[days[10], "AUSDT"]   # NaN


def test_zscore_is_cross_sectional_and_lagged():
    days = pd.date_range("2022-01-01", periods=5, freq="D", tz="UTC")
    R = pd.DataFrame({"A": [1.0, 2, 3, 4, 5], "B": [5.0, 4, 3, 2, 1],
                      "C": [3.0, 3, 3, 3, 3]}, index=days)
    Z = zscore_signal(R, lag_days=2)
    # row t reflects raw row t-2
    raw = np.log(R.iloc[0])
    expect = (raw - raw.mean()) / raw.std(ddof=1)
    pd.testing.assert_series_equal(Z.iloc[2], expect, check_names=False)
    assert Z.iloc[0].isna().all() and Z.iloc[1].isna().all()


def test_zscore_row_is_standardised():
    days = pd.date_range("2022-01-01", periods=3, freq="D", tz="UTC")
    R = pd.DataFrame({"A": [1.0, 2, 4], "B": [2.0, 4, 8], "C": [4.0, 8, 16]}, index=days)
    Z = zscore_signal(R, lag_days=0)
    assert Z.iloc[0].mean() == pytest.approx(0.0, abs=1e-12)
    assert Z.iloc[0].std(ddof=1) == pytest.approx(1.0)


# --- mutation kill-tests: these MUST fail if the shift direction is wrong ---

def test_lag_uses_past_not_future():
    days = pd.date_range("2022-01-01", periods=6, freq="D", tz="UTC")
    # a spike on day 2 must appear at day 4 under lag 2, never at day 0
    R = pd.DataFrame({"A": [1.0, 1, 100, 1, 1, 1], "B": [1.0, 1, 1, 1, 1, 1],
                      "C": [2.0, 2, 2, 2, 2, 2]}, index=days)
    Z = zscore_signal(R, lag_days=2)
    assert Z.iloc[4]["A"] > Z.iloc[3]["A"]
    assert Z.iloc[0].isna().all()


def test_simple_returns_are_simple_not_log():
    days = pd.date_range("2022-01-01", periods=3, freq="D", tz="UTC")
    k = {"AUSDT": pd.DataFrame({"close": [100.0, 110.0, 121.0]}, index=days)}
    R = simple_returns(k, days, ["AUSDT"])
    assert R.loc[days[1], "AUSDT"] == pytest.approx(0.10)
    assert R.loc[days[1], "AUSDT"] != pytest.approx(np.log(1.10))


def test_reversal_control_shorts_recent_winners():
    days = pd.date_range("2022-01-01", periods=40, freq="D", tz="UTC")
    up = pd.DataFrame({"close": np.linspace(100, 200, 40)}, index=days)
    dn = pd.DataFrame({"close": np.linspace(200, 100, 40)}, index=days)
    S = control_signal({"UUSDT": up, "DUSDT": dn}, days, ["UUSDT", "DUSDT"], "reversal")
    # higher signal = short leg; the winner must carry the higher signal
    assert S.iloc[-1]["UUSDT"] > S.iloc[-1]["DUSDT"]


def test_vol_control_shorts_high_vol():
    days = pd.date_range("2022-01-01", periods=60, freq="D", tz="UTC")
    rng = np.random.default_rng(1)
    calm = pd.DataFrame({"close": 100 * np.exp(np.cumsum(rng.normal(0, 0.002, 60)))}, index=days)
    wild = pd.DataFrame({"close": 100 * np.exp(np.cumsum(rng.normal(0, 0.05, 60)))}, index=days)
    S = control_signal({"CUSDT": calm, "WUSDT": wild}, days, ["CUSDT", "WUSDT"], "vol")
    assert S.iloc[-1]["WUSDT"] > S.iloc[-1]["CUSDT"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_xs_signal.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tradingagents.xsect.value_xs'`

- [ ] **Step 3: Write the engine**

```python
# tradingagents/xsect/value_xs.py
"""Cross-sectional crypto value signal (value_xs_t1).

Ratios are market cap per unit of network activity. Low ratio = cheap = long.
CapMrktCurUSD embeds price, so a cheap-looking coin is often just a coin that
fell -- the C2 reversal control in the dev runner exists to separate those.

Signal timing: features as of t-2 (CoinMetrics publication lag), positions
effective t+1 via run_ls_portfolio's own one-bar shift. Registered in
gates.json under value_xs_t1.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

METRIC_NUM = "CapMrktCurUSD"
METRIC_DEN = {"nvt_proxy": "TxCnt", "metcalfe_proxy": "AdrActCnt"}


def load_fundamentals(fund_dir: Path, asset_to_symbol: dict) -> dict[str, pd.DataFrame]:
    """Fundamentals keyed by perp symbol (not CoinMetrics asset id)."""
    out = {}
    for asset, symbol in asset_to_symbol.items():
        p = Path(fund_dir) / f"{asset}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        if df.index.tz is None:
            df.index = pd.to_datetime(df.index).tz_localize("UTC")
        out[symbol] = df.sort_index()
    return out


def value_ratio(fund: dict, metric: str, all_days: pd.DatetimeIndex,
                window: int = 30) -> pd.DataFrame:
    """Market cap over a ``window``-day mean of the activity denominator."""
    if metric not in METRIC_DEN:
        raise ValueError(f"unknown metric {metric!r}")
    den_col = METRIC_DEN[metric]
    cols = {}
    for sym, df in fund.items():
        d = df.reindex(all_days)
        den = d[den_col].rolling(window, min_periods=window).mean()
        num = d[METRIC_NUM]
        r = num / den.where(den > 0)
        cols[sym] = r
    return pd.DataFrame(cols, index=all_days).sort_index(axis=1)


def zscore_signal(ratio: pd.DataFrame, lag_days: int = 2) -> pd.DataFrame:
    """log -> per-row cross-sectional z-score -> lag by ``lag_days`` bars."""
    lg = np.log(ratio.where(ratio > 0))
    mu = lg.mean(axis=1)
    sd = lg.std(axis=1, ddof=1)
    z = lg.sub(mu, axis=0).div(sd.where(sd > 0), axis=0)
    return z.shift(lag_days) if lag_days else z


def membership_mask(all_days: pd.DatetimeIndex, columns,
                    universe: dict) -> pd.DataFrame:
    """True where a symbol is in that month's PIT universe."""
    M = pd.DataFrame(False, index=all_days, columns=list(columns))
    months = sorted(universe)
    for i, m in enumerate(months):
        lo = pd.Timestamp(m, tz="UTC")
        hi = pd.Timestamp(months[i + 1], tz="UTC") if i + 1 < len(months) else None
        seg = M.loc[lo:] if hi is None else M.loc[lo:hi - pd.Timedelta(days=1)]
        cols = [c for c in universe[m] if c in M.columns]
        if len(seg) and cols:
            M.loc[seg.index, cols] = True
    return M


def simple_returns(klines: dict, all_days: pd.DatetimeIndex, columns) -> pd.DataFrame:
    """Simple close-to-close returns (cross-sectional convention, not log)."""
    cols = {}
    for sym in columns:
        df = klines.get(sym)
        if df is None:
            cols[sym] = pd.Series(np.nan, index=all_days)
            continue
        cols[sym] = df["close"].reindex(all_days).pct_change(fill_method=None)
    return pd.DataFrame(cols, index=all_days)


def control_signal(klines: dict, all_days: pd.DatetimeIndex, columns,
                   kind: str, window: int = 30, lag_days: int = 2) -> pd.DataFrame:
    """Control signals, oriented so HIGH value = short leg.

    ``vol``      : trailing realized volatility (short the volatile names).
    ``reversal`` : trailing return (short the recent winners).
    """
    R = simple_returns(klines, all_days, columns)
    if kind == "vol":
        raw = R.rolling(window, min_periods=window).std(ddof=1)
    elif kind == "reversal":
        raw = R.rolling(window, min_periods=window).sum()
    else:
        raise ValueError(f"unknown control {kind!r}")
    mu = raw.mean(axis=1)
    sd = raw.std(axis=1, ddof=1)
    z = raw.sub(mu, axis=0).div(sd.where(sd > 0), axis=0)
    return z.shift(lag_days) if lag_days else z
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_xs_signal.py -v`
Expected: 9 passed

- [ ] **Step 5: Run the mutation kill-tests**

Temporarily change `z.shift(lag_days)` to `z.shift(-lag_days)` in `zscore_signal` and re-run.
Expected: `test_lag_uses_past_not_future` and `test_zscore_is_cross_sectional_and_lagged` **FAIL**.
Then revert the mutation and confirm all 9 pass again. A mutation that leaves the suite green means the suite does not test direction — fix the test, not the code.

- [ ] **Step 6: Commit**

```bash
git add tradingagents/xsect/value_xs.py tests/xsect/test_value_xs_signal.py
git commit -m "feat(value-xs): value ratio + z-score signal engine with controls

NVT-proxy and Metcalfe-proxy, log + cross-sectional z, t-2 lag. C1 vol and
C2 reversal controls oriented so high signal = short leg. Mutation
kill-tests pin the lag direction.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Value dev runner — probes P0–P2

Probes run **before** the grid and STOP on failure, so a broken data path cannot produce a publishable number.

**Files:**
- Create: `scripts/value_xs_dev.py` (probe half; grid added in Task 7)
- Test: `tests/xsect/test_value_xs_dev.py`

**Interfaces:**
- Consumes: everything from Tasks 1, 3, 4, 5.
- Produces:
  - `probe_p0_lag() -> dict` with key `measured_lag_days`, `pass`.
  - `probe_p1_breadth() -> dict` with `median_breadth`, `breadth_by_year`, `pass`.
  - `probe_p2_monotonicity() -> dict` with `spread_by_metric`, `pass`.
  - `main()` writing `data/rebuild/value_xs/probes.json`.

- [ ] **Step 1: Write the failing tests (pure helpers only — no network)**

```python
# tests/xsect/test_value_xs_dev.py
import numpy as np
import pandas as pd
import pytest

from scripts.value_xs_dev import decile_spread, measure_lag, verdict_from_probes


def test_measure_lag_detects_two_day_publication_delay():
    days = pd.date_range("2022-01-01", periods=10, freq="D", tz="UTC")
    # metric present only up to day 7 while klines run to day 9 => lag 2
    fund_last = days[7]
    kline_last = days[9]
    assert measure_lag(fund_last, kline_last) == 2


def test_decile_spread_orders_cheap_minus_expensive():
    days = pd.date_range("2022-01-03", periods=40, freq="D", tz="UTC")
    cols = [f"S{i}" for i in range(10)]
    # cheap (low signal) names earn +1%/day, expensive earn -1%/day
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    R = pd.DataFrame(0.0, index=days, columns=cols)
    R[cols[:5]] = 0.01
    R[cols[5:]] = -0.01
    valid = pd.DataFrame(True, index=days, columns=cols)
    spread = decile_spread(S, R, valid, leg_frac=0.2)
    assert spread > 0


def test_decile_spread_sign_flips_when_signal_inverted():
    days = pd.date_range("2022-01-03", periods=40, freq="D", tz="UTC")
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    R = pd.DataFrame(0.0, index=days, columns=cols)
    R[cols[:5]] = 0.01
    R[cols[5:]] = -0.01
    valid = pd.DataFrame(True, index=days, columns=cols)
    assert decile_spread(-S, R, valid, leg_frac=0.2) < 0


def test_verdict_stops_on_any_failed_probe():
    ok = {"pass": True}
    bad = {"pass": False}
    assert verdict_from_probes(ok, ok, ok) == "CONTINUE"
    assert verdict_from_probes(ok, bad, ok) == "NEGATIVE-at-probe"
    assert verdict_from_probes(bad, ok, ok) == "NEGATIVE-at-probe"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_xs_dev.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.value_xs_dev'`

- [ ] **Step 3: Write the probe half of the dev runner**

```python
# scripts/value_xs_dev.py
"""value_xs_t1 dev runner: probes P0-P2 (STOP semantics) then the frozen grid.

Probes run first and STOP the experiment on failure, so a broken data path
cannot reach a publishable number. Registered in data/rebuild/gates.json
under value_xs_t1; this file must not introduce any config not in that grid.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.fetch_xsect_fundamentals import ASSET_TO_SYMBOL  # noqa: E402
from tradingagents.xsect.ls_common import ls_weights, sharpe_365, zero_funding  # noqa: E402
from tradingagents.xsect.universe import load_klines, weekly_rebalance_dates  # noqa: E402
from tradingagents.xsect.value_xs import (  # noqa: E402
    control_signal, load_fundamentals, membership_mask, simple_returns,
    value_ratio, zscore_signal,
)

ROOT = Path(__file__).resolve().parents[1]
FUND_DIR = ROOT / "data" / "xsect" / "fundamentals"
KLINES_DIR = ROOT / "data" / "xsect" / "klines"
UNIV_FILE = ROOT / "data" / "xsect" / "value_xs_universe.json"
OUT_DIR = ROOT / "data" / "rebuild" / "value_xs"

DEV = ("2021-01-01", "2025-03-31")
WARMUP_START = "2020-06-01"        # 30d rolling windows warm up before DEV[0]
MAX_LOAD_END = "2025-03-31"        # holdout starts 2025-04-01; never load past this
REGISTERED_LAG = 2
MIN_MEDIAN_BREADTH = 20
LEG_FRAC = {"decile": 0.1, "tercile": 1 / 3}
GRID = [("nvt_proxy", "decile"), ("nvt_proxy", "tercile"),
        ("metcalfe_proxy", "decile"), ("metcalfe_proxy", "tercile")]


def measure_lag(fund_last: pd.Timestamp, kline_last: pd.Timestamp) -> int:
    """Publication lag in days between the fundamentals and price stores."""
    return int((kline_last - fund_last).days)


def decile_spread(S: pd.DataFrame, R: pd.DataFrame, valid: pd.DataFrame,
                  leg_frac: float) -> float:
    """Mean daily (cheap leg - expensive leg) return. Gross, no costs."""
    rb = S.index[S.index.dayofweek == 0]
    W = ls_weights(S.index, S, valid, rb, leg_frac)
    Wprev = W.shift(1).fillna(0.0)
    gross = (Wprev * R.fillna(0.0)).sum(axis=1)
    return float(gross.mean())


def verdict_from_probes(p0: dict, p1: dict, p2: dict) -> str:
    return "CONTINUE" if all(p.get("pass") for p in (p0, p1, p2)) else "NEGATIVE-at-probe"


def _load_all():
    days = pd.date_range(WARMUP_START, MAX_LOAD_END, freq="D", tz="UTC")
    klines = load_klines(KLINES_DIR)
    universe = json.loads(UNIV_FILE.read_text())
    symbols = sorted({s for v in universe.values() for s in v})
    klines = {s: d for s, d in klines.items() if s in symbols}
    fund = load_fundamentals(FUND_DIR, ASSET_TO_SYMBOL)
    fund = {s: d for s, d in fund.items() if s in symbols}
    return days, klines, fund, universe, symbols


def probe_p0_lag(days, klines, fund) -> dict:
    fl = max(d.index.max() for d in fund.values())
    kl = max(d.index.max() for d in klines.values())
    lag = measure_lag(fl, kl)
    return {"probe": "P0_publication_lag", "fund_last": str(fl)[:10],
            "kline_last": str(kl)[:10], "measured_lag_days": lag,
            "registered_lag_days": REGISTERED_LAG,
            "pass": bool(lag <= REGISTERED_LAG),
            "note": ("measured lag exceeds the registered t-2 convention; widen "
                     "the lag and log a pre-result amendment before the grid"
                     if lag > REGISTERED_LAG else "within registered lag")}


def probe_p1_breadth(universe) -> dict:
    sizes = {m: len(v) for m, v in universe.items()}
    by_year: dict[str, list[int]] = {}
    for m, n in sizes.items():
        by_year.setdefault(m[:4], []).append(n)
    med = statistics.median(sizes.values())
    return {"probe": "P1_breadth", "median_breadth": med,
            "min_breadth": min(sizes.values()),
            "breadth_by_year": {y: statistics.median(v) for y, v in sorted(by_year.items())},
            "floor": MIN_MEDIAN_BREADTH, "pass": bool(med >= MIN_MEDIAN_BREADTH)}


def probe_p2_monotonicity(days, klines, fund, universe, symbols) -> dict:
    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    R = simple_returns(klines, days, symbols)
    M = membership_mask(days, symbols, universe)
    spreads = {}
    for metric in ("nvt_proxy", "metcalfe_proxy"):
        S = zscore_signal(value_ratio(fund, metric, days), REGISTERED_LAG)
        valid = M & S.notna()
        spreads[metric] = decile_spread(S.loc[dev], R.loc[dev], valid.loc[dev],
                                        LEG_FRAC["decile"])
    return {"probe": "P2_monotonicity", "spread_by_metric": spreads,
            "pass": bool(any(v > 0 for v in spreads.values())),
            "note": "cheap-minus-expensive gross daily spread must be positive "
                    "for at least one metric"}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    days, klines, fund, universe, symbols = _load_all()
    p0 = probe_p0_lag(days, klines, fund)
    p1 = probe_p1_breadth(universe)
    p2 = probe_p2_monotonicity(days, klines, fund, universe, symbols)
    verdict = verdict_from_probes(p0, p1, p2)
    out = {"experiment": "value_xs_t1", "probes": [p0, p1, p2], "verdict": verdict}
    (OUT_DIR / "probes.json").write_text(json.dumps(out, indent=1, default=str))
    for p in (p0, p1, p2):
        print(f"{p['probe']}: {'PASS' if p['pass'] else 'FAIL'}  {p}")
    print(f"VERDICT: {verdict}")
    if verdict != "CONTINUE":
        sys.exit(2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_xs_dev.py -v`
Expected: 4 passed

- [ ] **Step 5: Run the probes on real data**

Run: `uv run --no-sync python scripts/value_xs_dev.py`
Expected: three `PASS`/`FAIL` lines and a `VERDICT:` line; exit 0 on CONTINUE, exit 2 on NEGATIVE-at-probe.

**Decision point:** on `NEGATIVE-at-probe`, stop Phase B here and go to Task 8's forensics + THESIS §51 write-up with the probe verdict. Do not proceed to the grid, and do not adjust probe thresholds.

- [ ] **Step 6: Commit**

```bash
git add scripts/value_xs_dev.py tests/xsect/test_value_xs_dev.py data/rebuild/value_xs/probes.json
git commit -m "run(value-xs): probes P0-P2 with STOP semantics

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Value grid runner — 4 configs, controls, dual-family placebo, DSR, ledger

**Files:**
- Modify: `scripts/value_xs_dev.py` (append the grid half)
- Test: extend `tests/xsect/test_value_xs_dev.py`

**Interfaces:**
- Consumes: the probe half (Task 6).
- Produces:
  - `run_config(metric, breadth, S, R, valid, ...) -> pd.Series` — daily net portfolio returns.
  - `placebo_family_a(S, ...) -> list[float]`, `placebo_family_b(S, ...) -> list[float]`.
  - `run_grid(...) -> dict` writing `data/rebuild/value_xs/grid.json` and one ledger row per config.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/xsect/test_value_xs_dev.py
import numpy as np
import pandas as pd
import pytest

from scripts.value_xs_dev import (
    GRID, LEG_FRAC, circular_shift_columns, dsr_or_nan, gate_config,
    rank_shuffle_columns,
)


def test_grid_is_frozen_at_four_configs():
    assert len(GRID) == 4
    assert set(GRID) == {("nvt_proxy", "decile"), ("nvt_proxy", "tercile"),
                         ("metcalfe_proxy", "decile"), ("metcalfe_proxy", "tercile")}


def test_leg_fractions_match_breadth_names():
    assert LEG_FRAC["decile"] == pytest.approx(0.1)
    assert LEG_FRAC["tercile"] == pytest.approx(1 / 3)


def test_circular_shift_preserves_values_per_column():
    days = pd.date_range("2022-01-01", periods=10, freq="D", tz="UTC")
    S = pd.DataFrame({"A": np.arange(10.0), "B": np.arange(10.0) * 2}, index=days)
    out = circular_shift_columns(S, np.random.default_rng(0))
    for c in S.columns:
        assert sorted(out[c].dropna()) == sorted(S[c].dropna())
    assert not out.equals(S)


def test_rank_shuffle_preserves_row_multiset():
    days = pd.date_range("2022-01-01", periods=5, freq="D", tz="UTC")
    S = pd.DataFrame(np.arange(15.0).reshape(5, 3), index=days, columns=list("ABC"))
    out = rank_shuffle_columns(S, np.random.default_rng(0))
    for t in days:
        assert sorted(out.loc[t]) == sorted(S.loc[t])


def test_dsr_returns_nan_not_crash_on_degenerate_returns():
    assert np.isnan(dsr_or_nan(pd.Series([0.01] * 50), sr_observed=1.0, n_trials=4))


def test_gate_requires_all_four_conditions():
    base = dict(net_sr=1.5, placebo_p_worse=0.01, dsr=0.95,
                delta_c1=0.2, delta_c2=0.3)
    assert gate_config(**base)["pass"] is True
    assert gate_config(**{**base, "net_sr": 0.9})["pass"] is False
    assert gate_config(**{**base, "placebo_p_worse": 0.06})["pass"] is False
    assert gate_config(**{**base, "dsr": 0.89})["pass"] is False
    assert gate_config(**{**base, "delta_c1": -0.01})["pass"] is False
    assert gate_config(**{**base, "delta_c2": 0.0})["pass"] is False


def test_planted_signal_is_recovered():
    """Harness sanity: inject real alpha, the pipeline must find it."""
    from scripts.value_xs_dev import run_config
    days = pd.date_range("2022-01-03", periods=400, freq="D", tz="UTC")
    cols = [f"S{i}" for i in range(20)]
    rng = np.random.default_rng(7)
    S = pd.DataFrame(rng.normal(size=(len(days), 20)), index=days, columns=cols)
    # cheap (low S) names outperform by 30bp/day -- a large, unmissable edge
    R = pd.DataFrame(rng.normal(scale=0.01, size=(len(days), 20)), index=days, columns=cols)
    R = R - S * 0.003
    valid = pd.DataFrame(True, index=days, columns=cols)
    port = run_config(S, R, valid, LEG_FRAC["decile"])
    from tradingagents.xsect.ls_common import sharpe_365
    assert sharpe_365(port) > 1.0


def test_mistimed_signal_does_not_recover_planted_alpha():
    """Kill-test: same data, signal shifted out of alignment -> edge disappears."""
    from scripts.value_xs_dev import run_config
    from tradingagents.xsect.ls_common import sharpe_365
    days = pd.date_range("2022-01-03", periods=400, freq="D", tz="UTC")
    cols = [f"S{i}" for i in range(20)]
    rng = np.random.default_rng(7)
    S = pd.DataFrame(rng.normal(size=(len(days), 20)), index=days, columns=cols)
    R = pd.DataFrame(rng.normal(scale=0.01, size=(len(days), 20)), index=days, columns=cols)
    R = R - S * 0.003
    valid = pd.DataFrame(True, index=days, columns=cols)
    mistimed = S.sample(frac=1.0, random_state=3).set_index(S.index)
    assert sharpe_365(run_config(mistimed, R, valid, LEG_FRAC["decile"])) < 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_xs_dev.py -v`
Expected: FAIL — `ImportError: cannot import name 'circular_shift_columns'`

- [ ] **Step 3: Append the grid half to `scripts/value_xs_dev.py`**

Add these imports at the top of the file:

```python
from tradingagents.rebuild.ledger import DEFAULT_LEDGER, log_trial  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.xsect.carry_xs import RF_DAILY, run_ls_portfolio  # noqa: E402
from tradingagents.xsect.portfolio import maxdd, rank_placebo_pvalue  # noqa: E402
```

Then append:

```python
N_PLACEBO = 500
GRID_GATE = {"net_sr_min": 1.0, "placebo_p_max": 0.05, "dsr_min": 0.9,
             "delta_sr_vs_c1_min": 0.0, "delta_sr_vs_c2_min": 0.0}


def run_config(S: pd.DataFrame, R: pd.DataFrame, valid: pd.DataFrame,
               leg_frac: float, cost_bps: float = 10.0) -> pd.Series:
    """Daily net portfolio returns for one signal matrix.

    P&L runs through the frozen section-46 engine with a zero funding leg, so
    cost, lag and rf semantics are byte-identical to carry_xs_t1.
    """
    rb = weekly_rebalance_dates(str(S.index[0])[:10], str(S.index[-1])[:10])
    W = ls_weights(S.index, S, valid, rb, leg_frac)
    F = zero_funding(S.index, S.columns)
    return run_ls_portfolio(W, R.reindex_like(W), F, cost_bps=cost_bps,
                            rf_daily=RF_DAILY)


def circular_shift_columns(S: pd.DataFrame, rng) -> pd.DataFrame:
    """Placebo family A: independent circular shift per symbol."""
    out = S.copy()
    n = len(S)
    for c in S.columns:
        k = int(rng.integers(1, n)) if n > 1 else 0
        out[c] = np.roll(S[c].to_numpy(), k)
    return out


def rank_shuffle_columns(S: pd.DataFrame, rng) -> pd.DataFrame:
    """Placebo family B: permute each row's values across symbols."""
    v = S.to_numpy(copy=True)
    for i in range(v.shape[0]):
        row = v[i]
        idx = np.arange(row.shape[0])
        rng.shuffle(idx)
        v[i] = row[idx]
    return pd.DataFrame(v, index=S.index, columns=S.columns)


def dsr_or_nan(returns: pd.Series, sr_observed: float, n_trials: int) -> float:
    """DSR, or NaN when the estimator is undefined (never a silent pass)."""
    try:
        arr = returns.dropna().to_numpy()
        var_sr = variance_of_sr(arr)
        se = float(np.sqrt(var_sr))
        e_max = expected_max_sharpe(n_trials, var_sr)
        return float(deflated_sharpe_ratio(sr_observed, e_max, se))
    except ValueError:
        return float("nan")


def gate_config(net_sr: float, placebo_p_worse: float, dsr: float,
                delta_c1: float, delta_c2: float) -> dict:
    checks = {
        "net_sr": net_sr >= GRID_GATE["net_sr_min"],
        "placebo": placebo_p_worse <= GRID_GATE["placebo_p_max"],
        "dsr": bool(dsr >= GRID_GATE["dsr_min"]),   # NaN >= x is False
        "delta_c1": delta_c1 > GRID_GATE["delta_sr_vs_c1_min"],
        "delta_c2": delta_c2 > GRID_GATE["delta_sr_vs_c2_min"],
    }
    return {"checks": checks, "pass": all(checks.values())}


def unique_config_hashes(ledger_path: Path = DEFAULT_LEDGER) -> int:
    """Distinct config evaluations in the ledger — the DSR denominator source."""
    seen = set()
    if ledger_path.exists():
        for line in ledger_path.read_text().splitlines():
            if line.strip():
                seen.add(json.loads(line)["config_hash"])
    return len(seen)


def run_grid(days, klines, fund, universe, symbols, n_placebo: int = N_PLACEBO,
             log: bool = True) -> dict:
    """Frozen 4-config grid.

    ``log=False`` suppresses ledger writes for smoke runs. A reduced-placebo
    smoke shares config_hash with the real run, so it would not inflate the
    DSR denominator — but it would put rows carrying 5-draw placebo p-values
    into the ledger that every DSR count in the thesis is audited against.
    """
    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    R = simple_returns(klines, days, symbols).loc[dev]
    M = membership_mask(days, symbols, universe).loc[dev]

    controls = {}
    for kind in ("vol", "reversal"):
        C = control_signal(klines, days, symbols, kind).loc[dev]
        controls[kind] = sharpe_365(run_config(C, R, M & C.notna(),
                                               LEG_FRAC["decile"]))

    ledger_before = unique_config_hashes()
    rng = np.random.default_rng(20260730)
    results = []
    for metric, breadth in GRID:
        S = zscore_signal(value_ratio(fund, metric, days), REGISTERED_LAG).loc[dev]
        valid = M & S.notna()
        leg = LEG_FRAC[breadth]
        port = run_config(S, R, valid, leg)
        net_sr = sharpe_365(port)

        srs_a = [sharpe_365(run_config(circular_shift_columns(S, rng), R, valid, leg))
                 for _ in range(n_placebo)]
        srs_b = [sharpe_365(run_config(rank_shuffle_columns(S, rng), R, valid, leg))
                 for _ in range(n_placebo)]
        p_a = rank_placebo_pvalue(net_sr, srs_a)
        p_b = rank_placebo_pvalue(net_sr, srs_b)
        p_worse = max(p_a, p_b)

        dsr_own = dsr_or_nan(port, net_sr, n_trials=len(GRID))
        dsr_ledger = dsr_or_nan(port, net_sr, n_trials=ledger_before + len(GRID))
        d_c1 = net_sr - controls["vol"]
        d_c2 = net_sr - controls["reversal"]
        gate = gate_config(net_sr, p_worse, dsr_own, d_c1, d_c2)

        cfg = {"metric": metric, "breadth": breadth, "leg_frac": leg,
               "lag_days": REGISTERED_LAG, "cost_bps": 10.0,
               "rebalance": "weekly_monday", "universe": "value_xs_universe.json",
               "n_symbols": int(len(symbols))}
        metrics = {"net_sr": net_sr, "maxdd": float(maxdd(port)),
                   "n_bars": int(len(port)),
                   "placebo_p_shiftfam": p_a, "placebo_p_randfam": p_b,
                   "placebo_p_worse": p_worse,
                   "dsr_own_n": dsr_own, "dsr_own_n_trials": len(GRID),
                   "dsr_ledger_n": dsr_ledger,
                   "dsr_ledger_n_trials": ledger_before + len(GRID),
                   "sr_control_vol": controls["vol"],
                   "sr_control_reversal": controls["reversal"],
                   "delta_sr_vs_c1": d_c1, "delta_sr_vs_c2": d_c2,
                   **{f"gate_{k}": v for k, v in gate["checks"].items()},
                   "gate_pass": gate["pass"]}
        if log:
            log_trial("value_xs_t1", cfg, DEV, metrics)
        results.append({"config": cfg, "metrics": metrics})
        print(f"{metric}/{breadth}: SR {net_sr:+.3f} p {p_worse:.4f} "
              f"DSR {dsr_own:.3f} dC1 {d_c1:+.3f} dC2 {d_c2:+.3f} "
              f"{'PASS' if gate['pass'] else 'FAIL'}")

    passing = [r for r in results if r["metrics"]["gate_pass"]]
    out = {"experiment": "value_xs_t1", "controls": controls,
           "ledger_unique_hashes_before": ledger_before,
           "results": results, "n_pass": len(passing),
           "verdict": "GO-at-dev" if passing else "NEGATIVE"}
    (OUT_DIR / "grid.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"VERDICT: {out['verdict']} ({len(passing)}/{len(GRID)})")
    return out
```

Then extend `main()` so that after `verdict == "CONTINUE"` it calls
`run_grid(days, klines, fund, universe, symbols)`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --no-sync python -m pytest tests/xsect/test_value_xs_dev.py -v`
Expected: 12 passed

- [ ] **Step 5: Smoke the grid with a reduced placebo count**

Run: `uv run --no-sync python -c "
import scripts.value_xs_dev as v
days,k,f,u,s = v._load_all()
out = v.run_grid(days,k,f,u,s,n_placebo=5,log=False)
print('configs:', len(out['results']))
"`
Expected: 4 config lines print, `configs: 4`. `log=False` is required — a smoke run must not write ledger rows.

Confirm the ledger is untouched:
```bash
uv run --no-sync python -c "
import json
n=sum(1 for l in open('data/rebuild/trial_ledger.jsonl') if l.strip())
print('ledger rows:', n, '(expect 120 — unchanged by smoke)')
"
```

- [ ] **Step 6: Run the real grid**

Run: `uv run --no-sync python scripts/value_xs_dev.py`
Expected: probes PASS, then 4 config lines, then `VERDICT:`. Runtime is dominated by 4 × 1000 placebo portfolio runs; expect tens of minutes. If projected wall-clock exceeds 2 hours, run under `nohup` and poll, per the long-run session discipline.

- [ ] **Step 7: Commit**

```bash
git add scripts/value_xs_dev.py tests/xsect/test_value_xs_dev.py \
        data/rebuild/value_xs/ data/rebuild/trial_ledger.jsonl
git commit -m "run(value-xs): frozen 4-config grid, dual-family placebo, DSR, ledger

DSR reported at both own-n (4) and ledger-cumulative denominators; gate uses
own-n per the pre-run amendment. C1 vol and C2 reversal deltas are gating.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Value forensics + THESIS §51

**Files:**
- Create: `scripts/value_xs_forensics.py`
- Creates at runtime: `data/rebuild/value_xs/forensics.md`
- Modify: `THESIS_FINDINGS.md`

**Interfaces:**
- Consumes: `data/rebuild/value_xs/grid.json`, `probes.json`.
- Produces: `forensics.md` and THESIS §51.

- [ ] **Step 1: Write the forensics script**

```python
# scripts/value_xs_forensics.py
"""Forensic verification of the value_xs_t1 verdict.

Per the forensic negative-verification discipline: a zero result must be
shown to be a real zero rather than a broken harness. Every item here is
reported whether the verdict was positive or negative.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.value_xs_dev as v  # noqa: E402
from tradingagents.xsect.ls_common import sharpe_365  # noqa: E402

OUT = v.OUT_DIR / "forensics.md"


def main() -> None:
    grid = json.loads((v.OUT_DIR / "grid.json").read_text())
    probes = json.loads((v.OUT_DIR / "probes.json").read_text())
    days, klines, fund, universe, symbols = v._load_all()
    dev = days[(days >= v.DEV[0]) & (days <= v.DEV[1])]
    R = v.simple_returns(klines, days, symbols).loc[dev]
    M = v.membership_mask(days, symbols, universe).loc[dev]

    lines = ["# value_xs_t1 forensics", ""]
    lines.append(f"Verdict: **{grid['verdict']}** ({grid['n_pass']}/4 configs)")
    lines.append("")

    # F1 -- sign inversion: does flipping the signal flip the sign?
    lines.append("## F1 sign inversion")
    for metric, breadth in v.GRID:
        S = v.zscore_signal(v.value_ratio(fund, metric, days), v.REGISTERED_LAG).loc[dev]
        valid = M & S.notna()
        leg = v.LEG_FRAC[breadth]
        a = sharpe_365(v.run_config(S, R, valid, leg))
        b = sharpe_365(v.run_config(-S, R, valid, leg))
        lines.append(f"- {metric}/{breadth}: long-cheap {a:+.3f} vs inverted {b:+.3f}")

    # F2 -- leg concentration
    lines.append("\n## F2 leg concentration")
    for metric, breadth in v.GRID:
        S = v.zscore_signal(v.value_ratio(fund, metric, days), v.REGISTERED_LAG).loc[dev]
        valid = M & S.notna()
        rb = v.weekly_rebalance_dates(str(dev[0])[:10], str(dev[-1])[:10])
        W = v.ls_weights(dev, S, valid, rb, v.LEG_FRAC[breadth])
        share = W.abs().sum() / W.abs().sum().sum()
        hhi = float((share ** 2).sum())
        top5 = float(share.sort_values(ascending=False).head(5).sum())
        lines.append(f"- {metric}/{breadth}: HHI {hhi:.4f}, top-5 share {top5:.1%}, "
                     f"names touched {int((share > 0).sum())}")

    # F3 -- yearly stability
    lines.append("\n## F3 yearly SR")
    for metric, breadth in v.GRID:
        S = v.zscore_signal(v.value_ratio(fund, metric, days), v.REGISTERED_LAG).loc[dev]
        port = v.run_config(S, R, M & S.notna(), v.LEG_FRAC[breadth])
        by_year = {str(y): round(sharpe_365(g), 3)
                   for y, g in port.groupby(port.index.year)}
        lines.append(f"- {metric}/{breadth}: {by_year}")

    # F4 -- breadth and honest denominators
    lines.append("\n## F4 honest denominators")
    p1 = next(p for p in probes["probes"] if p["probe"] == "P1_breadth")
    lines.append(f"- median breadth {p1['median_breadth']}, min {p1['min_breadth']}")
    lines.append(f"- breadth by year: {p1['breadth_by_year']}")
    lines.append(f"- dev bars: {grid['results'][0]['metrics']['n_bars']}")
    lines.append(f"- ledger unique hashes before this run: "
                 f"{grid['ledger_unique_hashes_before']}")

    # F5 -- DSR denominator sensitivity
    lines.append("\n## F5 DSR denominator sensitivity")
    for r in grid["results"]:
        m = r["metrics"]
        lines.append(f"- {r['config']['metric']}/{r['config']['breadth']}: "
                     f"DSR {m['dsr_own_n']:.3f} at n={m['dsr_own_n_trials']}, "
                     f"{m['dsr_ledger_n']:.3f} at n={m['dsr_ledger_n_trials']}")

    # F6 -- control comparison
    lines.append("\n## F6 controls")
    lines.append(f"- C1 vol-matched SR: {grid['controls']['vol']:+.3f}")
    lines.append(f"- C2 reversal SR: {grid['controls']['reversal']:+.3f}")
    for r in grid["results"]:
        m = r["metrics"]
        lines.append(f"- {r['config']['metric']}/{r['config']['breadth']}: "
                     f"dC1 {m['delta_sr_vs_c1']:+.3f}, dC2 {m['delta_sr_vs_c2']:+.3f}")

    # F7 -- cost sensitivity
    lines.append("\n## F7 cost sensitivity")
    for metric, breadth in v.GRID:
        S = v.zscore_signal(v.value_ratio(fund, metric, days), v.REGISTERED_LAG).loc[dev]
        valid = M & S.notna()
        row = [f"{sharpe_365(v.run_config(S, R, valid, v.LEG_FRAC[breadth], cost_bps=c)):+.3f}"
               for c in (10.0, 20.0, 30.0)]
        lines.append(f"- {metric}/{breadth}: 10/20/30 bps -> {' / '.join(row)}")

    OUT.write_text("\n".join(lines) + "\n")
    print(OUT.read_text())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `uv run --no-sync python scripts/value_xs_forensics.py`
Expected: prints the full forensics report and writes `data/rebuild/value_xs/forensics.md`.

- [ ] **Step 3: Write THESIS §51**

Append a new section to `THESIS_FINDINGS.md` following the structure of §49 and §50: registration reference (spec path + `gates.json` commit), design summary, probe results, grid table, forensics summary, verdict, and an explicit statement of what remains sealed. Report both DSR denominators. If the verdict is NEGATIVE, state which gate failed and by how much — never round a failure into a near-miss.

- [ ] **Step 4: Verify no holdout leakage**

Run:
```bash
uv run --no-sync python -c "
import json
rows=[json.loads(l) for l in open('data/rebuild/trial_ledger.jsonl') if l.strip()]
vx=[r for r in rows if r['experiment']=='value_xs_t1']
print('value_xs_t1 rows:', len(vx))
assert all(r['window'][1] <= '2025-03-31' for r in vx), 'HOLDOUT LEAK'
print('all windows end', max(r['window'][1] for r in vx), '- holdout intact')
"
```
Expected: `value_xs_t1 rows: 4` (plus 4 more if the smoke run was kept) and `holdout intact`.

- [ ] **Step 5: Commit**

```bash
git add scripts/value_xs_forensics.py data/rebuild/value_xs/forensics.md THESIS_FINDINGS.md
git commit -m "forensics(value-xs): verify verdict, THESIS section 51

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

# Phase C — `unlock_xs_t1`

Phase C is independent of Phase B's verdict. Run it regardless of whether `value_xs_t1` passed.

### Task 9: DefiLlama unlock store

**Files:**
- Create: `scripts/fetch_xsect_unlocks.py`
- Creates at runtime: `data/xsect/unlocks/{protocol}.json`, `data/xsect/unlocks_manifest.json`, `data/xsect/unlocks_vintage.json`
- Test: `tests/xsect/test_unlock_xs.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `PROTOCOL_TO_SYMBOL: dict[str, str]` — DefiLlama slug → perp symbol.
  - `fetch_protocol(slug: str) -> dict` — raw emissions payload.
  - `resolve_universe() -> dict[str, str]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/xsect/test_unlock_xs.py
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_protocol_map_matches_registration():
    from scripts.fetch_xsect_unlocks import PROTOCOL_TO_SYMBOL
    gates = json.loads((ROOT / "data" / "rebuild" / "gates.json").read_text())
    assert len(PROTOCOL_TO_SYMBOL) == gates["unlock_xs_t1"]["universe"]["n_candidates"]


def test_all_mapped_symbols_exist_in_perp_store():
    from scripts.fetch_xsect_unlocks import PROTOCOL_TO_SYMBOL
    kdir = ROOT / "data" / "xsect" / "klines"
    missing = [s for s in PROTOCOL_TO_SYMBOL.values() if not (kdir / f"{s}.parquet").exists()]
    assert missing == []


def test_manifest_and_vintage_written():
    m = ROOT / "data" / "xsect" / "unlocks_manifest.json"
    v = ROOT / "data" / "xsect" / "unlocks_vintage.json"
    assert m.exists() and v.exists()
    assert json.loads(v.read_text())["source_url"].startswith("https://defillama-datasets")


def test_most_stored_payloads_have_an_event_log():
    """Reports the empty ones AND bounds them: a store where most protocols
    carry no event log cannot support a PIT reconstruction."""
    m = json.loads((ROOT / "data" / "xsect" / "unlocks_manifest.json").read_text())
    no_events = sorted(k for k, val in m.items() if val["n_events"] == 0)
    print(f"protocols with zero events ({len(no_events)}/{len(m)}): {no_events}")
    assert len(no_events) <= 0.2 * len(m), (
        f"{len(no_events)}/{len(m)} protocols have empty event logs; "
        f"the as-of-t reconstruction has nothing to replay for those names"
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-sync python -m pytest tests/xsect/test_unlock_xs.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Write the fetcher**

```python
# scripts/fetch_xsect_unlocks.py
"""DefiLlama token-unlock schedule store for unlock_xs_t1.

Free, unauthenticated. api.llama.fi/emissions is 402-gated; the
defillama-datasets host is not. Payloads are stored raw so the as-of-t
reconstruction (tradingagents/xsect/unlock_schedule.py) can be re-derived
without a refetch.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "xsect" / "unlocks"
MANIFEST = PROJECT_ROOT / "data" / "xsect" / "unlocks_manifest.json"
VINTAGE = PROJECT_ROOT / "data" / "xsect" / "unlocks_vintage.json"
KLINES_DIR = PROJECT_ROOT / "data" / "xsect" / "klines"

LIST_URL = "https://defillama-datasets.llama.fi/emissionsProtocolsList"
PROTO_URL = "https://defillama-datasets.llama.fi/emissions/{slug}"
GECKO_LIST = "https://api.coingecko.com/api/v3/coins/list"


def _perp_bases() -> set[str]:
    return {p.stem[:-4].lower() for p in KLINES_DIR.glob("*USDT.parquet")}


def resolve_universe() -> dict[str, str]:
    """DefiLlama slug -> perp symbol, via CoinGecko id then bare-ticker fallback."""
    slugs = requests.get(LIST_URL, timeout=60).json()
    gecko = {c["id"]: c["symbol"].lower()
             for c in requests.get(GECKO_LIST, timeout=60).json()}
    bases = _perp_bases()
    out = {}
    for slug in slugs:
        s = slug.lower()
        sym = gecko.get(s)
        if sym and sym in bases:
            out[slug] = f"{sym.upper()}USDT"
        elif s in bases:
            out[slug] = f"{s.upper()}USDT"
    return dict(sorted(out.items()))


PROTOCOL_TO_SYMBOL = resolve_universe()


def fetch_protocol(slug: str) -> dict:
    r = requests.get(PROTO_URL.format(slug=slug), timeout=90)
    r.raise_for_status()
    return r.json()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    for i, (slug, symbol) in enumerate(PROTOCOL_TO_SYMBOL.items(), 1):
        out = OUT_DIR / f"{slug}.json"
        if out.exists() and slug in manifest:
            continue
        try:
            payload = fetch_protocol(slug)
        except Exception as e:                     # noqa: BLE001
            manifest[slug] = {"symbol": symbol, "error": str(e), "n_events": 0}
            print(f"[{i}/{len(PROTOCOL_TO_SYMBOL)}] {slug} FAILED {e}")
            MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
            continue
        out.write_text(json.dumps(payload))
        events = payload.get("metadata", {}).get("events", []) or []
        manifest[slug] = {"symbol": symbol, "n_events": len(events),
                          "token": payload.get("metadata", {}).get("token"),
                          "bytes": out.stat().st_size}
        MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        print(f"[{i}/{len(PROTOCOL_TO_SYMBOL)}] {slug} -> {len(events)} events")
        time.sleep(0.3)
    VINTAGE.parent.mkdir(parents=True, exist_ok=True)
    VINTAGE.write_text(json.dumps({
        "fetched_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": PROTO_URL.format(slug="{slug}"),
        "note": "schedule reflects vendor state at fetch time; amendments after "
                "this date are invisible to any run using this vintage",
    }, indent=1))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Build the store**

Run: `uv run --no-sync python scripts/fetch_xsect_unlocks.py`
Expected: 129 lines. Roughly 230 MB on disk (payloads average ~1.8 MB). Check free space first with `df -h .` — the plan needs at least 1 GB headroom.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run --no-sync python -m pytest tests/xsect/test_unlock_xs.py -v`
Expected: 4 passed. If the protocol count is not 129, report the number and stop — same rule as Task 3.

- [ ] **Step 6: Commit**

```bash
echo "data/xsect/unlocks/" >> .gitignore
git add scripts/fetch_xsect_unlocks.py tests/xsect/test_unlock_xs.py .gitignore \
        data/xsect/unlocks_manifest.json data/xsect/unlocks_vintage.json
git commit -m "data(unlock-xs): DefiLlama emissions store, 129 protocols with perps

Raw payloads stored so the as-of-t reconstruction is re-derivable without
refetch. Payloads gitignored; manifest and vintage tracked.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: As-of-`t` PIT schedule reconstruction

The highest-risk logic in the plan: getting this wrong silently injects look-ahead of exactly the kind the Jul-7 audit was about. It gets its own module and its own test file.

**Files:**
- Create: `tradingagents/xsect/unlock_schedule.py`
- Test: `tests/xsect/test_unlock_schedule.py`

**Interfaces:**
- Consumes: raw payloads from Task 9.
- Produces:
  - `parse_events(payload: dict) -> list[dict]` — normalized events sorted by timestamp, each `{ts, category, unlock_type, tokens, rate_duration_days}`.
  - `schedule_as_of(events: list[dict], t: pd.Timestamp) -> list[dict]` — only events with `ts <= t`.
  - `unlocked_between(events, t, horizon_days) -> float` — tokens released in `(t, t+horizon]` under the schedule known at `t`.
  - `circulating_as_of(events, t) -> float` — cumulative tokens released up to and including `t`.
  - `amendment_share(events, t_lo, t_hi) -> float` — fraction of signal mass from post-TGE amendments.

- [ ] **Step 1: Write the failing tests**

```python
# tests/xsect/test_unlock_schedule.py
import pandas as pd
import pytest

from tradingagents.xsect.unlock_schedule import (
    amendment_share, circulating_as_of, parse_events, schedule_as_of,
    unlocked_between,
)

DAY = 86400


def _payload(events):
    return {"metadata": {"events": events}}


def _cliff(ts, tokens, category="community"):
    return {"timestamp": ts, "noOfTokens": [tokens], "category": category,
            "unlockType": "cliff"}


def _linear(ts, frm, to, days=30.0, category="staking"):
    return {"timestamp": ts, "noOfTokens": [frm, to], "category": category,
            "unlockType": "linear", "rateDurationDays": days}


def test_parse_events_sorts_by_timestamp():
    p = _payload([_cliff(300, 1), _cliff(100, 2), _cliff(200, 3)])
    ev = parse_events(p)
    assert [e["ts"] for e in ev] == [100, 200, 300]


def test_schedule_as_of_excludes_future_events():
    ev = parse_events(_payload([_cliff(100, 1), _cliff(500, 2)]))
    t = pd.Timestamp(300, unit="s", tz="UTC")
    assert len(schedule_as_of(ev, t)) == 1


def test_schedule_as_of_includes_the_boundary_event():
    ev = parse_events(_payload([_cliff(300, 1)]))
    t = pd.Timestamp(300, unit="s", tz="UTC")
    assert len(schedule_as_of(ev, t)) == 1


def test_cliff_in_horizon_counted_once():
    ev = parse_events(_payload([_cliff(10 * DAY, 1000)]))
    t = pd.Timestamp(5 * DAY, unit="s", tz="UTC")
    assert unlocked_between(ev, t, 14) == pytest.approx(1000.0)
    assert unlocked_between(ev, t, 3) == pytest.approx(0.0)


def test_cliff_exactly_at_t_is_not_in_the_forward_window():
    """Window is (t, t+H] -- an unlock already released at t is not upcoming."""
    ev = parse_events(_payload([_cliff(10 * DAY, 1000)]))
    t = pd.Timestamp(10 * DAY, unit="s", tz="UTC")
    assert unlocked_between(ev, t, 14) == pytest.approx(0.0)


def test_linear_rate_accrues_over_the_horizon():
    # 700 tokens per 7-day period from day 0 => 100/day
    ev = parse_events(_payload([_linear(0, 0.0, 700.0, days=7.0)]))
    t = pd.Timestamp(10 * DAY, unit="s", tz="UTC")
    assert unlocked_between(ev, t, 14) == pytest.approx(1400.0)


def test_amendment_after_t_is_invisible():
    """The whole point: a rate increase dated later must not affect the as-of-t view."""
    ev = parse_events(_payload([_linear(0, 0.0, 700.0, days=7.0),
                                _linear(20 * DAY, 700.0, 7000.0, days=7.0)]))
    t = pd.Timestamp(10 * DAY, unit="s", tz="UTC")
    assert unlocked_between(ev, t, 14) == pytest.approx(1400.0)
    t2 = pd.Timestamp(25 * DAY, unit="s", tz="UTC")
    assert unlocked_between(ev, t2, 14) == pytest.approx(14000.0)


def test_circulating_accumulates_cliffs_and_linear():
    ev = parse_events(_payload([_cliff(0, 500), _linear(0, 0.0, 700.0, days=7.0)]))
    t = pd.Timestamp(10 * DAY, unit="s", tz="UTC")
    assert circulating_as_of(ev, t) == pytest.approx(500.0 + 1000.0)


def test_circulating_is_monotone_non_decreasing():
    ev = parse_events(_payload([_cliff(0, 500), _cliff(5 * DAY, 200),
                                _linear(0, 0.0, 70.0, days=7.0)]))
    vals = [circulating_as_of(ev, pd.Timestamp(d * DAY, unit="s", tz="UTC"))
            for d in range(0, 20)]
    assert all(b >= a for a, b in zip(vals, vals[1:]))


def test_amendment_share_zero_when_only_tge_schedule():
    ev = parse_events(_payload([_cliff(0, 500), _linear(0, 0.0, 700.0, days=7.0)]))
    lo = pd.Timestamp(0, unit="s", tz="UTC")
    hi = pd.Timestamp(30 * DAY, unit="s", tz="UTC")
    assert amendment_share(ev, lo, hi) == pytest.approx(0.0)


def test_amendment_share_positive_when_rate_changed_later():
    ev = parse_events(_payload([_linear(0, 0.0, 700.0, days=7.0),
                                _linear(15 * DAY, 700.0, 7000.0, days=7.0)]))
    lo = pd.Timestamp(0, unit="s", tz="UTC")
    hi = pd.Timestamp(30 * DAY, unit="s", tz="UTC")
    assert amendment_share(ev, lo, hi) > 0.0


def test_empty_event_log_is_zero_not_crash():
    ev = parse_events(_payload([]))
    t = pd.Timestamp(0, unit="s", tz="UTC")
    assert unlocked_between(ev, t, 14) == 0.0
    assert circulating_as_of(ev, t) == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-sync python -m pytest tests/xsect/test_unlock_schedule.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Write the reconstruction module**

```python
# tradingagents/xsect/unlock_schedule.py
"""Point-in-time reconstruction of DefiLlama vesting schedules.

The emissions payload's ``metadata.events`` list carries a timestamp on every
schedule change, including amendments ("linear unlock was increased from X to
Y per week"). Replaying that list in timestamp order and applying only events
with ts <= t therefore yields the forward unlock curve as it was KNOWN at t,
rather than today's amended schedule.

Residual hazard, not detectable from a single snapshot: DefiLlama may have
silently corrected bad data without emitting a timestamped event. Probe P0 in
scripts/unlock_xs_dev.py quantifies it against an independent supply series.

Timestamps are unix seconds. Forward windows are half-open (t, t+H] -- an
unlock released exactly at t is already circulating, not upcoming.
"""
from __future__ import annotations

import pandas as pd

SECONDS_PER_DAY = 86400.0


def parse_events(payload: dict) -> list[dict]:
    """Normalize metadata.events into sorted, typed records."""
    raw = (payload.get("metadata") or {}).get("events") or []
    out = []
    for e in raw:
        ts = e.get("timestamp")
        if ts is None:
            continue
        tokens = e.get("noOfTokens") or []
        out.append({
            "ts": int(ts),
            "category": e.get("category"),
            "unlock_type": e.get("unlockType"),
            "tokens": [float(x) for x in tokens],
            "rate_duration_days": float(e.get("rateDurationDays") or 0.0),
        })
    out.sort(key=lambda e: e["ts"])
    return out


def schedule_as_of(events: list[dict], t: pd.Timestamp) -> list[dict]:
    """Events knowable at ``t`` (inclusive of an event dated exactly t)."""
    cutoff = int(t.timestamp())
    return [e for e in events if e["ts"] <= cutoff]


def _rate_segments(events: list[dict]) -> list[tuple[int, float]]:
    """(effective_ts, tokens_per_second) for the linear component.

    A linear event's noOfTokens is [from_rate, to_rate] per rateDurationDays;
    a single-element list is treated as the new rate directly.
    """
    segs = []
    for e in events:
        if e["unlock_type"] != "linear" or e["rate_duration_days"] <= 0:
            continue
        new_rate = e["tokens"][-1] if e["tokens"] else 0.0
        per_sec = new_rate / (e["rate_duration_days"] * SECONDS_PER_DAY)
        segs.append((e["ts"], per_sec))
    return segs


def _linear_released(events: list[dict], lo: int, hi: int) -> float:
    """Tokens released by linear schedules over the open-closed interval (lo, hi]."""
    segs = _rate_segments(events)
    if not segs or hi <= lo:
        return 0.0
    total = 0.0
    for i, (start, rate) in enumerate(segs):
        end = segs[i + 1][0] if i + 1 < len(segs) else None
        seg_lo = max(lo, start)
        seg_hi = hi if end is None else min(hi, end)
        if seg_hi > seg_lo:
            total += rate * (seg_hi - seg_lo)
    return total


def unlocked_between(events: list[dict], t: pd.Timestamp, horizon_days: int) -> float:
    """Tokens released in (t, t+horizon] under the schedule known at ``t``."""
    known = schedule_as_of(events, t)
    if not known:
        return 0.0
    lo = int(t.timestamp())
    hi = lo + int(horizon_days * SECONDS_PER_DAY)
    cliffs = sum(e["tokens"][0] if e["tokens"] else 0.0
                 for e in known
                 if e["unlock_type"] == "cliff" and lo < e["ts"] <= hi)
    return float(cliffs + _linear_released(known, lo, hi))


def circulating_as_of(events: list[dict], t: pd.Timestamp) -> float:
    """Cumulative tokens released up to and including ``t``."""
    known = schedule_as_of(events, t)
    if not known:
        return 0.0
    hi = int(t.timestamp())
    lo = known[0]["ts"]
    cliffs = sum(e["tokens"][0] if e["tokens"] else 0.0
                 for e in known if e["unlock_type"] == "cliff" and e["ts"] <= hi)
    return float(cliffs + _linear_released(known, lo - 1, hi))


def amendment_share(events: list[dict], t_lo: pd.Timestamp,
                    t_hi: pd.Timestamp) -> float:
    """Fraction of released tokens over [t_lo, t_hi] attributable to post-TGE
    schedule amendments rather than the original schedule.

    Reported (not gated) so the residual look-ahead exposure of the
    reconstruction is visible in forensics.
    """
    if not events:
        return 0.0
    tge = events[0]["ts"]
    full = circulating_as_of(events, t_hi) - circulating_as_of(events, t_lo)
    if full <= 0:
        return 0.0
    original = [e for e in events if e["ts"] <= tge]
    orig_amt = (circulating_as_of(original, t_hi) - circulating_as_of(original, t_lo))
    return float(max(0.0, full - orig_amt) / full)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --no-sync python -m pytest tests/xsect/test_unlock_schedule.py -v`
Expected: 12 passed

- [ ] **Step 5: Mutation kill-test on the PIT cutoff**

Change `schedule_as_of`'s filter from `e["ts"] <= cutoff` to `e["ts"] <= cutoff + 30 * 86400` (a 30-day look-ahead) and re-run.
Expected: `test_schedule_as_of_excludes_future_events` and `test_amendment_after_t_is_invisible` **FAIL**.
Revert and confirm 12 pass. If the suite stays green under that mutation, the tests do not actually verify point-in-time behaviour and must be strengthened before proceeding.

- [ ] **Step 6: Commit**

```bash
git add tradingagents/xsect/unlock_schedule.py tests/xsect/test_unlock_schedule.py
git commit -m "feat(unlock-xs): point-in-time vesting schedule reconstruction

Replays metadata.events in timestamp order applying only ts <= t, so the
forward unlock curve is the one known at t rather than today's amended
schedule. Mutation kill-test pins the PIT cutoff.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: Unlock signal engine + monthly PIT universe

**Files:**
- Create: `tradingagents/xsect/unlock_xs.py`, `scripts/unlock_xs_universe.py`
- Creates at runtime: `data/xsect/unlock_xs_universe.json`
- Test: extend `tests/xsect/test_unlock_xs.py`

**Interfaces:**
- Consumes: Task 9 store, Task 10 reconstruction, Task 1 `ls_weights`.
- Produces:
  - `load_unlock_events(unlock_dir: Path, protocol_to_symbol: dict) -> dict[str, list[dict]]` keyed by perp symbol.
  - `burden_matrix(events_by_symbol, all_days, horizon_days) -> pd.DataFrame` — `unlock_burden(t, N)`.
  - `supply_matrix(events_by_symbol, all_days) -> pd.DataFrame` — as-of-`t` circulating supply.
  - `size_control(klines, supply, all_days, columns, lag_days=2) -> pd.DataFrame` — C2′, log market cap, z-scored, high = short leg.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/xsect/test_unlock_xs.py
import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.unlock_schedule import parse_events
from tradingagents.xsect.unlock_xs import burden_matrix, size_control, supply_matrix

DAY = 86400


def _ev(events):
    return parse_events({"metadata": {"events": events}})


def test_burden_is_upcoming_tokens_over_circulating():
    ev = _ev([{"timestamp": 0, "noOfTokens": [1000], "category": "c", "unlockType": "cliff"},
              {"timestamp": 20 * DAY, "noOfTokens": [500], "category": "c", "unlockType": "cliff"}])
    days = pd.date_range("1970-01-01", periods=40, freq="D", tz="UTC")
    B = burden_matrix({"AUSDT": ev}, days, horizon_days=30)
    # at day 10: upcoming 500 (the day-20 cliff is future-dated, so unknown) -> 0
    assert B.loc[days[10], "AUSDT"] == pytest.approx(0.0)
    # at day 20 the cliff is known but already released -> not upcoming
    assert B.loc[days[20], "AUSDT"] == pytest.approx(0.0)


def test_burden_zero_when_no_upcoming_unlocks():
    ev = _ev([{"timestamp": 0, "noOfTokens": [1000], "category": "c", "unlockType": "cliff"}])
    days = pd.date_range("1970-01-01", periods=40, freq="D", tz="UTC")
    B = burden_matrix({"AUSDT": ev}, days, horizon_days=14)
    assert (B["AUSDT"].fillna(0.0) == 0.0).all()


def test_burden_positive_for_known_linear_emission():
    ev = _ev([{"timestamp": 0, "noOfTokens": [0, 700], "category": "s",
               "unlockType": "linear", "rateDurationDays": 7.0}])
    days = pd.date_range("1970-01-01", periods=40, freq="D", tz="UTC")
    B = burden_matrix({"AUSDT": ev}, days, horizon_days=14)
    assert B.loc[days[20], "AUSDT"] > 0.0


def test_burden_is_nan_when_supply_is_zero():
    ev = _ev([])
    days = pd.date_range("1970-01-01", periods=5, freq="D", tz="UTC")
    B = burden_matrix({"AUSDT": ev}, days, horizon_days=14)
    assert B["AUSDT"].isna().all()


def test_supply_matrix_is_monotone():
    ev = _ev([{"timestamp": 0, "noOfTokens": [100], "category": "c", "unlockType": "cliff"},
              {"timestamp": 10 * DAY, "noOfTokens": [50], "category": "c", "unlockType": "cliff"}])
    days = pd.date_range("1970-01-01", periods=20, freq="D", tz="UTC")
    S = supply_matrix({"AUSDT": ev}, days)
    v = S["AUSDT"].to_numpy()
    assert all(b >= a for a, b in zip(v, v[1:]))


def test_size_control_shorts_large_caps():
    days = pd.date_range("2022-01-01", periods=10, freq="D", tz="UTC")
    k = {"BIGUSDT": pd.DataFrame({"close": [100.0] * 10}, index=days),
         "SMLUSDT": pd.DataFrame({"close": [1.0] * 10}, index=days)}
    sup = pd.DataFrame({"BIGUSDT": [1e6] * 10, "SMLUSDT": [1e3] * 10}, index=days)
    C = size_control(k, sup, days, ["BIGUSDT", "SMLUSDT"], lag_days=2)
    assert C.iloc[-1]["BIGUSDT"] > C.iloc[-1]["SMLUSDT"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-sync python -m pytest tests/xsect/test_unlock_xs.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tradingagents.xsect.unlock_xs'`

- [ ] **Step 3: Write the engine**

```python
# tradingagents/xsect/unlock_xs.py
"""Cross-sectional token-unlock burden signal (unlock_xs_t1).

burden(t, N) = tokens unlocking in (t, t+N] / circulating supply at t, both
computed from the as-of-t reconstruction in unlock_schedule.py. High burden =
short leg (dilution pressure). Registered in gates.json under unlock_xs_t1.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from tradingagents.xsect.unlock_schedule import (
    circulating_as_of, parse_events, unlocked_between,
)


def load_unlock_events(unlock_dir: Path,
                       protocol_to_symbol: dict) -> dict[str, list[dict]]:
    """Parsed event logs keyed by perp symbol."""
    out = {}
    for slug, symbol in protocol_to_symbol.items():
        p = Path(unlock_dir) / f"{slug}.json"
        if not p.exists():
            continue
        out[symbol] = parse_events(json.loads(p.read_text()))
    return out


def supply_matrix(events_by_symbol: dict, all_days: pd.DatetimeIndex) -> pd.DataFrame:
    cols = {}
    for sym, ev in events_by_symbol.items():
        cols[sym] = pd.Series([circulating_as_of(ev, t) for t in all_days],
                              index=all_days, dtype=float)
    return pd.DataFrame(cols, index=all_days).sort_index(axis=1)


def burden_matrix(events_by_symbol: dict, all_days: pd.DatetimeIndex,
                  horizon_days: int) -> pd.DataFrame:
    """Upcoming unlock tokens over circulating supply. NaN where supply is 0."""
    cols = {}
    for sym, ev in events_by_symbol.items():
        up = np.array([unlocked_between(ev, t, horizon_days) for t in all_days])
        sup = np.array([circulating_as_of(ev, t) for t in all_days])
        with np.errstate(divide="ignore", invalid="ignore"):
            b = np.where(sup > 0, up / sup, np.nan)
        cols[sym] = pd.Series(b, index=all_days, dtype=float)
    return pd.DataFrame(cols, index=all_days).sort_index(axis=1)


def size_control(klines: dict, supply: pd.DataFrame, all_days: pd.DatetimeIndex,
                 columns, lag_days: int = 2) -> pd.DataFrame:
    """C2': log market cap, cross-sectionally z-scored. High = short leg.

    Market cap = perp close x as-of-t circulating supply from the same
    reconstruction that feeds the signal denominator (NOT CoinMetrics: the 129
    unlock names and 132 CoinMetrics names are largely disjoint).
    """
    px = pd.DataFrame({s: klines[s]["close"].reindex(all_days)
                       for s in columns if s in klines}, index=all_days)
    mcap = px * supply.reindex(index=all_days, columns=px.columns)
    lg = np.log(mcap.where(mcap > 0))
    mu = lg.mean(axis=1)
    sd = lg.std(axis=1, ddof=1)
    z = lg.sub(mu, axis=0).div(sd.where(sd > 0), axis=0)
    return z.shift(lag_days) if lag_days else z
```

- [ ] **Step 4: Write the universe builder**

```python
# scripts/unlock_xs_universe.py
"""Monthly PIT universe for unlock_xs_t1: unlock protocols INTERSECT top-150."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.fetch_xsect_unlocks import PROTOCOL_TO_SYMBOL  # noqa: E402
from tradingagents.xsect.liq_fade import monthly_top_n  # noqa: E402
from tradingagents.xsect.universe import load_klines  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "xsect" / "unlock_xs_universe.json"
DEV = ("2021-01-01", "2025-03-31")
FLOOR_RANK = 150


def main() -> None:
    daily = load_klines(ROOT / "data" / "xsect" / "klines")
    liquid = monthly_top_n(daily, DEV[0], DEV[1], n=FLOOR_RANK)
    allowed = set(PROTOCOL_TO_SYMBOL.values())
    out = {month: sorted(set(syms) & allowed) for month, syms in liquid.items()}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    sizes = [len(v) for v in out.values()]
    by_year: dict[str, list[int]] = {}
    for m, v in out.items():
        by_year.setdefault(m[:4], []).append(len(v))
    print(f"months={len(out)} median={sorted(sizes)[len(sizes)//2]}")
    for y, v in sorted(by_year.items()):
        print(f"  {y}: median {sorted(v)[len(v)//2]}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Build and check the breadth STOP**

Run: `uv run --no-sync python scripts/unlock_xs_universe.py`
Expected: per-year median breadth printed.

**Decision point:** if overall median < 20, breadth STOP fires — record and stop Phase C. If only 2021 and 2022 fall below 20, truncate the dev window forward to `2023-01-01`, record the truncation in `gates.json` under a `dev_window_amendment` key with the observed numbers, commit that amendment, and only then continue.

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run --no-sync python -m pytest tests/xsect/test_unlock_xs.py -v`
Expected: 10 passed

- [ ] **Step 7: Commit**

```bash
git add tradingagents/xsect/unlock_xs.py scripts/unlock_xs_universe.py \
        data/xsect/unlock_xs_universe.json tests/xsect/test_unlock_xs.py
git commit -m "feat(unlock-xs): burden signal, supply matrix, size control, PIT universe

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: Unlock dev runner — probes P0–P2 and the frozen 2-config grid

**Files:**
- Create: `scripts/unlock_xs_dev.py`
- Test: `tests/xsect/test_unlock_xs_dev.py`

**Interfaces:**
- Consumes: Tasks 1, 9, 10, 11; reuses `circular_shift_columns`, `rank_shuffle_columns`, `dsr_or_nan`, `gate_config`, `run_config` imported from `scripts.value_xs_dev` (identical mechanics, so importing keeps the two experiments byte-comparable rather than re-deriving).
- Produces: `data/rebuild/unlock_xs/probes.json`, `grid.json`, and 2 ledger rows.

- [ ] **Step 1: Write the failing tests**

```python
# tests/xsect/test_unlock_xs_dev.py
import numpy as np
import pandas as pd
import pytest

from scripts.unlock_xs_dev import (
    GRID, event_study_forward_return, supply_divergence, verdict_from_probes,
)


def test_grid_is_frozen_at_two_configs():
    assert len(GRID) == 2
    assert set(GRID) == {14, 30}


def test_supply_divergence_zero_for_identical_series():
    days = pd.date_range("2022-01-01", periods=10, freq="D", tz="UTC")
    a = pd.Series(np.arange(10.0), index=days)
    assert supply_divergence(a, a.copy()) == pytest.approx(0.0)


def test_supply_divergence_detects_growing_gap():
    days = pd.date_range("2022-01-01", periods=10, freq="D", tz="UTC")
    a = pd.Series(np.arange(10.0) + 1, index=days)
    b = pd.Series((np.arange(10.0) + 1) * np.linspace(1.0, 2.0, 10), index=days)
    assert supply_divergence(a, b) > 0.1


def test_event_study_recovers_planted_negative_drift():
    days = pd.date_range("2022-01-03", periods=100, freq="D", tz="UTC")
    R = pd.DataFrame({"AUSDT": 0.0}, index=days)
    R.iloc[50:64] = -0.01          # 14 days of -1% after the event at day 49
    events = [("AUSDT", days[49])]
    m = event_study_forward_return(events, R, horizon=14)
    assert m < 0


def test_event_study_zero_when_no_events():
    days = pd.date_range("2022-01-03", periods=20, freq="D", tz="UTC")
    R = pd.DataFrame({"AUSDT": 0.01}, index=days)
    assert event_study_forward_return([], R, horizon=14) == 0.0


def test_verdict_stops_on_any_failed_probe():
    ok, bad = {"pass": True}, {"pass": False}
    assert verdict_from_probes(ok, ok, ok) == "CONTINUE"
    assert verdict_from_probes(ok, ok, bad) == "NEGATIVE-at-probe"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-sync python -m pytest tests/xsect/test_unlock_xs_dev.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Write the dev runner**

```python
# scripts/unlock_xs_dev.py
"""unlock_xs_t1 dev runner: probes P0-P2 (STOP semantics) then the frozen grid.

Grid mechanics (weights, P&L, placebo families, DSR, gate) are imported from
scripts.value_xs_dev rather than re-derived, so the two experiments are
byte-comparable and a fix to one cannot silently diverge from the other.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.fetch_xsect_unlocks import PROTOCOL_TO_SYMBOL  # noqa: E402
from scripts.value_xs_dev import (  # noqa: E402
    circular_shift_columns, dsr_or_nan, gate_config, rank_shuffle_columns,
    run_config, unique_config_hashes, verdict_from_probes,
)
from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.xsect.ls_common import sharpe_365  # noqa: E402
from tradingagents.xsect.portfolio import maxdd, rank_placebo_pvalue  # noqa: E402
from tradingagents.xsect.universe import load_klines  # noqa: E402
from tradingagents.xsect.unlock_schedule import (  # noqa: E402
    amendment_share, circulating_as_of, schedule_as_of,
)
from tradingagents.xsect.unlock_xs import (  # noqa: E402
    burden_matrix, load_unlock_events, size_control, supply_matrix,
)
from tradingagents.xsect.value_xs import (  # noqa: E402
    control_signal, membership_mask, simple_returns,
)

ROOT = Path(__file__).resolve().parents[1]
UNLOCK_DIR = ROOT / "data" / "xsect" / "unlocks"
KLINES_DIR = ROOT / "data" / "xsect" / "klines"
UNIV_FILE = ROOT / "data" / "xsect" / "unlock_xs_universe.json"
OUT_DIR = ROOT / "data" / "rebuild" / "unlock_xs"

DEV = ("2021-01-01", "2025-03-31")
WARMUP_START = "2020-06-01"
MAX_LOAD_END = "2025-03-31"
GRID = [14, 30]                    # lookahead days, decile only -- frozen
LEG_FRAC_DECILE = 0.1
LAG_DAYS = 2
MIN_MEDIAN_BREADTH = 20
CLIFF_PCT_FLOOR = 0.01             # "large" = >= 1% of circulating supply
EVENT_HORIZON = 14
MAX_SUPPLY_DIVERGENCE = 0.25       # P0 STOP threshold
N_PLACEBO = 500


def supply_divergence(recon: pd.Series, independent: pd.Series) -> float:
    """Mean absolute relative gap over the overlap, weighted toward recent dates.

    A silent restatement shows up as a gap that grows toward the present, so
    the second half of the overlap is weighted double.
    """
    a, b = recon.align(independent, join="inner")
    a, b = a.dropna(), b.reindex(a.index).dropna()
    a = a.reindex(b.index)
    if len(a) == 0:
        return float("nan")
    rel = (a - b).abs() / b.where(b > 0)
    rel = rel.dropna()
    if rel.empty:
        return float("nan")
    half = len(rel) // 2
    w = np.concatenate([np.ones(half), 2 * np.ones(len(rel) - half)])
    return float(np.average(rel.to_numpy(), weights=w))


def event_study_forward_return(events: list[tuple[str, pd.Timestamp]],
                               R: pd.DataFrame, horizon: int) -> float:
    """Mean cumulative simple return over (t, t+horizon] across events."""
    if not events:
        return 0.0
    vals = []
    for sym, t in events:
        if sym not in R.columns:
            continue
        seg = R[sym].loc[R.index > t].head(horizon)
        if len(seg) == horizon:
            vals.append(float(seg.sum()))
    return float(np.mean(vals)) if vals else 0.0


def _load_all():
    days = pd.date_range(WARMUP_START, MAX_LOAD_END, freq="D", tz="UTC")
    universe = json.loads(UNIV_FILE.read_text())
    symbols = sorted({s for v in universe.values() for s in v})
    klines = {s: d for s, d in load_klines(KLINES_DIR).items() if s in symbols}
    events = {s: e for s, e in
              load_unlock_events(UNLOCK_DIR, PROTOCOL_TO_SYMBOL).items() if s in symbols}
    return days, klines, events, universe, symbols


def probe_p0_supply(days, events, klines) -> dict:
    """Reconstructed supply vs an independent series, per symbol."""
    recon = supply_matrix(events, days)
    divs = {}
    fund_dir = ROOT / "data" / "xsect" / "fundamentals"
    for sym in recon.columns:
        # independent check: CoinMetrics SplyCur where the asset is covered
        asset = sym[:-4].lower()
        p = fund_dir / f"{asset}.parquet"
        if not p.exists():
            continue
        ext = pd.read_parquet(p)
        if "CapMrktCurUSD" not in ext.columns or sym not in klines:
            continue
        px = klines[sym]["close"].reindex(days)
        implied = (ext["CapMrktCurUSD"].reindex(days) / px.where(px > 0))
        d = supply_divergence(recon[sym], implied)
        if not np.isnan(d):
            divs[sym] = d
    med = float(np.median(list(divs.values()))) if divs else float("nan")
    return {"probe": "P0_supply_reconstruction", "n_compared": len(divs),
            "median_relative_divergence": med,
            "threshold": MAX_SUPPLY_DIVERGENCE,
            "worst": sorted(divs.items(), key=lambda kv: -kv[1])[:5],
            "pass": bool(divs and med <= MAX_SUPPLY_DIVERGENCE),
            "note": "no overlap names to compare" if not divs else ""}


def probe_p1_breadth(universe) -> dict:
    sizes = {m: len(v) for m, v in universe.items()}
    by_year: dict[str, list[int]] = {}
    for m, n in sizes.items():
        by_year.setdefault(m[:4], []).append(n)
    med = statistics.median(sizes.values())
    return {"probe": "P1_breadth", "median_breadth": med,
            "breadth_by_year": {y: statistics.median(v) for y, v in sorted(by_year.items())},
            "floor": MIN_MEDIAN_BREADTH, "pass": bool(med >= MIN_MEDIAN_BREADTH)}


def probe_p2_event_study(days, events, klines, symbols) -> dict:
    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    R = simple_returns(klines, days, symbols).loc[dev]
    big = []
    for sym, ev in events.items():
        for e in ev:
            if e["unlock_type"] != "cliff" or not e["tokens"]:
                continue
            t = pd.Timestamp(e["ts"], unit="s", tz="UTC").normalize()
            if not (dev[0] <= t <= dev[-1]):
                continue
            sup = circulating_as_of(schedule_as_of(ev, t), t)
            if sup > 0 and e["tokens"][0] / sup >= CLIFF_PCT_FLOOR:
                big.append((sym, t))
    mean_fwd = event_study_forward_return(big, R, EVENT_HORIZON)
    return {"probe": "P2_event_study", "n_events": len(big),
            "mean_fwd_return": mean_fwd, "horizon_days": EVENT_HORIZON,
            "cliff_pct_floor": CLIFF_PCT_FLOOR,
            "pass": bool(len(big) >= 30 and mean_fwd < 0),
            "note": "expected sign is negative (dilution); >=30 events required "
                    "for the probe to be informative"}


def run_grid(days, klines, events, universe, symbols, n_placebo: int = N_PLACEBO,
             log: bool = True) -> dict:
    """Frozen 2-config grid. ``log=False`` suppresses ledger writes for smoke runs."""
    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    R = simple_returns(klines, days, symbols).loc[dev]
    M = membership_mask(days, symbols, universe).loc[dev]
    supply = supply_matrix(events, days)

    controls = {}
    C1 = control_signal(klines, days, symbols, "vol").loc[dev]
    controls["vol"] = sharpe_365(run_config(C1, R, M & C1.notna(), LEG_FRAC_DECILE))
    C2 = size_control(klines, supply, days, symbols, LAG_DAYS).loc[dev]
    controls["size"] = sharpe_365(run_config(C2, R, M & C2.notna(), LEG_FRAC_DECILE))

    ledger_before = unique_config_hashes()
    rng = np.random.default_rng(20260730)
    results = []
    for horizon in GRID:
        B = burden_matrix(events, days, horizon).shift(LAG_DAYS).loc[dev]
        valid = M & B.notna()
        port = run_config(B, R, valid, LEG_FRAC_DECILE)
        net_sr = sharpe_365(port)

        srs_a = [sharpe_365(run_config(circular_shift_columns(B, rng), R, valid,
                                       LEG_FRAC_DECILE)) for _ in range(n_placebo)]
        srs_b = [sharpe_365(run_config(rank_shuffle_columns(B, rng), R, valid,
                                       LEG_FRAC_DECILE)) for _ in range(n_placebo)]
        p_a, p_b = rank_placebo_pvalue(net_sr, srs_a), rank_placebo_pvalue(net_sr, srs_b)
        p_worse = max(p_a, p_b)

        dsr_own = dsr_or_nan(port, net_sr, n_trials=len(GRID))
        dsr_ledger = dsr_or_nan(port, net_sr, n_trials=ledger_before + len(GRID))
        d_c1 = net_sr - controls["vol"]
        d_c2 = net_sr - controls["size"]
        gate = gate_config(net_sr, p_worse, dsr_own, d_c1, d_c2)

        amend = float(np.mean([amendment_share(e, dev[0], dev[-1])
                               for e in events.values() if e]))
        cfg = {"lookahead_days": horizon, "breadth": "decile",
               "leg_frac": LEG_FRAC_DECILE, "lag_days": LAG_DAYS, "cost_bps": 10.0,
               "rebalance": "weekly_monday", "universe": "unlock_xs_universe.json",
               "n_symbols": int(len(symbols))}
        metrics = {"net_sr": net_sr, "maxdd": float(maxdd(port)),
                   "n_bars": int(len(port)),
                   "placebo_p_shiftfam": p_a, "placebo_p_randfam": p_b,
                   "placebo_p_worse": p_worse,
                   "dsr_own_n": dsr_own, "dsr_own_n_trials": len(GRID),
                   "dsr_ledger_n": dsr_ledger,
                   "dsr_ledger_n_trials": ledger_before + len(GRID),
                   "sr_control_vol": controls["vol"], "sr_control_size": controls["size"],
                   "delta_sr_vs_c1": d_c1, "delta_sr_vs_c2": d_c2,
                   "mean_amendment_share": amend,
                   **{f"gate_{k}": v for k, v in gate["checks"].items()},
                   "gate_pass": gate["pass"]}
        if log:
            log_trial("unlock_xs_t1", cfg, DEV, metrics)
        results.append({"config": cfg, "metrics": metrics})
        print(f"N={horizon}: SR {net_sr:+.3f} p {p_worse:.4f} DSR {dsr_own:.3f} "
              f"dC1 {d_c1:+.3f} dC2 {d_c2:+.3f} amend {amend:.1%} "
              f"{'PASS' if gate['pass'] else 'FAIL'}")

    passing = [r for r in results if r["metrics"]["gate_pass"]]
    out = {"experiment": "unlock_xs_t1", "controls": controls,
           "ledger_unique_hashes_before": ledger_before,
           "results": results, "n_pass": len(passing),
           "verdict": "GO-at-dev" if passing else "NEGATIVE"}
    (OUT_DIR / "grid.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"VERDICT: {out['verdict']} ({len(passing)}/{len(GRID)})")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    days, klines, events, universe, symbols = _load_all()
    p0 = probe_p0_supply(days, events, klines)
    p1 = probe_p1_breadth(universe)
    p2 = probe_p2_event_study(days, events, klines, symbols)
    verdict = verdict_from_probes(p0, p1, p2)
    (OUT_DIR / "probes.json").write_text(json.dumps(
        {"experiment": "unlock_xs_t1", "probes": [p0, p1, p2], "verdict": verdict},
        indent=1, default=str))
    for p in (p0, p1, p2):
        print(f"{p['probe']}: {'PASS' if p['pass'] else 'FAIL'}  {p}")
    print(f"VERDICT: {verdict}")
    if verdict != "CONTINUE":
        sys.exit(2)
    run_grid(days, klines, events, universe, symbols)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --no-sync python -m pytest tests/xsect/test_unlock_xs_dev.py -v`
Expected: 6 passed

- [ ] **Step 5: Smoke, then run**

Smoke: `uv run --no-sync python -c "
import scripts.unlock_xs_dev as u
d,k,e,uni,s = u._load_all()
print(u.probe_p1_breadth(uni))
print(u.probe_p2_event_study(d,e,k,s))
"`
Expected: breadth and event-study dicts print with real numbers.

Full run: `uv run --no-sync python scripts/unlock_xs_dev.py`
Expected: three probe lines, then (on CONTINUE) 2 config lines and a `VERDICT:`.

**Decision point:** on `NEGATIVE-at-probe`, stop and write the verdict — do not adjust `MAX_SUPPLY_DIVERGENCE`, `CLIFF_PCT_FLOOR`, or the 30-event minimum after seeing the numbers.

- [ ] **Step 6: Commit**

```bash
git add scripts/unlock_xs_dev.py tests/xsect/test_unlock_xs_dev.py \
        data/rebuild/unlock_xs/ data/rebuild/trial_ledger.jsonl
git commit -m "run(unlock-xs): probes P0-P2 + frozen 2-config grid

Grid mechanics imported from value_xs_dev so both experiments stay
byte-comparable. Mean amendment share reported per config.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 13: Unlock forensics, THESIS §52 and §53, branch wrap-up

**Files:**
- Create: `scripts/unlock_xs_forensics.py`
- Modify: `THESIS_FINDINGS.md`

- [ ] **Step 1: Write the forensics script**

Mirror `scripts/value_xs_forensics.py` (Task 8) with these sections, reading `data/rebuild/unlock_xs/grid.json` and `probes.json`:

- **F1 sign inversion** — SR of the burden signal vs `-burden`, per horizon.
- **F2 leg concentration** — HHI, top-5 weight share, distinct names touched, per horizon.
- **F3 yearly SR** — per calendar year, per horizon.
- **F4 honest denominators** — breadth by year, dev bars, event count from P2, ledger hashes before the run.
- **F5 DSR denominator sensitivity** — DSR at n=2 and at the ledger-cumulative n.
- **F6 controls** — C1 vol and C2′ size SRs and both deltas.
- **F7 cost sensitivity** — 10 / 20 / 30 bps.
- **F8 amendment exposure** — distribution of `amendment_share` across symbols, plus the SR recomputed on the subset of symbols whose amendment share is 0. This is the direct read on residual look-ahead from schedule restatement; report it whatever it says.
- **F9 concentration disclosure** — the single symbol contributing the largest share of the pooled result, and the result with that symbol removed. **Disclosed, not acted on** — the stop rule forbids post-hoc exclusion.

- [ ] **Step 2: Run it**

Run: `uv run --no-sync python scripts/unlock_xs_forensics.py`
Expected: report printed and written to `data/rebuild/unlock_xs/forensics.md`.

- [ ] **Step 3: Write THESIS §52 and §53**

§52 (`unlock_xs_t1`): same structure as §51 — registration, design, probes, grid table, forensics, verdict, sealed-holdout statement. Report both DSR denominators and the amendment-exposure finding explicitly.

§53 (lead #5 retirement): reproduce the reasoning from the spec's final section — the sizing path already vol-targets on 20d realized vol via `vol_targeted_size`, and the stated drawdown-reduction ceiling is already occupied by the 15% circuit breaker (max observed DD across all 18 §41 factor-floor configs is 15.2%, the breaker itself). State plainly that no experiment was run and why, and what would be needed to revive it.

- [ ] **Step 4: Full test suite and holdout audit**

Run: `uv run --no-sync python -m pytest tests/ -q`
Expected: all pass, no regressions in the pre-existing suite.

Run:
```bash
uv run --no-sync python -c "
import json
rows=[json.loads(l) for l in open('data/rebuild/trial_ledger.jsonl') if l.strip()]
new=[r for r in rows if r['experiment'] in ('value_xs_t1','unlock_xs_t1')]
print('new ledger rows:', len(new))
assert all(r['window'][1] <= '2025-03-31' for r in new), 'HOLDOUT LEAK'
print('unique hashes total:', len({r['config_hash'] for r in rows}))
print('holdout intact')
"
```
Expected: `holdout intact`.

- [ ] **Step 5: Commit and push**

```bash
git add scripts/unlock_xs_forensics.py data/rebuild/unlock_xs/forensics.md THESIS_FINDINGS.md
git commit -m "forensics(unlock-xs): verify verdict, THESIS sections 52 and 53

Section 53 retires lead #5 without code: sizing path already vol-targets and
the drawdown ceiling is set by the 15% circuit breaker, not the strategy.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
git push -u origin feature/value-unlock-xs
```

---

## Self-Review

**Spec coverage.** Every spec section maps to a task: registration → Task 2; value universe/signal/lag/controls/grid/probes → Tasks 3–7; unlock PIT reconstruction/universe/signal/controls/grid/probes → Tasks 9–12; shared portfolio, P&L, costs → Task 1 plus `run_config`; windows and sealed holdout → Global Constraints, enforced by `log_trial` and audited in Tasks 8 and 13; stop rule → Tasks 8 F-sections and 13 F9; data build with vintage stamps → Tasks 3 and 9; testing discipline (mutation kill-tests, planted signal, placebo re-derivation, honest denominators) → Tasks 5, 7, 10, 8, 13; lead #5 retirement → Task 13 Step 3; deliverables → Tasks 8 and 13.

**Type consistency checked.** `ls_weights`, `sharpe_365`, `zero_funding` (Task 1) are used with identical signatures in Tasks 6, 7, 12. `run_config`, `circular_shift_columns`, `rank_shuffle_columns`, `dsr_or_nan`, `gate_config`, `unique_config_hashes`, `verdict_from_probes` are defined once (Tasks 6–7) and imported by Task 12 rather than redefined. `membership_mask`, `simple_returns`, `control_signal` are defined in Task 5 and reused by Task 12. `parse_events`/`schedule_as_of`/`unlocked_between`/`circulating_as_of`/`amendment_share` (Task 10) are consumed with matching signatures in Tasks 11 and 12.

**Known risk carried deliberately.** `probe_p0_supply` compares the reconstruction against a CoinMetrics-implied supply that exists only for the small overlap between the 129 unlock names and the 63 fundamentals names. If that overlap is empty the probe returns `pass: False` with `note: "no overlap names to compare"` — an honest STOP rather than a vacuous pass. Should that happen, the correct response is a written pre-run amendment substituting a CoinGecko circulating-supply source, not lowering the probe.
