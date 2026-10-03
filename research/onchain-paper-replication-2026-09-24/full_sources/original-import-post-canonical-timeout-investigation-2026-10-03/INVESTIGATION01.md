# Post-canonical original import timeout: exact residual source loop

The strongest concrete remaining optimization seam is **historical claim source authentication in `tradingagents/research/verify.py:76–84`**. This loop still spawns one `git show` per pinned source/charter for every historical claim, despite batching in current admission-source checks and the numerical anchor. The proposed change is bounded fresh batching within each invocation of this loop, preserving every claim verification and every original byte/hash comparison. No caching of successful claims, change to the number of Owner/Binding/runtime checks, numerical setting, sample, motif or pair is proposed. This is a static cost finding, not measured attribution of the1800-second timeout.

## Authenticated closed evidence

The exact executing capsule04 source was `ce0e37f8eaaca258c46944a4cbdb9ae30e40fa26`. The selected current original_dictionary wrapper is canonical candidate93c0cd1ae882d51df185458ce7304a46dfb66dc7ca337285039541fa70176e88. Actual identity `original-import-native-success-20261003-04` is permanently failed; it must not be rerun. `EXECUTION_PRIMARY01.json` SHA bbf573de6a92b66fb6d707e07c71c3d7d2d9c0fbd5c49765d8b26999aefd6cdf records native elapsed1802.3540939379964s under1800s policy, sampled peak395,300,864B, all memory events zero, native timeout and zero completed MCM stages. These are process/resource observations, not sufficient capacity or performance success.

`census01.py` checks the retained inventory SHA against the execution receipt, the actual04 claim SHA and each inspected source against the claim's162 selected source pins. The retained inventory has1058 members:750 files/308 directories,7,301,050 logical bytes. Source files total2,848,285 bytes; registered inputs total997,256 bytes by stat only. Array and binary score bodies were never opened, hashed or decoded in this investigation. Selected receipt JSON bodies were bounded-read and rehashed against retained inventory references. Existing recovered/off-laptop verification is inherited from coordinator evidence, not repeated here.

Original dictionary import has a retained complete marker, SHA03d7a36fa8a1b1a193f587a87961d93180ad95295dad39fc8973a26aa549f806. One MCM stage/stream started. Its first matching event member is2856 bytes; the selected fixed layout is168 bytes/record, giving17 record-width slots. Its first unsealed score tail is640 bytes, or8 slots at80 bytes/record. There are no score batch chunk payloads, stream terminal or complete MCM marker in the retained membership. This is structural progress only: no binary event kinds, checksums, scores or iterations were decoded, so eight verified successful pairs or an exact ninth-pair interrupted instruction is not claimed. Two original source-cell dispositions remain failed/unavailable, authenticated by coordinator and rehashed here; the worker's complete registered cell ledger/journal/summary is missing. The original lifecycle/outer failure is not relabelled successful.

File mtimes are recorded only as filesystem metadata. No method duration, exact interrupted PC or causal wall share is inferred from them. Original PID/cgroup absence is coordinator-observed in ROOT_PROCESS_ABSENCE04, not a new process probe. All four closed failures and unused dependent publication-failure case remain preserved. Paper36 closed attempts/highest64 and every budget remain unchanged.

## Residual repeated work after canonicalization

The selected source still has the same successful-path expansion cross-checked by AST in census01:

- CompactMatcher._check calls its live lease and PairLog._check, whose live lease repeats the path: two Target leases.
- Each Target.lease calls ImportedExecution.check. ImportStage.lease invokes PreparedImport._check once; execution_contract invokes it twice directly and once through stage_contract: four prepared checks per Target lease.
- Each prepared check performs full Binding.check and original capability.check. The capability validates all512 parsed samples/32 representatives and reads all11 original metadata roles both before and after its authority callback.
- Therefore one successful matcher check contains at least8 original validations,8 full Binding checks and176 original-role reads. Canonical candidate reduces membership graph serializations to8×544=4352, retaining8×16384=131072 ordered membership comparisons. It does not remove parsing, full sample validation, semantic hashes, original-body readbacks or authority checks.
- Each prepared check includes one Binding.lease from Binding.check and two more through original capability pre/post callbacks. Each Binding.lease calls the guard twice. This gives at least24 Binding leases/48 guard checks within this portion of one matcher check; other stage/Owner/final callbacks add further work.

Binding.check still calls ResearchRun._check_source→admit, rehashes all registered inputs, authenticates the numerical anchor, inventories runtime and leases. `environment.inventory` here checks five package versions (NumPy/SciPy/PyArrow/Torch/scikit-learn), uv.lock and Torch/CUDA metadata. It is **not** the separate251-RECORD root runtime checker. This distinction avoids attributing an unexecuted operation to the timeout.

