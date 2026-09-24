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

Metadata commit condition satisfied: independent Git-object verification confirms
that `d7ac2b5d4bc10e1adbd944f62342f0534ecb9d76` contains the exact reviewed gate-v3,
all registered source/input/charter bytes and lifecycle runtime helper hashes,
matching the current files. No metadata claim existed at this check. The bounded
72-slot metadata release conditions are satisfied; live admission and resource
checks still apply.

Separate proposed pilot startup amendment assessment: lowering startup
MemAvailable from9GiB to4GiB while retaining an effective6GiB kernel memory.max is
not approved as preserving3GiB additional host reserve. With6.5GiB available, a
rapid6GiB allocation can leave approximately0.5GiB before the0.25-second userspace
monitor reacts; memory.high5GiB does not close that headroom gap. Runtime monitoring
remains useful but is not a reservation against rapid allocations or competing
host activity. The current implementation explicitly requires startup headroom at
least memory.max+reserve.

A bounded alternative is to wait for the original9GiB startup headroom, or register
a smaller effective kernel cap and matching high watermark/startup requirement
before any attempt (for example3GiB cap plus3GiB host reserve). Such a measurement
must retain the whole graph and all attempted/unavailable cells, and qualify any
capacity outcome by its smaller tested resource budget. A staged cap would need
kernel readback and renewed peak-headroom checks before every increase. None of
these alternatives permits terminating competing workloads, reducing method scope,
reusing a terminal identity or inferring intrinsic-method infeasibility. No pilot
amendment or pilot launch occurred during this assessment.

BTC decoder/storage follow-up review (September24; corrections pending): the new
Parquet adapter binds object hash/count/date, required transaction position,
contiguous nested indexes and an explicit binary64 satoshi-grid inverse policy.
Observed creator/spender positions and100-block coinbase maturity are checked
without assuming monotonic timestamps across blocks. The immutable wrapper hashes
graph bytes and exact hexadecimal rational sidecars; observed overlap validation
remains distinct from canonical-chain and external-prevout proof.

Independent synthetic adversarial checks identify three remaining issues:

- The observed block table binds height→hash but not hash→height or consistent
  timestamp within a block. Identical hash/height with January7 and January8
  timestamps yields two weekly graphs with observed_chain_order_checked=True;
  reusing one hash at two heights is also accepted. Bind observed block hash,
  height and timestamp consistently, without imposing cross-block time ordering.
- A20000-bit rational sidecar saves and reloads exactly through btc_store, but
  whale filtering fails because subsets.py still converts exact incident values
  to decimal strings for hashing. Use canonical hexadecimal numerator/denominator
  records throughout that exact hash path, with the identity schema explicit.
- The decoder treats every list/tuple address as absent, including a singleton
  uniquely mappable address. Normalize a valid singleton explicitly or reject its
  source schema as unadmitted; do not silently classify it as a nonunique script.

These findings concern synthetic software behavior. BTC body data is not admitted;
chain identity, external prevout values/maturity, schema/precision provenance and
full source/calendar coverage still require their own release and evidence.
Transaction position is an additional required BTC source field; any denominator
amendment must preserve the currently active metadata gate and original85,488-cell
inventory. The reviewer performed no empirical HTTP/body read or control action
on the active metadata attempt.

BTC correction verification (September24; synthetic scope only): all three prior
counterexamples now behave as required. Independent reconstruction rejects one
observed block with differing January7/January8 timestamps and rejects one block
hash at two heights. Cross-block timestamp monotonicity is still not required.
A coherent three-node graph with20000-bit exact rational edge/incident values
roundtrips through the immutable wrapper, then whale filtering removes the middle
node and preserves the two isolated endpoints without decimal conversion failure.
Its receipt explicitly declares schema2 and hex-rational-v1. A singleton address
list now fails as an unadmitted source schema instead of silently becoming absent.
The store also checks Fraction incident types and boolean chain qualification.

The retained btc-synthetic-01.xml contains37 passing cases, zero failures/errors/
skips; SHA256
10b28a5e64c2b8f092ed18087cff2bb671a118d16d2c7e6ca3dd848957be9a22.
No remaining blocker was found in these bounded corrections. This closes the
three software findings only. Empirical BTC schema/precision, canonical-chain
coverage, unobserved prevout proof and calendar completeness remain untested and
unadmitted. Whale integration must pass the exact incident sidecar from the
validated BTC wrapper associated with the same graph; the generic filter accepts
caller-supplied incident values. No empirical payload, HTTP request, active-job
control, registration or ledger mutation was performed by this review.

Feature-pipeline integration review (September24; synthetic, corrections pending):
training-only motif sampling retains the frozen fold bounds, and raw GAT/GIN
features keep topology attached to trainable model inputs. The proposed synthetic
32-sample/32-motif fixture does not alter the production512 configuration.
Two integration defects require correction before this producer is admitted:

- P1, feature_pipeline.py:64–90: alignment is sorted by graph start but predecessor
  availability is checked only against the latest required graph in the entire
  population. Independent synthetic orchestration accepted a January26 training
  decision whose required January25-available graph was aligned to an unscored
  earlier-week graph unavailable until January30. Select only an eligible causal
  predecessor and bind the availability of its complete alignment ancestry;
  reject a noncausal chain before starting its embedding work. Add a delayed
  intermediate-snapshot regression, including transitive predecessor effects.
- P2, feature_pipeline.py:51–54,89,99: the final lineage covers required graphs
  only, although unscored intermediate embeddings affect those graph features.
  The same fixture leaves the intermediate graph absent from lineage and its
  hash present only as an unresolved alignment_previous_graph_hash. Retain the
  complete ordered dependency closure, including intermediate raw graph hashes,
  source hashes, clocks, topology identities and predecessor links. The final
  representation identity must bind that closure for cache/recovery review.

The independent counterexample mocked only the embedding and alignment numerical
kernels, exercising the actual orchestration and final binding without fitting.
No empirical inputs were read. Mandatory callbacks supply checkpoints but this
API has no resume/cache/admission lifecycle; those remain explicitly unimplemented
integration requirements, not completed-run replay permission. Cross-arm reuse
must be enforced by the later registered representation owner. This review does
not approve financial execution, prove production resource feasibility or assert
completion of the end-to-end financial pipeline.

Feature-pipeline correction verification (September24): independent replay of the
prior delayed-intermediate orchestration now processes publication order
(available_at,start_utc,graph_hash). The January26 example's January25-available
graph depends only on the earlier available anchor; the January30 publication
enters later representations. Schema2 retains every intermediate parent and its
raw/source/topology/clock lineage, and motif dictionary training inputs are also
included. The prior P1/P2 findings are closed for this pure component. The retained
feature-synthetic-01.xml has7 passes and no failure/error/skip; SHA256
bac141b57b2c97a3b8e051bba15f554f550d8e06c3773a0f2bf3bd3457c432e7.
Registered empirical ownership, durable cache/continuation and production resource
feasibility remain separate integration gates.

Independent terminal metadata audit (September24): the single closed
paper-full-source-metadata-20260924 attempt identifies committed source
369f2c38383155464a578d12d0c6c6945a0a7bf3 and gate-v3
7f528bfd1af7c43abcb068df46fd5222b525064caa20fd965be9d6b1aa8f7318.
All37 source/input/gate/charter bindings were checked against that Git commit.
All396 indexed retained artifacts match their SHA256 and byte lengths, with no
unindexed file in the source evidence root. Their total is9,078,969 retained bytes;
verified embedded raw HTTP catalogue/footer/trailer bodies total3,815,411 bytes.
The terminal binds all four output hashes and the claim hash. All72 registered
slots occur exactly once and are complete:18 listings and54 sampled footers.

Independent XML reconstruction reproduces6,576 distinct asset/date objects across
BTC/ETH2016–2024, with every expected calendar date represented. All54 footer and
trailer bodies match response hashes and valid Parquet trailer lengths; reading
metadata only independently reproduces row counts, row-group counts and every
reported compressed-column size. The unchanged85,488 required value/price cells
remain explicitly unavailable. The prospective additional BTC transaction-index
requirement still needs its preserved additive denominator; listing completeness
and sampled metadata do not admit transaction values or prices.

Whole listed object sizes reproduce1,661,405,812,699 bytes for BTC and
1,056,738,255,253 bytes for ETH. These are complete-object sizes, not necessary
projected-column storage. In the sampled objects, the declared required physical
columns (including BTC transaction index for this diagnostic) occupy approximately
13.69–35.93% of BTC and5.62–78.72% of ETH object bytes. These extrema are descriptive
sample metadata, not an estimate or guarantee for the full history. Exact projected
acquisition, footer coverage, checkpoint/graph growth and recoverable backup space
remain unmeasured; whole-object totals cannot establish projected infeasibility.

Guard/owner/monitor/observer identities and every observer-bound guard hash agree.
The guard records child exit0, cleanup_verified=true, no limit reason, zero OOM
and OOM-kill events,1,049.697 seconds and97,943,552 bytes sampled peak memory. The
recorded cgroup is absent at review; the observer and lifecycle both report
complete. Terminal SHA256:
46fe5b65159755226e3aedd36c7a6a0c6c2c60eef1155fdb21cd3b18106a1c3f.
No new metadata closure defect was found. The review used retained local metadata
only: no network request, relaunch, transaction-page decoding, financial fit or
registration/ledger mutation. Canonical chain, historical vintage, values/prices,
full daily schema consistency and external raw recoverability were not established.

Prospective pilot cap-v4 review (September24; no launch by reviewer): the reduced
3GiB kernel memory.max and2.5GiB memory.high, zero swap and unchanged3GiB additional
host reserve imply6GiB startup headroom. This addresses the earlier rejected
startup-only relaxation; the kernel cap is actually reduced. The1GiB neural
intermediate estimate is an explicit preallocation screen, not measured OOM or
proof that the remaining2GiB suffices for graph/model/runtime. All9 whole weeks,
109 cells,512 sampled centers and resource-only32 motifs remain unchanged. A
capacity failure under this cap cannot establish failure at6GiB or an intrinsic
method limit.

Gate-v3 SHA256
073300d64b60cb42ae2d42e63f8da9c41b1aefa6afb816c87056c11154807998
binds26 source files and85 inputs plus CHARTER-v2. Every binding and the v4 parent
freeze/file hashes match the reviewed working bytes. The original gate, gate-v2
and CHARTER.md match their committed preserved bytes. Both run.py and phase.py
request the3GiB/2.5GiB contract, and assert_guarded_worker checks exact kernel
readback, zero swap, containment/affinity, lease, covered disks, deadline and
startup cap-plus-reserve. Only the completed metadata claim exists in this
mechanism family:17 inherited plus1 new claim equals18 consumed of51, leaving33
before the prospective pilot. Family objects remain exactly equal; no allowance
is reset by keeping prior_attempts=17. No pilot owner, guard or claim exists.

