# Incremental independent implementation review

Tasks2–3: separate read-only reviewer independently reproduced four defects in
synthetic fixtures. Corrections before empirical use:

- Expected complete weeks are enumerated from declared coverage; empty source
  streams and absent expected weeks fail explicitly. ETH member status/count and
  expected per-member/total decoded counts are mandatory. Actual retained source
  inventory/date/block bindings still require stage-specific admission before
  decoding; adapter checks alone do not establish canonical-chain completeness.
- Aggregate-edge≤transaction inequality now applies only to ETH. BTC proportional
  projection can have more edges than transactions; its own rational conservation
  remains Task10's responsibility.
- Artifact directories and price intents synchronize parent directories before
  subsequent work. Newly created ancestors are synchronized too.
- Graph array buffers now use immutable bytes; attempts to reenable writes fail.

Four regression examples failed before the corrections, then passed.29 data-layer
checks pass. The original Task3 completion covers synthetic adapter software only;
C03 real source coverage and C04 real source-to-graph reconciliation remain pending.
No empirical data was decoded by the reviewer or implementation tests.

Task4: scalar Eq1 scores checked against independent exhaustive assignments through
four nodes; literal one-step half coefficient and48-step schedule tested. CPU
float32 tensor scores and soft matrices match within C06 tolerances on current
fixtures. GPU check skips explicitly because CUDA is unavailable; C06 GPU evidence
and full-size execution remain pending. Independent math review in progress.

Task4 independent review found a float32 iterative-roundoff failure outside the
initial fixture corpus. The retained regression failed before correction. A new
pre-result precision amendment preserves original protocol bytes and declares
float64 internal matching with float32 outputs.44 focused checks now pass,1 CUDA
check remains skipped. No objective or tolerance was changed. Active matching
configuration: config/matching-stable.json via protocol-freeze-v2.json.

Task5 independent review found mutable nested sampling/dictionary metadata and
partitioned clustering ties resolved by chunk order instead of original sample
order. Immutable nested records, content-bound dictionary identities, stable
original-ID ties and expanded memberships now have retained regression checks.
Task5 small synthetic tests pass; whole-graph sampling storage and speed still
require measurement and cannot be inferred from these fixtures.

Task6 independent two-head directed GAT scalar calculation (including mixed-sign
logits) agrees within1.39e-16. The frozen full architecture and initialization
match implementation. Two retained failing regressions caught an entirely masked
batch graph disappearing at pooling and NaN padding poisoning MLP gradients.
Both were corrected before fits: contiguous original batch IDs remain required,
empty admitted graphs reject, and masked inputs are zeroed before the MLP.
53 focused tests passed,1 CUDA parity check skipped at this checkpoint. Full
post-change offline validation and empirical scale checks remain pending.

Task7: independent review found no clock leakage in the frozen expected-week join,
label purge or unique training-input scaler. Retained fixes reject regression
broadcasting and contracted prediction batches, preserve constructor failures,
recover a final-epoch checkpoint without refitting, and prohibit continuing a
completed cell even when another cell caused the enclosing run to fail.
Synthetic registered Git fixtures exercise original and new continuation claims;
interruption after epoch1 and after finalepoch3 reproduces uninterrupted weights
and loss logs exactly. Original claim identities remain consumed. Real worker-death
proof and exact empirical factory/input membership still require release review.
Task7 pure checkpoint tests also reject corrupt bytes, absent RNG and provenance
mismatch. No empirical fit has been performed.

Task9 software review: independent four-chunk HLSTM calculation matches exactly;
asymmetric classification/regression fixtures and within-year moving-block
bootstrap match the frozen conventions. Actual baseline fits and comparison
coverage are pending. Resource guard review and synthetic containment evidence
are recorded separately in the forthcoming resource amendment.

Tasks10–12 incremental review: independent rational BTC fixtures caught Decimal
context rounding; conversion now uses exact Fraction(Decimal(text)) and rejects
arbitrarily long off-grid decimal strings. Whale review caught strict-threshold
changes from log/exponential round trips; raw aggregate arrays are preserved and
used directly. Induced subsets retain isolated selected vertices. No original
cohort has been invented. Default small comparator capacity caps were removed;
actual callers must supply a ceiling derived from the admitted resource budget.

