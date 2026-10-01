# Sampler proof enforcement in dictionary execution

This isolated successor to dictionary-sample-driver requires the exact current
sampler completion proof before constructing a dictionary consumer or running the
actual dictionary workload. The caller supplies registered policy names and an
explicit proof hash; no sample event, numerical settings or arbitrary pair
purpose is accepted from the caller. The proof route derives and verifies the
exact event/component and publishes no new sampler attempt.

Dictionary pair purposes remain internally derived. Each pair boundary and final
return lease the completion proof, sample artifact, owner and registered source
bytes. The result includes the exact admitted sample/proof provenance record for
subsequent dictionary publication. Existing dictionary identities and numerical
matching/clustering semantics are unchanged. Completed pair replay still rebuilds
matrices and clusters; it does not establish dictionary artifact publication or
completed representation reuse. Those remain mandatory separate work.

The tests produce actual tiny registered samples and proofs, run real dictionary
pairs and compare every matrix, membership, hierarchy and ordered representative
with the scalar reference. They check exact provenance, completed pair reuse with
PairSession.create/resume forbidden, terminal-conflict and omitted-draw refusal
before workload entry, proof drift after the first pair, and unregistered driver
refusal. Guard observations are mocked and the fixture has three samples without
partitioning; earlier partition evidence is separate. No empirical data or
financial fit is run. Mapped/full-fold resources and empirical admission are not
established.

red01 CLOSED five missing-driver failures in 0.003s, session98490 exit1.
check01 CLOSED five passes in 75.961s, session5887 exit0. Independent acceptance
remains pending review. No empirical admission follows from these checks.
