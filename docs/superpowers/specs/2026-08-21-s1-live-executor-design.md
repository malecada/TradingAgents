# S1 Champion Live Executor — Design

**Date:** 2026-08-21
**Status:** Approved design (chat), pre-implementation
**Branch:** `research/prediction-lab`

**Amended 2026-08-21 (post final review):** leverage raised 2→4 with a hard
`SCALE_CLAMP = 1.1` on the *executed* overlay scale (C2); daily-loss check
moved before the idempotency skip so it fires on every wake, not just the
first of the day (I1); a champion row with a live book but no marks now
WAITs instead of journaling a false-flat day (I2); book-departure closes no
longer require a same-day mark (C1). See Risk rails, Flow, and Sizing
sections below.

## Purpose

Measure real execution quality (fills, slippage, implementation shortfall) of the
Phase-O champion strategy by trading it with a small amount of real money
(~$2,000–5,000) on Binance USDT-M perpetual futures. Binance futnet (testnet) was
rejected: order books there are thin and unrepresentative, so testnet fills would be
*less* accurate than the existing mark-price simulation.

This is a **measurement run, not a registered thesis gate**. The registered forward
test remains the paper journal (`data/predlab/s1_paper/`, gates
`predlab_opt.final_champion`, sealed one-shot ≥ 2027-01). The live run is recorded in
`gates.json` only as an observational annotation — no pre-registered claim, no
pass/fail criterion attached to the sealed forward test.

## Hard constraints

1. **Paper journal untouched.** `scripts/predlab_s1_paper.py` and everything under
   `data/predlab/s1_paper/` are the registered forward test. The executor makes zero
   code changes to that path and never writes into that directory.
2. **Journal-follower.** The executor consumes the champion book already written by
   the paper trader (`journal_champion.jsonl` last row). It never recomputes signals.
   Signal parity with the paper record is therefore guaranteed by construction.
3. **Real-money rails.** Hard risk caps, a persistent halt flag, and an idempotency
   guard are mandatory before the first live order.

## Architecture

New code:

- `tradingagents/predlab/live_exec.py` — pure logic, fully unit-testable:
  sizing, rounding, min-notional filtering, position diffing, risk-cap checks,
  journal row construction.
- `scripts/predlab_s1_live.py` — thin CLI wrapper: reads journal row, talks to
  Binance signed REST API, applies `live_exec` logic, writes live journals.
  Subcommands: `run` (default), `run --dry-run`, `close-all`, `compare`, `status`.

Data (new directory, VPS authoritative like s1_paper):

```
data/predlab/s1_live/
  journal_live.jsonl   # one row per executed rebalance (UTC date keyed)
  fills.jsonl          # one row per order fill
  halt.flag            # presence blocks all trading; manual removal restarts
```

Cron (VPS): chained after the existing hourly paper-trader cron —
`predlab_s1_paper.py && predlab_s1_live.py run`. The executor exits fast when
`journal_live.jsonl` already has the champion journal's latest `asof` date
(idempotent, same pattern as the paper trader's `_already_done`).

Flow per run (reordered 2026-08-21, see I1/I2/C1/C2 amendment note above —
the daily-loss check now runs on every wake, before the idempotency skip):

1. Read last row of `journal_champion.jsonl`. (No journal row yet → `ERROR`, exit.)
2. If `halt.flag` exists → log and exit, no orders, **no API call at all**.
3. Fetch account equity and refresh/seed today's `day_equity.json`. Run the
   daily-loss check (needs equity) — on breach: fetch positions + filters,
   flatten (reduce-only, bypasses marks per point 7 below), write `halt.flag`,
   exit. This runs even on an hourly wake whose `asof` was already executed
   earlier in the day — equity is only ever read here, so checking it after
   the idempotency skip (the pre-amendment order) meant the breach could
   never fire on any wake but the first of the day.
4. If this `asof` already has a row in `journal_live.jsonl` → exit (idempotent
   skip). (Unparseable/torn lines are skipped, not fatal, when scanning.)
5. If `vt15_b100_scale` is `null` (vol window not yet accrued) → log `WAIT`, exit.
   A scale of `0.0` is a valid value meaning flat book (breadth floor tripped) —
   the executor then closes all positions.
6. If the champion row has a non-empty `weights` book but `mark_px` is
   null/empty → log `WAIT: champion row has no marks` and exit **without**
   writing a journal row (retry on a later wake or the next day) — a paper-
   trader data gap must not be silently journaled as a flat/no-op day.
7. Clamp the executed scale: `scale_executed = min(vt15_b100_scale, SCALE_CLAMP)`
   (`SCALE_CLAMP = 1.1`, see Risk rails). Fetch current positions and
   `exchangeInfo` filters.
8. Compute target notional per symbol: `w_i × scale_executed × equity`.
9. Round to `stepSize`; drop legs whose |notional| < symbol `minNotional` or whose
   qty rounds to zero at `stepSize` (log every dropped leg — measurement caveat).
   Empirically (2026-08-20 book, scale=1): equity ≥ ~$800 keeps 79/80 legs, only
   BTCUSDT drops (one step ≈ $73 > its per-leg target); ~$3,000 keeps all 80.
10. Diff targets against live positions → delta orders. Exposure-increasing deltas
    below the symbol's `minNotional` are dropped (Binance rejects them, error
    -4164); exposure-reducing deltas are sent `reduceOnly` (exempt from the
    filter) but skipped when < $7 (rebalance dust). A symbol that left the
    champion book entirely (target 0, position still open) is **always**
    closed in full reduce-only, bypassing the dust/min-notional checks and
    even when the symbol has no entry in today's `mark_px` — the paper
    trader only snapshots marks for the current book, so a departed symbol
    would otherwise never be flagged for pricing and would sit as a silent
    zombie position (fixed 2026-08-21, C1). Symbols that truly cannot be
    priced (live target, no mark) or cannot be rounded/ordered at all (no
    exchangeInfo filter — delisted/non-TRADING) are skipped and logged with
    a reason (`no_mark`, `no_filter`) instead of silently dropped.
