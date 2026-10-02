# Tiny streamed whole-graph checkpoint proof — preparation only

This source package prepares one finite synthetic engineering proof comparing the already installed streamed GAT backend with the existing complete GraphEncoder checkpoint option false and true. It is not executed or numerically accepted. The underlying original scientific model JSON remains byte-identical, SHA256 `20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d`. No production policy is widened: current neural-resource schema2 and financial candidate02 still refuse streamed checkpoint=true. No empirical65, full-size resource successor, cap ladder or financial model fit is admitted.

The read-only investigation is `neural-checkpoint-successor-investigation-2026-10-02/INVESTIGATION01.md`, SHA256 `ae5f37cfa48bd03b3077a46c994fefaae1d9d30c8f568357ab253643f2dedf23`. It explains why whole-region recomputation can retain fewer first-forward activations while still reproducing or exceeding the old backward peak. Passing this tiny proof must not be described as full-size capacity.

## Frozen numerical question

`protocol01.json` defines the complete fixture, tolerance, finite cases, modes and bounds before outcomes. CPU float32, seed11, batch16/lookback28, unchanged MLP/GAT/LSTM/attention widths and exact streamed policy (65,536 edge block maximum) are fixed. Primary cases change only explicit graph_activation_checkpointing. A separately named dropout0.2 diagnostic changes that one additional original dropout value; it is never relabelled as the paper-primary configuration.

The five cases are: fixed MCM with two shared weekly graph objects; identical fixture with MCM input gradients enabled; two-graph dropout/RNG diagnostic;28 distinct graph objects; and two-graph regression-head coverage. Graphs contain3–5 nodes, a directed cycle and one explicit self edge. Every graph index has different deterministic MCM values. All16 examples share the same graph objects; weekly membership changes every seven positions, while the28-distinct stress uses one per position. This tests complete multiple-graph gradients and within-forward reuse, but it is not the actual empirical weekly-membership census. The final two positions of example zero are masked with None graph inputs.

Float32 comparisons retain rtol1e-5/atol1e-6 from the accepted streamed protocol. Initial parameters, initial RNG, all nonfloating values, all RNG states and same-arm save/load/next-step continuation comparisons are exact. No normalization, fit to outcomes, tolerance widening, fallback, automatic retry or model simplification is present. Bitwise tensor differences and maximum absolute differences are recorded even when a fixed-tolerance comparison passes. Python, NumPy global, explicit PCG64 and Torch CPU RNG are captured through the production checkpoint utilities. The CPU-only proof refuses a CUDA context; GPU equivalence is outside scope.

Every arm constructs the actual production ReplicationModel with selected streamed execution, performs forward/loss/backward, verifies every named parameter gradient and nonzero aggregate gradient in every complete parameter group, takes an explicitly configured Adam update, durably saves through production save_checkpoint, reloads through production load_checkpoint, refuses a different effective checkpoint configuration before mutation, and compares the second update against the original model starting from the same saved RNG. Both eval and train/no_grad inference are compared. No stand-in model is used.

A graph forward-pre-hook counts initial calls and recompute entries in the correctness arm: one initial call per distinct object, and exactly one backward pre-entry per distinct object when checkpointing is enabled. The actual installed model source is pinned and invokes torch.utils.checkpoint in that selected branch. No completion post-hook is required, because non-reentrant early-stop can interrupt recomputation before it. An outer saved-tensor observer counts references and deduplicates backing storages while deliberately retaining them, bounded to20,000 records and16MiB of distinct storage. The inner checkpoint hook can conceal recompute saves. This telemetry therefore cannot establish total backward retention, process footprint or peak reduction. It has no memory-reduction acceptance threshold.

## Process and measurement separation

The coordinator starts exactly three fresh sequential child processes in one outer native unit:

1. `correctness`: five false/true comparisons, saved-storage diagnostic and durable checkpoint/continuation proof.
2. `profile_false`: uninstrumented with respect to tensor/module/storage hooks, primary fixed two-graph case and28-distinct case.
3. `profile_true`: the same finite profile with explicit checkpoint=true.

Profile modes do not retain oracle parameter/output/gradient snapshots or register tensor/module hooks. They still perform actual training, save/load and continuation. Their two cases run in order within each fresh profile process; the second inherits allocator and page-cache history. Native memory.peak may include earlier arms in the enclosing unit. It is recorded only as a cumulative high-water value, never subtracted or reported as an individual phase peak.

