# Fixed dated/perpetual spread: information-value design review

September11, 2026. **One explicitly registered seventh dated-family attempt is
worth preparing**, conditional on the pending independent dated-mark source
review. This is a source/charter review, not an executed book, adopted gate or
accounting approval. No price body, new market request, cashflow calculation or
financial output was inspected or produced. Only this report is edited.

## Why this attempt is informative

The fixed hypothesis is that long dated/short perpetual relative-price change
plus actual short-perpetual funding covers both derivative legs' transaction
costs on independently funded wallets. It differs from buying spot and selling
one future: spot principal is absent, a second margined derivative is present,
and the payoff contains the dated-minus-perpetual spread. Equal quantities and
an unchanged40% notional ceiling prevent a leverage rescue. It is not an
independent new source of alpha: at identical quantity and timestamps the gross
cash is spot/perpetual carry minus spot/dated carry. Existing results at different
periods/quantities cannot answer that identity by subtracting reported totals.

The [dated charter](../dated-book-charter.md) fixed May1 open through June25
close, BTCUSDT_260626/ETHUSDT_260626, and assumed common lots BTC0.001/ETH0.01.
The [carry charter](../carry-book-charter.md) uses the same common lots, futures
fee0.0005 and per-side adverse slippage0.0002; stress doubles those costs. Both
describe conditional lots rather than recovered historical exchange rules.
Reuse them literally. A future source/rule admission is required before actual
execution claims; do not substitute metadata precision for a lot increment.

The prior source-only sixth attempt reportedly retains two sources and112daily
mark slots, with13,666raw bytes and four outputs. Those are coordinator-reported
denominators pending independent review, not this report's reconstruction.
The newly acquired marks improve two-leg daily valuation and reserve diagnostics.
They do not create an untouched sample or prove actual margin survival. The
terminal-cash question was possible with existing trade bars; this source adds
a specifically missing risk-description input rather than a new return signal.

This attempt can distinguish insufficient spread/funding receipts from costs,
capital immobilization and adverse separate-wallet paths. Those diagnoses are
not obtained from another option component screen. A positive result remains
one exposed episode per asset, unable to establish expected profitability. A
negative result closes this fixed financing configuration without authorizing a
direction flip, later expiry, allocation change or asset/date search.

## Frozen book proposal

Eight primary cases: BTC/ETH ×1,000/10,000USDT ×base/stress transaction costs.
Each asset is an alternative use of all capital C, never a combined book with
double-counted capital. Exactly [2026-05-01T00:00:00Z,
2026-06-26T00:00:00Z),56days. No settlement, terminal June26 bar, borrowing,
portfolio margin, collateral transfer, reinvestment or rebalance. Long dated,
short perpetual only, with fixed equal base quantity q throughout.

Before calculating outcomes, revalidate the exact original receipt hashes,
archive checksums/members, normalized admission and contract identities. Require
the1344dated trade hours,56perpetual trade days,56mark days on each derivative
and complete matching funding-event identities. Retain exclusions and missing
slots; no interpolation, continuous contracts or zero-filled funding. Current
metadata and request clocks retain their own vintage separately from historical
bar/event times. Mark ignored fields are not trade volume. Entry/exit dated
trade bars must have the already required positive activity.

Let D_a be adversely shifted dated entry ask and P_b the adversely shifted
perpetual entry bid. A concrete conservative sizing rule for review is the
largest common-step q such that

```text
q * [max(D_a,P_b) + f*D_a + f*P_b] <= 0.40*C.
```

This ensures both entry notionals individually stay below40%C and reserves
room for both entry fees without optimizing leverage. It is proposed before
outcomes; the coordinator must freeze this exact rule or an explicitly reviewed
alternative. Quantity may differ across cost scenarios under the rule, but all
counterfactuals below retain their corresponding primary q. A below-lot quantity
is unavailable. Assume fees in USDT; don't infer actual fee applicability.

