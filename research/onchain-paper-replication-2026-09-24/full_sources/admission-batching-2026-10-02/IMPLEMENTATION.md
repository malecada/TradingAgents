# Bounded source admission Git batching — October 2, 2026

Prospective engineering change only. Independent correctness review, isolated
owner-fixture comparison and comparable unprofiled timing remain pending. No
measured speedup is claimed. Historical profile03's 118.12 seconds include
instrumentation; its 22,874 subprocess calls identify a target, not a baseline
wall-time comparison.

## Scope and behavior

Only `tradingagents/research/admission.py` changes, with the existing
`source_files` loop delegated to fresh finite Git batching. The registration,
charter, selection, runtime, HEAD/ancestry, history, budget and input code remains
unchanged. `verify.py` and amended/extended dialects remain unchanged.

Up to 128 source/design file pairs receive one `git cat-file --batch-check`
query. Source advertised size is compared with current local bytes before body
fetch. Body batches contain at most 8 MiB of advertised bytes, retaining the
count limit. Bodies are requested by the freshly resolved immutable object IDs;
headers must match those IDs and extents. SHA-1 and SHA-256 Git repositories are
supported. Blob type, hexadecimal ID length/format, decimal size, response count,
binary extent, delimiter and trailing bytes are checked. Processes use finite
`subprocess.run` input, capture both output streams and are reaped before return;
new batch process errors are converted to admission `ValueError`.

Each file retains local path checks, final local-byte equality, registered
SHA256 and original design SHA256 comparison. Source lookup normalizes
`Path(name).as_posix()` while design lookup uses the original name. Newline,
carriage-return, unencodable requests and oversized source/design pairs use the
original per-file checks. NUL remains invalid. No cache survives a call.

## Retained executions

The checkout-local locked runtime check passed: Python 3.13.13, no version
mismatches, locked sync check exit 0 and `ok: true`.

| Run | Result | Purpose |
| --- | --- | --- |
| red01 | 51 failed, 0.87 s, exit 1 | All tests failed on explicit missing batching-helper assertion before production edits. |
| check01 | 88 passed, 3.68 s, session 91194, exit 0 | Initial 51 batching cases plus 37 existing lifecycle cases. |
| red02 | 1 failed, 64 passed, 1.05 s, session 30521, exit 1 | Null expected hash reported registered-hash failure instead of original design mismatch. |
| check02 | 102 passed, 4.19 s, session 87045, exit 0 | Corrected null-hash compatibility; 65 batching cases plus 37 lifecycle cases. |

Every run directory retains the exact admission source and new test snapshot,
plus full pytest output. check01/check02 additionally retain the unchanged
lifecycle test snapshot. All failures remain preserved. Test timings describe
test execution only; they are not baseline/candidate optimization measurements.

Focused command, in the reviewed offline profile:

```sh
env -u PYTEST_ADDOPTS PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 RUN_ONLINE_TESTS=0 PYTHONPATH=. .venv/bin/python -B -m pytest -q -p no:cacheprovider --import-mode=importlib tests/research/test_admission_batching.py tests/research/test_lifecycle.py
```

Red commands select only the new batching test file. Imports and fixtures use
invented bytes and disposable temporary Git repositories. Subprocesses are local
Git operations on those fixtures. No network, credentials, research observations
or actual-owner closures occur. The named broad wrapper was not run: the
coordinator restricted this worker to focused tests while another worker edits
shared package sources.

Coverage includes same/distinct commits and SHA-1/SHA-256 repositories; empty,
binary and header-like bytes; space/tab/Unicode/newline/raw unencodable names;
local size and equal-size mutations; registered and design mismatch; missing
source/design paths; forbidden and secret-resolving paths; normalized-source vs
original-design lookup; malformed/truncated/extra responses; process errors;
count and byte thresholds; oversized fallback; mutation during body retrieval;
fresh repeated checks; and independent concurrent calls. Fallback paths also
exercise local, registered-hash and design mismatches. A real-Git counter proves
12 ordinary files need two finite subprocesses, rather than per-file reads.
Existing lifecycle tests cover committed registration/charter/source, selection
and design preservation, claims and further unchanged lifecycle gates.

`git diff --check -- tradingagents/research/admission.py` passed. Source/test
hashes and all evidence file hashes are recorded in `SHA256SUMS`. Sources are
frozen at check02 pending independent review. No commits or remote changes were
made by this worker.

## Remaining uncertainty

The exact isolated profile03 owner fixture and comparable unprofiled baseline/
candidate timings require coordinator execution after correctness review. The
broad offline profile has not been claimed. This bounded optimization does not
change source-check frequency or supply any empirical or financial evidence.
