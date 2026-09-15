# Independent lending-book engineering review

## Initial disposition

Changes required before an empirical contract relies on partial preservation.
The ordinary cash arithmetic and corrected opportunity bound passed the scoped
invented checks. This review does not admit F1 or validate source semantics,
execution, returns or a strategy.

Reviewed initial `lending_book.py` SHA256:
`c4f78b3cb943817132d9368b1de15e813d61c5be8d5b4a4956d76872ffb995cd`.
Test-file SHA256:
`c5e49d6a84ad0ccb0bae24a9d876eca98b294e96c7f8d5c7080031ade1c1ad4f`.
Only this review file was written. No network, empirical panel, active F2 root,
orders or existing financial run was accessed.

## Actionable findings

1. **Partial preservation blocker — lines226–232 and283–297.** A funded
   `ProtocolBook.convert` happens before the high-level marked event is appended.
   An invented `ValueError` in the immediately subsequent mark left the actual
   balances at2,997,000,000 USDC atoms,4,800,000,000,000,000 ETH atoms and
   6,993,000,000 scaled claim atoms, with zero high-level events. Calling
   `partial_snapshot` then raised `partial lending atom replay differs` instead
   of preserving that evidence. Serialize and independently replay the literal
   `book.events` deltas even when event valuation or attribution is incomplete.
   Preserve an explicit incomplete-attribution status and current exact source
   clock/marks/index references before fallible observation. The already
   calculated stress maxima at lines212–216 are also local only; a later source
   cash/flag failure currently loses those partial measurements. Retain them in
   the progress record. Test failure after mutation and during later observation.

2. **Opportunity-bound dependency limitation — lines301–308 versus49–64.** The
   bound advertises omitted withdrawal restrictions but invokes the primary
   validator, requiring all daily configuration and contract-cash values.
   Deleting an unused `contract_cash` in an invented row raises `KeyError` before
   the bound. If the registered diagnostic is intended to survive missing
   cap/withdrawal evidence, give it its actual fixed index/price/model validator
   and retain the missing feasibility evidence separately. Otherwise declare
   this stronger prerequisite explicitly; it cannot silently produce an
   economic rejection from a source gap.

## Independent verification

The named lending math/book tests passed18/18. A separate deterministic set of
24 invented books, eight varying exact price/index panels across all three cost
scenarios, was reconstructed directly from initial capital, literal half-up mint
and redemption formulas, idle cash, terminal native sale and route cost. Every
exact terminal P matched. Every signed event replay stayed nonnegative and
matched the recorded balances. The generous ceiling dominated all24 results.
This verification did not simply compare the helper's own attribution fields.

The accounting correctly funds the0.005ETH reserve from total capital. Supply
uses70% of initial USDC atoms; the receipt replaces spent USDC. Two entry gas
charges plus one withdrawal and one native-sale charge total four, funded from
held ETH. Unspent USDC, native-sale dust and the terminal route are retained.
Interest changes receipt entitlement and is paid only once on withdrawal.

The decomposition at lines190–194 is exact: old entitlement times the USD-price
change plus entitlement growth times the new USD price includes the cross term
once. Conversion rounding can create a small signed gain as well as a loss;
signed attribution accommodates both. The log diagnostic is isolated from cash.

The combined50% ordinary credit haircut and20% USDC depeg remain inside ordinary
market stress. Growth can increase the held lending share and worsen the shock;
the code tests held states rather than assuming70% forever. Contract-position
loss is revalued on the same net exit basis and separately reports gross affected
value. Delay flags explicitly leave horizon cash unavailable. These are authored
marked stress scenarios, not a forecast, solvency guarantee or modeled queue.
Daily observations do not bound intraday drawdown or withdrawal priority.

The nested ceilings at lines314–315 dominate half-up mint and redemption under
positive qualified indices. Keeping all initial native gas at its terminal mark,
omitting nonnegative transaction/sale/route costs, and retaining identical idle
USDC makes a generous endpoint bound for this fixed source-model allocation.
Below$1,000 can reject only this opportunity's absolute target; above it is
inconclusive. The bound has no power to establish cap admission, risk, execution,
benchmark superiority or promotion.

## Source and future registration limits

Cap-enabled but unproved entry remains unavailable; a false sufficient bound is
inconclusive, not actual cap failure. The input qualification Boolean is a
caller assertion whose evidence must be independently pinned by a future source
contract. It cannot stand for deployed historical semantics or absence of
counterfactual utilization/rate effects.

A clearer future output arrangement is one explicitly named cap-assumed
numerical diagnostic and a separate strict entry-feasibility/primary-availability
cell. Freeze its exact scenarios, assumptions and denominator before outcomes.
Do not forge a debt/cap flag or let diagnostic P rescue missing admission. A
duplicated strict/assumed pair is possible if fully counted, but adds no
scientific information when accounting is identical and only admission differs.

