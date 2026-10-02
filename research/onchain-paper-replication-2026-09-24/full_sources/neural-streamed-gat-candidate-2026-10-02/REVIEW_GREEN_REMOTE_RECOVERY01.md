# Independent review of GREEN failure remote recovery01

Disposition: **accepted for the four selected recovered objects and complete 15-member owned archive**. This is preservation verification of a failed numerical attempt, not GREEN acceptance, a candidate rerun or new empirical evidence. No material discrepancy was found.

Review was limited to read-only source inspection, standard-library hashes/JSON/archive streaming and local Git reads. Review Git commands set `GIT_NO_LAZY_FETCH=1` and `GIT_TERMINAL_PROMPT=0`. No network request, retained-content execution, archive extraction, numerical import, test or job occurred. Only this new review file was written.

## Fixed recovery lineage

The original recovery repository `green-remote-recovery01/repository.git` has `FETCH_HEAD=9b1ad313b34d6cbe10475e5fd804896cc28cf6b5`, exactly matching `GREEN_REMOTE_RECOVERY01.json`. The shared checkout had subsequently advanced to `dba18089034416baadfa0019dfd03eb1c8ee38f2` during inspection; this does not invalidate the fixed fetched lineage. The original failed GREEN execution source remains `f3fbf80c0bd69613530c34a8b5f4c9a613551de6`.

Recovery source `recover_green01.py` is 4,952 bytes, SHA-256 `d9111947ba0016f85ddba029d68f95151eedf8441afdde1bff89d14d2a88d972`. The completed recovery report is 1,351 bytes, SHA-256 `e68d01d7d2f11deb0a38f8cc409cb7eb2148ec746f1ddf2ca7cf33a47a52b520`.

The source checks the then-current remote branch against the intended source, creates a fresh exclusive output directory and bare partial Git repository, fetches that exact commit and retrieves the four selected blobs. It opens recovered outputs and the final report exclusively. Archive contents are streamed for comparison, never extracted or executed. The completed report and existing fetched objects support the coordinator's recorded actual remote recovery; this review did not repeat a network observation. A local repository alone would not prove a remote fetch.

Finite safeguards include a 10 GiB initial disk floor, inherited 4 MiB per-file limit, 60-second timeout per Git subprocess, 1 MiB selected-blob bound, exact fixed inventory and expected body totals. Captured subprocess output size is checked after capture; this is not a hard in-memory output cap, whole-operation deadline or aggregate storage quota. No stronger enforcement claim is needed for the actual small completed recovery.

## Independent content verification

All four recovered files are single-link regular files. Each matches its report size/hash, original retained local object, and the Git blob at the fixed fetched commit in both the recovered repository and shared repository:

| Object | Bytes | SHA-256 |
|---|---:|---|
| `green-retained-tree01.tar.gz` | 3,716 | `646853efcccfe23e5bb5a6d99198015c97416252071491cd0b16a40f701f3ed0` |
| `green-retained-tree01.json` | 3,443 | `d251314e8d2d3f15f14ea21b5f377d13cb6248a207d278c66541ebf13734a6e7` |
| `green-execution-result01.json` | 7,952 | `2c0ee4b3e7821f40aaa1566937cccd602b4a30071e4f3af02895cf44ca2bb068` |
| `REVIEW_GREEN_EXECUTION01.md` | 9,507 | `f34a93474211fe48c3d7c7af477c6a6791e2f014241cf23cf63934ba7196eba2` |

The archive was independently streamed in full. All 15 unique members under `retained/owned` match the manifest exactly: **10 regular-file bodies and five directories including the root**, with every body size/hash and every file/directory mode verified. No missing, duplicate or additional member, link or special type was admitted. File bodies sum to **20,680 logical bytes**. Manifest block counts sum to **69,632 original allocated bytes including directories**, consistent with the accepted original-tree inspection. Original filesystem allocation is not archive size or recovery-medium allocation.

The recovered evidence preserves both failures: the oracle's full-model tensor-comparison mismatch after six precursor passes, and the launcher's rejection of the nonzero GREEN child exit. It also includes original native controls, guard receipts, child exit/readiness/log, reservation and terminal. Recovery does not convert those failures into passes or establish the unexecuted derivative, block-bound or saved-storage checks.

## Scope and continuation

Acceptance covers these four recovered objects and the complete owned archive. The other outer references and 234 original selected source pins remain referenced but were not separately recovered by this operation; installed runtime binaries were not attested. No new financial fit, empirical claim, full-size capacity or candidate equivalence follows. Original GREEN01 is permanently closed. Preserve this recovery source/report/directory and review, then continue the independently reviewed fresh causal diagnostic under its own release and identity.
