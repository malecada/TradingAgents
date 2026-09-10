# Safe research verification

The default verification profile is a reviewed subset of engineering and independent checker tests. It is **not the complete legacy suite**, a strategy replay or evidence of positive alpha. Its inventory is maintained in `scripts/verify_offline.py`.

From the active checkout:

```bash
uv sync --locked --all-extras --python 3.13.13
.venv/bin/python -B scripts/research_runtime.py --check
.venv/bin/python -B scripts/verify_offline.py
```

Add `--collect-only` to the final command to inspect the admitted cases without executing test bodies. Do not use a sibling worktree interpreter for final verification. Environment installation can download the locked packages; the subsequent test profile does not fetch market data or use account credentials.

The profile covers synthetic accounting and settlement examples, missing/causal data, lifecycle and funding admission, statistical/gate checks, recent factor/carry arithmetic, new preparation contracts and the independent checker tests stored under `docs/`. Fixtures use invented observations and temporary files. Historical tests are retained in place; omitted tests are unreviewed for this profile, not declared irrelevant or passing.

## Collection and isolation

- Pytest uses `importlib` collection so independent checker modules with matching filenames can coexist. Plain repository pytest also uses the reviewed admission policy, although `pytest tests/` naturally omits explicitly separate `docs/` test paths; the named command includes them.
- Unknown test modules are withheld before import. An explicit unadmitted file request fails with a usage error. The summary reports encountered withheld files; directory pruning means this number is not the count of all legacy tests.
- The named command disables third-party plugin autoload, clears inherited `PYTEST_ADDOPTS`, disables persistent pytest cache and bytecode writes, and does not inherit an online-test opt-in.
- A Python audit hook denies Internet/DNS access during collection and execution unless explicitly enabled, and rejects Python writes into the checkout's `data/` or sibling `TradingAgents*/data/` stores. Temporary fixtures are allowed, including directory-descriptor based cleanup.
- These checks are defense in depth for reviewed code, **not an operating-system sandbox**. Native code or arbitrary external subprocesses are not generally contained by Python audit hooks. A test that launches a subprocess must be reviewed separately and use declared temporary inputs/outputs. Do not treat the guard as permission to run unknown code.

## Adding or explicitly invoking tests

Review module imports, fixture input origins, network/credential access and subprocess/output paths before adding a module to `OFFLINE_FILES`. Synthetic preparation contracts reside in the explicitly admitted `tests/research/` directory and require the same review. Missing listed test files fail the named command rather than silently shrinking coverage.

Real observation replay requires an `empirical` classification; external API and authenticated behavior require `network` and `account` classifications. The reviewed external-file map and matching `--run-empirical`, `--run-network`, `--run-account` options enforce explicit collection admission. A marker also gates a test body. Flags never replace user authorization, a committed registration or an unspent confirmation sample. There is no blanket option to admit every unreviewed test.

The preserved V2 regression is explicitly empirical. If separately authorized, its helper copies only the two prediction CSVs into a pytest temporary directory; report and plot outputs go there. The old golden numbers remain historical assertions, not validation of the corrected strategy. This preparation did not invoke that replay, restore its missing market inputs or regenerate its golden file.

## CI scope

`.github/workflows/research-offline.yml` installs the same Python and unchanged lock, checks runtime provenance and runs the named profile on Linux. It uses read-only repository permissions, no account secrets and no persistent checkout credentials. It does not download market datasets or run a paper/live system. Dependencies remain broad; splitting heavyweight optional groups is separate work.

Action revisions were checked against the official [checkout repository](https://github.com/actions/checkout) and [setup-uv repository](https://github.com/astral-sh/setup-uv), then pinned. A local passing profile does not claim hosted CI passed; that requires an actual hosted result after publication.
