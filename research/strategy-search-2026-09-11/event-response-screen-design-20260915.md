# Conditional event-response quote screen — design only

September 15, 2026. A concrete proposal for independent design review. No capture,
allowance, empirical claim or executable implementation is admitted. No option
worker, gate or runtime is changed. The [information-value review](reviews/event-response-information-value-20260915.md)
supports a cost-aware falsification design rather than a collector that merely
establishes message order. All LLG, OFLOW, ETHBTC and liquidity ancestry remains.

## Fixed question and inherited prediction

For a BTCUSDT aggregate trade received by the observer, can the registered
negative cross-response direction leave positive conditional quote headroom in
ETHUSDT after a fixed observation-to-action delay, when the opposing BTCUSDT leg
and all four entry/exit crossings are priced? This is an exploratory necessary
condition for one policy, not causation, expected returns, a portfolio or a
claim that every crypto lead-lag mechanism is covered.

BTCUSDT and ETHUSDT are chosen as the liquid named leader/follower/hedge instance,
not by new response outcomes. They inherit earlier ETHBTC and BTC/ETH forecasting
work; using ETH instead of the old alt basket does not create a fresh family.
Every unique admitted BTC aggTrade is an event: buyer-initiated BTC flow implies
short ETH/long BTC; seller-initiated flow implies long ETH/short BTC. No volume
threshold, learned parameter, follow-direction alternative or event filtering
based on subsequent returns. The leader is an aggregated flow message, not an
identified independent original taker order. No regression or significance test.

## Proposed fixed clocks, sources and denominator

One ten-minute observation, followed by two seconds of capture solely to finish
its last eligible event. Start must be a future exact UTC instant committed with
the source registration, not chosen from price behavior. The design assumes
250ms processing delay from actual local receipt and a one-second holding
interval from that action. These are fixed engineering assumptions, not latency
measurements or claims of a known economic response horizon. No alternative
clock/horizon is evaluated under this proposal.

Capture BTC aggTrade on its documented market route, and individual BTC/ETH
bookTicker on the public route, with one common local monotonic/UTC receipt
clock and preserved per-connection frame order. Record raw bytes, event/transaction
clocks, IDs, gaps, socket errors and exact cutoff. Independently admit instrument
rules, timestamp semantics and applicable conditional fee assumptions before
measurement. Two connections do not establish global exchange order.

At entry and exit use only the latest complete quote on each leg received at or
before the corresponding local action cutoff, no older than250ms by local
receipt. Exclude future receipts. Venue-event freshness, event/receipt clock
compatibility and uninterrupted source coverage require their own exact protocol;
receipt freshness alone is insufficient. A contradictory clock, absent quote,
connection gap, source restriction, conflicting ID, malformed field, ambiguous
maker side, inadequate visible size or unsupported instrument rule remains an
unavailable event/case. Never replace it with a later favorable quote. Raw event
and missingness denominators must survive even if the screen cannot finish.

Retain every leader frame, duplicate/conflict disposition, unique event ID,
intended action/exit, both quote witnesses and reason for every unavailable case.
No successful-only denominator. Retain repeated/overlapping events; do not count
them as independent evidence or simultaneous affordable trades. Unknown feed
loss remains unknown and may invalidate a whole interval. The bookTicker update
ID alone does not establish contiguous completeness. The exact gap policy is a
remaining design-admission requirement, not a silently supplied default.

## Four paired scenario cells and quote arithmetic

Capital1000/10000 USDT × fee5/10bp per side, fixed in advance. These are inherited
conditional scenarios, not verified account commissions. Each independent
counterfactual allocates at most half capital to each leg's gross entry notional,
rounding down to the admitted quantity grid; rule/minimum failure or insufficient
displayed quantity is unavailable. Reserve/collateral and liquidation feasibility
remain unadmitted, so even a positive cell cannot establish an affordable book.
The dollar hedge is imperfect and does not promise low BTC/ETH beta.

Use bid for selling and ask for buying at both boundaries. Compute per-leg
signed price-difference cash and deduct fees on each actual quoted entry/exit
notional. Report gross price difference, four crossing costs implicit in those
quotes, explicit fees and net conditional quote difference separately. No midpoint
fill, maker rebate, omitted hedge or arithmetic log-return PnL. Crossings must
not be charged twice as both bid/ask price effects and an extra spread deduction.
No full-capital annualization, Sharpe, compounded series or sum of overlapping
counterfactual profits is allowed.

A separate zero-fee same-quantity diagnostic may explain a negative result only
if included in the eventual fixed gate; it cannot substitute for either primary
fee cell or generate a new candidate. Funding absence cannot be presumed from a
short horizon. An event whose entry/exit or uncertainty overlaps an unadmitted
funding/settlement/rule boundary is unavailable; any later funding attribution
requires complete expected-event and ownership evidence. This screen does not
claim realized fills or event cashflows.

## Decision and finite stopping rule

After the entire capture is terminal and independently source-admitted, inspect
all four cells once. If no supported positive after-fee quote difference exists,
stop this fixed event/delay/direction screen. This is a necessary-condition
failure on the observed window, not global economic rejection. Inadequate source
support yields unavailable, not negative. A positive observation supplies only a
candidate episode for a separately registered dependence-aware test; maxima and
positive counts do not establish prediction, causation or expected profit.

The precise common-shock/null and portfolio comparison are NOT supplied by this
quote screen. No random-shift p-value, simultaneous basket hedge claim or favorable
subsample selection follows. A further empirical study would require enough
independent events, complete execution/funding/margin accounting and untouched
confirmation, with the same cumulative history.

## Admission work and resource boundary

Proposed caps: one local process, two CPU threads,512MiB,100MiB new raw data,
maximum20 public requests including handshakes/metadata, bounded10-minute window
plus two-second tail, no reconnect/retry, no credential/account endpoints. A
source failure terminates capture with retained prefix/intent/exit and no replay.
Resource tests must account for peak frame sizes/rates, flush/seal costs and
interference limits; no collector is built merely because this draft exists.

Before any implementation or allowance, independent design review must resolve:
(1) timestamp/unit/clock and aggregation semantics; (2) a defensible gap/completeness
contract rather than fabricated contiguous book IDs; (3) the information value
of the chosen delay/direction/horizon and proxy limitations; (4) exact source-rule,
funding-boundary and fee bindings; (5) preservation/runtime admission with the
active options claim and all terminal predecessors; and (6) a justified explicit
liquidity-family extension, never use of another row's spare slots. If these
cannot be resolved within a finite protocol, defer the candidate instead of
expanding it into a platform or fitting a different signal. Current state remains
one active options collection and zero new event-response financial tests.
