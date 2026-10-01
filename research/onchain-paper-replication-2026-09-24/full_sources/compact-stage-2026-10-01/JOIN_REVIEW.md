# Independent direct score-join evidence review

The specific evidence gap recorded in `REVIEW.md` is closed for a changed finite score. The production implementation is unchanged.

The added test uses the actual CompactMatcher first, allowing it to persist its original score in PairLog. Only the callback result passed to MCMScoreStream is changed for the first cell: zero replaces a nonzero score, or one replaces zero. Thus the replacement is always different, finite and within the allowed range; the original matching log is untouched. The stream builds normal tails, batches, checksums and completion around that altered score. A direct call to `compact_stage.stream` succeeds before the test requests a stage seal. The seal then raises the exact `matching and retained score purposes/values differ` diagnostic, and no stage receipt is created. This reaches the new cross-store comparison rather than an earlier malformed-byte/checksum refusal.

The retained `join01.log` reports **1 passed, 7 deselected in 0.90s**. The previous seven-case check02 test is preserved byte for byte as `test-check02.py`. This targeted run does not claim a repeat execution of those seven cases or separately test a purpose-only or ordinal-only substitution. The prior acceptance and all ownership, outer stage inventory, registered membership, resource and empirical exclusions remain unchanged. No tests or numerical jobs were rerun for this review.

| File | Reviewed SHA-256 |
| --- | --- |
| `compact_stage.py` | `fe96c774ec784cd2899747db8f9736ff6655a369a0113de001e3b60c782ad83f` |
| Current `test_compact_stage.py` | `54ccbdf58b4ea93829d4cdb4248c10500021c0620cd4e4a8c4f426eb0b80509e` |
| Preserved `test-check02.py` | `996e6d4b1d9357773c140ccf975ca489216476c4c32208790b0441657d1922c6` |
| `join01.log` | `2267135853fab4de0394192a247b52c02059e36fe82b3a8e5a3c08c60335cd48` |
