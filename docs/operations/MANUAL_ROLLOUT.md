# Manual monitor rollout and rollback

**Prepared for operator execution; no command in this document was executed on the VPS.** The current stage permits read-only inspection and local preparation. Root workspace instructions require production systemd changes to be surfaced for manual execution. The source candidate does not establish funded v2 paper or execution readiness.

## 1. Prepare the reviewed source locally

Use the final reviewed commit with a clean worktree. The package includes source and the committed built frontend, but excludes data, secrets, Git history and research reports. No package installation, deployment helper or trading script is run.

```bash
cd /home/malecada/master_thesis/TradingAgents-audit-fixes
test -z "$(git status --porcelain)" || exit 1
TA_RELEASE_SHA=$(git rev-parse HEAD)
TA_PACKAGE_DIR=$(mktemp -d /tmp/ta-release.XXXXXX)
git archive --format=tar.gz \
  --prefix="ta-source-${TA_RELEASE_SHA}/" \
  --output="$TA_PACKAGE_DIR/ta-source-${TA_RELEASE_SHA}.tar.gz" \
  "$TA_RELEASE_SHA" \
  tradingagents cli pyproject.toml README.md LICENSE uv.lock \
  scripts/predlab_s1_paper.py scripts/predlab_s1_live.py \
  scripts/predlab_journal_backup.sh scripts/predlab_journal_backup.py
(cd "$TA_PACKAGE_DIR" && sha256sum "ta-source-${TA_RELEASE_SHA}.tar.gz" > SHA256SUMS)
tar -tzf "$TA_PACKAGE_DIR/ta-source-${TA_RELEASE_SHA}.tar.gz"
```

Inspect the member list for the new monitor helper, both backup files and built frontend assets. Record the source commit and checksum. Transfer only this archive and its checksum when rollout is authorized. Do not run `deploy/deploy.sh`, rebuild Docker, replace a checkout with the whole research tree or run broad `uv sync`/`pip install`: these paths change more than the monitor and can enable stopped trading timers or install large research frameworks.

## 2. Stage without switching services

On the VPS, verify `SHA256SUMS` in the transfer directory, then set `TA_RELEASE_SHA` to the exact reviewed commit. Create a new `tabot`-owned `/opt/tradingagents/releases/ta-source-$TA_RELEASE_SHA` through archive extraction only if it does not already exist. Preserve `/opt/tradingagents/repo`, `/opt/tradingagents/predlab`, the existing virtual environment and all data directories. Do not overlay or reuse an existing release directory.

```bash
sha256sum -c SHA256SUMS
test ! -e "/opt/tradingagents/releases/ta-source-$TA_RELEASE_SHA" || exit 1
tar --no-same-owner -xzf "ta-source-${TA_RELEASE_SHA}.tar.gz" -C /opt/tradingagents/releases
```

Before restart, check the existing monitor interpreter's installed package metadata and the intended module origin. Do not import the application as a supposedly inert smoke test: its default configuration loads environment files. At minimum the import graph requires FastAPI, Uvicorn, NumPy, pandas, python-binance, requests and python-dotenv; S1 additionally needs its current numerical/parquet dependencies. Installed versions and complete runtime compatibility remain unverified on the VPS. Resolve any gap in an isolated runtime with pinned versions and a separate test before switching; do not upgrade the shared environment in place.

## 3. Switch only the monitor

Refuse an existing `20-audit-source.conf` rather than replacing prior operator configuration. Record the new file as the only rollback target. Use an operator-created drop-in `/etc/systemd/system/ta-monitor.service.d/20-audit-source.conf`. Replace `<REVIEWED_SHA>` below with the recorded commit. Preserve existing authentication, bind address, Caddy configuration and environment-file settings.

```ini
[Service]
WorkingDirectory=/opt/tradingagents/releases/ta-source-<REVIEWED_SHA>
Environment=PYTHONPATH=/opt/tradingagents/releases/ta-source-<REVIEWED_SHA>
Environment=PREDLAB_DATA_DIR=/opt/tradingagents/predlab-data
ExecStart=
ExecStart=/opt/tradingagents/venv/bin/python -m tradingagents.monitor
```

Then, manually:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ta-monitor.service
systemctl is-active ta-monitor.service
```

Use the existing authenticated browser session to inspect `/`, the S1 performance/gate/operations views and `/api/predlab/health`. Expected with the observed VPS data: legacy diagnostics, corrected performance unavailable, suspended validation gate. No positive return, reconciliation or fresh v2 claim should appear. Do not call `/api/performance`, `/api/positions`, `/api/adhoc`, an execution CLI, or arbitrary API routes as a read-only smoke check: some query accounts or launch/write work. Verify that quant/hybrid timers keep their prior inactive state. Do not enable or restart them.

If startup or checks fail, remove only the newly added `20-audit-source.conf` drop-in, run daemon-reload and restart only the monitor. This returns to the preserved old checkout and runtime, whose S1 display is legacy and cannot establish corrected results. Keep all new and old journals intact; a rollback never restores old data snapshots.

## 4. Update the paper-journal backup separately

The shell and Python helper must be installed together. Point the existing backup scheduler at the new release shell only after verifying its actual command, user and schedule. Set `S1_BACKUP_REPO=/opt/tradingagents/predlab`, since the release archive has no `.git`. Keep the backup worktree and remote branch unchanged. The other defaults remain `/opt/tradingagents/predlab-backup-wt` and `/opt/tradingagents/predlab-data/predlab/s1_paper`.

A manually authorized backup run commits and pushes journal bytes to the existing repository's origin. Inspect its dedicated branch and worktree before invocation. Unrelated dirty files, including a leftover modified legacy `cron.log`, intentionally stop synchronization and require preservation and operator resolution; never use an automatic reset/clean. Check the reported synchronization result separately from source freshness. Missing v2 files must report `V2_INCOMPLETE`. Git transport has no explicit timeout; a stalled process can hold the backup lock and needs operator investigation.

This backup does not preserve executor fills, order intents, closure records, day-equity state, halt flags or lock inodes. Their preservation needs a separate operational backup plan before any executor migration.

## 5. Prerequisites for a later paper/executor switch

This candidate does not start S1. Inventory the actual S1 scheduler commands and Python environment first, then pause only those specific schedules before a later authorized switch. Never stop the entire cron service or restart legacy execution over v2 state. Preserve all execution state and resolve any outstanding intent using account evidence before changing the executor.

Prepare verified current funding coverage and price coverage before creating v2 paper rows. Set `TRADINGAGENTS_DATA_ROOT=/opt/tradingagents/predlab-data` explicitly; otherwise a source-relative default can create an empty release-local data namespace. Keep legacy/v2 journals separate and require 20 contiguous complete base net observations before scale eligibility. Adding funding after a broken chain does not reconstruct it; preserve the failure and specify an explicit new measurement boundary.

`--offline` still writes paper journals, `run --dry-run` reads the account and writes local state, and `status` queries the account. None is a passive staging test. No live/testnet order, liquidation, account mode change or leverage update is part of this monitor rollout.
