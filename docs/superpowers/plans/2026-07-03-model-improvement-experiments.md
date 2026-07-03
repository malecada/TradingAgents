# Prediction-Model Improvement Experiments — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Experiments E1–E3 are independent — they may run in any order or in parallel worktrees; E4/E5 are decision tasks.

**Goal:** Test three evidence-ranked improvements to the V5 MIX LGB prediction/sizing pipeline (return-space target, training-window-staggered ensemble, quantile-based confidence) and close two ship decisions (carry sleeve, regime overlay), each behind pre-registered do-no-harm gates.

**Architecture:** Every experiment follows the house pattern: a flag/param in the shared model code → regenerate predictions with `scripts/evaluate_models_multi.py` → portfolio backtest via `scripts/baseline_v5_mix.py` primitives → stationary-bootstrap ΔSR CI (`scripts/bootstrap_sharpe.py`) → verdict logged in `THESIS_FINDINGS.md`. No experiment touches live config until its gate passes.

**Tech Stack:** Python 3.13 (uv), LightGBM, pandas, existing backtest harness.

**Design doc:** `docs/superpowers/specs/2026-07-03-quant-first-sentiment-and-model-improvements-design.md` §4 (evidence table, incl. what NOT to retry: V3 re-attempts, seed ensembles, intraday stop changes, weight optimization).

## Global Constraints

- Repo `/home/malecada/master_thesis/TradingAgents`; one worktree per experiment, branches `exp/return-target`, `exp/window-ensemble`, `exp/quantile-confidence`, cut from `f979683`. `export TRADINGAGENTS_DATA_ROOT=/home/malecada/master_thesis/TradingAgents/data`. `uv sync --all-extras --python 3.13.13`.
- Evaluation window for all experiments: the standard 4.5-yr WF window used by `walkforward_v2.py` (read its `START/END` constants; do not invent a new window). Quick-look iterations may use the last 18 months; final verdicts use the full window.
- Baseline: regenerated same-window V5 MIX predictions with unmodified code (4-coin core is enough for verdicts: BTC/ETH/BNB/SOL; add satellites only for a passing candidate). Reference SR 3.18 (4-coin) is context, not the comparator — always compare like-for-like regenerated runs.
- Gates (pre-registered, per experiment): ship only if portfolio ΔSR bootstrap `p_pos ≥ 0.90` AND no coin's SR degrades with `p_neg ≥ 0.90` AND MaxDD not worse by >1pp. E2 has an additional primary metric (flip-rate) defined in its task.
- `tests/strategies/test_v2_sizing_golden.py` and `tests/regression/test_v2_unchanged.py` must stay green with all new flags at their defaults.
- Commit per task; results (JSON/CSV) land under `data/exp_{name}/`; writeups appended to `THESIS_FINDINGS.md`.

---

### Task E1: Return-space target (`target_mode="logret"`)

**Hypothesis (structural):** `LGBMRegressor` predicts the raw price level `prices_h{h}`; trees cannot output values outside the trained target range, so at new all-time highs the model is mechanically biased toward "down" — and MinMaxScaler on level features drifts in the expanding window. Predicting `log(P_{t+h}/P_t)` removes both. This is the highest-upside signal fix identified in the design review.

**Files:**
- Modify: `tradingagents/models/model_utils.py` (`data_transform`, lines ~257-371) — new param `target_mode: str = "level"`; when `"logret"`, target column becomes `np.log(prices.shift(-h) / prices)` (computed BEFORE the global t−1 shift, exactly where `prices_h{h}` is created today; keep the column name `prices_h{h}` so downstream selection is untouched, but store the mode in the frame attrs).
- Modify: `tradingagents/models/lgb_model.py` (`walk_forward_pooled` ~111-204, `fit_pooled_full`/`predict_pooled` ~237-324) — when mode is `"logret"`, inverse-transform predictions to level (`pred_level = ref_price * np.exp(pred)`) before writing CSVs, so every downstream consumer (`v2_sizing`, `baseline_v5_mix`) is untouched.
- Modify: `scripts/evaluate_models_multi.py` — `--target-mode` flag.
- Test: `tests/models/test_target_mode_logret.py`

**Interfaces:**
- Produces: prediction CSVs identical in schema to today's (`preds_lgb_h{7,14}.csv` with `ref_price`) — downstream code must not need changes. That invariant IS the design.

