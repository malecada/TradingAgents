# Current-owner sample artifact admission

The isolated route joins one explicit first samples_complete event to the actual
registered OwnedJournal, live FeatureJournal and admitted workload. Both the
selected execution job and producer must name the same registered artifact-read
policy. Event hash, owner, claim, start, graph population, workflow and policy
references are checked. Historical sample reuse is refused; the current owner
must have no parent. The complete current event inventory is bounded and checked;
unknown entries, terminal markers (including dangling links), extra sample events
and changed live journal state are refused.

The strict component reader admits an array-backed sample record. Legacy numeric
JSON lists are rejected. Native float64 node/edge features and int64 edge indices
must have the required ranks and compatible dimensions, and every declared array
must occur exactly once in a numerical graph field. Policy limits are registered
before fixture execution. Half the array allowance is passed to the reader to
reserve the other half for immutable AttributedGraph payload copies. This does
not bound Python metadata, graph validation scratch, process RAM, physical workflow
storage, repeated verification I/O or elapsed time.

After bounded loading, the existing actual workload route validates sample
configuration/order identity, the complete training population and each induced
neighborhood against admitted resident parents. Detailed parent/record membership
and numerical graph checks happen at this stage, not before numerical loading.
An immutable receipt records exact event/component hashes, current owner and
workload scope. Its lease rechecks live and durable ownership, registered inputs,
source bytes, event state and component inventory/signatures. The repeated live
check includes FeatureJournal.directory. Arbitrary continuous filesystem changes
are not an atomic snapshot; immutable owner control remains required.

## Evidence and correction

red01 retained eight missing-implementation failures in 0.002 seconds. Initial
check01 passed eight tests in 63.227 seconds. Independent INITIAL_REVIEW withheld
acceptance for SAR1: FeatureJournal.directory was checked only at entry. Original
source/tests remain preserved. red02 reproduced both a redirect after sample_scope
and a redirect after receipt creation: two intended failures in 15.537 seconds.
The correction adds the directory equality to every repeated event check.

check02 CLOSED exit0: 13 tests passed in 201.698 seconds (session15036).
The expanded suite retains the original eight cases,
adds both SAR1 regressions, native dtype/rank/shape refusal before np.empty, live
parent and dangling terminal-link refusal, and twelve changed-state boundary
subcases. Those twelve inject directory, terminal, event, policy, inventory or
stored-parent drift immediately after reader.read_component or Route.sample_scope
returns; they do not inject inside those routines. Internal read drift is covered
separately by the previously accepted strict-reader suite. No older test identity
is rerun. The exact command is PYTHONPATH=. .venv/bin/python -B followed by this
directory's test_route.py, with each run retained in its uniquely named log.

The fixtures use real temporary Git registration, ResearchRun, FeatureJournal,
OwnedJournal, three sampled neighborhoods and immutable saved numerical arrays.
Kernel guard observations are mocked. No empirical data are read; admission makes
no sampler draw or pair reservation. The fixture's published draw is synthetic.
Direct bindings are evidence for this component, not a complete empirical source
closure or a replacement broad offline-suite receipt.

## Remaining requirements

Sampler source/RNG provenance, a registered bounded producer that publishes this
array-backed format, failed-owner sample reuse, dictionary/MCM publication and
complete representation reuse remain required. Actual outer dictionary execution
must derive pair purposes; a receipt or scope alone cannot authorize arbitrary
caller-supplied purposes. Mapped full-fold operation, measured resource feasibility,
whole-workflow physical quotas, orphan reconciliation and scalable leases remain
separate work. No scientific configuration, financial trial, empirical attempt
budget or historical result changes here. All 1,420 financial fits remain pending.
