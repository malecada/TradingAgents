# Pre-outcome independent review history

The first independent implementation review withheld approval for four
engineering gaps: completed fits existed only in memory; an inference exception
could erase already completed forecasts; strict clean-guard admission prevented
failure-only review; and only LightGBM, rather than the complete pinned runtime,
was checked before claim. These findings precede all empirical price/label
inspection and fitting. Corrective work adds claim-bound immutable fit
checkpoints, preserves forecasts on inference failure, separates failure-only
resource forensics from complete admission, and invokes the existing pinned
runtime checker. The second independent review accepted all four fixes after49 focused tests.
The final metadata/verification review then approved the exact contract recorded
in RELEASE_REVIEW.md, subject to committed remote verification and dry admission.

Metadata integration also corrected the historical failed-attempt set to four,
including the original temporal-motif attempt. The source predecessor is an
explicit enforced graph_parent, while lifecycle parent is null because that
field permits only a same-family fitted ancestry. All sixteen upstream claims
and cumulative17 remain retained; this creates no budget or sample reset.

The review found ordinary independent source decoding, D−2 clocks, common masks,
purged monthly membership, saved-model replay and paired bootstrap consistent
with the frozen scientific protocol on invented data. Synthetic correctness
is not evidence of observed prediction performance or historical availability.
