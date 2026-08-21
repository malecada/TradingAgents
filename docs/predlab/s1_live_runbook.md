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

Leverage is set to **4x** per symbol (raised from 2x in the final pre-deploy
review, 2026-08-21) with a hard clamp on the *executed* overlay scale at
**1.1** (`vt15_b100_scale` can reach ~2.0, and champion gross weight is
2.0x, so unclamped gross target notional could reach 4x equity — at 2x
leverage that would exceed the 2.2x gross cap and refuse every batch). The
live run always sizes off `min(vt15_b100_scale, 1.1)`; the unclamped value
is recorded as `scale_raw` in `journal_live.jsonl` alongside the executed
`scale`, so a capped-replica day is legible in the journal, not silently
mislabeled as full-scale.

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
- Positions in halted/delisted symbols can't be market-ordered — close
  manually in the Binance UI (executor logs them as `no_filter`).

## Invariants

- Executor never writes into s1_paper/ (registered forward test).
- Null scale -> WAIT is normal until the vol window accrues.
- Null/empty marks with a non-empty book -> WAIT, no journal row written
  (retried on the next wake; not a flat day).
- scale 0.0 (breadth floor) -> executor flattens the book; not an error.
- Executed sizing scale is `min(vt15_b100_scale, 1.1)`; the raw overlay
  scale is preserved as `scale_raw` in the journal.
- A symbol that leaves the champion book while still held is always closed
  reduce-only, even with no mark for it that day (never a silent zombie
  position).
- Daily-loss check reads equity and can halt on every wake, including an
  hourly wake whose asof was already executed earlier that day.
- Hedge (dual-side) position mode is rejected before any live order.
