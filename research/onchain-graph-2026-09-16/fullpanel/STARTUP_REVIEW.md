# Independent startup review

Observed at 2026-09-22T10:30:39.144018+00:00. Startup compute identity and retained day evidence
are consistent. A material final-checker serialization defect was found and
must be corrected explicitly before closure. The live extraction was not changed
or stopped; no raw data was decoded or numerically recounted by this review.

The Data checkout HEAD and committed claim both identify
`fdb33cf27ca97b8d32926f046be422d8b8b45b6f`. The claim's committed registration, all
54 source bindings, 6 lifecycle-runtime bindings and
1285 input bindings were independently verified at
2026-09-22T10:27:23.799545+00:00. The live launch PID 2182802,
start ticks 6170009 and boot ID `7efe60e3-fabc-4267-8881-15dfec9f3450` match the preserved observation.
Only one matching launch and one compute runner were observed. The runner and
active independent daily-check child have affinity CPUs 0 and 1. The launcher
monitor itself retains the wider host affinity; the frozen guard applies the
two-CPU restriction to the compute process tree and samples aggregate RSS against
8 GiB. The resource receipt remains empty and no terminal exists: neither a clean
exit nor a final resource verdict is claimed.

At this snapshot, 3 source days and 2 graph days have immutable
published outputs and passing independent daily reports:

| Date | Source rows | Graph status | Independent count |
|---|---:|---|---|
| 2022-01-01 | 1,180,989 | unavailable | False |
| 2022-01-02 | 1,158,900 | complete | True |
| 2022-01-03 | 1,209,173 | complete | True |

January 1 is the registered missing-prior-boundary exclusion. January 2 and
January 3 passed their daily independent count checks. Each observed daily report
matches its embedded output, frozen plan and checker SHA. Source-row metadata,
prior-output/audited-prefix chain, retained compressed-prefix byte hashes, exact
copied/original append receipt bytes and transaction stream digest agree. Each
published day's cleanup receipt binds its output and scratch manifest; its new
temporary array directory is absent. The exact-hash scratch remains present and
continues growing. This is append/preservation evidence, not a completed global
uniqueness audit. No array or raw-capture modification was performed by the review.

## Required closure correction

`check_final.py:178` reconstructs the phase with `json_bytes(phase)`. Fresh
`source.activity.in_degree_histogram` and
`source.activity.out_degree_histogram` originally have integer keys. The first
sorted JSON serialization orders those keys numerically. The runner reloads this
JSON and publishes its retained phase with string keys; reserialization orders
those strings lexically. Original and reconstructed byte lengths match, but the
hashes differ. The startup metadata check raised AssertionError at this comparison;
the frozen final checker was not executed and has no empirical failure report.

For every observed day, converting exactly those two known maps back to validated
integer keys reproduced both the original independent phase SHA and the retained
scratch-manifest SHA and byte length. Exact original, incorrect lexical and
restored hashes are retained in startup-review.json. The correction must preserve
the strict comparisons, apply only to fresh source (`source_reused == false`),
and keep string-key serialization for old JSON source reused from the pilot.
It requires a separately bound checker correction and meaningful synthetic
integer/string-key tests; changing the frozen Data checkout or suppressing the
phase check is not warranted. The source extraction, daily independent reports,
append population and cleanup manifest do not depend on this final-review
serialization reconstruction, so the finding does not require compute replay.

No full raw-store hash scan, global identity recount, exhaustive stars/triangles,
canonical-chain proof, historical publication proof or financial evaluation was
performed. No conclusion about full-panel success follows from this startup.
