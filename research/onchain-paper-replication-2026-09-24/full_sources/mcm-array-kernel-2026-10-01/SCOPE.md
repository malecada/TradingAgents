# Exact bounded array MCM

The isolated kernel replaces the legacy Python NeighborhoodIndex with the reviewed
ArrayNeighborhoodIndex. All complete induced neighborhoods remain required;
capacity failure raises without truncation. Node order, motif order, scalar
matching and float32 storage are unchanged. Pair purposes and workload identity
match the accepted scalar MCM workload byte-for-byte on the tested fixtures.
The pair callback must return an explicit purpose-bound finite score in [0, 1].
Missing, failed and zero scores remain distinct. No partial matrix is returned.
Completed rows and cells are counted and checked before return.

The exact schema-1 numeric policy has positive integer max_buffer_bytes,
edge_chunk, max_output_bytes and max_numeric_bytes. Output requires four bytes
per cell; the full output plus the entire allowed index/neighborhood buffer must
fit the combined numeric cap before allocating either. The index additionally
checks its conservative scratch envelope and each full neighborhood's numeric
output/copy allowance. An index context owns cleanup on success, score failure,
capacity refusal or lease failure. Each previous local graph is released before
extracting the next. Leases precede/follow extraction and pairs and precede final
return. Pair journal checkpoints remain the recovery mechanism: there is no
separate row publication or durable MCM reuse in this component.

The registered driver selects mcm_execution_input by joining the actual producer
plan and selected execution job, reads its exact admitted hash, and checks output
and combined numeric caps before dictionary loading. The dictionary artifact
route and exact required resident graph remain mandatory. Sources and selected
policy metadata join existing dictionary/owner/graph leases. The returned record
includes the selected input/hash, full row/cell counts, output bytes, graph/node/
motif order, workload scope and dictionary provenance. Completed pair replay
uses the actual Serial journal. No caller-supplied graph, numerical setting or
purpose bypass is introduced.

Bounds cover the output and the documented array-index numeric envelope, not
input populations, dictionary/sample receipts, callback pair workspace, Python
metadata, validation internals or total RSS. A callback that independently keeps
local graphs needs its own allowance; the actual Serial consumer closes its
pair sessions. Whole-workflow physical quotas, scalable lease cost, mapped input
support, historical continuation and measured resource admission remain required.
The policies here are synthetic fixture registrations, not empirical release.
No original sample count, matching cap, disk floor or scientific choice changes.

Evidence: kernel red01 CLOSED seven missing-kernel failures in 0.002s; kernel
check01 CLOSED seven passes in 0.200s. Tests compare every 7-by-2 cell and exact
ordered purposes against the scalar workload, including reversed dictionary
order; verify byte-cap/missing-lease refusal, no truncation, cleanup, partial-row
zero replay, no next pair after lease failure, local graph lifetime and invalid
score/purpose refusal. driver-red01 was interrupted (exit130, session11691)
after directly importing a unittest class accidentally discovered base tests.
Its exact test source and log are retained. The corrected module import yielded
driver-red02: seven methods/nine intended missing-driver failures in 0.003s,
session55586 exit1. driver-check01 CLOSED seven methods/nine expanded cases in 334.324s,
session62875 exit0. The actual registered fixtures compare every 2-by-2 cell to
independent scalar matching and forbid pair create/resume on completed replay
with unchanged reservations. Foreign graph, conflicting dictionary, post-first-
pair dictionary/policy drift and policy route/output/combined-cap refusals pass.
Guard observations are mocked; empirical guard/scale behavior is not measured.
No source freeze or active test process remains. Independent review is pending.
All 1420 financial fits remain pending; no empirical budget is consumed here.
