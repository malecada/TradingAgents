# Independent review of GREEN02 child completion and parent failure

Disposition: **accepted child numerical agreement and saved-storage assertions within the exact finite oracle; accepted preservation and post-closure cleanup; parent terminal remains failed**. The actual child passed all 13 frozen checks. The parent then rejected its cleanup evidence because the new predicate incorrectly required the still-running caller's own PID to be absent. This result does not retroactively pass the parent, release production integration or establish full-size capacity. Identity `neural-streamed-gat-oracle-green-20261002-02` is permanently closed and must not be rerun.

Review used read-only source inspection, standard-library JSON/hash/extent reconstruction, local Git blob reads with lazy fetching disabled, original-tree metadata inspection, full archive streaming without extraction, and current process/cgroup/unit observations. No numerical imports, tests, oracle, guard or job were invoked. Only this new review file was retained.

## Exact source and evidence

All 12 outer references matched their sizes and hashes. All **248 released source pins, 1,971,052 bytes**, match both canonical single-link regular current files and original Git blobs at `7d42f1410c1f15e52e2598f37444a7fb6c311bad`. Original reservation, released worker command, coordinator and terminal join the same identity, source and release. `oracle03.py` differs from oracle02 only in selecting `candidate02.py`; no tolerance, fixture, check or acceptance assertion was changed.

Key independently checked hashes:

- `green-execution-result02.json`: `6fa096240625db222459c11654dea814b58acca8f243a66adea01d69180b95aa`.
- `green-release02.json`: `f38adfce3bb7a99cd3428669900d000318093148195015696b65496e2b552aff`.
- `candidate02.py`: `e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f`.
- `candidate-manifest02.json`: `5cb3930364bd052d3e6b812b9e788615c8ca709fe8f57d9f5a35077765c335d7`.
- `oracle03.py`: `f7626de20851a0e255e927a8c0be9e8d7d433c833888cf206d8656ff24070d7b`.
- `guard_launcher03.py`: `8ab04bd1acb8142c3f50cc23bdb6e92077a4d6837c363016289d583e1cb4c809`.
- `green-retained-tree02.json`: `7bcf17bba3ac3420efdb18f9bb7bb03296fb82e2489bd75658841906079cf9b8`.
- `green-retained-tree02.tar.gz`: `86792eebcda0bc2e43ca4034c4ed73209ab25dce5ab849148be89f5d9635b320`, 4,071 bytes.

## Actual child acceptance within the oracle

The 397-byte child log contains exactly the 13 ordered PASS lines in the 15,324-byte oracle report; report status is passed and error null. The checks cover mixed/self/isolated nodes, zero edges, masking, float64, dropout/RNG, duplicate refusal, full-model 16×28 forward/loss/input and parameter gradients/Adam/RNG/in-memory reload, aggregation output/all gradients, independent gradcheck, independent central difference, invalid-block refusal, bounded forward/backward blocks with first-order contract, and removal of full-edge saved backing extents.

The float32 tolerances remain `rtol=1e-5, atol=1e-6`, float64 `rtol=1e-9, atol=1e-10`. The fixed independent gradcheck and finite-difference tolerances likewise remain unchanged. The block audit exactly records three blocks of at most three edges in both forward and backward for its nine-edge test. The first-order refusal assertion passed; it does not establish higher-order differentiation support.

Independent non-numerical reconstruction from retained saved-record extents gives:

| Quantity | Baseline | Candidate02 |
|---|---:|---:|
| Effective edges | 26,369 | 26,369 |
| Saved records | 27 | 26 |
| Sum of reference extents | 32,668,273 B | 5,863,793 B |
| Reported distinct backing bytes | 29,714,945 B | 2,778,881 B |
| Reported distinct backing stores | 20 | 17 |
| Full-edge backing records | 5, 8, 22, 24 | none |
| Unclassified backing extents | none | none |

The full edge/head/width threshold reconstructs as `26369 × 4 × 16 × 4 = 6,750,464` bytes. Every candidate record falls within the frozen dtype/extent ceilings; independent classification reproduces accepted=true. Both forward and backward hook scopes were exercised; the diagnostic records no additional autograd saves during backward. Raw storage identities are omitted, so the distinct-store totals and alias grouping remain source-derived child diagnostics rather than independently reconstructible identities. The observer deliberately retains backing storage and is not a process-peak measurement. Absence of full-edge **saved** backing does not assert absence of every temporary allocation.

