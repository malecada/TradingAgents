# Prediction Lab — Program Charter & Design (2026-07-30)

Branch: `research/prediction-lab` (worktree `TradingAgents-predlab`, base `main@382d189` = corrected causal harness).
Status: DESIGN — governs a long-running research program, not a single experiment.

## 0. Mandate and autonomous-mode assumptions

User directive (2026-07-30): separate research/development branch focused solely on the
prediction approach; do not fixate on previously selected features, data granularity, or
horizon; goal is a model with statistically significant predictions; research first, try
different approaches (price / trend / volume / …, short-term / long-term / intraday);
prediction quality first, profitability only after; start simple (ARIMA / LGB, small
feature sets) and build up; time and number of approaches unconstrained; separate branch
and separate memory section; consider a Ralph loop for iteration.

Session runs autonomously; clarifying questions are replaced by the following explicit
assumptions (each reversible if the user objects):

- **A1 — "statistically significant" is defined against the strongest sensible naive
  baseline per target** (random walk for returns, HAR-RV for volatility, seasonal-AR for
  volume), with multiplicity control and a sealed-holdout confirmation — not p < 0.05
  against a weak null. Beating a weak null is recorded as "predictability exists" but
  never claimed as model skill.
- **A2 — house pre-registration discipline carries over** (gates before results,
  append-only trial ledger, sealed holdout, one-shot, stop rules), adapted from
  trading-metric gates to forecast-metric gates. Predlab keeps its own namespace
  (`data/predlab/gates.json`, `data/predlab/trial_ledger.jsonl`) to avoid collisions
  with the active `value_xs`/`unlock_xs` session writing `data/rebuild/`.
- **A3 — dev/holdout windows reuse the house split**: dev 2021-01-01 → 2025-03-31,
  holdout 2025-04-01 → 2026-07-01, holdout sealed, spent one-shot per cell champion.
  (Earlier data may be used as burn-in/training history where stores reach back.)
- **A4 — compute is CPU-first for Tiers 0–2.** GPU/cloud spend is a decision point
  surfaced to the user when Tier 3 (deep learning) is reached, not assumed.
- **A5 — LLM-based prediction is out of scope initially** (§48 just falsified the LLM
  modulator on honest legs; the LLM-cutoff constraint would also bind any such
  backtest). It may re-enter later only as a clearly-motivated tier.
- **A6 — Ralph loop authorized** ("consider using ralph loop" + unconstrained time);
  started after the charter, backlog, and Phase-1 plan are committed. Cancellable
  anytime with `/cancel-ralph`.

## 1. Why a forecast-first program (the reframe)

Thirteen post-rebuild leads died mostly at rung 1 of the gate ladder: *no signal* at the
trading-metric level (LEADS_AND_GATES_2026-07-30.md §4). Trading metrics (Sharpe on a
sized, costed, rebalanced portfolio) are a *low-power instrument* for detecting whether
predictability exists at all: sizing, costs, turnover, and path-dependence add variance
before the question "was the forecast any good?" is ever asked.

The Prediction Lab inverts the pipeline:

1. Measure forecast skill directly — per-observation loss differentials against strong
   baselines (Diebold–Mariano-type tests use every bar as a data point; SR-difference
   bootstraps effectively use one path).
2. Sweep *targets beyond next-bar return* — realized volatility, volume, ranges,
   funding, cross-sectional ranks — because the literature says some of these are
   strongly predictable while returns are borderline-unpredictable. The output is a
   **predictability map** of crypto by target × horizon × method: which cells contain
   genuine out-of-sample skill, with honest significance.
3. Only cells with demonstrated, holdout-confirmed skill graduate to a separate
   profitability-mapping phase (own pre-registered spec; explicitly out of scope here).

This is scientifically valuable for the thesis regardless of outcome (a rigorous
predictability map with pre-registered negatives is a contribution in itself, matching
the house style of §32–§50), and it maximizes the chance of ending with a genuinely
*usable prediction model*, because it searches where predictability is known to live,
not only where profits would be convenient.

