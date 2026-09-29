# Independent mapped-graph implementation review

September 29, 2026. Scope: new mapped loader, graph-store export, mapped-ID validation, streamed node-order hash, feature-lineage call and synthetic tests. Source and saved compact evidence only; the reviewer ran no tests, raw reads, empirical work or network requests. Production files remain parent-owned.

## Initial snapshot

- `mapped_graph.py`: `c03438ac7780a49e076a3b20ecd963fcacc6b6fe7b4fb7573ee64550bd0b3f9f`
- `contracts.py`: `3f88e9e56f2bfca059e2ef9da2b01ae593444b05e1067154653ea6a5479fea1a`
- `graph_store.py`: `a03639a68f8727f422a2567a4737f1e5afcedd3990f36f327ecadd103b3a245d`
- `neighborhoods.py`: `58bf9e36ca688250ac51391730066219f0677b6cb0e41529c34b8e65c0e8f9f0`
- `feature_pipeline.py`: `b9071ab5596028372774bca2da416c792408e315c370013855ad4ffb41baa4ef`
- `test_mapped_graph.py`: `24d47b592978b3f5aba5d942fc4b50d52c9c09d0eeedef8f1837fc9046d6e165`

Saved initial `green01.log` reports 42 passed in 40.63 seconds. This does not yet cover the cleanup findings or all announced edge-case additions.

## Findings sent before acceptance

**P2 — unexpected NumPy loader return is not closed.** `open_mapped_graph` rejects `np.load` results that are not `np.memmap`, but does not close that object. NumPy accepts ZIP/NPZ format by content despite a `.npy` filename, returning an `NpzFile` with an open archive handle. Correctly hashed/size-admitted NPZ bytes renamed as a member therefore reach this branch. The rejected value can remain referenced through the propagated exception traceback, outside the `opened` mapping cleanup list. Reject non-NPY magic before invoking the loader or explicitly close every unexpected closeable return. Add a direct retained-reference regression rather than relying on garbage collection.

**Unresolved cleanup correctness question — ambient exception versus actual context error.** `_close_maps` reads `sys.exception()` instead of receiving the exception raised by the graph context. If the caller uses a successful context inside an unrelated `except` handler, an ambient handled exception may be mistaken for the context's primary failure and swallow a new close failure. A focused synthetic probe should settle this precise runtime behavior. Passing the actual caught context exception explicitly avoids the ambiguity. This is initially a required verification question, not a claim that the counterexample has already executed.

## Other source assessment

The implementation checks the complete required/optional member denominator, strict descriptors and safe filenames, declared total budget, actual sizes and all member hashes before the first mapping. It bounds manifest bytes and NPY header parsing, rejects object/pickle content through the NumPy reader, checks exact array extent and enforces fixed-width Unicode IDs plus real numeric mapped members. Every successful mapping is registered before later graph construction/validation/hash checks. The subclass introduces no dataclass fields and retains frozen metadata. Normal eager loading and constructor copying remain unchanged.

Mapped node validation is reached by repeated `validate_graph` calls, uses adjacent ordered comparisons with one-item overlap, and does not sort/materialize the entire ID population. Unsorted mapped IDs are rejected while eager unsorted unique IDs remain valid. Numeric finite/aggregate scans and duplicate-edge lexsort still have nontrivial allocations; the module correctly excludes validation/adjacency/model working memory from its file-byte ceiling.

The node-order helper streams the same canonical JSON list punctuation and chunk contents as the legacy tuple hash. The feature-lineage call no longer expands mapped IDs. Graph canonical identity remains based on the inherited logical fields. The current proposed-pipeline test compares complete feature bindings, dictionary identity and serialized sample events; after context closure it reads independently produced feature tensors and dictionary node features. This is meaningful consumer evidence rather than class-name-only verification.

Remaining planned checks include exact node-hash boundary cases, empty arrays/no aggregates, late open failure, close failure with/without a primary exception, hostile dtype/shape/header/extent, and alternate layout/byte order. Context-owned raw views must not escape or be read after closing their mmap. Published backing files must remain stable against external writers; read-only mappings are not snapshot isolation. Full-fold admission, adjacency/matching/model memory and empirical integration remain outside scope.

Disposition pending correction/probe and terminal focused evidence. No empirical release is inferred.

## Correction review and evidence qualification

The corrected loader validates NPY magic and supported format version for **every** admitted member before any call to `np.load`. Under the documented stable-file assumption, NPZ content cannot reach the unexpected return branch, closing the archive-handle path. Saved `red02.log` establishes absence of this complete preflight in the earlier implementation: its sentinel fires on the earlier valid `edge_aggregates.npy`, before reaching the substituted NPZ member. The text “NPZ reached numpy loader” is the sentinel message, not proof that NPZ itself opened or a direct leaked-file-descriptor measurement. The source-level issue and corrective exclusion remain valid; the evidence is deliberately narrower. Red02 SHA-256: `e843d4c7133a8fedad59e05e6d9b5023af8989b442b8093b350639f93f41b547`.

