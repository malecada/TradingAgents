# Independent completed dated-book review

**PASS for reconstruction; all eight conditional cash cases lose money.** The
fixed May 1–June 25, 2026 episode fails the frozen positive-cash and 3% descriptive
annualized relevance screen at both capital levels under base and stress costs.
This does not reject the entire dated-basis family or estimate expected returns.

## Cash result and cause

Values are USDT on the entire stated capital, using the registered assumed fees,
lots and adverse price slippage. No actual executed portfolio is claimed.

| Asset | Capital | Costs | Same-quantity frictionless gain | Slippage | Commissions | Net cash profit | Full-capital return |
|---|---:|---|---:|---:|---:|---:|---:|
| BTC | 1,000 | base | 0.490600 | 0.272401 | 1.021363 | -0.803164 | -0.080316% |
| BTC | 1,000 | stress | 0.490600 | 0.544803 | 2.042742 | -2.096945 | -0.209694% |
| BTC | 10,000 | base | 5.102240 | 2.832973 | 10.622174 | -8.352907 | -0.083529% |
| BTC | 10,000 | stress | 5.102240 | 5.665947 | 21.244519 | -21.808226 | -0.218082% |
| ETH | 1,000 | base | 0.336600 | 0.260222 | 0.975722 | -0.899345 | -0.089934% |
| ETH | 1,000 | stress | 0.336600 | 0.520445 | 1.951468 | -2.135313 | -0.213531% |
| ETH | 10,000 | base | 3.484800 | 2.694067 | 10.101597 | -9.310864 | -0.093109% |
| ETH | 10,000 | stress | 3.484800 | 5.388134 | 20.203436 | -22.106771 | -0.221068% |

Some basis convergence occurred, but round-trip costs exceeded it. At 1,000 USDT,
the same-quantity gross gain was only 0.34–0.49 USDT versus approximately
0.98–1.02 USDT of base commissions before slippage. Even the same-quantity
frictionless gain was below the 56-day 3% cash benchmark of 4.60274 USDT per 1,000
capital. Gross convergence was therefore too small for the stated relevance
screen as well as insufficient to pay the modeled trading costs. No funding cash
is part of this conditional dated contract. Profit equals signed spot price PnL
plus signed short-future price PnL minus all four commissions. Log-return sums
remain forensic diagnostics and are not booked as cash.

## Independent reconstruction

`check_dated_book_amended.py` independently decoded the raw archived ZIPs and
checksums and spot response bodies from the four registered input envelopes.
It verified their hashes, URL identities, full source clocks and OHLC, paired
archive integrity and clipping. Each asset retained 56 daily spot bars and 1,344
hourly dated bars; 30 earlier/five later spot days and nine later dated hours were
excluded. No retained dated hour had zero reported volume or trades; entry and
exit activity were positive in both legs. Activity is not proof of executable
quotes or fills.

The checker uses 60-digit Decimal arithmetic and independently reconstructs
quantities, signed entry positions, spot principal, fees, collateral and idle
cash; all 448 daily wallet/NAV rows; pre-exit and post-exit balances; terminal
cash; price/fee/slippage decomposition; drawdowns; same-quantity frictionless
profit; all 16 half/double price scenarios; and arithmetic/log convention
diagnostics. It imports no financial engine, runner or registered statistics
module. **9,352 numerical comparisons passed**, with maximum absolute difference
`7.275957614183426e-12`, below the 1e-8 cash tolerance. The independently
reconstructed statistical coefficients and intervals pass the tighter 1e-10
tolerance. The review JSON contains full per-case details.

Exposure was reconstructed from the same 56 close-to-close full-capital simple
NAV returns, with the first day measured from initial capital. BTC and ETH
benchmark first returns use the opening price; later returns use prior closes.
Joint OLS normal equations, Bartlett HAC with seven lags, no small-sample covariance
multiplier, and Student t with 53 residual degrees of freedom reproduce the
97.5% individual coefficient intervals. All eight BTC/ETH intervals contain zero;
all endpoints lie between approximately -0.01459 and +0.00925. These describe
trade-close proxy exposure in this spent episode. The within-book Bonferroni
construction does not cover the entire search or establish stable future beta.

Daily trade-high reserve proxies remain positive, and retained NAV maximum
drawdowns are approximately 0.111%–0.221%. **Trade highs are not conservative
mark-price bounds.** These observations do not establish actual maintenance
margin, liquidation-path survival or executable risk. Expected-profit confidence
and power correctly remain unavailable: one convergence episode per asset does
not provide repeated independent trades, and 56 daily marks do not repair that
limitation. No graduation or adoption flag is true.

## Receipt, resource and amendment preservation

Source commit `d75b6d15b3e08c10616fe25fbca4c01cf46b29ba` predates the claim and is
bound to gate SHA-256
`cc5e0458ccf4c51a545e9f9c1ac59f94e2241134bd77573129c4917dce1b66ae`.
All 12 runtime hashes match both committed and present source bytes. The separate
successor structural verifier independently accepts the amendment certificate,
complete prior inventory, original terminal receipts and the new completion.
The new run retains eight complete cells, zero unavailable cells and three
hash-verified outputs. Claim/completion identity, timestamps and denominator
reconcile. Verification does not itself prove pre-execution remote push timing.

The certificate's only increment is now consumed. Original base budget 4,
historical count 1 and three prior claims remain recorded; the effective total
budget is 5. Decisions 05/06 and both failed financial attempts remain unchanged.
The first failed attempt computed books in memory before its import failure;
the second failed before financial evaluation. Neither was removed or relabeled
as an unspent attempt.

The resource report records exit zero, no limit reason, 15.28857 seconds and
425,881,600 bytes peak sampled aggregate RSS under the 512 MiB/120-second guard.
The child reports 207,560 KiB self peak RSS. The sampled guard, process-exit retry
and largest-child versus aggregate-RSS qualifications remain binding; virtual
address space was unlimited. No new financial experiment or network request was
performed for this review.

## Decision and next justified step

Retain this episode as a cost-dominated negative development result, with positive
but economically small gross convergence. Do not tune the date, fee tier, quantity
or episode to reverse its sign, and do not create another automatic dated
amendment. Preserve zero validated strategies and the earlier holdout NO-GO.
The justified next work is the separately admitted linked-value/WBETH question
under its own fixed engineering and financial preregistration, including the
distinction between market-value matching and true underlying ETH exposure.

Historical/current account fees, fee assets, common lots, eligibility,
simultaneous fills, actual marks, maintenance tiers, liquidation, expiry
settlement, external backup timing and future expected profitability were not
validated. The cash reconstruction establishes correctness of the registered
conditional arithmetic and diagnosis for the captured episode only.
