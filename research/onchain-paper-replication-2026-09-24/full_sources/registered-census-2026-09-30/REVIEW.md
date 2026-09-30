# Independent registered census integration review

September 30, 2026. Initial source and saved-evidence inspection only; no tests, jobs, graph bodies, raw arrays or remote calls were executed. Production source remains author-owned and unfrozen. Final acceptance is pending the findings below and focused evidence.

## Initial findings

**R1 — output path can escape the guarded root before graph mapping (`census_production.py`, directory creation).** The derived `root/PREFIX/experiment` path is passed to durable_mkdir/mkdir without resolved-root containment or nearest-existing-ancestor device validation. An existing intermediate `sources` symlink can redirect creation to another directory or volume before input mapping. Check resolved containment and same-device ownership before any mkdir/publication, as already done for registered sampling scratch. A regression should assert no outside write and no mapping when an intermediate parent redirects outside the admitted root. Exclusive leaf creation does not solve ancestor traversal.

**R2 — reported/enforced allocation omits late output files (`census_production.py`, `_footprint` and final publication; `job.py`, `execute_source_job`).** The current footprint/check occurs before `result.json` and `cell.json`, and before three lifecycle JSON outputs including the artifact index. Consequently `allocated_output_bytes` is not the complete final producer/registered-output total. The approximate `logical+32*f_frsize` reservation is not itself an exact final-footprint check. Define and enforce the counted scope, account prospective encoded publication/rounding and measure the complete declared result after publication. Bound failure-reason metadata as well, so an unexpectedly long exception cannot exceed a fixed overhead allowance. Lifecycle identifiers are already capped at 128 characters; oversized admitted cell IDs are not a valid counterexample. Preserve existing failure/partial artifacts rather than remove them to satisfy the cap.

**R3 — durable census disposition is invisible to the existing observer (`census_production.py`, final cell publication; `job.py`, reconcile source-cell scan).** The producer writes `cell.json`, whereas reconcile recovers source cells only from `<registered_cell_id>.json`. Interruption after durable census-cell publication but before lifecycle terminal publication would therefore report unavailable instead of the retained exact completed/failed disposition. Publish the registered filename or explicitly extend observer routing, then test post-production/pre-lifecycle interruption and recovery without rerunning the census. Raw evidence is retained, but the reconciled denominator's disposition would otherwise be inaccurate.

## Supported behavior and evidence limits

The plan schema is exact; integer bounds, fixed cell/output denominators, graph/config/member identity pins and registered-window containment are checked before mapping. The node-order pin here is the SHA of the stored node_ids.npy file, not the separate canonical node-order hash API; final registration/docs should retain that distinction. The mapped loader subsequently enforces the complete member denominator, sizes/hashes, file-byte bound, graph validation and canonical content identity. Actual node/edge counts are compared after mapping and before census. Shape failure retains a failed cell and closes the normal map context. The graph window is contained in an admitted dataset window; exact week identity ultimately comes from the pinned graph manifest, not an equality comparison to the window endpoints.

The packaged census engine hash equals the reviewed corrected prototype. Its reciprocal/self-loop logic, full-node denominator and logical-byte accounting findings/qualifications therefore carry forward. Mapping, raw exclusion/transaction verification and empirical runtime are not re-established by the synthetic algorithm oracle. No graph rebuild, dictionary/MCM computation or fit is introduced by the new dispatch route.

Generic admission checks the complete registered execution job before dispatch. The new census job kind requires only a named plan input and a positive integer wall limit no greater than 540 seconds. Resource policy now accepts an explicitly registered floor of at least 10 GiB; existing stored 20 GiB policies remain unchanged. Worker admission receives the exact registered floor and compares the whole live policy to the registration before starting ResearchRun. Required package-source enumeration covers the new modules. Existing worker logic marks a failed finite cell as a failed lifecycle run, while complete cell/output denominators remain retained. Guard termination, failed-result cleanup and observer closure still need saved integrated evidence before release; a schema assertion is not a real 540-second workload demonstration.

The initial tests inspect real lifecycle admission with tiny saved synthetic graphs, literal expected all-node cardinalities, exact artifact hashes, malformed/identity mismatch refusal before mapping, shape-failure closure and guarded-worker disk-floor forwarding. The test named window/denominator currently mutates only the cell denominator, so its window-refusal claim is supported by source inspection rather than that test. No lifecycle gate or census claim exists for empirical execution. Parent is running focused verification; no terminal result is asserted in this initial review.

Initial identities:

