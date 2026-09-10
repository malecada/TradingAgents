#!/usr/bin/env bash
# Offline/synthetic checks; no paper journal, provider, account or service run.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=.
../TradingAgents-predlab/.venv/bin/python -m pytest -q \
  tests/monitor tests/test_accounting_audit.py tests/test_event_accounting.py \
  tests/predlab/test_paper_repair.py tests/predlab/test_execution_repair.py \
  tests/predlab/test_s1_live_cli.py tests/predlab/test_s1_paper.py \
  tests/predlab/test_live_exec.py tests/predlab/test_journal_backup.py \
  tests/predlab/test_lifecycle_exposure_audit.py tests/predlab/test_lifecycle_replay_guards.py \
  tests/predlab/test_recovered_liq_context.py tests/predlab/test_recover_binance_hourly.py \
  tests/predlab/test_funding_capture.py tests/predlab/test_funding_snapshot.py \
  tests/predlab/test_funding_paper_admission.py
../TradingAgents-predlab/.venv/bin/python docs/funding-capture/verification/verify_preservation.py --self-test
# Captured response bodies and test transcripts retain their original bytes.
git diff --check -- . ':(exclude)docs/funding-capture/verification/*.log' ':(exclude)data/operational_funding/**'
