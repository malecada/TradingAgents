# Reproduction status and commands

Engineering uses the existing locked runtime; no dependency upgrade was needed.
Python3.13.13, torch2.10.0+cu128, numpy/scipy/pyarrow versions are bound by the
repository uv.lock, SHA256
`f7a1829c0ae554fb00923eb07c3c5e5370c1eadb52698ea657446c64d6c83b9a`.
`sources/runtime-inventory.json` records CPU/CUDA discovery. CUDA is unavailable.
There is no separately unlocked neural environment.

From the active checkout:

```bash
.venv/bin/python -B scripts/research_runtime.py --check
.venv/bin/python -B research/onchain-paper-replication-2026-09-24/check_protocol.py
.venv/bin/python -B -m pytest -q --import-mode=importlib tests/research/onchain_replication
.venv/bin/python -B scripts/verify_offline.py
```

These are synthetic/read-only checks and do not launch empirical experiments.
No saved empirical inference example or fresh-environment offline reproduction
has yet been produced; C14 remains pending. Do not infer raw backup from this file.
