# Independent registered hub-edge integration review

September 30, 2026. Initial source and saved-evidence review only. No tests, empirical arrays, graph bodies or jobs were executed. Source/tests remain author-owned; no empirical gate is admitted by this review.

## Initial findings

**H1 — numeric allowance enforced after selector allocations (`hub_census_production.py:28–30,82–99`).** The plan checks only positivity/maximum, while the minimum required buffer is checked later inside measure, after cardinality selection and graph loading. A max_buffer_bytes=1 plan is admitted through _plan and can allocate chunk comparisons/flatnonzero arrays before refusal. A very large declared N can also cause mapped input work before its N-byte membership mask is known inadmissible. Reserve both selector peak and the engine formula before cardinality mapping/numeric work. Test insufficient positive allowance with _open_counts/graph/selection sentinels, not only boolean policy rejection.

**H2 — closed census inputs are not tied to the actual lifecycle parent (`hub_census_production.py:39–55`).** Checks establish mutual consistency of supplied JSON but never require census_experiment to equal this run's admitted parent or the claim/complete/result inputs to match that actual closed parent. The current success fixture demonstrates the gap: a minimal `{'experiment_id':'prior-census'}` object and synthetic mutually consistent terminal are accepted while example-a has no such parent. Require actual parent lineage and exact original claim/complete/output identity before mapping. Replace the success fixture with a genuinely closed lifecycle census parent; add unrelated-parent or forged-compact-evidence refusal before numeric work. Hash consistency alone does not establish the claimed lifecycle ancestry.

**H3 — character truncation does not satisfy encoded metadata reservation (`hub_census_production.py:34–38,107–112`).** The 2,304-byte per-record estimate assumes bounded encoded reason size, but truncation is to 2,048 characters and lifecycle _immutable uses ensure_ascii JSON encoding. Astral Unicode can expand to twelve ASCII bytes per character. Repetition across 35 cell files, producer result and lifecycle ledger/summary can exceed the 1 MiB allowance before final accounting detects it. Bound actual encoded reason bytes or a safely escaped ASCII prefix, retain the complete-message SHA and truncation flag, and verify the full duplicate-record/rounding allowance. Add a long-Unicode failure regression and assert complete producer-plus-output totals, not just string length. The final accounting prevents a successful terminal on excess but does not make the current prepublication reservation correct.

**H4 — cleanup failure can be silently attached to a swallowed exception (`hub_census_production.py:102–118`).** An ordinary error is converted to failed/unavailable rows while primary remains set. A later cardinality-map close failure only adds a note to that exception, which is no longer propagated or stored. The producer then returns normally with no cleanup failure evidence. Distinguish a propagating exception from a handled failure, make unresolved cleanup fatal or explicitly retained, and prevent ordinary dispatcher publication after a leak. Test simultaneous measurement/close failure, KeyboardInterrupt preservation and an all-complete graph-context cleanup failure.

## Supported behavior and test limits

The source preserves the accepted isolated measure implementation byte-for-byte. Selection scans the whole bound cardinality vector in ascending chunks, enforces the expected selected count and passes all selected centers without truncation. Per-center callbacks check center/count/rank and publish exact registered cell filenames, allowing the generic observer to reconstruct a durable prefix. Ordinary measurement failure retains completed rows and fills the remaining denominator with one failed and subsequent unavailable cells. BaseException interruptions propagate for post-death observer closure. Output root containment/same-device checks precede mkdir; the output leaf is exclusive. Cardinalities have hash, size, NPY-v1, dtype/order/shape/extent checks before their map is opened. Mapped graph validation and source shape checks remain active.

The generic source dispatcher writes all three registered outputs and then reuses the previously reviewed final complete storage-accounting check. The new job kind inherits the 540-second whole-job maximum and registered guard-floor forwarding. None of these checks provides a measured empirical runtime, graph residency requirement, or matching-capacity override.

Initial tests include literal/set-oracle complete center outcomes, exact durable cell publication, malformed plans, selected-denominator failure, a two-center completed prefix with actual observer recovery/idempotence, and the finite job schema. They do not yet cover the four findings above, genuine closed-parent lineage, Unicode encoded-byte failure accounting, corruption/header variants, unresolved cleanup, or actual interrupt after a durable partial prefix. The focused green01 was still nonterminal when inspected; no complete passing count is asserted here. Red01 is retained missing-feature/schema evidence as reported by the author, not independently rerun evidence.

Initial SHA-256 identities:

- `hub_census_production.py`: `e2837e8c5901b3732389557f47c9cc7d8081fc2746d339142a316a825230379e`
- `hub_edges.py`: `e5858170437f6d9f0a994315e2b2aa30d502844cf0a1c1b8ec782a1e693887e9`
- `job.py`: `4aff4c2f71bf9e0285ee4785c12710d39d41ff9b829dd95ad6875047a31d39e6`
- `test_registered_hub_edges.py`: `4940ab3ae319a933a76c195312eea042f37609619a0614a0defc9d2c03053afe`

Verdict: corrections and focused evidence required before engineering acceptance. Budget-only extension 54 remains distinct; actual accounting remains 26 consumed of 53 until proper adoption. No empirical execution, scientific capacity change, full matching feasibility or financial fit is approved.

## H1–H4 correction inspection

The four retained red02 failures directly exercise positive-but-insufficient numeric policy, unrelated lifecycle parent, Unicode encoded-reason growth and a measurement error combined with a count-map close error. The corrected focused green02 reports **21 passes in 8.45 seconds**. No tests were rerun by the reviewer.

H1 is resolved in source: _plan now checks the maximum of selector and engine numeric reservations before _open_counts or graph loading. The selector expression covers current/previous chunk indices and comparison temporaries, while the engine retains its N-byte membership plus bounded edge-work allowance. Input maps and graph validation allocations remain separate, explicitly outside this numeric policy.

H2 is resolved: census_experiment must equal the admitted lifecycle parent, and the named claim, successful terminal and summary inputs must resolve to the exact original parent's claim.json, complete.json and outputs/source-summary.json with matching hashes. Existing identity/output/graph joins still apply. The success fixture now actually executes and closes a synthetic registered census parent before admitting the registered child; it no longer supplies only mutually consistent stand-in JSON.

H3 is resolved for the reported expansion path: failure text is converted to printable ASCII and shortened until its actual JSON encoding fits 2,048 bytes, while the full original message SHA and truncation/sanitization indication survive. This covers backslash/quote escaping as well as non-ASCII expansion. The existing conservative physical reservation and authoritative final producer-plus-output measurement remain required; the focused Unicode regression establishes encoded-reason refusal, not an empirical 35-center maximum-allocation measurement.

H4 is resolved for the reported swallowed-error path: normal handled failures no longer receive a silently discarded close note. A count-map close error raises before result/dispatcher publication, while an already propagating interruption retains its primary exception with a cleanup note. Source inspection also confirms that graph-context failure after all durable center cells writes infrastructure-failure evidence and propagates rather than publishing success.

The expanded tests now include KeyboardInterrupt after one durable center, count-map closure observation, graph-context close-error refusal after all cells, root escape before outside write and late-quota failure retaining three lifecycle outputs. The close-error injections close the actual underlying mapping and then raise; they test failure classification/publication behavior, not a real unreleased operating-system map. The expanded green03 log was still nonterminal when inspected, so no passing count is attributed to those new paths yet.

Corrected identities:

- `hub_census_production.py`: `b9c406f19c32f2b78409b9a3260edebcad0ced042e9e4d187ff44e574d763d2a`
- `test_registered_hub_edges.py`: `2cd458be7f1741a1b3fea27fabfad8fd8cdccd6b85404b60dc2703549cb044d7`
- `hub_edges.py` and `job.py` retain their initial hashes above.

Provisional verdict: H1–H4 source corrections are accepted; no further blocking source finding identified in this bounded pass. Final focused acceptance awaits the expanded terminal evidence, and named broad verification/exact prospective gate and resource admission remain separate requirements. The current 26/53 budget and the budget-only extension54 disposition are unchanged.

## Final focused acceptance and prospective gate review

Saved green03 is terminal: **91 passed in 67.51 seconds**, covering the final 25 hub checks plus 66 existing census/job checks. The interrupt, all-complete graph-context failure, containment and late-quota paths described above are now included in passing saved evidence. Its log SHA is `7b3bef37f91260cb2c94ab2d084539cacb002d40f947987cdcd05c3d3dd55a7c`. Corrected producer/test and unchanged engine/job hashes remain as recorded above. No reviewer tests were run.

**H1–H4 are closed for focused engineering acceptance.** No further blocking source finding was identified. The exact source may be frozen for a named finite broad verification. This acceptance does not imply that a broad suite has run on the increment or that empirical execution is admitted.

Independent metadata checks of gate.draft.json confirm **82 source pins**, including the extension, independent review and allocation metadata, all match current bytes. All runtime pins and **12 compact inputs** among the 13 inputs match. The remaining cardinalities.npy input was not body-read or rehashed by the reviewer; its pin exactly equals the already closed census result's array hash. The four ancestor experiment objects exactly equal their original claim objects. The direct parent is the completed neighborhood census, preserving its full chain through graph successor, failed resource pilot02 and original failed pilot. No original family or ancestor is rewritten.

