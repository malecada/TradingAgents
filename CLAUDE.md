# TradingAgents — Prediction Lab Worktree

Branch `research/prediction-lab`. Active research worktree for pre-registered strategy/forecast cycles. The core `tradingagents/` package is shared with the main worktree (`../TradingAgents/CLAUDE.md` documents architecture, config, API); this file covers what is specific to research work here.

## Status (Sep 2026)

**All research cycles closed negative except the active one.** Zero validated strategies program-wide (STATE Aug-24). Champion ewma_20 low-vol LS and Phase O/P/Bybit results were VOIDED by the Aug-24 log-PnL audit (+1.892 → −0.371 simple returns); corrected S1 holdout −2.20; opt2 re-optimization 0/24. Subsequent cycles (xfam ×5, nlst, nlst2) all negative.

- No active cycle. nlst3 (moonshot-ranking) closed FAIL Sep-1: OOS IC +.136 real, top-quintile economics not significant (n=78, ex-top negative).
- S1 paper trader: VPS `/opt/tradingagents/predlab-data` is authoritative (hourly guard cron); S1 live executor built Aug-21, deploy pending testnet keys + funding
- Full history: `THESIS_FINDINGS.md` §54+ (43 sections) + closed-programs ledger in auto-memory

## Research discipline (mandatory — house standard)

Playbook: `../RESEARCH_LOOP_GUIDE.md`. Every cycle:

1. **Charter** — hypothesis, data, tests, kill criteria written BEFORE any result exists
2. **Pre-register** — gates key committed to `data/predlab/gates.json` pre-result; never edit criteria after results
3. **Tier ladder** — cheap P0 probe kills early → P1/P2 only on PASS
4. **One-shot verdict** — BH-FDR across the test family; NW t-stats; DSR where pooled; placebos (time-shift, symbol-shuffle) must FAIL to discriminate
5. **Forensics on every negative** — power probes, kill-tests, honest denominators; **convention-swap (log vs simple returns) kill-test mandatory** since Aug-24
6. **Write-up** — THESIS_FINDINGS section + gates.json verdict + memory entry, then commit

Engine rule: **simple returns only as PnL**. The Aug-24 correction is tested; never reintroduce log-return accounting (shorts gain fake +½σ²/day).

## Layout

```
data/predlab/               # gates.json (24 keys), per-cycle results json, run ledger
scripts/predlab_<fam>_*.py  # one family per cycle: xfam, nlst, nlst2, nlst3, opt, pp, s1, ...
                            # closed-cycle scripts stay for provenance — do not re-run without new charter
scripts/predlab_xfam_lib.py # shared stats/gate library (BH-FDR, NW, placebos)
scripts/predlab_nlst_lib.py # new-listing cycle shared lib (13+ unit tests)
THESIS_FINDINGS.md          # persistent empirical record — every cycle gets a section (KEEP UPDATED)
```

## Reusable data stores (survive their dead cycles)

- 799-sym Binance perp daily (survivorship-safe), 735-sym Bybit perp — ⚠️ delisted symbols have truncated history (store first-bar ≠ launch; 72/124 events artifacts, use exchange launchTime)
- 217-sym 1h intraday; 333-sym 1h klines (coverage ends 2024)
- 7,972-sym equity + futfx stores (`data/xsect_equity/`, `data/xsect_futfx/`)
- DEX pool store (Uniswap v2 via drpc.org; 10K-block range limit; GeckoTerminal for pool metadata)

## Environment

```bash
uv sync --all-extras --python 3.13.13
python -m pytest tests/
```

Long runs: nohup + idempotent caches + polling watcher; ledger/results-json on disk = recovery map after session loss. Push branch to origin each session (this + VPS copy are the only backups).
