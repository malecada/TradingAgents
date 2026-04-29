#!/usr/bin/env bash
set -euo pipefail

# Disk free check (>10% free on /opt)
disk_pct=$(df --output=pcent /opt | tail -1 | tr -d ' %')
if [ "$disk_pct" -gt 90 ]; then
    echo "preflight: disk usage $disk_pct% > 90% — aborting" >&2
    exit 1
fi

# Network reachability
if ! curl -sSf --max-time 5 https://api.binance.com/api/v3/ping >/dev/null; then
    echo "preflight: cannot reach Binance — aborting" >&2
    exit 1
fi

# Secrets file present + locked
secrets="/opt/tradingagents/secrets/.env.trading"
if [ ! -f "$secrets" ]; then
    echo "preflight: secrets file missing — aborting" >&2
    exit 1
fi
mode=$(stat -c "%a" "$secrets")
if [ "$mode" != "600" ]; then
    echo "preflight: secrets file mode $mode (expected 600) — aborting" >&2
    exit 1
fi
