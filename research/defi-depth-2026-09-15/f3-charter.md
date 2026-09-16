# F3: fixed full usable-range liquidity provision

Pre-execution contract for the unused F3 financial slot. Exact source ownership,
inputs, resource reservations, code and this charter require commitment and
independent review before acquisition. No financial outcome has selected this
recipe. All frozen options, F2 and F1 contracts and results remain preserved.

## Economic question and control

Supply the exact Base WETH/native-USDC v3 pool's full usable range at spacing60,
ticks−887220/+887220, on September2 and hold unchanged until September1,2026.
The whole account starts with$10000 USD value, including0.005nativeETH for gas;
remaining funds are nativeUSDC. Invest half of that initial USDC budget, including
WETH purchase friction, in the position. Keep the other cash and all rounding dust.
No recentering, new range, leverage, reward token or intermediate collection.

The matched control purchases precisely the same WETH atoms and keeps the same
USDC allocation in its wallet. Its protocol-operation gas is lower because it
never mints an LP position. Common purchase costs and asset identities match.
Candidate LP inventory changes as the relative token price changes; fees accrue
once from entry global growth to terminal growth. The signed book counts both.
It never treats collected fees alone as incremental profit or subtracts a second
impermanent-loss debit after already marking the changed underlying inventory.

The candidate must meet the fixed$1000 absolute annual net hurdle,30% observed
drawdown and50% authored market/stablecoin stress. Fixed benchmark comparisons
include B0–B9, wallet cash, walletETH25 and the matched entry inventory, with the
same$200 incremental hurdle against every known numerically risk-eligible control.
The primary cost scenario decides; doubled-cost and frictionless outputs diagnose
cost sensitivity. Missing actual B1 and execution/confirmation evidence still
prevent implementability or adoption. No favorable metric or window substitution.

## Exact funded implementation model

Integer liquidity is the largest value funded by the fixed sleeve budget using
core mint rounding and the authored WETH purchase cost. This solves a funding
constraint; it is not return optimization. Both sides must be positive at entry.
Check observed boundary gross liquidity plus the new position against the actual
spacing60 maxLiquidityPerTick, and active-liquidity uint128 headroom at entry.
Preserve matched-control output when qualified capacity observations show
insufficient candidate mint headroom. Missing common panel/witness evidence
makes both LP and matched control unavailable under the fixed source recipe.

The candidate has ten modeled transactions: two for USDC approval/WETH purchase;
three for two token approvals and mint; two for burn/collect; two for WETH approval
and sale; one for the terminal native-gas sale. The matched inventory control has
five. Primary gas is0.0001ETH per transaction; doubled0.0002ETH; frictionless zero.
All gas is paid from the initial reserve. WETH and nativeETH are separate ledger
assets; the USD mark assumes parity explicitly, without a free wrap/unwrapping
cashflow. Native residual ETH is sold after funding its own gas. Any unfunded
positive dust exit remains unavailable.

The primary selected0.3% swap fee and10bp adverse execution apply on both entry
and WETH/native sales; doubled uses0.6% fee and20bp adverse execution; frictionless
uses zero for both. These are authored execution-cost scenarios, not a claim that
the protocol fee changed. USD terminal routing remains$10/$20/$10 across
primary/doubled/frictionless. The prefunded start and USD route are conditional,
not demonstrated personal funding or withdrawal routes.

Core principal burn rounds down. Both fee counters subtract modulo2^256 from
the fixed entry, with a single terminal position update, no intermediate fee
reinvestment and no pre-entry fees. Principal plus owed fees must fit uint128.
A decrease in cumulative attributed fees is unqualified, not a negative fee
credit that silently repairs reset counters. Every literal event is retained,
including if later valuation fails; partial attribution remains labeled partial.

## Stress and remaining limitations

At every funded state recompute LP principal after authored relative-price shocks
under an operating arbitraged pool: ETH−50/80/90%, USDC−20% with30day lock,7day
outage with ETH−50% and fivefold adverse execution, and combinedETH−90%/USDC−20%/
30daydelay with fivefold adverse execution.
Accrued fees remain held tokens; no extra fees accrue during the authored shock.
Record an ETH double-then−60% path drawdown separately. Whole-wallet loss and
whole-pool-position failure are separate total-loss tails; actual loss always
reduces NAV. Delayed-exit marks do not promise usable dollars at day365.

The reviewed global-growth identity attributes fees on the frozen historical
path. Adding the account's liquidity changes fee denominators and may change
flows, prices, flash activity and subsequent liquidity. This book does not prove
counterfactual realized fee revenue. Daily virtual-to-historical liquidity ratios
are disclosed diagnostics; they cannot bound intraday participation or capacity.
Deployment and immutable-source qualification remain required for the stated
source model, and bytecode identity alone is not complete semantics proof.

## Fixed denominator and cumulative selection

The initial committed capital is$10000, USD reporting over365days before personal
tax. The $200 incremental hurdle and authored stress scenarios remain explicit
research assumptions. Separate catastrophic wallet/contract/token losses may be
100% of affected positions; actual losses always enter NAV. Larger capital is not
a free remedy for an economically negative percentage return.

