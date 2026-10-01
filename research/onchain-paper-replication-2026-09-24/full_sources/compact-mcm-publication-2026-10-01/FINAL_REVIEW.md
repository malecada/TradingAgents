# Independent corrected compact MCM publication review

Accepted for current-owner publication and mapping under the explicitly selected registered output policy. CMP1 and CMP2 in the preserved `REVIEW.md` are resolved. This does not certify training sample/dictionary provenance, select native production, append FeatureJournal events or admit a final representation.

The receipt now binds the full current Binding record by canonical hash and retains the exact claim hash, owner, stage receipt, selected policy hash and workflow output reservation. It no longer duplicates the large Binding object. Its exact encoding is checked before any namespace creation using a 64-character placeholder for the artifact hash; the real hash has the same encoded length. The original per-required-graph reservation still covers the artifact allowance plus one bounded receipt, separately from retained pair/score evidence.

The corrected mapping wrapper performs `_verify` after the underlying mapping context has fully exited. It supplies a no-op lease, so receipt, attempt inventory, stage evidence and artifact content are checked after all underlying live callbacks without introducing another external callback. The underlying primitive still pins the original mapped inode through its own exit checks. Exceptions propagate with mapping/file cleanup and evidence preservation; consumers may acknowledge work only after the outer context succeeds.

The two new regressions wrap the real underlying reader and enable mutation only after its yielded body finishes. One overwrites the receipt; the other adds a foreign attempt file during underlying exit leases. Both previously escaped the outer reader and now refuse. This directly exercises the nesting boundary rather than an earlier wrapper check.

Saved evidence remains separated:

- Original check01: **1 failed, 3 passed in 76.57s**. Positive publication hit the receipt cap; route, budget and foreign-scope/revoked-claim refusals passed.
- Red02 after the bounded receipt correction: **2 failed, 1 passed, 3 deselected in 76.00s**. Actual positive publish/verify/map/compact-owner closure passed, while both delayed exit mutations reproduced.
- Corrected check02: **3 passed, 3 deselected in 75.49s**. It executes the positive path and both delayed exit refusals. The three earlier refusal cases were not rerun in this targeted check.

The positive fixture has a real temporary ResearchRun/Binding, an explicitly selected committed policy, actual fourteen-pair MCM evidence and a current required-graph stage. Guard enforcement is mocked; the dictionary ownership fixture is zero-pair synthetic and expected scientific scope comes from the caller. No whole-workflow physical quota, RSS, empirical performance, successor admission, native route or externally recoverable test-artifact archive is claimed. Source/input immutability between full boundary checks remains a caller obligation. No test or historical job was rerun by this reviewer.

| File | Reviewed SHA-256 |
| --- | --- |
| Current `compact_mcm_publication.py` | `c0529fd08dc47ea674804bcea4f0875bf15312aa9ba4e7bc81c822eb201714d6` |
| Current `test_compact_mcm_publication.py` and preserved `test-red02.py` | `1d8a0ab4150bf97a05a90ea77ad618746617a21b598f830557db542abf57a681` |
| Preserved `publication-red02.py` | `241340d5eb2676f17a76d24ef1cf9b93ba4fd8baf0a2c1c5e8232795ac4f1533` |
| `red02.log` | `66c6af5e4139270ecd1f9612e38d06b0abc1affa0ec6d3fca3e24743fd325b25` |
| `check02.log` | `d3ffca13a32d890ca81bdeab908079b4d6490d5ddbd7158f1aeeb1c0cf49d5fb` |

These identify inspected files and saved evidence, not a complete execution-time dependency manifest.
