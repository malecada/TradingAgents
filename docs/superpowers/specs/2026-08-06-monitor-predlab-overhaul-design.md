# Monitor UI Overhaul — Predlab-First Dashboard

Date: 2026-08-06
Status: approved design, pre-implementation

## Context

The monitor service (`tradingagents/monitor/`, FastAPI + React SPA at 127.0.0.1:8800 behind Caddy) was built for the V5 8-coin quant/hybrid books. Those books were decommissioned on 2026-08-06 (ta-cycle + ta-rebacktest disabled; SQLite journals frozen and preserved). The active strategy is now the Prediction Lab champion: ewma_20 low-vol cross-sectional long-short, monthly PIT top-200, vt15_b100 overlay, tracked by a paper trader (`predlab_s1_paper.py`) writing dual JSONL journals on the VPS (`/opt/tradingagents/predlab-data/predlab/s1_paper/`): `journal.jsonl` (frozen old book: park_5 + vt10, pp2 forward confirmation) and `journal_champion.jsonl` (ewma_20 + vt15_b100).

The monitor and predlab are currently disjoint: nothing in the monitor reads predlab data. The journals are weights-and-returns records (no equity/positions fields) — equity must be compounded from `realized_book_ret`.

## Decisions made

- **Approach A**: extend the existing monitor service. Single systemd unit, same auth, same Caddy route, env-only deploy change.
- Old V5 quant/hybrid tabs collapse into a single read-only **Legacy** archive section.
- **Run Prediction tab dropped** (targets retired lgb_v5_mix checkpoints). Frontend code deleted; the adhoc backend module stays untouched (smaller diff, zero risk to stored runs).
- Predlab views: Performance, Book, Gate tracker, Ops health.

## Backend

New module `tradingagents/monitor/predlab.py` (pure functions + source class, mirroring the `sources.py`/`metrics.py` split):

- `PredlabSource(data_dir)` from env `PREDLAB_DATA_DIR`. Reads per request with the existing 30 s `ttl_cached` pattern:
  - `predlab/s1_paper/journal.jsonl` (book key: `vt10`)
  - `predlab/s1_paper/journal_champion.jsonl` (book key: `champion`)
  - optional reference files, null when absent: `predlab/champion_backtest.json`, `predlab/gates.json` (only the `predlab_opt.final_champion` block is consumed)
- Derived per book: equity = cumprod(1 + `realized_book_ret`) rebased to 100 (null returns skipped); rolling Sharpe (√365 annualization, reuse `metrics.py`); max drawdown; cumulative `est_cost`; vt-scale series; warm-up counter n/21 (scale keys stay null until 21 realized returns).

### Endpoints (read-only, existing basic auth)

| Endpoint | Payload |
|---|---|
| `GET /api/predlab/performance` | Both books: equity series, Sharpe (full + rolling 30d), MaxDD, turnover/cost stats, current scale, warm-up state; backtest reference metrics (ovl SR 1.892, MaxDD 0.176) for chart overlay |
| `GET /api/predlab/book?book=champion\|vt10` | Latest row: `asof`, breadth, `n_universe`, `membership_hash`, weights split long/short (sorted), scale, `est_turnover`, `est_cost`; previous-day delta (entered/exited symbol counts) |
| `GET /api/predlab/gate` | Sealed one-shot tracker: window start 2026-07-02, earliest evaluation 2027-01-02, days elapsed/remaining, running forward SR vs threshold 0.946, pass conditions; explicit flag that the display is informational only — the evaluation itself is one-shot and stays sealed |
| `GET /api/predlab/health` | Per journal: last `asof`, `written_utc`, staleness flag (> 36 h = STALE), known-gap list (champion 2026-07-31 → 2026-08-02 gap annotated as intentional), row counts, malformed-line count |

Degradation contract (same as existing quant/hybrid isolation): missing file → null block, endpoint still returns 200.

## Frontend

Tab bar: **Performance | Book | Gate | Ops | ▸ Legacy**. Stack unchanged (React 19, TanStack Query v5, lightweight-charts v5, Recharts, hash routing, Card/Badge/Section components).

1. **Performance** — card rows per book (champion primary, vt10 secondary): cumulative return, Sharpe since start, MaxDD, current vt scale (or "warming up n/21"), cost drag. Multi-pane chart: dual-line equity rebased to 100, drawdown pane, rolling Sharpe pane, dashed backtest-anchor reference line, 7d/30d/90d/all range pills. While the forward series has < 2 points, the pane shows the dev backtest equity from `champion_backtest.json`, clearly labeled "backtest (dev)".
2. **Book** — book switch pill, champion default. Header cards: `asof`, universe size, breadth, membership hash, scale, est turnover/cost. Two tables: 40 longs / 40 shorts (symbol, weight). Entered/exited badge vs previous day.
3. **Gate** — progress bar 2026-07-02 → 2027-01-02 with days remaining; running forward SR as headline number vs 0.946 threshold; pass-condition list (SR_F ≥ 0.946, same sign, placebo p < 0.10, single evaluation); prominent "informational — evaluation is one-shot at earliest 2027-01-02" note; forward equity mini-chart.
4. **Ops** — freshness badge per journal (OK/STALE), last `written_utc`, row counts, gap list, malformed-line count, pointer to the `predlab-journal-backup` branch heartbeat.
5. **▸ Legacy** — visually separated. Sub-tabs reuse the existing Performance/Positions/Executions/Decisions/Health components unchanged against the frozen quant/hybrid journals. Banner: "V5 books decommissioned 2026-08-06 — read-only archive."

New DTOs in `types.ts`; colocated vitest tests for new lib functions (equity compounding, staleness) per existing pattern.

## Deploy

- Changes land in the main TradingAgents repo (VPS deploys `/opt/tradingagents/repo` from main). Feature branch off main, merged after tests pass.
- Reference files (`champion_backtest.json`, `gates.json`) copied once to `/opt/tradingagents/predlab-data/predlab/` on the VPS; journals already arrive via cron.
- `deploy/systemd/ta-monitor.service` gains `Environment=PREDLAB_DATA_DIR=/opt/tradingagents/predlab-data`. Production systemd edits are performed manually on the VPS (unit edit, `daemon-reload`, restart) — commands surfaced, not executed by tooling.
- Local dev: `PREDLAB_DATA_DIR` pointed at the predlab worktree's `data/` directory.
- `frontend/dist/` rebuilt (`npm run build`) and committed — the VPS has no Node.

## Error handling

- Malformed JSONL line → skipped; count surfaced via `/api/predlab/health`.
- Empty/absent journal → all-null payload; UI renders "no data yet".
- Staleness computed from `written_utc` (UTC) only.
- Null `realized_book_ret` rows (first row per book, gap edges) excluded from compounding and Sharpe. Warm-up counter = count of non-null realized returns (matches the paper trader's ≥ 21 requirement for vt scale).

## Testing

- `tests/monitor/`: predlab source unit tests on fixture JSONL (compounding incl. nulls, staleness, gap annotation, missing-file degradation, malformed-line skip); endpoint tests via FastAPI TestClient (payload shape, 200-on-missing contract).
- Frontend: vitest for new lib functions; `npm run build` green before commit.
- Existing monitor tests must stay green (Legacy section reuses their code paths).

## Out of scope

- Any change to `predlab_s1_paper.py` or its journals.
- Removal of the adhoc backend module.
- Live trading integration for the champion (paper-only book).
- The sealed one-shot evaluation itself (2027-01-02, manual, one-shot).
