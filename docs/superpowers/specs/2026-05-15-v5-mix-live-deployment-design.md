# V5 MIX Live Deployment — Design Spec

**Date**: 2026-05-15
**Status**: design — pending implementation plan
**Branch**: feature/hybrid-modulator → main (live-v2.0 tag)
**Supersedes**: live-v1.0 (V2 + PIT on-chain 3-coin)

---

## 1. Architecture overview

V5 MIX live deployment extends the existing `tradingagents/execution/live/`
module in-place (approach A — multi-bundle in-place; B/C rejected, see §1.4).
The 10-step cycle shape is preserved; substance per step changes to support
per-coin feature routing, four coins, and an extended data layer.

### 1.1 Pipeline shape

Daily 00:05 UTC cycle, four coins (BTC, ETH, BNB, SOL), per-coin feature
routing:

```
[1] data_refresh   → CRITICAL (OHLCV, CoinMetrics) tier hard-fails
                     SUPPLEMENTARY (DefiLlama, Coinglass, Deribit, basis) degrade
[2] retrain        → composite bundle: 4 fit_pooled_full calls
                     {BTC,ETH}/78f, {BTC,ETH}/193f, {BTC,ETH,BNB}/78f, {BTC,ETH,SOL}/193f
                     joblib.dump → lgb_v5_mix_{asof}.pkl
[3] predict        → load composite, route per coin via static ROUTING map
[4-5] size + log   → existing sizer.compute_size, 4 coins iterated
[6] risk_check     → existing 4 gates; margin gate applied to 4-coin gross
[7] execute        → existing ExchangeClient
[8] shadow_replay  → existing, 4 coins
[9] snapshot       → portfolio + feature_snapshots; new bundle_route column
[10] notify        → Telegram, 4-coin status
```

### 1.2 Files changing

| File | Change |
|---|---|
| `live/config.py` | add `ROUTING` dict, default `COIN_UNIVERSE` = 4 coins, default `KELLY_FRACTION=0.25` |
| `live/data_refresh.py` | add `refresh_coinglass`, `refresh_deribit_dvol`, `refresh_perp_spot_basis`; tiered `refresh_all` orchestrator |
| `live/retrain.py` | 4 `fit_pooled_full` calls, composite bundle write |
| `live/predict.py` | load composite, route per coin |
| `live/runner.py` | wire new data_refresh + retrain/predict signatures |
| `live/schema.sql` | add `predictions.bundle_route`, `retrains.routes`, `cycles.*_sources` columns |
| `deploy/preflight.sh` | check Coinglass key + derivatives parquet dirs |
| `deploy/systemd/*` | unchanged (cycle name same); env file gains new keys |

### 1.3 Files unchanged

`sizer.py` (already per-coin), `risk.py` (gates coin-agnostic), `journal.py`
(schema extensible), `shadow.py`, `notify.py`, `rebacktest.py` (auto-picks
4-coin from journal).

### 1.4 Approach rejected

**B. Pluggable strategy module** — overkill until a 2nd strategy is on the
roadmap. **C. Parallel live_v5 module** — duplicates code; V2 path is being
replaced, not kept.

---

## 2. Components

### 2.1 `live/config.py`

New fields, env-overridable:

```python
COIN_UNIVERSE = ["bitcoin", "ethereum", "binancecoin", "solana"]
KELLY_FRACTION = 0.25
ROUTING = {
    "bitcoin":     {"feature_set": "78f",  "pool": ["bitcoin", "ethereum"]},
    "ethereum":    {"feature_set": "193f", "pool": ["bitcoin", "ethereum"]},
    "binancecoin": {"feature_set": "78f",  "pool": ["bitcoin", "ethereum", "binancecoin"]},
    "solana":      {"feature_set": "193f", "pool": ["bitcoin", "ethereum", "solana"]},
}
COINGLASS_API_KEY = os.environ["COINGLASS_API_KEY"]
DATA_REFRESH_CRITICAL = {"ohlcv", "coinmetrics"}
TRADINGAGENTS_DATA_ROOT = os.environ.get("TRADINGAGENTS_DATA_ROOT", "data")
```

