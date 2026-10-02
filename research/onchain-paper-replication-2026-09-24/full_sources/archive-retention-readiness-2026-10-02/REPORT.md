# Remaining archive and retention boundary — October 2, 2026

This is a read-only engineering/requirements investigation. Observed producer-to-
terminal sources are in progress, not asserted accepted or execution-admitted.
Exact29source snapshots and three compact metadata pins are in observations.json
and observed-source/. No package edits, tests, empirical runs, transfers or
historical deletions occurred.

## Finding and next decision

The current archive route handles matching pair-event payloads. It does not
archive score tails/batches, checkpoint trees, dictionary/sample artifacts, MCM
numeric outputs or saved graph artifacts. Current local-only post-close checks
still require those bodies. None can simply be removed after the existing pair
seal. Current-format local score/matrix payload remains55,439,818,752bytes across
nine32-motif resource graphs, before dictionary/checkpoint/edge/metadata costs.

**Preferred next candidate for policy review: prospectively versioned bounded
restart-state retention with complete scientific score/output blocks and immutable
manifests.** Before extending this storage representation mechanically, decide
the prospective retention contract. All-successful-progress checkpoint retention and duplicate
purpose-bearing score tails are operational implementation choices, not located
paper requirements. A reviewed fresh retention contract can bound future restart
state without changing matching equations or final scientific outputs. It must
not reinterpret or delete historical evidence, reduce cell populations, substitute
hashes for claimed recoverable bytes, or weaken independent verification.

If preserving the current completed-pair evidence representation is selected,
the narrow next implementation slice is **archived completed score tails**,
keeping active tails and sealed float64 batches local initially. This removes the
largest remaining duplicate local payload,46,199,848,960bytes conditionally, and
requires one coherent writer/reader/stage-verifier change. It does not by itself
solve checkpoint growth or prove whole-workflow capacity. If a reviewed compact
final-evidence policy instead makes successful tails temporary verification
scratch, use an explicit new contract rather than archive unnecessary duplicates
by default. Both are prospective choices requiring independent review.

## Actual local dependencies

Here `<stage>` means the exact claimed Stage.root; `<output>` means the exact
publication ticket directory; canonical paths and recorded device/inode identities
remain part of the current contracts.

| Component/path | Live necessity and retained checking | Current disposal status |
|---|---|---|
| `<stage>/matching` pair events and archive maps | Archived writer handles chunk preservation/disposition; owner seal joins full replay then local anchored receipts | Only owned success payloads disposed by the accepted explicit archive protocol; original historical local events untouched |
| `<stage>/stream/tails/tail-*/records.bin` | Active append; after completion `_seal_check`, `_history_check`, compact_stage.stream and archived_stage inspect every tail, its purpose chain and equality to batch values | Must remain local today, including after stage/owner closure |
| `<stage>/stream/batches/chunk-*.bin` and `.json` | Float64 score batches; full batch verification and compact_mcm_output._chunks read them to construct float32 output | Must remain local today; tail-only proposal intentionally keeps them |
| `<stage>/stream/{start,complete,seal-*}.json` | Scope, owner, exact ordinal/cell range, predecessor chain, tail terminal and batch-header joins | Keep bounded local immutable control evidence; a new format must specify exact replacement inventories |
| `<stage>/checkpoints/event-*/` | Matching annealing M/Q/V `.npy` and optional hardening order plus manifests; checkpoint event references join exact local trees | Must remain local under current stage verification, even for subsequently successful comparisons |
| `<output>/artifact/{matrix.f32,manifest.json}` and receipt.json | Saved float32 matrix; source stage checked again, matrix fully inspected, temporarily mapped readonly and compared to original numeric result | Keep today; archiving needs a new output reader/publication contract, not a path remap |
| `research_artifacts/onchain_compact_graphs/<workflow>/<experiment>/<graph>/artifact/` | Separate serialized MCM and edge-index arrays, verified by strict component reader and loaded for native features | Keep today; matrix copy alone is4bytes/cell, plus edge arrays/headers omitted from lower bound |
| compact sampler/sample/dictionary artifacts and resident objects | Sample proof and dictionary numeric/evidence checks are in every MCM/terminal ancestry chain; resident samples persist | Exact local artifacts/resident ancestry remain required; size/lifetime unresolved |
| archive operation/read/seal/journal metadata | Original owner/writer/read claims, exact namespaces and closed-ledger state anchor post-close verification | Retain; remote existence or untrusted self-rehashed metadata cannot replace these anchors |

Source anchors: score_tail.verify/seal; mcm_score_stream.py:_seal_check,
_history_check,finish; compact_stage.py:stream(lines126–175); archived_stage.py:
_trees and _inspect(line130 calls local.stream); compact_mcm_output.py:_source,
_chunks,_inspect,open_verified; compact_mcm.py:Produced._evidence/_numeric/_check;
compact_graph_artifacts.py:Published._evidence/_load; compact_terminal.py:_original.

