# Independent reconstruction — conditional funding-carry book

Disposition: **the completed results reconcile; all eight primary cases fail
the frozen cash-return screens**. No material implementation discrepancy was
found. This is a negative result for the specified fixed-quantity book and spent
2026 second quarter, not a rejection of every funding-carry mechanism.

Source: `7d704ca97606eea4ab953c29d7587e7e8af517f1`.
The [standalone checker](check_book.py) reconstructs the completed frozen cases
from the original captured bodies. It does not import the book, runner or
statistics module, perform a new financial experiment, change any configuration,
or contact the network. The [machine-readable review](book-review.json) retains
the identities, decomposition and reconciled results.

## Independent evidence

- All sixteen distinct registered cells are complete: eight primary books and
  eight explicit zero-funding counterfactuals. Zero unavailable cells; both
  declared result files and all source/gate/input/receipt hashes reconcile. The
  official independent receipt verifier also passed.
- Independent 50-digit Decimal transaction accounting reconstructs the common
  lot quantity, spot purchase and principal release, entry/exit commission,
  adverse execution prices, futures collateral and idle wallets, signed event
  funding and terminal cash. All **1,456 daily NAV snapshots** agree, including
  final post-exit wallets and preserved pre-exit exposure.
- The opening funding event is excluded exactly once. Every book retains the
  other 272 funding events; the zero-funding intervention preserves event
  ownership and quantity/cost construction. The difference between each primary
  and zero-funding cash profit equals the primary's signed funding cash.
- Daily negative-funding/high-mark reserve bounds, fixed down-50%/up-100%
  sensitivities, daily and terminal exposures, drawdown from initial capital and
  all convention diagnostics reconcile. Cash, arithmetic daily returns and log
  shadows remain distinct.
- The common 2,000 seven-day resamples were constructed explicitly and all
  bootstrap summaries, quantiles and approximate detectable effects reconcile.
  OLS coefficients and HAC intervals were independently derived using normal
  equations and a lag-seven Bartlett covariance sandwich with the frozen
  Student-t critical value, without statsmodels estimation.
- All summary metrics, separate cash benchmarks and every necessary conditional
  screen reconcile. **35,072 numeric comparisons passed**, with maximum absolute
  difference **2.91e-11**. Numeric tolerances were 1e-8 for cash and general
  values, 1e-10 for HAC intervals, and 1e-12 for daily returns, with relative
  tolerance 1e-10.

## What explains the result

All amounts below are modeled USDT cash profit over the fixed 91-day quarter,
after the specified costs and with all initial capital in the denominator.

| Asset | Capital | Base costs | Doubled costs |
|---|---:|---:|---:|
| BTC | 1,000 | -0.475395 | -1.680828 |
| BTC | 10,000 | -5.514581 | -19.497610 |
| ETH | 1,000 | -0.579205 | -1.836730 |
| ETH | 10,000 | -6.081648 | -19.285666 |

The independent decomposition is:

`cash profit = signed funding + raw entry/exit basis price PnL - commissions - slippage`.

At capital 1,000 in the base scenario:

| Asset | Funding | Raw basis price PnL | Commissions | Slippage | Net cash profit |
|---|---:|---:|---:|---:|---:|
| BTC | +0.848929 | -0.118900 | -0.951668 | -0.253756 | -0.475395 |
| ETH | +0.752102 | -0.073800 | -0.992784 | -0.264722 | -0.579205 |

Funding was positive and recovered part of the zero-funding loss. It was thin
relative to turnover costs: even without modeled slippage, commissions exceeded
funding after the entry/exit basis effect. Increasing capital to 10,000 did not
repair this per-unit economics; the quantity-step rounding merely changed the
fraction deployed. These are small cash amounts, not economically relevant
positive returns hidden by an opportunity-cost deduction. No cash benchmark was
subtracted from the stated cash profits.

Every primary case fails exactly the 3% annualized full-capital point-estimate
screen and the positive exploratory simultaneous lower-bound screen. The other
six conditional screens pass: daily beta estimate/interval limits, drawdown,
daily modeled reserve, matched base delta, doubling stress wallet/buffer and
cash-component reconciliation. Their passing status does not establish actual
execution or exchange margin safety.

## Uncertainty and decision

The descriptive annualized points range from approximately -0.19% to -0.78%.
Each exploratory interval includes zero. Approximate 80%-detectable annualized
effects range from **2.00 to 3.91 percentage points** under the frozen empirical
daily-mean/block-normal approximation. With only 91 days and approximately 13
blocks, this cannot resolve a small future positive edge or establish universal
negative expected returns. The cash loss in the specified observed book is
nevertheless a directly reconciled result; uncertainty about other periods does
not turn that loss into a passing development result.

Endpoint fees and basis changes are resampled as daily observations, so the
interval is not a confidence interval for coherent repeated complete trades or
future annual profit. Historical search multiplicity is incomplete and the
window is spent. Neither the bootstrap nor narrow fitted betas create fresh
confirmation.

Close this fixed book/quarter question under its failed cash screens. Preserve
the original historical holdout NO-GO and the earlier definition diagnostic:
they concern different book conventions and windows and are not overwritten by
this result. Three new carry investigations have used the current incremental
allowance. The justified next action is a separately registered dated-archive
input admission in the maintained research map, rather than another carry cost,
allocation or window variant. Any later carry reopening needs a documented
information-value case and relevant new evidence before its outcomes.

Not tested: achievable simultaneous fills, actual fee assets/commissions/lots,
historical calendar/product/maintenance applicability, continuous margin or
liquidation paths, stablecoin/counterparty losses, nominal bootstrap coverage,
prospective profit confidence, genuinely fresh confirmation, account eligibility,
external pre-result backup timing, or runtime concurrency/crash behavior. No
higher effort is needed for the completed reconstruction; those unresolved
claims require appropriate new evidence, not repetition of this experiment.
