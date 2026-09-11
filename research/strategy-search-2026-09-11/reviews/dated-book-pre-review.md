# Independent pre-result review — dated cash book

Disposition: **the book, runner, statistics and final gate pass the full bounded
pre-result review**. No material unresolved discrepancy remains. No captured
prices or financial outcomes were read or evaluated by the reviewer; empirical
input access was limited to hash verification.

Reviewed source: `dated_book.py`, SHA256
`94d591c304db92c16c1208b61269e0f8190d24ccecceedf70056d7788ebaa65c`.
The implementation dynamically loads `carry_book.py` to obtain the cost/lot
constants and cash-liquidation primitive. Its reviewed dependency SHA256 is
`8ad2a08b14653800d7c34a6a391a36fcb43717c7083ec7398f6bdbf8f5a72d55`.
The final gate pins both files, plus the statistical and archive/capture helpers,
so the reused economic and admission dependencies remain frozen.

Final additional SHA256 identities:

| File | SHA256 |
|---|---|
| `dated_book_run.py` | `87623dff2eb691cc2e6abdd35ca0bfc7289496a41e9b50a3e28981171b53699b` |
| `dated_statistics.py` | `28c5d01aeb5644b8edf65833fb95c291f8d5eb66dac53147269ea889ff77f61c` |
| `dated_archive.py` | `631412c60dd411466db185b3ae2cfb0cc62d5423153c98432e9aa93db86efb3d` |
| `carry_capture.py` | `323ea01ac0d8137288e6f72f697101db1884595e876622402c321f38367d6b12` |
| `dated-book-charter.md` | `c0fcee6424c8bc42e9f577f3013f21abde028ea4d85eb9f2239f86a4f46d4c01` |
| `gates-dated-book.json` | `1dec7b995bf47478810f106c041bd69db7ec3bbb410d99f0f9392ddadac9b546` |

## Verified accounting and chronology

- The fixed interval is 56 days: May 1 open through the final June 25 hourly
  close, with June 26 excluded. Exact 56-day spot and 1,344-hour dated grids are
  required. Positive dated volume and trade counts at both execution endpoints
  are required; interior zero-activity hours stay in the retained denominator.
  This does not establish simultaneous spot/future fills.
- The same base quantity is bought in spot and sold in the dated future.
  Principal and both entry commissions fit inside 40% of initial capital; 50%
  is reserved in the futures wallet and at least 10% remains idle. Short-sale
  notional is not counted as cash. No rebalancing, capital compounding or
  repeated percentage-return short-equity calculation was found.
- Terminal cash includes spot principal sale, futures reserve plus signed price
  PnL, idle cash and all exit costs. The four commissions and four adverse price
  shifts are proportional to the corresponding quantity/price. Periodic
  perpetual funding is not inserted into the dated-contract hypothesis.
- The frictionless counterfactual is a scalar at the exact primary quantity:
  `q × [(spot_exit - spot_entry) + (future_entry - future_exit)]` on raw prices.
  It does not refit quantity after removing costs or imply a larger portfolio.
  Its difference from executed price PnL isolates slippage; commissions remain
  separate. Signed-component and wallet terminal cash reconcile.
- The final daily trace switches to post-exit wallets and zero quantities,
  spot value, unrealized future PnL and net/gross exposure. Pre-exit components
  remain separately retained. Drawdown includes original capital; convention
  diagnostics include terminal fees and cannot replace cash wealth.

An independent invented example used distinct evolving spot and dated prices
and Decimal transaction accounting. All 56 pre-exit daily wealth observations,
terminal cash and the same-quantity frictionless scalar agreed within
1e-10 USDT. **All 11 focused synthetic tests passed**, including planted basis
profit, constant-price friction, principal release, endpoint/held zero activity,
missing hours, price stresses, negative wealth and terminal conventions. No
financial experiment was run. Final combined verification, including statistics
and runner tests, is **26 synthetic tests passed**.

## Runner, statistics and gate completion

