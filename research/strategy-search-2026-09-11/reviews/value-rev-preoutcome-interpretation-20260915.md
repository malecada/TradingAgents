# Independent pre-outcome interpretation — value_rev

September 15, 2026. The source-stability question remains eligible for offline
readiness work. **No P0 result or second-vintage capture is admitted by this
review.** The original September 4 charter and `data/rebuild/gates.json:value_rev`
remain unchanged. Explicit requirements can be restored in a new implementation;
the unresolved choices below need a separately committed, independently reviewed
clarification before observations or evaluation. The proposed choices are not
represented as clauses already present in the original registration.

Only the coverage review, charter, the named gate object and source code were
read. No raw response, normalized panel, P0/P1/P2 output, ratio, return or ledger
outcome was inspected. No network call or legacy main was executed. This review
owns only this document.

## Material findings and requirements already explicit

1. **Protocol-day identity is mandatory.** Charter lines 34–36 specifies common
   protocol-days; `scripts/value_rev_dev.py:65–77` instead joins token panels and
   calls their rows protocol-days. `scripts/fetch_defillama_fees.py:121–123`
   sums several protocol series into each token. Two invented protocols changing
   from 100/100 to 120/80 leave their token sum unchanged, although both protocol
   observations changed by more than 10%. Restore raw protocol identities before
   comparison; token aggregation belongs only to the later registered factor.
   Preserve each eligible observation's identity and the complete union/common/
   exclusion denominator. The strict `>10%` comparison and inclusive `<=5%` gate
   remain unchanged; no token weighting or pooled-token denominator is allowed.
2. **Labels cannot establish elapsed retrieval time.** `value_rev_dev.py:59–62`
   checks caller-supplied labels; `fetch_defillama_fees.py:72` records a start
   timestamp before requests, and writes its manifest only at line 128. The
   charter's fourteen-day gap concerns actual snapshots. Checking actual clock
   eligibility and binding exact first/second vintages restores that requirement.
   The first start timestamp does not establish first completion or each
   member's retrieval time. September 18 is an earliest calendar date, not an
   independently proved eligible instant for the complete pair.
3. **Missing data cannot become an observed zero.** `fetch_defillama_fees.py:108–123`
   omits failed metrics and uses a sum that can turn all-missing observations
   into zero. `value_rev_dev.py:93` then fills missing days with zero before the
   90-day sum. Neither operation is licensed by the charter. Missing/failed,
   absent and observed numeric zero must remain distinguishable. Complete
   trailing 90-day economic quantities require supported daily constituents;
   no unobserved prehistory or unobserved protocol contribution can be assigned
   a zero merely to create signal breadth. The exact constituency/zero/gate
   handling still needs the clarification below.
4. **A stage must prove its own admission.** `value_rev_dev.py:117–120` accepts a
   mutable truthy `pass` unrelated to the supplied first vintage; lines 139–144
   accept an equally unbound probes file. A file from another pair or altered
   raw store can therefore authorize the grid. Bind immutable stage results to
   the registered identity, source-code/policy hashes, full admitted input
   inventories, exact vintage pair and preceding stage digest. Refuse mismatch,
   incomplete stage, non-Boolean verdict, existing terminal or repeat intent.
   Retain failed/unavailable attempts. This restores the named experiment's
   ordered gate; it does not require changing a numerical threshold.
5. **Blocking means no later probe after a failed predecessor.** The charter
   explicitly says P0, P1 and P2 are blocking and ordered. At
   `value_rev_dev.py:128–133`, P2 is evaluated even after P1 failure. Stop before
   P2 when P1 fails. The grid cannot follow P0 alone or a failed/unavailable P1.
   A measured lag above two days may follow the charter's explicit logged
   pre-grid widening route; a silently changed global constant or the current
   unconditional P2 stop is not a complete implementation of that route.
6. **Original bytes remain immutable.** The fetcher checks only the normalized
   output directory at lines 68–71 and uses ordinary writes at line 75. A raw
   directory left by an earlier incomplete invocation can be overwritten when
   the normalized directory is absent. New source admission must refuse an
   occupied vintage/output namespace and preserve all prior files and failures.
   A portable read-only root mapping is acceptable; silent refetch or replacement
   of the preserved worktree is not.

