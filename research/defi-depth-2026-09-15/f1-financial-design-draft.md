# F1 financial design proposal: lending and cash

Unexecuted design. F2 is independently active; no F1 source capture or financial
book has been admitted. This proposal changes the earlier all-investable-USDC
lending draft before any F1 observations, for the explicit stress reason below.
The earlier proposal remains preserved. No parameter sweep or return-based choice.

## Mechanism and allocation

One unlevered native-USDC Aave V3 deposit on Base, held without reinvestment or
intermediate trades. Propose70% of initial investable USDC after prefunding the
same0.005nativeETH gas reserve;30% remains walletUSDC. Reuse$10000total capital,
365dayhorizon, September2entry and the fixed latest2025-09-01→2026-09-01window.
The two earlier annual cohorts remain visible unavailable when prerequisites are
missing. No leverage, rewards farming, token substitution or floating sleeve.

A proposed ordinary market-credit shock cuts the lender's underlying entitlement
by50%; a simultaneous USDC shock cuts both lending and walletUSDC dollar value
by20%, with30days of withdrawal/redemption delay. ETH gas loses90% in the combined
case. These are authored deterministic stress assumptions, not estimated
probabilities or a claim that all losses are bounded by these shocks. Contract
exploits remain separate tails; ordinary credit loss remains inside market stress.

Ignoring tiny gas/cost terms, account retention is0.8*(1−0.5*w) for lending sharew.
The50%stress-loss limit requiresw≤0.75. Thus the earlier100%lending proposal would
fail this combined stress algebra before source acquisition.70% leaves a margin
below that boundary without optimizing against any financial panel. Accrued
interest can increase the lending share over time; the actual fixed book must
check the shock at every state and can still fail. No forced rebalancing is added.
This is a testable capital-allocation proposal, not evidence that the protocol is
safe or that the sleeve will meet10%annual net return.

## Full cash book to be implemented before registration

Start with exact USD-valued prefunded gas plus integer USDC atoms; charge funding
rounding. Supply floor(initialUSDCatoms*7/10) with two modeled transactions,
approval and supply. Hold integer scaled aToken units, not a cash credit for an
APR. At terminal redeem the whole qualified underlying balance with one withdrawal
transaction, then sell residual nativeETH using one transaction funded from that
same gas balance. Primary0.0001ETH/transaction, doubled0.0002ETH, frictionless0;
USDterminal route$10/$20/$10. Swap/native-sale assumptions remain the F2one-hop
conditional model; no lending fee is invented or omitted contrary to actual terms.
Any observed additional cost or admission gap must remain explicit/unavailable.

P must reconcile from signed initial funding, deposit, receipt, redemption, gas,
residual nativeETH/USDC and final dollar-route events. Interest accrual changes the
underlying value of held scaled units; it is not credited a second time on exit.
Unknown withdrawal cash, pause/flags or claim units cannot become certain cash.
Compare both absolute P and all fixed D, including a matched walletcash book and
originalB0–B9 with their existing limitations.10%/$1000absolute and2%/$200incremental
hurdles and risk thresholds remain primary; no favorable metric substitution.

## Source prerequisites and cheapest adequate qualification

F2 owns common price/header observations. Reuse qualified retained inputs and
all failures; no old request repeats or unfinished source-program continuation.
F1's complete source inventory must be frozen together with the financial recipe.
No financial calculation until its necessary daily source panel is complete.

Daily requirements include exact normalized income and units, configuration and
observed contract withdrawal cash, with their immutable block association and
USDprice marks. Same-block scaled/total supply arithmetic and deployed identity
checks qualify the model but do not establish future solvency or priority.
No external funding enters the book when source cash or gas is inadequate.

Only the fixed entry needs a supply-cap admissibility proof. The direct model
needs next-index and post-update treasury consistency. A weaker, sufficient
conservative test may use a same-block upper bound on all current underlying debt,
with version-qualified nonnegative/monotone debt-interest and reserve-factor
assumptions. See reviews/lending-math-review.md. Failure of that loose bound is
inconclusive, not actual cap failure. A disabled cap short-circuits this question.
Neither a false qualification flag nor an unknown debt/treasury value may be
replaced by zero. Proxy/code identity and unobserved upgrades remain limitations
unless the exact contract source plan establishes more.

The next implementation should reuse the existing funded ledger, validated
integer ray helpers, daily marks and source pacing. Additional acquisition
complexity must materially reduce a real uncertainty or request burden. All
source calls, their ownership, worst-case bytes and financial unavailable cases
must fit the remaining phase grant and receive independent review. No new
financial or source authority follows from this draft by itself.

## Reviewed preparation refinements before any F1 observation

One numerical book is now proposed for each of the three fixed cost scenarios,
with an explicit cap-assumed diagnostic role. The actual entry-cap feasibility
cell remains separate: an enabled but unproved cap is unavailable, never passed.
The diagnostic keeps flags, observed withdrawal cash, funded gas and exact scaled
units. If an independent proof establishes the cap, the identical accounting can
support that narrower conditional claim; no second allocation or return-selected
variant is needed. Source-model qualification is not deployed-version proof, and
the added deposit can change utilization, subsequent interest and borrower behavior.

A separately fixed opportunity ceiling uses inception USD marks, entry normalized
income and terminal income/USD marks at the same three fixed endpoints. It ignores
nonnegative modeled costs and assumes entry/withdrawal; ceiling-rounded mint and
redemption units dominate half-up protocol rounding. It needs no missing daily
cash value or fabricated midyear panel. A bound below$1000 rules out only this
fixed70% source-model opportunity. A bound above the hurdle is inconclusive and
cannot rescue primary feasibility, risk, benchmarks or implementation. Full-year
risk remains unavailable without the required daily evidence.

The source plan will use the five already-reviewed scalar Aave getters rather
than an unverified reserve tuple or aggregation contract. Same-block scaled/total
supply coherence, fixed entry/terminal identities and nonempty code witnesses
support a conditional model only. They cannot prove proxy implementation history,
solvency, cap treasury/debt semantics or executable redemption.

For this distinct financial recipe, actual source clocks may be the fixed
canonical left block with timestamp within[target−1second,target]. No nearest-block
or adjacent-header assertion follows. Only terminal-audited previously successful
inputs and genuinely unsent new source keys may be used. F2's failed right header
and unavailable financial cells remain permanently unchanged. Its unused oracle
slots are not failed financial evidence. The exact new-key ownership inventory,
physical retry slots and global budgets must be committed and independently
reviewed before any F1 request. No acquisition follows from this proposal.
