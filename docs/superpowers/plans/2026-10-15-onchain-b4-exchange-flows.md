# B4 Exchange Flows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Register and run one ETH study that screens daily Coin Metrics exchange metrics and hourly exchange flows (ETH and stablecoins, exchange entities expanded by causal deposit-address inference) against price/volume history, with one committed selection and at most one opening of the sealed 2025–26 window.

**Architecture:** New package `tradingagents/research/onchain_b4/` beside B2/B3 (imported, never edited). A sequential day pass reads three public S3 tables per day, keeps a causal exchange-entity state (Bloom filter of seen senders, candidate table, deposit set) with snapshots, and writes 24 hourly rows per day. Feature, sample, screen and holdout stages follow B3's pattern with config-driven targets of two kinds (daily, hourly).

**Tech Stack:** Python 3.13, numpy, pandas, pyarrow (S3, parquet, compute), scikit-learn (via B2 `fit_predict`), pytest; systemd user units for long runs.

**Spec:** `docs/superpowers/specs/2026-10-15-onchain-b4-exchange-flows-design.md`

## Global Constraints

- Windows: development 2017-10-02 → 2024-12-31; sealed holdout 2025-01-01 → 2026-10-12; walk-forward test years 2019–2024; purge = target horizon.
- All price-derived data after 2024-12-31 (hourly Binance bars, Coin Metrics metrics) is written only to `research_artifacts/onchain-b4/sealed/` and read only by the holdout command.
- Chain pass days 2017-01-01 … 2026-10-11 (3,571), strictly in date order; reads may be prefetched.
- Tokens: USDT `0xdac17f958d2ee523a2206206994597c13d831ec7` (6), USDC `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` (6), DAI `0x6b175474e89094c44da98b954eedeac495271d0f` (18).
- Exchange set E(d) = L ∪ D(d); D from first-send rule and n_L / n_out ≥ 0.9; Bloom 2³² bits, 5 hashes; state updated after each day's flows.
- 42 comparisons (12 daily + 30 hourly); gate: 95 % interval upper < 0 and better in ≥ 4 of 6 years; ≤ 3 selected; bootstrap 2,000 draws, seed 20261015.
- `onchain_b`, `onchain_b2`, `onchain_b3` are imported, not edited. Study docs impersonal (no "we/our").
- Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Test command for the package: `.venv/bin/python -m pytest tests/research/onchain_b4 -q`.

## Review Focus

1. Early days without stablecoin transfers, and pre-London transactions whose effective gas price is null → empty arrays and nulls flow through reader, entities and flows without errors (Task 3 `test_reader_old_formats_and_nulls`, Task 4 `test_update_with_no_transfers`).
2. Token transfer addresses already 42 characters long (format variation across years) → kept as they are, not cut (Task 3 `test_reader_old_formats_and_nulls`).
3. Missing Binance hourly bars → every sample whose features or label need the bar is excluded, nothing crashes (Task 6 `test_missing_bar_excludes_dependent_rows`).
4. A crash between snapshots → the resumed pass produces outputs and state identical to an uninterrupted pass (Task 8 `test_resume_matches_uninterrupted`).
5. A bucket outage or reader bug that marks every day unavailable → the pass stops after three consecutive unavailable days instead of silently marking the whole history (Task 8 `test_consecutive_unavailable_stops`).

---

### Task 1: Skeleton, configuration, registration

**Files:**
- Create: `tradingagents/research/onchain_b4/__init__.py` (empty), `tradingagents/research/onchain_b4/config.py`
- Create: `research/onchain-b4-2026-10-15/config/b4.json`, `research/onchain-b4-2026-10-15/gates.json`, `research/onchain-b4-2026-10-15/CHARTER.md`, `research/onchain-b4-2026-10-15/STATE.md`
- Test: `tests/research/onchain_b4/__init__.py` (empty), `tests/research/onchain_b4/test_config.py`

**Interfaces:**
- Produces: `config.ROOT`, `config.STUDY`, `config.ARTIFACTS`, `config.B2_ARTIFACTS` (Path); `config.load() -> dict`; `config.windows(cfg=None) -> dict[str, date]`; `config.days(cfg=None) -> list[str]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b4/test_config.py
from tradingagents.research.onchain_b4 import config


def test_config_counts_windows_and_tokens():
    c = config.load()
    n = sum(len(c['comparisons'][t['kind']]) for t in c['targets'].values()) * len(c['families'])
    assert n == 42
    days = config.days(c)
    assert len(days) == 3571 and days[0] == '2017-01-01' and days[-1] == '2026-10-11'
    w = config.windows(c)
    assert w['dev_end'].isoformat() == '2024-12-31' and w['holdout_start'].isoformat() == '2025-01-01'
    assert sorted(v['decimals'] for v in c['tokens'].values()) == [6, 6, 18]
    assert all(v[0] in ('f0_', 'h0_') for v in c['sets'].values())


def test_study_registration_files_exist():
    for name in ('CHARTER.md', 'gates.json', 'STATE.md'):
        assert (config.STUDY / name).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_config.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.research.onchain_b4'`

- [ ] **Step 3: Write config module and registration files**

```python
# tradingagents/research/onchain_b4/config.py
"""Frozen B4 configuration (research/onchain-b4-2026-10-15/config/b4.json)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b4-2026-10-15'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b4'
B2_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b2'


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b4.json').read_text())


def windows(cfg=None) -> dict:
    return {k: date.fromisoformat(v) for k, v in (cfg or load())['windows'].items()}


def days(cfg=None) -> list:
    p = (cfg or load())['pass']
    return [d.date().isoformat() for d in pd.date_range(p['first_day'], p['last_day'], freq='D')]
```

`research/onchain-b4-2026-10-15/config/b4.json`:

```json
{
 "windows": {"dev_start": "2017-10-02", "dev_end": "2024-12-31", "holdout_start": "2025-01-01", "holdout_end": "2026-10-12"},
 "pass": {"first_day": "2017-01-01", "last_day": "2026-10-11", "snapshot_every": 30, "prefetch": 2, "max_consecutive_unavailable": 3},
 "s3": {"bucket": "aws-public-blockchain", "region": "us-east-2", "retries": [30, 120]},
 "tokens": {
  "0xdac17f958d2ee523a2206206994597c13d831ec7": {"name": "USDT", "decimals": 6},
  "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"name": "USDC", "decimals": 6},
  "0x6b175474e89094c44da98b954eedeac495271d0f": {"name": "DAI", "decimals": 18}},
 "entities": {"bloom_bits_log2": 32, "bloom_hashes": 5, "deposit_share": 0.9},
 "flows": {"large_eth": 100.0, "large_usd": 1000000.0},
 "hourly": {"h1_window": 168, "h1_min": 120, "d24_window": 720, "d24_min": 480, "clip": 10.0},
 "daily": {"z_window": 28, "z_min": 21, "clip": 10.0, "lag_days": 1},
 "cm": {"start": "2017-01-01", "end": "2026-10-12",
        "eth": ["FlowInExNtv", "FlowOutExNtv", "SplyExNtv", "SplyCur", "CapMVRVCur", "AdrActCnt", "FeeTotNtv"],
        "stables": ["usdt", "usdc", "dai"]},
 "binance": {"symbol": "ETHUSDT", "start": "2017-08-17", "end": "2026-10-13"},
 "targets": {
  "T1": {"kind": "daily", "task": "classification", "horizon_hours": 24, "block": 14},
  "R7": {"kind": "daily", "task": "regression", "horizon_hours": 168, "block": 28},
  "V7": {"kind": "daily", "task": "regression", "horizon_hours": 168, "block": 28},
  "R1": {"kind": "hourly", "task": "regression", "horizon_hours": 1, "block": 168},
  "R6": {"kind": "hourly", "task": "regression", "horizon_hours": 6, "block": 168},
  "R24": {"kind": "hourly", "task": "regression", "horizon_hours": 24, "block": 168},
  "V6": {"kind": "hourly", "task": "regression", "horizon_hours": 6, "block": 168},
  "V24": {"kind": "hourly", "task": "regression", "horizon_hours": 24, "block": 168}},
 "sets": {"D0": ["f0_"], "DF": ["f0_", "cmf_"], "DA": ["f0_", "cmf_", "cmo_"],
          "H0": ["h0_"], "HE": ["h0_", "eth_"], "HS": ["h0_", "stable_"], "HA": ["h0_", "eth_", "stable_", "act_"]},
 "comparisons": {"daily": [["DF", "D0"], ["DA", "D0"]], "hourly": [["HE", "H0"], ["HS", "H0"], ["HA", "H0"]]},
 "onchain_rank": {"DA": 0, "HA": 0, "DF": 1, "HE": 1, "HS": 1},
 "families": ["linear", "trees"],
 "folds": {"test_years": [2019, 2020, 2021, 2022, 2023, 2024], "inner_len": {"daily": 365, "hourly": 8760}},
 "models": {"alphas": [0.1, 1, 10, 100, 1000, 10000, 100000], "fallback_alpha": 100.0,
            "trees": {"max_iter": 100, "learning_rate": 0.05, "max_leaf_nodes": 7, "min_samples_leaf": 30,
                      "l2_regularization": 1.0, "random_state": 11}},
 "gate": {"draws": 2000, "seed": 20261015, "chunk": 100, "min_year_wins": 4, "max_selected": 3, "alpha": 0.05}
}
```

`research/onchain-b4-2026-10-15/gates.json`:

```json
{
 "registered": "2026-10-15",
 "spec": "docs/superpowers/specs/2026-10-15-onchain-b4-exchange-flows-design.md",
 "targets": "daily T1 next-day direction, R7 7-day log return, V7 7-day log realised volatility; hourly R1/R6/R24 log returns, V6/V24 log realised volatility",
 "comparisons": {"daily": [["DF", "D0"], ["DA", "D0"]], "hourly": [["HE", "H0"], ["HS", "H0"], ["HA", "H0"]]},
 "families": ["linear", "trees"],
 "screen_gate": "pooled loss difference 95% circular block-bootstrap interval entirely below 0 AND lower loss in >= 4 of 6 test years (2019-2024)",
 "selection": "at most 3 passing configurations by interval upper bound divided by comparator loss; ties prefer DA/HA; selection.json committed before any holdout read; screen never overwrites it",
 "holdout_gate": "one-shot lock with selection commit and blob; refit on all development samples; one-sided bootstrap p; Holm-adjusted p < 0.05 and mean difference < 0",
 "sealed_window": "ETH 2025-01-01..2026-10-12 (never read by M2, B2 or B3); daily and hourly samples",
 "no_tuning": "no feature, model or threshold change after any holdout read",
 "amendments": []
}
```

`research/onchain-b4-2026-10-15/CHARTER.md`:

```markdown
# B4 charter — ETH exchange flows, daily and hourly

Registered 2026-10-15 before any B4 data read. Spec:
`docs/superpowers/specs/2026-10-15-onchain-b4-exchange-flows-design.md`.

## Question

Do exchange flows — ETH and stablecoins moving into and out of exchange entities —
measured daily by Coin Metrics or hourly from the chain add out-of-sample information to
price/volume history for ETH direction, return and volatility (next day to next week;
next 1–24 hours)?

## Design

- Stage 1 (daily): Coin Metrics exchange inflow, outflow, net flow, exchange supply;
  MVRV, active addresses, fees, stablecoin supply and ratio; one-day lag; 28-day
  z-scores and one-day changes. Sets D0, DF, DA; targets T1, R7, V7.
- Stage 2 (hourly): own pass over transactions, token transfers (USDT, USDC, DAI) and
  blocks, 2017-01-01 → 2026-10-11; exchange entities = 4,961 labels plus causally
  inferred deposit addresses; 15 hourly series, 32 features. Sets H0, HE, HS, HA;
  targets R1, R6, R24, V6, V24.
- 42 comparisons, one screen, ≤ 3 selected, one holdout (`gates.json`).

## Disclosures

- Exchange labels are a 2026 snapshot applied to all years (look-ahead in coverage).
- Coin Metrics exchange history reflects its current labels (revised history).
- ETH moved inside contracts (`traces`) is not read; contract-based deposit forwarders
  are detected only when they move stablecoins.
- Four earlier studies used ETH 2017–2024 (M2, B2, B3, now B4); the sealed window
  2025-01-01 → 2026-10-12 has never been read. If B4 opens it, it is spent for later
  ETH studies.
- An arXiv study (2411.06327) motivated the design; its claims are not assumed.
```

