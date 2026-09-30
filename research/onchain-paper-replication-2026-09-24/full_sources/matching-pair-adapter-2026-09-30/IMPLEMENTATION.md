# Isolated ordered-pair checkpoint adapter

This implements the single-pair artifact layer identified by the independent
integration audit. Production consumers, registered matching policies, source
inventory, empirical gates, dictionary and MCM are unchanged. It is not a
registered research runner and loading a reference never admits a new owner.

The explicit backend descriptor names CPU scalar float64 affinity, SciPy float64
normalization, stable row-major ranked hardening, sparse float64 scoring and
composite checkpoint schema 2. Ordered left/right graph identities, configuration,
workflow namespace, source commit, runtime hash and four numerical component
source hashes form the identity. This is deliberately distinct from Torch's
float32 score output. Registered source/runtime verification remains a caller
obligation; synthetic tests use explicitly fake context hashes. No compatibility
with a different source commit/backend or historical production cache is implied.

Each session reserves a new exclusive directory beneath an existing nonsymlink
root. Progress publications save the accepted composite state and publish a
compact manifest last. A completed score is retained separately and can be
restored without loading arrays or entering create/advance/score again. A successor
records its exact parent reference and owner in both ownership and publication
metadata. It does not choose a newest directory, follow parent ancestry, prove a
failed ResearchRun relationship or overwrite/reopen a prior session. Admission,
lease ownership, latest accepted journal reference and cumulative ancestry must
be enforced by the forthcoming registered adapter/journal integration.

The caller owns graph/state objects exclusively. Numerical advancement and
publication failures poison and close the session; failed directories remain.
Secondary cleanup failure is attached to the primary exception. Recovery takes
an explicit prior trusted reference into another exclusive session. Completion
closes the numerical state and retains the immutable MatchScore value. The layer
does not emit dense assignment or soft matrices.

Policy binds composite state/normalization/ranking limits, sparse scoring limits,
per-checkpoint bytes, publication count and total reservations. Each session
reserves 64 KiB for owner metadata and max_checkpoint_bytes + 64 KiB for every
attempted publication, including failures and compact score publications. The
reservation is conservative and checked before creating a publication directory.
It is a logical per-session bound, not physical disk allocation or a cumulative
parent-history bound. Outer process RAM/CPU/time guards, host reserve/free disk,
retained parents, graphs and output arrays still need aggregate admission.
Atomic validation/hash/sort/scoring/fsync operations remain subject to the outer
finite guard; operation counts are not maximum wall-clock intervals.

Seven tiny synthetic tests pass in green02.log (0.165 seconds). They verify
directional scalar-reference score/convergence/iteration parity after progress
restore, completed-score reuse with all solver/load entry points forbidden,
orientation/config/source/runtime/namespace/owner/policy/hash rejection before
array loading, exclusive names and count/byte refusal, retained interrupted
publication with explicit prior recovery, exact parent provenance, and primary
exception preservation when cleanup also fails. red01.log, green01.log and
red02.log remain. The two errors reproduced by red02 (missing parent provenance,
secondary exception masking) were corrected; the prior source/test bytes and
hashes remain in pre-correction/. No empirical body or historical computation
was opened or repeated.

Next: independent review of this bounded layer; then maintained-package promotion
and registered journal/admission wiring, dictionary directional continuation and
MCM partial-row continuation with explicit precision/cache namespace. These later
steps, full real-graph capacity and all 1,420 financial fits remain unfinished.
