# Honest Rebuild — Full Strategy Re-derivation on the Corrected Harness

**Date:** 2026-07-08
**Status:** Approved design (brainstorm complete)
**Predecessors:** `AUDIT_BACKTEST_2026-07-07.md` (C1 same-bar look-ahead, C2 unpurged labels; corrected 8-coin live-contract SR +0.145 vs published +3.966), `DECISION_REVIEW_2026-07-08.md` (32 decisions classified; all model/feature/strategy selections rendered on contaminated evidence).

## 1. Problem statement

Every material selection in the current system — model family, target, horizons, pooling, feature sets, sizing components, universe, tuning — was made on a backtest inflated ~25× by two critical defects. The corrected harness shows the deployed strategy has no meaningful edge (SR ≈ 0.1–0.5). The system must be re-derived from scratch on the corrected harness. The objective is a **working trading system**; the thesis benefits as a byproduct but does not constrain the design.

## 2. Approved scope decisions

| Question | Decision |
|---|---|
| Success definition | Any robust positive edge net of costs; system = portfolio of independently validated sleeves (carry, directional, or both) |
| LLM layer | Out of the rebuild loop; one flagship hybrid re-test at the end (Phase 5) decides whether it returns |
| Live end-goal | Real money eventually, small size; strict validation gates; VPS repurposed for the rebuilt system |
| Anti-overfit discipline | Locked holdout + pre-registered gates + honest trial ledger |
| Directional search breadth | Existing LGB stack re-derived honestly, PLUS model-free classic factors (TSMOM, MA breakout, XS-momentum) as the floor any ML candidate must beat |

Rebuild structure: **Approach A — sleeve-portfolio rebuild, carry-audit-first.** Carry is model-free (immune to C1/C2), has the highest unaudited SR (8.24 upper bound), and can reach live validation without waiting for the directional rebuild.

## 3. Phase 0 — Methodology foundation

Rules fixed before any experiment runs.

### 3.1 Harness contract
- Every backtest uses: **causal convention** (post-remediation default) + **purged labels** + **rolling-730d training window** — i.e., the exact live contract. Legacy convention permitted only for forensic comparison, never for selection.
- Single shared evaluation path: `evaluate_models_multi.py --purge --train-window-days 730` → `baseline_v5_mix.py --convention causal` (or the factor-engine equivalent). No per-experiment engine forks.

### 3.2 Engine completion (prerequisite work)
- **Intrabar High/Low stop replay** in the backtest engine so the live 3% price-axis STOP_MARKET (and its stop-out → next-cycle re-entry behavior) is simulated. Audit HIGH finding: ≈64 engine stop events vs ≈1,723 replayed intrabar. Until this lands, no stop/sizing decision has valid evidence.
- Funding: 3bp/day, side-aware (already shipped for the causal path; verify side-awareness).

### 3.3 Data split
- **Dev window:** 2021-11 → 2025-03 (~41 months; covers the 2022 bear, 2023 chop, 2024 bull).
- **Locked holdout:** 2025-04 → 2026-07 (~15 months). No experiment, tuning, or model selection touches it before Phase 3. Enforced mechanically: dev prediction directories are generated with an end date of 2025-03-31, so holdout rows are physically absent during the search.

### 3.4 Trial ledger
- Append-only JSONL (`data/rebuild/trial_ledger.jsonl`): one row per full-window config evaluation — config hash, git commit, window, metric outcomes, timestamp.
- DSR trial counts are computed **from the ledger**, never quoted from memory. (Audit: 12 claimed vs >450 actual documented evaluations.)

### 3.5 Pre-registered gates
- Every experiment declares its gate, stop rule, and comparison arm **before** running (pattern already proven in the sentiment-index A/B and E1–E3). A failed gate is recorded as a negative result; no post-hoc reframing or gate adjustment.

### 3.6 Universe rule
- Core: BTC + ETH (top-2 by market cap for the entire window — no survivorship concern).
- Satellites: admitted only if the pool-size experiment (§5.2 axis 3) wins with them, and selected by a PIT rule — top-10 by market cap as of each dev-window start date — never from a present-day list. The 8-coin universe (2026 top-10 backtested from 2021) is retired.

