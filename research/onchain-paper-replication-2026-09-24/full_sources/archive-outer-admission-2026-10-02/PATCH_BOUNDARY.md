# Outer archive dispatch: next engineering boundary

Read-only assessment against committed `ed87418d`. Accepted archive transport,
producer and retained-checkpoint integration are reusable, but the ordinary fit
assembler does not construct or inject the transport. No source, registration,
scientific output, gate or other worker's module was changed. No test, admission,
SSH command or transfer ran. `OBSERVATIONS.json` pins the inspected committed
sources and existing audits. It is not a complete current source closure.

## Concrete missing connection

`job_payload.execute_fit_payload` preflights compact selection but its nested
`produce` calls `compact_native_producer.produce(run,name,job,graphs,examples)`
without `archive_transport` (line157 at the inspected base). The producer's
lines106–110 explicitly reconstruct the registered archive extension and require
transport presence exactly when that extension is selected. An archive-selected
job therefore refuses before the compact journal/owner claim. The accepted
in-process fixtures supply an injected transport directly; their success does
not cover this outer call or SSH interoperability.

Existing scientific and operational joins should be reused:

- `compact_native_producer.selected`: actual ResearchRun, active lifecycle,
  exact registered fit payload/representation, both-plan policy references,
  required resident route, fresh namespaces and source files.
- `compact_training._archive_extension`: both-plan input name and exact input
  SHA in `compact_archive_execution`. `_retention_extension` separately joins
  the new retained policy/input/descriptor and requires the archive route.
- `archive_owner_policy.select`: actual owner, registered endpoint identity,
  namespace, whole-workflow finite logical allowances and original descriptor.
- The producer attaches `archive_owner_operations.Ledger` before any stage.
  Existing writer/read wrappers bind claims, original owner/stage identity,
  scientific ancestry, captured lock/thread/lifetime and full read/seal joins.
- Original terminal content checks stay local-only. They do not need a newly
  opened transport and cannot be made dependent on a fresh remote fetch.

A bounded scan of49 tracked study JSON files named gate, execution-job or
producer-plan found no `compact_archive_input` or `compact_restart_retention_input`
selection. Exact scope and file hashes are retained; this is not a search of every
possible registration store. The current resource preparation remains a draft,
and acceptance of helper code does not amend any historical executable gate.

## Smallest coherent patch proposal

Proposed files are an ownership request for the next task, not edits made here.

| File | Narrow responsibility |
|---|---|
| New `archive_dispatch.py` | Read-only registered selection/config preflight; fresh outer transport context; immutable original configuration/namespace pins; durable cumulative transport reservations and bounded diagnostics; active operation lease binding; primary-aware terminal/failure closure. |
| `job_payload.py` | Preflight every selected archive representation before population/graph work; construct the admitted context only for an explicitly selected route; inject its transport into the existing keyword; close/check outer evidence without weakening fatal propagation or local route. |
| `archive_owner_writer.py` | Bind the already captured writer claim/science/held-token lease into the registered adapter for the exact active writer lifetime. Keep custom injected synthetic transport compatibility under the existing interface. |
| `archive_owner_stage.py` | Bind the corresponding read-claim/science/held-token lease for the exact reserved archive verification lifetime. Revoke the context on every exit. |
| New focused dispatch tests and evidence | Local children/fake transport first; then isolated immutable actual-owner outer-dispatch proof. |

No changes to numerical kernels, restart primitive, retained-stage formats,
scientific population or owner terminal are expected. `archive_transport.py`
should remain the reviewed low-level adapter; the new outer module supplies its
trusted configuration, budget and callback obligations. A defect requiring a
transport change needs explicit ownership and regression evidence first.

The preferred context factory takes an actual active ResearchRun, representation
name and exact registered job. It returns no transport for the old local route,
and refuses contradictory selection before allocating a context. It reads a new
explicit input reference, for example `compact_archive_transport_input`, present
identically in the execution job and producer plan, with an exact registered
content hash. That is a prospective name, not an existing supported schema.
All representations/configurations and aggregate budgets are preflighted before
any produce loop; no per-representation budget reset can evade the whole-job cap.

The existing archive descriptor already binds the archive policy input, whose
`transport_identity` binds connection configuration. A separate outer admitted
record must also bind the transport input SHA, representation/workflow, actual
run/source/guard, command configuration, rate/deadline/diagnostic limits and
cumulative budget. The latter are not in the existing transport identity. This
can avoid changing scientific descriptors if the exact job/plan/input joins and
outer terminal evidence are independently pinned. If the coordinator instead
requires these controls in the workflow descriptor, that is a larger coherent
change to compact_training and compact_native_producer reconstruction; do not add
an ignored descriptor field or weaken either exact equality check.

The outer context must use a fresh canonical owned namespace on an explicitly
admitted filesystem and retain its original inode/claim. Its registration must
name terminal and failure evidence. The actual fit output/journal inventory must
anchor the original context receipt; a mutable caller hash or rewritten final
receipt cannot become a new baseline. Keep records separate from existing exact
stage inventories. Failure preserves every partial transfer/diagnostic, claim
and spent reservation; duplicate close cannot poison prior successful evidence.

## Callback and lock boundary

The current maintained Transport accepts a single live callback; its constructor
makes a diagnostics directory but opens no credentials and starts no process.
Its callback is polled during transfers. Archive operations run under an already
held owner transition. Calling the public `Operation.lease()` there would attempt
to acquire that same nonreentrant lock and fail. Checking `lock.locked()` alone
would not prove authorization.