`feature_set="193f"` → `add_onchain_pit=True`. `"78f"` → `add_onchain_pit=False`.

### 2.2 `live/data_refresh.py`

Three new refreshers (idempotent, incremental, match existing pattern):

```python
def refresh_coinglass(coins, derivatives_dir) -> None
def refresh_deribit_dvol(currencies, options_dir) -> None
def refresh_perp_spot_basis(symbols, raw_dir, daily_dir) -> None
```

Each writes to the same parquet paths the §13 fetch scripts wrote, so
`build_pit_onchain_features` reads fresh data with no other changes.

Orchestrator `refresh_all(config, structured_log)`:

```python
critical_failures = []
for src in ("ohlcv", "coinmetrics"):
    try: ...
    except Exception as e: critical_failures.append((src, e))
if critical_failures:
    raise CriticalDataRefreshError(critical_failures)

supplementary_failures = []
for src in ("defillama", "coinglass", "deribit_dvol", "perp_spot_basis"):
    try: ...
    except Exception as e:
        supplementary_failures.append((src, e))
        structured_log.warn("supplementary_data_stale", source=src, err=str(e))
return {"critical_ok": True, "supplementary_failures": supplementary_failures}
```

### 2.3 `live/retrain.py`

```python
def run_retrain(routing: dict, horizons: list[int], asof: str, ckpt_dir: Path):
    bundles = {}
    for coin, route in routing.items():
        pool = route["pool"]
        use_pit = route["feature_set"] == "193f"
        route_id = f"{coin}_{route['feature_set']}"

        raw = build_pooled_dataset(coin_universe=pool, ..., add_onchain_pit=use_pit)
        transformed = _transform_pooled(raw, horizons)

        bundles[route_id] = {}
        for h in horizons:
            bundles[route_id][h] = fit_pooled_full(transformed, horizon=h)

    out = ckpt_dir / f"lgb_v5_mix_{asof}.pkl"
    joblib.dump(bundles, out)
    return CheckpointArtifact(path=out, sha=_sha256_of(out), routes=list(bundles.keys()))
```

`run_retrain_with_fallback` unchanged in shape — on any exception, glob
`lgb_v5_mix_*.pkl` for the most recent prior. Atomic: composite is one file →
either all 4 routes fresh or all 4 fall back.

### 2.4 `live/predict.py`

```python
def run_predict(coin_universe, ckpt_path, asof, store_root, ohlcv_cache, horizons):
    composite = joblib.load(ckpt_path)
    out_rows = []
    for coin in coin_universe:
        route = ROUTING[coin]
        route_id = f"{coin}_{route['feature_set']}"
        pool_bundles = composite[route_id]
        use_pit = route["feature_set"] == "193f"

        feats = build_features_asof(
            coin_pool=route["pool"], asof=asof,
            store_root=store_root, ohlcv_cache=ohlcv_cache,
            add_onchain_pit=use_pit, horizons=horizons,
        )
        row = feats[feats["coin_id"] == coin].iloc[[0]]
        for h, bundle in pool_bundles.items():
            pred = predict_pooled(bundle, row)
            out_rows.append({"coin": coin, "horizon": h, "prediction": pred,
                             "ref_price": float(row["ref_price"].iloc[0]),
                             "route": route_id})
    return pd.DataFrame(out_rows)
```

### 2.5 `live/runner.py`

Minimal wire-up. Step 1 calls `data_refresh.refresh_all(config, structured_log)`
instead of three separate refresh calls. Step 2 calls
`retrain.run_retrain_with_fallback(routing=config.routing, ...)`. Step 3 calls
`predict.run_predict(coin_universe=config.coin_universe, ...)`. Steps 4-10
iterate 4 coins — already coin-agnostic.

### 2.6 `live/schema.sql`

Additive columns:

- `predictions.bundle_route` TEXT — which route_id produced each prediction
- `retrains.routes` TEXT — JSON list of route_ids in the composite
- `cycles.critical_data_fail_sources` TEXT — JSON list, nullable
- `cycles.supplementary_stale_sources` TEXT — JSON list, nullable

Existing 9-table schema unchanged otherwise.

---

## 3. Data flow

