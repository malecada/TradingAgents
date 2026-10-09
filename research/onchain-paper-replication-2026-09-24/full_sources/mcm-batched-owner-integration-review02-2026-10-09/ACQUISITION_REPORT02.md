# Focused acquisition follow-up

Six independent failure injections reproduce stranded descriptors. All are synthetic source execution; each leaked descriptor was recorded by successful real `os.fstat` and then closed by the reviewer.

| Location | Failure | Descriptors left open |
|---|---|---|
| `_compute`, token acquisition before try | token open | journal |
| `_compute`, token signature before try | token fstat | journal and token |
| inherited `BatchJournal.__init__` | own descriptor fstat | journal |
| inherited `BatchJournal.__init__` | parent directory open | journal |
| inherited `BatchJournal.__init__` | parent fsync | journal (parent closed) |
| `_checkpoint_inventory` | fdopen of opened body | body descriptor |

The journal constructor defect is inherited from the unchanged accepted journal body; prior acceptance did not exercise these constructor failures. Its historical receipt and source remain immutable. A changed successor must explicitly own this additional cleanup fix; an adapter cannot close a constructor's locally stranded fd when construction raises.

Positive focused cases: spool-open failure closes token and journal; spool-fstat failure closes spool, token and journal; an injected driver boundary callback failure closes all three. In all tested cases the original OSError object is preserved. Cleanup failure precedence itself remains the established `owned_io._cleanup` contract: unresolved closes may raise CleanupFailure containing prior evidence, while genuine fatal exceptions take precedence. No blanket same-exception claim applies when cleanup also fails.

The `_compute` setup also has a callback-free allocation interval between its two try scopes (sink definition and descriptor dictionary construction); allocation failure there can strand all three acquired descriptors. This interval was inspected statically, not experimentally injected. Keep one cleanup scope across the whole acquired-resource lifetime, including signatures, setup and return preparation. The same principle applies inside the journal constructor and around `fdopen`. Retain artifacts, close acquired descriptors exactly once, and preserve the established cleanup-failure precedence.

The output mmap path has explicit matrix-fd finally and outer mapped-close failure handling; `_consume_recovered` enters its fd-finally immediately after open. This focused inspection is not acceptance of genuine Owner/publication/transport execution or all downstream seams. Withheld source status remains in force.
