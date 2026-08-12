# Honest Rebuild Phases 0–3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-derive every strategy selection (target, horizons, pool, features, sizing, universe) on the corrected causal+purged harness, audit the carry sleeve, and produce holdout-validated sleeves ready for live integration.

**Architecture:** Sleeve-portfolio rebuild per spec `docs/superpowers/specs/2026-07-08-honest-rebuild-design.md`. Phase 0 builds the methodology rails (trial ledger, holdout lock, intrabar stop replay); Phase 1 audits the model-free carry sleeve; Phase 2 derives the directional sleeve (factor floor first, then gated LGB axes); Phase 3 runs the one-shot holdout. Phases 4 (live) and 5 (LLM) are separate plans.

**Tech Stack:** Python 3.13 (uv), pandas/numpy/lightgbm, pytest, existing scripts (`evaluate_models_multi.py`, `baseline_v5_mix.py`, `baseline_strategy_v2.py`), carry module from branch `exp/carry-go-nogo`.

## Global Constraints

- Every backtest: `--convention causal` + `--purge` + `--train-window-days 730` (the live contract). Legacy convention only for forensic comparison, never selection.
- Dev window: predictions end **2025-03-31**. Holdout 2025-04-01→2026-07-01 untouched until Phase 3 (Task H2). Enforced by `assert_dev_window` (Task 2).
- Every full-window config evaluation appended to `data/rebuild/trial_ledger.jsonl` before its result is read.
- Gates are pre-registered in `data/rebuild/gates.json` (Task 2) and never edited after the corresponding experiment starts.
- Paired comparisons: stationary block bootstrap, block=21, n=2000 (existing pattern from `scripts/validate_sentiment_feature.py` on branch `feature/sentiment-index-quant`; re-implemented in Task F0 helper).
- Annualization: √252 on daily bars (house convention). All SRs net of costs.
- New empirical findings → THESIS_FINDINGS.md new sections (§39 carry audit, §40 directional derivation, §41 holdout).
- Working branch: `rebuild/honest-2026-07` off current `feature/trend-mult-v51-hybrid-routing` HEAD. Do not touch the user's uncommitted WIP files (`scripts/generate_hybrid_signals.py`, `scripts/parity_refetch_and_replay.py`, `tradingagents/agents/*`, `tradingagents/agents/utils/crypto_market_tools.py`).
- Long compute runs: `nohup ... &` with logs under `data/rebuild/logs/`; idempotent output dirs.

---

## Phase 0 — Methodology foundation

### Task 1: Rebuild branch + import carry module

**Files:**
- Branch: `rebuild/honest-2026-07`
- Import (from `exp/carry-go-nogo`): `tradingagents/strategies/carry_sleeve.py`, `scripts/carry_blend_p4.py`, `scripts/carry_data_audit.py`, `scripts/funding_correction_sweep.py`, `tests/strategies/test_carry_sleeve.py`, `docs/CARRY_SLEEVE_BACKTEST_SPEC.md`

**Interfaces:**
- Produces: `tradingagents.strategies.carry_sleeve` with `fetch_funding_raw(symbol, start, end) -> pd.DataFrame`, `aggregate_daily_funding_income(raw) -> pd.Series`, `funding_daily_income(symbol, start, end) -> pd.Series`, `carry_sleeve_return(...)`, `compute_price_pnl(spot_close, perp_close) -> pd.Series`, `blend_returns(core, sleeve, alloc) -> pd.Series`, `fetch_perp_mark(symbol, start, end) -> pd.Series` (signatures exactly as on `exp/carry-go-nogo`)

- [ ] **Step 1: Create branch**

```bash
cd /home/malecada/master_thesis/TradingAgents
git switch -c rebuild/honest-2026-07
```

- [ ] **Step 2: Bring carry files over from exp/carry-go-nogo (files only — do NOT merge the branch; it predates the audit remediation on this line)**

```bash
git checkout exp/carry-go-nogo -- \
  tradingagents/strategies/carry_sleeve.py \
  scripts/carry_blend_p4.py scripts/carry_data_audit.py \
  scripts/funding_correction_sweep.py \
  tests/strategies/test_carry_sleeve.py \
  docs/CARRY_SLEEVE_BACKTEST_SPEC.md
```

- [ ] **Step 3: Run the carry tests**

Run: `uv run pytest tests/strategies/test_carry_sleeve.py -v`
Expected: all pass. If any test imports something that moved since Jun-12, fix the import (mechanical) — do not change test assertions.

- [ ] **Step 4: Run the full suite to confirm no regression**

Run: `uv run pytest tests/ -x -q`
Expected: green except the 2 pre-existing `test_parity_script.py` failures from the user's uncommitted 8-coin `_PARITY_ROUTES` WIP (documented in §33.4 — not ours to fix).

- [ ] **Step 5: Commit**

```bash
git add tradingagents/strategies/carry_sleeve.py scripts/carry_blend_p4.py \
  scripts/carry_data_audit.py scripts/funding_correction_sweep.py \
  tests/strategies/test_carry_sleeve.py docs/CARRY_SLEEVE_BACKTEST_SPEC.md
git commit -m "feat(rebuild): import carry sleeve module from exp/carry-go-nogo"
```

### Task 2: Trial ledger + holdout guard + gate registry

**Files:**
- Create: `tradingagents/rebuild/__init__.py`, `tradingagents/rebuild/ledger.py`
- Create: `data/rebuild/gates.json`
- Test: `tests/rebuild/test_ledger.py` (create `tests/rebuild/__init__.py` empty)

**Interfaces:**
- Produces: `log_trial(experiment: str, config: dict, window: tuple[str, str], metrics: dict, ledger_path: Path = DEFAULT_LEDGER) -> dict` (returns the written row); `trial_count(ledger_path: Path = DEFAULT_LEDGER, experiment: str | None = None) -> int`; `assert_dev_window(end_date: str, allow_holdout: bool = False) -> None`; `HOLDOUT_START = "2025-04-01"`; `DEFAULT_LEDGER = PROJECT_ROOT / "data/rebuild/trial_ledger.jsonl"`
- Consumed by: every experiment task in Phases 1–3.

- [ ] **Step 1: Write the failing tests**