The36-case retained resource/pilot synthetic report has no failures/errors/skips;
SHA25654c4ea6f36b2fdebfdc500bdf39460ceea48f66d610ac3b2ed6cbdd56ae22bf8.
The amendment design is approved for a new small synthetic actual-guard probe.
Resource-only empirical pilot release remains conditional on successful probe
readback/cleanup and an exact committed source/gate matching these reviewed bytes,
plus live admission/startup checks. This is not financial-fit approval and does
not authorize reusing a terminal owner or claim identity. No guard execution or
empirical launch was performed by this reviewer.

BTC exact-subset integration review (September24): an independent coherent
four-node,20000-bit rational fixture with a self-loop confirms whale removal
preserves three isolated endpoints, fund selection preserves exact retained edge
order, incident values and incoming/outgoing node counts/volumes, and fees remain
explicit origin fees. Save/load preserves the exact result; altered node features
are rejected before filtering. Parent graph hash plus exact-parent hash binds
edges, incident values, fees and chain-order qualification. This closes the prior
caller-side linkage qualification when integration uses filter_btc_graph and its
validated ExactBTCGraph wrapper. The generic ETH/BTC filter by itself still does
not establish that linkage. The39-case retained BTC report has no failure/error/
skip; SHA256
0d24a524148b3082d1f0f3c147806abcc4bc4f78d6e627d9c61445f03dc19342.
No new bounded numerical defect was found. Empirical BTC input admission, full
source coverage and canonical/external-prevout qualifications remain untested.

Cap-v4 actual synthetic probe verification (September24): retained probe-v4-01
final/live bytes are identical and record complete, child exit0, verified cleanup,
no limit reason and no OOM/OOM-kill events. Kernel readbacks are exactly
memory.max3221225472, memory.high2684354560 and memory.swap.max0; startup headroom
is6442450944 with3221225472 additional host reserve. release.json confirms verified
controls. The retained child command invokes assert_guarded_worker with the exact
3GiB/2.5GiB contract, then allocates16MiB; child.log confirms successful verification
and16777216 payload bytes. The recorded unit is inactive/success and its cgroup is
absent. The0.371-second probe's sampled peak is not its instantaneous allocation
peak and is not production capacity evidence.

Probe final/live SHA256:
973139124796de4394d5425b83da797cf6e5ae4e397b81277d69968c5d28de62;
child.log SHA256:
f2405788f51045e9189284936d1b2d5908fc6ae9c3e4fdbd50dc3c030cd9fede;
child_exit.json SHA256:
bfb91ca807d851d6a51a64eb3a12f1436de28ed581d2e5bbbe4be531149c972d.
The actual synthetic-probe condition is satisfied. No remaining precommit review
blocker was found for the previously reviewed resource-only109-cell pilot.
Exact committed reviewed source/gate verification and live admission/startup
checks remain required before its single launch; financial fits remain unapproved.
The reviewer inspected receipts only and did not execute or relaunch any process.

Prospective BTC denominator/documentation review (September24): required-grid-v2
SHA256452f8c781489c2c1dee686bbe361bcf4af937e2b184e61308c13a7139e46c675
adds only BTC top-level transaction index. Independent calendar reconstruction
finds3,288 dates per asset (2016–2024 including three leap years):17 BTC fields give
55,896 cells and10 ETH fields give32,880, totaling88,776. The3,288 added cells are
prospective requirements, not captured/admitted values. The parent grid SHA256
5a4f769f40bfbe2e80698ea4e6f93554332550266332d83574fb67307117662e matches
preserved committed bytes; the terminal metadata source-coverage hash remains
079022f7775bb1e29ebe7e4d00f633ab0ae595672ae288f119b23884131f0339 and
retains85,488 cells. Historical receipts were not retroactively expanded.

BTC_REFINEMENTS_V2.md accurately distinguishes scalar-address schema rejection,
source binary64 precision assumptions, observed-chain checks, exact sidecars and
origin-fee/counter semantics from real source admission. Generic receipt schema2
and BTC wrapper schema3 describe new transformations; they do not reclassify old
receipts. Future body acquisition must bind the revised grid explicitly. Full
values, original fund cohort, canonical chain and independent raw-to-graph checks
remain pending; no financial outcome or new capture was evaluated by this review.

Component-store independent software review (September24; active pilot untouched):
no material defect was found in the bounded numeric checkpoint implementation.
An independent tiny synthetic Adam fixture performs a saved first update and then
compares the next restored update against uninterrupted parameters exactly; PCG
and Torch random outputs also match. Empty tensors, noncontiguous tensor views,
big-endian NumPy arrays and tuple/integer dictionary keys roundtrip as expected.
The restore creates writable independent arrays for optimizer continuation.

Synthetic malformed member traversal is refused. A save interrupted by an
unsupported nested type leaves its partial directory and array evidence without
a final manifest; another save to that directory raises FileExistsError. The
numeric member schema, no-pickle NumPy load, file size/hash and shape/dtype checks,
aggregate array-byte accounting and post-copy hash verification prevent the
reviewed corruption/allocation bypasses. Manifest/context identity still depends
on the caller retaining the externally bound manifest hash; a directory's mere
existence never proves checkpoint completion.

The max_array_bytes limit covers copied array payloads, not total process memory:
JSON parsing/scalar trees, object overhead, mapped pages and temporary copies need
the outer resource cap. Torch tensors restore on CPU and require explicit device
restoration if a later admitted GPU implementation needs it. Files can be streamed
without pickle but this primitive does not itself authorize continuation, enforce
research lease ownership, reconstruct publication after interruption, or permit
restarting terminal jobs. Those remain the registered representation owner's
responsibility. No pilot-bound file, active process, empirical input, gate or
ledger was read or modified by this review; only source, synthetic temporary
fixtures and this append-only review record were used.

Independent pilot01 failure/successor02 review (September24; no execution): parent
eth-paper-resource-pilot-20260924 is durably terminal failed at source
e446e1f948a8e0116bc08c212e5c0bed29ae72f1. Its registered109 identities are present
exactly once in both the run ledger and observer ledger:9 decode_graph failures
and100 unavailable cells. Every failed traceback stops at file_hash(path) with
AttributeError: 'str' object has no attribute 'open', before decode_eth is reached.
Each phase directory contains only intent/result/log files, with no decoded graph.
Input metadata/configuration and declared exploratory windows were still inspected
and reserved; the failed attempt remains consumed and never becomes a fresh sample.

Terminal output hashes, all observer-bound guard hashes and every retained
postmortem-index artifact hash/size match. Guard child exit1, verified cleanup,
zero OOM/OOM-kill and absent recorded cgroup corroborate implementation failure,
not a resource-capacity result. Final guard SHA256
c7b2bcb087ed73eb20d56acbc2fa031ec206b06528a854e3836f1eb712d111d2;
failed terminal SHA256
da08129d8e983047829180efec3fb01e6fb8c9fee6af316d9f83a450c6bd18d8;
observer ledger SHA256
928382a899504d2ed742f0ebf322925eb89cd0deacd93ed7df8b603b37cd7c7b.
All parent registered source files still match their bound hashes and committed
source; original phase.py, gate-v3 and charter bytes remain unchanged.

Successor02 gate-v3 SHA256
33ca7e3a000eaa5d2586967c5c1379c17962935c9b5082258f3c64377391f66d
has26 matching source bindings and88 matching input bindings plus matching charter.
It binds the exact parent claim/failure and includes the unchanged parent experiment
object required by admission. Its source index, resource contract and109-cell list
match the parent's; launch/monitor/run/reconcile consistently use the new
eth-paper-resource-pilot-20260924-02 and pilot-02 namespaces. The only runtime
behavior correction, apart from successor paths/identities, is Path(path) before
hashing serialized binding strings. The retained2-case synthetic report reproduces
the original error on synthetic bytes and exercises successor main's serialized
binding route through a synthetic Parquet graph plus drift refusal; SHA256
4b03a312b66f8fc06bba69c33feed81e2487e3d0e52c6645b86a26f193c74b23.
The guard assertion is mocked in that fixture; actual guard evidence remains the
previously reviewed unchanged cap-v4 probe. No empirical successor execution was
performed during this review.

The prospective allocation amendment is accepted within the unchanged51 cumulative
claim ceiling:17 source claims (1 metadata+14 missing-body batches+2 price batches),
2 resource pilots,1 initial ETH experiment and14 remaining asset folds give34 new
allowances plus17 preserved claims. Combining only still-unclaimed BTC2016/2017
body acquisition into one future finite registration preserves all15 missing
asset-years;13 other body batches are explicitly enumerated. It does not remove
any of the88,776 required field/date cells or change1420 fits. That two-year body
capture still needs its own finite request/storage/resource registration; this
allocation is not acquisition admission. Exactly two new family claims currently
exist, so19 total are consumed before the successor and20 would be consumed upon
its claim. Family budget/history objects remain exactly equal.

No remaining bounded precommit blocker was found for one resource-only successor02
launch. Approval is conditional on committing the exact reviewed source/gate and
amendment, successful normal admission/parent checks, absence of a successor owner/
claim and live cap/reserve/disk checks. Closed pilot01 must never be relaunched.
This review does not authorize financial fits, extra fit identities, silent source
scope reduction, paid resources, provider contact or a further unregistered retry.

Feature-journal/resume independent review (September24; corrections pending):
three material integration findings were reproduced using only tiny synthetic
journal payloads. No empirical continuation or successor pilot was executed.

- P1, feature_journal.py:59,62–74: max_array_bytes is reset for each event and
  recursive parent read. Two completed graph records with4,000-byte arrays each
  are both returned under a5,000-byte limit. Retained workflow arrays therefore
  exceed the supplied bound; completed graphs also keep superseded progress.
  Preflight and enforce a shared retained-state budget across events/ancestors,
  select only latest useful progress, discard progress superseded by completion,
  and keep only the final alignment basis required for continuation. Adjust the
  pipeline's completed-prefix iteration consistently. JSON/scalar metadata and
  sample/dictionary list-to-array reconstruction remain additional memory costs;
  the outer guard remains required and the bound's meaning must be explicit.
- P2, feature_journal.py:16–20,59–60: failed-parent recovery mishandles two valid
  failure boundaries. A parent sealed before its first checkpoint has identity
  None; a successor accepts that parent during construction but later fails
  readback when it acquires its first workflow identity. A failed parent that
  already contains representation_complete can be read itself, but a successor
  that only republishes the identical completed binding fails because
  prior_binding is not None. Define and validate empty-parent inheritance and
  publication-only recovery of already completed numerical work. Preserve failed
  lifecycle status, prohibit refitting, and keep admission external.
- P2, feature_journal.py:38–44,74–80: completion checks do not validate the final
  context binding_hash and accept an empty feature_hashes mapping with no graph
  records. A validly written/sealed synthetic journal with an intentionally
  mismatched binding_hash was returned as complete. Verify cache_key(payload)
  against the recorded binding hash and require a nonempty, exact expected graph
  closure with required schema/lineage. Do not treat a supplied empty subset as
  proof of completion; the registered producer must independently bind its
  expected graph membership.

