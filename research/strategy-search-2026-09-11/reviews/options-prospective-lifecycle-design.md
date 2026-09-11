# Narrow prospective source lifecycle for the options path

September11,2026. Read-only architecture review; no implementation, capture,
price-body read, gate change or remote operation. The user has an always-on VPS
available. Its existence does not authorize systemd edits or production reuse;
the reviewed manual deployment boundary remains. This is a design proposal,
not a granted fourth options question or a resumed failed run.

**Recommendation:** one additive, target-scoped **source collection lifecycle**
with a pre-network claim and bounded immutable observation journal, plus a
separate later offline economic child using prospective bindings. Preserve the
four frozen runtime packages. The source collection needs its own explicitly
reviewed cumulative options extension and resumability contract. None of the
current helpers can honestly supply all of this by an argument change.

## What existing code supports—and does not

`docs/research/README.md:88–124` describes prospective **evaluation**: freeze
pending input names/paths/datasets/windows with null hashes, commit before the
window, capture/admit separately, then commit exact hashes and manifest bindings.
The entire registration stays unchanged. This is not an API for starting a
45day collector with missing future inputs.

In `tradingagents/research/admission.py:240–295`, every window must have ended
for `ready`; unresolved prospective hashes also prevent readiness. The registered
input dataset set must equal the declared window dataset set. In
`lifecycle.py:65–90`, `ResearchRun.start` refuses an unready sample, exclusively
creates the run and hashes existing inputs. `write_json:134` permits only
declared basenames and immutable publication; `finish:157` requires exactly the
declared outputs and compares the process's recorded publication map. A crash
has no resume API, and terminal failed/complete runs cannot be reopened. The
README explicitly places interrupted empirical resumption outside that API.

`research_spread/README.md` and `grant.py:4,28–37` admit only
`dated-spread-book-20260911` through its consumed seventh dated certificate.
They do not grant options capture, future-window collection or another attempt.
The earlier amended/extended helpers also preserve target-specific limits.
Copying the old failed claim, changing its ID/certificate, setting a past input
window to disguise future observations, or appending to published JSON would
violate their contracts.

The exact options family inspected from `gates-options-entry.json` is
`options-volatility`, mechanism
`binance-option-delta-hedged-volatility-premium`, original budget4/prior1.
Three new claims plus one known historical administrative bundle consume4.
The12RVIV rows are not12independent attempts. A single new source claim requires
an explicit effective5 grant while the old family object remains byte-identical.
Any later economic child needs a separately adjudicated allowance; do not hide
its work inside a source grant or pre-authorize it here.

## Minimal separation of collection and analysis

1. **Freeze the scientific policy before its future window.** Pin instrument
   selection, eight intended future books, hedge/funding ownership, fees,
   missing-decision/terminal rules and all source endpoints/windows. Source-only
   collection interprets only the information necessary for deterministic
   contract selection and source validation. No delta hedge, premium cash,
   margin affordability, returns, paper journal or policy performance is
   computed while collecting. The fixed policy can be hashed preparation even
   when no economic child grant is issued yet.
2. **Grant and claim one source experiment before any market request.** Give it
   a future *output observation window*, distinct from existing design/metadata
   inputs. Its new source protocol explicitly allows collecting during that
   window; it does not weaken the old evaluation `ready` test. Commit/push the
   exact source/gate/extension and verify equality before claim and networking.
   The claim consumes the allowance once, records all source slots and becomes
   the exposure record. A pure design check is not the claim.
3. **Collect fixed slots under that claim.** Publish immutable intents and raw
   receipts in a bounded journal. Short invocations may stop between scheduled
   slots while the source experiment remains active. They must not use the old
   `ResearchRun` context manager, which closes unfinished work as failed.
4. **Close and independently admit the source.** At its fixed end—or a frozen
   unrecoverable failure—publish one terminal manifest/receipt with every
   intended/attempted/unavailable slot and all raw members. A successful source
   terminal is evidence of retained acquisition, not economic success.
5. **Only later bind and evaluate.** Independent semantic admission and a
   separate budget decision precede an offline economic child. Its bound input
   hashes reference the captured bytes and immutable manifest. No source
   manifest can smuggle a changed selection, fee or hedge schedule into analysis.

To use the existing prospective-binding semantics literally for that later
child, its full design registration, source and policy must already have been
committed before the future observation start, with exact pending input names
and null hashes. That pre-registration need not grant execution now. A later
child created only after viewing the episode is development/result-informed;
it cannot be called a pre-frozen prospective test. The collector's early
registration alone does not prove the financial rule was frozen.

## Concrete bounded raw journal rather than mutable outputs

The additive protocol should declare a maximum45day UTC observation envelope,
16routine hourly sources, separately enumerated initialization/funding/final
slots, deterministic slot IDs, body/total-byte limits and exact request recipes.
Selection may determine an earlier close under the frozen expiry rule; retain
the absolute envelope and explicit unused/post-close slots rather than silently
changing denominators. Alternatively freeze all calendar slot IDs after
deterministic selection in an immutable selection record, only if that two-stage
rule and maximum denominator were committed before selection. No price-driven
duration or replacement symbols.

Use append-by-new-file immutable records, not append to finalized JSON. A narrow
layout can contain `claim.json`, `journal/intents/<slot>.json`,
`journal/receipts/<slot>.json`, bounded raw-body members, immutable recovery
events, and fixed `outputs/capture-manifest.json` plus
`outputs/source-admission.json`. These paths are proposed, not created. Each
record carries the claim/design hash and sequence/slot identity. Publish with
exclusive creation, atomic finalization and fsync. The final verifier must cover
the journal/raw members—not merely the two top-level output hashes.

