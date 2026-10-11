# Fixture02 changed-seam review

Decision: **REFUSED_FAILURE_REPORTING_REPAIR_REQUIRED**. Original C/adapter source acceptance and fixture01 overwrite refusal remain unchanged.

**P1 — false success after traceback-storage failure, fixture02.py:77–80.** The exception handler writes failure.txt before assigning failure. If opening or writing the traceback raises, finally sees failure=None and writes PASS_FINITE_SYNTHETIC despite an original numerical failure. The escaping exception is also the reporting error, with the original retained only in its context. The independent counterexample executes the actual except/finally AST with a synthetic ValueError and a synthetic OSError from the traceback target. It records a PASS result with failure=null. No fixture, native loader, scientific module or numerical case was executed.

Mark failure before any fallible diagnostic formatting/storage; keep the original exception authoritative and retain reporting exceptions as secondary. The final status must remain FAILED even if traceback generation, string conversion or output fails. A missing/incomplete result on abrupt or storage failure must never become success. Preserve this candidate and use a new successor.

The other changed seams pass: exclusive attempt reservation occurs before raw descriptor redirection and native/science imports; repeated reservation and result creation refuse without changing an earlier synthetic failed result; original artifact references match the frozen candidate manifest; and the numerical body and criteria are byte-identical. Both literal inverse patches match. The native library was not read. Outer caller exit capture remains necessary for refusal before redirection and fatal termination.

The first reviewer check expected fixture01.py/fixture02.py patch labels, whereas the actual preserved patches use fixture.py for both. That failed check and stderr01 are retained. check02 corrects only that header expectation; its twenty checks establish the findings above. It does not repeat prior C or numerical matrices.

No execution release is granted. The active pilot, old artifacts, Main and registration remain unchanged.