11. Risk-cap check on the *post-trade* book (see Risk rails). Any violation →
    no orders at all, log ERROR.
12. Live path only: reject if the account is in hedge (dual-side position)
    mode (`GET /fapi/v1/positionSide/dual`) — the executor's reduceOnly
    semantics assume one-way mode throughout.
13. Place market orders (batch, sequential with pacing). Record each fill.
14. Append `journal_live.jsonl` row (`scale` = executed/clamped scale,
    `scale_raw` = the unclamped `vt15_b100_scale`); append fills to
    `fills.jsonl`.

## Sizing and orders

- **Capital source of truth:** live futures account equity, read each run. No
  config-file capital constant to drift.
- **Weights:** exactly the `weights` dict of the champion journal row
  (40L/40S, quintile-equal), times `scale_executed = min(vt15_b100_scale,
  SCALE_CLAMP)`.
- **Order type:** MARKET (taker). Matches the champion cost model (`TAKER_BP`) and
  produces honest taker slippage — the quantity being measured.
- **Position mode:** one-way, asserted before every live order batch (`ERROR`
  and no orders if the account is in hedge/dual-side mode). **Margin:**
  cross. **Leverage:** set to 4 per symbol at first touch (init subroutine,
  cached list of already-set symbols) — see Risk rails for why 4 (not 2).
- **Precision:** qty rounded down to `stepSize`; price fields untouched (market
  orders). `minNotional` from exchangeInfo `MIN_NOTIONAL` filter.

## Risk rails (all hard, checked before any order batch)

| Rail | Value | Action on breach |
|------|-------|------------------|
| Gross notional cap | ≤ 2.2 × equity | refuse whole batch, log ERROR |
| Per-symbol cap | ≤ 5% of gross target | refuse whole batch, log ERROR |
| Executed-scale clamp | `scale_executed = min(vt15_b100_scale, 1.1)` | sizing uses the clamp silently; `scale_raw` in the journal records the unclamped value |
| Leverage | 4x | set per symbol at first touch |
| Daily-loss halt | equity < 95% of day-start equity | close-all reduce-only, write `halt.flag` |
| Halt flag | `halt.flag` exists | no orders of any kind |
| Null scale | `vt15_b100_scale` is null | WAIT (no orders) |
| Null/empty marks | `weights` non-empty but `mark_px` null/empty | WAIT (no orders, no journal row) |
| Hedge mode | account in dual-side position mode | ERROR (no orders) |

**Why leverage 4 and a scale clamp of 1.1 (fixed 2026-08-21, C2):** the
champion book's gross weight is 2.0x; `vt15_b100_scale` can reach ~2.0, so
gross target notional can reach up to 4x equity. At leverage 2, required
margin is gross/2 — a scale above ~1.1 would exceed the 2.2x gross cap and
refuse the whole batch every wake (up to 24 refusals/day), and a scale above
~0.95 could partially fail on available margin. Leverage 4 (margin =
gross/4) plus clamping the *executed* scale to 1.1 keeps required margin and
the post-trade book comfortably inside the 2.2x gross cap in normal
operation — the gross cap remains a hard backstop but should never trip.
When the champion's raw overlay scale exceeds 1.1, the live run measures a
capped replica of the paper book, not the full-scale one; `scale_raw` in
`journal_live.jsonl` preserves the unclamped value for the record.

