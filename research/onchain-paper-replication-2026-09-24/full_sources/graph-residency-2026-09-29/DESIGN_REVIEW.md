# Independent registered graph-residency design review

September 29, 2026. Reviewed the proposal against current mapped loading, registered producer and job exception/control flow. No source/test edits, tests, raw-body reads, empirical jobs or external requests were made. This is a design review for bounded engineering, not empirical admission.

**Disposition: suitable for implementation subject to the ownership and failure contracts below.** The aggregate population context is the appropriate place to bound simultaneous mappings; per-graph limits alone cannot establish a fold-level mapping ceiling.

## Exact admission and denominator

Require precisely `schema_version`, `mode`, `max_graph_file_bytes` and `max_open_arrays`, actual integer version 1, mode `mapped`, and positive actual integer limits (reject bool). Read the policy through `run.read_input`, match producer-plan and caller/job names exactly, and reject a supplied policy on completed reuse. Preflight all job policies before any population producer or graph work, including invalid later jobs after valid earlier entries. Defaults with no policy retain eager behavior.

Define `max_graph_file_bytes` explicitly as the **sum of all member file bytes, including NPY headers, mapped simultaneously by this population context**, not an individual-file maximum or numeric payload alone. `max_open_arrays` counts the actual member mappings, including Unicode IDs and optional aggregates. Four-member and five-member graphs must both contribute their exact counts. Do not deduplicate paths or repeated hashes in accounting unless handles are actually shared; duplicate logical graphs should be rejected as a population error. Neither bound claims control of unrelated contexts or total process resources.

Shared `preflight_mapped_graph` should preserve the existing complete schema/member denominator, safe filenames, actual size/hash and NPY magic checks. Its result is verified inspection data, not independent empirical authority. Inspect all manifests and sum the full population before the first mmap; one corrupt final manifest or an aggregate byte/array excess must prevent mapping earlier valid graphs. Retain the existing `max_graph_payload_bytes` condition independently and conjunctively: satisfying either limit cannot bypass the other. If inspection results are cached to avoid rereading, maintain the existing stable-backing-file assumption and do not describe this as race-proof snapshot isolation.

## Direct-producer proof and ordering

**The current producer computes `representation_descriptor` before policy checks. Change that ordering for mapped-policy callers.** Graph hashing reads arrays, so a closed borrowed graph may fault before a late provenance check can reject it. Policy and active-owner validation must precede graph validation, hashing or any other buffer access.

A bare memmap type check or equal canonical graph hash does not prove compliance. The same logical graph can have different member files, dtype widths, headers or mapping multiplicity. Require an active population owner/lease (kept outside scientific dataclass fields) or equivalent loader-issued provenance sufficient to establish:

- Exact graph object membership and no substitutions, duplicates or omissions.
- Each admitted manifest's canonical resolved path and expected hash, and its inspected member identities, sizes and array count.
- Live read-only mappings belonging to that context, with aggregate limits checked against the producer's newly read policy.
- The requested graph hashes match the registered graph references and the scientific descriptor.

Reject eager objects passed under mapped policy, graphs mapped from an unadmitted equivalent manifest, arrays substituted after opening, closed/foreign ownership and a population created under looser limits that exceeds the current admitted policy. An execution-only lease/provenance field must not enter dataclass fields, graph canonical hashes, sample identities or full feature bindings. The ordinary Python trust model need not become a security sandbox, but supported public call paths must not bypass policy by supplying arbitrary graph objects.

Input references should remain the loader default. Current-run output references may be added only if their exact published bytes/hash and canonical path are proven to the same standard; an output name or matching graph hash alone is insufficient. This extension is optional and should not be inferred from the producer's pre-existing ability to read output metadata.

## Lifetime, cleanup and publication

Use one ExitStack/population context around the complete synchronous registered producer call, including sampling, dictionary/MCM computation and durable journal reads/publication that still need graph objects. Close it before model batch execution. Derived features, dictionaries and bindings must own their data; graph maps and views may not escape. This preserves the mapped loader's explicit lifetime contract rather than making a mapped graph look permanently immutable.

**Do not turn unresolved cleanup failure into ordinary representation unavailability and continue fitting.** Current `execute_fit_payload` catches `ValueError`, `RuntimeError` and `OSError` per representation, then proceeds to `execute_batch`. A new context-close failure could therefore leave a live map and still enter model fitting. Distinguish cleanup failures or verify the population's closed invariant before proceeding; unresolved mapping ownership must abort before batch execution. Attempt every close, preserve the primary exception and retain any completed numerical journal/binding. Cleanup failure must not erase completed numerical evidence or authorize recomputation.

The claim should record the enabled policy input name/hash and enough execution provenance to audit the actual population totals; no policy fields belong in the scientific descriptor. A failed-parent successor remains subject to existing exact ancestry, sample/dictionary reuse and terminal non-restart rules. This integration does not admit new numerical work merely because loading now uses maps.

## Required meaningful tests and limits

Use actual synthetic admitted graphs and a real registered producer to compare the complete eager/mapped feature binding, sample and dictionary identities. At the final batch boundary, assert every population mapping is closed and independently owned outputs remain usable. Include optional-aggregate variation and an aggregate limit exceeded only when several individually admissible graphs are combined; a sentinel on the first mapping should prove early refusal. Test each independent byte limit and the array-count limit separately.

Exercise policy/schema/hash drift, plan/job disagreement, unused reuse policy, malformed last member, duplicate population, invalid later job, eager/direct-producer substitution, wrong manifest provenance and closed-context rejection before graph hashing. Inject late graph-open failure and an actual job-boundary close failure with one mapping left open; assert cleanup attempts continue and `execute_batch` never runs. Reuse/continuation must preserve full binding identity without implicit sample replay. If current-run output loading is added, test unpublished, altered and wrong-path references.

The aggregate bound concerns mapped files and handle count, not RSS, page-cache residency, full validator temporaries, adjacency indices, alignment sets, retained neighborhoods, matching matrices, copied Torch features or model activations. All graph files may still be mapped simultaneously; this is not a streaming numerical pipeline. A finite outer guard and separately committed prospective policy/resource admission remain necessary for empirical execution. No gate, claim, allocation or financial fit is enabled by this review.
