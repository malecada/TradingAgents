---
title: "S1 Champion System — Overview, Terminology, UI Guide, and Performance Record"
date: 2026-08-23
geometry: margin=2.5cm
fontsize: 11pt
---

# S1 Champion System — Overview

**As of 2026-08-23.** This document describes the currently deployed Prediction Lab
system end to end: the strategy itself, every term used around it, the
infrastructure that runs it (paper trader, live executor, monitor), what each
element of the monitoring UI shows and how to read it, and the performance record
to date. It is a reference document; the authoritative registrations live in
`data/predlab/gates.json` and the design documents under `docs/superpowers/specs/`.

## 1. What the system is, in one paragraph

The champion is a **daily-rebalanced, market-neutral long–short portfolio of
cryptocurrency perpetual futures** built on a single anomaly: within the most
liquid ~200 USDT-perpetual contracts on Binance, coins with **low recent price
volatility** have tended to outperform coins with high recent volatility. Each
day the system ranks the universe by a smoothed volatility estimate, buys the
calmest quintile (40 names), shorts the most volatile quintile (40 names), equal
weight on both sides, and scales the whole book so the portfolio targets 15%
annualized volatility. No machine learning, no LLMs, no prediction of returns —
the signal is a ranking of realized volatility. The system was selected through
a pre-registered research program (Phase O, ~90+ trials, deflated-Sharpe
accounting) and is now in a **sealed forward test**: a paper trader journals the
book daily on a VPS, a live executor mirrors that book (currently on Binance
testnet, real $3,000 planned), and a web monitor displays both.

## 2. Strategy definition

### 2.1 Universe

- All Binance **USDT-margined perpetual futures** with contract status TRADING
  (~400+ symbols at any time).
- Each calendar month, membership is frozen: the **top 200 symbols by median
  daily dollar volume over the prior month** (a ~35-day pre-month window). Using
  the *prior* month prevents the ranking from peeking at the month being traded
  (point-in-time discipline), and monthly freezing keeps turnover from
  membership churn low.

### 2.2 Signal — `ewma_20` of Parkinson variance

- For each symbol and day, compute the **Parkinson variance estimate**
  `ln(high/low)² / (4·ln 2)` from the daily candle. The Parkinson estimator uses
  the intraday high–low range, which is a more efficient volatility proxy than
  close-to-close returns.
- Smooth it with an **exponentially weighted moving average with span 20**
  (`ewma_20`): recent days dominate, weights decay geometrically, ~20-day
  effective memory.
- The smoothed value is the signal: **low = attractive (long), high =
  unattractive (short)**.

### 2.3 Portfolio construction — quintile long–short

- Rank the 200 members by the signal. **Long the lowest quintile (40 names),
  short the highest quintile (40 names).**
- **Equal weight** within each side: every long +2.5% of one book unit, every
  short −2.5%. Sides sum to +1 and −1, so the book has **gross exposure 2.0**
  (2× capital deployed across both sides) and net exposure ≈ 0 (market-neutral
  by construction — a broad market move hits longs and shorts alike).
- Rebalanced **daily at the UTC close**. Realized one-way turnover averages
  ~0.22 book units/day for the champion book (most names stay in their quintile
  day to day).

### 2.4 Overlay — `vt15_b100` (volatility targeting + breadth floor)

The raw book's volatility drifts with the market. The overlay resizes it:

- **Vol target 15%**: `scale = 0.15 / realized_vol`, where realized_vol is the
  annualized standard deviation of the book's last 20 **gap-free** daily
  returns. If the book has been running hot at 68% annualized vol, scale ≈ 0.22
  — only ~22% of capital-equivalent exposure is deployed.
- **Scale cap 2.0**: leverage never exceeds 2× the base book even in dead-calm
  regimes.
- **Warm-up**: the scale is undefined (`null`) until **21 consecutive gap-free
  daily returns** exist. Until then the paper journal records the unscaled book
  and any live trading waits.
- **Breadth floor 100**: if fewer than 100 universe members have a valid signal
  on a given day (a data-quality symptom), the scale is forced to 0 — the book
  goes flat rather than trade a degraded universe.

### 2.5 Costs

All backtest and forward accounting assumes **taker fees** on every unit of
turnover (`TAKER_BP`, ~5 bp per side). At ~0.22 daily turnover this costs ~1 bp/day.
Fill realism beyond the fee (queue, impact, timing) is exactly what the live
executor phase measures.

### 2.6 Parameter summary

