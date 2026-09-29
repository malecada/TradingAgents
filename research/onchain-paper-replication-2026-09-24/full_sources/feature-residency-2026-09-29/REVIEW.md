# Independent implementation review — feature residency

Reviewed September 29, 2026 against base `c0b3f244b4e4faa4434014dd065be8ebf0831dde` on `research/onchain-paper-replication-2026-09-24`. Scope is the ten source/test files identified below, supporting source needed to trace their contracts, and compact saved engineering receipts. No tests, empirical jobs, network calls or real array reads were performed by the reviewer. No registration, state, ledger or implementation was changed. Applicable AGENTS instructions, starting point, study state and governance/cycle rules were consulted.

## Finding requiring correction

**P2 — lazy hashing changes the identity of supported zero-dimensional arrays.** `tradingagents/research/onchain_replication/component_store.py:68` hashes the original mapped array shape. The eager hash at `evaluation.py:147–149` first applies `np.ascontiguousarray`, which promotes a scalar array to shape `(1,)`. Consequently, a saved `np.array(1., dtype=np.float64)` or `torch.tensor(1.)` has metadata shape `[]` in the lazy hash and `[1]` in the eager hash, despite identical element bytes. Both shapes are currently admitted by the component store. `FixedFeatureMap.verified_hashes()` or batch verification can therefore reject an unchanged supported scalar payload. The added parity tests use only a `(30, 3)` array and miss this case.

Preserve the existing eager identity by applying its scalar-shape convention in the streaming hash, and add zero-dimensional numpy and tensor parity regressions. No present graph-arm feature is shown to be scalar: the existing feature producers emit vectors or matrices. The finding limits the generic exact-identity contract; it does not establish a current empirical graph failure. This report preserves the initial finding and initial source hashes even if a later correction is made.

## Independently traced behavior

- Policy admission is explicit. `read_feature_policy` reads an admitted input and requires exactly schema version 1, mode `batch` and a positive non-boolean integer `max_batch_array_bytes`. Registered production compares the policy input name with the producer plan before the exclusive representation claim. `execute_fit_payload` checks the registered job payload and policy before representation computation. Defaults continue to select eager behavior. Residency is an execution choice and is deliberately absent from the scientific representation identity.
- Lazy members retain descriptors, not mapped arrays. Manifest/context/member membership, shape, numeric dtype, size and file hashes remain checked. Each use rechecks the member before loading or streaming, and again afterward. C-order iteration handles a Fortran-stored matrix without retaining a full contiguous copy during reference verification. Scalar promotion is the exception identified above. This is corruption detection under the existing immutable-store contract, not a hostile concurrent-file-replacement security proof.
- Journal ancestry still recursively checks failed sibling parents, hashes, owners, required graphs, workflow identity and cycle/depth. Graph completion cannot replace a completed graph; final feature hashes and required closure remain checked. Lazy mode changes completed payload residency, not the retained journal history. Intermediate samples, dictionary and unfinished numerical state remain eager. Before materializing an eager event, `feature_journal.py:111–113` compares its descriptor bytes plus retained eager state with the bound. Old alignment bases are dropped from resident state only after their component bytes have been checked; their stored evidence remains intact.
- Registered production seals and rereads the persisted journal before publishing a binding. Completed numerical work remains complete after a later publication failure. Continuation still requires a new registered failed-parent successor and complete attempts must use reuse. The new path does not restart a terminal run or silently refit a completed graph.
- `FixedFeatureMap.load_batch` deduplicates requested graph identities, checks their summed descriptor bytes before calling any materializer, and verifies loaded numerical feature hashes. Graph sequences then share the same loaded feature object for repeated identities within that batch. The map keeps no loaded-batch cache or learned graph embeddings. Successful training deletes inputs, targets, output and loss before requesting another batch; prediction deletes graph inputs and output while retaining prediction results. The changes do not detach trainable graph encoders or alter optimizer order.
- Streaming production hashes each fixed feature before releasing it and retains feature metadata rather than every graph tensor. Registered reuse reconstructs references from the completed journal. Source graph tuples, sampling and preparation scratch are still eager; the change is not an end-to-end graph-residency solution.

## Exact meaning of the memory bound

`max_batch_array_bytes` bounds the sum of the unique **stored fixed-feature arrays materialized by one loader call**. It does not bound every numerical array in `batch_factory` or total process memory. In particular, `evaluation.py:38–40` expands vector features into a repeated batch/sequence numpy array and a torch copy after that loader check. A single reused width-32 float32 vector costs 128 admitted payload bytes regardless of how many sequence positions subsequently repeat it. Price/target tensors, hash buffers, transient copies, model parameters/activations, Python metadata, mappings and page cache are outside this bound and still require the outer guard. The implementation owner explicitly confirmed this interpretation during review and will clarify policy documentation. This interpretation must accompany release claims; a claim of a hard total-batch numeric limit would be unsupported.

