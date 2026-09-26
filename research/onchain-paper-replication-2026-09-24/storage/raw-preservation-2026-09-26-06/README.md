# Retained ETH backup continuation 06

The user explicitly requested resumption on September26 after05 stopped at its
host memory reserve. This is one new finite preservation attempt. No predecessor
is restarted; completed bundles, failed partials and spent resources remain.

Parent05 stopped after6,735.413494 guard seconds with3,165,048,832 bytes of host
available memory below the3,221,225,472-byte reserve. Cleanup is verified and its
controller, worker and cgroup are absent. No OOM event was recorded. The host
workload responsible for the dip is unknown. Available RAM has since recovered;
this is a point observation, not assurance of sustained headroom. The3 GiB
runtime reserve and4 GiB startup requirement are unchanged.

The original pilot02 plus verified03 batches1–33 and05 batches34–41 form the
exact prefix0–41:7,309 files /22,314,379,965 raw bytes. Every new05 manifest member
and recovered completion marker was reconciled against the frozen inventory.
All59,083 source sizes/modification times still match; no raw body was reread
during preparation. The same source hashing and full recovered-member checks
apply to every new transfer. Failed05 batch42 retains both its532,828,160-byte
packed archive and180,748,288-byte recovered partial without verified credit.

Continuation06 starts global batch42 under the separate remote root
`research-backups/onchain-paper-replication-2026-09-24/raw-retained-ETH-06`.
Exactly153 remaining batches cover51,774 files /81,210,109,078 raw bytes. Ten
phases cover42–194 once, nine with16 bundles and one with9. No completed batch
is uploaded again. Final recovery requires the original pilot02, completed03/05
bundles and verified06 bundles together.

The transfer source is byte-identical to05. Its original05 docstring is retained
to preserve exact source identity; dynamic HERE selects the new06 contract and
output directory. The reviewed42-test evidence is inherited without a redundant
test run. New configuration admission checked every bound hash, prefix totals,
phase coverage and scratch floor before release; no empirical work occurred.
Bounded stderr diagnostics remain enabled.

Limits remain one512 MiB-raw bundle at a time,2 GiB scratch,256/192 MiB memory
max/high, zero swap,3 GiB host runtime memory reserve and4 GiB startup reserve,
two-CPU affinity,8 MiB/s transfer cap,20 GiB local disk floor plus2 GiB scratch
preflight, and256 GiB remote floor plus phase occupancy. Each phase is <=8h;
the controller is <=48h, stops on the first failure, and never retries itself.
Only successfully verified generated tar copies are removed. Originals and all
failed partials stay preserved. No concurrent synthetic tests are admitted.

New06 reserves205 GiB file payload; phase caps total200 GiB. Prior conservative
660.625 GiB allocations remain, giving865.625 GiB combined. Prior measured guard
time totals20,848.202118532 seconds, including the full failed05 attempt; adding
the new172,800-second ceiling gives193,648.202118532 seconds. Old reservations
are not reset or relabeled as spent. SSH overhead/control commands and idle
preparation time are excluded from file-payload/guard totals. Earlier diagnostic
and read-only preflight receipts remain retained.

Before launch: independently review the exact configuration, lineage, closure,
inherited source evidence and cumulative budget; freeze and commit the release.
Invoke this directory's `transfer.py all-bulk` once. Thereafter inspect existing
controller/guard/bundle receipts only. On failure preserve partials and prepare a
separately reviewed successor; on completion independently reconcile the whole
59,083-file denominator. No recurring assistant wakeup or financial fit follows.
