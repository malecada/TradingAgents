# V5 MIX 8-Coin Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the canonical V5 MIX strategy from 4 coins to 8 (add XRP, DOGE, ADA, TRX) with a core/satellite weighting, without regressing risk-adjusted performance.

**Architecture:** Reuse the V5 MIX engine (`scripts/baseline_v5_mix.py`) unchanged — V2 signal+sizing core, per-coin LGB predictions, no regime overlay, no LLM. Only the coin set, `DEFAULT_ROUTING`, portfolio weight scheme, and `COSTS` tiers change. Build is staged: generate cheap 78f predictions for the new coins first, run a sanity-gate backtest, then ingest derivatives + on-chain data, generate 193f predictions, route each new coin data-driven, and run the final validated 8-coin backtest.

**Tech Stack:** Python, pandas, NumPy, LightGBM, pytest. Existing project scripts: `evaluate_models_multi.py`, `fetch_coinglass_history.py`, `refetch_coinmetrics_full.py`, `backfill_onchain.py`, `baseline_v5_mix.py`.

**Spec:** `docs/superpowers/specs/2026-05-21-v5-8coin-expansion-design.md`

---

## Conventions

- CoinGecko IDs used throughout: `bitcoin ethereum binancecoin solana ripple dogecoin cardano tron`.
- Core coins: `bitcoin ethereum binancecoin solana`. Satellite coins: `ripple dogecoin cardano tron`.
- **Pooling — "2+1" pattern.** Each new coin is trained in its own 3-coin pool `{bitcoin, ethereum, <newcoin>}`, never an 8-coin mega-pool. `CLAUDE.md` documents that pooling beyond BTC+ETH degrades directional accuracy 12-22pp; §20's V5 routing used 3-coin pools per coin (`multi_3coins_bnb_wf`, `multi_3coins_sol_pit_wf`). The existing 4 coins keep their frozen prediction dirs.
- Dir naming: 78f = `data/multi_3coins_<sym>_wf`, 193f = `data/multi_3coins_<sym>_pit_wf`, where `<sym>` ∈ `xrp doge ada trx`.
- Backtest window: `--start 2021-11-07 --end 2026-04-15` (the 4.5-yr V5 walk-forward window).
- All work happens on branch `feature/v5-8coin-expansion`. Create it before Task 1 if not already on it:
  `git checkout -b feature/v5-8coin-expansion`
- Run all commands from the repo root: `/home/malecada/master_thesis/TradingAgents`.

## File Structure

| File | Responsibility | Created / Modified |
|---|---|---|
| `tradingagents/dataflows/coingecko_binance.py` | OHLCV + Binance symbol map | Modify — add `tron` → `TRXUSDT` |
| `scripts/baseline_v5_mix.py` | V5 MIX strategy: routing, cost tiers, portfolio weighting | Modify — add cost-tier fn, weighting fn, 8-coin routing, CLI flags |
| `tests/strategies/test_v5_8coin.py` | Unit tests for cost tiers + core/satellite weighting | Create |
| `data/multi_3coins_{xrp,doge,ada,trx}_wf/` | 78f WF predictions, per-coin {BTC,ETH,coin} pool | Created by script run |
| `data/multi_3coins_{xrp,doge,ada,trx}_pit_wf/` | 193f WF predictions, per-coin {BTC,ETH,coin} pool | Created by script run |
| `data/derivatives/{ripple,dogecoin,cardano,tron}.parquet` | Coinglass derivatives per new coin | Created by script run |
| `data/v5_8coin_production/` | Final 8-coin backtest output (`daily_returns.csv`, `summary.json`) | Created by script run |
| `docs/superpowers/specs/2026-05-21-v5-8coin-routing.json` | Per-new-coin routing decisions from Task 7 | Create |

---

## Phase P1 — 78f predictions for new coins

### Task 1: Add TRX to the Binance symbol map

**Files:**
- Modify: `tradingagents/dataflows/coingecko_binance.py` (`_KNOWN_SYMBOLS`, around line 38-50)
- Test: `tests/strategies/test_v5_8coin.py`

- [ ] **Step 1: Write the failing test**

Create `tests/strategies/test_v5_8coin.py`:

```python
# tests/strategies/test_v5_8coin.py
"""Tests for the V5 MIX 8-coin expansion: symbol map, cost tiers, weighting."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_tron_symbol_resolves():
    from tradingagents.dataflows.coingecko_binance import _KNOWN_SYMBOLS
    assert _KNOWN_SYMBOLS["tron"] == "TRXUSDT"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/test_v5_8coin.py::test_tron_symbol_resolves -v`
