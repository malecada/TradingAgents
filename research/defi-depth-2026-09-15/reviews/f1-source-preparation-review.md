# Independent F1 source-preparation review

## Conclusion

The retained scalar getters can support a separately registered, explicitly
conditional normalized-income book. They do **not** establish deployability or
a treasury-inclusive entry-cap proof. A cap-unproved primary cell must remain
unavailable. A separately frozen generous opportunity bound is informative,
provided its rounding is an actual upper bound and passing it never rescues the
primary decision. No acquisition or financial calculation is admitted here.

This review inspected retained specifications, code, source-model documents and
the public address-book receipt only. No Aave observations, empirical returns,
network request or active F2 root/process was accessed. Only this review file was
written. The newer coordination documents supersede the initial brief's59/60
documentary count: `MULTICALL-PREFLIGHT.md:3` reports60/60. No lookup allowance was
used by this reviewer or assumed to remain.

## Exact retained Aave surface

Base identities in `q1-spec.json:256`–263 are the public Base endpoint, native
USDC `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`, Pool
`0xa238dd80c259a72e81d7e4664a9801593f98d1c5`, and aToken
`0x4e65fe4dba92790696d040ac24aa414708f5c0ab`.

| Getter | Target and argument | Selector | Qualified return shape / retained specification |
|---|---|---|---|
| `decimals()` | USDC | `313ce567` | canonical uint8, expected6; Q1 line274 |
| `POOL()` | aToken | `7535d246` | canonical address, expected Pool; Q1 line298 |
| `UNDERLYING_ASSET_ADDRESS()` | aToken | `b16a19de` | canonical address, expected native USDC; Q1 line310 |
| `getReserveNormalizedIncome(address)` | Pool, USDC | `d15e0053` | one uint256; Q1 line322, Q2 line5521 |
| `getConfiguration(address)` | Pool, USDC | `c44b11f7` | one raw uint256; Q1 line331, Q2 line5531 |
| `balanceOf(address)` | USDC, aToken address | `70a08231` | public contract cash, uint256; Q1 line340, Q2 line5540 |
| `scaledTotalSupply()` | aToken | `b1bf962d` | uint256; Q1 line349, Q2 line5549 |
| `totalSupply()` | aToken | `18160ddd` | uint256; Q1 line358, Q2 line5558 |

Q1's consistency check at `q1_source.py:193`–203 compares total aToken supply
with half-up `scaledSupply*income/RAY`, allowing one base unit. This is a public
aggregate consistency observation, not validation of a hypothetical investor's
mint, withdrawal, fee or priority. Q2 repeats the relation. It does not include
unminted treasury or establish total borrower debt.

`q2-spec.json:5661`–5678 additionally registers Pool/aToken implementation-slot
witnesses at the EIP1967 slot
`0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc`.
`q2-charter.md:45`–58 explicitly limits their interpretation: a nonzero stored
address is not deployed-behavior proof, and raw configuration was not permission
to assume a modern historical layout. Repeated slot values cannot exclude all
intraday upgrades or other semantic changes. Q3 adds wrapper/oracle observations,
not lending treasury/debt fields; `q3_source.py:221` explicitly retains continuous
semantic qualification as unavailable.

The retained address-book body hash
`135e2f325b53140c5a82895cf40debc80323fed77bd3ebb240a8d00248ba02ae`
was independently verified before inspecting its source constants. Its receipt is
dated2026-09-15T16:07:05.163003+00:00. It contains the current USDC variable-debt
candidate `0x59dca05b6c26dbd64b5381374aaac5cd05644c28` and a protocol data-provider
candidate `0x0f43731eb8d45a581f4a36dd74f5f358bc90c73a`. Those constants are not
historical reserve bindings or verified debt-token behavior. Absence of a stable
debt constant in the scoped declaration does not prove zero historical stable
debt.

## What a full reserve tuple would and would not establish

