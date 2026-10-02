# Final independent review

Accepted for the bounded current-owner reserved archive-writer execution contract. AOW1 is resolved; no further material blocker was identified in the inspected scope. This disposition follows independent source, test, retained-log and SHA-256 inspection. No checks, transfers or research jobs were rerun. `REVIEW_INITIAL.md` and the prior source/test/log evidence remain preserved.

The correction at `compact_pair_log.py:89` captures the in-flight exception and closes the constructor's parent directory once through the shared fatal cleanup helpers. A failed close now raises `CleanupFailure` even before construction returns a log object; an existing primary remains its cause. The wrapper's failed reservation and consumed owner are retained, and its captured transition lock is released. The change does not retry a possibly reused descriptor number. The actual constructor regression injects an error after performing the real close, so it establishes fatal propagation and preservation, not recovery of leaked kernel descriptors. Simultaneous constructor work failure and close failure is supported by the inspected primary-aware branch, but is not separately exercised by this new constructor test.

`archive_owner_writer.run` derives the archive policy, scope and limits from the actual admitted ledger/owner/stage; holds the captured owner transition; and restricts its callback lease by thread, lifetime and lock identity before and after ledger callbacks. The actual writer executes its own full remote-event replay. Exact stage pair counts or the explicitly admitted capacity count mode are checked. Original root inode, start, archive-start, terminal and archive-completion hashes are then rejoined after reservation completion callbacks using local source checks, ledger evidence and callback-free current-owner verification. This incurs no additional remote replay. Public ledger completion remains a lock-taking wrapper around the extracted internal body. A callback that finalizes its writer early is refused; the completed archive and failed reservation survive without reopening.

## Evidence

- Original `check01.log`: **4 passed, 157.66 seconds**. The positive actual-owner fixture executes nine tiny real matcher calls against the scalar reference, yielding 18 event records in 16- and 2-record chunks (2,688 and 336 bytes). Its other cases cover retained callback failure, late terminal-metadata corruption, nested public execution refusal and expired callback leases.
- `review-red01.log`: **1 failed, 1 passed, 5 deselected, 76.37 seconds**. The constructor close exposes AOW1; the final snapshot close already propagated fatal cleanup.
- Corrected `check02.log`: **42 passed, 349.14 seconds**. The selected population comprises seven reserved-writer cases, ten local compact-pair-log cases, 24 archive-writer cases and one public ledger finite-population regression. This is not a full repository or financial verification run.

The final seven writer cases include the original four, both constructor/final-snapshot close injections, and early callback finalization refusal. The close tests verify retained spent reservation, owner poisoning and release of the original transition lock. Wrong-thread use is refused in source but has no dedicated case in this selected writer suite. This fixture does not exercise the capacity-mode count branch or all possible cleanup combinations.

## Scope and limits

The receipt proves this bounded current-owner event-archive execution and its local evidence joins. Callback return values are unvalidated. Scientific checkpoint-tree and score-stream joins, durable sampler/dictionary provenance, producer/publication selection, stage sealing, whole-owner terminal dispatch and post-owner-close reuse remain separate. The wrapper does not meter individual transport operations. Conservative reservations are spent allowances, not measured remote transfer, physical storage, total memory or runtime requirements.

The actual ResearchRun/Binding/Owner fixture mocks the OS guard and uses synthetic filesystem transport. No network transfer, empirical outcome, financial job or actual guarded deployment is established. Remote content is observed during the writer's replay, not continuously thereafter. Mutation after the last sampled verification is not excluded. No timing, cashflow, fee/funding or financial-return claim was tested.

## Exact inspected identities

| File | SHA-256 |
|---|---|
| `archive_owner_writer.py` | `b13ba512752abd8d9370775e94273f268b2e0b2a15324bdfcbbc11fde109d622` |
| `archive_owner_operations.py` | `5882578d065e94af588511356071b8f575aa1e8a1bbd7a9ab116e5853eb4c83f` |
| `compact_pair_log.py` | `4c65ca7f8caf46760eeef23e2bd44e9bc87a64a54bb18a862662be2b15da0089` |
| `archive_pair_writer.py` | `c714c350f372be1b4e3c7840b5187deb7f72ee80549edfed4e48450e2d0ca052` |
| `archive_pair_reader.py` | `11aedf0b9e5e8698831854952033f36db185c0cb4948f226912731ffc68d16df` |
| `test_archive_owner_writer.py` | `75021bab6fbb1f77f0bf9e238dc8ef87adb7cdac4a770c4088403d114a4ed18f` |
| `CONTRACT.md` | `9882850bdedd87a81739429831bfb65c531a63fe2acb2ad883ce9e07f0212b66` |
| `check01.log` | `ffab596ade0cecc8b2fce97fd9c5038c079a0fb2ccec987a5d0f13e0c2c9e348` |
| `review-red01.log` | `f338f258c454ea73adab6bb2554f4f493d3ea55782ad2d5c9f96274a58eba6ed` |
| `check02.log` | `81d4aa2d57903c1949c0a1535a47735fb096c92e4e4c76edb93df97e2d217702` |
| `pair-log-check01.py` | `de8f5544d1689029b05e9e7978506dd8597da5e930308d1f1ae1c2788fffe860` |
| `writer-check01.py` | `b13ba512752abd8d9370775e94273f268b2e0b2a15324bdfcbbc11fde109d622` |
| `test-check01.py` | `11cc64be57841fb87d9dbb3783c489c2dd41a6d7de288668d1b7b0ce81a6a6ba` |
