# Independent non-tail local context review

Disposition: **WITHHELD for three source correctness defects**. No transport, authority, resource capacity or empirical release is accepted. The frozen author candidate and historical evidence remain unchanged.

The reviewed manifest is `8023fc8d06597f22291a25a495e38cac6c5c124f4184e32c705d9516a3705e06`; the selected `non_tail_context.py` body is `1a980f0de107f7fdabce52d4a45731b346594afd81091114ed6c065c0efd3d0d`. All **12 manifest members** and eight referenced dependency bodies were independently length/hash checked. The 13-file total includes the manifest itself. The author report and retained unsuccessful attempts were read, not treated as proof of the assertions below.

## Findings

1. **NTC1 — dependency bootstrap loses the first fatal and reads without a finite bound.** `non_tail_context.py:15` performs `Path.read_bytes()` before checking the 1MiB limit. The actual extracted `load` function, actual `Path.read_bytes` and a synthetic stream produce an unbounded `read()` call; a first `MemoryError` is replaced by the stream-close `OSError`. The resulting ordinary error is observably different from the actual fatal. Use bounded owned-descriptor reads and independent first-fatal cleanup at this bootstrap boundary; keep original path/body joins and do not depend on the module being loaded to provide its own safe bootstrap.

2. **NTC2 — shared reservations can lose cumulative spend under concurrency.** `non_tail_context.py:65–68` reads `_spent`, computes a successor, checks limits and replaces `_spent` without synchronization or thread/lifetime exclusion. A deterministic barrier at the actual `require(..., 'cumulative reservation exhausted')` boundary lets two threads both reserve one byte with `max_commands=1`. Both succeed; stored counters report only one command/part and 32,768 rounded bytes, rather than two/65,536. The barrier only selects a valid interleaving; it does not alter the arithmetic or limits. Serialize the whole check/reserve transition or explicitly reject non-owner threads/reentrancy before state access. This matters even for unadmitted proposal counters: the stated cumulative limit does not hold for the public shared object.

3. **NTC3 — clean-body cleanup uncertainty does not revoke shared reservations.** `non_tail_context.py:146–152` selects its final revocation action from the body exception before attempting reader closure. When the body succeeds but the actual root FD close reports an error, `finish` raises real `owned_io.CleanupFailure` and only sets the local Context flag. The shared Reservations object remains unrevoked and accepts a subsequent reservation. The retained test closes the real descriptor exactly once, then injects `OSError`; it does not leak a descriptor. Revoke the shared budget whenever cleanup fails, while still attempting all cleanup actions and preserving the first actual fatal. This is narrower than refund accounting: previous spend remains, but uncertain cleanup fails to close the shared session.

All three counterexamples and controls are retained in `check01.py` and `check01.log`. No author implementation was changed.

## Independently supported lower-layer behavior

Actual candidate code and the exact accepted LocalContent/owned_io modules were loaded using only stdlib. Tiny synthetic byte containers were constructed using the retained format fixture constructors; these are not genuine Owner/Target or empirical data. Independent reconstruction compared every emitted part with the original file bytes and recomputed cumulative 32KiB rounding for original and recovered streams.

The score-batch container retained four members, raw-f32 output two, and graph-artifact container three, including JSON/header/terminal and the NPY edge companion. The graph path preserves complete NPY files including headers, not recast arrays. All three local-copy controls passed original membership, bytes and doubled original/recovery accounting; activation raised `NotImplementedError`. No output was deleted. Metadata identities remain content claims, explicitly not authenticated live owner ancestry.

The exact reader checks complete terminal/header-chain and declared byte/header semantics; Context derives inventory rather than accepting caller-supplied identity rows. Policy limits are detached immutable scalar data, positive strict integers; command/part/rounded counters are reserved before reads and have no refund path. The deadline is sampled, not a hard wall. Initial reader verification and repeated whole-container hash reads are not remote command accounting. Failed/corrupt reads retain bytes and ordinarily revoke the context; the specific cleanup gap above remains.

The proposal rounds up by `ceil(size/32768)`. Existing `archive_transport.py:269–270` readback reserves `(size//32768 + 1)*32768` to inspect an extra block, so these are not identical prospective remote charges at exact block multiples. The candidate is explicitly unadmitted local accounting; an integrated successor must derive actual readback and control-command charges from its selected transport, not copy these counters as an operational budget.

`activate_transport` unconditionally refuses after its content check. Actual archive dispatch still requires its genuine registration/population, held Operation/Ledger and cumulative durable context. Existing event transport and the separately unadmitted tail adapter do not provide non-tail authority. A 168-byte event format cannot be substituted for these f64/f32/NPY members.

## Claims not tested or granted

No genuine registered population, durable reservation ledger, live/revoked held token, cold authority, source/runtime admission, native limits, remote upload/recovery, retirement/disposal, whole-size capacity, numerical cast/equivalence, gradient/checkpoint preservation or financial result was tested. No array package was imported, no array values decoded, no SSH/network/job/claim occurred. Source acceptance of a successor must precede separate integration and actual authority/resource review. The proposed counters are not research spend and this review changes no budget or historical outcome.
