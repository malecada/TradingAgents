# Explicit startup-reserve amendment — candidate only

The user-authorized new pilot tuple has start_reserve_bytes=2684354560 (2.5GiB), memory_max_bytes=6442450944 (6GiB), memory_high_bytes=5368709120 (5GiB), runtime reserve_bytes=2684354560 (2.5GiB), zero swap and10GiBdisk floor. The previous exact8.5GiBstartup tuple remains supported. No runtime reserve or memory cap was reduced.

## Changed behavior

- resources.guarded_run accepts an explicitly supplied startup threshold when it is at least the runtime host reserve. This is an intentional lower-level API change: an omitted startup threshold still becomes memory_max_bytes+reserve_bytes. This function receives scalar policy from monitor, not an Admission; it does not fabricate authenticated pilot authority. Job and worker validators continue to supply that authority.
- real_pilot_import_caller._amended_host_reserve admits only the exact existing fixed tuple with startup equal to2.5GiB or8.5GiB and schema2 storage. _finite_resources permits the sum-floor exception only for that exact tuple. Other intermediate/below-reserve startup settings refuse.
- job.resource_policy permits the startup-sum exception only for an exact amended tuple with explicit context. Existing checks still require genuine ready Admission, exact authenticated execution_job bytes/hash, exact authenticated schema2 plan/policy, fixed pilot identity and writable storage validation. Legacy job policies retain their original sum-floor contract.
- resources.assert_guarded_worker retains its original cap+reserve startup minimum for legacy callers. Only the existing fully authenticated pilot branch selects the exact admitted startup minimum. Original matching policy/live owner/source/swap/native/FSIZE/lease/containment checks remain unchanged.

Native hard/high/swap/CPU/wall/disk enforcement and the runtime host-reserve kill predicate are unchanged. No field, proxy, scheduler, generic framework, cached authority or altered scientific pipeline was introduced. Root owns final strict19 identity/configuration/source registration and any fresh admission.

## Focused evidence

RED01.log retains the expected baseline result: three new-floor failures and three passing old/default controls. GREEN01.log retains23passes and one engineering fixture failure: the reusable mock assumed one runtime observation before cleanup, so setup-refusal cleanup incorrectly remained active. The expected setup-pressure reason was already correct. test_startup01.before-stop-fixture.py preserves that fixture. The correction models the effect of the simulated stop at the kernel mock boundary; production code did not change for this test failure.

GREEN02.log records24passing focused synthetic cases in0.88seconds using the checkout-local interpreter and an explicit reviewed offline profile extension (one historical fixture copy withheld). Cases cover exact new/prior job and worker policies, unreviewed startup values, execution/plan hash mutations, missing context, legacy job/worker refusal, explicit floor and omitted cap+reserve default, below-runtime pre-receipt refusal, startup-pressure no-dispatch, post-native-setup refusal/no-release/cleanup, and unchanged runtime-reserve kill/cleanup. The simulated native command retains6GiBmax/5GiBhigh/zeroSwap/2CPU; FSIZE and authenticated live checks use the existing synthetic fixture. No genuine native unit, empirical claim, Owner, original input or numerical import is created. Synthetic admission/Git metadata are confined to pytest temporary directories. NumPy/SciPy/Torch/pandas imports are denied.

SOURCE_DELTA01.json/AST_DELTA01.json identify only five changed functions across three full candidate files. All signatures/defaults and every other top-level AST node are unchanged. The runtime kill predicate is AST-identical. Full source compilation and exact forward/inverse byte reconstruction passed. Original source bytes remained unchanged at verification. No broad legacy/numerical suite was run or implied passing.

## Review handoff

Full resources.py, job.py and real_pilot_import_caller.py candidates, raw RED/GREEN logs, failed fixture, exact forward/inverse patches and source manifest are retained. These are engineering/admission-contract checks, not evidence of sufficient RAM, peak job capacity or successful execution. No live source/Main/STATE/Git/configuration changes, empirical registration, credentials/network access or launch occurred. The separately prepared import-placement package remains untouched.

Invocation:

    .venv/bin/python -B research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-startup-reserve-correction01-2026-10-08/check01.py

Expected baseline RED:

    STARTUP_BASELINE=1 .venv/bin/python -B research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-startup-reserve-correction01-2026-10-08/check01.py -k 'exact_new_and_prior or explicit_floor'
