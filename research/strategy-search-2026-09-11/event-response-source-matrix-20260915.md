# Event-response source matrix — September 15, 2026

Documentation-only follow-up to the independent non-options coverage review.
No socket, market snapshot, source claim, financial draw or allowance was created.
This completes the immediate source-schema question; a prospective measurement
still needs an information-value decision against exhausted liquidity/OFLOW/
lead-lag ancestry, exact registration and independent admission.

## Primary documentation findings

[Binance USD-M public streams](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-streams/public)
document individual bookTicker E/T clocks, u update identifier, instrument and
best bid/ask prices and quantities, delivered under the public stream route.
Individual updates are described as real time, while the all-symbol stream is
listed at five seconds. RPI orders are excluded. Diff-depth provides U/u/pu
sequence fields. These are schema facts, not a measured latency or fill guarantee.
The old individual-stream documentation URLs redirected to a generic landing
page; the catalog above supplied the substantive replacement. No old stream
example was executed.

[Binance USD-M market streams](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-streams/market)
document aggTrade under a separate market route, 100ms aggregation by price and
taking side, E/T clocks, aggregate and first/last trade IDs, maker-side indicator,
and q/nq quantities. Insurance-fund/ADL trades are excluded; q includes RPI while
nq excludes it. This is not a feed of every individual aggressive order, and
aggTrade volume cannot silently be equated with visible public-book depletion.
Payload examples do not prove actual field presence or live compatibility.

## Exact evidence boundary

| Requirement | Available now | Missing for an actual observation |
| --- | --- | --- |
| Leader transaction/event identity | Official aggregated-trade schema | Exact selected instruments, immutable raw receipts, deduplication/conflict handling and batching interpretation |
| Follower and hedge bid/ask/size | Individual futures book schema | Joint actual capture and freshness at a predeclared action, supported lots/rules/capital; displayed size is not a fill |
| Common local observation order | Prior triangle engineering retains local clocks | New public/market connections must share a monotonic receipt clock and retain individual socket order. No global exchange serialization or causal treatment is implied. |
| Sequence/completeness | Book update ID; deeper-book sequence fields documented | A bookTicker ID alone is not a proved contiguous loss detector. Exact gap/reconnect/cutoff protocol and any snapshot/depth reconstruction remain unadmitted. |
| Historical reuse | Saved bars and three-spot-symbol bookTicker receipts | No saved aggressive-leader/alt-perpetual joint event archive identified; recent retrieval of old event times cannot reconstruct historical local availability. |
| Economic test | Old lead-lag and OFLOW evidence, preserved | No event-response advantage, funding ownership, actual fees, hedge cash book, latency advantage or expected profit established |

The narrower candidate is whether a received leader event leaves a measurable
post-receipt follower/hedge quote state under a fixed processing-delay assumption.
This is receiver-observable feasibility, not proof of economic causation or
execution. A complete predictive test would still need a fixed response target,
null/common-shock controls, all cost/unavailable cases and untouched validation.

## Decision

The documented schemas contain useful event and quote fields missing from the
saved spot/bar recipe. This resolves schema discovery positively, but does not
admit an archive or collector. A concrete future source proposal must select its
instruments without observed response performance, state the question's practical
value despite old cost failures, justify its cumulative allowance, retain every
failure and fit a finite resource budget. No grant is assumed merely because
collection is technically possible. Stop the present documentation search here;
no broad data download, repeated generic query or bar-predictor retest follows.
