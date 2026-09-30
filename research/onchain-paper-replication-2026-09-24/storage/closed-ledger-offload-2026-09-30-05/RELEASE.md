# Actual conditional preservation05 release

Graph08 producer and saved-array verifier now have independently accepted complete
closures, with absent owners/cgroups. Source graph07 producer and verifier remain
accepted. Storage04 is closed and accepted. Preserve only the original graph07
ledger: 3,760,664,576 bytes, original hash and exact current stat identity in manifest.
No prior body verification or transfer is repeated by preparation.

Actual free space at release preparation is 18,390,093,824 bytes, below December's
22,103,159,134-byte planning requirement. Full recovery scratch requires
14,514,860,032 bytes. Fresh preflight must still establish a deficit, sufficient
scratch, RAM and no active replication units; skip if unnecessary. Potential
reclaim is not current space and may still be insufficient after other disk use.
Keep the 10 GiB floor, 256 MiB maximum, 192 MiB high, zero swap, two CPUs,
3 GiB reserve, 3.5 GiB startup, 14,400 seconds and 5,400-second transport deadlines.

Original 30 bindings stay unchanged. Contextual release adds actual accepted
storage04, source07 and preceding08 verification closures,08 producer closure,
December projection, prerequisite helper and preflight. Independently review,
commit and push these exact compact files before one preflight and one launch.
The exact local connection metadata remains hash-only, unprinted and uncommitted.
Review indirect dependencies beyond the worker's direct-input eligibility check.
Future local ledger verification requires hash-verified restoration; preserve the
original artifact index. No raw or graph array is moved.

Launch offload.py once with the pinned runtime only after preflight passes. Freeze
HEAD and original/contextual bindings while active. Full upload/recovery/hash,
restoration metadata verification and durable receipt/sidecar precede source
revalidation and unlink. Completion metadata roundtrips too. Preserve all failed
or partial evidence and never relaunch the identity. Graph09 exact gate remains
absent until actual accepted05 closure; no financial experiment is admitted.
