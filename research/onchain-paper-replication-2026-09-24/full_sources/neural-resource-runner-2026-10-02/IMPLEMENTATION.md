# Maintained neural resource runner — synthetic engineering only

No retained empirical array was read, no identity was reserved, and no financial
fit or resource execution is admitted. The distinct budget62 draft remains
unadopted. Original resource outcomes, heuristic, model/GAT files and configuration
remain unchanged. This candidate requires independent review.

## API and exact plan

`produce_registered_neural_resource(run, plan_input)` returns the full cells,
resource summary and exclusive source directory. `job.py` now explicitly accepts
`kind=neural_resource` with payload exactly `{"plan_input":"registered-name"}`,
requires the Torch environment inventory, and publishes `cell-ledger.json`,
`resource-summary.json`, `artifact-index.json`. Existing outer ownership/source,
6 GiB memory maximum, 3 GiB host reserve, 10 GiB disk floor and whole-job guard
checks remain unchanged. Unknown job kinds still fail schema validation.

Plan v1 has exactly schema_version, model_input, graph_activation_checkpointing,
cells and limits. The nine ordered original ETH weeks/requirement identifiers are
fixed. Each cell binds graph_input, graph_hash, graph_config_hash,
node_order_sha256, expected_nodes, expected_edges, week and cell_id. Exact seven-day
UTC graph intervals must lie in the registered input dataset windows. Independent
mapped validation admits member extents/hashes and exact graph counts before the
existing graph loader runs. No graph rebuild or numerical MCM/dictionary input
exists in this route.

The original model's canonical JSON digest is fixed; scientific architecture and
hyperparameter shrinking are refused. The explicitly registered boolean checkpoint
policy is included in effective model/plan identity; false is the original default.
Source-admitted prospective true selection needs separate comparability review.

Limits contain positive integer max_graph_bytes, max_checkpoint_bytes,
max_output_bytes, cooperative_cell_seconds. Additional finite envelopes cap graph
bytes at 6 GiB, checkpoint file at 1 GiB and cooperative elapsed at 28,800 seconds.
These ceilings are refusal boundaries, not physical sufficiency claims. Output
allowance must reserve nine maximum checkpoint files plus 1 MiB metadata overhead.
Allocated output is measured between cells and after lifecycle publication; final
quota failure retains published evidence and prevents successful completion.
Guard/claim/terminal logs are separately registered obligations outside this count.

## Scientific behavior and failure preservation

The in-process route retains one graph/model/optimizer cell at a time. Every cell
resets seed11, constructs the original classification model, generates PCG64
float32(N,32) MCM, repeats the same graph item object over 16×28 positions, uses
linspace prices, alternating labels and one Adam(lr=.001) cross-entropy update.
No second optimizer update is performed by checkpoint verification.

The checkpoint contains complete model, optimizer, RNG, original epoch1/batch0
cursor, loss and immutable plan/claim/source/graph identity. A finite writer stops
before exceeding its checkpoint byte allowance; a failed write leaves its partial
file. The restored nested tensors/scalars/RNG are independently hashed against
pre-serialization state and model/optimizer/RNG readback after load. The existing
model/optimizer are reused for load; checkpoint deserialization still requires
additional memory and is not advertised as zero-copy.

Each completed/failed/unavailable cell is immutable at the existing source path
recognized by the outer observer. Any caught error or termination stops all later
cells and records them unavailable; failed identities are never resumed/refunded.
Uncatchable process death remains the existing observer's responsibility. Existing
claim/terminal machinery prevents relaunch; a producer-directory duplicate is
also refused. No deletion or checkpoint rotation occurs.

## Validation and retained failures

All commands use `PYTHONPATH=. .venv/bin/python -B -m pytest -q` with the normal
reviewed conftest. No broad suite or shared actual-owner source scan was run.
Tiny invented graphs use the same model and full 16×28 shape. The worker unit test
mocks only outer guard/admission/environment and runner return to isolate dispatch;
separate producer tests exercise actual graph save/load, model update and files.

| Log | Focus | Result |
|---|---|---|
| red01 | first four runner/schema tests, before implementation | 4 expected failures |
| red02 | six tests, before implementation | 6 expected failures |
| check01 | six tests | 1 failed, 5 passed: Torch replaced writer exception text |
| red03 | nine tests | same serialization-message failure, 8 passed |
| check02 | nine tests | 9 passed |
| red04 | eleven tests | 1 failed, 10 passed: exact graph end-date admission missing |
| check03 | eleven runner tests + activation-checkpointing tests | 22 passed, 1 skipped, 9.01 seconds |

The GPU checkpoint test was skipped because CUDA hardware was unavailable; no GPU
claim is made. The serialization exception is now explicitly framed as a failed
checkpoint with partial evidence retained. The exact graph interval gap is fixed.
An early preallocation test assertion could accept its own injected pytest failure
because the runner catches BaseException and the message contained “count”; it was
corrected to require the allocation observation remain empty. This weakness is
explicitly preserved in earlier reconstructed test snapshots.

Final check03 source/test snapshots are direct copies. Earlier snapshots are
reconstructed by reversing the exact retained tool edits, explicitly labelled as
reconstructed rather than contemporaneous captures. All original full attempt
logs remain unchanged. No failure or test omission is treated as a successful
empirical cell.

The independent numerical oracle separately reconstructs the original update and
compares every model tensor, optimizer tensor and PCG64/Torch RNG state. Additional
tests cover the entire nine-cell ledger, failure short-circuit, duplicate directory,
checkpoint partial-byte bound, model shrink refusal, exact denominator, pre-load
count refusal, explicit job payload and Torch/resource-output dispatch.

## Remaining limits

The existing graph loader still copies arrays into GraphSnapshot and materializes
node IDs; no loader optimization is claimed. GAT creates full edge/head tensors.
Whole-encoder checkpointing does not bound single-graph peak. Python garbage
collection does not prove native allocator release between cells. Reported RSS is
process-lifetime peak, not isolated per-cell peak; cgroup peak/events remain in
outer guard telemetry. Cooperative elapsed checks cannot interrupt a long PyTorch
call; only the existing outer guard gives hard whole-job containment.

Full-size physical feasibility, source-admitted real inputs, independent
comparability, exact registration/environment/source closure and cumulative budget
adoption remain prerequisites. The readiness report's torch.unique wording is
qualified: duplicate non-self edges are checked and rejected, not silently
normalized into accepted graphs. This implementation does not change that rule.
