# V5 MIX TP/SL Parameter Sensitivity Sweep — Design

**Date:** 2026-05-19
**Status:** Draft, pre-implementation
**Scope:** Research-only backtest extension. No live trading change.
**Repo:** `TradingAgents` (V5 MIX production strategy)

## 1. Motivation

V5 MIX is the canonical production strategy (THESIS §20): 4-coin equal-weight portfolio (BTC/ETH/BNB/SOL), per-coin feature routing, vol-targeted Kelly sizing, SMA30 trend filter. Validated SR +3.25 / +787% / -4.9% max DD over 4.5-yr walk-forward.

The current V5 backtest engine (`scripts/baseline_strategy_v2.py:run_coin_backtest`) already includes a **3% close-to-close equity-drawdown stop-loss** and a **1.5% early-exit-on-signal-change**. **No take-profit exists** anywhere in the backtest or live stack.

This sweep answers: **does varying SL / early-exit / adding TP change V5 MIX risk-adjusted return?** Framed as sensitivity analysis, not optimization — output is a heatmap, not a tuned parameter recommendation.

## 2. Out of Scope

- Intrabar OHLC SL/TP (low/high touches inside daily bar) — deferred to follow-up "approach B" if results warrant
- ATR-scaled SL/TP — deferred to "approach C"
- Per-coin parameter optimization (one tuple per coin) — risks overfit on single WF window
- Live `src_live/` / `tradingagents/execution/` SL/TP parameter change — research output only
- Trailing stops in backtest (`update_trailing_stop` exists in live, not backtest)
- Statistical accept/reject test — no acceptance threshold; pure exploration

## 3. Architecture

### 3.1 Engine extension

Single function modified: `run_coin_backtest` in `scripts/baseline_strategy_v2.py`. Add `take_profit: float = 0.0` parameter (default = current behaviour, no TP, bit-identical to today). Mirror existing SL logic right after the SL block (engine line ~135-138):

```python
# Existing SL block:
if target_pos != 0 and entry_equity > 0:
    trade_dd = (entry_equity - new_equity) / entry_equity
    if trade_dd >= stop_loss:
        target_pos = 0.0
    # NEW TP block (mirror):
    trade_up = (new_equity - entry_equity) / entry_equity
    if take_profit > 0 and trade_up >= take_profit:
        target_pos = 0.0
```

TP semantics:
- Close-to-close, equity-drawup measured from `entry_equity` snapshot (same anchor as SL)
- Flatten at next bar (same exit mechanic as SL)
- `take_profit = 0` disables TP — must produce bit-identical equity curve to today's engine (regression guard, see §6)

### 3.2 Sweep harness

New script: `scripts/v5_mix_sltp_sweep.py`. Reuses portfolio assembly from `scripts/baseline_v5_mix.py` (per-coin routing → equal-weight combine). Iterates over the (SL, EE, TP) grid; per cell runs 4 coin backtests then combines.

Single global tuple per cell (same `stop_loss`, `early_exit_loss`, `take_profit` for all 4 coins). Other V5 parameters held at production defaults.

## 4. Sweep Grid

| Param | Values | Count |
|---|---|---|
| `stop_loss` | off, 0.005, 0.01, 0.015, 0.02, **0.03** (V5 default), 0.05, 0.07, 0.10 | 9 |
| `early_exit_loss` | off, 0.005, 0.01, **0.015** (V5 default), 0.02, 0.03 | 6 |
| `take_profit` | **off** (V5 default), 0.01, 0.02, 0.03, 0.05, 0.08, 0.12 | 7 |

Total cells: 9 × 6 × 7 = **378**. Each cell = 4 coin backtests × 4.5-yr WF. Estimated wall-clock ~30s/cell → ~3h total on workstation. No parallelism in v1; add `joblib.Parallel` if too slow.

V5 baseline cell = `(SL=0.03, EE=0.015, TP=off)`. Must appear in grid and reproduce published SR 3.25.

`off` encoded as `0.0` for SL/TP (existing convention), large sentinel (e.g. `1.0`) for EE — verify EE handling for "disabled" path.

## 5. Outputs

