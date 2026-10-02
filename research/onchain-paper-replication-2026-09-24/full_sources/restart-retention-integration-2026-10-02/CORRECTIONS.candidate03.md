# Narrow review correction closure

Candidate03 manifest SHA256: `88d350c1c9d302e4091a173e15026d901e058121b65ff9564d04ad61f8b709a2`.
All source and tests are frozen pending independent final review. No active process remains.

The only package delta from candidate01 is the `CompactMatcher.__call__` retained
before-pair check and `stage_retention.Controller` original count/counter and
successful-close guards. The final tiny test file adds six cases: direct snapshot
cap with and without refunded public counter; next-pair admission with constrained
and ample original capacity; duplicate finish; direct failure after success. All
assert no unauthorized spending or historical success mutation. The old local
matcher path is unchanged.

`red05` used candidate01 package source plus the first four new review tests;
source/test copies are in `snapshots/red05`. `red06` used candidate02 package
source plus the parametrized ample-cap counter test in `snapshots/red06`.
`check09` used candidate03 package source and the test copy in
`snapshots/check09`; `check10` used final candidate03 tests. These preserve every
attempt; no closed identity was reused. `check08` corresponds to candidate02.

Commands ran from the checkout root using its locked Python runtime, with the
reviewed conftest offline exclusions active:

```sh
env -u PYTEST_ADDOPTS PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 RUN_ONLINE_TESTS=0 .venv/bin/python -B -m pytest -q -p no:cacheprovider --import-mode=importlib tests/research/onchain_replication/test_restart_retention_integration.py -k test_review --junitxml=E/red05.xml > E/red05.log 2>&1
env -u PYTEST_ADDOPTS PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 RUN_ONLINE_TESTS=0 .venv/bin/python -B -m pytest -q -p no:cacheprovider --import-mode=importlib tests/research/onchain_replication/test_restart_retention_integration.py -k refunded_counter --junitxml=E/red06.xml > E/red06.log 2>&1
```

`E` abbreviates this evidence directory (the actual tool commands used the full
relative directory). check08/check09 used both the new tiny integration file and
unchanged `test_compact_matcher.py` without a `-k` filter; check10 used the first
command with its fresh check10 filenames. Logs retain combined stdout/stderr;
XML retains exact selected cases. Third-party plugin auto-loading is disabled in
the reviewed bounded profile; no full legacy suite or actual-owner fixture is
imported by these tiny runs.

The separate owner05 command and immutable full source are documented by
`owner05-manifest.json`, `owner05-source`, raw log/XML and `owner05-replay.json`.
Its3passed543.85s applies to candidate01, while the final narrow correction has
check09:33passed4.90s and check10:6passed18deselected1.60s. The latter overlaps six
review cases; totals are not summed into a purported combined run.

All owner01–05 full snapshots remain locally intact. The owner05 compact backup
uses committed base `869caed7e9df2809165dbfb6f87215835fae4d7f` plus23 exact changed
files; the earlier four bundles retain their own original base. Backup replay is
source reconstruction only, not authorization to repeat scientific work.
