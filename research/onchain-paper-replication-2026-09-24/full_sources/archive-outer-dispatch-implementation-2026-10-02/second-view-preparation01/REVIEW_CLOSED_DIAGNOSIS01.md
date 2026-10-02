# Independent closed two-View diagnosis

The attempt is closed and unsuccessful. The final guard reports `ValueError: storage hardlink refused`, failed phase and verified cleanup. The launcher reports failed status without retry. The child wrapper retained exit125 with reason signal. No OOM/high/max event occurred; the sampled memory-current peak is546,107,392 bytes. This is not a RAM-limit failure or a completed two-case proof. The exact offending hardlink path/inode cannot be recovered from the available evidence.

Read-only current verification found the original cgroup absent, unit failed with empty ControlGroup, and monitor/bootstrap/workload/thread PIDs511886,511889,511896,511906,511912 and511936 absent. Guard elapsed time is1,131.063366781 seconds; the separately reported outer-controller duration includes additional work. No guard action, rerun, test, numerical import, source change or owned-tree mutation was performed by review.

## Hardlink evidence and attribution limits

An independent complete lstat traversal found no surviving regular file with nlink other than1 and no special entry. Thus there is no remaining hardlink topology from which to name the refused path or inode. The frozen `workflow_storage.py:48` checks nlink and raises only generic text; `resources.py` retains that exception text but no offending path/stat. This is a durable diagnostic gap, not permission to infer a path from nearby timestamps.

The base fixture does not clone a repository. `test_lifecycle.py:34–35` creates a new Git repository; its commit helper uses add/commit. `test_matching_owner.py:39–42` copies selected source files with shutil.copyfile before adding them. Therefore a local-Git-clone hardlink explanation is unsupported. Git implementation temporaries cannot be conclusively excluded, but are not established by the retained evidence.

Two actual selected source mechanisms explicitly expose temporary hardlinks:

- `lifecycle.py:58–73`: immutable publication writes/fsyncs a `.pending-*` file, links it to the final path, fsyncs the directory, then removes the temporary name. There is a real interval with two names for one inode.
- `archive_transport.py:264–280`: successful download links its retained staging path to the destination, then unlinks staging and syncs the directories.

These ordinary publication mechanisms are incompatible with an unsynchronized external sampler that unconditionally refuses every observed nlink greater than1. A scan can observe the permitted writer's intermediate state and fail closed even though no hardlink survives. This mechanism is established from source; attribution of this particular refusal to either call or a particular file remains unproved. The failure case's carry-forward publication, archive transfers and failed-publication cleanup all lie near the interrupted work; timestamps alone do not resolve the specific trigger. The absence of a surviving link does not disprove the observed guard error.

## First test failure versus interrupted second case

The final pytest log still contains only `F\n`: no summary or traceback survived because the guard stopped the unit during the second case. The first case nevertheless retained two complete scientific owners and a complete outer terminal:50 commands,806,400 logical reserved bytes and1,005,216 rounded reserved bytes. All persisted first-view ledger/publication hashes continue to match.

The first case's r dictionary completed20 comparisons, while r2 with the changed seed13 completed22. Each has two MCM stages of six pairs. The candidate success branch asserts dictionary pairs equal20 for every prepared representation. This is a concrete fixture assertion defect: the inherited seed12 count is not a cross-seed invariant. If that assertion is reached for r2, it necessarily fails against the retained contract. It is a strong explanation for the first F, but the missing traceback prevents claiming an independently observed exact failing line. The production count must not be altered to satisfy this expected value.

The second case reached r2's first intended download failure. Its retained transport receipt records returncode19, zero received bytes and expected2,688 bytes. Command-failed-00000028 records28 commands,504,000 logical reserved bytes and537,728 rounded reserved bytes. The second scientific owner has failed/attempt-failed records, and its archive ledger closed poisoned. The first representation's carry-forward hashes still match. However, neither local outer terminal nor registered outer-terminal output was published, and the second ResearchRun has no terminal closure record. Guard interruption prevents acceptance of the failure-case closure/post-close assertions. Retained partial work is evidence, not a passing second test.

## Minimal prospective corrections

