# Initial independent sampler-proof review

Acceptance is withheld pending proof-content consistency checks and corrected
negative-test evidence. Source and saved logs were inspected read-only. No test,
job or numerical file was opened or executed by the reviewer.

**PR1 — selected-neighborhood and retained-prefix claims are not joined to the
actual samples.** route.py:96 only format-checks selected_indices_sha256.
Lines 100–104 accept any strictly increasing retained byte sequence with the
correct final total. Self-consistently changing either field, rehashing the draw
chain and file references, and supplying the resulting expected proof hash can
therefore admit false evidence. After artifact admission, derive each local
graph's ordered indices in its admitted parent and compare the selected-index
digest. Sum actual local array nbytes for every prefix and compare each retained
count. This requires no weighted draw or RNG replay beyond the existing state
audit. Add counterexamples with a wrong selected digest and a wrong intermediate
prefix, preserving the correct final total and every surrounding hash link.

**PR2 — registered sampler limits are not validated or applied.**
route.py:44–50 checks outer policy fields and metadata caps but does not inspect
policy.limits. Validate the same kernel/neighborhood schema as the producer,
require the admitted training-center count and direct-weight arithmetic to fit
their registered bounds, and require actual retained prefixes to fit the
registered sample allowance. A completion proof should not claim success outside
its own registered sampler contract. These checks concern contract arithmetic,
not a new measurement of RSS or full-scale resource feasibility.

The route-check01 log is closed with five passes and one failure in 70.221
seconds. Its incorrect-RNG negative failed in the test's global np.empty mock
while retrieving PCG64.state at route.py:84, before reaching the corrupted draw.
This is not evidence that the RNG refusal is ineffective, but neither does it
verify that refusal. Forbid sample-materialization/array-reader entry instead,
or distinguish constant-size RNG internals from population arrays. Preserve the
failed test and log. The RNG audit may claim no weighted redraw or population
weight arrays, not zero NumPy allocation of any kind.

The inspected Metadata class correctly retains the admitted cap with each
snapshot and reuses that cap for subsequent leases. Its synthetic 512-reference
metadata fixture and actual tiny production under a registered larger cap do
not establish full 512-draw sampling or peak resource feasibility.

Inspected source SHA256:

- route.py: `23549937218bcf407f0aa4b08a32357eea789fb730a1f2774c54046dbbdcba98`
- producer.py: `f5703eea849b94707c750695f1bdd97512ed428e39033b013420043568762305`
- test_route.py: `47fed661068d56c77957ea9c48486b1b13818b1f102654af17763ab84ad34bd9`

Full weighted-choice recomputation, historical continuation, dictionary-driver
enforcement of this proof, full-scale measured resources and empirical release
remain explicitly outside this review. They are not presumed implemented.
