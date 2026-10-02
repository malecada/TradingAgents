# Independent admission batching review — October 2, 2026

Verdict: accepted for the bounded source-file verification change. No material
correctness regression was found in the diff against
`926fd667fbc4277408cf24c368986cd31423c22b`. This verdict does not establish an
optimization speedup or acceptance of the actual-owner integration fixture.

## Reviewed identity and method

The operative AGENTS.md, RESEARCH_START.md, current research/study state,
parallel-execution ADMISSION_BATCHING.md brief and implementation evidence were
read. The observed branch was `research/onchain-paper-replication-2026-09-24`;
HEAD was the baseline above. Review compared the actual working source with the
original source, inspected all 65 new cases and the existing lifecycle coverage,
and checked retained raw logs and snapshots independently of the implementation
conclusion. No tests or financial experiments were rerun. No registration,
ledger, source, test or historical evidence was edited.

Reviewed SHA256 identities:

- `tradingagents/research/admission.py`:
  `585d66f526d88f8488c6efcc4989a09328006e393566a596fe9e95c6c7f60cfd`.
- `tests/research/test_admission_batching.py`:
  `7cd75ca59de5fbed9ad91df20e019b64aaca39ed00094f142a6fc62998a0667b`.

All 15 entries in the existing SHA256SUMS verified. The check02 log contains
`102 passed in 4.19s`; its snapshots match the reviewed sources. The retained
red01 log contains 51 missing-helper failures, and red02 contains the null-hash
error-precedence failure with 64 passing cases. These are retained execution
records, not independently repeated executions. `git diff --check` passed for
the changed production file.

## Correctness assessment

- Admission lines 292–294 replace only the original source-files loop. The
  surrounding HEAD, ancestry, registration, charter, selection, runtime,
  history, exposure, denominator, budget and input behavior is unchanged.
- Lines 118–128 preserve worktree byte equality, the optional registered
  source digest comparison and the unconditional original-design digest
  comparison. The null expected hash still fails the original design check.
  Each body response is bound to its freshly queried object ID and extent.
- Lines 130–149 first compare the source extent with current local bytes, then
  cap body batches by advertised bytes. Lines 151–172 cap each size batch at
  128 file pairs. A pair exceeding 8 MiB uses the original per-file route.
  Source and design extents are both included in the body-byte denominator.
- Lines 83–104 parse bodies by their declared binary extent, require the body
  delimiter, reject malformed/non-blob headers and extra/truncated responses,
  and accept both 40- and 64-character hexadecimal Git object IDs. Embedded
  newlines and header-looking body bytes do not become protocol headers.
- Lines 153–165 retain local-path checks, normalized source lookup versus
  original design lookup, and the argv fallback for newline, carriage-return
  or unencodable requests. Fallback delegates to the original comparisons.
  NUL remains invalid. The source/test inspection supports the documented
  space, tab, Unicode, newline and surrogate-path coverage.
- Lines 72–80 use finite subprocess input and subprocess.run, with captured
  streams, process reaping and failure conversion. There is no persistent
  process or cross-call cache. All accumulated entries and extents are local
  to a call. The retained tests exercise fresh mutation detection and eight
  concurrent calls through a four-thread pool.

Independent comparison found changed scheduling and possible error precedence
when several files are invalid, but no path that converts one of the original
source/worktree/hash/design rejection conditions into successful admission.
As before, these checks do not provide an atomic snapshot of an arbitrarily
mutating worktree; this change does not claim that stronger contract.

## Untested claims and release boundary

The exact isolated profile03 actual-owner fixture, matched unprofiled
baseline/candidate wall time, broad named offline target and end-to-end owner
integration were not executed or accepted by this review. The coordinator's
planned isolated comparison remains necessary before reporting measured
optimization behavior. The 8 MiB limit bounds advertised body bytes per batch;
it is not a total process RSS bound, and oversized fallback retains the
original per-file allocation behavior.

No economic return, fee/funding, market-timing, data availability, financial
denominator or external-backup claim was tested. Those are outside this
source-admission optimization. No specific unresolved correctness question
requires escalation to higher effort at this checkpoint.
