# Independent corrected compact owner review

Accepted for explicit first-owner compact stage ownership and aggregate evidence closure. The initial findings in `REVIEW.md` are resolved within this component's stated scope. This does not select the native producer, prove scientific workload derivation, publish a representation or seal the existing FeatureJournal.

## Corrections verified in source

CO1 runtime changes are checked against the saved configuration digest and reserved counter. Stage intents are rederived, compared to pinned bytes and read back from disk; boundaries recompute cumulative reservations from the owned stages. CO2 uses symlink-aware marker checks for both compact and representation terminal entries. CO3 reserves two 65536-byte owner records plus two 8192-byte records per stage in addition to primitive allowances, and stage intent serialization is itself bounded to 8192 bytes. CO4 performs the owner lease after scope construction and immediately before stage-directory creation. Begin, finish-stage and aggregate finish use the same nonblocking transition lock.

The additional stage bindings require the log's integer iteration limit to equal registered matching configuration and the MCM stream graph to match the required stage name. They run before stage sealing and during aggregate verification. Policy and complete stage receipts remain joined through the actual compact-stage verifier.

CO5 is corrected by retaining the exact admitted Binding and ResearchRun objects and a snapshot digest of Binding record/context/limits plus run directory and claim hash. `check_binding` runs before a full boundary check and before and after the live Binding lease. Replacing the Binding, changing its source record or changing runtime context can no longer redirect authority while leaving compact owner bytes unchanged. This is ordinary in-process contract integrity; it is not protection against arbitrary modification of all private pins or Python method replacement.

Complete owner closure requires the exact required stage set, every stage closed, no active stage, correct cumulative reservation and content-valid stage receipts. After exclusive completion publication it repeats boundary and callback-free stage verification and reads back the exact completion bytes. Partial or conflicting evidence is retained on error. No empty old pair journal is used as a substitute for compact evidence.

## Saved evidence

- `check03.log`: **17 passed in 193.14s** on the pre-CO5 source, including actual aggregate closure, foreign-graph refusal and iteration-limit refusal.
- `red04.log`: **3 failed, 17 deselected in 34.21s** for replacement by another legitimate Binding object, changed `record.source_commit` and changed `context.runtime_hash`.
- `check04.log`: **4 passed, 16 deselected in 49.65s** on the corrected source: the three authority regressions and a fresh actual aggregate-completion case. This is a targeted run, not a claim that all twenty current cases were rerun together.

The positive completion fixture uses an actual temporary registered ResearchRun/Binding, a zero-pair synthetic dictionary stage and fourteen real checkpoint-engine MCM comparisons. The registered required graph and matching config are taken from the actual tiny numerical fixture. Both stage receipts and the two-stage/fourteen-pair aggregate complete; the owner becomes terminal while the FeatureJournal remains unsealed. The separate dictionary used for MCM comes from the scalar fixture: this does not establish registered sampler/dictionary provenance or a complete native pipeline.

No test or job was rerun by this reviewer. Actual kernel guard enforcement is mocked. Inner leases deliberately omit full graph/source/input rereads and depend on the caller's frozen source/input contract; full Binding checks remain stage-boundary operations. Reservations cover retained logical evidence, not allocated filesystem blocks, numerical scratch, process memory, predecessor storage or runtime feasibility. There is no successor/reopen admission, cold reuse or financial outcome claim. Dedicated concurrent-transition and late aggregate-completion corruption tests are not claimed from these logs; their boundaries were inspected statically. Temporary numerical fixtures are not represented as an externally recoverable artifact archive.

## Reviewed identities

| File | SHA-256 |
| --- | --- |
| Current `compact_owner.py` | `099b8facfa1a34224bfad631df139c2c196f4b0b90df1411b745129cca165de9` |
| Current `test_compact_owner.py` | `9314988a795edc37abe551f861b32663134de087958540f2aaca290abc6aac26` |
| Preserved `owner-check03.py` | `8901353047a818b84aee8e18008bd67f39bd99d3fd9e911d6a20acdc50c4dcdf` |
| Preserved `test-check03.py` | `9cfda53835a2ba4a7b1a6c5420e73eff0bb7305a756ed00ef2fb508ccde2ef3a` |
| `check03.log` | `27a256afbbab9832a255b1271020450d0f912de6b79eb9e1e8363ea612489b0c` |
| `red04.log` | `2679bc4c1d2129afe32bed7049528bb5ed9c3a4a3fe5cc7a1b823ade93e763b8` |
| `check04.log` | `a76af05ba5a2174abf4a623713b370a9a2d344643a012c86c0d7b692a577cd2c` |

These identify reviewed sources and saved logs, not a complete execution-time dependency manifest.