`research/onchain-b4-2026-10-15/STATE.md`:

```markdown
# Branch B4 state

2026-10-15 — Registered (charter, config, gates). No B4 data read yet.

Next safe action: implement plan tasks 2–8; then fetch hourly market and Coin Metrics
data (B4-CP1), run the chain pass (B4-CP2), screen and commit the selection (B4-CP3),
holdout only for a non-empty committed selection (B4-CP4).
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_config.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b4 tests/research/onchain_b4 research/onchain-b4-2026-10-15
git commit -m "feat(onchain-b4): register exchange-flow study and frozen config

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Hourly market and Coin Metrics data with sealing

**Files:**
- Create: `tradingagents/research/onchain_b4/hourmarket.py`, `tradingagents/research/onchain_b4/cmdaily.py`
- Test: `tests/research/onchain_b4/test_markets.py`

**Interfaces:**
- Consumes: `onchain_b2.market.http_get(url)`.
- Produces: `hourmarket.fetch(get, symbol, start, end) -> (dict[str hour_iso, (close, qvol)], list[bytes])`; `hourmarket.store(bars, pages, out_dir, cutoff_hour) -> dict`; `hourmarket.load_dev(path, cutoff_hour) -> DataFrame[close, qvol]`; `hourmarket.load_all(dev_path, sealed_path) -> DataFrame`; `cmdaily.fetch(get, assets, metrics, start, end) -> (dict, list[bytes])`; `cmdaily.to_frame(data, eth_metrics, stables) -> DataFrame`; `cmdaily.store(frame, pages, out_dir, cutoff) -> dict`; `cmdaily.load_dev(path, cutoff) -> DataFrame`; `cmdaily.load_all(dev_path, sealed_path) -> DataFrame`. Hour keys are `YYYY-MM-DDTHH` (bar open, UTC); frames are indexed by naive UTC timestamps.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b4/test_markets.py
import json

import pandas as pd
import pytest

from tradingagents.research.onchain_b4 import cmdaily, hourmarket


def _binance(last):
    stop = int(pd.Timestamp(last, tz='UTC').timestamp() * 1000)

    def get(url):
        ms = int(url.split('startTime=')[1].split('&')[0])
        rows = [[t, '0', '0', '0', str(1000 + t / 3.6e9), '0', 0, '5', 0, '0', '0', '0']
                for t in range(ms, min(stop, ms + 1000 * 3_600_000), 3_600_000)]
        return json.dumps(rows).encode()
    return get


def test_hourly_fetch_pages_store_and_seal(tmp_path):
    bars, pages = hourmarket.fetch(_binance('2025-01-03 00:00'), 'ETHUSDT', '2024-11-01', '2025-01-05')
    assert len(bars) == 63 * 24 and len(pages) == 2
    meta = hourmarket.store(bars, pages, tmp_path, '2024-12-31T23')
    assert meta['dev_hours'] == 61 * 24 and meta['sealed_hours'] == 48
    dev = hourmarket.load_dev(tmp_path / 'market' / 'hourly_dev.json', '2024-12-31T23')
    assert dev.index.max() == pd.Timestamp('2024-12-31 23:00') and list(dev.columns) == ['close', 'qvol']
    both = hourmarket.load_all(tmp_path / 'market' / 'hourly_dev.json', tmp_path / 'sealed' / 'hourly_sealed.json')
    assert len(both) == 63 * 24 and both.index.is_monotonic_increasing
    (tmp_path / 'bad.json').write_text(json.dumps({'2025-01-01T00': [1.0, 1.0]}))
    with pytest.raises(ValueError, match='sealed'):
        hourmarket.load_dev(tmp_path / 'bad.json', '2024-12-31T23')


def _cm():
    days = pd.date_range('2024-12-25', '2025-01-05', freq='D')

    def get(url):
        assets = url.split('assets=')[1].split('&')[0].split(',')
        metrics = url.split('metrics=')[1].split('&')[0].split(',')
        page = 2 if 'page=2' in url else 1
        part = days[:6] if page == 1 else days[6:]
        data = [{'asset': a, 'time': d.strftime('%Y-%m-%dT00:00:00.000000000Z'),
                 **{m: str(float(i + 1)) for m in metrics}} for a in assets for i, d in enumerate(part)]
        doc = {'data': data}
        if page == 1:
            doc['next_page_url'] = url + '&page=2'
        return json.dumps(doc).encode()
    return get


def test_coinmetrics_fetch_frame_store_and_seal(tmp_path):
    eth, p1 = cmdaily.fetch(_cm(), ['eth'], ['FlowInExNtv', 'SplyExNtv'], '2024-12-25', '2025-01-05')
    st, p2 = cmdaily.fetch(_cm(), ['usdt', 'usdc'], ['SplyCur'], '2024-12-25', '2025-01-05')
    assert len(p1) == 2 and len(eth['eth']['FlowInExNtv']) == 12
    frame = cmdaily.to_frame({**eth, **st}, ['FlowInExNtv', 'SplyExNtv'], ['usdt', 'usdc', 'dai'])
    assert list(frame.columns) == ['FlowInExNtv', 'SplyExNtv', 'usdt', 'usdc', 'dai'] and frame['dai'].isna().all()
    meta = cmdaily.store(frame, p1 + p2, tmp_path, '2024-12-31')
    assert meta['dev_days'] == 7 and meta['sealed_days'] == 5
    dev = cmdaily.load_dev(tmp_path / 'market' / 'cm_dev.json', '2024-12-31')
    assert dev.index.max() == pd.Timestamp('2024-12-31')
    both = cmdaily.load_all(tmp_path / 'market' / 'cm_dev.json', tmp_path / 'sealed' / 'cm_sealed.json')
    assert len(both) == 12
    with pytest.raises(ValueError, match='sealed'):
        cmdaily.load_dev(tmp_path / 'sealed' / 'cm_sealed.json', '2024-12-31')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_markets.py -q`
Expected: FAIL with `ImportError: cannot import name 'cmdaily'`

- [ ] **Step 3: Implement both modules**

```python
# tradingagents/research/onchain_b4/hourmarket.py
"""Binance ETHUSDT 1-hour bars (spec §4.5): close and quote volume per bar-open hour (UTC).
Hours after the development cutoff are written only to the sealed directory."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

URL = 'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&startTime={ms}&limit=1000'
HOUR_MS = 3_600_000


def _ms(ts):
    return int(pd.Timestamp(ts, tz='UTC').timestamp() * 1000)


def _iso(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime('%Y-%m-%dT%H')


def fetch(get, symbol, start, end):
    ms, stop = _ms(start), _ms(end)
    bars, pages = {}, []
    while ms < stop:
        raw = get(URL.format(symbol=symbol, ms=ms))
        pages.append(raw)
        rows = json.loads(raw)
        for k in rows:
            if k[0] < stop:
                bars[_iso(k[0])] = (float(k[4]), float(k[7]))
        if len(rows) < 1000:
            break
        ms = rows[-1][0] + HOUR_MS
    return bars, pages


def store(bars, pages, out_dir, cutoff_hour):
    out_dir = Path(out_dir)
    (out_dir / 'market').mkdir(parents=True, exist_ok=True)
    (out_dir / 'sealed' / 'raw').mkdir(parents=True, exist_ok=True)
    dev = {h: v for h, v in sorted(bars.items()) if h <= cutoff_hour}
    sealed = {h: v for h, v in sorted(bars.items()) if h > cutoff_hour}
    (out_dir / 'market' / 'hourly_dev.json').write_text(json.dumps(dev))
    (out_dir / 'sealed' / 'hourly_sealed.json').write_text(json.dumps(sealed))
    for raw in pages:              # raw pages span both windows, so they stay sealed
        (out_dir / 'sealed' / 'raw' / f'binance-{hashlib.sha256(raw).hexdigest()}.json').write_bytes(raw)
    meta = {'cutoff_hour': cutoff_hour, 'dev_hours': len(dev), 'sealed_hours': len(sealed), 'pages': len(pages)}
    (out_dir / 'market' / 'hourly_meta.json').write_text(json.dumps(meta, indent=1))
    return meta


def _frame(doc):
    idx = pd.to_datetime(list(doc), format='%Y-%m-%dT%H')
    vals = list(doc.values())
    return pd.DataFrame({'close': [float(v[0]) for v in vals], 'qvol': [float(v[1]) for v in vals]},
                        index=idx).sort_index()


def load_dev(path, cutoff_hour):
    df = _frame(json.loads(Path(path).read_text()))
    if len(df) and df.index.max() > pd.to_datetime(cutoff_hour, format='%Y-%m-%dT%H'):
        raise ValueError('development hourly file contains sealed hours')
    return df


def load_all(dev_path, sealed_path):
    return pd.concat([_frame(json.loads(Path(dev_path).read_text())),
                      _frame(json.loads(Path(sealed_path).read_text()))]).sort_index()
```

