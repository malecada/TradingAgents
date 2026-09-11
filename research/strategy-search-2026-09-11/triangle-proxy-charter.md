# Static triangular conversion proxy — frozen economic question

Experiment triangle-proxy-20260911, parent triangle-inputs-20260911. This is
exploratory development, the second of at most three new investigations for
spot-triangular-conversion and also charged to MAP row 5. Zero known exact old
triangle gates is not zero previous liquidity search; OFLOW/passive failures and
unknown historical multiplicity remain. No fresh holdout or confirmatory claim.

## Question and fixed denominator

For the single previously fixed BTCUSDT/ETHUSDT/ETHBTC batch book-ticker response,
do either of two idealized static conversion cycles return more USDT than they
consume under zero fees and an assumed 0.1% fee on each received asset? The
payer, if an executable discrepancy existed, would be inventory imbalance across
three linked spot books. This probe establishes arithmetic feasibility only.

Eight cases: USDT→BTC→ETH→USDT and USDT→ETH→BTC→USDT, each at initial full capital
1,000 and 10,000 USDT, each with received-asset fee 0 and 0.001. These scales
approximate the user's dollar budgets without asserting a riskless dollar peg.
No symbol, direction, threshold, fee or snapshot selection after outcomes. No
additional capture, retry or alternative price source. All cases retained even
when inputs are unavailable or displayed size insufficient.

## Inputs and accounting

Use only immutable parent capture and admission, hashed in the gate, with their
actual request/retrieval interval treated exposed. Reconstruct six source bodies
and compare successful normalized admissions exactly. Exchange-info and batch
book-ticker are required; depth and server-time availability remain explicit but
cannot establish fills or substitute prices. No account access or permission is
inferred from exchange metadata. No cross-market simultaneity is inferred.

Continuous unrounded buys divide by best ask; sells multiply by best bid. Each
fee reduces the acquired asset before the next leg. The initial full notional is
forced through all three idealized legs. Final USDT minus initial USDT is the
arithmetic cash proxy, with gross and fee reconciliation, and corresponding
simple return. Log-factor times capital is an invalid PnL shadow retained only
to expose that accounting mistake. No perpetual funding, borrow or opportunity
cost is charged to the static algebra; actual latency, impact and leg-risk costs
are unknown, not zero execution costs. Displayed-size checks use pre-fee traded
base quantities, without modeling fills. Actual trading filters, lot rounding,
residual cash and partial fills are unmodeled.

The unit conversion factor is optimistic only under simultaneous static quotes
and the specified fee model. Factor ≤ 1 excludes positive cycle profit within
that model. The forced-full-notional ending wallet is not a universal wealth
upper bound with abstention, smaller sizing or idle residual cash. Actual
asynchronous quotes do not establish an executable arbitrage in either direction.

## Decision and inference

Factor ≤ 1 for both zero-fee directions: this snapshot offers no positive static
cycle even before fees; do not replay the same observation or reject the family
for all times. Zero-fee positive but assumed-fee nonpositive: fees erase the
modeled discrepancy. Assumed-fee positive: further time-aligned executable-depth,
filter and partial-fill evidence is required; no strategy graduates. Insufficient
size keeps the proxy and the failed capacity flag, not a fictitious fill.

One observation provides no expected-return confidence interval, test power,
annual frequency, beta estimate, drawdown path or 3% annual relevance verdict.
All these are explicitly unavailable. Two cycles and two capital scales are
correlated algebraic cases, not independent trials. Interim inventory can carry
full capital in BTC or ETH between legs. Execution losses and unwind cannot be
bounded from this snapshot. Zero validated strategies and no orders remain.

## Resources and closure

Pinned Python and lifecycle; one foreground run, at most two CPUs, 512 MiB
sampled aggregate RSS and 120 seconds under frozen resource_guard_v2.py. No
network. One proxy.json output capped at 2 MiB; eight declared cells. Abrupt
failure retains its immutable claim/failed receipt and consumes this attempt.
Synthetic arithmetic/receipt tests and independent pre-review precede committed
source/gate freeze and verified remote backup. Independent reconstruction of
actual arithmetic and receipt verification follow execution, then a durable
decision and backed-up state. Select the next distinct informative question from
the program map; repeated snapshots require a separately justified finite design.
