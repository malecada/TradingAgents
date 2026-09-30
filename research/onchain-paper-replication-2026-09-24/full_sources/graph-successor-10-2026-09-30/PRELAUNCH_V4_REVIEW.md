# Independent Graph10 gate-v4 prelaunch review

Conditionally accepted for the still-unused Graph10 identity after the exact reviewed bytes are committed/pushed and the fresh sequential checks below pass. No material blocker was identified in this prospective resource amendment. Acceptance is for one full December graph capacity attempt, not proof that the reduced ceiling is sufficient. No generator, test, admission helper, temporary check or job was executed by this review; only this review file was written.

## Exact generated contract

The actual `gate-v4.json` SHA-256 is `76bf4e04c207ab3536ce79bdce0105c139bf7cb15ef40e498f49a4253fad35c6`. Independent JSON comparison with gate-v3 found unchanged top-level datasets, family/budget objects, program and schema; unchanged experiment membership and all eleven inherited experiment objects; and changes to Graph10 only in `charter`, `source_files` and `inputs`. Every inherited source pin remains exact. Only the existing `execution_job` input is replaced. Four source pins and thirteen compact input pins are appended, yielding105 sources and159 inputs. Every current source/input hash and the replacement charter hash independently match. The83-file execution closure reconstructed from the filesystem is fully covered.

The actual old/new execution-job objects differ only in `memory_max_bytes` (6,442,450,944→5,905,580,032) and `start_reserve_bytes` (9,663,676,416→9,126,805,504). Graph kind, environment, graph-plan selection, all other resource fields and the entire nonresource job object remain exact. The retained parent is `eth-paper-resource-pilot-20260924-02`; the December23–30,2024 window, seven source cells and one full graph cell, outputs, runtime hashes, selection and extension references are unchanged. No truncation, scientific substitution, fit admission or budget reset is introduced. The prior reviewed32/59 accounting and unadopted60 proposal are not independently re-ledgered here; their gate objects are unchanged, and this review performs no budget adoption.

`prepare_registration_v4.py` uses exclusive writes, requires absent Graph10 identities, verifies all prior pins, constrains the exact two resource changes, and asserts inherited experiment/source/input preservation. Actual output comparison, rather than the generator's declared derivation, supports the conclusion above. Old gate, charter, execution job, temp02 final receipt, preflight refusal and six prior graph guard receipts remain explicitly pinned.

## Resource evidence and preservation

All six cited graph03–08 final-receipt hashes match. Their recorded sampled peaks, memory events and elapsed times exactly reproduce the amendment evidence; each reports complete phase, zero child exit and verified cleanup. Sampled peaks range4,790,677,504–5,368,791,040bytes (approximately4.46–5.0001GiB), with zero `max`, `oom` and `oom_kill` events; high-throttle events remain disclosed. These are samples from different completed graphs, not a bound on December demand. The5.5GiB ceiling leaves approximately0.5GiB above the largest sampled peak, making the proposed capacity attempt plausible without establishing success.

The unchanged guard source passes zero swap explicitly and selects two CPUs. The new5.5GiB maximum plus the unchanged3GiB host reserve equals the8.5GiB startup requirement. The additional128MiB dispatch margin gives exactly9,261,023,232bytes. The retained disk projection11,365,740,894 plus the10GiB floor gives22,103,159,134bytes. Neither projection nor sampled peak guarantees feasibility. Any admitted resource failure must close and preserve the attempt without reducing the graph or relaunching its identity.

The saved v3 refusal states that exact failing RAM was not emitted and therefore remains unknown; its later RAM snapshot must not be treated as that missing measurement. Temp02's saved receipt confirms complete/exit0/cleanup. At this review, Graph10 claim/run/source paths, temp03, preflight04 receipt and dispatch04 receipt are absent. This establishes their unused state at inspection, not perpetual exclusivity.

## Conditions before the single launch

Commit and verify remote recovery of the exact reviewed gate, helpers and charter. Before temp03, perform the route's fresh HEAD/source, strict RAM/disk and ownership checks. Reject active or activating replication units and pending monitors. Run unused temp03 once, then preflight04, then immediate fresh outer ownership/resource/HEAD/source checks before one dispatch04 launch. Preserve refusals; a reserved or terminal identity cannot be restarted.

`preflight04.py:18–29` retains prior graph, package verification, all preservation, admission, source/input and environment/workspace checks. Lines30–36 reject existing target identities and active **or activating** replication units. Lines37–42 require successful cleaned temp03, absent monitor/cgroup, guarded-volume agreement and age at most300seconds. Lines43–46 enforce the registered disk projection and new RAM threshold, printing the sampled RAM before assertion. Lines47–51 inspect retained mappings and raw-file stats only. Its source/ownership checks are snapshots; pending-monitor exclusion remains an explicit outer-check obligation, and the route is not a global lock. Keep sole dispatch ownership and freeze HEAD/all pins through terminal reconciliation. If freshness or resources fail, do not skip a check or reuse the closed temp identity.

Not tested: current resource availability or live absence of competing processes, future temp03/kernel dispatch, December graph memory/disk sufficiency, saved-array correctness, final graph completion, matching consumers, dictionary/MCM integration or financial performance. No empirical body or numerical array was read. Source/input hashing covered only the registered source and compact evidence files. Separate terminal review remains required after any admitted graph run.

## Reviewed amendment hashes

| File | SHA-256 |
|---|---|
| `CHARTER_V4.md` | `d0ba25633fb18f57c4119b4cc4101a6896148935077201e7c8c73701108feb61` |
| `PRELAUNCH_ROUTE_V4.md` | `1bdd881cab499b9fc5e84feb2ac7ce8c1ab1070467f6c34121d0ef217c71ad08` |
| `memory-amendment-v4-evidence.json` | `50d4690c05754965ff2880e0c844f0f92f9daef5d0d759b458e0e73dbc91b2f3` |
| `execution-job-v4.json` | `281d448ed99fc5fe43aeea2b11f33300c2a1e0508eb605db20bd5e03bf8d0aff` |
| `prepare_registration_v4.py` | `9fefee9a9388544ca7e5df6b1b835016cad2c75a2e5e7f9bd3b998ea94ae1abf` |
| `preflight04.py` | `9f7917844bbd1ee6489f9df0874b641c3760cb5e8d83f4fdcf7951a1341cefc3` |
| `run_temp_check03.py` | `f0c4bb4e15a62dcb499c436aaa6427b06a6fc68dc7d6bb2f3bb1c50343169658` |
| `gate-v4-derivation.json` | `1942dd049a43a8b4db4e9b7f88416ac96cd9cd918989557ea51a26b62782d657` |