Allocate0.40C to the dated wallet,0.50C to the perpetual wallet and0.10C idle.
Deduct each leg's entry fee from its own wallet. No spot purchase occurs and no
future notional is credited as cash. Dated wallet valuation is its remaining
reserve plus q*(dated mark minus dated entry fill). Perpetual wallet valuation
is its reserve plus cumulative signed funding plus q*(perpetual entry fill
minus perpetual mark). Total wealth adds both wallets and idle cash exactly.
The40% allocation is a dated reserve, not the prior spot-principal debit.

Follow the carry event convention: exclude funding through start+5seconds since
pre-entry ownership is unestablished; include all subsequent captured events
strictly before end, with signed cash +q*event_mark*rate to the short wallet.
Negative funding remains a payment. Do not double funding rates in the cost
stress. The captured three-events/day calendar is conditional, not new proof of
historical exception-free timing.

Use dated first-hour open/perpetual first-day open for entry; dated last-hour
close/perpetual last-day close for exit, both adversely shifted in the proper
direction. Mark bars value positions, never supply fills. At exit book dated
signed price PnL, perpetual signed price PnL, all funding and all four execution
fees; release both collateral balances with no fictitious principal repayment.
Terminal holdings are zero. Preserve the last pre-exit mark valuation separately
from final cash NAV so entry/exit costs are included exactly once.

## Complete metrics, diagnosis and fixed counterfactuals

Report each primary case's q, all notionals/cash legs, entry and exit fees,
wallet funding totals, separate wallet balances, idle capital, final cash,
profit/C and simple365/56 annualization. Cash benchmarks0/3/5% apply to all C
over56/365 separately; none is subtracted to relabel positive cash as a loss.
Reconcile terminal cash to C plus both signed price PnLs plus funding minus
fees, absolute tolerance1e-8USDT. Report daily marked wealth and increments,
simple NAV returns, drawdown from a series including initial C, signed base
quantities, market-value net/gross notionals, and pre-exit versus final exposure.

Decompose at the primary q: raw two-leg price change, signed funding, slippage
loss and commissions. Retain two deterministic scalar counterfactuals per case:
(1) identical fills/fees/q with funding set to zero, and (2) raw trade-price
cash plus actual funding with execution costs removed, again at unchanged q.
These isolate funding and the maximum removable modeled transaction drag;
neither changes capital sizing or imputes missing funding. They are declared
diagnostic scalars inside all eight cases, not hidden extra candidate books.
If full daily counterfactual books are desired, explicitly add their separate
denominators before registration instead of silently expanding this proposal.

Include the required convention forensic: sum of valid log1p daily NAV returns
as an explicitly invalid arithmetic-PnL shadow, sum of daily simple returns,
and actual terminal cash return. Do not equate either sum to compounded cash.
Nonpositive NAV makes returns/log diagnostics unavailable while signed wallet
cash remains reportable; failed cases must not vanish from the denominator.

## Reserve and scenario risks

Describe each wallet independently, without offsetting a deficit in one using
the other's gain. Reuse the provisional1% marked-notional maintenance buffer
from carry, clearly labeled as an assumption. For each day, stress the long
dated wallet at its mark low and the short perpetual wallet at its mark high.
For the short wallet, use previous cumulative funding plus only current-day
negative events, following the prior conservative credit-order convention.
Subtract both entry fees and preserve cumulative prior funding. Display each
wallet's minimum diagnostic value and deficit flag. The two daily extrema need
not be simultaneous; their sum is an adverse sensitivity, not an observed NAV
or proof of the actual liquidation path. A positive buffer cannot verify real
maintenance tiers, intraday marks, transfers, ADL or account permissions.

