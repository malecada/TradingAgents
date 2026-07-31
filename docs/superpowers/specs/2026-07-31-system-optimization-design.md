# Phase O — System Optimization Cycle (predlab_opt)

Date: 2026-07-31. Status: registered (gates key `predlab_opt`) BEFORE any
optimization result. User directive: open-ended perfection of the whole
validated system (models + strategy + universe), best honest backtest
achievable, no time limit. Governed by the house pre-registration
standard (trial ledger, frozen per-stage grids, forensic verification,
sealed forward holdout).

## Starting point (incumbent)

- **S1 `eq_h1`** — park_5 daily cross-sectional rank on monthly top-200
  PIT universe; long lowest-vol quintile / short highest-vol quintile,
  equal-weight, daily rebalance. Dev net SR 1.483; strategy-holdout
  PASS net SR +2.20 (spent 2026-07-31).
- **vt10 overlay** — book scaled to 10% ann target vol (20d trailing,
  shifted, cap 2.0). Dev PASS (MaxDD 42.5%→9.9%, SR 1.40 ≥ 0.9×raw);
  forward confirmation pending (predlab_pp2).
- Usable forecast models (P5 holdout): LGB volume ×4, BTC HARQ rv ×2,
  T7 park_5.

## Window discipline

- **Design window D:** 2021-01-01 → 2025-03-31.
- **Validation segment V:** 2025-04-01 → 2026-07-01. Disclosed
  NON-VIRGIN (spent as P5/PP holdout; its results are known). Used as an
  internal consistency check, never as a fresh-holdout claim.
- **Forward holdout F:** 2026-07-02 → OPEN, sealed. Panels physically
  end 2026-07-02; extending any data store past that date for evaluation
  is forbidden outside the registered one-shot. Spend when ≥ 6 months
  accrued (earliest 2027-01-02), ONE evaluation of the final frozen
  champion. Same calendar window as the pp2 vt confirmation — separate
  claims, separate ledger rows, disclosed.

## Champion-chain adoption rule (frozen)

A variant replaces the incumbent champion only if ALL hold:

1. Net SR on D+V (full window) > incumbent's by ≥ +0.10.
2. Consistency: net SR on V ≥ 0.5 × net SR on D (both net of costs).
3. Dual-family placebo (time-shift + cross-sectional shuffle) p < 0.05
   on the full window.
4. DSR > 0.5 at n_trials = 16 (prior PP/PP2 strategy trials) +
   cumulative ledgered predlab_opt configs at evaluation time.
5. Net mean positive in ≥ 3 of 4 sub-periods {2021-22, 2023-24,
   2025H1, 2025H2+2026H1}.
6. Raw-book MaxDD ≤ 1.25 × incumbent raw-book MaxDD (overlay judged on
   its own gate).

Champion chain is append-only in `data/predlab/opt_champion_chain.jsonl`
(config hash, commit, full metrics, gate evidence). Any adoption →
forensic kill-tests (shuffled-signal, lag-direction mutation, cost-off
sanity, coverage audit) before the chain row is written.

## Registered axes (list fixed now; grids frozen per-stage)

Each stage: ≤ 12 configs, exact grid appended to
`gates.json.predlab_opt.stages.<id>` BEFORE the first run of that stage;
every evaluated config → one trial-ledger row. Failing axis = closed
this cycle.

- **O1 signal construction** — low-vol proxy family: Parkinson mean
  windows {3,5,10,20}, close-to-close vol windows, vol-of-vol,
  EWMA-weighted park. Same anomaly, better estimator.
- **O2 portfolio construction** — quantile width (terciles/quintiles/
  deciles), weighting (equal / rank / inverse-vol), turnover buffer
  bands (no-trade zones), rebalance cadence.
- **O3 universe** — top-N ∈ {100,150,200,300} PIT by qv, ADV floor,
  rank-band diagnostics (§50 FTT single-name concentration lesson:
  report max single-name PnL share; > 50% ⇒ automatic FAIL of that
  config).
- **O4 overlay re-tune** — vol-target level/estimator (incl.
  HARQ-style model on book returns), exposure caps. New claim set,
  distinct from the frozen pp2 vt10 confirmation (disclosed).
- **O5 funding-carry tilt inside the book** — leg- or name-level tilt
  by funding within selected quintiles. Disclosed prior: standalone
  XS carry NEGATIVE (§46); this tests carry as a CONDITIONAL tilt,
  a different mechanism.
- **O6 volume-forecast liquidity weighting** — LGB volume champions
  (P5-usable) as liquidity weights/filters inside the book.
- **O7 momentum/trend tilt inside the book** — disclosed prior:
  standalone XS momentum/trend NEGATIVE (§43/§45).
- **O8 final composition** — best surviving axes combined; interaction
  check; final champion freeze for F.

## Costs (unchanged from PP)

Taker 5 bp per side per rebalance + realized funding carry per leg
where funding data exists (else 0, disclosed). 2× cost stress reported
as diagnostic on every champion-chain row (not a gate).

## Stop rules

Axis list fixed at registration — new axes require a new registered
program. Per-stage grids frozen before first run; no post-hoc config
additions inside a stage. Single-name exclusions post-hoc forbidden
(§50 lesson) — concentration is a config-level FAIL, not an edit.
If no variant ever clears the adoption rule, the program ends with the
incumbent standing and a negative-result report. Forward holdout F is
spent once, on the final champion only.

## Deliverables

Parameterized engine `tradingagents/predlab/opt.py` (+ tests pinning
exact reproduction of `eq_h1` dev numbers), `scripts/predlab_opt_*.py`,
per-stage cards `docs/predlab/reports/opt_o<N>.md`, champion chain
JSONL, THESIS §59+, memory milestone updates.