Current `admission._source_files` is already batched in128-file groups with an8MiB body aggregate; the matching-owner numerical anchor is also a fresh batch. Those should not be mistaken for the remaining per-path loop. Owner/import integrity also hashes/compares completed metadata and original materialized motif arrays, and rederives current workload identities. Their timing is unmeasured. Numeric `engine.advance` still validates state and runs the exact original annealing/hardening schedule; its real call count/arithmetic cost is unknown here. The selected one-million-operations allowance/10,000 calls-per-checkpoint/max-one-checkpoint policy explains why absence of checkpoint files alone is not a checkpoint-policy failure.

## Concrete multiplicative Git source proof

Selected `verify.py` SHA a520a756ec3fa126f56ec1c694851b6f46416e462228eb51a6954385b449f439, `verify_claim` at28 and pinned-source loop at76–84:

```
for path, expected in pinned.items():
    for commit in {claim['source'], claim['design_source']}:
        compare_sha256(_blob(root, commit, path), expected)
```

`_blob` starts an uncached `git show` at23. `admission.claims` at188–204 invokes verify_claim for every actual prior/current claim; admit calls claims at317. There is no cached exemption for the current claim.

| Retained claim | Distinct pinned source/charter paths | Distinct source/design commits | Git processes in this loop |
|---|---:|---:|---:|
| success01 |154|1|154|
| success02 |157|1|157|
| success03 |160|1|160|
| success04 |163|1|163|
| One claims scan |634| |634|

The original claim JSON hashes are checked against retained inventory; only their source-map key counts and source/design identities are used. `count_claim_loop01.py` executes the **actual extracted source loop** with scalar synthetic byte-return stubs, not a counterfeit genuine claim or Git repository. It observes634 stub calls for one four-claim scan and5072 for eight scans. Real historical body hashes are not replaced at admission: this is explicitly a static invocation-count check. Registration/design-registration reads and extension/review reads add14 more `_blob` calls across those four verify_claim invocations (648 total for that path if all complete), before other admit/Git work. Thus634/5072 is a conservative narrower count, not a claimed complete runtime process count.

Each source authentication remains necessary; subprocess-per-member is not the semantic requirement. Reusing one fresh Git process per bounded group can retain all634 body authentications and all repeated checks. No empirical speed factor follows from the reduced process count.

## Exact proposed next source delta and proof

Implement only a new private helper in `tradingagents/research/verify.py` for the pinned-source loop, analogous to the already reviewed binary-safe admission batch reader but retaining verify._blob's path/commit/secret validation. Its request order is the same `(path, commit)` iteration, with fresh body acquisition per verify_claim invocation. Validate every original expected SHA, object type, framing/size/count and full response; no cross-call result cache or omission when source equals another claim's source. Preserve registration, charter/selection overwrite semantics, family/exposure/budget/current claim logic and bindings unchanged. Keep immutable original claims/Git bodies and use a new executing source only.

Finite groups of128 requests and8MiB aggregate bodies can use batch-check before exact-body batches. Oversized or unrepresentable line-protocol paths require an explicitly reviewed fallback retaining original argv validation/semantics, or a separately declared strict refusal; neither may silently skip verification. Subprocess/error-order/timeout/temporary-memory changes must be declared. Missing/wrong-type/short/trailing/dead subprocess and first-fatal cleanup require exact-source sentinels. Full other-AST parity and unchanged return claims must be proved. A helper importing admission and thereby weakening independent verification or creating cyclic authority is not the proposed route.

Minimum engineering test denominator before any real use: all four retained metadata key-count shapes, same/distinct source-design commits, duplicate path shared across claims, source/charter overwrite ordering, invalid/secret/newline path, missing/non-blob/wrong-hash/partial/trailing/oversize batch, fresh second invocation with changed source response, and first actual fatal plus cleanup uncertainty. Tiny generated Git fixtures may later prove actual framing and byte equivalence under a reviewed offline release; no original numerical job is needed to validate this source helper.

Instrumentation is optional after that concrete source correction, rather than a prerequisite to identify it. If causal wall shares are required, the smallest proposed genuine profile is a separately registered engineering question with one imported original32-motif dictionary/one fixed target, one complete Target.lease and one CompactMatcher._check, followed by one original scalar pair with the full original matching configuration. It is not a completed64/160-cell MCM proof or a rerun of04. Exact cases must report attempted/failed/unavailable if any boundary fails. Keep all callbacks/source/input/runtime checks in order. A finite timing record can separately capture verify_claim pinned-source read, admit, Binding source/runtime/input checks, original validate, full live lease, engine.advance and score-only, with inclusive nesting explicitly distinguished from exclusive totals. Bound category count, stack depth, record size/publication count and probe deadline before launch. Avoid per-event arbitrary JSON output or changing scientific RNG/operations. Root must separately review identity, budget, native limits and source instrumentation; no such job is admitted here.

No time-share, full-population throughput, RAM capacity, scientific completion or numerical agreement is established by this investigation. The exact helper seam and bounded source proof can proceed independently without guessing a longer deadline or spending another matching attempt first.
