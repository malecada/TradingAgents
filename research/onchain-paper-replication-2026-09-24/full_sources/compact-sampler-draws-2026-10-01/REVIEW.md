# Independent corrected sampler-draw review

Accepted for current-owner resident sampling with retained durable draw acknowledgements. CS1 and CS2 from the preserved `REVIEW_INITIAL.md` are closed by the reviewed source and saved targeted evidence. No numeric sample publication, scientific sample-provenance admission, dictionary consumption or empirical release is accepted here.

The review independently inspected the source delta, preserved leased kernel, matching identity implementation, writer/reader helpers, current tests, terminal logs and RESULT. No tests, historical jobs or empirical array reads were performed. Only this review note was written.

## Findings closed

**CS1:** `_fingerprint` now uses `matching_identity.graph_identity` for AttributedGraph samples. This validates local graph identities and includes framed node order, parent/center, array dtype/shape/extent and actual numerical bytes. It does not invent weekly GraphSnapshot metadata. The positive test independently compares each sampled node identity, parent/center and all three numerical arrays with `sample_neighborhoods`, along with records and sample identity; it no longer repeats the faulty fingerprint API as its oracle.

**CS2:** The writer's local lease first invokes the external training lease, then verifies pinned root, exact current inventory and every written file against its intended SHA using bounded reads, with no further external callback before return. The core invokes that lease before its first allocation/draw and before/after every checkpoint. Thus start metadata and all previously acknowledged draws are checked at numerical boundaries, and the just-written draw is checked after the late callback before acknowledgement returns. The red03 regression reached draw callbacks `[0, 1, 2]` after corrupting draw 0; the corrected test requires only `[0]`, refusal, owner poisoning and absence of draw 1. Static inspection of the unchanged core confirms this checkpoint refusal occurs before the next RNG selection.

## Saved evidence

- red01: 1 missing-module failure and 7 fixture errors, 24.02 seconds; the copied dated core was not staged in the temporary Git fixture. The original fixture remains preserved.
- red02: 1 missing-module failure, 7 deselected, 15.89 seconds, after fixture correction.
- check01: 3 failed, 5 passed, 139.27 seconds. The three failures reached the wrong AttributedGraph fingerprint; four preflight refusals and interrupted-write preservation passed.
- red03: 1 failed, 8 deselected, 19.95 seconds, demonstrating acknowledgement continued after saved evidence corruption.
- Final check02: 4 passed, 5 deselected, 92.78 seconds. These cover actual sampler parity and successful retained evidence, resident sample/draw damage, late verification callback mutation and acknowledgement refusal before the next draw.

The earlier five passing refusal/preservation cases and corrected four-case run are distinct evidence. No combined final-source nine-case run is claimed. RESULT was being updated by its owner when reviewed; the raw check02 log is terminal and supersedes its earlier Running table entry.

## Accepted boundaries and limitations

Admission requires the actual compact Training object and serializes creation through its Owner transition lock. Both registered routes select the same sampler input and compact backend. The separately admitted dated kernel, training identity, selected input hash, settings, ordered training hashes, seed and NumPy identity are pinned. The exclusive namespace is not reopened; post-creation failures retain residue, attempt a failure marker and poison the owner.

The logical `(count + 3) * metadata_cap` reservation includes start, draws and possible complete-plus-failed receipts, with completion size preflight. Selected center, direct-weight and neighborhood/sample-array caps remain separate from Python objects, choice scratch, filesystem overhead and process RSS. Each callback rereads all preceding draw metadata: this entails quadratic cumulative record reads in draw count, not demonstrated full-fold throughput. Verification is sampled and non-atomic against continuous external mutation.

The final live result joins its saved draw chain, resident records, RNG terminal state and attributed numerical fingerprint. Full checks revalidate training/source authority and repeat saved-evidence verification after the last external callback. Cheap leases retain the explicit frozen-resident-input contract and are not a substitute for full boundary checks.

Fixtures use actual temporary ResearchRun/Binding/Owner registration with mocked kernel guard surfaces and the inherited two-train/two-test-row supplied population. Complete calendar/exclusion accounting, reconstructed prices/labels, physical resource feasibility and full-fold performance were not tested. Single-uniform PCG64 state transitions and parity with the existing sampler do not constitute an independent overlap-weight probability oracle. Numeric publication and its scientific provenance consumer remain necessary; the two false receipt flags accurately preserve this distinction. No resume, cold admission, new empirical trial or financial result is established.

## Exact reviewed bytes

- `compact_sampler.py`: `7820254d9a9ac287e55b0d20d2c26e1907b625dd743e194fae0602110593a608`.
- `test_compact_sampler.py`: `decf48f9c68d95e58e40bff16fa088e3af8af30d0d84b82c023d0545bd46803c`.
- Preserved `sampler-check01.py`: `c8ca840a7a1b7fe6684ea89282dfc1979795bf6c7db3f5d8d89b870abc023473`.
- Preserved `test-check01.py`: `2603b2630a1ac30793f141e1bad246f8830c2d87f5f41246c3b2d394ec897761`.
- `check01.log`: `2830ef77e5b2af60662365df27b130cad66d51aeebe12877489942e608b26ca3`.
- `red03.log`: `f0dd2d6f62608b7b3bad512c34c21165db001852e1d398e7e053a30e5548add0`.
- `check02.log`: `7ba94234bec7f5cd72023c75113de5dbb2ac375ca1b622252fce1fe9d23f069c`.
