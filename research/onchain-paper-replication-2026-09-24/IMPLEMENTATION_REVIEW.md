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
