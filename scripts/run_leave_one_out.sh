#!/usr/bin/env bash
# Per-analyst leave-one-out ablation (assignment §4.5 / TODO-P0-1).
#
# Runs 4 hybrid V5 generations over the 88-bar window 2026-01-16..2026-04-15,
# each dropping exactly one of the 4 analysts. V5 quant routing, gpt-4o-mini
# both LLM slots (production config per THESIS §23.9).
#
# Reference (all 4 analysts) = the last-88-bar slice of the existing 1-year
# run data/hybrid_signals_v5_2coin_1y/ — no extra gen needed.
#
# Runs SEQUENTIALLY in one tmux session (CX22 has 3.7 GB RAM — one gen ≈ 1.7 GB,
# two in parallel risks OOM).
#
# Usage (on VPS, inside its own tmux):
#   tmux new -s loo -d "bash /opt/tradingagents/work_hybrid/scripts/run_leave_one_out.sh"

set -u
set -o pipefail

REPO_DIR="${REPO_DIR:-/opt/tradingagents/work_hybrid}"
PYTHON_BIN="${PYTHON_BIN:-/opt/tradingagents/venv/bin/python}"
START="${START:-2026-01-16}"
END="${END:-2026-04-15}"

cd "${REPO_DIR}" || exit 1
set -o allexport; source .env; set +o allexport
mkdir -p logs

log() { echo "[$(date -Is)] $*"; }

# analyst-to-drop -> remaining analyst list
run_one() {
    local drop="$1"; shift
    local remaining="$*"
    local out="data/loo_drop_${drop}"
    log "=== leave-one-out: drop ${drop} | analysts: ${remaining} ==="
    if grep -qcE '^202[0-9]' "${out}/ethereum_${START}_${END}.csv" 2>/dev/null \
       && [ "$(grep -cE '^202[0-9]' "${out}/ethereum_${START}_${END}.csv" 2>/dev/null)" -ge 88 ]; then
        log "drop ${drop} already complete — skipping"
        return 0
    fi
    "${PYTHON_BIN}" scripts/generate_hybrid_signals.py \
        --coins bitcoin ethereum \
        --start "${START}" --end "${END}" \
        --quant-version v5 --quant-pool-preset v5_2coin \
        --analysts ${remaining} \
        --llm-provider openai --deep-think gpt-4o-mini --quick-think gpt-4o-mini \
        --output-dir "${out}" \
        2>&1 | tee "logs/loo_drop_${drop}.log"
    log "=== drop ${drop} done ==="
}

log "Leave-one-out ablation start. Window ${START}..${END}, V5 routing, gpt-4o-mini."

run_one market      onchain crypto_sentiment prediction
run_one onchain     market crypto_sentiment prediction
run_one sentiment   market onchain prediction
run_one prediction  market onchain crypto_sentiment

log "ALL 4 leave-one-out runs complete."
