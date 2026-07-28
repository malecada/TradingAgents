# P5 — LLM Flagship Re-test (hybrid modulator on corrected legs) — Pre-registration

Date: 2026-07-28
Status: registered (gates.json entry `llm_p5_hybrid` written BEFORE any arm run)
Parent: docs/superpowers/specs/2026-07-08-honest-rebuild-design.md §8 (Phase 5)

## What this is

The one experiment the honest rebuild deferred: does the Layer-2 LLM modulator
add risk-adjusted value over the corrected-harness quant leg? Every prior
hybrid measurement (1-yr ETH ΔSR +1.10, LOO §23.11, sentiment §23.12, prompt
A/Bs) ran on the invalidated same-bar legs; the relative modulator effect was
explicitly flagged "needs re-measurement". This is that re-measurement, run
once, under the live contract.

## Precondition (spec §8) — engine audit DONE

`tradingagents/backtesting/engine.py` (`run_backtest`) audited 2026-07-28:
**same-bar confirmed** — `agent_signals[i]` (formed from day-i close data via
the propagate date filter) earns `(actual[i]−actual[i−1])/actual[i−1]`, the
bar that closed as the signal was formed. Same defect class as audit finding
C1. Consequences: (a) every legacy pure-LLM backtest number that flowed
through this engine is stale (already assumed post-audit; now verified);
(b) this engine is NOT used here. `scripts/backtest_hybrid.py` shares the
defect (positions[t] earn bar-t return; last touched pre-audit) and is also
NOT used. P5 runs on a new causal A/B harness (below).

## Experiment (single config — no grid)

**Coin:** ETH only (strongest prior; per-coin asymmetry §23.11; live A/B line).
**Window:** 2026-01-16 → 2026-05-21, 126 bars.
- Start: LLM-cutoff constraint (house rule: backtest must start after the
  model's training cutoff; 2026-01-16 is the P4-established post-cutoff start
  for gpt-5.4-mini).
- End: PIT feature-store limit (Coinglass derivatives end 2026-05-21; the
  ETH quant route consumes them via `--onchain-pit`).
- ≥90-bar spec requirement satisfied (126).

**Holdout interaction (recorded, deliberate):** the window lies inside the
2025-04+ locked-holdout region. This is legitimate and unavoidable here:
(a) the quant base leg is FROZEN (canonical V2 contract, no selection
happens in this experiment); (b) the directional-system holdout was already
spent by the rebuild's §41 one-shot (deploy = ∅); (c) the LLM-cutoff rule
forces any honest LLM window into 2026. The experiment measures ONLY the
paired delta (hybrid − quant) on a fixed base. Ledger rows are written with
`allow_holdout=True` citing this paragraph.

### Arm A — pure quant leg (no LLM)

- Predictions: `data/audit_fix/rolling730/multi_2coins_pit_wf_p5` —
  `evaluate_models_multi.py --coins bitcoin ethereum --horizons 7 14
  --models lgb --purge --train-window-days 730 --onchain-pit --days 890
  --min-train 730 --trade-date 2026-05-22` (exact audit recipe for the frozen
  §20 ETH route `multi_2coins_pit_wf`, extended to cover the window; the
  audit artifact dir itself is untouched).
- Signals: canonical V2 h7+h14 term-structure consensus.
- Sizing: canonical V2 (target_vol 0.10, half-Kelly 0.5, max_leverage 3.0,
  min_hold 7 with early_exit 0.015, SMA30 trend filter 1.5×/0.5×, 95th-pct
  vol cap), **causal convention** (`sizing_price_series(convention="causal")`
  — every sizing input sees close(D−1) only), via the audited
  `baseline_v5_mix` code path.
- Costs: `costs_for_coin("ethereum", convention="causal")` (core-coin cost
  set, causal funding), intrabar price-stop replay at 3% (live STOP_MARKET
  contract), initial capital 10,000.
- Accrual: position decided at close t earns bar t+1 (the audited engine's
  convention with causal position construction).

### Arm B — hybrid (quant × LLM modulator)

- `pos_B[t] = pos_A[t] × (1 + effective_weight[t] × (multiplier[t] − 1))`
  — the production composition formula, applied to the SAME arm-A sized
  position series, then run through the IDENTICAL engine/cost/stop path.
  Both factors (multiplier, effective_weight) come from the signals CSV row
  whose decision date matches the position's decision date.
- Multipliers: `scripts/generate_hybrid_signals.py`, ETH, analysts =
  `["onchain", "prediction"]` (live `ANALYSTS_BY_COIN["ethereum"]`;
  sentiment dropped per house policy; market dropped for ETH per live
  routing), gpt-5.4-mini deep / gpt-5.4-nano quick (live models),
  `modulator_prompt_version = "v1"` (live default), `anonymize_assets =
  False` (live default), replay cache ON (house rule), `quant_pred_dir` →
  the arm-A prediction dir (corrected quant context; small `--quant-pred-dir`
  flag added to the generator as part of this harness, pre-registered here).
- Missing/failed extraction on a bar → multiplier 1.0, effective_weight
  unchanged (production fallback semantics); the failure count is a
  registered diagnostic.

## Gate (frozen 2026-07-08 in the rebuild spec §8; restated verbatim)

- Paired block bootstrap on the daily-return difference (hybrid − quant),
  house convention: stationary block bootstrap, block = 21, n = 2000, shared
  index path (`tradingagents/rebuild/compare.py`).
- **PASS iff p_pos ≥ 0.90** (probability the true ΔSR > 0).
- Pass → the modulator earns a place in the system and a corrected positive
  claim in the thesis. Fail → LLM layer remains thesis-only, reported as
  base-dependent / no-effect on honest legs.
- One-shot: no prompt retuning, no window shopping, no second model, no
  post-hoc analyst-set changes. Deterministic re-runs after mechanical
  crashes are permitted via the replay cache (identical prompts → identical
  outputs); any change to prompts/config voids the run.
- Conventions: √252, ddof=1, zero-variance SR := 0; ΔSR and both arm SRs
  reported with the verdict either way.

## Diagnostics (registered, non-gating)

1. Multiplier distribution (mean/std/histogram buckets, % bars ≠ 1.0).
2. Extraction-failure rate (LLM output → multiplier parse).
3. effective_weight distribution.
4. ΔmaxDD (hybrid − quant) and per-arm maxDD.
5. Parity probe: CSV `quant_direction` vs h7/h14 consensus recomputed from
   the prediction CSVs (must match; mismatches quantified with honest
   denominators before the result is trusted).
6. Cost of the run (USD, from provider dashboard/token counts).

## Budget

≈$15–25 expected (126 bars × 1 coin × 2 analysts + debate/modulator layers,
gpt-5.4-mini/nano). Approved by the operator ("go" on the P5 quote).

## Deliverables

1. `--quant-pred-dir` flag on the signal generator (pre-registered harness fix)
2. Causal P5 A/B script + unit tests (accrual, composition, stop parity)
3. `llm_p5_hybrid` gates.json entry + ledger rows (`allow_holdout=True`)
4. Signals CSV + A/B results JSON + THESIS §48 either way
