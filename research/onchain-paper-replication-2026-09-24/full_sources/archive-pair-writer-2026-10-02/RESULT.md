# Archive-backed compact pair writer verification

The additive ArchivePairLog writer preserves the original event format and
keeps the latest acknowledged chunk local until the next append. Sealed chunks
are copied, read back, linked into an ordered manifest and disposed only after
checks of their original descriptor identity and content. Completion consumes
every archived chunk again and verifies the complete event stream. Only payloads
newly created by this writer are eligible for disposal; earlier empirical data
and existing local reader contracts are unchanged.

## Retained checks

- red01: 15 missing-module failures before implementation.
- check01: 86 passed in 1.33s.
- terminal-red01: two duplicate-terminal regressions failed against the saved
  writer-check01.py. Early terminal refusal corrected the defect.
- check02: 88 passed in 1.45s.
- REVIEW_INITIAL identified APW1–5: late acknowledgement mutation, constructor
  cleanup before identity setup, replacement-inode disposal, failure markers
  and uncertain owned child-descriptor cleanup.
- review-red01: seven failed, 17 deselected in 0.52s against writer-check02.py.
- check03: 95 passed in 1.55s, session88212 exit0. This includes 24 writer cases
  and the 71 prior archive component cases, not the full offline suite.
- REVIEW_FINAL independently accepts APW1–5 corrections; SHA-256
  968618155e1332ad9e86e35f410258d8a9a7d55b5a5f084f4fa942109a8064bb.

All earlier failed output and source snapshots remain. Synthetic filesystem
transport supplied the archive in these tests. No actual network transfer,
empirical source eviction, financial fit or new pilot occurred.

## Limits

The prebound chunk count and metadata allowance include seven retained metadata
files per chunk plus a fixed margin. The 10GiB free-space floor is enforced, but
logical allowances are not physical quotas or measured whole-workflow bounds.
Archive policy, transport and live authority are supplied by the caller. Failed
attempts cannot reopen; a failure after permitted disposal does not recreate an
already removed local payload. Checks are sampled filesystem boundaries.

This component does not admit a current owner or a scientific stage. Actual
matcher integration is recorded separately in archive-matcher-integration-
2026-10-02. A cold manifest reader, integrated checkpoint and score-stream joins,
explicit owner/terminal selection and cumulative resource accounting remain.
