# Explicit fixed-feature loading policy

The default remains eager loading. To request per-batch loading, register an
additional immutable JSON input with these exact fields:

```json
{"schema_version": 1, "mode": "batch", "max_unique_feature_bytes": 2147483648}
```

The2GiB number is an illustrative value, not an empirically admitted setting.
Select the actual value from the enclosing job's measured memory requirements.
Set `residency_input` to that admitted input name in both the representation job
and its producer-plan entry. Completed registered reuse can supply the same
input name to `reuse_registered_features`; no representation refit occurs.

The policy changes storage/execution only. It is recorded in the representation
claim and bound as an admitted input, while the descriptor, workflow identity,
dictionary identity and numerical feature hashes remain unchanged. A policy
mismatch or invalid schema fails before representation ownership is reserved.

The loader sums the numerical payload sizes of unique graph identities requested
by the batch and refuses excess before loading any arrays. Repeated graph
references within one chronological batch share the same loaded object. No
learned graph embedding is cached across optimizer updates. Component contents
are rehashed before and after loading; altered stored bytes fail. The training
loop releases its input/output/loss references before asking for the next batch.

`max_array_bytes` remains the separate journal/component admission bound. It
covers component-file and retained unfinished-state checks; the residency policy
does not replace or relax those checks. Completed feature arrays are represented
by verified descriptors, including through failed-parent ancestry. Alignment
still retains its necessary prior basis, and unfinished sample/dictionary/MCM
state can remain resident within existing limits.

`max_unique_feature_bytes` is not a full-batch or process memory promise. Vector
arms expand features over daily sequences; that expansion, prices and targets,
model/optimizer state, activations, transient copies, Python objects, decoder
state and page cache remain outside the loader counter and inside the outer
resource guard. Source graphs and the current sampler still load eagerly. GPU
operation and full-sized capacity are not established by the synthetic evidence.