## 2. Objective and success criteria

**Objective.** Find at least one (target, horizon, universe, model) cell whose champion
model demonstrates genuine out-of-sample forecast skill — and characterize the full map
of cells tried.

**"Usable prediction model" (program success) — all of:**

- **U1 Skill vs strong baseline.** Beats the cell's registered strong baseline on the
  registered loss with DM (HLN small-sample correction; Clark–West when nested)
  p < 0.05 on dev.
- **U2 Effect floor.** Improvement exceeds the registered economic-relevance floor for
  the cell (see §5 per-target gates) — significance alone at large N is not enough.
- **U3 Multiplicity survives.** Within-cell: model set passes SPA/MCS membership.
  Across-cells: cell's p survives Benjamini–Hochberg FDR (q = 0.10) over all registered
  cells in the predlab ledger.
- **U4 Holdout one-shot.** Frozen champion beats the same baseline on the sealed
  holdout window, one evaluation, no re-tuning; direction and magnitude consistent with
  dev (no sign flip, ≥ half the dev effect).
- **U5 Stability.** Skill is present (point estimate right-signed) in ≥ 2 of 3 dev
  sub-periods and, for cross-sectional cells, in a majority of universe tranches; and is
  seed-robust for stochastic models (dispersion across ≥ 5 seeds ≪ effect).

A cell failing any of U1–U5 is recorded NEGATIVE with the binding criterion, house
style. The map (positives *and* negatives) is deliverable D1; a U1–U5 survivor is
deliverable D2; graduation of D2 into a profitability study is Phase P, out of scope.

## 3. The predictability matrix (cells)

Targets (per asset unless XS):

| ID | Target | Definition | Strong baseline | Loss / test |
|----|--------|-----------|-----------------|-------------|
| T1 | Return level | log-return over next h | random walk (0) + AR(1) | MSE/MAE; DM-HLN; OOS R² (Campbell–Thompson) |
| T2 | Direction | sign of next-h return | base-rate (climatology) | accuracy vs base rate; Pesaran–Timmermann; AUC + CI; Brier vs climatology |
| T3 | Realized volatility | RV over next h from 5-min returns (annualized); also BV | HAR-RV (and EWMA/GARCH(1,1) as weak refs) | QLIKE (primary), MSE-of-log-RV (secondary); DM-HLN |
| T4 | Volume | next-h dollar volume (log) | seasonal-naive + seasonal-AR | MASE vs seasonal-naive; DM-HLN |
| T5 | Range | next-h Parkinson range | EWMA of range | QLIKE-style on range proxy; DM-HLN |
| T6 | Funding | next funding print / next-24h sum | AR(1) (funding is persistent) | MSE; DM-HLN; CW vs AR(1) |
| T7 | XS rank | cross-sectional rank of next-h return (and RV) across wide universe | zero-IC null; XS momentum as weak ref | daily Spearman IC series; Newey–West t; IC decay |

Horizons: 1h, 4h, 24h, 7d (5m added only if an intraday cell earns it — microstructure
noise and stale-price pitfalls acknowledged). Universes: BTC, ETH (depth cells);
top-20 (breadth-lite); wide PIT universe 150–300 syms (T7 only).

Not every (T, h, U) combination runs — the registered battery for each phase names its
cells in `data/predlab/gates.json` before results are produced. Initial battery:
T1/T2/T3/T4 × {1h, 24h, 7d} × {BTC, ETH} + T6 × {8h, 24h} × {BTC, ETH} + T7 × {24h, 7d}.

## 4. Method tiers (simple → complex; user's "start simple" mandate)

- **Tier 0 — naive set (the nulls):** RW/zero, unconditional mean, last-value
  persistence, seasonal-naive, EWMA (RiskMetrics λ=0.94), rolling climatology.
- **Tier 1 — classical:** AR(p)/ARIMA/SARIMA, ETS, GARCH(1,1)/EGARCH/GJR-GARCH (arch
  pkg), HAR-RV (+ HARQ if RQ available), OLS/ridge on small lag sets, VAR (BTC↔ETH
  spillover). Cheap, interpretable, sets the honest bar.