```python
# tradingagents/research/onchain_b4/cmdaily.py
"""Coin Metrics community daily metrics (spec §5.1). Dates after the development cutoff are
written only to the sealed directory: MVRV and the stablecoin ratio carry the price."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

URL = ('https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets={assets}&metrics={metrics}'
       '&frequency=1d&start_time={start}&end_time={end}&page_size=10000&paging_from=start')


def fetch(get, assets, metrics, start, end):
    url = URL.format(assets=','.join(assets), metrics=','.join(metrics), start=start, end=end)
    out, pages = {}, []
    while url:
        raw = get(url)
        pages.append(raw)
        doc = json.loads(raw)
        for r in doc['data']:
            for m in metrics:
                if r.get(m) is not None:
                    out.setdefault(r['asset'], {}).setdefault(m, {})[r['time'][:10]] = float(r[m])
        url = doc.get('next_page_url')
    return out, pages


def _frame(cols):
    df = pd.DataFrame({c: pd.Series({pd.Timestamp(d): v for d, v in s.items()}, dtype=float) for c, s in cols.items()})
    return df.sort_index()


def to_frame(data, eth_metrics, stables):
    cols = {m: data.get('eth', {}).get(m, {}) for m in eth_metrics}
    cols.update({a: data.get(a, {}).get('SplyCur', {}) for a in stables})
    return _frame(cols)


def _doc(frame):
    return {c: {d.strftime('%Y-%m-%d'): float(v) for d, v in frame[c].dropna().items()} for c in frame.columns}


def store(frame, pages, out_dir, cutoff):
    out_dir, cut = Path(out_dir), pd.Timestamp(cutoff)
    (out_dir / 'market').mkdir(parents=True, exist_ok=True)
    (out_dir / 'sealed' / 'raw').mkdir(parents=True, exist_ok=True)
    dev, sealed = frame[frame.index <= cut], frame[frame.index > cut]
    (out_dir / 'market' / 'cm_dev.json').write_text(json.dumps(_doc(dev)))
    (out_dir / 'sealed' / 'cm_sealed.json').write_text(json.dumps(_doc(sealed)))
    for raw in pages:
        (out_dir / 'sealed' / 'raw' / f'cm-{hashlib.sha256(raw).hexdigest()}.json').write_bytes(raw)
    meta = {'cutoff': str(cut.date()), 'dev_days': len(dev), 'sealed_days': len(sealed), 'columns': list(frame.columns)}
    (out_dir / 'market' / 'cm_meta.json').write_text(json.dumps(meta, indent=1))
    return meta


def load_dev(path, cutoff):
    df = _frame(json.loads(Path(path).read_text()))
    if len(df) and df.index.max() > pd.Timestamp(cutoff):
        raise ValueError('development Coin Metrics file contains sealed dates')
    return df


def load_all(dev_path, sealed_path):
    return pd.concat([_frame(json.loads(Path(dev_path).read_text())),
                      _frame(json.loads(Path(sealed_path).read_text()))]).sort_index()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_markets.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b4/hourmarket.py tradingagents/research/onchain_b4/cmdaily.py tests/research/onchain_b4/test_markets.py
git commit -m "feat(onchain-b4): hourly Binance bars and Coin Metrics daily metrics with sealing

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Day reader (three tables, unpadding, admission, retries)

**Files:**
- Create: `tradingagents/research/onchain_b4/reader.py`
- Test: `tests/research/onchain_b4/test_reader.py`

**Interfaces:**
- Consumes: `onchain_b2.s3source.DayUnavailable(day, errors)`, `onchain_b2.s3source.check_timestamps(table, day)`, `onchain_b3.history._LUT`.
- Produces: `reader.addr_keys(addresses) -> np.ndarray[uint64]` (one key per input, not unique); `reader.Day` dataclass with arrays `src, dst` (uint64), `asset` (int8: 0 ETH, 1 stable), `amount` (float64: ETH or USD), `ts` (int64 seconds), `block` (int64), `tx_ts` (int64), `tx_gwei` (float64), `blk_ts` (int64), `blk_gas` (float64), `blk_txs` (float64), `rows` (dict); `reader.read_day(day, *, filesystem, root, tokens, retries, sleep=time.sleep) -> Day`; `reader.TABLES`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b4/test_reader.py
import numpy as np
import pyarrow as pa
import pyarrow.fs as pafs
import pyarrow.parquet as pq
import pytest

from tradingagents.research.onchain_b2.s3source import DayUnavailable
from tradingagents.research.onchain_b4 import config, reader

A, B, C, D = ('0x' + c * 40 for c in 'abcd')
USDT, USDC, DAI = (k for k in config.load()['tokens'])
X = '0x' + '9' * 40
pad = lambda a: '0x' + '0' * 24 + a[2:]
TS = lambda h: np.datetime64('2025-06-02T00:00:00', 'ns') + np.timedelta64(h, 'h')


def _write(root, table, day, t):
    d = root / 'v1.0' / 'eth' / table / f'date={day}'
    d.mkdir(parents=True)
    pq.write_table(t, d / 'part-0.parquet')


def _fixture(root, day='2025-06-02'):
    _write(root, 'transactions', day, pa.table({
        'from_address': [A, A, C, B, D], 'to_address': [B, B, None, B, A],
        'value': [1e18, 0.0, 1e18, 1e18, 2e18], 'receipt_status': [1, 1, 1, 1, 0],
        'gas_price': pa.array([10_000_000_000, 30_000_000_000, 5_000_000_000, 5_000_000_000, 5_000_000_000], pa.int64()),
        'receipt_effective_gas_price': pa.array([None, 20_000_000_000, 5_000_000_000, 5_000_000_000, 5_000_000_000], pa.int64()),
        'block_number': [10, 11, 11, 12, 12], 'block_timestamp': pa.array([TS(1), TS(2), TS(2), TS(3), TS(3)], pa.timestamp('ns'))}))
    _write(root, 'token_transfers', day, pa.table({
        'token_address': [USDT, DAI, X, USDC, USDC],
        'from_address': [pad(A), pad(C), pad(A), pad('0x' + '0' * 40), B],
        'to_address': [pad(B), pad(D), pad(B), pad(A), C],
        'value': [5e6, 3e18, 1.0, 9e6, 2e6], 'block_number': [10, 11, 11, 12, 13],
        'block_timestamp': pa.array([TS(1), TS(2), TS(2), TS(3), TS(4)], pa.timestamp('ns'))}))
    _write(root, 'blocks', day, pa.table({
        'timestamp': pa.array([TS(1), TS(1), TS(5)], pa.timestamp('ns')), 'gas_used': [100, 200, 50],
        'transaction_count': [3, 4, 1]}))


def test_addr_keys_match_b3_rule_and_keep_order():
    k = reader.addr_keys(np.array([B, A, B], object))
    assert k.dtype == np.uint64 and k[0] == k[2] and k[1] == np.uint64(0xaaaaaaaaaaaaaaaa)


def test_reader_old_formats_and_nulls(tmp_path):
    _fixture(tmp_path)
    d = reader.read_day('2025-06-02', filesystem=pafs.LocalFileSystem(), root=str(tmp_path),
                        tokens=config.load()['tokens'], retries=[])
    key = lambda a: reader.addr_keys(np.array([a], object))[0]
    pairs = sorted(zip(d.src.tolist(), d.dst.tolist(), d.asset.tolist(), np.round(d.amount, 6).tolist()))
    assert pairs == sorted([(key(A), key(B), 0, 1.0), (key(A), key(B), 1, 5.0), (key(C), key(D), 1, 3.0), (key(B), key(C), 1, 2.0)])
    assert sorted(d.tx_gwei.tolist()) == [5.0, 5.0, 10.0, 20.0]          # failed tx excluded; null effective -> gas_price
    assert d.blk_gas.sum() == 350 and d.blk_txs.sum() == 8 and set(d.blk_ts.tolist()) == {TS(1).astype('int64') // 10**9, TS(5).astype('int64') // 10**9}
    assert d.ts.dtype == np.int64 and d.block.dtype == np.int64


def test_missing_day_retries_then_unavailable(tmp_path):
    slept = []
    with pytest.raises(DayUnavailable):
        reader.read_day('2025-06-03', filesystem=pafs.LocalFileSystem(), root=str(tmp_path),
                        tokens=config.load()['tokens'], retries=[1, 2], sleep=slept.append)
    assert slept == [1, 2]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_reader.py -q`
Expected: FAIL with `ImportError: cannot import name 'reader'`

- [ ] **Step 3: Implement the reader**

```python
# tradingagents/research/onchain_b4/reader.py
"""One UTC day of the public ETH tables (spec §4.1): admitted ETH and stablecoin transfers as
64-bit address keys, paid gas prices of successful transactions, and block gas. Nothing raw is
written to disk."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.fs as pafs
import pyarrow.parquet as pq

from ..onchain_b2.s3source import DayUnavailable, check_timestamps
from ..onchain_b3.history import _LUT

ZERO = '0x' + '0' * 40
TABLES = {
    'transactions': ['from_address', 'to_address', 'value', 'receipt_status', 'gas_price',
                     'receipt_effective_gas_price', 'block_number', 'block_timestamp'],
    'token_transfers': ['token_address', 'from_address', 'to_address', 'value', 'block_number', 'block_timestamp'],
    'blocks': ['timestamp', 'gas_used', 'transaction_count'],
}
_SHIFTS = np.arange(60, -1, -4, dtype=np.uint64)


@dataclass
class Day:
    src: np.ndarray
    dst: np.ndarray
    asset: np.ndarray
    amount: np.ndarray
    ts: np.ndarray
    block: np.ndarray
    tx_ts: np.ndarray
    tx_gwei: np.ndarray
    blk_ts: np.ndarray
    blk_gas: np.ndarray
    blk_txs: np.ndarray
    rows: dict = field(default_factory=dict)


def addr_keys(addresses):
    a = np.asarray(addresses).astype('S42')
    if len(a) == 0:
        return np.empty(0, np.uint64)
    nib = _LUT[a.view(np.uint8).reshape(-1, 42)[:, 2:18]]
    return np.bitwise_or.reduce(nib << _SHIFTS, axis=1)


def _arr(col):
    return col.combine_chunks() if isinstance(col, pa.ChunkedArray) else col


def _strs(col):
    return _arr(col).to_numpy(zero_copy_only=False)


def _floats(col):
    return _arr(col).cast(pa.float64()).to_numpy(zero_copy_only=False)


def _ints(col):
    return _arr(col).cast(pa.int64()).to_numpy(zero_copy_only=False)


def _secs(col):
    return _arr(col).cast(pa.int64()).to_numpy(zero_copy_only=False) // 1_000_000_000


def _unpad(col):
    a = pc.utf8_lower(_arr(col))
    return pc.if_else(pc.equal(pc.utf8_length(a), 66), pc.utf8_replace_slice(a, 0, 26, '0x'), a)


def admit(tx, tt, blocks, tokens):
    tx = tx.filter(pc.equal(_arr(tx['receipt_status']), 1))
    paid = pc.coalesce(_arr(tx['receipt_effective_gas_price']), _arr(tx['gas_price']))
    frm_e, to_e = _arr(tx['from_address']), _arr(tx['to_address'])
    keep_e = pc.and_(pc.and_(pc.greater(_arr(tx['value']), 0.0), pc.is_valid(to_e)), pc.not_equal(frm_e, to_e))
    e = tx.filter(keep_e)
    tt = tt.filter(pc.is_in(_arr(tt['token_address']), value_set=pa.array(sorted(tokens))))
    frm, to = _unpad(tt['from_address']), _unpad(tt['to_address'])
    keep = pc.and_(pc.and_(pc.greater(_arr(tt['value']), 0.0), pc.not_equal(frm, to)),
                   pc.and_(pc.not_equal(frm, ZERO), pc.not_equal(to, ZERO)))
    tt, frm, to = tt.filter(keep), pc.filter(frm, keep), pc.filter(to, keep)
    tok, raw = _strs(tt['token_address']), _floats(tt['value'])
    amt = np.zeros(len(raw))
    for addr, meta in tokens.items():
        m = tok == addr
        amt[m] = raw[m] / 10.0 ** meta['decimals']
    n_e, n_t = e.num_rows, tt.num_rows
    return Day(src=np.concatenate([addr_keys(_strs(e['from_address'])), addr_keys(_strs(frm))]),
               dst=np.concatenate([addr_keys(_strs(e['to_address'])), addr_keys(_strs(to))]),
               asset=np.concatenate([np.zeros(n_e, np.int8), np.ones(n_t, np.int8)]),
               amount=np.concatenate([_floats(e['value']) / 1e18, amt]),
               ts=np.concatenate([_secs(e['block_timestamp']), _secs(tt['block_timestamp'])]).astype(np.int64),
               block=np.concatenate([_ints(e['block_number']), _ints(tt['block_number'])]).astype(np.int64),
               tx_ts=_secs(tx['block_timestamp']).astype(np.int64), tx_gwei=_floats(paid) / 1e9,
               blk_ts=_secs(blocks['timestamp']).astype(np.int64), blk_gas=_floats(blocks['gas_used']),
               blk_txs=_floats(blocks['transaction_count']),
               rows={'transactions_ok': tx.num_rows, 'eth_transfers': n_e, 'stable_transfers': n_t,
                     'blocks': blocks.num_rows})


def _read_table(filesystem, root, table, day):
    sel = pafs.FileSelector(f'{root}/v1.0/eth/{table}/date={day}')
    infos = sorted((f for f in filesystem.get_file_info(sel) if f.path.endswith('.parquet')), key=lambda f: f.path)
    if not infos:
        raise FileNotFoundError(f'no {table} parts for {day}')
    parts = []
    for info in infos:
        with filesystem.open_input_file(info.path) as fh:
            parts.append(pq.ParquetFile(fh).read(columns=TABLES[table]))
    return pa.concat_tables(parts)


def read_day(day, *, filesystem, root, tokens, retries, sleep=time.sleep):
    errors = []
    for attempt in range(len(retries) + 1):
        try:
            t = {name: _read_table(filesystem, root, name, day) for name in TABLES}
            check_timestamps(t['transactions'], day)
            check_timestamps(t['token_transfers'], day)
            check_timestamps(t['blocks'].rename_columns(['block_timestamp', 'gas_used', 'transaction_count']), day)
            return admit(t['transactions'], t['token_transfers'], t['blocks'], tokens)
        except Exception as e:        # network, decode or integrity failure: retry, then mark unavailable
            errors.append(repr(e))
            if attempt < len(retries):
                sleep(retries[attempt])
    raise DayUnavailable(day, errors)
```


- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_reader.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b4/reader.py tests/research/onchain_b4/test_reader.py
git commit -m "feat(onchain-b4): day reader for transactions, stablecoin transfers and blocks

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Exchange entities (causal deposit inference, snapshots)

**Files:**
- Create: `tradingagents/research/onchain_b4/entities.py`
- Test: `tests/research/onchain_b4/test_entities.py`

