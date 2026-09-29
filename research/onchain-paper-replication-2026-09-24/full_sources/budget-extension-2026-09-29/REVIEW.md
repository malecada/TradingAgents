# Independent review — cumulative budget extension implementation

September 29, 2026; base `f199dddf`. Reviewed CONTRACT.md, `budget_extensions.py`, admission/lifecycle/structural-verifier changes, the new synthetic tests and saved focused receipts. No tests, admission commands, empirical jobs, raw inputs or network requests were run. Only this review was written. No actual allocation amendment or empirical claim is accepted by this report.

**No material counting or admission bypass was identified in the reviewed valid-admission paths.** The implementation preserves the historical family object and counts every recorded same-mechanism claim, including failed attempts. The focused evidence is meaningful but does not yet cover every edge promised by the contract; those gaps are specified below.

## Independently traced invariants

- `admission.py` retains exact family equality with every prior same-mechanism claim. The effective ceiling is separate from that family; `lifecycle.py` records it in new claims. Historical claims without the new field remain interpretable at their original family ceiling. Neither family renaming within the registration nor changed prior-attempt/history fields resets the count.
- Extension, review and allocation references must be included in `source_files`, agree with current committed bytes and agree with the design commit. Strict extension/review schemas bind the program, unchanged base family, integer ceiling, named first adopter, reason and accepted review of the exact extension hash. The allocation must parse as an object; its substantive accounting remains the independent review's responsibility.
- Before first adoption, the extension snapshot must equal the complete set of recorded same-mechanism claims. Every entry has a unique known identity, a claim hash, a complete/failed terminal hash, and matching terminal identity/status/claim binding. An active claim cannot be included without a terminal and cannot be omitted while satisfying set equality. Contradictory complete/failed terminals are rejected by the existing claim enumeration. This checks recorded lifecycle closure; it does not independently prove physical worker/cgroup death.
- `consumed_before` must equal unchanged `prior_attempts + snapshot size`. The admission spend check uses all current same-mechanism claims plus historical prior attempts, not the older snapshot count. Consequently later claims cannot spend repeatedly against a stale consumed count. Both preflight and the existing exclusive start lock re-evaluate admission before writing a new claim.
- The maximum effective ceiling already recorded for the mechanism prevents later omission of an adopted extension or use of a lower ceiling. Reusing an extension also binds its original adopter and rejects omitted pre-adoption claims. A new extension must initially bind the full updated closed snapshot. Same-ceiling, separately reviewed extensions are not prohibited by the current contract; they cannot create additional numerical capacity.
- Claim enumeration still counts across programs when the mechanism matches. Extension metadata itself is program-bound; moving programs is not a free reuse of an old program's extension. Unrelated mechanisms are excluded from this extension's count/snapshot and retain ordinary admission behavior.
- `verify.py` independently reconstructs the recorded effective ceiling from committed registration/extension/review bytes without importing `effective_budget`. Its existing pinned-file loop verifies extension/review/allocation bytes at both source and design commits. It rejects an inflated saved effective ceiling. This structural verifier does **not** independently repeat the full snapshot/adopter/history admission algorithm; its module's historical-completeness limitation remains applicable.

Review acceptance is a committed metadata assertion with reviewer/scope text, not cryptographic proof of independent human review. The actual accepted allocation and final release review remain necessary. Budget acceptance grants no new sample freshness, source-body admission, resource permission, financial fit or deployment authority.

## Tests and retained receipts

`red01` preserves the fixture's no-change commit error and is not useful feature-failure evidence. Corrected `red02` records 12 intended failures. `green01` records **49 passes** across the new extension and existing lifecycle suites, with child exit 0, verified cleanup and zero memory-limit events. The reviewer read those receipts rather than rerunning them.

The initial tests meaningfully cover: extension of an exhausted three-claim family by exactly one slot; failure consuming that slot; no mutation of prior receipt bytes; omission/corruption of snapshot identities/hashes; changed base history; boolean ceiling; wrong adopter; rejected/wrong-hash/unpinned review; a stale snapshot after another closed claim; carrying an adopted extension forward; and independent rejection of a tampered recorded effective ceiling.

The initial 12-test extension snapshot does not directly exercise several material contract edges:

1. Nonzero `prior_attempts`, particularly the real 17-historical-plus-current-claims arithmetic.
2. An actually active same-mechanism claim, both explicitly listed and omitted from the first snapshot.
3. A second extension following an adopted higher ceiling, including full prior-extension-claim closure and rejection of later rollback to the lower extension.
4. Extension/review/allocation drift between design and source, missing review metadata, and direct structural-verifier metadata tampering beyond the saved ceiling field.
5. A concurrently existing unrelated mechanism, including one with its own extension, to demonstrate that snapshot membership and cumulative counting stay separate.

