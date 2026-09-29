# Independent synthetic census-engine review

September 30, 2026. Initial source/evidence review only. No synthetic tests, empirical graph bodies, jobs or network calls were executed by the reviewer. This prototype is outside the active neighborhood-policy freeze. It has no execution release.

## Initial findings

**R1 — metadata reserve and completion ordering (`census_engine.py:46–54,109–111`).** The accepted identity can approach 16 KiB and is serialized independently in both phase receipts, summary and final phase receipt. Four such copies consume essentially the entire 64 KiB fixed reserve before other JSON fields and four NPY headers. The maximum accepted identity can therefore violate the admitted disk envelope. The post hoc size check runs only after `summary.json` and `03-summary.json` are published. Reserve the actual bounded serialization/file overhead before creation, and validate the terminal envelope before publishing completion evidence. Preserve the initial failure rather than narrowing the accepted fixture after observing it.

**R2 — cleanup stops after the first failed close (`census_engine.py:113–115`).** If counts-map close raises, keys-map close is never attempted. The cleanup exception also replaces a primary body exception. Attempt every owned close independently, preserve a primary exception with explicit cleanup context, and refuse success on unresolved cleanup. A synthetic injected counts-close failure should prove the keys close attempt on both normal and exceptional exits. These findings were reported before source freeze.

The formula currently bounds logical file sizes, not allocated filesystem blocks or wrapper artifacts. Target-volume allocation rounding and bounded wrapper metadata must be accounted separately or included explicitly before any 512 MiB disk claim. A post-write check alone is not preventive admission.

## Algorithm and denominator assessment

The numerical design is correct by inspection: each non-self directed edge maps to `(min(a,b),max(a,b))` encoded by `lo*N+hi`; reciprocal and duplicate edges therefore share one key. Self-loops use negative sentinel and contribute no additional neighbor. The maximum allowed N=3,037,000,499 keeps N²−1 within signed int64; endpoint-domain validation precedes allocation. In-place sort followed by streamed uniqueness uses the previous block's last key, so duplicates straddling block boundaries are counted once. Counting both distinct endpoints and initializing every node to one includes isolates and centers, without sampling or capacity truncation.

The result retains exact all-node cardinalities, original-order maximum indices, histogram and count above 10,000. The independent explicit-neighbor-set oracle in the saved seven-test run meaningfully exercises reciprocal/duplicate/directed edges, self-loops, isolates, random chunk-boundary invariance and a 10,002-node complete star. Green01 reports **7 tests passed in 3.086 seconds**. Its output-identity refusal test retains prior files unchanged. A checkpoint failure fixture retains the first completed phase while leaving no final summary. These tests do not yet address R1/R2, runtime containment or actual target filesystem allocation.

Numeric disk formula 8E+32N covers keys, per-node cardinalities, worst-case maxima and histogram payloads. For the previously verified metadata N=2,764,221 and E=3,504,159, the initial logical formula with 64 KiB reserve evaluates to 116,553,880 bytes; this is arithmetic from compact prior metadata, not a new graph measurement. Runtime uses mapped keys/counts, bounded edge chunks and additional full-node masks/bincount/histogram arrays. There is no standalone numeric-memory admission in this prototype. The proposed outer guard and a concrete simultaneous-allocation analysis must qualify any workload memory claim.

Exclusive new output-directory creation and exclusive metadata/NPY writes retain interrupted identities. Flush, fsync and directory sync precede phase receipt publication. Phase hashes bind durable outputs, but no partial-DB or intra-sort resume protocol exists. A future registered successor must preserve the old failed identity and cannot silently rerun it.

## Release prerequisites

The proposed 540-second **whole-job** wall limit can provide failure containment below 600 seconds only if it covers all empirical mapping, hashing, sorting, counting and output/checkpoint work, with monitoring/termination grace also within the remaining margin. It does not prove that the workload completes in 540 seconds, provide intra-sort progress, or establish resumability. The exact launcher/guard linkage remains to be reviewed. Independent source corrections, bounded JSON/block accounting, complete input/node-order/config hashes, output denominator verification, a committed exact lifecycle gate with the accepted cumulative allocation and complete ancestor lineage, plus fresh owner/host/storage admission remain required. No empirical execution is accepted here.

Initial hashes:

- Engine: `60ed2a7239b12b74a1e96b98c0f8ebc176acd2f96269af5f18cb024f13dd7131`
- Tests: `2006ff07c7bf0e850622bcb4de027ecb828fd4e1f4ef5ac06aa87e3bd15c68e1`
- Green01: `999dc464c9e2c4a9cb83d7b506bc3615748e20c0af71d9454bd288695973771b`

## Corrected prototype assessment

