# Triangle conversion proxy: independent pre-result review

Disposition: accounting and pure synthetic verification pass. Financial
execution admission is still pending the source-capture review and final bound
charter, runner and gate. No actual quotes, APIs, price histories or candidate
results were read. Only this review document was written by the reviewer.

## Independent accounting checks

For BTC-first routing, the gross unit factor is
`bid(ETHUSDT) / [ask(BTCUSDT) * ask(ETHBTC)]`. For ETH-first routing, it is
`bid(ETHBTC) * bid(BTCUSDT) / ask(ETHUSDT)`. The code applies each purchase at
ask and sale at bid, with the proper base/quote currency dimensions. A received-
asset fee fraction f on each leg gives net factor `gross_factor * (1-f)^3`.
The terminal wallet is USDT; intermediate BTC/ETH wallets close to zero in this
idealized continuous cycle. No fictitious extra starting inventory is introduced.

Independent 60-digit Decimal reconstruction used two invented spread/parity-
deviation quote sets, both directions, both capitals and both fee cases: sixteen
synthetic cases and 304 numerical comparisons. The maximum discrepancy was
2.228e-12 USDT/asset units, below 1e-8. Per-leg gross receipts, actual received-
asset commissions, net receipts, downstream fee conversions, terminal wallet and
simple cash profit all reconciled. The ten focused source tests also passed.

Each paid fee is converted through only the subsequent **gross** quote rates
(`triangle_bound.py:76-89`). Because the second and third actual fees are already
computed on reduced preceding receipts, their sum is exactly the zero-fee terminal
wallet minus the fee-paying terminal wallet. This is a correct decomposition,
not double-counting or an assumption that the fees were paid in USDT. The symbol
USDT is retained; no USD peg or independent fee-token account is assumed.

The two gross unit factors multiply to
`[bid(BTCUSDT)/ask(BTCUSDT)] * [bid(ETHUSDT)/ask(ETHUSDT)] *
[bid(ETHBTC)/ask(ETHBTC)]`, which cannot exceed one for uncrossed positive quotes.
Independent Decimal checks verify that identity. At exact currency parity with
zero spreads and zero fees both factors equal one. At parity and 10 bp per leg,
1,000 USDT loses 2.997001 USDT; a small planted gross advantage can be erased by
the three fees. This is an accounting benchmark, not a measured opportunity.

## Material interpretation finding and correction

The initial `conditional_upper_bound` label could overstate the full-capital cash
result as a bound on all feasible wallet outcomes. Under parity and 10 bp fees,
the forced 1,000-USDT cycle loses 2.997001 USDT, whereas routing only 500 USDT
and retaining the rest loses 1.4985005 USDT; abstention loses zero. Thus the forced
continuous full-capital value is not a universal upper bound once partial sizing,
rounding, residual cash or abstention is allowed.

The coordinator corrected the unfrozen source to
`conditional_full_notional_proxy` and added explicit full-notional and per-unit
scope fields (`:96`, `:117-118`). Arithmetic did not change. This resolves the
wallet-wealth interpretation. The final wording must describe the profit threshold
as a **roundtrip factor greater than one**, not merely a positive factor: every
admitted factor is positive. The implemented numerical test `cash_profit > 0`
at `:108` already uses the correct threshold. A factor at or below one rules out
positive cycle profit only within the frozen synchronous-price/assumed-fee model.

## Valid necessary claim and unavailable execution claims

Best-quote per-unit conversion is optimistic for fixed synchronous quotes and
the specified received-asset fee assumptions. Ignoring worse deeper prices and
lot restrictions does not establish fills. The calculation may remain defined
when displayed best size is insufficient; those flags are correctly preserved,
and they prevent a size-supported execution claim. Buy-side size is measured in
gross acquired base units before fee; sell-side size uses spent base units.

Actual source requests are asynchronous. Combining their prices does not prove
that this triangle existed at one instant, that it can be crossed sequentially,
or that its factor bounds later prices. A nonpositive **cycle profit** closes
only this measured static proxy. A positive one is at most a reason to investigate
timed executable observations; it does not pass feasibility. The 10 bp scenario
cannot rule out profitability under a different lower account fee, and the zero-
fee scenario cannot establish applicability of the fee-paying model.

The code retains all eight correlated cells on global or case-level input failure;
missing, nonfinite, zero and crossed inputs are unavailable. Signed wallet flows
are explicit. The log-factor shadow is labeled invalid as arithmetic PnL and is
not booked. Full BTC/ETH temporary exposure between idealized legs is disclosed.
No snapshot justifies expected-return confidence, power, beta intervals, annual
returns, repeated opportunity frequency, atomicity or candidate graduation.

## Still pending or untested

The pure evaluator does not validate actual source timestamps or decode registered
raw receipts; those belong to the forthcoming runner/source review. The final
charter and gate must pin the source, exact observed inputs, eight cases, complete
failure denominator and these conditional interpretations before outcomes.
Actual commissions/fee assets, lots/dust, depth depletion, market-order notional
rules, account access, fill latency and exposure under failed legs remain unknown.
No additional higher-effort accounting review is warranted for the verified pure
calculation; independent post-result reconstruction is still required later.

## Final pure-source disposition

The threshold wording is now corrected to factor greater than one / at or below
one at lines 109 and 118. Final pure-source review **PASS**, with no unresolved
accounting or interpretation blocker in the reviewed scope; final empirical
charter/runner/gate admission remains pending. All ten focused synthetic tests
pass on final source SHA256
`ff52dd58d2a60aa939997b64dde3ce77bc57857052257fc52820327501f9415a`.
Test file SHA256 is
`1fea27e6751adcdcc490efd923d4e0a2085b81b2a93c5e2b044b592a3d5f66ae`.