Terminal._original rejoins original dictionary/sample proof, owner stages, each
resident MCM/feature identity and saved graph artifact after closure. It is not a
cold reload interface. Remote-copying or rematerializing a file at an arbitrary
path cannot satisfy the current original-object/path/inode and exact-inventory
checks. New local-only anchored checks must be deliberately defined; they may
prove earlier verified content but must not claim fresh remote availability.

## Conditional byte lower bounds, not physical upper bounds

The pinned compact-workflow lower bound assumes all nine saved graphs receive
one32-motif MCM. It is not an adopted scientific graph union. Per cell: current
purpose-bearing tail80bytes, float64 batch8bytes, two float32 copies8bytes. Pair
events are excluded here because this investigation starts after their offload.

| Week | Tail bytes | Batch bytes | Two float32 matrix bytes | Local subtotal after pair offload | Conditional subtotal after tail offload |
|---|---:|---:|---:|---:|---:|
| 2022-01-03 | 5,245,683,200 | 524,568,320 | 524,568,320 | 6,294,819,840 | 1,049,136,640 |
| 2022-06-13 | 4,526,766,080 | 452,676,608 | 452,676,608 | 5,432,119,296 | 905,353,216 |
| 2022-07-25 | 7,076,405,760 | 707,640,576 | 707,640,576 | 8,491,686,912 | 1,415,281,152 |
| 2022-11-07 | 4,187,829,760 | 418,782,976 | 418,782,976 | 5,025,395,712 | 837,565,952 |
| 2023-06-05 | 4,703,354,880 | 470,335,488 | 470,335,488 | 5,644,025,856 | 940,670,976 |
| 2024-01-01 | 4,691,064,320 | 469,106,432 | 469,106,432 | 5,629,277,184 | 938,212,864 |
| 2024-03-11 | 5,903,718,400 | 590,371,840 | 590,371,840 | 7,084,462,080 | 1,180,743,680 |
| 2024-08-05 | 4,366,103,040 | 436,610,304 | 436,610,304 | 5,239,323,648 | 873,220,608 |
| 2024-12-23 | 5,498,923,520 | 549,892,352 | 549,892,352 | 6,598,708,224 | 1,099,784,704 |
| Total | 46,199,848,960 | 4,619,984,896 | 4,619,984,896 | 55,439,818,752 | 9,239,969,792 |

The original50,819,833,856score-history bytes equal tails+batches. A float64
batch and both float32 copies would still remain under the tail-only boundary.
Graph manifests separately declare4,779,690,416existing five-array bytes; do not
subtract this again from measured free space if those files already occupy that
filesystem. Current producer retains graph artifacts/originals through closure,
so sequential production does not imply completed local artifacts disappear.

No physical upper bound follows. Dictionary samples/matrices, matching snapshots,
model/optimizer, saved edges, progress/events, metadata/filesystem allocation,
upload/readback/download staging, memfd/RAM copies, partial failures and prior
attempts are excluded. The user10GiB floor remains. Source-observed selected
resident sampler requires direct16bytes/center plus unknown retained-sample/index/
NumPy-choice RAM; optional mapped sampler20GiB+workspace is route-specific.

## Retention requirement audit

