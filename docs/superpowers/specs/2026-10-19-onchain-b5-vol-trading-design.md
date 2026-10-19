# Branch B5 — exchange flows against the option market: forecast comparison and straddle backtest

Status: design approved in conversation 2026-10-19, written before any B5 data read or
outcome. Branch `research/onchain-replication-b-2026-10-12`. B4
(`research/onchain-b4-2026-10-15/`) confirmed on its one-shot sealed window that hourly
stablecoin and ETH exchange-flow intensity improves next-6-hour ETH realised-volatility
forecasts over a price/volume baseline (−6.6 % and −3.4 % squared error), with the
qualifier that a richer intraday baseline explains most of the 2019–24 gain. B5 asks
whether that information is worth anything against the option market's own price.

## 1. Decisions taken with the user (2026-10-19)

1. Historical data only for now; forward capture comes later as the confirmatory step.
2. Trading-oriented scope: short-dated implied volatility from Deribit option trades and
   a cost-aware straddle backtest, plus the BTC cross-check, an event study and a Tron
   USDT feasibility probe.
3. Framing: **exploratory with a pre-declared analysis plan.** The ETH 2025–26 window was
   opened in B4, and the closed rviv-p0 study used 2025–26 implied and realised
   volatility. B5 therefore makes no confirmatory claim: every analysis below is fixed
   before any B5 result, every result is reported, and nothing is tuned on 2025–26.

## 2. Questions

- **Q1 (forecast).** At a decision time before a Deribit daily expiry, does a forecast
  that adds exchange flows to price and option-market information predict realised
  volatility to expiry better than price and option-market information alone?
- **Q2 (trading).** After fees and bid–ask costs taken from real taker trades, does
  buying (or selling) the at-the-money straddle when the forecast differs from the
  implied volatility make money, and does the flow-augmented forecast make more than
  the forecast without flows?
- **Q3 (generality).** Do the same Ethereum-chain flows help for BTC?
- **Q4 (mechanism).** After large stablecoin inflows to exchanges, how do realised
  volatility and implied volatility move over the next 1–12 hours, compared with
  placebo activity spikes?
- **Q5 (coverage).** Can full-history USDT transfers on Tron and Tron exchange labels be
  obtained free?

## 3. Data

| Source | Content | Window | Storage |
|---|---|---|---|
| Deribit history API (`history.deribit.com`, `get_last_trades_by_currency_and_time`, `kind=option`) | every option trade: timestamp, instrument (expiry, strike, call/put), iv, price (coin), index_price, amount, direction (taker side), trade_id | ETH and BTC, 2021-03-24 → 2026-10-12 | one parquet per asset-day, ≈ 0.5 GB total |
| Deribit `get_volatility_index_data`, resolution 3600 | DVOL open/high/low/close | ETH and BTC, 2021-03-24 → 2026-10-12 | JSON |
| Binance klines 1 h | close, quote volume | ETHUSDT (B4 files), BTCUSDT 2017-08-17 → 2026-10-12 | JSON |
| B4 `features/hourly.parquet` | 32 registered hourly flow, gas and activity features | 2017 → 2026-10-11 | reused |

Raw API pages are not kept; each stored row keeps `trade_id` for deduplication. A day
whose download fails after retries is marked unavailable and excluded.

## 4. Decision schedules and implied volatility

Deribit daily options expire at 08:00 UTC.

| Schedule | Decision time t | Option | Time to expiry τ |
|---|---|---|---|
| S6 | 02:00 UTC | the same day's 08:00 expiry | 6 h |
| S24 | 08:00 UTC | the next day's 08:00 expiry | 24 h |

- **Near-ATM trades:** trades on the target expiry in [t − 2 h, t) with
  |ln(K / index)| ≤ 0.02.
- **IV_mid:** amount-weighted median IV of those trades. **IV_ask:** the same over taker
  buys. **IV_bid:** over taker sells.
- **Eligibility:** a decision is eligible only with at least 3 near-ATM trades. A
  missing IV_ask or IV_bid is filled from IV_mid ± the median half-spread
  (IV_ask − IV_bid)/2 of the previous 30 eligible decisions.
- All IVs are annualised percentages, as Deribit reports them; they are converted to
  the horizon with √(τ / 8760 h).

## 5. Q1 — forecast comparison

- **Target:** y = log realised volatility over (t, expiry], from hourly Binance log
  returns, annualised.
- **Forecasters:**
  - **M0:** B4's richer intraday price baseline P0, recomputed at t.
  - **M1:** M0 + log DVOL, its 24-hour change, and log IV_mid.
  - **M2:** M1 + B4's stablecoin and ETH flow blocks (22 columns) at the last complete
    hour before t.
  - **IV-only:** a linear calibration of log IV_mid.
- **Models:** ridge with B4's alpha search, and B4's tree settings.
- **Walk-forward:** expanding training from 2021-04; test years 2022, 2023 and 2024,
  plus 2025-01-01 → 2026-10-12 reported separately as already-opened.
- **Loss and intervals:** loss MSE; circular block bootstrap with 20-decision blocks,
  2,000 draws, seed 20261019.
- **Reported comparisons:** M1 vs M0, M2 vs M1, M2 vs IV-only, per schedule, asset and
  family.

## 6. Q2 — straddle backtest

- **Signal:** z = ŷ − log IV_mid, both converted to the horizon. ŷ is the out-of-fold
  forecast of M2 (with flows) or M1 (without flows); both are reported.
