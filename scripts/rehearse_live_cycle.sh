#!/usr/bin/env bash
set -euo pipefail

# Run 7 dry-run cycles back-to-back locally to validate the pipeline end-to-end.

export DATA_DIR=$(mktemp -d)
export LOG_DIR=$(mktemp -d)
export LIVE_MODE=false
# Pass through credentials if present, else error early.
: "${BINANCE_API_KEY:?BINANCE_API_KEY must be set}"
: "${BINANCE_API_SECRET:?BINANCE_API_SECRET must be set}"
: "${TELEGRAM_BOT_TOKEN:=}"  # optional
: "${TELEGRAM_CHAT_ID:=}"    # optional

for i in 1 2 3 4 5 6 7; do
    echo "── rehearsal cycle $i ──"
    python -m tradingagents.execution.live.runner --once --dry-run --cycle-id "rehearse-$i"
done

echo
echo "Journal contents:"
sqlite3 "$DATA_DIR/trade_journal.db" "SELECT cycle_id, status FROM cycles;"
sqlite3 "$DATA_DIR/trade_journal.db" "SELECT cycle_id, COUNT(*) FROM trades GROUP BY cycle_id;"
sqlite3 "$DATA_DIR/trade_journal.db" "SELECT cycle_id, AVG(agree) FROM shadow_decisions GROUP BY cycle_id;"

echo
echo "Cleanup: rm -rf $DATA_DIR $LOG_DIR"
