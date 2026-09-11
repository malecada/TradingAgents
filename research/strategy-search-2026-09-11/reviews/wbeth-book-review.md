# Independent completed WBETH book review

**PASS for reconstruction. All four primary cases produce positive conditional
cash, but none meets the frozen 3% full-capital relevance screen.** All four
same-quantity zero-funding counterfactuals are also positive. This remains one
spent 91-day episode, with no expected-profit confidence, power, validated true
ETH delta or strategy graduation.

## Reconstructed results

Values are USDT on the full stated capital, after the registered assumed fees
and adverse slippage. Annualization is a descriptive scaling of this episode,
not a forecast or assumption that it repeats.

| Capital | Costs | Primary cash profit | Paired zero-funding profit | Funding contribution | Primary full-capital return | Descriptive annualized return |
|---|---|---:|---:|---:|---:|---:|
| 1,000 | base | 2.02025468 | 1.23054780 | 0.78970689 | 0.202025% | 0.810322% |
| 1,000 | stress | 0.86674884 | 0.07704195 | 0.78970689 | 0.086675% | 0.347652% |
| 10,000 | base | 23.01003374 | 15.08789481 | 7.92213893 | 0.230100% | 0.922930% |
| 10,000 | stress | 9.80235778 | 1.89275388 | 7.90960390 | 0.098024% | 0.393171% |

The eight cases retain their original denominator. The two capital sizes, cost
scenarios and paired counterfactuals are correlated diagnostics, not eight
independent discoveries. Quantities vary mechanically with the registered
capital/cost formula and lot floors; only each primary/zero-funding pair holds
exactly identical quantities and costs. Results therefore need not scale exactly
tenfold or have identical gross price PnL across base and stress costs.

At 1,000 base, same-quantity frictionless price PnL is 2.557006, signed funding
is +0.78970689, slippage costs 0.27897099 and commissions cost 1.04748722. Their
signed sum is +2.02025468. The separate 3%/91-day cash benchmark is 7.47945205.
Even the fixed same-quantity frictionless price-plus-funding scalar is only
3.34671289; at 10,000 base it is 36.29344993 versus a 74.79452055 benchmark.
The observed opportunity is too small for the relevance threshold at these
quantities even before modeled costs. No alternate allocation, fee tier or date
was evaluated to reverse that result.

The WBETH long loses price value while the ETH perpetual short gains; their
relative result plus funding exceeds modeled costs in this episode. Removing
funding leaves only the paired cashflow counterfactual. It cannot identify pure
validator yield because WBETH market prices also contain basis, demand and
depeg effects. No redemption or contractual conversion cashflow was modeled.

## Independent arithmetic and source checks

`check_wbeth_book.py` uses 60-digit Decimal arithmetic and no financial engine,
runner or registered statistics import. It reconstructs WBETH and ETH quantities
separately, 40% joint entry spend, all fees, 50% collateral, idle cash, actual
event funding and its sign, pre-exit and flattened terminal wallets, signed
price PnL, full-capital cash returns, costs, log-return forensic and drawdown.
It checks all **728 daily NAV rows** and **32 fixed price-stress scenarios**.
All paired primary-minus-zero differences equal the removed funding cash.

**19,428 numerical comparisons passed**, with maximum absolute discrepancy
`5.051958851254312e-12`, below the 1e-8 cash threshold. Independently reconstructed
exposure coefficients/intervals pass the tighter 1e-10 tolerance. The JSON review
retains the complete per-case decomposition and exposure values.

All four input-envelope hashes match the claim. All 12 source receipts match
their separately retained receipt files, request identities, body sizes and raw
hashes; 1,286,031 raw bytes were checked. Strict decoding rejects duplicate JSON
fields and nonfinite JSON tokens. The two WBETH and ten carry source denominators
remain complete. The seven daily series retain exact 91-row UTC calendars and
valid OHLC/activity. Both 273-event funding series retain complete conditional
slots, finite signed rates/positive event marks, and event marks consistent with
their daily mark ranges. ETH's opening event is excluded and 272 subsequent
events are owned by each cash book. No missing funding was replaced with zero.

Current WBETH metadata matches its literal normalized row. The reported current
BTC/ETH perpetual metadata, normalized observation counts and server-clock
interval also reconstruct. All funding/price sources were retrieved before the
financial claim, but after the historical quarter. This verifies saved-source
consistency, not original publication time, historical trading-rule applicability
or fresh evidence. Positive reported activity and bar prices are not fills.

## Exposure, uncertainty and tail risk

The checker independently fits joint BTC/ETH least squares and constructs the
Bartlett HAC7 covariance sandwich with Student t at 88 residual degrees of
freedom. First benchmark returns use the first spot open; first portfolio return
uses initial capital. The 97.5% individual intervals provide the declared
within-book Bonferroni description, not across-search confirmation.

All primary point betas and intervals satisfy the frozen descriptive bounds;
all primary and counterfactual intervals include zero. Primary maximum observed
drawdown ranges approximately 0.210%–0.256%. These are historical mark/trade-price
descriptions. True WBETH-to-ETH delta remains unavailable in every case, as does
the realized net-base-delta ≤1% NAV gate. A market-value hedge and narrow measured
betas cannot establish that contractual or economic sensitivity.

The daily mark-high/negative-funding margin scenario shows no breach under the
registered assumptions; actual maintenance, liquidation and execution remain
unverified. Isolated WBETH −10% scenarios lose approximately 4.14%–4.28% of full
capital, while −50% scenarios lose approximately 20.08%–20.19%. Those fixed
illustrations expose linked-asset/depeg sensitivity despite small measured beta;
they are not universal loss bounds or assigned probabilities. Counterparty,
redemption and stablecoin risks remain outside the historical cash result.

Expected-profit confidence and power correctly remain unavailable: 91 marks of
one holding episode are not 91 independent repeat-trade outcomes. No graduation
flag is true. Positive historical cash does not establish durable positive
expected returns, pure staking attribution or investability.

## Lifecycle, preservation and decision scope

The original structural verifier passes eight complete cells, zero unavailable
cells and two immutable outputs totaling 931,662 bytes, below 20 MiB. Output
hashes, claim hash, timestamps and denominator reconcile. Source commit
`04e1fa48336bdb10e6a9795a91e24a72526c9ef7` predates the claim and is bound to gate
`9e92592a79b88716a15e7d5bba2a1b0e3c3b0891fdc415ee245c3136142c2afa`.
All original runtime hashes match committed and present source bytes. The guard
records exit zero, no limit reason, 9.33857 seconds and 436,752,384 bytes peak
sampled aggregate RSS under 512 MiB/120 seconds. Nominal sampling, process-exit
retry and individual-child versus aggregate-RSS qualifications remain explicit.
Receipt verification does not itself prove pre-result remote push timing.

Decision 14's provisional numerical table and diagnosis agree with this
independent reconstruction. Its distinction between positive cash and failed
relevance is warranted. Close this fixed episode's relevance claim while
preserving the positive result, all counterfactuals and their limits; do not
refit the hedge, increase allocation or select another sample to obtain a pass.
The separately bounded metadata-only news availability investigation is a
reasonable distinct next question once its own privacy/source review and gate
are complete. It is not an additional WBETH optimization or alpha result.

No new financial experiment, network request or implementation change was made
by this review. Actual fills, historical fee assets/lots/account eligibility,
staking attribution, contractual ETH delta, margin/liquidation, redemption,
future expected return and external backup timing were not validated. Zero
strategies validated and the earlier holdout NO-GO remain unchanged.