Day-start equity: persisted in `data/predlab/s1_live/day_equity.json` — the first
executor invocation of each UTC day (including no-op idempotent wakes) records
current equity for that date; the halt check reads it. Missing file (first ever
run) → seeded with current equity. The daily-loss check now runs before the
idempotency skip (see Flow), so every wake — not just the first of the day —
reads equity and can trigger the halt.

`close-all` subcommand: reduce-only market orders flattening every position; also
writes `halt.flag`. Manual flag removal is the only restart path.

API key: futures-trade permission only, withdrawals disabled, IP-whitelisted to the
VPS. Stored in `.env.trading` on the VPS (never in the repo).

## Journals

`journal_live.jsonl` row:

```json
{
  "asof": "2026-08-22",              // champion journal date executed
  "executed_utc": "...",             // when the executor ran
  "equity_before": 3000.0,
  "equity_day_start": 3010.0,
  "scale": 1.23,                     // executed scale (clamped to <= 1.1)
  "scale_raw": 1.23,                 // vt15_b100_scale before clamping
  "targets": {"BTCUSDT": 45.1},      // signed target notional per symbol
  "orders_placed": 62,
  "legs_dropped_min_notional": ["..."],
  "deltas_skipped_dust": 4,
  "gross_target": 6600.0,
  "halt": false,
  "dry_run": false
}
```

`fills.jsonl` row: `asof`, `symbol`, `side`, `qty`, `avg_price`, `quote_qty`,
`fee_usdt`, `order_id`, `ts_utc`.

## Slippage measurement (the deliverable)

The paper journal already snapshots `mark_px` (last traded price) at write time.
The executor runs immediately after that write, so:

- **Per-leg entry slippage:** `fill avg_price` vs the same-day `mark_px` of that
  symbol in the champion journal row, signed by trade direction, in bps.
- **Implementation shortfall:** live equity curve (from `equity_before` series and
  fills) vs the paper book curve (`realized_mark_ret` compounded, scaled).

`compare` subcommand: reads both journals, emits
`data/predlab/s1_live/compare_report.json` — per-leg bps distribution (mean, median,
p90, by side, by liquidity decile of the symbol) and cumulative shortfall. Monitor UI
wiring is out of scope (separate later task).

## Rollout

1. **Phase 1 — dry-run:** deploy to VPS, cron chained, `--dry-run` for ~1 day.
   Verifies: journal read, sizing, exchangeInfo filters, diff logic, intended-order
   logs sane, idempotency under hourly cron.
1b. **Phase 1b — testnet rehearsal (user-requested amendment 2026-08-21):**
   `--testnet` flag switches the executor to Binance futures testnet
   (`https://testnet.binancefuture.com`, keys `BINANCE_TESTNET_API_KEY/SECRET`,
   separate data dir `data/predlab/s1_testnet/`). Run a few days to validate
   plumbing end-to-end: orders accepted, precision/rounding, reduceOnly behavior,
   positions match journal targets, cron idempotency. Explicitly NOT a fill-quality
   measurement — testnet books are thin, and many of the 80 symbols are unlisted
   there (dropped with `no_filter` logs). Testnet fills never feed the slippage
   report's conclusions.
2. **Phase 2 — live:** fund account ($3,000), user go/no-go, remove `--dry-run`
   and `--testnet`. First live day manually observed.
3. gates.json: add observational annotation `predlab_s1_live` (start date, capital,
   no claim). Ledger row via `registry.log_trial()` marking the run as
   observational.

## Testing

TDD (tests first) against `live_exec.py` pure functions with stubbed exchangeInfo /
positions / journal rows:

- sizing: weights × scale × equity → notional targets
- rounding to stepSize; min-notional drop list
- diff logic: target vs current positions → deltas; dust threshold
- risk caps: gross, per-symbol, daily-loss trigger
- halt flag and null-scale behavior (no orders)
- idempotency: same `asof` twice → no orders
- scale 0.0 → close-all targets

No network in unit tests. Existing predlab suite (156 tests) must stay green.
`--dry-run` on VPS serves as the integration test.

## Out of scope

- Monitor UI slippage-vs-live tab (later task)
- Stop-losses / intraday risk management beyond the daily-loss halt (champion is a
  daily-rebalance strategy; intraday SL would change the strategy being measured)
- Trading the old `journal.jsonl` (park_5 / vt10) book — champion only
