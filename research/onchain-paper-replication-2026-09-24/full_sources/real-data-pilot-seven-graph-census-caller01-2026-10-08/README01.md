This caller performs one ordinary topology data-preparation census over an
explicit, immutable list of exactly seven retained graph manifests. It does not
create a ResearchRun, consume a financial trial, load a model, change a limit,
truncate a neighborhood, or authorize a subsequent MCM attempt.

`DRAFT_SETTINGS01.json` pins the exact caller, adopted helper and reviewed
`CALLER_INPUTS02.json`. Root must freeze the actual request and native controls
before using it. Settings schema is version1, kind
`topology-only-seven-graph-census-v1`, with `inputs:{path,sha256,bytes}`,
`caller_sha256`, `helper_sha256`, `max_work_bytes:268435456`,
`chunk_edges:65536`, and `chunk_centers:262144`. Paths in input references are
relative to the explicit repository root. The selected list contains exactly
seven distinct graph hashes and manifest paths. Each row has `graph_hash`,
`week`, optional `role`, `manifest:{path,sha256,bytes}`, integer `node_count`,
`node_count_reference:{path,sha256,bytes}`, and `edge_index`/`node_ids` references
with `path,sha256,bytes,dtype,shape,fortran_order`.

The count JSON must join the selected manifest hash and its declared node-feature
hash; the node-ID header must corroborate its row count. No node-ID body or
feature body is decoded or loaded. Node-ID body hashes are inherited manifest
pins, not revalidated. Manifest, count JSON and complete edge bytes are hashed
before and after calculation. Node-ID headers and file stats are checked before
and after. A read-only edge mmap is opened through the already-open descriptor
and supplied to the adopted helper as an ordinary, nonwriteable ndarray view.
The helper source is loaded directly from authenticated bytes, avoiding the
research package initializer and ResearchRun import.

The returned cardinalities are independently checked for center0 and the
reported maximum center, deduplicated when identical, by scanning edge chunks
and building a Python set of incident neighbors plus the center. This does not
independently prove the global maximum or verify every cardinality. The set is
bounded by the declared node universe and is outside the helper's numeric-array
envelope; Root's native controls bound the process separately. No capacity or
runtime conclusion follows from passing these checks.

The output directory must not exist and its parent must already exist. Each
attempt gets an immutable ATTEMPT01, RESULT01 and ordered int64 NPY chunks of at
most262144centers (about2MiB, always checked below4MiB). The seven-row SUMMARY01
retains completed, failed and unattempted dispositions and stops after the first
graph failure. A changed final input declaration/source fails the whole summary.
Partial files remain after a failed write. Original calculation errors survive
as `reason` alongside a separate `cleanup_error`; a sole mmap-close failure
changes an otherwise completed calculation to failed. Abrupt kill or inability
to write metadata can leave START/ATTEMPT and partial files without SUMMARY;
Root's native terminal evidence must reconcile that state, never infer success.

Elapsed and process CPU measurements include per-graph authentication, checking
and publication; helper-only times are separately labeled. `ru_maxrss_kib` is
Linux process-lifetime high-water RSS, not an isolated graph or cgroup peak.
Root's existing native monitor supplies process/cgroup evidence. Hash/stat
observations do not exclude concurrent writers or intermediate changes restored
between samples. Native resource controls and their actual request belong to
Root, outside this caller.

Invocation from the engineering CWD uses absolute caller/settings/output paths:

```text
<repo>/.venv/bin/python -B <caller01.py> --root <repo> \
  --settings <frozen-settings.json> --settings-sha256 <sha256> \
  --output <new-output-child>
```

Preparation opened no retained array payloads. Nine tiny synthetic checks cover
the exact weak counts with duplicate/reversed/self edges, all-seven completion,
wrong edge hash with failed/unattempted denominator, count-manifest mismatch,
one-use output and seven-row refusal, changed edge after computation, changed
declaration terminal evidence, independent-count disagreement, output chunk
continuity, and primary/cleanup error retention. The initial test-fixture syntax
error is preserved in TEST_SETUP_FAILURE01; RED01 and RED02 retain the observed
missing-feature/failure-evidence checks. GREEN01 records all nine passing tests.
No broad historical matrix, real census, native guard, network or empirical
experiment was executed by this implementation assignment.
