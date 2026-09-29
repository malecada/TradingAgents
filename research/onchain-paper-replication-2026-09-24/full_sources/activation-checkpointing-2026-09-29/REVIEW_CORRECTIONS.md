# Independent activation-checkpointing correction review

Status: **initial P1 resolved by the inspected correction; no further defect
identified in this delta.** The original `REVIEW.md` remains unchanged. This
conclusion closes the call-contract defect, not the separate question of actual
GPU equivalence or resource admission.

`model.py` now routes graph dictionaries through `_encode_graph(mcm, edge_index,
node_mask=None, batch=None)`. All four arguments are passed positionally to the
non-reentrant checkpoint function. The pinned Torch implementation inspected in
the initial review therefore discovers the actual tensor device and its RNG
state through `*args`. The original keyword-only omission is removed. All current
graph encoders share this positional signature, including GIN and both inherited
diagnostic arms. Strict boolean configuration, training/gradient gating,
within-forward embedding reuse and fixed-input joint gradients are preserved.

The new CPU call-boundary regression wraps the real checkpoint helper, rejects
missing positional graph tensors, executes the real forward/backward and checks
that each unique graph is checkpointed once. Its retained red receipt fails on
the original empty positional-argument tuple. This verifies the relevant calling
contract; it does not simulate CUDA RNG behavior. The conditional CUDA test
compares predictions, gradients, updated state and RNG, but is skipped because
CUDA is unavailable. No successful GPU result is claimed.

The saved `review-green01` log records30 passed/1 skipped in5.29s for activation,
model and bounded-hash checks. Its guard records child0, verified cleanup,
7.2144s elapsed,408,567,808 peak sampled cgroup bytes and no memory events. The
corrected saved tensor reference-byte diagnostic is1,444,104 ordinary versus
220,890 checkpointed. The earlier206,458 count belongs to the keyword-only
snapshot and is not attributed to this correction; positional inputs now also
participate in saved-input accounting. Neither diagnostic is a unique-storage or
full-size peak-memory measurement.

Independently recomputed identities:

| File | SHA256 |
|---|---|
| model.py | `ed4d5417202bb13ebc682d88d56942db74201feddc1b4d20511e54684fc252a0` |
| model_registry.py | `c0e2202578ae708e2fc0406ece5726541952bf40f29df9dc81812c177c334543` |
| test_activation_checkpointing.py | `0976c5dd8a464a766feec27c908886e08254b30a0e3bbd75b59386172222ed60` |

The reviewer read source and compact saved receipts only. No tests, actual array
loads, empirical execution, network calls, source edits or registration/ledger
writes occurred. `neural02` is outside this review's observed evidence. The
initial review's untested hardware, full-size capacity, mixed-precision,
distributed/compiled execution and empirical claims remain untested.
