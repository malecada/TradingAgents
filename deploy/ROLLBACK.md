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
set -a; source /opt/tradingagents/secrets/.env.trading; set +a
/opt/tradingagents/venv/bin/python -m tradingagents.execution.live.runner --kill-all
```

## Weekly rebacktest is intentionally not enabled on first deploy

`ta-rebacktest.timer` ships with the systemd units but `deploy.sh` does
not enable it on first boot. The pred-dir input is currently hardcoded
in `rebacktest.compute_backtest_metrics` (`BACKTEST_PRED_DIR`) and the
weekly-comparison semantics need design work before turning it on. To
re-enable manually once that work lands:

```bash
sudo systemctl enable --now ta-rebacktest.timer
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
