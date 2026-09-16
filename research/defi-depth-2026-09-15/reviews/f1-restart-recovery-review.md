# Independent F1 restart recovery investigation

## Initial disposition

A narrowly scoped manual continuation of the existing claim is justified in
principle under the user's explicit PC-restart/resume instruction, subject to
review of the actual committed recovery adapter and decision receipt. This is
not approval to rerun `ResearchRun.start`, replace a claim, change a financial
recipe or bypass a spent repair allowance. No adapter was executed by this
reviewer. The original claim remains nonterminal; no failed receipt was written.
Only this review file was created in the coordination root.

## Independently recovered facts

The isolated F1 root is
`/home/malecada/master_thesis/TradingAgents-defi-f1` at unchanged clean tracked HEAD
`b2a1659e2645c6fa6cba03bba6b73d0c74b30bb8`. Independent `verify_claim` passed
committed registration, source and claim identity. The run directory contains
exactly `claim.json` and an empty `outputs/` directory, including no hidden pending
file, complete receipt or failed receipt.

Original claim SHA256:
`2ad4dc79f812cafa80486b64a28cea1a45170c99380bb3eff9aaac187a1c6730`.
Original start time:2026-09-16T09:36:19.909003UTC. All1652 registered input hashes
were independently rechecked and match. Registered denominator remains3380 cells
and14913 outputs. Family prior6/cap7 already includes the single spent F1 claim;
its window remains exposed and its financial/phase slot remains consumed.

The parent reports the prior process absent after the PC restart. This review did
not inspect unrelated processes or options work. The recovery launcher must still
establish exclusive ownership immediately before attachment, because filesystem
state alone is not a process-liveness lock.

## What could execute before the first output

Frozen `f1_source.py:28` creates the claim and validates inputs. It then reads
registered design/context evidence and reparses retained sources at lines29–32.
Line33 publishes `history.json` before entering source capture at line36.
`financial_source_policy.py` publishes each physical intent before its fetch.
The immutable writer in `tradingagents/research/lifecycle.py:30`–44 fsyncs complete
temporary bytes, links without overwriting, and fsyncs the containing directory.

Therefore, under the intact-root/frozen-code assumption, no new F1 request or
financial book could have run while leaving the observed empty output directory.
The historical inputs may have been read, hashed or reparsed before interruption;
that earlier research exposure remains preserved. No return calculation lies on
that startup path. No attempt-count or financial-opportunity conclusion depends
on whether the interrupted process was inside initial input hashing or subsequent
retained-evidence verification.

This is a control-flow and durability inference, not a provider-side network log
or proof against undisclosed deletion/storage failure. Any conflicting retained
intent, hidden pending output, terminal receipt, changed claim or evidence of an
active worker would invalidate the narrowly empty-output recovery route.

## Existing lifecycle behavior and authority

Ordinary read-only admission was tested and rejects this identity with
"repeat run prohibited; use a separately justified registration". No new start
was attempted. Existing-claim source revalidation with `_own_claim` passes and
returns ready=true with the exact original contract, inputs and family. That
parameter is used internally for an already active run; it is not a public crash
resume API or independent authority to attach arbitrary claims.

The lifecycle's `start:78` requires a new directory, and class documentation
states partial claims block automatic retries. The cycle skill requires the
contract's permitted recovery/closure procedure. `docs/research/README.md:165`–168
requires review and a preserved explicit recovery decision, never deletion or
reuse as a fresh run. `AUTHORIZATION.md:27`–28 likewise requires explicit reviewed
recovery. The user's resume instruction supplies current task authority; the
missing engineering route must still be made concrete, committed and reviewed.
A new recovery decision should explicitly distinguish attaching the same durable
claim from creating another run with its ID.

## Minimum safe adapter contract

1. Pin exactly this root, original full source commit, experiment/gate and claim
   hash, including original start time, contract, inputs, windows and family.
   Refuse changed HEAD/source/runtime/input hashes, any terminal, any output or
   pending artifact, unexpected run entries, or nonexclusive ownership. Check
   again atomically immediately before attachment.
2. Keep the original claim and registered files byte-identical. Reconstruct an
   original `ResearchRun` object with the original admission and claim hash and
   an empty published-output map only after the empty-output proof. Do not call
   `start`, amend the gate, increase prior/cap values or invent a fresh run ID.
3. Retain the normal original source/input checks, immutable writer, denominator
   verification, failure handling and complete terminal publication. Resume the
   original startup path before its first output; do not skip provenance checks
   merely because their earlier execution is plausible. Avoid duplicating source
   or financial logic inside the adapter.
4. Use a separate committed and hash-pinned recovery decision/adapter plus an
   immutable external recovery-start receipt before attachment, with exact old
   claim hash, empty-output inventory, user resume authority, source/adapter
   identities and independent review reference. Keep it outside registered run
   outputs. Retain recovery completion/failure evidence separately as well.
   Reports must include both original scientific source and recovery supervision
   provenance; the old completion receipt alone does not describe the added
   execution adapter.
5. Hold a dedicated exclusive recovery lock for the entire attached session and
   prevent a second adapter from attaching to the same empty claim. The ordinary
   lifecycle's short per-operation lock alone is insufficient for two recovery
   processes. Do not enable automatic general retries after another interruption;
   any nonempty subsequent state is outside this adapter's approved scope.
6. Exercise invented fixtures for exact successful attachment, altered claim,
   source/input mismatch, terminal/nonempty/pending output, repeated/concurrent
   attachment and interruption around receipt publication. Verify claim bytes,
   original attempt count and immutable output accounting remain unchanged.

The recovery event is additional execution history, not a new economic recipe or
source experiment. It must not claim additional repair/confirmation capacity.
F1 remains the same one financial and phase attempt; the7239 physical reservation
and all prior exclusions/costs/stress/benchmarks stay frozen. Any changed API
behavior, economic rule, source scope or attempt after a retained unknown send
would require a different assessment and is not authorized by this narrow route.

## Remaining work and untested claims

The actual adapter, exact recovery receipt schema, lock behavior and synthetic
closure have not yet been reviewed. No source request, empirical arithmetic,
original claim edit, terminal closure or production mutation occurred here.
The incomplete claim is operationally recoverable in principle, not completed,
economically failed or a validated strategy. Final adapter review is required
before execution; no further user confirmation is inferred from this review.