The plan and closed prior summary agree on **2,764,221 nodes**, **3,504,159 edges** and **35 centers** above the fixed 10,000 threshold. The registered 35 cell IDs exactly equal the plan list, and the three required lifecycle outputs are preserved. Cardinalities are selected completely in original-index order and then checked against source-graph membership. The plan's maximum selector/engine numeric reservation is **4,927,469 bytes**, below its 8 MiB allowance. The graph file-byte bound remains 721,044,472 bytes; cardinality input residency and graph validation remain outside the scratch allowance under the aggregate guard. New producer-plus-lifecycle outputs have the explicitly scoped 1 MiB cap and final accounting.

The prospective job is hub_edge_census with a named plan only and **540-second whole-job wall limit**, 6 GiB max / 5 GiB high / zero swap / 3 GiB runtime reserve / 9 GiB startup / 10 GiB disk floor, using the existing two-CPU guard defaults. These are finite containment limits, not measured completion or peak-memory forecasts. Per-center completion files retain the exact denominator across failure/interruption; no same-identity restart, truncation, scientific capacity change, matching run or financial fit is authorized by this preparation.

Budget extension/review/allocation hashes retain the prior budget-only acceptance: current **26/53**, prospective **54 = 26 consumed + 12 body + 15 fit + one new resource claim**. The new claim directory is absent at review. Observed HEAD is `ee50b11de6aedd0f86efbd45e3a3d3f1602d9efe`; the uncommitted source identities, not that base commit alone, define the reviewed increment.

Exact prospective artifact hashes:

- `gate.draft.json`: `d2b086ca2ff3e414ff566a6a0ac3cdcfc044aff8a5f37e814ce1b00e4fdcc482`
- `CHARTER.md`: `dc9f0bf06d3ef312aa5c727e3d39a8e7b69243db483ad87eae919d1768fca597`
- `hub-plan.json`: `7caa072c1017ba0be436838b4b59687206b9a9ca4a9bd01c23e702bd7ff0b86a`
- `execution-job.json`: `99889b15d9e9be1974c37994900d4e3c47d772e6b9d5268cbe50359d9129ad3e`

Verdict: accept the focused implementation and exact prospective gate/resource design for broad engineering verification. The forthcoming finite launcher and frozen bindings must still be checked. Empirical release remains conditional on terminal broad verification/independent closure, committed exact source/gate/charter/runtime, successful fresh cumulative-budget/ancestry/input admission, exclusive ownership and current host capacity. All 1,420 fits and broader paper requirements remain pending.

## Finite named verification launcher acceptance

The final gate.json is byte-for-byte equal to the reviewed gate.draft.json (SHA `d2b086ca2ff3e414ff566a6a0ac3cdcfc044aff8a5f37e814ce1b00e4fdcc482`). The launcher is byte-for-byte equal to the previously reviewed registered-census launcher (SHA `7679f44c568dd2eb89f299804c864e43709821a5226287de5426e77da51be4ce`); its dynamic HERE selects this increment's distinct offline01 identity and binding manifest.

All **158 bindings** independently rehash correctly at the bound/current HEAD `ee50b11de6aedd0f86efbd45e3a3d3f1602d9efe`. They contain source/tests/compact registration evidence, not empirical arrays; this review did not hash any array body. This REVIEW.md is excluded from the frozen set. Binding-manifest SHA: `d08db359cb3f5515c5c1561cb12eee90e130c58f461c3a0ecbfa22e1faa024ec`.

The launcher checks exact HEAD, every bound file and the 10 GiB policy before running the named offline target. Its profile remains **3 GiB max / 2.75 GiB high / zero swap / 3 GiB runtime reserve / 6 GiB startup / 10 GiB disk reserve / two-CPU guard defaults / 3,600 seconds**. A successful launcher exit requires complete phase, child exit zero and verified cleanup.

**Accept one finite engineering verification under these exact bindings after fresh host/owner checks.** No job or test was started by this review. Empirical census admission remains subject to the separate requirements above and is not granted by this launcher acceptance.

## Failed offline01 closure and corrected offline02 preparation

Independent raw log/final inspection confirms offline01 is **failed**, with **2,767 standard passes, one sampled-guard failure and 97 subtests** in 1,035.23 seconds, plus **766 neural passes and two CUDA skips** in 514.67 seconds. Total: 3,533 passes, 97 subtests, two skips and one failure. Its outer guard reports child 1, cleanup verified, 1,553.721721795 seconds, sampled peak 2,028,310,528 bytes and zero recorded memory events. Monitor 3807099 and the recorded cgroup are absent. The closure evidence hashes match independently. This run supplies no full-suite success or empirical release; its historical helper source, logs and receipts remain preserved.

