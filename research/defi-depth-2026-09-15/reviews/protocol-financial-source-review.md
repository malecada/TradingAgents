# Independent protocol financial-source collector review

## Scope and initial findings

This is an engineering review of `protocol_financial_source.py`, its invented
tests, and the proposed zero-WST wallet-control adapter. No collector, financial
recipe or request is admitted here. Only this new review file was written. No
network, empirical values, active F2 root/process, wallet or account was accessed.

Initial collector SHA256:
`a35ae4cbe343e2e0431e34a2e24f54c3bf825d0bc59fd50f5f5931c9309fcd45`.

Two input checks require correction before relying on the collector:

1. **Date/clock binding, initial lines53–75.** Fixed ISO date strings were checked,
   but each supplied timestamp was not bound to that date's midnight UTC.
   An independently invented one-hour shift of the first timestamp and retained
   header passed `validate_design`. That can label an observation with a different
   financial date/clock. Derive and compare the exact UTC timestamp for every
   fixed date before any request; require an exact nonnegative integer candidate
   block height. The separate actual block offset remains within−1..0seconds.
2. **Ownership flag type, initial lines72–75.** Truthiness accepts a nonempty
   string such as`"false"` as a first-acquisition proof. Require literal`True`
   for both new-header and overlapping-price ownership assertions. Even a true
   Boolean remains an assertion: the pending terminal-history builder and exact
   evidence manifest must establish it independently.

## Independent synthetic verification

The initial four named tests passed. Additional independent full-calendar tests
used two invented newly owned header/price days among retained invented records.
Both paths retained exactly3,306 cells and11,443 output files:

- Complete path:1,846 actual requests, new positive two-asset oracle vectors
  decoded and bound to their exact new header hashes.
- One header outside its allowed clock:1,840 actual requests; that day's price
  request and five protocol calls were suppressed, with all physical-slot
  intents/receipts retained. The day and whole source remained unavailable.

No empirical source arrays were read. The fixtures supply invented indices,
cash, prices, hashes and clocks. Reusing old public getter definitions does not
turn those tests into source acquisition or financial evidence.

## Inventory and availability

The F1 inventory has five daily protocol getters, three daily clock/price/model
cells and one aggregate supply-identity cell. Six witness calls occur at each of
the fixed entry/terminal boundaries. With every common header/price retained
and every protocol field newly acquired,
this is1,842 logical requests, at most5,526 physical sends,3,306 cells and11,419
outputs. New common header/price ownership adds only its explicitly enumerated
logical requests and six output files per request. Method-specific retained
prefix caps are included in the three-slot raw reservation.

The collector preserves failed, unavailable and suppressed cells, and ordinary
non-denial gaps do not erase later dates. An endpoint stop suppresses all later
actual sends while retaining the fixed denominator. This differs from F2's
frozen first-indispensable-gap stop and must be stated in the new contract;
it does not alter F2. Source-summary output is separate from daily model cells.

Aggregate F1 consistency requires qualified income, scaled supply and total
supply, compares the exact half-up ray product and permits at most one atom of
residual. A missing cash field leaves that day unavailable rather than zero.
An available index or successful consistency relation does not prove deposit
capacity, solvency, withdrawal priority or executable prices. All five typed
daily fields are required for a complete daily source row.

Boundary witnesses are evaluated after collection. Daily completeness is not
represented as proof of those witnesses; the summary additionally requires both
boundary witness sets and equal boundary code evidence. Equal proxy bytecode
does not prove the implementation behind it, behavior between observations,
unchanged economic rules or the hypothetical investor's realized index path.
The final scope correctly withholds deployed-semantics/counterfactual/execution
claims. Ordinary source completeness must never be converted into strategy
admission by setting an unexplained qualification flag.

## Pending source-specific admission work

The collector validates action names/order, not the full contract address,
selector, calldata, expected value and ABI type definitions. Exact design/gate
review must bind those definitions to the reviewed Base native-USDC/Aave model.
It must also validate the F3-specific pool model if F3 uses this collector; the
reviewed synthetic full-calendar fixtures exercise F1, not an admitted F3 packet.

