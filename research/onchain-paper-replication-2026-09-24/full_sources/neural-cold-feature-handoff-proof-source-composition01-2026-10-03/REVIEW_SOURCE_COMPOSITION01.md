# Independent source composition review — withheld

The frozen composition is **WITHHELD as an executable scientific source closure**. Its declared body hashes and overlay provenance reproduce, but the actual scientific route requires missing source files. No numerical process, module import, admission, claim, model, matching computation, or capsule creation was performed by this review.

Reviewed manifest: `d1d5d3f60de896b14edfc254d3ca31a7d32dae7ed490a3f5db18c06e10094216`. The findings apply to the immutable source snapshots in `source-bodies/`, not to moving live package files. Existing accepted component reviews do not establish completeness of this new composition.

## CFC1 — selected scientific dynamic source closure is incomplete

`source-bodies/tradingagents/research/onchain_replication/compact_native_producer.py:44–48` requires the scientific producer's dated sampler, sample reader, MCM array kernel, feature boundary, denominator and native feature API. None of the following six direct paths is in the 164-target inventory:

- `pair-component-reader-2026-10-01/reader.py`, declared by `compact_samples.py:22`.
- `mcm-array-kernel-2026-10-01/kernel.py`, declared by `compact_mcm.py:29`.
- `sampler-leased-core-2026-10-01/core.py`, declared by `compact_sampler.py:23`.
- `graph-feature-boundary-2026-10-01/boundary.py`, declared by `compact_features.py:23`.
- `representation-denominator-2026-10-01/denominator.py`, declared by `compact_denominator.py:18`.
- `terminal-output-lifetime-2026-10-01/native_map.py`, declared by `compact_native_features.py:22`.

These are paths beneath `research/onchain-paper-replication-2026-09-24/full_sources/`. The native API has further dynamic dependencies: `native_map.py:18–22` loads `seal.py` and derives `SOURCES` transitively. Thus the six paths are a demonstrated minimum, not a complete replacement inventory.

The producer's `selected()` checks hashes for the required paths before production (`compact_native_producer.py:93–96`). Calling `required_sources()` itself calls `compact_native_features._api()` (`compact_native_features.py:25–31`), which loads the absent native map. In an isolated capsule containing only the declared map, this can fail before reaching the later source-hash loop. If those files happen to exist elsewhere locally, the absent admitted pins still prevent an eligible scientific producer. The materialization helper's complete discovery of the *declared* inventory cannot supply these undeclared dependencies.

An independent extraction of the actual `compact_dictionary._sources` function, with only a metadata boundary substitute and real selected source bytes, refuses with `ValueError: compact dictionary numerical source not admitted or changed`. The selected map has the workload source but no reader pin. This is source-selection evidence, not a genuine Owner/Binding test. The initial check's uncaught refusal remains in `review_checks01.log`; `review_checks02.py` records that same expected refusal and completes the remaining read-only checks.

Required correction: preserve this candidate; create a new explicit source composition including the entire actual scientific dynamic dependency graph, original origins and hashes. Check both local imports and all dated `spec_from_file_location` paths before any materialization/registration. Add an independent regression that compares actual required paths with the source map; merely checking the map against itself is insufficient.

## CFC2 — undeclared refusal instrumentation is on the ordinary MCM path

`compact_mcm.py:282–294` unconditionally imports `resource_refusal`, then uses `compute_callback`, `score_callback` and `returned`. No `resource_refusal.py` or equivalent package target is present. This is inherited from the exact `08150fb38943717d7f173c30b6dda12c494d8663654670c6b8cd865df1dd3caf` composition. It is not restricted by an imported-only or explicitly selected refusal condition. Scientific `compact_native_producer.produce()` calls ordinary `compact_mcm.produce()` at lines 135–140, which reaches the same `_produce_locked.compute` function.

An AST scan of all selected Python bodies found this missing relative module edge. `compile()` success does not resolve imports. Consequently the author's six passing source checks do not demonstrate a complete executable closure. Adding unrelated refusal modules without reviewing their effect on the ordinary scientific route is not the minimal safe correction. Compose only the accepted cleanup handler into the metadata-correct baseline, preserving the original numerical callback path; alternatively any intentionally selected instrumentation would require its complete reviewed closure and an explicit protocol. Preserve the failed imported attempt and this candidate unchanged.

## Metadata concern resolved narrowly

The suspected full-map overflow on the ordinary scientific dictionary/MCM route is not established. `compact_dictionary._sources` at lines 35–43 returns exactly the workload and sample-reader pins. `compact_mcm._sources` at lines 52–58 adds only its array-kernel pin. `_source_evidence` returns those three pins for a scientific dictionary; only the imported Target route uses the full registered map and count/digest encoding.

Using the actual path names and fixed-width 64-character pins, their canonical source maps occupy 338 and 504 bytes respectively. The complete registered map is 20,751 bytes, but it is not placed into these scientific `start.sources` fields. These are source-field extents only: they are not a published start/complete record, successful full metadata preflight, numerical materialization, or proof that every later metadata field fits 8,192 bytes. No metadata cap increase is justified by this concern.

## Independently verified preservation and limitations

`review_checks02.py` rehashes all 179 manifest bodies, totaling 3,147,795 bytes, and all 164 source bodies, totaling 2,963,908 bytes, including 147 package sources. All source snapshots equal their declared origin bodies; 113 rows with explicit Git origins also equal the exact local committed blobs with network/lazy fetching disabled. Of the 153 base rows, 147 remain byte-identical; the 11 scientific and six outer overlay bodies equal their declared accepted source snapshots. This verifies the recorded selection, not transitive completeness.

All 12 dependency bodies match their pins. The four recipe/config/model/training templates are identical to the selected prior preparation. All 11 original JSON bodies match their hashes and sizes; the 26 original source references are retained. Original historical Git objects were not independently reverified in this source review. All 251 selected installed distribution RECORD bodies match their recorded hashes; installed dependency payloads and future capsule module origins were not attested. None of these checks imports numerical packages.

The existing weak-reference-only parity test and source checks were inspected, not rerun as numerical tests. The source body preservation confirms that selected model/matching/training equations and existing typed archive implementation were not replaced by this composition. It does not establish actual archive/Owner lifetime, cold handoff, return equivalence, checkpoint/RNG continuation, memory capacity, whole native cleanup, remote recoverability, or paper-scope/financial success. The original dictionary's 512 spent samples remain separate from the proposed fresh synthetic 32-sample scientific proof; neither historical job was reopened here.

A corrected complete source composition and independent static closure check are necessary before the separately reviewed concrete capsule, generated inputs, cumulative engineering registration, native release and genuine bounded comparison. This review grants no execution authority.
