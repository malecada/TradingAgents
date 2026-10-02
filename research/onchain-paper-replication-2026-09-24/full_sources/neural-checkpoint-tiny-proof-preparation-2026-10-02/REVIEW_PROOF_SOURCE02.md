# Independent checkpoint tiny-proof source review02

Disposition: **accepted for the narrow TCP1 source correction and continued native-release preparation**. No remaining material TCP1 source blocker was found. This review does not authorize a native invocation, numerical experiment, empirical successor or financial fit. The withheld01 review and every predecessor source/evidence file remain preserved.

## Reviewed identity and independent checks

| Object | SHA-256 |
|---|---|
| manifest02.json | 8f9e6d7c5bdd7196d3f7c8a990f8409e209e63991a611e078857062e3bac67f2 |
| source-manifest02.json | 91e2027627b8213a746c191117c94a0cb1e1693242e453f8654407100b4418d3 |
| oracle02.py | 0a3efd885cbecb3019839a8aeed291aff7ac33071726c16efae1129867905530 |
| coordinator02.py | bacd5e42d0fd0c1ac73fa81de68f9a44a8e043ab161a96b951752dea7912971c |
| unchanged protocol01.json | c56c494966b42a5d15cead7f1bb51e1eb3d9e18cfeab91d2831eb743aa072d1c |

All 13 manifest02 members were independently read and rehashed as regular, single-link files, totaling 63,866 bytes. All 19 original manifest01 members remain byte-exact, totaling 83,627 bytes. All 17 selected source-manifest02 members were independently rehashed, totaling 1,463,194 bytes. This is a selected source closure, not a claim to attest every installed runtime binary. Both published patches reproduce the actual01-to02 source differences exactly.

AST comparison found only close_once, preserve, Phases and main changed in oracle, with safe_note and terminal_boundary added. Numerical fixture, comparison, Saved instrumentation, arm, run_correctness, run_profile, step, optimizer construction, forward/loss, gradients, clone_state, native checks and write_new are unchanged. Protocol/tolerances/cases remain unchanged. The numerical and protocol review in REVIEW_PROOF_SOURCE01.md continues to apply; its TCP1 withholding is resolved only for the new02 source.

## TCP1 resolution

At oracle02.py:64–80, terminal_boundary catches errors from the close action, assembly and publication independently. Assembly is attempted once; publication occurs at most once and only after a complete body has been assembled. Any selected error is raised rather than returning success. Failure to assemble produces no fabricated terminal; publication failure cannot return success merely because a partial or complete file now exists.

The actual worker route at oracle02.py:360–366 places phases.report (including deepcopy) and exception string conversion inside assemble, then places JSON encoding and write_new inside the protected publication callback. The concrete01 counterexample—an original body MemoryError followed by SystemExit from phases.report—therefore retains the original MemoryError object in02. An ordinary body failure followed by a first actual fatal selects that fatal and attempts to chain the original ordinary failure.

The actual coordinator route at coordinator02.py:52–61 similarly protects denominator padding, active-child PID access and exception formatting during assembly, then encoding and publication. Its import, manifest selection and child command select oracle02/source-manifest02 consistently (lines18,27,39). Child return code alone cannot establish success: lines48–51 additionally require the correctly identified passed terminal. The enclosing native launcher must likewise reject a missing/failed coordinator terminal. Preserving a SystemExit object is not a promise that its embedded exit code is nonzero.

The reducer at oracle02.py:36–61 avoids arbitrary secondary repr/str formatting. Once an actual fatal has been selected, later ordinary or fatal errors cannot replace its identity. Fixed best-effort notes cannot replace it if note allocation fails. A first actual fatal discovered after an ordinary error is selected directly; cause attachment is best effort. This is precedence among errors observed by the boundary, not a global temporal ordering guarantee across threads.

Phases.close at oracle02.py:138–146 captures an existing sampler error, attempts stop, join and liveness checks independently once, then rejoins the recorded sampler error. The unchanged write_new finally at line98 delegates independent descriptor closes to the corrected reducer with sys.exception(), preserving a body fatal while attempting both closes. No new claim that the coordinator itself owns descendant cleanup was introduced; its terminal explicitly delegates that responsibility to the outer native guard.

## Evidence strength and remaining requirements

The retained legacy RED dynamically executes the actual frozen01 main terminal tail and reproduces the original fatal-identity loss. The new six-method GREEN suite dynamically executes AST-extracted actual shared terminal_boundary/preserve/safe_note/close_once functions with stdlib stand-ins. It exercises original MemoryError/SystemExit identity, later-fatal promotion, formatting failures, one-shot close/publication, publication failure and the successful no-error control.

The final GREEN log repeats those six methods; it is not six additional independent methods. Actual02 worker/coordinator wiring is checked by AST/text assertions and independent source tracing, not by executing their complete main closures. The source routes are coherent, but these logs must not be described as an end-to-end02 main or native-runtime test. No tests were rerun for this review and no numerical module was imported.

The unchanged five-case correctness denominator, 147 correctness markers, 22 markers in each of two fresh profile processes, production checkpoint/reload/continuation comparisons and first-failure/unattempted-arm accounting remain prospective. The saved-storage instrumentation and sampled fresh-process profiles answer different questions; neither establishes full-graph first-forward, recomputation-backward or actual training-batch capacity. The 28-distinct-graph synthetic case is not evidence that an empirical batch contains 28 distinct weekly graphs.

Remaining release work is the separately owned exact native launcher/source/runtime binding review, committed and recoverable release evidence, fresh resource/identity/duplicate-process checks, and one admitted finite execution with all raw outcomes and cleanup retained. Numerical parity, native control enforcement, actual production checkpoint publication/reload, full-size capacity, empirical successor admission and financial wrapper admission remain untested by this source review. Closed historical identities remain closed and are not retry targets.