Benchmark comparison, complete source qualification, ownership exclusions,
resource manifests, run-level persistence and F1 admission were not tested here;
no complete F1 financial registration was presented. No finding changes the
frozen options, core allocation or active F2 work.

## Reviewed correction and final engineering disposition

Both initial findings are resolved in `lending_book.py` SHA256
`ada35d903b957bf036721dce79c3829c51aa326344e1180dcb08d4c9b5613f40`, using
new `literal_receipts.py` SHA256
`f6012f929b0b3250dd7703a43216bd0c7c00847f9b8732cfea7d677be81dea60`.
The source owner made these changes; this reviewer changed no implementation.
The original findings and reproduction above remain preserved.

The new partial snapshot retains the actual funded ledger's signed deltas and
asset identities, current balances, a replay result, valued-event coverage and
an explicit partial-attribution label. It does not erase a conversion because
the subsequent high-level mark failed. Current row/index/marks and partial
stress maxima are retained. Independent fault injection immediately after a
funded supply and during a later January1 stress observation now preserves
JSON-serializable receipts, reconciled balances and existing stress results.
Unknown asset identities remain visible and force reconciliation false.

The ceiling uses `validate_panel(..., operational=False)`: a complete fixed
calendar of positive exact marks and qualified nondecreasing indices is still
required, but unused config/cash values are not invented. Independent removal of
all config/cash fields now leaves the ceiling computable. This change affects
only the explicitly generous diagnostic.

The new explicit `assume-cap-for-diagnostic` role leaves a nonzero cap recorded
with `sufficient_cap_pass=None`, `cap_unproved=True` and strict proof false.
It does not manufacture debt/treasury evidence. Exact future registration must
still count and label this role; neither numerical target nor risk flags may be
reported as a primary adoption pass when cap proof is missing.

The combined focused check now passes30 tests:13 lending-book,8 lending-math
and9 LP-book tests. This is a scoped synthetic result, not the full offline
suite or financial evidence. **PASS for this narrow lending engineering helper;
F1 source/financial admission remains unreviewed and ungranted.**

### Final endpoint-only ceiling refinement

The final reviewed ceiling needs only the three fixed dated records: inception
September1,2025; deposit September2,2025; terminal September1,2026. It uses
inception/terminal USDC and ETH marks and deposit/terminal normalized indices.
Unused inception index, deposit USD prices, operational fields and intermediate
daily observations are not fabricated. It also accepts a366-record container
and explicitly selects those same endpoints; it does not validate or assert the
intermediate path. The final source SHA256 remains the one recorded above.

This is sufficient for the algebraic endpoint bound and does not admit a daily
drawdown/stress/path result. The exact dates, positive exact marks, model flags,
index domains and nondecreasing endpoint index remain checked. The new sparse
endpoint test and the combined focused suite pass31/31 (14 lending-book,
8 lending-math,9 LP-book). This supersedes only the preceding description of the
ceiling's full-calendar requirement; primary/conditional full books still need
their complete fixed source panel.

## Additional bounded LP-helper review

`lp_book.py` SHA256
`0f23c34aad58f9989730c80c7616c1f14cd71870354846b7c16f6511a2680420`
was separately reviewed with invented inputs only. Its ordinary arithmetic
passed twelve independent literal reconstructions: two price/index paths,
candidate and matched-entry inventory, and all three costs. Independent rational
burn-inventory formulas, integer fee-counter deltas and terminal sales reproduced
every exact P. Candidate and control consume respectively ten and five gas units
per modeled transaction cost; neither borrows gas from sale proceeds. The control
holds the same purchased WETH atoms and retains the USDC that the candidate
contributes. Native ETH remains a separate asset.

LP principal transformation, accrued fees and old-inventory USD repricing
reconcile without an additional impermanent-loss debit. Fees accrued before entry
are excluded and held fees are paid once. Full usable-range global-growth
attribution remains conditional on the previously reviewed standard-v3 model,
unchanged historical path, counter identity/continuity and integer domain. It is
not a finite-capital fee-dilution or trading-impact simulation. The sampled
virtual/historical liquidity ratio cannot bound intraday fee-producing steps.
Mint boundary headroom does not establish subsequent collect liquidity or
personal execution access. Those limitations are present in the helper's scope.

The same partial-preservation concern was identified at the original
`lp_book.py:238`–243/293–305. The new literal receipt helper resolves it for the
reviewed source. Independent failure immediately after the first funded WETH
purchase and during a later stress observation preserved current exact balances,
the low-level conversion, incomplete high-level coverage, current row and prior
stress maxima, with valid JSON. The implementation's additional failure after
the LP mint also passes. No LP accounting blocker remains in this scoped review.

This is **engineering PASS only**. A complete F3 financial charter, source
qualification, attempt ownership, source budgets, benchmark set and empirical
results have not been reviewed or admitted by this helper check.
