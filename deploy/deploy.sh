#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
    echo "Usage: $0 <hetzner-host-ip> <git-tag>" >&2
    echo "REPO_URL env var must be set if /opt/tradingagents/repo doesn't already exist on the host." >&2
    exit 1
fi

HOST=$1
TAG=$2
SSH="ssh tabot@$HOST"
SSH_ROOT="ssh root@$HOST"

REPO_URL="${REPO_URL:-}"

echo "→ cloning or updating repo"
if [ -n "$REPO_URL" ]; then
    $SSH "[ -d /opt/tradingagents/repo ] || git clone $REPO_URL /opt/tradingagents/repo"
else
    $SSH "[ -d /opt/tradingagents/repo ] || (echo 'ERROR: /opt/tradingagents/repo missing and REPO_URL not set'; exit 1)"
fi
$SSH "cd /opt/tradingagents/repo && git fetch --tags && git checkout $TAG"

echo "→ creating venv + installing"
$SSH "[ -d /opt/tradingagents/venv ] || python3.12 -m venv /opt/tradingagents/venv"
$SSH "/opt/tradingagents/venv/bin/pip install -U pip wheel && /opt/tradingagents/venv/bin/pip install -e /opt/tradingagents/repo"

echo "→ ensuring data + log dirs"
$SSH "mkdir -p /opt/tradingagents/data /opt/tradingagents/logs /opt/tradingagents/secrets && chmod 700 /opt/tradingagents/secrets"

echo "→ checking secrets file exists"
$SSH "[ -f /opt/tradingagents/secrets/.env.trading ] || (echo 'ERROR: scp secrets/.env.trading manually before re-running'; exit 1)"
$SSH "chmod 600 /opt/tradingagents/secrets/.env.trading"

echo "→ installing systemd units (root)"
$SSH_ROOT "cp /opt/tradingagents/repo/deploy/systemd/*.service /etc/systemd/system/"
$SSH_ROOT "cp /opt/tradingagents/repo/deploy/systemd/*.timer /etc/systemd/system/"
$SSH_ROOT "systemctl daemon-reload"
$SSH_ROOT "systemctl enable --now ta-cycle.timer ta-rebacktest.timer"

echo "→ verifying timers"
$SSH_ROOT "systemctl list-timers ta-cycle.timer ta-rebacktest.timer --no-pager"

echo "✓ deploy complete; pinned tag: $TAG"
