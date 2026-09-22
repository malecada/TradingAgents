# Interrupted full-panel checkpoint review

The completed checkpoint passes compact integrity review: 206 source dates
through 2022-07-25, 205 graph dates, and 234,828,370 checked source rows.
The 2022-01-01 graph exclusion is expected. There are 890 dates remaining,
2022-07-26 through 2024-12-31, within the unchanged 1,096-date,
1,221,389,903-row denominator. This approves preservation and exclusion of
completed dates from re-extraction; it does not approve a successor launch or
claim full-panel numerical admission.

Evidence is recorded in [interruption-review.json](interruption-review.json).
The execution checkout remains at
`fdb33cf27ca97b8d32926f046be422d8b8b45b6f`. Its launch boot
`7efe60e3-fabc-4267-8881-15dfec9f3450` differs from the observed boot
`6690623b-3299-42d4-8d7b-0847268fbe0c`. The 18:47:25 Prague process
snapshot contained no full-panel compute/review worker. The old resource file
has zero bytes and no terminal or independent-review receipt existed at initial
inspection. The reboot interrupted ownership; the original identity is not
safe to replay. OOM cause is undetermined. The user's report includes other
concurrent processes and does not establish that this research job caused it.

All 206 calls to the original final checker's `verify_daily`, loaded with the
approved phase-v2 serialization correction, passed. These checked retained
daily output/check identities, the frozen plan and daily-checker hashes,
reconstructed phase hashes, preceding-day links, 593 retained prefix shards
(138,497,531 stored bytes), cleanup records and deleted-array manifest links.
The hash review independently reconciled 412 receipt/intent copies, global day
indices 0–205, contiguous per-bucket offsets and the 256 physical bucket sizes.
The exact extents total 7,514,507,840 bytes; there is no day-0206 hash intent or
unexplained bucket suffix. Hash bucket bodies were not opened.

## Actionable finding and recovery conditions

**P1 — Exclude unpublished July 26 prefixes from the execution seed.**
[day.py:109](../fullpanel/day.py#L109) creates the day's retained-prefix directory
with `exist_ok=False`; [day.py:152](../fullpanel/day.py#L152) publishes prefixes
before graph computation and phase publication. Three July 26 prefix shards
(663,131 bytes) already exist outside scratch. Copying the entire artifacts
tree into the successor would collide at the first remaining date; treating
these shards as completed evidence would admit an unchecked partial result.
Preserve all three with old evidence, but seed only the 593 prefixes referenced
by the 206 completed outputs. The initial inventory assertion exposed these
three extras after all completed-day checks passed.

The July 26 scratch contains 112 partial source files (85,447,212 bytes):
110 event shards and two compressed transaction-hash shards. No phase, daily
check, daily output, cleanup record, or hash append intent supports completion.
Preserve this scratch separately without incorporating it into admitted reuse.

The failure-only closure must preserve claim/output bytes and the empty original
resource receipt, record an interruption with unknown cause, and append exactly
one failed terminal through the reviewed lifecycle path. The consumed 14/14
allowance and exposed interval remain in history. A new one-use 15/15
continuation requires committed admission and independent review.

The new execution seed must preserve the exact 206 output/check/cleanup/hash
receipt bytes and original relative prefix paths. July 26 must bind the original
July 25 output SHA and checked prefix. The original plan and numerical source
remain frozen. Hash day indices 206–1095 belong in a fresh root; the old root
remains immutable. Final admission requires a separately reviewed exact global
union check across both roots and the full denominator, without duplicating
bucket bodies. Repeat the process-ownership check immediately before launch.

## Claims not tested

This review reused the original compact verifier; it did not independently
reimplement graph counting or rerun raw-day reconstruction. Deleted arrays,
raw capture integrity, exact global hash uniqueness, exhaustive full-day
star/triangle counts, canonical-chain provenance, historical availability,
prices, model accuracy and financial returns were not tested. Prefix bodies
were decoded only for retained compact consistency. Partial scratch and global
transaction-hash bodies were not decoded or counted.

Interrupted resource-limit compliance, OOM causation, new launcher capacity,
external raw backup, the failure-only terminal, successor registration and
union checker remain outside this completed checkpoint review. No higher
effort is warranted for the checked compact checkpoint; the specific next
correctness review is whether the successor preserves all original checks
while reconciling hash segments across the two roots.