| Authority/source | Actual requirement | Consequence for successful per-pair progress bodies |
|---|---|---|
| Workspace AGENTS and operative AGENTS | Preserve original raw stores, historical worktrees, dated evidence, frozen gates/spent samples and all attempted/unavailable cells | Existing artifacts cannot be retroactively discarded or relabeled as scratch |
| Retained paper.txt §2.2.2/Algorithm1 and scientific PROTOCOL | Literal matching/temperature/hardening; full graph/motif architecture and populations | No mandate to keep every intermediate matching checkpoint body was found in the retained article text or its algorithm specification |
| REPLICATION_SPEC C01–C02,C05–C07 | Traceable choices, no omitted core block, independent arithmetic/tolerance and reproducible sampling/dictionary | Retention change cannot alter matching, sampling, RNG, tolerances, dictionary reuse or hide scientific deviations |
| C10–C12,C17 | Complete chronology, all predeclared fit/prediction cells including failures/unavailable, common comparators and full table scope | Compact evidence must preserve exact denominator, identities, outcomes and lineage; no selective favorable retention |
| C13–C14 | Saved-model CPU replay/independent metrics and bounded saved-checkpoint inference in clean offline environment | Required neural model/optimizer/config/provenance and selected replay bytes must remain genuinely available; matching progress matrices are not named as mandatory saved-model inference inputs |
| C15 | Enforced resource containment, complete terminals, no orphan/unexplained OOM | Bounded restart state and cleanup/failure preservation must be tested and resource-metered |
| C16 |100%immutable output/manifest coverage and verified external recovery of compact evidence/exact raw members for bounded replay | A checksum is not recoverable body evidence. Prospective distinction between retained outputs and disposable restart scratch must be explicit before execution; existing declared outputs remain preserved |
| C18 | No critical unresolved review finding; material assumptions/disagreements prominent | Independent review must approve any changed retention/verification contract before adoption |
| PROTOCOL resources paragraph; pilot_successor_02/CHARTER-v2 | Graph checkpoints; safe training/long-partial cadence≤600seconds where permitted; model/optimizer/cursor/RNG/provenance; failed attempt identity/last progress/unmet scope | Requires recoverable bounded progress and failure evidence, not an explicit universal forever-retention rule for every successful matching internal state |
| IMPLEMENTATION_ASSUMPTIONS October1 compact variant | Explicitly states progress/failure snapshots remain preserved; cadence changes are prospective operational variant | Current prospective variant does require those saved snapshots; a new reviewed variant is needed to change this |
| compact_policy.validate and compact_matcher | Cumulative max_total_checkpoints/bytes reserve every permitted retained snapshot; _save writes incomplete-state progress and emits referenced manifest | Concrete self-imposed persistence protocol, currently binding; cannot merely lower its caps or remove directories |
| compact_stage.checkpoint, archived_stage._trees | Exact progress-event→ordinal→manifest/tree joins and exact inventory; source/tree hashes fully reread | Current final verification requires every referenced tree. A hash-only replacement would fail and would change verification semantics |

C03–C04 data completeness/conservation and C08–C09 neural correctness remain
unchanged; no retention proposal supplies their missing empirical evidence.
Original PROTOCOL/resources.json contain historical20GiB startup settings; later
user/route decisions must be explicitly bound in a new registration rather than
silently editing those historical files. This audit is not an amendment.

A **prospectively reviewed bounded restart-retention policy is plausible** without
changing the algorithm or C01–C18 objectives. It must predeclare which objects are
scientific outputs, replay evidence, failure evidence and temporary recovery
state; retain immutable exact inputs/protocol/runtime/source/RNG/sampling,
dictionary and ordered final scores/features plus all terminal/cell dispositions;
retain full required neural checkpoints and the independently chosen replay set;
and preserve active/failed matching recovery state. Successful transient restart
bodies may then be retired only under that new contract after independent numeric
and lineage verification. This changes which historical intermediate states can
be replayed: disclose that loss. Retained hashes prove commitments, not recoverable
bytes or arithmetic correctness by themselves. The review must establish that
final numeric checks and required bounded replay remain sufficient, not merely
assert that a final score exists. All historical snapshots remain untouched.

The same distinction applies to two168-byte pair events per completion,80-byte
score-tail records and duplicate MCM storage: these encode present audit/runtime
contracts, not fundamental paper storage minima. Alternatives cannot inherit the
current verifier's acceptance automatically. No smaller byte upper bound is
invented here; exact retention policy/population/verification must come first.

Exact acceptance-source locators are REPLICATION_SPEC.md:C11 line200, C13 line202,
C14 line203 and C16 line205; PROTOCOL.md:resources/preservation lines112–119;
IMPLEMENTATION_ASSUMPTIONS.md:compact operational variant lines26–39; and
pilot_successor_02/CHARTER-v2.md:resource/checkpoint/output lines18–46. The audit
snapshots pin these bytes, so later line drift cannot change the cited meaning.

Logical comparison for prospective review: current selected payload is
249,479,184,384bytes before dictionary/checkpoint costs; existing event archival
leaves55,439,818,752local score/matrix bytes; retaining float64score blocks and the
two current float32outputs while eliminating or archiving duplicate successful
tails leaves9,239,969,792bytes of those selected numeric payloads. Bounded restart
state would additionally limit unquantified checkpoint growth excluded from all
three figures. A change to pair-event retention, output duplication or scientific
proof structure is a further explicitly reviewed decision, not implied by this
comparison. None is a physical upperbound or measured admission budget.

The existing archived-pair variant remains supported and unchanged. A new
retention version requires independent review and a committed pre-execution
amendment defining outputs, scratch retirement, failure/recovery and independent
verification. This is the existing research governance route, not a request for
new user permission. It does not authorize implementing changes during the active
source freeze or modifying existing producer ownership.

## Concrete implementation boundary after policy decision

For the conservative tail-archive route, assign one owner the new tail payload
writer/reader plus mcm_score_stream, the common stream verifier consumed by
compact_stage/archived_stage, archive policy/reservations, and owner-seal joins.
Keep the old local route unchanged. New explicit registered schema/version must:

