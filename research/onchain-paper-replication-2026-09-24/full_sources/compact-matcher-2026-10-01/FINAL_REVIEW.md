# Independent corrected compact-matcher review

Accepted for fresh synthetic direct-engine execution with compact event evidence. CM1–CM3 and the additional begin-publication counterexample are addressed in the reviewed source and saved tests. This is not registered producer integration, empirical admission or successor/recovery permission.

CM1: constructor validation preserves the conservative original per-pair byte envelope, `LIMIT + max_checkpoints * (max_checkpoint_bytes + LIMIT)`, and publication-count ceiling. Before begin/allocation, each pair must fit the remaining log-event capacity and the complete possible global checkpoint count/byte envelope. `_save` still charges each retained attempt before creating its directory; intent records retain cumulative counters. The new wrapper's two 8 KiB metadata allowances are included in global reservation. These are logical reservation bounds, not measured allocation or hard filesystem quotas.

CM2: the expected progress event frame/head is computed before publication. After PairLog publishes and the combined leases run, the executor rereads the prebound intent/wrapper and verifies the state manifest, nested hash tree, exact array extents/content and checkpoint state inventory, then reads back the exact acknowledged event without another external callback. A failure retains the event/checkpoint and poisons the matcher instead of continuing numerical work.

CM3 and begin boundary: begin and completion now also capture their expected frame/head before publication. After the external matcher/log checks, `_ack_check` validates pinned log start, exact event count/head, fd/path identity/extent and the complete 168-byte record. Numerical allocation follows successful begin validation. Completion follows actual engine cleanup and successful combined acknowledgement. The ownership and filesystem observations are sequential, not an atomic guarantee against changes after an individual final check.

Saved red03 reproduced late checkpoint mutation and matcher-lease loss during completion; saved red04 reproduced a corrupted durable begin before engine creation. Saved check04 reports **10 passes in 0.42 seconds**. The tests preserve an already published progress/completion event when a later check fails and prevent successful callback or new allocation. All original numerical methods remain unchanged. The reviewer inspected saved evidence/source without rerunning tests.

Positive numerical evidence remains a tiny ordered pair compared exactly with the scalar reference and the original PairSession numerical identity. A real progress checkpoint is saved and loaded read-only without advancement; actual state close is exercised. The cleanup-failure fixture performs real release, then injects an OSError, proving fatal BaseException propagation and absence of completion publication. It does not reproduce an actual operating-system mapping cleanup failure. Full MCM/tail composition is a separate pending test, not evidence assumed here.

Remaining scope limits are material: grouping advance calls changes checkpoint cadence and needs prospective admission; ranking inside advance still has separate sort/scratch/time behavior. Cached numerical-source identities rely on source freeze and external admission. Occurrence membership, owner admission, runtime guard, whole-workflow inventory/quota, existing predecessor evidence and checkpoint successor admission remain external. Hashing checkpoints does not independently rederive their numerical state semantics; the positive read-only load is separate evidence. The implementation removes per-completed-pair PairSession owner/artifact directories, but retained progress snapshots, compact events and downstream score tails/batches still require cumulative physical-resource assessment. No financial outcome or full-fold capacity claim is established.

Exact reviewed SHA-256:

| Artifact | SHA-256 |
|---|---|
| `compact_matcher.py` | `645925483675e5fb8bc0aad4c662fcff963db24125610928b532bb13f1b1b650` |
| `test_compact_matcher.py` | `f26bbbac6288b40a086aea57133062fffe31e8ee545924b13a7f4b60d77ff723` |
| `check04.log` | `b2cdaba3960f71a8fa30a0a8e0340cad5d15b9a2c387ab24eaf6b5f8e36419a7` |
| `red03.log` | `473d8345807ddd3c6fda91d3e9edc518c9bfc70938fee1e51d10944718af7326` |
| `red04.log` | `b84bcee7669899ced1aa502bc565e1ebecde4b4f0ff5e8e847d286a482922b8f` |
| preserved `check03-source.py` | `8f2aedd7e34791503fd6ffa74479c02c1fdf993d8a5b9a8597c7853cc9c61e61` |
