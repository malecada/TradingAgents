# Hardlink retry guard-precedence correction

Candidate01b46a84d625fafdd6146fb2ab7a06a669ee4f881c370c64c58a4b2b65087da96b
is preserved unchanged and WITHHELD. Independent review identified a material
precedence defect: an eligible hardlink could raise ChangingTree before observed
logical/allocated lower bounds were checked. A later smaller sample could therefore
hide a breach already visible to the discarded attempt. The original failed Git
fetch's cause remains unknown; this finding concerns candidate01 correctness.

The new watcher changes only initial/rejoin check ordering:

- Initial regular-file size remains immediately fatal when over4MiB. Its observed
  size is then added to logical usage; both logical and allocated caps are checked
  before classifying a hardlink as a retryable observation.
- Rejoin computes the original maximum-of-endpoints logical and allocated
  corrections, then checks both caps before a hardlink can trigger a retry.
  No observed size is refunded or omitted. Original counters remain intact.

The successful full-sample requirements, zero-link refusal, owned-fetch objects
scope, canonical path/type/device checks, file/member/depth/disk limits, receiver
caller predicate and every POLICY value are unchanged. The entire census retry
function is AST-identical to candidate01: three attempts, at most two100ms waits,
shared five-second limit. No new retry, cap, sleep, waiver or scheduling route.
The receiver982b51c67e7f7088d7bdd02de7f35c3bf720fcd7d7deed77c400dd78bca4224d
and owned_io09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb
are copied unchanged solely as candidate context. Their old fixed literals remain
non-release bindings; Root owns any actual fresh receiver integration.

## Bounded proof

Main .venv/bin/python -B runs eight unittest methods: the six existing focused
checks reused against the new watcher, plus one changed-counterexample method
and one exact inverse/unchanged-context check. All pass.

The changed counterexample uses actual temporary hardlinks and real filesystem
sizes/allocated blocks. At both initial and rejoin observations:

- logical witness: a linked4B file is observed under a3B cap; the retry callback
  removes its alias and shrinks it to2B;
- allocated witness: the observed file block exceeds the directory baseline plus
  4095B cap; the retry callback removes its alias and truncates it to zero blocks.

The withheld watcher incorrectly accepts the smaller second sample in all four
witnesses. The corrected watcher reports the whole logical/allocated cap failure
immediately, with zero retry requests and the original4B/two-link file still
present. These are two required counters at the two modified seams, not a new
broad regression matrix. Raw counterexample rows are retained in TEST_OUTPUT01.

The reused six checks cover original hardlink RED/new transient GREEN, persistent
internal/external alias refusal after three attempts, strict pre/post/out-of-scope
refusal, oversize and zero-link immediate refusal, exact caller source context and
actual child4MiB RLIMIT. The unchanged prior watcher/receiver inversion assertion
still concerns candidate01's original delta; the new inverse independently restores
candidate01b46 from candidate02121a and reconstructs candidate02 forward exactly.
No numerical packages, Git operation, network, Admission, Owner, ResearchRun,
claim, live source or runtime mutation occurs. The only child runs the original
source-defined file-limit function against a disposable temporary file.

No final-test failures occurred. The prior candidate's passing checks did not
cover this lower-bound precedence defect and are not represented as acceptance
of candidate01. No named offline inventory or historical matrix was changed.

## Release limits

Candidate02 watcher SHA256:
121a443011f6a95f6e5ec84fedd6a06c51e328d1d317cdf445b77ef192b20795.

All changes reside in this new directory. Source01, its tests, original receiver,
withheld Root drafts and failed recovery evidence remain intact. Root must obtain
independent review of candidate02, bind a genuinely fresh receiver and perform
any authorized actual recovery. This evidence establishes the check-order fix,
not the cause of the historical fetch failure, network success, external recovery,
continuous writer exclusion or research/launch authority.