- [ ] **Step 1: Failing tests**

```python
# tests/models/test_target_mode_logret.py
import numpy as np, pandas as pd
from tradingagents.models.model_utils import data_transform

def _toy():
    idx = pd.date_range("2024-01-01", periods=60, freq="D")
    return pd.DataFrame({"prices": np.linspace(100, 200, 60)}, index=idx)

def test_logret_target_values():
    out = data_transform(_toy(), horizons=[7], target_mode="logret")
    p = _toy()["prices"]
    expected = np.log(p.shift(-7) / p)
    # align on the transformed frame's index; the t-1 feature shift must NOT hit the target
    assert np.allclose(out["prices_h7"].dropna().values, expected.reindex(out.index).dropna().values, atol=1e-9)

def test_level_mode_unchanged_default():
    a = data_transform(_toy(), horizons=[7])
    b = data_transform(_toy(), horizons=[7], target_mode="level")
    pd.testing.assert_frame_equal(a, b)

def test_last_h_rows_have_nan_target():  # regression: the ffill-mask bug must not resurrect
    out = data_transform(_toy(), horizons=[7], target_mode="logret")
    assert out["prices_h7"].tail(7).isna().all()
```

- [ ] **Step 2: FAIL run.** **Step 3: Implement** (respect the existing target-NaN handling — see `tests/models/test_data_transform_target_nan.py`). **Step 4: Green, incl. full `tests/models/`.**
- [ ] **Step 5: Inverse-transform in lgb_model** + unit test: fabricate a fitted-mode bundle, assert CSV-level predictions satisfy `pred_level == ref_price * exp(raw)` and DirAcc computation is unchanged in level space.
- [ ] **Step 6: Quick-look regen** (BTC+ETH, last 18 months, h7/h14, both modes) → compare DirAcc h7/h14 and, critically, DirAcc conditioned on `price_at_ATH` days (within 2% of running max). Expected signature if hypothesis holds: logret ≥ level overall AND markedly better on ATH days.
- [ ] **Step 7: Full-window regen + V5 portfolio A/B + bootstrap.** Verdict vs Global-Constraint gates. Write up (either way — a null kills a persistent "maybe" cheaply).
- [ ] **Step 8: Commit + report.**

---

### Task E2: Training-window-staggered prediction ensemble

**Hypothesis:** The vintage/PIT audit attributed 100% of walk-forward non-reproducibility to training-window sensitivity (16% signal flips per 3-week train-end shift) — the model is high-variance in the time dimension. Averaging predictions from K=3 models whose training sets end at offsets {0, −21, −42} days should cut signal variance without the (already disproven) seed-ensemble's mistake of resampling the wrong noise source. Primary metric is **stability**, secondary is SR.

