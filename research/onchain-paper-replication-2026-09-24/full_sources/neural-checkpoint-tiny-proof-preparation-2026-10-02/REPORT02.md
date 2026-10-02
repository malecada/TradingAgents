# Terminal first-fatal correction02

The frozen01 protocol, numerical fixture, tolerance and source files remain unchanged. New `oracle02.py` and `coordinator02.py` address the independent review's actual terminal-assembly failure gap. They explicitly select `source-manifest02.json`, and coordinator02 invokes/imports oracle02 only. No numerical import, model output, native job, claim, production change or Git mutation occurred.

## Changed boundary

The shared actual `terminal_boundary` now encloses one phase-close attempt, one terminal assembly attempt, encoding and at most one publication attempt. Worker `phases.report`/deepcopy and exception string conversion execute inside assembly. Coordinator unattempted-arm padding, active PID access and exception string conversion also execute inside that boundary. The first observed actual fatal (MemoryError or any non-Exception BaseException) keeps precedence over later assembly, serialization or publication failures. An actual fatal discovered after an ordinary primary is raised with the earlier primary retained as its cause. Existing actual fatal objects are not replaced by freshly formatted wrappers.

If assembly fails, no complete terminal body exists and publication is not attempted. No fallback PASS, invented complete report, retry, overwrite or reclaimed identity is produced. If assembly succeeds, exactly one publication is attempted; a publication error leaves the attempt failed even if a partial file exists. Outer native collection/cleanup must preserve the actual exit and remaining raw phase/start/log files. Missing terminal evidence remains missing, not accepted completion.

Exception retention previously formatted secondary failures with repr, which itself could fail. New precedence selection uses identity/type checks and fixed diagnostic text only. A best-effort fixed BaseException note is attempted only when an earlier actual fatal already exists; failure to allocate that diagnostic cannot replace that prior actual fatal. Ordinary-primary precedence needs no annotation allocation. Cause attachment for a newly selected actual fatal is best effort and cannot replace the selected fatal if attachment fails.

`Phases.close` captures an already observed sampler error before stop/join/liveness checks, attempts those independent operations once, then rejoins the sampler error. The same observed first-fatal rule applies. Thread runtime failure and cleanup failures cannot fabricate sampler completion. Phase report allocation remains protected by terminal assembly. The outer unit still owns descendant cleanup; no successful child cleanup claim was added.

## Verification

All checks use the pinned local Python and extract actual source functions/terminal tails through AST, with stdlib-only IO/error stand-ins. They never import Torch/NumPy or replace a numerical model.

- `legacy-terminal-red02.log` reproduces the concrete frozen01 bug by executing its actual main terminal tail: a later SystemExit from phases.report replaces the original body MemoryError. The original source is unchanged.
- `terminal-red02.log` retains six initial failures before the new boundary existed.
- `terminal-green02.log` records six passing regression methods. They cover body MemoryError/SystemExit followed by ordinary or fatal assembly failures; phase-close and publication attempted once; later actual fatal promoted over an ordinary primary; exception __str__/__repr__ failures; publication failure never returning success; and actual worker/coordinator routing with explicit02 source-manifest selection.
- `terminal-green03.log` repeats only those affected checks after the final diagnostic-note allocation restriction. A new source/AST comparison verifies the numerical fixture, arm, comparison, profile and protocol bodies are unchanged from01; native/runtime numerical behavior remains unexecuted.

These are error-handling/source checks only. Neither numerical parity nor resource fit is established. Same-unit sequential fresh-process design, all native limits, fixed cases,147 correctness markers and22 markers per profile, sampled-memory qualifications, checkpoint publication dependency behavior and all original release requirements remain as documented in PROTOCOL01.md. Root must review and pin02 in a new native caller/release before the single future engineering execution.