The runner retains all eight primary cases on global or per-asset source failure.
It verifies source identities, admitted statuses, raw byte hashes, archive/checksum
pairs and member identities before clipping. Whole parent calendars are admitted
first; the retained interval and before/after exclusion counts are explicit.
Accounting disagreement above 1e-8 USDT blocks the affected case. The same-capital
base-and-stress relevance check is paired correctly; the frictionless scalar
does not become an extra, differently financed portfolio. Execution and actual
margin remain unavailable, with graduation and adoption false.

The date constants independently reconcile to May 1, 2026 UTC
(`1777593600000` ms), June 26, 2026 UTC exclusive (`1782432000000` ms), and the
final June 25 close (`1782431999999` ms). A latent statistics admission gap was
found: `int()` silently accepted a synthetic opening timestamp at START plus
0.5 ms. [The corrected strict parser](../dated_statistics.py#L34) accepts only
integer milliseconds or exact 13-digit integer strings; the independent
counterexample and added regression now reject the fractional clock. The book
already used this strict convention.

Statistics use exactly 56 valid paired simple NAV/spot observations, the first
spot open as the initial benchmark reference, intercept, joint BTC/ETH OLS and
HAC lag seven with 97.5% individual intervals. Nonpositive NAV, nonfinite values
and singular/missing benchmarks remain unavailable. Expected-return confidence
and power remain explicitly unavailable for every book; no bootstrap of this
single convergence episode is performed. Real-statistics synthetic integration,
not only a fake statistics callback, is included among the passing tests.

The final gate preserves all prior experiment objects, family counts and dataset
histories unchanged. Four input hashes match their declared paths; archive inputs
use the dated-contract identity and spot inputs retain the legacy exposed-history
identity. The gate contains exactly eight unique primary cells and two result
outputs. All declared source, charter and input hashes were checked against the
current bytes. This does not itself prove a prior external backup or authorize
execution before the required committed/pushed freeze.

## Claims that remain unavailable

The trade-high reserve value is explicitly a **nonconservative margin proxy**:
dated trade highs cannot upper-bound an unobserved exchange mark. The output
keeps actual margin risk unavailable regardless of that proxy. Trade-price
valuation and fitted exposure likewise cannot establish true mark-based risk or
intraday liquidation safety.

The episode ends before the unverified expiry-day terminal bar and realizes
modeled sale/cover proceeds; no unknown settlement price is substituted. The
charter discloses that the fixed lifetime/date cut was informed by prior data
admission. This is an exposed, conditional historical episode. One episode per
asset cannot establish expected profitability, power, fresh confirmation or an
annual return forecast, even if its point relevance screen passes.

Untested in this review: actual archive/spot values and empirical clipping;
statistical nominal coverage; actual fee assets, commissions and common lot
applicability; contract/account access; fills, maintenance tiers, settlement and
margin paths; actual financial results and their post-run reconstruction; and
crash/concurrency or remote-backup behavior. No higher effort is needed for the
completed pre-result arithmetic and admission checks. A single registered run
and independent reconstruction are the next evidence steps after the freeze.

## Final endpoint-admission addendum

The coordinator identified and corrected a charter/source gap before freezing:
positive endpoint activity now applies to both spot daily bars and dated hourly
bars. The guard at `dated_book.py:70` checks volume and trade count at all four
endpoints and preserves an unavailable result on failure. Four added synthetic
cases independently exercise zero spot entry/exit volume and trade counts.
The final combined synthetic suite passed **30 tests**. No empirical inputs or
outcomes were evaluated. The pre-result PASS remains applicable to final book
SHA256 `3977b87b507088238c346dd4dfa7ae3b7934bfd2900a313298df200f0bfcb6ab`
and gate SHA256
`ef446526b30409cfd32a5c0175a3b58ed3953248fac71ca2a9465cf8f5085ee6`,
which supersede the earlier hashes above. Positive daily spot activity alone
does not establish an executable quoted price; actual fills remain unavailable.
