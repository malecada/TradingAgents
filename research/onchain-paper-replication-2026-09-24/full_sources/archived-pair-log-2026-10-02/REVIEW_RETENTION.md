# Independent retention disposition

Accepted as a narrow improvement to the reader's own buffer lifetime. The only implementation delta from preserved reader-check01.py is `del raw` after each chunk's complete event processing and before the next archive read. Event replay, metadata checks and digests are unchanged. The prior REVIEW.md remains valid for semantics; its preceding-full-chunk retention qualification is superseded only to the extent stated here.

The corrected refcount test measures before invoking pytest's rewritten assertion. Against the preserved implementation, retention-red02 reports **1 failed, 14 deselected in 0.29 seconds**, observing three references instead of the baseline two at the second fetch. Corrected check03 reports **71 passed in 1.03 seconds**. Earlier failed assertion instrumentation and logs remain retained and are not treated as a separate production defect. No checks were rerun by the reviewer.

This establishes release of the `raw` binding before the next reader allocation in the tested full/partial fixture. Fixed-size final record/body/frame objects can remain; a one-record bytes slice may alias that small chunk. The change eliminates the preceding large chunk reference held by this binding, not every possible byte-object alias. It does not bound callback/transport staging, caller-retained chunks, concurrent calls, allocator retention or global RSS, and does not prove that external storage or every reader implementation frees its buffers. No scientific or archive-owner admission scope changes.

Verified SHA-256:

- archived_pair_log.py: `50ff9d9deaf665f5953bd0a82de6c48dbf84bace0ee8bc2dde86cb3581ed3c12`
- test_archived_pair_log.py: `7399095bab35eeba48e925b4254537b3374f4d2538c89a489cb0250587d57e7a`
- preserved reader-check01.py: `707a507570f85a5f95a8a1bf5d22995aff380fae3a3c0395f0bbd0ab0f21d1a2`
- check03.log: `6c3419d2bd516ea3975969f46f0dedc52e041bce2a5d24ffc3db9e9d7938ef13`
- retention-red02.log: `2241f67f8ff66e5329db7c3e8ae3910408bb184c29f37be2a84ab8fa73a80db2`
