# Hybrid V5 Live Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the hybrid V5 (quant base × LLM modulator) bot live on Binance testnet alongside the existing pure-quant V5 MIX bot, as a paired head-to-head A/B, **without touching the in-flight quant runner**.

**Architecture:** Two ordered systemd units. `ta-cycle` (existing, unchanged) runs the V5 quant cycle and writes its 8-coin predictions to the quant journal. `ta-hybrid-cycle` (new, `After=ta-cycle`, same UTC-date `cycle_id`) reads those predictions back, re-derives the V5 base via the shared `sizer`/`hold_sizer` against its own hold-state, runs the modulator graph per coin (`propagate_with_modulator`, gpt-4o-mini, Self-MoA N=5), recomposes `final = base × (1 + effective_weight × (multiplier − 1))`, and executes on a **second** Binance testnet account with its own journal. A weekly comparison job diffs the two journals.

**Tech Stack:** Python 3.9+, LangGraph/LangChain (modulator graph), SQLite (journals), Binance Futures testnet, systemd timers, pytest.

**Spec:** `docs/superpowers/specs/2026-06-11-hybrid-v5-live-deploy-design.md`
**Base branch:** `feature/hybrid-v5-live-deploy` (off `live-v2.2.2`).

---

## Conventions & verbatim interfaces (read before starting)

All paths are repo-relative. The hybrid module reuses these **unchanged** leaf modules from `tradingagents/execution/live/` — do not reimplement them:

