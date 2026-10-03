# Independent review — cold handoff outer preparation01

Decision: **WITHHELD**. The frozen source has two material correction groups, CO1 and CO2. This is a source/stdlib review of a different author's preparation, not a genuine native run or a numerical/financial verdict.

## Reviewed freeze and scope

MANIFEST01 SHA256 `e687bc2718f9e1ee2ba4e58e4739133bca2e72e87ee3dbec8c47444ad5c2aaa5`: all20 bodies and112569 bytes independently matched. Install map SHA256 `b99d2f86dc6a4191a9363f92d3bad7c1aa71fa9f6ad7d57b6dc2c8f6722040ed`: all6 eventual proof_tools bodies and73381 bytes matched. Protocol `cddf3de569243b5c8431a5533593120efcc9f46e7ed2216857286408ab7a45c9`; report `65741e3a418f5420e041a364589c0fcccd70dc06ef63f3accd059e15d9d65fae`. Author source, tests, reports and manifests were not changed.

Inspection covered proof_release01, proof_supervise01, proof_outer01, proof_raw01, runtime_gate01, draft builder, both test files and the selected baseline helper fragments. The current source itself uses a real job launch/worker command and separately describes materialization and comparison. The new metadata/native/document bounds remain8192/65536/4194304 bytes respectively. The whole writable capsule has sampled1GiB logical/allocated limits, finite cardinality/depth and10GiB floor; this is not a hard aggregate kernel quota. The native worker contract remains3GiB high=max/swap0/2CPUs/1800s with4MiB file limit. Supervisor/controller loops and final accounting have finite declared limits; actual full-tree/OS enforcement is unexecuted.

## CO1 — prior materialization is not reauthenticated before comparison (high)

`proof_release01.py:50–65` dereferences accepted/wait/authentication summaries but does not authenticate the prior materialization ResearchRun, registration, native/raw closure and actual emitted-input denominator. Neither accepted.source nor wait.source is joined to the comparison source. The prior release reference is only tested for mutual equality, not resolved to the original source/registration/native contract. `observed.proof` can contain only kind, scientific_completion=False and future_inputs; the input loop accepts a population-only document. Matching a hash supplied by such a document proves its bytes, not that a separately admitted genuine materialization produced them.

An exact-AST extraction of this branch accepted real tiny files containing those minimal summaries, a fake population-only future-input document, absent research_runs, conflicting current/accepted/wait commit strings and an invalid prior release reference shared by the two receipts. Both selected process IDs were absent. This does **not** claim a full released check_release/job invocation was run: the fixture isolates the exact prior-evidence checks, and the preceding current-release checks do not add the missing prior-materialization authentication.

Required correction: before comparison can enter the producer path, resolve and authenticate the original materialization release/registration/source/runtime/native/raw/ResearchRun completion and exact future-input population using the proof-specific original contracts. Join controller/supervisor claim, child identity, actual wait receipt and release/source identities; reject conflicting commits, absent original evidence and reduced materialization input populations. Reuse the actual materialization/lifecycle/native validators as appropriate with a separately validated historical context; do not call current one-use admission against a closed identity or replay the job. The earlier original materialization must remain closed and preserved. An independently reviewed release may pin retained evidence but must not substitute labels/self-hashes for these joins.

## CO2 — supervisor loses the first actual fatal (high)

Two reachable source boundaries require correction:

1. `proof_supervise01.py:20–22` uses `proof_raw01.py:19–20` preserve, classifying every non-Exception BaseException as a true fatal. The actual selected `owned_io.CleanupFailure` represents ordinary cleanup uncertainty and is itself a BaseException. If it is selected first and a later operation raises the first actual MemoryError, the wrapper wins. An exact-source class extraction plus the actual preserve function reproduces this. The controller already has a type-aware selector; the supervisor needs the same source-authenticated distinction rather than an unrelated fake wrapper type. Its `_native_receipt` writer can reach the selected owned cleanup boundary.
2. `proof_supervise01.py:25–27` wraps parent-directory fsync in `finally: os.close(fd)`. A MemoryError from fsync followed by ordinary OSError from close escapes as OSError before retain sees it. An exact-AST extraction with sentinel functions reproduced the identity loss and verified one fsync and one close call.

