# Fresh dictionary subset-reuse counterexample

A five-sample deterministic fixture produces fewer actual directional comparisons than the conservative dictionary capacity:

| Setting | Value |
| --- | --- |
| sample_count | 5 |
| size | 2 |
| partition_threshold | 2 |
| partition_size | 3 |
| seed | 12 |
| callback score for every direction | 0.5 |
| conservative comparisons / matrix entries | 22 / 36 |
| actual comparisons / unique matrix entries | 20 / 32 |
| accounting levels | 4 |

The ordered matrix visits are `[1,2,3]`, `[0,4]`, `[0,1,4]`, `[3]`, `[0,3,4]`, then final `[0,4]`. The last subset is identical to an earlier matrix key. `workload.fit` returns the cached complete matrix before emitting further purposes, saving exactly two directional comparisons and four matrix entries. Earlier occurrences of the individual pair `(0,4)` in different three-element blocks are still separate purposes; this is whole ordered-subset reuse, not global unordered-pair deduplication.

The fresh `investigation-02.py` first reconstructs partition visits using PCG64 and actual `cluster_medoids` on constant-distance matrices, searches 109 tiny candidates to this first example, then invokes the actual dated `workload.fit` once with this fixture and an explicit constant-score callback. It asserts the actual count, both-direction ordering and the strictly smaller count than `dictionary_capacity`. The JSON retains all twenty asked sample-index pairs, actual unique matrix subsets, hierarchy/memberships and exact source hashes checked before and after computation. The script exits zero; `investigation-02.log` records the concise result.

This is orchestration and conservative-count evidence only. The five immutable one-node/self-edge local graphs and SampleManifest are constructed synthetically; no empirical graph, registered sample draw or matching calculation is used. Matching config is an empty synthetic mapping because the callback supplies the fixed score. This does not establish scalar numerical parity, weighted sampling provenance or registered producer admission. It supports preserving the distinction between reserved maximum capacity and independently derived actual completed count; accepting an arbitrary smaller count would not prove dictionary completeness.

The first fresh investigation reached and passed its computation assertions but failed while serializing the frozen hierarchy (`mappingproxy`). Its source, partial JSON and failure record remain as `investigation-01*`. The separate second identity adds `thaw` at serialization and preserves the first attempt unchanged. No historical test or financial experiment was rerun. Only `investigation-*` files in this directory were created by the investigator.
