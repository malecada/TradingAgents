# Streamed-GAT candidate02: original multiply/sum node attention

Status: frozen unexecuted engineering candidate. This new source copies candidate01 byte-for-byte except exactly two statements: source and target node scores now use `(h*self.a_source).sum(-1)` and `(h*self.a_target).sum(-1)` in place of node-score einsum. Constructor/initialization/RNG, projections, heads, widths, masks, duplicate refusal, incoming neighbors/self-loops, softmax/dropout, current custom streamed message aggregation, dtype and checkpoint=false are unchanged. No production integration or numerical execution occurred.

## Evidence and limited inference

The closed one-use four-arm diagnostic's overall parent status is FAILED (cleanup_stop_returncode5), despite actual child0/guard completion and all four recorded arms reaching observed status. That historical failure and its raw evidence remain immutable. Numerical observations show eager attention with streamed aggregation has no tensor mismatches at the frozen tolerances, while both einsum-attention arms have the same three updated-parameter mismatches. The eager/eager entry is baseline self-comparison, not an independent repeated baseline experiment.

The fixed LSTM coordinate gradient differs from2.750311978161335e-9 to2.368324203416705e-9 between original and einsum attention. Adam epsilon1e-8 amplifies this to the observed2.4221837520599365e-5 update difference. First-step m/v/update reconstruction matches recorded values exactly. This isolates the observed tiny-fixture issue to the attention choice; it does not prove every graph or the new multiply/sum candidate will agree.

## Remaining numerical and resource limits

The proposed expressions retain the original D-axis multiply-then-sum operation, performed per node before scalar edge gathers. Original eager attention performs it after edge gathering. Changed layout/reduction implementation and backward grouping remain possible: the node path accumulates scalar edge gradients before multiplication, while the eager path multiplies edge contributions then scatters; attention-vector gradient sums similarly regroup from edge to node contributions. Exact constructor equality is insufficient. The original full output/loss/input/parameter-gradient/Adam/RNG/reload checks must pass unchanged.

The first full graph's N2,049,095/H4/D16 node-product transient is524,568,320 bytes (~500.27MiB), plus scalar node-score output. Sequential source/target expressions avoid intentionally retaining both products concurrently, but runtime allocator/gradient lifetimes must be measured. A node product is smaller than a full edge-wide product and is not a promise that total forward/backward fits3.75GiB. Saved-tensor backing checks must still pass; they do not measure all transient/process memory.

CPUfloat32/float64 and first-order-only semantics remain. The existing custom message aggregate retains once_differentiable and contiguous block bound<=65,536; no additional autograd rule is introduced. Higher derivatives/GPU, full-size capacity and scientific accuracy remain unproved. No checkpointing, changed dtype, smaller neighborhood/head/model, altered Adam or relaxed tolerance is introduced.

## Required next proof

Root owns a distinct unused GREEN02 release after independent candidate/source and corrected cleanup-guard review. The prospective copied oracle03 must change only candidate01 import to candidate02; original oracle02 bytes, all fixtures, thresholds and criteria remain frozen. Full numerical and saved-storage checks must run before any source integration or empirical resource release. Passing a tiny oracle alone would not establish full-size capacity. The former empirical neural identities remain closed/spent; no empirical allowance is created here.

Preparation checks: stdlib AST parse; exact two-line reversible source diff; all remaining AST nodes identical after removing only source_score/target_score assignments. No NumPy/Torch import, test/guard/claim/job, raw mutation or old-source edit. Source and evidence pins are recorded in candidate-manifest02.json; prior manifests/reports remain preserved.
