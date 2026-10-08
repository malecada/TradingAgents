# Lease hot-path source diagnosis and narrow candidate

The supplied actual21 measurements (2926.76s inclusive lease timing over88532calls;2871.71s inclusive solver timing) do not identify pure validation cost and must not be summed as disjoint work. No live or empirical workload was imported or measured here.

## Callback work retained

`imported_mcm_identity.Target.lease` enters `target_lease`, which rejoins the exact target object and calls `Lease.check`. Each invocation checks authority object identities and target pins, including current canonical serialization of the target's execution/workload/mapping. `Interval.validate` still determines all due checks using the original clock reads and live100ms/fingerprint1000ms/full10000ms/maxstale60000ms/maxcalls65536 policies. No code in the scheduler or callback routing changes.

A due live callback enters `Stage.lease` or `Owner.lease`, then `compact_owner.verify_current`. `Binding.lease` brackets its metadata reads with two `_guard` calls. Guard checks reread genuine lease/release and kernel/native state, verify authority/processes, and authenticate the amended resource policy. The final compact rejoin rereads claim, immutable binding metadata and owner evidence. Although some paths and values recur, these are distinct before/after mutation and callback boundaries. Removing them or reusing old I/O would require stronger proof and is not proposed.

A due fingerprint callback reserializes current configuration, stats the registered paths, and inventories loaded modules/functions. A due full callback executes genuine execution checks and `_authenticate_loaded`, which rereads and hashes each source and recompiles it. Those current source reads/compilations remain intact. The accepted constructor/preparation reuse is neither overwritten nor duplicated.

## Candidate

Only three lines in `_authenticate_loaded` change. The freshly compiled code-object list becomes an invocation-local dictionary of ordered lists keyed by `co_name`. Each authenticated function retains exact code-object equality, filename checks and special contextmanager/generated-metadata handling. Equality between Python code objects requires equal `co_name`; excluding differently named code objects therefore removes only comparisons that cannot succeed. Equal-name candidates remain in the original traversal order, including duplicate nested names. No authority result, compiled object or filesystem observation is cached across calls.

This is an actual full-callback CPU optimization, not a claim that the entire88532-callback total is optimized. The dominant real cost remains unmeasured. The dictionary adds O(number of compiled code objects) temporary references and names for one source compilation; no graph-dependent scratch or persistent/global cache is added. An external memory allowance still covers source authentication as before.

Focused synthetic metadata-only tests pass authored functions, methods, properties, contextmanager wrappers, nested code and refusal for changed name, constant, filename or source hash. Every invocation still performs exactly one source read per module in the instrumented fixture. No NumPy/SciPy/Torch import occurred. The original implementation and candidate share the same returned acceptance/refusal messages. Synthetic401-plus-function authentication medians showed about1.48x speedup over seven samples; these include source read/hash/compile and are not a real-data or whole-lease speedup. Commands used pinned Python3.13.13,512MiB address-space,60s timeout and thread1.

All files are isolated here. Main/Git/STATE/registrations/native jobs and policies were unchanged. MANIFEST.json binds baseline, candidate and inverse patch. Root integration and independent review remain separate.