Acceptance applies to the finite CPU fixtures, original dimensions and single-step training path actually executed. Tensor bodies, full optimizer state and in-memory checkpoint bytes were not retained for independent replay. No physical checkpoint artifact, GPU proof, full-size graph capacity, long-run convergence, paper accuracy or broader data coverage follows. The review did not rerun any numerical calculation.

## Concrete parent cleanup defect

Child exit is0, native unit result success/status0 and guard phase complete after 5.369447409000713 seconds. Coordinator exit is1 after 6.43810945199948 seconds, ending18:37:28.692052 UTC. Its preserved traceback reaches `guard_launcher03.py:114`, and the launcher terminal records `RuntimeError('descendant cleanup unverified')`.

`guard_launcher03.py:100` adds `result['monitor_pid']` to the PIDs required absent on the stop5 branch; line103 checks their `/proc` existence. But `resources.py:247` sets that field to `os.getpid()` inside `guarded_run`, called synchronously by this same launcher. The parent is necessarily still alive while validating its returned guard result. Thus the new predicate rejects its own live caller even when actual supervised descendants have exited. This is a definite source-level role error, not evidence that the model workload or cgroup remained alive.

The guard reports cleanup_verified=true, stop return5, inactive/dead, native success0 and empty control group. The exact reason for stop return5 is not retained; it must not be invented from the return code alone. Current independent inspection finds the original cgroup absent and the unit not-found/inactive/dead with MainPID0, empty ControlGroup and success/status0.

The durable receipts identify **three distinct PIDs**: caller/monitor1119868, supervisor1120119, and workload1120123; final thread readbacks repeat the latter two. All three are currently absent. No fourth distinct original PID appears in the reviewed evidence, so no four-PID absence claim is made.

The parent validation rejected early. Later validation clauses were therefore not all reached by that parent; this review independently checked the retained native, terminal, source and report joins. The failed terminal remains immutable. A new guardian correction must distinguish the current caller from supervised descendants, pin that role correctly, preserve all closure checks, and reject unrelated surviving PIDs or cgroups. Pure sentinels and a fresh bounded non-numerical native smoke are appropriate to validate that infrastructure correction without reopening GREEN02.

## Controls, closure and whole-tree preservation

Actual worker and guard readbacks agree on 1 GiB memory maximum/high, zero swap, CPUs `[0,1]`, original cgroup, and inherited 4 MiB hard/soft file limits. Active native unit evidence retains the two-minute runtime and MainPID1120119 matching readiness. Both final recorded thread affinities equal `[0,1]`. CPU quota controller availability is false despite a `2s` unit property, so only affinity/readback enforcement is claimed. Initial and terminal memory events are present and all zero. Sampled peak is426,430,464 bytes, terminal current10,665,984 bytes; no kernel lifetime-peak claim is made. Child and guard terminal memory snapshots match exactly.

The unchanged 3 GiB reserve, 4 GiB startup threshold, 120-second guard/unit envelope, 15-second monitor lease, 10 GiB floor and sampled64 MiB owned limits are recorded. Last disk free is20,206,563,328 bytes. Retry and elapsed-time kill are false; there are no storage-breach/error, cleanup-error or truncation flags. File limits are per-file, storage/free-space observations are sampled, and the unit deadline is not a whole-controller deadline.

Independent `lstat` enumeration verifies **10 regular single-link files, five directories including root, 15 total entries, 32,406 logical bytes and81,920 allocated bytes including directory blocks**. Exact file sizes/hashes, all modes, unique membership and original-root device/inode match. No symlink, surviving hardlink, special type or extra member was found. Live and final guard files are byte-identical. All15 archive members were independently streamed without extraction, verifying every body, size, type and mode. Local archive completeness does not by itself establish off-machine recoverability.

The last guard sample is69,632 allocated bytes,23,466 logical bytes and12 non-root entries. Complete closure adds12,288 allocated bytes,8,940 logical bytes and two non-root entries, consistent with final receipt/launcher terminal publication and live rewrite. Earlier overwritten live contents are not separately preserved. The complete manifest totals are the final denominator; original block allocation is not tar-media allocation.

## Remaining boundary

The tiny corrected numerical candidate has now met the finite child oracle, including the previously unexecuted storage and derivative requirements. It must not be described as overall parent success or full-size feasibility. Preserve both the child pass and parent failure. Complete and independently verify the new non-numerical guardian correction before integration; production source closure and empirical admission remain separate. No repeated closed numerical run is required to investigate this identified caller-role defect. No empirical04 claim, financial fit, original-dictionary bridge, long-history/asset comparison or paper numerical agreement is established by this review.