R1 is resolved for the explicitly **logical-file-byte** allowance. The reserve is now 128 KiB, sufficient for four bounded identity copies plus fixed headers/metadata. Before either summary completion file is written, the implementation constructs both exact encoded bodies, adds their lengths to all existing file sizes and checks the full total against the admitted reserve. Red02 retains the maximal-identity overflow counterexample; the same case passes in green03. For the earlier compact N/E metadata, the revised logical reserve is 116,619,416 bytes. Filesystem block allocation and wrapper artifacts remain separate and require target-volume admission/measurement; this correction does not establish a physical 512 MiB bound on its own.

R2 is resolved in source. Cleanup attempts counts and keys independently, collects all close exceptions, adds them as notes to an existing primary exception, or raises a cleanup failure when the body otherwise succeeded. Return cannot report successful engine completion if cleanup fails. The injected regression closes then raises on counts, verifies the keys close attempt and verifies preservation of the original phase failure plus cleanup note. This proves the tested exceptional-exit path; the otherwise-successful-body cleanup-failure branch is supported by inspection rather than a separate injected test. Ordinary success and failures at all three callbacks verify all real maps close. A durable numerical summary can remain after a later callback/cleanup failure; future lifecycle/guard terminal status must remain authoritative, and preserved phase files are not permission to restart that identity.

Saved green03 reports **10 tests passed in 0.265 seconds**. The numerical algorithm and denominator are unchanged. Corrected engine/source-level acceptance is granted for continued registered integration preparation, with no remaining material prototype finding identified. It is not empirical release: generic job routing and explicit 10 GiB outer/worker contract linkage are not yet implemented/reviewed for this census. The 540-second whole-job guard, complete registration/source/input/output bindings, actual allocation accounting, fresh resource admission and independent final release checks remain mandatory. No graph body or census measurement was accessed by this review.

Corrected identities:

- Engine: `be4704d1b19028c2ce734c35483986d6b49d7eecd6f6bd9048c96208b51c02a9`
- Tests: `76a495ae0424d3865f3b93ff9d927d378b80ec63cd938be8337bb9cf636041c9`
- Green03: `7632f7a2cc64c172327bfe919082f03ecb8dfba3776f7b03645c0bf9fc6d5adc`

## Synthetic scale verification

The separately guarded synthetic scale result is accepted within its fixture scope. Source builds a shuffled directed ring with **3,000,000 nodes and 4,000,000 edge columns**, including duplicate ring edges. Every node has exactly two distinct neighbors, hence cardinality 3; unique non-self pairs equal 3,000,000, every global index is a maximum, and histogram is exactly `[[3,3000000]]`. The saved worker checks every cardinality and maximum-index block plus that full histogram, not a sampled subset. The summary's cardinality/maxima file sizes each equal 24,000,128 bytes, consistent with 3,000,000 int64 entries plus the recorded format header. These are saved worker assertions and metadata, not an independent array reread by this reviewer.

All **seven frozen source/runtime bindings independently match**, with frozen/current HEAD `af9c82c1ec56a0d68dc4add3a92c9b78aed8079a`. Closure-evidence hashes match their actual compact files. The guard is complete with child exit 0 and verified cleanup: **5.751070 seconds**, sampled cgroup peak **198,012,928 bytes**, zero high/max/OOM events. Controls were 1 GiB maximum/0.75 GiB high, zero swap, 3 GiB host reserve, 4 GiB startup, 10 GiB disk reserve, two CPUs and 180-second wall limit. Monitor PID 3218467, recorded cgroup and last recorded workload threads are absent.

Worker elapsed is **5.205721 seconds**. The engine's **1.384061-second** elapsed value is captured internally before final file hashing, summary/checkpoint publication and cleanup; it is not full end-to-end census-call timing. Metadata-only stat reconciliation confirms **80,002,799 logical bytes** and **80,039,936 allocated bytes** across eight census files. These sums exclude the later `verification.json`, guard/source receipts and directory allocation; they are not a total experiment-storage measure. The engine's logical reserve for this fixture is 128,131,072 bytes.

Relevant evidence hashes:

- Scale bindings: `9b99fdf14ee880fb07de1e11fab21e5a44cb3cf7a89bb09c25d76c74a73bf548`
- Guard final: `29dd0cd2d8200882427feec5fff8d5e7e03b34044fe4f1229d6b3d1b71bc5d45`
- Verification: `5b8dd79bb4a99c77d0342483a638b1962c88677256d831ad760b19d96293306d`
- Closure check: `aea163b6e33cfb615b8545c5596bf9b8e38a81f8fb84395d564b3c8352ce9bfa`

The ring supplies a useful exact large-array oracle and observed execution envelope. It does not establish empirical graph validation/hash/loading cost, arbitrary topology or degree-distribution performance, full matching/neighborhood feasibility, cold-cache memory requirements or actual registered 540-second completion. All empirical release prerequisites remain. No tests, downloads, empirical inputs or array bodies were opened during this review.