Independent dense WatchYourStep/Adam reconstruction agrees with the blockwise
implementation to9.31e-10 in embeddings and4.77e-6 in summed float32 objective.
GraphWave sparse columns, Node2Vec fixed p=q=1 contexts and GIN incoming/self rules
match the frozen definitions. Node2Vec, WatchYourStep (including partial gradients)
and GraphWave interruption fixtures now reproduce uninterrupted outputs exactly;
checkpoint callbacks run within600seconds at safe batch/column boundaries. Actual
embedding-stage continuation still requires a new admitted claim and verified
source/config/input identity. Exact1420/initial45 cell enumeration is tested.

Pilot release review (September24, independent, still pending): metadata-only
reconstruction finds63 mapped days in9 complete calendar weeks,3312 mapped byte
spans,73,049,185 declared rows and109 distinct source/component cells. Source-map
and ancestor receipt hashes were checked without decoding transaction payloads.
The spent ETH2022–24 classification and cumulative17+34=51 allowance are explicit;
this source reuse is exploratory, with no fresh confirmation claim. Original
mapping failures and original registration bytes must remain retained.

Release review found and the implementation corrected unbound worker JSON reads,
nonrecoverable mutable MCM prefix checksums, and absence of an external post-death
observer. Worker configuration/source-map parsing now checks the exact parsed
bytes against registered input hashes; generated stage inputs are chained to
artifact hashes. MCM checkpoints now retain separate immutable, synchronized
prefix arrays with graph, dictionary, matching configuration and source identities.
Worker logs and guard receipt hashes are retained. These are implementation checks,
not evidence of full-size throughput or empirical predictive validity.

Two observer qualifications remain under correction at this checkpoint. In
`pilot/reconcile.py`, a lifecycle complete receipt alone currently causes observer
status complete even when the resource guard failed. An independent temporary-file
counterexample with an empty fake cgroup and a guard OOM failure reproduces that
contradiction. Also, an admitted claim with no recorded cgroup must not assert
verified cgroup death. Resource completion needs separate successful guard evidence;
existing lifecycle receipts must be preserved. The outer launch supervisor's
SIGKILL path also needs an explicit liveness/observer recovery policy: the present
monitor lease detects monitor death but does not detect loss of its own parent.
The previously retained guard signal/lost-monitor probes do not test this new
outer-supervisor boundary. No release approval is recorded here.

Financial evaluation release remains separate. Review identified missing actual
feature/scaler content bindings, scientific cell IDs incompatible with lifecycle
IDs, late output reservation, unsynchronized SVM persistence, and no explicit
prediction-only recovery after a completed fit. These require corrections before
financial fitting. Resource forecasts must still account for all retained raw,
graph/feature, checkpoint, temporary and backup storage, and global training
sampling/dictionary costs before a full training release. The small pilot's
single-week dictionary and synthetic one-graph neural batch cannot establish
those costs. No financial returns, fees/funding book, real test labels, saved-model
replay, CUDA parity, full-size resource claims or raw completeness were tested by
this release review. The parent owns the active full offline suite; it was not
rerun by the reviewer.

Additional release concurrency finding: `pilot/launch.py` checks for an existing
receipt before spawning its monitor, but that check does not reserve ownership.
Two simultaneous launchers can both pass; the second monitor then loses the
exclusive receipt creation and exits, after which its supervisor reconciles the
first monitor's receipt and may stop the active original unit. An exclusive
supervisor reservation and exact monitor/receipt ownership binding are required
before reconciliation; a duplicate invocation must not signal the original job.
This interleaving was established by source inspection, without launching either
empirical process.

Pilot conditional release review, September24 (supersedes the pending pilot
blockers above): no remaining critical blocker was found for the resource-only
109-cell stage. Approval is conditional on committing the reviewed source,
registration and charter before admission, and successful completion of the named
full offline verification. This approval does not cover financial fitting,
provider requests, paid resources, predictive conclusions or full-paper completion.

