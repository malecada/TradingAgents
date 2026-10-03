# Exact local member reader candidate01

Status: unintegrated source preparation for independent review. The candidate implements real descriptor-relative local IO and derives membership from original hash-pinned metadata. It does not construct or replace an Owner, Target, Binding, Published object, cold receipt, transport context or scientific lease. No live source, capsule, registration, empirical data or history was changed. Only tiny synthetic byte files were exercised.

## Implemented lowest layer

`exact_members01.open_local` requires an absolute non-redirected original directory, an explicit format and an independently supplied original document SHA256. It opens the directory once with no-follow/directory flags, pins its device/inode, derives the complete expected immediate membership from that original document and verifies all members. The returned frozen LocalContent offers bounded `read_part` for derived payload members only. It is content evidence, not an admission capability. Caller-created range dictionaries are not accepted by this API.

Three actual source formats are covered:

- **Score batches:** original canonical newline-terminated `terminal.json` SHA, original `start.json` SHA joined through the terminal, exact32 motifs/row-major `<f8`, original chunk capacity, complete cell/chunk denominator and no pending files, every chained chunk header's previous/index/start/cells/payload SHA, all binary payload lengths/hashes and exact directory membership. Failed stores are refused for this complete-only reader; failed raw remains untouched. Original finite-score validation remains the numerical consumer's responsibility, and tail-to-batch scalar equality/purpose proof remains in the stream/stage verifier.
- **Raw MCM output:** original canonical manifest SHA and exact output schema, owner/stage/contract references, six scope hashes,32-motif rows, `<f4` row-major layout,4×cells extent and full `matrix.f32` SHA. Stage-content validation and float64-to-float32 equality are not replaced; the existing publication/inspection consumer must still perform them.
- **Graph artifact:** original component-manifest SHA, actual component tree with only MCM/edge arrays plus aligned_vectors=None, exact two-member mapping, original descriptors and full-file SHA. The reader independently parses bounded NPY1.0/2.0 headers using stdlib only, rejoins C order, little-endian float32/int64, exact shape and header-plus-body extent. The artifact's original context is bound by its manifest SHA; its actual Owner/Published/cold semantic context must still come from the genuine caller. No numpy loading or numerical values are interpreted here.

The `.` sentinel in the prior scaffold is now explicitly refused, together with empty, parent, nested, absolute, NUL and backslash member names. Payload names are derived from the original formats; arbitrary path/hash plans cannot create membership. All files must be regular, single-link, no-follow members. Parent and child FD/path identity, size, mode, link count and modification/change times are rejoined. Initial scans hash full original bodies; each range read pins/rejoins the same member and directory, and successful context exit rehashes every original member and verifies exact inventory again. A same-content replacement inode is refused. Member topology/signatures cannot be rebound through normal attribute assignment.

This remains sampled verification under a sole-writer/source-freeze contract, not an atomic filesystem snapshot or adversarial filesystem protection. No data may be accepted/published from the context until successful exit. Mutations after a member's final read cannot be ruled out by a non-atomic scan. The layer exposes no remote fallback, missing-member waiver, local deletion, replacement restore or retirement operation.

## Bounds and cleanup

Range reads are limited to1MiB; hash scans use64KiB chunks. Compact metadata uses8KiB, original component manifests use4MiB, NPY headers use64KiB. Membership is bounded at65,536 entries and per-member bytes at64GiB. These are candidate parser bounds, not a resource admission for such a workload; actual native wall/memory/storage/entry limits must be stricter as selected by the registered caller. Returned metadata/signatures cost O(number of members); body reads cost O(chunk), apart from bounded metadata/NPY buffers. Full initial/final verification incurs complete byte rereads. No throughput, memory peak, quota, deadline or storage saving is claimed.

`owned_io.py` is an exact copy of the previously accepted reducer; its hash/source is pinned in source-origins01.json. Every acquired child FD and directory FD has one independent close path. The first actual fatal survives later ordinary close uncertainty; uncertain cleanup still raises if no fatal is already propagating. Scandir iterator closes use the same reducer. No source diagnostics invoke arbitrary exception repr/add_note. No fdopen wrapper takes ambiguous ownership. The candidate import is standalone local `owned_io`; eventual package integration must deliberately rebind this to the identical selected `.owned_io` dependency and pin that coordinated source closure.

## Retained verification

Checkout-local `.venv/bin/python -B` ran only standalone stdlib tests:

- `dot_counterexample01.py` executes the actual original scaffold and fails as expected because it accepts `path='.'`; `dot-RED01.log` preserves that independent-review counterexample.
- `RED01.log` retains the first reader tests before implementation (missing module).
- `GREEN01-attempt.log` preserves an initial six-test run whose fatal test patch ended before the reader's outer close, so no close was injected. That test-scoping error was corrected; no passing cleanup result was inferred from it.
- `GREEN02.log`: six passing tests for actual raw file reading, wrong manifest, directory paths, missing/extra/corrupt/symlink/hardlink payloads, mutation/inode replacement and first MemoryError across uncertain outer close.
- `formats01.log`: six passing tests for actual source-extracted ScoreBatches `_json` framing, complete batch header/terminal joins, independently resealed wrong start_cell refusal, exact two-array NPY headers/full hashes, a hash-valid manifest with wrong NPY dtype refusal, frozen object fields, original directory replacement, and SystemExit during actual read with both child/directory descriptors independently closed exactly once despite two close failures.

No fake research capability or scientific callback appears in these tests. Synthetic NPY files are encoded with stdlib bytes/struct solely to test header checks; no original numerical array, label or model was loaded. No genuine positive Owner/Binding/current-source/runtime/transport admission is claimed.

## Exact integration still required

Install only as a new selected lower reader module, leaving all historical source and existing default readers unchanged. The real typed held Target/current Owner or admitted cold capability must provide the original trusted terminal/manifest pin and derive the same graph/node/motif order, original matching, job/input/source/runtime and complete population. It must check before entry, while consuming and after exit using its actual authority, without substituting a no-op callback or treating this content object as a receipt.

Selected `score_batches.verify`, stream seal checks and stage/archive closure need the payload-reader seam while retaining finite-score and exact original tail/header/terminal proof. `compact_mcm_output` must retain its original float64→float32 conversion/equality and stage checks. Publication/Produced/Features and graph/native/cold readers must retain their original authority, object/inode lifetime, context and complete inventory joins. The first implementation here is local-only; offload requires a separately typed disposition mapping and shared durable transport Context with cumulative no-refund budgets, actual held token/revocation and independently recovered whole bodies before any disposition. It cannot restore a file over a still-pinned original inode.

The next proof must be a fresh finite genuine typed fixture under reviewed native limits, followed by resident/restored forward/all-gradient/Adam/RNG/checkpoint equivalence with full original population/order/dtype and no detached learned embeddings. Active arrays/activations and full multi-distinct-graph capacity remain separate. This candidate reduces no scientific denominator, frees zero production bytes and authorizes no execution or financial fit.
