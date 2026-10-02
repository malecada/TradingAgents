# Independent remote recovery of the closed neural attempt

**Verified actual retrieval from the configured origin**, using a new isolated shallow, blob-filtered bare repository. Remote branch HEAD at the capability check and the fetched exact commit both equal `e0cb08b6bf763ffec0bb4058d5d1d89bd3977486`. The server advertised filtering before fetch; depth-one verification found exactly one commit. Object inventory with lazy fetching disabled found one commit, 3,834 trees and exactly three blobs. No fallback full clone occurred.

The only retrieved file blobs were:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| retained-tree01.tar.gz | 23,725 | `cc2575307c51817d154d537fe6b1a7dfa3b2305de8b1fd81ab3dcab94faac862` |
| retained-tree01.json | 8,638 | `5785244060110608e9100b6d52c8a4661eeb01176de94565e280ae8d06e406d0` |
| execution-result01.json | 4,998 | `f01e981f0864ebcd37c202764a07ea13039121c0fdfa6766200f998716dabdfe` |

The independently retrieved result's archive/manifest hashes and lengths agree. Streaming the retrieved archive verified every one of its 20 regular files and 11 directories against the independently retrieved manifest, including exact names, parent-directory membership, types, modes, sizes and content hashes. Duplicate, absolute, noncanonical, foreign-root, special and link members were rejected. Total regular-file contents equal 107,458 bytes. No archive member was extracted and no recovered code was executed.

All nine bounded Git commands exited zero; the longest took approximately 2.122 seconds. Enforced per-command timeout was 120 seconds, with 64 MiB individual output-file limit, 128 MiB isolated-tree allowance and 1 MiB stderr/packet bounds. The isolated tree occupied 1,790,681 logical bytes before final report publication. The object-inventory warning merely notes that a promisor repository may omit unloaded objects; the three-blob count is the intended retrieval scope. No origin URL or credential value is exposed in these reports. Transport endpoint configuration was ephemeral; bounded fetch stderr was redacted. Session 79182 closed with exit code zero.

Raw logs, capability trace, verification script, fetched bare repository and retrieved blobs are retained under `/home/malecada/master_thesis/onchain-fixture-isolation/neural-backup-verification-20261002-01/`. The machine report `REMOTE_RECOVERY01.json` has SHA256 `6199a47c8cb0a6d33e5c5f89c3ef856aaec10118d50d8e6c2bbdadb629be54c3` and records exact local evidence hashes. The verification script is a single-use operation, not an empirical resume command.

This establishes off-checkout recovery of the exact closed neural attempt's retained three-root evidence, independently of the older owner-fixture backup. The two raw journal captures and other outer evidence are hash-referenced by the retrieved result but were not separately retrieved in this deliberately three-blob operation. The archive itself contains every retained control/lifecycle/producer file. This proves recoverable bytes at the observation time, not permanent remote availability, whole-environment reproducibility, a successful neural capacity result or paper agreement.

Only these new reports were added to the shared checkout. HEAD, source, runtime, registrations, inputs, empirical roots and existing evidence were not changed. No job, model, array, financial experiment or restored-code execution occurred. Reports are left uncommitted while the separate fixture work proceeds under its frozen source.
