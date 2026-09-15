# value_rev control preparation decisions — September 15, 2026

Preparation only. No source, capture, P0/P1/P2, grid or financial admission is
created. The original charter, named gate, four cells, sample history and code
remain unchanged. This is an additive definition to bind and implement only in
a later fully admitted pipeline. The [preparation contract](value-rev-preparation-contract-20260915.md)
sets the common cohort, lag and unavailable-input rules.

## C2: adopted explicit interpretation

Adopt the independently reviewed compounded 30-calendar-day simple price return
`R30 = product(1+r_d)-1`, score `-R30`, orientation `high_is_long`. A loser
returning -20% has score +20% and ranks toward long; a winner returning +25%
has score -25% and ranks toward short. Require exactly 30 consecutive admitted
intervals ending at the common economic feature cutoff, with separately admitted
source availability at the information boundary. Each return is finite and >-1
for the positive-mark instrument contract. No missing/duplicate/late interval,
funding component, compressed calendar, interpolation or summation substitute.
Thirty intervals require 31 supported boundaries or equivalent admitted returns.

This changes the inherited summed-return definition explicitly. Passing this
negative score into the old high-is-short ranker would reverse the intended
control and is prohibited. It is not a fifth candidate, and no real comparison
of summed versus compounded alternatives is admitted. See the independent
[C2 review](reviews/value-rev-c2-preparation-review-20260915.md), including the
invented example where their rankings differ.

## Common ranking: preserve inherited choices where possible

Retain minimum five value-valid cohort members and equal +0.5/-0.5 target legs.
For exact rational breadth 1/3 or 1/10, use
`k=max(1, nearest_integer_ties_to_even(n*breadth))`. Reject a nonpositive,
overlapping or incomplete leg. Do not adopt the separately considered floor
rounding or single-total-order tail rule: neither is necessary to repair parity.

Canonical instrument IDs must be unique, source-admitted, fixed before ranking,
and sorted lexically within equal scores. Form an economic shortness score:
use the declared score for `low_is_long`, negate it for `high_is_long`.
These are the exact orientation labels accepted by the pure declaration helper;
low-is-long is economically high-is-short for this two-leg ranking.
Choose shorts first by descending shortness then ascending ID. Choose longs by
ascending shortness then ascending ID, excluding selected shorts. This retains
the inherited short-first two-sort tie priority across all declared orientations.
Require finite scores on the complete fixed cohort. All-equal rows are unavailable,
preserving the inherited zero-dispersion behavior; lexical IDs must not fabricate
a signal in such rows. Missing minimum names or required input makes that
scheduled comparison unavailable, without silently skipping into a different
holding schedule. Retain tie counts and exact ranking declarations.

## Endpoints: adopted conditional source contract

Score every original dev date, January 1, 2021 through March 31, 2025 inclusive.
Once UTC-day semantics are supported, these increments cover January 1 00:00 UTC
through April 1, 2025 00:00 UTC. A final boundary price is not permission to read
an April 1 economic return or any holdout signal. Keep the valuation anchor out
of the scored vector; begin flat, and retain the first scored day's full-NAV
capital charge. Pre-dev lookback support cannot create pre-dev positions.

Monday-close decisions act at the immediate registered next daily boundary,
with source evidence establishing actual receipt before execution. Never search
forward to the next available date. At the exact terminal boundary liquidate all
positions and include closing costs; terminal liquidation supersedes a new
rebalance at that instant. Decisions with actions at or after termination do not
open positions. All roles share boundaries, funding ownership, costs and cashflow
ordering. Unsupported boundaries or held inputs make the book unavailable.
Final liquidation is an explicit addition to old marked continuation, and needs
its own executable-price and event-funding support before financial admission.

## Nulls: adopted B invariants and explicit A deferral

B permutes finite score values only among the fixed eligible cohort, preserving
its multiset, decision dates and leg counts. Keep duplicate permutations and all
500 intended identities; no redraw, jitter, cohort intersection or successful-only
denominator. One randomized score panel per metric/draw is shared across its two
breadths; this coupling does not add independent evidence. Actual RNG recipe,
seed, statistic, tail/tie treatment and p convention must be frozen in the
future empirical registration before any draws. No draw is authorized here.

The proposed full-index, per-symbol, nonzero circular shift A is explicitly
**not adopted for inference or execution**. Independent review finds that it can
make every draw unavailable on a sparse changing universe and that independent
nonzero shifts need not supply an exchangeable randomization law. A plus-one
p formula cannot establish calibration. Available-only offsets, compressed
observations, altered cohorts and alternate blocks would change the null and
are not fallbacks. A remains a blocking inference-design dependency: a separate
pre-outcome justification must preserve the registered question, explain the
transformation law and temporal/dependence assumptions, retain all 500 draws,
and pass independent review before any empirical draw. Holdout data cannot be
used. No source or financial success may be inferred from a conditional placebo
screen alone. The [null/endpoint review](reviews/value-rev-null-endpoint-preparation-review-20260915.md)
retains the considered proposals and invented sparse-vector counterexample.

This is a deliberate documented deferral of a scientific assumption, not an
unmentioned implementation default. Building a financial engine now would not
resolve the outstanding provider semantics, historical availability and event
funding. The finite pure helper work is complete; further code is deferred until
an admissible source/inference contract supplies a concrete implementation target.
