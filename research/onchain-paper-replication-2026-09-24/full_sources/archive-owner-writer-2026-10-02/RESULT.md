# Actual archive writer under a current-owner reservation

archive_owner_writer.run now executes the maintained ArchivePairLog under an
actual stage's durable writer claim and the captured owner transition lock. The
registered selection supplies scope, event/iteration bounds, archive policy and
transport. The callback lease checks thread, lifetime and lock before and after
owner callbacks. A completed writer is locally rejoined to its original inode,
start, archive-start, terminal and archive completion after reservation callbacks.
No additional unreserved cold replay is performed.

Callback values remain unvalidated. Exact stage pair counts or the admitted
capacity mode are enforced, but scientific checkpoint/score joins, producer
publication and terminal owner dispatch remain separate. A completion receipt is
not an empirical admission. Failure preserves the log, reservation and primary
cause and poisons the consumed owner. A refused duplicate leaves prior claims
unchanged. Public ledger completion retains its lock-taking wrapper around the
extracted nonlocking body used by this already-owned transition.

## Retained verification

- red01 CLOSED4missing-module failures53.29s/session36732exit1.
- check01 CLOSED4passed157.66s/session17785exit0. Actual tiny matching under a
  fresh ResearchRun/Binding/Owner matches reference scores for9pair calls and
  produces16+2event chunks. Callback failure retains the actual log and claim;
  post-completion owner callbacks cannot change source evidence unnoticed; nested
  execution and expired leases refuse. The fixture explicitly freezes the full
  matching configuration with beta_final1; production scientific values are unchanged.
- Independent REVIEW_INITIAL SHA256
  967ce9600b239a378e12075595a4facd48f98b79504228c7699d383c1b0a8b4e
  found AOW1: the inherited PairLog constructor parent-directory close could
  escape as ordinary OSError before the wrapper received its log object.
- review-red01 CLOSED1failed1passed5deselected76.37s/session57607exit1. The actual
  constructor path exposed AOW1; a final snapshot close was already correctly
  fatal and preserved completed/failed claim evidence. These injected exceptions
  follow real closes and do not demonstrate recovery from leaked kernel fds.
- Original PairLog/writer/test sources remain retained. The constructor close
  now uses the shared one-shot fatal cleanup helpers, preserving any primary
  exception; descriptor numbers are never retried. A separate case refuses a
  callback that finishes its writer early, preserving its completed archive and
  failed operation claim.

All transport is the synthetic filesystem implementation. OS guards are mocked
by the actual-owner fixture. No financial outcome, historical job, external
transfer, full scientific producer or current/post-owner-close seal is executed.

check02 CLOSED42passed349.14s/session86947exit0: seven reserved-writer cases,
ten local pair-log cases,24archive-writer cases and the public-ledger full
writer/read population regression. This is a focused profile, not the full
legacy suite. No active process or source freeze remains.

Independent REVIEW_FINAL accepted AOW1 closure within the stated scope, SHA256
f49dddefe8c85306deb6298e6864300c0eb3a20caec7bdf8584432324a9c28f3.
