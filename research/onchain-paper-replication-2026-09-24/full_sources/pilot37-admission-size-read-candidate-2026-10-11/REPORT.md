# Admission size-read candidate

Status: **UNINSTALLED_UNQUALIFIED**. Candidate preparation only; no tests, Git command, numerical import, native job, claim or production activation was executed. Live sourcefreeze998d353 and prior overhead evidence remain unchanged.

`admission.py` is an exact copy of current live admission.py with one literal replacement in `_source_files.batch`:

```diff
-            if len(local_path(root, name).read_bytes()) != current[1]:
+            if local_path(root, name).stat().st_size != current[1]:
```

`PATCH01.diff`, `INVERSE01.diff` and `CANDIDATE01.json` retain forward/inverse artifacts, hashes and literal inversion verification. The final full local-file read, byte equality and hashes remain intact. Source/design Git joins, route validation, byte/count batching, oversized and line-protocol fallbacks, and failure messages are unchanged. No cross-admission successful-check cache is introduced. A mutation between stat and final read must still fail the existing final comparison; stat is not treated as content authentication.

Maximum redundant local read elimination for the currently observed909-file source roster is15,334,401bytes per successful admission pass. Actual benefit is unknown: stat/path-validation costs, Git subprocess/pipe costs, other metadata checks and page-cache behavior remain. No throughput improvement is promised.

`test_candidate01.py` contains ten deferred standard-library synthetic tests: literal inversion, intact binary input with one content read, size mismatch before body fetch, same-size mutation, mutation after stat during body fetch, oversized fallback, newline/carriage-return/unencodable path fallback, expected hash/design checks, fresh second call and forbidden route. It extracts only the candidate's actual relevant functions with AST; Git responses are finite invented byte frames, and no actual Git or numerical module is called. Cases are adapted from the existing `tests/research/test_admission_batching.py`. This tests the narrow seam, not real Git process integration, admission authority or production safety.

After original36 closes, Root can run `.venv/bin/python research/onchain-paper-replication-2026-09-24/full_sources/pilot37-admission-size-read-candidate-2026-10-11/test_candidate01.py`. The candidate has not been imported, compiled or exercised here. Further integration/review and source-freeze decisions belong to Root.
