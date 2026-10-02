# Score-tail offload: exact remaining requirements

Read-only investigation, October2,2026. **A new score-tail archive adapter and verification contract are required; pair-event archival is not that adapter. The coordinator's current server report shows approximately5.36TB available remotely, but tail-only offload does not establish sufficient local headroom for all nine MCM outputs.** No storage purchase, upload, SSH, credential access, numerical import, test, claim, job, raw removal or production mutation was performed. Only this new requirements document was written.

## Current source boundary

`score_tail.py:ScoreTail` stores80-byte records (`<Qd32s32s`): global ordinal, exact float64 score, purpose hash and predecessor-dependent checksum. Start metadata binds current owner, scientific scope, starting ordinal/cell count and exact batch destination. Complete and failed terminals bind acknowledged prefix, record-body extent/hash and chain head. Failed pending bytes remain uninterpreted. `seal` verifies a complete tail, copies exact float64 values into its next ScoreBatches destination, then rechecks both original stores; it deliberately retains the tail.

`mcm_score_stream.py:_seal_check`, `_history_check` and `finish` reopen every original local tail, enforce exact chunk ranges/predecessor chain and compare tail values to retained float64 batches. `compact_stage.py:126–177` repeats full tail decoding and computes the ordered ordinal/value/purpose score digest used to join matching events. `archived_stage.py` still invokes that local stream verifier even when pair events are remote. Removing records.bin or replacing a tail directory with an arbitrary remote receipt breaks the current contract.

`compact_mcm_output` reads verified float64 chunks to write the float32 artifact, and `compact_mcm_publication:_prepare` calls the owner stage-content verifier again. Publication, graph-artifact and terminal readers therefore transitively depend on the current local tail format. A path remap, fabricated completed stage or self-hashed remote manifest cannot replace this chain. The ordered32 original January motifs, all graph nodes, original dictionary/scientific matching identity and new execution workload identity must remain distinct and joined.

The earlier archive-readiness report is partly superseded: current `job_payload.py:46–50,177` already preflights an archive Context and injects its per-representation View. That work must be reused. However `archive_dispatch.preflight:74–78` still requires kind fit and budgets event populations; `archive_owner_policy._inputs:38` and `compact_mcm_publication._output_policy:34` still read literal execution_job. Resource import needs an explicit actual-job-input/resource-mode join and a new tail population. The unintegrated dictionary/MCM candidates do not supply this merely by existing on disk.

## Arithmetic and present local constraint

Independent stdlib reconstruction of `score-tail-2026-10-01/accounting01.json` gives577,498,112 cells and8,816 chunks at the prospective65,536-cell chunk size. This is an existing conditional nine-graph inventory, not an empirical result or a fresh graph-body measurement.

| Retained selected payload | Bytes |
|---|---:|
|80-byte score-tail records|46,199,848,960|
|8-byte float64 batches|4,619,984,896|
|Two4-byte float32 copies|4,619,984,896|
|Total after pair-event offload|55,439,818,752|
|Remaining after successful tail offload|9,239,969,792|

At20:06:48UTC, read-only disk usage on this checkout filesystem showed20,166,332,416 free bytes. Subtracting the10GiB floor (10,737,418,240B) and the remaining selected9,239,969,792B leaves188,944,384B, about180MiB. This is a timestamped observation, not a reservation. Existing local score metadata allowance is289,177,600B; a changed archive format requires a newly derived allowance, not an assumption that all old metadata vanishes. Graph edges/output headers, dictionaries, checkpoints, matching scratch, logs, remote-copy controls, failed work and physical allocation overhead are additional. Existing graph inputs already occupy disk and must not be subtracted twice from measured free space.

Thus no current whole-nine-cell physical upper bound fits merely because the large tails become remote. Options are a separately verified additional local free-space allocation or a second reviewed reader/streaming contract that offloads completed float64 batches and/or one or both float32 copies while preserving exact recoverable bodies and truthful lifetime accounting. Sequential execution alone does not remove completed artifacts required through owner closure. Lowering the10GiB floor, dropping float64 or float32 evidence, shrinking32 motifs/nodes or omitting cells is not an implicit solution.

A full tail at65,536 cells is5,242,880B (5MiB), below archive_chunks'8MiB per-member limit. The existing preserve primitive temporarily keeps original+snapshot+readback, giving15,728,640B of these payloads alone, plus local metadata/batch bytes and upload sealed-memfd/RAM copies. One-at-a-time chunk staging is practical in principle; never stage the full46.2GB archive locally. The common tiny fixture4MiB per-file limit cannot admit this full tail size: a prospective full-size release must explicitly allow the measured file extent or register a smaller operational chunk size with recalculated counts. Numerical cell/order semantics remain unchanged.

