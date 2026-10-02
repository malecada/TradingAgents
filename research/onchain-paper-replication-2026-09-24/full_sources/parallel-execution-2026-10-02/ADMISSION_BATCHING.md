# Measured optimization target — prospective implementation

Read-only investigation identifies the smallest target as the source_files loop
in tradingagents/research/admission.py, originally lines185–190. Do not alter
_check_source frequency, lifecycle authority, historical verify.py, or amended/
extended admission dialects. The profile names admit:121/_git:51/_committed:58
identify this base module. Independent verify.py also accounts for7424calls and
28.398cumulative seconds; that separate verifier remains unchanged initially.

Replace repeated per-file git show with fresh finite cat-file size/body batches;
no cross-call cache. Retain every local_path prohibition, source/worktree byte
comparison, registered SHA256 and design-commit SHA256 comparison. Preserve HEAD,
ancestry, registration/charter/selection/runtime/history/input/budget behavior.
Existing source lookup normalizes Path(name).as_posix(); design lookup uses the
original name. Preserve that distinction. Existing newline filenames work via
argv git show: retain the original per-file path for newline/unencodable requests
rather than introducing a ban or requiring newer Git -Z. NUL remains invalid.

Parse binary bodies by declared extent, never by newline. Validate response count,
blob type, object-id format (not hard-coded SHA1 only), decimal size, body length,
delimiter, missing/ambiguous/non-blob responses and trailing bytes. First obtain
sizes; compare source extent with current bytes. Bound batches by both count and
advertised byte total; oversized single files use the existing per-file route.
Use communicate-style finite subprocess calls with error conversion and reaping,
not a persistent child. A prior local example is matching_owner._anchor_read /
_anchor_blobs, but its newline restriction/SHA1/size assumptions are unsuitable
for direct reuse in generic admission.

Fresh disposable-repo tests must cover same/distinct commits, all mismatch types,
empty/binary/header-like data, space/tab/Unicode/newline paths, forbidden paths,
malformed/truncated/extra Git responses, process failure, batch thresholds,
oversized fallback, mutation between checks and independent concurrent calls.
Then targeted lifecycle source/registration/charter/selection/design regressions
and the exact isolated profile03 owner fixture. Coordinate admitted source freezes.

Record comparable unprofiled baseline/candidate timings only after correctness
review. profile03's118.12seconds include instrumentation overhead; cumulative
call times overlap and cannot be summed. No measured speedup exists yet.