An intent is durable **before** its request begins. One network attempt per
registered source slot; raw retained bytes and request/retrieval UTC and
monotonic clocks must be durable before normalization or the next request.
Network failure or truncation retains its bounded body prefix and unavailable
reason. If raw streaming uses temporary partial files, include their explicit
names/hashes in recovery/final retention; do not delete a partial body merely
because it could not become a complete receipt.

The new schema may describe journal members by a strict slot grammar and
maximum count rather than thousands of mutable `outputs` entries. That is a
new, independently reviewed output contract, not an exception to the old helper.
Source slots and raw records are subordinate observations inside one claim;
hourly process restarts are not new financial attempts. Failed/oversize/suppressed
slots retain the full intended denominator, and terminal failure retains all
partial artifacts. No mutable pointer is the sole authority; any convenience
checkpoint must be reconstructible from immutable records and validated.

## Crash and restart: explicit new protocol, no failed-run reuse

Resumability must be granted in this new source charter before the initial
claim. It applies only while this exact claim is active and before its absolute
end, not to any of the19terminal runs. Hold a dedicated persistent process lock
for each invocation; use the shared research admission lock only for claim or
terminal transitions, never throughout45days.

At restart, verify claim/source/spec hashes and every published journal record,
then append an immutable recovery event identifying the prior tail and newly
missed slots. A fully published slot is never requested again. An intent with
no final receipt is an interrupted/uncertain request: retain its raw partials
and mark unavailable, **do not retry it**. A past slot with no intent is missed;
do not backfill current quotes or pretend retrieval occurred at the scheduled
time. Resume only future authorized slots. A differing existing record,
concurrent writer, changed source or expired window refuses continuation and
requires a retained failure/review disposition.

Under this pre-authorized protocol, ordinary process/session loss is an active
collection interruption, not automatically a failed terminal requiring a new
claim. If `failed.json` or `complete.json` has been published, resumption is
forbidden. That distinction is the reason an additive lifecycle is necessary;
monkeypatching `_active`, reopening a failed ID or manufacturing a terminal
after the fact would not be compliant. The old spread failure stays failed.

## History, budget and efficient verification

The new independent verifier must admit the exact19terminal-claim inventory,
preserve their original gate/source/runtime/certificate/terminal hashes, and
include all failed claims in budgets and exposures. Do not create a second run
root on the VPS containing only the new options claim, which would hide prior
history. A dedicated research checkout/run root can mirror the authoritative
retained history without touching production. If a compact history package is
used, its complete claim/terminal/output-hash proof and source objects need an
explicit reviewed portability contract; a hand-written count is insufficient.

In particular, a new closed-snapshot proof for the seventh dated claim is needed
where the existing live-ledger verifier refuses later descendants. Preserve
the earlier v1/v2 snapshot boundaries and the spread's failed status. The new
proof should reconstruct the original target certificate at its exact original
predecessor inventory, then verify its terminal output hashes; it does not grant
an eighth dated allowance. All four runtime packages remain unchanged and
hash-pinned. New unrelated claims arising during the45day collection must remain
visible and must not alter this source claim's frozen budget/history contract;
define their append-only verification treatment explicitly rather than locking
the research program for45days or dropping them.

Decision19 demonstrates why nested full-history admission on every raw write
is unsuitable. Perform comprehensive history/source admission at claim and
controlled resume/final boundaries; verify the active claim, source epoch and
new record identity under its lock for each write. Any cached validation must
be explicitly content-addressed and invalidated by changed dependencies, not
assumed trustworthy from a previous PASS. Benchmark representative retained
history **without financial input parsing** before deployment. Do not solve
the overhead by silently skipping ancestor checks or enlarging a frozen bound.

## Final binding and preservation

At end, independently reconstruct the fixed slot calendar, actual requests,
hashes, all unavailable/partial states, selection and clocks. Publish a canonical
capture manifest with every member path/hash and source window; commit/push raw
evidence and verify actual remote recovery, not only a marker. The source gate
does not require waiting for a successful economic interpretation to close.

For a pre-frozen economic child, the separate bindings object follows
`docs/research/README.md:99–120`: exact design_commit, experiment,
registration_sha256 and exactly the pending input names, each supplying only
sha256 and capture_manifest path/hash. Paths/windows/rules remain unchanged;
execution source descends from the design source. Bind missing/failed source
coverage honestly and retain unavailable economic cases. Any compact derived
input bundle also needs a frozen deterministic transformation and raw lineage;
do not replace the raw manifest with untraceable processed prices.

Prospective raw collection exposes those observations administratively. If the
existing helper classifies a later child as exploratory due to that parent
exposure, preserve that conservative classification. No confirmation exception
or claim of independent future profits is needed for this single episode.

## Minimum engineering scope and required synthetic proof

One target source lifecycle/grant, its independent historical/journal verifier,
and one collector adapter are sufficient. No generic scheduler, strategy engine
or multiple-venue framework is required. Test exclusive claims; initial network
denial; intent-before-request; kill during partial receipt; restart with no
duplicate request; missed/calendar-boundary slots; changed source/claim;
concurrent writers; byte/count caps; final source binding and terminal refusal.
Simulate45days by invented timestamps, including prior19claim history and a
later unrelated claim. Measure actual total serialization, CPU and RSS through
the real narrow wrapper; no45day sleep or market sample is needed for preflight.

This source-only extension is a concrete registered need permitted by the
README's additive design. The currently consumed certificates cannot supply
it. After independent acceptance, stage a separately hashed research package
under the existing VPS manual route; do not issue systemd changes, load secrets
or mutate production as part of lifecycle engineering. No implementation or
deployment grant is created by this architecture report.
