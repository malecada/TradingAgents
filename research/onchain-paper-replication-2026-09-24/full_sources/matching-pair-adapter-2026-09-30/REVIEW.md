# Independent isolated ordered-pair adapter review

Accepted for the inspected **GraphSnapshot-based synthetic artifact-layer scope**, subject to the explicit local-graph limitation below. No registered producer, dictionary/MCM integration, empirical continuation, or capacity-scale release follows. Source and saved evidence were inspected without running tests, opening checkpoint bodies or editing source.

All 100 compact bindings independently matched. Initial reviewed identities:

- `adapter.py`: `63cefb8d5b33b40e0c9dfd77a2ee506285f98da1dcec816fe783646f2f417787`
- `test_adapter.py`: `a7f0a868304b90f946f3d41de054e3bf150471ecdcf8c33271fac4fd8d6a5637`
- `IMPLEMENTATION.md`: `7ffd7a02dc716708ceed44143190458d172fab8079d81435abde2b997feba8ff`
- `bindings.json`: `3fb3f3d144565c664f67019eacabecf437c7e4d5099fd2af05dfa7d47ef7f428`

## Concrete boundary requiring follow-through

`adapter.identity` delegates ordered graph identity to `engine.ann.identity`. The inherited scalar annealer uses `neighborhoods.graph_hash`, which calls `validate_graph`; that validator accesses `.asset` and weekly source/clock fields. Actual sampled neighborhoods and dictionary representatives are `AttributedGraph` objects (`contracts.py:184–191`), deliberately lacking those fields. `NeighborhoodIndex.neighborhood` returns that type (`neighborhoods.py:83–88`). Therefore a real local pair currently fails identity construction before it reaches the solver. All seven adapter tests use the `GraphSnapshot` helper from `test_matching_reference.py` and do not exercise this boundary.

This is an inherited isolated-engine limitation, not a corruption of the current production path. It must be documented explicitly now, and resolved before claiming dictionary/MCM support. The future maintained implementation needs a validated type-specific local-graph identity that includes exact node/edge order and attributes plus `parent_hash` and `center_id`, without inventing weekly counters or clocks. Add a real sampler/neighborhood fixture and reject changed parent, center or order on restore. Do not alter preserved prototype identities or pretend existing scalar snapshot tests establish that compatibility.

## Identity, publication and ownership

The adapter explicitly distinguishes CPU scalar float64/SciPy/ranked/sparse-float64 semantics from the production Torch score path. Identity binds ordered left/right graph and config hashes, workflow namespace, declared source commit, runtime hash and four numerical component source hashes. Resume requires exact identity, owner and full policy before engine array loading. Source/runtime hashes are caller declarations at this layer; their actual admission remains external. No cross-commit compatibility is inferred.

Each session uses a new exclusive name beneath an existing resolved nonsymlink root. Trusted references require an absolute contained manifest path, bounded size and exact supplied hash. No latest-directory discovery or name reopening exists. Successor owner and publication metadata retain the immediate parent reference and owner; full ancestor validation and active/failed ResearchRun status are explicitly caller obligations. The adapter does not enforce one global scientific owner, cumulative ancestor budgets, or that the supplied reference is the latest admitted journal event.

A complete score manifest restores an immutable `MatchScore` without solver creation, state load, advancement or rescoring. The saved test forbids all four entry points and verifies repeated reads. Input graph identity is still recomputed; this is checkpoint-array-free reuse, not a claim that no input bytes are inspected. Numerical completion closes the state before score publication. Graphs, configuration and session attributes remain exclusively caller-owned, so mutation defense is not promised.

The retained red02 log directly exhibits the earlier missing-parent metadata and primary-interruption masking failures. The corrected source preserves parent references in both owner and publication manifests. Cleanup now preserves the primary `BaseException` and attaches a secondary close failure as a note. Failed publications retain their directory, consume the session's reservation, poison the session and require a new exclusive recovery session. A noted cleanup failure is not proof that a mapping actually closed; the outer guard must remain authoritative. The mock-based adapter cleanup test checks exception identity and poison state, not real mapped-handle reclamation under a failing close implementation.

## Limits and verification evidence

Policy schema requires exact positive integer fields, including composite, normalization, rank, score, checkpoint count and byte allowances. Before publication-directory creation, the session reserves 64 KiB owner metadata plus `max_checkpoint_bytes + 64 KiB` for each attempted publication. Completion-only publications conservatively spend that same reservation. Count/byte rejection before a new directory does not consume a publication; failures after reservation do. The saved test proves no extra directory after exhaustion.

The cap is logical and per session. It does not account for retained parent sessions, filesystem blocks, concurrent consumers, graphs, native sort workspace or process memory. A new owner can reserve another allowance only under the caller's separate aggregate admission; this layer does not grant it. Atomic hashing, sorting, scoring and fsync remain governed by an external finite process owner. No automatic retry, deletion or limit relaxation is introduced.

Saved green02 records seven tests passing in 0.165 seconds. Evidence covers one tiny ordered numerical fixture against scalar reference, progress recovery, complete-score reuse, orientation/config/context/owner/policy/hash refusal, exclusive paths and quota refusal, failed-publication retention, parent metadata and primary exception preservation. Orientation refusal is not a separate reverse-direction numerical parity campaign. No new capacity, process-guard, crash-durability, real-neighborhood, full dictionary, partial MCM-row or hostile-prefix test was performed.

The next registered layer must enforce exact source/runtime/lease and failed-parent ancestry, publication-gap recovery, latest accepted references and cumulative storage/compute admission. Production numerical defaults, gates, source coverage and empirical denominators remain unchanged. Full real-graph feasibility and all 1,420 fits remain pending.
