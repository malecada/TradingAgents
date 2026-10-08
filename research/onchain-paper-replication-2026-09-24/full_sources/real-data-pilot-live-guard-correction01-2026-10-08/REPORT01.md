# Bounded live guard authentication correction

The low-reserve fallback now reads execution_job through existing real_pilot_import_caller._read(ad, 'execution_job'). This enforces the existing metadata byte bound and registered content hash without invoking ResearchRun.read_input and its full admission/source/runtime validation. An explicitly supplied execution context is unchanged. resources.assert_guarded_worker and job.resource_policy still authenticate current execution/plan hashes, exact resource policy, native controls and live owner. The legacy 3 GiB branch performs no pilot read.

The complete source outside _guard is AST-identical. Both creation-lock guards retain explicit authenticated execution. Binding.check, source/input/runtime validation, lease scheduling, the 60-second deadline and all resource/method constraints are unchanged. No cached lease, preinstalled authority or relaxed refusal was introduced.

RED01.log retains one expected baseline failure: the actual guard fallback invoked the sentinel replacing ResearchRun.read_input. GREEN01.log records 8 passing cases in the explicitly extended reviewed offline profile: fresh bounded fallback; changed bytes, missing registered input, wrong hash, missing file and oversized file refusals; explicit-context success followed by changed-byte refusal; legacy 3 GiB success despite missing execution input. The exact _guard AST executes with actual authenticated synthetic admission and actual resources.assert_guarded_worker/job.resource_policy/_read. Kernel containment/control/file-limit boundaries are synthetic. Numeric imports are denied by audit hook; no numerical module, real data, empirical claim or job executes. The sentinel verifies the unwanted full-validation entry point is absent, not measured production latency or complete activation success.

The checkout-local Python interpreter ran the checks. Full candidate compilation, unchanged outside-guard AST, live baseline identity, and exact forward/inverse patch reconstruction passed. No unexpected failures occurred. Prior 7/17 lock tests and broad numerical suites were not repeated. Pilot17 remains permanently FAILED; Root owns independent review, preservation, integration and any separately admitted successor.

Invocation from checkout root:

    OWNER_SOURCE="$PWD/research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-live-guard-correction01-2026-10-08/matching_owner.py" .venv/bin/python -B research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-live-guard-correction01-2026-10-08/check01.py

For expected RED, set OWNER_SOURCE to baseline_matching_owner.py and add -k fallback_uses.