End-to-end at 00:05 UTC, 4 coins:

```
[1] data_refresh.refresh_all(config)
    ├─ CRITICAL: refresh_ohlcv(btc/eth/bnb/sol) → data/cache/{coin}.csv
    │            refresh_coinmetrics([...]) → data/onchain/{year}/{mm}.parquet
    │     any fail → raise CriticalDataRefreshError → cycle abort
    └─ SUPPLEMENTARY: refresh_defillama, refresh_coinglass, refresh_deribit_dvol,
                      refresh_perp_spot_basis
       per-source fail → log warn, reuse last-good parquet, continue

[2] retrain.run_retrain_with_fallback(routing, horizons, asof, ckpt_dir)
    ├─ bundles["bitcoin_78f"]     = build+fit({BTC,ETH}, 78f) for h7+h14
    ├─ bundles["ethereum_193f"]   = build+fit({BTC,ETH}, 193f)
    ├─ bundles["binancecoin_78f"] = build+fit({BTC,ETH,BNB}, 78f)
    └─ bundles["solana_193f"]     = build+fit({BTC,ETH,SOL}, 193f)
       any failure → drop new pkl, use prior composite

[3] predict.run_predict(coin_universe, ckpt_path, asof)
    for coin in [btc, eth, bnb, sol]:
        route_id = f"{coin}_{routing[coin]['feature_set']}"
        feats = build_features_asof(pool=routing[coin]['pool'],
                                    add_onchain_pit=(route['feature_set']=='193f'))
        row = feats[feats.coin_id == coin].iloc[[0]]
        for h in [7, 14]:
            pred = predict_pooled(composite[route_id][h], row)

[4-5] sizing — sizer.compute_size per coin, kelly=0.25
[6] risk_check — leverage_cap gate on 4-coin gross
[7] execute — ExchangeClient, 4 coins, delta-trade
[8] shadow_replay — existing, 4 coins
[9] snapshot — portfolio + feature_snapshots; new bundle_route column
[10] notify — Telegram 4-coin status
```

**Atomicity guarantees**:
- 4-pool retrain → one composite `.pkl`. All-fresh or all-fallback. Never mixed-vintage.
- data_refresh writes append-only; supplementary fail → `build_pit_onchain_features` reads last-good via `merge_asof` PIT alignment.
- predict reads composite by sha256 — corrupt half-file → joblib.load raises → fallback.

**Per-cycle invariants**: 4 routes × 2 horizons = 8 predictions; 4 coins each
get one (signal, confidence, position) triple; all journal rows carry
`cycle_id`.

---

## 4. Error handling

### 4.1 Failure surface table

| Surface | Class | Runner action | Status | Alert |
|---|---|---|---|---|
| critical data | hard | abort cycle, hold positions | `critical_data_fail` | Telegram immediate |
| supplementary data | soft | continue with stale features | `success_with_stale_data` | Telegram batched |
| retrain | soft | fall back to prior composite | cycle continues, `retrain_fallback=True` | Telegram on 3rd consecutive |
| predict (1 coin) | soft | skip coin, hold position | `bundle_route=null` for skipped | Telegram in summary |
| predict (≥3 coins) | hard | abort cycle | `predict_majority_fail` | Telegram immediate |
| sizing / risk gate | per-coin soft | skip coin | gate-specific | Telegram if blocked |
| execution | per-coin soft | log error, leave position | `execution_error` | Telegram in summary |
| margin gate | per-coin soft | reject new position | `risk_blocked: leverage_cap` | Telegram if rejected |

### 4.2 Critical data refresh fail

`refresh_all` raises `CriticalDataRefreshError`. Runner catches at step 1
boundary, skips steps 2-10. Journals `cycles.status=critical_data_fail`,
positions held, Telegram immediate. Recovery: manual `runner --once
--cycle-id YYYYMMDD-rerun` after operator fix.

### 4.3 Supplementary data fail

Orchestrator catches per-source, logs `event=supplementary_data_stale`,
continues. After 72h of failure on a single source, `notify.py` escalates to
secondary Telegram channel.

### 4.4 Retrain fail

