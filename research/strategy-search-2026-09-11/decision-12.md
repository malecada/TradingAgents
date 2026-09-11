# Decision 12 — WBETH source admitted for a separate market-value book

The fixed two-request WBETH source probe completed once from
 ea63d7b1aa9176faeddd7640eef09af1a2bdecc5, pushed and remotely verified before
execution. Two complete cells, zero unavailable, four outputs retain 20,794 raw
bytes and total 69,105 bytes. Independent raw/schema review and receipt
verification pass; see reviews/wbeth-inputs-review.md and its JSON checker output.

Actual request/retrieval span is September 11, 2026 09:39:02.312942–09:39:03.433509
UTC. The input-document observation interval does not backdate those receipts.
Resource use is 4.625 seconds and 59,449,344 bytes sampled peak tree RSS, within
frozen limits. No hidden additional request, source fallback or financial
calculation occurred.

The exact active WBETHUSDT metadata and all 91 daily bars over April 1–July 1,
2026 exclusive pass the fixed schema/clock/OHLC checks. No day has zero reported
volume or trade count. This is activity/coverage evidence, not a filled trade.
The current LOT_SIZE minimum/step are 0.0001; MARKET_LOT_SIZE minimum/step are
zero and maximum 19.80402541. NOTIONAL min/max are 5/9,000,000 with different
market-order applicability flags. All 11 filters are preserved literally.
Their historical and account applicability remains unknown; no order rule is
inferred by combining the observed precision and filter numbers.

## Learning and next action

This removes the fixed market-price source dependency. The documented link to
staked ETH supplies the relationship before performance inspection, but price
changes combine rewards, basis/depeg and demand. A separate fixed WBETH spot
long/ETH perpetual short book can use a conservative entry market-value hedge
and a spot exit without inventing public redemption-rate history. True
contractual ETH delta, separate validator-yield attribution and future neutrality
remain unavailable. The already spent ETH Q2 source and old PRX/DEX/carry history
stay inherited; no fresh confirmation is claimed.

Freeze that future book's exact quantities, costs, capital/reserves, reference
sources, counterfactuals, exposure/risk and inference rules before arithmetic.
The planned conservative sizing includes both entry fees within 40% of capital,
50% futures reserve and at least 10% idle; it is not a retrospectively optimal
hedge. Its pure engine is in synthetic implementation and no financial gate or
actual book has run. One of three new WBETH investigations is used, also charged
to the linked relative-value/on-chain map rows.

First complete the independently approved, exactly-one dated amendment after
this results checkpoint and the final source/certificate remote freeze. The
original dated cap/claims, economic source and inputs remain unchanged; the
separate certificate makes the single additional administrative allowance
explicit. Then diagnose its economic result while WBETH implementation and
independent review proceed. No candidate is validated and the program remains
active/incomplete.
