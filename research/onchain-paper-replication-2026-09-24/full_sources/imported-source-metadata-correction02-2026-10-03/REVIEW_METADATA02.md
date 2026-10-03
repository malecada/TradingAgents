# Independent imported-source metadata review 02 — 2026-10-03

Disposition: **accepted as a narrow source correction**. The exact candidate resolves ISM1 from the immutable withheld metadata01 review. This does not admit a numerical job or imply that the separate failure-cleanup correction, complete capsule/gate, runtime, or full-size capacity has been verified.

## Exact snapshot and independent byte checks

- Manifest `e559e8053194565c280c720f75b11efa1e05b740b2c4582ffd58cb8f4604909b`: all 11 bodies verified by size and SHA-256.
- Candidate `compact_mcm.py`: `9009112805eec33444030058d30bd7d741b59fdb0bcfb9ab031f9862923d7f53`.
- Source inventory `e304ff9f880003f224d08900c2a61c918eccaf9be45a6438b1b7b77be6096e0d`: all 153 origins verified; declared 142-package closure; sole changed target remains `tradingagents/research/onchain_replication/compact_mcm.py`.
- Baseline `ed94415ff1798422d66bb19fc6b7ab72e70afef999101d0fb206e3f65556f93a` and original-start reconstruction `26a8082317afeb94cdc69f7b3772f608f5c69e91716da622cfb9ef12d03f38ab` remain pinned.
- Prior withheld review `30245ac0fac119133cb0f6dda4566562176987741d83451a53ab36a3040b6fd8` remains unchanged.

The predecessor inventory hash was independently checked. Every unchanged inventory row is byte-for-byte the predecessor row. Whole-module AST comparison independently confirmed that removing only the new `_source_evidence` helper, the imported start-reference expression and the two reference-join clauses restores the original module AST. In particular, numerical production, metadata caps/reservations, output publication, original read paths and all other Produced methods are unchanged.

## ISM1 closure: actual last-callback boundary

The second callback-bearing `_sources(Target)` join now follows the final `self.lease()` and precedes final `_original`, `_numeric`, `_evidence` and callback-free `publication._verify`. There is no source callback appended after that final verification. Full source-body validation remains required rather than being replaced by digest-only trust.

The original independent counterexample was reconstructed against both immutable metadata01 and new metadata02. It compiled the actual `Produced._check`, `_sources`, `_source_evidence`, and actual selected `Target.sources` method ASTs into a stdlib-only namespace. Fake guard/authority boundaries and nonempty scalar byte buffers isolate ordering; they are not a genuine Owner or numerical execution.

| Extracted-method case | Observed result |
| --- | --- |
| Metadata01: mutate matrix during fourth dictionary check, reached through final actual Target.sources | Returned successfully with changed matrix, reproducing ISM1 |
| Metadata02: same mutation at the same callback | Raised `ValueError: matrix changed` at the final numeric rejoin |
| Metadata02: unchanged matrix control | Returned successfully after final numeric and publication verification |

The metadata02 control sequence was dictionary checks 1 and 2, numeric verification, dictionary checks 3 and 4, numeric verification, then final publication verification. In the mutation case the fourth check changed the buffer and the next numeric verification refused it. This is independent confirmation of the specific missing-rejoin correction, not a claim that an OS or real imported authority fixture passed.

Implementation `red02.log` preserves the same boundary failure with its own extracted-method harness; `green02.log` reports nine passing methods. Initial `.cast` harness errors remain recorded and are not counted as the meaningful RED. These raw logs and test source were read, not rerun as a suite. The separately reconstructed counterexample above uses the actual Target.sources body rather than a stand-in sources callback.

## Retained size and authority constraints

The imported source map is encoded as the explicit `registered-source-map-v1` count and canonical digest. `_sources` still freshly authenticates the complete source closure. Legacy dictionary maps remain the exact original objects and legacy control flow reduces to its original AST. The unchanged 8,192-byte cap is not widened. The actual 19,902-byte failed start and prospective complete-expression shapes are covered by the retained bounded extent tests, with placeholders explicitly restricted to in-memory size checks.

New rendered identities, paths, source maps and complete receipts still require exact capsule preparation checks. Successful start serialization is not sufficient evidence of actual completion/readback. The final callback-free rejoin addresses ISM1 but does not compose the separately pending candidate03 cleanup correction; its source inventory is explicit about that limit.

No production module, NumPy/Torch, native guard, numerical job, claim or network operation was invoked. No source, old evidence, registration or ledger was edited. The closed first primary remains failed after genuine import completion and before any MCM target/scalar comparison. Source acceptance supplies no rerun, scientific, financial, capacity, paper-agreement or budget-transfer claim.
