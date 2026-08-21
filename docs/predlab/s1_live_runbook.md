# S1 Live Executor — Runbook

## Deployment (VPS tabot@46.225.169.184)

Code path: /opt/tradingagents (same checkout as paper trader), branch
research/prediction-lab. Data: /opt/tradingagents/predlab-data/predlab/s1_live/
(TRADINGAGENTS_DATA_ROOT=/opt/tradingagents/predlab-data as for s1_paper).

API key: Binance key with **futures trading only** (reading + trading;
withdrawals DISABLED), IP-whitelisted to the VPS IP. Stored in
/opt/tradingagents/.env.trading as BINANCE_API_KEY / BINANCE_API_SECRET,
chmod 600, owner tabot. Never in the repo.

Fund with $3,000 USDT (decided 2026-08-21); the account must be dedicated to this executor — any position outside the champion book will be force-flattened.

Cron (chained after the paper trader, same hourly guard pattern):
  <existing paper cron command> && \
  cd /opt/tradingagents && set -a && . ./.env.trading && set +a && \
  TRADINGAGENTS_DATA_ROOT=/opt/tradingagents/predlab-data \
  .venv/bin/python scripts/predlab_s1_live.py run >> \
  /opt/tradingagents/logs/s1_live.log 2>&1

During Phase 1 the cron line uses `run --dry-run`.

## Phase 1b — Testnet rehearsal (before any real money)

After ~1 clean dry-run day, switch the cron line to testnet mode for a few days:
  ... predlab_s1_live.py --testnet run ...
(--testnet goes BEFORE the subcommand.)

Testnet specifics:
- Keys: BINANCE_TESTNET_API_KEY / BINANCE_TESTNET_API_SECRET in .env.trading
  (register at https://testnet.binancefuture.com — separate login from binance.com).
- Data dir: data/predlab/s1_testnet/ (own journal, fills, halt.flag, day_equity).
- Purpose: plumbing validation ONLY — orders accepted, precision, reduceOnly,
  positions match targets, cron idempotency. Testnet books are thin and many
  champion symbols are unlisted there (dropped with no_filter logs): fills and
  slippage numbers from testnet feed NO conclusions.
- Exit criteria: >= 2 consecutive testnet days with a journal row, zero
  unexplained order errors, positions matching targets for listed symbols.
  Then user go/no-go for real funding.

## Daily watch checklist (Phase 1b + Phase 2, first 2 weeks — REQUIRED)

1. `predlab_s1_live.py status` — no WARN lines.
2. Last journal_live row: orders_placed sane (day 1: ~80; after: ~15-40
   from est_turnover ~0.45), gross_target ≈ 2 x scale x equity,
   legs_dropped list small (BTCUSDT at scale <= ~0.98 is expected).
3. fills.jsonl tail: no "error" rows; avg_price within ~1% of mark_px.
4. `predlab_s1_live.py compare` — mean slippage bps drifting? (> ~15 bps
   mean = investigate before continuing).
5. Binance app/web: positions match journal targets (~80 small positions).
6. Equity vs yesterday: moves should match scale x champion book return
   (paper journal realized_mark_ret) within fees+slippage.

## Emergencies

- Stop everything NOW: `predlab_s1_live.py close-all`
  (flattens reduce-only + writes halt.flag; cron becomes a no-op).
- Resume after halt: inspect cause, then `rm .../s1_live/halt.flag`.
- Daily-loss halt fired: do NOT remove the flag same-day; review first.

## Invariants

- Executor never writes into s1_paper/ (registered forward test).
- Null scale -> WAIT is normal until the vol window accrues.
- scale 0.0 (breadth floor) -> executor flattens the book; not an error.
