# Independent initial review

Acceptance withheld pending the following bounded correctness corrections. Source and saved evidence were inspected; no tests, remote operations or empirical jobs were run by the reviewer.

1. **APW1 — acknowledgement after an unchecked callback.** `archive_pair_writer.py:110–111` calls `_archive_check()` after the inherited PairLog has performed its exact event readback. This invokes the external lease again. A callback that changes the newly acknowledged record once `log.events` advances is followed only by start/policy/root checks, so `begin`, `progress` or `complete` can return with damaged acknowledged bytes. Retain the expected final record and original chunk identity and verify them callback-free after the final callback. A later rotation/finish refusal does not repair the earlier acknowledgement.

2. **APW2 — constructor failure dispatch uses uninitialized cleanup state.** At lines53–55, `super().__init__` can call the overridden `close()` on a start-write or post-start lease failure before `root_identity` has been assigned. The final close at line301 then evaluates the missing attribute before entering `_close_attempt`, leaving the opened root descriptor unclosed and replacing the primary failure. Make cleanup safe for the inherited construction phase while retaining one-shot descriptor ownership; test both publication and lease failure after the root descriptor exists.

3. **APW3 — disposal loses the original chunk inode.** Lines122–124 close the original writer descriptor and read the current pathname without joining it to the original `chunk_identity`. The later content comparison at line166 proves bytes, not ownership. Equal valid bytes in a substituted inode can therefore be archived and deleted, contradicting the contract that only this writer's newly owned chunk is disposed. Pin the original descriptor/identity through archive and final pre-disposal verification; reject pathname replacement before deletion.

4. **APW4 — failure markers do not stop disposal or acknowledgement.** `_archive_check` does not reject root `failed.json` or `cleanup-failed.json`, including dangling links. A final mapping callback can add a root failure marker and still permit lines168–170 to delete local evidence and the next append to return. Root inventory is checked only at terminal replay. Refuse these conflicts before further acknowledgement/disposal, with a callback-free check after the final lease.

5. **APW5 — ordinary error on an uncertain owned child close.** Line84 uses raw `os.close` for the directory descriptor opened by `_archive_check`. If it fails, outer abort can successfully close the writer and rethrow ordinary `OSError` although that child descriptor's cleanup remains uncertain. Use the shared fatal cleanup contract for this newly owned descriptor and verify remaining independent cleanup still occurs.

The separately identified duplicate terminal invocation is addressed by the new early `not self.closed` guard outside the aborting path. The only difference from preserved `writer-check01.py` at inspection is that guard. Raw check01 reports **86 passed in1.33s**; raw check02 reports **88 passed in1.45s**. These suites do not test the five boundaries above and do not establish real network operation, current-owner/stage admission, checkpoint-tree or score-stream joins, restart/recovery, empirical source eviction or measured physical/RSS bounds.

The successful metadata allowance is internally consistent: each archived chunk retains mapping/disposition, two copy receipts and three consumed-read receipts, totaling seven metadata files; the fixed margin covers start/archive-start/terminal/archive-complete plus failure overhead. This is a logical allowance with finite chunk count, not a physical quota or transport/global concurrency bound. Existing old local routes remain unchanged.

Inspected SHA-256:

- Current source: `5cf6d79032347b0928ef5aa58af8d7647e2ddac993d1ceeafb87af80f868590c`
- Current test: `b53c98fcf405f6e1ea228d43f6620b51ae2741acdd0f982696058e1b8ec831f3`
- Preserved check01 source: `5b3ad8dc53b072a6c7bd0dd15c41be2cf4665148b40116041ba404c7a62b8dca`
- check01.log: `85946a933918f1675be534c7d79c66b167fa2972e0d457ba541ad0728e43f5aa`