Retained context is trusted as already qualified. The raw receipt hashes,
request/envelope identities, completion clocks, canonical block tags, oracle
units and price/header associations must be reconstructed by the pending input
builder and pinned by the gate. A matching caller-supplied hash field is not raw
evidence. Similarly, nominal candidate heights need their frozen derivation;
there is no height search in this collector.

Prior literal request keys do not by themselves exclude address-case/tag aliases
or overlapping fields in different oracle vectors. The builder must prove new
ownership only after terminal F2 reconciliation, preserve all old attempted or
uncertain observations, and include semantic overlap exclusions. Source/price
failures cannot be repaired by new field names. The common ETH/USDC vector must
be captured only when its overlapping observations are genuinely unattempted.

The exact future lifecycle must bind the complete source and financial output
denominator, cumulative physical/raw resources, prior claims and partial failure
closure. This review did not test a complete financial runner, CLI admission,
detached-root freeze or lifecycle terminal receipt. A callback persistence failure
can interrupt publication; existing intents/receipts remain spent and cannot be
silently retried in another claim.

## Proposed wallet-control adapter

The proposal is mathematically sound for the two restricted policies
`wallet-cash` and `wallet-ETH25`. WST is an absent exposure. Supplying a positive
internal sentinel solely to satisfy the unchanged engine's three-asset validator
is not valuation of a missing held asset, provided its zero-exposure invariant is
enforced and the sentinel is never reported as source evidence.

An independent check ran six invented policy/scenario pairs using WST sentinel1
and, separately, alternating10^80/10^-80. After removing only WST price fields,
the entire returned books were identical: P, attribution, events, states, stress,
drawdown and log diagnostics. Initial, every state/event and terminal WST
quantities were zero. ETH/USDC prices were unchanged.

The eventual adapter should reject every other policy, require positive exact
actual ETH/USDC marks, assert zero WST in initial/current/state/event/terminal
balances and all literal deltas, and remove only unused WST marks from reported
source/ledger output. Retain explicit internal-sentinel and zero-exposure
provenance. Do not permit an actual WST position to use this route.

For partial failures, use the new authoritative literal receipt serializer and
validate the zero-WST invariant there too. The frozen wrapper's own
`partial_snapshot` still replays high-level events, so it is not sufficient if a
funded conversion occurs before a later valuation exception. No frozen wrapper
change is required. Adapter implementation and its assertions remain unreviewed;
this is approval of the narrowly stated approach, not an admitted new book.

## Final reviewed corrections and disposition

The final reviewed collector SHA256 is
`0e14cc0b41421e8cef6fde97f4d418a5a9365f006a1a3f25959e6e9a1b95360d`.
The implementation owner corrected both initial findings. Each fixed ISO date
now binds to its exact midnight UTC timestamp, candidate heights must be exact
nonnegative integers, and new-header/price flags must be literally true. The
independent one-hour-shift counterexample is now rejected. String, integer1,
false and absent ownership assertions are also rejected.

The updated collector adds explicit retained/new/unavailable roles for each
protocol field. Retained fields must match the declared action and retained
header hash, and do not create a new request. Unavailable inherited fields stay
visible without a replacement. The raw input builder remains responsible for
proving retained values, ABI/expected-identity qualification and complete history;
the collector trusts its qualified decoded context rather than reconstructing
the original receipts itself.

The final named suite passes7/7. An additional independent full-calendar case
retained all five scalar values for one invented day and kept a different day's
cash field unavailable. It produced all3,306 cells and11,383 declared outputs,
with1,836 actual requests and no send for the retained day or failed field.
The source correctly remained unavailable. These counts are synthetic branch
checks, not proposed or actual live acquisition counts.

**PASS for this scoped F1 collector engineering review after the corrections.**
The exact terminal-history builder, deployed-model assumptions, action manifest,
source and financial gates, physical-budget import, lifecycle failure closure
and adapter implementation are still pending independent review. This review
does not authorize a request, a F1/F3 financial execution or a source-family
budget reset. The untouched F2 and prior failed claims remain governed by their
original contracts.
