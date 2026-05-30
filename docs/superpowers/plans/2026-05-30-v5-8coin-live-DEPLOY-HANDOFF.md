# V5 MIX 8-coin — Operator Deploy Handoff

**Tag:** `live-v2.2.0`  ·  **Branch merged:** `feature/v5-8coin-live` → `main`
**VPS:** `pck-preds-1` (`46.225.169.184`), Binance Futures **testnet** (`LIVE_MODE=false`)
**Prereq:** these steps mutate prod systemd + `.env.trading`, which the agent is blocked from doing — run them by hand.

> ⚠️ Do NOT skip the `.env.trading` edits: the preflight hard-gates on `CONFIDENCE_REF_RETURN=0.05` and `SYMMETRIC=false` and will refuse to start otherwise (intended).

## What changed since `live-v2.1.5`

- **8-coin universe** (was 4): BTC/ETH/BNB/SOL core + XRP/DOGE/ADA/TRX satellite. Core 15% ×4, satellite 10% ×4, renormalized over the active universe (C1 weights).
- **Stateful 7-day min-hold** (P1): new `hold_state` journal table; live now reproduces `build_positions_with_hold` (golden-tested) instead of re-sizing statelessly every cycle.
- **Remaining P0/P1 hardening** not in the v2.1.5 line: S3265 (portfolio_before floor + raise on missing `totalMarginBalance`), J1 (journal WAL + busy_timeout), PF1 (preflight demotes supplementary-source failures to warnings; now validates routing instead of a fixed coin count), AL1 (alert 4xx visibility + per-cycle dead-man heartbeat).
- Inherited from the v2.1.5→`fix/c1-portfolio-weight` stack: C1, L1+R4, R2/R3, R1/R5, P2/P3, P4, P5.

## Deploy steps (run as root on the VPS)

```bash
# 1. Quiesce
systemctl stop ta-cycle.timer ta-rebacktest.timer ta-monitor.service

# 2. Pull the tag
cd /opt/tradingagents/repo
git fetch --tags origin
git checkout live-v2.2.0

# 3. Journal: hold_state is created automatically by schema.sql on next start
#    (CREATE TABLE IF NOT EXISTS). Run the V5 additive migration for older cols:
/opt/tradingagents/venv/bin/python -m tradingagents.execution.live.journal \
    --migrate --db /opt/tradingagents/data/trade_journal.db

# 4. Edit /opt/tradingagents/secrets/.env.trading — set/confirm:
#      COIN_UNIVERSE=bitcoin,ethereum,binancecoin,solana,ripple,dogecoin,cardano,tron
#      MAX_OPEN_POSITIONS=8
#      CONFIDENCE_REF_RETURN=0.05      # preflight blocks deploy if not 0.05
#      SYMMETRIC=false                 # preflight blocks deploy if not false
#      MIN_CAPITAL_FLOOR=100           # S3265 floor (default 100 if unset)
#    (KELLY_FRACTION stays 0.25.)

# 5. Preflight (must print "V5 preflight: ALL OK"; Coinglass auth is now a
#    non-fatal WARN if it fails)
cd /opt/tradingagents/repo && PYTHON=/opt/tradingagents/venv/bin/python bash deploy/preflight.sh

# 6. One manual dry-run cycle sanity (optional but recommended)
DRY_RUN=true /opt/tradingagents/venv/bin/python -m tradingagents.execution.live.runner --once

# 7. Restart services
systemctl start ta-monitor.service ta-cycle.timer ta-rebacktest.timer
```

## Post-deploy verification (first real cycle, ~00:05 UTC)

```bash
DB=/opt/tradingagents/data/trade_journal.db
# 8 coins predicted this cycle:
sqlite3 "$DB" "SELECT coin, COUNT(*) FROM predictions WHERE cycle_id=(SELECT MAX(cycle_id) FROM cycles) GROUP BY coin;"
# hold_state populated for held coins:
sqlite3 "$DB" "SELECT coin, current_dir, bars_held FROM hold_state;"
# WAL active:
sqlite3 "$DB" "PRAGMA journal_mode;"   # -> wal
# heartbeat fresh:
cat /opt/tradingagents/data/last_cycle_heartbeat.txt
```

Also confirm in the monitor / logs: portfolio weights sum to 1.0 over the 8 coins, and aggregate gross leverage stays ≤ 3× (C1). Confirm the exchange account is in **one-way** position mode (delta sizing assumes it).

## Follow-ups (not blocking, recommended soon)

- **Dead-man timer (completes AL1):** add a systemd `OnCalendar` timer that alerts if `last_cycle_heartbeat.txt` is older than ~26h (catches a *missing* cycle, which in-process alerting cannot). The heartbeat file is already written every cycle by `runner._write_heartbeat`.
- **Richer alert channel:** Telegram is still the only channel; consider an email/SMS fallback.
- **Trend-on-hold parity gap (documented):** on no-signal/vol-capped hold bars the live sizer holds the frozen pre-trend base without re-applying that bar's SMA multiplier (bounded by the 0.5–1.5× band). Quantify via the weekly S1 parity job; close if material.

## Acceptance gate (90-day window restarts at deploy)

- Hard floor: **portfolio SR ≥ +2.86**, return ≥ +6.5%, MaxDD ≤ −4%.
- Report against the 8-coin backtest at the live Kelly=0.25: **SR ≈ +3.91, MaxDD ≈ −2.4%, vol ≈ 5%** over the 4.5-yr WF (the published +1053%/−4.8% headline is at Kelly=0.5; SR is leverage-invariant, return/vol/DD scale with Kelly).

## Rollback

```bash
systemctl stop ta-cycle.timer ta-rebacktest.timer ta-monitor.service
cd /opt/tradingagents/repo && git checkout live-v2.1.5
# revert .env.trading: COIN_UNIVERSE back to 4 coins, MAX_OPEN_POSITIONS=4
systemctl start ta-monitor.service ta-cycle.timer ta-rebacktest.timer
```
(The `hold_state` table is additive and harmless under v2.1.5, which ignores it.)