| Parameter | Value |
|---|---|
| Universe | Top 200 Binance USDT-perps, prior-month median dollar volume, monthly frozen |
| Signal | ewma(span 20) of daily Parkinson variance |
| Book | Quintile long–short, 40L/40S, equal weight, gross 2.0 |
| Rebalance | Daily, UTC close |
| Overlay | Vol target 15%, 20-day gap-free window, scale cap 2.0, breadth floor 100 |
| Costs | Taker fees on turnover |

## 3. Terminology glossary

| Term | Meaning |
|---|---|
| **Parkinson variance** | Volatility estimate from the daily high–low range: `ln(H/L)²/(4 ln 2)`. More statistically efficient than squared close-to-close returns. |
| **EWMA (span 20)** | Exponentially weighted moving average; recent observations weighted most, ~20-day effective memory. |
| **Quintile** | One fifth of the ranked universe (here 40 of 200 names). |
| **Gross / net exposure** | Gross = sum of absolute position sizes (2.0 here). Net = longs minus shorts (≈0 here → market-neutral). |
| **Vol targeting** | Scaling position size so the portfolio's realized volatility tracks a target (15%). Cuts size after volatile stretches, adds after calm ones. |
| **Scale (`vt15_b100_scale`)** | The overlay multiplier actually applied: 0.15/realized vol, capped at 2.0, `null` during warm-up, 0.0 when the breadth floor trips. |
| **Breadth** | Number of universe members with a valid signal on the day. |
| **`realized_book_ret`** | The day's raw book return (at gross 2.0, unscaled), computed close-to-close from the previous journal row's weights. **Not** an account return. |
| **NAV / account return** | Return on total capital: `scale × realized_book_ret`, compounded. This is the number that answers "if $10k is on the account and it made $1k, show +10%." |
| **`mark_px` / `realized_mark_ret`** | Prices snapshotted at the moment the journal row is written (minutes after the UTC close), and the book return measured between those snapshots. The difference vs the close-to-close return exposes what the "fills at the close" assumption hides. |
| **Slippage (bp)** | Execution shortfall vs an assumed price, in basis points (1 bp = 0.01%). Positive = cost. |
| **Sharpe ratio (SR)** | Annualized mean return divided by annualized volatility. The headline risk-adjusted performance number. |
| **Deflated Sharpe Ratio (DSR)** | Probability that the observed SR is not an artifact of testing many strategies: corrects for the number of trials, non-normality, and track length. DSR 0.913 = 91.3% confident the edge is real after multiplicity correction. |
| **Placebo test** | Re-running the backtest with the causal link deliberately broken (e.g. time-shifted signals). A strategy that still "works" under placebo is exploiting an artifact. |
| **Sealed one-shot forward test** | Pre-registered evaluation: criteria and date fixed in `gates.json` *before* any forward data existed. One evaluation, earliest 2027-01-02; no peeking-and-adjusting. |
| **Pre-registration** | Writing the hypothesis, method, and pass/fail gates into `gates.json` before running the experiment, so results cannot be cherry-picked after the fact. |
| **Journal-follower** | The live executor's design: it never computes signals; it reads the book the paper trader already journaled and reproduces it on the exchange. Signal parity is guaranteed by construction. |
| **Reduce-only order** | Exchange order flag: may only shrink an existing position, never open or grow one. Used for all closes and the emergency flatten. |
| **`minNotional` / `stepSize`** | Per-symbol exchange minimums: smallest order value (typically 5–50 USDT) and quantity granularity. Legs too small to clear them are dropped and logged. |
| **Implementation shortfall** | Total live-vs-paper performance gap: fees + slippage + dropped legs + timing. The quantity the live phase measures. |
| **Halt flag** | A file (`halt.flag`) whose presence blocks all executor trading. Written automatically on a daily-loss breach or manually via `close-all`; only manual removal resumes trading. |
| **Warm-up (21 days)** | Days of gap-free returns required before the vol-target scale is defined. |

## 4. Infrastructure

Everything runs on the Hetzner VPS (`46.225.169.184`); the laptop runs nothing.

### 4.1 Paper trader (`scripts/predlab_s1_paper.py`) — the registered forward test

- Hourly cron (minute 15); the first wake after the UTC day rolls does the work,
  later wakes exit cheaply (idempotent).
- Fetches daily candles for all perps from the public Binance API, rebuilds the
  book for the last complete UTC day, and appends one row per day to two
  journals under `predlab-data/predlab/s1_paper/`:
  - `journal_champion.jsonl` — the Phase-O champion (ewma_20, vt15_b100). **This
    is the sealed forward test record.**
  - `journal.jsonl` — the older S1 book (park_5 signal, vt10 overlay), kept
    for a separate registered confirmation.
