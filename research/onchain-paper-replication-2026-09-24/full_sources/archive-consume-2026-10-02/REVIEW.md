# Independent archive consumer disposition

ACC1 is closed. Accepted for the bounded additive receipt-bytes consumer with disposal limited to its own freshly downloaded cache file. REVIEW_INITIAL.md and the original source remain preserved. This disposition checks the narrow correction and retained tests/logs; no tests or external actions were rerun.

Final attempt closure now invokes `_close_attempt` with the original directory device/inode and in-flight exception. It closes the original descriptor once. On uncertainty it raises the shared BaseException CleanupFailure, preserving the primary cause when present and otherwise chaining the close error. A separately opened descriptor must match the original namespace identity before recording cleanup-failed.json and a missing failed.json. That new ownership is closed once; the ambiguous original descriptor is never retried. Evidence-writing or fresh-close failures become diagnostics on the fatal error. Durable markers cannot be guaranteed if the filesystem/namespace is unavailable; the fatal return still prevents ordinary continuation.

The retained cleanup-red01 result is **2 failed, 18 deselected in 0.26 seconds**, reproducing ordinary OSError escape after both successful disposal/completion and an existing content failure. Corrected check03 reports **56 passed in 0.87 seconds**: 20 consumer cases plus 36 archive/transport cases. The new tests inject an error after the real original close, verify shared fatal propagation, cause preservation, cleanup/failure markers and correct completed-versus-incomplete state. They exercise ambiguous final-close handling, not a genuinely still-open original descriptor, namespace-unavailable marker failure or every inherited I/O cleanup path.

The original accepted content boundaries remain: bounded canonical trusted receipt bytes and hash, explicit expected scope/endpoint/member, exact downloaded extent/hash, exclusive cache attempt, final metadata/root/inventory checks and immutable returned bytes. Only payload.bin in this call's owned cache is deliberately removed after verification. Late failure may retain completed/failure receipts and remote evidence after cache disposal; it does not promise restoring disposable bytes. Old source/preservation directories and local-only owner/stage/terminal readers are unchanged.

Caller obligations remain scientific eligibility, actual guarded finite transport, cumulative metadata, parallel calls, retained return buffers, staging and whole-workflow physical/RSS limits. This does not admit original-source eviction, archive-backed scientific ownership, remote availability or empirical execution. No existing-source disposal or network transfer occurred in this review.

Verified SHA-256:

- archive_consume.py: `9cfa242b77e42c2385e3c4cb8e51086965cc7d42768f2c52364fa3fd4ec77dc5`
- test_archive_consume.py: `f1666f5fc41423197a0cf7bfea5a9ada0b65a34aab4ca40158fe629fff4f29c9`
- check03.log: `16a7a7291551088f5882ccd7c4ccd2b19bc7d2122d53376128d4d93d98a21430`
- cleanup-red01.log: `40f5c91c74972a01766cdee3bbc5808e0a34ba786ef2166445a531852cd5fee7`
- preserved consume-check02.py: `d86b66232e88b02432e3fdb2eaefd918af5b6ae622094f3be24b20f7be552b90`
