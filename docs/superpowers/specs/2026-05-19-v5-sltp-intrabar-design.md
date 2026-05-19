# V5 MIX TP/SL Intrabar OHLC Sweep (Approach B) — Design

**Date:** 2026-05-19
**Status:** Draft, follow-up to §29 (close-only sweep)
**Scope:** Research-only. No live trading change.
**Repo:** TradingAgents
**Branch:** `feature/v5-sltp-sweep-intrabar`
**Predecessor:** `docs/superpowers/specs/2026-05-19-v5-sltp-sweep-design.md`

## 1. Motivation

§29 close-only sweep found best cell at SL=10%, EE=disabled, TP=off → SR +3.335
/ DD 3.6% (vs baseline +3.178 / 4.9%). The §29 limitations section flagged
**intrabar wick risk** as the dominant unaddressed unknown: close-only SL/TP
fires on bar close, but a real intrabar SL would fill when `low ≤ entry × (1−SL%)`,
regardless of where the bar closes. Crypto's long wicks could systematically
trigger tight SLs that close-only logic ignores — eroding or reversing the
+0.157 SR delta.

This sweep re-runs the §29 grid with **intrabar OHLC** SL/TP checks to
quantify wick impact. Acceptance criterion (locked by stakeholder):
**best cell SR delta vs the new intrabar baseline must remain ≥ +0.15**.
If yes, the §29 finding is robust and we proceed to walk-forward parameter
split (separate spec). If no, the close-only result is wick-fragile and
should not motivate any live change.

## 2. Out of Scope

- ATR-scaled SL/TP (approach C)
- Per-coin parameter optimisation
- Live `src_live/` / `tradingagents/execution/` parameter change — even if B
  confirms A, walk-forward validation is required first
- Statistical test (bootstrap CI / DSR) — deferred to a separate follow-up
- Slippage on SL/TP fills beyond the existing `slippage` parameter — fills
  assumed at the trigger price exactly

## 3. Architecture

### 3.1 Engine extension

Single function modified: `run_coin_backtest` in `scripts/baseline_strategy_v2.py`.
Add three optional parameters:

- `intrabar: bool = False` — opt-in switch. Default `False` preserves §29 / close-only behaviour bit-identically.
- `highs: np.ndarray | None = None` — per-bar highs, required when `intrabar=True`
- `lows: np.ndarray | None = None` — per-bar lows, required when `intrabar=True`

When `intrabar=True`, the engine tracks **entry_price** (in addition to existing
`entry_equity`) at every position open. On each bar, BEFORE applying the
close-to-close `gross_ret`, check intrabar fills:

```
if position == long and entry_price > 0:
    sl_price = entry_price * (1 - stop_loss) if stop_loss > 0 else 0
    tp_price = entry_price * (1 + take_profit) if take_profit > 0 else inf
    hit_sl = (sl_price > 0 and low <= sl_price)
    hit_tp = (take_profit > 0 and high >= tp_price)
    if hit_sl and hit_tp:                    # same-bar collision → SL-first pessimistic
        fill_price = sl_price
        exit_reason = "SL"
    elif hit_sl:
        fill_price = sl_price
        exit_reason = "SL"
    elif hit_tp:
        fill_price = tp_price
        exit_reason = "TP"
    else:
        fill_price = None
```
(Symmetric inversion for short positions: `sl_price = entry_price * (1 + stop_loss)`,
`tp_price = entry_price * (1 - take_profit)`, hit_sl on `high >= sl_price`,
hit_tp on `low <= tp_price`. Same-bar collision still SL-first.)

When an intrabar fill happens at `fill_price`:
- The bar's gross return becomes `position × (fill_price − p_prev) / p_prev`
  (truncated at the fill, not the close)
- The bar's `target_pos` is set to `0` (flatten next bar; same one-shot semantics as close-only)
- `entry_price` reset to `0`

The existing close-to-close SL/TP block (added in §29) remains active so that
a position whose `entry_price` was not set (legacy path) still uses the
equity-drawdown safeguard. With `intrabar=True` the price-based check fires
first on most bars, making the close-only check a fallback.

### 3.2 Position-builder unchanged

