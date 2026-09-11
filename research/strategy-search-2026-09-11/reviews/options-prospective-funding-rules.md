# Prospective funding calendar and rule-vintage contract

September11,2026. Source/design review only: no market response, rate, price,
Greek, account or economic calculation. This document is the sole edited file.
The existing16routine sources do not contain fundingInfo, either exchangeInfo,
or final fundingRate history; additional source slots must be registered openly.

## Documentary evidence and request denominator

Read retained `docs/funding-capture/SOURCE_POLICY.md`, its design and timestamp
amendment first. Three explicit primary URL opens, zero search queries:

1. https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data — initial fetch timed out; dependent cached finds yielded no text.
2. https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-Info — readable, redirected to the same current market-data page.
3. https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History — readable, same redirect.

AccessSeptember11,2026; exact retrieval seconds and publication date unspecified.
Further finds used returned text, not additional URL opens. The initial timeout
is retained; it is not evidence that any market API is unavailable.

The [current documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)
says fundingInfo covers adjusted symbols, with fundingIntervalHours, cap/floor
and no historical effective-time parameter. Funding history is ascending,
inclusive in both millisecond bounds and capped at1,000rows; it returns symbol,
fundingTime, signed fundingRate, event markPrice and rateType. Both funding routes
share500requests/five minutes/IP. PremiumIndex gives an announced nextFundingTime
and latest rate, not a substitute history row. An omitted symbol in adjusted
fundingInfo is not independently documented here as an eight-hour historical
default. Do not infer completeness or old schedules from current metadata.

The retained source policy cites documented1/2/4/8hour intervals and intraday
changes, including delayed update visibility. Those earlier sources were not
re-fetched in this task. Its timestamp amendment is an engineering convention,
not a guarantee of event jitter: preserve original timestamps and the separately
declared comparison labels, never silently import an old matching policy.

## Expected future events: maintain evidence, not an invented regular grid

Every hourly premiumIndex observation already in the16slot batch should retain
its provider time, nextFundingTime, local observation clocks and hash. An
announced-next timestamp observed **before** its due time is prospective
expectation evidence. A later history row is published-event evidence. Neither
is proof of a particular account debit, and the latter's first local observation
time must not be backdated to fundingTime.

Maintain an immutable expectation ledger in source normalization with these
distinct states: announced due event, revised/cancelled announcement (where
explicit evidence supports that interpretation), published matching event,
announced but missing after the fixed grace, and interval/schedule unknown.
Conflicting announcements remain conflicts with both observations. Do not
silently remove an earlier due expectation because the next observation jumps
past it. A nextFundingTime at/before observation is stale, not a forecast.

fundingInfo intervals can explain a *current* announced schedule and test its
consistency. They cannot be extrapolated backwards or indefinitely forward.
For bounded diagnostics, an hourly grid is a candidate superset under the
documented minimum interval, not a claim that every hour owes funding. An
unobserved candidate hour is neither automatically a missing payable event nor
automatically zero. Keep conditional stable-interval inference separate from
directly announced expectations. An intraday change between observations can
remain ambiguous even when all HTTP calls completed.

All returned event rows must be retained and reconciled, including events not
previously announced locally. Unexpected events are not discarded to force
calendar agreement. Missing rate/mark, duplicate/conflicting event identities,
unsupported rateType or a due announcement without a final row makes its
cash-flow admission unavailable. Returned-history exhaustion alone establishes
query completeness, not that every economically due event was published.

The economic child must use inventory held before each actual event under its
frozen boundary rule. Calendar comparison labels do not shift cash membership
or manufacture event marks. No current lastFundingRate, interval average,
forward-filled rate or later price repairs a missing final event. This source
capture must not compute the hedge or funding cash while recording the ledger.

## Cheapest honest schedule: hourly expectations, daily rule vintages

Recommended minimum incremental schedule, in addition to the fixed16slots:

- Before initial selection, capture EAPI exchangeInfo, FAPI exchangeInfo and
  FAPI fundingInfo once under explicit bounded metadata slots.
- At one frozen UTC daily checkpoint, capture those same three endpoints. Use
  the nearest existing EAPI/FAPI time observations only within their declared
  calibration span; otherwise schedule explicit time slots, not invented
  clocks. Do not squeeze large metadata fetches into the5second routine quote
  batch and then erase their elapsed time from that batch.
