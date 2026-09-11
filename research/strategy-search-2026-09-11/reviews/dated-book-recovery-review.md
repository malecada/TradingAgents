# Dated-book resource failure and recovery review

## Disposition

A separately registered resource correction is justified in principle. Final
execution admission remains conditional on review of the concrete wrapper,
correction charter/gate and invented full-pipeline preflight. No financial
experiment or empirical reconstruction was executed in this review.

## Independently retained evidence

The failed run `research_runs/dated-book-20260911` contains a claim and failed
receipt, with no result files. The structural receipt verifier passes: failed
status, zero completed cells and zero outputs. This is **eight intended cases
with no completed cell verdicts**, not an eight-cell economic rejection and not
zero attempted configurations. The claim retains all eight identities, fixed
inputs, exposed windows, source `d287a1420d70e298bae9b0f7e69fdc79c665720e`
and gate hash `ef446526b30409cfd32a5c0175a3b58ed3953248fac71ca2a9465cf8f5085ee6`.
The terminal reason is `MemoryError: ` and its output hash map is empty.

Source inspection at `dated_book_run.py:117` through `:134` shows that book
objects are computed before the lazy statistics import at `:105`; the first
result write is after `evaluate` returns at `:178`. The coordinator reports
failure during that import under `ulimit -v 524288` and no inspection of the
in-memory financial values. The receipt proves absence of durable results; it
does not independently prove the exact import traceback, shell limit, peak
resident usage or absence of transient human inspection. Preserve the original
traceback and command as coordinator provenance where available. Do not recreate
them by rerunning empirical inputs.

## Resource diagnosis and recovery boundaries

`RLIMIT_AS`/`ulimit -v` bounds virtual address space, including reserved/mapped
space. It is not a measurement or cap of resident physical memory. Consequently
this failure does not demonstrate that the pipeline requires over 512 MiB RSS.
The old charter specifies 512 MiB without defining its memory metric; the
correction must explicitly disclose the changed enforcement rather than
retroactively redefining the old run as compliant or complete.

The proposed child `dated-book-resource-correction-20260911` must name the failed
book as parent, retain the original experiment object exactly, and preserve the
same family, input hashes, dates, eight cases, costs, accounting, statistics and
screens. The lifecycle counts each claim, including failures
(`admission.py:81`, `:218`). One historical prior attempt plus the archive and
failed book consume three of the four family administrative units. The child
uses the third and final new allowance. These counts are administrative attempts,
not independent hypotheses; the windows remain exposed. No favorable economic
adaptation is supported by the retained evidence.

The corrected wrapper should explicitly clear inherited virtual limits, cap
execution at 120 seconds, constrain numerical threads and CPU affinity to two
CPUs, and report sampled resident usage plus Linux child `ru_maxrss` in KiB.
A 20 ms RSS sampler is a detection policy with possible transient overshoot,
not an absolute instantaneous kernel memory cap. Its scope must include every
allowed worker process, or prohibit worker subprocesses explicitly. Monitor
failures, killed children and partial evidence require retained terminal resource
records; no automatic retry follows. A full invented fixture must exercise the
real statistics import and pipeline under exactly that wrapper before freezing.

## Untested claims

Financial values, economic screens, fees/fills, mark-based margin safety,
statistical coverage and external backup equality have not been tested here.
The specific unresolved correctness question is whether the concrete monitor
enforces and retains its declared resource procedure; no broader or higher-effort
economic analysis is warranted before that question is resolved.

## Concrete recovery review, before final freeze

The proposed correction gate preserves every previous experiment object and all
family/dataset metadata. Independent byte checks confirm unchanged original
financial sources, input identities, windows, eight cases and statistics, with
only the new wrapper/entry point, resource output and correction charter added.
Preloading statistics before admission is a justified way to discover dependency
failure before opening inputs. The correction still uses the unchanged evaluator.

Two concrete pre-freeze findings require resolution:

1. `dated_resource_preflight.py:7` uses constant spot fixture prices. The real
   statistics module imports, but its rank guard returns unavailable before
   performing OLS/HAC. Thus the saved successful resource measurement does not
   cover the full intended statistics path. Use invented noncollinear BTC/ETH
   paths and require complete exposure calculations for all eight cases under
   the exact wrapper.
2. `resource_guard.py:37` can raise during launch or pre-exec limit setup outside
   its reporting path. `main` reserves the report at `:78` but leaves it empty.
   An independent invented missing-executable counterexample returned exit 1
   and a zero-byte report. Persist a structured launch failure, including
   unavailable child metrics, and retain the exclusive no-overwrite rule.

The original process-tree claim also exceeds its implementation: reading only
`/proc/<pid>/task/<pid>/children` omits children created by other threads, and
the monitoring loop ends when the leader exits even if descendants survive.
Either explicitly restrict the supported process model to the known synchronous
financial child/helpers with no detached/background descendants, or implement
complete traversal and descendant cleanup. This is a resource-scope limitation,
not evidence of a financial-book defect.

## Final concrete disposition: PASS

All three pre-freeze findings are resolved within the declared scope. The final
preflight uses two distinct invented sine/cosine price paths and asserts complete
OLS/HAC exposure calculations for all eight books. The earlier singular-design
resource record is retained separately. Launch/setup exceptions now yield a
structured failed monitor record with unknown child metrics and no retry. The
resource contract is explicitly limited to this single financial process and
its synchronous leader-thread Git helpers; detached/background or secondary-thread
subprocesses are not admitted. No generic daemon supervision is claimed.

Independent verification ran the three focused guard tests successfully, then
exercised the real CLI with a nonexistent invented executable: exit 1 and valid,
nonempty JSON failure evidence. A second independent invented full-pipeline
preflight under the exact CLI wrapper passed all eight books and OLS/HAC checks
in 3.551 seconds. Peak sampled RSS was 215,887,872 bytes; the Linux child peak
was 213,140 KiB. These values establish headroom for that invented fixture,
not a guarantee about the future empirical invocation. No empirical input or
financial result was evaluated.

Final byte checks again confirm unchanged historical gate objects, financial
sources, four input identities, dates, cases and budget. The corrected resource
policy, sampled overshoot limitation, exposed sample and final remaining attempt
are explicit. There is no unresolved blocker to the separately registered child
after the required committed/pushed freeze and preservation of the failed parent.

| Final artifact | SHA256 |
|---|---|
| `resource_guard.py` | `4a4d6d17d144fa769bccd4f799828cc6c63dc55d89a521a24716c0fd17f5cbf1` |
| `dated_book_correction.py` | `1359933f91a9f5b68e21c22351a9ee42f1fc2eda5cdf0b73a102f245d236decc` |
| `dated_resource_preflight.py` | `050b3bca82dc838c79366ee030d96c2f3636e632026bfa6fbc0430ebad2f9df0` |
| `dated-resource-correction-charter.md` | `f3fa6813e3a14d6202fda59f5e31473286b025d31e397aed4535d1efb4cd718f` |
| `gates-dated-correction.json` | `2fe1fef99d9b9f6c2454ac705e0bf89753b79f3a83d34c875ae8bd0eaae73322` |

The untested economic, actual-execution and external-backup claims listed above
remain unavailable. No higher-effort review is needed for the resolved resource
question. A completed empirical result still requires independent raw-input cash
and exposure reconstruction before interpretation.