The reviewed gate-v2 SHA256 is
`b0a06f6a7710ec0788f8e94105b76caa57f16e0655c75f974e9c743721faed57`.
All26 registered source hashes,82 registered input hashes, the charter hash,
lifecycle runtime hashes and pinned environment inventory matched independently.
The preserved initial gate SHA256 remains
`bc8df5009c5a37b00082cbf2c2dd76d5ed9117e346543a4ff2bb0fcb3294d3c1`.
Independent enumeration again finds109 exact distinct cells,63 source days,
9 weeks and73,049,185 declared rows. Prior17 claims and cumulative ceiling51 remain
explicit. The narrowed source set includes the current transitive pilot imports;
shared admission/lifecycle helpers are bound separately by runtime hashes.

Atomic supervisor reservation and monitor identity binding prevent a duplicate
invocation from owning or stopping the original process. The Linux parent-death
signal has a parent-PID race check. Guard cleanup and observer qualification remain
separate from the lifecycle terminal. Wrong ownership and absent cgroup proof
reject closure; failed or missing resource terminals cannot qualify a completed
lifecycle as successful resource verification. Observer-only recovery now accepts
an existing postmortem directory, verifies already published output bytes, and
publishes missing immutable outputs without replaying empirical work.

Independent targeted execution passed9 tests: all8 pilot tests plus the isolated
real-process parent-SIGKILL→monitor-SIGTERM test. The latter proves Linux signal
binding using synthetic forked processes; it is not an end-to-end empirical pilot
or a new measurement of resource capacity. The previously retained independent
cgroup signal, monitor-loss and affinity checks supply the complementary guard
cleanup evidence. No transaction bodies or financial experiments were read or
rerun during this review. The full offline suite was not duplicated. Real source
completeness, throughput, memory/storage forecasts, CUDA parity, saved-model CPU
replay, financial comparison coverage and numerical agreement remain unproved.

Financial evaluation follow-up review (September24; no financial release approval):
reversible scientific/lifecycle IDs, actual feature-tensor hashes, admitted feature
binding artifacts, source/fold/training-row checks, scaler values in configuration
identity, early prediction reservation, synchronized SVM persistence and completed-
model inference recovery address the previous implementation findings. Completed
fit recovery reads a registered completion receipt/checkpoint from the registered
parent fit directory and verifies checkpoint/member hashes. It performs no refit.

Four remaining corrections were identified in the reviewed evaluation snapshot:

- The actual test dates are not rehashed; `require_test_mask` only compares stored
  strings. An independent synthetic90-row example still passes after dropping its
  final row while retaining the old hash. Exact ordered unique test dates must be
  recomputed, and test input/label bytes must be bound to an admitted example
  artifact so a common mask cannot conceal altered outcomes or price inputs.
- Completed-fit recovery bypasses `_reserve`, so the common entry path must check
  that the current lifecycle cell is registered and that provenance.source_commit
  equals the admitted source before reserving any prediction output.
- Neural prediction/recovery errors lack the prediction failed receipt currently
  written only for SVM errors. All post-reservation branches need one durable
  failure path; a completed fit must remain completed and must not be repeated.
- Configuration identity omits lane/asset although predictions write both. Bind
  those fields and verify that the production seven-component scientific ID
  agrees with the cell fields, preventing an unchanged fit identity from acquiring
  a different asset/lane label.

Current masked GAT/GIN/diagnostic paths zero excluded node inputs before learned
layers, exclude masked endpoints from message aggregation, and exclude them from
pooling. Feature hashes include the mask bytes. This does not independently prove
that producer-supplied topology or masks correspond to the admitted whole-graph
hash; the eventual registered feature producer must establish that relationship.
No empirical examples, actual saved models, raw payloads, or financial outcomes
were inspected. The named full offline suite was not duplicated.

