# Correction attempt commands

All commands from checkout root, using local locked Python and normal conftest.

```sh
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/red05.log 2>&1
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/check04.log 2>&1
PYTHONPATH=. .venv/bin/python -B -m pytest -q tests/research/onchain_replication/test_neural_resource.py -k 'finalization_refuses_replaced_owned_directory' > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/red06.log 2>&1
PYTHONPATH=. .venv/bin/python -B -m pytest -q --capture=tee-sys tests/research/onchain_replication/test_neural_resource.py tests/research/onchain_replication/test_activation_checkpointing.py > research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-runner-2026-10-02/check05.log 2>&1
```

Exit codes in order: 1, 0, 1, 0. No empirical jobs or network requests.
