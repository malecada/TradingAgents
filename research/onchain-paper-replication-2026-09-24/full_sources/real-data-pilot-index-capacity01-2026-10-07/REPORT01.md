# Seven-graph index reservation correction

Candidate only. Root owns live integration, registration, review, preservation and empirical execution. Pilot15 and its 1 MiB policy remain unchanged. No array payloads were read or loaded, and no sampling, matching, labels or neural computation was performed for diagnosis.

The frozen policy SHA `97ef6a748bc8ccdd02f0dfdf6a5995c8bce91522306d4b3849dfa0e91c4d8e9d` grants `max_buffer_bytes=1048576`, `edge_chunk=4096`, `max_output_bytes=289981568`, `max_numeric_bytes=291030144`. `CAPACITY01.json` contains exact gate, policy, source and graph manifest SHA joins; each node count joins its retained authenticated receipt. Three bounded current NPY headers per graph supply complete axes/float64 widths, joined to the admitted manifest member SHA and extent. No file-size inference supplies dimensions. Historical body identity is inherited; current headers are observations, not a new complete-body authentication or writer-exclusion guarantee. Later existing full graph validation remains required.

| Graph | Nodes | Edges | Retained index bytes | Constructor additive bytes | Output-inclusive bound bytes |
|---|---:|---:|---:|---:|---:|
| May 2 | 1878300 | 2779164 | 74519440 | 202286664 | 380793160 |
| May 9 | 2265481 | 3149567 | 86640784 | 237370420 | 439582708 |
| May 16 | 2048710 | 2812471 | 77778912 | 213577088 | 394215232 |
| May 23 | 1875043 | 2642414 | 72279328 | 197715244 | 367469740 |
| May 30 | 1581441 | 2426106 | 64120768 | 173177268 | 329088052 |
| June 6 | 1581761 | 2355230 | 62991872 | 170928436 | 322303156 |
| June 13 (first attempted) | 1768268 | 2518332 | 68585616 | 187338120 | 349151368 |

For `n` nodes, `e` edges, `c=4096`, node width `wN=32` and edge width `wE=16` bytes:

- Retained index `R = 16*(e+n+1)` covers two int64 edge orders and two int64 offsets.
- Existing conservative additive envelope `A = R +16e+40(n+1)+4n+c*(64+2wN+2wE)`. This deliberately adds some nonconcurrent temporaries; it is not a measured live peak.
- A complete induced output cannot exceed `O = min(n,10000)*wN + e*(16+wE)` bytes. This includes all possible graph edges, with no degree probing or truncation. `AttributedGraph` copies bytes once per array; originals and immutable outputs coexist. The existing admission expression is `A+2O`.
- The same finite maximum over all seven graphs is **439582708 B**. The largest output is **289981568 B** (`2265481*32*4`). Their sum is **729564276 B**.

The amendment in `mcm_policy01.json` changes only `numeric.max_buffer_bytes` to439582708 and `numeric.max_numeric_bytes` to729564276. This is a single calculation for the complete frozen population, not a cap ladder. It avoids an unnecessary algorithm rewrite: the existing index already performs bounded complete extraction and preserves original directed edge-column ordering. No matching precision, neighborhood rule, dictionary, sample, graph, chunk, physical6GiB cap,5GiB high or10GiB disk floor changes.

`candidate/index_capacity.py:validate(root, inputs, graph_inputs, numeric, dictionary)` is executable early preflight. It authenticates the seven manifests, reads only bounded headers, checks graph identities/axes/types/extents, and fails before any expensive import or graph load if the index/output/numeric reservation is insufficient. Root should call it in the next preflight after exact input authentication, using the actual execution descriptor and MCM input, before launching RootIO. A return value is only early reservation success. The original graph body validation, later index/output gates, source authority and native resource guard remain authoritative.

Peak qualifications: the reservation excludes original graph inputs, Python node IDs, runtime/imported authority, matching allocations, previously retained outputs, model/optimizer state and charged file cache. The seven original serialized array files total3496602912 B including headers and Unicode node-ID arrays; that total is neither their live Python representation nor simultaneously resident RSS. Only one active MCM output is counted by this policy; retaining others requires the existing outer/offload accounting. Pilot15's sampled charged peak near5GiB cannot establish that this prospective extraction path fits6GiB. No new whole-capacity/throughput claim is made. Runtime memory pressure or an existing scientific neighborhood/pair limit can still stop the fresh attempt; no limit is relaxed here.

Verification: checkout-local locked runtime check passed with no problems. `run_tests01.py` admits only the reviewed synthetic candidate file into the existing offline profile in memory; normal root network/store guards apply, no persistent test-inventory change. Final result29passed in0.81s:9 new checks plus20 existing complete-array neighborhood regressions/equivalence checks. New checks cover exact implementation formula and one-byte boundary, all-seven calculation without `np.load`, separate index/output/numeric underfunding, changed manifest/graph identity/extent/width, symlink and boolean-policy refusals. The first test run had28passes/1failure because a local-slice fixture was incorrectly supplied to the full-graph constructor; that fixture was corrected to an invented `GraphSnapshot`, with no production code change. Full legacy tests and empirical work were not run.