**Interfaces:**
- Consumes: `onchain_b3.history.Bloom(log2_bits, hashes)` with `.bits`, `.log2`, `.k`, `.add`, `.contains`.
- Produces: `entities.member(sorted_keys, keys) -> bool array`; `entities.Entities(labels, log2_bits, hashes, share)` with `.is_exchange(keys)`, `.is_labelled(keys)`, `.update(src, dst, block, day)`, `.save(path)`, `Entities.load(path)`, attributes `labels, c_keys, c_out, c_lab, deposits, last_day`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b4/test_entities.py
import numpy as np

from tradingagents.research.onchain_b4.entities import Entities, member

u = lambda *x: np.array(x, np.uint64)
L = 100


def _ent():
    return Entities(u(L), 16, 5, 0.9)


def test_first_send_to_label_becomes_deposit_next_day():
    e = _ent()
    # X=1 first sends to L; Y=2 first sends to 3, later (block 9) to L; L itself sends to 4
    e.update(u(1, 2, 2, L), u(L, 3, L, 4), np.array([5, 5, 9, 5]), '2017-01-01')
    assert e.deposits.tolist() == [1] and e.c_keys.tolist() == [1]
    assert e.is_exchange(u(1, 2, L, 4)).tolist() == [True, False, True, False]
    assert e.is_labelled(u(1, L)).tolist() == [False, True]


def test_seen_sender_never_joins_and_share_drop_leaves():
    e = _ent()
    e.update(u(1, 4), u(L, 3), np.array([1, 1]), '2017-01-01')      # 4 seen as a sender
    e.update(u(4, 1, 1), u(L, 3, 3), np.array([2, 2, 3]), '2017-01-02')
    assert 4 not in e.c_keys.tolist()                                 # previously seen sender
    assert e.c_out.tolist() == [3] and e.c_lab.tolist() == [1] and e.deposits.tolist() == []


def test_update_with_no_transfers():
    e = _ent()
    e.update(u(), u(), np.array([], np.int64), '2017-01-01')
    assert e.deposits.size == 0 and e.last_day == '2017-01-01'


def test_snapshot_round_trip(tmp_path):
    e = _ent()
    e.update(u(1, 5), u(L, L), np.array([1, 1]), '2017-01-01')
    e.save(tmp_path / 'state' / 'entities.npz')
    f = Entities.load(tmp_path / 'state' / 'entities.npz')
    assert f.last_day == '2017-01-01' and f.deposits.tolist() == [1, 5] and np.array_equal(f.bloom.bits, e.bloom.bits)
    for x in (e, f):
        x.update(u(6, 1), u(L, 7), np.array([1, 1]), '2017-01-02')
    assert np.array_equal(e.c_keys, f.c_keys) and np.array_equal(e.deposits, f.deposits)
    assert member(u(1, 6, 9), u(9)).tolist() == [True]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_entities.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.research.onchain_b4.entities'`

- [ ] **Step 3: Implement entities**

```python
# tradingagents/research/onchain_b4/entities.py
"""Exchange entities (spec §4.2): labelled addresses plus deposit addresses learned causally.
An address joins the candidate table on the day of its first observed send if it was never seen
sending before and its earliest block of sends that day includes a transfer to a label; it is a
deposit address from the next day while at least `share` of its outgoing transfers go to labels."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from ..onchain_b3.history import Bloom


def member(sorted_keys, keys):
    keys = np.asarray(keys, np.uint64)
    if len(sorted_keys) == 0 or len(keys) == 0:
        return np.zeros(len(keys), bool)
    pos = np.searchsorted(sorted_keys, keys)
    pos[pos == len(sorted_keys)] = 0
    return sorted_keys[pos] == keys


class Entities:
    def __init__(self, labels, log2_bits, hashes, share):
        self.labels = np.unique(np.asarray(labels, np.uint64))
        self.bloom = Bloom(log2_bits, hashes)
        self.share = float(share)
        self.c_keys = np.empty(0, np.uint64)
        self.c_out = np.empty(0, np.uint32)
        self.c_lab = np.empty(0, np.uint32)
        self.deposits = np.empty(0, np.uint64)
        self.last_day = None

    def is_labelled(self, keys):
        return member(self.labels, keys)

    def is_exchange(self, keys):
        return member(self.labels, keys) | member(self.deposits, keys)

    def update(self, src, dst, block, day):
        src, dst, block = np.asarray(src, np.uint64), np.asarray(dst, np.uint64), np.asarray(block, np.int64)
        keep = ~member(self.labels, src)
        s, b, lab = src[keep], block[keep], member(self.labels, dst[keep])
        if len(s):
            order = np.lexsort((b, s))
            s, b, lab = s[order], b[order], lab[order]
            uniq, first, counts = np.unique(s, return_index=True, return_counts=True)
            n_lab = np.add.reduceat(lab.astype(np.uint32), first).astype(np.uint32)
            earliest = np.repeat(b[first], counts)
            first_lab = np.add.reduceat(((b == earliest) & lab).astype(np.uint32), first) > 0
            known = member(self.c_keys, uniq)
            pos = np.searchsorted(self.c_keys, uniq[known])
            self.c_out[pos] += counts[known].astype(np.uint32)
            self.c_lab[pos] += n_lab[known]
            new = ~known & first_lab & ~self.bloom.contains(uniq)
            if new.any():
                at = np.searchsorted(self.c_keys, uniq[new])
                self.c_keys = np.insert(self.c_keys, at, uniq[new])
                self.c_out = np.insert(self.c_out, at, counts[new].astype(np.uint32))
                self.c_lab = np.insert(self.c_lab, at, n_lab[new])
        if len(src):
            self.bloom.add(np.unique(src))
        ok = (self.c_lab >= 1) & (self.c_lab.astype(np.float64) >= self.share * self.c_out)
        self.deposits = self.c_keys[ok]
        self.last_day = day

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.stem + '.tmp.npz')
        np.savez(tmp, labels=self.labels, bits=self.bloom.bits, bloom=np.array([self.bloom.log2, self.bloom.k]),
                 share=np.array([self.share]), c_keys=self.c_keys, c_out=self.c_out, c_lab=self.c_lab,
                 last_day=np.array([self.last_day or '']))
        os.replace(tmp, path)

    @classmethod
    def load(cls, path):
        z = np.load(path)
        e = cls(z['labels'], int(z['bloom'][0]), int(z['bloom'][1]), float(z['share'][0]))
        e.bloom.bits = z['bits'].copy()
        e.c_keys, e.c_out, e.c_lab = z['c_keys'].copy(), z['c_out'].copy(), z['c_lab'].copy()
        ok = (e.c_lab >= 1) & (e.c_lab.astype(np.float64) >= e.share * e.c_out)
        e.deposits = e.c_keys[ok]
        e.last_day = str(z['last_day'][0]) or None
        return e
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_entities.py -q`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b4/entities.py tests/research/onchain_b4/test_entities.py
git commit -m "feat(onchain-b4): causal exchange entities with deposit inference and snapshots

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Hourly flows for one day

**Files:**
- Create: `tradingagents/research/onchain_b4/flows.py`
- Test: `tests/research/onchain_b4/test_flows.py`

**Interfaces:**
- Consumes: `reader.Day`; `Entities.is_exchange`, `Entities.is_labelled`.
- Produces: `flows.SERIES` (15 names), `flows.FLOW` (first 10), `flows.LAB` (`lab_` + FLOW); `flows.hourly(day, d, is_ex, is_lab, cfg_flows) -> DataFrame` (24 rows, naive UTC hourly index, columns SERIES + LAB).

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b4/test_flows.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b4 import flows
from tradingagents.research.onchain_b4.entities import member
from tradingagents.research.onchain_b4.reader import Day

U, X, Q, L = 1, 2, 3, 100           # user, known deposit, new deposit, label
T0 = int(pd.Timestamp('2025-06-02').timestamp())
h = lambda k: T0 + 3600 * k + 5


def _day():
    rows = [(U, X, 0, 150.0, 3), (X, L, 0, 150.0, 4), (L, X, 0, 0.01, 4), (L, U, 0, 2.0, 5),
            (U, L, 1, 2e6, 6), (U, Q, 0, 1.0, 1), (Q, L, 0, 1.0, 2)]
    a = np.array(rows, dtype=object)
    return Day(src=np.array(a[:, 0], np.uint64), dst=np.array(a[:, 1], np.uint64), asset=np.array(a[:, 2], np.int8),
               amount=np.array(a[:, 3], float), ts=np.array([h(k) for k in a[:, 4]], np.int64),
               block=np.arange(len(rows), dtype=np.int64),
               tx_ts=np.array([h(0), h(0), h(0), h(7)], np.int64), tx_gwei=np.array([1.0, 3.0, np.nan, 9.0]),
               blk_ts=np.array([h(0), h(0)], np.int64), blk_gas=np.array([10.0, 20.0]), blk_txs=np.array([2.0, 3.0]))


def test_hourly_flows_entities_and_labels_only():
    ex = lambda k: member(np.array([X, L], np.uint64), k)
    lab = lambda k: member(np.array([L], np.uint64), k)
    r = flows.hourly('2025-06-02', _day(), ex, lab, {'large_eth': 100.0, 'large_usd': 1e6})
    assert len(r) == 24 and list(r.columns) == flows.SERIES + flows.LAB and r.index[0] == pd.Timestamp('2025-06-02')
    r = r.reset_index(drop=True)
    assert r['eth_in_val'][3] == 150.0 and r['eth_big_in'][3] == 1 and r['eth_in_val'][4] == 0.0     # sweep internal
    assert r['eth_out_val'][4] == 0.0 and r['eth_out_val'][5] == 2.0                                   # top-up internal
    assert r['eth_in_val'][1] == 0.0 and r['eth_in_val'][2] == 1.0                                     # new deposit: once, at sweep
    assert r['stable_in_val'][6] == 2e6 and r['stable_big_in'][6] == 1 and r['stable_in_cnt'][6] == 1
    assert r['lab_eth_in_val'][3] == 0.0 and r['lab_eth_in_val'][4] == 150.0 and r['lab_eth_out_cnt'][4] == 1
    assert r['act_gas_price'][0] == 2.0 and r['act_gas_price'][7] == 9.0 and r['act_gas_price'][1] == 0.0
    assert r['act_gas_used'][0] == 30.0 and r['act_tx_count'][0] == 5.0
    assert r['act_eth_transfers'].sum() == 6 and r['act_eth_value'][3] == 150.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_flows.py -q`
Expected: FAIL with `ImportError: cannot import name 'flows'`

- [ ] **Step 3: Implement flows**

```python
# tradingagents/research/onchain_b4/flows.py
"""One day of admitted transfers -> 24 hourly rows (spec §4.3). Inflow = non-exchange to exchange,
outflow = exchange to non-exchange; transfers inside the exchange set are excluded. The same flows
are computed with labels only (`lab_` prefix) for exploration."""
from __future__ import annotations

import numpy as np
import pandas as pd

FLOW = ['eth_in_val', 'eth_out_val', 'eth_in_cnt', 'eth_out_cnt', 'eth_big_in',
        'stable_in_val', 'stable_out_val', 'stable_in_cnt', 'stable_out_cnt', 'stable_big_in']
SERIES = FLOW + ['act_gas_price', 'act_gas_used', 'act_tx_count', 'act_eth_transfers', 'act_eth_value']
LAB = ['lab_' + s for s in FLOW]