Evaluation correction review (September24, supersedes the four evaluation defects
above): common admission now checks the active run, registered lifecycle cell and
current source on both ordinary fitting and completed-fit recovery. Actual ordered
unique test dates are rehashed; actual test rows, fold/source identities and scaler
values must match an admitted or already published example manifest. All scientific
cell fields enter configuration identity, and production scientific IDs must agree
with those fields. A common post-reservation exception handler now preserves
prediction failures across neural, SVM and recovery paths without invalidating or
repeating a completed fit.

An independent synthetic Git fixture rejected each of four mutations before
fitting: one dropped test date, a changed test label with unchanged dates, a wrong
source commit, and an unregistered cell. An injected neural fit-entry error produced
the expected durable prediction failure receipt. No remaining defect was identified
in this bounded correction review. Producer-specific graph topology/mask lineage,
real price/calendar admission and independent real saved-model replay remain
financial release requirements; this does not grant financial release.

Offline runtime isolation review: `scripts/verify_offline.py` now launches the
standard and neural groups in separate fresh pytest processes. Independent inventory
reconstruction found212 modules partitioned into184 standard and28 neural modules,
with no omissions, duplicates or overlap. Existing process limits and assertions
are unchanged; either group's failure still makes the named command fail. The
retained first full-suite log shows the five failures were the low-RSS checks
(one dated lifecycle test and four options-worker subtests). The synthetic shared-
collection regression passed independently, confirming that neural collection state
cannot contaminate the standard test process. This tests isolation rather than
asserting that the active second full suite has passed. That suite was not duplicated,
and the original failed-suite evidence remains retained.

Task13 bounded engineering reproduction review (September24): the reviewer loaded
and replayed the preserved `replay/synthetic-01` checkpoint using the separate
`/tmp/onchain-paper-replay-env-20260924-01/bin/python` interpreter with a network-
denying audit hook installed before neural imports. Both saved predictions match
exactly (maximum absolute difference0; fixed atol1e-5,rtol1e-4). The five fixture
members cover all saved input/configuration/expected/checkpoint files and total
507,035 bytes including the outer manifest. The checked fixture manifest SHA256 is
`ad3047707bbb903b2647e43b633b4deb7aa9d016d66af35ec25f3ba130f43b09`.
No fixture, saved expected value, checkpoint or previous receipt was regenerated.
The interpreter's actual runtime inventory matches `fresh-environment-01.json`;
its virtual-environment configuration disables system site packages.

The preserved fresh-environment JUnit evidence contains191 test cases:190 passed,
zero failures/errors and one explicit CUDA-unavailable skip. Independent inspection
of `implementation-coverage-v1.json` verified all34 F/U IDs against frozen fidelity,
all recorded code hashes, all88 linked test dispositions against that JUnit file,
and the parent fidelity/JUnit hashes. No missing or mismatched link was found.
Coverage SHA256 is
`97aa7f61a748c71e405d1be2fdba1136dc91b41f07cf72df7b5b370611b54983`.
The frozen fidelity file remains unchanged; blocked original fund-cohort and other
empirical limitations remain explicit despite passing component tests.

This evidence supports the clean-environment synthetic reproduction requirement.
It does not establish empirical C13, independent reconstruction from transaction
raw data, all-architecture/asset/lane saved-model replay, paper numerical agreement,
or external recoverability under C16. The example uses synthetic MCM inputs and
one synthetic optimizer step, not an empirical motif dictionary or prediction
experiment. Execution loaded source from the current checkout; committed compact
backup, remote commit verification and bounded retrieval remain separate actions.
The active named full offline suite was not rerun by the reviewer.

BTC weekly assembly independent review (September24, correction required): exact
rational edge and incident-volume arithmetic passes an independent fixture with
repeated sender/recipient addresses, an observed self-transfer and an excluded
nonunique script. The manually derived edges are2,5/2,2,5/2 satoshis; incident totals
are17/2,9/2,5, summing to twice the9-satoshi transferred amount. Included and known
excluded fees total2 satoshis. Per-edge contributing-transaction counts, log/native
attributes and strict whale filtering against the exact sidecar agree. The current
full-stream ingestion performs duplicate identity/spend and observed value/address
checks before yielding weekly graphs; complete-week declarations still require
independent decoder/source admission.

