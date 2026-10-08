# Lease hotpath attribution03 — metadata sizes and bounded timing

**No additional patch is proposed.** The measured same-shaped unconditional metadata work is small: roughly0.151ms for all three Target pin serializations and0.098ms for a synthetic producer root/read/serialize call. The supplied actual22 lease total is293s across tens of thousands of calls. These fixture timings do not isolate that total and do not justify declaring serialization its largest cost. Existing accepted code-name grouping remains independently useful but applies to full checks, not every callback.

## Actual metadata extent

Three bounded, non-sensitive metadata files were read once: current22 import-complete receipt5019B, current producer start1445B and registered execution_job6143B. METADATA_PROFILE01.json pins their paths, hashes and lengths. No graph arrays, labels, numerical packages, native process probes or full source census were used.

The receipt's current/original metadata reconstructs the exact Target execution shape; execution_identity is replaced by a same-width64-character fixture value. Serialized sizes are mapping589B, execution4964B and scope476B. Producer start.sources contains a183-source count and digest, not the complete source map. Consequently neither ordinary Target._pins nor producer start serialization traverses183 source files or population-sized graph arrays.

The synthetic producer file contains the exact1445B metadata body under this owned directory. Five batches of1000calls measured ordinary stdlib time.perf_counter under CPUaffinity0–1, nice10,256MiB address-space and60s shell timeout. Medians:

| Operation | Seconds/call | Milliseconds/call |
|---|---:|---:|
| All three Target canonical serializations and comparisons |0.000150589|0.150589|
| Producer canonical root check + open/read/currentness checks + serialize/compare |0.000098061|0.098061|
| Producer start serialization alone |0.000016412|0.016412|

The combined approximately0.249ms is a synthetic fixture result, not a measured actual22 lease component or rigorous bound. The synthetic path, filesystem scheduling and concurrent native activity differ. Real target object identity checks, scheduler, live/fingerprint/full checks and progress are excluded. No measured real-data speedup follows.

## Remaining source paths with greater possible cost

`compact_mcm._lease_body:324–331` always calls target_lease and does exact producer root/start checks. `Target._pins:64–69` always serializes the three small values above. Those immediate metadata mutation refusals remain necessary.

On each due100ms live callback, `Lease._live:125–131` executes active Stage.lease/Owner.lease followed by compact_owner.verify_current. Owner.binding_value thaws and hashes the complete bound record, which includes admitted numerical source metadata; Owner.lease checks this before and after Binding.lease, and verify_current checks it again. Binding.lease also checks genuine claim, performs two native guard validations and rereads immutable binding snapshots. Source live checks therefore do substantially more work than the small Target fixture, but their actual share/count was not measured here. Multiple before/after reads protect different mutation boundaries and cannot be removed just because their filenames repeat.

The attached archive ledger participates in verify_current. With history present and no `_typed_expected`, the hot route samples history while rejoining the ledger directory. If `_typed_expected` exists, source selects ordinary ledger._evidence and may perform complete typed metadata rechecks. `typed_payload_operations.ledger_evidence:240` walks each typed control entry and rereads its bytes; archive `_full_evidence:104` also checks its expected files and each operation. The scoped bounded names-only observation found start.json330B and one writer directory, with **no typed-* files**. That is not inspection of in-memory attributes and cannot prove a selected code branch, but it supplies no evidence of a large typed-history roster at this prefix. LEDGER_NAMES01.json retains that observation.

Due1000ms fingerprint callbacks serialize configuration/source/input mappings, stat evidence paths and inventory loaded functions. Due10000ms full callbacks perform genuine execution/source/input/runtime and numeric-motif checks plus loaded-source authentication. A slow full callback can make another live check due at its end. Preserved frozen interval/call/staleness policies remain unchanged. The aggregate does not expose how many checks of each type ran or their duration, so the largest measured actual contributor remains unknown.

## Exactly one optimization considered, withheld

An exact-plain-JSON serialization fast path for Target._pins was considered. It would retain fresh byte comparison while bypassing repeated thaw copying for exact built-in metadata. However, eligibility must itself traverse the live tree and preserve fallback and failure ordering for mutated/non-plain values. The maximum targeted ordinary work in this fixture is only0.151ms/call before eligibility overhead. No independently reviewed equivalence/proportionate benefit is established, so no speculative helper, generic serializer framework or patch is emitted.

The concrete next evidence requirement is live/fingerprint/full invocation counts and duration at their actual scheduler call sites, alongside unconditional lease-body timing, under a separately reviewed future diagnostic. It would preserve all existing callbacks and thresholds. This report does not install that instrumentation or change current22. Main/Git/source freeze, native job, budgets and all original authority checks remain untouched.
