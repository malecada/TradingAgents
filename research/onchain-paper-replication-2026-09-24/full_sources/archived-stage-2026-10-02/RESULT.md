# Archived scientific-stage content joins

An explicit archived_stage.verify route now joins cold archived matching events
to actual local checkpoint trees and complete retained MCM score streams.
The old compact_stage functions remain unchanged. Optional verified-event
visitors in archived_pair_log/archive_pair_reader retain their existing return
schemas and default behavior when no visitor is supplied.

The stage creates a fresh attempt outside its source. Actual progress frames
are checked against checkpoint intent and state content, including pair purpose
and numerical identity, before recording a 40-byte event/reference. A subsequent
bounded scan binds every checkpoint tree to its reference by ordinal. The
ordered reference hash matches cold replay. MCM score tails and batches are
fully checked, including ordinal/purpose/value equality with matching events.
Final post-publication callbacks are followed by complete local source-manifest,
new-read receipt, reference-file, checkpoint-tree and score-stream checks.
Scientific and archive policies are privately frozen before external callbacks.

## Retained verification

- red01: 15 failures in 0.91s for missing stage/visitor APIs.
- check01: 15 passed in 13.26s, session87267 exit0.
- check02: 142 passed in 57.46s, session26932 exit0, including previous archive,
  actual matcher integration and unchanged local-stage checks.
- Initial independent review identified AS1: reconstructing progress identity
  from checkpoint intent omitted its join to the actual archived event. AS2:
  callback mutation could change the policy serialized into intent after its
  original hash/allowance was computed. Initial source/test snapshots remain as
  stage-check02.py and test-check02.py.
- review-red01: four failed, 13 deselected in 8.04s. Two counterexamples rebuild
  valid fresh archived event chains that reference a real checkpoint for a
  different purpose or identity; separate cold verification succeeds before the
  scientific join is tested. Two callback cases mutate scientific/archive
  policies. Original source evidence remains unchanged.
- Corrected check03: 146 passed in 64.53s, session18140 exit0. This includes
  17 archived-stage cases, two visitor cases, 117 prior archive cases, two actual
  matcher/archive cases and eight unchanged local-stage cases. No full offline
  suite claim is made. All failed output and snapshots remain.
- Independent REVIEW_FINAL accepts AS1/AS2 corrections for this content-join
  scope; SHA-256 6e8be268ed88f040fef80c8b40461d1d4b393baad803e30e656baaede5174110.

The stage fixture executes actual tiny dictionary/MCM and checkpoint engines.
Only the fixture constructor explicitly selects ArchivePairLog; production
generic readers are not monkeypatched. A first advance is limited to one
operation to produce an actual intermediate checkpoint; later calls use the
fixture's schedule. Scientific production parameters are unchanged. Transport
is a fresh synthetic filesystem store. Counterexamples include corrupt state,
valid but wrong scores, foreign checkpoints, extra files, wrong denominators,
late source/read/reference/score/state mutation and budget refusal.

## Scope still open

This verifier returns execution_admitted=false. Explicit current-owner,
publication and terminal selection/source binding remain unimplemented for the
archive route. Checkpoint and score payloads remain local. Whole-workflow
physical/transport/concurrency/resource accounting and scientific budget/hub
amendments remain required before a resource successor. Remote bytes are checked
during cold replay; post-publication verification does not promise continuous
remote availability. Original local archive manifests remain required. No new
external request, empirical source eviction, financial fit or pilot occurred.
