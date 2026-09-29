# Independent neighborhood-policy integration review

September 30, 2026. Source and saved synthetic-evidence inspection only. No tests, jobs, raw arrays, remote access, source edits or registration changes were performed. Expanded focused evidence and one retention clarification remain pending at this initial review.

## Initial retention finding

**R1 — avoid retaining the previous MCM local graph during the next extraction (`mcm.py`, center loop).** At the next `local=index.neighborhood(...)` call, the preceding `local` is still referenced both by the local variable and by `pairs`. Evaluation of the right-hand side happens before replacement, and replacing `local` alone would leave the old graph in `pairs`. Thus a previous full local graph remains live alongside the next index extraction/output copies. It is not part of the retained sampled-graph allowance. The array component explicitly excludes caller-retained prior outputs, so this is an integration allocation outside that envelope, not a numerical-parity error. Release `scores`, `pairs` and `local` after their result/checkpoint use, or explicitly account for the extra live predecessor graph. A weak-reference assertion before the next neighborhood construction should prove the intended lifetime. This was reported to the author before source freeze.

## Admission, identity and bounds

The new policy requires exactly schema_version 1, mode array and positive nonboolean integer buffer/chunk/sample limits. It accepts no scientific capacity override. Job preflight checks every policy before population work, requires exact job/producer reference agreement, and refuses unused completed-reuse or non-MCM policy. The direct producer independently validates the admitted input/hash and arm before graph iteration or journal claim, and records the policy name/SHA in the claim. Execution fields remain outside scientific/sample/workflow identities. Default consumer/configuration/capacity paths are unchanged.

The sampler's nested ExitStack closes the old array index before constructing another graph's index and closes the final owner on success or failure. Sample retention counts actual node/edge feature and endpoint nbytes before append; an excessive complete neighborhood fails rather than truncates. The transient current output remains within the separately admitted per-index allowance. MCM now owns its array index through the center loop and checkpoint callback. Its context closes on callback failure; R1 concerns graph objects retained by that caller, not index closure.

`check_sample_records` traverses scalar rectangular rows before the graph decoder, requires matching node counts, exactly two endpoint rows, matching edge rows and valid edge width, and computes actual float64/int64 decode payload bytes. The total retained sample payload is checked against its own cap, while twice each individual payload must fit the separate buffer cap for construction/copy coexistence. Validation of actual row lengths prevents understated declared dimensions from bypassing these checks. Parsed JSON/Python metadata, source graphs, validation internals and separately decoded dictionary representatives remain outside these allowances. This is not a whole-process memory limit; the outer guard remains required.

Green01 reports **28 passed in 44.73 seconds**. Initial inspected expanded tests include exact serialized sample records/probabilities/RNG/graph data with both eager and mapped weights, graph-switch ownership checks, retained-sample failure cleanup, MCM callback cleanup, malformed resumed dimensions and decoder-buffer refusal before decode, full producer binding parity and positive job delivery with only the final model batch stubbed. Their expanded execution result was still pending at inspection. Genuine failed-parent continuation coverage was also pending; no such integrated result is inferred from lower-level resume tests.

Initial source snapshot:

- `neighborhood_policy.py`: `f86e19de0bedd4c12ef73fe2ba243990256f592c604c083d8e772ce8131bc12a`
- `neighborhoods.py`: `b53901125dc20dbb8a38b6e0e539866fb04109053afbcba0d75b2a2a8dc38271`
- `mcm.py`: `2defd5961a5d0e07257a5c24a25eaab1bf88fb85e66af0c2f219c9ff49f65a5e`
- `feature_pipeline.py`: `19ebe96275095ded92743a1a1bcadc4178f85cd5d39f1ed23786fba279b5fa41`
- `registered_features.py`: `8a79c459336773bd139f377fe44fe1006796378651d30a8eb22c966c72f7b267`
- `job_payload.py`: `d8af20331d57d30f36bba3fc750ac0e1725ff1080258f2bb64946c5ba2b35f7e`
- Expanded test file: `bb057e59f15c6b22b1c99ba73b43b02cc13f382365bcb9814982b4cb0c96b5b4`

No empirical configuration, sampling permission, matching-capacity increase, resource claim or financial fit is enabled by this implementation review. Full-size matching, whole-fold memory and tighter checkpoint latency remain distinct unresolved requirements.

## R1 correction and expanded review

R1 is corrected in inspected `mcm.py` SHA `d2527cdc34f1032f6ed9a3ff175fd1e7c21412e19e1d449ac53f773bd582f9df`: after copying scalar scores into the output row, the consumer explicitly deletes `scores`, `pairs` and `local` before the callback and before the next extraction. Arithmetic and checkpoint position relative to completed scalar output are unchanged. Retained red02 directly demonstrates two prior-local weak-reference failures, one each for diagnostic and score-only matching. The new regression checks absence before every next extraction and in the checkpoint callback.

