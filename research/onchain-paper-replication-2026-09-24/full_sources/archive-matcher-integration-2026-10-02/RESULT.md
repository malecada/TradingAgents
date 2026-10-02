# Actual matcher and archive writer integration

Two fresh synthetic cases call the actual CompactMatcher and checkpoint engine
with the accepted ArchivePairLog and a filesystem archive transport. Exact
scores are compared with match_reference. No numerical production code changed.

The first case completes two pairs across a three-record full chunk and a
one-record final partial chunk. The second uses operations_per_call=10 and
calls_per_checkpoint=1 to produce actual intermediate checkpoints before both
pairs complete. Retained remote event frames are decoded directly. Each actual
checkpoint tree is checked through compact_stage.checkpoint, including its
intent, numerical identity, state content and cumulative reservation. Ordered
score and checkpoint-reference digests are independently packed in the test and
compared with completion replay. Local event/upload/readback/cache payloads are
absent after successful completion; checkpoint trees remain local.

check01 retained one pass and one fixture-construction failure in 0.57s. The
fixture requested 32 checkpoints while retaining max_publications=10; production
correctly refused it. test-check01.py preserves that fixture. The corrected
fixture explicitly sets max_publications=32 and closes the log if matcher
construction fails. check02 CLOSED: two passed in 0.58s, session95269 exit0.
Independent REVIEW accepted this narrow composition; SHA-256
13c7883b73e50f588aa6b5f3cb49bf1ed5a78c00a067ced24ebdd7f73c8ce204.

The graphs have two nodes each and beta_final=1; these are explicit synthetic
settings, not changes to the registered scientific configuration. Exact score
comparison uses the maintained reference algorithm, not an independent paper
implementation. Direct remote decoding in this tiny fixture is not a production
cold reader. No MCM score stream, current-owner/stage/terminal admission, actual
network transport or OS guard is covered. Whole-workflow physical capacity and
all1420financial fits remain open. No historical claim was replayed.
