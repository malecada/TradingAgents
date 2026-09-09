# Registered execution record

Source49fb9e47c4d9e40b9c3f1b7de475041ec63aac76 was clean and committed before any result. GateSHA256 b74efa4273a38339cab652cb140b0aa64df1778a1f7f8bcb015e49c3f357e894; correction-policySHA256 fba631d9bb458decc4b278c1b224a2441d97b75d7a328dffa0850c9799619a4d. Independent reviews and171 passing integrated tests preceded the source commit.

Commands run from TradingAgents-audit-fixes, with PYTHONDONTWRITEBYTECODE=1, OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1, MKL_NUM_THREADS=1, PYTHONPATH=., and TRADINGAGENTS_DATA_ROOT=$PWD/data:

```bash
../TradingAgents-predlab/.venv/bin/python scripts/audit_reevaluate_accounting_2026_09_09.py --family momentum --execute
../TradingAgents-predlab/.venv/bin/python scripts/audit_reevaluate_prx_2026_09_09.py --execute
```

stdout/stderr are preserved separately under verification/*-run.log. Process completion and all result checksums will be recorded below. No source/gate/policy edits or commits are allowed until every family has completed.

Additional frozen commands started after the initial daily/pair runs:

```bash
../TradingAgents-predlab/.venv/bin/python scripts/audit_reevaluate_accounting_2026_09_09.py --family carry --execute
../TradingAgents-predlab/.venv/bin/python scripts/audit_reevaluate_accounting_2026_09_09.py --family liq_fade --execute
```

Momentum, carry and PRX processes exited0 with immutable results. Momentum12 and carry6 are unavailable because of missing held marks; process success is not a research PASS. PRX retains all50months: its original conditional comparison fails, while complete-panel inference is unavailable for47/50complete months. Liquidation-fade is still running.

Liquidation-fade exited0: three measured original-gate failures, three missing-mark cells. Its P0/P1/P2 probes passed; no placebo performance was computed after primary gate failures, with original RNG draws still advanced as registered. The DEX family then started using the same frozen source:

```bash
../TradingAgents-predlab/.venv/bin/python scripts/audit_reevaluate_nlst4_2026_09_09.py --execute
```

NLST4 exited0, completing the full26-cell slate. It retained3981cohortrows and2776new-set rows, with2718scoreable. T1passes andT2fails, explicitly as a retrospective diagnostic. The process ran16:22:04.758–16:53:53.051UTC; no source,gate,policy,orHEAD changed during any family run. Finalmanifest:verification/manifest.json. All five start/result artifacts and saved vectors are preserved; no invocation was restarted.
