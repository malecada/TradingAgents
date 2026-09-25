# Retained ETH backup continuation 03

This is a finite byte-preservation continuation, not an empirical research claim.
The user reported newly available RAM on September 25. Initial MemAvailable was
about 10.1 GiB; the current boot differs from all prior backup attempts and their
owned cgroups are absent. Reconciliation evidence is retained separately.

The verified continuation02 pilot (149 files, 517,291,351 raw bytes, batch0) is
reused at its original location and contract hash. Its archive digest is checked
again remotely before release. No raw pilot is repeated. The first failed upload,
the successful pilot, and the failed bulk02 startup remain unchanged.

Exactly 194 remaining batches cover 58,934 files / 103,007,197,692 raw bytes.
Each bundle is freshly source-hashed, uploaded, downloaded and member-verified.
Only successfully verified generated temporary tar copies are removed. Originals,
failed partials and all receipts remain. The new remote identity is
`research-backups/onchain-paper-replication-2026-09-24/raw-retained-ETH-03`.
Recovery of the full inventory requires both the original pilot02 and new03.

Limits: one bundle at a time; 512 MiB raw/bundle; 2 GiB temporary allowance;
256 MiB memory.max; 192 MiB memory.high; zero swap; 3 GiB host runtime reserve;
4 GiB startup reserve; 20 GiB local free-space floor; two-CPU affinity;
8 MiB/s transfer cap; 256 GiB remote floor plus planned phase occupancy.
Thirteen phases have at most16 bundles each, <=8h per phase, <=48h cumulative.
The controller stops on the first failure. No automatic retry or old identity
relaunch is permitted. Estimated bulk duration remains28.69h, or43.04h with the
1.5 planning margin; this is a one-bundle extrapolation, not a guarantee.

The new transfer's payload ceiling is245 GiB. A conservative all-attempt ceiling
is249 GiB, retaining2 GiB for each earlier pilot and zero for bulk02 (no worker
released). SSH protocol overhead is excluded. The measured prior guard times
remain spent:242.812704s +518.698803s +14.566215s; adding the new48h ceiling gives
173,576.077722s. Financial trial accounting and all1,420 pending fits are unchanged.

Before launch: review the exact contract, candidate, code, pilot and failed-parent
receipts; freeze `BULK_RELEASE.json` and commit the reviewed preparation.
Only the new script's `all-bulk` command is allowed; `pilot` is rejected.
During execution, inspect existing `bulk-controller/intent.json`, phase guards,
per-batch completion receipts and logs. Do not invoke the command a second time.
After failure, preserve partials and reconcile a separately reviewed successor.
After success, independently verify the combined pilot02/new03 denominator.

The preparation has23 synthetic test passes (8 new reuse-admission cases and15
preservation tests). Historical full-suite evidence remains pinned separately.
No synthetic tests should compete with the active transfer.