- **Rule:** buy 1 at-the-money straddle (call and put at the strike nearest the index at
  t) when z > θ; sell it when z < −θ; otherwise no trade. Thresholds θ ∈ {0.05, 0.10,
  0.20} are all reported, with none chosen.
- **Entry price:** Black-76 premium with forward = index at t, τ, strike K and
  volatility IV_ask for buys or IV_bid for sells. Premiums are in USD per 1 coin of
  notional.
- **Fees:** Deribit's current option fee of 0.03 % of the underlying per leg, capped at
  12.5 % of the leg price, at entry and again as the delivery fee at expiry. Charging
  delivery is conservative, and the constant schedule is a disclosed approximation,
  since historical fees changed.
- **Payoff:** |S_T − K| with S_T = the Binance close at the expiry hour, standing in for
  Deribit's 30-minute delivery index.
- **Reported metrics:** per decision P&L in USD per coin and as a share of premium; mean
  with block-bootstrap interval; annual totals; Sharpe on decision days; hit rate;
  maximum drawdown; number of trades.
- **Benchmarks:** always buy, always sell (the volatility risk premium), and a sign-flip
  placebo of the signal.
- **Long and short sides are reported separately.** Short straddles carry unbounded
  risk and need margin, which a small account may not have.
- **Read as positive only if** the M2 rule beats the M1 rule and both benchmarks after
  costs in 2022–24, with the 2025–26 period shown alongside.

## 7. Q3 — BTC

Sections 4–6 repeated for BTC options, with BTC prices from Binance BTCUSDT and the same
Ethereum-chain flow features. BTC and ETH volatility co-move, so this checks
generalisation rather than giving independent evidence.

## 8. Q4 — event study

- **Events:**
  - Hours where B4's stablecoin inflow h1z ≥ 3 and the hour contains at least one
    ≥ $1M inflow; the first such hour within any 24 hours.
  - Inflow and outflow events are analysed separately.
- **Placebo events:** the same number of hours chosen by exchange activity alone
  (|r₁| z ≥ 3 or last-hour volume z ≥ 3, first per 24 h).
- **Responses, k = 1 … 12 hours:**
  - Log realised volatility surprise against the out-of-fold M0 forecast.
  - The change in near-ATM implied volatility of the nearest expiry.
  - Signed log return.
  - The same responses over the 12 hours before each event.
- **Statistics:** means with block-bootstrap intervals over events; ETH 2019–24 and
  2025–26, BTC alongside.

## 9. Q5 — Tron feasibility probe

Measure whether SQD's free portal (or another free source) returns full-history USDT
TRC-20 Transfer logs and at what rate, and whether public exchange labels for Tron exist
(e.g. Dune Spellbook CEX lists). Deliverable: `TRON_PROBE.md` with go or no-go and a cost
estimate. No Tron analysis in B5.

## 10. Pre-declared analysis plan

`research/onchain-b5-2026-10-19/PLAN.md` lists every comparison, table and threshold of
§§5–8 and is committed before any B5 model or backtest runs. `RESULTS.md` reports all of
them, including negatives; post hoc additions are labelled as such.

## 11. Compute and storage

- **Engineering:** about 1 day, with 25–30 tests.
- **Downloads:** Deribit trades about 2 h for both assets (about 2 s and 4–9 calls per
  day); DVOL and BTC bars in minutes.
- **Models and backtests:** minutes, since S6 and S24 each give about one decision per
  day, about 1,950 per asset per schedule.
- **Disk:** about 0.6 GB.

## 12. Package layout

```
tradingagents/research/onchain_b5/
  config.py      # research/onchain-b5-2026-10-19/config/b5.json
  deribit.py     # option trades and DVOL fetch, day files, retries
  implied.py     # instrument parsing, near-ATM selection, IV_mid/ask/bid per decision
  decisions.py   # S6/S24 schedules, targets, M0/M1/M2 feature rows, BTC bars
  forecast.py    # walk-forward models and comparisons (B2/B4 primitives)
  straddle.py    # Black-76, fees, payoff, rule, metrics, benchmarks
  events.py      # event and placebo selection, response paths
  cli.py         # fetch, decisions, forecast, backtest, events, report
tests/research/onchain_b5/
research/onchain-b5-2026-10-19/   # CHARTER.md, PLAN.md, config/b5.json, STATE.md, RESULTS.md
research_artifacts/onchain-b5/     # gitignored
```

`onchain_b`, `onchain_b2`, `onchain_b3` and `onchain_b4` are imported, not edited.

## 13. Testing

- **Parsing and selection:** instrument-name parsing across date formats (e.g.
  `2JUN21`, `28JUN19`); near-ATM selection and the eligibility rule; IV fill from the
  half-spread.
- **Pricing:** Black-76 against known values, including put–call parity; fee cap.
- **Payoff and P&L:** straddle payoff, and P&L signs for long and short.
- **Causality:** every input to a decision at t is timestamped before t (option trades,
  DVOL, flows, prices). Executions and payoffs use only post-t data.
- **Timing:** schedule times across daylight-saving-free UTC dates and expiry-day
  boundaries.
- **Statistics:** walk-forward folds and purge; event spacing; placebo selection size
  equal to the event count.
- **Downloads:** API pagination with `has_more`, retries and deduplication by trade_id.

## 14. Checkpoints

- **B5-CP1:** data stored (option trades, DVOL, BTC bars); `PLAN.md` committed.
- **B5-CP2:** decision tables (S6, S24, ETH and BTC) with eligibility counts.
- **B5-CP3:** Q1 forecast comparison and Q2 backtests reported.
- **B5-CP4:** Q4 event study, Q5 Tron note, `RESULTS.md`.
