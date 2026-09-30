# Durable normalization phases in the isolated scalar matcher

This prototype combines the accepted scalar annealing checkpoint state machine
with the accepted C-order chunked normalization arithmetic. It changes no
registered producer, scientific configuration, graph array, empirical capacity,
financial outcome or historical checkpoint. The prior prototypes remain unchanged.

After Q edge accumulation completes, the previous soft assignment M is no longer
needed for that iteration. M is reused as scratch for scale, row normalization,
column normalization and exponentiation. Each successful normalization chunk
returns a safe state with its own phase and cursor. Only V, M and Q are retained:
24*n*m float64 bytes, excluding graph inputs and caller-held older states.
No fourth full matrix is retained for normalization. Native SciPy temporaries,
validation scans, hashes, arrays retained by callers and final-result copies are
not included in that allowance. No measured RSS reduction is claimed.

The arithmetic follows the existing scalar order: complete Q, scale by beta,
row then column logsumexp, exponentiate, then update beta and iteration count.
The pinned SciPy singleton-column padding rule is retained so a one-column tail
of an original wider C-order matrix keeps the reference reduction layout. The
chunk allowance bounds native normalization input elements, including padding;
it must accommodate a whole reduction axis and, for wider matrices, two complete
columns. It does not bound SciPy temporary bytes or elapsed time. A larger axis
therefore requires an explicitly supplied allowance; the default is 65,536.

Checkpoint schema 2 adds the exact normalization allowance and phase/cursor.
Save publishes the same three hashed NPY files and fsynced exclusive manifest.
Load requires the caller's allowance to match before opening any numeric array;
old schema 1 checkpoints are not silently reinterpreted. Input/config identities,
C-order float64 shapes, phase reachability, cursor bounds, beta/iteration state,
hashes and finite arrays are checked. The original max_pair_entries validation
remains active. Checkpoints are valid only after successful advance returns.
An exception after a numeric mutation poisons the state and prevents save/reuse.

Ten synthetic tests passed in 2.444 seconds (green01.log). Three end-to-end shapes
(3x4, 3x5, 3x1), with two annealing iterations and small allowances, save and reload
a unique checkpoint after every advance return. Final soft-assignment bytes,
hard assignments, score, iteration count and convergence match the unchanged
scalar reference. The 3x5 case exercises a padded singleton tail; 3x1 exercises the
original single-column path. The tests also preserve earlier node/edge boundaries,
zero-edge/tie/iteration-cap cases, tamper rejection, input/config changes, existing
identity refusal, invalid-state rejection, resource-policy mismatch before restore
and post-write exponentiation interruption. red01.log preserves the expected
pre-implementation failure (one phase assertion and three missing-policy errors).
No empirical graph, saved array, SQLite, remote body or price was read.

Limits remain explicit. Input validation/hash scans, initialization, Q setup,
checkpoint publication, final hardening/scoring and result copying are still
atomic. This is not a wall-time, process-memory, disk-allocation or crash-safety
proof for a production owner. The existing isolated hardening checkpoint module
is not integrated here. No Torch/accelerated parity, capacity relaxation, new
resource pilot, financial-fit admission or full MCM feasibility is established.
Independent review is required before further engineering use; production release
requires separate integration, source lineage, synthetic verification and reviewed
resource admission. The storage03 HEAD/source freeze is preserved.
