# Compact MCM output and saved reader

The maintained `compact_mcm_output.py` publishes an exclusive raw little-endian
float32 matrix with an explicit row-major shape/dtype manifest. It consumes
completed compact matching and score evidence; it does not repeat matching or
allocate a complete output matrix. Every saved output byte must equal the
float32 conversion of the corresponding retained float64 score. The complete
stage verifier also joins matching purposes, scores and retained checkpoints.

External arguments must identify the exact stage receipt, contract and scientific
scope. Hashes alone are not registration, dictionary-training admission or a
representation seal. The output manifest explicitly records execution as not
admitted. The distinct registered publication adapter supplies current-owner and
output-policy joins; full native integration remains separate.

The logical output reservation is four bytes per cell plus an 8192-byte manifest
allowance, checked before namespace creation. Scratch is proportional to chunk
size, including overlapping conversion/read copies. Memory mapping, page cache,
physical allocation, prior matching evidence and runtime need their outer guards
and reservations. No full-size capacity or throughput measurement is claimed.

## Closed synthetic checks

| Identity | Result | Evidence |
| --- | --- | --- |
| red01 | 12 missing-module failures, 0.59s, session34625 exit1 | `red01.log` |
| check01 | 12 passed, 9.27s, session42039 exit0 | `check01.log`; preserved `output-check01.py`, `test-check01.py` |
| red02 | 1 failed, 12 deselected, 1.59s, session9202 exit1 | `red02.log` |
| check02 | 3 passed, 10 deselected, 3.62s, session85334 exit0 | `check02.log` |

The fixture performs fourteen real compact checkpoint-engine comparisons. Tests
cover exact conversion/read-only access, external scope and budget refusal,
changed source/output, redirection, exclusive identities, interrupted writes and
late callback mutation. No financial data, model fit or resource pilot is used.
Temporary numerical fixtures are not an externally recoverable raw-data archive.

Independent review identified a detached mapped-inode vulnerability. The red02
case changes the inode read by the consumer, moves it outside the output and
restores valid bytes under the original path. Previously pathname verification
could pass. The corrected context retains the original descriptor through exit
and compares its original signature with both the current pathname and final
verified signature before closing. Check02 covers this regression, ordinary
during-read mutation and the successful publication/read path. The earlier
twelve-case run is not represented as a combined thirteen-case final-source run.

Initial review and final acceptance are retained in `REVIEW.md` and
`FINAL_REVIEW.md`. The final review SHA-256 is
`ac1c0b21f9aff81ab78a82f0cd77bf3949a59837037aa6929716b570941fb6e4`.
Consumers must remain inside the mapping context and acknowledge downstream work
only after successful exit. Verification is sampled, not an atomic snapshot or
protection against arbitrary replacement of Python methods/private pins.