**Files:**
- Modify: `tradingagents/models/lgb_model.py:walk_forward_pooled` — param `train_end_offsets: list[int] | None = None`; when set, per date fit one model per offset (train on rows `< cur_date - offset_days`) and emit the mean prediction (plus per-offset columns `pred_off{k}` for diagnostics).
- Modify: `scripts/evaluate_models_multi.py` — `--train-end-offsets 0,21,42`.
- Create: `scripts/exp_flip_rate.py` — flip-rate metric: run prediction generation twice with the whole evaluation grid shifted by 21 days; flip-rate = share of common dates where sign(pred−ref) differs between runs. (This reproduces the audit's measurement — read `docs`/THESIS §on vintage audit for the original recipe and match it.)
- Test: `tests/models/test_train_end_offsets.py` — toy frame, offsets [0, 5]: assert two models trained, mean emitted, offset-5 model's train set excludes the 5 newest days.

- [ ] **Step 1-3: TDD as above** (runtime guard: K=3 triples training cost — verify quick-look runtime acceptable before full window; if not, drop retrain cadence for the ensemble legs to weekly-refit, document the deviation).
- [ ] **Step 4: Quick-look** BTC+ETH 18mo: flip-rate baseline vs ensemble. Gate to continue: flip-rate reduction ≥ 30% relative AND quick-look SR not down by >0.2.
- [ ] **Step 5: Full window, 4 coins, V5 portfolio A/B + bootstrap.** Ship gates from Global Constraints, with the addition: flip-rate reduction must hold on the full window. Write up.

---

### Task E3: Quantile-LGB confidence for sizing

**Hypothesis:** ~90% of V5 alpha is sizing; the sizing input `confidence = clip(|pred−ref|/ref / 0.05, 0, 1)` is an uncalibrated constant-scaled heuristic. Three quantile models (α = 0.1/0.5/0.9) give a distribution: direction from q50, confidence from how far the interval clears zero — `confidence_q = clip((q50 − ref) / (q90 − q10), -1, 1)` magnitude (sign must agree with q50 direction; if the interval straddles ref widely, confidence collapses). Better-calibrated confidence should improve Kelly/vol-target allocation even with identical directional signals.

**Files:**
- Modify: `tradingagents/models/lgb_model.py` — `_build_lgb(objective="quantile", alpha=a)` variants; `walk_forward_pooled(quantiles=(0.1, 0.5, 0.9))` emits `pred` (=q50 level), `q10`, `q90` columns.
- Modify: `tradingagents/strategies/v2_sizing.py:generate_term_structure_signals` (~22-76) — optional `confidence_mode="quantile"` reading q-columns when present; default `"ref"` path byte-identical (golden tests).
- Modify: `scripts/evaluate_models_multi.py`, `scripts/baseline_v5_mix.py` — flags to thread the mode through.
- Test: `tests/models/test_quantile_lgb.py` (q10 ≤ q50 ≤ q90 on toy data ≥95% of rows); `tests/strategies/test_confidence_quantile.py` (hand-computed confidence on 3 fabricated rows: wide-straddle → ~0, tight-above → ~1, disagreement q50-vs-interval → 0).

- [ ] **Step 1-3: TDD** both units; golden tests untouched at defaults.
- [ ] **Step 4: Regen** (3× fit cost; quick-look first, then full window 4 coins). Compare: same-direction rate vs baseline should be ~100% at q50 (it is the same objective family — if direction changes materially, stop and investigate before trusting results).
- [ ] **Step 5: Portfolio A/B** where ONLY confidence differs. Gates per Global Constraints. Interaction note for the writeup: if E1 shipped, rerun E3 on top of E1 (quantiles in return space are better-posed anyway).

---

### Task E4: Carry sleeve — go/no-go confirmation (ship decision)

Already validated (repo doc §32: sleeve SR 8.24 standalone, corr +0.003, blend @20% → portfolio SR 3.178→3.287, DD 4.9→4.0%; 23 tests; code committed). This task is NOT a rebuild.

- [ ] **Step 1:** Re-run the §32 blend backtest on data refreshed through 2026-06 (drift check — same script, updated end date). Gate: blend still ΔSR-positive with p_pos ≥ 0.90 and DD still ≤ baseline.
- [ ] **Step 2:** If pass → produce a one-page live-integration scope (funding-leg execution on Binance, margin interplay with the 3% stops and the −1003/−1007 ban/timeout handlers, monitor tab) and STOP — live integration is its own plan+deploy cycle per the V5.1 handoff pattern. If fail → write the drift note; done.

### Task E5: Regime overlay (V4-heuristic) — decision only

SR-neutral DD-reducer (BTC 6.7→4.4%, ETH 8.2→6.4%). Value proposition is smoother live equity, not alpha.

- [ ] **Step 1:** Rerun V4-heuristic overlay on the current 8-coin V5 MIX preds (original run was 4-coin era). Gate: portfolio DD improves ≥1pp with SR change bounded in [−0.10, +∞) at p ≥ 0.80.
- [ ] **Step 2:** Pass → scope note for live (same stop-vs-overlay interaction caution as E4); fail → close as "4-coin-era result did not carry".

---

## Sequencing recommendation

E1 first (cheapest structural test, informs E3's target space) → E2 and E4 in parallel → E3 (on E1's winner mode) → E5 last. If Plan A (sentiment) ships a `+s` route meanwhile, rerun the winning experiment's final A/B on the shipped route config before any live change — one integration pass, not three.

## Self-review notes

- All line anchors from HEAD `f979683`; verify before editing.
- E2's weekly-refit fallback and E3's direction-invariance check are the two places an executor is most likely to silently diverge — both are called out inline.
- Deliberately excluded (documented negatives, do not re-add): NH-HMM/VPIN/multi-horizon stacks, seed ensembles, SL/TP grid changes, portfolio-weight optimization, sentiment analyst revival.
