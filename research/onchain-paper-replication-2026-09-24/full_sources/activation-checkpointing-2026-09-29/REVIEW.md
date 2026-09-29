# Independent activation-checkpointing review

Status: **changes required for device RNG preservation** on the initial reviewed
snapshot above base `19ffd7fa`. CPU synthetic evidence supports joint-gradient
equivalence, but does not resolve the device-specific issue below. No empirical
or GPU execution is admitted by this review.

Scope: `model.py`, `model_registry.py` and
`tests/research/onchain_replication/test_activation_checkpointing.py`, with
relevant encoder, training, checkpoint and pinned Torch implementation inspected
as supporting contracts. No tests, real arrays, raw data, external calls or
historical jobs were executed by the reviewer. Only this report was written.

## Actionable finding

**P1 — keyword-only tensors bypass device RNG discovery.** At
`tradingagents/research/onchain_replication/model.py:65`, every graph tensor is
passed through `**graph`; the checkpoint call has no positional tensor inputs.
The pinned Torch non-reentrant implementation at
`.venv/lib/python3.13/site-packages/torch/utils/checkpoint.py:1545` infers the device
from `*args`, and at line1570 calls `get_device_states(*args)`. It does not inspect
the keyword dictionary for this operation. With the present call, the captured
device list is empty. CPU RNG is still saved and restored independently, which
explains why the CPU dropout/RNG tests pass.

For a CUDA graph with dropout enabled, the original forward consumes CUDA RNG;
backward recomputation then uses its advanced CUDA state instead of the original
mask. Different masks can change parameter gradients and optimizer updates even
though `preserve_rng_state=True` was requested. This is established from the
pinned source contract, not a performed GPU experiment. Pass the MCM/features
tensor and edge tensor positionally to checkpoint, forwarding optional graph
fields separately, so device-state discovery sees the actual graph device. Add
a CPU-only device-discovery regression through the installed checkpoint helper;
actual CUDA gradient/RNG equivalence remains a separate bounded verification
requirement before GPU release.

## Other implementation conclusions

- Explicit `use_reentrant=False` is correct for fixed MCM inputs without
  `requires_grad`. The pinned implementation records the autograd graph and does
  not require a differentiable input. The tests check every named parameter's
  gradient and update, plus nonzero aggregate gradients in MLP, GAT, LSTM and
  each temporal-attention/head block.
- The encoded-graph dictionary is local to each forward. Repeated references to
  the same graph share its differentiable embedding within that forward; the
  cache is neither detached nor retained across optimizer steps. This preserves
  the existing repeated-graph semantics.
- `_configure` validates a strict boolean and defaults to false. Calling it from
  `AlternativeGraphTemporal` covers GIN and both graph diagnostic comparators.
  The proposed and label-permutation arms both instantiate `ReplicationModel`.
  Price/vector arms do not use this graph checkpoint option. No frozen model
  configuration was changed in the reviewed delta, and the existing evaluator's
  configuration digest includes the entire model configuration.
- Evaluation mode or disabled gradients bypass checkpointing. The current
  encoders do not update running-statistic buffers, and the training loop
  performs backward before changing model mode or parameters. No CPU
  recomputation/state-mutation defect was found in these paths.

## Saved evidence and its limits

All three source hashes match `source-bindings.json`:

| File | SHA256 |
|---|---|
| model.py | `52d4cd71d0ecc07764396717e42e28127d516bf2d67a42a3afbd8541884a2a5d` |
| model_registry.py | `c0e2202578ae708e2fc0406ece5726541952bf40f29df9dc81812c177c334543` |
| test_activation_checkpointing.py | `e74ae997c8965e1a60c41f022f722fdee3578c8cb6c6d7233b03f6e3d7093f35` |

The retained logs distinguish all attempts: red01 rejected the unadmitted test
path; red02 had four intended feature failures plus two invalid-mask fixture
failures; red03 retained four intended failures and three passes; red04 retained
three inherited-comparator failures. None is represented as a successful run.

`green01/child.log` records fifteen passing activation/model checks in10.75s.
The guard terminal records child zero, verified cleanup,12.7585s elapsed,
416,722,944 peak sampled cgroup bytes and no memory events. The saved tensor
reference-byte diagnostic is1,444,104 ordinary versus206,458 checkpointed.
The reference counts may count shared storage more than once; they are not a
measurement of unique allocation, peak RAM, GPU memory or large-graph capacity.

The synthetic CPU checks compare predictions, loss, all gradients, Adam-updated
state and CPU Torch RNG across ordinary/checkpointed execution. Exact checkpoint
replay checks the next CPU update and RNG after restoring saved model/optimizer
state. Inference checks use valid prefix padding. The inherited comparators
receive separate gradient/update/RNG comparisons.

Untested claims include actual CUDA/device RNG equivalence, mixed precision,
compiled/distributed execution, multi-device models, regression-task checkpoint
equivalence, full-sized peak allocation and runtime, large-neighborhood MCM
feasibility, empirical prediction quality and profitability. Broader neural-suite
work by the implementation owner was not operated or judged here. Checkpointing
still requires the largest individual graph operation and fixed feature tensors
to fit; this increment alone does not release an empirical resource pilot.
