# Graph-hash chunk serialization candidate

UNINSTALLED. Only a copy of neighborhoods.py is changed. The baseline source and baseline result bodies are retained; all Main/live39 source, Git, STATE, registrations and inputs remain unchanged. No real graph/labels, research claim, empirical/numerical engine or network operation ran.

A private `_graph_chunk_bytes` helper skips the recursive JSON-domain scan only for exact np.ndarray chunks with1or2dimensions, at most1024scalar cells, no object/fields/subdtype/metadata, and signed/unsigned integer widths1/2/4/8 or float widths2/4/8. `.tolist()` yields fresh built-in scalar/container objects for this finite domain. The existing JSON options remain identical: sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False, then UTF-8. There is no cache. Subclasses are rejected before inspecting dtype and execute the original `.tolist()`→current_canonical_bytes fallback. Unsupported Unicode/bool/object/structured/complex/datetime/longfloat and metadata dtypes retain fallback. NumPy expands ordinary subarray dtypes into dimensions; remaining structured subarray fields are excluded.

`graph_hash` uses the helper only at its existing ndarray chunk writes. All validation, framing, mapping ordering, slices, recursive wide-row route and1024cell chunk sizes remain. Every other function/class is AST-identical, including node_order_hash; typed local matching_identity and source/currentness/callback boundaries are not edited. Exact np.memmap is a subclass and retains original fallback. Consequently these measurements do not predict an improvement for an all-memmap workload.

Checks:179chunk cases compare exact bytes, hashes and exception type/message against the original current serializer, then against immutable baseline result records. Cases cover empty shapes,1023/1024/1025 boundaries, wide rows, native/big-endian integer and float widths, integer extremes, float16/32/64 extrema/subnormals/signedzero/hard values, Unicode, nonfinite values, strided arrays and unsupported types/subclasses. Nine actual validate_graph/graph_hash synthetic cases preserve hashes/errors; fresh graph mutation changes both hashes identically. Focused follow-up checks prove a subclass dtype trap is untouched, synthetic memmap mutation stays fresh, three complete canonical graph framing hashes match, and graph validation plus every other source function remains. No genuine Run or Owner is constructed.

An initial draft inspected subclass dtype too early. It was corrected before freeze; its exact draft body and first result/benchmark files are retained under iteration01. Final compatibility and benchmark files are numbered02 and refer to the final candidate. No initial measurement is substituted for the final source.

Seven alternating baseline→candidate repetitions per case, pinned to CPUs2,3, with OpenBLAS/OMP threads1,1GiB address-space and60CPU-second limits. Serialization cases contain131072synthetic scalar values; graph case has32769nodes/32768edges and retains full original validation. Peak process RSS reported by getrusage:432456KiB (~422MiB), including process setup/imports, not an isolated allocation measurement.

| Synthetic case | Baseline median s | Candidate median s | Ratio | Wall reduction |
|---|---:|---:|---:|---:|
| int64 | 0.014490130 | 0.007724609 | 1.876× | 46.69% |
| float64 | 0.058019251 | 0.048987637 | 1.184× | 15.57% |
| validated_graph | 0.060885728 | 0.035871599 | 1.697× | 41.08% |

The host is shared with active39; these are finite ordinary engineering measurements, not a causal live profile or a performance guarantee. The validated graph case includes validation, but no Owner lease, source admission, archive, real dictionary, pipeline or complete authority boundary. In particular no full batch or85-second authority-boundary gain is claimed. Genuine integration/source-pin refresh and future protocol review remain Root-owned after39 closure.
