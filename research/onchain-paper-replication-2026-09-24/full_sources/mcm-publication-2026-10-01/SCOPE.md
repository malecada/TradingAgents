# Current-owner per-graph MCM publication

This isolated publisher consumes the accepted bounded resident MCM computation
and publishes one exact required graph to the actual FeatureJournal. Its derived
driver retains the combined dictionary/source/policy/owner/graph lease closure
through publication. This avoids loading a second sample/dictionary receipt.
No scientific setting, matching purpose, node/motif order or score changes.

The selected producer plan and execution job must agree on mcm_output_input.
Its schema-1 policy bounds metadata, manifest, encoded artifact, reserved attempt
and numeric MCM array bytes. The logical reservation is four metadata ceilings
plus the artifact ceiling: start, complete, failed, one event and its component.
This is per-attempt logical accounting, not a physical quota, aggregate workflow
reservation or process memory bound. Existing parent population, pair journal,
sample/dictionary receipts, prior outputs and partial storage remain separate.

Before computation the publisher checks required graph membership, output entry
and numeric capacity, selected policy/reservation, available journal event count,
no prior numerical progress for this graph and an unused event/component slot.
An exclusive attempt directory is keyed by workflow, current experiment and graph.
An existing attempt refuses regardless of its partial/failed/complete status.
Other graph attempts have distinct paths; this does not grant concurrent mutation
of the shared feature journal. Historical owners and ancestry remain rejected.

After actual computation the retained receipt is leased and complete shape/type,
bytes, rows/cells and dictionary proof are joined. The actual encoder's predicted
manifest/artifact/numeric size and lifecycle event encoding are checked before
any feature write. The full float32 MCM is recorded as mcm_progress with next_node
equal to the graph node count. The proof distinguishes this complete MCM from a
completed graph representation, which still requires neural/representation work.
Its event context and completion sidecar bind node order, ordered motif identities,
dictionary provenance, matching workload, registered MCM policy and output policy.

The output is independently inspected using the strict component reader. Exact
inventory/signatures are retained for final compact checks after the receipt and
owner checks. Failures preserve attempts and attempt a bounded failed sidecar.
A late complete-plus-failed conflict is intentionally retained and must be refused
by future admission. Existing identities cannot be retried to overwrite failure.
Publication alone does not admit this output for saved reuse or historical work.

Tests use real temporary registered owners, three sampled graphs, two dictionary
motifs, actual checkpointed scalar matching and a two-node required graph. Kernel
guard observations are mocked. No empirical bodies, financial fits or historical
jobs are executed. Every output cell is independently computed using the scalar
oracle after strict saved-array loading. Additional cases cover completed/partial/
failed relaunch refusal, route/reservation/numeric/event preflight, artifact cap
before feature writing, dictionary drift after computation and output drift during
completion. red01 is closed: six methods/nine missing-publication failures in
0.003s, session45112 exit1. check01 CLOSED six methods in357.516s, session61740 exit1, with one error
(float32 rejection) and one failure (completion drift never reached). Initial review withheld acceptance for MP1: the reused sampler sizing function
rejects float32, so normal MCM publication currently fails before feature writing.
The failed source, original negative artifact-cap test (which accepts an unrelated
ValueError) and closed attempt evidence must be preserved before correction.
The correction will use a local float32-only predictor and exact serialized-byte
checks; the historical sampler helper must remain unchanged.

Next: exact current-owner saved MCM admission/reuse without numerical APIs, then
historical continuation/mapped populations/full-workflow accounting and measured
resource admission. All1420financial fits remain pending.

MP1 correction: original publication.py/test_publication.py retained as .check01.
The local sizing helper now accepts only native nonempty float32 matrices and
predicts one numeric component, with no broadening of the sampler helper. New
size-red01 closed two methods/six failures in1.018s; size-check01 closed two
methods in1.130s. Predicted manifest/NPY/total bytes equal actual component writes
for C, Fortran, strided, reversed and one-cell layouts. Wrong dtype, rank and
empty payloads refuse. The artifact-cap test now requires the intended allowance
error. Corrected integration check02 CLOSED six methods/nine expanded cases in367.376s,
session17402 exit0. All actual publication, independent scalar-cell equality,
exact encoded-byte, preflight, attempt-refusal and dictionary/output drift cases
pass, including the qualified artifact-cap check. No active job/source freeze
remains. Final independent review is pending.