Required correction: acquire/close each owned descriptor once, independently preserve the first actual fatal, and retain ordinary cleanup uncertainty if no actual fatal occurred. Do not use optional diagnostics/exception formatting that can introduce another masking boundary. Authenticate the canonical cleanup class under the existing capsule/source contract. Add mixed-order wrapper→fatal and fatal-fsync→ordinary-close sentinels against the actual supervisor reducer/FD boundary. Preserve the one-use refusal and best-effort process/descriptor cleanup contracts.

## Positive inspected boundaries and limits

The controller independently observes the native launch, attempts controlled process/unit cleanup, reads original native and lifecycle evidence, then calls the proof-specific materialization/comparison validator. Comparison source inspects Binding/Owner/Published/scientific terminal and raw artifact references, checks the fixed representation/population/weak-reference/checkpoint denominators and compares bounded opaque ZIP members without unpickling. Runtime checks bind capsule import origins and selected dependency RECORD hashes; RECORD hashes are not a claim to rehash every installed dependency body. New receipts are compact paged references instead of widening scientific metadata limits.

The supervisor actually polls/waits its controller and expressly does not claim its own death. Root still must observe the supervisor's real terminal result and recover the final tree. These positive boundaries do not close CO1/CO2 or establish successful native/scientific execution. No independent numerical equality, gradient/Adam/checkpoint correctness or full resident/cold capacity was measured here.

## Checks, retained failures and remaining release requirements

`review_counterexamples02.py` completed all three actual-source fragment reproductions. It asserted that NumPy, Torch, SciPy and tradingagents were not imported, and did not start subprocesses, claims or native units. Its first draft `review_counterexamples01.py` had a syntax error and is retained unchanged with its failure log.

Initial direct authored-suite discovery ran20 tests but failed its broad `*.py` compile test because the retained reviewer syntax-error draft was in the same directory. That is reviewer evidence contamination, not an authored source failure. The exact20 manifest bodies were then copied unchanged to a disposable tiny directory and the same authored suite ran20 tests successfully in0.073s. Both logs are retained; the failed draft was not erased or silently repaired. This qualification matters because the author's tests do not cover CO1 or the two CO2 boundaries.

No production, registration, STATE, runtime, source HEAD or prior source candidate was modified. No numerical imports, native jobs, claims, network or external backup actions occurred. Independent review of a corrected frozen successor, complete capsule/gate/runtime/input binding, actual separately admitted materialization then comparison, real native cleanup/outer-exit evidence, full watched-tree accounting, and off-machine recovery remain necessary before a success claim. This review provides no paper financial-fit or27-refusal-suite progress.

## Reviewer evidence hashes

- `review_counterexamples01.py`: `c6cb90274302e8af8398454a557df37c05d54a0b707cf6d0d7cf5c6b4317a8a1`.
- `review_counterexamples01.log`: `a02a83464693ddaf7027cc97cb25869e5c211689f470a1d396c1068e89daacc3`.
- `review_counterexamples02.py`: `044c659c64eef14c34eda246e7a7f4679d60538489b17d8e8f8d76b2488f8a03`.
- `review_counterexamples02.log`: `e17b1a64d63b63ee83fc964bc029e238a37ccb50116395c573f25b307a9ea99b`.
- `review_corpus01.log`: `b84817bca6fbd9e545ab461e73a7c0d500b61511b3a5051efc8f2d452c0d064f`.
- `review_corpus02.log`: `68ee7547d43a223f387fa0498db5c8d235f4ef6f4cb52b5c3c3e604e93d45c22`.
- `review_integrity01.json`: `5b5a0aa7b2b6f7d1058b91ed066b46c619f1df45c7011d9d89f8cf076ae55d50`.