`run_retrain_with_fallback` returns prior composite. After 3 consecutive
fallbacks, rebacktest verdict flags it.

### 4.5 Predict fail

Per-coin try/except. Skip-on-fail for 1-2 coins; abort cycle if ≥3 fail.

### 4.6 Margin gate

`risk.leverage_cap_gate` sums absolute gross across 4 coins. kelly=0.25 keeps
gross ≈ 92% — same envelope as 3-coin kelly=0.33. Verified empirically in
preflight rehearsal (§5.4).

### 4.7 Kill-all

`runner --kill-all` unchanged. Coin-agnostic.

---

## 5. Testing

### 5.1 Golden invariants

`tests/strategies/test_v2_sizing_golden.py` (13 invariants) must stay green —
sizer.py unchanged, so this is a regression check at every commit boundary.

### 5.2 V5 unit tests under `tests/execution/live/`

| Test file | What it pins |
|---|---|
| `test_config.py` | `LiveConfig.from_env()` returns `ROUTING` matching static dict; missing `COINGLASS_API_KEY` raises; 4-coin universe + kelly=0.25 defaults |
| `test_data_refresh.py` | 6-source orchestrator: critical fail raises; supplementary fail caught + logged; tiered classification matches `DATA_REFRESH_CRITICAL` |
| `test_data_refresh_idempotent.py` | Each new refresher idempotent — twice in one cycle = same parquet as once |
| `test_retrain.py` | Composite bundle has all 4 route_ids; each route uses correct `pool` + `add_onchain_pit`; atomic — partial failure → no `.pkl` |
| `test_retrain_fallback.py` | On any pool failure, returns prior `lgb_v5_mix_*.pkl`; never half-written composite seen |
| `test_predict.py` | Routes each coin to correct `route_id`; `bundle_route` populated; skip-on-fail; ≥3-coin fail raises |
| `test_predict_feature_parity.py` | predict uses same `add_onchain_pit` flag retrain used for that route |
| `test_runner_v5.py` | End-to-end mocked cycle: 10 steps in order; 4 coins iterated; cycle status reflects worst per-coin failure |
| `test_runner_critical_fail.py` | Critical data fail → steps 2-10 skipped, status `critical_data_fail`, no orders |
| `test_journal_v5_schema.py` | New columns round-trip cleanly; backward-compatible with v1 rows |

### 5.3 Online-gated refresher integration tests (`@pytest.mark.online`)

| Test | What it pins |
|---|---|
| `test_refresh_coinglass_live.py` | 1-day pull for BTC+ETH+BNB+SOL succeeds; rate-limit respected; parquet schema matches §13 |
| `test_refresh_dvol_live.py` | 1-day pull for BTC + ETH succeeds; new rows append correctly |
| `test_refresh_basis_live.py` | 1-day Binance perp + spot pull, basis computed, appended |

### 5.4 Local rehearsal — `scripts/rehearse_live_cycle.sh`

7 sequential cycles in `--dry-run` mode. Asserts:
- Composite bundle has 4 routes after cycle 1
- Subsequent cycles either fresh-retrain (4 new routes) or fall back atomically (4 old routes), never mixed
- Prediction count per cycle = 4 × 2 = 8
- Margin gate stays under 100% gross across all 7 cycles

Non-zero exit on any assertion failure.

### 5.5 Pre-deploy gate

All of the following green before `deploy.sh`:

1. `pytest tests/` — full suite
2. `pytest -m online tests/execution/live/` — 3 online refresher tests
3. `scripts/rehearse_live_cycle.sh` — 7-cycle local dry-run, exit 0
4. `python scripts/baseline_v5_mix.py` — backtest reproduces SR > 3.0
5. `python scripts/baseline_v5_mix.py --kelly 0.25 --output-dir data/v5_mix_kelly_025` — re-run at live kelly for acceptance target

---

## 6. Margin sizing + acceptance target

### 6.1 Kelly determination

3-coin live at kelly=0.33 lands ≈ 92% gross. Naive proportional scaling for
4 coins:

```
kelly_new ≈ 0.33 × 3/4 = 0.2475 → round to 0.25
```

