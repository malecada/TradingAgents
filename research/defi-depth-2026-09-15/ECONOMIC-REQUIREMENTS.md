# What each mechanism must earn

Preparation and algebra only. No real price, index, fee or return observations
have been evaluated by this document or protocol_stress.py. The four financial
recipes remain unexecuted. Numerical examples below are invented illustrations,
not investment forecasts, selected parameters or revised user preferences.

## Full-capital profit and incremental value

At the $10,000 baseline, the accepted10% annual target requires at least$1,000
net cash profit under the explicit365-day research horizon. The2%-capital
incremental hurdle is a separate authored research assumption: at least$200
against each applicable independently feasible benchmark. Both must be reported;
a strategy can make money yet add no value over passive exposure or cash.
Unknown benchmark feasibility is retained, not treated as permission to omit it.

All wallets, exchange balances, gas reserves, receipt tokens, bridge/queue claims,
unused cash and terminal dust belong to the same funded account. A protocol's
APR is not the account's return. Delayed or unavailable liquidation is not cash
received at the deadline. Daily NAV and actual cash realization remain distinct.
The primary financial rule cannot be chosen after observations.

## F1: unlevered stablecoin lending

Economic source: borrower payments allocated to suppliers. Competing explanation:
the quoted rate compensates for stablecoin, credit, withdrawal and protocol risk;
a favorable current rate need not persist. Lending index growth describes a token
claim, not necessarily withdrawal proceeds. Incentive tokens, if any, require
separate units, realization costs and dilution treatment rather than a headline APR.

For an ideal frictionless account with lending fractionw, lending token-growth
g, idle-cash growthc and unchanged USD marks, gross account growth is
w*g + (1-w)*c. Thus even a10% lending yield does not meet the10% account target
when some capital earns less and costs are positive. In an invented example,
80% lent at10% and20% idle at0% gives8% before costs. The required yield would be
12.5% before costs. These are algebraic cash shares, not observed Aave yields.

The cheapest informative financial check, once inputs qualify, is the fixed
full-capital signed book plus a separately labeled frictionless diagnostic.
It must retain aToken rounding, withdrawal capacity, aToken/underlying identity,
protocol version, actual USDC/USD marks, entry/exit charges and market-driven
credit losses. A bad net result with a good frictionless result identifies a
cost problem; failure even in the stated frictionless model narrows the modeled
mechanism. An oracle/index without an admitted cash route cannot support either
an implementability claim or an unconditional bound on real executable profit.

## F2: unhedged staking with cash

Economic source: ETH-denominated quantity growth. Competing explanations are
ETH price appreciation, wrapper valuation changes, lock/liquidity compensation
and risk transfer. A higher token count can coincide with fewer dollars.

For an ideal account, ETH price factorp, staking quantity factorq and allocationw
give a staking-sleeve factorp*q. Idle cash has factorc. Before costs, terminal
account factor is w*p*q + (1-w)*c. The matched unstaked allocation is
w*p + (1-w)*c, so the modeled staking increment is w*p*(q-1). This decomposition
is invalid if a wrapper market price already includes quantity growth and q is
then added again. Wrapper discount, slashing and queue haircut must be treated
in their appropriate channels, not double-counted.

In an invented example withw=0.30,p=0.50,q=1.04,c=1, staking quantity rises4%
but the account loses14.4% before costs. The matched unstaked allocation loses15%;
the staking increment is0.6percentage points. This illustrates why absolute
profit and benchmark-relative value are separate tests.

The primary redemption route and its timing must be frozen. Requesting a
withdrawal at day365 does not create dollars at day365. Direct wrapper sale,
bridge redemption and native queue claims are different realizations; they
cannot be substituted after seeing which exit looks better. Native historical
conversion and wrapper market price are not interchangeable evidence.

## F3: low-maintenance liquidity provision

Economic source: swap and possibly flash fees. Competing explanation: those fees
compensate for selling the rising asset and buying the falling asset, adverse
selection, exit costs, price impact and custody/protocol exposure. Low turnover
by the owner does not mean the pool's underlying inventory stays unchanged.

The appropriate direct control holds the exact funded entry-token quantities.
Both control and LP account retain cash/gas leftovers. LP terminal inventory is
computed from exact liquidity, ticks and terminal pool price, with separately
claimable fees. Comparing that total wealth with the control already captures
inventory divergence; subtracting another impermanent-loss charge counts it twice.

The reviewed full-usable-range identity allows attribution from historical global
fee growth under strict protocol/path assumptions. It does not establish that a
new investor would earn the attributed fees. Adding liquidity changes its share
of fees and can change price/flow paths. In an ideal proportional fixed-flow
calculation, virtual liquidityl added to historical active liquidityL receives
L/(L+l) times its infinitesimal attribution. If a verified positive lower boundm
holds at every fee-producing step, that ratio lies between m/(m+l) and1.
Daily snapshots cannot certify that intraday bound. Integer rounding, zero-active-
liquidity intervals, changed flow/prices and flash mechanics remain outside this
ideal identity. It is not an executable fee-profit bound.

The added protocol_stress.py uses exact integer square-root scaling for a chosen
operating/arbitraged-pool scenario: sqrt-price changes by sqrt(factor0/factor1),
where factors are separate token/USD shocks. Inventory is recomputed, not frozen.
Equal proportional USD shocks leave relative inventory unchanged while reducing
both token values. No favorable shock fees are credited in that chosen scenario.
A paused/unreachable market cannot be assigned an arbitraged executable price
merely by calling the helper. These primitives have invented tests only.

## F4: mature-token adoption

The hypothesized chain is specific adoption evidence, increased token demand or
credible holder distributions, then sufficient realized value to pay dilution,
transaction costs and losses on failed holdings. More users alone need not
benefit a governance token. Incentives, wash activity, issuance and common market
beta are explicit competing explanations.

The source investigation found preserved monthly universe metadata but also
later identity/rank mapping and a different inherited wallet-flow estimand.
Financial testing requires a causal roster, failures, supply/unlock vintages,
a defined value-capture channel and two-way exit. A missing price cannot remove
a losing holding; a purchase quote does not prove future sellability. Low-cap
labels and lower gas on a chain do not establish the economic mechanism.

## When greater capital can help

More capital can dilute fixed costs; it cannot cure negative gross economics,
missing data, percentage fees, risk violations or absent liquidity. In a purely
algebraic model with evidenced gross rate g, proportional costs v, annual targett
and fixed dollar costF, the condition is C*(g-v-t) >= F. A finite threshold
C >= F/(g-v-t) exists only when g-v-t is positive. Capacity/impact must remain
valid at that C. No larger capital amount is selected merely to improve a report.

## Next admission decision

Q3's boundary observations passed for two cohorts, but the runner subsequently
failed its current-HEAD check; see Q3-RESULT.md. No annual panel was captured.
Retained values require independent review before any financial use. F1/F3 require a
legitimate source route after the preserved failed R1, not a renamed retry;
independent review is assessing whether a distinct financial recipe can acquire
never-attempted prerequisites within the remaining grants. Q4/Q6 source limits
remain inadequate evidence, not economic failure. No source failure or long
runtime is being presented as proof that a mechanism cannot work.
