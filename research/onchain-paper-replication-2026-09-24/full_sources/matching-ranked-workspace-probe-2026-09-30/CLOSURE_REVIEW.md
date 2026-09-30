# Independent ranked-profile terminal review

Accepted as a completed single synthetic profile at source `7b09c9665de23afba5d748f3e8cb69748cc3311a`. No inconsistency was found in the compact terminal evidence. This review reconciled saved receipts, source bytes, checkpoint metadata and file extents; it did not rerun matching, load arrays, rehash NPY bodies or repeat a historical profile.

All 96 source/evidence bindings match both current bytes and the recorded commit. Current HEAD remains that commit. All nine compact hashes in `closure01.json` match; the parsed raw child log equals `result.json`. The closure receipt SHA-256 is `f0d69b3b45e47f45ecc239956bb26e113f300bbfc7481796f1022dd08be68cd1`.

The saved preflight records an absent attempt identity, zero active units, 9,746,980,864 available RAM bytes and 24,962,547,712 free disk bytes, exceeding this profile's startup requirements. The saved owner observation records monitor 1151404, start ticks 9496211 and unit `onchain-replication-bf989310d5c64782bdaf5ce371205b26.service`. The monitor path and exact cgroup are now absent. The recorded worker command is the reviewed pinned-runtime invocation; child-exit evidence independently records workload exit zero. The guard reports complete, cleanup verified, no limit reason and 23.746975636 seconds elapsed.

The saved kernel controls are 1 GiB maximum, 768 MiB high and zero swap, with 3 GiB host reserve, 4 GiB startup, 10 GiB disk floor and 1,800 seconds. Per-thread readback records the two admitted CPU affinities. Sampled peak cgroup memory is 334,196,736 bytes; all recorded high, max and OOM counters are zero. This is a sampled whole-profile cgroup observation, including checkpoint page cache and diagnostic temporaries, not an exact RSS peak, cold-cache requirement or ranking-only memory measurement.

## Result and checkpoint reconciliation

The result records 48 annealing iterations, temperature termination, 4,012,048 annealing operations in two calls, 4,000,000 ranked entries scanned, 2,000 selected pairs and score 0.5. These agree with the independent analytical counts in the prospective review. The compact prefix contains exactly `[[i,i] for i in range(33)]` at cursor 65,536; the final compact state contains exactly 2,000 ordered diagonal pairs at cursor 4,000,000. Both were independently checked from the small manifests. Retained numeric state is 128,000,000 bytes.

The uniform-matrix error is `1.0842021724855044e-19`; the worker's soft-matrix identity is `e5f5cd5a84eebc8b61f69f1f590c04ef695f093a382779437ec65014a97f64f8`. Both outer manifests, rank input identities and result join to that identity. Their common order-body SHA is `600666bb89c5b69fbcfd323c5b8ceeda2c5a7b6130ee6eeca81122a002fcf35d`. The shared annealing-manifest bytes are identical across the two checkpoints.

Each checkpoint contains four NPY files of 32,000,128 bytes. All seven per-checkpoint file extents match the recorded metadata. The first checkpoint totals 128,002,213 logical bytes; the second totals 128,023,746, for 256,025,959 retained bytes in total. Both remain below their separate 128 MiB allowances. Outer-to-inner manifest SHA joins and recorded component policies were independently checked. These are file-length totals, not physical allocated-byte measurements.

The outer manifest hashes are `ac1b597f6970ed6f1fa27002c5ed3ba012561eff2fd5f8271da2a413fde57663` and `d913703735de5f73d214a6fef154e014923b5c6b76e4f0f99488bbf75d718965`. Guarded-worker assertions establish full NPY hashing, save/restore checks and actual restored mapping closure. Independent review confirms their compact joins and extents, rather than claiming an independent body verification. Successful result publication follows the explicit final mapping-close assertion.

The saved timing is 17.695621932 seconds for annealing including atomic rank creation, 0.050590235 seconds for the prefix scan and 3.930574051 seconds for remaining ranked hardening. Prefix save/load took about 0.3316/0.2167 seconds and final save/load about 0.3841/0.2225 seconds. These are observations of this invocation, not a controlled speed comparison with earlier profiles.

Principal evidence hashes:

- `result.json`: `97337848f3ec109e1c69bd30d9d6428ef7cdadf31d4eac09726da26bdbcff550`
- `guard01/final.json`: `ad3ed2c23229218fb5cda95526efa328b1cff48a9a2fc86ca1e720fff6f582f3`
- `guard01/child.log`: `0badff674599d407dc03b13609dd3484646014964ee3b552eedeaddc94ac31cb`

The admitted measurement covers a fresh constant-attribute, zero-edge, 2,000-square synthetic pair at the unchanged 4,000,000-pair capacity. It provides actual resource and restoration evidence for this composition on that fixture. It does not establish worst-case native sorting memory, full nonzero-edge or real-hub schedules, production dispatch/cache identity, dictionary/MCM/neural or GPU feasibility, financial performance, or Graph 10 admission. Atomic sort creation, scoring and publication remain non-resumable within their operations. Existing financial denominators and pending empirical work are unchanged.