- Each row: date, weights (40L/40S), realized return of yesterday's book,
  turnover and cost estimates, the vol-target scale, breadth, and the
  write-time price snapshot (`mark_px`) enabling the fill-assumption check.
- Rows are append-only and idempotent; journals are backed up daily (00:45 UTC)
  to a git branch. **No orders are placed by this component.**

### 4.2 Live executor (`scripts/predlab_s1_live.py`) — the measurement instrument

Purpose: measure what real execution costs. It chains after the paper cron and:

1. Reads the latest champion journal row (never recomputes signals).
2. Safety gates, in order: halt flag → daily-loss check (equity < 95% of
   day-start → flatten everything reduce-only + halt) → idempotency (day already
   executed → exit) → scale defined? (`null` → WAIT) → marks present? → hedge-mode
   check (account must be in one-way position mode).
3. Sizes each leg: `weight × min(scale, 1.1) × account equity`. The **1.1 clamp**
   exists because the overlay's own cap (2.0) would exceed the executor's risk
   rails; on days the overlay wants more, the live book is a proportionally
   smaller replica (recorded as `scale_raw` vs `scale` in the journal).
4. Diffs targets against actual exchange positions and places **market orders**
   for the deltas. Positions whose symbol left the champion book are always
   closed in full. Legs below exchange minimums are dropped and logged.
5. Risk rails (hard): gross ≤ 2.2 × equity, per-symbol ≤ 5% of gross, leverage 4,
   cross margin, 5% daily-loss halt, `halt.flag` kill switch, `close-all`
   emergency command.
6. Writes its own journals (`journal_live.jsonl`, `fills.jsonl`) with every
   fill's price and fee — the raw material for the slippage measurement.

**Rollout (current position in bold):**

| Phase | What | Status |
|---|---|---|
| Dry-run | Full pipeline, zero orders | done |
| **Testnet rehearsal** | Real orders on Binance *testnet* (`--testnet`, separate data dir). Plumbing validation only — testnet books are thin and fills there feed **no** conclusions. | **armed; first cycle expected 2026-08-25 ~00:15 UTC** (waiting for the 21-day scale warm-up: 19/21 as of Aug-23) |
| Live | $3,000 real USDT, after ≥2 clean testnet days and an explicit go/no-go | pending |

The live run is registered in `gates.json` (`predlab_s1_live`) as
**observational** — a measurement, not a pass/fail experiment; the sealed
forward test is unaffected by anything the executor does.

### 4.3 Monitor (web UI, `live-v2.7.2`)

FastAPI backend + React frontend served from the VPS behind password auth.
Reads the journals read-only every 30 s. Described in §5.

## 5. What the UI shows and how to read it

The monitor's Prediction Lab section has four tabs. Two books appear
throughout: **champion** (the system described above) and **vt10** (the older
park_5 book — context only).

### 5.1 Performance tab

- **Equity curves (base 100)** — each book's raw daily returns compounded from
  100. **This is the unscaled book at gross 2× exposure, before the overlay** —
  it answers "is the signal working?", not "what would an account have made?".
  The card is labeled *"Book return (gross 2× unscaled)"* for exactly this
  reason.
- **Account NAV (scaled)** — *new.* The overlay-adjusted, account-percent
  cumulative return: each day contributes `scale × book return`, where the
  scale used is the one that was known when the position was put on. **This is
  the number that scales to portfolio size** ($10,000 account, +10% shown →
  $1,000 made). Until the 21-day warm-up completes it shows *"overlay warming
  up n/21"* — no scale existed, so no scaled return is claimable; the series
  starts accruing 2026-08-25.
- **Account cards (testnet / live)** — *new.* Appear once the executor trades:
  actual account equity in USDT, cumulative % vs. starting equity (fees and
  slippage included — the truest performance number), cycle count, a **HALTED**
  badge if the halt flag is present, and a *(dry-run)* suffix where applicable.
  The gap between the paper NAV curve and this curve **is** the implementation
  shortfall being measured.
- **Fill slippage card** — mean and cumulative difference (bp) between the
  close-to-close return the journal assumes and the mark-to-mark return actually
  observable at write time. Negative mean = the close-fill assumption has been
  flattering the paper record. Only days since 2026-08-18 carry marks.
- **Rolling Sharpe (30d) and drawdown series** — risk-adjusted trend and
  peak-to-trough loss of the raw book.
- **Reference / backtest yearly** — the frozen dev-period metrics and yearly
  overlay returns from the registered backtest, for eyeballing forward vs.
  backtest.

### 5.2 Book tab

Today's portfolio composition: the 40 longs and 40 shorts with weights,
universe size, **breadth** (signal coverage; the floor is 100), **membership
hash** (fingerprint of the name list — parity checks against the executor),
estimated turnover and cost for the day, and how many names entered/exited
vs. yesterday.

