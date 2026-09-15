# Protocol accounting design and engineering scope

Status: preparation with invented quantities only. No financial recipe, actual
protocol transformation or empirical result is admitted by this document.
`protocol_math.py` is an additive helper; the original spot ledger, original
financial books and live R1 source are unchanged. R1 continues in its isolated
root at aa926ef. The remaining financial gates must pin these exact dependencies
and independently qualify their inputs before using them.

## One funded account, several kinds of claims

Each inventory key identifies location and asset. Wallet tokens include chain
and contract; LP receipts include pool/version/range/position identity; redemption
claims include queue/request identity. Supply consumes underlying tokens and
creates a receipt. A queue request consumes the staking receipt and creates a
pending redemption claim. Neither transaction creates simultaneous spendable
cash. Withdrawal consumes the claim and credits only the actual modeled proceeds.

The existing `SpotBook` supplies signed postings, fees, missing-mark rejection,
transfer receivables and write-offs. `ProtocolBook.convert` adds a single atomic
conversion of explicitly supplied quantities. It requires enough input assets
and gas before receiving any output. A failed on-chain transaction requires a
separate gas debit; a rejected local calculation alone does not invent a paid
transaction. No helper looks up or defaults a receipt price, discount or delay.

Liquidation wealth includes every idle USDC balance, native gas token, LP token
inventory, collectible fee and remaining claim, less only unpaid exit costs.
Already debited gas, spread and commission are not charged twice. Every positive
position requires a qualified mark; missing redemption or market value stays
unknown. Separately reporting a catastrophic scenario does not remove an actual
loss from account NAV.

## Lending: separate accounting accrual and investor redemption

The source panel supplies normalized reserve income and aToken supply identity,
not a user account's executed mint/burn. Before a financial calculation, qualify
the actual implementation and rounding at each relevant version. A hypothetical
deposit must debit underlying, retain rounding residuals and produce the scaled
claim the implementation would create. Later claim value may use that scaled
quantity and the qualified index; interest is not also credited to cash.

`converted_units` is an exact rational conversion primitive with explicit floor
or ceiling. It is not an implementation of all Aave versions. In particular,
ray-half-up supply identity checks from Q1 cannot be silently reused as every
investor mint/burn rule. Decreasing or reset indices require interpretation of
the actual deployment, not a forced nonnegative return.

Entry constraints include supply enablement, caps and gas. Exit constraints
include pause status, unborrowed liquidity, protocol solvency and transaction
execution. The public aToken cash balance is useful but insufficient. A price
oracle can report a dollar mark without proving that dollars or USDC can be
received then. Terminal claims with a waiting period beyond day365 do not count
as cash delivered within the investment horizon.

## Staking: three separate price and quantity channels

For q wrapper units, r stETH units per wrapper, d market ETH per stETH, and p
USD per ETH, the gross liquidation proxy is q*r*d*p. The units and clocks must
match. Direct wrapper/USDC executable prices already embed r and d; multiplying
by the conversion ratio again would double-count rewards. Protocol conversion,
market sale and queued ETH redemption are separate exit routes. A route must be
chosen before outcomes, with unavailable alternatives retained as diagnostics.

An unhedged staking/cash book compares with both identical initial ETH exposure
and the fixed broader cash/crypto comparator panel. It cannot claim staking
value merely because ETH appreciated. A queue model must retain request time,
claim ownership, finalization, token/reward changes while waiting, claimable ETH,
claim transaction costs and delayed access. A present-day queue state cannot
reconstruct a past investor's place in that queue.

Base's bridged wstETH and Ethereum's native wrapper have different interfaces
and risks. The native conversion method cannot be assumed on the bridged token.
Any bridge/market discount belongs to the chosen position's cash book. More
capital can reduce fixed gas drag; it does not fix a missing exit or guarantee
a staking reward exceeds ETH price losses.

## LP inventory: integer cash quantities before dollar metrics

For liquidity L and square-root prices a < s < b in raw token1/token0 units,
inventory is L*(1/s-1/b) token0 and L*(s-a) token1. Outside the range, s is clamped
to its boundary. The helper uses integer Q64.96 prices. Mint debits round up;
burn proceeds round down. Periphery sizing retains its intermediate truncation,
then verifies that core mint quantities fit both funded token balances. Leftover
tokens remain in the wallet. Integer helpers reject unsupported overflow ranges.

The additive v3_ticks.py helper now supplies exact TickMath boundaries, retaining
integer intermediate truncation and contract rounding. Five invented-input tests
and independent170digit multiplier reconstruction pass. Actual pool spacing and
deployed semantics remain source qualifications; see reviews/v3-ticks-review.md.

Inside fee growth excludes growth below and above the position. Boundary-outside
counters depend on current tick and boundary initialization/crossings; their
differences use uint256 modular arithmetic. Accrued tokens for a single unchanged
position update equal the floor of L times the inside-growth delta divided by
2^128. Daily observation is not a daily fee collection: repeatedly rounding
daily increments would alter the actual terminal claim. The helper rejects
uint128 owed-balance overflow instead of treating a wrapped balance as cash.