These findings concern reconstruction/closure contracts, not observed financial
results. Existing externally hashed component bytes still protect against simple
file corruption, and the original publication-order causal alignment correction
is retained. No empirical recovery authorization follows from these helper APIs.

Feature-journal correction re-review (September24): the original retained-state
counterexample now raises the shared array-budget error, completed progress is
removed, and only the latest completed static alignment basis is kept. Independent
GIN orchestration confirms that a failed but numerically complete parent can
produce a one-event publication-only successor with an identical final binding.
Mandatory nonempty required graph membership, final binding hash, schema, exact
required feature hashes and graph/dictionary/alignment lineage checks address the
previous false-completion finding. The retained feature-recovery-synthetic-03.xml
has18 passes and no failures/errors/skips; SHA256
82c1810ea181cd275e87e1b35d835f153e12d29f8587b03df3f53a3643653a48.

One remaining P2 recovery boundary was independently reproduced:
feature_journal.py:43,83–87 initializes every new journal identity to None even
when its pinned failed parent already has a workflow identity. If that successor
is itself sealed failed before its first event, readback inherits the parent's
numerical state then rejects parent identity versus child None. Initialize or
explicitly inherit the parent's identity for zero-event successors, retaining
None only for entirely empty ancestry. Add a two-interruption regression so the
second failed journal remains readable and preserves its ancestor work without
recomputation. This blocks complete recovery-contract closure, not the already
active separate resource pilot. Array budgeting remains a retained-payload bound;
JSON metadata and transient allocations still require the outer resource guard.

External metadata backup03 independent verification (September24; no new network
request): all411 recovered files under the registered temporary recovery root
match both the pinned contract hashes/sizes and the retained local original bytes.
The verified total is13,451,854 bytes, within20MiB overall and4MiB per member.
Every individual receipt records HTTP200 from the exact public
raw.githubusercontent.com/malecada/TradingAgents/e446e1f948a8e0116bc08c212e5c0bed29ae72f1
member path. The411 unique receipts equal the completion results; the recovery
intent binds the contract hash and the output result equals the retained complete
receipt. Static downloader review confirms direct bounded GETs, no redirects,
exclusive destinations, per-member hash/size checks, four workers and no retries;
it does not use a local-copy fallback or Git promisor archive fetch.

Contract SHA256:
26bd35135a94ea800c7577097649df47f8c386b8c3b7f1a3c89a44f18c4a8dd2;
completion SHA256:
28158fcd263681a899e5d073795e5927e9b08ead6e7120bcc1ad39914b942066;
guard final/live SHA256:
1a6d5f775ffcfe8b22340c21950f95f89d8978a28038ba572505dbf00dd3fd35.
Guard release, child exit0, final/live bytes, verified cleanup and absent recorded
cgroup agree; no OOM/OOM-kill or limit reason was recorded. Elapsed time is45.147s
and sampled peak memory49,172,480 bytes. This establishes retrieved external
recoverability for the finite metadata/compact-receipt set only. No transaction
body, empirical model, full historical raw store or full C16 scope is certified.
Earlier failed recovery attempts remain separate; this success does not overwrite
or reclassify them. The active pilot was not inspected, controlled or modified.

Final zero-event journal correction verification (September24): independent
synthetic reconstruction now reads a twice-interrupted ancestry correctly for
both an entirely empty parent and a parent with completed numerical state. The
successor inherits the pinned parent's workflow identity before its first event,
so no ancestor state is lost or recomputed. The retained2-case
feature-recovery-synthetic-04.xml is passing; SHA256
219fbaba76395a0037a428e7351e3268bbba99aa9569a71157e6af3072187285.
The remaining journal finding is closed. This closes the bounded software review,
not empirical continuation admission.

Prospective price-source release review (September24; corrections required):
gate-v1 SHA256
13eb5e346907d957f96cb0fe511a66d366b0da34b0d8571ecb897ccc93198570
matches the reviewed draft. Both assets have matching13 source-file bindings,
8 inputs, lifecycle runtime hashes and charter. The query timestamps independently
resolve to2016-01-01 through2025-01-01 exclusive at interval1d, and each asset has
exactly3,289 unique cells:1 capture plus3,288 daily dispositions. Missing/null
prices remain unavailable rather than filled. Separate asset-specific owner/
monitor/guard/claim namespaces, parent-death behavior, postmortem denominator and
no-retry capture intent follow the previously reviewed supervision design. The
512MiB cap plus3GiB reserve gives3.5GiB startup headroom. No price claim exists.
The retained7-case price/parser/supervisor XML has no failures/errors; SHA256
8b31cbe1e5b53e1f6e2fb24eae4e83110bef2811166b1f229ffa22453da48eaf.

Three material corrections are required before source release:

- P1, prices-01/gate-v1.json families.paper.history_reference: appended allocation
  text changes the family object relative to the consumed metadata/pilot claims.
  admission.py:215–217 requires exact equality and will reject both assets before
  claim. Preserve the exact established family object; keep the allocation detail
  in separately bound inputs/charter. No budget or sample-history reset is needed.
- P1, prices.py:20–26: dataGranularity is not validated. A synthetic Yahoo result
  explicitly marked1wk, with a UTC-midnight timestamp and positive Close, is
  accepted as a daily bar. Weekly Close at a period-start timestamp would be
  assigned the wrong daily clock and label meaning. Require declared1d granularity
  before admitting daily values, retaining mismatched/missing schema as unavailable
  under the chosen explicit policy. Add the adversarial weekly-bar fixture.
- P2, prices.py:14–16: hashing the path and later reading it separately does not
  bind the bytes actually parsed. Independent synthetic replacement between those
  operations returns a999 Close while the panel retains the original100-body
  source hash. Read once, verify that exact byte buffer and parse the same buffer;
  retain immutable/hash-bound source publication. Add a parsed-byte drift fixture.

The review confirms the two price allowances already exist in the unchanged51
claim/1420-fit plan; their correctness does not cure the exact-family mismatch.
Prepare a preserved prospective registration revision with corrected source hashes
and worker/observer gate references. Financial execution remains unadmitted and
historical publication time remains an explicit retrospective-source assumption.
No actual Yahoo request, empirical capture, fit, active-pilot modification or
commit was performed by this reviewer.

Price-source v2 release re-review (September24): all three prior findings are
resolved. Gate-v2 SHA256
14a0bd784aa0a9086a9071739f650d7a1187e3d6f3ac640a0cbfb8ed70f08302
retains the exact established family object, matching the consumed metadata claim;
all source/input/runtime/charter bindings match, worker and observer select v2,
and the original v1 bytes remain preserved. Independent synthetic reconstruction
confirms an explicitly weekly response is refused and a100→999 file replacement
after the first read leaves parsing bound to the original100 response buffer.
Each asset retains3,289 distinct cells and no price claim exists. The13-case
synthetic-02.xml has no failures/errors/skips; SHA256
9025f30b37fcb4f743e95ec09384b6a14995083950582d91b73bf0b42ef3954b.

No remaining bounded precommit blocker was found for these two sequential,
source-only price captures. Conditions remain exact committed reviewed source/
gate, ordinary cumulative-family admission, exclusive asset identity and live
resource/startup checks. The active pilot's source/HEAD constraints still apply.
This approval does not admit predictive fitting or reinterpret retrospective
publication assumptions as verified historical availability. No actual source
request was performed by the reviewer.

Selected-column Parquet software review (September24; corrections pending): the
planner retains every selected physical leaf in every row group, includes
header/footer framing spans, splits bounded contiguous ranges and binds the
recomputed plan to the decoded projected manifest. An independent synthetic
fixture successfully decodes all2 rows across2 row groups using selected nested
BTC leaves while unused script pages remain unavailable. The retained2-case
selected-columns-synthetic-01.xml has no failure/error/skip; SHA256
f2093589476a53a8d0cc38f2a9b46455ee322a83c59136181398d01b2076e282.

Two P2 source-qualification gaps were independently reproduced:

- parquet_ranges.py:80–87 supplies pre-parsed metadata to ParquetFile without
  checking the acquired first four bytes. Replacing the source header with FAIL
  while retaining valid footer/data pages and updated synthetic range hashes
  still yields both rows. Verify the actual acquired header equals PAR1 before
  treating the source as an admitted Parquet object.
- parquet_ranges.py:43–51 ignores ColumnChunk.file_path. Synthetic footer metadata
  declaring external-object.parquet for its chunks still produces a current-file
  byte plan and successfully reads current-file rows. Reject nonempty external
  chunk locations unless a separate explicit source mapping admits and binds the
  referenced object; silently interpreting external offsets in the current file
  weakens source identity and completeness.

The proposed fixes belong to the new unadmitted range planner/decoder, not an
active pilot-bound adapter. No real BTC object, transaction page, network capture,
model fit or active-pilot source was read/changed. Exact projected storage and
full-history feasibility remain unmeasured; this pure helper does not admit the
source acquisition or replace the registered field/date denominator.


Selected-column Parquet correction closure (September 24): the planner now
rejects selected nonempty ColumnChunk.file_path and the decoder checks the
actual acquired four-byte PAR1 header before trusting supplied metadata. The
four targeted synthetic cases independently pass, including both prior
counterexamples. Retained selected-columns-synthetic-02.xml has four passes,
no failures/errors/skips; SHA256
 dcd07c6800ee296718f7de32e5aaf4fb79673a96d91f298aed78fae4b593f8e8.
No remaining bounded blocker was found in these two corrections. This remains
pure adapter verification, without real BTC decoding or acquisition admission.

Registered feature producer review (September 24; corrections pending): the
exclusive descriptor directory, active-run/source checks, exact registered
plan membership, failed-parent requirement, completed numerical reuse and
ancestry closure were inspected. Both retained lifecycle tests independently
pass. A separate synthetic three-attempt reconstruction confirms that trying
to resume the first failed ancestor after a second failed successor is refused
with the explicit omitted-prior-attempt error. Retained
registered-features-synthetic-01.xml has two passes and SHA256
480f80e3f1dbc83a8c75ca5a4f2f60a8a38497cae4ae7cfda02a58640fe585af.

Two material integration corrections remain:

- P2, registered_features.py:47–48: graph output verification reads the parsed
  buffer and hashes a separate later read. An independent synthetic replacement
  reproduces acceptance of an unregistered graph-hash buffer while the second
  read matches a different published buffer. Hash the exact raw buffer passed
  to json.loads against the run's published output hash. This is an actual
  provenance check bypass, not merely a missing durability guarantee.
- P2, registered_features.py:23–24 and feature_pipeline.py:50–51: scientific arm
  enters representation identity directly. Consequently proposed,
  mcm_without_gat and training_label_permutation can own separate equivalent
  dictionary/MCM producers, contrary to the frozen exact-reuse requirement.
  Canonicalize their common representation identity and provide bound read-only
  same-run reuse; retain the predictive arm in its separate fit identity. The
  producer author independently identified this same integration requirement.