**Default: kelly_fraction = 0.25.** Preflight rehearsal (§5.4) verifies
empirically. If margin walls hit, drop further to 0.20.

### 6.2 Backtest re-run at live kelly

Required artifact before deploy: `data/v5_mix_kelly_025/summary.json`
produced by extending `baseline_v5_mix.py` with a `--kelly` CLI arg
(currently hardcoded 0.5 in `_v2_positions`).

Expected output by extrapolation from kelly scaling (3-coin precedent: SR
preserved -2%, return scales ~kelly ratio, MaxDD shrinks proportionally):

```
Sharpe       ≥ 2.9
Return       ≥ +250% over 90 days (annualized from backtest)
Max DD       ≤ 5.5%
```

Numbers are placeholders — finalized after the actual kelly=0.25 backtest run.

### 6.3 90-day review cadence

- **Day 7**: cycles green, no margin walls, journal complete, Telegram alerts reasonable. **Parity check passes (§7).**
- **Day 30**: weekly rebacktest verdict from `ta-rebacktest.timer` shows live SR within 0.5 of backtest target. Parity check at day 30.
- **Day 90**: final live-vs-backtest written to `THESIS_FINDINGS.md §22`.

### 6.4 Rebacktest module change

`live/rebacktest.py` extended to:
- Run `baseline_v5_mix.py` over the live observation window at live kelly
- Per-coin SR comparison + portfolio SR comparison
- Verdict scheme unchanged (`ACCEPT` / `INVESTIGATE` / `REJECT`)

Minor change — same shape, different signal source.

---

## 7. Live-vs-backtest parity via historical refetch

### 7.1 Why

Backtest establishes SR + DD targets the thesis defense rests on. Live must
reproduce those targets. Primary check = re-fetch historical data fresh from
external APIs into an isolated sandbox, rebuild the backtest from scratch,
then compare to live journal. This validates the entire pipeline end-to-end:
data ingestion, parquet writes, PIT alignment, feature builder, retrain,
predict, sizer.

### 7.2 Three parity axes

| Axis | Source A (live) | Source B (replay) | Tolerance | Divergence means |
|---|---|---|---|---|
| **Prediction parity** | journal `predictions.prediction` | sandbox backtest preds | exact (LGB `random_state=42`) | data pipeline drift or training-window timing bug |
| **Sizing parity** | journal `decisions.target_position` | sandbox backtest position | exact (V2 sizing deterministic) | sizing primitives diverged |
| **Execution slippage** | journal `trades.fill_price` vs `decisions.ref_price` | sandbox synthetic fill at ref_price | < 50bps cumulative | bounds `COSTS` realism |

### 7.3 When

- N=7 cycles (week 1) — first authoritative check
- N=30, N=90 — acceptance review milestones
- Ad-hoc — operator CLI on demand

### 7.4 New script: `scripts/parity_refetch_and_replay.py`

```
python scripts/parity_refetch_and_replay.py \
    --journal /opt/tradingagents/data/trade_journal.db \
    --start-cycle 20260516 --end-cycle 20260522 \
    --sandbox /home/malecada/parity_w1_sandbox \
    --lookback-days 1500
```

Pipeline:

1. **Wipe sandbox**: `rm -rf {sandbox}/data`
2. **Refetch historical data into sandbox** (each fetch script accepts `--data-root` or equivalent flag; CM, DefiLlama, funding, basis, DVOL, Coinglass, OHLCV)
3. **Required script extension**: every fetch script grows a `--data-root` arg. Most already have output-dir args; verify each. Where missing, add.
4. **Run replay backtest**: `baseline_v5_mix.py --data-root {sandbox}/data --kelly 0.25 --start --end --output-dir {sandbox}/replay`
5. **Required `baseline_v5_mix.py` + `build_pooled_dataset` extension**: env var `TRADINGAGENTS_DATA_ROOT` honored by `onchain_store.DEFAULT_ROOT`, derivatives_dir defaults, etc. One env var = whole pipeline switches sandboxes.
6. **Compare**: load live journal rows; load sandbox replay outputs; produce side-by-side report.

### 7.5 Report format

`{sandbox}/parity_report.md`:

