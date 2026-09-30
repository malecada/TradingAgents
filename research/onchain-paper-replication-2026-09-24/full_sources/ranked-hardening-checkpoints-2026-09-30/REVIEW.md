# Independent isolated-component review

Accepted for the documented synthetic engineering scope after the restore cleanup correction. No remaining blocking defect was identified in that scope. This does not approve production integration, an empirical gate, a different pair capacity, or a capacity-scale checkpoint run.

Review inspected source, tests and saved logs without executing them, opening checkpoint arrays, or changing source. HEAD was `a301da699de42ec9d511c58cfeb99bc29ba505b0`. All 14 current compact bindings were independently rehashed with no mismatch; `bindings.json` SHA-256 is `7f2c64fdb386ef179d9f31f3c63bda22640b3ebba524192e004a2d2cac3d0a02`.

## Initial finding and retained history

**R1 — failed restore could retain an open mapping.** In the initial `checkpointed.py:111–112`, `np.load(..., mmap_mode='r')` preceded state validation without an exception cleanup path. A post-map validation exception retained the mapped order through its traceback; an interruption had the same ownership problem. Malformed compact phase/cursor metadata could also reach mapping unnecessarily. The required correction was to validate compact state before mapping, close any returned mapping on subsequent failure, and provide explicit successful-state disposal.

Initial source SHA-256: `38ec3a0b35cae8cac38d8a2b8f042d734c70154d3e118da3a197c4698f4bed3e`. Initial test SHA-256: `6226e40fa094fd0ae861b0a6315ecd851061c06fec475c374d3a8c0d3de010c2`. The original source, tests, implementation document and eight-entry manifest remain byte-exact under `pre-review/`. The initial four passing tests did not establish restore cleanup. `red02.log` retains two direct failures: the mapping sentinel was reached for invalid metadata, and a retained real mapping remained open after the post-map exception.

## Correction assessment

Current source SHA-256: `c0c4a2eb21ad62d3a966e8619d84370be388e1e4a402f7608fc91abb3f796312`; current tests: `96cb7bc8dee05672a5ea00239b5b98410e695b2a198a917784d4d5e53c3ac2df`.

`load` now invokes `_check_metadata` before `np.load`, and its `BaseException` handler attempts closure of the returned mapping while preserving the original exception. A secondary close failure is recorded as a note, not reported as successful cleanup. `close(state)` poisons the state before closing and then drops the order reference; a successful repeated close is harmless. These operations require the documented exclusive ownership: external aliases cannot safely access mapped data after closure.

The saved `green03.log` records six tests passing in 0.950 seconds. New tests retain the actual mapping object and prove it is closed after both `ValueError` and `KeyboardInterrupt`; they check primary exception identity, pre-map metadata refusal, successful explicit closure, idempotence and subsequent advance refusal. R1 is resolved. Secondary close failure and process-crash durability were inspected statically, not demonstrated by these tests. The every-boundary test still relies on object disposal when replacing earlier restored states; future consumers must explicitly call `close` and test that lifecycle rather than infer it from parity tests.

## Numerical, ownership and resource scope

Creation requires an existing native float64 C-order matrix and a 64-bit indexing runtime. Stable sorting of the negated row-major values preserves descending float64 order and row-major ties, including signed-zero ties. Taking the first remaining candidate whose row and column are unused is the same greedy selection rule as repeated masked global argmax. No value cast is introduced within this narrower input domain. The saved boundary tests compare exact ordered pairs against the accepted ranked hardener across tied, random, rectangular and empty tiny fixtures; no broad independent matrix campaign was run here.

Advance scans at most 65,536 ranking entries per call, retains the cursor and accepted pairs, and poisons state on an escaping mutation-path exception. Rebuilding masks and validating the pair prefix remain proportional to the accepted prefix, so this is an entry-scan limit, not a whole-call time limit. Atomic sorting, initial validation and hashing are not resumable.

The explicit creation allowance `17*n*m + n + m + 16*min(n,m)` conservatively covers the numeric key, ranking, finite-check and axis-mask/pair allowance on the admitted runtime. It excludes the input, native sort workspace, Python containers, allocation overhead and process residency. Retained order storage is `8*n*m`; hashing uses 1 MiB read chunks in addition. The 64 KiB manifest and asserted 128-byte NPY header give a logical checkpoint reservation of `8*n*m + 128 + 65,536`, not allocated disk blocks or total process memory. Metadata size is checked before creating the exclusive destination; file and directory fsync and manifest-last publication preserve a successful checkpoint, while partial failures remain retained.

Restore verifies the trusted manifest hash, exact policy and input-identity string, body extent/hash, and read-only order structure. It does not independently verify the external matrix after restore or replay the greedy prefix/permutation. The trusted publication and exclusive-file/state contracts are therefore substantive prerequisites, not optional security guarantees.

No empirical data, financial returns, scientific denominator, fees/funding, source exposure, production backend, cache identity or registered gate changed. Combined annealing/ranking/scoring integration, aggregate memory and disk admission, capacity-scale save/load measurement, crash recovery, full matching parity and real-graph feasibility remain untested and unapproved by this review.