Three annual cohorts ending2024/2025/2026 remain visible. Only the fixed latest
cohort has a new source plan. The financial denominator is36books: three cohorts
by F3, matched-entry-inventory, walletcash and walletETH25, by three cost scenarios.
There are39 fixed latest-cohort D comparisons (13percostscenario), plus boundary,
primary-decision, implementation and confirmation:79financialcells and73outputs.
Every numerical book has an immutable attempt before financial arithmetic.
Incomplete source and cell-local feasibility failures remain unavailable; a
measurement defect retains literal partial ledgers and suppresses later books.
No alternate window, metric, fee-only accounting or cost diagnostic rescues a
primary failure. All D values and absolute P remain separately reported.

Seven direct predecessor claims are imported: original allocationDEX source,
Q1,Q2,R1,Q3,F2,F1. Family prior7/cap8 admits exactly this first LP recipe. The
original allocation188/189 and44 related DeFi records overlap; they are not
summed as independent tests. No confirmation allowance or alpha evidence arises
from these exposed development windows. Q4/F4 missing causal-universe evidence
and Q5/Q6 inherited failures remain preserved.

## Source requirements and ownership

Use the same fixed Base WETH/native-USDC0.3%pool identified in q1-spec.json,
0x6c561b446416e1a00e8e93e221854d6ea4171372. Daily fields are slot0, active
liquidity and both global fee-growth counters. Fixed entry/terminal witnesses are
USDC/WETH decimals, factory mapping, tokens, fee, spacing, maxLiquidityPerTick,
both boundary ticks and nonempty pool/WETH/USDC code. The maxLiquidityPerTick
getter selector is0x70cf754a, derived from Ethereum Keccak256 of its signature,
with uint128 output required to equal floor((2^128−1)/29575) at spacing60.
Full boundary/slot decoding and price/tick consistency are mandatory.

F1 owns the shared actual-clock headers and ETH/USDC prices. Wait for terminal
F1 reconciliation, reuse qualified exact raw bodies, and preserve all failed or
uncertain keys. Reuse USDC decimals/code already attempted in F1 at the same
blocks; a failed shared witness stays unavailable. No duplicate or semantic
alias of an earlier actual/uncertain source request is allowed. Fixed left-block
clocks must be within[target−1second,target]; no canonical adjacent-bracket or
nearest-block assertion is made. Transferred unattempted shared header/price/USDC
witness slots require exact terminal-audited suppression proof before new
ownership. Genuinely new LP-only keys require the complete terminal exclusion
union and semantic novelty checks; they have no earlier suppression receipt.
No new F2 or F1 result is filled or recalculated by F3.

F1's subsequent PC interruption happened with an empty output directory. Its
separately reviewed same-claim recovery preserves the scientific trial and
budget but adds execution provenance. F3 must register and verify the original
claim/terminal, shared attachment marker, recovery started/completed receipts,
recovery config/source/decision and review. The original source commit alone is
not the complete execution chain. These operational records do not create a
fresh sample, source retry or another financial attempt.

The daily fee-growth path remains conditional. Historical global counters do
not prove realizable fees after this account changes pool liquidity, nor do
daily capacity diagnostics bound intraday conditions. Oracle ETH/USD and USDC/USD
marks use the inherited unit model; nativeETH/WETH parity is explicit. Equal
proxy bytecode does not prove historical implementation semantics. Actual trading,
private account eligibility, usable USD withdrawal and untouched confirmation
remain unavailable unless separately evidenced under the frozen program.

## Finite source policy and closure

Use only the fixed public Base endpoint and reviewed financial source policy.
Three physical slots per genuinely new logical request; retry only registered
transient502/503/504 or specified transport failures,15seconds then60seconds
following the preceding response, minimum5seconds response-to-request pause.
Exact −32011 no-healthy-backend is the only RPC error compatible with those
transientHTTP retries. Complete RPC/schema failures receive no retry. Every
sent/unused attempt has a retained intent/receipt. Prior failures cannot consume
new retry slots. Acquiring distinct LP fields is not permission to restart F1.

Mandatory401/403/418/429/451, quota/throttle and access/TLS/authentication errors
stop the endpoint. Honor recorded Retry-After up to300seconds, with short sleep
chunks; malformed/longer delays stop the endpoint. No provider/VPN substitution.
Each request has a30second wall deadline; there is no experiment duration or CPU
kill. At most two computation threads. Retained-prefix limits are16KiB for calls,
64KiB for code and256KiB for headers; an extra detection byte is possible.

Freeze full request/byte reservations inside the shared25000RPC/2GiB envelope
before execution, reconciled against terminal F1 and prior claims. Documentary
60/60 and shared repair1/1 remain spent. F3 consumes one of four financial slots
and one of eleven total claims, independently of result. Continue the entire
registered inventory through isolated field gaps; endpoint denial suppresses
later sends but preserves all unavailable cases. Financial and source completion
are different claims. Independent raw/accounting/denominator/selection review
must distinguish economic failure, source absence and inadequate evidence.
No orders, paid resources, wallet/account action, production mutation or new
ongoing monitor is authorized by this contract.

The F1 closure review must inventory the entire original recovery-receipt
directory, including hidden, failed or pending records, and preserve it byte for
byte before adding the separate attachment marker to the imported directory.
The F3 handoff accepts exactly started.json, complete.json and attachment.json;
any additional record requires a separately reviewed disposition before F3
admission. A selected completion subset does not prove successful recovery.
