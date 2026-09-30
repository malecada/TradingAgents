# Isolated resumable greedy hardening

The scan preserves float64 casting and strict first row-major maximum selection.
Each advance processes at most a declared number of chunks, each at most 65,536
entries. A complete finite-value scan precedes selection. Sparse output pairs
remain in greedy choice order. Synthetic parity includes rectangular ties,
int64 values that become equal after casting, noncontiguous arrays and emptiness.

Safe state is returned only after successful advancement; an escaping exception
poisons scratch state. Recovery reloads a prior complete hash-pinned checkpoint.
JSON checkpoints use exclusive files, file fsync and parent-directory fsync.
Partial files are retained and never overwritten. State structure, injectivity,
phase/cursor and best-entry eligibility are checked. Caller mutation of the
numerical history is not independently reconstructed.

The caller must externally verify and freeze the matrix body identified by the
provided SHA. The component compares the provided identity and metadata; it does
not hash matrix contents itself or establish concurrent-owner exclusion. Numeric
scratch accounting is 48*min(n,m)+64*min(chunk,n*m), excluding input residency,
Python state/sets/lists and JSON serialization. The checkpoint allowance counts
logical bytes, not filesystem allocation. Operation chunking is not a measured
wall-time guarantee. No dense assignment is returned.

Five synthetic tests pass in 0.100s. The missing-module red01 is preserved.
Independent review accepts isolated engineering only. No production integration,
resource-capacity override, registered trial or financial result is implied.
