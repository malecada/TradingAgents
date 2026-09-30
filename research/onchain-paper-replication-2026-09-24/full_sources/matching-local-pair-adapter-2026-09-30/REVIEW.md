# Independent review — typed local pair adapter

Accepted for the isolated synthetic component scope. No blocking defect was found in the typed identity change or its derivation. This acceptance does not enable a registered producer, dictionary or MCM consumer, change an empirical gate, or establish real-graph feasibility.

Review used source, exact diffs, saved test logs and compact hash reconstruction at HEAD `b5aaf4fd8bd2ed76768b8bff963199cc4b9d401e`. No tests, solver runs, empirical inputs, saved numerical array bodies or remote services were accessed. Only this review was written.

## Identity and derivation

`local_identity.py:14–42` separates weekly and local graph domains. Weekly snapshots retain the validated existing canonical digest inside a new type tag. Local graphs must satisfy the attributed-graph contract and have nonempty string node identifiers. Their identity binds parent hash, center, ordered node identifiers, and the names, dtype/byte order, shape, byte length and exact bytes of all three arrays. In particular, a center or parent change cannot reuse a completed local score even if the numerical features happen to be equal. Node or edge reordering remains significant.

The framing is unambiguous within this fixed format: the node count fixes the number of 1,024-identifier frames, each metadata frame has a length, and each subsequent array payload has a declared byte extent. Empty arrays still contribute dtype, shape and extent metadata while avoiding a shaped-memoryview cast. The added singleton case exercises that branch with actual `NeighborhoodIndex` outputs. C-contiguous real arrays are an intentional input restriction; the attributed-graph constructor already produces immutable contiguous arrays. Exact dtype, signed-zero or byte-order distinctions can conservatively prevent reuse, which is consistent with exact identity rather than numerical-equivalence caching.

Both old and new SHA-256 values in `derivation.json` were independently reconstructed. The complete three-file diffs contain only the declared identity/import/schema/backend changes:

- `annealing.py` selects the local identity implementation and changes checkpoint schema 2 to 3. Its numerical updates, iteration schedule and normalization operations are unchanged.
- `combined.py` selects the new annealer and changes the outer checkpoint version 2 to 3. Ranking, scoring, ownership and cleanup behavior are unchanged.
- `adapter.py:27–30,78–89` selects the new composite, declares backend version 2 and checkpoint schema 3, and fingerprints the typed identity source in addition to the existing numerical components.

Old accepted source files still match their recorded hashes. The adapter manifest remains schema 1, but exact backend/component identities distinguish the new variant. Old outer and annealing schemas are rejected before their numerical array loads; the change does not silently migrate old checkpoints. Ordered left/right identity, configuration and caller namespace/source/runtime fields remain bound.

## Evidence and ownership

The retained `red02.log` records 16 tests with nine actual local-input errors from the old weekly validator, including the missing `asset` boundary; seven snapshot tests still passed. This is a real contract counterexample, not a missing-module result. `green02.log` records 18 passing tests in 0.279 seconds. The tests reuse the seven artifact checks for snapshots and real local neighborhoods, then add local soft-byte/hard-assignment/scalar-score parity, graph-identity mutation rejection, schema rejection before array loads and closure of an actual restored rank mapping.

The separately retained `singleton01.log` records one passing test in 0.028 seconds. It constructs two isolated one-node, zero-edge neighborhoods, saves and closes the first session, restores into a new exclusive session, advances with one operation per call, and compares the resulting score, convergence and iteration count with the scalar reference. The result is additional tiny-fixture evidence, not a rerun of the 18-test suite.

All 112 original bindings matched current compact/source bytes. The 114-entry `bindings-with-singleton.json` retains every original entry unchanged and adds only `test_singleton.py` and `singleton01.log`; all 114 hashes matched. Source derivation and the identity-specific tests support preservation of the scalar arithmetic for these fixtures. No new broad-suite result, capacity-scale local-graph profile, Torch precision equivalence or general numerical proof is claimed.

Exclusive session names, exact caller-supplied parent references, per-publication reservations, retained failed outputs and primary-exception preservation are inherited unchanged from the reviewed snapshot adapter. The local variant does not add an admission mechanism. Trusted references and exclusive graph ownership remain necessary; source/runtime declarations supplied by a caller are not independently admitted merely because they are well-formed hashes.

## Remaining integration limits

Full identity/finite validation and hashing remain atomic. Identifier chunking bounds the count of identifiers per serialization, not arbitrary string byte lengths, validation's Python allocations, total RSS or time per operation. Original pair-capacity and sparse-objective domain restrictions remain effective. The retained-state and checkpoint allowances do not cover all native sort/normalization work, parsed metadata, ancestor storage or process memory.

Registered ownership and failed-parent ancestry, the latest durable journal reference, aggregate resource accounting, immutable source/runtime admission and backend-aware cache lineage still require the separate integration work identified in the integration audit. This variant does not provide production dictionary directional continuation or MCM partial-row continuation. It does not establish financial correctness, return conventions, fees/funding, exposure independence or any completed financial fit; those paths are unchanged and were not tested here.

## Reviewed bytes

| File | SHA-256 |
|---|---|
| `local_identity.py` | `220c3ebf08ce9cc7796a8ebfed4ba7822236ab3a9de475637dd8bd5450927375` |
| `annealing.py` | `781551b0a4d548fe67045390a7f9584e6371d73f0e6a1e3d16c3b0a720156d21` |
| `combined.py` | `cb5c3a567a6e3f239eedda5dcbdb39fe1d9f0ef39c2319a941fa618bc1aac487` |
| `adapter.py` | `1147001fde722f05ed76a5039befc1c9e5b1ef0825e9b7167a64f737b290f1a3` |
| `test_adapter.py` | `6bd0c7c5736fb7c8cd7d5457b24338e76bd3930068ea40720de78825e19d385d` |
| `test_singleton.py` | `6e4130377bd85e0cb2b8d18b3f72f30c0d9902c4b7f4bd9b8d999df3265983fb` |
| `derivation.json` | `b9eb8e3028889fb69a90d4738e2158d3984e36ee2b9aa2d76a5d0a958aa48546` |
| `IMPLEMENTATION.md` | `5fc0d83f17aaf13d5ba6b5af048103a303d77d7d0be5c57c3ca3f632747e9f0d` |
| `bindings.json` | `93fb33a184b49e67d85eebb32ca6594769e2f322b4bf8e0e23a7e6af853a104e` |
| `bindings-with-singleton.json` | `bb76bd20c6fe329c2af37aee21b27b660f890aea9d5adf3697c0f3ada17f0aaf` |
| `green02.log` | `04a67849d9a648e7b6820f07ab46dd5bd9cc63e173f95d2230c858c16a6053dd` |
| `singleton01.log` | `17455243c2641afa8a539b33fbfebbdae8c63be1a7c20ecd1a8855184e0c76bf` |
