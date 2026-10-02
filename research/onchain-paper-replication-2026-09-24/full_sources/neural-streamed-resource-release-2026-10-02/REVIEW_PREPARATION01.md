# Independent neural04 preparation review

Disposition: **accepted as prospective preparation, including the explicitly declared scheduling amendment**. This is not a completed gate/admission, resource-capacity result or authorization to reuse a closed identity. Exact final source/runtime/input/budget binding, external recovery, registration review and actual admission remain pending. No material configuration inconsistency was found in the reviewed preparation.

Review used read-only source, JSON, hashes and preserved pure-test logs. No numerical imports, tests, RAM observation window, workload, guard, admission, claim or commit was performed. Only this review was written. Root retains sole launch ownership.

## Exact reviewed preparation

- CHARTER.md: `369d6d61d28fe5448216bc5fcd023dd2847a55dd033ed1eb247559a567372fc2`.
- neural-plan.json: `b82fc3634ad17d6fa633d4c62c4026211911ee685031a219873e65294ae5bfc2`.
- execution-job.json: `7a3ebe37bce0a5e412e17d0991f3a754ba7a7a8b53e33cda258e516b935bd8a0`.
- launch_scheduling.json: `5c0b225570a3d4a00385c88c5bb6fc07616bad14719d7c44365891bb4e410d21`.
- readiness.py: `df2e97c33e3be4d05396d533ad795f945ad47735d054ae7d0c6fded4e2c6040b`.
- launch_once.py: `8a2becc3e751dc1576a38bdbfe30c4ad32fedc862fddd650ee35016b3e791b42`.
- test_readiness04.py: `c19b9a8683b94c1130881c6c439a8337fb8d638f6816847ae99c92e9ebacf2e7`.
- readiness-red01.log: `97895840ec0dcecad13fd38cf87af820e9027e89f276125b5dc81b8a748477c0`.
- readiness-green01.log: `b46c34aa336a0196b9653936223ed59d303777630f028a43264f84c3b9d04223`.

Original readiness and scheduling copies are byte-identical to the closed03 release: helper `6606cf9bb0e97e11f87129fe577e2c3a41905027d43996afe4a764d7f13a64bd`, policy `6b96747b70d2065dd24070544ec02d71474f7137553f6cf7db3fd5b15540b8e0`. The new helper differs from that preserved helper by exactly one integer minimum,7,516,192,768 to7,247,757,312 bytes. The caller differs from closed03 only in the prospective experiment identifier ending04. The selected job is byte-identical to closed03.

## Resource amendment and remaining practical risk

The exact arithmetic is4,026,531,840-byte worker maximum plus3,221,225,472-byte host reserve =7,247,757,312-byte hard startup minimum. Old scheduling added268,435,456 bytes; the new scheduling condition removes only that extra256 MiB. It does not increase worker memory, lower host reserve, weaken zero-swap enforcement, alter memory.high, disable pressure protection or modify the independent hard startup check.

This is a real prospective scheduling relaxation and is appropriately stated as such, rather than described as unchanged readiness. It is compatible with `job.resource_policy`, which permits start_reserve equal to maximum plus reserve and requires at least3 GiB host reserve. `resources.guarded_run` independently checks startup memory before unit setup and again before workload release, then monitors ongoing host reserve. Memory.max=memory.high remains3.75 GiB. No hard policy requires the optional former scheduling margin.

Removing the margin reduces tolerance for new coordinator/supervisor allocations and unrelated host changes between observations and release. The full workload may still be refused during native setup, fail under the unchanged kernel cap, or be stopped for ancestor/host pressure. A passing fresh window does not reserve physical RAM or establish capacity. Current6.8–6.9 GiB availability in the charter is motivation, not a retained launch permit or a value independently sampled by this review. Do not disable OOMD or relax protections if the narrower margin proves insufficient. Once a claim is actually made, failure remains spent even if numerical cells do not complete.

Other limits are unchanged:10 GiB disk floor,7200-second guard deadline, zero swap passed explicitly by job.monitor, two-CPU enforcement/readback, physical allocated160 MiB/logical128 MiB/128 entries,8 MiB per-file cap,256 KiB JSON cap and32 MiB terminal reserve. The plan retains600-second cooperative per-cell limit,4 MiB checkpoint,1 GiB graph and64 MiB output bounds. Actual native enforcement and controller availability must be reported from the eventual receipts, not inferred from requested unit properties.

## Readiness and sole invocation

The helper keeps16 observations at least two seconds apart, a60-second logical observation window and expiry within one second of the final read. It rejects noninteger/bool memory values and any modified policy field/type. The bounded native reader accepts one correctly formed MemAvailable line from at most64 KiB. Logical deadlines do not preempt a blocked OS read or scheduling delay; delayed completion is refused by the subsequent time/freshness checks.

