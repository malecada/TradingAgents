# Retained ETH backup continuation 04

The user reported newly available local space on September 25. Preparation
observed approximately 40.0 GB free. This continuation preserves bytes under the
existing authorization; it creates no financial experiment or new source data.

Continuation03 stopped at its 20 GiB local disk floor. Its controller and owned
cgroup are absent, cleanup is verified, and the incomplete batch0034 archives
remain under their original identity. Their sizes are 536,811,520 bytes packed
and 482,181,120 bytes partially recovered; neither is counted as a verified batch.
No completed or failed job is relaunched.

The original pilot02 plus completed03 batches1–33 form the exact inventory prefix
of 5,832 files / 18,052,844,567 raw bytes. Their archive/member verification,
manifest hashes and downloaded completion markers are retained and reused.
Preparation reconciled every member with the original inventory. It also checked
size and modification time for all 59,083 retained sources after the disk cleanup;
all matched. This metadata check does not replace source hashing during transfer.
No earlier successful archive download is repeated for this preparation.

The new remote identity is
`research-backups/onchain-paper-replication-2026-09-24/raw-retained-ETH-04`.
Exactly 161 remaining batches (global34–194) cover 53,251 files /
85,471,644,476 raw bytes. Eleven phases each contain at most16 bundles. Batch34
is a newly accounted attempt of previously incomplete bytes, not a retry under
the stopped03 identity. Recovery requires the original pilot02, verified03
bundles and verified04 bundles together.

Limits remain one bundle at a time, 512 MiB raw per bundle, 2 GiB temporary
allowance, 256/192 MiB memory max/high, zero swap, 3 GiB available host memory
at runtime and 4 GiB at startup, two-CPU affinity, 8 MiB/s transfer cap and
256 GiB remote floor plus phase occupancy. The local runtime floor stays20 GiB;
the new preflight requires this floor plus the full2 GiB scratch allowance
before each phase. Each phase is limited to8h, the controller to48h, with no
automatic retry and stop on the first failure. Only generated tar copies from
successfully verified bundles are removed; originals and failed partials remain.

The new conservative payload ceiling is205 GiB; phase reservations total203 GiB.
All prior allocations remain:249 GiB for backup attempts and1.625 GiB for the
two diagnostics. The conservative combined ceiling is455.625 GiB, excluding SSH
protocol overhead. Prior measured guard time is13,141.744918814 seconds, including
failed and successful backup/diagnostic guards. Adding the new48h allowance gives
185,941.744918814 seconds measured-plus-prospective; this does not erase or relabel
earlier prospective allocations as spent. Idle preparation/review time is excluded.

The source change adds verified-prefix admission and local scratch preflight to
a preserved copy of03's transfer controller. Thirteen new synthetic cases were
observed failing before implementation; the36-test focused preservation suite now
passes. This is not a full offline-suite rerun or a financial result. Shared
preservation/guard sources and prior attempt sources remain unchanged.

Before launch, independently review the exact contract, candidate, source,
reconciliation and cumulative budget, freeze `BULK_RELEASE.json`, and commit.
Only one invocation of this new script's `all-bulk` is admitted. Check the existing
controller/phase receipts thereafter; never invoke it again. No concurrent
synthetic tests are admitted while the transfer runs. On failure, preserve all
partials and reconcile a separately reviewed successor. On success, independently
verify the combined pilot02/03/04 denominator. No recurring monitor is configured.
