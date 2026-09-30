# Typed local-graph pair adapter

The snapshot adapter review identified a real boundary failure: its inherited
annealing identity called the weekly graph validator on AttributedGraph objects.
The preserved red02.log reproduces nine local-neighborhood test errors while
the seven snapshot tests still pass. No weekly metadata is fabricated for slices.

A new isolated variant supplies an explicit typed identity. Weekly snapshots
retain their validated canonical weekly digest inside a new weekly type domain.
Local slices validate the AttributedGraph contract and hash parent_hash,
center_id, exact ordered node IDs, and each array's name, dtype, shape, byte length
and exact contiguous bytes. Metadata frames carry lengths; array payload sizes
are declared. Local node IDs are required to be nonempty strings, and arrays
contiguous real integer/unsigned/float values. Node IDs are serialized in chunks
of1,024 and array bytes hashed through memoryview chunks of1MiB. No whole-array
tolist or invented source clocks/counts is used. Validation and full-input
hashing remain atomic; existing validation allocations need the outer guard.

Original accepted sources remain unchanged. derivation.json identifies the
original/new hashes. The copied annealer changes only the graph identity import
and checkpoint schema2→3; the copied composite changes only its annealer import
and outer version2→3. All numerical operations, schedule, normalization, ranking,
score and4Mpair cap are unchanged. The copied artifact adapter selects that local
composite, declares typed backend version2/checkpoint3, and adds the identity
module to numerical source fingerprints. Old schemas are refused rather than
implicitly migrated. The adapter manifest remains schema1 but exact backend and
component identities distinguish it from the snapshot-only implementation.

Eighteen tiny synthetic tests pass in green02.log(0.279seconds). The seven artifact
tests run for both GraphSnapshot and actual AttributedGraph objects constructed
by NeighborhoodIndex. They cover reference directional score parity, interrupted
publication, exact prior-reference recovery, complete-score reuse with numerical
entry points forbidden, context/orientation/policy/owner rejection, quotas,
parent provenance and primary exception preservation. Additional local tests
compare soft bytes and hard assignment/score exactly against scalar reference;
reject changed parent, center, node order, features and edge order before array
load; reject old outer/annealing schemas before numeric loading; and observe an
actual restored rank memmap closing on numerical completion. red01,red02 and the
earlier16-test green01 are retained. This is synthetic neighborhood data, not an
empirical graph or financial fit.

The artifact layer's reviewed limits and caller obligations remain: trusted exact
references, exclusively owned graphs, a separately admitted process/lease and
failed-parent ancestry, latest journal reference, cumulative retained storage,
aggregate RAM/CPU/time/disk guard and no automatic retries. The per-session
logical reservations are not physical disk or ancestor-history accounting.
Actual runtime/source declarations must be checked by admission; the tests use
fake hashes. No registered caller, dictionary/MCM consumer, Torch policy, cache,
package source inventory or empirical gate dispatches this variant yet.

Next: independent exact-derivation and boundary review, then maintained-package
promotion with registered ownership/journal/resource wiring, directional
dictionary continuation and MCM partial rows under explicit backend/precision
lineage. Full real-hub/pipeline feasibility and all1,420 financial fits remain.
