# Wide-Universe Trend Following (top-N liquid perps) — Design

Date: 2026-07-28
Status: approved (brainstorm session 2026-07-28)
Registration: gates.json entry `trend_wide_t1` (to be written BEFORE any experiment run)

## Background and provenance

Post-§44 go-forward menu ranked two leads above all others. Lead #1 (cross-crypto
spillover long/short, anchored on Guo, Sang, Tu, Wang, *Cross-cryptocurrency return
predictability*, JEDC 163 (2024) 104863) was investigated first and **dropped before
registration**: the paper is a minute-frequency study (30 coins, 1-minute bars,
2019-03-25 → 2021-04-30; futures leg 2020-07-29 → 2021-04-30 only; quintile long/short
rebalanced every 5–10 minutes; net 0.34–0.66 bps per 10-minute bar at 4 bps taker fee;
universe selected by volume as of 2020-05-09, i.e. after sample start). It provides no
evidence for daily-horizon spillover, and the mechanism (limited-attention diffusion)
operates at minute scale. A daily spillover test would be an original low-prior
hypothesis in the momentum family already closed 0/12 (§43). Recorded here so the
detour is documented; PDF at scratchpad `guo2024_spillover.pdf`.

This design executes lead #2: **time-series trend ensemble across the top-N liquid
perps** ("breadth does the work"). External anchors (both unverified, replicate
in-house, treated as motivation only): practitioner trend ensemble top-20, net SR ~1.57
@ 10 bps (SSRN 5209907); AdaptiveTrend 6h bars net SR 2.41 (arXiv 2602.11708). Prior
internal evidence: 2-coin version of the same frozen primary, holdout +0.389 n.s. (§44)
— breadth is the axis being tested, not new signal rules.

## Decisions taken at brainstorm

- Position scheme: **long-flat only** (matches frozen primary incl. explicit exit rule;
  no perp-funding modeling needed for shorts; no LO-halt trap because the primary exits
  on vote ≤ 0.5).
- Dev gate: **relative + absolute** — must beat EW buy-and-hold benchmark AND clear an
  absolute net-SR floor. Kills pure-beta capture in the bull-heavy dev window.
- Build approach: **A** — new daily-position runner in `tradingagents/xsect/`, reusing
  the frozen metalabel primary, the PIT universe module, and rebuild bootstrap/ledger
  infra. (B: porting metalabel event replay rejected — triple-barrier baggage; C:
  weekly discretization rejected — loses mid-week trend exits.)

## Signal (frozen, reused verbatim)

`tradingagents/metalabel/primary.py` (branch feature/meta-labeling, §44 registration):
vote = mean of 4 binary rules — MA-cross 5/20, 10/40, 20/60 and stateful Donchian
20-entry/10-exit; 60-bar warmup. Long when vote > 0.5, flat otherwise. **No parameter
re-tuning.** The module is copied/imported unchanged; a parity unit test pins its
output against a fixture generated from the metalabel worktree.

## Universe

PIT eligibility via existing `tradingagents/xsect/universe.eligibility` (799-symbol
survivorship-safe store, includes delisted symbols): USDT-M perp with kline on day D,
first kline ≤ D−30, 30d median quote-volume ≥ $5M; rank by 30d median quote-volume;
keep top-N. Universe refreshed **monthly** — first Monday close of each calendar
month, using data ≤ that close. A coin leaving the universe is force-flattened at the
next bar with turnover cost. Additional history requirement: a symbol must have ≥ 90
daily bars at decision time (60-bar vote warmup + 30d vol window) or it is skipped
that month.

## Sizing

Per-coin weight at daily decision close t:
`w_i(t) = (1/N) * min(1, vol_target / (sigma_i(t) * sqrt(365))) * 1{vote_i(t) > 0.5}`
where `sigma_i(t)` = std of daily log-returns over the 30 calendar days ending at t
(NaN/insufficient → weight 0). No per-coin leverage above the 1/N slot. Portfolio
daily log-return = Σ_i w_i · r_i (weight-anchored; a member missing a kline that day
contributes 0, weights NOT redistributed intra-period — store convention).

