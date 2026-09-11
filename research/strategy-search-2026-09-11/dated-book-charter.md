# Dated cash-and-carry historical episode

Experiment `dated-book-20260911`, child of `dated-archive-20260911`. Second new
investigation in the dated-basis allowance; the prior September10 measurement
and first archive admission remain. Eight fixed primary cases: BTC/ETH ×
1,000/10,000 USDT capital × base/stress costs. No selected champion, parameter
grid expansion, current quote refresh or fresh confirmation.

## Question and admissible claim

Does fixed matched-quantity cash-and-carry earn positive, economically relevant
modeled cash in the completely observed pre-expiry interval of this dated
contract? Compared with perpetual funding carry, the mechanism here is price
basis convergence with no perpetual funding receipt. Competing explanations
are adverse/nonconvergent basis, fees/slippage, capital immobilization, exposure
and insufficient executable data. A fixed positive episode would not establish
expected profitability; a negative episode would not reject all future bases.

The parent archive review establishes 1,344 consecutive positive-volume/trade
hours per asset over [2026-05-01T00:00:00Z,2026-06-26T00:00:00Z). Entry is the
May1 open; exit is the June25 close. This56-day rule uses the complete interval
before the June26 zero-trade terminal bar. Its date/lifetime selection is
result-informed by data admission, not by prices or returns. All history is
development/exposed; underlying spot history is already spent. Exact expiry
and settlement cashflows remain unknown and are not used for terminal wealth.

## Frozen inputs and cash book

Read only the parent raw archive capture/admission and the previously admitted
spot daily capture. Verify recorded raw SHA256, paired archive checksum and exact
member names; clip explicitly to the56-day interval, retaining exclusion counts.
Require56 complete spot days and1,344 complete dated hourly bars, with positive
volume/trades at entry and exit. Other zero-activity bars, if any, remain marked
in the retained denominator. No fill/interpolation/continuous-contract mapping.
Actual instrument IDs are BTCUSDT_260626 and ETHUSDT_260626, conventional USDT
linear dated futures under the conditional book. Contract incarnation is kept.

Reuse the reviewed quantity/wallet convention: spend at most40% of initial C
on spot principal and all entry fees, reserve50% in the futures wallet and
retain at least10% idle. Largest matched quantity in assumed common lots
BTC0.001/ETH0.01 is computed from the entry budget; short futures notional is
not cash received. Base spot/future fees0.001/0.0005 and adverse price slippage
0.0002 per side; stress doubles all. Fees in USDT are a conditional assumption.
No borrow, transfer or perpetual funding leg belongs to the hypothesized
long-spot/short-dated book. This does not establish all real fees or permissions.

Entry spot ask/future bid are adversely shifted first open prices. Exit spot
bid/future ask are adversely shifted last closes. Quantities stay fixed with no
rebalance, signal, optimization or capital reinvestment. Report every cash leg,
spot purchase/sale principal, short signed price PnL, entry/exit commissions,
idle cash and released collateral. Terminal cash must reconcile to the sum of
signed price PnL less fees, at absolute tolerance1e-8 USDT.

Daily dated valuation uses the last hourly trade close; daily trade high is
retained only as a reserve scenario proxy. It is NOT an actual mark or a
conservative bound on margin. Actual margin/liquidation risk is unavailable
throughout this run, regardless of proxy buffer. Price-basis/exposure calculations
must carry the same proxy qualification. End-of-day terminal quantities/exposure
are zero, with pre-exit fields separately retained. Public OHLC is not a fill.

## Metrics and decision rules

Report cash profit, profit/all initial capital, simple365/56 annualization as
descriptive only, drawdown including initialC, signed net/gross market notionals,
matched base delta, traded-high reserve scenario, and fixed half/double underlying
price stresses. Decompose raw basis convergence, slippage and commissions at
the SAME primary quantity. The frictionless scalar is a forensic counterfactual,
not a larger optimally financed portfolio. Cash benchmarks0/3/5% on all C for
56/365 are separate and are never deducted to report cash profit.

Necessary relevance screen: positive cash profit and at least3% annualized
full-capital point return under each capital's base AND stress cases. This is
a provisional research allocation threshold, not a changed carry gate or user
investment preference. Accounting checks must pass. Actual risk, execution and
adoption screens remain unavailable rather than automatically passing.

There is ONE historical convergence episode per asset, not56 independent
strategy trials. Expected-return confidence, power and fresh confirmation are
unavailable from this design. No bootstrap of endpoint PnL is presented as an
expected strategy-profit interval. This deliberately narrower deterministic
episode screen cannot graduate a candidate even when the relevance screen passes.
No repeated look, p-value selection or retrospective annual forecast.

For exposure description only, use joint OLS of daily valid simple NAV returns
on contemporaneous BTC/ETH simple spot returns with intercept, HAC lag7 and
97.5% individual beta intervals (within-book95% Bonferroni). First day references
the registered open and initial capital.56 observations, no fitting of a trading
signal. Nonpositive NAV, singular design or invalid data is unavailable. The
program's beta thresholds may be reported as descriptive comparisons but cannot
replace missing mark/margin/execution evidence.

Required convention forensic: log1p daily NAV returns summed as an explicitly
invalid arithmetic-PnL shadow, compared with daily arithmetic-return sum and
true terminal cash return. Only the cash book governs. Synthetic planted basis
profit, matched-price cancellation, principal release, costs, lots, missing
hours, zero-activity endpoints, negative NAV and price stress checks precede
commit. An independent reviewer reconstructs all eight primary books and scalar
counterfactuals from raw inputs without importing the runner/book/statistics.

One run, eight cells, one primary configuration per asset/capital/cost case,
two CPU threads,512MiB,120seconds, no network. Complete all attempted/unavailable
cases; unknown inputs do not disappear. Preserve source, inputs and outputs.

## Follow the result

If these fixed episode economics are inadequate, diagnose basis versus costs
and move to the next materially different eligible mechanism unless a specific
data defect justifies the remaining dated investigation. Do not tune fees/dates
or imply all dated/calendar opportunities are disproved. If conditional relevance
passes, actual mark/margin/fees/lot/access and independent future observations
remain dependencies for a separately registered next stage. Source work on
options, public triangles, relative-value or information families continues
while such dependencies are unresolved. Zero strategies validated by this run.
