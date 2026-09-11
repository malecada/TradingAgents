# WBETH spot source prerequisite for a fixed market-value hedge

Proposed experiment wbeth-inputs-20260911, a new economic-linked-value question.
The documented WBETH claim on staked ETH supplies an economic relationship
before outcomes; no pair selector, threshold sweep or post-hoc DEX signal is
introduced. Prior PRX, funding-carry, staking references and DEX-ratio failures
remain relevant history with incomplete broader multiplicity. Register all
incremental work under one stable WBETH/ETH mechanism and a three-question
administrative allowance, also charged to the relative-value/on-chain map rows.
This is not a route for rerunning old failed funding configurations unchanged.

## Narrow source question and exact requests

Can a fixed WBETHUSDT daily spot series and current instrument metadata pass
source admission for the same exposed 2026 Q2 period already admitted for ETH
spot/perpetual funding and marks? Two requests only, once each:

- https://api.binance.com/api/v3/exchangeInfo?symbol=WBETHUSDT
- https://api.binance.com/api/v3/klines?symbol=WBETHUSDT&interval=1d&startTime=1775001600000&endTime=1782863999999&limit=1000

The interval is April 1, 2026 00:00 UTC through July 1, 2026 exclusive. Require
91 exactly consecutive daily open/close millisecond clocks, 12 fields per bar,
finite positive OHLC with proper ordering and finite nonnegative volumes/trade
counts. Preserve all rows, zero-activity dates and missing/unavailable cells.
No interpolation, date substitution or new quote acquisition. Metadata requires
exact symbol WBETHUSDT, base WBETH/quote USDT, TRADING and explicit spot-enabled
status; retain every raw filter field without treating precision as lot size.
These are current rules, not retrospective account/fee/lot authority.

Raw strict JSON bytes and request/retrieval times precede schema interpretation.
No numerical return, ratio, staking yield, spread, candidate PnL or hedge fitting
is performed in source admission. Data from an earlier inspected ETH period
remains exploratory/exposed even if this WBETH response is newly acquired.

## Why this source is informative

A later separately registered book may hold fixed WBETH spot and an ETH perpetual
short sized from entry market values, and close WBETH by spot sale. Public
contractual conversion-rate history is not required for those signed market
cashflows. The hedge would be an approximate market-value hedge, not contractual
ETH-delta neutrality. Market prices combine staking accrual, redemption/depeg
risk and demand; no separate validator-reward attribution is possible without
additional evidence. Funding and entry/exit fees, lots, residual inventory and
reserve needs must all enter that future book. Coarse bars remain fill proxies.

This differs from asserting a guaranteed staking arbitrage or booking ratio
increments as spendable cash. Official redemption locks the rate, interrupts
rewards during waiting and has quotas/processing delays; a redemption-based
strategy needs a different instrument/state model. The intended market book
avoids claiming those unadmitted redemption cashflows. Independent review must
confirm this distinction and inherited ancestry before financial registration.

## Resources, denominator and follow-up

Two cells wbeth-exchange-info and wbeth-spot. Four immutable outputs: individual
receipts, wbeth-capture.json and wbeth-admission.json. Twenty seconds and 5 MiB
per response; 10 MiB raw total, 10 MiB actual serialized admission and 40 MiB
all outputs. Cooperative 60 seconds, hard 120 seconds, two CPUs, 512 MiB sampled
aggregate RSS under frozen resource_guard_v2.py. No network retries, credentials,
redirect/proxy/fallback or denial bypass. Both receipts saved immediately before
parsing/next request; cooperative failures retain both source cells. Abrupt
failure preserves claim/partial outputs and consumes the attempt.

Synthetic hostile JSON, clock, OHLC, zero-activity, identity and maximum-payload
full lifecycle checks and independent pre-review precede gate/source commit,
push and verified remote equality. One acquisition then independent raw/schema
review and receipt verification. Valid inputs justify a separately fixed cash
book only, with unchanged exposed chronology and every financial configuration
registered before arithmetic. Invalid input defers this exact route; no silent
replacement or minimum number of attempts is required. Record the result,
diagnose, back up and choose the next informative action. No strategy success,
expected-return interval, power, beta or annual relevance is evaluated here.