Remote payload reservation must cover at least46,199,848,960B for these tail bodies, plus remote metadata, pair events and retained partial/failed namespaces. Transport.get reserves `(bytes//32768+1)*32768` per retrieval, including an extra block on exact multiples. For these8,816 chunks, one full download sweep reserves46,488,551,424B. Upload plus immediate readback plus one additional complete recovery sweep would therefore reserve139,176,951,808 payload bytes under the present rounding rule, before other stage reads, failures, pair events or diagnostics. This is arithmetic for that explicitly named three-transfer pattern, not a proposed final budget or throughput estimate.

## Smallest coherent new source slice

Reuse the existing low-level Transport, durable Context/View accounting, actual Owner held-operation authority, archive preserve/consume primitives and owned disposition pattern. Do not call an unheld public transport callback or create per-stage budgets. Add a separately named/versioned completed-score-tail archive writer and reader, with coordinated changes to MCMScoreStream, compact_stage.stream and archived-stage/owner-seal consumers. Keep the old local route unchanged.

The registered tail policy and original claim must bind actual job_input/hash, current ResearchRun/Binding/Owner/stage, complete source/runtime, graph/node order, original dictionary and ordered32 motifs, original matching and execution/workload identity, dtype/endianness, rows×32 total, chunk index/range, tail start/terminal/body hash and acknowledged head, exact batch destination/header/payload hash, predecessor manifest hash and endpoint/remote namespace. Separate tail allowances from168-byte pair-event allowances; do not inflate max_events and pretend that authenticates tails. Preflight aggregate all-nine populations and all representations before creating the first output.

The required one-way per-chunk sequence is:

1. Keep the active tail local; complete it and its exact next float64 batch under the actual live stage. Verify the full purpose chain, ordinal denominator, score range and exact values against the batch. Retain original inode/signatures and immutable terminal bytes.
2. Durably reserve the attempted upload/readback/metadata/command allowance in the original shared ledger before transfer. Upload an immutable snapshot to an exclusive new namespace; retrieve the complete body into a bounded fresh cache and verify every byte/hash and the semantic chain against the original tail/batch. Bind the returned receipt to the original stage, held token, configuration and source objects after every external callback.
3. Publish and fsync an immutable owner-anchored mapping/verification receipt before disposing any explicitly designated newly produced successful payload. Rejoin original source path/inode/signatures, original readback bodies and batch bytes after the final callback. Dispose only those owned success bytes allowed by the new prospective contract; fsync and publish the exact disposition. No unverified original/historical raw, active tail, failed partial or unknown inode may be removed.
4. Preserve exact local start/terminal/range/hash/control evidence and the chained tail-to-batch-to-matching proof. Stage/owner completion must account for every chunk and current pair, including partial/unavailable cells. Complete all required remote-content verification under a live reserved operation before terminal closure. Post-close checks use original anchored local receipts without hidden network callbacks; they prove an earlier verification, not current remote availability.

`archive_chunks.preserve` deliberately retains source+snapshot+readback and frees no disk. `archive_consume` disposes only its own newly recovered successful cache. The existing pair writer's source-disposition logic shows the required pinned ownership/order but cannot be reused as a score-tail reader by changing an event count. New source must preserve first-fatal identity, attempt independent cleanup once and withhold success after uncertain cleanup; old helper acceptance is not proof of all newly composed failure paths.

## Resume, external evidence and capacity

Transport explicitly has no retry, overwrite recovery, remote deletion or remote capacity admission. A failed namespace remains consumed. A future resume protocol must use a new registered successor identity and reconcile predecessor terminal/death, retained complete mappings, partial remote/local attempts and all spent reservations. It may adopt verified completed object references only through that explicit authority; it must not relaunch a closed claim, overwrite a partial remote object or recompute already completed historical work. Merely restarting rsync or resetting a Budget is not admitted recovery.

Historical `storage/RECOVERY.md` requires complete archive download and member verification; upload exit status, listing or remotely computed hash alone is insufficient. The independently reviewed cold-offload03 closure retained verified recovery/disposition for nine inactive failed artifacts totaling3,584,497,664B under its own10GiB floor and finite bounds. That establishes a historical mechanism and those exact objects, not current account quota/free space or permission to reinterpret them as tail fixtures. Existing archive-transport tests use local child processes; the three-case genuine owner fixture proves its finite one-view route. The two-view fixture is closed failed and cannot be cited as a completed multi-view proof.

