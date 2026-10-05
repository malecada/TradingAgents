# Selected typed score storage — source preparation only

The candidate implements a registered typed storage route around the original
80-byte `<Qd32s32s` score records and original f64 batch payloads. It changes no
matcher, score order, value, checksum algorithm, motif count, or f64→f32 cast.
The original local route remains selected by default. Eight literal/AST inverses
reconstruct the exact predecessor source bodies; the banked codec and streaming
semantic verifier are copied unchanged. `SOURCE_DELTA01.json` identifies all
13 module bodies and their actual baselines; `integration.patch` is the overlay.

## Functional path

An explicitly selected transport schema2 adds `typed_payload_input`, an actual
registered input consumed by `ResearchRun.read_input`. Its
`typed-payload-budget-v1` policy declares all three kinds (`score-tail-f64`,
`score-batch-f64`, `mcm-output-f32`) for every actual required graph, with original
rows, 32 motifs, chunk cells, finite operation/byte/chunk/control allowances and
floor. No allowance values are selected here. Dispatch preflight restricts this
route to one genuine real-resource representation and charges additional decoded
and conservatively rounded transfer capacity to the existing shared Context.
Selected helper imports occur before imported-authority module attestation.

`typed_payload_operations.operation(owner, stage, kind=..., binding=...,
payload_bytes=..., chunk_count=...)` requires actual Owner/Stage/Ledger/View and
the original held transition. A writer child preserves its active parent claim;
a separate output/read operation requires a genuinely closed MCM stage and idle
ledger. Reservations are retained on failure. Ledger metadata and terminal
journal pins include typed claims, successful parts and completion chains.
`preserve` uses the existing upload/full-fresh-get primitive, then disposes only
its verified snapshot/readback. `recover` uses the existing full fresh consume
and cache-disposal primitive. No new transport or supervisor is introduced.

At each original successful local tail seal, `typed_score_store` preserves finite
parts, freshly recovers and checks every original record/checksum/EOF and f64 bit
against the genuine batch, archives that unchanged batch, and retains anchored
metadata while retiring the corresponding successful local payloads. Transfer
failures retain incomplete evidence and poison the operation. The final stream
schema2 binds a whole-roster semantic recovery proof; the actual archived-stage
scientific result also binds that proof hash. `typed_tail_binding.bind_archived`
consumes the genuine archived marker and original contract, never a synthesized
legacy stage receipt. `batch_reader` provides ordered fresh f64 recovery under a
real held operation, with full scientific entry/exit checks and exhaustive marker
chain verification. Returned batches are provisional until successful exit.

## Material assumption and limits

Closed/post-owner checks authenticate the prior full byte and semantic recovery,
original roster, metadata, stage claims and completion anchors. They do **not**
assert current remote byte availability. Every future byte restore/use requires
fresh retrieval and authentication. This is an explicit new registered storage
assumption, not an unchanged temporal guarantee or current callback-free byte
verification. Source preparation grants no execution authority.

Transport parts remain ≤4MiB. This is not a claim that the real resource worker's
whole-file RLIMIT is 4MiB; its prospective actual bound must cover required
original files, including the unchanged final matrix/memmap. Registered guard
storage includes payloads, all retained transfer/ledger/control metadata and
failure residues. The selected `max_control_bytes` is an additional finite typed
ledger metadata envelope, not an increase/refund of original event capacity.
No runtime performance, physical storage saving, or empirical capacity has been
measured. Existing original guard/source/currentness checks are not waived.

## Checks and integration prerequisites

Five pure offline controls pass (`checks05.out`): original f64 record semantics
with fragmented reads and corruption/EOF/fatal cases; explicit finite policy and
full population refusal; historical part-chain/order/missing-body/binding
corruption; actual changed-source disposal ordering and required capability
predicates. No numerical modules were imported. `source_proof04.out` records
eight exact literal and AST inverses and two unchanged banked helpers. The first
check run's assertion misspelled `op.context` as `self.context`; its script and
failure output are retained, corrected in `checks02.py`. No genuine Owner,
ResearchRun, transport, or native activation was simulated or executed.

Root must combine this overlay with the output agent's `mcm_raw_parts` and exact
publication/output copies, bind all actual source/input roles, select finite
budgets and prospective policy, and obtain changed-seam review before activation.
The copied Owner now additionally joins only the genuine attached archive ledger
at `journal/archive-operations`, preserving the original parent inventory. The
terminal writer roster authenticates actual nonnumerical ImportStage.content,
zero current-pair credit and original dictionary/receipt, then requires exactly
the remaining MCM writers. These changes have focused source-interface and
actual roster-comparison refusal controls and exact default inverses; no Owner
was constructed in tests. An earlier path concern was corrected by direct source
inspection: the ledger is inside journal, not beside journal. No nonexistent
sibling or broad inventory exclusion was authorized. Genuine activation remains
unproved until combined source review, registration and actual finite execution.
