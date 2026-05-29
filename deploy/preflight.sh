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

# === V5 preflight additions ===
set -e

echo "=== V5 preflight ==="

# 1. COINGLASS_API_KEY present
if [ -z "${COINGLASS_API_KEY:-}" ]; then
    echo "FAIL: COINGLASS_API_KEY not set"
    exit 1
fi
echo "  COINGLASS_API_KEY: set"

# 2. Coin universe = 4 coins
N_COINS=$(echo "${COIN_UNIVERSE:-bitcoin,ethereum,binancecoin,solana}" | tr ',' '\n' | wc -l)
if [ "$N_COINS" -ne 4 ]; then
    echo "FAIL: COIN_UNIVERSE must have 4 coins, got $N_COINS"
    exit 1
fi
echo "  COIN_UNIVERSE: 4 coins"

# 3. Kelly is set + reasonable (0.10 to 0.29 band)
KELLY="${KELLY_FRACTION:-0.25}"
case "$KELLY" in
    0.[12][0-9]|0.[12]) ;;
    *) echo "FAIL: KELLY_FRACTION=$KELLY out of [0.10, 0.29] band"; exit 1 ;;
esac
echo "  KELLY_FRACTION: $KELLY"

# 3b. Signal config must match the canonical backtest (P2/P3 parity). The
# published SR +3.18 run used confidence_ref=0.05 + asymmetric (SYMMETRIC=false);
# any other value silently trades a different signal/size than was validated.
CONF_REF="${CONFIDENCE_REF_RETURN:-0.05}"
if [ "$CONF_REF" != "0.05" ]; then
    echo "FAIL: CONFIDENCE_REF_RETURN=$CONF_REF != canonical 0.05 (backtest parity)"
    exit 1
fi
echo "  CONFIDENCE_REF_RETURN: $CONF_REF"
SYM_LC=$(echo "${SYMMETRIC:-false}" | tr '[:upper:]' '[:lower:]')
case "$SYM_LC" in
    false|0|no) ;;
    *) echo "FAIL: SYMMETRIC=$SYM_LC must be false (canonical V5 MIX is asymmetric)"; exit 1 ;;
esac
echo "  SYMMETRIC: $SYM_LC"

# 4. Derivatives + options dirs writable
DATA_ROOT="${TRADINGAGENTS_DATA_ROOT:-/opt/tradingagents/data}"
for sub in derivatives derivatives_raw options onchain cache; do
    DIR="$DATA_ROOT/$sub"
    if [ ! -d "$DIR" ]; then
        mkdir -p "$DIR" || { echo "FAIL: cannot create $DIR"; exit 1; }
    fi
    if [ ! -w "$DIR" ]; then
        echo "FAIL: $DIR not writable"
        exit 1
    fi
done
echo "  data subdirs: writable"

# 5. Can import V5 live modules
# Use $PYTHON if set (deploy passes /opt/tradingagents/venv/bin/python via systemd
# Environment=), else fall back to bare `python`. Service user has no venv on PATH
# unless explicitly added.
PYTHON_BIN="${PYTHON:-/opt/tradingagents/venv/bin/python}"
[ -x "$PYTHON_BIN" ] || PYTHON_BIN="python"
"$PYTHON_BIN" -c "
from tradingagents.execution.live.config import LiveConfig
from tradingagents.execution.live.data_refresh import refresh_all, CriticalDataRefreshError
from tradingagents.execution.live.retrain import run_retrain_with_fallback
from tradingagents.execution.live.predict import run_predict, PredictMajorityFail
print('  V5 imports: OK')
" || { echo "FAIL: V5 import error"; exit 1; }

# 6. Sample Coinglass auth
curl -s --max-time 8 -H "CG-API-KEY: $COINGLASS_API_KEY" \
    "https://open-api-v4.coinglass.com/api/futures/supported-coins" \
    | grep -q '"code":"0"' || { echo "FAIL: Coinglass auth"; exit 1; }
echo "  Coinglass auth: OK"

echo "V5 preflight: ALL OK"