The new adapter should accept an operation capability only from the existing
private wrapper while its typed captured token is active. Capture exact claim,
ledger, stage, owner, thread and lock, and use the wrapper's existing private
lease; revoke in a primary-aware finally block. Every subprocess/poll/reservation
requires that capability plus actual outer run/source/guard liveness. No transport
operation is allowed between claims or after owner closure. Do not replace
scientific ancestry with an outer guard check, and do not call a closed owner
lease from post-close content verification. Outer finalization uses the existing
terminal-phase run/source/guard authority and original context evidence.

The reviewed low-level adapter treats mutable attributes and budget as trusted
caller state. The context must serialize access, pin/recheck the actual command,
endpoint, diagnostic root, budget and callback configuration across callbacks,
and reject replacement/refund/reentrancy. Preserving just `.identity` is not an
immutability check of `.ssh`, `.scp`, `.budget`, `.live` or `.diagnostics`.

## Transfer accounting: retain distinct units

The operation ledger reserves decoded logical payload, not network traffic. A
writer reserves3×stage payload; each reserved verifier adds1×stage payload.
The low-level adapter's `Budget` only holds a mutable in-memory `remaining` value.
It is neither a durable no-refund job ledger nor an independent physical meter.

For an actual member of length b, upload reserves b; each download reserves
`32768 * (floor(b / 32768) + 1)`. This intentionally includes an extra read block,
even at an exact block boundary. Writer copy/readback and later archive retrievals
must be counted from the exact permitted operation/chunk population; failed
commands still spend, and command diagnostics also consume their own finite
allowances. Do not equate `max_decoded_transfer_bytes` with that rounded transport
budget. Derive a conservative job-wide bound including every writer/readback/read,
maximum chunks, representations, requested verifications and failures, and reject
insufficient finite allowances before claim. Keep separate durable counters for
logical reservation, rounded payload reservation and observed transfer results.

Neither counter is SSH/SCP wire bytes: framing, encryption, stderr, handshakes and
other traffic are excluded. A rate limit is not a total-byte cap. A per-command
deadline is not a whole-job deadline, and upload snapshot preparation precedes the
child deadline. Local raw bytes and sealed memfd copies coexist; their RAM is not
free because the upload is bounded. Cleanup sends a process-group kill request
and confirms the direct child only; the admitted outer guard must establish full
descendant cleanup. Diagnostics and receipt/control publications need bounded
cumulative bytes/counts and reserved failure headroom, not only a16KiB stderr tail.

## SSH and physical release remain separate

Before any real transfer, bind explicit host/user/port, absolute identity and
known-hosts paths, endpoint identity and a fresh remote namespace. Never discover
or print credentials. Current transport identity hashes paths/configuration, not
key-file contents. Strict host-key checking is already enabled; no host-key
learning, retries, overwrite recovery or remote deletion should be added.
Versioned command/tool/runtime pins and Linux sealed-memfd plus /proc capability
must be established. The remote command environment and namespace owner/capacity
must support exclusive creation and the exact payload contract. A fresh bounded
SSH interoperability/recovery smoke needs separate admitted identity/source and
must preserve failed attempts; no historical smoke script should run again.

Physical admission needs independent aggregate RAM, actual allocated disk,
local free floor, remote retained/peak space, transfer ceiling, process/descendant
lifetime and elapsed-time enforcement. Preserve the user10GiB floor. Include
source/input arrays, resident sampler and samples/dictionary, active engine,
current+candidate/replay state, archive snapshots/readbacks/downloads/memfd,
metadata/diagnostics, failed attempts and final outputs. Existing receipt hashes
or logical byte formulas do not prove remote capacity or local allocated blocks.
The retained-stage controller bounds its own declared route only, not all those
other lifetimes. Reuse the accepted retention/readiness and resource revision02
worksheets; this assessment does not reopen score-tail archival research.

Do not reuse the in-progress neural physical helper merely because it exists.
Its accepted applicability to a fit/archive worker, subprocess transport, output
namespaces and transfer accounting must be established after that source freezes.
No active job/resources/neural source was inspected or modified for this note.

## Decisive next verification

Tiny tests should first reject absent/mismatched input references, altered
endpoint/controls, insufficient rounded budget, wrong actual run/job/guard,
expired/wrong-thread operation capability, concurrent use, callback counter
refund, namespace replacement and direct use outside a claim. Construction and
all preflight negatives must forbid subprocess/network calls. Local children
exercise bounded success, short/oversized transfer, deadline, diagnostic failure,
cleanup fatality and no-refund failure receipts through the existing adapter.

Then freeze the full dynamic required_sources closure in an immutable isolated
copy and run an actual execute_fit_payload archive-selected invented fixture,
with only transport subprocess execution replaced by an explicit local harness.
It must traverse dictionary→MCM→publication→owner/terminal and outer transport
terminal, prove exact original references and cumulative spending across multiple
stages, retain late transfer failure, and forbid transport on post-close checks.
Preserve unchanged local-route regression. Label injected/local proof separately
from real SSH and physical capacity; neither is implied by synthetic success.

Only after independent engineering review and committed source closure may a
new registration pin source/runtime/design commit, exact finite policy inputs,
scientific population/dictionary convention, original attempt budget and all
required output/failure cells. Retention amendment/replay obligations and all
historical gates remain. Current source additions are not admitted by old source
hashes. Final guard/OS/network smoke and empirical gate are coordinator-owned
release steps, not part of this read-only handoff.
