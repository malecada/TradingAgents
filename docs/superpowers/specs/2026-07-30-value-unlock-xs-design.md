# Cross-Sectional Crypto Value + Token-Unlock Burden — Design

Date: 2026-07-30
Status: approved (brainstorm session 2026-07-30)
Registration: gates.json entries `value_xs_t1` and `unlock_xs_t1` (to be written BEFORE any experiment run)

## Background and provenance

Executes lead #7 of the post-§44 go-forward menu (SUPERVISOR_REPORT_2026-07-28 §6) plus
one new hypothesis surfaced during the 2026-07-30 data-source audit.

Lead #7 (crypto value factor) had been recorded as **data-blocked**. That classification
was wrong, and was scoped to the Glassnode UTXO tier only. Live probing on 2026-07-30
established that the CoinMetrics **community** API (free, no key) serves `AdrActCnt`,
`TxCnt` and `CapMrktCurUSD` from 2017 for **132 assets**, including delisted names
(`ftt`, `srm`, `lend`, `ant`), so it inherits the survivorship safety of the 799-symbol
perp store. Intersecting the two and removing stablecoin and pegged names (`usdc`,
`frax`, `paxg`, `xaut`) leaves **63 candidates**. `TxTfrValAdjUSD` is not in the free
tier, so classic NVT (market cap ÷ transfer value) is unavailable; activity-based
ratios are.

The second experiment comes from the same audit. `defillama-datasets.llama.fi/emissions/`
serves, free and unauthenticated, full token vesting schedules for **359 protocols** —
per-allocation daily curves spanning past and future, plus a timestamped event log.
**129** of those protocols have a tradeable Binance perp. Dated, ex-ante-known supply
shocks are a hypothesis family the programme has never tested, and unlock dates being
public in advance makes the signal point-in-time by construction. (The `api.llama.fi/emissions`
route is 402-gated; the `defillama-datasets` host is not. Coinglass sells nothing
comparable: its unlock endpoints are current-snapshot and forward-only, with no
historical event series.)

External anchor (motivation only, unverified): the C-4 factor-model literature reports
value as the dominant robust crypto factor post-2020. No external study is claimed for
the unlock hypothesis; it is exploratory.

Lead #5 (RV forecasting → sizing overlay) is **retired without being run** — see the
final section for the reasoning.

## Decisions taken at brainstorm (all pre-registered here)

1. **Two independent registrations, one spec.** `value_xs_t1` and `unlock_xs_t1` get
   separate gates.json entries and separate DSR denominators, sharing this design
   document, the data-layer work, and the gate shape. Precedent:
   `2026-07-14-xs-mom-fg-beta-prereg.md`.

2. **DSR denominator amendment, declared before any data is touched.** DSR is gated at
   each experiment's **own** trial count (4 and 2). The ledger-cumulative count is
   computed and reported alongside, **gated on nothing**. Rationale: multiplicity
   correction attaches to the search that produced the candidate. A momentum grid from
   §43 has no bearing on whether a value factor is real. Precedent: the `liq_fade_r1`
   amendment, likewise declared pre-run with alternative denominators reported so the
   choice stays auditable. The trial ledger stands at 120 rows / **100 unique
   `config_hash`** at the time of writing; both denominators appear in every reported
   result. This amendment is made for a new hypothesis family before any result exists,
   not to rescue a failing one — §49's DSR failure is explicitly **not** revisited or
   relaxed by it.

3. **Sequencing.** Shared data layer first, then `value_xs_t1`, then `unlock_xs_t1`, so
   the second registration records the true ledger state at its own run time.

4. **Weekly rebalance, frozen, not an axis.** Both signals move on monthly timescales;
   daily rebalancing buys turnover cost and no signal.

5. **PIT liquidity floor plus a vol-matched control on both experiments.** §43's
   cross-sectional momentum result turned out in forensics to be a vol-selection
   mechanism. The control that would have caught it prospectively is pre-registered here
   as a gate, not left to post-hoc diagnosis.

6. **No post-hoc exclusions.** Binding stop rule — see below.

## Build approach

New branch off `feature/xs-momentum` (which carries the xsect engine, dual-family
placebo, `dsr.py`, `ledger.py`, and the monthly PIT universe selector). Not off `main`.

Two thin signal engines, `tradingagents/xsect/value_xs.py` and
`tradingagents/xsect/unlock_xs.py`, delegating portfolio construction, placebo, DSR and
ledger writes to the existing shared modules. Shape follows `carry_xs.py` so the diff
against §46 stays readable.

---

## Experiment A — `value_xs_t1`

### Signal

Two value metrics, both on 30-day means to damp chain-level noise:

```
nvt_proxy      = CapMrktCurUSD / mean(TxCnt, 30d)
metcalfe_proxy = CapMrktCurUSD / mean(AdrActCnt, 30d)
```

Log-transformed (both ratios are heavy-tailed across a 63-name crypto cross-section),
then cross-sectionally z-scored per rebalance date. Low ratio = cheap = long leg.

### Universe