Expected: FAIL with `KeyError: 'tron'`

- [ ] **Step 3: Add the symbol**

In `tradingagents/dataflows/coingecko_binance.py`, add to `_KNOWN_SYMBOLS` (next to the other entries):

```python
    "tron": "TRXUSDT",
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/test_v5_8coin.py::test_tron_symbol_resolves -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tradingagents/dataflows/coingecko_binance.py tests/strategies/test_v5_8coin.py
git commit -m "feat(data): add TRX/TRON to Binance symbol map"
```

### Task 2: Generate 78f walk-forward predictions for the 4 new coins (per-coin 3-coin pools)

**Files:**
- Created by run: `data/multi_3coins_{xrp,doge,ada,trx}_wf/preds_lgb_h{7,14}.csv`

Data-generation task (long-running scripts, not a unit-test cycle). Each new coin is trained in its own "2+1" pool `{bitcoin, ethereum, <newcoin>}` — see Conventions; an 8-coin mega-pool would degrade directional accuracy 12-22pp. The existing 4 coins keep their frozen prediction dirs.

- [ ] **Step 1: Run the 78f walk-forward evaluation, one per new coin**

Run (4 separate runs):
```bash
python scripts/evaluate_models_multi.py --coins bitcoin ethereum ripple   --horizons 7 14 --models lgb --output-dir data/multi_3coins_xrp_wf
python scripts/evaluate_models_multi.py --coins bitcoin ethereum dogecoin --horizons 7 14 --models lgb --output-dir data/multi_3coins_doge_wf
python scripts/evaluate_models_multi.py --coins bitcoin ethereum cardano  --horizons 7 14 --models lgb --output-dir data/multi_3coins_ada_wf
python scripts/evaluate_models_multi.py --coins bitcoin ethereum tron     --horizons 7 14 --models lgb --output-dir data/multi_3coins_trx_wf
```
Expected: each completes without error; prints a per-horizon walk-forward summary.

- [ ] **Step 2: Verify each prediction set covers its target coin**

Run:
```bash
python -c "
import pandas as pd
for sym, coin in [('xrp','ripple'),('doge','dogecoin'),('ada','cardano'),('trx','tron')]:
    d = pd.read_csv(f'data/multi_3coins_{sym}_wf/preds_lgb_h7.csv')
    print(sym, coin, 'rows:', int((d['coin_id'] == coin).sum()))
"
```
Expected: each new coin has a non-trivial row count (hundreds of dates spanning 2021→2026). If a coin has zero or very few rows, stop — its OHLCV/feature build failed; diagnose before continuing.

- [ ] **Step 3: Commit the prediction artifacts**

```bash
git add data/multi_3coins_xrp_wf/ data/multi_3coins_doge_wf/ data/multi_3coins_ada_wf/ data/multi_3coins_trx_wf/
git commit -m "data: 78f walk-forward predictions for XRP/DOGE/ADA/TRX (3-coin pools)"
```
(If `data/` is gitignored, skip the `git add` and check `git status` first.)

---

## Phase P2 — sanity gate

### Task 3: 8-coin sanity-gate backtest (new coins on 78f)

**Files:**
- Created by run: `data/v5_8coin_sanity/daily_returns.csv`, `data/v5_8coin_sanity/summary.json`
- Create: `data/v5_8coin_sanity_routing.json`

Purpose: catch a degenerate new coin (dead/flat signal, blown fills) before spending effort on data ingestion. New coins use their 78f 3-coin-pool predictions from Task 2; the existing 4 use their frozen dirs.

- [ ] **Step 1: Write the sanity routing JSON**

Create `data/v5_8coin_sanity_routing.json`:
```json
{
  "bitcoin": "data/multi_2coins_walkforward",
  "ethereum": "data/multi_2coins_pit_wf",
  "binancecoin": "data/multi_3coins_bnb_wf",
  "solana": "data/multi_3coins_sol_pit_wf",
  "ripple": "data/multi_3coins_xrp_wf",
  "dogecoin": "data/multi_3coins_doge_wf",
  "cardano": "data/multi_3coins_ada_wf",
  "tron": "data/multi_3coins_trx_wf"
}
```

- [ ] **Step 2: Run the sanity backtest**