```
# Parity report — cycles 20260516..20260522

## Refetch summary
- CM rows added to sandbox: 113,528
- Coinglass rows: 27 cols × 4 coins
- Date span: ...
- Total refetch wall time: ...

## Prediction parity (4 coins × 2 horizons × 7 cycles = 56 rows)
| cycle | coin | h | live_pred | replay_pred | abs_diff | match |
Verdict: 56/56 exact match → PASS

## Sizing parity
| cycle | coin | live_pos | replay_pos | abs_diff | match |

## Execution slippage
| cycle | coin | live_fill | ref_price | slip_bps | cumulative_bps |
Cumulative slippage: Xbps (< 50bps cap → execution realistic)

## Aggregate metrics over window
| metric | live (journal) | replay (sandbox) | gap |
```

### 7.6 Verdict scheme

- **PASS**: prediction parity 100%, sizing parity 100%, slippage < 50bps cumulative
- **INVESTIGATE**: parity 100%, slippage 50-200bps → tune `COSTS`, deployment continues
- **FAIL**: any prediction or sizing mismatch → STOP live timer, debug, do not deploy further

### 7.7 Acceptance gate

Day-7 parity report **must be PASS** (not INVESTIGATE) before further live
trading. INVESTIGATE allowed at day 30 / 90 with documented `COSTS`
adjustment. FAIL at any milestone = `systemctl stop ta-cycle.timer` +
investigation.

### 7.8 Implementation notes

- **Sandbox root pattern**: `TRADINGAGENTS_DATA_ROOT` env var threaded through `onchain_store.DEFAULT_ROOT`, `build_pooled_dataset` OHLCV cache, `derivatives_dir` defaults.
- **Refetch idempotency**: refetch scripts already idempotent (Section 5.2). Re-running over identical date range yields identical parquets.
- **Wall time**: full refetch ~10-15 min first run, ~5 min if incremental. Backtest replay ~30s. Total parity check ~20 min.
- **Cumulative slippage formula**: `slip_cum_bps = Σ (live_fill_price - ref_price) × sign(target_position) / equity × 10000`.

---

## 8. Deployment + rollback

### 8.1 Pre-deploy gate

All §5.5 items green.

### 8.2 Merge to main

```bash
git checkout main
git pull
git merge --no-ff feature/hybrid-modulator -m "Merge V5 MIX live deployment (§22)"
git tag live-v2.0 -m "V5 MIX 4-coin per-coin-routed canonical"
git push origin main live-v2.0
```

### 8.3 Hetzner upgrade procedure

```bash
# 1. SSH in
ssh root@46.225.169.184
cd /opt/tradingagents

# 2. Kill open positions under V2
set -a; source /opt/tradingagents/secrets/.env.trading; set +a
/opt/tradingagents/venv/bin/python -m tradingagents.execution.live.runner --kill-all
sqlite3 /opt/tradingagents/data/trade_journal.db \
  'SELECT coin, qty FROM portfolio_snapshots WHERE snapshot_ts = (SELECT MAX(snapshot_ts) FROM portfolio_snapshots)'
# Verify: all qty = 0

# 3. Stop timers
systemctl stop ta-cycle.timer ta-rebacktest.timer

# 4. Backup
tar czf /root/backup_pre_v5_$(date +%Y%m%d).tar.gz \
    /opt/tradingagents/data/trade_journal.db \
    /opt/tradingagents/data/checkpoints \
    /opt/tradingagents/secrets

# 5. Update code to live-v2.0
sudo -u tabot git fetch --tags
sudo -u tabot git checkout live-v2.0
sudo -u tabot /opt/tradingagents/venv/bin/pip install -e .

# 6. Add new env vars
sudo -u tabot tee -a /opt/tradingagents/secrets/.env.trading <<'EOF'
COINGLASS_API_KEY=<from operator>
COIN_UNIVERSE=bitcoin,ethereum,binancecoin,solana
KELLY_FRACTION=0.25
EOF

# 7. Preflight
bash /opt/tradingagents/deploy/preflight.sh

# 8. Schema migration (additive columns)
sudo -u tabot /opt/tradingagents/venv/bin/python -m tradingagents.execution.live.journal --migrate

# 9. First supervised cycle
sudo -u tabot bash -c '
    set -a; source /opt/tradingagents/secrets/.env.trading; set +a
    /opt/tradingagents/venv/bin/python -m tradingagents.execution.live.runner \
        --once --cycle-id $(date -u +%Y%m%d)-supervised 2>&1 | tee /tmp/v5_first_cycle.log
'

# 10. Re-enable timers
systemctl start ta-cycle.timer ta-rebacktest.timer

# 11. Observe first autonomous cycle next 00:05 UTC
journalctl -u ta-cycle.service --since '2h ago' -f
```

