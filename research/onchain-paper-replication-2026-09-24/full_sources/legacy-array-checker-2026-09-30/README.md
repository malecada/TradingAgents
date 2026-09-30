# Independent legacy saved-array checker candidate

`arrays.py` independently hashes the five retained NPY files and reconstructs
the canonical graph identity, transaction-count conservation, edge transforms
and four node features. It imports NumPy and standard-library modules only.
Numerical checks derive transparently from the previously accepted
`../graph-verification-10-2026-09-30/verify.py`. Added checks bound declared file
extents, reject extra directory members and nonregular/multiply linked files,
check file signatures across verification, and close all loaded mappings on
success and failure. The independent expected manifest hash and array-byte
budget must come from the future reviewed release binding.

`red01.log` retains eleven failures before implementation. `green01.log` records
eleven passing unittest cases using invented two-node arrays only. No empirical
array body, transaction body or mapping body was read by these tests. The
candidate has no CLI and is not released for actual graph verification.

Independent review found AC1: a rehashed NPZ archive renamed `.npy` was rejected
but its returned `NpzFile` handle was not closed. Original source/tests/docs are
retained as `.original`, and `red02.log` reproduces the failure. The corrected
cleanup explicitly closes rejected archives and checks both archive and file
handles. `green02.log` records twelve passing cases, including AC1. Initial
review remains preserved. `REVIEW_V2.md` accepts the corrected isolated component;
SHA256 `6ecd22c740af98e3b6fd786be5be8ba377d8a73dff9bce962cbb9b8f5f370c39`.
This acceptance does not release empirical execution.

The test suite checks manifest and array corruption, rehashed invalid features,
counts, dtype, identifiers and endpoints, symlinks/hardlinks, extra files,
pre-load byte refusal, independently wrong graph identity, and explicit mapping
cleanup on both success and numerical rejection. Actual immutable input and
resource ownership remain wrapper responsibilities. Signature checks are not a
defence against a malicious concurrent filesystem writer. The byte cap is not
a whole-process memory cap: numeric work arrays and canonical edge-row JSON
serialization allocate additional memory. The future finite cgroup guard remains
mandatory and must process the two legacy graphs sequentially.

Pending before release: compact metadata adapter and independent release review
binding the original FAILED claim and complete graph phases (preserving all109
historical cells); graph configuration raw and canonical hashes; wrapper source,
runtime and exact ownership checks; exclusive receipts; committed release and
fresh resource preflight after the active offline verification is closed.
Saved-array verification does not independently audit raw transaction semantics
or exclusion classification and does not itself admit future empirical reuse.