```python
# tests/rebuild/test_ledger.py
import json
from pathlib import Path

import pytest

from tradingagents.rebuild.ledger import (
    HOLDOUT_START, assert_dev_window, log_trial, trial_count,
)


def test_log_trial_appends_jsonl(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    row = log_trial(
        experiment="factor_floor",
        config={"kind": "tsmom", "lookback": 30},
        window=("2021-11-07", "2025-03-31"),
        metrics={"sharpe": 0.83, "max_drawdown": -0.06},
        ledger_path=ledger,
    )
    lines = ledger.read_text().strip().splitlines()
    assert len(lines) == 1
    loaded = json.loads(lines[0])
    assert loaded["experiment"] == "factor_floor"
    assert loaded["config"]["lookback"] == 30
    assert loaded["metrics"]["sharpe"] == 0.83
    assert loaded["window"] == ["2021-11-07", "2025-03-31"]
    assert "ts" in loaded and "git_commit" in loaded and "config_hash" in loaded
    assert row["config_hash"] == loaded["config_hash"]


def test_trial_count_total_and_per_experiment(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    for lb in (7, 14, 30):
        log_trial("factor_floor", {"kind": "tsmom", "lookback": lb},
                  ("2021-11-07", "2025-03-31"), {"sharpe": 0.1}, ledger_path=ledger)
    log_trial("axis_target", {"target_mode": "logret"},
              ("2021-11-07", "2025-03-31"), {"sharpe": 0.2}, ledger_path=ledger)
    assert trial_count(ledger_path=ledger) == 4
    assert trial_count(ledger_path=ledger, experiment="factor_floor") == 3


def test_log_trial_rejects_holdout_window(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    with pytest.raises(ValueError, match="holdout"):
        log_trial("factor_floor", {}, ("2021-11-07", "2026-06-01"),
                  {"sharpe": 9.9}, ledger_path=ledger)


def test_assert_dev_window():
    assert_dev_window("2025-03-31")  # ok
    with pytest.raises(ValueError, match="holdout"):
        assert_dev_window("2025-04-01")
    with pytest.raises(ValueError, match="holdout"):
        assert_dev_window(HOLDOUT_START)
    assert_dev_window("2026-07-01", allow_holdout=True)  # one-shot escape hatch
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `uv run pytest tests/rebuild/test_ledger.py -v`
Expected: FAIL — `ModuleNotFoundError: tradingagents.rebuild`

- [ ] **Step 3: Implement the module**

```python
# tradingagents/rebuild/__init__.py
```

```python
# tradingagents/rebuild/ledger.py
"""Trial ledger + holdout guard for the honest rebuild.

Every full-window config evaluation MUST be logged here before its result is
read. DSR trial counts are computed from this file, never quoted from memory
(audit 2026-07-07: 12 claimed vs >450 actual evaluations).

The holdout window (>= HOLDOUT_START) is locked until the Phase 3 one-shot;
log_trial and assert_dev_window enforce it mechanically.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_LEDGER = PROJECT_ROOT / "data" / "rebuild" / "trial_ledger.jsonl"
HOLDOUT_START = "2025-04-01"


def assert_dev_window(end_date: str, allow_holdout: bool = False) -> None:
    """Raise if end_date reaches into the locked holdout window."""
    if allow_holdout:
        return
    if str(end_date)[:10] >= HOLDOUT_START:
        raise ValueError(
            f"window end {end_date} reaches into the locked holdout "
            f"(>= {HOLDOUT_START}); pass allow_holdout=True only for the "
            f"Phase 3 one-shot"
        )


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def log_trial(
    experiment: str,
    config: dict,
    window: tuple[str, str],
    metrics: dict,
    ledger_path: Path = DEFAULT_LEDGER,
    allow_holdout: bool = False,
) -> dict:
    """Append one config evaluation to the ledger; returns the written row."""
    assert_dev_window(window[1], allow_holdout=allow_holdout)
    cfg_json = json.dumps(config, sort_keys=True, default=str)
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "experiment": experiment,
        "config": config,
        "config_hash": hashlib.sha256(cfg_json.encode()).hexdigest()[:12],
        "window": list(window),
        "metrics": metrics,
    }
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path, "a") as f:
        f.write(json.dumps(row, default=str) + "\n")
    return row


def trial_count(
    ledger_path: Path = DEFAULT_LEDGER, experiment: str | None = None
) -> int:
    """Number of logged trials (optionally for one experiment) — DSR input."""
    if not ledger_path.exists():
        return 0
    n = 0
    with open(ledger_path) as f:
        for line in f:
            if not line.strip():
                continue
            if experiment is None or json.loads(line)["experiment"] == experiment:
                n += 1
    return n
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `uv run pytest tests/rebuild/test_ledger.py -v`
Expected: 4 PASS

- [ ] **Step 5: Write the pre-registered gate registry**

```json
// data/rebuild/gates.json
{
  "registered": "2026-07-08",
  "spec": "docs/superpowers/specs/2026-07-08-honest-rebuild-design.md",
  "carry_go": {
    "stressed_sharpe_min": 1.5,
    "worst_90d_loss_max_at_allocation": 0.05,
    "note": "stressed = after execution-realism cost pass C2 haircuts"
  },
  "axis_experiments": {
    "adopt_rule": "delta_sharpe > 0 AND p_pos >= 0.85 (paired block bootstrap, block=21, n=2000) AND max_drawdown_worsening <= 0.01",
    "note": "applies to axes: target, horizons, pool, features, sizing components"
  },
  "ml_survival": {
    "vs": "best factor-floor config",
    "delta_sharpe_min": 0.0,
    "p_pos_min": 0.85,
    "dsr_min": 0.90,
    "dsr_trials": "trial_count() from ledger at evaluation time"
  },
  "holdout_deploy": {
    "portfolio_net_sharpe_min": 0.5,
    "max_drawdown_max": 0.15,
    "sleeve_contribution_min": 0.0,
    "placebo_p_max": 0.05,
    "one_shot": true
  }
}
```

- [ ] **Step 6: Commit**

```bash
git add tradingagents/rebuild/ tests/rebuild/ data/rebuild/gates.json
git commit -m "feat(rebuild): trial ledger, holdout guard, pre-registered gates"
```

### Task 3: Intrabar price-stop replay in the backtest engine

**Files:**
- Modify: `scripts/baseline_strategy_v2.py` (`run_coin_backtest`, lines 80–193)
- Modify: `scripts/baseline_v5_mix.py` (`run_coin`, pass High/Low through)
- Test: `tests/strategies/test_intrabar_stop.py`

**Interfaces:**
- Produces: `run_coin_backtest(..., highs: np.ndarray | None = None, lows: np.ndarray | None = None, price_stop_pct: float = 0.0)` — new keyword-only-style optional params appended after `take_profit`. When `price_stop_pct > 0` and highs/lows given: simulate the live price-axis STOP_MARKET; per-trade equity-axis stop is disabled by the caller (pass `stop_loss=1.0`) to avoid double-counting. Defaults reproduce old behavior byte-identically.
- Produces: `baseline_v5_mix.run_coin(..., price_stop_pct: float = 0.0)` — when > 0, loads High/Low from `_load_crypto_ohlcv` and forwards; sets `stop_loss=1.0` in the engine costs.
- Consumed by: every Phase 2/3 strategy run (all use `price_stop_pct=0.03`).

**Semantics (mirrors live `runner.py` STOP_MARKET behavior):**
- Entry price = `prices[i-1]` on the bar where the position opens (prev_pos was 0, or sign flipped) — live enters at 00:05 UTC at ≈ close(D−1).
- Long stop level = `entry * (1 - price_stop_pct)`; short = `entry * (1 + price_stop_pct)`.
- Trigger on bar i if `lows[i] <= stop_level` (long) / `highs[i] >= stop_level` (short). Fill at the stop level (gap-through approximated at the stop level; documented limitation).
- Stopped bar return: `pos * (stop_level - p_prev) / p_prev` minus normal costs plus exit trade cost on `abs(pos)` notional; position 0 after the bar. Next bar the positions array re-enters as it wishes — this models the stop-out → next-cycle re-entry whipsaw the audit flagged as unsimulated.
- Resizing without sign change keeps the original entry/stop.

- [ ] **Step 1: Write the failing tests**

```python
# tests/strategies/test_intrabar_stop.py
import numpy as np
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.baseline_strategy_v2 import run_coin_backtest

COSTS = dict(fee_rate=0.0, slippage=0.0, spread=0.0, price_impact=0.0,
             funding_rate=0.0, stop_loss=1.0, max_portfolio_dd=1.0)


def _dates(n):
    return np.arange(n)


def test_no_stop_params_is_byte_identical():
    """highs/lows omitted -> exact old behavior (golden guard)."""
    prices = np.array([100.0, 101.0, 99.0, 102.0, 103.0])
    positions = np.array([0.0, 1.0, 1.0, 1.0, 0.0])
    eq_old, m_old = run_coin_backtest(_dates(5), prices, positions.copy(),
                                      10_000.0, **COSTS)
    eq_new, m_new = run_coin_backtest(_dates(5), prices, positions.copy(),
                                      10_000.0, **COSTS,
                                      highs=None, lows=None, price_stop_pct=0.0)
    assert eq_old == eq_new
    assert m_old == m_new


def test_long_stop_triggers_on_low():
    """Long from bar1 (entry=prices[0]=100, stop 3% -> 97). Bar2 low=96
    triggers: bar2 return = (97-101)/101, position flat after."""
    prices = np.array([100.0, 101.0, 100.0, 105.0])
    highs  = np.array([100.0, 102.0, 101.0, 106.0])
    lows   = np.array([100.0, 100.0,  96.0, 104.0])
    positions = np.array([0.0, 1.0, 1.0, 1.0])
    eq, m = run_coin_backtest(_dates(4), prices, positions, 10_000.0, **COSTS,
                              highs=highs, lows=lows, price_stop_pct=0.03)
    # bar1: (101-100)/100 = +1%
    assert eq[1] == pytest.approx(10_000.0 * 1.01)
    # bar2: stopped at 97 -> (97-101)/101
    assert eq[2] == pytest.approx(eq[1] * (1 + (97.0 - 101.0) / 101.0))
    # bar3: positions array says 1.0 again -> re-entry at prices[2]=100,
    # low 104 doesn't touch new stop 97 -> full close-to-close return
    assert eq[3] == pytest.approx(eq[2] * (1 + (105.0 - 100.0) / 100.0))


def test_short_stop_triggers_on_high():
    prices = np.array([100.0, 99.0, 101.0, 95.0])
    highs  = np.array([100.0, 100.0, 103.5, 96.0])
    lows   = np.array([100.0,  98.0, 100.0, 94.0])
    positions = np.array([0.0, -1.0, -1.0, -1.0])
    eq, _ = run_coin_backtest(_dates(4), prices, positions, 10_000.0, **COSTS,
                              highs=highs, lows=lows, price_stop_pct=0.03)
    # entry 100, short stop 103; bar2 high 103.5 triggers; fill at 103:
    # ret = -1 * (103-99)/99
    assert eq[2] == pytest.approx(eq[1] * (1 - (103.0 - 99.0) / 99.0))


def test_no_trigger_when_low_stays_above_stop():
    prices = np.array([100.0, 101.0, 102.0])
    highs  = np.array([100.0, 102.0, 103.0])
    lows   = np.array([100.0, 99.0, 100.5])
    positions = np.array([0.0, 1.0, 1.0])
    eq_stop, _ = run_coin_backtest(_dates(3), prices, positions, 10_000.0,
                                   **COSTS, highs=highs, lows=lows,
                                   price_stop_pct=0.03)
    eq_plain, _ = run_coin_backtest(_dates(3), prices, positions, 10_000.0,
                                    **COSTS)
    assert eq_stop == eq_plain


def test_exit_cost_charged_on_stop():
    prices = np.array([100.0, 101.0, 100.0])
    highs  = np.array([100.0, 102.0, 101.0])
    lows   = np.array([100.0, 100.0, 96.0])
    positions = np.array([0.0, 1.0, 1.0])
    costs = dict(COSTS, fee_rate=0.001)
    eq, _ = run_coin_backtest(_dates(3), prices, positions, 10_000.0, **costs,
                              highs=highs, lows=lows, price_stop_pct=0.03)
    # bar2: gross (97-101)/101; costs = normal holding-bar cost (no resize:
    # trade_notional 0) + exit cost (2*fee)*|pos|=0.002
    expected = eq[1] * (1 + (97.0 - 101.0) / 101.0 - 0.002)
    assert eq[2] == pytest.approx(expected)
```

- [ ] **Step 2: Run tests, verify failure**

Run: `uv run pytest tests/strategies/test_intrabar_stop.py -v`
Expected: FAIL — `TypeError: run_coin_backtest() got an unexpected keyword argument 'highs'`

- [ ] **Step 3: Implement in `run_coin_backtest`**

Signature change (`scripts/baseline_strategy_v2.py:80`):

```python
def run_coin_backtest(
    dates: np.ndarray,
    prices: np.ndarray,
    positions: np.ndarray,
    initial_capital: float,
    fee_rate: float,
    slippage: float,
    spread: float,
    price_impact: float,
    funding_rate: float,
    stop_loss: float,
    max_portfolio_dd: float,
    take_profit: float = 0.0,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    price_stop_pct: float = 0.0,
) -> tuple[list, dict]:
```

State added before the loop:

```python
    use_price_stop = price_stop_pct > 0 and highs is not None and lows is not None
    entry_price = 0.0  # price-axis entry for the live-style STOP_MARKET
```

Inside the loop, after `target_pos = positions[i]` and the existing `entry_equity` bookkeeping, add entry-price tracking and the intrabar check. The stop check replaces the bar's close-to-close crediting when it fires:

```python
        if use_price_stop and target_pos != 0:
            opened = (prev_pos == 0) or (np.sign(target_pos) != np.sign(prev_pos))
            if opened:
                entry_price = p_prev
            stop_level = (entry_price * (1 - price_stop_pct) if target_pos > 0
                          else entry_price * (1 + price_stop_pct))
            hit = (lows[i] <= stop_level) if target_pos > 0 else (highs[i] >= stop_level)
            if hit and entry_price > 0:
                gross_ret = target_pos * (stop_level - p_prev) / p_prev
                trade_notional = abs(target_pos - prev_pos)
                exit_notional = abs(target_pos)
                fee_cost = (2 * fee_rate + slippage + 2 * spread) * (trade_notional + exit_notional)
                impact_cost = price_impact * trade_notional * trade_notional
                holding_cost = funding_rate * abs(target_pos)
                net_ret = gross_ret - fee_cost - impact_cost - holding_cost
                new_equity = equity[-1] * (1 + net_ret)
                daily_returns.append(net_ret)
                equity.append(new_equity)
                prev_pos = 0.0
                entry_price = 0.0
                peak_equity = max(peak_equity, new_equity)
                dd_from_peak = (peak_equity - new_equity) / peak_equity if peak_equity > 0 else 0
                if dd_from_peak >= max_portfolio_dd:
                    halted = True
                continue
```

Place this block after the `trade_notional`/`entry_equity` bookkeeping and before the existing `price_return = ...` line, so a non-triggering bar falls through to the unchanged legacy path. Note the fee model matches the engine's existing per-side convention (`2*fee_rate + slippage + 2*spread` per unit notional) and charges both the resize notional and the stop-exit notional.

- [ ] **Step 4: Run new tests + golden guard**

Run: `uv run pytest tests/strategies/test_intrabar_stop.py tests/strategies/test_causal_convention.py -v`
Expected: all PASS (causal-convention goldens prove default path untouched).

- [ ] **Step 5: Wire through `baseline_v5_mix.run_coin`**

In `scripts/baseline_v5_mix.py` add `price_stop_pct: float = 0.0` to `run_coin`'s signature (after `convention`), and replace the merge + engine call:

```python
    cols = ["Date", "Close"] + (["High", "Low"] if price_stop_pct > 0 else [])
    merged = preds.merge(ohlcv[cols], left_on="date", right_on="Date")
    merged = merged.dropna(subset=["Close"]).reset_index(drop=True)
```

```python
    costs = dict(COSTS if costs_override is None else costs_override)
    stop_kwargs = {}
    if price_stop_pct > 0:
        costs["stop_loss"] = 1.0  # price-axis stop replaces the equity-axis proxy
        stop_kwargs = dict(highs=merged["High"].values, lows=merged["Low"].values,
                           price_stop_pct=price_stop_pct)
    equity, _m = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=pos, initial_capital=10_000.0, **costs, **stop_kwargs,
    )
```

Add CLI flag in `main()`: `p.add_argument("--price-stop-pct", type=float, default=0.0, help="Intrabar live-style price stop (0=off; live uses 0.03). Replaces the equity-axis per-trade stop when set.")` and forward `price_stop_pct=args.price_stop_pct` in the `run_coin` call.

- [ ] **Step 6: Integration check — 4-coin causal run with and without price stop**

```bash
uv run python scripts/baseline_v5_mix.py --start 2021-11-07 --end 2025-03-31 \
  --routing-json data/rebuild/routing_4coin_dev.json --output-dir data/rebuild/smoke_nostop
uv run python scripts/baseline_v5_mix.py --start 2021-11-07 --end 2025-03-31 \
  --routing-json data/rebuild/routing_4coin_dev.json --price-stop-pct 0.03 \
  --output-dir data/rebuild/smoke_stop
```

(`routing_4coin_dev.json` = the 4 core-coin entries of `DEFAULT_ROUTING`, written by hand in this step; existing frozen pred dirs are fine for a smoke test.) Expected: both complete; stop run reports hundreds-to-thousands of stop events fewer bars held (sanity: audit replay estimated ≈1,723 intrabar touches over 2,671 entries on 8 coins / 4.5 yrs); SRs differ.

- [ ] **Step 7: Commit**

```bash
git add scripts/baseline_strategy_v2.py scripts/baseline_v5_mix.py \
  tests/strategies/test_intrabar_stop.py data/rebuild/routing_4coin_dev.json
git commit -m "feat(engine): intrabar price-axis stop replay (live STOP_MARKET parity)"
```

### Task 4: Dev-window prediction regeneration (compute, background)

**Files:**
- Create (outputs): `data/rebuild/preds/btc_eth_78f/`, `data/rebuild/preds/btc_eth_193f/`
- Create: `data/rebuild/logs/`

**Interfaces:**
- Produces: purged rolling-730d prediction dirs ending 2025-03-31 with `preds_lgb_h{1,3,7,14}.csv` — consumed by every Phase 2 task.
- Consumes: `evaluate_models_multi.py --purge --train-window-days 730 --trade-date --days` (existing CLI).

- [ ] **Step 1: Launch the two dev regenerations (background, ~hours each)**

```bash
mkdir -p data/rebuild/logs
nohup uv run python scripts/evaluate_models_multi.py \
  --coins bitcoin ethereum --horizons 1 3 7 14 --models lgb \
  --days 1606 --min-train 365 --trade-date 2025-03-31 \
  --purge --train-window-days 730 \
  --output-dir data/rebuild/preds/btc_eth_78f \
  > data/rebuild/logs/regen_78f.log 2>&1 &
nohup uv run python scripts/evaluate_models_multi.py \
  --coins bitcoin ethereum --horizons 1 3 7 14 --models lgb \
  --days 1606 --min-train 365 --trade-date 2025-03-31 \
  --purge --train-window-days 730 --onchain-pit \
  --output-dir data/rebuild/preds/btc_eth_193f \
  > data/rebuild/logs/regen_193f.log 2>&1 &
```

(`--days 1606` = 2020-11-01→2025-03-31 of data; with `--min-train 365` predictions start ≈ 2021-11-01, matching the dev window start.)

- [ ] **Step 2: While they run, proceed to Phase 1 (carry audit is independent of LGB predictions).**

- [ ] **Step 3: On completion, verify holdout absence + purged sanity**

```bash
tail -3 data/rebuild/logs/regen_78f.log data/rebuild/logs/regen_193f.log
uv run python - <<'EOF'
import pandas as pd
for d in ("btc_eth_78f", "btc_eth_193f"):
    for h in (7, 14):
        df = pd.read_csv(f"data/rebuild/preds/{d}/preds_lgb_h{h}.csv", parse_dates=["date"])
        assert df["date"].max() <= pd.Timestamp("2025-03-31"), (d, h, df["date"].max())
        ok = (df["prediction"] > df["ref_price"]) == (df["actual"] > df["ref_price"])
        print(d, f"h{h}", f"DirAcc={ok.mean():.3f}", f"rows={len(df)}", f"max={df['date'].max():%Y-%m-%d}")
EOF
```

Expected: max date ≤ 2025-03-31 everywhere; DirAcc ≈ 0.50–0.56 (the honest range — a value >0.65 means purging silently failed: STOP and investigate before any Phase 2 work).

- [ ] **Step 4: Commit the log tails + a README stamp (CSVs are gitignored data)**

```bash
git add -f data/rebuild/preds/btc_eth_78f/summary.json data/rebuild/preds/btc_eth_193f/summary.json 2>/dev/null || true
git commit -m "chore(rebuild): dev-window purged prediction regeneration stamps" --allow-empty
```

---

## Phase 1 — Carry sleeve audit (independent of Phase 0 Task 4; needs Tasks 1–2)

All carry tasks write artifacts to `data/rebuild/carry_audit/` and log to the ledger with `experiment="carry_audit"`. Every SR quoted uses √252. Window: dev only (`--start 2021-11-08 --end 2025-03-31`).

### Task C1: Reproduce §32 on the dev window + timing-convention pass

**Files:**
- Create: `scripts/carry_audit_timing.py`
- Output: `data/rebuild/carry_audit/timing.json`

**Interfaces:**
- Consumes: `funding_daily_income`, `fetch_perp_mark`, `compute_price_pnl`, `carry_sleeve_return` from `tradingagents.strategies.carry_sleeve`; `fetch_spot_close` from `scripts/carry_blend_p4.py`.
- Produces: `timing.json` with `{reproduction: {...}, lag_variant: {...}, verdict: str}`.

- [ ] **Step 1: Reproduce the sleeve on the dev window**

Run `carry_blend_p4.py` with dev dates, no V5 blend (sleeve-only mode — if the script requires `--v5-csv`, point it at any existing daily_returns.csv and read only the sleeve metrics from its output):

```bash
uv run python scripts/carry_blend_p4.py --start 2021-11-08 --end 2025-03-31 \
  --v5-csv data/v5_mix_production/daily_returns.csv | tee data/rebuild/carry_audit/repro.txt
```

Expected: sleeve SR in the 7–9 range on the dev window (published 4.5-yr value 8.24; dev subset will differ some). Record exact numbers.

- [ ] **Step 2: Write the timing audit script**

`scripts/carry_audit_timing.py` — core check: the daily sleeve return at date D must combine (a) funding income whose 8h events all have `fundingTime` within day D **and** a position established at or before D−1's close, and (b) price P&L close(D−1)→close(D). Implement a one-day-lag variant (funding income shifted +1 day against the price legs) and compare:

```python
#!/usr/bin/env python
"""Carry audit pass 1: timing convention.

