# Initial independent review — acceptance withheld

## GP1 — saved numeric bytes are not joined to the admitted feature identity

`publication.py:129–140` accepts the newly saved component when its manifest/event hashes are self-consistent and its total size matches the prediction. The returned feature receipt checks the original tensor values, and final component signatures detect later changes. Neither check establishes that the bytes first incorporated into the saved component actually equal those tensors or `feature_provenance.feature_hash`.

The concrete counterexample is a payload byte changed after the NPY write but before `component_store.save_component` obtains that file's SHA-256 for its manifest. The input tensor stays unchanged. The resulting manifest, event and component inspection can all be internally valid; the final signatures preserve the wrong saved content. The existing final-drift test changes bytes after component inspection and therefore does not exercise this boundary.

Compute expected per-array encoded hashes from the admitted input before writing and compare the strict inspected manifest to those expected declarations, including the exact tree/member mapping. Alternatively independently recompute the saved feature identity using a bounded read. Add an injected early-storage-drift regression and require refusal before completion, while retaining the failed attempt. This counterexample follows from source inspection; no reviewer test was executed.

## GP2 — predecessor metadata cap is silently narrowed

`publication.py:83` reads the saved MCM completion with `Metadata.read`'s default 65,536-byte cap. The selected `mcm_output_input` policy can admit a larger `max_metadata_bytes`, which the actual saved-MCM route honors. This new join therefore imposes an undeclared smaller input limit and can reject an otherwise admitted predecessor proof.

Read the registered predecessor output policy and retain its metadata cap in this snapshot and repeated lease. An explicitly selected smaller input cap would also be a valid separately stated contract; the current output policy does not express one. Test propagation through repeated reads, including a proof larger than the default cap or a focused boundary fixture that verifies the admitted cap used.

## Other reviewed boundaries and scope

Inspection found explicit selected output-policy joining, current required graph membership, exclusive per-graph attempts, event/numeric/logical reservation preflight, native two-array sizing, retained source/owner/feature leases and late component signature checks. Native storage is explicitly marked and does not authorize the old generic loader to feed arrays directly to the model. These checks do not resolve GP1 or GP2.

Acceptance awaits corrected source and closed evidence. No tests, historical jobs, empirical numerical arrays, raw bodies or SQLite were read or executed by this review. No source/test file was changed. Aggregate workflow accounting, model training, top-level representation closure and empirical release remain outside scope.