No reviewed Q1/Q2/Q3 specification registers a full `getReserveData` decoder,
stored treasury or current debt-token supply. Do not invent return positions from
memory or accept an arbitrary tuple solely because its length looks familiar.
The Pool and data-provider can expose the same
`getReserveData(address)` signature while returning different structures.
Independent Keccak gives selector `35ea6a75`; a selector encodes neither target
contract identity nor return layout. Historical compatibility returns and
repurposed fields require the exact selected source model/version.

If the Pool tuple's model is qualified, it can supply stored reserve indices,
timestamps, configuration, treasury and debt-token identities. It does not by
itself turn stored treasury into the post-update treasury used by a subsequent
supply, and debt-token addresses/rates are not current aggregate debt amounts.
A properly qualified data-provider may supply debt totals, but its interface and
same-block debt semantics must be established separately. AToken scaled/total
supply measure lender claims; they cannot replace total variable plus stable
debt. Neither `totalSupply−cash` nor a zero-filled missing component is a proved
debt bound in the presence of treasury, unbacked claims, rounding or deficits.

For the conservative entry proof, the sufficient inputs remain same-state
`S` (scaled aToken supply), stored scaled `T`, the hypothetical update's index
`I`, current underlying-debt upper bound `D`, config/reserve factor and the fixed
deposit. The source model must justify nonnegative accrued interest bounded by
`D`, percentage/ray rounding and the timestamp relationship. Then
`ray_mul(S+T+ray_div(D,I),I)+deposit <= cap` is sufficient; failure is inconclusive.
The already-reviewed `lending-math-review.md` and `f1-design-review.md` spell out
the assumptions. Exact pending-interest reconstruction is unnecessary when that
bound passes, but merely reading stored treasury/debt fields does not prove its
assumptions. A genuinely disabled cap short-circuits only the cap question.

## Cheapest adequate conditional route

Reuse the five known daily Aave getters and qualified common USD marks/headers,
with fixed source identity, canonical block tags, availability handling and
integer limits. Entry and terminal identity witnesses can support the declared
model. Do not add hundreds of implementation-slot calls on the premise that
addresses alone would solve historical behavior. Any extra witness should answer
a specifically frozen question. A complete entry-cap proof is needed only at the
sole deposit, not every day; withdrawal cash/flags and interim liquidation limits
remain separate.

Within this route, a numerical normalized-income claim is conditional on the
mint/burn model and on following the recorded index path. The extra deposit can
change reserve utilization, rates and subsequent borrower behavior; a historical
index series does not prove the new investor would earn precisely that path.
Aggregate supply coherence does not remove this counterfactual limitation.
Positive contract cash cannot prove redemption timing, solvency, priority,
transferability or personal eligibility. All such gaps block deployability even
if a conditional number is favorable.

An unproved cap must remain unproved, not a generic economic rejection. A
diagnostic assuming entry and withdrawal can still measure the conditional
opportunity, with fixed70% allocation, full prefunded capital, all unavailable
cases and no primary promotion. If USD marks are unavailable it can report only
qualified underlying-unit evidence, not dollar P/D.

## Opportunity-ceiling correction

Continuous, unrounded claim units are **not** automatically an upper bound on
half-up protocol accounting. An invented deposit of one underlying atom at
1.5RAY mints one scaled unit and redeems two underlying atoms at an unchanged
index; the unrounded continuous claim returns only one. Therefore an economic
ceiling must include a proved rounding allowance.

A simple sufficient integer construction for the identical deposit `A` is:

```
upper_scaled = ceil(A*RAY/I_entry)
upper_terminal_underlying = ceil(upper_scaled*I_terminal/RAY)
```

Each ceiling dominates the corresponding half-up step, and multiplication by a
positive index is monotone.1,000 independently generated integer cases confirmed
the bound. Add the unchanged idle USDC and all surviving initial native gas,
mark them with the same qualified positive USD model, and omit only explicitly
nonnegative modeled costs in this separately registered diagnostic. Omitting the
USD route here is allowed as a stated generous bound; it must not alter the
primary or the earlier frozen frictionless scenario.