The bounded targeted run passed all six Parquet/registry tests. Pytest emitted
six cleanup warnings for pre-existing temporary garbage directories; these do
not concern assertions in the selected tests. No production source was edited,
no actual empirical input was decoded, and no network request, fit, commit,
active-pilot process control or research ledger change was performed. The
outer guarded producer runner and post-death reconciliation remain explicitly
unimplemented release conditions. This review does not approve financial
execution or establish empirical coverage, agreement or recovery.


Registered representation correction closure and comparison review (September
24): graph output references now validate digest(raw) on the exact parsed
buffer. All three motif-sharing arms use the same descriptor and workflow
identity. A registered, published journal pointer supports exact same-run
read-only reuse; completed journal path, owner and workflow identity are checked.
The four registry tests and two comparison tests independently pass. A separate
synthetic motif checkpoint test passes with sampling, dictionary fitting and
MCM computation replaced by forbidden callbacks during replay for proposed and
both diagnostic arms; dictionary identity and binding remain exact. Both prior
registry findings are closed. Retained registered-features-synthetic-02.xml
contains 20 passes, SHA256
 eae71f4702a3c353a996e075b0835645c85bf151f69c6c6223d770f41b716d29;
registered-features-synthetic-03.xml contains two passes, SHA256
2ccb1a5de6092b986ef87e4c21d89421459908c6b4ca9b82ec231431ee47647e.

Independent enumeration reconstructs 44 printed rows times seven years times
five seeds = 1,540 printed cells, with 1,400 distinct paper fits and 20 additional
diagnostic fits. The 15 execution batches allocate every distinct fit exactly
once, including the initial 45 ETH-2024 fits and the other 100 ETH-2024 fits.
Generated fit-allocation-v1.json and table-status-pre-fit-v1.json exactly match
recomputation; all pre-fit dispositions remain pending. An independent nonlinear
annual-value fixture gives the expected equally weighted year/seed mean 51.6.
Shared proposed rows reuse identical fit identities; one missing member prevents
the entire affected printed row's aggregate. metrics_verified=false and
numerical_agreement=null correctly preserve the arithmetic-only scope.

One P2 reporting correction remains in comparison.py:31,36–40,57–60. The function
accepts each exact failed/unavailable reason but returns only aggregate counts,
IDs and the ledger hash, so the per-cell dispositions and reasons cannot be
recovered from its report. A synthetic exact missing-source reason disappears
from the output. Retain the reconciled full ledger or a hash-bound retrievable
ledger reference, and expose exact remaining requirements for incomplete rows.
This does not invalidate the denominator or arithmetic checks, but the current
report is insufficient as a standalone failure/coverage account.

No empirical graph, price, model outcome or active-pilot input was inspected or
changed. No new financial registration, claim, execution or release is approved;
guarded producer execution, post-death reconciliation and independently verified
prediction evidence remain separate requirements.

Comparison reporting correction closure (September 24): the returned report now
retains a deep copy of all reconciled cell dispositions, including exact reasons,
attempts and supplied metrics. Independent reconstruction confirms the retained
ledger hash matches these bytes semantically and later mutation of the caller's
nested attempts does not change the report. The preserved pre-fit v1 remains;
new table-status-pre-fit-v2.json exactly matches recomputation and remains wholly
pending. comparison-synthetic-02.xml records two passes and SHA256
26f3de9d955928d284dcb62f4e713e928af7364967a054d6abd9237e720a5193.
The reporting finding is closed; no additional bounded software blocker was
identified. All prior empirical-release and verification limits remain in force.


Preparation snapshot external recovery review (September 24): all 53 recovered
members, totaling 1,899,175 bytes, were independently compared with Git blobs
from exact commit 35c92e56b143226df07050edaa8665b34d52663f (lazy fetching disabled),
not the subsequently edited working files. Every byte count and SHA256 matches
the contract, recovered file and retained HTTP-200 member receipt. The receipts
use the exact pinned raw.githubusercontent.com/malecada/TradingAgents URLs;
the recovered intent binds the contract and recovered result equals the retained
completion. Contract SHA256
1254d2464e9a5561bec5505260a3e1b02b43e02392ffe439928b31333354bbb4;
completion SHA256
2fc49cb726ea17c73b2efbdf8756c270fb01e6ba26267a4355ee044d2420dbe9.

Guard final/live bytes agree (SHA256
 a43fbe164b380e7ee9e53104f4107d8dc925d441c552dd6a87af7a72cb2180c3):
child exit 0, cleanup verified, cgroup absent, no resource-limit reason or OOM;
256 MiB hard cap, 192 MiB high threshold, zero unit swap, two observed CPUs.
Observed elapsed time is 6.369 seconds and sampled peak is 31,383,552 bytes.
Active HEAD remains c6b568d4b1c177ab94ac37fbad462c2decc721c0.
This verifies recovery of the finite preparation snapshot, not a complete
transaction-store/model backup or full empirical C16. No network request,
fetch, checkout, commit or active-pilot action was performed by this reviewer.

Retained ETH metadata mapping review (September 24): independent reconstruction
confirms all 1,096 dates from 2022-01-01 through 2024-12-31 and all 156 consecutive
complete Monday UTC weeks from 2022-01-03 through 2024-12-23. The weekly population
contains 1,092 dates, seven exact members per week, and the four boundary dates
2022-01-01, 2022-01-02, 2024-12-30 and 2024-12-31 remain explicitly excluded.
Every generated day receipt/map hash and member row denominator agrees with the
preserved fullpanel plan. Every ordinary map's 58,965 spans was checked against
hashed old manifest/projection/request metadata, exact half-open range, object
ETag/If-Match, declared raw/stored hashes, codecs and stored file size. The special
2024-01-01 map's 118 spans were checked against its separately bound prototype,
pilot-context and footer receipts. Only metadata and file stat calls were used;
no transaction blob was read, hashed, decompressed or decoded.

The index records 1,221,389,903 declared source rows and 103,524,489,043 summed
stored-span bytes. These are retained metadata declarations, not newly decoded
row validation or a newly measured unique physical disk footprint. The index
explicitly leaves transaction_data_admitted=false. Index SHA256
2f0f79e37e2beb5beb1baee0e4fb6c5242a10dd4b370e0c87f4413c859383636;
completion SHA256
b62e47e176d0a50a509ffb3f765bba830c58cba76ef09c006045d5e39b8c9f25.
The mapping guard final/live SHA256 is
f0c722397f37f05c6872a282dec51167baa3d76ca069372307acd5da55638359;
child exit 0, cleanup verified, cgroup absent, no OOM or hard-limit reason,
24.503 seconds and 402,653,184 sampled peak bytes. There were 815 memory.high
throttling events, which must not be described as absent resource pressure.
No current numerical completeness, value admission, forecast fit or paper-scope
completion follows from this metadata mapping. No material mapping discrepancy
was found within the inspected metadata scope.


Selected-range capture review (September 24; corrections pending): the new
range_source helper checks an admitted run, exact registered policy and date
cells, complete asset/year catalogues, object keys and ETags before requests.
Finite request/received/compressed-blob limits, conditional half-open range
requests, full selected-column plan checks, planning/footer consistency, exclusive
object directories and immutable normal/denied/one-byte-overflow responses were
inspected. All seven retained synthetic tests independently pass. Successful
byte retention explicitly leaves transaction_data_admitted=false, and missing
objects/dates remain in the denominator. No real request was made.

Two P2 corrections are required before empirical source release:

- range_source.py:84–92 discards partial response bytes on transport exceptions
  and charges no received bytes. An independent two-object fixture throws
  IncompleteRead(partial=b'12345678') twice under a registered nine-byte maximum:
  16 bytes were observed, summary.received_bytes was zero, and no body was
  retained (two error-text receipts only). Preserve bounded exposed partial
  prefixes, and charge a conservative reserved maximum or stop on errors whose
  consumed byte count is unknown. The request counter alone does not enforce the
  promised received-byte limit. The default HTTP reader can fail after partial
  consumption, so this is not limited to an invalid oversized mock transport.
- range_source.py:204–206 creates the objects subdirectory but fsyncs only the
  capture directory's parent. Before the first request, the objects entry in
  the capture directory has not been durably flushed. Independent instrumentation
  confirms this missing parent sync. A power loss during the first object's
  capture can lose its retained evidence subtree before the first daily receipt
  later flushes that directory. Fsync the capture directory after objects.mkdir
  and before releasing any request (or use the reviewed durable_mkdir helper).

No other material issue was identified within this bounded helper review.
Actual source acquisition still requires a committed finite registration and
outer resource/ownership/post-death reconciliation; this helper does not admit
values, canonical-chain completeness, model fitting or full paper coverage.
Only temporary synthetic fixtures and the review appendix were written.


Selected-range capture correction closure (September 24): both findings are
resolved in the reviewed helper. A request reserves maximum+1 charged bytes
before transport; only a normal bounded return refunds its unused reservation.
Exceptions retain a compressed, hashed partial prefix when available and mark
unknown received bytes explicitly. A separate charged-byte counter prevents
reusing unknown transfer capacity. The capture directory is now fsynced after
creating objects/ and before any request. Header fragments below four bytes
are compared against the exact corresponding PAR1 slice.

Independent repetition of the original two-object counterexample now makes
only one request under the nine-byte budget, charges nine bytes, preserves all
eight known prefix bytes with verified stored/raw hashes, retains the complete
date denominator, and confirms the parent directory was synced before transport.
All ten selected tests independently pass, including the unknown-timeout case.
Retained range-capture-synthetic-03.xml has ten passes, no failures/errors/skips,
SHA256 3bef332bfa6d865413f34f7729aa2d5df7aa360fa05377d55a333e51f888c92d.
The earlier nine-case XML02 is preserved with SHA256
0b248766dc70d4490c4b7863c463441fac41060de824621d86e63cf3a9d7e3d8.
No additional bounded helper blocker was found. This remains synthetic software
verification; no source request, transaction decoding, active-pilot mutation or
empirical-release approval occurred. Committed finite registration, guarded
ownership and post-death reconciliation remain required for actual acquisition.


Prepared-component batch execution review (September 24): the exact registered
cell denominator, exclusive batch directory, immutable per-cell dispositions,
registered unavailable evidence, zero-fit controls and continuation of ordinary
independent fit failures were inspected. The initial three synthetic SVM/
isolated-failure/membership tests independently pass. Retained
batch-execution-synthetic-01.xml SHA256 is
0d2f8fa603813600203baab819b00bde40d36bb580204e04f7feef45e75cee81.

The review identified three P2 integration gaps, corrected during review:
(1) run.py originally matched only decision-date masks, allowing conflicting
same-asset/fold labels and target prices across comparator populations;
(2) neither batch nor evaluator matched representation identity to model arm,
allowing WatchYourStep features to reach a Node2Vec fitting path; and
(3) evaluation.py's same-run feature-output route hashed one file read but
parsed a later read. The first two were independently reproduced with synthetic
registered populations and a sentinel before numerical fitting.