The ambient-exception question is now a **confirmed P2 failure**, directly reproduced by `red03.log`: normal context exit inside a handled `LookupError` added the cleanup error to that unrelated exception and failed to raise the expected `RuntimeError`. The corrected context initializes its own failure variable, catches and rethrows its own `BaseException`, and passes that exact object to `_close_maps`. Normal exit passes `None` regardless of the caller's exception handler; close failure therefore raises. A true body failure receives a cleanup note without being replaced. Every remaining map still receives a close attempt. Red03 SHA-256: `454d5e89fbb0b4d9a62aa36de8e300fe0472e09bbe0189f7af24de6169267132`.

Expanded tests meaningfully cover 65,536-boundary duplicate IDs, repeated validation without the Python sort path, exact legacy node-order hash across many chunks, optional aggregates absent and empty edge arrays, Fortran storage and both explicit float byte orders, malformed ID/features dtype/shape, trailing bytes, non-NPY preflight, a third-map failure with earlier maps closed, real-map cleanup despite another close failure, and preserved primary `KeyboardInterrupt`. The zero-ID hash is checked independently; a fully empty-node graph roundtrip is not established by the empty-edge fixture. The cleanup tests include both helper behavior and the actual context's ambient-exception path.

Corrected source SHA-256: `mapped_graph.py` = `ef56db744e1f616bedc045a7647a262d7a6f413f4c741ecc7a48e49582d6d19b`; expanded test = `7d8cae64fcc043d222584450e5debe951d4aa1eca1d3a416bbc10612d779ddd0`. Both findings are resolved on static inspection at these identities. No further blocking source issue was identified. Focused green02 is still in progress at this checkpoint, so terminal result acceptance remains pending; no new run was launched by the reviewer.

## Focused corrected-code acceptance

Saved `green02.log` subsequently closed with **96 passed in 56.73 seconds**, SHA-256 `84d10fd3c20566dc562214bcc9f4ea791dca9aceca98a0894c33fb1934900c2d`. All six current source/test identities were freshly rehashed: the corrected loader/test identities above match, and the four other initial hashes remain unchanged. The reviewer did not rerun tests.

**Accepted for frozen-source named offline verification.** Both initial cleanup findings are closed for this stable-file, context-owned API; the red02 preflight-order qualification remains unchanged. The focused suite does not establish broad offline closure, cold-cache/total-memory bounds, arbitrary filesystem mutation safety, registered loader integration or any empirical outcome. No job or policy enables this optional API as a consequence of review acceptance.

## Terminal named-suite closure and engineering acceptance

Saved evidence independently confirms the pinned `.venv/bin/python -B scripts/verify_offline.py` command in the active checkout. The reviewed 250-module profile comprises 185 standard modules and 65 isolated neural modules. The log reports **2,768 passed plus 97 subtests in 1,036.06 seconds**, followed by **598 passed and 2 skipped in 444.71 seconds**: **3,366 passed plus 97 subtests, with 2 CUDA-dependent skips** overall. These counts describe the named reviewed profile, not all legacy tests or CUDA execution.

The guard closed `complete`, child exit 0 and verified cleanup after **1,484.0964055 seconds**, with sampled cgroup-memory peak **2,475,028,480 bytes**, zero reported memory events and no limit reason. Runner and final receipt agree on 3 GiB memory maximum, 2.75 GiB high threshold, zero worker swap allowance, 3 GiB ongoing/6 GiB startup host reserves, 20 GiB disk floor and a 3,600-second wall limit. Final recorded free disk was 24,583,983,104 bytes. `final.json` and `live.json` are byte-identical and the child-exit receipt agrees. At review, the recorded cgroup, monitor PID 2636564 and workload PID are absent. Cleanup stop return code 5 is supported by inactive/dead unit properties, empty control-group property and independent cgroup-absence observation.

All **130 frozen source bindings** were freshly reconstructed and match. The six reviewed source/test files also match the final identities recorded above. The runner enforces the saved bindings before dispatch. No tests, raw arrays or jobs were rerun by the reviewer.

- `source-bindings.json` SHA-256: `75f9a6e57f40085656f305af3c477a4963fc7d6360a798e69e43240c78bbf7a9`
- `offline01/final.json` SHA-256: `e96d72a066c209b8fd8855cab64db18bc91129e71eff8201da847581caa84737`
- `offline01/child.log` SHA-256: `5a2ac0199464a71086e58de8190f5166a7b49112dd6ad411fbe88c2f795d1325`

**Engineering release accepted for the optional mapped-graph API at these identities.** Both cleanup findings remain closed with their original evidence and qualifications preserved. Existing eager behavior stays the default; no empirical job/policy enables the new loader. Its ceiling bounds declared files mapped by one context, not RSS, page cache, aggregate full-fold mappings, validation/adjacency/matching/model allocations or cold-cache feasibility. The sampled suite peak supplies none of those broader bounds. Borrowed raw mappings still require stable backing files and a live context; independently owned outputs are the supported objects that survive closure. No financial fit, resource allowance or scientific completion criterion is admitted by this engineering acceptance.
