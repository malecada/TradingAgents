# Independent isolated normalization implementation review

September30,2026. Static source, pinned-library reasoning and saved synthetic receipts only; no tests/probes, empirical body reads, source edits or production execution.

**Accept as an isolated C-order scratch-state prototype within its declared limits. No material defect was found in the reviewed phase/capacity logic. This is not durable checkpoint or production-policy approval.** The earlier counterexample and investigation remain unchanged.

`create` requires nonempty two-dimensional C-contiguous float64 Q, finite/nonnegative values, positive finite beta, enough declared output bytes and a full-axis/padding entry allowance. It rejects detectable beta×Q overflow before output allocation. Input validation itself scans Q and allocates masks; those costs are explicitly outside the output/native-call bounds. The separate zero-initialized output avoids uninitialized checkpoint-like suffix contents. The caller must keep Q immutable and exclusively owned; the module does not hash, freeze or revalidate it at each call. Only unmodified create-generated states are supported.

The four phases preserve dependency order: scale every entry, normalize complete rows, normalize complete columns, then exponentiate. Maximum row block entries are floor(cap/m)×m≤cap. Maximum ordinary column block entries are floor(cap/n)×n≤cap. For originalm>1, create requires cap≥2n, so a singleton tail's duplicated n×2 scratch fits the stated native-input count. Originalm=1 follows the singleton reference path. Flat multiply/exp slices also have at mostcap entries. C-order validation is substantive: the separate padded diagnostic has Fortran mismatches. Arrays simultaneously held by SciPy and transient/persisting padded locals are not bounded by this entry-count contract; it is not a total scratch, RSS or wall-time cap.

Within `advance`, state is marked unsafe before any mutation; data and cursor/phase advance together before a successful safe return. Escaping BaseException leaves the state poisoned. The initial phase/cursor checks prevent the obvious negative/end/out-of-range cursors. There is no save/load, serialization, restart after process death, adversarial state validation or input identity proof. Completed blocks are merely in-process return points. If integrated with annealing, old M must remain available through every edge update before normalization may overwrite it; this independent prototype does not implement that integration.

## Saved numerical evidence

The padded diagnostic contains1,152exact-value comparisons: C order0 row/column/final mismatches; F order16row and45column/final mismatches. `np.array_equal` in that diagnostic does not distinguish signed zero and is not byte identity. These fixtures are random/wide/ties/zeros and do not constitute a universal parity proof. Their aggregate records and probe hash reconcile.

The new four-test saved log reports **4passed in0.040s**. The normalization test exercises60finite nonnegative C-order cases: five shapes, three input constructions, two beta values and two allowances. It compares final literal output bytes against the pinned whole-matrix scalar normalization. Every advance call uses max_blocks1 and checks safe state, and phase traversal is checked. It does **not** compare an independent intermediate oracle after every return, serialize/restore a state, or exercise a full matching solver. Additional tests prove a post-write multiplication interrupt poisons the state, ordinary inputs remain unchanged, and selected layout/capacity errors occur before output allocation.

The retained red log is a missing-module setup error, not four independent behavioral failures. No near-overflow, negative/nonfinite/type-rejection matrix grid, signed-zero byte probe, every-phase interruption, native-call shape instrumentation or actual agreement-derived full-solver trace is demonstrated. Static inspection supports the cap and shared exception handling; these remain specific useful tests before broader integration rather than claims already tested. The module does not enforce NumPy/SciPy versions itself; this acceptance is scoped to the currently pinned environment and reviewed source.

## Concrete next engineering boundary

The prototype supplies bounded-call normalization return points with demonstrated final-byte parity on the listed C-order fixtures. A next integration should add explicit normalization phases to the isolated annealing state schema, input/config identity and durable save/load of consistent boundaries, then compare uninterrupted/resumed complete scalar matching results and exact iteration state. It must retain original capacity checks and independently budget SciPy temporaries/whole-axis calls under an outer guard. No accelerated/Torch substitution, empirical capacity relaxation or financial release is justified by these four tests.

Reviewed identities:

- normalization.py: `6d7154d0e09548a31478273d31535aedef258375b0b1fe45be1447e4338377fe`
- test_normalization.py: `0b218595690d1899cc62d02cb175fe76a9621776ccba89c8f1c502bb2aefc6d6`
- normalization-green01.log: `119eb158af9c8a17b35e94789e871de6f57880473f2db9e480f799d8e7a49d2d`
- probe_padded.py: `eb76d8a4ee58793e6b00923354fa9e3a31a1c4eeed530024df1d812cd17484d1`
- padded-result.json: `5c32f6a9b97523faf505a51c73ed64f0155f70a1e53c36a40e12c7e52ee368be`
