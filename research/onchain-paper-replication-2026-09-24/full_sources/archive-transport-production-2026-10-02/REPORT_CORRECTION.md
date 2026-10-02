# Cleanup correction following independent review

This report supersedes incompatible acceptance/cleanup implications in REPORT.md;
that initial report, source/test snapshots and successful checks remain historical
evidence. REVIEW_INITIAL.md identified ATP1 (receiver cleanup/publication) and
ATP2 (upload descriptor cleanup). Initial source success was not accepted.

The receiver now captures any primary failure and independently attempts process
group kill, direct-child wait, bounded stderr drain, stdout close, stderr close
and output close. The existing score_batches fatal cleanup helper attempts each
action once even after a BaseException. Uncertain cleanup raises CleanupFailure
and chains the original primary failure. Raw descriptor integers are never
retried. Output cleanup precedes success receipt publication; cleanup uncertainty
instead produces a failed receipt. Receipt-write failure preserves an existing
failure with a diagnostic note. The upload source-directory and sealed-memfd
closes use the same existing primary-aware one-shot cleanup contract.

New regression tests inject uncertainty after the actual local operation has
occurred, avoiding leaked test children/descriptors. Receiver injections target
kill, wait, stdout close, stderr close and output close, both with and without a
primary oversize failure. Each case requires all independent owned cleanup
attempts exactly once, a failed receipt, no published destination and a retained
primary cause where applicable. Upload tests cover directory and memfd close,
with and without a source/upload primary failure; spent payload reservations
remain charged. A diagnostic publication failure test requires the original
oversize error and its diagnostic note to remain visible.

- `review-red02.xml` and `review-red02.log`: CLOSED, exit 1, 15 failed,
  24 deselected, 0.78 s. All newly injected paths reproduced ATP1/ATP2 or primary
  loss during diagnostic publication against the retained initial source.
- `check03.xml` and `check03.log`: CLOSED, session 94153, exit 0, 44 passed,
  1.28 s. Includes all 39 new-module cases and five predecessor cases.
- `git diff --check`: exit 0. Source/test hashes and corrected snapshots are
  in source-manifest02.json, source02.py.txt and tests02.py.txt. The initial
  source-manifest.json, source01.py.txt and tests01.py.txt remain unchanged.

Both invocations use the REPORT.md reviewed offline environment and arguments.
The red run selected the new production file only, with
`-k 'cleanup_is_fatal or close_uncertainty or diagnostic_publication'` and distinct
review-red02 XML/log destinations. The green run used both modules exactly as
check02, with distinct check03 XML/log destinations. Shell redirection retained
stdout and stderr together; no repeated run was performed merely to acquire logs.

Limits remain: local children do not establish actual SSH interoperability or
remote availability. A process-group kill request and successful direct-child
wait do not independently prove descendant termination; the outer guard owns
full cleanup verification. Failure-path cleanup wait is separately bounded at
ten seconds. The caller must serialize shared transport/budget access; concurrent
reservations and publication were not validated. Lease, guard, source/admission,
physical accounting and producer/owner integration remain external obligations.
No external transfer, credential read, empirical operation or acceptance gate
change occurred. Independent final review remains required.
