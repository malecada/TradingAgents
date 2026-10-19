# B5 results — exchange flows against the option market

Exploratory study with a pre-declared plan (`PLAN.md`, amendments 1–6 committed before
any decision table). All pre-declared tables are in `TABLES.md` (generated) and
`research_artifacts/onchain-b5/{forecast,backtest,events}/results.json` (which also hold
P&L per premium). Groups: 2022–24 (test years) and 2025–26 (already opened in B4, shown
alongside). Decisions: ≈ 1,980 per asset and schedule (S6 at 02:00 UTC for the same-day
08:00 Deribit expiry; S24 at 08:00 for the next day's), 2021-04 → 2026-10-12.

## Answer

Exchange flows do not add usable information once the option market's own prices are
in. For ETH, adding B4's flow features to price and option-market features never lowers
volatility-forecast error significantly. The straddle rules built with and without flows
differ by amounts far inside their noise. The only consistently profitable pattern —
selling 6-hour straddles before the 08:00 expiry — does not depend on flows. It is thin
after realistic costs and faded in 2024–25 (post hoc, §4). B4's confirmed volatility
gain is therefore real against price history but already priced by the option market.

## Q1 — forecast comparison (log realised volatility to expiry, MSE difference)

| Comparison | ETH S6 | ETH S24 | BTC S6 | BTC S24 |
|---|---|---|---|---|
| M1 (price + option market) vs M0 (price), linear, 2022–24 | −0.027 [−0.047, −0.008] | −0.037 [−0.050, −0.027] | −0.088 [−0.137, −0.041] | −0.100 [−0.143, −0.062] |
| M2 (+ flows) vs M1, linear, 2022–24 | +0.005 [−0.000, +0.009] | +0.004 [+0.001, +0.008] | +0.006 [−0.000, +0.013] | +0.013 [+0.007, +0.018] |
| M2 vs M1, trees, 2022–24 | −0.002 [−0.012, +0.007] | +0.003 [−0.006, +0.012] | −0.019 [−0.033, −0.006] | −0.007 [−0.014, +0.000] |
| M2 vs M1, linear, 2025–26 | −0.002 [−0.005, +0.001] | −0.001 [−0.003, +0.002] | −0.002 [−0.007, +0.002] | +0.001 [−0.002, +0.003] |
| M2 vs M1, trees, 2025–26 | +0.002 [−0.003, +0.008] | −0.002 [−0.005, +0.002] | +0.006 [−0.002, +0.015] | −0.001 [−0.005, +0.003] |

- Option-market information (DVOL, its 24-hour change, short-dated implied volatility)
  improves the price-only forecast in 7 of 8 family × asset × schedule cells in 2022–24
  (interval below zero; the exception is ETH S6 trees).
- Flows on top of it improve one cell of sixteen (BTC S6 trees 2022–24, −0.019), which
  reverses in 2025–26 (+0.006); linear models are significantly worse with flows in two
  cells (ETH S24, BTC S24).
- M2 beats implied volatility alone for 6-hour ETH (linear −0.040, trees −0.039 in
  2022–24) because the calibrated price features add to the raw implied level, not
  because of flows (M2 and M1 differ by less than 0.005).

## Q2 — straddle backtest (USD per coin, after fees and spreads)

Benchmarks, 2022–24 (2025–26):

| Table | Always buy | Always sell |
|---|---|---|
| ETH S6 | −9,365 (−4,825) | +3,415 (+634) |
| ETH S24 | −5,260 (−1,936) | −778 (−2,303) |
| BTC S6 | −153,749 (−126,813) | +53,873 (+8,157) |
| BTC S24 | −137,290 (−123,952) | +35,205 (−2,934) |

- The signal rules sell in most decisions at 6 h (mean z −0.36 ETH, −0.44 BTC, after the
  log-RV bias correction): the forecast sits well below 6-hour implied volatility. At
  24 h they trade both sides (mean z −0.04 to −0.12).
- **Pre-declared positive reading** (amendment 1: M2 total 2022–24 above M1, always buy
  and always sell, same family and θ): met in 7 of 24 family × θ × table cells — ETH S24
  linear θ 0.05 and trees θ 0.05/0.10/0.20, ETH S6 linear θ 0.20 and trees θ 0.10, BTC S6
  linear θ 0.20. In each the M2–M1 difference is small against the per-trade interval
  (largest: ETH S24 trees θ 0.10, +1,214 USD per ETH over three years; BTC S6 linear
  θ 0.20, +985 USD per BTC, 1.7 % of the rule's total), three of the seven reverse in 2025–26,
  and under no information M2 would beat M1 in about half the cells — 7 of 24 is
  consistent with chance. The pre-declared criterion is met literally in those cells and
  does not indicate flow value.
- 6-hour signal rules earn Sharpe ratios of about 2.4–3.1 in 2022–24 for both M1 and M2;
  this is the short-dated volatility premium, captured almost equally by always-sell.

## Q3 — BTC

Same picture as ETH: option-market data dominates price data; flows add nothing reliable
(Q1); BTC 6-hour selling is profitable in 2022–24 for all rules and benchmarks (Q2).

## Q4 — event study (k = 1 … 12 h; full tables in `TABLES.md`)

Strict events (stablecoin inflow h1z ≥ 3 with a ≥ $1M transfer, one per 24 h): 66 inflow
and 66 outflow events in 2019–24, 17 and 16 in 2025–26; placebo activity spikes 61–63
and 18–20.

- No realised-volatility surprise after inflow events at any k; ETH at 6 h is lower than
  forecast (−0.139 [−0.285, 0.000]). Placebo spikes show no surprise either.
- Pre-event windows (ending the hour before the event) show isolated rises (BTC outflow
  2019–24 at 6 h +0.17 [+0.04, +0.33]; ETH placebo 2019–24 at 1 h +0.37 [+0.13, +0.60])
  but no consistent pattern across assets and periods.
- Near-expiry implied volatility falls after inflow events in 2025–26 (6 h: ETH −7.6
  [−15.2, −0.3], BTC −7.3 [−14.9, −0.6] vol points) on 17 events; the expiry can roll
  inside the window, so this is weak.
- Signed returns 6 h after inflow events, 2019–24: ETH −0.5 % [−1.0 %, −0.0 %], BTC
  −0.4 % [−0.7 %, −0.0 %] — marginal and one of many tests.

## Q5 — Tron

Go: free and feasible labels-only via SQD with server-side filtering (`TRON_PROBE.md`).

## 4. Post hoc: is the 6-hour selling premium tradable? (exploratory)

Always-sell, all decisions 2022-01 → 2026-10, USD per coin
(`research_artifacts/onchain-b5/explore_vrp.txt`):

| Pricing | ETH S6 | BTC S6 | ETH S24 | BTC S24 |
|---|---|---|---|---|
| Registered (pooled near-ATM IV at the bid) | +8.2 % of premium, Sharpe 1.74 | +7.1 %, 1.49 | −3.0 %, −0.56 | +1.7 %, 0.34 |
| + one Deribit tick per leg | +2.7 %, 0.57 | +2.1 %, 0.44 | −6.9 %, −1.30 | −3.3 %, −0.64 |
| IV at the traded strike | +5.4 %, 1.12 | +2.0 %, 0.40 | −3.7 %, −0.70 | +0.1 %, 0.02 |
| IV at the traded strike + one tick per leg | −0.1 %, −0.01 | −3.0 %, −0.59 | −7.7 %, −1.44 | −4.9 %, −0.94 |

- The pooled ±2 % near-ATM IV exceeds the IV at the traded strike by 1.5 (ETH) and 2.0
  (BTC) vol points at 6 h — the volatility smile inside the window — which inflates
  registered short P&L.
- With strike-level pricing and one tick per leg the premium is gone; every variant loses
  in 2025 (ETH S6 −386 to −1,413; BTC S6 −5,867 to −35,530 USD per coin), and single
  days lose up to about 200 USD per ETH and 5,600 USD per BTC.
- Short straddles also need margin (about 30 % of the underlying for an at-the-money
  pair under standard margin) and carry crash risk the sample under-represents.

## Reading

Within this design, B4's hourly exchange-flow information does not improve on the
option market's own forecast of ETH or BTC volatility and does not improve a
cost-aware daily straddle rule. The 6-hour short-straddle premium is a market feature
independent of flows, small after realistic execution costs and absent in 2025. No
flow-based trading strategy follows; a forward test would only be warranted for the
short-dated premium itself, with quote-level spreads and margin modelled, which is a
different study.
