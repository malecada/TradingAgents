# Independent compact MCM output review

Acceptance withheld for the mapped-file lifetime issue below. Review used source and saved logs only; no tests, numerical jobs or historical runs were executed.

## CMO1 — Exit verification can certify a different inode from the consumed mapping

`compact_mcm_output.py:184–192` pins the initially mapped file, yields its read-only mapping, closes it, then calls `_verified` on the current pathname. It never requires that final verification's file signature equal the original mapped signature.

A concrete failure path is to retain the original valid bytes, overwrite the mapped inode with a different finite value, move that inode outside the output directory, then create a new `matrix.f32` containing the original valid bytes. The consumer can observe the altered old mapping. The output directory again contains only valid manifest and matrix files, so the current final pathname verification can pass despite consumption of the detached changed inode. This is not the documented limitation concerning mutation after the final observation: the identity discontinuity can be checked at context exit.

Keep the original descriptor available through exit verification. Check its pinned signature against both its current `fstat` and the current directory entry, and require the final verified identity to equal that originally mapped. Retain cleanup in all exception paths. Add a fresh synthetic context regression that observes the changed mapped value after replacement and then requires exit refusal. The existing in-place mutation test does not cover replacement with valid bytes. This counterexample was reconstructed statically, not executed by this reviewer.

## Other inspected boundaries and qualifications

Publication validates the exact completed stage, matching-versus-stream score join, external scientific scope and logical output allowance before reserving the output directory. It writes float32 values in retained score order without numerical matching or a full matrix copy, prebinds the manifest content hash, preserves partial namespaces and uses exclusive creation. Postpublication external leases are followed by content verification. The saved reader checks exact output inventory, regular single-link extent, manifest fields and every output byte against the retained float64-to-float32 conversion. These are appropriate within the caller-supplied trusted-reference and frozen-stage contract.

Scratch usage is bounded by chunk size, but `_chunks`' comment that only one score chunk and its conversion are live is not an exact accounting statement. Raw float64 bytes, a float32 ndarray and the yielded bytes copy coexist; `_inspect` also retains expected bytes, short-read pieces and joined actual bytes. Prior loop values may remain live while the next chunk is allocated. No explicit scratch-cap or process-RSS guarantee is established. `max_output_bytes` reserves the raw output plus one metadata cap only. Mapping/page-cache resources remain external, and array views must not outlive the context.

The saved `check01.log` reports **12 passed in 9.27s**. Its positive case compares all 7-by-2 output values, dtype, read-only behavior and exclusive publication. Negative cases cover precreation scope/cap/stage-kind/ref refusal, raw output/source corruption, foreign files and symlink redirection, interrupted publication, late publication callback corruption and in-place mutation during mapping. These do not cover the detached-inode failure above. The supplied stages use real tiny matching evidence but no actual registered output producer, sample/dictionary admission, current OS guard, physical quota or representation closure is established.

Reviewed source SHA-256: `ceb8a7757dd5a78a1804c25a10d7827afa7ebe061180b49030bb65a897e75b5a`.

Reviewed test SHA-256: `70f780801e9dddcc11fd6daca89d81ca1d1fa9411e94bd648734b389ad9d8303`.

These identify inspected files; the pass log is not a complete execution-time dependency manifest.
