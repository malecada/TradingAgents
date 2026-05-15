#!/usr/bin/env bash
# Watcher: when tmux session $WAIT_SESSION dies, launch a second hybrid gen
# at the last 30 bars of the 1-year window using a different LLM.
#
# Intended to be itself launched inside its own tmux session, so it survives
# the VPS ssh disconnect.
#
# Usage (on VPS):
#   tmux new -s queue_5mini -d "bash /opt/tradingagents/repo/scripts/queue_model_compare.sh"
#
# Override defaults via env:
#   WAIT_SESSION=hybrid_v5 NEW_MODEL=gpt-5-mini ./queue_model_compare.sh

set -u
set -o pipefail

WAIT_SESSION="${WAIT_SESSION:-hybrid_v5}"
NEW_MODEL="${NEW_MODEL:-gpt-5-mini}"
NEW_SESSION="${NEW_SESSION:-hybrid_v5_5mini}"
START="${START:-2026-03-16}"
END="${END:-2026-04-15}"
OUTPUT_DIR="${OUTPUT_DIR:-data/hybrid_signals_v5_5mini_30bar}"
REPO_DIR="${REPO_DIR:-/opt/tradingagents/repo}"
PYTHON_BIN="${PYTHON_BIN:-/opt/tradingagents/venv/bin/python}"

log() {
    echo "[$(date -Is)] $*"
}

log "Watching tmux session '${WAIT_SESSION}'. Will launch '${NEW_SESSION}' on '${NEW_MODEL}' over ${START}..${END} when it dies."

# Wait until the long-running session is gone
while tmux has-session -t "${WAIT_SESSION}" 2>/dev/null; do
    sleep 300
done

log "Session '${WAIT_SESSION}' is gone. Verifying output exists before launching ${NEW_SESSION}."

# Sanity: 1y output dir must exist with at least 1 csv
ONE_YR_DIR="${REPO_DIR}/data/hybrid_signals_v5_2coin_1y"
if ! ls "${ONE_YR_DIR}"/*.csv >/dev/null 2>&1; then
    log "ERROR: ${ONE_YR_DIR} has no CSVs. 1y gen likely crashed. Aborting queue."
    exit 1
fi

cmd="cd ${REPO_DIR}; set -o allexport; source .env; set +o allexport; ${PYTHON_BIN} scripts/generate_hybrid_signals.py --coins bitcoin ethereum --start ${START} --end ${END} --quant-version v5 --quant-pool-preset v5_2coin --analysts market onchain crypto_sentiment prediction --llm-provider openai --deep-think ${NEW_MODEL} --quick-think ${NEW_MODEL} --output-dir ${OUTPUT_DIR} 2>&1 | tee logs/${NEW_SESSION}.log"

log "Launching tmux session '${NEW_SESSION}'."
tmux new-session -d -s "${NEW_SESSION}" "${cmd}"

sleep 5
if tmux has-session -t "${NEW_SESSION}" 2>/dev/null; then
    log "Session '${NEW_SESSION}' is live. Done."
    exit 0
else
    log "ERROR: '${NEW_SESSION}' failed to start. Check logs/${NEW_SESSION}.log on VPS."
    exit 2
fi