Verifies the sleeve cannot see same-day information it wouldn't have live,
by comparing the as-built daily series vs a funding-lagged (+1d) variant.
For an always-on hedged sleeve the two should differ only marginally
(reordering, not information) — a large SR drop indicates a same-bar credit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.carry_blend_p4 import fetch_spot_close  # noqa: E402
from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.strategies.carry_sleeve import (  # noqa: E402
    compute_price_pnl, fetch_perp_mark, funding_daily_income,
)

ANN = np.sqrt(252)
START, END = "2021-11-08", "2025-03-31"


def sr(x):
    x = x.dropna()
    return float(x.mean() / x.std() * ANN) if x.std() > 0 else 0.0


def main():
    from datetime import date
    start, end = date(2021, 11, 8), date(2025, 3, 31)
    out = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        funding = funding_daily_income(sym, start, end)
        spot = fetch_spot_close(sym, start, end)
        perp = fetch_perp_mark(sym, start, end)
        hedge = compute_price_pnl(spot, perp)
        asbuilt = (funding + hedge.reindex(funding.index)).dropna()
        lagged = (funding.shift(1) + hedge.reindex(funding.index)).dropna()
        out[sym] = {"sr_asbuilt": sr(asbuilt), "sr_funding_lag1": sr(lagged),
                    "delta": sr(asbuilt) - sr(lagged)}
        print(sym, out[sym])
    verdict = "PASS" if all(abs(v["delta"]) < 0.5 for v in out.values()) else "INVESTIGATE"
    out["verdict"] = verdict
    outp = PROJECT_ROOT / "data/rebuild/carry_audit/timing.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=2))
    log_trial("carry_audit", {"pass": "timing", "variant": "funding_lag1"},
              (START, END), {k: v for k, v in out.items() if k != "verdict"})
    print("verdict:", verdict)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run it**

