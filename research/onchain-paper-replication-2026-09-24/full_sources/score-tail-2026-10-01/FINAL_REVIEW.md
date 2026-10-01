# Independent corrected tail/seal review

The original ST1 tail-loss counterexample is corrected, but acceptance of the combined seal boundary remains withheld for the reciprocal destination gap below. Earlier source and review remain preserved.

The source now runs full two-pass tail verification after `batches.append`, using the original terminal hash and the explicitly supplied tail lease. The targeted saved red02 run failed as expected, and check02 reports **13 passes in 0.23 seconds**. The regression uses an independent still-valid batch lease, revokes the tail lease during batch header publication, expects refusal and confirms that the destination payload remains. The correction preserves both stores and does not retry. No tests were rerun by the reviewer.

## Residual ST1 — final tail callbacks can invalidate the destination

`score_tail.py:240–244`: the newly added `verify` invokes external tail lease callbacks after the final checks inside `ScoreBatches.append`. It validates only the tail. If one of those final callbacks alters the just-published batch payload/header, redirects its root, or revokes the independent batch lease, `seal` still returns the previously computed batch head. The returned combined seal can therefore describe an invalid destination despite both components having been checked at separate earlier points.

Required correction: preserve the expected destination root/start/chunk identities and exact header/payload hashes, perform the final external checks for both leases, then validate the exact newly published destination and tail evidence through the return boundary without a subsequent external callback that can invalidate the other side unchecked. Retain the explicit non-atomic limitation after the final observations. Add a targeted final-tail-lease destination-corruption case; do not erase the already published destination if it fails. This is a source-derived counterexample, not an additional executed test.

The underlying per-record fsync/readback, ordinal/purpose chain, failed-prefix/pending-byte accounting and unchanged scope exclusions remain as assessed in INITIAL_REVIEW. This primitive still provides no matcher integration, actual purpose derivation, successor admission, scratch replacement or full-workflow capacity. Post-publication tail verification also rereads/decodes the bounded tail again; the 8 MiB record cap is not a total live-memory or I/O allowance.

Exact reviewed SHA-256: source `d81cb1e769c8e8faf7bdda731408a21eabce49292810679ba04b880133226f52`; tests `d7997700c385eed9074f9fac53c3771233e83c3d449c1e47dc3008546666ab9c`; check02 `a4fcbae31f76559530513a3c4c547938a1d87a68e3c33f5e4fb2496d7128502d`; red02 `ea1ae3e9b24d0c8540333b9709514c91fa3c394fc323d206437b417a9c2f97b4`. Preserved check01 source hash is `d4617fa72973e15940e00860a546a924ce643bbaa6f248469980885955a16f01`.