Static tracing supports the intended rejection/accounting behavior, but it is not a substitute for these regression cases before using the new mechanism for the prospective empirical amendment. No broader named offline result is claimed for this increment. The prior 3,272-pass memory-engineering result belongs to the earlier committed source, not these budget changes.

## Initial reviewed identities

| File | SHA-256 |
| --- | --- |
| tradingagents/research/budget_extensions.py | `fb8cbfe5cb7b2841e940a6b1874830d801bda3ff157751e1756f4c5ae38d3e7b` |
| tradingagents/research/admission.py | `d9cf69e5685311f2a666167144243b3176e00eb621765264d90fe9037f7cb63f` |
| tradingagents/research/lifecycle.py | `23d7fef7dbdf1eb4833bcf1b9b2c35df4f88bc9550dcb65f1b31c9fe2d9dfe53` |
| tradingagents/research/verify.py | `796434dc9ca486f349a3a48904eb0925658e161656d94188faeb70b58e8f63df` |
| tests/research/test_budget_extensions.py | `248d7ecd8c6b080529f5ceb15d01ee4b5d84520ae02495ac6cb7dc0f1a738fae` |

## Expanded regression review

Independently inspected the subsequent test additions and strict reference validation. Admission now requires string paths and lowercase 64-character SHA-256 strings before resolving an extension/review/allocation reference. Existing committed-path and source/design checks still apply; no new path or pinning bypass was found.

The added tests substantively close the principal missing accounting cases. A family with 17 historical attempts and one closed claim can spend its nineteenth allowed attempt but cannot start a twentieth. First adoption rejects an actually live same-mechanism claim whether omitted or listed without a terminal. A second extension includes the first adopter in its closed snapshot, preserves that claim's bytes, rejects rollback to the first lower ceiling and permits continuation at the new ceiling. Separate extension/review/allocation working-file drift cases fail before claim creation. A different mechanism can still claim its own original one-attempt budget after the first mechanism adopts an extension.

Saved `green02/child.log` independently records **57 passes** across extension and lifecycle suites. The final receipt records complete phase, child 0, verified cleanup and zero memory-limit events. No test was rerun by the reviewer. The initial tests/receipts and initial hash snapshot above remain preserved.

No material production correctness finding remains from this bounded re-review. Remaining limits are narrower than the initial gap list: the new drift cases exercise working-tree versus commit drift, not a dedicated different-design-commit extension fixture; the unrelated-mechanism test checks a new ordinary claim, not two simultaneously extended mechanisms. Missing-file/malformed-reference and additional structural-verifier corruption cases are not individually demonstrated by these additions. Existing source/design checks and mechanism filtering were traced statically; these statements must not be advertised as separately executed tests. The verifier's limited independent ceiling reconstruction, rather than a full second history/adopter admission implementation, remains an explicit boundary.

Current reviewed hashes: admission.py `61d7f91a331a95c3f00b56ba35daab63d18ab903ee0ea64a0eada3f9a7871e4f`; test_budget_extensions.py `1314b3c778a11a798a748f661963f701d380e5faea50d950dfb559b54c9f7ff2`. The other three production files retain the initial hashes above. Named offline verification is a separate pending step. No real extension, allocation, data/resource admission or empirical claim has been accepted by this implementation review.

## Historical compatibility finding — P1, correction required

A subsequent real-history metadata inspection identified a material namespace collision missed by the synthetic review above. This finding supersedes the earlier no-material-finding conclusions for the initial source hashes.

`research_runs/dated-mark-20260911/claim.json` (SHA-256 `0b65ed7dbbe221b3e0544f677266ac320eb67e03134f5cfdd39137f0d6eac274`) contains the historical experiment field:

```json
{"budget_extension":{"path":"research/strategy-search-2026-09-11/dated-extension-certificate.json","sha256":"242f31d42386e23906138c703ca6b440153cdaefd61c035db83062938afc4b0a"}}
```

The original source is `5cf5dd843131da489a4695623b81009a244ab49f`; its committed registration is `research/strategy-search-2026-09-11/gates-dated-mark.json`. The existing certificate uses a `{path, sha256}` format, not the new `{extension, review}` format. The reviewer independently read the compact claim and confirmed this shape; no historical experiment was executed.

The new `verify.py:49–53` interprets every non-null `budget_extension` as the new schema and immediately indexes `reference['extension']`. That raises `KeyError` on this valid historical record. `admission.claims()` verifies **all** saved claims before filtering mechanisms, so this collision blocks otherwise unrelated future admission and source rechecks throughout the shared repository. The new admission helper also assumes the same overloaded field at `budget_extensions.py:14–19`. Existing ordinary tests and the unrelated-mechanism synthetic case did not contain this real legacy field shape, so their passing results cannot establish historical compatibility.

