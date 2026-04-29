# Rollback procedure

## Halt only (no data change)

```bash
ssh tabot@<host>
sudo systemctl stop ta-cycle.timer ta-rebacktest.timer
```

Cycles will not run again until timers are re-enabled.

## Halt + close all open positions

```bash
ssh tabot@<host>
sudo systemctl stop ta-cycle.timer ta-rebacktest.timer
cd /opt/tradingagents/repo
EnvironmentFile=/opt/tradingagents/secrets/.env.trading \
  /opt/tradingagents/venv/bin/python -m tradingagents.execution.live.runner --kill-all
```

## Roll back to previous git tag

```bash
ssh tabot@<host>
sudo systemctl stop ta-cycle.timer
cd /opt/tradingagents/repo
git fetch --tags
git checkout <previous-tag>
/opt/tradingagents/venv/bin/pip install -e /opt/tradingagents/repo
sudo systemctl start ta-cycle.timer
```

## Restore data from snapshot

```bash
# On Hetzner Cloud Console: select "Snapshots" → restore latest
# This replaces the entire VM. After restore, re-run /opt/tradingagents/repo/deploy/deploy.sh
```

## Rebuild from scratch

```bash
# Locally:
./deploy/provision_hetzner.sh <new-host-ip>
scp /path/to/.env.trading tabot@<new-host>:/opt/tradingagents/secrets/.env.trading
./deploy/deploy.sh <new-host-ip> <git-tag>
```
