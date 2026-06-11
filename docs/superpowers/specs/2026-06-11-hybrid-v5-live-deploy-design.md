# Hybrid V5 Live Deployment — Paired Quant-vs-Hybrid Testnet A/B

**Date:** 2026-06-11
**Status:** Design — awaiting user review
**Base:** `live-v2.2.2` (clean deploy tag; has the full modulator graph stack + all v2.0–v2.2 live hardening)
**Related:** THESIS §23 (Hybrid V5 1-yr ETH alpha +1.10), `project_hybrid_v5_1yr`, `project_v5_8coin_live_deploy`, `project_v5_live_deploy`

## 1. Goal

Run the **hybrid quant+LLM-modulator** strategy live on Binance testnet **in parallel** with the existing pure-quant V5 MIX live bot, so the two can be compared head-to-head on the same calendar window. The hybrid is the V5 quant base position scaled by the LLM modulator multiplier; the live test asks whether the §23 backtest alpha (ETH SR +1.10 over pure V5) reproduces in forward live trading.

### Success criteria

- A second testnet bot trades the live 8-coin universe each daily cycle, sizing each coin as `base × (1 + effective_weight × (multiplier − 1))`.
- The existing quant bot's behavior is **byte-for-byte unchanged** (it is mid-flight in a 90-day acceptance window — no regression permitted).
- Both bots share **one** V5 train/predict per cycle, so their quant bases are identical by construction (true paired A/B).
- A comparison report (extending the existing weekly rebacktest + monitor UI) shows ΔSharpe / Δreturn / ΔmaxDD between quant and hybrid, focused on the BTC+ETH sleeve (where alpha is validated) and the full 8-coin book.

### Non-goals (YAGNI)

- No mainnet / real-capital trading. Testnet only.
- No new modulator research, re-tuning, or architecture change — deploy the validated §23 modulator as-is.
- No change to the quant bot's universe, sizing, risk, or schedule.
- No intraday/event-driven hybrid — daily cycle only.

## 2. Locked decisions

| Decision | Choice |
|---|---|
| Comparison design | **Paired, dual-execution** — one cycle, one V5 base, two accounts execute base vs base×modulator |
| Coin universe | **Full live 8-coin** — BTC ETH BNB SOL XRP DOGE ADA TRX |
| Cold-start | **Pre-train missing per-coin checkpoints before deploy** |
| Reporting | **Extend existing infra** (rebacktest/parity + monitor UI), hybrid writes its own journal |

## 3. Background — what already exists (de-risks the build)

- **The modulator graph stack is already on the deploy base.** `git diff --stat live-line…feature/hybrid-modulator` for `agents/modulator.py`, `strategies/modulator.py`, `strategies/calibration.py`, `graph/setup.py`, `graph/trading_graph.py` is **empty** — identical. Phase-4 wiring (`Trader→Modulator→Risk→PM`, Self-MoA sampler) is present in `graph/setup.py`. **No merge of the research branch is needed.**
- **Composition formula** (reference: `scripts/backtest_hybrid.py:118`, `scripts/ablate_hybrid.py:73`):
  `final = base × (1 + effective_weight × (multiplier − 1))`.
- **Graph entry point exists:** `TradingAgentsGraph.propagate_with_modulator(coin, date)` → `(final_state, modulated_position, quant_signal, narrative)`, where `modulated_position` carries `llm_multiplier`, `effective_weight`, `llm_confidence`, `llm_uncertainty`.
- **Effective-weight is asset-agnostic** (derived from `regime`, `uncertainty`, `rolling_llm_edge[coin]`, `unlock_flag` via `strategies/effective_weight.py` + config `regime_weighting`, dampeners) — the same single code path runs all 8 coins, so 8-coin needs no per-coin modulator logic.
- **The quant Layer-1 reads predictions from a static dir** (`quant_pred_dir → data/multi_2coins_v2/preds_lgb_h{7,14}.csv`, `strategies/quant_engine.py`; accepts a `base_dir` override). This is the one live seam (§5.3).

## 4. Architecture

Single daily process (one systemd trigger), additive to the quant path:

```
ta-cycle (daily 00:05 UTC) — ONE process
│
├─ STEP 1  quant run_cycle()  ── UNCHANGED ──▶ QUANT testnet acct + journal(quant)
│            data→retrain→predict(8-coin preds_df)→size(V5 base)→risk→execute
│            (this is today's live bot, untouched; writes predictions + sizing to journal)
│
└─ STEP 2  hybrid_runner (NEW, additive)
             a. read this cycle's V5 base[coin] + preds from journal(quant)   ← zero-touch reuse
             b. stage preds → quant_engine CSV layout (8 coins, h7/h14) in a per-cycle dir;
                point quant_pred_dir/base_dir at it
             c. for coin in 8:
                  propagate_with_modulator(coin, date)  →  (multiplier, effective_weight)   [gpt-4o-mini]
             d. final[coin] = base[coin] × (1 + effective_weight[coin] × (multiplier[coin] − 1))
             e. risk-check final (same per-coin caps + gross cap + 3% price stops as quant)
             f. execute final on HYBRID testnet acct  ──▶ journal(hybrid)
│
└─ STEP 3  comparison: weekly rebacktest job + monitor read both journals →
             ΔSR / Δret / ΔmaxDD  (BTC+ETH sleeve + full 8)
```

