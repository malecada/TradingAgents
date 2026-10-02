# Independent final archive owner policy disposition

Accepted for the read-only prospective registered policy gate. AOP1 in REVIEW_INITIAL.md is resolved by the inspected one-line final freshness postcondition. Earlier findings, source/test snapshots and failed evidence remain preserved. No tests, transfers or empirical jobs were rerun by the reviewer.

After `_record` completes every live owner/guard and registered-input recheck, `select` now requires empty owner.stages and no active stage again before constructing Selection. There is no subsequent external callback before issuance. The new late-boundary regression invokes actual `owner.begin`, confirms that a valid dictionary stage exists and is active, and requires selection refusal. It therefore exercises the original timing gap rather than an invalid synthetic owner. Direct already-started refusal is separate evidence. This sampled selection check does not replace the future mutating adapter's transition lock, durable reservation or operation meter.

Saved baseline check01 reports **14 passed in252.86s**. The retained review-red01 reports **1 failed, 1 passed, 14 deselected in35.13s**: the late creation was accepted by prior source, while direct already-started rejection already worked. Corrected check02 reports **3 passed, 13 deselected in73.92s**, selecting the fresh positive, direct started refusal and late valid-stage refusal. There was no combined sixteen-case run against final source. The implementation delta is only the final postcondition; unrelated baseline evidence is not relabelled as a final full-suite result.

The initial review's authority and arithmetic assessment remains applicable. Selection joins the actual current compact Owner/Binding, current run/source/input/runtime authority and guard checks, matching plan/job selections, bound descriptor hash, exact registered archive-policy bytes and transport identity. The record is frozen, the writer-policy return is a fresh dictionary, and full required dictionary/MCM stage membership determines deterministic distinct remote prefixes and conservative allowances.

Remote payload allowance is stages times maximum events times168 bytes; decoded payload allowance multiplies that by `3+max_stage_verifications`, for upload, readback, writer-final replay and declared cold reads. Writer/read/reference/control metadata allowances are summed over the full required-stage population. These are prospective logical and decoded-member quantities, not measured physical space, RSS, network framing or throughput. The future adapter must meter attempted operations, including failures, before dispatch and enforce cumulative limits across concurrent activity.

The tests use actual synthetic registered ResearchRun/Binding/Owner fixtures with mocked OS guard. No archive writer is installed, no read attempt or remote namespace is created by selection, and no transfer is made. Current archived stage sealing, owner publication/terminal integration, real OS-guard/network execution, scientific source admission and empirical execution remain outside this acceptance. Existing local routes are unchanged.

Inspected SHA-256:

- archive_owner_policy.py: `8408af398925ff31705e6f827e4261c6e293b19e6782534fe20f582e9903f2b6`
- test_archive_owner_policy.py: `90e6ca14ed7070ae3b69f42a5cdc501a6b41585acad0e6a37c069c8a0f930c66`
- policy-check01.py: `7b3c73746d171fb6fafec14409921fcf9d0d46a4c962a2b06520d2141571cf55`
- test-check01.py: `daf265a62467f29a809d9387dcd5223434c2d95140a738b07a55dd312eec73a6`
- review-red01.log: `2df27bf7fda2e0a935e46a55b14f78c0ac80db9619b214482389f46bc383d6ca`
- check01.log: `34a7efd936b227c1bee26293bfd11771189d05c16609a3c10427834ffb8f6e83`
- check02.log: `0cfd7693e7b77e47f2d6eeefdb0cfcadcd9296891688ab7800f2435aa18431d9`