- **Config:** `config.load_config() -> LiveConfig` (frozen dataclass). Fields used: `coin_universe`, `portfolio_weights`, `routing`, `horizons`, `symmetric`, `target_vol`, `kelly_fraction`, `max_leverage`, `vol_lookback`, `vol_cap_pct`, `confidence_ref_return`, `trend_sma`, `trend_multiplier`, `min_hold`, `early_exit_loss`, `stop_loss_pct`, `max_open_positions`, `max_daily_loss_pct`, `max_portfolio_dd`, `binance_api_key`, `binance_api_secret`, `binance_base_url`, `live_mode`, `data_root`, `initial_capital`, `min_capital_floor`. Helpers `config.to_binance_symbol(coin)`, `config.compute_portfolio_weights(universe)`.
- **Journal:** `journal.Journal(db_path: str)`. Writers: `log_cycle_start(cid, *, git_sha)`, `log_cycle_end(cid, *, status, error_msg="")`, `record_cycle(*, cycle_id, start_ts, end_ts, status, n_trades=0, ...)`, `log_prediction(*, cycle_id, coin, horizon, model_path_sha, pred_value, ref_price, signal_h7, signal_h14, consensus_signal)`, `log_sizing(*, cycle_id, coin, realized_vol, target_vol, kelly, confidence, base_size, leverage, sma30_multiplier, final_size_notional)`, `log_trade(*, cycle_id, coin, side, qty, entry_price, exit_price, pnl, fees, slippage, order_id, stop_loss_id, status) -> int`, `log_risk_check(cycle_id, coin, check_name, passed, value, threshold, reason)`, `log_shadow_decision(*, cycle_id, coin, live_signal, backtest_signal, live_size, backtest_size)`, `log_portfolio_snapshot(cycle_id, total_value, usdt_balance, position_qty_per_coin: dict, unrealized_pnl)`, `get_hold_state(coin) -> dict|None` (keys `current_dir,bars_held,entry_price,entry_base,entry_cycle`), `upsert_hold_state(*, coin, current_dir, bars_held, entry_price, entry_base, entry_cycle)`, `close()`. **There is NO reader for `predictions`/`sizing` by cycle_id — use a raw `sqlite3` SELECT** (WAL is on; the runner already does this at `runner.py:554-561`). Schema in `tradingagents/execution/live/schema.sql`; `predictions` columns: `cycle_id, coin, horizon, model_path_sha, pred_value, pred_quantile_low, pred_quantile_high, ref_price, signal_h7, signal_h14, consensus_signal, bundle_route`.
- **Sizing:** `sizer.compute_size(*, coin, prediction, price_history, horizons, symmetric, target_vol, kelly_fraction, max_leverage, vol_lookback, vol_cap_pct, confidence_ref, trend_sma, trend_multiplier) -> SizingResult` (fields `coin, signal, confidence, realized_vol, base_size, leverage, sma_multiplier, final_size_notional, vol_ok, dirs_per_horizon`). `sizer.bars_through(price_history, asof)`. `sizer.target_position_qty(*, size_fraction, portfolio_value, weight, ref_price) -> float`. `prediction` arg shape: `{"ref_price": float, "pred_h7": float, "pred_h14": float}`.
- **Hold state:** `from tradingagents.execution.live.hold_sizer import HoldState, step_hold_state`. `HoldState(current_dir, bars_held, entry_price, entry_base)`. `step_hold_state(state, *, sig, vol_ok, fresh_base, price, min_hold, early_exit_loss) -> (new_state, base_target)`. Executed base fraction = `base_target * sz.sma_multiplier` (this is the runner's `held_fraction`, `runner.py:464`).
- **Exchange:** `from tradingagents.execution.exchange import ExchangeClient, BinanceIPBan, BinanceOrderTimeoutUnknown`. `ExchangeClient(api_key, api_secret, testnet)`. Methods used: `set_leverage(symbol, int)`, `get_total_portfolio_value() -> float`, `get_current_position(symbol) -> float` (signed), `round_quantity(symbol, qty) -> float`, `min_notional(symbol) -> float`, `place_market_order(symbol, side, qty, reduce_only=False) -> dict`, `get_ticker_price(symbol) -> float`, `cancel_all_orders(symbol)`, `get_usdt_balance() -> float`.
- **Risk (live):** `tradingagents/execution/live/risk.py` module fns, each returning `(ok: bool, why: str)`: `check_leverage(held_fraction, max_leverage)`, `check_daily_loss(pnl_today_pct, max_daily_loss_pct)`, `check_drawdown(dd_from_peak, max_portfolio_dd)`, `check_frequency_guard(coin, today_count)`, `check_max_positions(open_count, max_open_positions, opening_new=bool)`.
- **Stops:** `stops.arm_stop_loss(ex, *, symbol, net_position, stop_price, stop_side) -> (stop_id, status)`.
- **Halt/heartbeat:** `halt.is_halted(*, data_dir=)`, `halt.halt_reason(*, data_dir=)`, `halt.write_halt(reason, *, data_dir=)`, `halt.clear_halt(*, data_dir=)`. Heartbeat = write ISO ts to `data_dir/last_cycle_heartbeat.txt`.
- **Modulator graph:** `from tradingagents.graph.trading_graph import TradingAgentsGraph`. `TradingAgentsGraph(selected_analysts=[...], debug=False, config=<dict>)`. `propagate_with_modulator(company_name, trade_date) -> (final_state, modulated_position, quant_signal, narrative)`. `modulated_position` is a dict (or `None` if Layer-1 failed) with keys: `coin, quant_direction, quant_magnitude, llm_multiplier, llm_confidence, llm_uncertainty, effective_weight, position, narrative, regime, unlock_flag, rolling_llm_edge`. **Use `llm_multiplier` + `effective_weight`; discard `position`.**
- **Quant-engine staging target:** `quant_engine._load_pred_row` reads `{quant_pred_dir}/preds_lgb_h7.csv` + `preds_lgb_h14.csv`, columns `date, coin_id, ref_price, prediction`; override via `config["quant_pred_dir"]`.
- **`cycle_id`** default = UTC date ISO string (`datetime.now(timezone.utc).date().isoformat()`), e.g. `"2026-06-11"`. The hybrid cycle uses the **same** id so it reads the same quant cycle.

**Commit after every task. Run `python -m pytest <the task's test file> -v` before committing.**

---

## Phase 0 — Pre-train missing per-coin checkpoints

Live universe (`config.py:179-182`): `bitcoin ethereum binancecoin solana ripple dogecoin cardano tron`. Regime HMM present: BTC/ETH/BNB/SOL. Isotonic calibration present: BTC/ETH.

### Task 0.1: Train regime HMM for XRP, DOGE, ADA, TRX

**Files:**
- Use existing: `scripts/train_regime_hmm.py`
- Produces: `data/checkpoints/regime_hmm_{ripple,dogecoin,cardano,tron}.pkl`
- Test: `tests/strategies/test_regime_hmm_satellites.py`

- [ ] **Step 1: Write the failing test** (asserts all 8 live coins have a loadable regime HMM)

```python
# tests/strategies/test_regime_hmm_satellites.py
import pickle
from pathlib import Path
import pytest

LIVE_COINS = ["bitcoin", "ethereum", "binancecoin", "solana",
              "ripple", "dogecoin", "cardano", "tron"]

@pytest.mark.parametrize("coin", LIVE_COINS)
def test_regime_hmm_present_and_loadable(coin):
    path = Path("data/checkpoints") / f"regime_hmm_{coin}.pkl"
    assert path.exists(), f"missing regime HMM for {coin}"
    with open(path, "rb") as f:
        bundle = pickle.load(f)
    # FittedHMM bundle: has a fitted GaussianHMM + a 3-state label map
    assert hasattr(bundle, "model")
    assert hasattr(bundle, "state_to_label")
    assert len(set(bundle.state_to_label.values())) >= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/strategies/test_regime_hmm_satellites.py -v`
Expected: FAIL for ripple/dogecoin/cardano/tron ("missing regime HMM").

- [ ] **Step 3: Train the four satellites**

Run (`--through` = yesterday UTC, to respect the no-look-ahead boundary):
```bash
python scripts/train_regime_hmm.py \
    --coins ripple dogecoin cardano tron \
    --through 2026-06-10 --out-dir data/checkpoints --n-iter 200
```
Expected stdout: one "saved data/checkpoints/regime_hmm_<coin>.pkl" line per coin. If a coin raises `insufficient OHLCV history` (<200 bars), note it in the commit message — TRX/DOGE have long histories so this should not trigger.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/strategies/test_regime_hmm_satellites.py -v`
Expected: PASS (8/8).

- [ ] **Step 5: Commit**

```bash
git add tests/strategies/test_regime_hmm_satellites.py data/checkpoints/regime_hmm_ripple.pkl data/checkpoints/regime_hmm_dogecoin.pkl data/checkpoints/regime_hmm_cardano.pkl data/checkpoints/regime_hmm_tron.pkl
git commit -m "feat(hybrid): regime HMM checkpoints for XRP/DOGE/ADA/TRX"
```

### Task 0.2 — DROPPED (calibration is inert on the hybrid position)

> **Decision 2026-06-11: DO NOT run this task.** Code trace confirms the isotonic-calibrated confidence (`agents/modulator.py:166-168`) lands only in `ModulatedPosition.llm_confidence` — a logged audit field. The position formula (`strategies/modulator.py:66`) is `magnitude × (1 + effective_weight × (multiplier − 1))`, where `multiplier=m_mean` (raw) and `effective_weight` keys on `uncertainty=m_std` (raw); neither reads the calibrated confidence, and the live runner discards `llm_confidence` (`extract_modulator_outputs` pulls only multiplier + effective_weight). So fitted vs identity calibrators ⇒ **identical trades**. The 6 satellites use identity calibration (`load_or_identity`) — behaviorally identical, not a degradation. Saves the ~$50–75 one-off LLM spend. Re-open ONLY if a future change makes `llm_confidence` affect sizing, or the thesis needs the logged confidence empirically meaningful. **The steps below are retained for reference and MUST NOT be executed.**

**Files:**
- Use existing: `scripts/generate_hybrid_signals.py`, `tradingagents/strategies/calibration.py` (`IsotonicCalibrator`)
- Create: `scripts/fit_isotonic_from_signals.py`
- Produces: `data/checkpoints/isotonic_{binancecoin,solana,ripple,dogecoin,cardano,tron}.pkl`
- Test: `tests/strategies/test_isotonic_satellites.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/strategies/test_isotonic_satellites.py
from pathlib import Path
import pytest
from tradingagents.strategies.calibration import IsotonicCalibrator

SATELLITES = ["binancecoin", "solana", "ripple", "dogecoin", "cardano", "tron"]

@pytest.mark.parametrize("coin", SATELLITES)
def test_isotonic_fitted(coin):
    path = Path("data/checkpoints") / f"isotonic_{coin}.pkl"
    assert path.exists(), f"missing isotonic calibrator for {coin}"
    cal = IsotonicCalibrator.from_pkl(str(path))
    assert cal.n_train >= 10
    # monotone, bounded
    assert 0.0 <= cal.transform(0.5) <= 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/strategies/test_isotonic_satellites.py -v`
Expected: FAIL (missing pkls).

- [ ] **Step 3: Generate signals (GATED) then write the fitter**

Generate the historical hybrid signals (only after the cost gate above is cleared):
```bash
python scripts/generate_hybrid_signals.py \
    --coins binancecoin solana ripple dogecoin cardano tron \
    --analysts market onchain prediction \
    --start 2024-05-01 --end 2025-05-01 \
    --deep-think gpt-4o-mini --quick-think gpt-4o-mini \
    --out-dir data/hybrid_signals_calib
```

Then create `scripts/fit_isotonic_from_signals.py`:
```python
"""Fit per-coin isotonic calibrators from cached hybrid-signal CSVs.

Reads the generate_hybrid_signals output (one CSV per coin with columns
including llm_confidence/llm_uncertainty + the realized forward direction),
builds (raw_conf, outcome) pairs, and fits + saves an IsotonicCalibrator.
"""
from __future__ import annotations
import argparse, glob, os
import numpy as np
import pandas as pd
from tradingagents.strategies.calibration import IsotonicCalibrator


def _pairs_for_coin(csv_path: str) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(csv_path, parse_dates=["date"]).sort_values("date")
    df = df[df["error"].isna()] if "error" in df.columns else df
    # raw_conf the modulator calibrates is (1 - llm_uncertainty); see
    # agents/modulator.py:166. Fall back to llm_confidence if absent.
    if "llm_uncertainty" in df.columns:
        raw = (1.0 - df["llm_uncertainty"].astype(float)).clip(0.0, 1.0)
    else:
        raw = df["llm_confidence"].astype(float).clip(0.0, 1.0)
    # outcome = was the quant direction correct over the next bar?
    fwd = df["ref_price"].shift(-1) / df["ref_price"] - 1.0  # placeholder fwd ret
    sign = df["quant_direction"].map({"long": 1, "short": -1, "flat": 0}).fillna(0)
    outcome = ((np.sign(fwd) == np.sign(sign)) & (sign != 0)).astype(float)
    mask = raw.notna() & fwd.notna() & (sign != 0)
    return raw[mask].to_numpy(), outcome[mask].to_numpy()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--signals-dir", default="data/hybrid_signals_calib")
    p.add_argument("--coins", nargs="+", required=True)
    p.add_argument("--out-dir", default="data/checkpoints")
    args = p.parse_args()
    for coin in args.coins:
        matches = glob.glob(os.path.join(args.signals_dir, f"{coin}_*.csv"))
        if not matches:
            print(f"SKIP {coin}: no signals CSV")
            continue
        raw, outcome = _pairs_for_coin(sorted(matches)[-1])
        if len(raw) < 10:
            print(f"SKIP {coin}: only {len(raw)} usable pairs (<10)")
            continue
        cal = IsotonicCalibrator().fit(raw, outcome, coin=coin)
        out = os.path.join(args.out_dir, f"isotonic_{coin}.pkl")
        cal.to_pkl(out)
        print(f"saved {out} (n_train={cal.n_train})")


if __name__ == "__main__":
    main()
```

Run it:
```bash
python scripts/fit_isotonic_from_signals.py \
    --coins binancecoin solana ripple dogecoin cardano tron
```
Expected: one "saved ... (n_train=N)" per coin (N ≥ 10). Any "SKIP" coin stays on identity calibration — record it.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/strategies/test_isotonic_satellites.py -v`
Expected: PASS for every coin that fit (≥10 pairs). Mark `xfail` for any documented SKIP coin.

- [ ] **Step 5: Commit**

```bash
git add scripts/fit_isotonic_from_signals.py tests/strategies/test_isotonic_satellites.py data/checkpoints/isotonic_*.pkl
git commit -m "feat(hybrid): isotonic calibrators for satellite coins (gated LLM pass)"
```

---

## Phase 1 — Offline-testable compose primitives

New module `tradingagents/execution/live/hybrid_compose.py` holds pure functions (no I/O, no network) so they are fully unit-testable.

### Task 1.1: `compose_final` — the composition formula

**Files:**
- Create: `tradingagents/execution/live/hybrid_compose.py`
- Test: `tests/execution/live/test_hybrid_compose.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/live/test_hybrid_compose.py
import math
from tradingagents.execution.live.hybrid_compose import compose_final

def test_multiplier_one_is_identity():
    assert compose_final(base=0.8, multiplier=1.0, effective_weight=0.7) == 0.8

def test_effective_weight_zero_is_identity():
    assert compose_final(base=0.8, multiplier=1.5, effective_weight=0.0) == 0.8

def test_full_formula():
    # base * (1 + eff_w*(mult-1)) = 0.8*(1+0.5*(1.4-1)) = 0.8*1.2 = 0.96
    assert math.isclose(compose_final(base=0.8, multiplier=1.4, effective_weight=0.5), 0.96)

def test_negative_base_preserves_sign():
    # short base, mult>1 levers the short further
    assert math.isclose(compose_final(base=-0.5, multiplier=1.2, effective_weight=1.0), -0.6)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/live/test_hybrid_compose.py -v`
Expected: FAIL ("cannot import name 'compose_final'").

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/execution/live/hybrid_compose.py
"""Pure compose primitives for the hybrid (quant base × LLM modulator) path.

The composition mirrors the validated §23 backtest
(scripts/backtest_hybrid.py:118, scripts/ablate_hybrid.py:73):

    final = base * (1 + effective_weight * (multiplier - 1))

where ``base`` is the V5-sized quant position and (multiplier, effective_weight)
come from the modulator graph's ``modulated_position`` (NOT its ``position``,
which composed against the graph's own internal magnitude).
"""
from __future__ import annotations


def compose_final(*, base: float, multiplier: float, effective_weight: float) -> float:
    return float(base * (1.0 + effective_weight * (multiplier - 1.0)))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/execution/live/test_hybrid_compose.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/hybrid_compose.py tests/execution/live/test_hybrid_compose.py
git commit -m "feat(hybrid): compose_final composition primitive"
```

### Task 1.2: `extract_modulator_outputs` — safe extraction with skip fallback

The graph returns `modulated_position=None` on Layer-1 failure, and defaults `multiplier=1.0` when no multiplier parses. The hybrid must degrade to **pure quant** (mult=1.0, eff_w=0.0) on any missing field so a modulator failure never changes the position vs the quant base.

**Files:**
- Modify: `tradingagents/execution/live/hybrid_compose.py`
- Test: `tests/execution/live/test_hybrid_compose.py`

- [ ] **Step 1: Write the failing test** (append)

```python
from tradingagents.execution.live.hybrid_compose import extract_modulator_outputs

def test_extract_none_is_pure_quant():
    mult, eff_w = extract_modulator_outputs(None)
    assert (mult, eff_w) == (1.0, 0.0)

def test_extract_missing_keys_is_pure_quant():
    mult, eff_w = extract_modulator_outputs({"coin": "bitcoin"})
    assert (mult, eff_w) == (1.0, 0.0)

def test_extract_reads_fields():
    mp = {"llm_multiplier": 1.3, "effective_weight": 0.6, "position": 999.0}
    assert extract_modulator_outputs(mp) == (1.3, 0.6)

def test_extract_clamps_multiplier_to_contract_bounds():
    # ModulatedPosition bounds llm_multiplier to [0, 1.5]
    assert extract_modulator_outputs({"llm_multiplier": 9.0, "effective_weight": 0.5})[0] == 1.5
    assert extract_modulator_outputs({"llm_multiplier": -9.0, "effective_weight": 0.5})[0] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/live/test_hybrid_compose.py -v`
Expected: FAIL ("cannot import name 'extract_modulator_outputs'").

- [ ] **Step 3: Write minimal implementation** (append to `hybrid_compose.py`)

```python
def extract_modulator_outputs(modulated_position: dict | None) -> tuple[float, float]:
    """Return (multiplier, effective_weight) from a modulated_position dict.

    Degrades to pure quant (1.0, 0.0) when the modulator was skipped or any
    field is missing, so a modulator failure never moves the hybrid position
    away from the quant base. Multiplier clamped to the contract bounds [0,1.5].
    """
    if not modulated_position:
        return (1.0, 0.0)
    mult = modulated_position.get("llm_multiplier")
    eff_w = modulated_position.get("effective_weight")
    if mult is None or eff_w is None:
        return (1.0, 0.0)
    mult = max(0.0, min(1.5, float(mult)))
    eff_w = max(0.0, min(1.0, float(eff_w)))
    return (mult, eff_w)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/execution/live/test_hybrid_compose.py -v`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/hybrid_compose.py tests/execution/live/test_hybrid_compose.py
git commit -m "feat(hybrid): extract_modulator_outputs with pure-quant fallback"
```

### Task 1.3: `stage_quant_preds` — pivot cycle preds to the quant_engine CSV layout

**Files:**
- Modify: `tradingagents/execution/live/hybrid_compose.py`
- Test: `tests/execution/live/test_stage_quant_preds.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/live/test_stage_quant_preds.py
import pandas as pd
from tradingagents.execution.live.hybrid_compose import stage_quant_preds

def test_stage_writes_h7_h14_with_required_columns(tmp_path):
    # cycle preds rows: (coin, horizon, prediction, ref_price)
    rows = [
        {"coin": "bitcoin", "horizon": 7,  "prediction": 0.012, "ref_price": 65000.0},
        {"coin": "bitcoin", "horizon": 14, "prediction": 0.020, "ref_price": 65000.0},
        {"coin": "ethereum","horizon": 7,  "prediction": -0.005,"ref_price": 3200.0},
        {"coin": "ethereum","horizon": 14, "prediction": -0.001,"ref_price": 3200.0},
    ]
    out = stage_quant_preds(rows, date="2026-06-11", out_dir=tmp_path)
    h7 = pd.read_csv(out / "preds_lgb_h7.csv")
    h14 = pd.read_csv(out / "preds_lgb_h14.csv")
    assert set(["date", "coin_id", "ref_price", "prediction"]).issubset(h7.columns)
    assert set(["date", "coin_id", "ref_price", "prediction"]).issubset(h14.columns)
    btc7 = h7[h7["coin_id"] == "bitcoin"].iloc[0]
    assert btc7["prediction"] == 0.012 and btc7["ref_price"] == 65000.0
    assert h14[h14["coin_id"] == "ethereum"].iloc[0]["prediction"] == -0.001
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/live/test_stage_quant_preds.py -v`
Expected: FAIL ("cannot import name 'stage_quant_preds'").

- [ ] **Step 3: Write minimal implementation** (append to `hybrid_compose.py`)

```python
from pathlib import Path
import pandas as pd


def stage_quant_preds(rows: list[dict], *, date: str, out_dir) -> Path:
    """Write cycle predictions to the quant_engine CSV layout.

    ``rows`` = list of {coin, horizon, prediction, ref_price}. Writes
    preds_lgb_h7.csv and preds_lgb_h14.csv (columns date, coin_id, ref_price,
    prediction) under ``out_dir`` and returns it. Point config["quant_pred_dir"]
    at the returned path.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    for h, fname in [(7, "preds_lgb_h7.csv"), (14, "preds_lgb_h14.csv")]:
        sub = df[df["horizon"] == h].copy()
        sub["date"] = pd.to_datetime(date).normalize()
        sub = sub.rename(columns={"coin": "coin_id"})
        sub[["date", "coin_id", "ref_price", "prediction"]].to_csv(
            out_dir / fname, index=False
        )
    return out_dir
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/execution/live/test_stage_quant_preds.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/hybrid_compose.py tests/execution/live/test_stage_quant_preds.py
git commit -m "feat(hybrid): stage_quant_preds pivots cycle preds to quant_engine CSV layout"
```

### Task 1.4: `read_cycle_predictions` — raw SELECT of the quant journal's preds

**Files:**
- Create: `tradingagents/execution/live/hybrid_io.py`
- Test: `tests/execution/live/test_hybrid_io.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/live/test_hybrid_io.py
from tradingagents.execution.live.journal import Journal
from tradingagents.execution.live.hybrid_io import read_cycle_predictions

def test_read_cycle_predictions_roundtrip(tmp_path):
    db = str(tmp_path / "trade_journal.db")
    j = Journal(db)
    j.log_cycle_start("2026-06-11", git_sha="abc")
    import pandas as pd
    preds_df = pd.DataFrame([
        {"coin": "bitcoin", "horizon": 7,  "prediction": 0.012, "ref_price": 65000.0, "bundle_route": "bitcoin_78f"},
        {"coin": "bitcoin", "horizon": 14, "prediction": 0.020, "ref_price": 65000.0, "bundle_route": "bitcoin_78f"},
        {"coin": "ethereum","horizon": 7,  "prediction": -0.005,"ref_price": 3200.0,  "bundle_route": "ethereum_193f"},
        {"coin": "ethereum","horizon": 14, "prediction": -0.001,"ref_price": 3200.0,  "bundle_route": "ethereum_193f"},
    ])
    j.record_predictions(cycle_id="2026-06-11", preds_df=preds_df)
    j.close()

    rows, preds = read_cycle_predictions(db, "2026-06-11")
    # rows: list of {coin, horizon, prediction, ref_price} (for staging)
    assert len(rows) == 4
    # preds: per-coin dict for sizer.compute_size
    assert preds["bitcoin"]["ref_price"] == 65000.0
    assert preds["bitcoin"]["pred_h7"] == 0.012
    assert preds["bitcoin"]["pred_h14"] == 0.020
    assert preds["ethereum"]["pred_h14"] == -0.001

def test_read_missing_cycle_returns_empty(tmp_path):
    db = str(tmp_path / "trade_journal.db")
    Journal(db).close()
    rows, preds = read_cycle_predictions(db, "2026-06-11")
    assert rows == [] and preds == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/live/test_hybrid_io.py -v`
Expected: FAIL ("No module named ...hybrid_io").

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/execution/live/hybrid_io.py
"""Read-only access to the quant journal for the hybrid cycle.

The Journal class has no reader for the predictions table, so we open our own
sqlite3 connection (WAL is enabled by the writer) and SELECT directly — the
same pattern the runner uses for its frequency-guard read (runner.py:554-561).
"""
from __future__ import annotations
import sqlite3


def read_cycle_predictions(quant_db_path: str, cycle_id: str):
    """Return (rows, preds) for a cycle.

    rows  = list[{coin, horizon, prediction, ref_price}]  (for stage_quant_preds)
    preds = {coin: {"ref_price": float, "pred_h7": float, "pred_h14": float}}
            (for sizer.compute_size). Only coins with both horizons present
            appear in preds.
    """
    conn = sqlite3.connect(quant_db_path)
    try:
        cur = conn.execute(
            "SELECT coin, horizon, pred_value, ref_price "
            "FROM predictions WHERE cycle_id = ? ORDER BY coin, horizon",
            (cycle_id,),
        )
        raw = cur.fetchall()
    finally:
        conn.close()

    rows: list[dict] = []
    preds: dict[str, dict] = {}
    for coin, horizon, pred_value, ref_price in raw:
        rows.append({"coin": coin, "horizon": int(horizon),
                     "prediction": float(pred_value), "ref_price": float(ref_price)})
        d = preds.setdefault(coin, {"ref_price": float(ref_price)})
        d[f"pred_h{int(horizon)}"] = float(pred_value)
    # drop coins missing either horizon
    preds = {c: d for c, d in preds.items() if "pred_h7" in d and "pred_h14" in d}
    return rows, preds
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/execution/live/test_hybrid_io.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/hybrid_io.py tests/execution/live/test_hybrid_io.py
git commit -m "feat(hybrid): read_cycle_predictions raw SELECT of quant journal preds"
```

---

## Phase 2 — Hybrid graph config + base re-derivation

### Task 2.1: `build_hybrid_config` — pinned validated modulator config

**Files:**
- Modify: `tradingagents/execution/live/hybrid_compose.py`
- Test: `tests/execution/live/test_hybrid_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/live/test_hybrid_config.py
from tradingagents.execution.live.hybrid_compose import build_hybrid_config, HYBRID_ANALYSTS

def test_pins_gpt_4o_mini_both_slots():
    cfg = build_hybrid_config(quant_pred_dir="/tmp/x")
    assert cfg["deep_think_llm"] == "gpt-4o-mini"
    assert cfg["quick_think_llm"] == "gpt-4o-mini"
    assert cfg["llm_provider"] == "openai"

def test_points_quant_pred_dir():
    cfg = build_hybrid_config(quant_pred_dir="/tmp/cycle/preds")
    assert cfg["quant_pred_dir"] == "/tmp/cycle/preds"

def test_replay_cache_off_for_live():
    assert build_hybrid_config(quant_pred_dir="/tmp/x")["replay_cache"] is False

def test_analyst_set_drops_sentiment():
    assert HYBRID_ANALYSTS == ["market", "onchain", "prediction"]
    assert "crypto_sentiment" not in HYBRID_ANALYSTS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/live/test_hybrid_config.py -v`
Expected: FAIL (import error).

- [ ] **Step 3: Write minimal implementation** (append to `hybrid_compose.py`)

```python
from tradingagents.default_config import DEFAULT_CONFIG

# Validated §23 production analyst set: market + onchain + prediction.
# crypto_sentiment dropped (feedback_drop_sentiment_analyst); market kept
# (market-analyst-v2 refactor rejected, project_market_analyst_v2).
HYBRID_ANALYSTS = ["market", "onchain", "prediction"]


def build_hybrid_config(*, quant_pred_dir: str) -> dict:
    """DEFAULT_CONFIG with the validated hybrid pins applied.

    Pins gpt-4o-mini for both LLM slots (gpt-5-mini HURT, §23.9), turns the
    replay cache off (live), and points quant_pred_dir at the staged live
    preds. Modulator config (regime_weighting, dampeners, rolling_edge_*) is
    inherited from DEFAULT_CONFIG unchanged (validated defaults).
    """
    cfg = DEFAULT_CONFIG.copy()
    cfg["asset_class"] = "crypto"
    cfg["llm_provider"] = "openai"
    cfg["deep_think_llm"] = "gpt-4o-mini"
    cfg["quick_think_llm"] = "gpt-4o-mini"
    cfg["replay_cache"] = False
    cfg["quant_pred_dir"] = quant_pred_dir
    return cfg
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/execution/live/test_hybrid_config.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/hybrid_compose.py tests/execution/live/test_hybrid_config.py
git commit -m "feat(hybrid): build_hybrid_config pins gpt-4o-mini + validated analyst set"
```

### Task 2.2: `derive_base` — re-derive the executed V5 base for one coin

**Files:**
- Create: `tradingagents/execution/live/hybrid_base.py`
- Test: `tests/execution/live/test_hybrid_base.py`

This wraps `sizer.compute_size` + `hold_sizer.step_hold_state` exactly as the runner does (`runner.py:385-464`), but against a caller-supplied prior `HoldState` (the hybrid journal's own). Returns the executed base fraction `held_fraction` plus the new `HoldState` and the `SizingResult` (needed for journaling + shadow + stop side).

- [ ] **Step 1: Write the failing test** (uses a real price history fixture + real prediction; asserts identity vs the runner's formula)

```python
# tests/execution/live/test_hybrid_base.py
import numpy as np
import pandas as pd
import pytest
from tradingagents.execution.live.hold_sizer import HoldState
from tradingagents.execution.live.hybrid_base import derive_base

@pytest.fixture
def history():
    # 60 bars of synthetic but monotone-ish OHLCV so vol + SMA are well-defined
    idx = pd.date_range("2026-03-01", periods=60, freq="D")
    px = pd.Series(100.0 + np.arange(60) * 0.5)
    return pd.DataFrame({"Date": idx, "Open": px, "High": px * 1.01,
                         "Low": px * 0.99, "Close": px, "Volume": 1000.0})

def test_derive_base_returns_fraction_state_and_sizing(history):
    cfg = dict(horizons=[7, 14], symmetric=False, target_vol=0.10,
               kelly_fraction=0.25, max_leverage=3.0, vol_lookback=20,
               vol_cap_pct=0.95, confidence_ref_return=0.05, trend_sma=30,
               trend_multiplier=1.5, min_hold=7, early_exit_loss=0.015)
    prediction = {"ref_price": float(history["Close"].iloc[-1]),
                  "pred_h7": 0.03, "pred_h14": 0.05}
    held_fraction, new_state, sz = derive_base(
        coin="bitcoin", prediction=prediction, price_history=history,
        prev_state=HoldState(0, 0, 0.0, 0.0), cfg=cfg, asof="2026-04-29",
    )
    assert isinstance(held_fraction, float)
    assert new_state.bars_held >= 1
    # identity with the runner's formula: held_fraction == base_target * sma_mult
    assert sz.coin == "bitcoin"
    # long prediction => non-negative base
    assert held_fraction >= 0.0

def test_insufficient_history_returns_zero(history):
    cfg = dict(horizons=[7, 14], symmetric=False, target_vol=0.10,
               kelly_fraction=0.25, max_leverage=3.0, vol_lookback=20,
               vol_cap_pct=0.95, confidence_ref_return=0.05, trend_sma=30,
               trend_multiplier=1.5, min_hold=7, early_exit_loss=0.015)
    short = history.iloc[:5]
    prediction = {"ref_price": 100.0, "pred_h7": 0.03, "pred_h14": 0.05}
    held_fraction, new_state, sz = derive_base(
        coin="bitcoin", prediction=prediction, price_history=short,
        prev_state=HoldState(0, 0, 0.0, 0.0), cfg=cfg, asof="2026-04-29",
    )
    assert held_fraction == 0.0 and sz is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/live/test_hybrid_base.py -v`
Expected: FAIL (no module).

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/execution/live/hybrid_base.py
"""Re-derive the executed V5 base fraction for one coin.

Mirrors the runner's size+hold sequence (runner.py:373-464) so the hybrid
composes against the same V5 base the quant logic would produce — but using
the HYBRID journal's own prior HoldState, so the hybrid runs its own min-hold
discipline on its own book. Zero dependency on the quant runner.
"""
from __future__ import annotations
from tradingagents.execution.live import sizer
from tradingagents.execution.live.hold_sizer import HoldState, step_hold_state


def derive_base(*, coin: str, prediction: dict, price_history,
                prev_state: HoldState, cfg: dict, asof: str):
    """Return (held_fraction, new_state, sizing_result_or_None).

    held_fraction == base_target * sz.sma_multiplier (the runner's executed
    base). Returns (0.0, prev_state, None) when history is too short.
    """
    history = sizer.bars_through(price_history, asof)
    if len(history) < int(cfg["vol_lookback"]):
        return 0.0, prev_state, None

    sz = sizer.compute_size(
        coin=coin, prediction=prediction, price_history=history,
        horizons=cfg["horizons"], symmetric=cfg["symmetric"],
        target_vol=cfg["target_vol"], kelly_fraction=cfg["kelly_fraction"],
        max_leverage=cfg["max_leverage"], vol_lookback=cfg["vol_lookback"],
        vol_cap_pct=cfg["vol_cap_pct"], confidence_ref=cfg["confidence_ref_return"],
        trend_sma=cfg["trend_sma"], trend_multiplier=cfg["trend_multiplier"],
    )
    new_state, base_target = step_hold_state(
        prev_state, sig=sz.signal, vol_ok=sz.vol_ok,
        fresh_base=sz.leverage, price=prediction["ref_price"],
        min_hold=cfg["min_hold"], early_exit_loss=cfg["early_exit_loss"],
    )
    held_fraction = base_target * sz.sma_multiplier
    return float(held_fraction), new_state, sz
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/execution/live/test_hybrid_base.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/hybrid_base.py tests/execution/live/test_hybrid_base.py
git commit -m "feat(hybrid): derive_base re-derives executed V5 base via shared sizer/hold_sizer"
```

---

## Phase 3 — `hybrid_runner` orchestration + second-account execution

### Task 3.1: Hybrid config loader (second account + own data dir)

The hybrid reuses `config.load_config()` for the V5 sizing/risk knobs but overrides the **account** + **data dir** from `HYBRID_*` env vars so it never touches the quant account/journal.

**Files:**
- Create: `tradingagents/execution/live/hybrid_config.py`
- Test: `tests/execution/live/test_hybrid_account_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/live/test_hybrid_account_config.py
import os
from tradingagents.execution.live.hybrid_config import load_hybrid_account

def test_reads_hybrid_env(monkeypatch):
    monkeypatch.setenv("HYBRID_BINANCE_API_KEY", "hk")
    monkeypatch.setenv("HYBRID_BINANCE_API_SECRET", "hs")
    monkeypatch.setenv("HYBRID_DATA_DIR", "/opt/tradingagents/data-hybrid")
    monkeypatch.setenv("QUANT_DATA_DIR", "/opt/tradingagents/data")
    acct = load_hybrid_account()
    assert acct.api_key == "hk" and acct.api_secret == "hs"
    assert acct.data_dir.endswith("data-hybrid")
    assert acct.quant_db_path.endswith("data/trade_journal.db")

def test_missing_hybrid_key_raises(monkeypatch):
    monkeypatch.delenv("HYBRID_BINANCE_API_KEY", raising=False)
    import pytest
    with pytest.raises(ValueError):
        load_hybrid_account()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/live/test_hybrid_account_config.py -v`
Expected: FAIL (no module).

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/execution/live/hybrid_config.py
"""Second-account + data-dir resolution for the hybrid cycle.

V5 sizing/risk knobs come from the shared config.load_config(); only the
Binance account credentials and the data dir are overridden so the hybrid
book is fully isolated from the quant book.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HybridAccount:
    api_key: str
    api_secret: str
    data_dir: str
    quant_db_path: str


def load_hybrid_account() -> HybridAccount:
    key = os.environ.get("HYBRID_BINANCE_API_KEY", "")
    secret = os.environ.get("HYBRID_BINANCE_API_SECRET", "")
    if not key or not secret:
        raise ValueError("HYBRID_BINANCE_API_KEY / _SECRET must be set")
    data_dir = os.environ.get("HYBRID_DATA_DIR", "data-hybrid")
    quant_data = os.environ.get("QUANT_DATA_DIR", os.environ.get("DATA_DIR", "data"))
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    return HybridAccount(
        api_key=key, api_secret=secret, data_dir=data_dir,
        quant_db_path=str(Path(quant_data) / "trade_journal.db"),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/execution/live/test_hybrid_account_config.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/hybrid_config.py tests/execution/live/test_hybrid_account_config.py
git commit -m "feat(hybrid): hybrid account + data-dir env resolution"
```

### Task 3.2: `run_hybrid_cycle` — orchestration skeleton (halt/heartbeat/journal lifecycle)

**Files:**
- Create: `tradingagents/execution/live/hybrid_runner.py`
- Test: `tests/execution/live/test_hybrid_runner_skeleton.py`

- [ ] **Step 1: Write the failing test** (halt short-circuits; heartbeat written; reuses `CycleResult`)

```python
# tests/execution/live/test_hybrid_runner_skeleton.py
from pathlib import Path
from tradingagents.execution.live import hybrid_runner, halt
from tradingagents.execution.live.runner import CycleResult

def test_halt_short_circuits(tmp_path, monkeypatch):
    monkeypatch.setenv("HYBRID_DATA_DIR", str(tmp_path))
    halt.write_halt("test", data_dir=tmp_path)
    res = hybrid_runner.run_hybrid_cycle(cycle_id="2026-06-11", dry_run=True)
    assert isinstance(res, CycleResult)
    assert res.status == "halted"
    assert (tmp_path / "last_cycle_heartbeat.txt").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/live/test_hybrid_runner_skeleton.py -v`
Expected: FAIL (no module / wrong behavior).

- [ ] **Step 3: Write minimal implementation** (skeleton — full per-coin loop added in 3.3)

```python
# tradingagents/execution/live/hybrid_runner.py
"""Hybrid (quant base × LLM modulator) live cycle.

Runs AFTER ta-cycle, reads the quant cycle's predictions, re-derives the V5
base, runs the modulator graph per coin, recomposes, and executes on a SECOND
testnet account with its own journal. Zero writes to the quant book.
"""
from __future__ import annotations
import argparse, logging, os, sys
from datetime import datetime, timezone
from pathlib import Path

from tradingagents.execution.live import config, halt, journal
from tradingagents.execution.live.hybrid_config import load_hybrid_account
from tradingagents.execution.live.runner import CycleResult, _today_id, _write_heartbeat

logger = logging.getLogger(__name__)


def run_hybrid_cycle(cycle_id: str | None = None, dry_run: bool = False) -> CycleResult:
    cycle_id = cycle_id or _today_id()
    acct = load_hybrid_account()
    data_dir = Path(acct.data_dir)
    n_executed = 0
    try:
        if halt.is_halted(data_dir=data_dir):
            return CycleResult(cycle_id=cycle_id, status="halted", n_executed=0,
                               error_msg=halt.halt_reason(data_dir=data_dir))
        # --- per-coin loop added in Task 3.3 ---
        return CycleResult(cycle_id=cycle_id, status="ok", n_executed=n_executed)
    except Exception as e:  # never raise — mirror run_cycle contract
        logger.exception("hybrid cycle failed")
        return CycleResult(cycle_id=cycle_id, status="error", n_executed=n_executed,
                           error_msg=str(e))
    finally:
        _write_heartbeat(data_dir)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/execution/live/test_hybrid_runner_skeleton.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/hybrid_runner.py tests/execution/live/test_hybrid_runner_skeleton.py
git commit -m "feat(hybrid): run_hybrid_cycle skeleton with halt+heartbeat lifecycle"
```

### Task 3.3: Per-coin loop — read preds → stage → derive base → modulate → compose → execute

**Files:**
- Modify: `tradingagents/execution/live/hybrid_runner.py`
- Test: `tests/execution/live/test_hybrid_runner_loop.py`

The loop reuses the runner's execution sequence (`runner.py:576-758`) but on the hybrid account: `target_position_qty` → delta vs current pos → `round_quantity` → `min_notional` guard → `place_market_order` → `arm_stop_loss` → journal. The modulator graph is injected (a `graph_factory` param) so the test can stub it.

- [ ] **Step 1: Write the failing test** (mocked exchange + stubbed graph; asserts compose + that orders hit only the hybrid account)

```python
# tests/execution/live/test_hybrid_runner_loop.py
import pandas as pd
import pytest
from tradingagents.execution.live import hybrid_runner
from tradingagents.execution.live.journal import Journal

class FakeExchange:
    def __init__(self): self.orders = []; self.stops = []
    def set_leverage(self, *a, **k): pass
    def get_total_portfolio_value(self): return 10000.0
    def get_usdt_balance(self): return 10000.0
    def get_current_position(self, symbol): return 0.0
    def round_quantity(self, symbol, q): return round(q, 3)
    def min_notional(self, symbol): return 5.0
    def get_ticker_price(self, symbol): return 65000.0
    def place_market_order(self, symbol, side, qty, reduce_only=False):
        self.orders.append((symbol, side, qty)); return {"orderId": 1, "status": "FILLED"}
    def cancel_all_orders(self, symbol): return []

class StubGraph:
    # returns a fixed modulator output: mult=1.4, eff_w=0.5
    def propagate_with_modulator(self, coin, date):
        mp = {"coin": coin, "llm_multiplier": 1.4, "effective_weight": 0.5,
              "position": -999.0, "regime": "bull", "llm_uncertainty": 0.1}
        return ({}, mp, {"coin": coin, "direction": "long", "magnitude": 0.2}, "ok")

def _seed_quant_db(db, cycle_id):
    j = Journal(db); j.log_cycle_start(cycle_id, git_sha="x")
    preds_df = pd.DataFrame([
        {"coin": "bitcoin", "horizon": 7,  "prediction": 0.03, "ref_price": 65000.0, "bundle_route": "bitcoin_78f"},
        {"coin": "bitcoin", "horizon": 14, "prediction": 0.05, "ref_price": 65000.0, "bundle_route": "bitcoin_78f"},
    ])
    j.record_predictions(cycle_id=cycle_id, preds_df=preds_df); j.close()

def test_loop_composes_and_executes_on_hybrid_only(tmp_path, monkeypatch):
    quant_dir = tmp_path / "data"; quant_dir.mkdir()
    hybrid_dir = tmp_path / "data-hybrid"
    _seed_quant_db(str(quant_dir / "trade_journal.db"), "2026-06-11")
    monkeypatch.setenv("HYBRID_BINANCE_API_KEY", "k")
    monkeypatch.setenv("HYBRID_BINANCE_API_SECRET", "s")
    monkeypatch.setenv("HYBRID_DATA_DIR", str(hybrid_dir))
    monkeypatch.setenv("QUANT_DATA_DIR", str(quant_dir))
    monkeypatch.setenv("COIN_UNIVERSE", "bitcoin")
    # seed an OHLCV cache the sizer can read for bitcoin
    _seed_ohlcv_cache(hybrid_dir, "BTCUSDT")  # helper writes 60-bar parquet

    fake_ex = FakeExchange()
    res = hybrid_runner.run_hybrid_cycle(
        cycle_id="2026-06-11", dry_run=False,
        _exchange=fake_ex, _graph=StubGraph(),
    )
    assert res.status == "ok"
    # an order was placed on the hybrid (fake) exchange
    assert len(fake_ex.orders) >= 1
    # hybrid journal got a trade row; quant journal untouched (still 0 trades)
    import sqlite3
    qn = sqlite3.connect(str(quant_dir / "trade_journal.db")).execute(
        "SELECT COUNT(*) FROM trades").fetchone()[0]
    assert qn == 0
```

(Provide `_seed_ohlcv_cache` in the test file: write a 60-row parquet to `<hybrid_dir>/ohlcv_cache/BTCUSDT_1d.parquet` with Date/Open/High/Low/Close/Volume, matching the runner's cache path at `runner.py:373`.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/live/test_hybrid_runner_loop.py -v`
Expected: FAIL (loop not implemented; `_exchange`/`_graph` params unknown).

- [ ] **Step 3: Implement the per-coin loop**

Add the `_exchange`/`_graph` injection params (default `None` → build real `ExchangeClient(acct...)` and `TradingAgentsGraph(selected_analysts=HYBRID_ANALYSTS, config=build_hybrid_config(...))`), then the loop:

```python
# (inside run_hybrid_cycle, replacing the "--- per-coin loop ---" comment)
from tradingagents.execution.live import sizer, stops
from tradingagents.execution.live import risk as live_risk
from tradingagents.execution.live.config import to_binance_symbol
from tradingagents.execution.live.hold_sizer import HoldState
from tradingagents.execution.live.hybrid_io import read_cycle_predictions
from tradingagents.execution.live.hybrid_base import derive_base
from tradingagents.execution.live.hybrid_compose import (
    build_hybrid_config, extract_modulator_outputs, compose_final,
    stage_quant_preds, HYBRID_ANALYSTS,
)
import pandas as pd

cfg = config.load_config()
cfg_dict = dict(
    horizons=cfg.horizons, symmetric=cfg.symmetric, target_vol=cfg.target_vol,
    kelly_fraction=cfg.kelly_fraction, max_leverage=cfg.max_leverage,
    vol_lookback=cfg.vol_lookback, vol_cap_pct=cfg.vol_cap_pct,
    confidence_ref_return=cfg.confidence_ref_return, trend_sma=cfg.trend_sma,
    trend_multiplier=cfg.trend_multiplier, min_hold=cfg.min_hold,
    early_exit_loss=cfg.early_exit_loss,
)
rows, preds = read_cycle_predictions(acct.quant_db_path, cycle_id)
if not preds:
    return CycleResult(cycle_id=cycle_id, status="no_quant_cycle", n_executed=0,
                       error_msg=f"no predictions for {cycle_id} in quant journal")

staged = stage_quant_preds(rows, date=cycle_id, out_dir=data_dir / "cycle_preds" / cycle_id)
ex = _exchange or _build_exchange(acct)
graph = _graph or _build_graph(str(staged))
j = journal.Journal(str(data_dir / "trade_journal.db"))
try:
    j.log_cycle_start(cycle_id, git_sha="hybrid")
    portfolio_before = float(ex.get_total_portfolio_value())
    asof = (datetime.now(timezone.utc).date()).isoformat()
    weights = config.compute_portfolio_weights(list(preds.keys()))
    for coin in preds:
        symbol = to_binance_symbol(coin)
        cache = data_dir / "ohlcv_cache" / f"{symbol}_1d.parquet"
        history = pd.read_parquet(cache) if cache.exists() else pd.DataFrame()
        prev = j.get_hold_state(coin)
        prev_state = HoldState(
            current_dir=prev["current_dir"] if prev else 0,
            bars_held=prev["bars_held"] if prev else 0,
            entry_price=prev["entry_price"] if prev else 0.0,
            entry_base=prev["entry_base"] if prev else 0.0,
        )
        base, new_state, sz = derive_base(
            coin=coin, prediction=preds[coin], price_history=history,
            prev_state=prev_state, cfg=cfg_dict, asof=asof,
        )
        if sz is None:
            continue
        # modulator (gpt-4o-mini); degrade to pure quant on any failure
        try:
            _state, mp, _qs, _narr = graph.propagate_with_modulator(coin, cycle_id)
        except Exception as e:
            logger.warning("modulator failed for %s: %s; pure quant", coin, e)
            mp = None
        mult, eff_w = extract_modulator_outputs(mp)
        final_fraction = compose_final(base=base, multiplier=mult, effective_weight=eff_w)
        j.upsert_hold_state(coin=coin, current_dir=new_state.current_dir,
                            bars_held=new_state.bars_held, entry_price=new_state.entry_price,
                            entry_base=new_state.entry_base, entry_cycle=cycle_id)
        j.log_sizing(cycle_id=cycle_id, coin=coin, realized_vol=sz.realized_vol,
                     target_vol=cfg.target_vol, kelly=cfg.kelly_fraction,
                     confidence=sz.confidence, base_size=sz.base_size,
                     leverage=sz.leverage, sma30_multiplier=sz.sma_multiplier,
                     final_size_notional=final_fraction)
        # convert to qty and execute (mirror runner.py:576-758 on the hybrid acct)
        target_qty = sizer.target_position_qty(
            size_fraction=final_fraction, portfolio_value=portfolio_before,
            weight=weights[coin], ref_price=preds[coin]["ref_price"])
        try:
            current = float(ex.get_current_position(symbol))
        except Exception:
            current = 0.0
        delta = target_qty - current
        if abs(delta) < 1e-8:
            continue
        side = "BUY" if delta > 0 else "SELL"
        qty = ex.round_quantity(symbol, abs(delta))
        price = preds[coin]["ref_price"]
        if qty * price < ex.min_notional(symbol) and abs(current) < 1e-9:
            continue  # below MIN_NOTIONAL for an opening order
        if dry_run:
            continue
        order = ex.place_market_order(symbol, side, qty)
        n_executed += 1
        # stop: 3% price-based, on the resulting net position
        net = current + (qty if side == "BUY" else -qty)
        if abs(net) > 1e-9:
            stop_side = "SELL" if net > 0 else "BUY"
            stop_price = price * (1 - cfg.stop_loss_pct) if net > 0 else price * (1 + cfg.stop_loss_pct)
            stop_id, _status = stops.arm_stop_loss(ex, symbol=symbol, net_position=net,
                                                   stop_price=stop_price, stop_side=stop_side)
        else:
            stop_id = None
        j.log_trade(cycle_id=cycle_id, coin=coin, side=side, qty=qty,
                    entry_price=price, exit_price=0.0, pnl=0.0, fees=0.0,
                    slippage=0.0, order_id=str(order.get("orderId", "")),
                    stop_loss_id=str(stop_id or ""), status="executed")
    j.log_cycle_end(cycle_id, status="ok")
    return CycleResult(cycle_id=cycle_id, status="ok", n_executed=n_executed)
finally:
    j.close()
```

Add the two builders:
```python
def _build_exchange(acct):
    from tradingagents.execution.exchange import ExchangeClient
    return ExchangeClient(api_key=acct.api_key, api_secret=acct.api_secret, testnet=True)

def _build_graph(quant_pred_dir: str):
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.execution.live.hybrid_compose import build_hybrid_config, HYBRID_ANALYSTS
    return TradingAgentsGraph(selected_analysts=HYBRID_ANALYSTS,
                              config=build_hybrid_config(quant_pred_dir=quant_pred_dir))
```
(Note: `testnet=True` is hard-pinned — the hybrid bot is testnet-only for the thesis A/B.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/execution/live/test_hybrid_runner_loop.py -v`
Expected: PASS — order on the fake exchange, hybrid journal has the trade, quant journal `trades` count still 0.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/hybrid_runner.py tests/execution/live/test_hybrid_runner_loop.py
git commit -m "feat(hybrid): per-coin modulate+compose+execute loop on second account"
```

### Task 3.4: CLI entrypoint + risk gates + kill/resume

**Files:**
- Modify: `tradingagents/execution/live/hybrid_runner.py`
- Test: `tests/execution/live/test_hybrid_runner_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/live/test_hybrid_runner_cli.py
import subprocess, sys

def test_cli_dry_run_exits_zero(tmp_path, monkeypatch):
    env = dict(**__import__("os").environ)
    env.update(HYBRID_BINANCE_API_KEY="k", HYBRID_BINANCE_API_SECRET="s",
               HYBRID_DATA_DIR=str(tmp_path), QUANT_DATA_DIR=str(tmp_path),
               COIN_UNIVERSE="bitcoin")
    # no quant cycle seeded -> status no_quant_cycle -> exit code 1
    r = subprocess.run([sys.executable, "-m", "tradingagents.execution.live.hybrid_runner",
                        "--once", "--dry-run", "--cycle-id", "2026-06-11"],
                       capture_output=True, env=env)
    assert r.returncode in (0, 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/live/test_hybrid_runner_cli.py -v`
Expected: FAIL (`__main__` not wired; module not runnable).

- [ ] **Step 3: Add `main()` + `--kill-all`/`--resume`** (mirror `runner.py:973-1006` + `kill_all`, but on the hybrid account/data dir)

```python
def kill_all() -> None:
    acct = load_hybrid_account()
    data_dir = Path(acct.data_dir)
    halt.write_halt("operator --kill-all (hybrid)", data_dir=data_dir)
    ex = _build_exchange(acct)
    for coin in config.load_config().coin_universe:
        symbol = config.to_binance_symbol(coin)
        try: ex.cancel_all_orders(symbol)
        except Exception: pass
        try:
            pos = ex.get_current_position(symbol)
            if pos: ex.place_market_order(symbol, "SELL" if pos > 0 else "BUY", abs(pos))
        except Exception: pass


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    p = argparse.ArgumentParser(description="TradingAgents hybrid live cycle")
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--cycle-id", default=None)
    p.add_argument("--kill-all", action="store_true")
    p.add_argument("--resume", action="store_true")
    args = p.parse_args()
    if args.resume:
        acct = load_hybrid_account()
        halt.clear_halt(data_dir=Path(acct.data_dir)); sys.exit(0)
    if args.kill_all:
        kill_all(); sys.exit(0)
    res = run_hybrid_cycle(cycle_id=args.cycle_id, dry_run=args.dry_run)
    sys.exit(0 if res.status == "ok" else 1)


if __name__ == "__main__":
    main()
```

Also add the daily-loss / drawdown / max-positions gates inside the loop using `live_risk.*` before placing orders (mirror `runner.py:478-611`), logging each via `j.log_risk_check(...)`. Keep it minimal: check `live_risk.check_max_positions(open_count, cfg.max_open_positions, opening_new=opening)` and `live_risk.check_leverage(final_fraction, cfg.max_leverage)`; on fail, skip the coin and `continue`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/execution/live/test_hybrid_runner_cli.py tests/execution/live/test_hybrid_runner_loop.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/hybrid_runner.py tests/execution/live/test_hybrid_runner_cli.py
git commit -m "feat(hybrid): CLI entrypoint, risk gates, kill-all/resume"
```

### Task 3.5: Full hybrid test suite green + no-regression check

- [ ] **Step 1: Run the whole hybrid suite + the quant runner suite**

Run:
```bash
python -m pytest tests/execution/live/ -v
```
Expected: all hybrid tests PASS and **all pre-existing live runner tests still PASS** (no regression — the hybrid added only new files; `runner.py` untouched).

- [ ] **Step 2: Confirm `runner.py` is unmodified**

Run: `git diff --stat live-v2.2.2 -- tradingagents/execution/live/runner.py`
Expected: **empty** (no changes to the quant runner).

- [ ] **Step 3: Commit any test fixups**

```bash
git add -A && git commit -m "test(hybrid): full live suite green, quant runner unmodified" || echo "nothing to commit"
```

---

## Phase 4 — Ops: second account secrets + systemd

### Task 4.1: systemd units `ta-hybrid-cycle.{service,timer}`

**Files:**
- Create: `deploy/systemd/ta-hybrid-cycle.service`
- Create: `deploy/systemd/ta-hybrid-cycle.timer`

- [ ] **Step 1: Write `ta-hybrid-cycle.service`** (mirror `ta-cycle.service`, hybrid module + hybrid data dir; ordered after the quant cycle)

```ini
[Unit]
Description=TradingAgents hybrid (quant×LLM) live cycle
After=ta-cycle.service
Wants=ta-cycle.service

[Service]
Type=oneshot
WorkingDirectory=/opt/tradingagents/repo
EnvironmentFile=/opt/tradingagents/secrets/.env.trading
EnvironmentFile=/opt/tradingagents/secrets/.env.hybrid
Environment=QUANT_DATA_DIR=/opt/tradingagents/data
Environment=HYBRID_DATA_DIR=/opt/tradingagents/data-hybrid
Environment=LOG_DIR=/opt/tradingagents/logs
ExecStart=/opt/tradingagents/venv/bin/python -m tradingagents.execution.live.hybrid_runner --once
```

- [ ] **Step 2: Write `ta-hybrid-cycle.timer`** (fire ~30 min after the quant cycle so UNIT 1 has written its predictions; the quant cycle at 00:05 UTC, retrain+predict typically completes within minutes, but 00:35 gives ample margin)

```ini
[Unit]
Description=Run TradingAgents hybrid cycle daily

[Timer]
OnCalendar=*-*-* 00:35:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
```

- [ ] **Step 3: Commit**

```bash
git add deploy/systemd/ta-hybrid-cycle.service deploy/systemd/ta-hybrid-cycle.timer
git commit -m "feat(hybrid): systemd units for ta-hybrid-cycle (After ta-cycle, 00:35 UTC)"
```

### Task 4.2: Secrets template + preflight extension

**Files:**
- Create: `deploy/secrets/.env.hybrid.example`
- Modify: `deploy/preflight.sh` (add a hybrid-secrets presence check, guarded so the quant preflight is unaffected)

- [ ] **Step 1: Write `.env.hybrid.example`**

```bash
# Second Binance TESTNET account for the hybrid bot (NEVER the quant account's keys)
HYBRID_BINANCE_API_KEY=
HYBRID_BINANCE_API_SECRET=
# gpt-4o-mini for the modulator graph
OPENAI_API_KEY=
```

- [ ] **Step 2: Add a hybrid check to `preflight.sh`** (only when invoked for the hybrid unit — gate on an env marker so the existing quant preflight path is byte-identical)

```bash
# --- hybrid preflight (only when HYBRID_DATA_DIR is set) ---
if [ -n "${HYBRID_DATA_DIR:-}" ]; then
  : "${HYBRID_BINANCE_API_KEY:?HYBRID_BINANCE_API_KEY missing}"
  : "${HYBRID_BINANCE_API_SECRET:?HYBRID_BINANCE_API_SECRET missing}"
  : "${OPENAI_API_KEY:?OPENAI_API_KEY missing for modulator}"
fi
```

- [ ] **Step 3: Commit**

```bash
git add deploy/secrets/.env.hybrid.example deploy/preflight.sh
git commit -m "feat(hybrid): hybrid secrets template + preflight guard"
```

### Task 4.3: Extend `deploy.sh` to install the hybrid unit + data dir

**Files:**
- Modify: `deploy/deploy.sh`

- [ ] **Step 1: Add hybrid provisioning** (create `data-hybrid`, copy the two unit files, `daemon-reload`, enable the timer). Mirror however `deploy.sh` already installs `ta-cycle`. Do not enable the timer until the dry-run (Phase 6) passes — add a `--enable-hybrid` flag that gates `systemctl enable --now ta-hybrid-cycle.timer`.

- [ ] **Step 2: Commit**

```bash
git add deploy/deploy.sh
git commit -m "feat(hybrid): deploy.sh installs hybrid unit + data dir (gated enable)"
```

---

## Phase 5 — Comparison reporting (extend existing)

### Task 5.1: Quant-vs-hybrid comparison in the weekly rebacktest

**Files:**
- Modify: `tradingagents/execution/live/rebacktest.py` (or wherever `compute_live_metrics` lives)
- Test: `tests/execution/live/test_hybrid_comparison.py`

- [ ] **Step 1: Write the failing test** — given two journals with portfolio snapshots, `compare_quant_hybrid(quant_db, hybrid_db, coins)` returns `{quant: {sharpe,ret,maxdd}, hybrid: {...}, delta: {...}}` for the full book and the BTC+ETH sleeve.

```python
# tests/execution/live/test_hybrid_comparison.py
from tradingagents.execution.live.rebacktest import compare_quant_hybrid
# seed two journals with portfolio_snapshots equity curves, assert delta sign + keys
def test_compare_returns_delta_keys(tmp_path):
    # ... seed quant_db and hybrid_db with log_portfolio_snapshot over N days ...
    out = compare_quant_hybrid(str(quant_db), str(hybrid_db), coins=["bitcoin", "ethereum"])
    assert {"quant", "hybrid", "delta"}.issubset(out)
    assert {"sharpe", "ret", "maxdd"}.issubset(out["delta"])
```

- [ ] **Step 2-4:** Run-fail → implement `compare_quant_hybrid` (read `portfolio_snapshots` from each DB, compute Sharpe/return/maxDD over the overlapping date window, diff) → run-pass. Reuse the existing metric helpers in `rebacktest.py` (the same ones `compute_live_metrics` uses) to avoid DRY violations.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/rebacktest.py tests/execution/live/test_hybrid_comparison.py
git commit -m "feat(hybrid): quant-vs-hybrid comparison metrics in rebacktest"
```

### Task 5.2: Surface the comparison in the monitor UI

**Files:**
- Modify: the monitor FastAPI app (`project_live_monitor_ui`) + its template

- [ ] **Step 1:** Add a read-only `/compare` route that calls `compare_quant_hybrid` against the two journal DBs and renders the Δ table (BTC+ETH sleeve + full 8). Reuse the existing dashboard's DB-path resolution; add `HYBRID_DATA_DIR` to its config.
- [ ] **Step 2:** Manual check: `curl localhost:<port>/compare` returns the table. Commit.

```bash
git add <monitor files> && git commit -m "feat(hybrid): monitor /compare quant-vs-hybrid panel"
```

---

## Phase 6 — Deploy, dry-run, go-live

Not TDD — operational checklist. Run each step, paste output into the PR/notes.

- [ ] **Step 1: Provision the second testnet account.** Create a separate Binance **testnet** futures account, generate API key/secret, fund via the testnet faucet to match the quant account's `INITIAL_CAPITAL`. Put keys + `OPENAI_API_KEY` in `/opt/tradingagents/secrets/.env.hybrid` (chmod 600).

- [ ] **Step 2: Ship the branch.** Merge `feature/hybrid-v5-live-deploy` → tag `live-v2.3.0`. `git push origin live-v2.3.0`.

- [ ] **Step 3: Deploy.** On the VPS: pull the tag, `deploy/deploy.sh` (creates `data-hybrid`, installs the unit — **without** `--enable-hybrid`). Verify checkpoints present: `ls /opt/tradingagents/data/checkpoints/regime_hmm_*.pkl` shows all 8 coins.

- [ ] **Step 4: Dry-run on the VPS** (no orders):
```bash
sudo systemctl start ta-cycle.service          # ensure today's quant preds exist
QUANT_DATA_DIR=/opt/tradingagents/data HYBRID_DATA_DIR=/opt/tradingagents/data-hybrid \
  /opt/tradingagents/venv/bin/python -m tradingagents.execution.live.hybrid_runner --once --dry-run
```
Expected: log shows per-coin `base`, `mult`, `eff_w`, `final` for all 8 coins; status `ok`; **zero** orders; hybrid journal has `sizing` rows; quant journal `trades` count unchanged.

- [ ] **Step 5: Verify isolation.** Confirm the dry-run wrote only under `data-hybrid/` and touched no quant file: `git -C /opt/tradingagents/repo status` clean; `sqlite3 /opt/tradingagents/data/trade_journal.db "SELECT COUNT(*) FROM trades WHERE cycle_id=date('now')"` unchanged.

- [ ] **Step 6: Go live.** `deploy/deploy.sh --enable-hybrid` → `systemctl enable --now ta-hybrid-cycle.timer`. Confirm `systemctl list-timers | grep ta-hybrid` shows the next 00:35 UTC fire. Start the common-window clock (note the date).

- [ ] **Step 7: Wire the weekly comparison.** Confirm the existing `ta-rebacktest.timer` job now also emits `compare_quant_hybrid` output (or add a `ta-hybrid-compare` step). Check the monitor `/compare` panel renders.

- [ ] **Step 8: Day-1 health check.** After the first live hybrid cycle: hybrid heartbeat fresh, `n_executed` sane, both books moving independently, no quant regression (quant heartbeat + trades unaffected).

---

## Self-Review notes (author)

- **Spec coverage:** §5.1 hybrid_runner → Tasks 3.2–3.4; §5.2 base re-derive → Tasks 1.4, 2.2, 3.3; §5.3 staging → Task 1.3; §5.4 config pins → Task 2.1; §5.5 compose+execute → Tasks 1.1–1.2, 3.3; §5.6 isolation → Tasks 3.1, 4.1–4.3, 6.5; §5.7 pre-train → Phase 0; §5.8 reporting → Phase 5. All covered.
- **No-regression** is enforced structurally (new files only) and verified twice: Task 3.5 Step 2 (`git diff --stat` empty for `runner.py`) and Phase 6 Step 5.
- **Composition correctness:** Task 1.2 discards `position`; Task 1.1 implements the exact §23 formula; verified against `ablate_hybrid.py:73`.
- **Gated cost:** Task 0.2 has an explicit STOP gate before any LLM spend; identity fallback documented.
- **Open risk:** the modulator graph's per-coin latency × 8 coins must finish before the next day — the 00:35 UTC start + daily bar gives ~23h of slack; acceptable. If a single graph run hangs, the cycle's `try/except` returns `error` and the heartbeat still fires (dead-man monitor covers a missed cycle).