Freeze a small synthetic stress lattice, inherited from the earlier half/double
and0/10/50bp basis scenarios: common underlying reference equal to entry spot
reference times{0.5,1,2}, adverse relative basis widening{0,10,50}bp. At each
invented terminal state, dated mark is common reference*(1-b/20000) and
perpetual mark is common reference*(1+b/20000), so widening is adverse to the
fixed orientation. Keep original q and entry fills and set future funding to
zero. Report pre-exit wallets less the same1% maintenance buffer separately
from hypothetical closed cash after the case's adverse exit prices/fees.
Maintenance is not a cash fee and is not deducted again after closing. Report
both wallets and total wealth, with all9states per primary case (72
subordinate scenarios) retained. This is not a claimed settlement price or
calibrated tail distribution. The doubled-cost primary cases are the liquidity
cost sensitivity; they do not represent actual depth or gap-fill costs. No
new stress threshold is selected after outcomes.

Stablecoin depeg, venue/counterparty failure, mark manipulation, omitted fees
and unobserved true liquidation remain named unmodeled risks. Constant signed
base quantities cancel nominal underlying delta under the linear model; they
do not establish empirical low beta or safety of separate wallets.

## Uncertainty and decision rules

There is one56-day episode per asset, not56independent convergence trades or
112independent returns across correlated assets. Cash-profit expected-return
confidence bounds, power and fresh confirmation are unavailable. Do not
bootstrap endpoint cash into an expected-profit interval or copy the earlier
91-day carry daily-mean bootstrap as if it described repeated dated spreads.
Expected-return uncertainty must remain explicitly unresolved even if this
episode meets point relevance. This follows the dated-book uncertainty scope.

For descriptive exposure only, jointly regress56valid daily simple NAV returns
on contemporaneous BTC/ETH simple spot returns with intercept, OLS HAC lag7.
First-day benchmarks reference their corresponding spot opens and NAV initialC.
Report both coefficients, standard errors,97.5% individual intervals giving
Bonferroni95% coverage for the two coefficients within each book, n and covariance.
Across eight books these are exploratory comparisons, not family-wide95%
confirmation or an opportunity to select a winner. Invalid NAV, singular design
or inadequate inputs make the corresponding estimate unavailable, not zero.

Necessary episode relevance: cash positive and simple annualized profit/C at
least3% for both base and stress at the given asset/capital. Preserve separate
point-beta bounds±0.10, within-book interval containment±0.20, drawdown<=10%,
modeled base-delta<=1%NAV and no modeled reserve/stress-wallet deficit. These
are individual conditional diagnostics, not automatic advancement. Missing
actual margin/execution/rule evidence and missing expected-profit confidence
prevent graduation even if every numerical diagnostic passes. No combined
claim that pooled cases are an independent successful strategy.

Failure diagnosis must identify price spread, funding, friction, reserve risk,
relevance and uncertainty separately. For example, frictionless failure rules
out rescuing the same q/path merely by reducing modeled fees; it does not rule
out all future relative-basis opportunities. A positive fixed episode warrants
adjudicating precise account/mark/path/future-data prerequisites, not retuning
q, directions, dates, reserve splits or fees. Record all eight decisions.

## Bounded implementation and extension conditions

One foreground offline run, two CPU,512MiB,120seconds, no network. Proposed
output bound8MiB, including source references, eight full daily books and72
stress subcases; exact file denominator must be frozen in the new gate. Require
synthetic planted funding and spread profits/losses, zero shared-price delta,
separate-wallet deficits despite positive total wealth, cost and lot boundaries,
entry funding exclusion, negative funding, mark/trade distinction, missing rows,
nonpositive NAV and exact collateral release. A guarded full-lifecycle fixture
must verify actual encoded size and retention. Independent financial review
must reconstruct quantities, cash/wallets, scenarios and beta inputs from raw
sources without importing the financial engine.

Record six consumed dated attempts and explicitly add this seventh; preserve
carry ancestry, old resource failures, prior extensions, known-incomplete
configuration multiplicity and all exposed samples. The source-six helper and
its certificate are hardcoded and remain frozen. Admission requires a separately
reviewed additive seventh-attempt route, concrete pre-outcome information-value
approval and exact hash-pinned charter/gate/source, including the independently
admitted new marks. It cannot chain or reuse the sixth certificate implicitly.
This review supports preparing that bounded proposal, not changing any gate.
