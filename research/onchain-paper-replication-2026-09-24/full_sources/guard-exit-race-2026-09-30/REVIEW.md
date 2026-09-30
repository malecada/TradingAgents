# Independent sampled-RSS guard exit-transition review

September 30, 2026. Source/diff and saved evidence inspection only. No tests, processes, empirical data or historical jobs were run. The registered-hub offline01 source/HEAD freeze remains separate and active; no bound file was edited by this review.

## Failure attribution

The active offline run's saved standard-phase log reports **one failure, 2,767 passes and 97 passing subtests in 1,035.23 seconds**. The failed success/affinity test records child_exit_code=0 together with `resource monitor failed: live process has no VmRSS field`. Thus successful child completion did not produce a successful guard result, and the broad run cannot be called passing regardless of its later neural outcome.

An exit transition between sampling and status interpretation is consistent with this evidence. The old guard did not retain the status snapshot or a second observation, so the exact process state and missing-VmRSS cause are not established. The synthetic reproduction demonstrates the implementation's behavior under chosen transitions; it does not prove that one of those exact transitions occurred in the recorded run. Preserve the original failed result and avoid retrospectively relabeling it successful or solely environmental.

## Candidate behavior

The only candidate code difference is within tree_rss. It permits at most two immediate status/children reads per sampled PID when the first status lacks RSS. A valid RSS field returns its actual value plus recursively sampled children; a fresh second RSS field is not replaced with zero. An observed exact Z or X state, or FileNotFoundError during the process reads, permits zero for the exiting/disappeared process. Persistent live or unknown missing-RSS observations still raise. Invalid numeric RSS still raises ValueError rather than becoming zero. No sleeps, process relaunches, financial retries, cap relaxation or extra third telemetry retry are introduced.

This is a bounded telemetry recheck, not a general guarantee against every procfs/process-tree race. Existing leader-thread descendant scope, prohibition of detached/background and secondary-thread subprocesses, possible shared-page double counting, sampled overshoot, and unchanged failure/kill handling remain. The separate onchain cgroup guard is untouched. The change neither proves a real process tree stayed below an instantaneous bound nor broadens the historical guard's admitted workload.

Saved red01 ran six deterministic checks and retained **four errors** against the old behavior: transition to zombie, disappearance, dead state and second real RSS. Saved green01 reports **six passes in 0.001 seconds** with the correction. Negative controls retain persistent-live and unknown-state failures and invalid numeric RSS refusal. These fixtures independently specify procfs transitions without running empirical jobs. They do not exercise a real scheduler race or re-establish the existing live child memory/wall/affinity checks, which remain required after promotion.

## Promotion disposition

**Accept the isolated candidate for promotion after the active full run closes.** Preserve the dated `research/strategy-search-2026-09-11/resource_guard.py` bytes and historical outcomes. Place the corrected implementation under the maintained `scripts/research_resource_guard.py`, explicitly repoint maintained guard tests, and add the deterministic transition checks there. Inspect the final promoted byte identity/diff and retain focused real guard test evidence before a fresh named broad successor under new source bindings. Do not edit any active run's frozen source, resume/reuse its terminal identity, or attribute its results to the future corrected source.

This acceptance is a narrow code/maintenance decision, not a release of the current failed broad verification or empirical permission. No remaining blocking issue was identified in the reviewed two-snapshot correction itself. Final full-suite closure and promoted-source verification remain pending.

SHA-256 identities:

- Preserved historical guard: `4a4d6d17d144fa769bccd4f799828cc6c63dc55d89a521a24716c0fd17f5cbf1`
- Isolated corrected guard: `a9a285f45dcbdb70340090964eb605f01b908c0dc49f48a08e99b1287237c9f3`
- Synthetic tests: `286ce53b9282957bb714a85366b1fb4c65e533504bddd33cdb794b5604c77f61`
- red01: `f8d936ed5aceb8cef27d201de7b542d6ffacbdbd39a22923d66be0476cae0da4`
- green01: `77f438ccee7d9e694b0f499d09029c18c8b9a26795128d5aa41cd62b6077872d`
- Observed frozen HEAD: `ee50b11de6aedd0f86efbd45e3a3d3f1602d9efe`.

## Promotion and failed-run closure assessment

The original full run is now terminal failed: standard **2,767 passes, one guard failure and 97 subtests** in 1,035.23 seconds; neural **766 passes and two CUDA skips** in 514.67 seconds. Total 3,533 passes does not erase the one failure. Outer guard records child exit 1, cleanup verified, 1,553.721721795 seconds, sampled peak 2,028,310,528 bytes and zero recorded memory events. The exact monitor 3807099 and cgroup are absent. Saved closure evidence hashes match; this failed verification remains unreleased and unrepeated under its identity.

The maintained `scripts/research_resource_guard.py` is byte-identical to the accepted candidate, SHA `a9a285f45dcbdb70340090964eb605f01b908c0dc49f48a08e99b1287237c9f3`. The dated helper retains SHA `4a4d6d17d144fa769bccd4f799828cc6c63dc55d89a521a24716c0fd17f5cbf1`. The old maintained test bytes are preserved and match HEAD; the only edit to that test file is its import path. The separate six deterministic tests now target the maintained helper. Existing three subprocess contracts are unchanged.

Saved promoted-green01 reports **nine passes in 0.29 seconds**. Saved live-green01 independently reports the three isolated candidate subprocess contracts passing in **0.203 seconds**, covering affinity/unlimited address space, explicit setup failure and real synthetic RSS/wall refusals. These overlapping checks are not twelve independent contracts. They support the promoted correction without proving the exact historical race diagnosis or all possible process-tree timings.

**Promotion accepted for fresh named broad verification.** The old dated source and failed full run remain preserved. No onchain cgroup guard or empirical source gate changed. The new full offline02 has its own receipt and binding identity; its result must be assessed independently before engineering release.

Additional evidence identities:

- `promoted-green01.log`: `fee2def07ee7c6cea72f0ba70de4ac51038f426e07fead6cce313f8b5c2707c0`
- `live-green01.log`: `182e0eff320b9a132e0d9ef11893bd00c89a8e8b4370024455747eed5a51320b`
- Preserved old maintained test: `ba267b18c2baaa413dca966aab442d528bd32a1ad41d6e16caeb707281908025`
