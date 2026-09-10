# Manual prospective funding collection

This workflow prepares public funding evidence for a later S1 paper-measurement start. No VPS change, scheduler installation, paper start, account request or order is performed by preparing this document. Capture success is not economic completeness or execution readiness. The [source policy](SOURCE_POLICY.md) and [design](2026-09-10-design.md) define the measurement limits.

The [previous manual rollout guide](../operations/MANUAL_ROLLOUT.md) and its release package remain immutable. That package predates funding capture. The superseding [funding source archive](/home/malecada/master_thesis/funding-release-2026-09-10/ta-source-7d2a0ae9ef4ad707774360d2f67af40258a7d2e3.tar.gz) is pinned to `7d2a0ae9ef4ad707774360d2f67af40258a7d2e3`, contains 288 files and has SHA-256 `3d3dbc688322abba70a0f0a208bf6bbaee0ca42cbb8791d01d9584a87606490c`. The [release record](verification/release-package.json) verifies its allowlisted files against the commit and its source-identity fallback without Git. The archive has not been uploaded or deployed. Its plain `SOURCE_COMMIT` file identifies source; it does not by itself verify package contents. Verify the archive checksum and marker against this record before collection.

Use an already provisioned interpreter with the required dependencies and an immutable source release. Do not upgrade the shared environment or copy source over either running checkout as part of collection. The operator must provision a dedicated writable capture directory and a persistent lock directory, separate from historical stores and paper journals. No environment file is sourced; the collector uses its public client without account credentials.

The following is a manual collector invocation after those prerequisites. It uses the reviewed source commit; confirm each absolute path. The existing interpreter is shown explicitly; dependency failure requires review rather than an automatic installation.

```bash
set -euo pipefail

TA_FUNDING_COMMIT=7d2a0ae9ef4ad707774360d2f67af40258a7d2e3
TA_FUNDING_SOURCE="/opt/tradingagents/releases/ta-source-${TA_FUNDING_COMMIT}"
TA_FUNDING_PYTHON=/opt/tradingagents/venv/bin/python
TA_FUNDING_ROOT=/opt/tradingagents/funding-captures
TA_FUNDING_LOCK=/opt/tradingagents/locks/s1-funding-capture.lock

[[ "$TA_FUNDING_COMMIT" =~ ^[0-9a-f]{40}$ ]]
test -x "$TA_FUNDING_PYTHON"
test -r "$TA_FUNDING_SOURCE/SOURCE_COMMIT"
test "$(cat "$TA_FUNDING_SOURCE/SOURCE_COMMIT")" = "$TA_FUNDING_COMMIT"
test -r "$TA_FUNDING_SOURCE/scripts/predlab_capture_funding.py"
test -d "$TA_FUNDING_ROOT"
test -w "$TA_FUNDING_ROOT"
test -d "$(dirname "$TA_FUNDING_LOCK")"

(
  flock -n 9 || {
    echo 'Funding collection already holds the persistent lock.' >&2
    exit 75
  }
  env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$TA_FUNDING_SOURCE" \
    "$TA_FUNDING_PYTHON" -B \
    "$TA_FUNDING_SOURCE/scripts/predlab_capture_funding.py" \
    --output-root "$TA_FUNDING_ROOT"
) 9>>"$TA_FUNDING_LOCK"
```

The default selects the current eligible metadata universe; its count can change. An explicit subset uses space-separated symbols through `--symbols BTCUSDT ETHUSDT`, but such a subset is not sufficient for a later book holding other names. The source window covers nine UTC calendar dates through one fixed exchange-clock cutoff, including the partial current date. Each invocation creates a new timestamped directory with a unique suffix. Retain the printed snapshot path, final status and all request outcomes.

Prospective hourly collection around `:20` UTC is the proposed operating cadence, allowing time for documented post-settlement schedule updates. It is not installed by this workflow and does not guarantee observation of every change. Every invocation for the same collector must use the same persistent lock; never delete or replace that lock while a process might hold it. The source defaults to one-second request pacing. Funding requests share an IP quota with other processes, so this pacing is not a reserved allocation. A 429 or 418 stops collection; preserve the run and respect the restriction instead of immediately retrying, switching identities or launching another collector.

A nonzero exit, missing final manifest or `partial`/failed status must not be relabeled as full success. Preserve failed and partial directories, raw responses and any normalized files. A retry creates another directory; it never completes a prior snapshot in place. Inspect the manifest's requested-symbol denominator, per-symbol outcomes, query cutoff, timing, hashes and exclusions. Do not automatically choose the newest directory or silently drop unavailable instruments. A usable subset of a partial snapshot is subject to the reader's validation and the complete needs of both books.

Snapshot use is a separate, later paper boundary. The reader is opt-in through `--funding-snapshot` or `S1_FUNDING_SNAPSHOT`, naming one specific immutable snapshot directory. A configured missing or invalid snapshot produces WAIT without fallback to the legacy funding store. Pair preflight requires usable funding for the relevant held exposure of both books, complete required closing prices and current quotes, and valid account state before either append. Collection alone does not supply the other prerequisites. No executable paper-start command is provided here; `--offline` also writes paper journals and is not a smoke check.

Paper invocations must also be serialized across manual and scheduled callers. Pair preflight is not a transaction or a concurrency lock: a crash between appends can leave one row written. Preserve that row and its input provenance. A same-day retry retains the already written row and attempts the remaining book only after preflight; it must not truncate, overwrite or duplicate the first row. Existing broken or gapped chains require a separate disposition rather than a reset disguised as a retry.

The timestamp matching policy was committed as `7654889` before use. Only raw event times in the inclusive interval `[UTC hour, UTC hour + 1 second]` may receive a derived hourly comparison label. Raw timestamps remain unchanged; daily membership remains `[D 00:00, D+1 00:00)`. The following boundary must be an actual captured event. Earlier timestamps, larger offsets and multiple distinct events mapping to one hour are not silently aligned. The one-second bound is an engineering policy, not a Binance guarantee. [Timestamp amendment](2026-09-10-timestamp-amendment.md).

Cash funding remains the existing signed daily approximation. Current interval metadata cannot establish historical schedules, and missing faster events can resemble a slower regular grid. These qualifications remain even when every request succeeds. No coverage totals or financial conclusions are asserted here; the finalized capture report must provide the observed denominators and limitations.
