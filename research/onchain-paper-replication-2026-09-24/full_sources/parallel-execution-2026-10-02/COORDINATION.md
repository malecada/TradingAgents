# Parallel execution checkpoint — October 2, 2026

The user explicitly requested parallel unattended continuation. The existing
paper-replication-progress heartbeat was updated through the app tool, preserving
ACTIVE status, 15-minute cadence, thread target and quiet routine notifications.
Up to three bounded agents can work alongside the root coordinator when tasks
are independent. This does not authorize parallel empirical admission or paid
resources. Existing jobs/agents must be inspected before dispatch.

## Ownership and active work

- Root: STATE, integration decisions, isolated test-cost profiling and this record.
- archive_transport: new archive_transport.py, new test_archive_transport_production.py,
  full_sources/archive-transport-production-2026-10-02/ only. Implementation active;
  local subprocess tests only, no real transfer. Existing sources remain untouched.
- resource_parallel_readiness: read-only investigation complete; findings below.
- owner_closure_review: read-only integration investigation complete; findings below.
  Available for independent transport review after implementation.

The isolated profiling snapshot is exported from committed b449a2a59549ea500790e95df1615df21b753401,
with manifest and archive digest retained. It does not share mutable package
sources with the transport worker. profile01 setup failed before any test because
an optional nonexistent tests/__init__.py path was supplied; failure is retained.
profile02 closed with one fixture setup error because the export omitted the
required matching config; the failed log/profile and result record are retained.
profile03 includes the committed configs and is the fresh synthetic single-test
cost profile, session7403. Inspect profile03.log/process before further action. No historical empirical
identity was reopened. The snapshot is retained locally; its tracked manifest
and source commit identify reproducible bytes, not an empirical result.

## Coupled integration ownership

One integration owner must handle the producer-to-terminal slice coherently:
compact_native_producer and compact_training descriptor reconstruction must bind
compact_archive_execution; dictionary/MCM producers need explicit lock-held
writer/seal internals; their evidence and compact_mcm_publication._prepare,
compact_mcm_output._source and compact_owner._verified_stages need shared archive
content verification. Public archive wrappers currently acquire the same lock
already held by producers; calling them recursively is invalid.

compact_terminal._original checks evidence after owner closure. A callback-free
content verifier must consume original pinned claims/seals/proofs under terminal
phase authority. An optional bypass flag on current-owner APIs is not acceptable.
Terminal exact journal membership must derive archive namespaces from admitted
ledger operations rather than discovering and blessing arbitrary entries.
The decisive integration test includes dictionary, MCM, saved output, publication,
owner/terminal completion and local-only post-close validation with remote calls
forbidden, plus late-failure preservation and local-backend regression.

job.required_sources dynamically includes every package .py file. New modules
therefore change source-admitted fixtures too. Run those fixtures against an
immutable isolated snapshot, or freeze the full package until the run closes.
Lightweight independent tests may run concurrently only with disjoint outputs
and bounded aggregate resource use. Never weaken provenance checks for speed.

## Independent resource preparation

The preserved coverage05 inventory and native-resource-admission inputs02 bind
32 pending requirements and43 compact input pins:

| Weeks | Pending requirements |
|---|---|
| 2022-01-03, 2022-06-13 | MCM and neural checkpoint for each |
| 2022-07-25, 2022-11-07, 2023-06-05, 2024-01-01, 2024-03-11, 2024-08-05, 2024-12-23 | neighborhoods, matching, MCM, neural checkpoint for each |

Totals remain7+7+9+9=32, coverage77/109. The original resource contract uses the
2022-01-03 dictionary across MCM weeks. Its neural test uses synthetic random MCM
and repeats one graph across16×28 inputs: preparation is independent of actual
MCM numerical completion, but neither chronological multiweek capacity nor
financial validity follows. Preserve this distinction in successor admission.

Independent work can draft exact population/reuse and32-cell mappings, retained
failure dispositions, hub/node/pair amendments, physical-storage worksheet and
aggregate scheduling constraints. Draft cumulative61 remains unadopted:
33spent+12body+15financial+1resource. graph09 allowance was consumed by graph10.
The measured hub701309nodes/712125edges conflicts with the10000node cap, and
4207854 hub-pair entries exceed the4000000 cap. Never truncate to fit.

Conditional selected-payload lower bound249479184384B excludes overhead. Moving
pair events alone still leaves50819833856B of score tails/batches and4619984896B
of two matrix copies across all nine weeks. These are logical arithmetic, not
measured peak-live requirements. Score/checkpoint lifetime and retention must be
included in the final archive route. sampling_weights.py additionally enforces
20GiB plus workspace; reconcile that prospectively with the user10GiB floor.

At dispatch the host reported8.4GiB available RAM and about20GiB free disk. Two
hypothetical3GiB workers plus3GiB host reserve require9GiB, so default to one
resource-heavy job. Extra compute does not remove integration/admission gates.
Use current aggregate RAM/disk/transfer reservations before any concurrency.

Evidence routes: resource-coverage-05-2026-09-30/coverage.json;
native-resource-admission-2026-10-01/{inputs02.json,INPUTS_REVIEW.md,REQUIREMENTS.md,budget-allocation.draft.json};
compact-workflow-accounting-2026-10-02/ASSESSMENT.md; historical
pilot_successor_02/phase.py (read only; never rerun); registered-hub-edges-2026-09-30/.
