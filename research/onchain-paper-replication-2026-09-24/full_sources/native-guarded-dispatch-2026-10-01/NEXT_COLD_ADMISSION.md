# Next cold native admission boundary

Read-only interface investigation; no implementation or release acceptance. A new current-run adapter is required. Existing live-owner contracts must not be weakened or reconstructed with forged in-memory receipts.

## Reusable interfaces and blockers

- terminal-output-lifetime-2026-10-01/native_map.py `_NativeMap`, strict component reader and graph-feature boundary identity/materialize already support bounded native float32 MCM/int64 edge tensors and lazy requested-key batching. Its constructor alone grants no admission.
- That module's `prepare` calls `seal.finish` once and captures live OwnedJournal/ticket/resident-graph leases. It cannot serve a completed historical run.
- graph-feature-artifact-route-2026-10-01/route.py `admit` requires an unsealed journal and rejects representation_complete. matching_owner.bind requires a producing job and an active representation owner. Both are intentionally unsuitable for cold admission.
- maintained registered_features.py `reuse_registered_features` uses read_feature_journal and reconstructs earlier sample/dictionary/MCM components. It lacks native_graph_feature_v1 terminal-proof admission and must not silently substitute for it.

## Minimum historical joins

Bind exact prior registration, claim/source, lifecycle completion, declared output hashes and accepted guard/observer cleanup. Verify the historical owner and immutable complete-run denominator; reject failed/conflicting markers, partial inventories and foreign paths. Preserve the old producer/source identity separately from the current consumer. An output with a caller-supplied hash alone is insufficient.

The seal schema1 complete proof binds start, publication, pair_terminal, feature_terminal and the two published outputs. Its publication closure contains schema3 binding, denominator and per-graph records. Join the exact feature terminal events to sample/dictionary, each required MCM/graph pair and final representation completion; verify unique/order-complete graph membership without reopening numerical production.

Join expected current descriptor and full ExampleManifest/fold/train hashes, seed/configuration, dictionary identity/training-only lineage and exact required graph union. Each graph record binds graph proof/event/component, native storage marker, node order, feature wire hash and MCM provenance. MCM provenance binds ordered motifs, workload and complete rows/cells. Derive dimensions from admitted historical proof/header metadata, not caller assertions. Preserve original policy/read limits per file and bound every traversal before allocating.

A first conservative release can trust exact accepted historical producer evidence for the saved MCM-to-feature transformation while independently verifying saved native content against its pinned wire hash. It must explicitly state that this is reuse of admitted producer evidence rather than rerunning weighted sampling, clustering, matching or arithmetic provenance. No historical source claim becomes a current execution owner.

## Current consumer boundary

Require an actual active ResearchRun with an explicitly selected native reuse route, exact registered old references, current reader source/runtime/input bindings and the current worker's real guard. Use a new terminal-content lease plus current-run liveness; do not call old owner/ticket leases. Initially restrict artifacts to canonical paths inside the same root. Moving a retained checkout requires a reviewed explicit path mapping, not implicit path rewriting.

Construct `_NativeMap` only after terminal admission. Keep its actual FixedFeatureMap subclass dispatch, strict native tree/dtype/order checks, wire-hash verification including empty edges, live tensor accounting and current registered batch policy. Publish or reference the exact binding as a current admitted input/output, satisfying evaluation.evaluate_cell. Native selection currently accepts only operation=produce; a distinct reviewed reuse branch must precede the generic loader.

Required counterexamples include wrong historical owner/source/output, complete+failed conflict, omitted/duplicate/reordered events, changed full denominator/train scope or motif order, self-consistent rehashed false feature payload, current guard loss, and drift between metadata admission and batch read. A positive test must forbid sampler/dictionary/MCM producers and generic journal reconstruction, demonstrate exact values and repeated bounded batch use, and retain separate terminal evidence. No real historical job needs to be rerun to implement these checks.
