# Independent source-only handoff review

Verdict: WITHHELD for reuse of generator efcba9d1. The retained generated drafts independently authenticate; this does not accept the generator's I/O behavior or any installation.

## Material findings

- SH1 — generate01.py:19–30, especially final check at line30: a parent directory replaced during reading by a symbolic link to the retained original directory is accepted. The initial canonical-path check passes, the final Path.stat follows the new link, and the retained file signature matches. The owned real-directory witness preserves original bytes and literal link target. Require anchored traversal and final validation of every parent and leaf; an unchanged leaf inode alone is insufficient.
- SH2 — generate01.py:91–92: the plain output context manager can replace a write MemoryError with its close OSError. The exact extracted output loop ran against an owned concrete BufferedWriter whose controlled write closed its real descriptor and raised MemoryError; actual builtin close then raised EBADF. The first exception remains only in __context__, not as the propagated primary. Use the accepted first-fatal cleanup ownership wrapper and preserve secondary errors. This is a controlled failure-seam witness, not evidence of an actual Root execution failure.

## Authenticated scope

2,076 independent checks authenticate the complete frozen author manifest and modes, original HEAD649, all325 actual Git blob/body/mode joins,194 implementation/149 package closure,193 unchanged bodies, f4ea wrapper and full byte/AST inverse to original e2d. All8 role descriptors and the five unchanged input bodies match actual originals; source_closure has only the wrapper hash substitution, execution_job only the two destination-root fields, wrapper_plan only identity and namespace substitutions. Original model20f451, trainingd527, guards and runtime/scientific implementation remain unchanged. All251 installed RECORD metadata bodies and interpreter/lock hashes were read as opaque bytes. No installed dependency-body recovery or runtime API observation is claimed.

The genuine derive function refused each of194 wrong source pins, an extra source, wrong candidate and invalid first-phase/prior/reference fields. Exact scalar role hash predicates were independently checked; these do not claim a fresh admission or whole future runtime execution. Accepted reader _cleanup retained the original MemoryError after actual descriptor close failure and left that descriptor absent. SH1/SH2 witnesses use extracted actual source, real exceptions, and only owned opaque files.

## Timing and retained failures

The review's original mode comparison mistakenly compared an integer to the author's octal string. HARNESS_FAILURE01 preserves this reviewer error and check02 unchanged. The corrected check03 then encountered a concurrently created proposed destination parent; HARNESS_FAILURE02 preserves the failed freshness assumption. check04 called build only to observe its correct immediate existing-target refusal, then independently reconstructed retained-byte/Git/source joins. It did not bypass the guard, inspect the new capsule, rerun generation or create a target. The author’s earlier atime-signature failure remains included in the authenticated author manifest.

## Authority and untested claims

The draft's new source, design, gate, charter, cumulative19 admission, caller, source review, recovery and source_file_map remain null; release is false. Genuine prospective budget19 review3268 and exact history-copy spec2857 are separate records, not substituted authority. Existing failed/spent claim1 and original18-phase requirements remain unchanged. Actual destination history copy, full source/gate/current=design admission, fresh caller/Owner, recovery and numerical release remain separate Root obligations. No claims, clone, capsule mutation, scientific imports, empirical run, array read, native process, network or Git mutation occurred. No paper-fit, tolerance execution, economic performance, 100-epoch feasibility or capacity conclusion was tested.