- `census_production.py`: `c24c6f807a6a5b5175e832e0efed48d0a15d9ee303aed722081d66de9f1f79dd`
- `neighborhood_census.py`: `be4704d1b19028c2ce734c35483986d6b49d7eecd6f6bd9048c96208b51c02a9`
- `job.py`: `fb550a51fdca6149ccb2f3730160a1ca138c637f6c0d82600064a8baa9673ae8`
- `test_registered_census.py`: `0eed71ad886633bc27ea13b8d81f1b360686bdc0d1152308e31c403522dc36fe`
- `test_neighborhood_census.py`: `56e16518cc10da47af3eb453333fdf6792f337a58a695e5bc1af838860365c83`

The accepted budget-only extension remains a prospective allocation, not source/resource/execution approval. A committed exact gate, complete ancestor lineage, fresh adoption snapshot, final resource review and host/owner checks remain required. None of this work establishes matching feasibility or financial accuracy.

Saved initial green01 is terminal: **69 passed in 72.78 seconds**. This supports its collected paths, not the later R1–R3 corrections or missing observer-recovery counterexample.

## Corrected source and focused acceptance

The current corrections resolve R1–R3 within the declared single-owner execution contract. Resolved containment and nearest-existing-ancestor device checks now precede directory creation. Durable cell publication uses the exact registered ID filename. Final storage accounting occurs after all three lifecycle outputs are published and includes every file and directory block in both declared roots; it emits an explicit file list and scope to the retained child log. A quota failure raises before lifecycle completion and retains the outputs. The earlier summary metric is now explicitly prepublication-only. Exception text is bounded to 2,048 message characters, with the complete message SHA and truncation flag retained. Guard logs and lifecycle claim/terminal files remain outside this artifact quota; it is not a whole-process or whole-filesystem allocation limit.

Saved red02 contains three failures and one pass for containment, complete accounting and bounded error evidence; red03 contains both complete/failed observer counterexamples. Corrected green02 reports 75 passes in 20.85 seconds; the separate late-quota green03 reports one pass in 0.53 seconds. The final expanded green04 reports **135 passes in 62.66 seconds**, including the final registered census and engine tests with existing job, graph-production and resource checks. These overlapping runs are not additive independent test counts. No tests were rerun during this review.

The observer regressions exercise the actual reconcile route with synthetic dead-owner metadata after real tiny-graph producer publication, before successful lifecycle completion, and verify exact recovered dispositions and idempotence. They do not simulate an operating-system kill during every write. The late-quota regression adds unexpected storage after the final lifecycle output, verifies refusal to complete, and preserves all three outputs and a failed terminal. A disjoint-window regression now explicitly verifies refusal before mapping. The initial window-test limitation above is therefore corrected. The engine's independent literal/set oracle and full-node denominator remain intact.

Reviewed final source identities:

- `census_production.py`: `37ec0a081edaf2928146fab3984e362f1241809af43009eb05de307f247665b1`
- `job.py`: `e9ec08f01a415d7778524070a5ee98347170e377fec2547cc9ff71a7dc53c958`
- `test_registered_census.py`: `f65fffb017d7d1af65ebfd526ee425725e6d435667c56c2672af2784ad081164`
- Engine and engine-test hashes remain the initial hashes above.
- `green04.log`: `1d0013c6c87023d1910b5b0010039ee12b8c9521db30159427e0dd95ae988076`

No remaining blocking source finding was identified in this bounded review. Focused engineering acceptance supports freezing these files for named broad verification; it does not establish empirical runtime, memory fit or census outcomes.

## Final prospective gate and finite verification review

The final `gate.json` SHA is `71c917b1c1298d2af108fb392d5010226801b1a5a77d5500b66ae42b0a38e130`. Relative to the retained draft, only the new census experiment's source pins changed. All **77 source pins and 10 compact input pins** independently match current bytes. The three ancestor experiment objects exactly equal their original claim objects, preserving the chain census → completed graph successor → resource pilot 02 → original pilot → no parent. The original family object remains unchanged. The accepted extension/review references remain exact, with current accounting **25 consumed of 52** until adoption; the prospective ceiling 53 adds only one census slot while preserving 12 body and 15 fit allocations and all 1,420 pending fits.

The pinned manifest and plan identify 2,764,221 nodes and 3,504,159 directed edges. The logical reservation arithmetic is `8*3,504,159 + 32*2,764,221 + 131,072 = 116,619,416` bytes before the wrapper's conservative filesystem-block allowance. The 512 MiB artifact limit and 721,044,472-byte mapped-member limit are separate from the outer RAM guard. Neither is an RSS estimate. The stored node-order pin is the node_ids.npy file SHA, as qualified above. No graph body was opened to reconfirm these metadata counts.