A material observed-prevout completeness defect remains at this review snapshot:
`btc_weekly.py:68–77` accepts a spend of index9 from an observed creator transaction
that declares only output0, because the supplied prevout creates a new output key.
An independent synthetic example is admitted as two transactions. Track each
observed creator's complete output count and reject every referenced index outside
that range, regardless of stream order, before yielding any graph. Matching a
supplied prevout value is insufficient when that output was never declared.

An initial suggestion to infer spend order from timestamp comparison was withdrawn:
Bitcoin header time is bounded by the preceding11-block median, rather than the
immediately preceding block timestamp. Same-block transaction order is separately
constrained. Therefore chain-order validation requires admitted block height and
transaction position, not a strict creator-time≤spender-time rule. See the
[Bitcoin developer block reference](https://developer.bitcoin.org/reference/block_chain.html).
The timestamp-only fixture is not evidence of an invalid chain. Prevout source
lineage, chain order/maturity, complete raw decoding, external sidecar persistence
and real full-history conservation remain source/integration admission requirements.
No empirical transactions were read or historical job rerun.

Pilot release condition satisfied (September24): independent verification against
commit `040d4145fa83e8c4f826abd18d1cf15dd2163413` found the reviewed gate-v2, all
registered source/input/charter bytes and runtime helper hashes committed and
unchanged. Gate SHA256 remains
`b0a06f6a7710ec0788f8e94105b76caa57f16e0655c75f974e9c743721faed57`.
The named full offline check02 is terminal successful:2747 standard tests plus97
subtests,189 neural tests and1 explicit CUDA skip. Guard child exit is0, cleanup is
verified, limit reason is null and OOM counters are zero. Terminal receipt SHA256:
`7a0e66e7dc969dd4f242a5064030b39f4ae567f72865faeb4ebbbd3a69a0cb6a`;
retained log SHA256:
`dd97e5a7557465615915202ed77cfe6a57837f1491cc0a1dc7173422a8660088`.
No pilot claim existed at the independent check. The earlier conditional approval
is now satisfied for one launch of the exact registered109-cell resource-only
pilot, subject to the launcher's live admission/resource checks. A later compact
evidence commit must retain these bound bytes. This is not financial-run approval,
a resource feasibility conclusion, or empirical replication completion.

BTC weekly correction verified (September24): the full-stream join now checks each
spent index against every observed creator's declared output count before any
weekly graph is yielded. This closes the reproduced phantom-output defect in both
stream orders. Independent targeted verification passed all10 BTC-weekly tests,
including observed creator amount disagreement, missing prevouts, cross-week double
spends and incomplete/empty coverage. No remaining defect was identified within
the normalized-input aggregator's reviewed scope. The earlier chain-order,
prevout-source, decoder completeness and exact-sidecar persistence requirements
remain admission gates; synthetic aggregation success does not admit BTC data.

Full-history metadata release review (September24; pending corrections): the
proposed gate retains the pilot's exact mechanism/family object,17 prior attempts
and cumulative ceiling51. The source reallocation is arithmetically consistent:
1 aggregate metadata claim+15 missing asset/year body claims+2 asset-price claims
=18 source claims. Reusing existing ETH2022–2024 bodies does not reset exposure.
Independent enumeration confirms72 distinct catalogue/footer slots and85,488
required asset/date/field cells. All transaction-value/price cells remain
unavailable under this metadata stage; this is not financial admission. Current
registered source/input hashes match their files. The1GiB metadata cap is separate
from the unchanged6GiB neural pilot; inability to start the latter does not itself
justify reducing its architecture or source scope.

Corrections required before metadata release:

- `full_sources/metadata-01/launch.py:104–107` uses one process as guard monitor and
  sole post-death observer. Killing that monitor leaves lease-based child shutdown
  but no surviving actor to retain the72-cell terminal ledger and close the claim.
  Use separate durable ownership/supervision and exact monitor identity, with
  idempotent observer-only recovery and an interrupted-artifact hash index.
- `source_footers.py:51` parses a generated catalogue without checking the
  catalogue hash already retained by the worker. Bind and verify the exact parsed
  catalogue bytes before selecting or requesting any footer object.
- The worker's RuntimeError shutdown signal can be caught as an ordinary source
  failure inside capture_catalogue/capture_footer, allowing later requests to
  start. Shutdown must escape those request-error catches or be checked before
  every subsequent acquisition.
- The charter's no-transaction-values wording needs qualification. An independent
  synthetic Parquet fixture demonstrates that footer bytes alone contain value
  statistics (min17,max42 in the fixture), without any data page. No data-page or
  transaction-row decoding is an accurate bound; incidental footer statistics
  must be recorded as metadata exposure and must not enter fitting or selection.

Range/ETag checks, deterministic first/largest/last object selection, finite
request/byte maxima, no retries and retention of failed returned bodies are
present. Real endpoint behavior, current public inventory, schema compatibility,
raw/prevout completeness and source vintage were not tested. No empirical HTTP
request, transaction payload read, registration edit or acquisition occurred in
this review, and no metadata release approval is recorded at this checkpoint.

Metadata controller revision review (September24; release still blocked): separate
owner/monitor/worker/observer files, escaping shutdown exceptions, exact parsed
catalogue-byte hashing and the incidental-footer-statistics qualification address
the original design defects. A new namespace mismatch was found in the copied
controller: metadata `launch.py:15` and `monitor.py:21` still name `pilot-01-guard`,
while `monitor.py:16` reads `pilot-01-supervisor`; the metadata worker correctly
expects `source-metadata-01-guard`. This prevents startup and risks consuming or
interfering with the separate pilot identity. All controller paths must use the
metadata namespace; verify cross-file agreement and disjointness from pilot before
freezing a successor to the preserved gate-v2. No metadata launch is approved.

Metadata release correction approval (September24): no remaining critical blocker
was found in the revised bounded stage. All owner/monitor/worker paths now agree
on `source-metadata-01-guard` and `source-metadata-01-supervisor`, disjoint from the
neural pilot. The reviewed active gate-v3 SHA256 is
`7f528bfd1af7c43abcb068df46fd5222b525064caa20fd965be9d6b1aa8f7318`.
All10 source hashes,25 input hashes, charter/runtime hashes and the environment
inventory matched independently. Original gate/controller drafts remain retained.
The original allocation proposal points to its original draft; this review applies
the same1+15+2=18 source allocation to active gate-v3, without changing the exact
pilot family,17 prior attempts,51 cumulative ceiling, fit count or retry allowance.

The recorded source suite has20 passes, zero failures/errors/skips; XML SHA256:
`ae8d7af74550d0dfb1826ee746c42939745cb45ac8387943957344669aea274e`.
An additional independent synthetic observer exercise verifies that wrong ownership
causes no stop, expired monitoring targets only the recorded synthetic unit,
reconciliation retains all72 cells (one preserved completed cell and71 unavailable
cells), and repeated observation preserves identical terminal bytes. The process
stop was mocked; no real unit or empirical acquisition was signaled. Shared guard
parent-death/lease behavior retains its prior separate synthetic-process evidence.
Exact catalogue-byte binding, escaping shutdown exceptions, partial artifact hashes,
observer recovery and incidental-footer-statistics qualification close the prior
review findings.

Approval is limited to one execution of this72-slot unsigned catalogue/footer
metadata stage after committing the reviewed gate/source/charter and retaining
these bytes through live admission. The1GiB cap,768MiB high watermark,zero swap,
two CPUs,3GiB reserve,20GiB disk floor and30-minute limit remain mandatory.
No transaction data pages, prices, fits, retries, provider contact or paid capacity
are admitted by this review. All85,488 transaction-value/price requirement cells
remain unavailable pending their own source releases. The unchanged6GiB pilot
still needs its own host reserve. No HTTP request or empirical claim was made by
the reviewer.
