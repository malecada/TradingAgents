# Retained ETH backup continuation 05

The user explicitly requested resumption after continuation04 stopped. This is
one new finite byte-preservation attempt, with all failed identities, partials,
completed bundles and spent resources retained. It is not a financial experiment.

Continuation04's first batch0034 archive download exited unsuccessfully after
971.043706 guard seconds. The local recovered partial contains212,402,176 bytes
of the536,811,520-byte packed archive. Its error cause is unknown because the
historical receiver discarded subprocess stderr. Cleanup is verified; its
controller, worker and cgroup are absent. No new04 bundle receives backup credit.

A fresh, single read-only SSH capacity check succeeded in0.812 seconds. This
demonstrates current connectivity, not the cause or resolution of the earlier
interruption. All59,083 retained sources still match inventory size and mtime.
Current disk and memory exceed22 GiB and4 GiB startup requirements respectively.

The original pilot02 plus completed03 batches1–33 remain the exact verified
prefix:5,832 files /18,052,844,567 raw bytes. Continuation05 covers the same161
remaining batches34–194:53,251 files /85,471,644,476 raw bytes. Its new remote root
is `research-backups/onchain-paper-replication-2026-09-24/raw-retained-ETH-05`.
It does not overwrite04's partial objects or rerun a completed bundle.

The only transport change is diagnostic capture in this successor's local source.
The receiver drains stdout and stderr concurrently in chunks of at most64 KiB,
retains the last16 KiB of raw stderr, and writes an exclusive per-download
`.transport.json` receipt with exit code, elapsed time and received-byte count.
UTF-8 replacement/JSON encoding can expand the stored tail beyond16 KiB. The
exact payload-size bound, per-connection rate limit and1800-second deadline remain.
Nonzero SSH/SCP setup/upload commands retain an error tail in the guard log.
No automatic retry, longer timeout or extra transfer concurrency was added.
Prior/shared transfer sources remain unchanged. The original failure is not
claimed fixed; another interruption should have more useful diagnostic evidence.

The guard retains256/192 MiB memory max/high, zero swap,3 GiB runtime available
RAM and4 GiB startup reserve, two-CPU affinity and20 GiB free-disk floor.
Preflight additionally requires2 GiB packing/readback scratch. One512 MiB-raw
bundle is processed at a time, with upload and full recovered-member verification
before deleting only successful generated tar copies. Originals and failed
partials remain. Eleven phases have at most16 bundles each, <=8h per phase and
<=48h controller execution. Any failure stops the controller; no old identity
may be relaunched and no concurrent synthetic test is admitted after launch.

New05 reserves205 GiB file payload; its phase reservations total203 GiB.
Prior conservative455.625 GiB allocations remain, making660.625 GiB cumulative.
Prior measured guard elapsed time is14,112.788624346 seconds; with the new48h
allowance the measured-plus-prospective ceiling is186,912.788624346 seconds.
These totals retain the failed04 attempt; old reservations are not reset or
relabeled as spent. SSH overhead/control-command traffic and idle preparation
time are excluded from file-payload/guard ceilings. The separate read-only
capacity check has its own small receipt; it transferred no raw research payload.

The42-test focused synthetic suite passed. Six new cases first failed before the
diagnostic receiver existed, then passed: exact/short/oversize streams, large
stderr with nonzero exit, timeout with child cleanup, and rate/exclusive-output
behavior. This is not a full-suite rerun or evidence of future transport success.

Before launch: independently review the exact contract/source, prefix, closure,
test evidence and cumulative budget; freeze and commit `BULK_RELEASE.json`.
Launch this script's `all-bulk` once. Thereafter inspect existing receipts only.
On failure preserve partials and reconcile a separately reviewed successor. On
success independently reconcile the entire pilot02/03/05 recovery denominator.
No recurring monitor or financial fit is started by this continuation.