`build_positions_with_hold` does NOT change. EE remains close-only because EE
is a signal-flip-confirmation rule, not a price stop — it depends on
cumulative cumulative bar return + signal change, both close-only quantities.
This is intentional: EE keeps the same semantics across A and B, so the
"EE-disabled dominates" finding from A is testable on an apples-to-apples
basis in B.

### 3.3 Sweep harness extension

New script: `scripts/v5_mix_sltp_sweep_intrabar.py`. Mirrors
`v5_mix_sltp_sweep.py` but:
- Loads OHLC `high` / `low` columns alongside `close` in `_load_coin_data`
- Passes `intrabar=True, highs=…, lows=…` to `run_coin_backtest` per cell
- Output dir defaults to `data/v5_sltp_sweep_intrabar/`
- Records `n_intrabar_sl`, `n_intrabar_tp` counts per cell (new diagnostic columns)
- Reuses the per-EE position cache from §29 (positions never depend on intrabar)

## 4. Sweep Grid

**Identical to §29** — same 9 × 6 × 7 = 378 cells. Apples-to-apples comparison
demands grid parity.

| Parameter | Values |
|---|---|
| `stop_loss` | off, 0.5%, 1%, 1.5%, 2%, **3%** (V5), 5%, 7%, 10% |
| `early_exit_loss` | disabled, 0.5%, 1%, **1.5%** (V5), 2%, 3% |
| `take_profit` | **off** (V5), 1%, 2%, 3%, 5%, 8%, 12% |

Wall clock: ~15-30 s expected (intrabar check adds ~2× to engine eval, dominated by data load).

## 5. Outputs

`data/v5_sltp_sweep_intrabar/`:

| Artifact | Contents |
|---|---|
| `results.csv` | 378 × 5 = 1890 rows; columns include diagnostic `n_intrabar_sl`, `n_intrabar_tp` |
| `summary.json` | Grid + intrabar baseline cell + best cell + delta-vs-§29 + git SHA |
| `top20.md` | Top-20 portfolio cells with the diagnostic columns |
| `heatmaps/` | 12 PNGs (6 EE × 2 metrics: SR, DD) — same format as §29 |
| `comparison.md` | Side-by-side §29 close-only vs B intrabar for the top-20 cells (key deliverable) |
| `sweep.log` | tee'd run output |

## 6. Test Plan

`tests/strategies/test_sltp_sweep_intrabar.py`:

1. **`intrabar=False` is bit-identical to §29** — call engine without `highs`/`lows`, confirm `assert_array_equal` on equity vs prior path (regression guard for the most-important property)
2. **Intrabar SL fires** — synthetic 10-bar series, `prices[5] = entry × 0.94` with `low[5] = entry × 0.94`, `SL=0.05` → fill at `entry × 0.95`, NOT at `entry × 0.94` (price truncation correct)
3. **Intrabar TP fires** — symmetric on rising path
4. **Same-bar collision: SL fires, TP does not** — `low[5] = entry × 0.94, high[5] = entry × 1.10`, both SL=5% and TP=8% configured. Assertion: exit at SL price `entry × 0.95`, `exit_reason == "SL"` (pessimistic)
5. **Intrabar required arrays** — calling `intrabar=True` without `highs` raises `ValueError` (not silent NaN cascade)
6. **`@pytest.mark.slow` intrabar baseline reproduction** — close-only cell on 4.5-yr WF still produces SR ≈ 3.178 ± 0.05 (Task 4 regression guard)
7. **`@pytest.mark.slow` intrabar baseline reproduction** — intrabar baseline cell (SL=0.03, EE=0.015, TP=off, intrabar=True) produces a sensible SR (no exception, SR in [+2.5, +3.5] range — wide tolerance because this is a NEW value we're discovering, not reproducing)

## 7. Acceptance Criterion

Locked by stakeholder:

> **Best cell SR delta vs intrabar baseline ≥ +0.15** (preserves §29 finding magnitude).

Where:
- Intrabar baseline = (SL=0.03, EE=0.015, TP=off, intrabar=True). Reproducible single-cell run.
- Best cell = highest-portfolio-SR cell in the intrabar 378-cell sweep.

**Outcomes:**

| Outcome | Action |
|---|---|
| Best intrabar cell ΔSR ≥ +0.15 AND best cell still has EE-disabled | **B confirms A.** Proceed to WF param split spec. |
| Best intrabar cell ΔSR ≥ +0.15 BUT best cell has EE-enabled | **B partially confirms A.** Document, then WF param split with smaller grid focused on EE on/off. |
| Best intrabar cell ΔSR < +0.15 | **B rejects A.** Stop. Document as a controlled negative result in THESIS §30. No WF split, no live change. |
| Best intrabar cell ΔSR < 0 (intrabar destroys alpha entirely) | **B kills A.** Same as above plus update memory + flag for thesis discussion. |

## 8. Reproduce Commands

```bash
# Full sweep (~30s)
python scripts/v5_mix_sltp_sweep_intrabar.py \
    --start 2021-11-07 --end 2026-04-15 \
    --output-dir data/v5_sltp_sweep_intrabar

# Single intrabar cell (regression check)
python -c "
import sys; sys.path.insert(0, '.')
import numpy as np, pandas as pd
from scripts.baseline_v5_mix import COSTS, DEFAULT_ROUTING, PROJECT_ROOT
from scripts.v5_mix_sltp_sweep_intrabar import run_coin_intrabar
rets = {c: run_coin_intrabar(c, PROJECT_ROOT/p, '2021-11-07', '2026-04-15',
                              early_exit_loss=0.015, sl=0.03, tp=0.0)
        for c, p in DEFAULT_ROUTING.items()}
df = pd.DataFrame(rets).dropna(); port = df.mean(axis=1)
print('intrabar baseline SR:', float(port.mean()/port.std()*np.sqrt(252)))
"

# Comparison view (after sweep done)
python scripts/v5_sltp_sweep_intrabar_compare.py
```

## 9. Reporting

### 9.1 THESIS_FINDINGS.md §30

Title: `## 30. V5 MIX TP/SL Intrabar OHLC Sweep — §29 Wick-Risk Validation (2026-05-19)`.

Body must include:
- Methodology (intrabar fill rules, SL-first collision)
- Intrabar baseline cell SR (new reproducible number)
- Best intrabar cell + ΔSR vs intrabar baseline
- Side-by-side table: top-5 cells from §29 vs same cells under intrabar
- Acceptance verdict (confirm / partial / reject)
- Decision: proceed to WF split (or stop)

### 9.2 §29 update (cross-reference)

Append a single line to §29 pointing forward: `**Follow-up:** §30 validates this
under intrabar OHLC rules; see verdict there.`

## 10. Acceptance for THIS Spec

Done when:
- Engine `intrabar` path implemented, bit-identical when disabled
- 378-cell intrabar sweep completes without errors
- All 7 tests pass
- `results.csv`, `summary.json`, `top20.md`, 12 heatmaps, `comparison.md` written
- THESIS §30 added with verdict + §29 cross-reference line
- If acceptance criterion met → branch tagged ready for WF spec; if not → branch tagged as controlled negative result, no WF work scheduled

## 11. Risks

1. **Position re-entry semantics under intrabar.** When SL fires intrabar at bar k, `target_pos = 0` for k. Bar k+1 re-evaluates `positions[k+1]`; if still long, re-enters at close. This is identical to §29 semantics — preserved deliberately for apples-to-apples.
2. **Same-bar collision rate.** If SL-first pessimistic systematically fires on uptrending bars where both SL and TP touched (low-then-high wick), TP may show artificially low contribution. Diagnostic columns `n_intrabar_sl` and `n_intrabar_tp` quantify this.
3. **SOL data starts 2020-08-11.** Sweep window 2021-11-07 onwards — no truncation needed.
4. **OHLCV cache freshness.** All 4 coins have data through 2026-04-14 (one day before sweep end). Confirmed via direct loader call.

## 12. Follow-ups (Conditional)

- **WF param split (spec #2):** Train SL/EE/TP params on 2021-11 → 2024-12, test OOS on 2025-01 → 2026-04. Only if B verdict = confirm.
- **Approach C (ATR-scaled SL/TP):** Deferred indefinitely.
- **Live param change spec:** Requires both B confirm AND WF OOS preserved.