Written to `data/v5_sltp_sweep/`:

| Artifact | Format | Contents |
|---|---|---|
| `results.csv` | Flat CSV, 1890 rows | One row per (SL, EE, TP) × scope (portfolio + 4 coins) = 378×5. Cols: `sl`, `ee`, `tp`, `scope`, `sharpe`, `total_return`, `max_dd`, `calmar`, `n_trades`, `win_rate`, `profit_factor`, `halted` |
| `top20.md` | Markdown table | Top 20 cells by **portfolio** SR descending, with full metric row each. V5 baseline row highlighted |
| `heatmaps/sr_sl_x_tp__ee_{ee}.png` | PNG × 6 | SR heatmap (SL × TP grid) at each fixed EE level. V5 baseline cell marked with cross |
| `heatmaps/dd_sl_x_tp__ee_{ee}.png` | PNG × 6 | Max DD heatmap (same layout) |
| `summary.json` | JSON | Run metadata: grid, V5 baseline SR/DD reproduction, best cell, sweep wall-clock, git SHA |

## 6. Test Plan

Unit tests in `tests/strategies/test_sltp_sweep.py`:

1. **TP trigger** — synthetic price/position series; verify TP fires when `trade_up >= TP`, position flattens next bar
2. **TP disabled regression** — `take_profit=0` produces bit-identical `equity` array vs current engine on canonical BTC fixture. **Hard equality assertion** (not approx)
3. **SL still works alongside TP** — both flags active, verify SL still triggers on losing trades
4. **Engine signature backward-compat** — calling `run_coin_backtest` without `take_profit` kwarg works (default 0.0)

Integration tests:

5. **V5 baseline reproduction** — sweep cell `(0.03, 0.015, 0.0)` produces portfolio SR within ±0.01 of published 3.25 over the canonical 4.5-yr window. Hard failure if drift > 0.05
6. **Smoke** — random 5-cell subsample completes end-to-end before launching full 378-cell sweep

## 7. Reporting

Add §24 to `THESIS_NARRATIVE.md`: "TP/SL Parameter Sensitivity Sweep". Sections:

1. Methodology — grid, global-tuple choice, scope limits, baseline engine quoted
2. V5 baseline reproduction (sanity check)
3. Heatmap figures — SR(SL × TP) at EE=0.015 (main), DD(SL × TP) at EE=0.015
4. Top-20 table — best cells by portfolio SR
5. Discussion — is SR landscape **flat** (V5 robust to SL/TP choice) or **peaked** (SL/TP material)?
6. Limitations — close-only assumption, single-window result, no out-of-sample param validation, no live deployment recommendation

## 8. Reproduce Commands

```bash
# Full sweep (~3h)
python scripts/v5_mix_sltp_sweep.py \
    --start 2021-11-07 --end 2026-04-15 \
    --output-dir data/v5_sltp_sweep

# Smoke (5 random cells)
python scripts/v5_mix_sltp_sweep.py --smoke --n-smoke 5

# Single cell (regression check)
python scripts/v5_mix_sltp_sweep.py --sl 0.03 --ee 0.015 --tp 0.0 --single-cell
```

## 9. Acceptance

This is a **research deliverable**, not a feature gate. Done when:

- 378-cell sweep runs to completion without errors
- V5 baseline reproduction within tolerance
- All 6 tests pass
- `results.csv`, `top20.md`, 12 heatmap PNGs, `summary.json` written
- §24 added to `THESIS_NARRATIVE.md` with figures embedded
- No live trading parameter change made

## 10. Follow-ups (Conditional)

Triggered only if sweep shows SR landscape is **peaked**, not flat:

- **Approach B (intrabar OHLC)** — add daily OHLC into engine, check `low <= entry*(1-SL)` / `high >= entry*(1+TP)` within bar. Pessimistic SL-before-TP on same-bar collision. Validates against crypto wick risk.
- **Approach C (ATR-scaled)** — express SL/TP as `k × ATR(14)` not fixed percent. Adapts to vol regime.
- **Live parameter update** — only if both A and B agree on improvement. Requires separate spec covering `src_live/config.py` change, deployment, monitoring.
