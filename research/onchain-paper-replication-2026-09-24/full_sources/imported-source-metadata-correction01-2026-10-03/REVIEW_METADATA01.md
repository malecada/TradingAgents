# Independent imported-source metadata review 01 — 2026-10-03

Disposition: **WITHHELD**, for one concrete validation-order regression (ISM1). The imported-only bounded reference is a justified correction to the actual failed start metadata, but the new final check reintroduces live callbacks after the last MCM matrix/receipt/output checks. Frozen candidate01 and its failed/successful source-test evidence must remain unchanged.

## Exact reviewed snapshot

- Manifest: `02ccaa50c57e36598a0ddeb219a8261753d78fbb0903cbd5fa7e17676635df24`.
- `compact_mcm.py`: `0c27b0963ce8e1b20bfcd387537eed1b376524c4e3dfabf9b37fddbdaea3cdc8`.
- Baseline: `ed94415ff1798422d66bb19fc6b7ab72e70afef999101d0fb206e3f65556f93a`.
- Source inventory: `9b4eb6799cb7484b71e0c0dc914b28d4e6bfac678aed5ba810e7c55a257cf69c`.
- Retained actual-start reconstruction: `26a8082317afeb94cdc69f7b3772f608f5c69e91716da622cfb9ef12d03f38ab`.

All 12 manifest bodies were independently checked for byte extent and SHA-256. All 153 source origins were read and checked against the inventory. Comparison with the hash-authenticated native03 predecessor found exactly one changed target, `tradingagents/research/onchain_replication/compact_mcm.py`; the 142-package composition remains declared. The baseline and current snapshot were parsed without importing either. Removing only the new helper, its start-expression call, and the two new `_check` clauses produced exact whole-module AST equality, including all numerical functions, production paths, serializer/read uses, reservations and legacy code. No production module was installed or imported.

The eight passing methods in `green04.log` are retained stdlib/extracted-AST checks. Their source and raw logs were read, not rerun as a suite. The original missing-helper RED, intermediate relative-import harness failures and subsequent successful runs remain preserved. The tests correctly label prospective completion hashes/inodes as placeholders rather than published authority.

## ISM1 — a new last callback invalidates the final output verification

**Location:** candidate `compact_mcm.py:218–221`, reached after `publication._verify` at lines 216–217. The last clause calls `_sources(self._dictionary)` and then returns without another MCM matrix, receipt or output rejoin.

This call is not callback-free. `_sources` at line 53 dispatches to genuine `Target.sources`. In the unchanged selected `imported_mcm_identity.py`, `Target.sources` first calls `self.check()`. Its chain includes `Target.check` → `ImportedExecution.check` → import-stage lease → compact Owner lease → Binding lease and its live `_guard` calls. Those checks authenticate the imported dictionary/target and source closure; they do not revalidate this Produced MCM's numeric output or published output namespace after a live callback. The former final callback-free verification is therefore no longer final.

**Impact:** a live check that mutates the produced matrix or output after `publication._verify` can leave dictionary, target, source-map and source-reference checks valid. `_check` can then return successfully despite invalid output. No claim is made that the retained real failure exercised this route: it failed before any MCM stage. The defect is prospective, introduced by the new clause.

**Independent counterexample:** the exact candidate `Produced._check`, `_sources`, `_source_evidence`, and selected actual `Target.sources` method ASTs were compiled into an isolated stdlib namespace. Byte buffers represented the compared matrices; fake authority and publication helpers represented only their boundary predicates. The fake dictionary check mutated the matrix on the fourth check, reached through the final actual `Target.sources`. Earlier numeric and publication predicates would reject that mutation if called afterwards. Observed sequence:

```text
dictionary_check_1
dictionary_check_2
matrix_verified
dictionary_check_3
matrix_verified
final_publication_verified
dictionary_check_4
late_live_callback_mutated_matrix
[actual Produced._check returned successfully]
```

