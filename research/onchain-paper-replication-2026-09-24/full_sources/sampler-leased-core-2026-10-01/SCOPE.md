# Leased resident sampler core

This isolated prerequisite is derived from the existing sample_neighborhoods
resident path. It retains training filtering/order, unique centers, initial equal
mass, PCG64/NumPy choice, zero selected weight and overlap halving. Output identity
uses the unchanged training/configuration/seed/records/final-RNG formula.
No maintained source, frozen scientific configuration or mapped-weight policy
is changed. The prior 20GiB mapped-weight disk floor is untouched.

The existing producer cannot check ownership between draws. This derived core
requires a lease callback before numerical weights are allocated and before/after
each draw, with additional checks around index creation, evidence publication and
final return. It uses the accepted array-neighborhood implementation with its
explicit scratch allowance. Retained sample payload has a separate cap; that cap
is checked after constructing the next local graph, whose live scratch/output
copies are covered by the separate neighborhood allowance.

The direct weight cap covers exactly the retained weights and one probability
array (16bytes per candidate). The previous probability is deleted before the next
draw. This is not a peak allocation/RAM cap: NumPy choice's cumulative probability
scratch, parent inputs, offsets, Python metadata and validation need the outer
process guard and a measured resource admission. The component does not establish
scaled feasibility or alter the separately required empirical budget amendments.

Each completed draw emits immutable metadata containing training hashes, sampling
configuration hash, seed, NumPy/PCG64 identity, before/after RNG state, actual sample
record, selected-neighborhood index hash and retained-array count. Events form an
index/previous-hash chain. The caller's mandatory checkpoint callback receives each
event after a lease and is followed by another lease. Callback failure propagates
and closes the array-neighborhood index; no next draw or SampleManifest is returned.

These callbacks are not durable checkpoints by themselves. No attempt owner,
exclusive reservation, source/registered-policy admission, saved artifact, resume
API or current/historical sample-consumer provenance verification exists here.
The same function can be called again: the production wrapper must prohibit
redrawing any reserved/partial/failed/complete attempt identity. That wrapper must
write reserved→failed/complete disposition, enforce pre-write artifact capacity,
and bind its completion proof to exact sample event/component, registered policy,
source, owner and starting/final RNG evidence. Existing sample-artifact admission
does not consult a sampler sidecar and does not become provenance-aware merely
because this core exists.

## Evidence

red01 CLOSED: seven missing-core failures/0.002s. check01 CLOSED exit0:
seven tests/0.055s. Five seeds (11,23,37,51,71) each sample seven centers from two
training graphs, with a future graph excluded. Exact comparison with the maintained
sampler includes record probabilities/order, source hashes, local array bytes,
parent/center identities, final PCG64 state and complete sample identity. The
per-draw evidence chain is recomputed. Additional tests check pre-allocation weight
capacity and initial lease refusal, mandatory callback/policy types, retained-array
and hub refusal without truncation, callback-failure cleanup and lease expiry after
the first checkpoint stopping subsequent work. All inputs are tiny synthetic data.
No empirical data, actual guard, financial fit or historical rerun was executed.
Direct bindings are component evidence, not an empirical source/runtime closure.
