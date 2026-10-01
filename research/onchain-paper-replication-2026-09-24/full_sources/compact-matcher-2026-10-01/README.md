# Direct compact matcher and MCM composition

`compact_matcher.py` invokes the unchanged `matching_checkpoint` engine's
`create`, `advance`, `score_only`, `save` and `close` functions. A durable begin
record precedes allocation. Successful numerical cleanup precedes the durable
completion record and callback acknowledgement. Exact original PairSession
numerical identity, score, convergence and iteration evidence are preserved.
No per-pair owner/complete directory is needed for a comparison that finishes
within the configured call grouping.

The prospective execution schedule explicitly groups `calls_per_checkpoint`
bounded engine calls before a progress snapshot. This is an operational change
from the earlier Serial runner and is recorded in IMPLEMENTATION_ASSUMPTIONS.md.
It is not adopted for empirical execution. Stable ranking within an engine call
still requires an outer process guard; operation counts do not bound its time
or scratch. Source-component hashes are pinned once under the required source
freeze rather than re-reading implementation files for each pair.

Per-pair checkpoint count/byte ceilings and the complete prospective global
checkpoint envelope are checked before allocation. Checkpoint reservations have
exclusive, retained intent records; engine state metadata and array hashes are
verified using bounded reads before and after progress publication. Fatal cleanup
failure poisons the consumer and cannot become ordinary unavailable data. A
checkpoint stop requires a separately admitted successor; no self-resume exists.
All bytes from failed/partial publication remain present.

## Evidence

- `red01.log`: five expected missing-module failures.
- `check01.log`: four failed, one passed in 0.41 seconds. The tiny fixture's
  normalization cap of two was below the existing complete-axis requirement of
  four. Test/source snapshots retained; the numerical engine was not changed.
- `check02.log`: corrected fixture, five passed in 0.39 seconds.
- `red02.log`: per-pair/global capacity counterexamples failed as intended,
  two failed/five deselected in 0.37 seconds.
- `check03.log`: seven passed in 0.38 seconds after conservative preflight fixes.
- `INITIAL_REVIEW.md`: retained late checkpoint/independent-lease findings.
- `red03.log`: reproduced both late publication findings, two failed/seven
  deselected in 0.34 seconds.
- `red04.log`: corrupted begin before allocation reproduced, one failed/nine
  deselected in 0.34 seconds.
- `check04.log`: ten passed in 0.42 seconds. Exact event readback now follows all
  external lease callbacks before allocation, progress return or completion.
- `FINAL_REVIEW.md`: independent bounded matcher acceptance, SHA
  `126d36bb4aae2b56b967f54c664c6c1d1c05de25671a0238346e5bedf7d903a6`.

The tiny direct test executes real numerical cleanup, a retained checkpoint that
loads without advancing, corruption refusal, and a synthetic cleanup exception
injected after real release. It does not prove cleanup of every OS-level failure.

## Fresh full MCM composition

`test_compact_mcm_integration.py` connects the actual scalar checkpoint engine,
compact event log, MCM score stream, retained score tails and batch publisher to
the existing array MCM kernel. The seven-node/two-motif fixture completes 14
comparisons, 28 events (4,704 record bytes in two files), and four score batches.
No progress snapshots, per-pair owner.json or artifact directories are created
in this fixture. All 14 ordered purposes and retained float64 scalar bytes match
the independent reference; final float32 MCM values also match exactly.

`integration01.log` passed in 0.60 seconds. Its test was preserved before adding
exact float64/purpose assertions; `integration02.log` then passed in 0.60 seconds
(session 5868 exited 0). These are new synthetic cases, not repeated historical
jobs or inspected financial samples. The registered native producer still uses
its original route until explicit source/policy/ownership integration is reviewed.

Independent `INTEGRATION_REVIEW.md` accepts the tiny composition, SHA
`3cc5764d7e670e040fd28420ccd8c3abdaeb1298893392ada16e35cc93e71624`.
Full-chain failure/progress handling and resource feasibility remain separate.

## Remaining executable work

Integrate the compact route through an explicit registered native backend and
producer policy; bind completed-score and checkpoint evidence into representation
closure. Validate the distinct dictionary hierarchy/directional schedule and
partial-run successor admission. Finish whole-workflow physical storage/offload
and resource bounds, large-hub caps and the cumulative reviewed gate before any
full-size resource pilot. Tiny success does not establish resource coverage,
paper-scope completion or financial-model accuracy.
