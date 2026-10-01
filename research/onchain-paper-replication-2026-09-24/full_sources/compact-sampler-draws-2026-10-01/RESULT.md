# Compact sampler durable draw adapter

The maintained `compact_sampler.py` uses an actual admitted compact Training
route and its live compact Owner. Both registered execution job and producer
plan must select `compact_sampler_input`; its exact input hash, training receipt,
Binding hash, configuration, training graph order, seed and NumPy version are
retained in the start and completion metadata. The preserved leased sampler
core is separately required in committed source admission and rechecked at full
boundaries. Sampling semantics are unchanged.

The first attempt reserves `(sample_count + 3) * max_metadata_bytes` before
creating an exclusive namespace. This covers the start, every draw, completion
and a possible failure receipt together. The metadata cap is at most 2 MiB;
center, direct-weight and neighborhood/sample-array limits are explicit. Complete
receipt size is preflighted. These are logical metadata and selected numerical
array bounds, not measured RSS, physical filesystem use or a whole-workflow quota.
The existing outer resource guard remains required.

Each draw records the kernel's ordered training population, exact configuration,
selected center/probability, selected-index hash, retained numerical bytes,
previous-event hash and RNG state before/after. The adapter checks the chain and
one-uniform PCG64 transition, exclusively writes and fsyncs each acknowledgement,
and verifies all acknowledged files after the last live-owner callback. A failed
write or lease preserves the namespace and poisons the owner. Existing incomplete,
failed and complete namespaces cannot be relaunched. No resume API is provided.

The completion receipt additionally pins the resident SampleManifest and every
attributed graph's numeric bytes, node order, parent and center through the
existing bounded `matching_identity.graph_identity`. Returned public views are
read-only; full checks rejoin registered training/source boundaries, exact saved
files and resident samples. Full metadata verification is repeated callback-free
after the last lease. This introduces repeated bounded reads of retained draw
metadata; its full-size cost still needs measurement.

## Retained checks and corrections

All inputs are synthetic temporary ResearchRun registrations with actual source,
input, Binding and compact Owner joins; only kernel guard surfaces are mocked.
The training fixture retains two supplied train and two test examples. Complete
calendar/price/label provenance is not established by that fixture.

| Identity | Outcome | Evidence |
| --- | --- | --- |
| red01 | 1 missing-module failure, 7 fixture errors, 24.02s, session71428 exit1 | `red01.log`, `test-red01.py` |
| red02 | 1 missing-module failure, 7 deselected, 15.89s, session89668 exit1 | `red02.log` |
| check01 | 3 failed, 5 passed, 139.27s, session14365 exit1 | `check01.log`, `sampler-check01.py`, `test-check01.py` |
| red03 | 1 failed, 8 deselected, 19.95s, session60622 exit1 | `red03.log` |
| check02 | 4 passed, 5 deselected, 92.78s, session53264 exit0 | `check02.log` |

Red01 exposed an engineering fixture error: the copied dated core was not staged
in the temporary research commit. That fixture was preserved, corrected and the
fresh red02 reached actual admission before reporting the missing implementation.
Check01 exercised all then-current cases: four preflight refusals and interrupted
write preservation passed; the three positive-publication cases failed because
the initial sample fingerprint used the weekly GraphSnapshot hashing API for
AttributedGraph samples. Independent REVIEW_INITIAL identified the same mismatch
and a missing callback-free acknowledgement check.

Red03 injected draw-file corruption from the owner callback immediately after
the first draw write. Before correction, the sampler reached draws 1 and 2 after
the corrupted draw 0. The fix checks exact written-file hashes, inventory and
pinned root after each callback before returning to the kernel. The attributed
identity fix includes all numerical sample bytes; the positive check compares
actual arrays, identities and records with the existing sampler directly.

Check02 verifies all three corrected publication cases plus the acknowledgement
regression. The five earlier passing refusal/interruption cases were not repeated;
no combined final-source nine-case run is claimed. All checks are terminal.

## Remaining interfaces and claims

This is durable **draw evidence with a live resident result**, not durable numeric
sample publication. Both `numeric_artifact_published` and
`sample_provenance_admitted` are explicitly false. Single-uniform RNG transitions
do not independently prove the overlap-weighted probabilities or induced graph
contents; they are linked here to the admitted unchanged kernel. The positive
fixture checks exact agreement with the existing sampler, not an independent
probability oracle. Existing independent sampler oracles remain separate.

Next publish the sampled numeric arrays with bounded preflight and the strict
component reader, join their identity and saved draw evidence to the current
training route, and provide the explicit scientific proof consumed by the compact
dictionary producer. No arbitrary SampleManifest can replace that join. Then
complete dictionary/MCM/feature closure and explicit native selection, physical
whole-workflow resource reservations and reviewed committed resource amendment.
Coverage remains 77/109; all 1,420 financial fits remain pending.

Independent [corrected review](REVIEW.md) accepted this bounded contract;
initial findings remain in [initial review](REVIEW_INITIAL.md). Final review SHA:
`e46eaa1fcb68f8a7f38c24e699c8b8bd9eb5ce2afdc7a26cef98253b0e0aad3a`.
