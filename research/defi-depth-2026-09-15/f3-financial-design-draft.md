# F3 full usable-range liquidity provision: unexecuted financial proposal

This is the fixed50% of initial investable USDC proposal preserved in
financial-design-draft.md, now implemented with invented-input accounting checks.
It is not admitted source acquisition, a financial result or a new strategy grant.
The active options study and F2 source contract remain unchanged.

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
Preserve matched-control output if candidate mint capacity is unavailable.

The candidate has ten modeled transactions: two for USDC approval/WETH purchase;
three for two token approvals and mint; two for burn/collect; two for WETH approval
and sale; one for the terminal native-gas sale. The matched inventory control has
five. Primary gas is0.0001ETH per transaction; doubled0.0002ETH; frictionless zero.
All gas is paid from the initial reserve. WETH and nativeETH are separate ledger
assets; the USD mark assumes parity explicitly, without a free wrap/unwrapping
cashflow. Native residual ETH is sold after funding its own gas. Any unfunded
positive dust exit remains unavailable.

The primary selected0.3% swap fee and10bp adverse execution apply on both entry
and WETH/native sales; doubled friction is an authored cost scenario, not a claim
that the protocol fee changed. USD terminal routing remains$10/$20/$10 across
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
outage with fivefold adverse execution, and combinedETH−90%/USDC−20%/30daydelay.
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

No new financial observations have selected the range, allocation or fee policy.
Exact source fields, common-header/price ownership, code witnesses, physical
attempts and denominator still need one committed F3 registration and independent
pre-execution review. Its finite financial slot remains unused.