These are source-code observations. Their effect on actual results has not
been measured. Source presence, successful decoding and stable revisions alone
do not establish historical first-publication availability.

## Conservative proposal requiring separate registration

### Protocol, metric and denominator

Freeze a first-vintage raw-manifest inventory and its protocol-slug-to-token
mapping before second capture. Request the fixed first-vintage protocol/metric
recipe; record later listing/mapping changes separately without adding or
substituting protocols after seeing responses. Preserve every requested member,
status, raw hash, byte count and decoding outcome. A missing member, conflicting
identity or invalid response is source-unavailable, not a zero series.

**Proposed metric rule:** compute two separate P0 results, dailyFees and
 dailyRevenue, each on unique common `(protocol identity, UTC economic day)`
observations for that metric. Require both results to pass before the four-cell
family proceeds. Do not pool fee/revenue rows or select whichever metric passes.
The original grid has both metrics but does not spell out this joint P0 rule;
fees-only code is not enough to infer the intended revenue admission. Each
metric keeps the original `changed/common <= 0.05` threshold and each change
keeps the original strict 10% boundary. Zero common observations are unavailable.

Retain counts and identities for all requested protocols, each vintage's eligible
days, common days, first-only deletions, second-only additions, explicit zero,
invalid/negative/nonfinite values, duplicate timestamps and excluded recent days.
Do not silently merge distinct slugs, overwrite duplicate timestamps through a
Python dictionary (`fetch_defillama_fees.py:113`), or deduplicate conflicting rows.
A first-only historical observation is an explicit absence; an ordinary common-
day stability result cannot establish stability of that disappeared observation.
**Proposed conservative admission rule:** unresolved deletion of an eligible
first-vintage observation blocks a full-family source pass as unavailable, rather
than reducing the denominator and letting an apparently stable subset proceed.
This additional completeness rule must be registered explicitly. It is not a
new numerical restatement threshold hidden in implementation.

**Proposed zero rule:** for finite positive baseline `a` and finite nonnegative
second value `b`, classify a change exactly when `abs(b-a) > 0.10*a`, avoiding
floating-point division at the boundary. An explicit `0→0` counts as unchanged;
an explicit `0→positive` counts as changed, with percentage change recorded as
undefined rather than a fabricated finite value. `positive→0` is changed.
Negative/nonfinite/missing values are invalid or unavailable, not dropped as
stable rows. The original code's positive-baseline filter at line 67 does not
settle these conventions; all-zero source rows must not be assumed meaningful
without source admission. The proposed zero handling is an explicit extension
of the undefined mathematical baseline case, not an assertion that division by
zero has a percentage value.

For later token sums, freeze required protocol constituents per token/metric;
require each required constituent to be observed on every included economic
day. An absent protocol before inception is unknown unless a pre-registered
source rule establishes zero activity. Do not infer inception from the first
nonmissing returned point. Sum only admitted daily values and require all 90
calendar days; positive aggregate denominator, supported market cap and all
other signal conditions determine validity. No additional market-cap source,
forward-filled publication history or substitute circulating-supply estimate is
introduced. The fixed-constituency choice and its treatment of historical
inception require explicit registration because the original sum clause does
not define them.

### Days and actual observation clock

The charter says economic days **ending** at least thirty days before snapshot
one; the current `index <= cutoff` does not prove this if timestamps label day
starts. Provider timestamp semantics were not verified in this review and must
remain unresolved until supported by source documentation or an admitted schema
contract. No network documentation search was performed.

**Proposed calendar convention, conditional on that source support:** timestamps
must identify unique UTC daily intervals. Compare interval end to a frozen
first-snapshot reference, not its start label. Use September 4, 2026 00:00 UTC as
a conservative first-snapshot cutoff reference, so a day beginning August 5
would not be included merely because its start equals the thirty-day cutoff.
Do not round non-daily timestamps or interpret future-dated points as timely
observations. This conservative cutoff reference and interval convention need
registration before P0; the numeric thirty-day requirement stays unchanged.

