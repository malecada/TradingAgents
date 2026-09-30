# Isolated annealing and greedy-hardening checkpoint composition

The new combined.py composes the accepted normalization-checkpoint annealer and
accepted greedy-hardening checkpoint module without editing either component or
any registered production source. The scientific pair capacity remains enforced
by the scalar reference. This is synthetic engineering, not empirical release.

A composite state proceeds through annealing, hardening and completion. When
annealing ends, M is hashed directly through a C-order memory view and marked
read-only before hardening starts. The hardening component retains its row-major
first-maximum tie rule and bounded scan chunks. The caller must exclusively own
and freeze state/inputs; a read-only NumPy flag does not defeat hostile writable
aliases. The wrapper checks cached identity and ownership flags during progress;
it does not rehash the entire M before every hardening chunk. Restoration always
rehashes M against the saved hardening input identity before accepting the state.

One successful advance return is a safe boundary. The composite and active inner
component are poisoned on an escaping mutation exception. A prior valid checkpoint
can be restored; poisoned state cannot be saved or reused. Existing checkpoint
identities and partial publication directories are never overwritten.

Exclusive publication saves the nested annealing checkpoint, optional bounded
hardening JSON, then a fsynced outer manifest binding both component digests,
phase, M identity and exact normalization/hardening policies. Load verifies the
outer digest and exact caller policies, then hardening JSON identity before
numeric arrays. The annealer independently checks all three numeric files and
source/config identities. Finally M is rehashed and made read-only for hardening.
Composite schema 1 and nested annealer schema 2 are distinct explicit formats.
No old checkpoint is migrated or silently reinterpreted.

Retained annealing numeric state remains three dense float64 matrices, 24*n*m
bytes. Hardening has its separate numeric scratch allowance. Python pairs/JSON,
input graphs, callers' previous states, component validation and native temporaries
remain outside those component allowances. Publication reserves a conservative
three 64 KiB metadata/header allowance in addition to the numeric state; the hardening
and outer metadata are each capped at 64 KiB. Logical bytes are not physical disk
allocation. Final result construction allocates an int8 assignment matrix and
copies M, then uses the original scalar objective unchanged. These allocations
and final scoring remain atomic. Input/config hashes, full validation scans and
transition hashing also remain atomic. No total RSS or wall-time bound is claimed.

Five synthetic tests passed in 6.335 seconds (green02.log). Three graph-pair shapes
exercise save/load after every advance return through annealing and hardening,
including ties, no edges and a single column. Final soft-assignment bytes, hard
assignments, score, iterations and convergence agree with the unchanged scalar
reference. The old atomic hardener is patched to fail during result construction,
proving the selected pairs come from the checkpointed component. Further tests
reject policy mismatch and corrupted hardening JSON before numeric-array loading;
reject a rehashed nested M whose bytes disagree with hardening's recorded identity;
poison an interrupted hardening scan while retaining the prior checkpoint; and
retain scientific capacity and exclusive publication checks. All data are tiny
synthetic fixtures. No empirical graph/array/raw/SQLite/price or remote body is read.

red01.log preserves four pre-implementation interface errors. green01.log preserves
the first four passing tests (14.105 seconds); green02 adds the meaningful restored
matrix identity regression. Timing includes ordinary host/background activity
and is not a resource benchmark. No underlying source or registered outcome was
rerun, changed or replaced.

Independent review is pending. This does not establish arbitrary state validity,
power-loss or filesystem-race safety, whole-hub feasibility, accelerated/Torch
parity, scoring checkpointing, production ownership/admission or a financial fit.
Production integration still needs explicit source/cache/capacity lineage,
bounded resource pilots and independent release under frozen registrations.
