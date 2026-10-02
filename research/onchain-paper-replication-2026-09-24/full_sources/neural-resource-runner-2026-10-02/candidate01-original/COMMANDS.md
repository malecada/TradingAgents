# Attempt commands, in execution order

```sh
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/red01.log 2>&1
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/red02.log 2>&1
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/check01.log 2>&1
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/red03.log 2>&1
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/check02.log 2>&1
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/red04.log 2>&1
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py tests/research/onchain_replication/test_activation_checkpointing.py > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/check03.log 2>&1
```

Exit codes: 1, 1, 1, 1, 0, 1, 0.