Run:
```bash
python scripts/baseline_v5_mix.py \
    --start 2021-11-07 --end 2026-04-15 \
    --routing-json data/v5_8coin_sanity_routing.json \
    --output-dir data/v5_8coin_sanity
```
Note: this works today because `main()` already iterates `routing.items()` for any number of coins and equal-weights via `df.mean(axis=1)`. No code change needed yet.
Expected: prints a per-coin line (SR, return, maxDD) for all 8 coins plus a portfolio block.

- [ ] **Step 3: Evaluate the gate**

Inspect the per-coin output. **Gate criteria:**
- No new coin (XRP/DOGE/ADA/TRX) shows a degenerate result: SR is a finite number, return is not ~0% or an extreme blow-up (e.g. < -90%), `n_bars` is comparable to the existing coins.
- The 8-coin portfolio SR is a finite, non-catastrophic number (this is a smoke check, NOT the acceptance gate — a modest SR here is fine).

If any new coin is degenerate: STOP. Document the failure, diagnose (inspect that coin's predictions and OHLCV merge), and do not proceed to Phase P3 until resolved.

- [ ] **Step 4: Commit the gate result**

```bash
git add data/v5_8coin_sanity_routing.json
git commit -m "test: P2 sanity-gate backtest — 8-coin all-78f portfolio"
```

---

## Phase P3 — data ingestion + 193f predictions

### Task 4: Ingest Coinglass derivatives for the 4 new coins

**Files:**
- Created by run: `data/derivatives/ripple.parquet`, `data/derivatives/dogecoin.parquet`, `data/derivatives/cardano.parquet`, `data/derivatives/tron.parquet`

- [ ] **Step 1: Inspect the fetch script's interface**

Run: `python scripts/fetch_coinglass_history.py --help`
Confirm how coins are passed (a `--coins`/`--coin` argument) and where output is written (`data/derivatives/<coin>.parquet`). Match the calling convention already used for the existing 4 coins.

- [ ] **Step 2: Fetch derivatives history for the new coins**

Run (adjust the flag name to match Step 1's `--help`):
```bash
python scripts/fetch_coinglass_history.py --coins ripple dogecoin cardano tron
```
Expected: completes; writes one parquet per coin under `data/derivatives/`.

- [ ] **Step 3: Build derived derivatives features**

Run:
```bash
python scripts/build_derivatives_features.py --coins ripple dogecoin cardano tron
```
(If `build_derivatives_features.py` has no `--coins` flag or runs over all coins automatically, run it with no args — check `--help` first.)
Expected: derivatives parquets now contain the Coinglass-augmented columns expected by `_add_derivatives_derived` in `tradingagents/dataflows/onchain_features.py`.

- [ ] **Step 4: Verify coverage**

Run:
```bash
python -c "import pandas as pd; \
[print(c, pd.read_parquet(f'data/derivatives/{c}.parquet').shape, \
       pd.read_parquet(f'data/derivatives/{c}.parquet').index.min(), \
       pd.read_parquet(f'data/derivatives/{c}.parquet').index.max()) \
 for c in ['ripple','dogecoin','cardano','tron']]"
```
Expected: each coin has a non-empty frame with history starting on or before 2021-11-07. If a coin's history starts later, note it — that coin's early walk-forward folds will have null derivatives features (acceptable; LGB tolerates nulls).

- [ ] **Step 5: Commit**

```bash
git add data/derivatives/ripple.parquet data/derivatives/dogecoin.parquet data/derivatives/cardano.parquet data/derivatives/tron.parquet
git commit -m "data: Coinglass derivatives history for XRP/DOGE/ADA/TRX"
```
(If `data/` is gitignored, skip the `git add` and record the run in a later commit message — check `git status`.)

### Task 5: Ingest CoinMetrics on-chain data for the 4 new coins

**Files:**
- Modified by run: `data/onchain/<year>/<month>.parquet` (pooled bitemporal store)

- [ ] **Step 1: Inspect the on-chain refetch interface**

Run: `python scripts/refetch_coinmetrics_full.py --help` and `python scripts/backfill_onchain.py --help`
Confirm how coins and date ranges are specified.

- [ ] **Step 2: Refetch CoinMetrics community metrics for the new coins**

Run (adjust flags to match Step 1):
```bash
python scripts/refetch_coinmetrics_full.py --coins ripple dogecoin cardano tron
```
Expected: pulls CoinMetrics community-tier metrics for the 4 coins.

- [ ] **Step 3: Backfill the bitemporal on-chain store**

Run:
```bash
python scripts/backfill_onchain.py --coins ripple dogecoin cardano tron
```
Expected: the `data/onchain/` store now contains rows for the new coins with as-of timestamps (PIT-safe).

- [ ] **Step 4: Verify the PIT on-chain feature builder returns data for the new coins**

Run:
```bash
python -c "
import pandas as pd
from tradingagents.dataflows.onchain_features import build_pit_onchain_features
idx = pd.date_range('2022-01-01', '2026-01-01', freq='D', tz='UTC')
for c in ['ripple','dogecoin','cardano','tron']:
    f = build_pit_onchain_features(c, idx)
    print(c, 'cols:', 0 if f is None else len(f.columns),
          'non-null rows:', 0 if f is None or f.empty else int(f.notna().any(axis=1).sum()))
"
```
Expected: each coin returns a non-empty feature frame. Account-model chains (XRP/TRX/ADA) will have fewer columns than BTC — UTXO-style features are null. This is expected and fine.

- [ ] **Step 5: Commit**

```bash
git add data/onchain/
git commit -m "data: CoinMetrics on-chain PIT store for XRP/DOGE/ADA/TRX"
```
(If `data/` is gitignored, skip and check `git status`.)

### Task 6: Generate 193f walk-forward predictions for the 4 new coins (per-coin 3-coin pools)

**Files:**
- Created by run: `data/multi_3coins_{xrp,doge,ada,trx}_pit_wf/preds_lgb_h{7,14}.csv`

Same "2+1" per-coin pooling as Task 2, with the `--onchain-pit` flag added for the 193f extended feature pool.

- [ ] **Step 1: Run the 193f walk-forward evaluation, one per new coin**

Run (4 separate runs):
```bash
python scripts/evaluate_models_multi.py --coins bitcoin ethereum ripple   --horizons 7 14 --models lgb --onchain-pit --output-dir data/multi_3coins_xrp_pit_wf
python scripts/evaluate_models_multi.py --coins bitcoin ethereum dogecoin --horizons 7 14 --models lgb --onchain-pit --output-dir data/multi_3coins_doge_pit_wf
python scripts/evaluate_models_multi.py --coins bitcoin ethereum cardano  --horizons 7 14 --models lgb --onchain-pit --output-dir data/multi_3coins_ada_pit_wf
python scripts/evaluate_models_multi.py --coins bitcoin ethereum tron     --horizons 7 14 --models lgb --onchain-pit --output-dir data/multi_3coins_trx_pit_wf
```
The `--onchain-pit` flag pulls PIT on-chain + Coinglass derivatives features (see `build_pit_onchain_features`, which reads `data/derivatives/<coin>.parquet`).
Expected: each completes; prints a per-horizon walk-forward summary.

- [ ] **Step 2: Verify each prediction set covers its target coin**

Run:
```bash
python -c "
import pandas as pd
for sym, coin in [('xrp','ripple'),('doge','dogecoin'),('ada','cardano'),('trx','tron')]:
    d = pd.read_csv(f'data/multi_3coins_{sym}_pit_wf/preds_lgb_h7.csv')
    print(sym, coin, 'rows:', int((d['coin_id'] == coin).sum()))
"
```
Expected: each new coin has a non-trivial row count.

- [ ] **Step 3: Commit**

```bash
git add data/multi_3coins_xrp_pit_wf/ data/multi_3coins_doge_pit_wf/ data/multi_3coins_ada_pit_wf/ data/multi_3coins_trx_pit_wf/
git commit -m "data: 193f walk-forward predictions for XRP/DOGE/ADA/TRX (3-coin pools)"
```
(If `data/` is gitignored, skip and check `git status`.)

---

## Phase P4 — routing, code changes, validation

### Task 7: Per-new-coin routing decision (78f vs 193f)

**Files:**
- Create: `docs/superpowers/specs/2026-05-21-v5-8coin-routing.json`

For each new coin, run a standalone single-coin V5 backtest with the 78f predictions and again with the 193f predictions; route the coin to whichever gives the higher Sharpe. One pre-registered choice per coin — no sweep.

- [ ] **Step 1: Run each new coin standalone on both feature pools**

For each `(COIN, SYM)` in `ripple/xrp dogecoin/doge cardano/ada tron/trx`, run twice — once on the 78f dir, once on the 193f dir:
```bash
# example for ripple/xrp — repeat for doge, ada, trx
python scripts/baseline_v5_mix.py --start 2021-11-07 --end 2026-04-15 \
    --routing-json <(echo '{"ripple": "data/multi_3coins_xrp_wf"}') \
    --output-dir data/v5_route_xrp_78f
python scripts/baseline_v5_mix.py --start 2021-11-07 --end 2026-04-15 \
    --routing-json <(echo '{"ripple": "data/multi_3coins_xrp_pit_wf"}') \
    --output-dir data/v5_route_xrp_193f
```
Each run prints a per-coin SR line. Record the Sharpe from each (8 runs total).

- [ ] **Step 2: Record the routing decisions**

For each new coin, pick the dir (`data/multi_3coins_<sym>_wf` or `data/multi_3coins_<sym>_pit_wf`) with the higher standalone Sharpe. Create `docs/superpowers/specs/2026-05-21-v5-8coin-routing.json` with the existing 4 frozen routes plus the 4 chosen routes, e.g.:

```json
{
  "bitcoin": "data/multi_2coins_walkforward",
  "ethereum": "data/multi_2coins_pit_wf",
  "binancecoin": "data/multi_3coins_bnb_wf",
  "solana": "data/multi_3coins_sol_pit_wf",
  "ripple": "data/multi_3coins_xrp_wf",
  "dogecoin": "data/multi_3coins_doge_wf",
  "cardano": "data/multi_3coins_ada_pit_wf",
  "tron": "data/multi_3coins_trx_wf"
}
```
(The four new-coin values are whichever pool won in Step 1 — `_wf` for 78f or `_pit_wf` for 193f. The example above is illustrative, not prescriptive.)

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-05-21-v5-8coin-routing.json
git commit -m "docs: V5 8-coin per-coin routing decisions (data-driven)"
```

### Task 8: Two-tier cost function

**Files:**
- Modify: `scripts/baseline_v5_mix.py` (after the `COSTS` dict, around line 56)
- Test: `tests/strategies/test_v5_8coin.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/strategies/test_v5_8coin.py`:

```python
def test_costs_for_coin_core_unchanged():
    from scripts.baseline_v5_mix import COSTS, costs_for_coin
    c = costs_for_coin("bitcoin")
    assert c == COSTS  # core coins get the legacy cost dict verbatim


def test_costs_for_coin_satellite_haircut():
    from scripts.baseline_v5_mix import COSTS, costs_for_coin
    c = costs_for_coin("ripple")  # default haircut = 1.5
    assert c["slippage"] == pytest.approx(COSTS["slippage"] * 1.5)
    assert c["price_impact"] == pytest.approx(COSTS["price_impact"] * 1.5)
    assert c["fee_rate"] == COSTS["fee_rate"]  # non-haircut keys unchanged


def test_costs_for_coin_satellite_haircut_param():
    from scripts.baseline_v5_mix import COSTS, costs_for_coin
    c = costs_for_coin("dogecoin", sat_haircut=2.0)
    assert c["slippage"] == pytest.approx(COSTS["slippage"] * 2.0)
    assert c["price_impact"] == pytest.approx(COSTS["price_impact"] * 2.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/strategies/test_v5_8coin.py -v -k costs`
Expected: FAIL with `ImportError: cannot import name 'costs_for_coin'`

- [ ] **Step 3: Implement the cost tiers**

In `scripts/baseline_v5_mix.py`, immediately after the `COSTS = dict(...)` block, add:

```python
# --- 8-coin expansion: coin tiers + per-coin cost function -----------------
CORE_COINS = ("bitcoin", "ethereum", "binancecoin", "solana")
SATELLITE_COINS = ("ripple", "dogecoin", "cardano", "tron")
SATELLITE_HAIRCUT = 1.5            # conservative slippage/impact multiplier
SATELLITE_COST_KEYS = ("slippage", "price_impact")


def costs_for_coin(coin: str, sat_haircut: float = SATELLITE_HAIRCUT) -> dict:
    """Return the cost dict for a coin.

    Core coins get the legacy ``COSTS`` verbatim. Satellite coins get
    ``slippage`` and ``price_impact`` scaled by ``sat_haircut`` (default 1.5,
    a margin-of-safety for lower-cap perps). All other cost keys are shared.
    """
    c = dict(COSTS)
    if coin in SATELLITE_COINS:
        for k in SATELLITE_COST_KEYS:
            c[k] = COSTS[k] * sat_haircut
    return c
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/strategies/test_v5_8coin.py -v -k costs`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/baseline_v5_mix.py tests/strategies/test_v5_8coin.py
git commit -m "feat(v5): two-tier cost function (core vs satellite haircut)"
```

### Task 9: Core/satellite portfolio weighting

**Files:**
- Modify: `scripts/baseline_v5_mix.py` (after the cost block from Task 8)
- Test: `tests/strategies/test_v5_8coin.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/strategies/test_v5_8coin.py`:

```python
def test_portfolio_weights_sum_to_one():
    from scripts.baseline_v5_mix import PORTFOLIO_WEIGHTS
    assert sum(PORTFOLIO_WEIGHTS.values()) == pytest.approx(1.0)
    # core coins heavier than satellites
    assert PORTFOLIO_WEIGHTS["bitcoin"] > PORTFOLIO_WEIGHTS["ripple"]


def test_portfolio_return_weighted():
    from scripts.baseline_v5_mix import portfolio_return
    idx = pd.date_range("2022-01-01", periods=3)
    df = pd.DataFrame({"bitcoin": [0.10, 0.0, 0.0],
                       "ripple": [0.0, 0.20, 0.0]}, index=idx)
    weights = {"bitcoin": 0.15, "ripple": 0.10}
    # subset renormalizes: 0.15/0.25=0.6 BTC, 0.10/0.25=0.4 XRP
    out = portfolio_return(df, weights)
    assert out.iloc[0] == pytest.approx(0.10 * 0.6)
    assert out.iloc[1] == pytest.approx(0.20 * 0.4)
    assert out.iloc[2] == pytest.approx(0.0)


def test_portfolio_return_4coin_equals_mean():
    """Regression guard: 4 equal-weight core coins reproduce df.mean()."""
    from scripts.baseline_v5_mix import portfolio_return, PORTFOLIO_WEIGHTS
    idx = pd.date_range("2022-01-01", periods=4)
    df = pd.DataFrame({c: [0.01, 0.02, 0.03, 0.04]
                       for c in ["bitcoin", "ethereum", "binancecoin", "solana"]},
                      index=idx)
    out = portfolio_return(df, PORTFOLIO_WEIGHTS)
    pd.testing.assert_series_equal(out, df.mean(axis=1), check_names=False)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/strategies/test_v5_8coin.py -v -k portfolio`
Expected: FAIL with `ImportError: cannot import name 'PORTFOLIO_WEIGHTS'`

- [ ] **Step 3: Implement the weighting**

In `scripts/baseline_v5_mix.py`, after the cost block from Task 8, add:

```python
# Core/satellite portfolio weights (§ 8-coin expansion spec). Core coins
# 15% each (60% total), satellites 10% each (40% total).
PORTFOLIO_WEIGHTS = {
    "bitcoin": 0.15, "ethereum": 0.15, "binancecoin": 0.15, "solana": 0.15,
    "ripple": 0.10, "dogecoin": 0.10, "cardano": 0.10, "tron": 0.10,
}


def portfolio_return(df: pd.DataFrame, weights: dict) -> pd.Series:
    """Weighted daily portfolio return series.

    ``df`` columns are per-coin daily return series. Weights are restricted
    to the columns present in ``df`` and renormalized to sum to 1, so a
    subset run (e.g. a 4-core-coin regression check) still produces a valid
    portfolio — and an equal-weight subset reproduces ``df.mean(axis=1)``.
    """
    cols = [c for c in weights if c in df.columns]
    if not cols:
        raise ValueError("no weighted coins present in df")
    w = pd.Series({c: weights[c] for c in cols}, dtype=float)
    w = w / w.sum()
    return (df[cols] * w).sum(axis=1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/strategies/test_v5_8coin.py -v -k portfolio`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/baseline_v5_mix.py tests/strategies/test_v5_8coin.py
git commit -m "feat(v5): core/satellite portfolio weighting"
```

### Task 10: Wire 8-coin routing, weights, and cost tiers into `main()`

**Files:**
- Modify: `scripts/baseline_v5_mix.py` (`DEFAULT_ROUTING`, `run_coin` loop and portfolio aggregation in `main()`, `--sat-haircut` CLI flag)

- [ ] **Step 1: Extend `DEFAULT_ROUTING` to 8 coins**

Replace the 4-entry `DEFAULT_ROUTING` dict with the 8-entry routing from Task 7's `2026-05-21-v5-8coin-routing.json` (paste the resolved values — the four new-coin dirs are whatever Task 7 chose):

```python
DEFAULT_ROUTING = {
    "bitcoin":     "data/multi_2coins_walkforward",   # 78f canonical (frozen)
    "ethereum":    "data/multi_2coins_pit_wf",        # 193f extended (frozen)
    "binancecoin": "data/multi_3coins_bnb_wf",        # 78f canonical (frozen)
    "solana":      "data/multi_3coins_sol_pit_wf",    # 193f extended (frozen)
    "ripple":      "data/multi_3coins_xrp_wf",        # routed in Task 7 (_wf or _pit_wf)
    "dogecoin":    "data/multi_3coins_doge_wf",        # routed in Task 7 (_wf or _pit_wf)
    "cardano":     "data/multi_3coins_ada_pit_wf",     # routed in Task 7 (_wf or _pit_wf)
    "tron":        "data/multi_3coins_trx_wf",         # routed in Task 7 (_wf or _pit_wf)
}
```

- [ ] **Step 2: Add the `--sat-haircut` CLI flag**

In `main()`, in the argparse block, add:

```python
    p.add_argument("--sat-haircut", type=float, default=SATELLITE_HAIRCUT,
                   help="Satellite-coin slippage/impact multiplier "
                        "(default 1.5; sweep 1.0/1.5/2.0 for sensitivity)")
```

- [ ] **Step 3: Apply per-coin costs in the `run_coin` loop**

In `main()`, change the coin loop so each coin uses its tiered costs. Replace:

```python
    coin_rets: dict[str, pd.Series] = {}
    for coin, pdir in routing.items():
        r = run_coin(coin, PROJECT_ROOT / pdir, args.start, args.end,
                     kelly_fraction=args.kelly)
        coin_rets[coin] = r
```

with:

```python
    coin_rets: dict[str, pd.Series] = {}
    for coin, pdir in routing.items():
        r = run_coin(coin, PROJECT_ROOT / pdir, args.start, args.end,
                     kelly_fraction=args.kelly,
                     costs_override=costs_for_coin(coin, args.sat_haircut))
        coin_rets[coin] = r
```

- [ ] **Step 4: Use weighted portfolio aggregation**

In `main()`, replace:

```python
    df = pd.DataFrame(coin_rets).dropna().sort_index()
    port = df.mean(axis=1)  # 25% equal-weight
```

with:

```python
    df = pd.DataFrame(coin_rets).dropna().sort_index()
    port = portfolio_return(df, PORTFOLIO_WEIGHTS)  # core/satellite weighted
```

Also update the portfolio print header line from `4-coin V5 MIX portfolio (25% equal-weight, ...)` to `{len(coin_rets)}-coin V5 MIX portfolio (core/satellite weighted, ...)`.

- [ ] **Step 5: Verify the 4-coin regression path still works**

Run the legacy 4-coin config via a routing JSON containing only the 4 frozen coins:
```bash
python -c "import json; json.dump({k: v for k,v in [
  ('bitcoin','data/multi_2coins_walkforward'),
  ('ethereum','data/multi_2coins_pit_wf'),
  ('binancecoin','data/multi_3coins_bnb_wf'),
  ('solana','data/multi_3coins_sol_pit_wf')]}, open('data/v5_4coin_routing.json','w'))"