- **Tier 2 — ML, small registered feature sets:** LightGBM, elastic net, kernel ridge.
  Feature sets are pre-registered per cell family and *small* (≤ ~25): price lags, RV
  terms, taker-imbalance, OI deltas, funding, calendar dummies, on-chain where PIT.
  (LGB was retired for *return-SR trading*; forecast losses on new targets are a
  legitimate, different question — the retirement verdict is not silently overturned:
  T1-cell LGB results will be reconciled against §40 explicitly.)
- **Tier 3 — sequence DL (gated on compute decision + Tier-2 evidence):** LSTM/GRU,
  TCN, N-HiTS, PatchTST. Enter only for cells where Tier ≤ 2 shows near-skill (p < 0.20
  vs strong baseline) or literature gives specific cause; multi-seed mandatory.
- **Tier 4 — TS foundation models, zero-shot/fine-tuned:** Chronos-class, TimesFM-class,
  Moirai-class, TabPFN-TS (exact set per RESEARCH.md). **Pretraining-leakage rule**
  (generalizes the house LLM-cutoff constraint): a model may only be evaluated on dates
  after its training-data cutoff unless its corpus verifiably excludes crypto series;
  per-model evaluation windows documented in gates before running.
- **Tier 5 — combinations:** forecast combination / regime-conditional ensembles over
  cells with ≥ 1 skilled or near-skilled model; MCS across the final model set.

Ordering rule: a tier for a cell family may start only when the previous tier's results
for that family are ledgered. Baselines are never skipped.

## 5. Evaluation protocol (the heart)

- **Scheme:** rolling-origin walk-forward: train on data ≤ t, forecast t+h, roll.
  Refit cadence registered per cell (daily for cheap models, weekly/monthly for
  expensive). Purge/embargo ≥ h between train end and forecast origin where features
  aggregate windows; **no shuffled CV anywhere**.
- **Data hygiene:** scalers/transforms fit on train only; features lagged to be in the
  information set at origin (house causal convention frozen in spec); vol proxy noise
  acknowledged — QLIKE + RV-proxy consistency per Patton (2011); overlapping-horizon
  autocorrelation handled with HAC variance in DM (lag ≥ h−1).
- **Tests:** DM-HLN (primary), Clark–West (nested), Pesaran–Timmermann + binomial-on-
  independent-bars (direction), Newey–West t on IC series (XS), stationary block
  bootstrap on loss differentials (robustness companion), SPA/MCS (within-cell
  multiplicity), BH-FDR across cells (registry-wide).
- **Per-target effect floors (U2), registered before any run:**
  T1: OOS R² vs RW ≥ 0.2% (1h) / 0.5% (24h) / 1.0% (7d). T2: accuracy ≥ base rate
  + 2 pp AND AUC CI excludes 0.5. T3: ΔQLIKE ≥ 2% vs HAR-RV. T4: ΔMASE ≥ 5% vs
  seasonal-naive. T6: ΔMSE ≥ 5% vs AR(1). T7: mean |IC| ≥ 0.02 with NW-t ≥ 3.
  These anchors are copied into `data/predlab/gates.json` verbatim at battery
  registration; any per-cell deviation is an amendment and must be declared there
  before the cell runs.
- **Ledger:** every (cell, model, config, seed-set) evaluated on dev gets an append-only
  row (`data/predlab/trial_ledger.jsonl`) with config hash + git commit; the FDR/DSR-
  style denominators come from the ledger and cannot be reset.
- **Forensic verification of results (house discipline):** any PASS triggers kill-tests
  before it is believed: shuffled-target must destroy skill; lag-direction mutation must
  flip/kill; train-on-future canary must dramatically beat the honest run (proves the
  harness *can* leak, and therefore that not-leaking is informative); zero/NaN coverage
  audits with honest denominators. Any NEGATIVE on a cell literature says is predictable
  (T3/T4) triggers the inverse: probe for harness bugs before recording.