Similarly, `max_array_bytes` retains its component/journal role. It does not prospectively cap every allocation made by fresh MCM, sampling or static-embedding engines. Alignment bases and unfinished state can coexist with active preparation scratch. No full-size RAM, GPU, throughput or scratch-space feasibility conclusion follows from these checks.

## Evidence and verification limits

Saved `red01/child.log` records five intended missing-feature failures; `red02/child.log` records seven intended registered integration/release failures. `green01/child.log` records 25 passes; `green02/child.log` records 22 passes. Both corresponding green final receipts have child exit 0, verified cleanup and zero recorded memory-limit events. These are engineering suite observations, not financial observations. The two actual-job disposition tests present in the reviewed test snapshot were added after green02 collection, as disclosed in WORK_LOG; green02 is not evidence for those tests. Integration01 was not attributed a passing result in this review.

The new tests meaningfully probe: no copied payload during lazy C/Fortran matrix verification, post-verification member corruption, within-batch graph object sharing and weak-reference release, rejection before loading an over-limit set, streamed GIN producer release, registered policy rejection before claim, GIN production/reuse binding parity and exact output/gradient/Adam state parity, failed-parent graph preservation, and training/prediction release before the next batch. Existing component/journal tests provide useful eager compatibility and closure coverage.

The initial tests do not establish scalar-array parity (the finding), lazy failed-parent alignment continuation for node2vec/watchyourstep, or lazy motif/MCM production and joint fitting combined with the optional activation-checkpoint path. Exact GIN parity does not itself prove every representation/comparator combination. No CUDA or full-sized residency execution, real-data source admission, economic accounting, leakage/return result, or full paper replication was evaluated. Existing full population, denominator, frozen configuration and pending empirical requirements remain unchanged. No empirical release is recommended by this report.

## Initial reviewed file identities

Source paths are relative to `tradingagents/research/onchain_replication/`; test paths are relative to `tests/research/onchain_replication/`.

| File | SHA-256 |
| --- | --- |
| component_store.py | `55981ff27dcfbc80d29e318bd5aea84b307da29fb1cc067af8af379125a5a6e0` |
| feature_residency.py | `e8a53714255f56f43ced904a1f6700e7506d118f98e2486e3004593ab0cd6ae1` |
| feature_journal.py | `d997b27bf3c5d5a1db0c77a6ce5bf9ed696800a4c88300634eec3efed349ff59` |
| feature_pipeline.py | `e1f7b9336ae7fac8ed6da0e20d2c3a5d0a3599db5bb6c150820066a0d18af13d` |
| registered_features.py | `3121eae17fee805e60f54e02bc6c009672608b506b03c10450412f8cee86f784` |
| evaluation.py | `b3af7cf6b71f8adcdd762eb471abb66d8fdd00f20087aeff377447d51a854b29` |
| job_payload.py | `a7d8066c5d88a7b7c015868b0e74a4d4bc4ec9c6a5fbe9ac23cadc62f5cfefcb` |
| training.py | `5c0380de62c670d356ea3546c7b81eed4ccab55a886bc27b6a1bbfd75c2c3369` |
| test_feature_residency.py | `67c9e8c71b34844e313da0f4dc693a78cdfe2fb8cb16912a372e54c3028d4bf6` |
| test_registered_feature_residency.py | `4273fc25c965440ea78917ca8b5651702387281fadf6d3e6de79138ca8cf8176` |

## Correction review — scalar identity and explicit loader policy

The initial finding and hash snapshot above remain unchanged. A subsequent bounded read-only review checked the scalar correction, policy rename and expanded test source. No reviewer test or empirical execution was performed.

**P2 is resolved in the corrected source.** `ArrayReference.feed_hash` now records `array.shape or (1,)`, matching the eager scalar promotion while retaining the original shape for every non-scalar array. The stored descriptor shape and materialized scalar itself remain unchanged. `red03/child.log` independently demonstrates the two intended pre-fix numpy/tensor scalar hash failures. `green03/child.log` records those scalar cases passing; its separate alignment-test failure does not negate their result.

The new, not empirically used policy field is now `max_unique_feature_bytes`. Exact-key admission, both registered constructors and test fixtures use the new name consistently. The `feature_residency` module explicitly documents exclusions for vector expansion, prices/targets, model state/activations, transient copies, Python metadata and page cache. This makes the narrower loader contract explicit; it does not reduce the study's memory or empirical requirements. `PreparedFeatures.features` is now annotated as `Mapping`, correctly allowing eager dictionaries and the lazy map without a runtime behavior change.

`integration01` independently records 58 passing tests, child exit 0, verified cleanup and zero memory-limit events, including the previously unverified job-disposition tests. It predates the scalar/expanded-alignment correction and is not evidence for those later tests.

The expanded registered parity test now exercises both GIN and actual proposed-model dictionary/MCM production, with graph activation checkpointing enabled for eager and lazy joint updates. It compares the complete representation binding, output, every parameter gradient and post-Adam parameter state exactly. These cases passed in green03. This extends the prior GIN-only evidence to the proposed CPU checkpointed residency path; it does not establish CUDA parity or all comparator/configuration combinations.

