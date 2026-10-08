# Xsect retirement readiness — no mutation

Observed2026-10-08T23:03:42Z. Original `/home/malecada/master_thesis/TradingAgents/data/xsect` and recovered `/home/malecada/master_thesis/onchain-pilot-recovery/xsect-posix-recovery-20261009-01` each contain3783 regular files,14 directories and6,915,716,585 logical bytes. Allocated bytes including directories: original6,924,103,680; recovered6,924,247,040. Both device66310, no nonregular entries or multiply-linked files observed. Current available bytes18,120,257,536.

| Conditional action | Projected free bytes | Draft23 margin | Historical full-pilot margin |
|---|---:|---:|---:|
| Keep both |18,120,257,536|-6,130,191,451|-14,179,495,651|
| Retire original, keep recovered |25,044,361,216|793,912,229|-7,255,391,971|
| Retire both |31,968,608,256|7,718,159,269|-331,144,931|

Draft23 exact PREPARATION_RESULT02 requires13,513,030,747 declared allocated growth +10,737,418,240 floor =24,250,448,987 free bytes. It is DRAFT_NOT_REGISTERED_NOT_ADMITTED and reserves only one partial first-stage checkpoint diagnostic. Historical final20 ACTUAL_STORAGE_REFUSAL01 requires32,299,753,187 bytes and separately refuses aggregate writable scope logical capacity (required24,558,127,461 versus limit17,179,869,184; required allocated26,708,147,939 versus limit21,474,836,480). Deletion cannot cure that distinct budget refusal. A future full-seven model may differ; neither comparison is admission. Reclamation is conditional on final links/open references/shared extents and intervening filesystem activity; remeasure free bytes after any authorized action.

## Existing consumers and process observation

Two actual preserved predlab symlinks point directly to original `funding` and `klines`: `TradingAgents-predlab/data/xsect/{funding,klines}`. Active-checkout `scripts/predlab_xfam_lib.py:24` defines MAIN_WT as sibling TradingAgents; line123 reads original `klines_1h`. `scripts/predlab_oflow_p0.py:46` uses that same original store. Original `TradingAgents/scripts/xs_mom_dev.py:52` reads data/xsect/klines; original fetch_xsect_funding.py:27-30 declares writer paths under the same original store. These are source dependencies, not evidence those scripts currently run. Scoped Python search of `tradingagents/research/onchain_replication` found no xsect references.

One bounded /proc cwd/root/fd-link observation covered413 processes and4335 readable links: no matching original/recovered-tree links,263 denied accesses and1 process race, no scan limit reached. No environments, command lines, body contents or denied-access retries were read. This is incomplete observation, not proof of absent users/writers; closed descriptors, mmap-only users and later opens are not excluded.

## Concrete conditional route and refusal

Read-only rerun: `.venv/bin/python -B research/onchain-paper-replication-2026-09-24/full_sources/xsect-retirement-readiness01-2026-10-09/inventory.py` regenerates only this owned inventory; it neither hashes payloads nor deletes anything. Preserve the current receipt before rerunning.

Root-only retirement may use the original-only option after accepted independent byte/mode/mtime/currentness review, explicit writer exclusion or accepted concurrency risk, fresh exact namespace identity, and separate authorization. Declare a relocation mapping from every original relative path to the recovered root. Preserve existing consumer access through an explicitly approved compatibility link at the original root or explicitly retarget the two predlab links and every direct consumer; a mapping document alone does not preserve executable access. This changes original namespace identity, so references requiring real directory/no-symlink/original inode must be marked retired and restored before reuse. Do not silently substitute a symlink into the historical snapshot contract. No compatibility link or source edit was installed here.

Retiring both would leave the known consumers unavailable unless restored from external preservation first, and still misses the historical full-pilot free-space requirement by331,144,931 bytes at this snapshot. It is not recommended as a capacity solution on this evidence. Refuse any claim of ready deletion or full-pilot capacity from this inventory alone.

Retain outside either retiring tree: CONTENT_ROWS01.json and DIRECTORIES01.json with exact hashes; BATCHES01 start/stop/index mapping; all29 archive/manifest identities and numeric tar-member-to-original path mapping; external transport bindings/receipts and retained remote object identities; restoration contract/helper/source hashes; complete/terminal/root-pin/batch receipts; independent outcome review with all3783 hashes and14 directory metadata; and a new relocation/retirement receipt enumerating exact namespaces and lost inode/ctime identity. Mapping, remote availability and recovery evidence must survive independently of reclaimed payload trees. No owner/scientific/trading credit, writer exclusion or retirement permission is inferred.