- **Reporting:** per-cell result cards (baseline losses, model losses, test statistics,
  sub-period table) accumulate in `docs/predlab/reports/`; phase reports roll up into
  THESIS_FINDINGS.md §54+ in house style.

## 6. Approaches considered

- **A — Predictability-matrix program (CHOSEN).** Systematic cell sweep, tiered models,
  forecast-level gates, map as first-class deliverable. Pros: highest probability of
  finding real skill (searches vol/volume where predictability is documented), maximum
  statistical power, thesis-grade output either way, reuses proving discipline. Cons:
  breadth requires the multiplicity machinery (built in §5) and disciplined pacing
  (handled by backlog + loop).
- **B — Single-target deep dive** (e.g., BTC 24h return only, every model thrown at
  it). Rejected as the *program* frame: highest risk of another rung-1 string of
  negatives; contradicts the user's explicit breadth ("price/trend/volume/…"). Becomes
  the natural *second phase* inside skilled cells found by A.
- **C — Foundation-models-first.** Fast coverage, but violates "start simple", has
  unresolved pretraining-leakage subtleties, and poor attribution when it wins.
  Folded in as Tier 4 instead.

## 7. Risks and mitigations

- **Harness bugs corrupt verdicts** (the July-7 lesson): plumbing probes run before any
  battery (timestamp reconciliation; a deliberately-leaky canary model must win big);
  engine provenance declared in gates.
- **Multiplicity inflation from a long-running loop:** ledger + BH-FDR + SPA are
  denominator-honest by construction; grids must be registered before running.
- **Vol/volume "wins" oversold:** strong-baseline rule (A1) — beating unconditional or
  EWMA is a map entry, not a claim.
- **Foundation-model leakage:** per-model post-cutoff evaluation windows (Tier 4 rule).
- **Compute creep:** Tier 3+ gated on explicit user decision (A4).
- **Concurrent session collisions:** own worktree, own data namespace (`data/predlab/`),
  own ledger; never touches `data/rebuild/` or `data/xsect/` write-paths.
- **Loop runaway:** per-iteration contract (one backlog item), stop conditions, infra-
  failure circuit breaker (3 consecutive failed iterations → stop and surface).

## 8. Deliverables and thesis mapping

- **D1 Predictability map** — per-cell result cards + roll-up tables/figures;
  THESIS_FINDINGS.md §54+ (numbering after value/unlock §51–§53 land).
- **D2 Usable model(s)** — any U1–U5 survivor: frozen config, holdout card,
  reproduction script.
- **D3 Methodology section** — forecast-evaluation gate battery (this charter §5) as
  the forecast-level analogue of the trading gate battery, for the thesis methods
  chapter.
- **D4 Reusable library** — `tradingagents/predlab/` package: losses, tests, splitters,
  baselines, runners (tested, importable by later phases).

## 9. Iteration engine (Ralph loop)

State lives on disk; every iteration is recoverable (ledger = recovery map):

- `docs/predlab/BACKLOG.md` — ordered work items (checkboxes), phase-structured.
- `docs/predlab/STATE.md` — current phase, last completed item, blockers, next action.
- `data/predlab/gates.json` + `trial_ledger.jsonl` — registration + results.
- Iteration contract: read STATE+BACKLOG → take top open item → TDD (tests first for
  library code) → run → forensically verify → ledger/report → update BACKLOG+STATE →
  commit → end turn. One item per iteration; no grid runs without registration.
- Milestone hook: phase completion or any gate PASS/holdout event → update predlab
  memory (`predlab_status.md`) and surface prominently in the iteration summary.
- Stop conditions: backlog empty (final report + stop), U1–U5 success (report + stop),
  3 consecutive infra failures (stop + surface), user `/cancel-ralph`.

## 10. Out of scope

Profitability mapping (position sizing, costs, portfolio construction on skilled
forecasts) — Phase P, separate spec + registration once D2 exists. Live deployment.
LLM/sentiment predictors (A5). Options/derivatives pricing applications.