Current corrections compare common train/test price inputs, input dates,
decision/label clocks, targets, up labels, fold identity and scaler values while
allowing different graph lineage. Both batch and evaluator enforce the requested
representation/asset (motif_mcm is shared only by the three appropriate arms).
The evaluator hashes and parses one identical same-run output buffer.
Independent repetitions confirm conflicting labels and wrong representation
are refused before fitting. A substituted output buffer now produces a durable
failed cell while the independent synthetic SVM cell continues. The three
findings are closed within this bounded scope.

The executor remains a prepared-component stage, without a connected raw-source
controller, guarded whole-run lifecycle or post-death batch reconciliation.
Failure attempts are retained as attempts, not established successful numerical
fits; controls retain fit_count=0. Independent prediction/metric verification,
real price/calendar checks and actual financial release remain outstanding.
No real financial input, source request, active-pilot mutation or HEAD change
was performed by this reviewer.


Post-death representation journal recovery review (September 24; terminal-proof
correction pending): the helper targets an exact owned representation directory,
requires run-specific guard and launch-owner evidence, current boot, verified
cleanup and an absent/empty owned cgroup, and validates the durable contiguous
event prefix before publishing a terminal. Unpublished component bytes remain
untouched, and neither computation nor successor admission occurs. Five initial
targeted tests independently pass. These are synthetic proof fixtures, not an
actual generic-controller crash or financial continuation test.

Two P2 findings were independently reproduced. First, a synthetic observer crash
after recovery-candidate publication left a permanent FileExistsError on the
next closure attempt. This has been addressed in the current source by exact-byte
idempotent candidate/evidence publication, with mismatched retained bytes refused;
new author regressions cover interruption after either file's publication.
Second, journal_recovery.py:_death originally verified the hash of failed.json
but ignored its actual lifecycle fields. Replacing it in a synthetic proof with
status=complete, experiment_id=unrelated and a wrong claim_sha256 still authorized
journal closure. Require status=failed, the exact owner experiment_id and the
hash linkage to the already verified claim before any candidate publication.
The existing synthetic fixture's reason-only failed record must also be replaced
with the actual lifecycle schema. No guard/process action, active-pilot change,
empirical source access or model computation was performed by this reviewer.


Post-death journal correction closure (September 24): both findings are closed.
The actual failed lifecycle status, owner experiment_id and exact claim_sha256
are now required before candidate publication. Independent repetition refuses
the unrelated complete-status terminal before writing any candidate. Independent
repetition of observer interruption after candidate validation now completes
closure while retaining identical candidate bytes and untouched unpublished
component bytes. All ten targeted journal tests independently pass, including
individual status/owner/claim mismatch and both observer interruption positions.
Retained journal-postdeath-synthetic-03.xml has ten passes, no failures/errors/
skips; SHA256 ae8160e5525d2ea9bd822f9b413865255d2899303e6ccf82e1eb25e5dcb648e0.

The updated batch/evaluation retained XML02 was also inspected: 15 passes, no
failures/errors/skips, SHA256
60f15e7d92f3cd2aedb5a8eac69c84c499b0e8deca8a23bbfdb59b6b65fd48d7.
That evidence includes synthetic full-architecture integration; it does not
establish empirical C13, whole-history scope or agreement with published values.
No additional material blocker was identified in these bounded helpers.
Connecting and verifying the generic guarded controller, batch observer and
actual registration/admission remain separate release requirements.


Generic job controller and prepared-payload review (September 24; pure-preflight
ordering correction pending): launch/monitor/worker ownership, conditional guard
policy, registered source/range payload dispatch, dynamic same-run representation
bindings, independent price-cell continuation on representation capacity failure,
and complete post-death cell denominator retention were inspected. The initial
nine supervisor/payload cases independently pass. The observer correctly emits
proof for unsealed journals without loading their numeric components; actual
journal validation remains a separately guarded operation. Incomplete fit bytes
are preserved rather than recomputed.

Four P2 findings were identified and corrected during review: incomplete source
dependency binding; external reconciliation able to stop a still-live monitor's
owned group; successful final guard receipt accepted from another owner/command;
and lifecycle terminal existence trusted without owner/claim/denominator linkage.
Independent synthetic probes reproduced acceptance of a foreign successful guard,
a simulated stop while the monitor remained alive, and both completed and failed
terminal files carrying unrelated experiment and claim fields. No real process
was stopped. Current source binds the complete local replication package and
lifecycle entry files, verifies import root, checks PID/start ticks before any
external action, validates final/live ownership, and checks lifecycle status,
owner/claim/source/registration/output hashes and complete-cell denominator.
Complete observer status now separates all_cells_complete from
financial_completion=false. Updated supervisor cases independently pass.

One material P2 ordering gap remains: job_payload.py:execute_fit_payload starts
representation production before execute_batch validates the comparator
populations and semantic job references. A fully registered synthetic payload
with real tiny graph manifests and conflicting same-date labels reaches
prepare_registered_features before rejection; a sentinel stopped it before any
representation computation. Move pure population/cell/model/descriptor/output
preflight ahead of all representation loading/fitting/reuse, deferring only checks
of not-yet-produced binding bytes. An invalid comparison should not consume
representation work before its frozen labels/splits are checked.

The generic payload currently supports representation continuation but has no
per-fit continuation or completed-fit prediction-recovery route in its batch
item schema. Existing lower-level recovery APIs do not make this connected yet;
this remains an explicit implementation requirement, not permission to rerun a
closed fit. A new isolated synthetic guarded-controller probe is appropriate
only after the preflight issue is closed. No empirical generic-job registration
or launch has been approved, and no market capture, financial data read, active
pilot mutation, source commit or HEAD change was performed by this reviewer.


Generic payload preflight and fit-recovery closure (September 24): the remaining
ordering finding is closed in the current source. run.preflight_batch now runs
before representation loading, production or reuse; it verifies actual ordered
unique training/test decisions, exact membership hashes, common comparator
labels/prices/splits/scaler/mask, scientific cell semantics, registered outputs
and recovery inputs. job_payload additionally checks every consumer descriptor,
producer population training/fold/required-graph identity, registered producer
outputs and unused representation jobs before loading any graph arrays. The
original conflicting-label sentinel was independently repeated and refused
before graph loading or producer entry. Five targeted payload cases independently
pass. Only actual not-yet-produced feature bytes are deferred to batch execution.

The per-fit continuation and completed-fit prediction-only routes are now wired
through explicitly registered checkpoint/provenance inputs; prediction recovery
also requires the registered completion input and a new parent run. Independent
execution of test_batch_prediction_recovery_uses_completed_parent_fit_without_refitting
passes: recovered predictions equal the completed parent's predictions, a
sentinel forbids creating a new fit reservation, and exactly one fit claim
remains. Existing lower-level interrupted-training evidence covers exact numeric
continuation; this bounded check did not repeat every interruption mode through
the generic controller.

Retained job-payload-synthetic-03.xml contains 15 passes with no errors/failures
(SHA256 d2fe97aedc9e748fb1aca9aec85151d8db40492877cc81fdf7d0bea53b81a7f0).
The preceding XML02 collection error remains preserved (SHA256
0c9f3679bd66315fb648e0de607886f79117099127802aa8ec04b90b504df9fd);
it is not counted as a passing run or empirical exposure.

No remaining material blocker was identified for one separately identified,
isolated temporary-repository synthetic end-to-end guarded controller probe,
subject to exact source/runtime/input admission and the existing resource limits.
That probe must establish the actual child/monitor/observer terminal and cleanup
evidence before claiming controller integration success. This conditional
software disposition does not release source capture, market-data fitting,
financial recovery, empirical C13, full paper coverage or numerical agreement.
No network request, empirical body read, active-pilot input mutation, HEAD change
or process control was performed by the reviewer.


Repeated-observer integrity review (September 24; further correction required):
the current patch revalidates retained lifecycle terminal SHA, owner claim, output
bytes and contradictory terminal, and moves preexisting failed-terminal validation
ahead of postmortem publication. Two independent synthetic counterexamples still
pass through job.py:238–256: after successful reconciliation, changing the retained
final guard child_exit_code from zero to one returns the unchanged complete
observer; after failed reconciliation, replacing postmortem-cells.json with an
empty list returns the unchanged failed observer and its stale cell_ledger_sha256.
Bind and verify the retained guard/denominator evidence on repeated reconciliation,
including the live/final or observer-death receipts and unsealed-journal list used
by that disposition. This is a P2 evidence-integrity blocker for copying the final
synthetic-probe controller source. The probes used only temporary synthetic
repositories and fake nonexistent cgroup paths; no process was controlled.


Repeated-observer integrity correction closure (September 24): job.py SHA256
ced2f9d3505d41ab7f5af354669d2a279be3780134b38f1757c2c3fc2ef0fe5a
now records and revalidates the exact present evidence map for launch, live/final
guard, observer-death, postmortem cell ledger and unsealed-journal list. Independent
repetition refuses both prior counterexamples (modified final exit code and
emptied cell ledger), plus removal of the journal-list receipt and addition of a
previously absent final guard receipt. All four targeted adversarial tests also
independently pass. Retained job-supervisor-synthetic-05.xml contains 24 passes,
no errors/failures/skips; SHA256
4997521d618e60d2b722dc0be21f1448cc0e64aae7ced40fd77b891af6d47c9c.
The identified blocker is closed for this exact controller source. The conditional
disposition for one isolated, newly identified synthetic guarded controller probe
is restored; the superseded unlaunched preparation is not an executed attempt.
Actual guard/process/terminal receipts remain subject to independent inspection
after the probe. No empirical release or active-pilot mutation is authorized by
this software review.


