# Startup storage race: bounded read-only investigation

Source inspected: actual CAP a5bcc943167ad035b45e12ddf9864d46e685b124. No live source, registration, Parent, outcome or numerical input was changed or executed. Only this new report is written. CAP means `/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source`; Parent means `/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01`.

## Evidence and uncertainty

`full_sources/heartbeat-root-checkpoint10-2026-10-04/SUCCESSOR_NUMERICAL_ROOT01.stderr` identifies Parent line201 `watch.check()` called by supervisor01.py:29, then installed workflow_storage.py:234, `directory changed at namespace rejoin`. Main's workflow_storage.py is older and was not used to infer actual behavior.

Installed workflow_storage.py:118–158 already retries HardlinkObservation and StorageMutationObservation at most three times, sharing one five-second budget, with at most5ms between attempts. Each failed census is discarded after cleanup; it never becomes an accepted observation. The propagated exact StorageMutationObservation means the third eligible mutation was reached. A time cap or cleanup uncertainty would instead take its separate failure path. First two reasons, exact changed directory, partial counters and aggregate elapsed time were not persisted: StorageMutationObservation.__str__ omits evidence; Parent:221 records error_type only. They cannot be reconstructed from final tree state. No assertion that all three failures occurred in guard/ is justified.

Observed file mtimes (UTC; filesystem timestamps, not independent event log or publication times): launch.json07:12:47.208095876; owner.json07:12:48.370058794; guard/cpu_ready.json07:12:48.579052124; guard/child_exit.json07:12:48.682048837; guard/live.json07:12:48.840043795; guard/final.json07:12:48.847043571. live.json is overwritten and its retained mtime describes final publication. guard/final.json records `InterruptedError: guard received signal15`; child_exit records125, `signal before release`, workload_pid null. Thus Parent failure caused drainage before release; the guard's recorded interruption is downstream evidence, not the initiating storage failure.

The guard independently accepted a full CAP scan:1770entries/1309regularfiles/462directories,86,536,192allocated and81,121,620logical bytes,0.141528728s, one attempt/no mutations. Final host availability10,465,075,200B and disk15,531,286,528B exceed frozen limits. These observations do not prove every concurrent sample was under all caps, but the retained initiating exception is mutation, not StorageLimit.

## Responsible integration and narrow executable correction

Leave installed StorageWatch, all its strict namespace/file checks, limits, three-attempt budget and fatal/cleanup precedence unchanged. Leave native job, guard, model and training unchanged. The avoidable collision is the duplicate Parent whole-CAP census running concurrently with the genuine guard's own receipt publication and startup file creation.

For a prospectively reviewed NEW Parent only, split existing `checked` at Parent:200–201:

```python
 def active_checked():
  parentwatch.check();require(shutil.disk_usage(CAP).free>=10*GIB,'active disk floor')
 def checked():
  watch.check();active_checked()
```

Keep existing `checked()` at line202 before child spawn and in cleanup action sequence at line222 after owned drainage and native cleanup. Change only the supervisor callback at line214 from `checked` to `active_checked`. Parent-tree checks and independent disk checks continue every supervisor iteration. Whole-CAP accounting while the genuine job runs is performed by the existing source-pinned native guard; there is no filename exemption, fabricated observation, larger cap, added retry or sleep ladder.

This is a source-bound allocation of existing enforcement responsibility, not a claim that the Parent stopped checking a tree because it was inconvenient. Required source joins are already in Parent preflight: exact execution_job, full current source map, protocol pins and genuine job command. They must remain intact in the new review.

Concrete existing enforcement: job.py:264–282 admits exact job, binds monitor parent death, verifies launch/Owner, and passes the unchanged complete registered storage budget into guarded_run. resources.py:405–438 applies StorageWatch to the whole CAP and disk floor; boundaries():456 precedes native dispatch, :526 follows cpu_ready/kernel verification and precedes release:529, :532 runs in every native loop. Its own publish happens after census at:445–449, so it does not race its own live.tmp/live.json writes. Finalization independently invokes observe-storage and final disk at:636–641. job.py:340–360 verifies actual live/Owner/full policy before genuine ResearchRun.start. No metadata startup path supplies claim authority without that release chain.

The startup interval before the guard's first census can create bounded metadata, but no workload is released there; the complete guard census must accept it before native dispatch and again before release. This preserves sampled enforcement, not a hard filesystem quota or atomic snapshot. Other concurrent workload publications can still cause the unchanged native watcher to fail closed. This correction addresses the demonstrated duplicate Parent observer race; it does not promise universal liveness.

## Required focused regression before release

One bounded stdlib synthetic scheduling regression should load the exact prospective Parent and replace only external process/native effects. Record events and assert: (1) complete CAP+Parent+disk check before spawn; (2) active supervisor callbacks check Parent+disk without a second CAP traversal while the modeled genuine guard performs its full CAP checks; (3) startup Owner/guard/cpu_ready publication succeeds under the unchanged genuine StorageWatch and is included in the guard's accepted denominator; (4) full CAP check runs after drainage and terminal publication, on both success and failure paths. Use the existing accepted watcher fixture machinery rather than building a new matrix.

Retain direct failure controls: native StorageLimit allocated/logical/entries/depth/time or hardlink/namespace/cleanup failure prevents release and remains nonzero; Parent-tree breach and disk breach still stop supervisor; a post-drain CAP excess still fails; source/policy mismatch refuses admission; removed/missing native guard release never authorizes ResearchRun.start. Replay the relevant existing fatal-cleanup regression only if callback implementation touches those paths. No empirical launch is needed for these tests.

Prior accepted evidence reused: financial-wrapper-storage-watch-concurrent-publication-correction03-2026-10-04/REPORT01.md and corresponding review03/REPORT01.md. They preserve strict full census, fixed retry/time limits, fatal/cleanup precedence and acknowledge non-atomic sampled limitations. No historical outcomes or broad matrices were rescanned.

## Diagnostic retention seam

The actual changed directory is missing evidence, not a negative finding. A future Parent may additionally retain bounded builtin StorageMutationObservation.evidence and observation in its terminal receipt while preserving selected-fatal identity and existing first-fatal handling. This is diagnostic only and not needed to change the scheduling defect; it must not replace the primary exception or become a retry path.

The current identity and Parent remain permanently reserved. This report neither authorizes relaunch nor supplies a new registration, claim, recovery acceptance or financial result. Root owns current outcome preservation and any prospective corrected successor.