An initialized boundary snapshot alone does not prove uninterrupted identity.
Clearing/reinitialization or an absent hypothetical boundary can change the
meaning of the counters. A caller's `boundaries_qualified=True` flag is a required
assertion, not its proof. The consuming gate must specify evidence or mark the
position's fee calculation unavailable. Likewise, modular arithmetic cannot
distinguish a legitimate wrap from an incorrectly joined/reset source counter.

A subsequently reviewed proof supplies a narrower exception for a continuously
held **full usable-range** virtual position on the fixed historical path:
global fee-growth increments equal its virtual inside-growth increments.
Historical boundary clearing therefore does not require reconstruction for that
specific attribution. Arbitrary ranges retain the above requirements. See
reviews/full-range-fee-identity.md for proof and assumptions. This does not prove
counterfactual earnings after adding liquidity, especially during historical
zero-liquidity intervals, or establish actual mint/exit capacity.

The primary LP comparator starts with the exact same token quantities and gas
reserve. Account return and incremental LP value are both reported. There is no
second subtraction for inventory divergence once final token inventories are
valued. Principal burn, fee collection and token liquidation are distinct cash
events; collection costs cannot be omitted because the fees are still in a
contract. Incentive tokens require their own entitlement, quantities and exit.

Historical fee growth assumes the recorded liquidity and price path. Adding a
position dilutes fee share and can change execution. Daily active liquidity
alone cannot bound all intraday participation or liquidity cliffs. A price-taking
book therefore remains explicitly conditional unless a preregistered capacity
bound is supported. Increasing capital can worsen this condition.

## Execution costs that still need admission

| Route component | Required treatment |
| --- | --- |
| Initial funding | The already-funded USDC starting point remains a disclosed hypothetical. Actual USD purchase/withdrawal/bridge basis is separate and cannot be assumed paid before the test. |
| Gas reserve | Buy/fund and hold native tokens within the $10,000 total; retain their USD gains/losses and leftover liquidation. |
| Approval, supply/mint, exit/collect | Count each required transaction and failed transaction assumption. Token allowances are modeled, never queried on the user's wallet. |
| L2 transaction cost | Base header baseFeePerGas is only one component; gas units, priority fee and L1 data fees need evidence or authored conditional values. |
| Swaps | Include pool fee, adverse price movement, depth, MEV/slippage and output minimum. A spot oracle is not a two-way executable quote. |
| Transfer/bridge | Include fees, delays and claim ownership throughout; no instant shared balance across chains/venues. |
| Terminal USD | Distinguish a valued token claim from net USD cash. Delayed/unavailable redemption is retained. |

No gas or execution number is silently borrowed from the earlier Binance-only
book. A lower-cost/frictionless scenario can diagnose cost drag after freezing;
it cannot become the primary scenario because it gives a better result.

## Frozen economic objective to carry into each financial gate

At $10,000, annual absolute net P >= $1,000 and incremental D >= $200 against
every independently feasible comparator remain necessary, alongside 30% drawdown,
50% market/stablecoin stress and the accepted cost robustness conditions.
The primary scenario must be named in advance. Unknown comparator feasibility
does not authorize dropping it. B1 accessible cash is still unavailable.

Three calendar cohorts are development exposure, not three independent trials.
Their use in the decision rule must be frozen before financial outcomes; the
best year or a retrospectively preferred CAGR cannot replace the annual cash
question. All ten original comparators and route-matched controls need explicit
availability, risk and capital comparability. Financial variant/contrast counts
must be expanded prospectively; the old88 contrast reserve is not sufficient.

## Engineering verification and source basis

Thirteen invented-input tests initially passed: rational inventory integrals,
mint/burn rounding, funded sizing, boundary cases, outside-range fee exclusion,
fee-counter wrap, terminal rather than daily rounding, unit conversion, missing
claims, atomic debits, prefunded gas and duplicate events. They establish no
historical profitability, actual protocol compatibility or implementation gate.
Independent review is required before use.

The initial independent review found an ambient Decimal precision defect in the
unfrozen conversion interface: an invented10^30balance could lose a1unit debit.
No empirical calculation used this helper. The additive subclass now wraps all
exposed ledger arithmetic, including inherited operations, in256digit precision
with inexact-result traps. Values outside that exact domain fail before mutation.
Regression cases cover low ambient precision, large-balance debits and atomic
rejection beyond the supported precision. Frozen spot_book.py remains unchanged.

The four official source reads below add four documentary operations, bringing
the phase inventory to45/60. They are current source-code orientation, not proof
of historical deployed bytecode. Original source attribution and licenses remain
at the linked repositories; the helper implements mathematical relationships.

- [v3 inventory rounding](https://raw.githubusercontent.com/Uniswap/v3-core/main/contracts/libraries/SqrtPriceMath.sol)
- [v3 periphery sizing](https://raw.githubusercontent.com/Uniswap/v3-periphery/main/contracts/libraries/LiquidityAmounts.sol)
- [v3 position fees](https://raw.githubusercontent.com/Uniswap/v3-core/main/contracts/libraries/Position.sol)
- [v3 tick fee accounting](https://raw.githubusercontent.com/Uniswap/v3-core/main/contracts/libraries/Tick.sol)