## 4. Phase 1 — Carry sleeve audit

Five-pass audit of `carry_blend_p4.py` / §32, applying the same discipline that invalidated V5:

1. **Timing/convention** — funding-accrual timestamps vs position timestamps; check for any same-bar credit analogous to C1.
2. **Execution realism** — spot-leg trading costs, perp entry/exit spread, rebalance-on-drift costs, basis convergence P&L at entry and exit. Quantify the gap behind the "real-basis upper bound" caveat.
3. **Funding realism** — reconcile modeled accrual against actual Binance 8h funding-rate history per leg; side-aware.
4. **Regime & persistence** — funding-flip stress (post-window 37 days already showed BTC net-negative funding, ETH at 8% of run-rate); rolling 30d funding-sign distribution; worst-90d P&L; audited haircut curve.
5. **Capacity & margin** — sub-account isolation vs reserve-margin accounting; margin interplay with directional positions; leverage ≤ 3.

**Deliverable:** audited, haircut-stressed carry SR on the dev window.
**Pre-registered GO gate:** stressed SR ≥ 1.5 **and** worst-90d loss within the portfolio DD budget (≤ 5% at the sleeve's intended allocation). GO → carry becomes the portfolio anchor and enters the Phase 4 live track immediately, in parallel with Phase 2.

## 5. Phase 2 — Directional sleeve derivation (dev window only)

### 5.1 Step 1: model-free factor floor
Run before any ML work, all through the same causal engine, full costs, vol-targeted sizing:
- Time-series momentum: sign of k-day return, k ∈ {small set of lookbacks, e.g., 7/14/30/90}.
- MA crossover / channel breakout: a few canonical parameterizations.
- Cross-sectional momentum: BTC vs ETH relative strength.

≈15–20 configs total, every one ledger-logged. **The best survivor is the floor.** Literature (and the audit's own placebo analysis) suggests crypto TSMOM is a real effect; plausible floor SR 0.5–1.0.

### 5.2 Step 2: LGB re-derivation, one axis at a time
Each axis is a pre-registered gated experiment vs the current best configuration (paired stationary block bootstrap, block 21, n=2000):
1. **Target:** level vs logret (E1 re-run purged — the recorded NEGATIVE was rendered on leaked DirAcc).
2. **Horizon set:** purged DirAcc + causal SR per horizon; single-horizon vs consensus (the h7+h14 consensus premise was the leaked DirAcc ladder; purged h7 ≥ h14 on most routes).
3. **Pool size:** BTC+ETH vs +satellites (the old "altcoins cost 12–22pp DirAcc" finding is contaminated).
4. **Feature sets:** 78f vs 193f vs +sentiment-index, purged (all prior feature negatives were measured against a leaked near-oracle baseline with no headroom; they may flip).
5. **Sizing ablation:** trend filter, vol targeting, Kelly fraction, min-hold/early-exit — each toggled causally with intrabar stops active (the old attribution — "trend filter is the single highest-impact improvement" — was the C1 artifact).

### 5.3 Step 3: survival rule
The ML sleeve ships only if it beats the factor floor on dev: **ΔSR > 0 with p_pos ≥ 0.85 (paired bootstrap) and DSR > 0.90 against the ledger's trial count.** Otherwise the directional sleeve is the simple factor. No attachment to LGB.

Budget: Steps 1–2 ≈ 40–60 ledger entries, all CPU, days not weeks.

## 6. Phase 3 — Holdout one-shot + portfolio assembly

1. **Freeze** the candidate portfolio: audited carry + best directional survivor + allocation rule derived on dev only (expected: vol-weighted with a carry allocation cap; exact rule fixed before the holdout run).
2. **One-shot holdout run** (2025-04 → 2026-07) of the frozen portfolio and each sleeve. No retuning afterward. A sleeve that fails holdout is reported as a negative result and ships nothing; the portfolio may still ship with the surviving sleeves.
3. **Pre-registered deploy gate:** holdout portfolio net SR > 0.5, MaxDD < 15%, each shipped sleeve's holdout contribution ≥ 0, placebo beat p < 0.05.
4. Re-run the validation battery (placebo, DSR, regime slices, cost stress) against the causal floor (placebo null ≈ 0, not the legacy +2.87).

## 7. Phase 4 — Live rebuild

- **VPS disposition (day 1 of the phase):** stop the invalidated V5.1 8-coin config — both the quant line and the hybrid A/B line (its quant legs are equally invalid). Redeploy only from the rebuilt system.
- **Carry track** (starts at Phase 1 GO, parallel to Phase 2): sleeve runner per the E4 scope — daily job, short perp + long spot BTC/ETH, leverage ≤ 3, sub-account (preferred) or reserve-margin isolation, order-tag namespace so the −1003/−1007 ban/timeout handlers and directional stops never touch sleeve orders, `data-carry/` journal, monitor tab (funding collected vs paid, trailing 30d funding-sign alert, basis tracking). **30-day testnet acceptance: funding-accrual reconciliation vs exchange statements.**
- **Directional track** (after Phase 3 pass): deploy the surviving sleeve (factor or LGB) through the existing parity/preflight/monitor infrastructure. Live config = exactly the frozen holdout config, enforced via the preflight gate 3c pattern.
- **Acceptance gate replaced:** the old SR ≥ 2.86 @ 90d gate is void (artifact target, underpowered, config drift mid-window). New gate = **paired live-vs-replay daily-return regression** (implementation fidelity — answerable in 90 days) plus a sanity band around the honest expectation. Alpha existence at SR 0.5–2 is not measurable in 90 days and will not be pretended to be.
- **Mainnet-small:** after testnet parity passes — carry first (highest audited SR, model-free), small fixed notional; directional joins later. Explicit operator sign-off before any mainnet key reaches the box.

## 8. Phase 5 — LLM flagship re-test (optional, last)

- Precondition: audit `backtesting/engine.py` for the same-bar convention (never audited; all pure-LLM backtest numbers flow through it).
- One experiment: ETH hybrid A/B — LLM modulator over the honest directional legs vs the pure sleeve, ≥90 bars, paired block bootstrap, ≈$15–25 LLM cost.
- Pre-registered gate: p_pos ≥ 0.90. Pass → LLM modulator earns a place in the system and a corrected positive claim in the thesis. Fail → LLM layer remains thesis-only, reported as base-dependent/no-effect on honest legs.

## 9. Explicitly out of scope

- New model families (NNs, TCNs), new data purchases — excluded by the search-breadth decision.
- Multi-exchange execution, options/basis trades beyond the carry sleeve.
- Thesis text rewrite (separate workstream; consumes this rebuild's outputs).
- Reusing any pre-audit number for any selection decision.

## 10. Success criteria

1. Every selection decision in the shipped system traceable to a ledger-logged, gated experiment on the corrected harness.
2. At least one sleeve passes its pre-registered holdout gate and reaches testnet with the new fidelity-based acceptance gate. (If none passes, the honest negative is itself the outcome — the system does not deploy on hope.)
3. VPS no longer runs any configuration selected on contaminated evidence.

## 11. Risks

| Risk | Mitigation |
|---|---|
| Carry audit reveals the 8.24 is mostly basis/execution artifact | That is the audit working as intended; gate at stressed SR ≥ 1.5, not at 8 |
| Funding regime stays flipped (carry pays instead of collects) | Trailing 30d funding-sign monitor + always-on vs gated decision revisited with audited data |
| No directional candidate beats the factor floor | Ship factor sleeve; LGB reported as honest negative |
| Nothing passes holdout | Report negatives; deploy nothing; thesis still gains the methodology chapter |
| Holdout contamination via repeated peeking | Mechanical enforcement (dev dirs end 2025-03-31) + one-shot rule in this spec |
| Search grows unbounded (450-config repeat) | Trial ledger + DSR against ledger count + pre-registered per-axis experiments |