python scripts/baseline_v5_mix.py --start 2021-11-07 --end 2026-04-15 \
    --routing-json data/v5_4coin_routing.json --output-dir data/v5_4coin_regression
```
Expected: portfolio Sharpe ≈ +3.18 (the current 4-coin V5 baseline; the renormalized 15%-each weights reduce to 25% equal-weight for a 4-core-coin subset, and core coins use unchanged costs — so the result must match the documented baseline). If it does not match within rounding, STOP and diagnose before continuing.

- [ ] **Step 6: Run the full strategy test suite**

Run: `pytest tests/strategies/ -v`
Expected: all tests PASS (existing tests + the new `test_v5_8coin.py`).

- [ ] **Step 7: Commit**

```bash
git add scripts/baseline_v5_mix.py
git commit -m "feat(v5): wire 8-coin routing, core/satellite weights, cost tiers into main()"
```

### Task 11: Final 8-coin walk-forward run + cost sensitivity

**Files:**
- Created by run: `data/v5_8coin_production/`, `data/v5_8coin_sat1.0/`, `data/v5_8coin_sat2.0/`

- [ ] **Step 1: Run the canonical 8-coin backtest**

Run:
```bash
python scripts/baseline_v5_mix.py --start 2021-11-07 --end 2026-04-15 \
    --output-dir data/v5_8coin_production