**No-regression guarantee:** STEP 1 is the existing `run_cycle()` invoked unmodified — it executes the quant account exactly as today and persists predictions/sizing to its journal. STEP 2 only *reads* that journal and trades a *separate* account. The sole code addition to the existing path is, at most, surfacing the in-memory base weights to avoid a journal round-trip — and even that is optional (the journal already records them).

## 5. Components

Each is a small, independently testable unit.

### 5.1 `hybrid_runner` (new — `tradingagents/execution/live/hybrid_runner.py`)
- **Does:** orchestrates STEP 2 — read base, stage preds, call modulator per coin, compose, risk-check, execute on the hybrid account, write hybrid journal, heartbeat.
- **Interface:** `run_hybrid_cycle(cycle_id, *, dry_run=False) -> CycleResult`. CLI `--once/--dry-run/--cycle-id/--kill-all/--resume` mirroring `live/runner.py`.
- **Depends on:** quant journal (read), `quant_engine` staging, `TradingAgentsGraph.propagate_with_modulator`, `execution/risk.py`, a second `ExchangeClient`, hybrid journal.

### 5.2 Quant-base reuse (read-only)
- **Does:** load the just-written `predictions` + `sizing` rows for `cycle_id` from the quant journal → `base[coin]`.
- **Why journal-read:** zero modification to `run_cycle()` → strongest no-regression guarantee. (Alternative: have the paired orchestrator pass base weights in-memory; decide at plan time — default to journal-read.)

### 5.3 Prediction staging (the one real seam)
- **Does:** each cycle, write the live V5 8-coin predictions to the CSV layout `quant_engine` expects (`preds_lgb_h{7,14}.csv` per coin) in a per-cycle dir; set `base_dir`/`quant_pred_dir` so the modulator graph's Layer-1 consumes live preds, not the static backtest dir.
- **Interface:** `stage_quant_preds(preds_df, out_dir) -> Path`.

### 5.4 Modulator invocation + config pinning
- **Does:** build one `TradingAgentsGraph` with the **validated hybrid config**, call `propagate_with_modulator` per coin.
- **Config pins (must override branch defaults):**
  - `deep_think_llm = quick_think_llm = "gpt-4o-mini"` (branch `default_config` ships `gpt-5.4-mini/nano`; gpt-5-mini **hurt**, §23.9).
  - `selected_analysts = ["market", "onchain", "prediction"]` — drop `crypto_sentiment` (policy `feedback_drop_sentiment_analyst`). Keep `market` (asset-agnostic path; the market-analyst-v2 refactor was **rejected**, `project_market_analyst_v2`). **Caveat:** sentiment-drop validated on BTC+ETH only — 8-coin is an extrapolation; record it.
  - Self-MoA **N=5** — confirmed hard-coded (`graph/setup.py:126`, `agents/modulator.py:112`, `effective_weight.py:16`). Pin/assert it.
  - Modulator config (`regime_weighting`, `rolling_edge_window_days`, dampeners) — already validated defaults on the base; keep.

### 5.5 Composition + execution
- **Does:** apply the formula (§3), then route through the **same** `execution/risk.py` path (per-coin notional caps, gross cap, MIN_NOTIONAL, LOT_SIZE rounding, 3% **price**-based STOP_MARKET algo stops) before placing orders on the hybrid account.
- **Note:** `multiplier>1` can lever the hybrid position *above* the quant base; the shared risk caps bound it. Stops/risk apply post-composition.

### 5.6 Second-account isolation
- **Does:** hybrid trades a **separate Binance testnet account** (its own API key/secret) so positions never collide with the quant account.
- **Isolation:** separate `DATA_DIR` (own `trade_journal.db`, heartbeat, halt file), separate secrets file, separate systemd unit body. Same VPS, same trigger time.
- **External deps (user provides):** (1) a 2nd Binance **testnet** API key/secret; (2) `OPENAI_API_KEY` on the VPS (gpt-4o-mini).

### 5.7 Pre-train missing checkpoints (pre-deploy phase)
Live universe = BTC ETH BNB SOL XRP DOGE ADA TRX. Current checkpoints: regime HMM for BTC/ETH/BNB/SOL; isotonic calibration for BTC/ETH.
- **Regime HMM (cheap, deterministic — price history only):** train **XRP, DOGE, ADA, TRX** via
  `scripts/train_regime_hmm.py --coins ripple dogecoin cardano tron --through <deploy-date> --n-iter 200`.
  (Missing HMM already degrades gracefully — `regime.py:284` try/except → warning + default — so this is quality, not a blocker.)