def _hours(ts, start):
    return ((np.asarray(ts, np.int64) - start) // 3600).astype(np.int64)


def _count(idx):
    return np.bincount(idx, minlength=24).astype(float)


def hourly(day, d, is_ex, is_lab, cfg_flows):
    start = int(pd.Timestamp(day).timestamp())
    hr = _hours(d.ts, start)
    out = {}
    for prefix, ex in (('', is_ex), ('lab_', is_lab)):
        se, de = ex(d.src), ex(d.dst)
        inflow, outflow = ~se & de, se & ~de
        for code, name, big in ((0, 'eth', cfg_flows['large_eth']), (1, 'stable', cfg_flows['large_usd'])):
            a = d.asset == code
            i, o = inflow & a, outflow & a
            out[f'{prefix}{name}_in_val'] = np.bincount(hr[i], weights=d.amount[i], minlength=24)
            out[f'{prefix}{name}_out_val'] = np.bincount(hr[o], weights=d.amount[o], minlength=24)
            out[f'{prefix}{name}_in_cnt'] = _count(hr[i])
            out[f'{prefix}{name}_out_cnt'] = _count(hr[o])
            out[f'{prefix}{name}_big_in'] = _count(hr[i & (d.amount >= big)])
    eth = d.asset == 0
    out['act_eth_transfers'] = _count(hr[eth])
    out['act_eth_value'] = np.bincount(hr[eth], weights=d.amount[eth], minlength=24)
    th = _hours(d.tx_ts, start)
    gas = []
    for k in range(24):
        v = d.tx_gwei[(th == k) & ~np.isnan(d.tx_gwei)]
        gas.append(float(np.median(v)) if len(v) else 0.0)
    out['act_gas_price'] = np.array(gas)
    bh = _hours(d.blk_ts, start)
    out['act_gas_used'] = np.bincount(bh, weights=d.blk_gas, minlength=24)
    out['act_tx_count'] = np.bincount(bh, weights=d.blk_txs, minlength=24)
    return pd.DataFrame(out, index=pd.date_range(day, periods=24, freq='h'))[SERIES + LAB]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_flows.py -q`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b4/flows.py tests/research/onchain_b4/test_flows.py
git commit -m "feat(onchain-b4): hourly exchange flows, gas and activity for one day

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Dataset (hourly and daily transforms, targets, windows, samples)

**Files:**
- Create: `tradingagents/research/onchain_b4/dataset4.py`
- Test: `tests/research/onchain_b4/test_dataset4.py`

**Interfaces:**
- Consumes: `flows.SERIES`, `flows.LAB`; `onchain_b2.targets.f0/t1/t3/t4(prices, ...)` with `{date: float}` dicts.
- Produces: `dataset4.zscore(x, window, min_periods, clip) -> Series`; `hourly_table(hours_dir, days) -> DataFrame`; `transform_hourly(raw, c) -> DataFrame`; `price_features(bars) -> DataFrame` (`h0_*`); `hourly_targets(bars) -> DataFrame` (R1, R6, R24, V6, V24); `window_mask(index, horizon_hours, unit_hours, window, cfg) -> bool array`; `hourly_samples(trans, bars, window, cfg) -> (DataFrame, dict)`; `cm_values(cm, prices) -> DataFrame` (`cmf_*`, `cmo_*`); `transform_daily(values, c) -> DataFrame`; `daily_samples(trans, prices, volumes, window, cfg) -> (DataFrame, dict)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b4/test_dataset4.py
from datetime import date, timedelta

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b4 import config, dataset4 as D, flows


def _raw(start, hours, seed=1):
    idx = pd.date_range(start, periods=hours, freq='h')
    rng = np.random.default_rng(seed)
    return pd.DataFrame({c: rng.gamma(2.0, 3.0, len(idx)) for c in flows.SERIES + flows.LAB}, index=idx)


def _bars(start, hours, seed=2):
    idx = pd.date_range(start, periods=hours, freq='h')
    rng = np.random.default_rng(seed)
    return pd.DataFrame({'close': 1000 * np.exp(np.cumsum(rng.normal(0, 0.01, len(idx)))),
                         'qvol': rng.gamma(2.0, 1e6, len(idx))}, index=idx)


def test_hourly_transforms_are_causal_and_counted():
    c = config.load()['hourly']
    raw = _raw('2024-01-01', 1500)
    a = D.transform_hourly(raw, c)
    changed = raw.copy()
    changed.iloc[1200:] *= 5
    b = D.transform_hourly(changed, c)
    pd.testing.assert_frame_equal(a.iloc[:1200], b.iloc[:1200])
    registered = [x for x in a.columns if not x.startswith('lab_')]
    assert len(registered) == 32 and a.iloc[1000:].notna().all().all()
    const = pd.Series(3.0, index=raw.index)
    assert (D.zscore(const, 168, 120, 10.0).dropna() == 0).all()


def test_price_features_and_targets():
    bars = _bars('2024-01-01', 400)
    f, t = D.price_features(bars), D.hourly_targets(bars)
    lc = np.log(bars['close'])
    h = bars.index[200]
    assert np.isclose(f.loc[h, 'h0_r24'], lc.iloc[200] - lc.iloc[176])
    assert np.isclose(t.loc[h, 'R6'], lc.iloc[206] - lc.iloc[200])
    r = lc.diff()
    assert np.isclose(t.loc[h, 'V6'], np.log(np.sqrt((r.iloc[201:207] ** 2).sum())))
    assert len([x for x in f.columns if x.startswith('h0_')]) == 8


def test_missing_bar_excludes_dependent_rows():
    bars = _bars('2024-06-01', 1200).drop(pd.Timestamp('2024-06-30 12:00'))
    cfg = config.load()
    trans = D.transform_hourly(_raw('2024-05-01', 2000), cfg['hourly'])
    s, ex = D.hourly_samples(trans, bars, 'dev', cfg)
    gap = pd.Timestamp('2024-06-30 12:00')
    assert gap not in s.index and pd.Timestamp('2024-06-30 13:00') not in s.index      # r1 needs the missing close
    assert pd.isna(s.loc[pd.Timestamp('2024-06-30 11:00'), 'R1']) and ex['features_incomplete'] > 0


def test_hourly_windows_stop_at_cutoff():
    cfg = config.load()
    bars = _bars('2024-11-01', 24 * 75)
    trans = D.transform_hourly(_raw('2024-10-01', 24 * 110), cfg['hourly'])
    dev, _ = D.hourly_samples(trans, bars[bars.index <= '2024-12-31 23:00'], 'dev', cfg)
    assert dev['R24'].last_valid_index() == pd.Timestamp('2024-12-30 23:00')
    assert dev['R1'].last_valid_index() == pd.Timestamp('2024-12-31 22:00')
    hold, _ = D.hourly_samples(trans, bars, 'holdout', cfg)
    assert hold.index.min() >= pd.Timestamp('2025-01-01')


def _cm(start, n):
    idx = pd.date_range(start, periods=n, freq='D')
    rng = np.random.default_rng(3)
    df = pd.DataFrame({m: rng.gamma(5.0, 100.0, n) for m in config.load()['cm']['eth']}, index=idx)
    for a in ('usdt', 'usdc', 'dai'):
        df[a] = rng.gamma(5.0, 1e9, n)
    return df


def test_daily_lag_and_windows():
    cfg = config.load()
    cm = _cm('2024-06-01', 214)
    prices = {(date(2024, 6, 1) + timedelta(days=k)): 1000.0 + k for k in range(214)}
    volumes = {d: 1e9 for d in prices}
    v = D.cm_values(cm, prices)
    spike = cm.copy()
    spike.loc['2024-10-01', 'FlowInExNtv'] *= 50
    a, b = D.transform_daily(v, cfg['daily']), D.transform_daily(D.cm_values(spike, prices), cfg['daily'])
    assert a.loc['2024-10-01', 'cmf_in__z28'] == b.loc['2024-10-01', 'cmf_in__z28']
    assert a.loc['2024-10-02', 'cmf_in__z28'] != b.loc['2024-10-02', 'cmf_in__z28']
    assert len(a.columns) == 20
    s, _ = D.daily_samples(a, prices, volumes, 'dev', cfg)
    assert s['R7'].last_valid_index() == pd.Timestamp('2024-12-24')
    assert s['T1'].last_valid_index() == pd.Timestamp('2024-12-30')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_dataset4.py -q`
Expected: FAIL with `ImportError: cannot import name 'dataset4'`

- [ ] **Step 3: Implement dataset4**

```python
# tradingagents/research/onchain_b4/dataset4.py
"""B4 features, targets and samples (spec §4.6–4.7, §5.2–5.3). Every feature at time t uses data
up to the end of t only; a sample enters a target only if the label window lies in its window."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2 import targets as T
from . import flows

HOURLY_FEATURES = ('h0_', 'eth_', 'stable_', 'act_')
HOURLY_TARGETS = ('R1', 'R6', 'R24', 'V6', 'V24')


def zscore(x, window, min_periods, clip):
    prev = x.shift(1)
    mean = prev.rolling(window, min_periods=min_periods).mean()
    std = prev.rolling(window, min_periods=min_periods).std(ddof=0)
    z = (x - mean) / std
    z[(std == 0) & x.notna()] = 0.0
    return z.clip(-clip, clip)


def hourly_table(hours_dir, days):
    frames = [pd.read_parquet(hours_dir / f'{d}.parquet') for d in days if (hours_dir / f'{d}.parquet').exists()]
    raw = pd.concat(frames).sort_index()
    return raw.reindex(pd.date_range(days[0], periods=24 * len(days), freq='h'))


def transform_hourly(raw, c):
    out = {}
    for name in flows.SERIES + flows.LAB:
        out[f'{name}__h1z'] = zscore(np.log1p(raw[name]), c['h1_window'], c['h1_min'], c['clip'])
        s24 = raw[name].rolling(24, min_periods=24).sum()
        out[f'{name}__d24z'] = zscore(np.log1p(s24), c['d24_window'], c['d24_min'], c['clip'])
    for prefix in ('', 'lab_'):
        for a in ('eth', 'stable'):
            i24 = raw[f'{prefix}{a}_in_val'].rolling(24, min_periods=24).sum()
            o24 = raw[f'{prefix}{a}_out_val'].rolling(24, min_periods=24).sum()
            out[f'{prefix}{a}_net24__z'] = zscore(np.log1p(i24) - np.log1p(o24), c['d24_window'], c['d24_min'], c['clip'])
    return pd.DataFrame(out, index=raw.index)


def _full(bars):
    return bars.reindex(pd.date_range(bars.index.min(), bars.index.max(), freq='h'))


def price_features(bars):
    b = _full(bars)
    lc = np.log(b['close'])
    r = lc.diff()
    f = pd.DataFrame(index=b.index)
    for k in (1, 4, 24, 168):
        f[f'h0_r{k}'] = lc - lc.shift(k)
    for k in (24, 168):
        f[f'h0_rv{k}'] = np.sqrt((r ** 2).rolling(k, min_periods=k).sum())
    v24 = b['qvol'].rolling(24, min_periods=24).sum()
    v168 = b['qvol'].rolling(168, min_periods=168).sum()
    f['h0_lvol24'] = np.log(v24)
    f['h0_volratio'] = np.log(v24 / (v168 / 7))
    return f.replace([np.inf, -np.inf], np.nan)


def hourly_targets(bars):
    b = _full(bars)
    lc = np.log(b['close'])
    r2 = lc.diff() ** 2
    t = pd.DataFrame(index=b.index)
    for k in (1, 6, 24):
        t[f'R{k}'] = lc.shift(-k) - lc
    for k in (6, 24):
        fut = r2.rolling(k, min_periods=k).sum().shift(-k)
        t[f'V{k}'] = np.log(np.sqrt(fut).clip(lower=1e-8))
    return t


def window_mask(index, horizon_hours, unit_hours, window, cfg):
    w = {k: pd.Timestamp(v) for k, v in cfg['windows'].items()}
    start, end = (w['dev_start'], w['dev_end']) if window == 'dev' else (w['holdout_start'], w['holdout_end'])
    t = pd.DatetimeIndex(index)
    return np.asarray((t >= start) & (t + pd.Timedelta(hours=horizon_hours + unit_hours) <= end + pd.Timedelta(days=1)))


def hourly_samples(trans, bars, window, cfg):
    df = trans.join(price_features(bars), how='inner').join(hourly_targets(bars), how='left')
    df = df[window_mask(df.index, 0, 1, window, cfg)]
    req = [c for c in df.columns if c.startswith(HOURLY_FEATURES)]
    ok = df[req].notna().all(axis=1)
    excluded = {'features_incomplete': int((~ok).sum())}
    df = df[ok].copy()
    for name, tc in cfg['targets'].items():
        if tc['kind'] == 'hourly':
            df.loc[~window_mask(df.index, tc['horizon_hours'], 1, window, cfg), name] = np.nan
    return df, excluded


def cm_values(cm, prices):
    idx = pd.date_range(cm.index.min(), cm.index.max(), freq='D')
    cm = cm.reindex(idx)
    p = pd.Series({pd.Timestamp(d): v for d, v in prices.items()}, dtype=float).reindex(idx)
    stable = (cm['usdt'].fillna(0) + cm['usdc'].fillna(0) + cm['dai'].fillna(0)).where(cm['usdt'].notna())
    v = pd.DataFrame(index=idx)
    v['cmf_in'] = np.log1p(cm['FlowInExNtv'])
    v['cmf_out'] = np.log1p(cm['FlowOutExNtv'])
    v['cmf_net'] = (cm['FlowInExNtv'] - cm['FlowOutExNtv']) / cm['SplyExNtv']
    v['cmf_sply_chg7'] = np.log(cm['SplyExNtv'] / cm['SplyExNtv'].shift(7))
    v['cmf_ex_share'] = cm['SplyExNtv'] / cm['SplyCur']
    v['cmo_mvrv'] = np.log(cm['CapMVRVCur'])
    v['cmo_adr'] = np.log(cm['AdrActCnt'])
    v['cmo_fee'] = np.log1p(cm['FeeTotNtv'])
    v['cmo_stable_chg7'] = np.log(stable / stable.shift(7))
    v['cmo_ssr'] = np.log(stable / (p * cm['SplyCur']))
    return v.replace([np.inf, -np.inf], np.nan)


def transform_daily(values, c):
    x = values.shift(c['lag_days'])
    out = {}
    for name in x.columns:
        out[f'{name}__z28'] = zscore(x[name], c['z_window'], c['z_min'], c['clip'])
        out[f'{name}__d1'] = x[name] - x[name].shift(1)
    return pd.DataFrame(out, index=x.index)


def daily_samples(trans, prices, volumes, window, cfg):
    rows, excluded = {}, {'features_incomplete': 0, 'f0_unavailable': 0}
    for t in trans.index[window_mask(trans.index, 0, 24, window, cfg)]:
        feats = trans.loc[t]
        if feats.isna().any():
            excluded['features_incomplete'] += 1
            continue
        d = t.date()
        f0 = T.f0(prices, volumes, d)
        if f0 is None:
            excluded['f0_unavailable'] += 1
            continue
        rows[t] = {**feats.to_dict(), **f0, 'T1': T.t1(prices, d), 'R7': T.t3(prices, d), 'V7': T.t4(prices, d)}
    df = pd.DataFrame.from_dict(rows, orient='index').sort_index().astype(float)
    for name, tc in cfg['targets'].items():
        if tc['kind'] == 'daily':
            df.loc[~window_mask(df.index, tc['horizon_hours'], 24, window, cfg), name] = np.nan
    return df, excluded
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_dataset4.py -q`
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b4/dataset4.py tests/research/onchain_b4/test_dataset4.py
git commit -m "feat(onchain-b4): causal hourly and daily features, targets and windows

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Screen, selection, holdout evaluation, report

**Files:**
- Create: `tradingagents/research/onchain_b4/screen4.py`
- Test: `tests/research/onchain_b4/test_screen4.py`

**Interfaces:**
- Consumes: `onchain_b2.screen.folds/fit_predict/row_loss`, `onchain_b2.holdout.holm`, `onchain_b.evaluate._bootstrap_means` (test reference only).
- Produces: `screen4.bootstrap_means(values, block, draws, seed, chunk) -> ndarray`; `interval(...) -> (lo, hi)`; `columns4(df, set_name, cfg) -> list[str]`; `folds_for(index, target, cfg)`; `run_screen4(samples, cfg) -> list[dict]`; `select4(results, cfg) -> list[dict]`; `evaluate4(dev, hold, selection, cfg) -> list[dict]`; `report4(results, selection) -> str`. Result dicts carry B3's keys plus `extra` with `r2c_<set>` (regression) or `llgain_<set>` and `accuracy_<set>` (classification).

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b4/test_screen4.py
import copy

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b.evaluate import _bootstrap_means
from tradingagents.research.onchain_b4 import config, screen4 as S


def test_chunked_bootstrap_equals_reference():
    x = np.random.default_rng(1).normal(size=500)
    assert np.allclose(S.bootstrap_means(x, 28, 300, 7, chunk=37), _bootstrap_means(x, 28, 300, 7))


def _frames(rng):
    hi = pd.date_range('2017-10-02', '2024-12-31 23:00', freq='6h')
    n = len(hi)
    sig = rng.normal(size=n)
    h = pd.DataFrame({'h0_r1': rng.normal(size=n), 'eth_x__h1z': sig, 'stable_x__h1z': rng.normal(size=n),
                      'act_x__h1z': rng.normal(size=n)}, index=hi)
    for t in ('R1', 'R6', 'R24', 'V6'):
        h[t] = rng.normal(size=n)
    h['V24'] = 2 * sig + 0.3 * rng.normal(size=n)
    di = pd.date_range('2017-10-02', '2024-12-30', freq='D')
    d = pd.DataFrame({'f0_r1': rng.normal(size=len(di)), 'cmf_x__z28': rng.normal(size=len(di)),
                      'cmo_x__z28': rng.normal(size=len(di))}, index=di)
    d['T1'] = (rng.random(len(di)) > 0.5).astype(float)
    d['R7'], d['V7'] = rng.normal(size=len(di)), rng.normal(size=len(di))
    return {'hourly': h, 'daily': d}


def test_screen4_counts_signal_constant_columns_and_selection():
    cfg = copy.deepcopy(config.load())
    cfg['families'] = ['linear']
    res = S.run_screen4(_frames(np.random.default_rng(4)), cfg)
    assert len(res) == 21
    get = {(r['target'], r['set']): r for r in res}
    assert get[('V24', 'HE')]['passed'] and get[('V24', 'HA')]['passed'] and not get[('V24', 'HS')]['passed']
    assert not get[('R1', 'HE')]['passed'] and not get[('T1', 'DF')]['passed']
    assert 'r2c_HE' in get[('V24', 'HE')]['extra'] and 'llgain_DF' in get[('T1', 'DF')]['extra']
    sel = S.select4(res, cfg)
    assert sel and sel == sorted(sel, key=lambda s: s['dev_hi'] / get[(s['target'], s['set'])]['loss_comparator'])
    assert all(s['target'] == 'V24' for s in sel)
    text = S.report4(res, sel)
    assert '21 comparisons' in text and 'V24' in text and 'vs constant' in text


def test_evaluate4_refits_and_applies_holm():
    cfg = config.load()
    rng = np.random.default_rng(5)
    f = _frames(rng)
    hold = _frames(np.random.default_rng(6))
    for k in hold:
        hold[k].index = hold[k].index + pd.DateOffset(years=8)
    sel = {'selected': [{'target': 'V24', 'family': 'linear', 'set': 'HE', 'comparator': 'H0'},
                        {'target': 'R1', 'family': 'linear', 'set': 'HE', 'comparator': 'H0'}]}
    out = S.evaluate4(f, hold, sel, cfg)
    assert [r['target'] for r in out] == ['V24', 'R1'] and out[0]['passed'] and not out[1]['passed']
    assert out[0]['p_holm'] >= out[0]['p']
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_screen4.py -q`
Expected: FAIL with `ImportError: cannot import name 'screen4'`

- [ ] **Step 3: Implement screen4**

```python
# tradingagents/research/onchain_b4/screen4.py
"""B4 screen and holdout evaluation (spec §6): B2 model primitives, targets of two kinds from
config, a constant-forecast reference for every row, and a chunked circular block bootstrap that
draws exactly the resamples of the B branch reference."""
from __future__ import annotations

import numpy as np

from ..onchain_b2.holdout import holm
from ..onchain_b2.screen import fit_predict, folds, row_loss

_CONST = ('r2c_', 'llgain_')


def bootstrap_means(values, block, draws, seed, chunk=100):
    x = np.asarray(values, float)
    n = len(x)
    if n < block:
        raise ValueError(f'series of {n} rows is shorter than the {block}-row block')
    rng = np.random.Generator(np.random.PCG64(seed))
    k = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(draws, k))
    out = np.empty(draws)
    for i in range(0, draws, chunk):
        s = starts[i:i + chunk]
        idx = ((s[:, :, None] + np.arange(block)[None, None, :]) % n).reshape(len(s), -1)[:, :n]
        out[i:i + chunk] = x[idx].mean(1)
    return out


def interval(values, block, draws, seed, chunk=100):
    m = bootstrap_means(values, block, draws, seed, chunk)
    return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def columns4(df, set_name, cfg):
    return sorted(c for c in df.columns if c.startswith(tuple(cfg['sets'][set_name])))


def folds_for(index, target, cfg):
    return folds(index, cfg['folds']['test_years'], cfg['targets'][target]['horizon_hours'] / 24)


def run_screen4(samples, cfg):
    g, fc = cfg['gate'], cfg['folds']
    results = []
    for target, tc in cfg['targets'].items():
        kind, task = tc['kind'], tc['task']
        comps = cfg['comparisons'][kind]
        sets = sorted({s for pair in comps for s in pair})
        df = samples[kind]
        n_missing = int(df[target].isna().sum())
        df = df[df[target].notna()].sort_index()
        y = df[target].to_numpy(float)
        fl = folds_for(df.index, target, cfg)
        tested, const = np.zeros(len(df), bool), np.full(len(df), np.nan)
        for _, tr, te in fl:
            tested |= te
            const[te] = y[tr].mean()
        yt = df.index.year.to_numpy()[tested]
        closs = float(row_loss(task, y[tested], const[tested]).mean())
        for family in cfg['families']:
            preds, alphas = {}, {}
            for s in sets:
                X = df[columns4(df, s, cfg)].to_numpy(float)
                p = np.full(len(df), np.nan)
                alphas[s] = {}
                for yr, tr, te in fl:
                    info = {}
                    p[te] = fit_predict(family, task, X[tr], y[tr], X[te], fc['inner_len'][kind], cfg, info)
                    alphas[s][int(yr)] = info['alpha']
                preds[s] = p
            loss = {s: row_loss(task, y[tested], preds[s][tested]) for s in sets}
            for a, b in comps:
                diff = loss[a] - loss[b]
                lo, hi = interval(diff, tc['block'], g['draws'], g['seed'], g['chunk'])
                per_year = {int(yr): float(diff[yt == yr].mean()) for yr in fc['test_years']}
                wins = sum(v < 0 for v in per_year.values())
                if task == 'classification':
                    extra = {f'llgain_{s}': closs - float(loss[s].mean()) for s in (a, b)}
                    extra.update({f'accuracy_{s}': float(((preds[s][tested] > 0.5) == (y[tested] > 0.5)).mean())
                                  for s in (a, b)})
                else:
                    extra = {f'r2c_{s}': 1 - float(loss[s].mean()) / closs for s in (a, b)}
                results.append({'target': target, 'kind': kind, 'task': task, 'family': family, 'set': a,
                                'comparator': b, 'n': int(len(diff)), 'mean_diff': float(diff.mean()), 'lo': lo,
                                'hi': hi, 'wins': int(wins), 'years': per_year,
                                'alphas': {a: alphas[a], b: alphas[b]}, 'n_missing_target': n_missing,
                                'passed': bool(hi < 0 and wins >= g['min_year_wins']),
                                'loss_set': float(loss[a].mean()), 'loss_comparator': float(loss[b].mean()),
                                'loss_constant': closs, 'extra': extra})
    return results


def select4(results, cfg):
    passing = [r for r in results if r['passed']]
    passing.sort(key=lambda r: (r['hi'] / r['loss_comparator'], cfg['onchain_rank'][r['set']]))
    return [{'target': r['target'], 'family': r['family'], 'set': r['set'], 'comparator': r['comparator'],
             'dev_mean_diff': r['mean_diff'], 'dev_hi': r['hi']} for r in passing[:cfg['gate']['max_selected']]]


def evaluate4(dev, hold, selection, cfg):
    g, fc = cfg['gate'], cfg['folds']
    out = []
    for s in selection['selected']:
        tc = cfg['targets'][s['target']]
        kind, task = tc['kind'], tc['task']
        d = dev[kind][dev[kind][s['target']].notna()].sort_index()
        h = hold[kind][hold[kind][s['target']].notna()].sort_index()
        yd, yh = d[s['target']].to_numpy(float), h[s['target']].to_numpy(float)
        loss = {}
        for name in (s['set'], s['comparator']):
            cols = columns4(d, name, cfg)
            pred = fit_predict(s['family'], task, d[cols].to_numpy(float), yd, h[cols].to_numpy(float),
                               fc['inner_len'][kind], cfg)
            loss[name] = row_loss(task, yh, pred)
        diff = loss[s['set']] - loss[s['comparator']]
        means = bootstrap_means(diff, tc['block'], g['draws'], g['seed'], g['chunk'])
        out.append({**{k: s[k] for k in ('target', 'family', 'set', 'comparator')}, 'n': int(len(diff)),
                    'mean_diff': float(diff.mean()), 'p': float((means >= 0).mean())})
    for r, adj in zip(out, holm([r['p'] for r in out]) if out else []):
        r['p_holm'] = adj
        r['passed'] = bool(adj < g['alpha'] and r['mean_diff'] < 0)
    return out


def report4(results, selection):
    lines = [f'{len(results)} comparisons are screened, each against a 95 % interval; about '
             f'{0.05 * len(results):.0f} false passes are expected by chance, which is why the sealed holdout exists.', '',
             '| target | family | comparison | n | mean loss diff | 95 % CI | years better | pass | vs constant | detail |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for r in results:
        const = ', '.join(f'{k} {v:+.4f}' for k, v in r['extra'].items() if k.startswith(_CONST))
        detail = ', '.join(f'{k} {v:.4f}' for k, v in r['extra'].items() if not k.startswith(_CONST))
        lines.append(f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n']} | "
                     f"{r['mean_diff']:+.6f} | [{r['lo']:+.6f}, {r['hi']:+.6f}] | {r['wins']}/6 | "
                     f"{'PASS' if r['passed'] else '—'} | {const} | {detail} |")
    lines += ['', '## Selected for the holdout', '']
    lines += [f"- {s['target']} · {s['family']} · {s['set']} vs {s['comparator']} (dev upper bound {s['dev_hi']:+.6f})"
              for s in selection] or ['- none: screen negative, holdout stays unused']
    return '\n'.join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_screen4.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b4/screen4.py tests/research/onchain_b4/test_screen4.py
git commit -m "feat(onchain-b4): config-driven screen with constant-forecast reference and chunked bootstrap

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: CLI stages (market, cm, pass, features, screen, holdout)

**Files:**
- Create: `tradingagents/research/onchain_b4/cli.py`
- Test: `tests/research/onchain_b4/test_cli4.py`

**Interfaces:**
- Consumes: everything above; `onchain_b2.market.http_get/load_dev/load_all`, `onchain_b2.labels.load`, `onchain_b2.holdout.committed_selection/selection_identity`, `onchain_b.runlog.Log`.
- Produces: `cli.main(argv)`; module attributes `ARTIFACTS`, `STUDY`, `B2`, `ROOT` (patchable); `cli.filesystem()` (patchable); `cli.pass_complete() -> bool`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b4/test_cli4.py
import copy
import json
import subprocess

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2.s3source import DayUnavailable
from tradingagents.research.onchain_b4 import cli, config, reader
from tradingagents.research.onchain_b4.reader import Day

A, B, E = ('0x' + c * 40 for c in 'abe')


def _day(day):
    t0 = int(pd.Timestamp(day).timestamp())
    k = reader.addr_keys(np.array([A, B, E], object))
    seed = int(pd.Timestamp(day).dayofyear)
    src = np.array([k[0], k[1], k[0]], np.uint64)
    dst = np.array([k[2], k[0], k[1]], np.uint64)
    return Day(src=src, dst=dst, asset=np.array([0, 1, 0], np.int8), amount=np.array([1.0 + seed, 2e6, 3.0]),
               ts=np.array([t0 + 60, t0 + 7200, t0 + 9000], np.int64), block=np.array([1, 2, 3], np.int64),
               tx_ts=np.array([t0 + 60], np.int64), tx_gwei=np.array([5.0]), blk_ts=np.array([t0 + 60], np.int64),
               blk_gas=np.array([1.0]), blk_txs=np.array([1.0]))


def _setup(tmp_path, monkeypatch, unavailable=()):
    art, b2 = tmp_path / 'b4', tmp_path / 'b2'
    (b2 / 'labels').mkdir(parents=True)
    (b2 / 'labels' / 'labels.json').write_text(json.dumps({E: {'name': 'X'}}))
    cfg = copy.deepcopy(config.load())
    cfg['entities']['bloom_bits_log2'] = 16
    cfg['s3']['retries'] = []
    monkeypatch.setattr(cli, 'ARTIFACTS', art)
    monkeypatch.setattr(cli, 'B2', b2)
    monkeypatch.setattr(cli.config, 'load', lambda: cfg)
    monkeypatch.setattr(cli, 'filesystem', lambda: None)

    def fake(day, **kw):
        if day in unavailable:
            raise DayUnavailable(day, ['boom'])
        return _day(day)
    monkeypatch.setattr(reader, 'read_day', fake)
    return art


def test_pass_writes_hours_and_snapshot(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch)
    cli.main(['pass', '--end', '2017-01-03'])
    assert all((art / 'hours' / f'2017-01-0{d}.parquet').exists() for d in (1, 2, 3))
    h = pd.read_parquet(art / 'hours' / '2017-01-02.parquet')
    assert len(h) == 24 and h['eth_in_val'].iloc[0] == 3.0
    z = np.load(art / 'state' / 'entities.npz')
    assert str(z['last_day'][0]) == '2017-01-03'


def test_resume_matches_uninterrupted(tmp_path, monkeypatch):
    art = _setup(tmp_path / 'one', monkeypatch)
    cli.main(['pass', '--end', '2017-01-04'])
    full = {d: pd.read_parquet(art / 'hours' / f'2017-01-0{d}.parquet') for d in (3, 4)}
    art2 = _setup(tmp_path / 'two', monkeypatch)
    cli.main(['pass', '--end', '2017-01-02'])
    cli.main(['pass', '--end', '2017-01-04'])
    for d in (3, 4):
        pd.testing.assert_frame_equal(full[d], pd.read_parquet(art2 / 'hours' / f'2017-01-0{d}.parquet'))
    a, b = np.load(art / 'state' / 'entities.npz'), np.load(art2 / 'state' / 'entities.npz')
    assert np.array_equal(a['c_keys'], b['c_keys']) and np.array_equal(a['bits'], b['bits'])


def test_unavailable_day_is_marked_and_pass_continues(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch, unavailable=('2017-01-02',))
    cli.main(['pass', '--end', '2017-01-03'])
    assert (art / 'hours' / '2017-01-02.unavailable.json').exists() and (art / 'hours' / '2017-01-03.parquet').exists()


def test_consecutive_unavailable_stops(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, unavailable=('2017-01-01', '2017-01-02', '2017-01-03', '2017-01-04'))
    with pytest.raises(SystemExit, match='consecutive'):
        cli.main(['pass', '--end', '2017-01-05'])


def test_features_refuse_incomplete_pass(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    cli.main(['pass', '--end', '2017-01-02'])
    with pytest.raises(SystemExit, match='pass incomplete'):
        cli.main(['features'])


def test_screen_never_overwrites_selection(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(cli, 'STUDY', tmp_path)
    (tmp_path / 'selection.json').write_text('{"selected": []}')
    with pytest.raises(SystemExit, match='exists'):
        cli.main(['screen'])


def test_holdout_refuses_empty_committed_selection(tmp_path, monkeypatch, capsys):
    art = _setup(tmp_path, monkeypatch)
    repo = tmp_path / 'repo'
    repo.mkdir()
    git = lambda *a: subprocess.run(['git', '-C', str(repo), *a], check=True, capture_output=True)
    git('init', '-q')
    (repo / 'selection.json').write_text('{"selected": []}')
    git('add', 'selection.json')
    git('-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 's')
    monkeypatch.setattr(cli, 'STUDY', repo)
    monkeypatch.setattr(cli, 'ROOT', repo)
    cli.main(['holdout'])
    assert 'holdout not opened' in capsys.readouterr().out and not (art / 'screen' / 'holdout.lock.json').exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_cli4.py -q`
Expected: FAIL with `ImportError: cannot import name 'cli'`

- [ ] **Step 3: Implement the CLI**

```python
# tradingagents/research/onchain_b4/cli.py
"""B4 stage runner. The chain pass is sequential (exchange state), prefetches reads in threads,
snapshots the state every N days and resumes from the last snapshot; later stages refuse to run
until every day is built or marked unavailable."""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from ..onchain_b.runlog import Log
from ..onchain_b2 import holdout as H2
from ..onchain_b2 import labels, market
from ..onchain_b2.s3source import DayUnavailable
from . import cmdaily, config, dataset4, flows, hourmarket, reader, screen4
from .entities import Entities

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B2 = config.B2_ARTIFACTS
ROOT = config.ROOT


def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))
    os.replace(tmp, path)


def _peak_rss_mb():
    try:
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmHWM:'):
                return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        pass
    return None


def filesystem():
    import pyarrow.fs as pafs
    return pafs.S3FileSystem(anonymous=True, region=config.load()['s3']['region'])


def _cutoff_hour(c):
    return c['windows']['dev_end'] + 'T23'


def stage_market(args):
    c = config.load()
    if (ARTIFACTS / 'market' / 'hourly_dev.json').exists():
        raise SystemExit('hourly market data already stored')
    b = c['binance']
    bars, pages = hourmarket.fetch(market.http_get, b['symbol'], b['start'], b['end'])
    print(json.dumps(hourmarket.store(bars, pages, ARTIFACTS, _cutoff_hour(c))))


def stage_cm(args):
    c = config.load()
    if (ARTIFACTS / 'market' / 'cm_dev.json').exists():
        raise SystemExit('Coin Metrics data already stored')
    m = c['cm']
    eth, p1 = cmdaily.fetch(market.http_get, ['eth'], m['eth'], m['start'], m['end'])
    st, p2 = cmdaily.fetch(market.http_get, m['stables'], ['SplyCur'], m['start'], m['end'])
    frame = cmdaily.to_frame({**eth, **st}, m['eth'], m['stables'])
    print(json.dumps(cmdaily.store(frame, p1 + p2, ARTIFACTS, c['windows']['dev_end'])))


def _hours_dir():
    return ARTIFACTS / 'hours'


def day_status(day):
    if (_hours_dir() / f'{day}.parquet').exists():
        return 'done'
    if (_hours_dir() / f'{day}.unavailable.json').exists():
        return 'unavailable'
    return None


def pass_complete():
    return all(day_status(d) is not None for d in config.days(config.load()))


def _new_entities(c):
    keys = reader.addr_keys(np.array(sorted(labels.load(B2 / 'labels' / 'labels.json')), object))
    e = c['entities']
    return Entities(keys, e['bloom_bits_log2'], e['bloom_hashes'], e['deposit_share'])


def stage_pass(args):
    c = config.load()
    days = [d for d in config.days(c) if args.end is None or d <= args.end]
    snap = ARTIFACTS / 'state' / 'entities.npz'
    ent = Entities.load(snap) if snap.exists() else _new_entities(c)
    todo = [d for d in days if ent.last_day is None or d > ent.last_day]
    log = Log(ARTIFACTS / 'logs' / 'pass.jsonl')
    fs, p = filesystem(), c['pass']
    hours = _hours_dir()
    hours.mkdir(parents=True, exist_ok=True)

    def fetch(day):
        return reader.read_day(day, filesystem=fs, root=c['s3']['bucket'], tokens=c['tokens'], retries=c['s3']['retries'])

    consecutive, since = 0, 0
    with ThreadPoolExecutor(max_workers=max(1, p['prefetch'])) as pool:
        futures = {}
        for i, day in enumerate(todo):
            for nxt in todo[i:i + p['prefetch'] + 1]:
                if nxt not in futures:
                    futures[nxt] = pool.submit(fetch, nxt)
            t = time.time()
            try:
                d = futures.pop(day).result()
            except DayUnavailable as e:
                _write_json(hours / f'{day}.unavailable.json', {'day': day, 'errors': e.errors})
                log.event(event='day', day=day, status='unavailable')
                ent.last_day = day
                consecutive += 1
                if consecutive >= p['max_consecutive_unavailable']:
                    ent.save(snap)
                    raise SystemExit(f'{consecutive} consecutive unavailable days up to {day}: stopping the pass')
                continue
            consecutive = 0
            rows = flows.hourly(day, d, ent.is_exchange, ent.is_labelled, c['flows'])
            tmp = hours / f'.{day}.tmp.parquet'
            rows.to_parquet(tmp)
            os.replace(tmp, hours / f'{day}.parquet')
            (hours / f'{day}.unavailable.json').unlink(missing_ok=True)
            ent.update(d.src, d.dst, d.block, day)
            log.event(event='day', day=day, status='done', seconds=round(time.time() - t, 1), transfers=int(len(d.src)),
                      candidates=int(len(ent.c_keys)), deposits=int(len(ent.deposits)), peak_rss_mb=_peak_rss_mb(), **d.rows)
            del d
            since += 1
            if since >= p['snapshot_every']:
                ent.save(snap)
                since = 0
    ent.save(snap)


def _require_pass():
    if not pass_complete():
        raise SystemExit('pass incomplete: build or mark every day first')


def stage_features(args):
    _require_pass()
    c = config.load()
    days = config.days(c)
    raw = dataset4.hourly_table(_hours_dir(), days)
    trans = dataset4.transform_hourly(raw, c['hourly'])
    out = ARTIFACTS / 'features'
    out.mkdir(parents=True, exist_ok=True)
    raw.to_parquet(out / 'hourly_raw.parquet')
    trans.to_parquet(out / 'hourly.parquet')
    prices, volumes = market.load_dev(B2 / 'market' / 'dev.json', config.windows(c)['dev_end'])
    cm = cmdaily.load_dev(ARTIFACTS / 'market' / 'cm_dev.json', c['windows']['dev_end'])
    daily = dataset4.transform_daily(dataset4.cm_values(cm, prices), c['daily'])
    daily.to_parquet(out / 'daily_dev.parquet')
    missing = [d for d in days if day_status(d) == 'unavailable']
    _write_json(out / 'missing.json', missing)
    print(json.dumps({'days': len(days), 'unavailable': len(missing), 'hourly_rows': len(trans),
                      'hourly_columns': len([x for x in trans.columns if not x.startswith('lab_')]),
                      'daily_columns': daily.shape[1]}))


def _samples(window):
    c = config.load()
    trans = pd.read_parquet(ARTIFACTS / 'features' / 'hourly.parquet')
    if window == 'dev':
        bars = hourmarket.load_dev(ARTIFACTS / 'market' / 'hourly_dev.json', _cutoff_hour(c))
        prices, volumes = market.load_dev(B2 / 'market' / 'dev.json', config.windows(c)['dev_end'])
        cm = cmdaily.load_dev(ARTIFACTS / 'market' / 'cm_dev.json', c['windows']['dev_end'])
    else:
        bars = hourmarket.load_all(ARTIFACTS / 'market' / 'hourly_dev.json', ARTIFACTS / 'sealed' / 'hourly_sealed.json')
        prices, volumes = market.load_all(B2 / 'market' / 'dev.json', B2 / 'sealed' / 'market_sealed.json')
        cm = cmdaily.load_all(ARTIFACTS / 'market' / 'cm_dev.json', ARTIFACTS / 'sealed' / 'cm_sealed.json')
    daily_trans = dataset4.transform_daily(dataset4.cm_values(cm, prices), c['daily'])
    hourly, ex_h = dataset4.hourly_samples(trans, bars, window, c)
    daily, ex_d = dataset4.daily_samples(daily_trans, prices, volumes, window, c)
    return {'hourly': hourly, 'daily': daily}, {'hourly': ex_h, 'daily': ex_d}


def stage_screen(args):
    if (STUDY / 'selection.json').exists():
        raise SystemExit('selection.json exists: the B4 screen has already run')
    _require_pass()
    cfg = config.load()
    samples, excluded = _samples('dev')
    results = screen4.run_screen4(samples, cfg)
    selection = screen4.select4(results, cfg)
    _write_json(ARTIFACTS / 'screen' / 'screen.json', {'results': results, 'excluded': excluded,
                                                     'n': {k: len(v) for k, v in samples.items()}})
    head = (f"# B4 screen — development 2017-10 → 2024 (walk-forward 2019–2024)\n\n"
            f"Samples: daily {len(samples['daily'])} (excluded {excluded['daily']}), "
            f"hourly {len(samples['hourly'])} (excluded {excluded['hourly']}).\n\n")
    report = screen4.report4(results, selection)
    (STUDY / 'SCREEN.md').write_text(head + report + '\n')
    _write_json(STUDY / 'selection.json', {'registered_from': 'screen.json', 'selected': selection})
    print(report)


def stage_holdout(args):
    lock = ARTIFACTS / 'screen' / 'holdout.lock.json'
    if lock.exists():
        raise SystemExit(f'holdout already opened ({lock}); it is one-shot')
    cfg = config.load()
    selection = H2.committed_selection(STUDY / 'selection.json', ROOT)
    if not selection['selected']:
        print('screen negative: holdout not opened')
        return
    identity = H2.selection_identity(STUDY / 'selection.json', ROOT)
    _write_json(lock, {'opened_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), **identity})
    dev, _ = _samples('dev')
    hold, excluded = _samples('holdout')
    res = screen4.evaluate4(dev, hold, selection, cfg)
    _write_json(ARTIFACTS / 'screen' / 'holdout.json', {'results': res, 'excluded': excluded, **identity})
    lines = ['# B4 holdout — sealed 2025-01-01 → 2026-10-12', '',
             f"Opened once from selection.json blob {identity['blob']} at commit {identity['head']}.", '',
             '| target | family | comparison | n | mean loss diff | p (one-sided) | p Holm | pass |',
             '|---|---|---|---|---|---|---|---|']
    lines += [f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n']} | {r['mean_diff']:+.6f} | "
              f"{r['p']:.4f} | {r['p_holm']:.4f} | {'PASS' if r['passed'] else '—'} |" for r in res]
    (STUDY / 'HOLDOUT.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b4')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('market').set_defaults(fn=stage_market)
    sub.add_parser('cm').set_defaults(fn=stage_cm)
    a = sub.add_parser('pass')
    a.add_argument('--end', default=None)
    a.set_defaults(fn=stage_pass)
    sub.add_parser('features').set_defaults(fn=stage_features)
    sub.add_parser('screen').set_defaults(fn=stage_screen)
    sub.add_parser('holdout').set_defaults(fn=stage_holdout)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests to verify they pass, then the whole package**

Run: `.venv/bin/python -m pytest tests/research/onchain_b4/test_cli4.py -q`
Expected: `7 passed`

Run: `.venv/bin/python -m pytest tests/research/onchain_b4 tests/research/onchain_b3 tests/research/onchain_b2 tests/research/onchain_b -q`
Expected: all pass (155 earlier + 27 new)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b4/cli.py tests/research/onchain_b4/test_cli4.py
git commit -m "feat(onchain-b4): stage runner with sequential resumable chain pass

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Market data, heavy-day probe, chain pass (B4-CP1, B4-CP2 data)

Operational.

- [ ] **Step 1: Fetch hourly bars and Coin Metrics**

Run: `.venv/bin/python -m tradingagents.research.onchain_b4.cli market` then `.venv/bin/python -m tradingagents.research.onchain_b4.cli cm`
Expected: hourly meta with ≈ 64,600 development hours from 2017-08-17 and ≈ 15,600 sealed hours; Coin Metrics meta with ≈ 2,922 development days and ≈ 650 sealed days. Do not open any file under `sealed/`.

- [ ] **Step 2: Record B4-CP1 in `STATE.md` and commit** (`docs(onchain-b4): B4-CP1 market and Coin Metrics data stored`).

- [ ] **Step 3: Probe one heavy day with a fresh label-only state**

```bash
/usr/bin/time -v .venv/bin/python - <<'EOF' 2>&1 | grep -E 'Maximum resident|Elapsed|rows|sec'
import time, numpy as np
from tradingagents.research.onchain_b4 import cli, config, flows, reader
from tradingagents.research.onchain_b4.entities import Entities
c = config.load(); t = time.time()
d = reader.read_day('2025-06-02', filesystem=cli.filesystem(), root=c['s3']['bucket'], tokens=c['tokens'], retries=[])
print('rows', d.rows, 'read sec', round(time.time() - t, 1))
e = cli._new_entities(c); t = time.time()
r = flows.hourly('2025-06-02', d, e.is_exchange, e.is_labelled, c['flows']); e.update(d.src, d.dst, d.block, '2025-06-02')
print('flows+update sec', round(time.time() - t, 1), 'candidates', len(e.c_keys))
EOF
```
Expected: read ≈ 25–35 s, processing < 15 s, peak < 3 GB. Record in `STATE.md`.

- [ ] **Step 4: Launch the pass (check `df -h /` shows ≥ 5 GB free first)**

```bash
P=$PWD; systemd-run --user --unit onchain-b4-pass -p MemoryMax=6G -p WorkingDirectory=$P -E OMP_NUM_THREADS=2 \
  $P/.venv/bin/python -m tradingagents.research.onchain_b4.cli pass
```
Expected: `logs/pass.jsonl` gains one `day` event per day; ≈ 15–25 h. If the unit dies (OOM, crash), relaunch the same command: it resumes from the last snapshot.

---

### Task 10: Features, screen, selection, holdout, forensics (B4-CP2 … CP4)

Operational. The selection commit precedes the holdout.

- [ ] **Step 1:** `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b4.cli features` — expect `days` 3571, `hourly_columns` 32 (registered chain features; the 8 price features are built per sample), `daily_columns` 20, and the unavailable count; record B4-CP2 in `STATE.md`, commit.
- [ ] **Step 2:** `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b4.cli screen` (as a systemd unit with `MemoryMax=6G`) — expect 42 rows in `SCREEN.md` and `selection.json`.
- [ ] **Step 3:** Commit `SCREEN.md`, `selection.json`, `STATE.md` (`research(onchain-b4): B4-CP3 screen and committed selection`).
- [ ] **Step 4:** `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b4.cli holdout` — either "screen negative: holdout not opened" or `HOLDOUT.md`.
- [ ] **Step 5:** Write `FORENSICS.md` (spec §7: constant-forecast harness check per target, feature counts, labels-only against deposit-expanded flows on the same models, signs of hourly ETH and stable net-inflow coefficients against the motivating claim, per-year detail for near misses); update `STATE.md`, memory note and the audit page; commit (`research(onchain-b4): B4-CP4 result`).

---

## Self-review

**Spec coverage:** §3 windows/sealing → Tasks 2, 6, 8; §4.1 reads → Task 3; §4.2 entities → Task 4; §4.3 series → Task 5; §4.4 persistence → Tasks 4, 8; §4.5 hourly market → Task 2; §4.6–4.8 features/targets/sets → Tasks 1, 6; §5 Coin Metrics → Tasks 2, 6; §6 screen/holdout → Tasks 7, 8; §7 forensics → Task 10; §8 compute → Task 9; §9 layout → as listed; §10 testing → Tasks 2–8; §11 checkpoints → Tasks 9–10.

**Type consistency:** `reader.Day` fields used by `flows.hourly` and `Entities.update(src, dst, block, day)`; `flows.SERIES/LAB` used by `dataset4.transform_hourly`; `cfg['targets'][t]['horizon_hours']`, `['kind']`, `['block']` used by `dataset4` and `screen4`; `columns4(df, set, cfg)` used by `run_screen4`/`evaluate4`; `cli.filesystem()`, `cli.ROOT`, `cli.STUDY`, `cli.ARTIFACTS`, `cli.B2` patched in tests.

**Review Focus coverage:** 1 → Task 3 `test_reader_old_formats_and_nulls`, Task 4 `test_update_with_no_transfers`; 2 → Task 3 `test_reader_old_formats_and_nulls` (42-character USDC row); 3 → Task 6 `test_missing_bar_excludes_dependent_rows`; 4 → Task 8 `test_resume_matches_uninterrupted`; 5 → Task 8 `test_consecutive_unavailable_stops`.
