# Independent graph duplicate-validation review

Status: **no correctness defect identified in this bounded increment.** Review
covers the duplicate-validation delta in `contracts.py`, its new synthetic tests
and compact saved verification receipts. No tests, real data/arrays, external
calls, empirical jobs or source edits were performed by the reviewer. Only this
report was written.

## Exact rejection behavior

`contracts.py:102` first rejects nonstring or empty node IDs, preserving the
previous validation order. For admitted strings, sorting makes equal identities
adjacent, and `pairwise` detects duplicates without constructing a full Python
set. Empty/singleton sequences have no adjacent pair, as before. Unicode strings
retain their ordinary exact equality; the comparison does not normalize or alter
node IDs.

`contracts.py:81–88` lexicographically sorts endpoint pairs using the original
integer arrays. The caller validates `[2,E]` shape, integer dtype, feature-row
count and endpoint range before reaching this helper. Equality compares both
endpoints; duplicate pairs become adjacent regardless of original order. Signed
and unsigned integer values are not multiplied, packed into one integer or cast
to a narrower type, so the new algorithm introduces no pair-encoding overflow.
GraphSnapshot construction preserves the input dtype, making the int32/int64/
uint64 tests substantive.

Each iteration reads at most65537 consecutive sorted pairs and compares at
most65536 adjacent pairs. The next iteration starts65536 pairs later, sharing
one pair with the preceding block. Thus the first block compares positions
0–1 through65535–65536 and the next compares65536–65537 onward; no boundary
comparison is omitted. Zero or one edge produces no comparisons and no false
duplicate. The graph arrays are never reordered or mutated, so graph identity
and downstream edge order remain unchanged. Count, clock, finite-attribute,
aggregate and BTC/ETH conservation checks retain their prior code paths.

## Test and receipt assessment

The six dtype/permutation cases compare the result against an independent
Python pair-set oracle. A large reversed input puts a duplicate at sorted
positions65535/65536, which would fail if the block overlap were removed.
Unicode duplicate nodes are tested separately. The allocation probe forbids
module-level calls to `set` while validating a66049-edge synthetic graph; it
detects the removed allocation but is not a general allocation profiler.

`red01/child.log` retains the expected set-allocation failure plus eight passing
semantic cases. `green01/child.log` records81 passing tests in24.75s across the
new module, bounded hashing, contracts, ETH/BTC weekly builders and registered
graph production. The guard records child0, verified cleanup,26.0913s elapsed,
110,227,456 peak sampled cgroup bytes and no memory events. These are read saved
receipts, not reruns by the reviewer.

## Memory scope and remaining limits

The change removes the full Python node-ID set and one Python tuple per edge
plus its containing set. Node sorting still allocates a linear reference list
and sorting workspace. Edge sorting retains an E-length integer ordering array
and NumPy sorting workspace; only the gathered endpoint comparison block and
its boolean comparison temporaries have fixed element bounds. GraphSnapshot
copies, resident graph arrays, other whole-array validation temporaries and
downstream neighborhood/population allocations remain. This is not an
out-of-core validator, a constant-memory validator, or proof that the largest
historical graph fits current resources.

Full-sized peak memory, validation-time tradeoffs, end-to-end capacity, the
implementation owner's separate allocation diagnostic, external recovery and
empirical scientific outcomes were not assessed here. No financial or resource
pilot is released.

Independently recomputed source identities:

| File | SHA256 |
|---|---|
| contracts.py | `3946a14d65f6e7b42e76f4c409c0d08325243d74e98a98e805ba924df1bb0b32` |
| test_graph_validation_memory.py | `53b1d295af81fe3fc4d9687536be9de4a8b753247f8749bb276f094fe3243b49` |
