# Cold archived event verification

archive_pair_reader.verify implements an explicit cold read of a successfully
closed ArchivePairLog. Expected completion hash, owner, full scope and archive
policy are mandatory. Original source metadata and ordered manifest chains are
checked before a fresh read claim. Every event chunk is fetched and replayed;
the complete event result must match the trusted writer completion. Source and
new consumption metadata are checked again after the final callback and after
publishing the read completion. The original source namespace remains read-only.

## Retained checks and corrections

- red01: 17 missing-module failures in 0.38s before implementation.
- check01: 112 passed in 2.57s, session2595 exit0 (17 reader, 95 prior archive).
- REVIEW_INITIAL withheld acceptance for APR1–4: an uncertain source close lost
  the original explicit failure cause; late source failure markers did not stop
  the next transfer; owner lease needed refreshing immediately before a new
  claim; and a four-record metadata margin omitted some failure records.
- reader-check01.py and test-check01.py preserve the initial implementation and
  fixture. review-red01 reproduced five failures, 17 deselected in 0.59s.
- Corrections preserve the primary cause under fatal cleanup, check source and
  attempt failure markers after every lease, refresh lease and full source
  checks immediately before claim, and reserve eight fixed metadata records
  beyond three per possible consumed chunk.
- check02: 117 passed in 9.55s, session68256 exit0 (22 reader, 95 prior archive).
  Every earlier failed log remains retained. No historical job was replayed.
- REVIEW_FINAL independently accepts APR1–4 and this bounded scope; SHA-256
  1274180206dbbc07900c6075465e2ca9e5421014edba78d7e576470c2c4a071f.

Cases cover full/partial chunks, unchanged source hashes, fresh-attempt replay
refusal, incorrect trust/policy/allowances, changed source receipt/manifests,
dangling failure markers, missing/corrupt remote bytes and final callback
mutation/revocation. Tests use the actual archive writer/consumer/event verifier
with a fresh synthetic filesystem transport. The cleanup regression raises
after actually closing the descriptor; it does not simulate a kernel leak.

## Remaining boundaries

This is event/manifest verification only. Generic scientific-stage checkpoint
and score-stream joins, current-owner/publication/terminal selection and
retention of large score/checkpoint objects remain. The old local route is
unchanged. Logical metadata allowances, a bounded chunk and the 10GiB floor are
not physical reservations, measured RSS or cumulative remote transfer budgets.
Transport, actual guard, concurrency and the total number of read attempts are
caller obligations. Original source metadata stays locally required; this is
not recovery after losing the entire local manifest tree. No actual network
request, empirical source eviction, fit or resource-pilot admission occurred.
