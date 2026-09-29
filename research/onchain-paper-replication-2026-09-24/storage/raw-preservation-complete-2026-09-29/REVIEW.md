# Independent final retained-ETH backup audit

Disposition: COMPLETE for the frozen retained ETH raw-file inventory. No remaining
blocking correctness finding was found in the final recovery index, terminal
receipts or scope claims. This establishes completion of the admitted preservation
workflow using independently reconciled historical upload/readback evidence; it
is not a new recovery of103GB or a current recheck of every remote archive.

Exact final artifacts reviewed:

- recovery-index.json: `89710723686c617d56449e9f8e2d7bb990518a5d22c23dafb0859deb46e5eb66`.
- reconciliation.json: `6b1c5b4952eaaecc60f0e951a115bf8cab1dcc1e378eba47b0c24e9d09335680`.
- RESULT.md: `e8df01545e7c6a2a5237659f26b19ae322b1a8afbdb0300b4d5321256bf8bab1`.
- Continuation09 controller completion: `24d120c54855d86a810c7daaf9211ad442b3692116d5e54793e535d74878a024`.

The operative instructions and review brief were read, and actual branch/status
was inspected. The audit first reconstructed the entire completed denominator
directly from the frozen inventory and retained per-batch evidence, before reading
the author's final recovery index. No expected aggregate was imported from that
index for the reconstruction.

## Independent whole-inventory reconstruction

Exactly195 completed batches cover indices0..194 and every inventory row0..59082
once. All59,083 resolved source paths are distinct. Their103,524,489,043 raw bytes
match the frozen inventory exactly. The successful archives total103,571,036,160
bytes and have195 distinct remote archive locations. There are no duplicate,
missing or survivor-only inventory entries.

| Successful source | Batches | Files | Raw bytes |
| --- | ---: | ---: | ---: |
| pilot02 | 1 | 149 | 517,291,351 |
| continuation03 | 33 | 5,683 | 17,535,553,216 |
| continuation05 | 8 | 1,477 | 4,261,535,398 |
| continuation06 | 3 | 634 | 1,593,323,300 |
| continuation07 | 9 | 1,823 | 4,797,931,389 |
| continuation08 | 4 | 1,077 | 2,129,704,225 |
| continuation09 | 137 | 48,240 | 72,689,150,164 |
| Total | 195 | 59,083 | 103,524,489,043 |

For every batch, all manifest rows—including original/resolved paths, expected
SHA256, size, modification metadata and numeric member name—match the exact
frozen inventory positions. Receipt offsets, counts, raw bytes, archive byte
length/hash and preservation/source/readback flags agree. Each manifest hash
matches both its completion receipt and recovered manifest. Completion-payload,
recovered-complete and local complete bytes agree. Cleanup receipts confirm only
verified generated tar copies were removed, and all successful local bundle.tar/
recovered.tar copies are absent.

All519 available successful diagnostic transport receipts across the admitted
history and09 phase metadata show complete status, returncode0, no recorded error
and equal received/expected sizes. Earlier successful bundles predate those
additional diagnostic receipts; their original full archive/member verification
and roundtrip metadata receipts remain present. Actual raw archive/member bytes
were verified by the reviewed transfer implementation during each recorded
transfer; this final audit did not repeat those large reads.

Every one of the recovery index's195 rows was then checked against the independent
reconstruction and original completion receipt. Archive, manifest and completion
remote paths are exactly the successful receipt's remote directory plus the
correct basename. All local receipt/manifest hashes and inventory ranges agree.
Inventory and batch-plan hashes match their frozen files. The index therefore
provides an exact cross-attempt recovery map without crediting failed partials.

## Continuation09 execution and ownership

All nine phases cover58..194 once. Phase completion lists exactly match their
registered ranges and individual batch receipts. Phase aggregate counts/bytes
reconstruct48,240 files /72,689,150,164 bytes. Recovered phase inventory, batch plan,
contract and completion payloads match their originals. Controller intent binds
the exact contract and committed release; its reused prefix1..57 plus pilot0 is
counted once. Terminal controller totals equal the full inventory.

Every09 guard is COMPLETE with child exit0, verified cleanup and zero kernel OOM
or OOM-kill counters. All owned cgroups, recorded monitor/workload/thread PIDs and
controller894430 are absent. Guard resource settings retain256/192MiB memory
caps, zero swap,3GiB runtime/4GiB startup host reserves and20GiB disk floor.
Every phase stayed under8h and the controller under48h. Memory.high throttling
was present; these are completed bounded transfers, not isolated throughput
benchmarks. Maximum sampled09 memory is203,792,384 bytes.

Phase intents span commits555c30d1742bb2c36ed3917933dd440b898cde8b,
678a1319558c1b24772c39be7ead9563a158b82c and
bc7b17ed54c93ef3b84cce74764cf4ecde3f5fa5. Independent git-object reads confirmed
that every bound source file and the exact release bytes match at all three
commits. The changing repository checkpoint did not change the admitted code
or release. Current source/input hashes also match the09 contract.

Nine09 guards sum38,502.81746238501 seconds; the controller records
38,502.920119751 seconds. Prior33,536.73581249901 guard seconds plus09 gives
72,039.55327488402 cumulative measured guard seconds. These totals include prior
guarded diagnostic runs01/02 and exclude separately timed read-only connectivity
preflights, preparation and scheduling. A misleading exclusion of diagnostics in
the draft reconciliation wording was corrected before these final hashes were
recorded. Numerical accounting was unchanged. Allocated payload ceilings are
preserved allocations, not measured network traffic.

## Preservation and limits of the conclusion

Attempt01's pilot and the02..08 failed controllers remain terminal FAILED.
No failed batch has been promoted to complete. All11 previously recorded local
failed archives/readback partials remain at their preserved sizes, checked by
metadata only. The02 startup failure remains a zero-transfer failure. Successful
batches inside later-failed phases retain their own verified completions. No
closed identity was rerun for this audit, and no partial/original was deleted.
Current contents of the remote failed partials were not independently reread.

RESULT.md and the new STATE checkpoint correctly distinguish complete preservation
of this existing retained ETH store from BTC/history acquisition, graph/MCM
production, full paper coverage and numerical agreement. This backup does not
cover the separate graph/MCM/pilot scratch stores or establish their feasible
compute/local-disk allocation. All1,420 financial fits remain pending.

No network request, raw-body read, source-stat rescan, test rerun, financial
experiment, ledger mutation or restore into original paths was performed by
this reviewer. The final conclusion is based on independently checked complete
metadata, committed source control flow, saved downloaded-byte verification
receipts and terminal ownership evidence. Present remote-byte integrity, another
full restore and future storage durability remain untested. No unresolved
correctness question requires a higher-effort escalation.
