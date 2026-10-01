# Independent corrected compact MCM output review

Accepted for bounded publication and context-scoped read-only mapping from externally trusted completed compact MCM evidence. CMO1 from the preserved `REVIEW.md` is resolved. No registered producer selection, sample/dictionary admission, output-budget admission or representation closure is established.

`open_verified` now retains the original source descriptor and mapping throughout successful context exit. Before final content verification it requires the original signature to match both that descriptor and the current directory entry. After `_verified`, it requires the returned signature and both live identities to still equal the original. The changed detached inode can no longer be hidden by a new valid pathname. The mapping closes in `finally`; the source file and directory descriptor close through their enclosing context/finally paths. A consumer exception propagates after cleanup rather than yielding successful acceptance. Consumers must still discard all views on exit and defer downstream acknowledgement until exit succeeds.

The new test actually observes the changed finite value through the original mapping after moving that file away and replacing the pathname with original valid bytes. Its pre-fix run fails because exit did not raise. The corrected targeted run includes that refusal, the existing in-place mapping mutation refusal and successful exact read-only publication/mapping. It therefore exercises the specific identity discontinuity rather than merely a bad hash at a pathname.

Saved evidence: `red02.log` reports **1 failed, 12 deselected in 1.59s**; `check02.log` reports **3 passed, 10 deselected in 3.62s**. Original check01 source/test bytes are preserved and match the initial review hashes. This targeted run is not a claim that all thirteen current cases were rerun together. No test or numerical job was rerun by this reviewer.

The memory comment now correctly describes O(chunk) scratch including raw bytes, conversion and byte copies. It does not claim an exact scratch or process-RSS reservation. The original numerical float64-to-float32 join, exclusive publication, full stage verification, partial evidence preservation and scope/cap refusal remain unchanged. Current-state and content checks are sampled, not an atomic snapshot against arbitrary continuous mutation. Physical quota, mapping/page-cache usage, actual OS guard, historical admission and a native production route remain external responsibilities.

| File | Reviewed SHA-256 |
| --- | --- |
| Current `compact_mcm_output.py` | `d462f271dc688e16321a52ed493aa8d81ca890974ccbf2fef209b4764293d393` |
| Current `test_compact_mcm_output.py` | `1402db15e65d5d430bb35cd0758c981e5b7946dee929151372fde9fe9f126ffd` |
| Preserved `output-check01.py` | `ceb8a7757dd5a78a1804c25a10d7827afa7ebe061180b49030bb65a897e75b5a` |
| Preserved `test-check01.py` | `70f780801e9dddcc11fd6daca89d81ca1d1fa9411e94bd648734b389ad9d8303` |
| `red02.log` | `7a6c8c952eae10a891939090448afb8304a55803b07eb6e1df520c79d30cb946` |
| `check02.log` | `1d98837760742973ccdf373448b1cc11b26d369382eb2adbf5d381f940908a1d` |

Hashes identify inspected files and saved logs, not a complete execution-time dependency manifest.
