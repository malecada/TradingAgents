# MCM durable-score callback integration

Maintained `mcm_score_stream.py` derives the existing MCM workload identity from
the actual graph, ordered dictionary, matching configuration and scalar backend.
It validates each exact row/motif occurrence and typed graph purpose before
dispatch, then saves the returned float64 score durably before the callback
returns. Completed bounded tails are copied to ScoreBatches and linked by an
immutable seal chain. No tail or historical pair artifact is deleted.

Every seal callback return verifies the retained tail, link and destination after
all external lease callbacks. Stream completion validates the complete batch
chain, every retained tail/link and exact inventories without executing another
numerical comparison. This is bounded-memory, sampled verification under the
sole-writer/source-freeze contract, not an atomic filesystem snapshot. It adds
content reads whose cost must be measured in a future admitted resource pilot.

## Synthetic evidence

The tests build a fresh seven-node synthetic fixture with two dictionary motifs
and execute the existing array MCM kernel. All 14 comparison purposes match the
reference workload in order. Retained float64 scalar values match the independent
reference callback's saved values byte for byte; final float32 7x2 MCM values
also match exactly. Four chunks are produced. These fixtures are not historical
job reruns, empirical data or paper-scale capacity evidence.

- `red01.log`: three expected missing-module failures in 0.52 seconds.
- `check01.log`: three passed in 0.55 seconds.
- `INITIAL_REVIEW.md`: withheld acceptance for late callbacks altering prior
  child artifacts and a test that initially checked only float32 parity.
- `red02.log`: three late-mutation counterexamples failed, three deselected,
  0.73 seconds; session 51331 exited 1. Original source retained.
- `check02.log`: six passed in 0.85 seconds; session 16877 exited 0. Includes
  exact float64 bytes, late batch/link mutation, incorrect occurrence refusal,
  and failure propagation from an injected callback RuntimeError.
- `FINAL_REVIEW.md`: accepted the corrected bounded adapter, SHA
  `73c78ea16cf9e9b9c2a61b690b988d6d25b0e5fc33792eb55438104872ab2e58`.

The injected error is labeled a synthetic cleanup failure; it does not exercise
actual PairSession cleanup. The numerical callback retains responsibility for
iteration/convergence, progress checkpoints and fatal cleanup handling.

## Next required implementation

The production native producer still selects the original Serial/per-pair journal
route. The new adapter therefore has not yet removed its growing dictionary of
completed pairs, file count or constant per-pair reservations. Next implement an
explicit compact completion route that retains matcher convergence/iteration and
source/policy evidence, while preserving failed/progress artifacts and admitting
bounded prospective live scratch/offload behavior. Verify actual matcher cleanup
and numerical parity, then integrate the new route through registered ownership
and source/policy declarations. Dictionary fitting's directional/hierarchical
schedule is distinct; this MCM-only adapter does not implicitly replace it.

Full physical workflow reservations, large-hub capacity amendments, successor
rules and the reviewed committed cumulative resource gate remain prerequisites
to the full-size pilot. Resource coverage and all financial fits are unchanged.