Below$1,000, this corrected bound establishes only that the specified fixed
source-model opportunity cannot meet the absolute target, even under generous
entry/withdrawal/cost assumptions. Above$1,000 is inconclusive. Neither result
establishes native protocol profitability, and it cannot rescue unavailable
primary feasibility. Preserve exact rational comparisons at the boundary.

## Aggregation and preservation

`MULTICALL-PREFLIGHT.md:10`–20 reports that Base deployment and historical runtime
were not verified by the available documentary evidence. No Multicall address,
ABI wrapper or on-chain route is admitted from memory. Direct existing calls are
the supported preparation path. If aggregation were ever separately qualified,
it would still need explicit getter whitelists, per-member failure/ABI evidence,
same-block semantics and transparent RPC/inner-getter/resource counts; it cannot
hide scientific requests or replay failed observations.

No new source permission follows from this investigation. F1 must remain one
indivisible frozen financial attempt with existing source budgets, retired
failures and header ownership intact. Unsent-header routing is conditional on
the terminal-only proof in `f1-design-review.md`; actual or uncertain attempted
keys remain excluded. Nothing here changes active F2, repairs Q1/Q2/Q3/R1, or
creates another documentary lookup or confirmation allowance.

## Provisional actual-clock and future retry route

The F2 owner subsequently reported an HTTP503 right-header failure after a
successful left header, followed by suppression of later requests. This reviewer
did not inspect the active execution root or independently establish that
closure. The following route is conditional on terminal independent accounting
of every attempted, uncertain and explicitly unsent observation.

An unfrozen F1/F3 source model may prospectively require one canonical block's
own recorded timestamp to lie in `[nominal target−1 second, nominal target]`,
instead of requiring an adjacent right-header bracket. Use the actual recorded
timestamp and hash for all state observations. This establishes a bounded actual
clock; it does **not** establish the nearest block, absence of an intervening
block, an exact midnight fill or the old adjacent-bracket qualification.
Freeze this rule for the entire new financial question before outcomes, without
choosing dates from economic values.

Successful old left headers can be reused as such. Old failed/uncertain right
requests remain excluded and the old F2 source/financial cells remain failed or
unavailable under their original rule. Only demonstrably unsent future header or
price observations can receive prospective ownership under F1's indivisible
financial contract. A changed getter/vector/method cannot disguise remeasurement
of a previously failed overlapping observation. F1 must not backfill F2, finish
Q2/R1/Q3, claim old source completion or run the old F2 book from newly acquired
inputs. Exact identity, attempt provenance and all overlapping history belong in
the new registration. Under these conditions, this is a new source estimand for
an unused financial question, not an additional repair. Otherwise it is not
admitted by this recommendation.

`PHASE.md:21`–22 and69–72 require explicit pre-result retry counts and prohibit
unregistered retries. They do not prohibit every prospectively enumerated retry
within a new financial claim. The frozen F2 no-retry rule remains unchanged.
A future F1 transport can therefore propose three physical attempt slots per
newly owned logical key, with fixed15/60second delays and only explicitly
enumerated HTTP502/503/504 or transport-timeout triggers. This is a proposal for
exact code/gate review, not an executed or admitted transport.

Every physical send, uncertain send, receipt, error and unused slot must remain
counted and retained; worst-case requests/bytes must fit the remaining phase
envelope. Authorization denial, throttling or quota/rate text takes precedence
over a superficially transient HTTP status and stops the endpoint. No retry of
RPC/schema/ABI/scientific failure, provider substitution, new logical key alias,
old failed/uncertain observation or extra financial claim follows. An ordinary
transient backend outage is not automatically an authorization denial, but its
classification must use retained actual response evidence. All novel retry and
clock semantics require independent review before the new claim begins.
