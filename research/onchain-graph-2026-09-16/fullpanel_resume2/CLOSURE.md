# Full-history graph extraction — verified result and preservation

The second continuation completed at 2026-09-23 18:35:02 UTC from frozen source
`87b6ac39d12a4f9a2ac1832f34f68647c52c53c8`. Independent final verification
passed at 21:10:08 UTC. Neither computation nor the final checker was replayed.

The complete denominator is 2,193 cells and 1,099 outputs: 1,096 source days,
1,094 graph-feature days and the global uniqueness cell. Only January 1, 2022
and December 31, 2024 have the registered graph-boundary exclusions. The
independent two-root identity check verified 1,221,389,903 distinct full
transaction hashes, no duplicates, and all 1,096 daily sorted streams.

Compute took 23h32m40s; final verification took 612.79 seconds and peaked at
5.03 GiB cgroup memory. Both guards exited zero with verified cleanup and no
OOM counters or limit stop. The compute guard's 86,839 memory.max reclaim
events remain visible; they are not recorded OOM kills. These outcomes do not
establish the cause of the earlier reboot.

## Complete compact-evidence preservation

The September 24 import preserved 8,432 files / 1,033,405,844 bytes, including
8,429 new files and three existing unchanged files. The exact intent and result
are in [full-import-20260924](full-import-20260924/result.json). All retained
source and destination sizes and streaming SHA256 hashes matched. The set
includes all 1,099 outputs; 7,314 retained artifacts comprise 1,096 daily checks,
1,096 cleanup receipts, 2,930 prefixes, 1,096 append intents and 1,096 receipts.
Run claims/terminals, compute/review resources, logs and ownership metadata are
included. No raw bodies or transaction-hash payload were copied into Git.

An independent read-only preservation reviewer repeated all 8,432 source and
destination checks, exact report/terminal membership and source/guard binding.
No material discrepancy or omitted execution evidence was found. The two older
archives also matched all 1,744 and 1,747 recorded files. All 206 seeded daily
outputs matched their frozen bytes, and the excluded first-continuation hash
directory remained empty. Original stores and frozen checkouts were unchanged.

Durable SHA256 identities:

| Artifact | SHA256 |
|---|---|
| Independent report | ba2cab064b463a924eba402429f6eaee4308dd1e5d003ae2db33b53812481f4e |
| Compute terminal | 6cfbe0ecf07c6a1d7d1de9c41ef6b9e0134b7fef547fba38e29d7cba2814b2e9 |
| Panel | a43eed74519c45757e58f11ad03bcdb00a609fcad80236cb8ad5c4ca7069a7b7 |
| Review guard | ef61f8eaa50fc7bfd8925fcfc7d77d370a57a1608ab2e127d35b11e29103e433 |

Remote preservation is recorded separately after pushing and verifying the
exact Git commit; the local import receipt itself makes no external-backup
claim. Raw stores and both populated hash roots remain on the same physical
NVMe device, without a verified off-device full raw backup.

## Interpretation and continuation

This result supports computational feasibility of the declared daily feature
pipeline across 2022–2024 under the stated checks. It does not prove historical
publication, canonical-chain completeness, exhaustive independent full-day
star/triangle recounts, paper replication, forecast accuracy or profitability.
Deleted intermediate arrays were not reconstructed at closure.

All 16 lineage claims, including failures, remain consumed and preserved. The
user authorized the fixed matched M0/M1/M2 comparison as the next step. Its
new charter/gate, exact source/input bindings, independent admission and offline
checks must precede any observed price/label decoding or fitting. No neural
follow-up or trading is authorized by this numerical result.
