# Independent graph preservation preparation review

September 29, 2026. Metadata/stat review only: no array, archive or database body was read, no transport or preservation job was run, and no external copy is asserted.

The inventory exactly covers the two original completed graph stores (January 3 and June 13, 2022): two manifests and their ten declared arrays, **12 files / 1,037,095,664 bytes**. Both manifest hashes match; every array's expected hash, byte count and filename match its original manifest. Every inventory resolved path, current size and mtime matches current filesystem metadata. These checks preserve declared identity; they do not freshly verify array contents.

The three contiguous, non-overlapping batches cover all 12 entries once. Their raw-byte totals independently reconstruct to **218,311,796; 521,714,716; 297,069,152**. Each member and batch is below the existing 512 MiB raw-byte cap; the largest member is **344,248,088 bytes**. Static reconstruction of the existing USTAR writer's padded sizes gives approximately **218,316,800; 521,728,000; 297,072,640** archive bytes, also below 512 MiB. Raw-byte caps should not generally be confused with archive-byte caps; the distinction does not invalidate this small-member-count plan.

At the recorded Data-volume free space of **23,975,342,080 bytes**, two 512 MiB staging copies leave **22,901,600,256 bytes**, above the 20 GiB floor. If the separately reviewed three-archive relocation consumes 1,286,025,216 bytes first, the same two-copy staging allowance leaves only **21,615,575,040 bytes**, or **140,738,560 bytes** above that floor before new metadata, allocation overhead or concurrent writes. Neither preparation reserves capacity. Any later preservation registration requires a fresh combined capacity check and actual-volume guard, not reuse of this historical free-space assertion.

The interrupted **3,755,212,800-byte** SQLite file exceeds the whole-file 512 MiB cap and is correctly excluded without being discarded. Two such large staging copies would exceed current Data-volume headroom; a future chunked recovery design or larger qualified scratch arrangement requires its own reviewed contract. This review does not certify the interrupted database's rows or completeness.

No material metadata or arithmetic error was identified. Before graph preservation, bind this inventory, exact preservation/transport source, approved connection metadata, fresh capacity, unique output identities and a finite round-trip contract. Packing must compare streamed array bytes against these expected hashes, and downloaded members must be independently verified. The existing ETH raw backup does not cover these graphs; C16 remains partial.

Reviewed SHA-256: inventory.json `5fa342661f873a62c6fce986fa97fbea9fb05f96fbeaff2c5149e9846133bbe3`; batches.json `4baac73cb06b78a712d99713e109e31b3492c12d8c6884e9b35b385aaf91488f`; STATE.md `e9207561bdb687454c68c2915756aef6d58bf8d35e51b61c418c545085595ecd`.
