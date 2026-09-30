# Isolated scalar annealing checkpoints

The prototype preserves the scalar reference node and edge accumulation order,
normalization, temperature schedule and final hardening/scoring. Synthetic tests
exercise successful return boundaries within node agreements, edge-pair updates,
and between dense transforms. All three retained matrices are float64.

A safe-point flag is cleared before mutable advancement and restored only on a
successful return. An escaping exception poisons the scratch state. Such state
cannot be saved, advanced or converted to a result. Recovery must load an earlier
complete checkpoint. Saving validates input/configuration identity and reachable
phase/cursor/iteration/temperature combinations before creating any output.
This protects interruption consistency; it is not proof that arbitrary caller
mutation of numerical state can be detected.

Each exclusive checkpoint writes three arrays and a manifest last, with fsync.
Load checks the caller-pinned manifest and every array hash/header/extent before
loading arrays, then checks state. The caller must ensure exclusive ownership and
frozen input/checkpoint bytes. Production ownership, atomic publication selection
and outer resource-guard integration are not implemented here.

Retained numerical state is 24*n*m bytes. This excludes inputs, validation and
identity hashing, transient normalization arrays, hardening/scoring, checkpoint
serialization and caller-held earlier states. This is not a memory reduction.
Dense initialization, normalization, hardening and scoring remain atomic and are
not wall-time bounded. Original scientific capacity checks remain unchanged.
No Torch parity, financial outcome, production release or empirical claim follows.

Evidence: red01 missing module; green01 contained a read-only fixture mutation
error, corrected without changing the oracle; green02 five passes. Review A1/A2
counterexamples are retained in red02. green03 failed at import before tests due
to missing PYTHONPATH. Corrected invocation green04: seven passes in 1.423 seconds.
The full registered-hub offline verification does not cover this isolated module.
