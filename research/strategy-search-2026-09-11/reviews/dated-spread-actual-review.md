# Dated/perpetual retained outputs: independent forensic review

September 11, 2026. **PASS for reconstructed retained-output arithmetic;
operational experiment status remains FAILED.** The registered 120-second
limit was exceeded before a terminal receipt was published. Reviewed failure-
only closure preserved the claim and all three output hashes. There is no
complete.json, no successful resource verdict and no completed lifecycle cell
verdict. The eight cases below are reconstructed contents of a failed run,
not a relabeled successfully completed trial.

Source commit is `6d6d65f9712dd41e135672a2f0fb8a7d8389507b`.
Failed receipt SHA256 is
`4527836bd62688857764f7d68f7c98660522b6e54f5e64b81f5841c959a4b021`.
The resource guard records 120.0510955 seconds, wall-clock limit exceeded,
exit -15 and 418,467,840 bytes sampled aggregate RSS. The recovery review,
one-time closure record and retained guard establish this operational failure;
the scientific reconstruction does not override it or repeat the experiment.

## Independent reconstruction and retained denominator

check_dated_spread_actual.py reads registered raw parent responses and independently
reconstructs quantities, signed cash, funding, fees, wallets, marked NAV, scalar
diagnostics and stress values with Fractions. It does not import the engine,
adapter, runner or statistical implementation. Direct OLS/Bartlett-HAC covariance
and Student-t intervals use independently reconstructed NAVs and raw spot prices.
The separate receipt verifier is used only for structural provenance.

All 20 raw source cells pass independent request/hash/schema/chronology checks:
ten carry responses, eight ZIP/checksum responses and two dated-mark receipts.
The full 91-day carry histories and 273-event funding calendars are checked
before clipping. Paired archive digests, single expected CSV members, complete
May hours and contiguous observed June tails reconcile. The June tail remains
an observed tail, not a proven complete contract lifetime. The 56-day marked
episode uses 1,344 dated trade hours and 56 daily rows of each required series.
Funding event marks lie within their source day's mark range.

All eight retained cases, 448 NAV values, 16 same-q scalar diagnostics and 72
stress states reconcile. Each case retains 168 canonical funding observations,
excludes the first May1 slot and credits exactly 167 later events. The 90 prior
and 15 later Q2 slots remain outside this window. First and later actual event
clocks are respected; no early June26 event enters. No held price/funding gap
was filled. Claim/input/source/output hashes and all three output names match.
Output bytes total 1,063,909.

The final checker passes 9,344 numeric assertions, maximum absolute error
3.637978807091713e-12. Signed quantities, exact lot ceiling, separate reserves,
all execution fees, adverse slippage, funding, final collateral release and
post-exit zero holdings reconcile. The log shadow telescopes on this positive-NAV
path but remains invalid arithmetic PnL. Every covariance entry, beta/standard
error and interval endpoint reconciles to the direct HAC construction. Conditional
screen statuses and separate wallet flags also match reconstructed quantities.

## Financial contents of the failed-run outputs

All modeled cash profits are negative. Base and stress use the same selected
quantity within each asset/capital pair in this episode.

| Asset | Full capital | Quantity | Base cash profit | Stress cash profit | Same-q frictionless cash |
|---|---:|---:|---:|---:|---:|
| BTC | 1,000 | 0.005 | -0.237869 | -1.191052 | +0.715314 |
| BTC | 10,000 | 0.052 | -2.473838 | -12.386943 | +7.439265 |
| ETH | 1,000 | 0.17 | -0.045520 | -0.956075 | +0.865035 |
| ETH | 10,000 | 1.76 | -0.471266 | -9.898187 | +8.955653 |

At 1,000 capital, BTC's raw two-leg price cash is -0.586000 and short funding
is +1.301314. Base fees of 0.680845 and slippage of 0.272338 exceed that remaining
0.715314 gross cash. ETH's raw price cash is -0.360400 and funding +1.225435;
base fees 0.650396 and slippage 0.260158 exceed its 0.865035 gross cash. Doubling
transaction costs worsens both. Funding materially offsets the adverse relative
price change; all same-q zero-funding scalar profits are negative.

Removing every modeled transaction cost would make these fixed paths positive,
but would still miss the 3% annual simple full-capital relevance benchmark:
4.602740 over 56 days at 1,000 capital and 46.027397 at 10,000. Therefore reducing
the modeled fee/slippage assumptions alone cannot rescue the registered economic
relevance of this fixed quantity/path. This is narrower than saying transaction
cost reduction could never yield positive cash or that all future derivative
spreads fail. Changing notional, reserves, dates or direction would be a new
economic question, not a correction of these outputs.

Every conditional beta/interval, drawdown, modeled linear delta and separate
path/stress-wallet screen passes numerically. BTC coefficient estimates across
the eight books range approximately -0.00571 to -0.00245 and ETH coefficients
from +0.00078 to +0.00283. These descriptive estimates do not establish actual
market neutrality or safety. The reserve checks assume separate fixed wallets,
daily extrema and provisional one-percent maintenance, without actual exchange
tiers, intraday liquidation, portfolio margin, fills or access verification.

Expected-profit confidence and power remain unavailable for one exposed episode
per asset. The eight cases are correlated alternatives, not independent successes
or a pooled portfolio. Every retained graduation/validated-strategy flag remains
false. The operational resource requirement also failed independently of these
financial diagnostics.

## History and next information value

The new verifier accepts the failed receipt with three retained outputs and zero
completed lifecycle cells. Historical v1 and v2 proofs pass at their respective
closed inventories. Their frozen live-ledger verifiers now refuse with
"amendment inventory or original budget differs" and "complete current prior
inventory differs", respectively; both expected refusals remain preserved.
Six visible program claims plus historical1 consume effective7. Original cap4/
prior1, both earlier failed harnesses and both earlier consumed grants remain
unchanged. This failed claim does not restore an allowance.

No further trial is justified merely to obtain a complete receipt or tune costs
around near-zero net cash: the full retained diagnostics are independently
recoverable and even the same-q frictionless scalar misses relevance. A future
implementation reuse must account for the observed full-repository lifecycle
cost rather than assume disposable preflight timing transfers unchanged; no
causal timing profile was run in this financial review. Preserve this failure
and all bytes instead of silently increasing the resource limit.

The next decision should reassess materially motivated remaining families and
concrete source/design prerequisites. This result neither establishes complete
research exhaustion nor automatically authorizes another dated attempt. The
specific prospective options policy deserves a separate information-value review;
unknown account access must not be substituted for determining which public
research or preparation is actually possible.