- Keep hourly nextFundingTime evidence from the existing premiumIndex slots.
  Adding daily fundingInfo is inexpensive but does not guarantee observing
  every intraday interval transition. An hourly fundingInfo request would improve
  contemporaneous adjustment observations at one additional request per batch;
  it still cannot prove absence of a shorter-lived change. No hourly metadata
  sweep is required for the conditional episode unless actual rule-at-every-
  decision certification is made a goal.
- Capture BTC and ETH final history daily at a fixed checkpoint using explicit
  trailing48hour query windows and limit1,000. This overlap is a registered
  revision/late-publication check, not an outcome-selected retry. Preserve all
  versions; differing rate/mark/type at one identity is a conflict, not “latest
  wins.” Final closure uses the separately bounded queries below.

This adds five ordinary daily source requests (three rules, two histories),
plus any declared clock-calibration slots and final queries. Existing metadata
5MiB caps and complete raw preservation multiply by day; update the whole-
episode storage budget before freezing. A daily exchangeInfo body is not an
8KiB routine price response. No unregistered conditional refresh on a filter
change or HTTP failure. Do not change existing16source adapter definitions;
model the additional sources as separate registered slot classes.

Daily rule observations support a last-observed-rule **conditional model**, not
proof that the venue's rule was unchanged between them. Freeze a maximum rule
age of24hours plus the declared checkpoint tolerance; after a missing refresh,
new decisions lack admitted rules and become no-trade under the policy.
Compare only the four fixed options and two fixed perpetuals' relevant rule
fields while retaining entire raw metadata. Unrelated new listings do not
change fixed instrument selection or invalidate every book.

On a changed relevant tick/lot/minimum/status/unit/settlement/margin field,
record an unknown effective-time interval between the last old and first new
observation. Never apply the new rule retroactively. Freeze this conservative
response: stop further new modeled hedges until the change is adjudicated;
continue source collection, retain existing inventory and unavailable rule-
dependent decisions. Do not resize holdings or replace symbols to pass. A
terminal closing quote cannot establish that its quantity was legal without
applicable closing-rule evidence. Unit/contract identity changes are especially
not safely inferred as a routine filter update.

This minimum schedule is appropriate only for the declared conditional
development episode. If the intended claim instead requires exact historical
rule applicability at every hedge, daily snapshots are insufficient—and even
hourly polling supplies observations, not effective-time guarantees. That
stronger claim needs an authoritative change feed/rule history or remains
unavailable; simply buying more polling frequency cannot prove it.

## Final history queries: four fixed partitions, not one truncated page

At most44days can contain1,056hourly events per asset; the45day envelope can
contain1,080. Therefore one1,000row request per asset is insufficient under the
supported hourly case. Freeze **two disjoint time partitions per asset** rather
than an open-ended response-adaptive pagination loop:

```text
T0 = registered observation-window start in integer UTC milliseconds
T1 = registered observation-window end (exclusive; at most T0 +45 days)
B  = T0 + floor((T1-T0)/2) milliseconds
BTC/ETH partition1: symbol, startTime=T0, endTime=B-1, limit=1000
BTC/ETH partition2: symbol, startTime=B, endTime=T1-1, limit=1000
endpoint: https://fapi.binance.com/fapi/v1/fundingRate
```

These four requests cover the fixed source envelope even if the selected
position closes earlier. They are registered source evidence; the later cash
book clips its own ownership interval. Each partition is at most23days, below
the limit under the conditional one-event/hour premise. Reaching1,000rows,
out-of-range/nonascending rows or faster/ambiguous types means query exhaustion
is unproven; preserve the response and mark unavailable, without a third page.
The1,000threshold is not a promise about future exceptional event multiplicity.

Use a fixed final acquisition time **T1+24hours** as a late-publication grace.
The24hour choice is a conservative research deadline, not a venue publication
guarantee. No retry after a missing final row or denial. Register that final
acquisition/retention tail explicitly: a45day market-observation envelope then
needs up to46days of collector lifecycle, not a secretly enlarged45day deadline.
If45days is a hard whole-lifecycle cap, reserve the final day for this grace and
reduce the observation envelope before selection, or choose a shorter declared
grace; do not change the cap once started. No additional following-boundary
event is required for a raw-time cash interval merely by borrowing a legacy
daily cadence check. If a boundary diagnostic is desired, its extra query span
and denominator must be declared before capture.

Missing terminal history or calendar ambiguity remains unavailable after grace,
not zero funding or successful completion of economic coverage. All initial,
daily and final responses are immutable and independently comparable. Complete
source retention can coexist with unavailable economic cash or rule fields.
This proposal is ready for a bounded source-spec decision; it does not fetch
anything, expand a gate or authorize account/production actions.
