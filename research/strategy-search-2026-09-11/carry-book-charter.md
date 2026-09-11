# Fixed quantity funding-carry development book

Experiment `carry-book-20260911`, child of `carry-inputs-20260911`; third and
last new investigation in the family's current incremental allowance. Existing
BTC/ETH funding-carry ancestry and all spent samples remain. Financial results
belong only to this new lifecycle's sharded ledger; original ledgers/gates are
immutable. The changed question is a literal cash/quantity book, not removal of
a failed criterion or a newly discovered mechanism.

## Hypothesis and fixed cases

Can actual recorded funding transfers cover specified trading costs and produce
economically relevant full-capital cash profit in the fixed historical quarter,
without meaningful crypto-price exposure or a visible reserve deficit? The
competing explanations are thin/negative funding, entry/exit basis, fees,
capital immobilization, residual price exposure or inadequate reserve.

Use only the once-captured and independently reviewed BTC/ETH inputs for
[2026-04-01T00:00:00Z,2026-07-01T00:00:00Z). This is 91 days of already spent
development. Newly downloaded fields do not create untouched confirmation.
Eight cases: BTC/ETH × capital1,000/10,000 USDT × base/stress costs. No assets,
dates, thresholds, allocations, forecasts or parameters are selected afterward.
Each asset is an alternative use of total capital, not a simultaneous sleeve.

Base costs per execution: spot taker0.001, futures taker0.0005 and adverse
slippage0.0002 on each price. Stress doubles all three. They are provisional
scenario assumptions, not authenticated commission/fill schedules. Assume fees
in quote USDT, already on venue, no borrowing, no transfers and no expiry of
these conventional linear perpetual positions. Actual missing economic legs
are unverified and bar any executable/adoption claim; they are not asserted zero.
Lot steps BTC0.001 and ETH0.01 are conditional common base-quantity assumptions,
not historical exchange-rule recovery. Minimum notionals and fee-asset deductions
require separate actual applicability before any advancement.

## Cash and event chronology

Entry uses the first day's spot/perpetual open with adverse slippage: spot buy
ask and short future bid. Quantity is the largest common-step amount satisfying
`q * (spot_ask*(1+spot_fee) + future_bid*future_fee) <= 0.40*C`.
Post0.50*C in the futures wallet and retain at least0.10*C idle after entry.
There is no compounding allocation, leverage optimizer, rebalance or equity-drift
proxy. Hold matched signed quantities throughout; short sale notional is not
spendable cash. A zero/below-lot quantity is unavailable, not silently omitted.

Exclude the first funding timestamp through start+5seconds because ownership
before the entry-boundary event is not established. Include every subsequent
captured event before the interval end with cash `+q*event_mark*rate` for the
short. Negative rates are actual modeled cash payments. Match funding events
by their timestamps; missing events/marks remain unavailable. The3/day capture
schedule is an explicit conditional assumption; historical expected-calendar
proof is absent. No interpolation, successor ticker or zero-filled event.

Daily wealth is idle cash + futures collateral wallet + short unrealized PnL
`q*(entry_future-mark_close)` + marked spot principal `q*spot_close`. Preserve
funding cash, quantities and each wallet. Exit at last spot/perpetual close with
adverse slippage and fees. Sell the spot principal, cover the short, release
collateral, reconcile terminal cash exactly. Daily mark closes are valuation
proxies; trade OHLC with slippage is a conditional execution model, not fills.

Daily conservative reserve diagnostic uses the previous funding balance plus
only that day's negative funding payments, subtracts short loss at the mark
high and a provisional1% of marked short notional maintenance buffer. A negative
value is a modeled deficit. A positive value is not exchange maintenance-margin
or intraday liquidation proof. Report fixed-quantity down50%/up100% proportional
spot/perp stresses with zero future funding explicitly as invented sensitivities.
Net base delta is zero; market-value net/gross notionals and stress wallets remain
visible. Stablecoin depeg/counterparty failure are unmodeled risk, not zero risk.