The coordinator subsequently supplied `REMOTE_CAPACITY01.json` SHA256 `95add741b29b523e7313b172453cef907377317bb77a7b9b85cd8d0ef7fce7c2`, a read-only existing-key/strict-known-host `df -k` result at20:08:03UTC, exit0. Its original output reports5,368,709,120 total,137,939,328 used and5,230,769,792 available1024-byte blocks. Independent multiplication confirms5,356,308,267,008B available (approximately5.36TB), comfortably above the46.2GB selected tail-body arithmetic at that observation. Thus lack of a current reported remote-capacity observation is no longer the blocker. This review did not issue SSH or inspect credentials. The server report is neither a reservation nor complete remote inventory reconciliation, sustained throughput, object immutability or full upload/recovery proof. A real release still needs freshness, a finite margin joining all retained/partial namespaces and exact new namespace/traffic policy. The immediate capacity concern is local staging and accumulated batches/float32 outputs. No new purchase or provider contact is indicated solely by this report; any such expenditure/contact remains separately authorized.

## Decisive fixtures and release boundary

A small local fake-transport fixture can prove completed tail→batch→archive mapping, full-byte recovery and source-disposition rules without real graph history. It must include full and partial final chunks, two graph targets sharing the same original dictionary, exact32-column ordering, duplicate/missing/reordered purpose and chunk refusal, wrong source/inode/receipt/endpoint/hash, terminal owner/expired or cross-thread token, callbacks mutating original authority, interrupted upload/readback/seal/unlink, low-floor admission, cumulative rounded command/byte budgets across the second target and failed operations, and first-fatal cleanup. Failure after first output must preserve the first output and all charged/evidentiary history. A verified-local receipt alone must not impersonate fresh remote verification.

Then one separately released finite native fixture must exercise real ResearchRun/Binding/Owner/import stage, typed imported MCM kernel/stream/publication, whole-stage/owner terminal and full retained-tree recovery under actual bounds. Tiny imported numerical authority work can proceed with all tails local; it does not require46.2GB remote capacity. Add the archive variant only when its exact source/controls are accepted. Existing closed one-view/two-view identities stay closed.

Finally, real external interoperability and body recovery need a new bounded tiny transport release with exact endpoint/namespace, source/runtime, guard/disk/staging/file/RAM/time/command/traffic budgets and independent complete receipt/member review. Passing that mechanism probe still leaves the full nine-cell physical/storage and cumulative empirical amendment to admit. Register the exact all23 resource-cell map (7 neighborhood,7 matching,9 MCM), failures/unavailable states and selected tail/output policy before full data execution; do not conflate this with the1,420 financial fits or paper numerical agreement.

## Point-in-time source pins

The following source hashes anchor this investigation, not a launch closure:

- score_tail: b5e807e022349ca7e0d18c02512812932103865ba0779d641be6877995694870
- score_batches:715125e543edd383c4bdeab59d10f7a269faec18f3b5fd16af79013e1bb37555
- mcm_score_stream:c70b23d4f8d16aa418109647bdba7ccd2139a2c1ef910b5acad8535aeebde1d7
- compact_stage:78a5164a711ee69b3a0406ca63a620e781776798864075c9dd820229ccd4ccc4
- archived_stage:1e4b09210a0a9384b778a71e1573298cb923711bcf7c7dcd3b464460001dc407
- compact_mcm_publication:d80315a270fab3c4a349e22cd114fa46041c121cdbfccbdc47ae7ce4b04edd25
- archive_dispatch:05eafe349dfafefe0b17ed8b8efaa3a480eff0f943988212846cabcec414f953
- archive_owner_policy:81b0e2fa4220c45461ffad850209e92819b65a56a7037887d1d7ba92c97956c9
- archive_transport:ef0fdc052a354af5b83e487cbc2d2cf92170149d64f90117adcb5ee37e3b572d
- archive_chunks:f26f1cb62334497494f9b02579f53be9e2238889a81f56c04fd4e781542b38fe
- archive_pair_writer:c714c350f372be1b4e3c7840b5187deb7f72ee80549edfed4e48450e2d0ca052
- archive_consume:9cfa242b77e42c2385e3c4cb8e51086965cc7d42768f2c52364fa3fd4ec77dc5

Existing readiness reports supplied historical requirement context; current production call sites and arithmetic were inspected independently. No numerical/storage capacity success, reserved future remote space, scientific retention amendment or complete implementation is inferred. The coordinator's actual current server report is separately qualified above.
