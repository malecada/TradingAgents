# Exact metadata denominator for representation closure

This pure metadata component validates every daily decision slot from fold
training start through test end against the complete ExampleManifest. Included
train/test rows and explicit exclusions must form a unique complete partition;
both included sequences and exclusions must remain chronological. Rehashing a
truncated or duplicated manifest does not waive the full calendar requirement.
An explicit maximum calendar-day count bounds this enumeration.

The caller supplies an externally admitted full-manifest hash, fold, lookback
configuration and exact graph population/required union. This component does not
itself establish their registration or raw-data provenance. Graph inputs are
CalendarGraph metadata, not loaded arrays. Weekly Monday boundaries, seven-day
intervals, at least the frozen one-day publication lag and raw-source membership
are checked. Every included lookback position must use the exact expected week
and a graph available at that input step, not merely by the final decision.
Input dates, label interval, maximum input clock and partition boundaries must
match the frozen calendar conventions.

Calendar-driven exclusions are replayed, and missing/late graph exclusions are
checked against the actual metadata lookup with the maintained precedence.
Warmup/missing-price exclusions remain explicitly recorded but are not revalidated
without admitted price membership. The result marks price_exclusions_revalidated
false. It reports all calendar/test days, included rows and every exclusion reason;
passing this accounting check does not establish complete price/history coverage
or permission to drop dates from a registered experiment.

The test fixture uses five literal dates, two weekly graphs and a two-day lookback
for engineering only. It does not change the paper's registered 28-day lookback.
red01 CLOSED five missing-component failures in0.002s. check01 CLOSED five methods
with two errors in0.020s because a datetime was passed to the existing string-only
expected_week API; original source/test/log retained. Corrected code passes a
canonical timestamp string. check02 CLOSED five passes in0.015s. Additional graph
exclusion/purge branch coverage justified check03, which CLOSED seven passes
in0.026s; the previous test version is retained. No production source changed
between check02 and check03. These are new synthetic test identities, not reruns
of historical empirical work.

Cases cover full accounting, rehashed missing/duplicate/reordered dates,
per-input future graph use that would pass a final-decision-only clock check,
lookback/label/exclusion-partition/population/cap refusals, preserved price
exclusions with no false price claim, exact missing/late graph exclusions and a
purged training label retained in the denominator. No raw numerical market data,
model fitting or trial budget is consumed.

Still required: actual registered current-owner linkage to this validator,
exact equality of caller fold/configuration/graph metadata to admitted sources,
all required graph completion receipts and leases, whole-workflow physical and
resident accounting, durable representation closure and admitted top-level reuse.
