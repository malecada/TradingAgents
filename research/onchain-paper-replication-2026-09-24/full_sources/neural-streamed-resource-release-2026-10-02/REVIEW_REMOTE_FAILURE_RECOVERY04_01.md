# Independent neural04 remote failure-recovery review

Disposition: **accepted for the reported selected external recovery scope.** The complete archived three-root neural04 failure bodies/modes and 25 selected closure/release/source blobs are recoverable in the fresh remote-retrieval namespace. This does not alter the closed failed outcome or establish complete recovery of all study source/input bodies.

Reviewed recovery report SHA-256: `599d9ab0ca2c8f69a73b338ccc93efb71db4d2a448c9b453187b871f05272552` (`REMOTE_FAILURE_RECOVERY04_01.json`).
Fetched backup commit: `9cf4cf815c2aef5b288b1c0eebb99400bbd60854`.
Actual execution source: `8631cbcce34cf827f0551dad04f6822ca8e1e1ec`.
The backup commit and execution source have different roles and are not substituted for each other.

## Independent recovery checks

The fresh `failure-remote-recovery04-01/repository.git` resolves FETCH_HEAD to the exact reported backup commit and reports a shallow repository. Each of the **25** retrieved regular blobs was compared against its report hash/size, the existing fixed-commit Git blob in that bare repository, and the retained original selected file. All match, totalling **440,369 bytes**. Reviewer Git reads used GIT_NO_LAZY_FETCH=1 and protocol.allow=never; no additional network retrieval, object fetching or FETCH_HEAD change occurred.

The independently retrieved archive is **29,965 bytes**, SHA `17a1353ca08105cb1816616ac14719ee980bfff8cddbed322736495945f96706`; retrieved inventory SHA is `8e8ad5d1c8d4f3fb011e3334d5306a4fd97cbe634b9823a79ec2a464f963096d`. Streaming inspection, without extraction, checked all **32** member names against the independently retrieved manifest: **21 regular files and 11 directories**, including each control/lifecycle/producer root. Every file size/body SHA and every file/directory mode agrees. There are no duplicate, foreign, absolute, traversal, symlink, hardlink or special members. Total regular-body extent is **145,567 bytes**. The original manifest's file/directory allocated-byte sum independently reconstructs **249,856 bytes**; this is original storage accounting, not predicted allocation on recovery media.

All **16** outer references in the retrieved execution result are among the recovered selected files and match their individual hashes/sizes. The selected set also includes the failed-result review, additive PID correction, charter/job/scheduling/caller/helper, preserved first collector and its failed traceback, corrected collector and recovery script. It therefore retains reporting failures as well as corrected evidence. No raw failure evidence was replaced by a cleaned summary.

The coordinator separately reported successful execution of the fresh remote fetch/retrieval. Inspection of the pinned recovery script confirms that the route checks actual remote branch HEAD, creates a new bare namespace, requests depth-one blob filtering, retrieves the selected fixed-commit bodies and writes each file exclusively before checking the archive. Its code contains no numerical imports, restored-code execution or empirical replay. A bare repository or script alone would not prove remote transfer; the external-recovery conclusion uses that reported actual execution together with the independently verified resulting objects and bodies. This reviewer did not repeat the transfer, inspect credentials/configured remote URL, or infer that only 25 Git objects traversed the network.

## Failure and identity preservation

The retrieved result remains SHA `c6471bcf5ce7ed042f510dfb6326628adbc2f3e6a63d0a436f5ebcbf48b89129`, with independent failed execution review SHA `943e7fb9cf4aa823002781e1613ccf4bd1c02a98a9ac2717a4e914ddd0713c0b`. The recovered lifecycle claim SHA is `a14c14a320475942ec45a9423ae20626e235b08b3cf4de21cf8a8f04f0098bfd`; its exact experiment object equals the recovered gate, its registration hash matches gate `b5d83f7ed997acb1de09032efe2ecbe989b2ee20200a7da3637d28e0117b603d`, and its source is the original execution commit. The recovered failed terminal links that claim exactly and equals the result's terminal.

Recovered admission/readiness/intent remain distinct from the earlier deferred observation. Readiness contains 16 observations spaced at least two seconds apart over 30.006151485 seconds, minimum 7,272,259,584 bytes above the 7,247,757,312-byte threshold. That sequence proves a passed scheduling observation, not sustained memory capacity.

Recovered guard memory events equal the result: max 2181, oom 2, oom_kill 3, oom_group_kill 1, high/low zero. The bounded kernel journal names the exact unit and CONSTRAINT_MEMCG, including the additional task PID and group-kill statement. These support the retained kernel-OOM failure. No child Python exit receipt is invented. The producer's schema2 journal contains nine markers ending in forward_before, with no returned forward/backward/update/checkpoint proof. All nine postmortem cell IDs exactly equal the claim's original denominator and remain unavailable. The archive contains no checkpoint or completed cell outcome; one attempted forward does not constitute nine observed OOMs or an exact required-RAM measurement.

PID addendum SHA `e445b0a191fadde29247e0d1250e41591fe3a4299ef365610f02d331331fce80` correctly links the original result and kernel journal, preserves the prior omission and records all five identified PIDs absent. This review checks that retained closure evidence and linkage, not a new live process/cgroup inspection. Native CPU quota, postmortem sampling and complete final-versus-earlier storage qualifications remain those of the accepted execution review.

The recovered actual claim adopts ceiling 64. The retained independent execution review/result records 36 spent attempts = 27 complete + 9 failed, no refund and zero new financial fits. This recovery review verifies the current claim and those retained accounting assertions; it does not independently recensus every historical claim/terminal. Identity04 remains permanently closed and cannot be replayed under this recovery proof.

## Scope limits

The 25 selected blobs include the gate and source manifest, not all 249 registered source bodies, all 109 scientific/input bodies or a restorable full runtime. Prior original raw data, other study attempts, full repository recovery, numerical capacity, paper agreement and 1,420 financial fits are not established here. Directory modes and logical file contents are preserved; uid/gid, timestamps, sparse layout and identical filesystem block allocation are not recovery promises.

No tests, numerical imports/deserialization, checkpoints, restored code, resource job, admission, claims, extraction, SSH, network fetch, deletion, source edit, ledger edit or Git mutation was performed by this review. Only this new review file was written.
