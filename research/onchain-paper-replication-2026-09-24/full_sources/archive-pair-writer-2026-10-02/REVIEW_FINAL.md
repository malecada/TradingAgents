# Independent final review

Accepted for the bounded fresh archive-backed PairLog writer contract. APW1–5 from REVIEW_INITIAL.md are resolved in the inspected source. Earlier reviews, failed checks and source snapshots remain evidence; this disposition does not replace them. No tests, empirical jobs or remote operations were rerun by the reviewer.

## Corrections

- **APW1:** After the last external append check, the writer verifies the captured event count, head, state, original chunk descriptor/identity, exact final record bytes and extent, stable descriptor/path signatures and root. The added live callback can no longer corrupt that acknowledgement unnoticed. This is a latest-event acknowledgement check; full earlier-event replay remains at chunk sealing and completion.
- **APW2:** `close()` now establishes the opened root's identity when inherited constructor failure dispatch occurs before subclass setup. The failure writer also tolerates an uninitialized archived counter. Both post-start write and lease failures preserve the primary exception and close the opened root in the targeted evidence. Partial constructor evidence is not converted into a successful claim.
- **APW3:** The original chunk descriptor remains owned through sealing, round-trip copying and disposal. `_owned_chunk` joins original identity, regular single-link extent and pathname signatures before and after reads and immediately before deletion. Copy payload signatures are also pinned across the mapping callback. Equal-content substitution of the original chunk is refused and retained. This remains a sampled boundary contract, not atomic exclusion of an adversarial concurrent filesystem writer.
- **APW4:** Every archive check rejects existing or dangling root failure and cleanup-failure markers after its external lease, before further acknowledgement or disposal. Both dangling-marker counterexamples are covered.
- **APW5:** Newly opened child-directory descriptors use shared fatal one-shot cleanup. The targeted error after a real child close propagates `CleanupFailure` rather than ordinary `OSError`; the writer records failure. The regression does not simulate an actually leaked operating-system descriptor or exhaust all inherited I/O failure sites.

The prior early terminal guard remains outside the abort path. Repeated finish/fail against a successfully closed writer therefore refuses without altering the successful namespace.

## Evidence and scope

The saved review-red01 log reports **7 failed, 17 deselected in 0.52s** against preserved writer-check02.py. Its failures correspond to the acknowledgement case, two constructor cases, replaced inode, two dangling markers and child cleanup. The corrected check03 log reports **95 passed in 1.55s**: 24 writer cases plus the 71 prior archive checks. Initial check01 and duplicate-terminal check02 remain separate retained evidence. Source delta and test assertions were inspected independently of these summaries.

The positive fixture uses actual event encoding/state replay and a synthetic filesystem transport. A full three-record chunk remains local through its latest acknowledgement, is archived before the next chunk is opened, and a final two-record partial chunk is archived at finish. Successful completion re-fetches/replays the archived chunks and joins their metadata chain and exact inventories. Failure cases exercise corrupt/missing-quality remote data, changed local evidence, callback revocation and publication conflicts. Successful disposal applies only to newly created chunk/cache payloads; immutable receipts remain. Failure after an authorized disposal does not promise to restore already disposed local payloads.

The successful metadata count remains seven files per chunk: mapping, disposition, two copy receipts and three consumption receipts, plus bounded fixed metadata/failure margin. Finite chunk count, bounded record reads and the 10GiB floor do not establish a filesystem quota, measured physical/RSS peak, transport staging bound, global parallelism bound or future remote availability. Caller aliases and external callbacks/transports remain outside the local allocation claim.

No actual CompactMatcher/checkpoint-engine integration, checkpoint-body verification, score-stream join, registered current-owner/stage admission, source-policy admission, restart/reopen route or real network operation was tested in this component's suite. The old local writer/reader is unchanged. No historical source eviction, financial experiment or whole-workflow capacity is admitted.

## Inspected SHA-256

- archive_pair_writer.py: `c714c350f372be1b4e3c7840b5187deb7f72ee80549edfed4e48450e2d0ca052`
- test_archive_pair_writer.py: `991546a03e2a54ec3ad653619a3989084c403e9e096dacca7b16576505a120c4`
- CONTRACT.md: `0a68e56691cc356782b9e8b886bac5f49f5f45aacf074927d89973cc6601dea7`
- writer-check02.py: `5cf6d79032347b0928ef5aa58af8d7647e2ddac993d1ceeafb87af80f868590c`
- review-red01.log: `31e24faa924b31b0f1b435898b4b3e817a7fcae2538b7014831c9feda396c638`
- check03.log: `df3389753c8164f9a869b48316ee49c0143b6eb2fb2a443f41a2f04b884457fe`