**Green03 is a retained failed test run, not a passing suite:** 17 passed and 1 failed, child exit 1, verified cleanup, zero memory-limit events. The Watch Your Step failed-parent case reaches successor production but fails at `test_registered_feature_residency.py:97`: the assertion compares 103 new alignment snapshots with 9 required feature payloads. Static pipeline reconstruction explains the mismatch: the alignment closure includes all 104 causal intermediate snapshots, whereas only 10 snapshots are required as final features. The prior completed graph was not republished. The expected successor identity sequence should be the uninterrupted binding's alignment order after its first graph, not the required-feature subset count. This is a test-oracle defect; reducing the producer closure to satisfy it would violate the existing ancestry contract. The later binding-equality assertion did not execute, so interrupted alignment parity remains unverified until that oracle is corrected and checked in a new retained run.

Corrected-source hashes at this review:

| File | SHA-256 |
| --- | --- |
| component_store.py | `ba0cf44dd7cf5af8c0b99cbe129f107ef7b40833a76b8162ae9d91512b566b68` |
| feature_residency.py | `4ea5370958b65edf0d37950f12d358ab562291c786f28a287514c77c3838ddcd` |
| feature_pipeline.py | `3934a425d19d2245f21edb145c411a7a6b03f484c40df8d6063f14cf1590dc63` |
| registered_features.py | `fa62c8470053a5d034c297805d814c82af2ab19c0fcb8559aada239327700ca7` |
| test_feature_residency.py | `7853bb768bbc8d7f2c5a48888f29447869c586b6a377c2829acbdde9100e02b4` |
| test_registered_feature_residency.py | `7868fabf56cf1928ae95cf428c6284ca08a0de3cd6a32e204d1f9e9432b5f421` |

The other four reviewed source hashes remain as recorded initially. No new production-code defect was found in these corrections. Full source-graph residency, resource feasibility, GPU execution and empirical release remain unresolved.

## Alignment verification closure

The later test-only correction explicitly expects this fixture's 103 successor alignment graph completions for Watch Your Step (104 causal snapshots including the retained parent) and 9 for GIN (10 required feature snapshots including the parent). The no-republication, verified feature-hash and exact uninterrupted-binding equality assertions remain in place. Complete binding equality includes the full causal alignment order, feature hashes and lineage; the correction does not shorten the production graph closure. Production source hashes are unchanged from the correction review.

Independently inspected `green04/child.log` records **1 passed, 10 deselected** for the Watch Your Step case. Its final receipt records phase complete, child exit 0, verified cleanup and zero memory-limit events. The binding-equality assertions therefore executed successfully. This closes the outstanding interrupted Watch Your Step residency verification gap for the bounded synthetic fixture. The prior green03 failure and its mistaken subset-count oracle remain preserved above.

The corrected registered test hash is `7e6be2751c908f16e3e4c53cfdc390722490f2ada6922c5fb039dea2075994ec`. All ten entries in the frozen `source-bindings.json` were independently rehashed and matched current source/test files. No new material issue was found. Named offline01 is pending at this closure and is not attributed a successful result here. GPU/full-size feasibility, direct node2vec lazy continuation coverage and empirical completion remain outside the demonstrated evidence.

## Terminal named-offline addendum

The earlier pending offline01 statement is now superseded. Saved log independently records standard **2,747 passes plus 97 subtests** (1,114.07 seconds), followed by isolated neural **525 passes and 2 skips** (422.10 seconds): **3,272 total passes plus 97 subtests, 2 CUDA skips**. Final guard independently records phase complete, child 0, verified cleanup, 1,540.0154409609995 seconds, 2,133,311,488 peak sampled bytes, no limit reason and zero memory-limit events. All ten frozen source/test hashes still match. No verification was rerun by this reviewer.

This closes the named engineering profile on the reviewed source snapshot; it is not the withheld legacy suite, fresh clean-environment replay, GPU parity, full-size feasibility or empirical release. Existing graph-residency, resource/admission and study-completion limitations remain. For precision, the initial report's “Adam state parity” shorthand means post-Adam **model parameter** parity: the test does not compare optimizer moment-buffer state, as the later correction section and RESULT.md now explicitly state.

Final receipt SHA-256 `53957ea99d8e5fd8779bcf8903c3abd783e7566d27f78349bfae069a66999794`; log `29f5a6d210cb43087ba41387c109e5cc3534365dbb3eb83d57172f122cb0d192`; source-binding manifest `6c79f0e86fb2ebf823d69c835e7c8c6ef8f75c5ee435232c36a14a4fd75d0a1e`; reviewed RESULT.md `0bb6b4b05cb9c9cb99b22e20520d0f1a873b18eb63ac66db74ae7b1a0300ee39`. No additional material issue was identified in this terminal reconciliation.