This is an actual-method control-flow counterexample with scalar fake authority, not a genuine Owner, NumPy result, OS proof or model execution. It isolates the missing last rejoin and does not require changing numerical equations or assuming a source-hash collision.

**Narrow correction:** retain the full callback-bearing source validation, but perform its second reference join after the last `self.lease()` and before `_original`, `_numeric`, `_evidence` and final callback-free `publication._verify`. Alternatively introduce a genuinely callback-free original-source validation with a separately reviewed contract. Do not merely relabel `Target.sources` as callback-free. Preserve a candidate01 RED against the whole selected `_check` and an independently reviewed new candidate GREEN that either rejects late matrix/output mutation or verifies all affected original contents after the last live call. The existing extracted equality-clause test cannot establish this ordering property.

A reproducible minimal harness outline follows; source extraction must retain the actual method bodies. It is not an authorization to run the numerical fixture:

```python
# Extract actual Produced._check, _sources, _source_evidence and Target.sources.
# Globals: _imported = lambda d: True; _owner = lambda d: d.owner;
# _sources itself is the extracted actual function, not a stub.
# Real Target.sources sees a fake run with admitted source_files for p/k/h,
# required_sources()={'p'}, KERNEL='k', HELPER='h', file_hash returns 'a'*64.
class Buffer(bytearray):
    shape = (1, 1)
    dtype = 'synthetic-byte'
matrix, saved = Buffer(b'a'), Buffer(b'a')
calls = 0
def dictionary_check():
    global calls
    calls += 1
    if calls == 4:
        matrix[0] = ord('b')
# dictionary.check = dictionary_check
# dictionary.sources delegates to the extracted actual Target.sources.
# self.lease and _original are no-op fake authority boundaries.
# self._numeric asserts matrix == b'a'.
# publication._open_verified yields saved, permitting real memoryview compare.
# publication._verify asserts matrix == b'a'.
# self._start.sources is actual _source_evidence of admitted p/k/h map;
# remaining _check receipt/scope/path fields are fixed scalar placeholders.
actual_produced_check(self)
assert matrix == b'b'  # candidate01 incorrectly returned after this mutation
```

## What the proposed representation does establish

The actual failed start was 19,902 bytes against an unchanged 8,192-byte limit, including an 18,610-byte canonical map of 144 sources. `_source_evidence` replaces only the imported route's repeated map with explicit `registered-source-map-v1`, count and canonical digest. Full source reconstruction and actual body-hash checking remain in `Target.sources`; the full admitted map remains available from genuine registered source authority. Legacy dictionaries return the original map object unchanged. The new stored-reference equality checks cover changed digest, count, kind and extra fields against the freshly reconstructed map. These useful properties do not cure ISM1's placement.

Both actual retained start shapes and prospective complete-record expressions were included in the implementation's bounded extent checks. The unchanged completion body derives from start, so the source-reference representation is carried forward without widening metadata limits or reservations. Exact successor-generated path lengths, committed source identities, registered source map, completion/readback and failure paths still require review in their actual assembled capsule. Placeholder completion checks are not evidence of an actual stage, output receipt, successful numerical comparison or available full-size capacity.

The source snapshot explicitly does not compose the separately pending candidate03 cleanup correction. Acceptance of any later metadata correction must not imply that composition or the independent cleanup review has already happened.

## Unproved and next boundary

No NumPy/Torch module, genuine matching/dictionary pipeline, new native unit, admission, claim, registration mutation, numerical fixture or network operation was executed during this review. No financial return convention, timing, fees, funding or predictive result was exercised by this metadata-only change. The complete existing two-cell failed/unavailable denominator and spent claim remain unchanged; no retry, budget refund, paper-budget transfer or success claim follows.

A new frozen source revision resolving ISM1 must be reviewed independently. A later actual execution additionally needs the composed source closure, new identity, cumulative engineering amendment, generated inputs, genuine gate/capsule/runtime mapping, finite native controls and preservation release. The closed first primary and its original failure remain immutable.
