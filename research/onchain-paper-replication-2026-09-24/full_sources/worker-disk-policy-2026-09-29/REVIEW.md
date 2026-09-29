# Independent worker disk-policy correction review

September 29, 2026. Source/diff and saved-evidence review only; no tests, probe, raw reads, credentials or remote actions were executed by the reviewer.

**Accepted as a narrow guard-admission correction.** `assert_guarded_worker` retains its **20 GiB default** while accepting an explicit integer, nonboolean requirement of at least **10 GiB**. Invalid declarations fail before receipt I/O. The actual live guard floor must meet or exceed the declared requirement, so an explicit 20 GiB caller cannot run under a 10 GiB guard and a stricter actual guard remains valid. The 3 GiB runtime RAM reserve, startup-RAM condition, wall/volume coverage, containment, CPU, lease, command and kernel-control checks are unchanged.

The function accepts an execution requirement; it does not itself authorize a caller to lower a registered limit. Each lower-floor caller must first validate its separately admitted policy and pass the requirement explicitly. Existing callers that omit the new keyword retain their prior 20 GiB minimum. This is the missing caller/guard linkage exposed by cold-offload02, not a reinterpretation of that failed attempt.

The new eleven parametrized cases meaningfully check default rejection, explicit acceptance, below-declared rejection, stricter actual guard acceptance and six invalid declarations. Retained red01 reports **10 unsupported-keyword failures plus 1 pass**, before implementation. Saved green01 reports **39 resource tests passed in 0.62 seconds**. The assertions preserve default behavior and enforce admission before receipt access; they do not mirror only a successful branch.

The separate real `probe01` exercised the actual guard/worker path with explicit 10 GiB on both sides. Its stdout confirms worker admission with 10,737,418,240 disk-floor bytes and 3,221,225,472 RAM-reserve bytes. Guard result is **complete, child exit 0, verified cleanup**, elapsed **0.369319 seconds**, sampled peak **8,597,504 bytes**, zero memory events. The 60-second finite probe used 256 MiB maximum/192 MiB high memory and no network or large allocation. The recorded cgroup and monitor are absent at independent review. This validates admission plumbing, not transfer throughput or full-workload resources.

All four frozen probe bindings were independently rehashed and match:

- `resources.py`: `5e2617f2a8112183e610254f42ab9e14b0bc7cf10f8e0940e6c569395251bb16`
- `test_resources.py`: `93c8914dbf798f88cd8f20a38b6b8b44408f4e5f475ed0dbb2c35ea330eb8a45`
- `probe.py`: `8154616f90dffe310f8dcefdda7cb77140dc1cf4487877ef72d3debd4444f2b5`
- Disk policy: `fa093b7c683687e98b09533fbbd363c8fdca8f91406a80f1169c51fbdf8e44d0`

Evidence hashes: bindings `4ff3a13b4f86b3a5df74b68e824e8e44337d1cdce298e354426306b2eb9076ca`; green01 `63969e2c010178db40bd93700789aa9f703e7b4251faeb1486abaddba3b31c0a`; probe final `0da446b65fa8599ebfc545a7d40ff18eef8405af0c7bd5e24d7ad8330648323d`.

The prior named **3,390-pass** suite predates this guard edit and is not attributed to the current entire branch. This narrow acceptance rests on the focused resource regressions, source delta and real tiny probe. New transfer callers require their own reviewed policy ordering and exact bindings; no transfer, financial fit or empirical release is granted by this guard review.