### 8.4 Stop-the-line conditions

Halt + rollback if:
- Step 2 leaves any non-zero positions
- Step 3 timer doesn't stop
- Step 7 preflight non-zero exit
- Step 8 schema migration fails
- Step 9 supervised cycle status ≠ success
- Step 11 first autonomous cycle status ≠ success

### 8.5 Rollback procedure

`deploy/ROLLBACK.md` extended for V5. ~3-minute rollback to live-v1.0:

```bash
systemctl stop ta-cycle.timer ta-rebacktest.timer
set -a; source /opt/tradingagents/secrets/.env.trading; set +a
/opt/tradingagents/venv/bin/python -m tradingagents.execution.live.runner --kill-all
cd /opt/tradingagents
sudo -u tabot git checkout live-v1.0
sudo -u tabot /opt/tradingagents/venv/bin/pip install -e .
sudo -u tabot sed -i '/^COINGLASS_API_KEY=/d; /^COIN_UNIVERSE=/d; /^KELLY_FRACTION=/d' \
    /opt/tradingagents/secrets/.env.trading
sudo -u tabot bash -c 'echo "KELLY_FRACTION=0.33" >> /opt/tradingagents/secrets/.env.trading'
# Schema rollback unnecessary — V5 columns are additive
systemctl start ta-cycle.timer ta-rebacktest.timer
```

Journal backup from §8.3 step 4 lives at `/root/backup_pre_v5_YYYYMMDD.tar.gz`.
Restore only if SQLite corruption suspected.

### 8.6 90-day observation plan

| Milestone | Required artifact | Required verdict |
|---|---|---|
| Day 0 | `/tmp/v5_first_cycle.log` + journal row | `status=success` |
| Day 7 | `data/parity_w7/parity_report.md` | PASS |
| Day 30 | Weekly rebacktest verdict + `parity_w30/parity_report.md` | live SR within 0.5 of backtest target; parity PASS |
| Day 90 | Final live-vs-backtest written to `THESIS_FINDINGS.md §22` | live SR ≥ 90% of backtest target |

### 8.7 Out of scope

- 5th-coin extension (XRP/DOGE) — defer until 90-day acceptance
- Strategy plugin abstraction — defer until 2nd strategy on roadmap
- Mainnet (real money) — defer pending 90-day testnet acceptance
- Thesis chapter writing — separate spec post-90-day

---

## 9. Open questions / decisions deferred to implementation

1. **Exact kelly value**: 0.25 default; preflight rehearsal may force 0.20 if margin walls hit.
2. **Backtest re-run acceptance target numbers**: placeholders in §6.2; finalized after `baseline_v5_mix.py --kelly 0.25` run.
3. **Per-source supplementary fail escalation threshold**: §4.3 says "72h of failure" — verify with operator if shorter (24h?) preferred.

These are documented but not blocking — resolved during plan execution.

---

## 10. Acceptance criteria for "design done"

- ✅ All 8 design sections approved
- ✅ Architecture preserves V2 sizing layer 1:1 (golden tests pass)
- ✅ Per-coin feature routing matches §17/§20 backtest results
- ✅ 4-bundle composite atomicity defined
- ✅ Tiered data refresh failure handling defined
- ✅ Live-vs-backtest parity check via historical refetch defined
- ✅ Deployment + rollback procedure defined
- ✅ Test surface defined (golden + V5 unit + online-gated + rehearsal + pre-deploy gate)
- ✅ 90-day acceptance plan defined

Next: writing-plans skill converts this spec into a task-by-task implementation plan.
