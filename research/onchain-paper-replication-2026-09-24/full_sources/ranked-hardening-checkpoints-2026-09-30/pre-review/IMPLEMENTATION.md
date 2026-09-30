# Isolated ranked-hardening checkpoints

This prototype retains the independently reviewed stable float64 ranking and
row-major tie semantics. It accepts only existing C-order float64 matrices on
the pinned64-bit runtime. The original4Mpaircap is passed by the study caller;
this interface does not authorize a different scientific allowance.

Creation validates the finite matrix, hashes its bytes, casts no values, and
performs one atomic stable ranking. Before creation returns, no new checkpoint
exists. A failure in sort or initial identity work requires the preceding
annealing/composite checkpoint; this module does not resume inside sort.

After creation, readonly int64 ranking and exclusive state are retained. Advance
scans at most65,536entries per call, reconstructing used-axis boolean masks from
accepted pairs. Every safe boundary may be saved in a fresh exclusive directory.
An interruption after mutation begins poisons the state. Only the previous
checkpoint may be restored; partially written checkpoint directories are kept.

Each checkpoint contains order.npy and a compact manifest with shape, original
matrix hash, policy, cursor and pairs. File/directory fsync precedes successful
publication. Restore requires an externally supplied trusted manifest SHA, exact
input identity and exact original numeric policy, verifies body extent and SHA,
then memory maps the order readonly with pickle disabled and a bounded header.
The caller must verify its frozen matrix identity independently after restore;
the string alone does not prove an external matrix's current contents.

Structural state validation rejects malformed shapes, wrong dtypes/ownership,
noninjective pairs, impossible cursor bounds, phase/count disagreements and
poisoned states. It is not a replay proof of a greedy prefix or hostile caller
mutation defense. The state, matrix and checkpoint files must remain exclusively
owned and unmodified. Trusted outer hashes and publication provenance are needed.

Explicit creation allowance17*n*m+n+m+16*min(n,m) counts key, index permutation,
finite scratch and conservatively pair/mask buffers, excluding input, Python
state/container costs, allocator/runtime and native sort workspace. Retained
numeric order is8*n*mbytes plus masks during advance. Save/load hashing additionally
uses fixed1MiB I/O chunks; metadata is capped at64KiB and NPY header at128bytes.
The logical checkpoint reservation is8*n*m+128+65,536bytes. This is not whole
process peak or filesystem allocation. A finite process guard is mandatory for
capacity-scale use. Composite integration must separately account for annealing
state plus ranking and checkpoint disk consumption; old composite limits are
not silently reused.

Four synthetic tests pass in green02.log, retaining red01 missing-module and
initial green01 history. Tests restore at every single-entry boundary, including
an initial/empty checkpoint; verify exact ordered pair parity with the accepted
ranked hardener; refuse capacities, changed policy/input, appended body data,
exclusive publication reuse and structural corruption; and simulate interrupted
mutation then recover a prior checkpoint. No matrix body from any empirical or
closed profile was read and no historical job was repeated. Production and all
registered gates remain unchanged. No capacity-size checkpoint or combined full
matching measurement has run for this module.

Next requirements: independent review, finite checkpoint resource measurement,
composition/score-only integration with explicit new memory/checkpoint policies,
backend/cache/source lineage, full reference parity and guarded real-graph pilots.
Atomic ranking-profile evidence does not by itself satisfy these requirements.