## Metrics, uncertainty, forensics and gates

Report net cash profit and full-capital profit/C,91-day simple annualization
365/91 as descriptive only, entry/exit/funding/basis decomposition, cash balances,
drawdown including initial capital, exposure, reserve and stress diagnostics.
Illustrative cash benchmarks0%,3%,5% apply to all C over91/365 and stay separate
from cash profit. A zero-funding counterfactual uses the identical prices,
quantities/costs and zero signed rates solely to isolate funding contribution.
It is not missing-data substitution. All eight cases and counterfactuals remain.

For daily fixed-initial-capital cash changes, report a circular moving-block
bootstrap (block7days,2,000 paired resamples,seed20260911). Use common resample
indices across all cases to retain cross-case dependence. Exploratory95%
simultaneous Bonferroni intervals across eight annualized means use quantiles
0.003125 and0.996875. Finite bootstrap tails and only13approximate blocks limit
precision. Endpoint fees and basis changes are resampled as daily observations;
the resulting interval is sensitivity of this empirical daily-mean model, not
a coherent repeated 91-day trade path or a confidence interval for future annual
profit. These intervals are development diagnostics, not confirmatory
probabilities; result-informed ancestry/unknown historical multiplicity remain.
Report standard error and approximate80% detectable annualized mean relative
to zero under a normal/block-bootstrap approximation; insufficient power is
unresolved evidence, not proof of no effect. No repeated looks or new seed search.

Regress daily valid simple NAV returns on contemporaneous BTC/ETH simple spot
returns including an intercept; first day references its spot open and initial
C. Fixed OLS HAC lag7, with97.5% individual intervals for two betas (Bonferroni
95% within each book). Across cost/capital books this is descriptive and does
not grant strategy validation. Singular benchmarks/insufficient observations
produce unavailable beta, never zero. Preserve coefficients, intervals and n.

Necessary conditional development screens: annualized cash point estimate at
least3% of full C; simultaneous cash-mean interval lower bound above0; both BTC
and ETH beta points within±0.10 with intervals within±0.20; drawdown<=10%; no
modeled reserve deficit; matched base delta<=1% NAV; stated doubling stress
wallet check nonnegative. Separate scenario screens, never a universal Sharpe
floor. No candidate earns advancement unless base and stress cases at its own
capital pass and remaining source/execution/account/risk evidence is admitted.
No ranking/selecting a best BTC/ETH variant from these results. An economic
failure is specific to this fixed book and historical quarter.

Independent accounting review reconstructs initial quantities, all funding,
terminal proceeds/fees, daily wallets/wealth and metrics from raw evidence
without importing the book. Synthetic tests cover planted positive/negative
funding, hedge cancellation, principal release, fee/lot reserve constraints,
missing events, price stresses and the old false-drift counterexample. Required
convention shadow is sum(log1p(daily valid NAV returns)) against their arithmetic
sum and terminal cash wealth, explicitly invalid as arithmetic PnL; only literal
cash/quantity wealth governs. No forecasting leakage channel is claimed: fixed
entry and holdings depend only on specified contemporaneous entry proxies.

Resource bound: one run, eight primary plus eight declared zero-funding
counterfactual books,2,000 common bootstrap draws, two CPU threads,512MiB,
120seconds; no network, fitting a predictive model, retuning or history extension.

## Decision and continuation

Positive conditional development evidence warrants resolving named actual
execution/account/calendar/risk gaps before a separately reviewed prospective
design. It does not authorize a new historical variant after budget exhaustion.
Insufficient economics/power or missing evidence receives its own disposition;
do not transform a near-pass into more parameter searches. Continue the ranked
dated/calendar/options or other independent mechanism investigation while this
family is deferred or its incremental allowance is exhausted. Full feasible-map
exhaustion still requires independent coverage review; this experiment cannot
establish that all funding carry opportunities fail.
