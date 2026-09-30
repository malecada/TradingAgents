# Initial independent sample-artifact review

Acceptance is withheld for a current FeatureJournal path-binding gap. Source and
saved evidence were inspected read-only. No test, job, empirical array read,
source change or commit was performed by the reviewer.

**SAR1 — the live journal directory is checked only at entry.**
`route.py:101` requires the passed FeatureJournal.directory to equal the admitted
owner directory. The repeated `events()` check at lines 104–128 verifies the
object's owner, parent, identity, required graph set and sealed status, but does
not recheck its directory. Consequently, changing this attribute during loading
or sample_scope, or after receipt creation, leaves every subsequent disk check
anchored to the old captured directory. Admission or receipt.lease can succeed
although the same FeatureJournal would publish future events elsewhere. This
breaks the claimed current live-object/durable-owner directory join.

Require `journal.directory == directory` in the repeated event check. Add a
synthetic regression that changes the actual object's directory during the
induced-sample check or after receipt creation and requires refusal. Preserve
the original source and test evidence before correcting it.

No other material source blocker was found in this inspection. The explicit
array-backed format correctly differs from legacy samples_to_record's JSON
numeric lists. Slot checks require native float64/int64 fields and exact ranks
and compatible shapes before materialization; every array must belong to a graph
numeric field. Half the registered array allowance is supplied to the reader,
reserving the other half for AttributedGraph's immutable payload copy. This does
not account for neighborhood-validation scratch or whole-process RAM.

The initial fixtures cover a real temporary first owner and FeatureJournal,
published samples, exact scope, legacy-list and budget refusal, wrong policy
route, wrong event/owner, duplicate samples, induced-graph tampering and later
policy/artifact drift. Saved check01 reports eight passes in 63.227 seconds;
that result does not address SAR1. Additional during-load/during-scope drift
tests were announced but not present in the inspected initial test source.

Inspected source SHA256:

- route.py: `702dcd26862f2476049356510c4e1fdc1454579994a74d62b5de99ac430838af`
- test_route.py: `707fbef9307541593e64d0979fe21b85b45e2c0f996c84a6a10935b2556c33ce`
- red01.log: `4ea8bd4779977e7af7a46b9b9790ea0b7dc606923dc87b670c871da05445ed43`

Registered production publication, weighted RNG provenance, historical reuse,
physical workflow quotas, mapped/scaled feasibility and empirical admission
remain outside this bounded component review. Kernel guard behavior is mocked
in the synthetic fixtures.
