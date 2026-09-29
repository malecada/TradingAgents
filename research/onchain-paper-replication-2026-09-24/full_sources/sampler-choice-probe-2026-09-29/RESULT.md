# Weighted sampling storage feasibility

The pinned NumPy2.3.0 choice implementation builds a cumulative probability array,
normalizes its final entry, draws one uniform value and searches to the right.
Source: [NumPy2.3.0 _generator.pyx](https://github.com/numpy/numpy/blob/v2.3.0/numpy/random/_generator.pyx).
A synthetic probe preserved the existing NumPy float64 sum/divide/cumulative-sum
order using mapped arrays instead of changing the probability calculation.

All6,400 sequential choices across15 cases matched exactly: chosen center,
selected probability bytes and PCG64 state after every draw. Candidate counts
257,4097,131071; seeds11,23,37,53,71; maximum512 draws per case. Deterministic
synthetic overlapping neighborhoods zero selected mass and halve neighbor mass.
No graph, paper input, financial outcome or historical job was read or rerun.
The probe took7.99 guarded seconds, peak sampled49,618,944bytes, child0 and
verified cleanup. These small cases do not establish full-fold memory or speed.

This is algorithm feasibility evidence, not a production implementation. A safe
integration still needs admitted scratch policy, disk reservation, exclusive
retained workspaces, failure evidence, finite-weight validation, graph-level
sample-manifest parity and interruption handling. Existing raw graph residency
and neighborhood ceilings remain unresolved. The temporary mapped arrays remain
local evidence; compact source/transcript/guard receipts are the portable proof.

Review wording correction: weights are initially positive and subsequently
nonnegative (chosen centers have zero mass). The saved result's phrase "positive
finite weights" is imprecise; the retained probe explicitly exercises these zero
weights. Original result bytes are preserved. No broader invalid-input validation
is claimed.
