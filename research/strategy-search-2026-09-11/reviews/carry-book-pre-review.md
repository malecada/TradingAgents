# Independent pre-result review — conditional quantity book

Disposition: **pass for the frozen conditional development investigation**.
The signed-cash implementation, statistics, orchestration, charter and complete
gate were reviewed before financial outcomes. One concrete invalid-NAV check was
corrected and one uncertainty interpretation was clarified during review. No
unresolved blocker remains in the reviewed scope. No raw financial book or
economic outcome was executed by the reviewer.

Reviewed SHA256 identities:

| File | SHA256 |
|---|---|
| `carry_book.py` | `8ad2a08b14653800d7c34a6a391a36fcb43717c7083ec7398f6bdbf8f5a72d55` |
| `carry_statistics.py` | `bb38bad2185c058233625050234364c8c111caf035e7c7666748893f374b0c82` |
| `carry_book_run.py` | `e96684b6cc433e62c2d2d0975b646284ff59dc2428b3e2ecec6ebb639c6fd74c` |
| `carry-book-charter.md` | `5ce44f44663b1da2be785e0d15fbd37c153e02bd165381353778d7618e4cd3b5` |
| `gates-book.json` | `66bf66deabbc639dd4151d7bd6df7273b90594b1c086daae796000f20b81ecfe` |

The gate's source/charter hashes match the reviewed bytes. Its capture and
admission input hashes match the independently reviewed parent outputs. The
earlier gate objects, family budget and dataset history are unchanged from
`gates-capture.json`. Sixteen unique cells preserve all eight primary books and
eight zero-funding counterfactuals. Unknown legacy multiplicity remains unknown;
this is the third investigation in the fixed new allowance, not a reset.

## Accounting and timing findings

- Matched signed base quantities are used throughout. Spot principal and both
  entry fees consume at most 40% of initial capital; 50% is reserved in the
  futures wallet and at least 10% remains idle. The entry futures fee is funded
  from the entry budget. Futures sale notional is never booked as cash.
- Funding uses quantity times the associated event mark times its signed rate.
  The opening canonical funding event through start plus five seconds is
  excluded, and all subsequent captured events remain in the conditional
  calendar. No price/funding interpolation, percentage-return short-equity drift
  or zero-fill of missing events was found.
- Daily wealth includes spot principal, idle cash, funding-adjusted futures
  cash and the short's linear mark-to-market. Terminal spot sale, short cover,
  collateral, adverse execution prices and all four fees reconcile to the
  signed price/funding components. The final trace shows post-exit cash and zero
  exposure while retaining its pre-exit components.
- An independent invented example used different spot, perpetual and mark
  price levels, alternating signed funding and Decimal transaction accounting.
  All 91 pre-exit daily wealth snapshots and terminal cash agreed to 1e-10 USDT.
  This example read no captured financial observations and imported no runner.
- The daily reserve diagnostic is a conservative lower bound under its stated
  fixed-quantity model: prior funding cash plus all negative payments that day,
  loss at the reported mark high and an assumed 1% maintenance buffer. The raw
  capture review already checked all event marks against the corresponding
  daily mark range. This does not establish actual intraday liquidation safety,
  historical maintenance tiers or the ability to continue holding after a
  modeled deficit.
- Fixed down-50% and up-100% sensitivities preserve quantities and initial fees,
  use zero future funding explicitly and expose the futures wallet. Fees,
  common quantity steps, fills and maintenance are scenario assumptions.

## Corrected and qualified statistical findings

1. **A negative final NAV could receive beta estimates.** The initial
   [market-exposure guard](../carry_statistics.py#L35) checked previous wealth
   but not current wealth. An invented sequence with 90 daily NAVs of 1,000 and
   terminal NAV of -1 returned a complete regression despite a terminal return
   below -100%. The corrected guard rejects any nonpositive current or previous
   NAV. The independent counterexample and added last-day regression now return
   unavailable exposure. This prevents an invalid wealth path being labeled a
   valid simple-return beta estimate.
2. **Bootstrap intervals have a narrower interpretation than future-profit
   uncertainty.** Resampling daily changes also resamples one-off entry/exit
   fees and basis changes. An invented series containing only deterministic
   endpoint fees produced positive bootstrap dispersion; it is not a coherent
   resampling of repeated complete 91-day trades. The charter and output scope
   now explicitly limit these intervals to sensitivity of the empirical
   daily-mean model. Future-profit confidence and confirmatory coverage remain
   unestablished.

The bootstrap implementation matches its frozen description: eight 91-day
fixed-initial-capital cash-change series, common circular seven-day blocks,
2,000 paired draws, seed 20260911, and tail quantiles 0.003125/0.996875 for the
eight-case Bonferroni diagnostic. Array axes preserve the intended case and
resample dimensions. Standard error and the normal/block-bootstrap detectable
effect are labeled approximate.

Exposure uses contemporaneous simple BTC/ETH spot returns, a separate
intercept, OLS HAC lag seven and 97.5% individual beta intervals, corresponding
to the stated within-book Bonferroni convention. Singular and invalid designs
remain unavailable. These are descriptive estimates on spent history; no
across-history multiplicity or genuine sample freshness is established.

The runner retains each primary/counterfactual cell, marks missing inputs
unavailable, and blocks the paired eight-case uncertainty result if its primary
denominator is incomplete. Zero-funding results are an explicit intervention
with the same price/quantity/cost construction, not a substitute for missing
funding. Cash benchmarks remain separate from cash profit. Every summary fixes
adoption validation to false and makes no best-case selection.

## Verification and limits

**21 focused synthetic tests passed** across the book, statistics and runner.
Coverage includes funding signs and opening-event exclusion, principal release,
cost/lot/reserve constraints, planted funding, shared-price hedge cancellation,
the old false-drift failure, price stresses, missing data, paired resampling,
planted beta recovery, invalid NAV and the full sixteen-cell denominator.
The independent invented transaction reconstruction and invalid-final-NAV
counterexample also passed. The full legacy suite was not run.

Not tested: any actual financial result, post-run cash/statistical reconstruction,
nominal interval coverage under nonstationarity or the full historical search,
historical calendar/fee/lot/maintenance applicability, actual fee-asset handling,
simultaneous executable fills, continuous margin paths, stablecoin/counterparty
losses, account eligibility, fresh confirmation, external pre-result backup
timing, or crash/concurrency fault injection. Positive conditional screens cannot
remove these missing claims or establish a validated strategy.

No higher effort is needed to resolve the corrected source guard or the frozen
arithmetic question before execution. After the committed/pushed freeze and one
run, independent reconstruction from retained raw inputs is required before any
economic interpretation or next-stage decision.
