# Metadata fingerprint limitation and deterministic fixture correction

The named offline profile returned1911passed/81subtests and one failure in
HeritageTests.test_partial_error_and_concurrent_change_bytes_charged. Its fixture
rewrote a short file with the same length immediately before the second fstat.
It assumed the rewrite necessarily changed mtime_ns or ctime_ns. That assumption
is not reliable even though those fields are expressed in nanoseconds.

A separate100-case invented-file reproduction yielded84complete and16unavailable
classifications. In a retained complete example all five compared identity fields
were equal before and after, while the captured body hash differed from a later
read of the rewritten file. This demonstrates both the nondeterministic fixture
and the frozen reader's observation limit; it is not merely an irrelevant test
failure. No actual Q4 metadata file was reopened or altered in this diagnosis.

The test now explicitly changes the invented file's mtime by1second after its
same-length rewrite, deterministically exercising the **observable identity
change** rejection. It uses no sleep. The frozen heritage_source.py, Q4/Q6 gates,
claims, outputs and original raw stores remain unchanged. No source retry or
financial trial is created by this engineering test correction.

Interpret original successful fingerprints as **no metadata identity change was
detected during this read**, not proof that no concurrent rewrite occurred or
that the source path remains an immutable snapshot. The recorded hash describes
the captured byte stream; the original `complete stable file` digest_scope label
must be read with this narrower qualification. The source reader already states
that later changes do not automatically preserve the previous file version.
The Q4/Q6 schema/provenance-unproved findings and lack of economic validation are
unchanged. No universal concurrent-change detection or archived-vintage guarantee
is established by those results.

F2 uses preserved public-response bytes and pinned input/source content hashes;
it does not import or execute heritage_source.py. This diagnosis therefore does
not alter F2's recipe or source protocol. The focused failed module and all new
financial/accounting source tests must pass before F2 execution. The named profile
is reported with its observed failure and subsequent focused resolution, not
misrepresented as a clean original run.
