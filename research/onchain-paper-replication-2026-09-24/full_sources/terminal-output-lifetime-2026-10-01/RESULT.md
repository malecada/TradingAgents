# Terminal output lifetime and native executor verification result

integration-check01 CLOSED: one full registered synthetic test passed in258.536s,
exec session84650exit0; exact PythonPID1682009 is absent. All573 frozen files were
verified unchanged at closure. Freeze SHA256:
fc793b783861f68b54b3cbd7cbee47bd479c83d70455d775d80ae3507e1236a3.
The six focused output-tracker methods previously passed in3.343s; independent
source review found no blocker. Failed predecessor executor check01/check02,
original source snapshots and diagnostic records remain preserved unchanged.

The actual temporary registered executor completed two full proposed-model cells:
direction and regression. Each produced two expected test predictions with exact
order, labels, clocks and cell metadata. Actual fit completion references matched
checkpoint manifest hashes and verified artifact members/provenance; saved state
contained optimizer data and epoch1/batch0. Strict model restoration reproduced
the saved probabilities/prices exactly, using the native feature loader after
batch ledger/control publication. Independent arithmetic matched metrics using
the expected example labels. No producer or generic NumPy loader was reentered.
Original returned feature wrappers released, pair reservation count was unchanged,
and a duplicate batch refused without changing its output ledger. The terminal
receipt lease still passed after the registered outputs were appended.

Direction checkpoint SHA256:
21e0301d56f0850e8ebf1be3e3ddadb951fb94fcb9ea5f03f0e5b6a406bc3848.
Regression checkpoint SHA256:
8345c223f5239ebad0a9ffaed11765990700e87340158cfd2b3eaea90639c8f1.
These are observations from temporary synthetic fixtures, not retained financial
model artifacts. The fixture cleans temporary run directories on exit. Logs,
source snapshots and tests are retained; no external recovery of those temporary
checkpoint blobs is claimed.

The narrow float64 classification-metric correction is included. Its three new
regressions and49 maintained metric/verifier checks passed before this integration;
formulas, threshold, clipping convention and independent tolerance were unchanged.
Source-review acceptance of that correction and the prior source-supplement
qualification are recorded in native-batch-executor/FAILURE_CHECK01.md and STATE.

Scope remains tiny synthetic data, reduced fixture motif width/two-day lookback,
one epoch/batch size one and mocked kernel guard. The full trainable architecture
is exercised, but this is not paper-scale training, measured resource admission,
cold/historical feature admission or a claim of numerical agreement. Restoring
model predictions does not prove optimizer/RNG continuation parity; those use
separate continuation checks. Output observation verifies identity, not ledger
semantics or changes restored between observations. The per-output metadata cap
is not total RAM/disk accounting. All1420 financial-data fits remain pending.

Next: close independent final review and preserve reviewed changes remotely, then
implement the actual guarded job producer selection and first-owner orchestration
specified in native-batch-executor/DISPATCH_GAP.md. It is still absent from the
normal job_payload execution route. Mapped parents, cold/history reuse and full
resource coverage remain mandatory separately; no scope is silently dropped.