Run: `uv run python scripts/carry_audit_timing.py`
Expected: prints per-symbol SR as-built vs lagged; verdict PASS (funding accrual is mechanical income — a big delta means the series construction credits funding the position couldn't have earned; investigate `aggregate_daily_funding_income` before proceeding).

- [ ] **Step 4: Commit**

```bash
git add scripts/carry_audit_timing.py data/rebuild/carry_audit/timing.json
git commit -m "audit(carry): pass 1 timing convention"
```

### Task C2: Execution-realism cost pass (the stressed sleeve)

**Files:**
- Create: `scripts/carry_audit_costs.py`
- Output: `data/rebuild/carry_audit/costs.json`, `data/rebuild/carry_audit/sleeve_stressed_daily.csv`

**Interfaces:**
- Produces: `sleeve_stressed_daily.csv` — the **canonical stressed sleeve return series** (columns: date, btc, eth, sleeve) consumed by C4 and Phase 3.
- Cost model applied on top of the as-built series (all parameters explicit in the JSON output):
  - Entry/exit turnover: spot taker fee 0.10% + perp taker fee 0.04% + spread 0.01% per side, charged on both legs at inception, at rebalances, and at final exit.
  - Rebalance-on-drift: hedge ratio recomputed daily; when |drift| > 20% of target notional, charge the round-trip cost on the drift notional (mirrors the E4 live scope rule).
  - Margin capital cost: sleeve holds ≤3x leverage; charge rf (4.5%/yr, daily) on the margin fraction (1/3 of notional) as opportunity cost.
  - Basis at entry/exit: mark the spot-perp basis on inception and exit days into P&L (already in `compute_price_pnl` if it uses both series' actual prices — verify; if the hedge P&L assumes basis=0 at the boundaries, add the actual boundary basis).

- [ ] **Step 1: Write `scripts/carry_audit_costs.py`** — same fetch skeleton as C1; build as-built daily series per symbol, then apply the four cost layers above as explicit daily deductions; write the stressed series CSV + a JSON with SR before/after each cost layer (waterfall: as_built → +turnover → +rebalance → +margin_cost → +boundary_basis = stressed). Log to ledger (`{"pass": "costs"}` config, stressed metrics).

- [ ] **Step 2: Run it**

Run: `uv run python scripts/carry_audit_costs.py`
Expected: waterfall printed; stressed SR recorded. The published 8.24 is an upper bound — the interesting question is how much survives. Any layer that removes >2 SR alone deserves a comment in the JSON.

- [ ] **Step 3: Commit**

```bash
git add scripts/carry_audit_costs.py data/rebuild/carry_audit/costs.json \
  data/rebuild/carry_audit/sleeve_stressed_daily.csv
git commit -m "audit(carry): pass 2 execution-realism cost waterfall"
```

### Task C3: Funding-realism reconciliation

**Files:**
- Create: `scripts/carry_audit_funding_recon.py`
- Output: `data/rebuild/carry_audit/funding_recon.json`

- [ ] **Step 1: Write the reconciliation script** — for 3 sampled quarters (2022-Q2 bear, 2023-Q4 chop, 2024-Q1 bull): re-fetch raw 8h funding events via `fetch_funding_raw`, recompute quarterly funding income independently (sum of rate × notional per event, short side receives positive rates), and diff against `funding_daily_income`'s aggregate for the same quarter. Also count events/day (expect 3) and report the share of negative-funding days per quarter.

- [ ] **Step 2: Run it**

Run: `uv run python scripts/carry_audit_funding_recon.py`
Expected: per-quarter relative diff < 1% (pure aggregation identity). Larger diff → bug in `aggregate_daily_funding_income`; fix before continuing.

- [ ] **Step 3: Commit**

```bash
git add scripts/carry_audit_funding_recon.py data/rebuild/carry_audit/funding_recon.json
git commit -m "audit(carry): pass 3 funding reconciliation vs raw 8h events"
```

### Task C4: Regime & persistence stress

**Files:**
- Create: `scripts/carry_audit_regime.py`
- Output: `data/rebuild/carry_audit/regime.json`, `data/rebuild/carry_audit/haircut_curve.csv`

- [ ] **Step 1: Write the regime script** — on the **stressed** series from C2: (a) rolling 30d funding-sign share per leg; (b) worst-90d compounded return; (c) per-year SR table; (d) haircut curve: blend-relevant SR at funding haircuts {100%, 75%, 50%, 25% of realized funding income}; (e) longest drawdown duration. Log to ledger.

- [ ] **Step 2: Run + eyeball the three known stress episodes** (2022-05 LUNA, 2022-11 FTX, any sustained negative-funding stretch): print worst-90d window dates and its return.

Run: `uv run python scripts/carry_audit_regime.py`
Expected: JSON + curve written. Note explicitly whether any 90d window loses more than the gate's 5%-at-allocation bound.

- [ ] **Step 3: Commit**

```bash
git add scripts/carry_audit_regime.py data/rebuild/carry_audit/regime.json \
  data/rebuild/carry_audit/haircut_curve.csv
git commit -m "audit(carry): pass 4 regime/persistence stress"
```

### Task C5: Capacity/margin note + GO/NO-GO + findings

**Files:**
- Modify: `THESIS_FINDINGS.md` (append §39)
- Output: `data/rebuild/carry_audit/verdict.json`

- [ ] **Step 1: Write the capacity/margin note** (analysis, no code): sub-account isolation vs reserve-margin; interaction with directional-sleeve margin; leverage ≤3 confirmation from the stressed series' realized notional; order-tag namespace requirement. One page inside §39.

- [ ] **Step 2: Evaluate the pre-registered gate** (`data/rebuild/gates.json` → `carry_go`): stressed SR ≥ 1.5 AND worst-90d loss at intended allocation ≤ 5%. Write `verdict.json` with the gate inputs and GO/NO-GO. **The gate values must come from C2/C4 outputs — no re-running with different parameters to pass** (that's the ledger's job to expose).

- [ ] **Step 3: Append §39 to THESIS_FINDINGS.md** — structure: passes 1–5 findings, cost waterfall table, haircut curve, gate evaluation, verdict. Follow the §33 factual style.

- [ ] **Step 4: Commit**

```bash
git add THESIS_FINDINGS.md data/rebuild/carry_audit/verdict.json
git commit -m "audit(carry): §39 five-pass audit verdict (GO/NO-GO at pre-registered gate)"
```

---

## Phase 2 — Directional sleeve derivation (needs Task 4 outputs)

All experiments: dev window, causal convention, `--price-stop-pct 0.03`, ledger-logged. Comparison helper first.

### Task F0: Paired-bootstrap comparison helper

**Files:**
- Create: `tradingagents/rebuild/compare.py`
- Test: `tests/rebuild/test_compare.py`

**Interfaces:**
- Produces: `paired_bootstrap(a: pd.Series, b: pd.Series, block: int = 21, n: int = 2000, seed: int = 7) -> dict` returning `{"sr_a", "sr_b", "delta_sr", "p_pos", "ci_low", "ci_high"}` where `p_pos = P(SR(b) - SR(a) > 0)` under stationary block bootstrap with a **shared index path** for both arms (the §33-sentiment harness convention); √252 annualization.
- Consumed by: F2–F6, H2.

- [ ] **Step 1: Write the failing tests**

```python
# tests/rebuild/test_compare.py
import numpy as np
import pandas as pd

from tradingagents.rebuild.compare import paired_bootstrap


def _series(mu, n=500, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    return pd.Series(rng.normal(mu, 0.01, n), index=idx)


def test_identical_series_p_pos_half():
    a = _series(0.0005)
    r = paired_bootstrap(a, a.copy())
    assert r["delta_sr"] == 0.0
    assert 0.4 <= r["p_pos"] <= 0.6


def test_clearly_better_arm_wins():
    a = _series(0.0, seed=1)
    b = a + 0.002  # same noise, higher mean -> paired design must detect
    r = paired_bootstrap(a, b)
    assert r["delta_sr"] > 0
    assert r["p_pos"] > 0.99


def test_deterministic_given_seed():
    a, b = _series(0.0, seed=1), _series(0.001, seed=2)
    assert paired_bootstrap(a, b) == paired_bootstrap(a, b)
```

- [ ] **Step 2: Run, verify fail** — `uv run pytest tests/rebuild/test_compare.py -v` → `ModuleNotFoundError`

- [ ] **Step 3: Implement**

```python
# tradingagents/rebuild/compare.py
"""Paired stationary-block-bootstrap SR comparison (shared index path)."""
from __future__ import annotations

import numpy as np
import pandas as pd

ANN = np.sqrt(252)


def _sr(x: np.ndarray) -> float:
    sd = x.std(ddof=1)
    return float(x.mean() / sd * ANN) if sd > 0 else 0.0


def paired_bootstrap(
    a: pd.Series, b: pd.Series, block: int = 21, n: int = 2000, seed: int = 7,
) -> dict:
    ab = pd.concat({"a": a, "b": b}, axis=1).dropna()
    xa, xb = ab["a"].values, ab["b"].values
    T = len(xa)
    rng = np.random.default_rng(seed)
    deltas = np.empty(n)
    for k in range(n):
        idx = []
        while len(idx) < T:
            start = rng.integers(0, T)
            length = rng.geometric(1.0 / block)
            idx.extend(((start + np.arange(length)) % T).tolist())
        idx = np.array(idx[:T])
        deltas[k] = _sr(xb[idx]) - _sr(xa[idx])
    return {
        "sr_a": _sr(xa), "sr_b": _sr(xb), "delta_sr": _sr(xb) - _sr(xa),
        "p_pos": float((deltas > 0).mean()),
        "ci_low": float(np.percentile(deltas, 2.5)),
        "ci_high": float(np.percentile(deltas, 97.5)),
    }
```

- [ ] **Step 4: Run tests** — `uv run pytest tests/rebuild/test_compare.py -v` → 3 PASS

- [ ] **Step 5: Commit** — `git add tradingagents/rebuild/compare.py tests/rebuild/test_compare.py && git commit -m "feat(rebuild): paired block-bootstrap comparison helper"`

### Task F1: Model-free factor floor

**Files:**
- Create: `scripts/factor_baselines.py`
- Output: `data/rebuild/factor_floor/{config}/daily_returns.csv`, `data/rebuild/factor_floor/floor_table.md`

**Interfaces:**
- Consumes: `_load_crypto_ohlcv`, v2_sizing (`compute_realized_vol`, `vol_regime_mask`, `build_positions_with_hold`), `run_coin_backtest` with `price_stop_pct=0.03`, `log_trial`.
- Produces: best-factor daily return series at `data/rebuild/factor_floor/BEST/daily_returns.csv` (BTC+ETH equal weight) — **the floor** for F6/H2.

**Factor set (the full pre-registered list — 18 configs, no additions without a new gates.json entry):**
- TSMOM: `sign(close[t-1] / close[t-1-k] - 1)`, k ∈ {7, 14, 30, 90} → 4 configs
- MA cross: fast/slow ∈ {(10,50), (20,100), (50,200)} → 3 configs
- Donchian breakout: entry on n-day high/low break, exit mid-channel, n ∈ {20, 55} → 2 configs
- XS momentum: long the stronger of BTC/ETH by 30d return, short the weaker (dollar-neutral) → 1 config
- Each of the 10 signal configs × {long-only, long-short} where applicable, capped at 18 total.

All configs share the identical causal sizing path: signal computed on close(D−1) and earlier only → confidence 1.0 → `build_positions_with_hold` with `target_vol=0.10, kelly_fraction=0.5, max_leverage=3.0, min_hold=7, early_exit_loss=0.015` on lagged prices (the Task 3 causal pattern: `px_sizing[1:] = px[:-1]`) → `run_coin_backtest` with core-coin causal costs (`costs_for_coin("bitcoin", convention="causal")`) and `price_stop_pct=0.03`.

- [ ] **Step 1: Write `scripts/factor_baselines.py`** — signal builders as small pure functions (`tsmom_signal(closes, k)`, `ma_cross_signal(closes, fast, slow)`, `donchian_signal(highs, lows, closes, n)`, `xs_mom_signals(btc_closes, eth_closes, k=30)`), each returning an int8 array in {−1, 0, +1} built strictly from index ≤ t−1; a `run_factor(coin, signal, name)` wrapper reusing the sizing path above; main loop over the 18 configs × {bitcoin, ethereum}, equal-weight portfolio per config, `log_trial("factor_floor", ...)` per config, floor table sorted by portfolio SR written to `floor_table.md`, best config's series copied to `BEST/daily_returns.csv`.

- [ ] **Step 2: Unit-test the signal builders (causality)**

```python
# tests/rebuild/test_factor_signals.py
import numpy as np

from scripts.factor_baselines import tsmom_signal, ma_cross_signal


def test_tsmom_uses_only_past():
    closes = np.array([100.0] * 40)
    closes[-1] = 200.0  # today's spike must not affect today's signal
    sig = tsmom_signal(closes, k=7)
    assert sig[-1] == tsmom_signal(np.array([100.0] * 40), k=7)[-1]


def test_ma_cross_shapes_and_warmup():
    closes = np.linspace(100, 200, 300)
    sig = ma_cross_signal(closes, fast=10, slow=50)
    assert sig.shape == closes.shape
    assert (sig[:50] == 0).all()      # warm-up neutral
    assert (sig[60:] == 1).all()      # steady uptrend -> long
```

Run: `uv run pytest tests/rebuild/test_factor_signals.py -v` → FAIL first (script missing), then implement, then PASS.

- [ ] **Step 3: Run the sweep**

Run: `uv run python scripts/factor_baselines.py --start 2021-11-07 --end 2025-03-31`
Expected: 18 ledger rows; `floor_table.md` written; best config named. Sanity: TSMOM-family SR on the dev window expected roughly +0.3…+1.0 (crypto literature) — a factor SR > 2.5 would itself be suspicious; re-check causality before accepting.

- [ ] **Step 4: Commit**

```bash
git add scripts/factor_baselines.py tests/rebuild/test_factor_signals.py \
  data/rebuild/factor_floor/floor_table.md
git commit -m "feat(rebuild): model-free factor floor (18 pre-registered configs)"
```

### Task F2: Axis 1 — target mode (level vs logret), purged re-run of E1

**Files:**
- Create (outputs): `data/rebuild/preds/btc_eth_78f_logret/`
- Output: `data/rebuild/axis_target/result.json`

**Interfaces:**
- Consumes: `--target-mode logret` flag on `evaluate_models_multi.py` — **lives on branch `exp/e1-logret-target`** (commits 5caf7ac, d117e26). First step cherry-picks it.

- [ ] **Step 1: Cherry-pick the E1 plumbing (plumbing only — its THESIS §34 verdict is void, see decision review)**

```bash
git cherry-pick 5caf7ac d117e26
uv run pytest tests/models/ -q   # E1 shipped 10 tests; default byte-identical
```

If the cherry-pick conflicts with the audit-remediation changes in `lgb_model.py`/`model_utils.py`, resolve keeping BOTH the purge/rolling params and the target_mode param (they touch different function args).

- [ ] **Step 2: Regenerate the 78f route with logret target (background)**

```bash
nohup uv run python scripts/evaluate_models_multi.py \
  --coins bitcoin ethereum --horizons 7 14 --models lgb \
  --days 1606 --min-train 365 --trade-date 2025-03-31 \
  --purge --train-window-days 730 --target-mode logret \
  --output-dir data/rebuild/preds/btc_eth_78f_logret \
  > data/rebuild/logs/regen_78f_logret.log 2>&1 &
```

- [ ] **Step 3: A/B through V5 sizing (both arms identical except pred dir)** — small driver script or direct calls: `run_coin` per coin per arm (`data/rebuild/preds/btc_eth_78f` vs `..._logret`, window 2021-11-07→2025-03-31, `price_stop_pct=0.03`, causal costs), equal-weight the two coins, `paired_bootstrap(level_port, logret_port)`, write `result.json`, `log_trial("axis_target", ...)` for both arms.

- [ ] **Step 4: Evaluate the gate** (`axis_experiments` in gates.json): adopt logret iff ΔSR > 0 AND p_pos ≥ 0.85 AND maxDD worsens ≤ 1pp. Record the decision in `result.json` as `{"adopt": true/false}`. **Whichever wins becomes the incumbent for F3–F6.**

- [ ] **Step 5: Commit** — `git add data/rebuild/axis_target/result.json && git commit -m "exp(rebuild): axis 1 target mode — purged E1 re-run"`

### Task F3: Axis 2 — horizon set

**Files:**
- Output: `data/rebuild/axis_horizons/result.json`

Arms (7 configs, all on the incumbent pred dir which has h ∈ {1,3,7,14} columns): single-horizon h3, h7, h14; consensus pairs {3,7}, {7,14}, {3,14}; triple {3,7,14}. Signal generation via `generate_term_structure_signals(merged, horizons, V5_CONFIDENCE_REF, asymmetric=True)` — single-horizon arms pass a one-element list.

- [ ] **Step 1: Driver** — loop the 7 configs through `run_coin`-equivalent calls (needs a small variant of `_load_preds` that merges the needed horizon columns; write it in the driver, don't fork `baseline_v5_mix.py`), equal-weight BTC+ETH portfolio per config, ledger-log each.
- [ ] **Step 2: Pick the best by dev SR; paired-bootstrap it against the incumbent (h7+h14)**. Gate as in gates.json `axis_experiments`. Winner becomes incumbent signal definition.
- [ ] **Step 3: Write `result.json` (all 7 SRs + bootstrap vs incumbent + decision); commit** — `git commit -m "exp(rebuild): axis 2 horizon set"`

### Task F4: Axis 3 — pool size

**Files:**
- Output (preds): `data/rebuild/preds/pool3_sol/`, `data/rebuild/preds/pool5/`
- Output: `data/rebuild/axis_pool/result.json`

- [ ] **Step 1: Regenerate two pool variants (background, incumbent target mode + feature set):** 3-coin (bitcoin ethereum solana) and 5-coin (add binancecoin, ripple) — same `--purge --train-window-days 730 --trade-date 2025-03-31 --days 1606` protocol.
- [ ] **Step 2: Compare BTC+ETH performance across pools** (the question is whether extra pool coins help/hurt the core signal): incumbent 2-pool vs 3-pool vs 5-pool, paired bootstrap vs incumbent, ledger-log, gate, decide.
- [ ] **Step 3: `result.json` + commit** — `git commit -m "exp(rebuild): axis 3 pool size"`

### Task F5: Axis 4 — feature set

**Files:**
- Output: `data/rebuild/axis_features/result.json`

Arms per coin: 78f (`btc_eth_78f`) vs 193f (`btc_eth_193f`) — both already generated in Task 4 (adjusted to incumbent target/pool if F2/F4 changed them: regenerate accordingly, background). Optional third arm iff both lose: +sentiment-index (branch `feature/sentiment-index-quant` has `add_sentiment=True` plumbing) — only wire if 193f shows signs of life (pre-registered: run sentiment arm iff 193f ΔSR > −0.2).

- [ ] **Step 1: Per-coin A/B 78f vs 193f** through the incumbent signal+sizing, paired bootstrap, ledger-log. This re-decides the voided §20 routing per coin.
- [ ] **Step 2: Gate + per-coin routing decision → `result.json`** (e.g. `{"bitcoin": "78f", "ethereum": "78f|193f"}`), commit — `git commit -m "exp(rebuild): axis 4 feature routing (replaces voided §20 T7)"`

### Task F6: Axis 5 — sizing ablation + ML survival verdict

**Files:**
- Output: `data/rebuild/axis_sizing/result.json`, `data/rebuild/directional_verdict.json`
- Modify: `THESIS_FINDINGS.md` (append §40)

- [ ] **Step 1: Sizing ablation on the incumbent config** — 6 arms, each toggling one component off (all else canonical): no-trend-filter (`trend_sma=0`), trend-multiplier 1.0 (filter on, no boost), no-vol-target (fixed size 1.0 pre-leverage), kelly 0.25 vs 0.5, min-hold 1 (vs 7), early-exit off (0). Each arm ledger-logged; paired bootstrap vs full config. Components that HURT (removal improves, p_pos ≥ 0.85) get removed from the final config. This re-measures the C1-artifact-inflated "trend filter is the biggest win" claim causally.
- [ ] **Step 2: ML survival gate** — final incumbent LGB config vs `data/rebuild/factor_floor/BEST`: `paired_bootstrap(floor, lgb)` + DSR of the LGB config with `n_trials = trial_count()` (all rebuild trials, honest count). Gate (gates.json `ml_survival`): ΔSR > 0, p_pos ≥ 0.85, DSR ≥ 0.90. Write `directional_verdict.json`: `{"sleeve": "lgb"|"factor", "config": {...}, "evidence": {...}}`.
- [ ] **Step 3: Append THESIS_FINDINGS §40** — all five axes + ablation + survival verdict, in §33's factual style. Include the honest-vs-void comparison for each axis (what the contaminated harness had chosen vs what the honest one chooses).
- [ ] **Step 4: Commit** — `git add THESIS_FINDINGS.md data/rebuild/axis_sizing/ data/rebuild/directional_verdict.json && git commit -m "exp(rebuild): §40 sizing ablation + directional sleeve verdict"`

---

## Phase 3 — Holdout one-shot + portfolio assembly

### Task H1: Freeze the candidate portfolio

**Files:**
- Create: `data/rebuild/frozen_portfolio.json`

- [ ] **Step 1: Write the freeze file** — exact sleeve configs (carry: stressed construction from C2 with its parameters; directional: `directional_verdict.json`'s config), allocation rule computed on DEV data only: inverse-vol weights with carry capped at 50% of book (cap prevents the audit-unfriendly "all eggs in the newest basket" even if carry SR dominates), rebalanced monthly. Include the literal holdout command lines to be run in H2. Commit BEFORE any holdout data is touched:

```bash
git add data/rebuild/frozen_portfolio.json
git commit -m "freeze(rebuild): candidate portfolio + allocation ahead of holdout one-shot"
```

### Task H2: Holdout one-shot

**Files:**
- Output (preds): `data/rebuild/preds_holdout/` (per the frozen routing)
- Output: `data/rebuild/holdout/result.json`
- Modify: `THESIS_FINDINGS.md` (append §41)

- [ ] **Step 1: Regenerate predictions through the holdout** (frozen config only, `--trade-date 2026-07-01`, `--days` extended accordingly (2063), same purge/rolling flags; `allow_holdout=True` on the ledger call — the ONLY place it is ever used). Carry: extend the C2 stressed series to 2026-07-01 with identical parameters.
- [ ] **Step 2: Run the frozen sleeves + portfolio on 2025-04-01→2026-07-01 exactly as written in `frozen_portfolio.json`.** One run. No parameter changes regardless of outcome.
- [ ] **Step 3: Evaluate the deploy gate** (gates.json `holdout_deploy`): portfolio net SR > 0.5, maxDD < 15%, each sleeve contribution ≥ 0, random-entry placebo p < 0.05 (reuse the placebo pattern from `validate_v5_mix.py` under causal convention). Write `result.json` with PASS/FAIL per criterion and per sleeve.
- [ ] **Step 4: Append THESIS_FINDINGS §41** — holdout table, gate evaluation, final verdict per sleeve, and the explicit statement of what ships to Phase 4 (possibly: carry only; possibly nothing — both are valid recorded outcomes).
- [ ] **Step 5: Commit** — `git add THESIS_FINDINGS.md data/rebuild/holdout/ && git commit -m "exp(rebuild): §41 holdout one-shot + deploy verdict"`
- [ ] **Step 6: Handoff** — Phase 4 (live integration) and Phase 5 (LLM re-test) get their own brainstorm+plan cycles seeded by `data/rebuild/holdout/result.json`.

---

## Self-review notes (kept for the executor)

- Spec §3.1 single entry point: honored — all runs go through `evaluate_models_multi.py` + `run_coin`/`run_coin_backtest`; the factor engine reuses the same sizing + engine, no fork.
- Spec §3.2 side-aware funding: `costs_for_coin(convention="causal")` charges side-blind on |pos| (documented conservative-for-shorts); carry uses real signed funding. Accepted as-is per audit remediation note — no task needed.
- Spec §5.1 says ≈15–20 factor configs: plan pins exactly 18.
- Spec §6 allocation rule: pinned to inverse-vol with 50% carry cap (H1) — was "expected vol-weighted with carry cap" in spec; this is the concretization.
- E1/E2/E3 plumbing: only E1's target-mode is cherry-picked (F2). E2 (offset ensemble) and E3 (quantile confidence) are NOT re-run in this plan — decision review rates E2 "may flip" but it is a variance-reduction refinement, meaningless before a sleeve exists; revisit post-holdout if the LGB sleeve survives. Recorded here so the omission is deliberate.
