# Candidate03 — independent terminal evidence attempts

Only the remaining NR1 publication ordering gap changes. failure-ledger.json and
result.json now each receive their own namespace check and publication attempt.
Failure of either cannot skip the other; the original fatal identity and cause
remain unchanged and publication diagnostics are attached as notes. No later
scientific cell is attempted. job.py is unchanged from candidate02.

red07: 1 failed, 1 passed, 25 deselected, 1.89 seconds. The first-write failure
reproduced missing summary publication. check06: 6 passed, 21 deselected. Both
fault directions retain the other real output, all nine individual dispositions,
the original exception/cause, and the diagnostic. Related cell-publication and
fatal SystemExit/MemoryError/Torch OOM regressions pass. Direct source/test snapshots
are snapshots/red07 and snapshots/check06. Candidate01/02 files remain unchanged.
No empirical execution, admission, broad tests or source-owner scans occurred.

Commands from checkout root with normal reviewed conftest:

```sh
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py -k terminal_evidence_attempts > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/red07.log 2>&1
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py -k 'terminal_evidence_attempts or failed_publication or fatal_propagates' > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/check06.log 2>&1
```

Exit codes: 1, 0. No broad rerun; previous numerical/source/guard coverage remains
as recorded in candidate02, with this narrow delta independently reviewed next.