```
Expected: per-coin lines for all 8 coins + portfolio block. Record portfolio SR, total return, max drawdown.

- [ ] **Step 2: Run the satellite-cost sensitivity sweep**

Run:
```bash
python scripts/baseline_v5_mix.py --start 2021-11-07 --end 2026-04-15 \
    --sat-haircut 1.0 --output-dir data/v5_8coin_sat1.0
python scripts/baseline_v5_mix.py --start 2021-11-07 --end 2026-04-15 \
    --sat-haircut 2.0 --output-dir data/v5_8coin_sat2.0
```
Expected: three results total (haircut 1.0 / 1.5 / 2.0). Portfolio SR should not collapse across the range — if SR is highly fragile to the haircut, flag it in Task 12's report.

- [ ] **Step 3: Commit the run outputs**

```bash
git add data/v5_8coin_production/ data/v5_8coin_sat1.0/ data/v5_8coin_sat2.0/
git commit -m "data: 8-coin V5 MIX backtest + satellite-cost sensitivity sweep"
```
(If `data/` is gitignored, skip the `git add` — check `git status`.)

### Task 12: Validation, acceptance gate, and report

**Files:**
- Create: `docs/superpowers/specs/2026-05-21-v5-8coin-results.md`

- [ ] **Step 1: Run CPCV / DSR / bootstrap validation**

Inspect `scripts/validate_v5_mix.py` and `scripts/validate_v5_robustness.py` (`--help`) — these are the existing V5 validators. Run them against `data/v5_8coin_production/daily_returns.csv` (or with the 8-coin routing, matching how they were invoked for the 4-coin V5). Capture: CPCV per-fold SR, Deflated Sharpe Ratio, bootstrap CI on portfolio SR.

- [ ] **Step 2: Build the comparison table**

Compare 8-coin vs 4-coin V5 baseline. Pull per-coin attribution (SR / return / DD contribution) from `data/v5_8coin_production/summary.json`. Tabulate: portfolio SR, total return, max drawdown, annualized vol — 8-coin vs 4-coin (SR 3.18).

- [ ] **Step 3: Evaluate the acceptance gate**

**Acceptance gate (from spec):** 8-coin portfolio walk-forward SR ≥ ~3.0 **AND** max drawdown below the 4-coin V5 max drawdown.

- If both hold → expansion accepted.
- If not → document which condition failed and the per-coin attribution showing why; the expansion is rejected (or sent back for diagnosis). A failed gate is a valid, reportable outcome — do not tune parameters to force a pass.

- [ ] **Step 4: Write the results document**

Create `docs/superpowers/specs/2026-05-21-v5-8coin-results.md` with: the comparison table, per-coin attribution, CPCV/DSR/bootstrap numbers, the cost-sensitivity sweep results from Task 11, the routing decisions from Task 7, and the gate verdict (accepted / rejected, with reasoning).

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-05-21-v5-8coin-results.md
git commit -m "docs: V5 8-coin expansion results + acceptance-gate verdict"
```

---

## Self-Review Notes

- **Spec coverage:** P1→Task 1-2; P2→Task 3; P3→Task 4-6; P4 routing→Task 7; cost tiers→Task 8; weights→Task 9; engine wiring→Task 10; final run + cost sensitivity→Task 11; CPCV/DSR/bootstrap + acceptance gate→Task 12. Regression guard: `test_portfolio_return_4coin_equals_mean` (Task 9) + the live 4-coin run check (Task 10 Step 5). All spec sections mapped.
- **Account-model nulls** (XRP/TRX/ADA): handled by Task 5 Step 4 verification + noted as expected; LGB tolerates null columns. **DefiLlama TVL** is pulled implicitly via the `--onchain-pit` feature build; no separate task needed since the spec marks those columns as expected-null for non-DeFi chains.
- **Data gitignore caveat:** several tasks note "if `data/` is gitignored, skip `git add`" — the engineer must `git status`-check, since prediction/derivative artifacts may or may not be tracked in this repo.
