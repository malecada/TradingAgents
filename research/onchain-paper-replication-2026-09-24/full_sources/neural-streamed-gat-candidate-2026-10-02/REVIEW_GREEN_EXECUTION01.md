# Independent review of closed failed GREEN01

Disposition: **accepted as a correctly classified, preserved numerical failure; candidate equivalence and GREEN acceptance are withheld**. The actual attempt failed the unchanged full-model comparison after six precursor checks. It did not run the later memory-retention or aggregation derivative checks. No resource-limit failure or material retention/cleanup discrepancy was found. Identity `neural-streamed-gat-oracle-green-20261002-01` is permanently closed and must not be repeated.

Review used read-only source inspection, standard-library JSON/AST/hash and filesystem reconstruction, local Git blob comparison with lazy fetching disabled, archive streaming without extraction, and current process/cgroup/unit observations. No numerical imports, tests, experiment, guard or job were run. Only this new review file was written.

## Exact source and evidence

All 12 references in `green-execution-result01.json` matched their sizes and hashes. All **234 released source pins, totaling 1,819,280 bytes**, matched both current canonical single-link regular files and Git blobs at original execution commit `f3fbf80c0bd69613530c34a8b5f4c9a613551de6`. Reservation, terminal, coordinator and released worker command join that identity, source and release digest. Later shared HEAD changes do not redefine the original source.

Key independently rehashed objects:

- `green-execution-result01.json`: `2c0ee4b3e7821f40aaa1566937cccd602b4a30071e4f3af02895cf44ca2bb068`.
- `green-release01.json`: `dbb77a314e351eee054bce3b4dfd4a8c8da1b7a54ba5e5e56f43eba1642ceaa9`.
- `candidate01.py`: `0cb820710876a4cb59b94b43f1aa8e3e80429d69c35c40a579067eead3ff91b2`.
- `candidate-manifest01.json`: `d4561bb2dcf371ac3207f1ec8144c20bc84cfdeaa3eec8e2961209b05067ffce`.
- `oracle02.py`: `74a21db805cb1ab8e5f7c42a8d54b5f90400b4d794eebb0fbf7d438b41d655ee`.
- `guard_launcher02.py`: `3f8f49f21274381a4a081bba021eff2d0420517399825702193e758e0c0112db`.
- `green-retained-tree01.json`: `d251314e8d2d3f15f14ea21b5f377d13cb6248a207d278c66541ebf13734a6e7`.
- `green-retained-tree01.tar.gz`: `646853efcccfe23e5bb5a6d99198015c97416252071491cd0b16a40f701f3ed0`, 3,716 bytes.

## Actual failure and impact

The coordinator closed with exit 1 after 6.137784981998266 seconds, at 18:09:28.659991 UTC. Guard duration was 5.093866651001008 seconds. The actual worker exited 1 with `reason: workload exited` and no terminal snapshot error. Oracle report, child log and execution summary agree on six ordered passes: mixed/self/isolated layer, zero edges, masking, float64, dropout/RNG, and duplicate refusal.

The next comparison failed at `oracle02.py:179`, after both `model_run` calls returned. Raw traceback records one mismatched element out of 8,448, index `(136,9)`, greatest absolute difference **2.4221837520599365e-05** and relative difference **0.00026740931207314134**. Frozen float32 tolerances remain `atol=1e-6, rtol=1e-5`; the reported rounded `0.0%` mismatch fraction does not turn the mismatch into a pass. Source traversal and the three nested dictionary frames place the failure in the updated-state comparison. Both paths therefore reached their individual forward/backward, Adam step and in-memory save/reload before this cross-path assertion; this does **not** establish equality of their full updated states.

The raw report does not retain the failed dictionary key, tensor values or prior gradient differences. The 256×33 extent implied by the frozen LSTM input/hidden widths is consistent with `temporal.lstm.weight_ih_l0`, but that name is a **source inference, not a measured parameter attribution**. No particular causal mechanism—score reduction, aggregation reduction, optimizer sensitivity or nondeterministic execution—is proved by the traceback. A new bounded diagnostic needs exact named comparison paths and relevant pre/post-update evidence before any source correction is justified. Loosening tolerances or declaring the mismatch harmless would violate this result's acceptance criteria.

