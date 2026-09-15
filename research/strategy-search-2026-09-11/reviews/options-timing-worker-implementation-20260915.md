# Timing successor worker — completed synthetic engineering checks

Scope: isolated, unadmitted `research_options_timing` preparation. No market requests, financial runs, release, grant or real claim changes occurred in this worker task. The old capture package and its historical policies were not edited. The new Journal and transport copies are byte-identical to their old counterparts.

Hourly Journal slots now have acquisition release `N+2000` and absolute deadline `N+5000`. Validated nominal-time lookup preserves entry selection, own-exit inclusion, longer-asset benchmark coverage and economic action/freshness clocks. The worker uses the explicit deadline rather than adding five seconds to release. Selected acquisition follows known acquisition and entry selection immediately, within the same remaining three seconds. Bootstrap, daily and final calendar contents and all 17,144 slot identities remain unchanged. The assignment requires successor target `options-timing-20260915`, protocol schema 3 and exactly 2,000 ms hourly delay. Host/data remain externally anchored; production literals are enforced by the separately owned release builder.

A restart after durable immutable selection can attempt untouched selected slots before the original deadline. A consumed initial known group without immutable selection fails the source episode without retry or replacement entry. No economic rejection is implied.

## Frozen capture source hashes

| Module | SHA-256 |
| --- | --- |
| schedule.py | `55126e0830166a98c6d30f837516ef68f4d5281e1aee645cd2bf68e5e3de5c18` |
| worker.py | `340dc23251f50b35a3c69bc91ce4644c15facea9c416fafa376a5edcadc0c19a` |
| transport.py | `0c96d542101a5455c8674b76ac8f2964de66ed28b09cafb69bbc82ce197e8b4e` |
| journal.py | `0ceebb774e33a1f9faffaaf0c58769dc30bfc65acbb0b12dc82e596b22b02bdd` |
| adapter.py, owned separately | `17fb1a79d08ce4f13957e8a210b6a58bdafa899ace54cf65251b2521b970bc6a` |

## Checks and retained failures

The checkout-local Python 3.13.13 ran 28 synthetic worker/schedule tests successfully under the reviewed 120-second, 512 MiB sampled aggregate RSS, two-CPU guard: 24.200 seconds, peak 94,838,784 bytes. Tests cover all calendar clocks, unchanged nonhourly sources, early acquisition refusal, original deadline enforcement without child creation after expiry, actual adapter selection/recovery, remaining-window use after 2,900 ms known acquisition, late selection failure, both interruption boundaries, old target/protocol rejection, source hashes, isolation, locks and resource ceilings. See `options-timing-worker-tests-20260915-final-guard.json`. The initial transitional bootstrap test failure used the old namespace in the separately owned copied bootstrap; subsequent tests passed after its namespace update.

The resource proof passed in 40.102 seconds, peak 238,030,848 bytes. Exact serialized maximum-body arithmetic remains within the 2 GiB logical policy and the existing conservative 8 GiB regular-file allocation envelope at 4 KiB blocks. Full known and selected journal caches, validation and seals were measured together. A 5 MiB, 10,000-row invented metadata fixture required 1.831 seconds for local entry preparation, leaving 1.169 seconds of the three-second acquisition allowance. This excludes HTTP latency, real transport child creation and VPS storage measurement; known and selected groups remain sequential. It does not establish that the production window will succeed. Filesystem metadata, unrelated writers and runtime/release files remain outside the regular-file allocation bound. See `options-timing-resource-20260915.json` and its guard report.

The first full-lifecycle synthetic proof reached its 120-second guard. Its copied fixture represented known and selected raw timestamps as overlapping despite sequential worker calls. This is an engineering-fixture limitation, not a capture-runtime defect. That fixture, progress, attempts and guard remain preserved under `options-timing-episode-20260915*` and `/tmp/options-timing-full-episode-kf1jnuy0`. It was not used as the stronger chronology proof.

The corrected proof advances the fake clock by 300 ms per acquired group. Entry known retrieval is `N+2300`, selected controller start is `N+2300`, and selected request is `N+2500`; both retain deadline `N+5000`. Its unchanged source package completed the entire 1,057-hour calendar through fixed final histories and global source seal using three controlled segments: 120.017 seconds (timeout), 120.041 seconds (timeout), and 114.496 seconds (pass), total 354.554 seconds compressed computation. Each resume inventories prior bytes, advances beyond the maximum prior intent deadline and never retries consumed slots. These segments exercise interrupted recovery; they do not extend any source window or the 120-second per-operation production watchdog.

The final audit accounts for all 17,144 receipts: 17,133 received, three unavailable and eight missed; 4,375 completed synthetic requests and 12,758 post-exit unused receipts. All 225 daily and four final requests completed. No attempt repeated across segments and all prior members remained unchanged. Missing/interrupted slots remain in the denominator. Final segment peak RSS was 174,596,096 bytes. See `options-timing-episode-20260915-v2-resume2.json` and all preceding v2 guard/progress/inventory records.

Fixture: `/tmp/options-timing-full-episode-yktcby37`, with package/data subdirectories. Assignment SHA-256: `441584fbd0648469251e52d3494cd2aba078529102b0c37e26e6a61f3d29df68`. Global source-seal SHA-256: `52ea0611ccaac96555b52a3a84adb44a30c15dc082ccaa15204d8dbbc9c5de63`. Proof script SHA-256: `cb7b0504e271b448eb968884a43c95f3d7ad1b1bca82ab97105b2d84bdfebd8f`.

Independent returned-source normalization, financial-engine synthetic integration, real-history preservation/admission review, deployment and any prospective episode authorization are separate coordinator-owned steps. These engineering results establish neither usable live observations nor an economic edge.

## Persistent inert synthetic archive

All 38,686 package/data regular-file members were archived locally without executing or extracting them. The 24,296,328 member bytes were independently streamed back from the archive and compared with the exact pre-archive member inventory; a second input inventory proved source preservation. The complete member manifest and archive are stored under `/home/malecada/master_thesis/research-deployment/options-timing-20260915/synthetic/`. No VPS copy occurred in this task. Archive construction and verification passed the same guard in 9.854 seconds, peak 97,787,904 bytes; see `options-timing-synthetic-archive-20260915-guard.json`.

- Archive: `options-timing-synthetic-20260915.tar.gz`, 1,070,390 bytes, SHA-256 `54f38f5c87ed3adfd9a4c64e03a59272b129e4ebed75fe2bf8dc0873803c18eb`.
- External member manifest: `options-timing-synthetic-20260915.members.json`, SHA-256 `6d5d239116cf1065bbea41068e7feb8c6a8212827adf688cbb8a6bcde1cc17e0`.

The archive has relative `package/` and `data/` file names and regular-file entries only. It contains invented fixtures, not real market observations or deployment authority. The manifest is external to the archive and binds its hash plus every member's bytes and hash. Archive checks enforce the fixed package inventory and the complete source/journal denominator; authoritative source semantics remain covered by the separate returned verifier. The local persistent copy does not establish an off-host recoverable backup.
