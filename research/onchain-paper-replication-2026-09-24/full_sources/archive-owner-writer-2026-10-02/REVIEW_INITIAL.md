# Initial independent review

Disposition: acceptance withheld for AOW1. Source, contract, tests and saved log were inspected read-only; no test, transfer or research job was rerun.

## AOW1 — constructor parent descriptor uncertainty remains an ordinary exception

`tradingagents/research/onchain_replication/compact_pair_log.py:88` closes the parent directory with raw `os.close(fd)` after creating the matching namespace, before installing the writer's root descriptor. This path is inherited by the actual `ArchivePairLog` constructed at `archive_owner_writer.py:66`. If that close raises, the assignment to `log` has not completed. The wrapper can preserve and fail the reservation and poison the owner, but its `_abort` cannot identify this unresolved descriptor: the original ordinary `OSError` is re-raised. An ordinary producer-unavailable handler could therefore continue despite cleanup uncertainty. If another error was already in flight, raw close also replaces its exception chain.

Use the shared fatal, primary-preserving cleanup contract for this owned parent descriptor, once only, and preserve the old source identity. A fresh actual-wrapper regression should inject this constructor boundary and require fatal cleanup, retained claim/namespace, poisoned owner and released original transition lock. An injection after a real close demonstrates exception propagation, not recovery of an actually leaked descriptor.

## Source and evidence assessment

The new wrapper captures the actual lock, thread and callback lifetime; uses internal ledger methods under that transition; selects the real owner/stage policy; and pins the original source inode and start records. Completion checks the exact or bounded-count stage contract. After the writer performs its remote replay, the wrapper completes the reservation and rechecks the pinned local archive and owner/ledger evidence without an extra remote read. The existing public ledger completion wrapper delegates to the extracted internal body.

The saved `check01.log` closes with **4 passed in 157.66 seconds**. The positive fixture executes nine real tiny matcher pairs against the scalar reference and exercises 18 event records split into 16 and 2 records (2,688 and 336 bytes). Other cases cover callback failure, terminal metadata corruption during reservation completion, nested public transition refusal and expired callback leases. These four cases do not exercise the constructor cleanup finding, wrong-thread callback use, early callback-issued writer closure, or every fatal cleanup path.

The callback's returned values are caller-owned. This is current-owner reserved event-archive execution, not scientific checkpoint/score-stream admission, stage sealing, producer selection, transport metering, post-owner-close reuse or financial admission. The fixture mocks the OS guard and uses filesystem transport; no network or actual resource guard result follows. Remote bytes are verified during writer replay, not continuously after it. Reservation amounts remain conservative spent allowances rather than measured transfer or disk usage.

Inspected SHA-256 identities:

- `archive_owner_writer.py`: `b13ba512752abd8d9370775e94273f268b2e0b2a15324bdfcbbc11fde109d622`
- `archive_owner_operations.py`: `5882578d065e94af588511356071b8f575aa1e8a1bbd7a9ab116e5853eb4c83f`
- `test_archive_owner_writer.py`: `11cc64be57841fb87d9dbb3783c489c2dd41a6d7de288668d1b7b0ce81a6a6ba`