The 63 candidates, further restricted by a monthly point-in-time liquidity floor using
the existing `liq_fade` universe selector: a name is eligible for month `m` if its
median daily quote-asset volume over month `m−1` places it in the **top 150** of the
799-symbol perp store. The rank threshold is frozen here and is not a search axis.
Effective daily breadth is a Task-1 reported number, not an assumption.
**Pre-registered breadth STOP**: if median daily breadth after the floor is below 20
names, the experiment closes NEGATIVE-at-probe — a decile sort on fewer than 20 names is
not a decile.

Return series for P&L is the daily close-to-close simple return of the corresponding
`USDT` perp from `data/xsect/klines/`, consistent with the cross-sectional convention
used in §43/§45/§46 (trend and carry use log returns; cross-sectional sorts use simple —
do not swap).

### Timing and lag

CoinMetrics publishes day-`t` metrics with a delay. Pre-registered conservative
convention: features as of `t−2`, position effective `t+1`. P0 measures the actual
publication lag against the store's own arrival stamps. If the measured lag exceeds
2 days, the lag is widened before the grid runs and the widening is logged as a
pre-result amendment.

### Controls (both gating)

- **C1 vol-matched** — sort on trailing 30d realized volatility alone, identical
  pipeline.
- **C2 reversal** — sort on `−(past 30d return)` alone, identical pipeline. Necessary
  because `CapMrktCurUSD` embeds price: a coin looks cheap mainly because it fell, so
  the null hypothesis is that `mcap/activity` is a slow reversal factor in a fundamental
  costume.

A config clearing the absolute Sharpe bar but failing either ΔSR control is NEGATIVE.

### Grid (frozen before first run — 4 configs)

2 metrics (`nvt_proxy`, `metcalfe_proxy`) × 2 breadths (decile, tercile). Dollar-neutral
long-short. Rebalance frequency is not an axis.

### Probes (STOP on fail, run before the grid)

- **P0** — publication-lag and stamp alignment.
- **P1** — breadth floor (≥20 names median, per above).
- **P2** — monotonicity: the cheap-to-expensive decile spread must be ordered in the
  expected direction on dev, on at least one metric, before any P&L is computed.

---

## Experiment B — `unlock_xs_t1`

### Signal

```
unlock_burden(t, N) = tokens_unlocking(t, t+N] / circulating_supply(t)
```

Rank the cross-section, short the high-burden decile, long the low-burden decile,
dollar-neutral.

### Point-in-time schedule reconstruction

