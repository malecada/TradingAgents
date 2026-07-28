# Cross-Sectional Funding-Carry L/S (wide perp universe) — Design

Date: 2026-07-28
Status: approved (brainstorm session 2026-07-28)
Registration: gates.json entry `carry_xs_t1` (to be written BEFORE any experiment run)

## Background and provenance

Executes lead #3 of the post-§44 go-forward menu (SUPERVISOR_REPORT_2026-07-28 §6),
after lead #1 (spillover) was dropped pre-registration and lead #2 (wide trend) closed
dev-gate negative (§45).

Prior internal evidence (§32, §39, §41): the BTC/ETH spot-hedged funding-carry sleeve
passed its dev GO gate but **failed the pre-registered holdout one-shot** on the
risk-free margin opportunity-cost hurdle — a ~0.4% ann-vol sleeve cannot clear T-bills.
Critically, **funding income itself held out-of-sample** (+7.53 as-built SR; +1.93
after trading frictions). The failure was capital efficiency, not fake signal. §41
mandates that any carry revival be a NEW pre-registered cycle with the margin-cost
convention decided upfront. This design is that cycle.

External anchor (motivation only, unverified): practitioner evidence that carry IC is
strongest and stickiest cross-sectionally in crypto perps (Robot Wealth). BIS WP 1087
documents naive (time-series, spot-hedged) carry as structurally compensated risk —
consistent with our §41 negative; the cross-sectional relative-rank form is a distinct
hypothesis it does not address.

## Decisions taken at brainstorm (all pre-registered here)

1. **Construction: perp-only dollar-neutral L/S deciles.** Short high-funding perps
   (receive funding), long low/negative-funding perps (receive or avoid paying). No
   spot leg. Portfolio vol will be tens of percent, not 0.4%, so the rf drag that
   killed the old sleeve is proportionally small. Rejected alternatives: widened
   spot-hedged sleeve (repeats the capital-inefficiency failure mode; needs alt spot
   data), long-flat funding filter (overlay family, weaker prior).
2. **t1 = pure CS funding sort.** Clean single hypothesis. The carry × trend/breakout
   interaction (noted negative correlation) is a potential t2 ONLY if t1 shows signal.
3. **rf convention: deduction on full capital.** T-bill daily rate deducted from
   strategy returns on 100% of capital, then gate on net SR. Harshest honest
   convention — deliberately the same one that killed the old sleeve, so a pass is
   unambiguous and convention-shopping criticism is impossible.

## Build approach

**A (chosen): new module `tradingagents/xsect/carry_xs.py`** plus a funding-history
fetch script, reusing from `feature/xs-momentum`: `universe.eligibility` (799-symbol
survivorship-safe klines store), portfolio/SR/DSR helpers, dual-family placebo,
trial ledger + gates infra. New code is only the funding store and the funding-rank
L/S weight builder.
Rejected: B — extend `strategies/carry_sleeve.py` (spot-hedge structure, per-coin
API, wrong shape for cross-sectional L/S); C — generalize `trend.py` with pluggable
signals (long-flat weight/cost path differs from dollar-neutral L/S; YAGNI).

## Signal

Per symbol, trailing mean **daily funding income** over lookback L days, where daily
funding = **SUM of the day's 8h funding prints** (carry_sleeve lesson: `groupby.mean()`
undercounts 3×). Realized prints only (no predicted next-funding), timestamped at
print time → point-in-time safe at decision close t. Daily cross-sectional rank
within the current universe.

## Universe

Existing PIT eligibility (`tradingagents/xsect/universe.eligibility`): USDT-M perp
with kline on day D, first kline ≤ D−30, 30d median quote-volume ≥ $5M; rank by 30d
median quote-volume; keep **top-50**. Monthly refresh at first-Monday close using
data ≤ that close. Additional requirement: a symbol must have ≥ max(L, 30) days of
funding history at decision time or it is skipped that month; since the grid caps
L at 30, this is a constant 30-day requirement, so the universe is identical across
all 6 configs (required for grid-level DSR comparability). A coin leaving the
universe (rotation or delisting) is force-flattened at the next bar with turnover
cost; mid-month delisting exits at last available close.

Leg membership is refreshed **daily** inside the monthly universe (funding ranks move
fast; universe membership does not).

## Portfolio construction

At decision close t, within the 50-symbol universe:

- SHORT leg: top `leg_frac × 50` symbols by trailing funding signal.
- LONG leg: bottom `leg_frac × 50` symbols.
- Equal weight within each leg; each leg 50% of capital → gross 1.0, net 0.
- No vol targeting and no per-symbol vol scaling in t1 (keeps the hypothesis clean;
  also avoids re-introducing the §43 vol-selection mechanism through sizing).