Keep this identity and all its partial results closed. A new candidate should make only justified fixture/resource-integration corrections:

1. Replace the unjustified universal20 assertion with a predeclared independently justified seed-specific expectation or a scientifically appropriate invariant for this ownership/accounting proof. Preserve the observed20/22 discrepancy and distinguish correction of test expectations from production numerical changes. Do not tune the scientific algorithm or rerun the old identity.
2. Remove the conflict between selected atomic publication and hardlink-intolerant observation without disabling/excluding the guard. A suitable narrowly reviewed option is atomic no-replace publication that never exposes two hardlinked names, retaining complete-file visibility, no overwrite, fsync durability and fatal-error preservation. Cover both selected link-based publication routes or otherwise provide an explicit reviewed coordination mechanism. Do not silently substitute a partially visible exclusive-write publication or relax nlink rejection. This is a prospective integration remedy; it is not a claim that the exact historical trigger has been identified.
3. Retain path, device, inode, link count and accounting progress in a bounded storage-refusal diagnostic before stopping the unit. Add a focused synthetic concurrency/counterexample check showing valid atomic publication cannot trigger the scan while an unexpected hardlink still does. This does not require another financial experiment or full owner fixture merely to diagnose the mechanism.
4. Retain per-case failure tracebacks promptly in bounded files, so interruption of a later case cannot erase the earlier test failure detail. Preserve the existing combined log and failed result unchanged.

A newly frozen source/candidate, independent review, fresh identity/resource release and exact cumulative accounting review are required before a successor integration invocation. Final manifest/archive/result reconciliation for this closed attempt remains separate pending coordinator publication.

## Coordinator-proposed bounded rescan alternative

A narrowly bounded whole-scan retry can also preserve the documented sampled-accounting contract without changing the publishers. This is an explicit prospective observation-policy change, not a claim that the historical path was identified or that no transient hardlink ever existed. Each attempt observing an unexpected link must be discarded; acceptance requires a new complete scan in which every observed regular file has nlink1 and all existing type, filesystem, namespace, root-identity and byte/entry/depth checks pass. Never combine partial totals from different attempts or accept the first partial observation after its link disappears.

Required constraints for review:

- At most two retries, hence three total complete-scan attempts. Use one original monotonic deadline covering all scans, bounded backoff and descriptor cleanup; no resetting max_scan_seconds. If less than the proposed delay remains, fail within the common budget instead of granting another full wait.
- Retry only a typed unexpected-link observation. Quota breach, excessive entries/depth, root replacement, filesystem crossing, symlink/special entry, unrelated I/O error, interrupt or fatal exception must not be converted into retry eligibility. A persistent link fails after the finite attempt/deadline bound. The original root device/inode must be checked again on each attempt and at completion.
- Close every scan iterator and descriptor before retry. Preserve primary/fatal exception priority if cleanup fails; a failed cleanup must not silently permit another scan.
- Retain bounded offending relative path/device/inode/nlink and partial accounting for each failed attempt, including when a later scan succeeds. Record attempt count, total elapsed time and final accepted accounting separately. Diagnostic publication must not become an unbounded write or erase the original failure.
- State the traversal-work bound honestly. If max_entries applies separately to each attempted tree scan, three attempts can visit up to three times that many entries in aggregate. Either impose a common entry-work budget or disclose the enlarged bounded work allowance. Keep final accepted tree cardinality within the original max_entries. A common time bound alone does not justify claiming the old total visit bound unchanged.

Decisive deterministic tests should demonstrate: transient two-link publication followed by an exact full singly linked observation; persistent internal and outside-root-linked files rejected; common deadline exhausted across retries without reset; finite retry count even when the fake clock does not advance; exact totals restarted rather than accumulated or reused; file growth/quota breach between attempts detected; root replacement between attempts refused; quota/type/path errors and BaseException sentinels never retried; descriptor/iterator closure and first-fatal priority; and bounded retained diagnostics on both success-after-retry and final failure. Those focused synthetic checks can assess the mechanism without another owner fixture or financial experiment. Actual concurrent filesystem and full two-View behavior remain separate later release/result claims.