The appropriate correction is a distinct new reserved field, proposed as `cumulative_budget_extension`, consistently used by admission, adopter matching, structural verification, tests and contract documentation. Preserve the legacy field, registration, certificate and claim bytes and their prior interpretation. Do not mutate history, reinterpret its certificate as a new extension, or silently ignore malformed objects in the new field. Add a committed historical-format fixture and confirm both direct verification and a subsequent all-history admission scan remain valid while the new field retains its strict validation.

The initial broad offline01 source is now superseded and must not be credited as verification of the pending correction. Its run/stop outcome must remain preserved. At this addendum the rename, regression and corrected-source verification have not yet been independently reviewed; no release conclusion is made.

## Historical compatibility correction review

The P1 namespace collision is resolved in the current inspected source. `budget_extensions.py:14,69` now reads and matches adopters through `cumulative_budget_extension`; `verify.py:49–50` independently uses that same new field. CONTRACT.md reserves the new field and explicitly preserves the older `budget_extension` metadata interpretation. The renamed tests exercise the new mechanism, while the historical-format fixture deliberately retains the original `{path, sha256}` field. No permissive fallback was added for malformed new-field objects: admission still requires the exact extension/review reference shape and pinned metadata. The corrected namespace does not change cumulative spend arithmetic or rewrite historical family objects.

The saved `red03` is an actual before-fix rejection of the committed historical-format fixture at admission. `green03/child.log` records **58 passes** across the extension and lifecycle suites. Its final receipt records complete phase, child exit 0, verified cleanup and zero memory-limit events. The fixture checks historical-format admission, completion and direct structural verification; it does not separately start a second claim after that historical-format claim. The saved real-history metadata check supplies a distinct integration observation: `historical-compatibility.json` records successful structural enumeration of **61 claims**, **121 preserved claim/terminal hashes**, and **zero new extension adoptions**. The reviewer independently rehashed all 121 listed compact receipts and found every current hash equal to the saved value. The reviewer did not rerun claim enumeration; the saved observation does not validate economic results, raw inputs or terminal output bodies.

`offline01/final.json` preserves the superseded run as failed after `InterruptedError: guard received signal 15`, with child status unknown (`null`) and verified cleanup. STOP_REASON.md explains the namespace correction. That interrupted run is not passing evidence. Corrected-source `offline02` is a separate pending broader verification and is not credited here.

All seven entries in `source-bindings-v2.json` were independently rehashed and match. The changed current identities are:

| File | SHA-256 |
| --- | --- |
| tradingagents/research/budget_extensions.py | `59d22880e9ff7909508db6b0c15a7a833df30be365af4e31d643ed64afabb25a` |
| tradingagents/research/verify.py | `a520a756ec3fa126f56ec1c694851b6f46416e462228eb51a6954385b449f439` |
| tests/research/test_budget_extensions.py | `64b68027a12ea0c9e21176e7f17adcd89186cde06d893d787baa88534e3df64f` |
| CONTRACT.md | `5951ed04f26834390169cac17f520d97748cadf8b5005fd6bc5cf72c0045d33d` |

Admission and lifecycle retain their most recent hashes above. Evidence identities: source-bindings-v2.json `5a0e0c1637abd6139b8958eafefec588cc4037f2561878f527ba9784c8bd8aeb`; historical-compatibility.json `2380ce25ca0ce3f5d48594b8f93d254fbfc47662b493681808089c449d04473b`; green03/final.json `9cd9a0610c3afdc79b466a66b2b78784b9dd2e86701214f339b7edcbd4acba90`.

No additional material finding was identified in this bounded correction. Earlier limits on structural verification and unexecuted edge cases remain. No actual cumulative amendment, allocation acceptance or empirical release follows from this implementation review.

## Corrected-source broad verification closure

The saved named `offline02/child.log` now records **2,768 standard passes plus 97 passing subtests** in 1,141.06 seconds and **525 neural passes with 2 skips** in 426.08 seconds: **3,293 passes plus 97 subtests, 2 skips** in total. The two CUDA-dependent checks remain unexecuted; the retained test profile also explicitly withholds legacy files. This is the named offline target, not a claim that every repository test or empirical requirement ran.

`offline02/final.json` independently reads complete, child exit 0, verified cleanup, zero memory-limit events, elapsed **1,571.4648030209992 seconds** and sampled memory peak **2,569,056,256 bytes**. Its SHA-256 is `897a58200ea6e56aaf3a0073e3331a251bdf0b6c5aafd1cbcce4095dc4a46c9a`. All seven frozen source-bindings-v2 entries were rehashed and still match. The earlier interrupted offline01 remains preserved and receives no passing attribution. The reviewer ran no tests. This closes the pending broad engineering verification for the inspected budget implementation; it does not itself release an empirical claim.
