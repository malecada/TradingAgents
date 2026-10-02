# Independent initial archive consumer review

Acceptance withheld for ACC1 below. Source, test bodies and closed evidence were inspected; no tests, SSH actions or numerical jobs were rerun. The component remains additive and no old archive/owner reader is replaced.

**ACC1 — final descriptor cleanup bypasses the failure contract.** `archive_consume.py:80` closes the owned attempt descriptor in a finally block outside the failure handler at lines 75–79. If this close fails after the success body, the caller receives an ordinary OSError, complete.json remains present, the cache has already been deliberately disposed and no failed.json is attempted. If a primary operation already failed, the close error can replace it. This contradicts the explicit late-failure receipts/failure guarantee and bypasses the repository's fatal cleanup-uncertainty convention.

Add narrow final-close regressions after both a successful body and an in-flight failure. Preserve the original cause, propagate the shared fatal cleanup type, and never retry an ambiguous old descriptor number. If a failure marker needs writing after that close, use a fresh attempt descriptor pinned to the original directory identity and retain any marker/cleanup failure without losing the primary evidence. The existing unlink-failure test does not cover this boundary. No broader rewrite of inherited I/O helpers is requested.

Other inspected boundaries are consistent with the stated scope: receipt bytes are immutable, capped and hash-bound; canonical exact schema, explicit expected scope, endpoint/member and positive bounded extent are checked before download. Only a fresh exclusive cache path is disposable. Post-download and post-verified callbacks are followed by exact metadata/inventory/content checks. The payload is read to immutable bytes, its identity is rechecked without an intervening external callback, and only payload.bin in the pinned owned attempt is unlinked. The post-completion callback is followed by metadata/root/inventory and returned-byte verification. Successful cache disposal is not original-source eviction, and failures after disposal do not promise restoration of those intentionally disposable bytes.

check02.log reports **54 passed in 0.84 seconds**, combining this consumer with earlier archive/transport coverage. The consumer has 18 cases. They exercise retained immutable-byte success, four sequential synthetic reads without the original preservation directory, receipt/scope/endpoint/extent/floor preflights, corrupt/foreign/symlink/revoked downloads, verified/completion publication mutations and unlink failure. check01 retained one assertion error because a correctly refused symlink raised OSError outside the expected exception tuple; only that assertion was broadened. The corrected result does not prove ACC1, real external consume integration, cumulative memory/disk bounds, scientific source eligibility or archive-backed compact owner/terminal admission.

Caller obligations remain aggregate metadata growth, parallel calls, retained returned buffers, transport staging, finite transfer/guard budgets and remote availability. Returning one capped immutable object per call is not a whole-workflow RSS or storage bound. Existing remote copy evidence does not itself authorize any original-source deletion.

Inspected SHA-256:

- archive_consume.py: `d86b66232e88b02432e3fdb2eaefd918af5b6ae622094f3be24b20f7be552b90`
- test_archive_consume.py: `009aa72709753898527748365320a12ee3a09455173f7775ecb0ff858dde05cc`
- CONTRACT.md: `332d1ff5f5ba79b820beb300815e0ed3e424d385bc53dee51729e08381d842fb`
- check02.log: `45b93e8d343ade2dd242db29e960ec8e21faaf4ad0a86088a2b66c1470c12a4a`