## Execution and costs

- Decision at close t → weights apply from bar t+1 (causal next-bar accrual, corrected
  harness convention; the decision bar never accrues the return that produced it).
- Costs: 10 bps per side × Σ|Δw|, charged on the first accrual day after each weight
  change. Weights change daily (vote flips, vol drift) and monthly (universe rotation).
- Delisting mid-month: position exits at last available close; exit cost charged.

## Grid (frozen before first run — 6 configs)

- N ∈ {10, 20}
- vol_target ∈ {0.20, 0.30, 0.40}

Nothing else varies. No second pass, no added axes after seeing results (house
pre-registration methodology; violations void the run).

## Benchmark

Per-N EW buy-and-hold of the same monthly top-N universe: equal weights set at each
monthly refresh, held within the month, same t+1 execution and 10 bps turnover costs.
SR comparison is scale-invariant, so no vol matching.

## Windows

- Dev: 2021-01-01 → 2025-03-31
- Holdout: 2025-04-01 → 2026-07-01 — **sealed, one-shot**, spent only if dev passes.
- Store coverage 2019-09+ → warmup satisfied at dev start.

## Gates (`trend_wide_t1`, registered in data/rebuild/gates.json before any run)

dev_select (winning config must clear ALL):
- net SR ≥ 1.0
- ΔSR vs matching EW benchmark > 0 with paired stationary-block bootstrap
  p_pos ≥ 0.90 (block 21, n = 2000)
- placebo p ≤ 0.05 under BOTH placebo families (gate on the WORSE of the two p-values),
  500 draws each, costs re-applied to shifted weights,
  p = (1 + #{placebo SR ≥ real SR}) / (N + 1):
  - (a) per-coin independent circular time-shifts of the final daily weight series —
    nulls per-coin directional timing (caveat: breaks cross-coin co-activation);
  - (b) shared-offset circular time-shift (one offset for all columns per draw) —
    preserves cross-coin regime co-activation, nulls calendar alignment; guards against
    fake significance from correlated regime exposure (task-3 review finding, amended
    2026-07-28 BEFORE gates registration).
- DSR ≥ 0.9 computed over the 6-config grid
- tiebreak: highest DSR, then lowest placebo p

holdout_deploy (one-shot, only if dev_select passes):
- net SR ≥ 0.5, ΔSR vs benchmark > 0, p_pos ≥ 0.85, placebo p ≤ 0.05
- fresh halt-latch semantics per house rule; SR := 0 on zero variance

Any failure → honest negative recorded in THESIS §45; holdout stays sealed (dev fail)
or verdict stands (holdout fail). Trial ledger rows written for every run.

## Error handling

- Missing kline mid-position: coin contributes 0 that day; no weight redistribution.
- Zero-variance return series: SR := 0 (house convention).
- σ NaN / < 30d of data: weight 0 that day.
- Universe refresh yielding < N eligible coins: use all eligible (log count).

## Testing

1. Vote parity: fixture from metalabel worktree, assert identical votes on BTC slice.
2. No-look-ahead probe: mutate close at day t, assert all positions/weights ≤ t
   unchanged (forensic discipline).
3. Delisting: synthetic coin ends mid-month → forced exit + cost on last bar.
4. Cost accounting: 2-coin toy, hand-computed turnover vs engine.
5. Placebo kill-test: synthetic trending series where real signal earns — placebo
   distribution must center at ~0 and real SR must exceed it (mutation kill-test).
6. Benchmark mechanics: EW B&H toy with known return path.

## Deliverables

- `tradingagents/xsect/trend.py` (runner + placebo + benchmark)
- `scripts/trend_wide_dev.py` (dev grid, ledger writes)
- gates.json `trend_wide_t1` entry + trial ledger rows
- `tests/test_xsect_trend.py`
- THESIS §45 section (either outcome)
