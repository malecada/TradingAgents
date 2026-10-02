# Archived compact event replay verification

An explicit archive-aware reader now replays the unchanged compact event format.
The actual synthetic PairLog emits one full chunk and one partial last chunk,
including two pair completions and one checkpoint reference. Both chunks are
preserved and consumed through the real archive helpers after only the disposable
synthetic originals are removed. Full semantic state agrees with prior local
replay; independent struct/hash arithmetic checks ordered scores and checkpoint
references. Successful download cache payloads do not remain locally.

- red01:14absent-module failures0.30s.
- check01:70passed1.01s (14event cases plus56archive/transport cases), accepted
  REVIEW63d55b82ccb8d4ef24b144e5001f3a0112939b443dd3892efe8879a0eec417ac.
- Review noted the loop retained its previous full chunk until the next read
  returned. Original source remains reader-check01.py.
- retention-red01:1failure14deselected0.25s. Initial assertion rewriting itself
  added a temporary reference; check02 preserved1failure70passed1.06s even after
  a one-line release. Source/test snapshots reader-check02.py/test-check02.py.
- Corrected measurement occurs before assertion. retention-red02 on the original
  source reproduces one extra reference:1failure14deselected0.29s (3 versus2).
- Release the prior raw chunk reference after processing. Final check03:
  71passed1.03s. This verifies only the reader's own previous full-chunk reference,
  not caller aliases, transport allocations or RSS. Record/body/frame references remain
  bounded small values; an entire one-record slice may alias its168Bchunk.
  Narrow REVIEW_RETENTION accepted SHA0a3c6625e8f595f0755514c239b256ade8d61470f61f980a99b4dc2f6cf227eb.

No current-owner, actual checkpoint-tree or MCM score-stream join is admitted.
The semantic state machine is reused from compact_pair_log; agreement with the
local replay is not an independent algorithm oracle. The fixture covers one
small two-pair/progress log, not empty/large logs or every final-lease failure.
Caller provides genuine bounded/guarded retrieval, trusted manifest/scope and
cumulative resource accounting. Old local writer/readers and empirical files are
unchanged. No new network operation or financial sample exposure occurred.

Next implementation: fresh archive-aware sealed-chunk writer/manifest, followed
by actual checkpoint/score-stream joins and explicit current-owner/terminal
selection. Success of this reader does not authorize eviction under old receipts.