A separate stdlib thread samples whole-unit memory.current every10ms, with at most12,000 samples and bounded per-phase scalar maxima. It does not inspect tensors. These sampled maxima can miss short spikes, include the coordinator and charged file cache, and add small observer overhead. Exact phase timestamps allow the root guard's separate observations to be joined. No sample is labelled process-only or exact peak. Correctness-arm samples remain instrumented evidence and are never used as uninstrumented footprint. Root-owned final native/closure review remains authoritative.

There are at most256 immutable phase marker files per child. Correctness has147 planned markers; each profile has22. Metadata bodies are capped at1MiB. The proposed outer envelope is1GiB memory.high=max, swap0,2 CPUs,120s for the whole finite unit,4MiB hard per-file/log cap,64MiB sampled owned storage,3GiB host reserve,4GiB startup available RAM and10GiB disk floor. Whether the finite proof finishes inside these bounds is unknown until separately released. A bound failure remains failure, without relaunching its identity.

## Coordinator interface and ownership

The root coordinator owns native launch/admission, complete source/runtime closure, no-active-owner checks, source commit/external verification, one-use identity, storage guard,120s deadline, logs and descendant cleanup. This package only supplies a future caller:

```
.venv/bin/python -B .../coordinator01.py \
  --owned /absolute/new/owned-proof-root \
  --source-commit ACTUAL_40_HEX_COMMIT \
  --run-id NEW_ENGINEERING_ID \
  --manifest-sha256 EXACT_SOURCE_MANIFEST_SHA
```

The parent directory must already exist; owned-proof-root must not exist. Mode directories, logs, phase/intent/terminal files and checkpoints all reside beneath it. The coordinator records each actual child PID, start/end monotonic timestamps and exact return code (including negative signal returns). A failed arm stops the sequence; later modes remain explicitly unattempted. If receipt failure leaves a child active, its PID is retained where possible and outer-native-guard remains the cleanup owner. No child cleanup success is fabricated. The native launcher must include all enclosing logs/control receipts and this entire root in its owned storage allowance.

Direct worker CLI is `oracle01.py --mode correctness|profile_false|profile_true` plus the same four arguments. It is an internal child interface, not authority to bypass the coordinator. Each child verifies the manifest's selected source bytes and actual inherited memory/CPU/file controls before numerical imports. The root release must additionally pin/verify the source manifest itself and the complete runtime/source mapping. Worker/coordinator arguments do not independently authenticate a research claim.

No pytest process is involved. The inherited PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and empty PYTEST_PLUGINS/PYTEST_ADDOPTS are nevertheless required. Numerical imports occur only inside the guarded worker main; tests below do not import that main. Existing production checkpoint publication uses regular files and temporary hardlinks, then removes its own publication temp directory on normal cleanup. It is not replaced by a synthetic serializer. Its cleanup/IO behavior remains inherited source, and failed evidence must be retained by the outer collection rather than assumed complete from a successful local receipt.

## Source preparation verification and limitations

Only the checkout-local locked Python interpreter ran pure stdlib/AST checks. `red01.log` records five expected failures with no oracle implementation. `green01.log` records five passing checks before the underscore mode spelling/coordinator addition; `green02.log` records the same five after it. `io-green01.log` records three checks for exclusive regular bounded publication, first-fatal identity with one close attempt per action, and finite phase/coordinator structure. The tiny IO fixture retains its original three-byte regular file. A later final source pass is recorded separately. `cleanup-red01.log` additionally captures an ordinary primary exception incorrectly hiding a later actual MemoryError during descriptor cleanup; `cleanup-green01.log` verifies that the actual fatal object now survives with the original error retained as its cause. Earlier first-fatal objects retain precedence.

These checks do not establish any numerical assertion, actual tensor dtype/shape, recomputation count, runtime, fitting result, resource sufficiency or genuine native launch. No Torch/NumPy module, numerical fixture, model output, resource job or empirical data was imported/created by this preparation. All five numerical cases are new prescribed work, not repeated closed jobs. No existing model/runtime source, previous candidate, STATE, registration or Git HEAD was edited.

Independent review is required before release, particularly for native caller integration, complete phase expectations, true false/true numerical comparison, production checkpoint lifetime/error paths, bounded result size and failure retention. The first numerical result—pass or failure—must be preserved under its single new identity.