`metadata.events` in the DefiLlama emissions payload carries a timestamp on every
schedule change, including amendments (e.g. *"linear unlock was increased from X to Y
tokens per week"*). The schedule as known at time `t` is therefore recoverable: replay
the event list in timestamp order and apply only events with `timestamp ≤ t`. This
yields a genuinely point-in-time forward unlock curve rather than today's amended one,
and it allows linear unlocks to remain in scope rather than being discarded by a
cliff-only restriction.

**Residual hazard, stated plainly**: DefiLlama may have silently corrected bad data
without emitting a timestamped event, and a single snapshot cannot detect that. P0
quantifies it.

### Universe

The 129 protocols with a tradeable perp, same monthly PIT top-150 liquidity floor, same
≥20-name breadth STOP, same simple-return convention. Coverage is thin early — most of
these had their TGE in 2021 or later — so breadth is reported **per year**. If the dev
window's first two years fall below the floor, the dev window is truncated forward and
the truncation is logged before the grid runs.

### Controls (both gating)

- **C1 vol-matched** — as in Experiment A.
- **C2′ size** — sort on log market cap alone. Reversal is not the confound here (no
  price in the numerator); size is, because high unlock burden concentrates in small,
  young tokens. Market cap for this universe is computed as `perp close price ×
  as-of-t circulating supply` from the same reconstruction that produces the signal
  denominator — not from CoinMetrics, since the 129 unlock names and the 132
  CoinMetrics names are largely disjoint.

### Grid (frozen before first run — 2 configs)

`N ∈ {14, 30}` days, decile breadth only, weekly rebalance.

### Probes (STOP on fail, run before the grid)

- **P0** — supply reconstruction: as-of-`t` circulating supply compared against an
  independent series (CoinMetrics `SplyCur` where covered, CoinGecko circulating
  otherwise) across overlap names. A systematic divergence growing toward the present is
  the signature of silent restatement and is a STOP.
- **P1** — breadth floor, reported per year.
- **P2** — event study: mean forward return around **large** cliff unlocks must carry
  the expected negative sign before any portfolio P&L is computed, where large is frozen
  as a cliff releasing **≥ 1% of circulating supply** on a single date, and forward
  return is measured over `t+1 … t+14`. Mirrors §49's P2 gate.

---

## Shared: portfolio construction, P&L, execution, costs

Dollar-neutral long-short, equal weight within leg, weekly rebalance, positions
effective `t+1` from features known at `t` (or `t−2` for Experiment A per its lag
convention). Costs 10 bps/side on `|ΔW|`; risk-free 4.5%/yr charged on full capital.
Identical to §46 and §49 so results are directly comparable to those negatives.

## Windows

Dev `2021-01-01 → 2025-03-31`. Holdout `2025-04-01 → 2026-07-01`, **sealed and unspent**.
No holdout access at dev-gate stage under any outcome.

## Gates

Registered in `data/rebuild/gates.json` as `value_xs_t1` and `unlock_xs_t1` before any
run. Identical shape for both:

| Gate | Bar |
|---|---|
| net SR | ≥ 1.0 |
| ΔSR vs C1 (vol-matched) | > 0 |
| ΔSR vs C2 / C2′ (reversal / size) | > 0 |
| dual-family placebo, 500 draws each | worse-family p ≤ 0.05 |
| DSR | ≥ 0.9 at own n (4 / 2) |
| DSR at ledger-cumulative n | computed and reported, **gated on nothing** |

Placebo families: (A) per-symbol circular shift of the signal series; (B) count-matched
random re-assignment of cross-sectional ranks among eligible names. `p = (1 + #{placebo
SR ≥ real SR}) / (N + 1)`, costs and rf re-applied inside every draw, gate on the worse
family.

Conventions frozen: `sqrt(365)` annualization on daily net returns, `ddof=1`,
zero-variance SR := 0. Tiebreak: highest DSR, then lowest placebo p.

`holdout_deploy` (pre-registered, one-shot, not reachable this cycle unless the dev gate
passes): net SR ≥ 0.5, placebo p ≤ 0.05, halt latch fresh per evaluation window.

## Stop rule

**No post-hoc exclusions.** If a single symbol or period dominates the result, it is
disclosed in forensics and the verdict stands as computed. Precedent: the `liq_fade_r1`
FTT episode, where one symbol drove 160% of the pooled sum and ex-FTT would have flipped
the sign — the honest handling was disclosure without action, and the same rule binds
here. Any amendment must be declared before the result it affects is read.

## Data build

Two new point-in-time stores, both following the `fetch_xsect_klines_1h.py` pattern —
per-month coverage manifest, confirmed-404 sidecar, interior gaps retried rather than
silently skipped:

- `data/xsect/fundamentals/` — CoinMetrics community `AdrActCnt`, `TxCnt`,
  `CapMrktCurUSD` for the 63 names.
- `data/xsect/unlocks/` — DefiLlama emissions snapshots for the 129 protocols, plus the
  as-of-`t` reconstruction module.

Both carry an explicit **vintage stamp** recording fetch date and source URL. Every
vendor in this stack restates; a store without a vintage stamp cannot later be checked
for it.

## Testing (TDD, house discipline)

Tests written before implementation, per task. Beyond unit coverage, the forensic
negative-verification discipline applies — a zero result must be shown to be a real
zero rather than a broken harness:

- **Mutation kill-tests** on signal construction: shift by one bar, flip sign. Tests
  must fail.
- **Planted-signal test**: inject known alpha into the return series; the harness must
  recover it.
- **Placebo machinery independently re-derived** with fresh draws; non-degeneracy
  (spread of the placebo distribution) checked and reported.
- **Honest denominators** throughout: names per day, events per year, configs run —
  reported alongside every pass/fail, never only the verdict.
- **Frozen-config tests** pinning the `config_hash` inputs, so a silent change to the
  grid cannot alter the DSR denominator undetected.

## Lead #5 retirement (no code)

Lead #5 proposed an RV-forecast sizing overlay, with a stated honest ceiling of
drawdown reduction rather than alpha (V4 precedent). Two findings from this session
close it without an experiment:

1. The sizing path **already vol-targets**. `vol_targeted_size` in
   `tradingagents/strategies/v2_sizing.py` computes `base = target_vol / realized_vol`
   on a 20-day trailing window. The lead therefore reduces to swapping one vol estimator
   for another inside an overlay that already exists — a far smaller hypothesis than the
   menu implies.
2. The stated ceiling is **already occupied**. Across all 18 configs of the §41 factor
   floor, maximum observed drawdown is 15.2% — the 15% portfolio circuit breaker, not
   the strategy, sets the drawdown. An overlay's remaining available effect is delaying
   or avoiding the halt trip, which is a single path-dependent event per coin rather
   than a repeatable edge. Any measured "improvement" would largely be one halt date
   moving.

Recorded as THESIS §53, negative-by-design, with the reasoning above. Revival would
require a base whose drawdown is set by the strategy rather than the circuit breaker.

## Deliverables

- `docs/superpowers/specs/2026-07-30-value-unlock-xs-design.md` (this file), committed
  before any data work.
- `gates.json` entries `value_xs_t1`, `unlock_xs_t1`, committed before any run.
- PIT stores `data/xsect/fundamentals/`, `data/xsect/unlocks/` with vintage stamps.
- Engines `tradingagents/xsect/value_xs.py`, `tradingagents/xsect/unlock_xs.py` + tests.
- Dev runners with probes P0–P2 per experiment; grid runners writing ledger rows.
- Forensics scripts and reports for whichever outcome occurs.
- THESIS §51 (`value_xs_t1`), §52 (`unlock_xs_t1`), §53 (lead #5 retirement).
