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
A saved empirical inference example and real raw-to-prediction replay remain
pending. Completed clean-environment synthetic reproduction is recorded below;
its scope does not establish empirical replay or full raw-data backup.


## Latest completed offline checkpoint

`replay/fresh-expanded-02-source.json` freezes the current source and test bytes.
The previously created clean offline locked environment at
`/tmp/onchain-paper-replay-env-20260924-01` was reused with exactly unchanged
installed distributions. Under a2.5 GiB guard and network-denying main-process
audit hook, the expanded synthetic suite passed 387 tests with one CUDA skip and
six inherited pytest temporary-directory cleanup warnings. Guard 443.445 seconds,
peak sampled 934,776,832 bytes, child 0, no memory events and cleanup verified.
`replay/fresh-expanded-02.xml` and its guard retain the full evidence.

`replay/fresh-expanded-02-replay.json` records two saved synthetic model
predictions with maximum absolute difference 0. This is saved-checkpoint replay,
not a real financial fit. Full raw-to-prediction replay remains pending.
The verifier script is `replay/fresh_expanded_02.py`; its output identities are
closed evidence and must not be rerun into the same paths. A future verification
uses a new bounded directory/identity and a new source freeze.