- **Isotonic calibration (heavier — needs LLM signal history):** missing for **BNB, SOL, XRP, DOGE, ADA, TRX** (6). `IsotonicCalibrator.fit` needs ≥10 `(raw_conf, outcome)` pairs, which only exist after a historical `generate_hybrid_signals` pass per coin → real LLM cost. **Cutoff constraint:** that historical pass must start **after 2023-10** (gpt-4o-mini cutoff; `feedback_llm_cutoff_constraint`). Missing calibration falls back to **identity** (`load_or_identity`) — the validated BTC+ETH-era state itself used identity for all-but-two coins, so this is acceptable if cost is a concern.
  - **Scope flag for review:** regime HMM pre-train is clearly worth it; calibration pre-train for the 6 satellites carries an LLM-cost historical pass — see §8. Confirm at review whether to do all 6 or accept identity for the satellites.

### 5.8 Comparison reporting (extend existing)
- **Does:** extend the weekly `rebacktest.py`/parity job + monitor UI to read **both** journals and emit quant-vs-hybrid ΔSR / Δret / ΔmaxDD over the overlapping live window; per-coin + BTC+ETH sleeve + full-8 aggregate.
- **Comparison metric:** relative — does hybrid beat quant live (esp. ETH)? Null = "no live modulator alpha." Report from the hybrid start date forward over the common window.

## 6. Data flow (one cycle)

1. `run_cycle()` (quant) → executes quant acct, writes `predictions` + `sizing` to journal(quant), heartbeat(quant).
2. `hybrid_runner` reads `base[coin]` from journal(quant); stages preds → CSV dir.
3. Per coin: `propagate_with_modulator` → `multiplier`, `effective_weight` (gpt-4o-mini, Self-MoA N=5).
4. Compose `final[coin]`; risk-check; execute on hybrid acct; write journal(hybrid); heartbeat(hybrid).
5. (Weekly) comparison job diffs the two journals.

## 7. Testing

- Unit: `stage_quant_preds` round-trips to the exact `quant_engine` CSV schema; composition formula matches `ablate_hybrid.py:73` on fixtures; config-pin asserts (gpt-4o-mini, no sentiment, N=5).
- Integration: `hybrid_runner --dry-run` over a mocked exchange + a stubbed graph → asserts per-coin `final` and that **no order hits the quant account**.
- Regression guard: a test asserting `run_cycle()` output is unchanged with the hybrid path present (e.g. quant journal rows identical with/without STEP 2).
- Parity: extend the existing harness to verify hybrid live decisions replay from journal.

## 8. Risks / cost / caveats

- **8-coin cold-start:** even after regime-HMM pre-train, `rolling_llm_edge` cold-starts per coin (`rolling_edge_min_trades=10`) → the 6 satellites' effective_weight is under-informed for the first ~weeks. Self-warms. Expected; the validated alpha is BTC+ETH, which are fully warm.
- **LLM cost/latency:** 8 full graphs/day × Self-MoA N=5, gpt-4o-mini — small daily run-cost, but the calibration pre-train (§5.7) is a one-off **historical** LLM pass over 6 coins → the main cost line. Bound it (window length × coins) and confirm at review.
- **Cutoff:** any historical hybrid-signal generation must start after 2023-10.
- **Sentiment-drop extrapolation:** dropping `crypto_sentiment` is validated on BTC+ETH only; applying to all 8 is an assumption — recorded as a caveat, revisitable.
- **No-regression is the hard constraint:** all hybrid work is additive; STEP 1 stays untouched and is covered by a regression test.

## 9. Rollout

1. Pre-train regime HMM (XRP/DOGE/ADA/TRX) + (scoped) calibration; validate checkpoints load.
2. Build `hybrid_runner` + staging + config pins + tests (off `live-v2.2.2` in an isolated worktree).
3. Provision 2nd testnet key + `OPENAI_API_KEY`; second `DATA_DIR`/secrets/systemd unit.
4. Dry-run on VPS (no orders) → verify per-coin `final`, isolation, journals.
5. Enable hybrid cycle; start the common-window clock; wire the comparison report.

## 10. Resolved decisions (2026-06-11)

1. **Calibration pre-train scope** (§5.7/§8): regime HMM pre-trained for all 4 missing coins (XRP/DOGE/ADA/TRX, cheap/deterministic). Isotonic calibration for the 6 satellites generated over the §23 validated window (1-yr, post-2023-10) as a **gated, cost-estimated pre-deploy task** — the LLM spend is surfaced for go/no-go before it runs; identity fallback (`load_or_identity`) if declined.
2. **Quant-base handoff** (§5.2): **journal-read** (zero-touch to the quant path).
3. **Self-MoA N=5** (confirmed in code) and **analyst set = `market` + `onchain` + `prediction`** (sentiment dropped). See §5.4.
