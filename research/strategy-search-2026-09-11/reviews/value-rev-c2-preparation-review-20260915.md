# Independent C2 preparation review — September 15, 2026

**Decision: the proposed C2 convention is defensible as an explicit pre-outcome
clarification of the registered economic reversal control.** Recording it for
preparation does not itself require a different strategy family or consume an
empirical allowance. It creates no source, P0, grid or financial admission.
The original charter, gate, inherited score defaults and prior evidence remain
unchanged. A later financial run still requires its complete registered source,
accounting, controls and trial admission.

The original goal says that the reversal control may absorb the value factor;
the gate describes C2 as `reversal (-30d return) sort`. The inherited control
instead sums 30 simple daily returns and passes a positive score into a
high-is-short ranker (`value_xs.py:88–105`, `ls_common.py:47–64`). Its economic
direction is reversal, but its numerical return definition is not a compounded
holding-period return. This source difference is material and must remain
visible; the new definition is not a claim that the old code already implements
it or that old comparisons can be relabeled.

## Proposed explicit contract

For one symbol and a common feature cutoff, take exactly 30 consecutive admitted
calendar-day simple **price-return** intervals ending at that cutoff. Define

`R30 = product(1 + r_d for the 30 intervals) - 1`

and `C2_score = -R30`, with the mandatory orientation `high_is_long`. No funding,
trading fee or risk-free charge enters this price-return signal; those remain in
the identical downstream portfolio accounting. Returns must be finite and
strictly greater than -1 for the admitted positive-mark instrument convention.
A missing, duplicated, nonconsecutive, late or otherwise unadmitted interval
makes that required symbol's control unavailable. Do not fill, interpolate,
compress to 30 observed dates, substitute a sum, drop the symbol from the fixed
cohort, or infer a terminal zero price for a positive-mark instrument.

The window requires 31 supported boundary prices, or equivalently 30 separately
admitted simple-return intervals with their provenance. The same price series,
corporate/token-unit adjustment convention and instrument identity must apply
throughout. Mathematical validity of a list of 30 numbers does not establish
those source facts.

The score/orientation pair has the required economic direction. An invented
loser with `R30 = -0.20` has score `+0.20` and ranks toward the long leg; a winner
with `R30 = +0.25` has score `-0.25` and ranks toward the short leg. This statement
concerns ranks; membership still depends on the full admitted cohort, breadth
and tie policy. Passing the negative score into the unchanged high-is-short
legacy ranker would reverse that direction and is explicitly inadmissible.
An additive adapter must respect the declared orientation or perform an
explicitly equivalent score conversion with a proved common ranking contract.

Compounding is a substantive definition choice, not a harmless sign cleanup.
For example, 20% followed by -20%, with the other 28 returns zero, compounds to
-4% although its simple-return sum is zero. A second invented asset with -1%
and 29 zeros has compounded and summed return -1%. The two definitions reverse
their relative order. This is exactly why the compounded definition must be
committed before value_rev control outcomes and must not be tuned against them.
No empirical calculation or engine run was performed for these algebraic examples.

## Remaining ranking and clock conditions

- **Ties:** equal compounded returns produce equal scores. Freeze one common
  deterministic tie rule, disjoint-leg construction, leg-size rounding and
  minimum-name behavior for strategy/C1/C2/placebos before the grid. The old
  ranker uses lexical symbol order, short-leg selection first and rounded leg
  counts. Changing score orientation must not accidentally change tie-side
  priority or choose a different cohort. No random, turnover-minimizing or
  outcome-informed tie breaking is approved here. All-equal-score rows also need
  an explicit common treatment: the inherited z-score has zero dispersion and
  becomes unavailable; raw scores with lexical sorting would instead fabricate
  a ranked portfolio. Preserve unavailability unless a separately reviewed
  common policy deliberately changes that case.
- **Normalization:** a positive finite cross-sectional standardization preserves
  ranks, so using `-R30` directly can be equivalent on nondegenerate rows.
  It is not automatically equivalent for zero dispersion, missing values or
  floating-point ties. Keep orientation and validity independent of any such
  normalization and test those cases before implementation admission.
- **Economic cutoff versus availability:** specify both the economic end of the
  last included interval and the latest allowed source-availability clock.
  The common feature lag may move the economic cutoff; it does not itself prove
  when the 30 returns became observable. Every interval must be admitted under
  the frozen information boundary, no later than the actual decision. Do not
  derive historical availability from a recent backfilled array. UTC day
  semantics, consecutive boundaries, Monday decision and later action timing
  remain common to all roles. No default two-day lag may survive only inside C2
  when an admitted common lag is widened.
- **Missing support:** an unavailable C2 member makes the matched comparison
  unavailable under the proposed fixed-cohort policy. Do not repair parity by
  running C2 on a smaller universe or silently carrying a different rebalance
  schedule. Low exposure or profitable outcomes are not inferred from reversal
  orientation or dollar-neutral targets.

## Governance and scope

The clarification fixes the registered control's intended economic direction
and a precise interpretation of “30-day return”; it does not add a metric,
breadth, lookback candidate or fifth value_rev grid cell. No alternative C2
formulation may be evaluated and selected after outcomes under this decision.
Keep the four original cells, both required control comparisons, all original
numerical gates and cumulative research history. Any later comparison of
compounded versus summed C2 on real data would be a separately registered
investigation, not free preparation.

This review inspected the original charter/gate and the source-only engine audit,
then reread the relevant inherited control/ranking functions. It did not inspect
raw prices, fees, funding, panels, financial outcomes or ledger values, and did
not execute tests or a financial engine. No original file was edited. The source
clock, ties, first/last scored dates, realized funding and complete accounting
admission remain separate requirements. The C2 convention can now be explicitly
recorded as preparation; it cannot advance the program past any blocking gate.
