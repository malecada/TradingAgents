# Independent corrected component review

Accepted for current-owner, in-process saved MCM admission with the separately prepared, locally issued dictionary prerequisite. MA1 and MA2 are resolved in the reviewed source and saved evidence. No remaining material blocker was identified within this scope. Cold-start, historical, mapped and empirical admission are not released.

## Exact evidence

All 256 final bindings match current bytes, including all 237 inherited entries unchanged. Final manifest SHA-256: `b1bf4e75249a49ea77ff37d447ee821f85c66bff1a40654b6dac313621ec1fb1`. All 240 frozen test-source bindings also match; `check02-sources.json` SHA-256: `6ac8c63340866c3ee73762882bbb9403ce73c3399a44b3b68e9e9a5c2b711c46`. These bind declared component/dependency evidence, not a complete empirical execution closure.

Reviewed current source/test SHA-256 values:

- `route.py`: `88482b62d4bdb86ea9fabba2da0b4e36955084c03866766d16300d98da508070`.
- `test_route.py`: `5f17a5bfb91bca604f3ee6083edf269efca386f7903ce39be6e0e70a56a1761f`.
- `test_values.py`: `bb0d02e92e0d5e5152460b9f7ccac3587839aa05bdd90e51bc517b5677d42887`.

Saved `check02.log` reports ten methods passing in 764.785 seconds, SHA-256 `018e08cf6c90c36eb4ebd202d00191513691a8a3a5ed6b63b2ef6bdfd354eda9`. Saved `value-check01.log` reports two methods passing in 2.230 seconds, SHA-256 `048e5adf77b80c7c074e22ab817c4d36197cc6a1f8be1d68e5e2c61bc3b059a9`. No reviewer rerun was performed. The import-error evidence, missing implementation failures, interrupted original integration run and reproduced MA1/MA2 failures remain preserved; the interrupted run is not counted as green.

`INITIAL_REVIEW.md` remains unchanged with SHA-256 `3847a0a0753bdaa3c4a3bd40123a3f3a42d244828c8c436e44f336eb579e1788`.

## Corrected boundaries

MA1: admitted values now reside in an independent immutable bytes-backed float32 matrix. Receipt properties and backing attribute assignment are blocked. Shape, strides, dtype and writeability are checked before and after evidence leases. The read policy reserves two full payloads plus five bytes per validation-chunk entry before loading; the writable reader matrix is released before final admission. Tests cover writes, writeability re-enablement through the matrix/base/view, replacement, shape/stride drift, insufficient copy allowance and source-independent copying. Chunked validation rejects nonfinite and out-of-range values, including the final element; zero remains valid.

MA2: earlier embedding/completion checks now apply to the selected graph, while earlier representation completion remains globally disallowed. The regression publishes and admits another required graph after first-graph stage events. Those embedding/completion payloads are placeholders: the test establishes event-order compatibility, not their numerical correctness.

Local dictionary tickets are issued only after the predecessor's actual admission. Registry membership and exact owner/journal identity are required; receipt dictionary, record, callback, class lease function and preparation input names/hashes are pinned. Dictionary identity/configuration and matching identity are recomputed around the original lease. Forged constructors, copied receipts, cross-owner/journal use and replaced prerequisites are covered by refusals.

Saved admission checks selected policies, exact proof/start/source/event/component joins, required graph membership, node/motif order, workload/dictionary provenance, row/cell/byte counts and unique selected-graph MCM events. Strict component inspection precedes loading. Compact evidence checks surround the prerequisite lease and follow the immutable conversion. Tests cover conflicting markers, corruption before loading, rehashed false provenance/count/order claims and post-read/later drift.

Positive reuse tests forbid fresh dictionary admission, driver/kernel/workload numerical entry points, Serial and PairSession creation/resumption, and both neighborhood extraction APIs. Pair reservations remain unchanged. Initial ticket preparation is outside that forbidden region and may reconstruct sample membership and load dictionary/sample data.

## Scope and untested claims

The evidence uses tiny actual registered publications with mocked guard observations. It does not establish process RSS, physical quotas, aggregate retained receipt accounting, mapped populations, full-fold feasibility, historical continuation, sealed-run reuse or a Python process-security boundary. Parent graphs, ticket-held sample/dictionary data and previously returned matrices require separate resource accounting. Repeated leases do not provide atomic protection against continuous concurrent mutation.

Hash/provenance and finite-range checks admit the retained output; this component does not independently recompute matching scores or certify downstream representations. No new financial trial, empirical budget consumption or scientific configuration change follows from this acceptance. Review activity read source, compact logs and declared compact-file hashes only; no tests, historical jobs, empirical arrays, raw bodies or SQLite stores were read or executed.