1. Reserve exact owner/stage/stream/chunk ordinal, start/count, scientific scope,
   dtype/endianness, purpose order, tail start/terminal/body hash, batch-header/
   payload hash and destination, predecessor hash and remote transport namespace.
   No cache or arbitrary caller-supplied receipt becomes the trust root.
2. Keep current active tail local. After durable tail completion and batch seal,
   verify full source content and value equality, upload/read back under a fresh
   owned claim, and anchor the immutable successful verification in original
   owner/stage evidence. Retain exact ordinal/purpose/value digest needed for the
   matching-event-to-score join; hashes cannot omit that scientific link.
3. Only after successful full checks and cleanup may the new protocol dispose
   its explicitly owned success payload. Preserve failed/partial local and remote
   namespaces, spend reservations without refunds, and prohibit retry under old
   identity. Validate canonical paths, exact inventories, no symlink/hardlink or
   cross-device substitution, source inode/descriptor identity through callbacks,
   and cleanup uncertainty as fatal before acknowledgement.
4. Rework stream.finish, stage/owner evidence and postclose check to consume those
   anchored tail proofs and retained batch bytes. Current compact_stage.stream
   cannot accept an absent tail. Local-only postclose verification must remain
   callback-free after its final live lease and must not fetch/recompute/bypass
   owner closure. Bounded explicit new remote verification claims are distinct.
5. Preserve local float64 batches and numeric output/graph consumers in this first
   slice. Subsequent batch/output eviction requires a separate scientific reader
   contract; checkpoint-tree retention requires the separate decision above.

Important primitive limitation: archive_chunks.preserve intentionally retains
original+snapshot+readback. It alone does not free disk. Reuse the fully anchored
owned-disposition/consume pattern, not bare preserve plus ad-hoc unlink. Success
archive_consume retains metadata and removes its own consumed payload; failed
attempt evidence remains. Rehashing a user-supplied mapping is not equivalent to
trusted original claim/seal binding.

## Separate dispatcher/config/transport ownership

- `job_payload.py:execute_fit_payload` currently calls
  `compact_native_producer.produce(run,name,job,graphs,examples)` without its new
  archive_transport keyword. The producer requires transport iff descriptor
  compact_archive_execution is selected. Outer selection/config/transport
  construction and injection remain a separate integration task. Do not construct
  transports from unreviewed defaults or infer selection from installed modules.
- `job.py` owns execution-job resources/source closure/guard startup; `resources.py`
  and `workflow_storage.py:StorageWatch` own containment/storage observations.
  StorageWatch counts sampled st_blocks, not a hard filesystem quota. Extend
  exact registered roots, aggregate reservations and failure handling; don't
  mislabel logical caps as physical limits.
- Registered execution_job.representation_jobs, plan.producers and their descriptor
  must agree on compact_archive_input and backend/policy hash, as enforced by
  compact_training._archive_extension and archive_owner_policy._inputs. There is
  no compact_archive_execution.py: it is a descriptor field. New config owner
  must freeze exact graph union, dictionary reuse, retention version, limits and
  transport identity in fresh inputs; no historical configuration edits.
- `archive_transport.py:Transport/Budget` owns finite SSH/SCP calls and shared
  conservative payload accounting. `archive_owner_operations.py` reserves whole
  operation allowances but explicitly is not transport metering. Join both with
  one whole-workflow budget and durable attempted-transfer records; no per-stage
  budget reset. Transport.get reserves `(expected_bytes//32768+1)*32768`, larger
  than decoded bytes; include that rounding for each readback/replay/download.
  Upload source bytes and sealed memfd copies also affect RSS. SSH framing,
  bounded diagnostics/filesystem overhead are excluded from payload budget and
  need separate physical/network accounting. No retry/refund is implicit.
- `archive_owner_policy.py` currently bounds only event payload: stages×max_events
  ×168, with decoded-transfer multiplier3+max_stage_verifications. Score tails,
  batches, checkpoints and output archives need explicitly separate typed
  populations/allowances and exact claim namespaces; silently inflating the event
  cap is not a sound replacement. Remote free-space/capacity admission is absent
  from Transport and remains required before any real use.

## Verification and limits

`capture_metadata.py` ran once under checkout-local .venv Python; check01.log
records PASS,29source captures, three compact inputs, nine-week arithmetic and
unchanged hashes across the bounded capture. requirements02.json/check02.log pin
and check the additional requirement-source audit. No numeric arrays or empirical
outcomes were read. No tests were run during sourcefreeze check04. Initial guessed
filenames caused read-only lookup errors; corrected exact modules are recorded.
No production failure or fresh resource measurement is claimed.