Find a trustworthy upper bound `B1` on completion/existence of all exact
first-vintage bytes without inspecting economic values. A contemporaneous
immutable archive/commit or retained completion evidence could supply it;
ordinary filesystem modification time or the manifest's start time cannot.
Require every second-vintage request start to be at least `B1 + 14 days`.
If an earlier completion bound is unavailable, a new independently timestamped
hash inventory provides a conservative later bound, making the second capture
eligible fourteen days after that later observation. This preserves existing
first-vintage bytes; it does not restart or retake vintage one. Merely adding
fourteen days to September 4's acquisition start is insufficient for a complete
per-member gap claim. Record request start/end and response/controller receipt
bounds for vintage two, fixed attempt/resource budgets and an immutable
completion seal. Actual date labels must be derived from those receipts.

### P1, P2 and the later grid

**Proposed P1 rule:** report median weekly signal-valid counts separately for fees
and revenue on every scheduled dev-window Monday, including zero-valid weeks,
and require both medians to be at least twenty before this four-cell grid may
proceed. `any(metric)` at `value_rev_dev.py:128` could admit revenue cells that
fail breadth merely because fees passes. The charter does not state any-versus-
both or authorize dropping the failing metric's two cells. Requiring both is the
conservative proposal; it needs registration and does not reduce the trial count.

**Proposed P2 rule:** inspect each required protocol/metric's latest valid economic
day, not a token frame's latest shared index. A current fee point with missing
revenue cannot prove revenue availability. Missing, malformed or future points
are unavailable. Define lag in the same frozen UTC interval/calendar convention
as P0 and require the worst lag across required inputs to be covered; a median
can hide half the input series. Metric coverage, required scope, maximum versus
median and rounding must be registered. The original charter explicitly names
the fee series; extending the same admission to revenue is a clarification.

For finite supported lag above two days, the charter permits a logged widening
before the grid. Freeze the deterministic common lag rule in advance (for example,
maximum of two and the ceiling of the greatest required delay), log the measured
widening once, and revalidate P1 at the final lag before any grid computation.
An unknown lag cannot be cured by a large chosen number. Whether first-vintage
or second-vintage latest points define this P2 check must also be fixed; the
conservative proposal uses the bound first vintage used for factor inputs,
with second-vintage lag as separately labeled source information. Neither
latest-point statistic demonstrates publication delay for historical dev dates.

Bind P1/P2 to the same first-vintage inputs that passed the exact P0 pair, not a
more favorable later panel. Any authorized widening binds a new immutable
pre-grid policy reference and predecessor chain, not an overwritten prior result.
Ordered stages remain P0 → P1 → P2 → any logged deterministic lag correction and
P1 revalidation → grid. No financial computation is authorized until this
clarification and full source/engine admission are complete.

## Preserved criteria and limits

Preserve the four metric/breadth cells, 90-day window, Monday schedule, 10 bp per
side, realized funding, 4.5% full-capital annual risk-free charge, simple-return
accounting, identical control pipelines, original ordered numerical gates,
500 draws for each placebo family, DSR own-grid n=4 and cumulative trial
accounting. No sample, metric, breadth, market-cap source or threshold is chosen
after looking at outcomes. The historical H1 label is retained as a registration
fact; this review does not independently prove virgin availability or eligibility.
A P0 pass is a bounded revision-stability finding, not complete PIT safety.

The whole financial engine was not audited here. One directly visible deferred
issue reinforces the requirement for a separate pre-grid audit:
`value_rev_dev.py:156–160` constructs both controls at decile breadth while the
grid also contains terciles; the charter requires identical pipelines. No
control, return or funding result was computed to assess its numerical impact.

The next justified implementation is pure synthetic protocol-level source and
stage validation, with cancellation, missing metrics, zeros, exact 10%/5%
boundaries, duplicate days, forged labels, wrong pairs and prior-stage mismatch
fixtures. The separately committed interpretation must precede any second
capture or actual P0. No extra factor-family trial or new empirical allowance is
created by this document.
