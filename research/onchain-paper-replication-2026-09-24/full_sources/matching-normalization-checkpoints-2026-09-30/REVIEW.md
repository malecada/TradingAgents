# Independent checkpointed normalization review

September 30, 2026. Source and compact saved evidence were inspected independently. No tests, empirical arrays, raw sources, SQLite bodies, remote transfers or production jobs were executed. Only this review was written.

**Accept for further isolated engineering within the stated scope. No blocking defect was found in this delta. This is not approval to replace the registered matcher or relax its capacity.**

## Arithmetic and state transitions

`annealing.py:69–122` preserves scalar node and edge traversal. Every edge contribution for an iteration reads the previous M; M is first overwritten only after Q is complete. Scaling finishes before row normalization, all rows finish before column normalization, and all columns finish before exponentiation. Beta and iteration count advance only after the last exponentiation block. Zero-edge graphs enter normalization without performing an edge division. The reference's original pair-capacity validation, hardening and scoring remain in use.

The normalization allowance is checked before creation or restoration of the three numeric matrices. Flat blocks contain at most the allowance; complete-row and complete-column block sizes use integer division by the corresponding axis length. The two-column padding for a singleton tail fits because wider original matrices require an allowance of at least twice the row count. Original single-column matrices retain their distinct reduction path. These conclusions concern the pinned C-order scalar implementation. Earlier Fortran-layout counterexamples remain relevant; this module requires C-contiguous state and does not establish universal reduction parity across library versions.

The state is poisoned before mutation and marked safe only on a successful return. An escaping BaseException therefore prevents saving or advancing partially updated state. Schema 2 binds the normalization allowance as well as phase, cursor, graph and configuration identity, shape and temperature/iteration metadata. Load checks the expected manifest hash, exact caller allowance, all three member hashes and NPY extents/headers before `np.load`. The loaded state receives the same finite-array and phase checks as an in-process state.

These checks support states produced and left unmodified by this API. They are not a proof of arbitrary state reachability: for example, a caller can manually fabricate an in-range normalization cursor that is not a block boundary. Such caller mutation is outside this acceptance; the expected manifest hash must come from a trusted completed save. No hostile concurrent mutation or filesystem replacement defense is established here.

## Publication, ownership and bounds

`save` validates the state and conservative logical allowance before exclusively creating its directory. Each array is written and fsynced before the manifest is published; the directory is then fsynced. Existing identities are refused. A failed publication retains the exclusive partial directory rather than overwriting it or automatically continuing it. An interrupted advance requires recovery from a previous valid checkpoint, not reuse of its poisoned in-memory state.

The retained state is exactly V, M and Q, each float64 with shape n×m: 24×n×m bytes. Reusing M avoids a fourth retained full matrix. This is not a bound on simultaneous process memory. Q setup, validation masks, graph/config hashing, SciPy temporary arrays, padded locals, checkpoint I/O, caller-held old states and final hardening/scoring/copies remain outside it. The chunk allowance bounds native normalization input elements, not all temporary bytes. Initialization, full scans, publication and other atomic work remain outside any per-call wall-time guarantee. Logical checkpoint size is not physical disk allocation.

## Evidence and qualifications

The saved red log records one phase assertion failure and three missing-policy keyword errors, with six other tests passing. The saved green log reports **10 tests passed in 2.444 seconds**. No rerun was performed.

The new end-to-end test saves and reloads after every one-operation return for 3×4, 3×5 and 3×1 pairs over two iterations. It compares all three matrix byte strings before and after each restore and final soft-assignment bytes against the unchanged scalar reference, plus hard assignments, score, iteration count and convergence. The 3×5 fixture exercises the padded singleton tail. Existing cut-point, zero-edge/tie, identity, tampering, budget and exclusive-directory tests remain. New tests also reject policy mismatch before array loading and demonstrate poisoning after exponentiation has already mutated its output.

This evidence does not exercise every phase's interruption point, power loss/fsync failures, arbitrary metadata corruption, near-overflow inputs, all shapes/strides or native allocation peaks. It does not establish accelerated/Torch parity, whole-hub feasibility, bounded hardening, full solver wall time, registered checkpoint ancestry, empirical admission or financial results. Those claims remain untested and unapproved.

## Reviewed identities and active freeze

All 12 entries in `source-bindings.json` were independently rehashed and matched. Key identities:

- `annealing.py`: `ef795c3b434fab1980aac40bbb25925d9ac817d1dab1a82690a4f0b498b8b4cc`
- `test_annealing.py`: `621c54a7c880acdd9b0b28369e10b2e1cb55adb47ac46f7a53a1f461654df9ca`
- `IMPLEMENTATION.md`: `fbe25c74b4f6b1b5b0461a3dcd60d9a34d05a42b7d13205d6187b8b99de06f40`
- `green01.log`: `4eaaa7d6833d35118a7efcd372068159a42b4ee5c08131c8c9d5395ba427e69f`
- `red01.log`: `a5c85d43f456b0cfa59c695522a9a6f24dd0ee4481e7a28033db4ceb06677778`

HEAD remained `62c5b6ea66e95cc67a404d1f13898619a88237fc`. All 22 original and 26 contextual storage03 bindings also matched. Connection metadata was checked by hash only; its contents were not inspected. This review neither changes nor closes the separate active preservation job.
