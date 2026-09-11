# Second dated resource failure: independent review

## Evidence and disposition

The failed receipt for `dated-book-resource-correction-20260911` verifies
structurally and retains zero outputs. The claim preserves eight intended cases;
there are no completed financial cell verdicts. The external resource report
records child exit 1 after 4.680430 seconds, with reason
`resource monitor failed: live process has no VmRSS field`. Peak sampled RSS is
215,728,128 bytes against a 536,870,912-byte threshold. Child `ru_maxrss` is
203,968 KiB. The observed failure is therefore the monitor's process admission,
not a measured resident-memory overrun or a financial rejection.

The coordinator reports that SIGTERM interrupted the first `read_input` source
check while a transient Git helper exited. `lifecycle.py:124` checks source before
reading/returning the requested bytes at `:128`, so that reported traceback is
consistent with failure before parsed input or financial evaluation. Admission
already hashes raw input bytes in `ResearchRun.start`; it would be inaccurate to
say the attempt performed no raw-input reads at all. The failed receipt alone
cannot establish the exact interruption point or prove absence of live RAM
inspection. No financial results were evaluated or reconstructed by this review.

## Source diagnosis and engineering admission

Frozen `resource_guard.py:20-24` assumes that absence of VmRSS implies either a
zombie or a live-process error. Linux process exit can remove a task's memory
accounting before a separately read status exposes zombie state. Status and child
enumeration are not atomic. A short-lived Git helper can therefore trigger the
error without excessive memory. The retained report is consistent with this
diagnosis but does not retain the offending PID/status bytes to prove the precise
transition. Preserve the old source and both failed claims.

A separate `resource_guard_v2.py` is appropriate engineering work. Before its
use on empirical inputs, verify missing-VmRSS then disappearing, zombie, restored
RSS and persistent-live missing-RSS cases with deterministic invented `/proc`
responses. A bounded second read may tolerate a confirmed departed task or use a
restored measurement; it must not silently turn persistently unknown live memory
into zero. Retain PID and status context on a persistent failure. The retry adds
detection latency and must be disclosed alongside the 20 ms sampling interval.

The previous preflight covered financial evaluation and real OLS/HAC but omitted
the actual `ResearchRun` source/claim/output lifecycle and its Git subprocesses.
It was insufficient to admit that process interaction. A disposable invented
lifecycle exercise, complete statistics path and rapid synchronous Git helpers
under the exact wrapper are the next bounded checks. This is not a reason to run
the financial inputs again during engineering.

## Attempt budget and next research step

The dated allowance is exhausted: historical prior one, archive one, first book
failure one and resource-correction failure one total four administrative units.
Neither engineering defect releases a claimed attempt. No mechanism/family rename,
new gate identity or financial re-evaluation may silently reset this count.

Defer dated financial work while the options admission proceeds and the shared
resource wrapper is repaired. A later single additional unchanged dated episode
could have information value: cash viability remains unanswered, no favorable
economic setting was selected, and all required price inputs are already retained.
That possibility does not itself authorize or admit an extension. Reassess it
after the competing options question and robust wrapper checks, against remaining
research value and implementation effort.

The current lifecycle deliberately rejects changed family metadata
(`admission.py:214-217`). The README at lines 81-85 requires a separately reviewed
engineering/policy amendment preserving all old claims and does not provide an
implicit extension switch. Any eventual extra dated attempt therefore needs that
explicit amendment, its rationale and independent review before a new frozen
registration. Until then the correct state is deferred, incomplete and resumable,
with zero validated strategies; neither family-wide rejection nor phase exhaustion
has been established.

## Untested claims

Actual financial PnL, exposure statistics, execution and margin feasibility,
exact live process transition, original traceback and external backup equality
were not independently tested. Concrete v2 wrapper review is pending. No broader
economic or higher-effort investigation is needed to diagnose the preserved
monitor failure.