The final expanded test SHA is `fb62168a795f4742c737f15175e4fe22c387b18f495c38fb243f4014ce98bbe6`. Its real failed-parent successor fixture durably records a completed graph under default execution, closes the predecessor as failed, admits a new array policy and exact parent reference, forbids resampling/dictionary refitting, and checks complete feature/dictionary identity plus unchanged original failed bytes. This supports samples/dictionary/completed-graph preservation across the policy switch. It does not establish integrated partial-MCM-prefix continuation. The positive job fixture retains real admission, graph loading and representation production while stubbing only the final fit boundary.

Saved green02 reports **65 passed in 100.21 seconds** on the preceding collected suite; it is not attributed to the later R1 correction/new successor tests. Green03 remains pending at this addendum. The inspected finite launcher SHA is `4c1a6cbbd19828b83ee3b3d92c04e4e957066cf3468e0330e9313d2b89ec4d02`. It checks frozen HEAD and all file bindings, validates the 10 GiB policy, then runs the pinned named offline target under 3 GiB maximum/2.75 GiB high, zero swap, 3 GiB runtime reserve/6 GiB startup, 10 GiB disk floor, two-CPU guard default and 3,600-second wall limit. Success requires complete, child exit 0 and verified cleanup. All **141** current source bindings independently rehash correctly; binding file SHA is `f57c26e3a21c01483e1e17cd08a59e4c51daddcd7bdd7728cb8fb0c121119e45`. This launcher/source preparation is suitable for a fresh guarded engineering run after focused closure and normal fresh owner/capacity checks. No broad execution or empirical admission is inferred.

## Final focused acceptance

Saved green03 is now terminal: **89 passed in 144.84 seconds**, SHA `9ce8521cf2562996b89d1a196cb76be05d48e458ee2d9f5059a33af50b7edc62`. This includes both R1 lifetime regressions, actual failed-parent continuation, positive job delivery, eager/mapped-weight exact sample parity and cleanup/predecode checks. R1 is closed by the inspected release ordering and passing direct counterexample. All 141 bindings still match, and current HEAD equals frozen `af9c82c1ec56a0d68dc4add3a92c9b78aed8079a`. IMPLEMENTATION.md retains the substantive memory, checkpoint and empirical limitations without claiming a broader workload result.

Focused source and finite-launcher acceptance is complete for the bound snapshot. One fresh named offline verification may proceed after normal fresh host/owner checks. This does not attest future test success, authorize a terminal rerun or admit any empirical configuration. Prior source hashes, failure evidence and qualifications remain preserved above.

## Terminal engineering closure

The saved named offline01 is complete. Independent child-log inspection confirms **2,768 standard passes plus 97 subtests in 1,060.37 seconds**, followed by **706 neural passes and 2 CUDA skips in 561.38 seconds**: **3,474 passes plus 97 subtests, 2 skips**. Reviewed-profile exclusions remain explicit; unrestricted historical tests were not claimed.

All **141 source bindings independently match**, and frozen/current HEAD remains `af9c82c1ec56a0d68dc4add3a92c9b78aed8079a`. Final/live receipts agree: complete, child exit 0, verified cleanup, **1,625.725651 seconds**, sampled cgroup peak **2,239,954,944 bytes**, zero memory.high/max/OOM events and no limit reason. The command and controls match the reviewed named target and finite profile: 3 GiB maximum/2.75 GiB high, zero swap, 3 GiB runtime reserve, 6 GiB startup, 10 GiB disk floor, two CPUs and 3,600 seconds. Monitor PID 2799571, recorded cgroup and last recorded workload threads are absent. Parent closure-check01 agrees with the independently read counts, hashes and cleanup state.

Terminal evidence hashes:

- Final receipt: `f46c89ce2792e9c438ca91f779871839f0c66c323f8a6fc123e6a2a644d39bd0`
- Child log: `3263fcdd98163a672e1836c99d750919ea9ddfeeedee97dfa4b5bd3d399ac47b`
- Closure check: `78b273b28a007013fd30871a46c97a5ab62439440875ca39ee8f2b36dac22a39`

Engineering closure is accepted for this optional registered neighborhood-policy integration and the corrected MCM lifetime. This supersedes only pending broad verification. The measured synthetic-suite peak is not a full-fold or cold-cache workload guarantee. Parsed JSON/dictionary residency, full matching capacity, tighter checkpoint latency and integrated partial-MCM-prefix cross-policy continuation remain outside the established claims. No empirical gate, census claim, financial fit or frozen study-cap change is enabled. No rerun, array access, source edit or HEAD change was performed during this review.
