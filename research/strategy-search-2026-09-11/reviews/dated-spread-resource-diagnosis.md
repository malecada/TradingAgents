# Dated spread resource diagnosis — September 11, 2026

The single attempt from `6d6d65f9712dd41e135672a2f0fb8a7d8389507b` exceeded the registered 120-second wall limit. It did not exhaust the sampled RSS limit. All three outputs existed before termination, but no successful terminal receipt was produced. The subsequently reviewed failure closure preserves those outputs and the consumed attempt; it does not convert the run to successful completion.

This diagnosis used source, claim/receipt metadata, file timestamps and saved resource reports only. No book was evaluated again, no output financial values were parsed, no admission was attempted, and no frozen runtime or ledger was changed. A further profile was unnecessary for the bounded conclusion below.

## Observed evidence

The actual guard reports 120.0511 seconds, exit −15, `wall-clock limit exceeded`, and peak sampled aggregate RSS 418,467,840 bytes against 536,870,912 bytes. This supports a wall-limit termination, not an out-of-memory diagnosis. Sampling does not establish a continuous memory maximum.

The claim records start at `2026-09-11T11:49:04.276789+00:00`. Its execution contract contains eight inputs, 18 source-file pins and 26 runtime-module pins. Filesystem timestamps observed after closure were:

| Artifact | Bytes | Modification time UTC | Seconds after claim timestamp |
|---|---:|---|---:|
| books.json | 1,003,789 | 11:50:27.927374 | 83.650585 |
| summary.json | 37,815 | 11:50:37.357352 | 93.080563 |
| source-audit.json | 22,305 | 11:50:46.577331 | 102.300542 |
| failed.json | 894 | 11:53:29.496943 | 265.220154 |

The last row is the later reviewed closure, not the original process's termination time. File modification times are filesystem evidence, not instrumented function timings or monotonic-clock observations. The guard begins before the claim is created, so its 120-second duration must not be equated with 120 seconds after the claim timestamp.

The saved exact-CLI synthetic preflights completed in 29.7015 seconds (full), 30.4008 seconds (partial) and 28.9609 seconds (unavailable). Their peak sampled RSS values were approximately 419–432 MB, comparable to the actual run. The smaller disposable lifecycle proof took 14.9431 seconds. Those passing fixtures established interface, denominator and representative financial-path execution checks in invented repositories. They did not establish the wall cost of repeated validation against the actual accumulated registration/source/artifact history.

## Supported inference and its limits

`dated_spread_run.main` evaluates the inputs once, assembles all outputs, checks their total serialized size, writes the three outputs in the observed order, then immediately calls `finish`. There is no additional financial evaluation between these writes or after the third write. Consequently the retained output set supports that financial evaluation and output assembly had already occurred; successful lifecycle closure remained outstanding.

Each `write_json` first repeats `_check_source`, which calls complete `admit`. Each of the eight `read_input` calls also does this. Startup calls `admit` twice, including under the exclusive lock. `finish` repeats admission once more, then rehashes all inputs and outputs before publishing completion. A successful path therefore requires 14 complete admission passes: two at startup, eight reads, three writes and one finish.

Each admission repeats current claim/source checks, historical artifact and physical registration preservation, the five-predecessor grant proof, and the nested closed v2/v1 reconstructions. The source readers invoke separate Git subprocesses for committed blobs. Repeated references are visited across these layers. The approximately 9.43-second and 9.22-second gaps between output modification times, despite the latter outputs being only tens of kilobytes, are consistent with substantial repeated validation cost. They do not isolate Git latency from filesystem I/O, scheduling or serialization.

The probable engineering cause is therefore an unrepresentative history-cost preflight combined with repeated nested validation on the hot path. It is not proven that the kill occurred inside a particular Git call, admission function or `finish` statement: no interruption stack or phase-level monotonic trace was retained. Serialization, final input/output hashing, lock acquisition and scheduling remain possible contributors. The evidence does not justify attributing an exact fraction of runtime to financial calculation or claiming a specific speedup.

## Prerequisites for any future financial CLI

Before another separately authorized investigation, the wall budget must be demonstrated using the actual preserved history shape and artifact sizes: a read-only admission/history proof plus a representative-history disposable no-op/full-retention lifecycle under the exact guard, including all reads, writes and terminal publication. Phase timing and subprocess counts should be retained in that synthetic engineering proof. A small invented ledger alone is insufficient.

Any separately reviewed runtime redesign should avoid unnecessary recursive Git/blob validation while preserving equivalent immutable source, current-file, live-inventory, locking and per-operation tamper checks. An immutable content-addressed proof reused within an operation could be assessed with adversarial mutation/concurrency tests; caching or skipping checks is not authorized by this diagnosis. All four existing runtime packages, gates, certificates, outputs and failure receipts must remain unchanged.

Retained-output forensics can proceed within the existing failed attempt's scope. This report provides neither an eighth grant nor a rerun instruction, and it does not establish scientific validity or economic success.

Evidence: `dated-spread-actual-guard.json`, `dated-spread-failure-closure.json`, the three `dated-spread-cli-preflight-*-guard.json` files, `dated-spread-lifecycle-preflight-guard.json`, `research_runs/dated-spread-book-20260911/claim.json` and artifact stat metadata; source `dated_spread_run.py`, `research_spread/lifecycle.py`, `admission.py`, `grant.py`, and independent snapshot modules.