The full-model pass marker was not emitted. `oracle-report.json` contains `results: {}`. Aggregation output/all-gradient comparison, gradcheck, central difference, invalid-block refusal, bounded forward/backward block audit, explicit higher-order refusal, and saved-storage classification/reduction were all later in the source and were **not reached** in this attempt. Thus neither reduced retained memory nor complete candidate gradient equivalence is demonstrated by GREEN01. Its lower observed memory peak cannot be compared with the RED peak as a memory-saving result because execution terminated earlier.

The launcher correctly rejects the child exit 1 where GREEN requires 0 at `guard_launcher02.py:133`. Its terminal error is `RuntimeError('child terminal code differs')`; the coordinator traceback preserves that rejection while the separate oracle report preserves the original numerical failure. No expected-RED exception was applied to GREEN.

## Native enforcement and terminal cleanup

Worker-native and guard readbacks match 1,073,741,824-byte memory maximum/high and zero swap in the same original cgroup. All initial and terminal memory event fields are present and zero. Peak **sampled** memory is 372,649,984 bytes; terminal current memory is 9,654,272 bytes. These are not an independently measured full-lifetime kernel peak or a full-size capacity result.

Active native unit evidence retains `LimitFSIZE=LimitFSIZESoft=4194304`, `RuntimeMaxUSec=2min`, MainPID 1097439 and the original cgroup. Worker readback records the same hard/soft 4 MiB limit and CPUs `[0,1]`; supervisor readiness and guard affinity agree. The last per-thread map contains supervisor 1097439 only; earlier workload thread maps are not reconstructed from it. The CPU quota property says `2s`, but the guard reports the quota controller unavailable, so CPU enforcement remains the inherited two-CPU affinity/readback claim.

The guard records the unchanged 120-second wall, 15-second lease, 3 GiB reserve, 4 GiB start threshold, 10 GiB disk floor and sampled 64 MiB storage stop thresholds. Final observed disk free is 20,219,817,984 bytes. Child log is 403 bytes. Elapsed kill and retry are false; no storage-breach/error, cleanup-error or truncation flag appears. Terminal memory snapshots agree exactly between child exit and guard. Parsed guard failure reason, unit properties and cleanup properties all agree on exit-code/status1, failed state and empty control group. Cleanup stop returned 0 and cleanup is verified.

Independent current inspection found monitor 1097187, supervisor 1097439 and workload 1097443 absent from `/proc`, and the original cgroup absent. The retained unit is loaded/failed with MainPID0, empty ControlGroup, Result exit-code and ExecMainStatus1. It is a terminal record, not an active workload.

The native 4 MiB control is per file; storage and free-space checks are sampled, not hard aggregate quotas. The systemd deadline applies to the unit, not all parent verification and preservation work. Actual successful limit readbacks do not imply every hypothetical limit-trigger path was exercised.

## Whole-tree preservation

Independent `lstat` enumeration matched the exact original manifest membership, modes, sizes, hashes and block allocation: **10 regular single-link files, five directories including the owned root, 15 total entries, 20,680 logical bytes, and 69,632 allocated bytes including directory blocks**. No extra member, symlink, surviving hardlink or special file was found. Root device/inode still match the guard's original storage identity. Guard live and final are byte-identical.

All 15 unique tar members under `retained/owned` were independently streamed without extraction. Every file body hash and size, every directory/file mode and all membership/type checks match the original tree. The archive preserves both numerical and launcher failure evidence. Original-host block allocation is not equated with archive/recovery-medium allocation, and this local archive alone is not proof of external recovery.

The last guard sample has 57,344 allocated bytes, 11,491 logical bytes and 12 entries excluding the root. Complete closure adds **12,288 allocated bytes, 9,189 logical bytes and two non-root entries**. This is consistent with the final guard receipt, launcher terminal and final live rewrite; overwritten intermediate live contents are not separately retained. The complete 15-member manifest, not the earlier sampled count, is the final evidence denominator.

## Required next boundary

Preserve this failed attempt and its exact tolerance/source/results permanently. Proceed only with a new explicitly bounded causal diagnostic that distinguishes baseline repeatability from candidate score and aggregation effects and records named parameters, gradients and updates. That diagnostic requires its own reviewed finite source, limits, fresh identity and release; this failure review does not launch or release it. A corrected candidate still needs independent source review and a fresh complete GREEN proof under unchanged criteria before production integration or empirical04 consideration.

No empirical data, financial fit, original-dictionary bridge proof, full-size capacity, paper numerical agreement or broader asset/history/comparison coverage was tested here. The synthetic path is consistent with zero new empirical claims; the complete historical spend ledger was not recounted by this review.