The failing inner sampled-RSS guard recorded child exit 0 but missing VmRSS telemetry. The specific exit transition was not retained and remains a race-consistent inference rather than proven attribution. The separately reviewed correction was promoted byte-for-byte to scripts/research_resource_guard.py after closure; the dated helper is unchanged. Maintained tests now target that current script, with six deterministic transition checks added; nine focused checks pass. The original guard contracts and finite limits remain, and the onchain cgroup guard is unchanged. See the separately owned guard-exit-race review for exact candidate/evidence identities and scope.

The new run_offline02.py differs from offline01's launcher only in source-bindings02.json and the exclusive offline02 receipt directory. The finite profile remains **3 GiB max / 2.75 GiB high / zero swap / 3 GiB runtime reserve / 6 GiB startup / 10 GiB disk reserve / two-CPU affinity defaults / 3,600 seconds**. All **163 bindings** independently match at HEAD `ee50b11de6aedd0f86efbd45e3a3d3f1602d9efe`. All original 158 bound bytes remain unchanged; five additions pin the successor launcher, historical helper, promoted helper and two maintained guard test files. The modified maintained legacy guard test was not in the original 158-file manifest; its original bytes are separately retained. No source-binding claim is broadened retroactively.

All 82 empirical gate source pins still match, and the exact reviewed gate/charter/plan/resource design remains unchanged. **Accept one corrected finite offline02 execution after fresh capacity and exclusive-owner checks.** Preserve offline01 as failed; do not resume or overwrite it. No empirical claim, capacity override, fit or scientific configuration change is admitted by this successor verification. Empirical release still requires successful terminal broad review, committed source/gate and fresh lifecycle/budget/input/resource admission.

Closure/successor identities:

- `closure-check01.json`: `114609d8e7b07b2525378e1165c0a58dfa66409668ce07b11a72356138d87c6c`
- Failed offline01 final: `5bc986d8c193bc65a8652e2ebea1597cd308b62cf9f0fbf47decddb3c7766464`
- Failed offline01 log: `c3dcd021e88ba5e8b4738ff4db1240cbc74319153235259e971a74e6edd88555`
- `run_offline02.py`: `98e9d92bb0d4b3789da39d846e1808696e4ff85cad06c4f34256074841a767b4`
- `source-bindings02.json`: `28959485113f085290bdd0e08fe040f70d89e83dcd9775998af31de40a3ad8c9`

## Offline02 terminal engineering release

Independent saved raw-log/final inspection confirms the corrected named profile completed: **2,774 standard passes plus 97 passing subtests in 1,035.13 seconds**, then **766 neural passes and two CUDA skips in 554.99 seconds**. Total: **3,540 passes, 97 subtests, two skips**. This is the reviewed named offline profile, not every historical test or an empirical experiment.

The exact guard command is the reviewed scripts/verify_offline.py invocation. Final phase complete, child exit 0, cleanup verified and no limit reason are recorded after **1,594.166966419 seconds**. Sampled peak memory was **2,952,871,936 bytes**. There were **157 memory.high throttle events**, with zero max/OOM/OOM-kill events; this must not be described as zero memory events. Throttling near the configured 2.75 GiB high threshold occurred within the 3 GiB maximum and did not prevent completion. This sampled workload observation is not a cold-cache requirement or an empirical hub-census peak forecast.

All **163 bound files** independently rehash correctly and HEAD remains `ee50b11de6aedd0f86efbd45e3a3d3f1602d9efe`. Closure evidence hashes match. Monitor **79528** and its exact recorded cgroup are independently absent. No tests or processes were started by this review.

**Verdict: accept the registered hub-edge engineering increment and promoted guard correction for commit; the new-source broad verification requirement is closed.** Offline01 remains failed with its original source and evidence intact. The prospective resource-only hub measurement remains conditional on committed exact source/gate/charter/runtime, successful fresh complete-budget/ancestor/input admission, exclusive ownership and current startup/reserve/storage capacity under its separately reviewed 6 GiB/5 GiB/9 GiB-startup/540-second profile. No empirical claim, budget adoption, result, scientific capacity change or financial fit is created by this review. Current budget remains 26/53 until valid adoption; the isolated matching-checkpoint prototype is outside this full-run release.

Terminal identities:

- `closure-check02.json`: `e1de948249e84ba208aab880f2f446817f6e46b229b3cafeb925e6ab840f9aca`
- `offline02/final.json`: `d33c4adafefb46bd1e00f1d78d3fedaa77b051cd5fae047ac978c48a13b96aff`
- `offline02/child.log`: `26416a7214131390a341cd4675d704726af638640bae55121048a0f9b1efe89e`
