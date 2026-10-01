# Initial independent dictionary-publication review

Acceptance is withheld for two publication-boundary gaps. Source and fixtures
were inspected read-only while check01 was active. No tests, jobs or numerical
files were opened or executed by the reviewer. Only this review file was written.

**DP1 — dictionary component drift after inspection is not checked at return.**
publication.py:119–120 discards inspect_component's admitted signatures and exact
file inventory. The final lease at line 128 verifies sampler/sample artifacts
and event/attempt metadata, but not the new dictionary component's files. A
dictionary array or manifest can change, or a foreign component entry can appear,
during complete.json publication after inspection, and the function can still
return success. The author independently suspected this gap. Retain the component
signatures/inventory and recheck them after the last potentially long owner and
sample/proof checks before successful return. Add synthetic post-inspection
array, manifest and foreign-entry drift cases. Compact signature/inventory checks
are sufficient for the stated immutable-artifact boundary; no additional array
body read is requested.

**DP2 — the registered feature-event ceiling is not checked before adding the
dictionary event.** A valid artifact policy with max_journal_events=1 permits
the sampler's first samples_complete event. This publisher does not preflight
that ceiling, so it can execute the dictionary pairs and write event1 before the
sample receipt lease rejects the now-two-event journal. Check that the selected
policy admits the required second event before fit/attempt reservation. Add a
validly registered one-event policy case with driver.fit forbidden and verify
no dictionary attempt or new feature event appears. This is a known registered
publication constraint, not a deferred artifact-admission requirement.

The inspected numerical subset budget is otherwise conservative for its stated
scope: the sample reader allowance plus eight times the cumulative matrix-entry
cap is checked before fit; actual sample/matrix payloads are measured afterward.
Dictionary representatives reference existing immutable sample graphs. Output
NPY/manifest and lifecycle event bytes are sized before FeatureJournal writes.
The four metadata allowances account for start, complete, failed and the separate
event. These remain logical encoded/payload limits, not physical quotas or total
RAM, pair-workspace or clustering-scratch bounds.

The local driver preserves the accepted proof-required workload and adds its
internal admitted sample receipt to the returned result. Current fixtures target
scalar membership/representative/hierarchy parity, exact encoded bytes, retained
failure markers, duplicate/partial refusal and ownership/policy boundaries.
check01 was still active at this review; no passing-suite conclusion is made.

Inspected source SHA256:

- publication.py: `6ab2e2357d7d68660e5094ddb137d2363822aa5d66f281fb8e19bdf7b1347403`
- driver.py: `487da65650c7905a8c27fd7adab76084aa572f800959299077e034918a0e55aa`
- test_publication.py: `0dfd08cb20bdd1dac96817880b4e5bd9366b7c169ff0de2f258301af3f0f86ad`

Dictionary artifact admission, completed dictionary reuse without pair/workload
APIs, historical continuation, mapped/full-fold resources, MCM integration and
empirical release remain explicitly separate. The tiny three-sample fixture is
nonpartitioned and mocks kernel guard observations.