### 5.3 Gate tab

The sealed one-shot forward test tracker — **informational only**; the actual
evaluation stays sealed:

- Window started 2026-07-02; earliest evaluation **2027-01-02**; days
  elapsed/remaining.
- Pass criteria, fixed in advance: net overlaid forward SR ≥ **0.946** (half the
  dev SR of 1.892), same sign as dev, time-shift placebo p < 0.10, one
  evaluation only.
- A running SR proxy from the paper journal — a progress glance, explicitly
  *not* the official evaluation (which uses the backtest harness on the sealed
  window).

### 5.4 Ops / Health tab

Freshness and integrity: last row age per journal (stale after 36 h), row and
malformed-line counts, calendar gaps (the 2026-07-31…08-02 VPS migration gap is
marked as known), and the daily journal-backup heartbeat note.

## 6. Performance record to date

### 6.1 Registered backtest (development, pre-registered; 2020–2026 data)

| Metric | Value |
|---|---|
| Overlay net Sharpe (full period) | **+1.892** |
| Max drawdown (overlay) | 17.6% |
| Deflated Sharpe Ratio | **0.913** (≥90% confidence after ~90+ trial correction) |
| Yearly results | 6 of 6 years positive |
| Phase-P S1 holdout (sealed, one-shot) | net SR **+2.20** — passed |

Supporting validation:

- **Venue replication (Bybit, 735 symbols):** champion applied verbatim on a
  different exchange's data — raw SR +1.94 / overlay +1.71, placebo clean, all
  folds positive. Robustness check (same market, so not an independent sample).
- **Capacity study:** square-root impact model puts the strategy at SR ≈ 1.0
  around **$21M** deployed and SR ≈ 0 around $91M; the binding constraint is
  short-leg small-caps. At $3K, capacity is a non-issue.
- **Cross-asset probes (equities, futures/FX):** the same recipe applied outside
  crypto perps is flat-to-negative — the edge is a crypto-perp phenomenon, which
  bounds how far the result generalizes.

### 6.2 Forward paper record (the sealed window, so far)

As of 2026-08-22 (19 return days for the champion):

| | Champion (ewma_20) | vt10 book (park_5) |
|---|---|---|
| Journal span | 2026-08-03 → 08-22 | 2026-07-30 → 08-22 |
| Cumulative return (raw book, gross 2×, unscaled) | **+34.7%** | +21.9% |
| Mean daily return | +183 bp | +110 bp |
| Annualized vol (raw book) | 68.5% | 60.6% |
| Naive annualized SR | +9.7 | +6.6 |
| Mean daily turnover / cost | 0.22 / 1.1 bp | 0.65 / 3.3 bp |
| Mark-to-mark check (4 days so far) | +19.6% | +6.2% |

**Read these numbers with three caveats:**

1. **They are unscaled book returns.** The overlay would have deployed only
   ~0.2× (15% target ÷ ~68% realized vol), so the account-equivalent
   ("NAV") return over the window is roughly **+7%**, not +34.7%. The UI's new
   NAV card exists precisely to prevent this misreading.
2. **19 days is a tiny sample in an unusually good stretch.** An audit placed
   this window around the **87th percentile** of the historical mean-return
   distribution. The anchored expectation remains the backtest's overlay SR
   ≈ 1.9, not 9.7.
3. **Costless fills assumed.** The close-to-close journal assumes frictionless
   fills at the close; the mark-to-mark leg and, from Aug-25, real testnet and
   then real-money fills progressively replace that assumption with data.

### 6.3 Live execution status

- Executor deployed and armed on the VPS; every hourly wake currently exits
  `WAIT` (scale warm-up 19/21). First testnet trading cycle expected
  **2026-08-25 ~00:15 UTC**; the testnet account's 7 leftover positions will be
  flattened on that first cycle (an incidental live test of the close path).
- Success criteria for the testnet phase: ≥2 consecutive clean days (journal row
  each day, zero unexplained order errors, positions matching targets for
  symbols listed on testnet). Then a go/no-go decision gates the $3,000 live
  phase, whose watch procedure is in `docs/predlab/s1_live_runbook.md`.

## 7. Governance summary

Every claim above is bounded by the pre-registration discipline: the champion's
configuration and pass criteria were frozen in `gates.json` before the forward
window opened; the forward evaluation is one-shot and sealed until 2027-01-02;
the live run is registered as observational and cannot be promoted into
evidence for the gate; and the raw-vs-scaled distinction in the UI keeps the
headline numbers honest. The corresponding thesis sections are §54–§61.