Preserved RED shows two policy-rejection errors and one pass when the old helper receives the new policy. GREEN shows all three pure fake-clock cases passing. Those cases exercise the full minimum-threshold window and1.01-second expiry, immediate below-minimum refusal and fixed reserve/count/policy-type checks. They do not measure host RAM, execute the guard or add new empirical evidence. The broader algorithm,60-second check and original fatal propagation are unchanged; no numerical test was rerun here.

The caller performs actual metadata admission before a new in-process observation, measures the exact claim and authority RPC extent, authenticates its own/helper source pins and policy hash, and writes immutable observations. A deferred/expired readiness result does not invoke the job CLI or reserve an empirical namespace. Before the sole CLI call it checks all three namespace paths, current HEAD and disk floor, then checks freshness again after opening the bounded outer log. No sleep or repeat invocation is introduced. Preserved receipts cannot be reused as a future permit. Final execution must use the current admitted full commit and a newly observed window; absence now is not durable authorization.

All three prospective04 empirical namespace paths were absent during review. Terminal03 and earlier failed identities remain closed; caller identity04 is not a rename/relaunch of them.

## Original numerical workload and implementation boundary

Independent whole-object comparison with closed03's pinned plan confirms all nine cell objects—including exact IDs, graph manifests/hashes, config hashes, node-order hashes, node/edge counts and weeks—are unchanged. All prior plan fields are unchanged except schema_version1→2; the sole new model_execution object explicitly selects schema1/streamed-gat-mulsum-v1/block_edges65536. Graph activation checkpointing remains false. Scientific model configuration is not rewritten by this plan.

The selected streamed module is exact candidate02 `e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f`, with original multiply/sum node attention and bounded first-order weighted-aggregation recomputation. Existing source confirms seed11,32-column float32 synthetic MCM,16 repeated28-step sequences using one unique graph, classification/cross-entropy and one Adam0.001 update. This is a full retained graph resource question with synthetic features/labels, not fitting genuine completed MCM features or a financial model. No cell omission, neighborhood sampling, dtype reduction or test-accuracy tuning follows from capacity trouble.

The accepted candidate02 thirteen-check child evidence and its failed parent stay separate. Native cleanup smoke confirms the corrected owner branch. The now-accepted actual adapter02 review is `79cf9b5fbbda0166be16a5bf79ba2cb2e08bf35ebf764b48a77ba6115533dc23`; its four tests and complete parent/child/guard closure satisfy the finite adapter prerequisite, with mocked-admission/full-size qualifications preserved. Pin that actual result/review and recovery rather than treating the charter's still-conditional adapter paragraph as evidence by itself. Previous adapter01 remains failed.

## Budget and final release obligations

The immutable accepted64 callback documents were independently rehashed: extension02 `72561ea7648e43c5ee81f1d99a00c52091d0664827df4a3ba970e3c9ec654fc8`, allocation02 `d238ffd07c4f183b447509ffd967c928944c4dea95e77c88d4d2a102250765a8`, accepted review `0ff87a42b58659c8791eeac1673cf89997eaf268b344a2be8a33aee18a3189bc`. This scheduling amendment changes neither that single prospective streamed resource question nor its category/attempt allocation.64 remains35 spent +12 body +15 financial +1 neural +1 other; current adopted ceiling remains63 until actual04 claim. Full fresh population/claim/terminal rehash belongs to the final exact gate review/admission and was not repeated in this bounded preparation review.

The final gate must preserve complete original ancestry including closed03 as parent, all spent/unavailable history and original family; source-pin all three budget callback documents; bind new charter/plan/job/scheduling/helper/caller and accepted finite proofs; include actual complete Python closure with streamed_gat and all parent initializers, required runtime hashes and original metadata/graph bindings. A count alone is not closure proof. At inspection the onchain subpackage has126 Python files; full required closure also includes parent modules. Final source may not be inferred from stale earlier132/133 counts.

After exact gate assembly, require independent final review, committed externally recoverable source and evidence, actual admission with exact claim/RPC below256 KiB, fresh relevance/population and namespace checks, sustained readiness and original native guard release. The later actual resource result must retain all nine durable dispositions, failure/unavailable cells, bounded phase journals, checkpoints where completed, cleanup, full final physical denominator and outer logs. No automatic follow-up allowance, capacity guarantee or paper agreement follows from this preparation. Twenty-eight distinct training graphs, real MCM production,23 other resource cells, broader asset/history/comparison coverage and all45 initial/1,420 total financial fits remain outstanding requirements.
