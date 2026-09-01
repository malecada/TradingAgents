#!/usr/bin/env bash
# Queued A/B: modulator prompt v1 (frozen) vs v2 (realigned), ETH 1-yr.
#
# Waits for the in-flight production hybrid gens to finish (so we do NOT contend
# for OpenAI quota and 429 the prod run), then:
#   1. generates the v2 arm (ETH, same window/preset/analysts as prod, only the
#      modulator prompt differs),
#   2. backtests the existing prod run (v1 arm) and the new v2 arm,
#   3. bootstraps each arm's hybrid-vs-baseline CI,
#   4. writes a verdict + DONE marker.
#
# The v1 arm is the already-running prod dir data/hybrid_signals_v5_eth_prod3_1y
# (default prompt == frozen v1, verified byte-identical). We only pay for v2.
set -u
cd /home/malecada/master_thesis/TradingAgents-research || exit 1

PY=.venv/bin/python3
OUT=data/ab_modprompt
mkdir -p "$OUT"
LOG="$OUT/run.log"
exec >>"$LOG" 2>&1

echo "=== $(date) launcher start; waiting for prod gens to clear ==="

# Wait until no production generate_hybrid_signals.py remains (exclude our own
# v2 arm and the bash monitor loop, which lacks the .py suffix).
while pgrep -af 'generate_hybrid_signals\.py' | grep -v -- '--prompt-version v2' | grep -q . ; do
    echo "$(date +%H:%M) prod gen still running; sleeping 900s"
    sleep 900
done
echo "=== $(date) prod gens clear; starting v2 arm ==="

V1_DIR=data/hybrid_signals_v5_eth_prod3_1y
V2_DIR=data/hybrid_signals_v5_eth_prod3_1y_v2

# 1) v2 arm — mirror the prod ETH command exactly, only add --prompt-version v2.
$PY scripts/generate_hybrid_signals.py \
    --coins ethereum --start 2025-04-18 --end 2026-04-15 \
    --analysts market onchain prediction \
    --quant-version v5 --quant-pool-preset v5_2coin \
    --deep-think gpt-4o-mini --quick-think gpt-4o-mini \
    --prompt-version v2 \
    --output-dir "$V2_DIR"
echo "=== $(date) v2 gen done ==="

# 2) backtest both arms against the identical v5_2coin pure-quant baseline.
$PY scripts/backtest_hybrid.py \
    --signals-dir "$V1_DIR" --coins ethereum \
    --start 2025-04-18 --end 2026-04-15 \
    --v2-sizing --baseline-preset v5_2coin \
    --output-dir "$OUT/bt_v1" || true
$PY scripts/backtest_hybrid.py \
    --signals-dir "$V2_DIR" --coins ethereum \
    --start 2025-04-18 --end 2026-04-15 \
    --v2-sizing --baseline-preset v5_2coin \
    --output-dir "$OUT/bt_v2" || true
echo "=== $(date) backtests done ==="

# 3) bootstrap each arm (hybrid vs baseline CI). Best-effort.
$PY scripts/bootstrap_hybrid.py \
    --backtest-dir "$OUT/bt_v1" --signals-dir "$V1_DIR" \
    --coins ethereum --start 2025-04-18 --end 2026-04-15 \
    > "$OUT/bootstrap_v1.txt" 2>&1 || true
$PY scripts/bootstrap_hybrid.py \
    --backtest-dir "$OUT/bt_v2" --signals-dir "$V2_DIR" \
    --coins ethereum --start 2025-04-18 --end 2026-04-15 \
    > "$OUT/bootstrap_v2.txt" 2>&1 || true
echo "=== $(date) bootstraps done ==="

# 4) verdict: compare ETH hybrid SR across arms (both vs same baseline).
$PY - "$OUT" <<'PYEOF' || true
import json, sys
out = sys.argv[1]
def eth(p):
    try:
        d = json.load(open(f"{out}/{p}/summary.json"))
        return d.get("ethereum", {})
    except Exception as e:
        return {"error": str(e)}
v1, v2 = eth("bt_v1"), eth("bt_v2")
def sr(x, k): return (x.get(k) or {}).get("sharpe_ratio")
verdict = {
    "coin": "ethereum",
    "window": "2025-04-18..2026-04-15",
    "baseline_sr": sr(v1, "baseline"),
    "v1_hybrid_sr": sr(v1, "hybrid"),
    "v2_hybrid_sr": sr(v2, "hybrid"),
}
b = verdict["baseline_sr"]
if verdict["v1_hybrid_sr"] is not None and b is not None:
    verdict["v1_delta_vs_baseline"] = verdict["v1_hybrid_sr"] - b
if verdict["v2_hybrid_sr"] is not None and b is not None:
    verdict["v2_delta_vs_baseline"] = verdict["v2_hybrid_sr"] - b
if verdict.get("v1_hybrid_sr") is not None and verdict.get("v2_hybrid_sr") is not None:
    verdict["v2_minus_v1_sr"] = verdict["v2_hybrid_sr"] - verdict["v1_hybrid_sr"]
json.dump(verdict, open(f"{out}/VERDICT.json", "w"), indent=2)
print(json.dumps(verdict, indent=2))
PYEOF

echo "DONE $(date)" > "$OUT/DONE"
echo "=== $(date) launcher complete ==="