The charter's concrete amendment lowers its earlier prospective 3,600-second maximum to **540 seconds for the complete census job**, including mapping/hash validation and publication. The job schema enforces that ceiling; the outer guard supplies finite wall enforcement and termination, with retained phase evidence and no intra-sort or same-identity restart. This is a bounded failure contract, not a guarantee of completion or a hard real-time guarantee under host/filesystem failure. The registered empirical profile remains 6 GiB max / 5 GiB high / zero swap / 3 GiB runtime reserve / 9 GiB startup / 10 GiB disk reserve, with two-CPU guard defaults.

The separate `run_offline.py` uses the named offline target under 3 GiB max / 2.75 GiB high / zero swap / 3 GiB runtime reserve / 6 GiB startup / 10 GiB disk reserve / 3,600 seconds and the same two-CPU defaults. It checks frozen HEAD, every binding and the user-authorized disk policy before starting the guard. Launcher SHA: `7679f44c568dd2eb89f299804c864e43709821a5226287de5426e77da51be4ce`. All **154 bindings** in `source-bindings.json` independently match at HEAD `f762b47d3b10b514fec5e7b8122210751b62a61f`; binding-manifest SHA: `f72285c40f09847dde53684f65585ea264a9927754e0b059cb31a7d9411f4e4b`. This prospective engineering run is acceptable within the reviewed finite profile after fresh host/owner checks.

Empirical release remains pending: terminal broad verification and independent closure, committed exact source/gate/runtime/charter, fresh complete budget-adoption and ancestor admission, current input identity and exclusive-owner checks, and adequate startup RAM/disk under the registered empirical limits. Earlier broad verification covers the previous source and cannot substitute for this increment. No financial return convention, fees/funding, model fit, full matching feasibility or uninspected-data claim was tested here. The existing failed attempts and broader resource requirements remain unchanged.

## Named offline terminal closure and engineering release

Independent saved-evidence review confirms offline01 completed the named `scripts/verify_offline.py` profile: **2,768 standard passes plus 97 passing subtests in 1,057.09 seconds**, followed by **741 neural passes and two CUDA skips in 509.73 seconds**. Total: **3,509 passes plus 97 subtests; two skips**. This is the reviewed 257-module offline profile, not all legacy tests. No tests were rerun during review.

The raw final receipt records phase complete, child exit 0 and cleanup verified after **1,570.629697623 seconds**. Peak sampled cgroup memory was **2,183,454,720 bytes**; high/max/OOM and other recorded memory-event counters remained zero. The configured 3 GiB max, 2.75 GiB high, zero swap, 3 GiB runtime reserve, 6 GiB startup threshold, 10 GiB disk floor and 3,600-second wall limit match the reviewed launcher. Two-CPU affinity and thread readback were used; a CPU quota controller was unavailable. Cleanup records inactive/dead unit state and success. Monitor PID **3280613** and the exact recorded cgroup path are independently absent at review. The sampled peak is an observation of this offline workload, not a cold-cache requirement or forecast for the empirical graph census.

All **154 bound files** independently rehash to the frozen manifest, HEAD remains `f762b47d3b10b514fec5e7b8122210751b62a61f`, and the gate remains SHA `71c917b1c1298d2af108fb392d5010226801b1a5a77d5500b66ae42b0a38e130`. Closure-check evidence hashes also match independently:

- `offline01/final.json`: `e07e9f49ccf7b95db1fe1b2fd7a6d53c8f29f4bb48a420c0c291c47d137e8233`
- `offline01/child.log`: `631d985d17680d5cd3860dc9c0e577ae4467c6306c03422d1c996bcc8d903b2d`
- `closure-check01.json`: `9d591e01833c30bf8b7996389b5b3fd6f856e2404aa0a3d013940b5ae43cbece`

**Verdict: the reviewed registered-census engineering increment is accepted for commit and its broad verification requirement is closed.** The source/resource design is acceptable for the single prospective registered resource-only census, conditional on committed exact source/gate/charter/runtime, fresh complete lifecycle and cumulative-extension admission, exclusive ownership, current input identity, and fresh capacity checks under its separate 6 GiB/5 GiB/9 GiB-startup/540-second profile. This review neither creates a claim nor substitutes for those checks. Budget remains 25/52 until actual prospective adoption; no census outcome, matching feasibility, financial fit or broader task completion is inferred. The isolated bounded-hardening/sparse-objective prototypes are outside this frozen verification and outside this release verdict.
