# Retained ETH backup continuation 07

The user reported a connection loss and explicitly requested resumption.
Continuation06 is terminal FAILED: SCP exited1 with `lost connection` during
batch45 archive upload. Its guard elapsed2,022.109623 seconds and verified cleanup;
the controller, worker and owned cgroup are absent. Its535,347,200-byte local
archive, manifest, failed receipt and unverified remote partial remain preserved.
The precise cause of connection loss is not established. A fresh, single read-only
SSH capacity check succeeded in0.768 seconds; future stability is not guaranteed.

The three completed06 batches42–44 add634 files /1,593,323,300 raw bytes. Combined
with pilot02 and completed03/05, the exact prefix0–44 is7,943 files /
23,907,703,265 bytes. Every new manifest member and recovered completion marker
was reconciled against the original inventory. All59,083 retained sources match
inventory size/mtime; raw bodies were not reread during preparation.

The new remote root is
`research-backups/onchain-paper-replication-2026-09-24/raw-retained-ETH-07`.
Only150 remaining batches45–194 are admitted:51,140 files /79,616,785,778 bytes.
Ten phases cover them once, nine with16 bundles and one with6. Completed bundles
are excluded from new uploads. All previous outcomes and partials remain intact.

Transfer source is byte-identical to05/06; its original05 docstring is retained
for exact identity and dynamic HERE resolves07 paths. The source-bound42-test
evidence is inherited without rerunning tests. Exact configuration/hash/prefix
and scratch admission passed. Bounded stderr/exit diagnostics remain enabled.

Unchanged limits: one512 MiB-raw bundle at a time;2 GiB scratch;256/192 MiB cgroup
memory max/high;zero swap;4 GiB host startup reserve and3 GiB runtime reserve;
two-CPU affinity;8 MiB/s transfer cap;20 GiB local disk floor plus2 GiB preflight
scratch;256 GiB remote floor plus phase occupancy. Each phase is <=8h, controller
<=48h; stop on the first failure without automatic retry. Successful generated
tar copies alone are removed after full archive/member/marker verification.
No concurrent synthetic tests are admitted while the transfer runs.

New07 reserves205 GiB file payload; phase caps total200 GiB. Prior865.625 GiB
conservative allocations remain, giving1,070.625 GiB combined. Prior measured
guards total22,870.311741608 seconds; adding172,800 prospective seconds gives
195,670.311741608 seconds. Prior reservations and failed spending are not reset.
SSH overhead/control-command traffic and idle preparation are excluded from these
file-payload/guard totals. Read-only connectivity checks remain separately receipted.

Before launch: independently review the exact source/configuration, lineage,
closures and cumulative budget; freeze and commit `BULK_RELEASE.json`. Launch
this directory's `transfer.py all-bulk` once, then inspect existing receipts.
Never restart a closed identity. On failure retain partials and reconcile a new
reviewed successor; on completion independently verify combined pilot02/03/05/06/07
recovery against all59,083 files. No financial fit or recurring monitor is started.
