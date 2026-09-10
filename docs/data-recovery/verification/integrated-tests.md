# Integrated verification before execution

The first recovery/exposure source freeze passed 143 tests in 2.36 seconds. The later conditional-replay source, including the optional lifecycle guards and exact snapshot overlays, passed **173 tests in 2.58 seconds** before financial execution. Both commands returned exit status 0. No original market dataset was used by these synthetic test suites.

Final command, executed from the correction checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -m pytest tests/predlab/test_lifecycle_exposure_audit.py tests/predlab/test_lifecycle_replay_guards.py tests/predlab/test_recover_binance_hourly.py tests/predlab/test_recovered_liq_context.py tests/xsect/test_klines_1h_merge.py tests/xsect/test_vision_1m_coverage.py tests/predlab/test_audit_reeval_common.py tests/predlab/test_audit_reevaluate_accounting.py tests/test_accounting_audit.py -q -p no:cacheprovider
```

The tests cover coverage gaps, corrupt/checksum-conflicting source rejection, immutable insertions, original/snapshot/documentary hashes, date filtering, distinct result/ledger namespaces, exact and intrabar termination boundaries, restriction semantics, P2 denominators, primary/cost/convention guards, and placebo rejection without RNG redrawing. Existing accounting and wrapper regressions remain green. Independent review also reproduced the original auxiliary-path startup failure with a synthetic fixture and confirmed the narrow fix; documentary pins do not grant market-read access outside the registered source roots.
