# Independent adapter release01 review

Disposition: **withheld before execution** for AR1–AR3. The four-test design and inherited native envelope are appropriate, but the exact selected release does not yet bind every executed pytest source/configuration or exclude environment-driven extra work. No tests/numerical imports/jobs/claims were run. Original release/source bytes must remain preserved.

Reviewed release `adapter-release01.json`: `409f20d60a516ae0c2ffe236f477438c9a33fe54a7b5f2ef37573ecbf573d480`; child adapter_tests02 `71d7f2b694fb98fd64cfa2a64971aef971d1e0e0bd95f569de7e0c046ee9441b`; launcher02 `779522dcee42a63be613d17086f166720aa097dbe7dc26135642650756386147`.

## AR1 — exact release qualification describes the wrong workload

The release qualification says one stdlib cleanup proof, no numerical imports and37-byte scratch. Actual adapter_tests02 imports pytest and the new test module imports Torch/NumPy and performs a numerical constructor/checkpoint update. This copied description also names the previous OS identity scope. Correct the new release's qualification to exactly four new numerical adapter tests under native limits, with mocked admission clearly separated from genuine admission. Preserve release01. This does not call for any numerical tolerance or test change.

## AR2 — implicit pytest execution closure is not pinned

The selected source_files omits `conftest.py`, `scripts/verify_offline.py` and `pyproject.toml`. Pytest loads the root conftest; it imports scripts.verify_offline and installs reviewed-profile/network/retained-store isolation. Pyproject supplies addopts including importlib mode. Those files influence imports, admission and test behavior before collection and execution. PYTEST_DISABLE_PLUGIN_AUTOLOAD does not suppress repository conftest/configuration.

Add exact current hashes of all three files to a newly named release and require the same committed source checks as other selected files. Retain the repository protections; do not solve this by skipping conftest. No nested conftest or package __init__ was present in the tests/research/onchain_replication ancestry at review. Selected test_model, test_neural_resource, test_subsets and the new integration test are explicitly pinned; imported helpers are not selected as separate pytest test files. The entire dynamic production package closure still needs final exact verification.

## AR3 — environment can add plugin/pytest work before final cardinality check

Launcher environment only sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1. This suppresses installed entrypoint discovery, but pytest also accepts explicit PYTEST_PLUGINS and PYTEST_ADDOPTS environment settings. Neither is explicitly cleared or rejected before pytest import/main. An inherited setting can alter hooks/options or request extra behavior before the final collected-list check detects it; post-execution rejection cannot establish that only the prescribed work executed.

Freeze PYTEST_PLUGINS and PYTEST_ADDOPTS as empty strings in the native child environment and verify empty values before importing pytest, or fail closed on any nonempty value before numerical/test imports. Keep PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, no-cache provider, exact absolute test path, owned basetemp and final exact setup/call/teardown observations. Source correction gets new filenames/hashes and a new exact review; the unused identity need not be consumed merely by preparation.

## Confirmed design and remaining review scope

Child native_envelope precedes pytest import. Its exact four expected test names and three passed lifecycle phases per name reject skips, omissions, extra collected tests or failed teardown as success. It captures pytest outcomes in a report below64KiB and propagates primary failure. The owned basetemp is below the already owned tmp directory; no closed oracle file is selected. The copied launcher uses the accepted current-caller cleanup distinction, with unchanged native memory/event/file/time/CPU/storage/log/terminal checks and corrected source-root depth. These are source observations, not actual test results.

The selected four tests remain adapter evidence with mocked source/guard admission, not an actual registered producer or whole-workload capacity test. New release qualification must preserve that limitation. The original preparation SyntaxError and unused sources/releases should remain retained. After AR1–AR3, independently verify exact new source pins, runtime metadata, source/config closure, path/namespace absence and unchanged limits before root's commit/external backup and one native launch. Final execution review must distinguish actual cleanup branch, child test status, parent terminal and full owned/outer retention. No source approval, numerical acceptance, empirical claim or budget adoption follows from this withheld release.
