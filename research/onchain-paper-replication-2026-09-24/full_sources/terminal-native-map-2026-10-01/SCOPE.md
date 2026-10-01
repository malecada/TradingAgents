# Current terminal native-feature batch adapter

prepare admits a selected native_feature_batch_input through both registered
routes, verifies its execution/source closure and calls the actual reviewed seal
transition exactly once. The returned receipt is from that call; the public
Receipt constructor or an arbitrary caller callback cannot authorize admission.
Proof/event/component references come from its actual source-validated graph
closure and exact published schema3 binding. The initial seal closure retains
the original MCM/source-value joins. The map does not redo those numerical stages.
Cold/historical saved admission and mapped parent populations remain separate.

The private numeric helper subclasses maintained FixedFeatureMap and overrides
all metadata iteration, item access, load_batch and verified_hashes paths. This
preserves both existing evaluation dispatches without using generic ArrayReference
or np.load/mmap. An arbitrary helper construction is not registered admission.
The strict reader checks exact native tree, shape, type, C order, file hashes and
extents before numeric allocation. The reviewed boundary constructs independent
CPU float32 MCM/int64 edge tensors and checks feature wire identity, including
empty edges. Only unique requested graph keys are loaded. No learned graph
embedding is cached across model updates; the full trainable architecture remains.

A nonblocking lock serializes load_batch, verified_hashes and the public live-byte
query; its internal pruning routine runs only while the lock is held. Before allocations,
load_batch checks L+sum(N)+max(N)+9C against max_numeric_bytes and L+sum(N)
against max_live_tensor_bytes, where L counts still-live original returned tensor
wrappers, N is each unique native graph payload, and C is bounded chunk entries.
The conversion receives the remaining allowance after prior live and new retained
outputs. verified_hashes checks L+max(N)+9C, reads one native component at a time
and computes actual feature wire hashes without returning tensors. Every live
wrapper retains its original storage identity, pointer/extent, shape, stride,
dtype, CPU device and no-grad flags; mutation refuses subsequent accounting.
Weakrefs avoid retaining completed batches. Late failure clears newly allocated
results; reentrant allocation calls refuse.

These are numeric allowance checks for this adapter's allocations and original
returned tensor wrappers, NOT a bound on all resident feature storage. Detached
aliases, autograd-held storage after wrapper death, model state/activations,
parent graph population, dictionary/sample prerequisites, metadata, stream
buffers and page cache are excluded. The outer process guard and still-open
whole-workflow resource admission remain mandatory. Explicit generalized batch
release would require a separate consumer lifecycle change. The maintained
training/prediction loops delete per-batch inputs/output; that ordinary usage is
compatible with this limited wrapper accounting.

The actual terminal receipt/content lease brackets each operation. During strict
reads and tensor conversion, the callback checks the active run and actual bound
guard; the full lease checks all prerequisites before exposing results. Repeated
full-fold hashing, resident parent graphs and source/runtime validation costs are
not a scalability or full-fold performance claim. No empirical release is implied.

red01 CLOSED6missing-component failures0.002s, session58112 exit1.
Focused check01 CLOSED6passes1.094s, session38533 exit0. These use synthetic native
components: byte parity/deduplication/empty edges/release, pre-allocation aggregate
and unknown-key refusal, layout and file corruption, shape mismatch, reentrant
calls and late-lease cleanup. Maintained batch_factory sends those synthetic
features through the full ReplicationModel with nonzero finite gradient evidence
in its parameter groups. No financial fit or optimizer update is used.
The actual registered prepare/seal/reuse integration has a separate test identity
and remains pending; focused helper checks alone do not prove admission.

Independent initial review withheld acceptance for NM1 (single-graph capacity
not admitted before irreversible sealing) and NM2 (an unlocked public accounting
query could overwrite newly added live registrations). Original source and both
tests are preserved as .check01; INITIAL_REVIEW.md retains those findings.
prepare now checks the largest required native graph against the live-wrapper
cap and twice its payload plus chunk scratch against the numeric cap BEFORE
calling seal.finish. This guarantees individual graph feasibility at zero prior
live returns; it does not prove every multi-graph chronological batch fits. The
latter is still checked before allocation and requires empirical resource admission.
The public accounting query takes the same nonblocking lock as allocating paths;
the internal helper is called only with that lock. A prior wrapper may legitimately
die during an operation, so final accounting may decrease from the conservative
preflight amount; every still-live wrapper retains its exact storage/layout check.

red02 CLOSED2methods0.215s: one missing minimum-capacity helper error and one
missing accounting-query lock failure, session86815 exit1. Corrected check02
CLOSED8passes1.232s, session22209 exit0. A controlled thread/barrier case pauses an
active batch and requires the accounting query to refuse, then checks its new
registrations remain counted and further excess load refuses. This is the new
query-lock contract, not a claim that the old lost-registration schedule itself
was reproduced. The minimum-capacity numeric boundary is also tested. All earlier
pure focused tests pass against the corrected source, including full neural
forward/backward parameter-group gradients. No optimizer or financial fit runs.
The new actual registered integration includes low-cap refusal with seal.finish
forbidden, and the actual seal→map→maintained batch_factory path. It is not yet
closed; final independent acceptance remains pending.