Dependency-closure addendum before any probe launch: the author identified the
additional dynamic research/verify.py path during isolated source-copy preflight.
The conservative source set now includes every parent research/*.py file, matching
the lifecycle runtime-hash set as well as the full replication package and root
initializer. Independent inspection of the change and targeted dependency test
pass. The current reviewed job.py SHA256 is
7c91e29a1d817b41af20747a68413a2a80e7cf231dfeed703856637e63c0092d;
this supersedes the immediately preceding source hash without changing the
conditional one-probe scope. Retained supervisor XML06 has 24 passes and no
errors/failures/skips, SHA256
f14f3a93811a767d7157912a29b54a55fea3afeb79cfa0f23ad9f4084e1a1917.


Independent isolated guarded probe02 audit (September 24): retained temporary
repository /tmp/onchain-paper-generic-job-synthetic-20260924-02, experiment
controller-synthetic-20260924-02, source
6b778c75e861403edf44c356f33429ed76456bfc. Exact raw ledger inspection corrects
the initial author interpretation: only the SVM regression count cell completed.
The proposed direction sum cell is unavailable because representation production
failed with ValueError: insufficient unique centers; the deliberately blocked
cell is also unavailable. All three cells and both distinct reasons are retained.
The representation has failed/attempt-failed records with numerical_complete=false,
and no neural fit claim/checkpoint exists. Therefore this probe establishes
containment and independent-cell continuation, not full guarded motif execution.
The initial claim of neural completion was immediately reported and withdrawn.

Independent hashing verifies 59 admitted source files, 23 input artifacts, all
five output files, owner/launch/live/final linkage, exact claim and lifecycle
terminal linkage, and the source HEAD. Guard terminal SHA256
55dbcfc8a580964a66e5d2b7961298cdfd2cb3acca30fc7e4a67f349a41757ff
records child exit zero, cleanup verified, no limit reason or memory events,
36.69961 seconds, 378937344 bytes sampled peak, 1.5 GiB hard/1.25 GiB high,
zero swap and two-CPU affinity. The owned cgroup and recorded supervisor, monitor
and workload PIDs are absent. Cleanup stop returncode five is retained alongside
inactive/dead unit evidence. Observer SHA256
0a5b760cb8de582ec9040cd7e6e52b3bd799544259dc5f046a6cc42716772e9a
correctly has all_cells_complete=false and financial_completion=false. Lifecycle
terminal SHA256 is
3d524125e4e88d819a835290d7376fd793445efaf3539e80d123c26a16583c9d;
claim SHA256 is f176baf83d7ecf671eab53126a1b003cc0eba298196aa05bde020d3c0c254519.

The sole retained model.joblib SHA256
28f01e45707723cd522ec50a760183695c2173210879e7b6e9ed85a35a8d59e3
matches prediction/cell/fit completion bindings. Independent scalar recomputation
from four saved synthetic regression rows reproduces MAE 0.8453929716747979,
MSE 0.7160077297638942, RMSE 0.84617239955218 and MAPE percent
0.7132448683850259 within 1e-12, with valid row clock inequalities. Model inference
was not rerun. No classification metrics can be verified because that cell did
not produce predictions. The 32-sample/32-motif fixture configuration is synthetic
and does not alter production 512-sample requirements, establish empirical C13,
or admit any market source or financial fit.


Prospective synthetic probe03 fixture review (September 24; not executed by
reviewer): prepared source c9f03c003f899ce752a6aad292e323e8fb9592f5,
registration SHA256
a46763bb1f824807da14e487e12c965a6e21151f2c836cf8d31a02298ec93df0,
under /tmp/onchain-paper-generic-job-synthetic-20260924-03. All 59 copied source
hashes equal probe02 exactly. Batch plan and population bytes are unchanged.
The declared dictionary population now retains all 117 deterministic fixture
graphs; independent metadata/array-member hash checking identifies 103 eligible
training snapshots and 206 unique (snapshot, node) centers, sufficient for the
unchanged sample_count=32 and dictionary size=32. The exact 15 required graph
hashes remain unchanged and are included in the declared graph population.
Training remains one epoch, batch size two, seed eleven and fixed configuration.
The implementation still filters dictionary samples by the frozen training
interval; enlarging this explicit synthetic population does not admit test
graphs to dictionary fitting. No launch directory or lifecycle claim exists.

This concrete fixture correction is appropriate for one separately identified
probe03 under the same resource ceilings, after the other synthetic guarded
suite ends and live reserve/admission checks pass. Probe02 must remain terminal
and unchanged. This is ordinary synthetic verification, with no empirical
family-budget use or implication for production 512-sample capacity. Success
requires actual proposed-model completion evidence; a clean guard alone remains
insufficient. No probe was launched, fitted or replayed by the reviewer.


Legacy price-controller release re-review (September 24): sharing research_runs
and research_artifacts through fixed worktree symlinks is compatible with the
current lifecycle paths: the lock is the same physical .lock file, claims remain
visible centrally, and verify_claim resolves the physical ledger root with shared
Git objects. Actual prepared-worktree/runtime/admission checks would still be
required. However, the pinned prices-01/reconcile.py retains the P2 observer
integrity flaws corrected in the generic controller. An independent temporary
synthetic fixture supplies a foreign-owner successful final guard plus a
complete.json containing status=failed and an unrelated experiment; lines 44–48
still publish complete. Replacing both files with empty objects then returns
the same complete result through line 28 without revalidation. Therefore the
legacy price-controller release remains blocked despite the earlier source
review. No process or HTTP request was made. The parent accepted the finding and
will preserve v1/v2 bytes while proposing price dispatch through the reviewed
generic controller under a new exact source/gate freeze.


Independent guarded synthetic probe03 terminal review (September 24): exact
three-cell ledger now has proposed direction complete, SVM regression complete
and the deliberately blocked cell unavailable without an attempt. All source,
input, lifecycle-output, claim, owner and observer evidence hashes were checked.
Guard terminal SHA256
d1e33ea0b821f556d58c50e3042048eb140351a3db3d5d1ff29031b2fb0d261b
records 143.08513 seconds, 477642752 bytes sampled peak, child zero, verified
cleanup, no limit or memory event. Owned cgroup and supervisor/monitor/workload
PIDs are absent. Observer SHA256
41d1bb80f23962160578be20340ae31577bf6511fe1e750ab98fe207510c5b48
and lifecycle terminal SHA256
6ed0277719f7deac79390f47cad1709b5c19c3ba937954168bf7e489f8b916dd
retain the expected unavailable cell rather than claiming all cells complete.

The completed numerical journal contains samples, dictionary, all fifteen
required MCM/graph completions and representation completion. All 33 event
manifest hashes and 45 referenced numeric-array hashes were independently
checked. Dictionary metadata contains 32 representatives, 32 memberships and
103 training graph identities. Journal completion SHA256
f26b15eab9e471683a2ad8b9e91f8840cb635c2b3a69e3312d9b0aba21562dda
is retained. Neural checkpoint manifest
97ab3a825819aadc4f3aeb8a3b90ff22ea6acfd590f2516321c59e10eab709db
binds state.pt SHA256
27640cbd837208c3406e81d73944e588e84cb21de4c888d6513711630f077a28.
Read-only weights-only inspection confirms epoch one/batch zero, optimizer/RNG
state and twenty finite model tensors covering motif MLP, both GAT layers, LSTM,
query/key/alignment attention and output. No inference or fitting was rerun.

Independent scalar metrics from the four saved rows match the frozen C13
atol=1e-10/rtol=1e-8: regression matches exactly; classification has TP=4, other
confusion counts zero, accuracy/up precision/recall/F1 one, macro/
balanced measures one half, Brier 0.0000512087492969826 and independently
computed log loss 0.007181726727244589. Reported log loss differs by
1.3450053e-10, within that frozen combined tolerance (not within 1e-12). Clock
inequalities and prediction/cell/checkpoint hashes agree. The all-up four-row
fixture supports software plumbing only. This closes the intended guarded
synthetic full-architecture probe; production sample count, empirical C13 model
replay, paper-scope coverage and numerical agreement remain unestablished.
Probe02 remains preserved with its distinct representation failure.


Generic price dispatch and gate-v3 review (September 24; prospective source only):
exact gate SHA256 e1112f5d9330a611f9b738ad4a8537f7787e315aaa130de267a20661bff13bed
was compared with v2. Family objects, datasets, experiment identities, all
3289 cells per asset, windows, outputs, prior eight inputs and capture policies
are unchanged. Changes are the explicit generic-controller charter, two bound
execution inputs (job and workspace) and conservative 59-file source closure.
All current source/input/charter hashes match. Current job.py SHA256 is
dfe7a862a5dc1d4708bb1a5f0a954378a0abfa54a71ae86511c872a4ef1cdea5.
The prices branch calls the unchanged bounded price producer and uses the
reviewed generic owner/terminal/evidence observer. Only an exact supported asset
payload is accepted. Resource caps remain 512 MiB hard, 384 MiB high, zero swap,
two CPUs, 3 GiB host reserve, 3.5 GiB startup, 20 GiB disk and 300 seconds.

The hash-bound workspace mapping checks the exact checkout root, physical
ledger/store and shared Git common directory before launch and worker admission.
Independent targeted tests pass all eleven cases: strict asset schema, one
synthetic HTTP429 response with all 3289 dispositions and indexed retained bytes,
physical symlink mapping, and refusal of each altered root/ledger/store/Git
mapping before job access. No real request was made. The current shared ledger
contains three new family claims, all carrying the exact same family object;
17 historical plus three new is 20/51. Both price identities and source
directories remain unclaimed; sequential launches would reach 22/51, using the
existing two allocations.

No remaining material software or budget-equivalence blocker was identified for
this prospective gate. Conditional release still requires the committed exact
source, actual sparse-worktree/import/runtime/input verification, the same
physical central ledger lock/artifact store, no existing per-asset owner/claim,
and live resource admission. The worktree path must remain available while
absolute capture-manifest references depend on it, or receive a separately
declared relocation mapping. Old gates/controllers and the active pilot checkout
remain unchanged. This disposition admits only the two finite sequential source
captures after those checks; it does not admit prediction fitting or new claims
outside the existing family allocation.


Actual price worktree release-condition closure (September 24, before requests):
independent read-only admission from /tmp/onchain-paper-prices-checkout-20260924-01
confirms HEAD 652b2766cacd0c5f5b2c830bafeaa7315bb42fc2 and gate-v3
e1112f5d9330a611f9b738ad4a8537f7787e315aaa130de267a20661bff13bed.
Both assets are ready with 59 source files, ten exact-hash inputs and 3289 cells.
The job module is imported from that worktree; actual Python 3.13.13 is the
explicit shared pinned interpreter and its inventory exactly matches the bound
environment. This confirms the mapped runtime directly; it does not assert the
checkout-local runtime helper passed.

Physical ledger and artifact paths match workspace-03.json, the .lock inode is
shared with the active main checkout, all three paths use the same filesystem,
and verified prior claims give 20/51 before price capture. Both per-asset claim,
generic owner/guard and source directories are absent. Main HEAD remains
c6b568d4b1c177ab94ac37fbad462c2decc721c0. At this read-only check
MemAvailable was 5242516 KiB and guarded-volume free bytes 30391209984; actual
launch must still enforce fresh live checks. Retained job-prices XML02 contains
38 passes and no failures/errors/skips, SHA256
5c1d50a5ee8afb2914410441cd09313e0fdf659cc0e3c9e859e595d472b62455.

The outstanding source/checkout conditions are satisfied. Release is scoped to
one BTC request followed by one ETH request, each under its own registered
generic guard and existing identity, with complete closure/evidence inspection
between assets and no retry of a claimed identity. The two source allocations
remain within the same 51 ceiling. This review performed no request, claim,
financial fit or process action and grants no predictive-data admission.


Independent Yahoo BTC/ETH terminal audit (September 24; no refetch): both exact
source-652b2766cacd0c5f5b2c830bafeaa7315bb42fc2 captures received HTTP429.
Each retains one 23-byte response, SHA256
0d24c98db98d3b4a87b9626a026e7d72c99754ab6bd88211a17bc372350b7d89,
with distinct request URL/timestamps/receipts and the original error reason.
Independent calendar construction confirms all 3288 dates from 2016-01-01
through 2024-12-31, plus capture: exactly 3289 unavailable cells per asset,
zero admitted prices, null parsed panels, and no missing date omitted. All
3295 indexed files per asset match retained hashes and sizes. Capture manifest
member hashes, response-byte binding, lifecycle claim/output hashes and observer
owner/evidence/terminal bindings agree. BTC closure precedes ETH claim start.

BTC guard SHA256 c45169ac4a8483b6a7952c7f5eb0f2de648126f27f7adb9f9e89deac34a65c4c
records 70.24708 seconds and 84238336 bytes sampled peak; terminal SHA256
1a60689f8bd818e5d0d49f73e7796fc4be4f60aa6a41fc49dbecdbed318c8577,
observer SHA256 f198ca06d07d1b6d0c0e53b643766c3e0efae55709e76b8d87abcd56bce3bd44.
ETH guard SHA256 1ed79e60bc5836aaa16acc4c87408fd78e09b30bab4c493acae6e4f43e22444c
records 104.13779 seconds and 84918272 bytes sampled peak; terminal SHA256
12497fb854fdc2dc878f127f91e160b8c0a68d2e41b32a1cf9b59f0b5e7a96d4,
observer SHA256 1faa46693731b0f603cfcd416f7ebd71e161db3e83f6d01fd884f8a867592ae9.
Both guards have child zero, verified cleanup, no limit reason and zero memory
events. Their cgroups and recorded supervisor/monitor/workload PIDs are absent.
These are completed source attempts with unavailable data, not successful price
coverage. Both claims remain consumed; cumulative use is now 22/51. No request,
market-value reconstruction or fitting was performed during this review.

Any alternative price provider requires an explicit prospective protocol and
cumulative-budget amendment before capture. In particular, current lifecycle
admission requires exact family equality with prior claims; simply changing the
family ceiling from 51 to 53 is not an implemented extension mechanism. Preserve
all old claim bytes, mechanism identity and failed source attempts while using
or implementing a separately reviewed explicit extension path. No alternative
source capture has been approved by this terminal audit.


Prospective Coin Metrics allocation/protocol review (September 24; no CSV
retrieval): the proposed unchanged-ceiling allocation is legitimate prospective
batch regrouping. Arithmetic remains 17 historical + 2 resource pilots +
17 source claims + 15 registered financial batches = 51. Source allocation is
1 metadata + 4 price attempts (two closed Yahoo and two prospective alternatives)
+ 12 body batches. Combining the unclaimed BTC2016–2019 years into one batch
releases two slots; the other five BTC years and six missing ETH years remain,
with all required source cells and 1420 fits preserved. Five consumed new claims
remain visible, so use stays 22/51 before any alternative capture. Exact prior
family identity must remain unchanged in the eventual gate. This does not prove
four-year acquisition feasibility: its later finite manifest must retain every
date/field and explicit request/byte/time/resource bounds without implicit
continuation or retry under the same identity.

The proposed calendar changes only provider, price field, schema version and
explicit retrospective-source qualification; all seven folds, decision/label
clocks, horizon, lookback and graph join are unchanged. Independent metadata-only
inspection confirms that Coin Metrics defines daily PriceUSD at UTC day-end
([provider documentation](https://gitbook-docs.coinmetrics.io/network-data/network-data-overview/market/price)).
The pinned [archive generator](https://raw.githubusercontent.com/coinmetrics/data/f1a36afb962731c387bb03982758ab0103063da5/scripts/generate.js)
selects daily metrics and writes the date component of API time. The proposed
D-to-next-midnight availability is explicitly assumed; historical publication
latency and author-exact price identity are not recovered. The [official archive](https://github.com/coinmetrics/data)
states its CC BY-NC 4.0 license and warns that available assets/metrics may change.
No archive CSV or financial values were retrieved. Actual schema/coverage and
strict parser/gate/resource admission remain pending; this protocol review is
not an alternative-capture release.

Independent preparation recovery02 audit: all 2270 unique required results,
34235495 bytes, were hashed against both retained recovered files and exact Git
blobs at commit 652b2766cacd0c5f5b2c830bafeaa7315bb42fc2, using local
cat-file with lazy fetching disabled. Every retained result has HTTP200, the
exact pinned raw-GitHub URL and matching path/size/hash; no remote request was
repeated. Contract SHA256
70581d676e628b59e962aa1aa792c4f3871cd5e6a0ca10f28a61014082a507ea;
completion SHA256
24b97930427f24686b015ef2c77ca539c2a6fe868bbac8a42de223ad5b045589.
Guard SHA256 e41bdae07b2533afd17efcd5a4720bed0b2dd19510d8035d7a7daffae866b14c
records child zero, cleanup verified, no limit/memory event, 251.72321 seconds,
101588992-byte sampled peak under 256 MiB maximum; cgroup is absent. This proves
external recovery of the enumerated compact source/synthetic/public-metadata
snapshot, not full transaction-body or empirical-model backup.

Implementation coverage-v3 SHA256
584bbcb5d5a29cdd5e48bc4fed312f6ca83354f64e1587ad9c1f451b439aeb3a
was independently checked: frozen-fidelity parent and prior-report hashes agree;
all 34 record dispositions, 728 test references and 37 referenced source files
match the retained evidence. All 101 source/test snapshot members were compared
to commit652b: only job.py and test_job.py differ from the 350-pass/one-CUDA-skip
baseline, exactly as declared, with 38 subsequent passing targeted tests. Baseline
guard records 256.85701 seconds, 631595008-byte sampled peak, child zero, clean
cleanup and no memory event/limit; its cgroup is absent. These are overlapping
evidence sets, not 388 distinct full-suite passes or complete empirical coverage.
The report appropriately retains explicit assumptions, known deviation and
blocked fund-cohort/source items; no frozen fidelity record was changed.


Coin Metrics implementation and prospective source-gate review (September 24):
exact gate SHA256
232d416fdc96acc0f8f9ce9287fdfbf920962e9ddf87b815cc23c54ae5855979
binds sixty current source files and twelve inputs per asset; all source/input/
charter hashes and protocol-freeze-v5 parent/file links independently match.
Family objects equal the prior Yahoo gate exactly; both 3289-cell denominators,
windows, outputs and exploratory reuse remain unchanged. New provider-specific
dataset identities do not reset the shared mechanism budget. Retained inputs
include history, runtime/lockfile and full required source grid.

Reviewed job.py SHA256
ce3aa010033e0de5d1adb22f79a71eb42ad16244e45c409fb0a7d7e0325a0723
and coinmetrics_prices.py SHA256
5e14eae6fafccdfe562ab07c73ac3854f5e86751d74e468807b82be0a3a0a62f
use the reviewed generic owner/guard/observer path. The source policy fixes one
asset-specific pinned URL, one request, 30-second transport timeout, 32 MiB plus
sentinel bound and no redirects/proxy/retry. Exclusive durable intent precedes
transport. Known IncompleteRead partial bytes are retained; interrupted or
invalid sources remain unavailable, never retried by reopening the identity.
The parser hashes the exact byte buffer, rejects invalid UTF8/CSV, duplicate
headers/dates, unsorted or noncanonical dates, excessive rows/columns and invalid
PriceUSD values. It selects only PriceUSD, excludes outside-window rows and
retains missing required dates. Source HTTP completion is distinct from schema
and daily data acceptance. The 512 MiB/384 MiB/zero-swap/two-CPU/300-second
resource contract is unchanged; no parser success implies financial admission.

Seventeen targeted parser/capture synthetic cases independently pass. An
additional independently constructed CSV with conflicting ReferenceRateUSD,
outside-window prices and an absent required date returns only PriceUSD
11 and 13 on the original dates and preserves the gap. Retained synthetic-01.xml
contains 61 passing cases and no errors/failures/skips, SHA256
650cb3ddd29e747743d18e5344f13c2fdf8b47175d922e925465e57ed1765601.
No empirical CSV or provider request was accessed during this code review.

No material implementation/admission blocker was identified for this exact
prospective source gate. Conditional release requires a committed matching
source checkout, actual imported-root/runtime/workspace/shared-lock/input checks,
absent new claim/owner/source identities and fresh guarded resource preflight.
Then one BTC capture followed by one ETH capture is within the reviewed existing
51-claim allocation; each must close and retain its full denominator before the
next starts. This does not approve source-value fitting, scope reduction,
alternate metrics/providers, date blending or retry of either closed Yahoo run.


Interim capacity arithmetic review (September 24): capacity-interim-01.json
SHA256 5214090521b21bbf8e157464cb44c0f30e7c8478ff68b5ff9ea50f2246acd11f
was reconstructed from the exact first two completed decode_graph result bytes,
whose retained hashes and stated counts/sizes/times match. Mean graph size
518547832 bytes times 156 is 80893461792 bytes. Mean 1908681.5 nodes times
32 motifs times four bytes times 156 weeks times five seeds is 190562760960
bytes. Their sum is 271456222752 bytes; multiplying by 1.5 gives
407184334128 bytes (407.184 decimal GB, 379.220 GiB). Both stated filesystem
headroom subtractions above the 20 GiB floor are exact. This is an interim
shape projection from two weeks, not a full-history measurement or safe storage
reservation; simultaneous raw, intermediates, scratch, model, backup and other
fold/arm requirements remain excluded. The excluded 103524489043-byte raw figure
is specifically the retained mapping's summed stored-span bytes, not a proven
unique physical raw-store size. No combined physical-drive headroom or independent
backup should be inferred from the two path measurements.

Retained phase receipts confirm both full-node MCM attempts are unavailable on
neighborhood capacity, and neural phases stop before forward with formula
estimates 10713395200 and 8778956800 bytes exceeding the 1073741824-byte
registered allowance. These establish explicit capacity-check refusals, not
measured neural minimum RAM or successful complete MCM sizes. The largest stress
week remains outside this review. No graph computation, source query, empirical
fit or active process action was performed.

Critical assembly accounting requirement: raw-to-weekly-to-population preparation
can be included prospectively within the existing fifteen financial-batch claims,
but their present allocation alone is not an executable admission for those
phases. Before decoding, freeze the complete source/date/field denominator,
phase input/output bindings, explicit assembly resource bounds and ownership,
common availability mask before any representation/model fitting, and train-only
dictionary lineage. Shared graph reuse must reference an exact immutable owner
and completed artifact; failure must preserve every downstream unavailable cell
and permit only independently valid registered work. A checkpoint does not
authorize reopening a terminal claim. Any interruption requiring a successor
needs a separately registered identity with explicit remaining-budget treatment;
no uncounted assembly claim or implicit retry is available in the fifteen slots.
The current generic fit executor begins from prepared populations, so actual
raw assembly integration remains an explicit unreleased requirement.


Independent actual BTC Coin Metrics source audit (September 24; retained bytes
only): source 3b8e660842c9634f0dadaea3ee81c34571d7772a and exact gate
232d416fdc96acc0f8f9ce9287fdfbf920962e9ddf87b815cc23c54ae5855979
remain bound to all sixty source files and twelve inputs, independently hashed
from the mapped worktree. The single retained HTTP200 body is 2482497 bytes,
SHA256 06495ff8e643432e6948b7b4686ce44fc106217287dabdc1b38351d9ddec46c3.
Independent CSV parsing (without the producer parser) confirms 32 unique columns,
6351 strictly increasing canonical dates from 2009-01-03 through 2026-05-24,
and positive finite nonmissing required PriceUSD values. Exactly all 3288
required dates 2016-01-01 through 2024-12-31 and their unchanged-date PriceUSD
values match the saved panel; the 3063 outside-window rows are excluded. No
ReferenceRate field, date shift, interpolation or gap fill is used. Availability
at next midnight remains the documented provider-clock assumption, not recovered
historical publication evidence; historical_vintage_verified remains false.

All 3289 lifecycle cells are complete, including capture; every one of 3295
indexed artifact files matches size/hash. Intent/receipt/capture members, raw
manifest, panel, lifecycle outputs/claim, owner and observer evidence linkage
independently agree. Claim SHA256
d1bd8f7fa874b2d474521ed76d17c9fb587634ccdc38daf4f6d623b174a8e763;
terminal SHA256
2e34319ed8173e702c54e736efeda94c8c26ccece738026d3016e4903ed926fe;
price-panel SHA256
10ac061629f175d623f5dd22c77000ffc9bf65d2b90154ebe3b24f5ae8ff4679;
observer SHA256
ce11312027f1cd82a0f79f97ae9330b3cb73dd90f88c0822708794d9b9ec22ed.
Guard SHA256
b2267fd0d97c91444a48e62baa595465c083ff181b2b905718678e41079c7dd2
records 83.56230 seconds, 91312128-byte sampled peak, child zero, verified
cleanup, no limit and zero memory events. The owned cgroup and recorded
supervisor/monitor/workload PIDs are absent.

The BTC alternative consumes its separate allocated claim: 23/51 after BTC
closure, with any subsequently claimed ETH attempt additionally consumed even
before terminal. ETH artifacts were not inspected during this BTC-only review.
This verifies BTC price-source coverage and provenance under the declared
substitution, not author-exact source agreement, empirical predictive performance
or financial admission; financial_completion remains false. No refetch, model
fit, graph computation or process action occurred.


Independent actual ETH Coin Metrics terminal audit (September 24): the retained
2121732-byte HTTP200 CSV, SHA256
46b18f3df967405374b1f6ee8a3d11ee1b7a5b176ac9fb4342caf6bf8648f2cc,
was parsed independently of the producer. It has 32 unique columns and 3952
strictly increasing canonical dates from 2015-07-30 through 2026-05-24. All
3288 required dates and positive finite PriceUSD values exactly match the saved
panel; 664 outside-window rows are excluded, with no shifts, filling or alternate
metric use. All 3289 cells complete and 3295 indexed artifacts match sizes/hashes.
Exact sixty-source/twelve-input gate, owner, capture, claim, outputs and observer
chains agree. Claim SHA256
e3706c46725b96c22b0e744705d7b5270e3fc4f0fdd179dcfca373df26a0706e;
terminal SHA256
5f73ee1f0a8028fa11c54e53ba56c9e45c7fe8b08e520fdf68f150355331ffc4;
panel SHA256 f7a4d89ff66d37ec00d8d4d834a1a771ac55f36bc9b210cfbecb6768ecc3bbbe;
observer SHA256
cd3253767a68f2a9d4c9adc6fc9fb9692c3a0498e3fb8b648b859c363a9a97a0.
Guard SHA256
4825c56a01ce5bb6f2432780560a957c4c422aa5341d8953490b5aa2ec44d22c
records child zero, clean cleanup, no limit/memory event, 104.92631 seconds and
90120192-byte sampled peak. Cgroup and recorded process IDs are absent; BTC
terminal precedes ETH claim. All seven new family claims carry the same family
object, giving 17+7=24/51. Historical availability remains assumed and
financial_completion remains false; no refetch or fit occurred in review.

Independent snapshot03 delta recovery audit: both retained HTTP200 download
results match their pinned remote f45ffecafec136db14c8214208690110b82dc216
URLs, contract sizes and hashes. The 926053-byte archive SHA256
03f08e6c9941839ded8902288bbe4d2d5d2208984e71cba1f8fea91bc99c522f
contains exactly 6651 unique regular members and 6964291 uncompressed bytes.
Every entry was hashed against the manifest and compared byte-for-byte to its
local Git blob at 3b8e660842c9634f0dadaea3ee81c34571d7772a; no extraction,
clone, git archive or network request was performed. Local Git comparison with
base652b2766cacd0c5f5b2c830bafeaa7315bb42fc2 has exactly those added/modified
paths and no omitted deletion/rename. Manifest SHA256
df3e0cd3a8416c1d50e99a5ed6dde91a92fbdf6e599e001e15d9af70197160d5;
recovery-completion SHA256
5193fad9b2704c71f3ff04e988dedd63425781bb2bdf946ec51777c3cc0be63a.
Guard SHA256 dcec327e3300b8833b985d084070e32304d54c278054fe2652f7fa3680dd6c98
records child zero, verified cleanup, no memory event/limit, 2.68019 seconds and
26718208-byte sampled peak under 256 MiB; cgroup is absent. This is exact delta
recovery plus the separately verified compact base, not full raw-store backup
or backup of later Coin Metrics outcome artifacts absent from source3b8.

Consolidated interim acceptance review: completion-interim-01.json contains all
C01–C18 exactly once, and every linked evidence path exists. Its met_synthetic
dispositions are supported by component reviews and guarded synthetic evidence;
partial/pending classifications and false implementation/paper-scope/exactness
flags remain appropriate. Numerical agreement remains unevaluated. The document
predates the latest outcomes: update C03 to state both completed Coin Metrics
source coverages and C16 to state verified snapshot03 delta recovery. Neither
change closes the criteria: full transaction/graph populations, empirical saved
model/metric replay, required raw replay recovery, active pilot terminal/resource
review and fund-cohort source scope remain outstanding. The 34 fidelity records,
1420-fit denominator, all 44 table rows and all thirteen tasks must remain in
scope; no accuracy result or source success supplies an exemption. No criteria,
ledger, source or active HEAD was edited by the reviewer.


### Independent consolidated checkpoint review — expanded verification 02

Read-only inspection independently verified implementation-coverage-v4.json
(SHA256 28369afb5d830b38bfd283c09f393ba7e47522a63e4c2188bf5dd6fb3aae6cc6),
its unchanged parent fidelity identity and previous-report hash. All 103 source
snapshot files match current bytes; all 38 distinct mapped code files match the
snapshot; all 812 test references across 34 records match actual XML dispositions.
The full XML has 388 cases: 387 passed, one CUDA skip, zero failures/errors.
XML SHA256 554daa8de7b7354ff157383c4f96e586f107b3c611f93fb9d0493370cff173fc;
source-freeze SHA256 4cb38060147fcc4c35dcb5600925aa5b453a1aa9366a96ca0123ea133ce0b4a4.
The child log records six warnings. This is the expanded replication suite,
not a claim that every legacy repository test was executed.

Guard final SHA256 f5e0352465673c5b74b52d32a2487e2789c1fc1fd9d41ea807c6784d6a82198c
agrees with release, child-exit and CPU-ready receipts: child zero, verified
cleanup, 443.445245687 seconds, 934776832-byte sampled peak, unchanged zero
memory-event counters, no triggered limit, 2.5 GiB maximum/2 GiB high/zero swap.
The recorded cgroup, monitor PID, wrapper PID and workload PID are absent at
independent inspection. The command uses the previously created clean locked
Python environment. The verifier checks exact installed-distribution equality
against its earlier inventory and freezes source bytes before and after testing.
Its network-denying audit hook is explicitly main-process scoped. Replay receipt
SHA256 1a336bceef418b63461df25abb0e4a4574eeeca7d2a88535e9c1fc4cbec8a801
binds that source freeze and the actual saved fixture manifest; two predictions
have recorded maximum absolute difference zero. No test or model was rerun by
this review. This remains synthetic saved-checkpoint evidence, not empirical
C13 or complete raw-to-prediction recovery.

completion-interim-03.json contains C01–C18 exactly once, has no missing evidence
path, and correctly hashes its preceding version. Its implementation-complete
and paper-scope-complete flags remain false, numerical agreement remains
unevaluated, and exact reproduction eligibility remains false. RESULT.md retains
all 44 printed table rows and 1420 pending unique fits, distinguishes source
coverage from fitting, declares the Coin Metrics deviation and retrospective
availability limitation, and qualifies the 407.184 GB figure as a two-week
projection for the current artifact format rather than intrinsic algorithmic
minimum storage. Full-scale MCM/neural capacity is not established by estimates.

The assembly admission document accurately states the remaining prepared-input
integration gap. Its requirements preserve complete cross-year/week source and
BTC spend/chain checks, exclusive transform ownership and exact completed reuse,
pre-fit common populations/masks, all downstream unavailable cells and the
24/51 cumulative accounting. No additional uncounted preparation claim is
implicitly released. Whole-history raw admission, empirical graph reconciliation,
financial fitting, real saved-model/metric replay, full raw off-device recovery,
active pilot terminal review and original fund cohort/vintage remain unverified.

Three stale prose claims were reported: REPRODUCE.md formerly denied any fresh
synthetic reproduction (corrected and independently reread); ACCEPTANCE_CHECKPOINT.md
C14 still described latest expanded synthetic clean-environment evidence as
pending, and C16 still described snapshot03 recovery as pending at inspection.
Those two table rows should match completion-interim-03.json while retaining
empirical raw-to-prediction/full raw backup as outstanding. These are conservative
understatements, not grounds to mark either criterion complete. No source, gate,
ledger, empirical job or active HEAD was changed by this review.


Follow-up: ACCEPTANCE_CHECKPOINT.md C14 and C16 were regenerated from the current
machine-readable matrix and independently reread. Both stale statements are
closed; the consolidated checkpoint is consistent at this reviewed scope.

Bounded preparation-script review identified two preventive fixes before local
snapshot assembly: replay/prepare_checkpoint_04.py checks aggregate archive bytes
after reading a complete Git blob into memory, so the size must be compared with
the remaining 128 MiB allowance before reading; its Git helper and cat-file
subprocess should both receive GIT_NO_LAZY_FETCH=1 to enforce local-only Git
access in this promisor repository. The earlier broad implicit-fetch failure
makes that boundary material. Temporary-index assembly, explicit closed source
claims, allowed path prefixes, exclusive outputs and active-HEAD preservation
otherwise match the described compact checkpoint scope. This review does not
prove a future push or external recovery; those require actual independent
retrieval evidence.
