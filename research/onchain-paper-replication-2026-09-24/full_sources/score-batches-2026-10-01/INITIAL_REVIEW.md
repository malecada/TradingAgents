# Independent initial completed-score storage review

Acceptance withheld pending the return-boundary corrections below. Review is limited to the new storage primitive and saved synthetic evidence; no financial experiment, numerical integration, successor admission or whole-workflow resource claim is evaluated.

## SB1 — Successful publication can escape a lost lease or changed file/root

`tradingagents/research/onchain_replication/score_batches.py:123`, `:148` and `:173`: creation, append and terminal publication call `_write` without a subsequent lease/root/file check before returning success. `_write` returns a hash of the supplied body, not a readback of the saved file. A sync callback that revokes the owner lease, renames the store root or alters the newly written file can therefore leave the caller holding an apparently successful publication. The append case also advances in-memory counts before any final admission check; finish immediately closes its descriptor.

Required correction: prebind the exact intended bytes, retain bounded file identity/content checks, and recheck the owner/root and newly published records at the final return boundary. A failed final check must preserve the bytes and refuse success; explicitly define poison/terminal handling when the terminal file already exists. Add isolated regressions for revocation and same-size write/root replacement during publication. The current revoked-lease test exercises only revocation before append.

## SB2 — Verification does not protect earlier observations through its final callback

`score_batches.py:223` and `:259`: each header/payload is checked once, then forgotten. Inventory is checked before the last caller lease. That callback can change a previously verified payload, start, terminal or header, or insert a foreign file, and `verify` still returns a successful count record because the final `_root` only checks the directory inode. A later chunk read can likewise alter an earlier file without detection. This is an avoidable return-boundary gap, distinct from an impossible atomic snapshot against unlimited concurrent mutation.

Required correction: provide a bounded final whole-store consistency boundary after the final external callback, retaining/rechecking the admitted content, exact extents and inventory with an explicit memory/I/O bound. Do not silently replace O(chunk_bytes) memory with one signature object per cell/chunk. Add late-callback inventory/content drift regressions and a change to an early chunk while a later chunk is read. State the remaining non-atomic limitation explicitly.

## Crash-durability qualification

`score_batches.py:117`: the new root directory's parent is not synchronized. Fsync of files and the new root directory does not by itself establish crash persistence of the parent's new directory entry. Synchronize that parent before accepting durable publication, or explicitly withhold crash-durability claims. This is a source-level persistence requirement; no power-loss experiment was performed.

## Supported properties and evidence limits

The source binds owner plus six supplied scope hashes, exact dimensions/order/dtype, chained headers, exact ordinal offsets, chunk payload hashes and externally supplied terminal hash. The reader uses descriptor-relative nofollow/nonblocking opens, bounds metadata to 8 KiB and payload reads to at most the 8 MiB chunk ceiling plus one byte, refuses nonregular/multilink files, and enumerates inventory incrementally. These are useful primitive checks. They do not prove that scope hashes represent actual admitted numerical inputs. Scores are finite float64 values; the source deliberately does not enforce [0,1], and an existing test publishes values above one. Numerical score-domain validation remains a caller responsibility until integrated explicitly.

The closed `check01.log` reports 12 passes in 0.23 seconds under the reviewed profile, with historical test withholding disclosed. The red log is retained. Tests cover ordinary ordering/dtype/nonfinite failures, wrong owner/scope/terminal, payload/missing/symlink corruption, partial-write preservation, pre-operation lease loss and root replacement. They do not cover SB1/SB2, actual registered leases, crash recovery, concurrency between callers, full MCM computation or total process memory. No test was rerun by the reviewer.

The logical formula `8 * cells + (ceil(cells/chunk_cells) + 2) * 8192` correctly reserves raw float64 bytes and one bounded header per chunk plus start/terminal metadata for this writer's admitted files. The six-cell/two-chunk example is 32,816 bytes. This changes metadata growth from the old per-cell 196,608-byte constant allowance to a per-chunk term; it does not convert that reservation difference into measured disk savings or feasible runtime/RSS. Input arrays, private byte snapshots, finite-validation scratch, filesystem blocks/directories, matching scratch, logs and other workflow outputs remain separate. Failed pending bytes are retained rather than replayed or erased; caller-written foreign files are outside the formula and must refuse admission.

Reviewed source SHA-256: `0384312746e7150d75e3cc875ae0a65d9f842cfa0cb0060bd55ef0545ab9b2fb`.
Reviewed test SHA-256: `94585bdf186f03101e64af4bbc67bb06a668294be48ea7e8209a2c03ac2840f2`.