**Vol-selection diagnostic (post-hoc, NOT a gate):** report rank-correlation between
the funding signal and 30d realized vol across the universe, and per-leg mean vol.
§43 showed CS sorts can select on vol rather than the named characteristic; this
diagnostic is recorded with results either way.

## P&L, execution, costs

Decision at close t → weights apply from bar t+1 (causal next-bar accrual, corrected
harness convention). Daily portfolio log-return:

```
r_p(t+1) = Σ_i w_i · r_i(t+1)                    price leg (w signed, long > 0)
         − Σ_i w_i · funding_daily_i(t+1)        funding accrual: long pays positive
                                                  funding, short receives (sign via w)
         − 0.0010 · Σ_i |Δw_i|                   10 bps per side on turnover
         − rf_daily(t+1)                          3M T-bill on full capital
```

- Funding accrual uses realized prints of day t+1 (position holds through prints).
- Turnover cost charged on the first accrual day after each weight change; weights
  change daily (rank churn) and monthly (universe rotation).
- rf source: FRED 3-month T-bill (DTB3), forward-filled to daily, /365.
- Missing kline for a held member: contributes 0 that day, weights not redistributed
  intra-period (store convention, matches trend_wide).

## Grid (frozen before first run — 6 configs)

- L ∈ {1, 7, 30} (signal lookback, days)
- leg_frac ∈ {0.10, 0.20} (5 or 10 symbols per leg at N=50)

N=50 fixed. Nothing else varies. No second pass, no added axes after seeing results
(house pre-registration methodology; violations void the run).

## Windows

- Dev: 2021-01-01 → 2025-03-31
- Holdout: 2025-04-01 → 2026-07-01 — **sealed, one-shot**, spent only if dev passes.
- Klines store covers 2019-09+; funding history fetched from each symbol's listing.

## Gates (`carry_xs_t1`, registered in data/rebuild/gates.json before any run)

dev_select (winning config must clear ALL):

- net SR ≥ 1.0 (net of turnover costs, funding accrual, and rf deduction)
- placebo p ≤ 0.05 under BOTH families (gate on the WORSE p-value), 500 draws each,
  p = (1 + #{placebo SR ≥ real SR}) / (N + 1), with turnover costs AND funding
  accrual re-applied to shifted weights:
  - (a) per-coin independent circular time-shifts of the final daily weight series;
  - (b) shared-offset circular shift (one offset for all columns per draw).
- DSR ≥ 0.9 computed over the 6-config grid with ledger-cumulative n_trials
- tiebreak: highest DSR, then lowest placebo p

No relative benchmark gate: the portfolio is dollar-neutral, so the natural
benchmark is cash and the rf deduction already embeds it.

holdout_deploy (one-shot, only if dev_select passes):

- net SR ≥ 0.5, placebo p ≤ 0.05 (worse-of families)
- fresh halt-latch semantics per house rule; SR := 0 on zero variance

Any dev failure → honest negative recorded in THESIS §46; holdout stays sealed.

## Data build: funding store

Fetch full funding-rate history for all 799 store symbols via Binance
`GET /fapi/v1/fundingRate` (free, paginated 1000 rows, ~2–3M rows total). Store as
per-symbol parquet + manifest beside the klines store (`data/xsect/funding/`),
idempotent tail-append (no date-embedded filenames — house rule).

**Known risk — delisted-symbol funding coverage.** The API may return empty history
for delisted perps, which would punch survivorship holes in a store whose klines side
is survivorship-safe. Mitigation, run BEFORE registration is considered complete:
forensic coverage report matching funding symbols × date ranges against the klines
manifest, with honest denominators. If delisted coverage is materially incomplete,
the limitation is recorded in the registration itself (universe conditioned on
funding availability) before any backtest run.

## Testing (TDD, house discipline)

- Weight builder: rank correctness, leg sizes, dollar-neutrality (Σw = 0, Σ|w| = 1),
  daily leg refresh inside fixed monthly universe, force-flatten on rotation and
  delisting.
- Funding accrual sign: long pays positive funding, short receives; fixture-pinned
  SUM-of-prints daily aggregation parity.
- Engine: causal t+1 accrual (decision bar never accrues its own return), turnover
  cost on |Δw|, rf deduction wiring.
- Placebo kill-test: planted funding signal survives both families; shuffled signal
  does not.
- Forensic pass on any zero/negative result per house discipline (probes, mutation
  kill-tests, honest denominators).

## Deliverables

1. `data/xsect/funding/` store + fetch script + coverage report
2. `tradingagents/xsect/carry_xs.py` + tests
3. `carry_xs_t1` gates.json entry + trial-ledger rows
4. Dev-run results + report; THESIS §46 section either way
