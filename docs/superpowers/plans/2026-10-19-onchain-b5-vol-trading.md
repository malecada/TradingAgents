# B5 Exchange Flows Against the Option Market — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test, on historical data with a pre-declared plan, whether B4's hourly exchange-flow features improve volatility forecasts once the option market's own information is included, and whether a cost-aware Deribit daily-straddle rule built on them makes money; plus a BTC check, an event study and a Tron data probe.

**Architecture:** New package `tradingagents/research/onchain_b5/` that imports B2/B4 primitives. Option trades (with taker side and IV) and DVOL come from Deribit's public history API into per-day parquet files; decision tables (two daily schedules, two assets) join price features, option-market features and B4 flow features at the last complete hour before each decision; walk-forward ridge/trees produce out-of-fold forecasts that feed the forecast comparison and the straddle backtest.

**Tech Stack:** Python 3.13, numpy, pandas, pyarrow, scipy (`ndtr`), scikit-learn via B2 `fit_predict`, pytest; systemd user units for downloads.

**Spec:** `docs/superpowers/specs/2026-10-19-onchain-b5-vol-trading-design.md`

## Global Constraints

- Exploratory with a pre-declared analysis plan: `research/onchain-b5-2026-10-19/PLAN.md` is committed before any B5 model or backtest runs; every analysis in it is reported; nothing is tuned on 2025–26.
- Window 2021-03-24 → 2026-10-12 (2,029 days), ETH and BTC.
- Schedules: S6 decision 02:00 UTC → same-day 08:00 expiry (τ = 6 h); S24 decision 08:00 UTC → next-day 08:00 expiry (τ = 24 h).
- Implied: trades on the target expiry in [t − 2 h, t), |ln(K/index)| ≤ 0.02, ≥ 3 trades; IV_mid / IV_ask (taker buys) / IV_bid (taker sells) amount-weighted medians; missing side filled from the median half-spread of the previous 30 eligible decisions.
- Forecasters M0 (h0_ + px_), M1 (M0 + mk_), M2 (M1 + eth_ + stable_), IV (mk_iv); comparisons M1 vs M0, M2 vs M1, M2 vs IV; families linear and trees; test years 2022–2026, reported as 2022–24 and 2025–26.
- Straddle: thetas 0.05, 0.10, 0.20; fees 0.03 % of underlying per leg capped at 12.5 % of the leg price, at entry and as delivery fee; Black-76 at IV_ask (buy) / IV_bid (sell); payoff |S_T − K| with Binance close at the expiry hour.
- Bootstrap: circular blocks of 20 decisions, 2,000 draws, seed 20261019 (events: block 1 over events).
- `onchain_b`, `onchain_b2`, `onchain_b3`, `onchain_b4` are imported, not edited. Study docs impersonal.
- Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Package test command: `.venv/bin/python -m pytest tests/research/onchain_b5 -q`.

## Review Focus

1. Decision days without a daily expiry (early 2021) or with fewer than 3 near-ATM trades → the decision is skipped, never filled from another expiry (Task 4 `test_build_skips_ineligible_and_is_causal`).
2. A missing ask or bid side → filled only from earlier decisions' half-spreads (Task 4 `test_fill_spread_uses_only_earlier_rows`).
3. API pages whose boundary splits trades with the same timestamp → no duplicate and no lost trade (Task 2 `test_fetch_day_paginates_and_dedupes`).
4. Black-76 at extreme inputs (τ = 6 h, far strikes) → finite prices, put–call parity (Task 6 `test_black76_values_parity_and_extremes`).
5. Expiry roll in the hourly IV series used by the event study → the nearest expiry at least 2 h after the hour, never an expired one (Task 7 `test_iv_series_uses_nearest_live_expiry`).

---

### Task 1: Skeleton, configuration, registration and pre-declared plan

**Files:**
- Create: `tradingagents/research/onchain_b5/__init__.py` (empty), `tradingagents/research/onchain_b5/config.py`
- Create: `research/onchain-b5-2026-10-19/config/b5.json`, `research/onchain-b5-2026-10-19/CHARTER.md`, `research/onchain-b5-2026-10-19/PLAN.md`, `research/onchain-b5-2026-10-19/STATE.md`
- Modify: `.gitignore` (add `/research_artifacts/onchain-b5/`)
- Test: `tests/research/onchain_b5/__init__.py` (empty), `tests/research/onchain_b5/test_config.py`

**Interfaces:**
- Produces: `config.ROOT`, `config.STUDY`, `config.ARTIFACTS`, `config.B4_ARTIFACTS`; `config.load() -> dict`; `config.days(cfg=None) -> list[str]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b5/test_config.py
from tradingagents.research.onchain_b5 import config


def test_config_schedules_sets_and_window():
    c = config.load()
    assert c['schedules']['S6'] == {'hour': 2, 'tau_h': 6, 'expiry_days': 0}
    assert c['schedules']['S24'] == {'hour': 8, 'tau_h': 24, 'expiry_days': 1}
    assert c['sets']['M2'][:3] == c['sets']['M1'] and c['sets']['IV'] == ['mk_iv']
    d = config.days(c)
    assert len(d) == 2029 and d[0] == '2021-03-24' and d[-1] == '2026-10-12'


def test_registration_files_exist():
    for name in ('CHARTER.md', 'PLAN.md', 'STATE.md'):
        assert (config.STUDY / name).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_config.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.research.onchain_b5'`

- [ ] **Step 3: Write config module and registration files**

```python
# tradingagents/research/onchain_b5/config.py
"""Frozen B5 configuration (research/onchain-b5-2026-10-19/config/b5.json)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b5-2026-10-19'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b5'
B4_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b4'


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b5.json').read_text())


def days(cfg=None) -> list:
    w = (cfg or load())['window']
    return [d.date().isoformat() for d in pd.date_range(w['start'], w['end'], freq='D')]
```

`research/onchain-b5-2026-10-19/config/b5.json`:

```json
{
 "window": {"start": "2021-03-24", "end": "2026-10-12"},
 "assets": ["ETH", "BTC"],
 "binance": {"ETH": "ETHUSDT", "BTC": "BTCUSDT", "start": "2017-08-17", "end": "2026-10-13"},
 "deribit": {"trades_url": "https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time",
             "dvol_url": "https://www.deribit.com/api/v2/public/get_volatility_index_data",
             "count": 1000, "retries": [10, 60], "pause": 0.05},
 "schedules": {"S6": {"hour": 2, "tau_h": 6, "expiry_days": 0}, "S24": {"hour": 8, "tau_h": 24, "expiry_days": 1}},
 "implied": {"lookback_h": 2, "moneyness": 0.02, "min_trades": 3, "spread_window": 30},
 "flow_prefixes": ["eth_", "stable_"],
 "sets": {"M0": ["h0_", "px_"], "M1": ["h0_", "px_", "mk_"], "M2": ["h0_", "px_", "mk_", "eth_", "stable_"], "IV": ["mk_iv"]},
 "comparisons": [["M1", "M0"], ["M2", "M1"], ["M2", "IV"]],
 "families": ["linear", "trees"],
 "folds": {"test_years": [2022, 2023, 2024, 2025, 2026], "inner_len": 365, "min_train": 30},
 "groups": {"2022-24": [2022, 2023, 2024], "2025-26": [2025, 2026]},
 "models": {"alphas": [0.1, 1, 10, 100, 1000, 10000, 100000], "fallback_alpha": 100.0,
            "trees": {"max_iter": 100, "learning_rate": 0.05, "max_leaf_nodes": 7, "min_samples_leaf": 30,
                      "l2_regularization": 1.0, "random_state": 11}},
 "gate": {"draws": 2000, "seed": 20261019, "block": 20, "chunk": 100},
 "straddle": {"thetas": [0.05, 0.10, 0.20], "fee_rate": 0.0003, "fee_cap": 0.125, "variants": ["M1", "M2"]},
 "events": {"z": 3.0, "spacing_h": 24, "kmax": 12, "test_years": [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
            "inner_len": 8760, "placebo_seed": 20261019, "iv_min_ahead_h": 2, "z_window": 168, "z_min": 120}
}
```

`research/onchain-b5-2026-10-19/CHARTER.md`:

```markdown
# B5 charter — exchange flows against the option market

Registered 2026-10-19 before any B5 data read. Spec:
`docs/superpowers/specs/2026-10-19-onchain-b5-vol-trading-design.md`.

## Question

Do B4's hourly exchange-flow features (stablecoin and ETH flows to and from exchange
entities) add to price and option-market information when forecasting realised
volatility to a Deribit daily expiry, and does a cost-aware at-the-money straddle rule
built on the forecast make money, for ETH and BTC, 2022–2026?

## Framing

Exploratory with a pre-declared analysis plan (`PLAN.md`). The ETH 2025–26 window was
opened in B4 and the closed rviv-p0 study used 2025–26 implied and realised volatility,
so no B5 result is confirmatory. Confirmation is a later forward study.

## Disclosures

- Option prices come from executed trades (taker side gives ask or bid), not quotes.
- Deribit's current fee schedule is applied to all years.
- Settlement uses the Binance close at the expiry hour instead of Deribit's 30-minute
  delivery index.
- BTC and ETH volatility co-move; the BTC check is a generalisation check.
```

`research/onchain-b5-2026-10-19/PLAN.md`:

```markdown
# B5 pre-declared analysis plan (committed before any B5 model or backtest)

All items are run once and reported in `RESULTS.md`, including negatives. Groups:
2022–24 (test years 2022, 2023, 2024) and 2025–26 (already opened; shown alongside).

## Q1 forecast comparison
For each asset (ETH, BTC) × schedule (S6, S24) × family (linear, trees):
M1 vs M0, M2 vs M1, M2 vs IV — mean squared-error difference of log realised
volatility to expiry, 95 % block-bootstrap interval, years better, per group.

## Q2 straddle backtest
For each asset × schedule × family × variant (M1, M2) × θ ∈ {0.05, 0.10, 0.20}, and the
sign-flipped rule: per-group mean P&L per trade (USD per coin) with interval, total P&L,
trades, hit rate, Sharpe on decision days, maximum drawdown, P&L per premium, long and
short sides separately. Benchmarks: always buy, always sell.
Read as positive only if the M2 rule beats the M1 rule and both benchmarks after costs
in 2022–24.

## Q3 BTC
Q1 and Q2 for BTC with Ethereum-chain flows.

## Q4 event study
ETH and BTC; inflow events, outflow events, placebo activity events; responses k = 1 … 12
h: realised-volatility surprise against the out-of-fold M0 forecast, pre-event surprise,
change in near-expiry implied volatility, signed return; means with intervals; groups
2019–24 and 2025–26 (implied volatility from 2021-04).

## Q5 Tron
`TRON_PROBE.md`: free full-history source for USDT TRC-20 transfers and Tron exchange
labels — go or no-go with a cost estimate.
```

`research/onchain-b5-2026-10-19/STATE.md`:

```markdown
# Branch B5 state

2026-10-19 — Registered (charter, config, pre-declared plan). No B5 data read yet.

Next safe action: implement plan tasks 2–8; fetch option trades, DVOL and BTC bars
(B5-CP1); decision tables (B5-CP2); forecast comparison and backtests (B5-CP3); event
study, Tron probe, `RESULTS.md` (B5-CP4).
```

Add to `.gitignore` after the B4 line:

```
# B5 option-trade, DVOL and decision artifacts
/research_artifacts/onchain-b5/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_config.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add .gitignore tradingagents/research/onchain_b5 tests/research/onchain_b5 research/onchain-b5-2026-10-19
git commit -m "feat(onchain-b5): register option-market study, config and pre-declared plan

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Deribit option trades and DVOL

**Files:**
- Create: `tradingagents/research/onchain_b5/deribit.py`
- Test: `tests/research/onchain_b5/test_deribit.py`

**Interfaces:**
- Produces: `deribit.COLUMNS`; `deribit.Unavailable(errors)`; `deribit.fetch_day(get, currency, day, cfg, sleep=time.sleep) -> DataFrame[COLUMNS]`; `deribit.with_retries(fn, retries, sleep=time.sleep)`; `deribit.save_day(df, path)`; `deribit.load_day(path) -> DataFrame`; `deribit.fetch_dvol(get, currency, start, end, cfg, sleep=time.sleep) -> Series` (index naive UTC candle start, close values).

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b5/test_deribit.py
import json

import pandas as pd
import pytest

from tradingagents.research.onchain_b5 import config, deribit

T0 = int(pd.Timestamp('2023-06-01', tz='UTC').timestamp() * 1000)


def _trade(i, ts):
    return {'timestamp': ts, 'trade_id': f'E-{i}', 'instrument_name': 'ETH-2JUN23-1900-C', 'iv': 50.0 + i,
            'price': 0.01, 'index_price': 1900.0, 'amount': 1.0, 'direction': 'buy' if i % 2 else 'sell', 'extra': 1}


def test_fetch_day_paginates_and_dedupes():
    trades = [_trade(i, T0 + 1000 * (i // 2)) for i in range(7)]   # pairs share a timestamp
    calls = []

    def get(url):
        calls.append(url)
        s = int(url.split('start_timestamp=')[1].split('&')[0])
        rest = [t for t in trades if t['timestamp'] >= s]
        page = rest[:3]
        return json.dumps({'result': {'trades': page, 'has_more': len(rest) > 3}}).encode()

    df = deribit.fetch_day(get, 'ETH', '2023-06-01', config.load(), sleep=lambda s: None)
    assert list(df.columns) == deribit.COLUMNS and sorted(df['trade_id']) == [f'E-{i}' for i in range(7)]
    assert 'kind=option' in calls[0] and 'sorting=asc' in calls[0]


def test_retries_then_unavailable():
    slept = []

    def boom():
        raise OSError('net')
    with pytest.raises(deribit.Unavailable):
        deribit.with_retries(boom, [1, 2], sleep=slept.append)
    assert slept == [1, 2]


def test_save_load_round_trip(tmp_path):
    df = pd.DataFrame([{k: _trade(1, T0)[k] for k in deribit.COLUMNS}])
    deribit.save_day(df, tmp_path / 'ETH' / '2023-06-01.parquet')
    pd.testing.assert_frame_equal(deribit.load_day(tmp_path / 'ETH' / '2023-06-01.parquet'), df)
    deribit.save_day(df.iloc[:0], tmp_path / 'ETH' / 'empty.parquet')
    assert len(deribit.load_day(tmp_path / 'ETH' / 'empty.parquet')) == 0


def test_fetch_dvol_follows_continuation():
    hours = [T0 + 3_600_000 * h for h in range(10)]

    def get(url):
        e = int(url.split('end_timestamp=')[1].split('&')[0])
        rows = [[h, 1, 1, 1, 50.0 + i] for i, h in enumerate(hours) if h <= e][-4:]
        cont = rows[0][0] - 3_600_000 if rows and rows[0][0] > hours[0] else None
        return json.dumps({'result': {'data': rows, 'continuation': cont}}).encode()

    s = deribit.fetch_dvol(get, 'ETH', '2023-06-01', '2023-06-01', config.load(), sleep=lambda x: None)
    assert len(s) == 10 and s.index[0] == pd.Timestamp('2023-06-01 00:00') and s.iloc[-1] == 59.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_deribit.py -q`
Expected: FAIL with `ImportError: cannot import name 'deribit'`

- [ ] **Step 3: Implement deribit.py**

```python
# tradingagents/research/onchain_b5/deribit.py
"""Deribit public history (spec §3): every option trade of a UTC day with its implied
volatility and taker side, and hourly DVOL. Raw pages are not kept."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd

COLUMNS = ['timestamp', 'trade_id', 'instrument_name', 'iv', 'price', 'index_price', 'amount', 'direction']
DAY_MS = 86_400_000


class Unavailable(RuntimeError):
    def __init__(self, errors):
        super().__init__(f'unavailable after {len(errors)} attempts: {errors[-1] if errors else ""}')
        self.errors = errors


def _ms(day):
    return int(pd.Timestamp(day, tz='UTC').timestamp() * 1000)


def fetch_day(get, currency, day, cfg, sleep=time.sleep):
    d = cfg['deribit']
    s, end = _ms(day), _ms(day) + DAY_MS - 1
    rows, seen = [], set()
    while True:
        url = (f"{d['trades_url']}?currency={currency}&kind=option&start_timestamp={s}&end_timestamp={end}"
               f"&count={d['count']}&include_old=true&sorting=asc")
        res = json.loads(get(url))['result']
        trades = res['trades']
        new = [t for t in trades if t['trade_id'] not in seen]
        for t in new:
            seen.add(t['trade_id'])
            rows.append({k: t.get(k) for k in COLUMNS})
        if not res.get('has_more') or not trades:
            break
        last = trades[-1]['timestamp']
        s = last if new else last + 1        # same-millisecond trades may straddle pages
        sleep(d['pause'])
    return pd.DataFrame(rows, columns=COLUMNS)


def with_retries(fn, retries, sleep=time.sleep):
    errors = []
    for attempt in range(len(retries) + 1):
        try:
            return fn()
        except Exception as e:          # network or decode failure: retry, then mark unavailable
            errors.append(repr(e))
            if attempt < len(retries):
                sleep(retries[attempt])
    raise Unavailable(errors)


def save_day(df, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name('.' + path.name + '.tmp')
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)


def load_day(path):
    return pd.read_parquet(path)


def fetch_dvol(get, currency, start, end, cfg, sleep=time.sleep):
    url0 = cfg['deribit']['dvol_url']
    s, e = _ms(start), _ms(end) + DAY_MS
    vals = {}
    while e > s:
        res = json.loads(get(f'{url0}?currency={currency}&start_timestamp={s}&end_timestamp={e}&resolution=3600'))['result']
        for row in res['data']:
            vals[int(row[0])] = float(row[4])
        cont = res.get('continuation')
        if not res['data'] or cont is None or cont >= e:
            break
        e = cont
        sleep(cfg['deribit']['pause'])
    keys = sorted(k for k in vals if s <= k < _ms(end) + DAY_MS)
    return pd.Series([vals[k] for k in keys], index=pd.to_datetime(keys, unit='ms'), name='dvol')
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_deribit.py -q`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b5/deribit.py tests/research/onchain_b5/test_deribit.py
git commit -m "feat(onchain-b5): Deribit option-trade and DVOL fetch with pagination, retries and day files

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Instrument parsing and decision-time implied volatility

**Files:**
- Create: `tradingagents/research/onchain_b5/implied.py`
- Test: `tests/research/onchain_b5/test_implied.py`

**Interfaces:**
- Consumes: day DataFrames with `deribit.COLUMNS`.
- Produces: `implied.parse(names) -> DataFrame[expiry, strike, kind]`; `implied.prepare(day_df) -> DataFrame` (adds `ts`, `expiry`, `strike`, `kind`); `implied.wmedian(values, weights) -> float`; `implied.decision_iv(trades, t, expiry, c) -> dict | None` with keys `iv_mid, iv_ask, iv_bid, n_trades, strikes`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b5/test_implied.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import config, implied

C = config.load()['implied']


def test_parse_instrument_names():
    p = implied.parse(['ETH-2JUN21-2500-C', 'BTC-28JUN19-11000-P'])
    assert list(p['expiry']) == [pd.Timestamp('2021-06-02 08:00'), pd.Timestamp('2019-06-28 08:00')]
    assert list(p['strike']) == [2500.0, 11000.0] and list(p['kind']) == ['C', 'P']


def test_wmedian():
    assert implied.wmedian(np.array([3.0, 1.0, 2.0]), np.array([1.0, 1.0, 5.0])) == 2.0


def _day(rows):
    ts0 = int(pd.Timestamp('2023-06-01', tz='UTC').timestamp() * 1000)
    return implied.prepare(pd.DataFrame([{'timestamp': ts0 + int(h * 3_600_000), 'trade_id': str(i), 'instrument_name': n,
                                          'iv': iv, 'price': 0.01, 'index_price': 1900.0, 'amount': a, 'direction': d}
                                         for i, (h, n, iv, a, d) in enumerate(rows)]))


def test_decision_iv_window_moneyness_sides_and_eligibility():
    t = pd.Timestamp('2023-06-01 03:00')                         # window [01:00, 03:00)
    exp = pd.Timestamp('2023-06-01 08:00')
    tr = _day([(0.5, 'ETH-1JUN23-1900-C', 99.0, 1, 'buy'),       # before the window: excluded
               (1.0, 'ETH-1JUN23-1900-C', 50.0, 2, 'buy'),
               (1.5, 'ETH-1JUN23-1900-P', 52.0, 1, 'sell'),
               (1.6, 'ETH-1JUN23-1925-C', 48.0, 1, 'sell'),
               (1.7, 'ETH-1JUN23-2100-C', 80.0, 5, 'buy'),          # far strike: excluded
               (1.8, 'ETH-2JUN23-1900-C', 70.0, 5, 'buy'),          # other expiry: excluded
               (3.1, 'ETH-1JUN23-1900-C', 90.0, 5, 'buy')])         # after t: excluded
    r = implied.decision_iv(tr, t, exp, C)
    assert r['n_trades'] == 3 and r['iv_mid'] == 50.0 and r['iv_ask'] == 50.0 and r['iv_bid'] == 48.0
    assert r['strikes'] == [1900.0, 1925.0]
    assert implied.decision_iv(tr, t, pd.Timestamp('2023-06-02 08:00'), C) is None    # fewer than 3 trades
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_implied.py -q`
Expected: FAIL with `ImportError: cannot import name 'implied'`

- [ ] **Step 3: Implement implied.py**

```python
# tradingagents/research/onchain_b5/implied.py
"""Instrument parsing and decision-time implied volatility (spec §4): near-ATM trades on the
target expiry in [t - lookback, t), amount-weighted medians over all, taker-buy (ask) and
taker-sell (bid) trades."""
from __future__ import annotations

import numpy as np
import pandas as pd

MONTHS = {m: i + 1 for i, m in enumerate(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'])}


def parse(names):
    parts = pd.Series(list(names)).str.split('-', expand=True)
    m = parts[1].str.extract(r'^(\d{1,2})([A-Z]{3})(\d{2})$')
    expiry = pd.to_datetime(pd.DataFrame({'year': 2000 + m[2].astype(int), 'month': m[1].map(MONTHS),
                                          'day': m[0].astype(int)})) + pd.Timedelta(hours=8)
    return pd.DataFrame({'expiry': expiry, 'strike': parts[2].astype(float), 'kind': parts[3]})


def prepare(day_df):
    df = day_df.reset_index(drop=True).copy()
    df['ts'] = pd.to_datetime(df['timestamp'], unit='ms')
    if len(df):
        p = parse(df['instrument_name'])
        df[['expiry', 'strike', 'kind']] = p[['expiry', 'strike', 'kind']].to_numpy()
        df['expiry'] = pd.to_datetime(df['expiry'])
        df['strike'] = df['strike'].astype(float)
    else:
        df['expiry'], df['strike'], df['kind'] = pd.Series(dtype='datetime64[ns]'), pd.Series(dtype=float), pd.Series(dtype=object)
    return df


def wmedian(values, weights):
    v, w = np.asarray(values, float), np.asarray(weights, float)
    o = np.argsort(v, kind='stable')
    c = np.cumsum(w[o])
    return float(v[o][np.searchsorted(c, 0.5 * c[-1])])


def decision_iv(trades, t, expiry, c):
    lo = t - pd.Timedelta(hours=c['lookback_h'])
    win = trades[(trades['ts'] >= lo) & (trades['ts'] < t) & (trades['expiry'] == expiry)]
    atm = win[np.abs(np.log(win['strike'] / win['index_price'])) <= c['moneyness']]
    if len(atm) < c['min_trades']:
        return None
    buy, sell = atm[atm['direction'] == 'buy'], atm[atm['direction'] == 'sell']
    return {'iv_mid': wmedian(atm['iv'], atm['amount']),
            'iv_ask': wmedian(buy['iv'], buy['amount']) if len(buy) else float('nan'),
            'iv_bid': wmedian(sell['iv'], sell['amount']) if len(sell) else float('nan'),
            'n_trades': int(len(atm)), 'strikes': sorted(float(k) for k in atm['strike'].unique())}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_implied.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b5/implied.py tests/research/onchain_b5/test_implied.py
git commit -m "feat(onchain-b5): instrument parsing and decision-time implied volatility from taker trades

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Decision tables (features, targets, prices, spread fill)

**Files:**
- Create: `tradingagents/research/onchain_b5/decisions.py`
- Test: `tests/research/onchain_b5/test_decisions.py`

**Interfaces:**
- Consumes: `onchain_b4.dataset4.price_features(bars)`; `implied.decision_iv`; prepared trades by day.
- Produces: `decisions.px_features(bars) -> DataFrame` (`px_*`); `decisions.realized_logvol(closes, t, tau_h) -> float`; `decisions.fill_spread(df, window) -> DataFrame`; `decisions.build(sched, bars, dvol, flows, trades_for_day, cfg) -> DataFrame` indexed by decision time with columns `h0_*, px_*, mk_dvol, mk_dvol_chg24, mk_iv, eth_*, stable_*, y, s0, sT, K, tau_h, iv_mid, iv_ask, iv_bid, n_trades`; `decisions.load_bars(path) -> DataFrame[close, qvol]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b5/test_decisions.py
import json

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import config, decisions, implied

CFG = config.load()


def _bars(start, hours, seed=1):
    idx = pd.date_range(start, periods=hours, freq='h')
    rng = np.random.default_rng(seed)
    return pd.DataFrame({'close': 1900 * np.exp(np.cumsum(rng.normal(0, 0.005, hours))),
                         'qvol': rng.gamma(2.0, 1e6, hours)}, index=idx)


def test_realized_logvol():
    idx = pd.date_range('2023-06-01', periods=10, freq='h')
    closes = pd.Series(100 * np.exp(0.01 * np.arange(10)), index=idx)
    t = pd.Timestamp('2023-06-01 03:00')
    want = np.log(np.sqrt(6 * 0.01 ** 2 * 8760 / 6))
    assert np.isclose(decisions.realized_logvol(closes, t, 6), want)
    assert np.isnan(decisions.realized_logvol(closes, pd.Timestamp('2023-06-01 06:00'), 6))


def test_fill_spread_uses_only_earlier_rows():
    df = pd.DataFrame({'iv_mid': [50.0, 50.0, 50.0, 50.0], 'iv_ask': [52.0, np.nan, 60.0, np.nan],
                       'iv_bid': [48.0, 49.0, 40.0, np.nan]}, index=pd.date_range('2023-01-01', periods=4))
    f = decisions.fill_spread(df, 30)
    assert f['iv_ask'].iloc[1] == 52.0            # earlier half-spread 2 only
    assert f['iv_ask'].iloc[3] == 50.0 + np.median([2.0, 10.0]) and f['iv_bid'].iloc[3] == 50.0 - 6.0


def _trades_for(day, tag):
    t = pd.Timestamp(day)
    ts0 = int(pd.Timestamp(day, tz='UTC').timestamp() * 1000)
    exp6 = t + pd.Timedelta(hours=8)
    name = f"ETH-{exp6.day}{exp6.strftime('%b').upper()}{exp6.strftime('%y')}-1900-C"
    rows = [{'timestamp': ts0 + int(h * 3_600_000), 'trade_id': f'{day}-{i}', 'instrument_name': name, 'iv': 50.0 + tag,
             'price': 0.01, 'index_price': 1900.0, 'amount': 1.0, 'direction': 'buy' if i % 2 else 'sell'}
            for i, h in enumerate([0.5, 1.0, 1.5, 1.7])]
    return implied.prepare(pd.DataFrame(rows))


def test_build_skips_ineligible_and_is_causal():
    cfg = json.loads(json.dumps(CFG))
    cfg['window'] = {'start': '2023-06-10', 'end': '2023-06-14'}
    bars = _bars('2023-05-01', 24 * 50)
    dvol = pd.Series(60.0, index=bars.index)
    flows = pd.DataFrame({'eth_x__h1z': np.arange(len(bars), dtype=float), 'stable_x__h1z': 1.0}, index=bars.index)
    have = {'2023-06-10', '2023-06-11', '2023-06-13', '2023-06-14'}
    get = lambda day: _trades_for(day, 0) if day in have else None
    a = decisions.build('S6', bars, dvol, flows, get, cfg)
    assert [str(i) for i in a.index] == ['2023-06-10 02:00:00', '2023-06-11 02:00:00', '2023-06-13 02:00:00', '2023-06-14 02:00:00']
    t = a.index[0]
    assert a.loc[t, 'eth_x__h1z'] == flows.loc[t - pd.Timedelta(hours=1), 'eth_x__h1z']
    assert a.loc[t, 's0'] == bars.loc[t - pd.Timedelta(hours=1), 'close'] and a.loc[t, 'sT'] == bars.loc[t + pd.Timedelta(hours=5), 'close']
    assert a.loc[t, 'K'] == 1900.0 and np.isclose(a.loc[t, 'mk_iv'], np.log(0.5))
    bars2 = bars.copy()
    bars2.loc[t:, 'close'] *= 1.5                 # change prices from the decision time on
    flows2 = flows.copy()
    flows2.loc[t:, 'eth_x__h1z'] = -99.0
    b = decisions.build('S6', bars2, dvol, flows2, get, cfg)
    feats = [c for c in a.columns if c.startswith(('h0_', 'px_', 'mk_', 'eth_', 'stable_'))]
    pd.testing.assert_series_equal(a.loc[t, feats], b.loc[t, feats])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_decisions.py -q`
Expected: FAIL with `ImportError: cannot import name 'decisions'`

- [ ] **Step 3: Implement decisions.py**

```python
# tradingagents/research/onchain_b5/decisions.py
"""Decision tables (spec §§4–6): one row per daily decision time with price, option-market and
B4 flow features taken at the last complete hour before t, realised log volatility to expiry,
the index at t and at expiry, the straddle strike, and implied volatilities."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..onchain_b4 import dataset4
from . import implied

H = pd.Timedelta(hours=1)


def load_bars(path):
    doc = json.loads(Path(path).read_text())
    idx = pd.to_datetime(list(doc), format='%Y-%m-%dT%H')
    v = list(doc.values())
    return pd.DataFrame({'close': [float(x[0]) for x in v], 'qvol': [float(x[1]) for x in v]}, index=idx).sort_index()


def _full(bars):
    return bars.reindex(pd.date_range(bars.index.min(), bars.index.max(), freq='h'))


def px_features(bars):
    b = _full(bars)
    lc = np.log(b['close'])
    r = lc.diff()
    f = pd.DataFrame(index=b.index)
    f['px_abs_r1'] = r.abs()
    f['px_rv4'] = np.sqrt((r ** 2).rolling(4, min_periods=4).sum())
    f['px_rv6'] = np.sqrt((r ** 2).rolling(6, min_periods=6).sum())
    f['px_lvol1'] = np.log(b['qvol'])
    f['px_lvol4'] = np.log(b['qvol'].rolling(4, min_periods=4).sum())
    return f.replace([np.inf, -np.inf], np.nan)


def realized_logvol(closes, t, tau_h):
    seg = closes.reindex(pd.date_range(t - H, periods=tau_h + 1, freq='h'))
    if seg.isna().any():
        return float('nan')
    r = np.diff(np.log(seg.to_numpy(float)))
    return float(np.log(max(np.sqrt((r ** 2).sum() * 8760 / tau_h), 1e-8)))


def fill_spread(df, window):
    df = df.copy()
    hs = ((df['iv_ask'] - df['iv_bid']) / 2).where(df['iv_ask'].notna() & df['iv_bid'].notna())
    med = hs.shift(1).rolling(window, min_periods=1).median()
    df['iv_ask'] = df['iv_ask'].fillna(df['iv_mid'] + med)
    df['iv_bid'] = df['iv_bid'].fillna(df['iv_mid'] - med)
    return df


def build(sched, bars, dvol, flows, trades_for_day, cfg):
    s = cfg['schedules'][sched]
    tau = s['tau_h']
    full = _full(bars)
    closes = full['close']
    pf = dataset4.price_features(bars).join(px_features(bars))
    w = cfg['window']
    times = pd.date_range(pd.Timestamp(w['start']) + pd.Timedelta(hours=s['hour']),
                          pd.Timestamp(w['end']) + pd.Timedelta(hours=s['hour']), freq='D')
    rows = {}
    for t in times:
        tr = trades_for_day(t.date().isoformat())
        if tr is None or not len(tr):
            continue
        expiry = t.normalize() + pd.Timedelta(days=s['expiry_days'], hours=8)
        iv = implied.decision_iv(tr, t, expiry, cfg['implied'])
        bar = t - H
        if iv is None or bar not in pf.index:
            continue
        s0, s_t = closes.get(bar), closes.get(expiry - H)
        dv, dv24 = dvol.get(bar), dvol.get(bar - 24 * H)
        frow = flows.loc[bar].to_dict() if bar in flows.index else {c: np.nan for c in flows.columns}
        rows[t] = {**pf.loc[bar].to_dict(), **frow,
                   'mk_dvol': np.log(dv) if dv else np.nan,
                   'mk_dvol_chg24': np.log(dv) - np.log(dv24) if dv and dv24 else np.nan,
                   'mk_iv': np.log(iv['iv_mid'] / 100.0),
                   'y': realized_logvol(closes, t, tau), 's0': s0, 'sT': s_t,
                   'K': min(iv['strikes'], key=lambda k: abs(k - s0)) if s0 is not None and s0 == s0 else np.nan,
                   'tau_h': float(tau), 'iv_mid': iv['iv_mid'], 'iv_ask': iv['iv_ask'], 'iv_bid': iv['iv_bid'],
                   'n_trades': iv['n_trades']}
    df = pd.DataFrame.from_dict(rows, orient='index').sort_index()
    if not len(df):
        return df
    df = fill_spread(df, cfg['implied']['spread_window'])
    need = [c for c in df.columns if c.startswith(('h0_', 'px_', 'mk_', 'eth_', 'stable_'))] + ['y', 's0', 'sT', 'K', 'iv_ask', 'iv_bid']
    return df[df[need].notna().all(axis=1)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_decisions.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b5/decisions.py tests/research/onchain_b5/test_decisions.py
git commit -m "feat(onchain-b5): causal decision tables with implied volatility, prices and flow features

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Walk-forward forecasts and comparisons (Q1)

**Files:**
- Create: `tradingagents/research/onchain_b5/forecast.py`
- Test: `tests/research/onchain_b5/test_forecast.py`

**Interfaces:**
- Consumes: decision tables from Task 4; `onchain_b2.screen.fit_predict/folds`; `onchain_b4.screen4.interval`.
- Produces: `forecast.columns(df, set_name, cfg) -> list[str]`; `forecast.run(df, cfg) -> (preds: DataFrame[f'{family}:{set}'], results: list[dict])` with result keys `family, set, comparator, group, n, mean_diff, lo, hi, wins, years, loss_set, loss_comparator`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b5/test_forecast.py
import copy

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import config, forecast


def _table(rng):
    idx = pd.date_range('2021-04-01 02:00', '2026-10-12', freq='D')
    n = len(idx)
    df = pd.DataFrame({'h0_r1': rng.normal(size=n), 'px_abs_r1': rng.normal(size=n), 'mk_dvol': rng.normal(size=n),
                       'mk_iv': rng.normal(size=n), 'eth_x__h1z': rng.normal(size=n), 'stable_x__h1z': rng.normal(size=n)},
                      index=idx)
    df['y'] = 0.8 * df['mk_iv'] + 1.5 * df['stable_x__h1z'] + 0.3 * rng.normal(size=n)
    df['tau_h'] = 6.0
    return df


def test_forecast_comparisons_groups_and_signal():
    cfg = copy.deepcopy(config.load())
    cfg['families'] = ['linear']
    preds, res = forecast.run(_table(np.random.default_rng(3)), cfg)
    assert list(preds.columns) == ['linear:M0', 'linear:M1', 'linear:M2', 'linear:IV']
    assert preds.loc[:'2021-12-31'].isna().all().all() and preds.loc['2022-01-01':].notna().all().all()
    assert len(res) == 3 * 2
    get = {(r['set'], r['comparator'], r['group']): r for r in res}
    assert get[('M2', 'M1', '2022-24')]['hi'] < 0 and get[('M2', 'IV', '2025-26')]['hi'] < 0
    assert get[('M1', 'M0', '2022-24')]['hi'] < 0
    assert set(get[('M2', 'M1', '2022-24')]['years']) == {2022, 2023, 2024}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_forecast.py -q`
Expected: FAIL with `ImportError: cannot import name 'forecast'`

- [ ] **Step 3: Implement forecast.py**

```python
# tradingagents/research/onchain_b5/forecast.py
"""Walk-forward forecasts of log realised volatility to expiry and the pre-declared comparisons
(spec §5): M1 vs M0, M2 vs M1, M2 vs IV, per family and group."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2.screen import fit_predict, folds
from ..onchain_b4.screen4 import interval


def columns(df, set_name, cfg):
    return sorted(c for c in df.columns if c.startswith(tuple(cfg['sets'][set_name])))


def run(df, cfg):
    df = df.sort_index()
    y = df['y'].to_numpy(float)
    fc, g = cfg['folds'], cfg['gate']
    fl = folds(df.index, fc['test_years'], float(df['tau_h'].iloc[0]) / 24)
    tested = np.zeros(len(df), bool)
    for _, _, te in fl:
        tested |= te
    preds = {}
    for fam in cfg['families']:
        for s in cfg['sets']:
            X = df[columns(df, s, cfg)].to_numpy(float)
            p = np.full(len(df), np.nan)
            for _, tr, te in fl:
                if te.any() and tr.sum() >= fc['min_train']:
                    p[te] = fit_predict(fam, 'regression', X[tr], y[tr], X[te], fc['inner_len'], cfg)
            preds[f'{fam}:{s}'] = p
    P = pd.DataFrame(preds, index=df.index)
    years = df.index.year.to_numpy()
    results = []
    for fam in cfg['families']:
        for a, b in cfg['comparisons']:
            la = (y - P[f'{fam}:{a}'].to_numpy()) ** 2
            lb = (y - P[f'{fam}:{b}'].to_numpy()) ** 2
            for name, yrs in cfg['groups'].items():
                m = tested & np.isin(years, yrs) & np.isfinite(la) & np.isfinite(lb)
                d = (la - lb)[m]
                lo, hi = interval(d, g['block'], g['draws'], g['seed'], g['chunk']) if len(d) >= g['block'] else (np.nan, np.nan)
                per_year = {int(yr): float(d[years[m] == yr].mean()) for yr in yrs if (years[m] == yr).any()}
                results.append({'family': fam, 'set': a, 'comparator': b, 'group': name, 'n': int(len(d)),
                                'mean_diff': float(d.mean()) if len(d) else np.nan, 'lo': lo, 'hi': hi,
                                'wins': int(sum(v < 0 for v in per_year.values())), 'years': per_year,
                                'loss_set': float(la[m].mean()) if len(d) else np.nan,
                                'loss_comparator': float(lb[m].mean()) if len(d) else np.nan})
    return P, results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_forecast.py -q`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b5/forecast.py tests/research/onchain_b5/test_forecast.py
git commit -m "feat(onchain-b5): walk-forward volatility forecasts and pre-declared comparisons

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Straddle pricing, P&L and backtest (Q2)

**Files:**
- Create: `tradingagents/research/onchain_b5/straddle.py`
- Test: `tests/research/onchain_b5/test_straddle.py`

**Interfaces:**
- Consumes: decision table columns `s0, K, sT, tau_h, mk_iv, iv_ask, iv_bid`; forecast preds `f'{family}:{variant}'`.
- Produces: `straddle.black76(F, K, T, sigma) -> (call, put)`; `straddle.pnl(side, s0, K, sT, T, iv_ask, iv_bid, rate, cap) -> (pnl, premium)`; `straddle.sides(z, theta) -> ndarray[int]`; `straddle.metrics(p, side, premium, index, groups, gate) -> dict[group -> dict]`; `straddle.backtest(df, preds, cfg) -> list[dict]` with keys `rule, family, variant, theta, groups`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b5/test_straddle.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import config, straddle


def test_black76_values_parity_and_extremes():
    c, p = straddle.black76(np.array([100.0]), np.array([100.0]), np.array([1.0]), np.array([0.2]))
    assert np.isclose(c[0], 7.9656, atol=1e-4) and np.isclose(p[0], 7.9656, atol=1e-4)
    F, K = np.array([2000.0, 2000.0, 2000.0]), np.array([1500.0, 2000.0, 3000.0])
    c, p = straddle.black76(F, K, np.full(3, 6 / 8760), np.full(3, 0.6))
    assert np.isfinite(c).all() and np.isfinite(p).all() and np.allclose(c - p, F - K)


def test_pnl_signs_fees_and_cap():
    s0, K, T = np.array([2000.0, 2000.0]), np.array([2000.0, 2000.0]), np.array([6 / 8760] * 2)
    iv = np.array([50.0, 50.0])
    big = np.array([2100.0, 2100.0])
    p, prem = straddle.pnl(np.array([1, -1]), s0, K, big, T, iv, iv, 0.0003, 0.125)
    # long + short on the same straddle sum to minus both sides' fees: entry 0.6 per leg, delivery 0.63 on the call
    assert p[0] > 0 > p[1] and np.isclose(p[0] + p[1], -2 * (2 * 0.6 + 0.63), atol=1e-6)
    p0, _ = straddle.pnl(np.array([0]), s0[:1], K[:1], big[:1], T[:1], iv[:1], iv[:1], 0.0003, 0.125)
    assert p0[0] == 0.0
    one = lambda x: np.array([x])
    c, pu = straddle.black76(one(2000.0), one(2500.0), one(6 / 8760), one(0.5))
    out, _ = straddle.pnl(one(1), one(2000.0), one(2500.0), one(2000.0), one(6 / 8760), one(50.0), one(50.0), 0.0003, 0.125)
    assert 0.125 * c[0] < 0.6                               # far OTM call: the 12.5 % cap binds
    assert np.isclose(out[0], 500.0 - (c[0] + pu[0]) - (0.125 * c[0] + 0.6) - 0.6)


def test_sides_and_backtest_benchmarks():
    assert list(straddle.sides(np.array([0.3, 0.0, -0.3]), 0.1)) == [1, 0, -1]
    idx = pd.date_range('2022-01-01 02:00', '2026-06-30', freq='D')
    rng = np.random.default_rng(1)
    n = len(idx)
    real = rng.normal(np.log(0.5), 0.3, n)
    df = pd.DataFrame({'s0': 2000.0, 'K': 2000.0, 'tau_h': 6.0, 'mk_iv': np.log(0.5), 'iv_ask': 51.0, 'iv_bid': 49.0,
                       'y': real}, index=idx)
    df['sT'] = 2000.0 * np.exp(0.798 * np.exp(real) * np.sqrt(6 / 8760) * rng.choice([-1, 1], n))   # |move| = E|Z| σ√T
    preds = pd.DataFrame({'linear:M1': rng.normal(np.log(0.5), 0.3, n), 'linear:M2': real}, index=idx)
    cfg = config.load()
    cfg = {**cfg, 'families': ['linear']}
    out = straddle.backtest(df, preds, cfg)
    get = {(o['rule'], o['variant'], o['theta']): o for o in out}
    assert ('always_buy', None, None) in get and ('always_sell', None, None) in get
    assert get[('signal', 'M2', 0.1)]['groups']['2022-24']['total'] > get[('signal', 'M1', 0.1)]['groups']['2022-24']['total']
    assert get[('flip', 'M2', 0.1)]['groups']['2022-24']['total'] < 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_straddle.py -q`
Expected: FAIL with `ImportError: cannot import name 'straddle'`

- [ ] **Step 3: Implement straddle.py**

```python
# tradingagents/research/onchain_b5/straddle.py
"""At-the-money daily straddle backtest (spec §6): Black-76 at the ask (buys) or bid (sells)
implied volatility, Deribit fees capped at 12.5 % of each leg, payoff |S_T - K| at expiry."""
from __future__ import annotations

import numpy as np
from scipy.special import ndtr

from ..onchain_b4.screen4 import interval


def black76(F, K, T, sigma):
    F, K, T, sigma = (np.asarray(x, float) for x in (F, K, T, sigma))
    v = sigma * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * v ** 2) / v
    d2 = d1 - v
    call = F * ndtr(d1) - K * ndtr(d2)
    put = K * ndtr(-d2) - F * ndtr(-d1)
    return call, put


def pnl(side, s0, K, sT, T, iv_ask, iv_bid, rate, cap):
    side = np.asarray(side, int)
    sigma = np.where(side > 0, iv_ask, iv_bid) / 100.0
    c, p = black76(s0, K, T, sigma)
    fee_in = np.minimum(rate * s0, cap * c) + np.minimum(rate * s0, cap * p)
    ic, ip = np.maximum(sT - K, 0.0), np.maximum(K - sT, 0.0)
    fee_out = np.where(ic > 0, np.minimum(rate * sT, cap * ic), 0.0) + np.where(ip > 0, np.minimum(rate * sT, cap * ip), 0.0)
    premium = c + p
    gross = np.where(side > 0, ic + ip - premium, premium - ic - ip)
    out = np.where(side == 0, 0.0, gross - fee_in - fee_out)
    return out, premium


def sides(z, theta):
    z = np.asarray(z, float)
    return np.where(z > theta, 1, np.where(z < -theta, -1, 0))


def _maxdd(p):
    c = np.cumsum(p)
    return float(np.max(np.maximum.accumulate(np.concatenate([[0.0], c]))[1:] - c)) if len(c) else 0.0


def metrics(p, side, premium, index, groups, gate):
    years = index.year.to_numpy()
    out = {}
    for name, yrs in groups.items():
        m = np.isin(years, yrs)
        pm, sm, prm = p[m], side[m], premium[m]
        tr = sm != 0
        tp = pm[tr]
        lo, hi = interval(tp, gate['block'], gate['draws'], gate['seed'], gate['chunk']) if len(tp) >= gate['block'] else (np.nan, np.nan)
        sd = pm.std()
        out[name] = {'decisions': int(m.sum()), 'trades': int(tr.sum()), 'mean_trade': float(tp.mean()) if len(tp) else np.nan,
                     'lo': lo, 'hi': hi, 'total': float(pm.sum()), 'hit': float((tp > 0).mean()) if len(tp) else np.nan,
                     'sharpe': float(pm.mean() / sd * np.sqrt(365)) if sd > 0 else np.nan, 'maxdd': _maxdd(pm),
                     'per_premium': float(tp.sum() / prm[tr].sum()) if tr.any() else np.nan,
                     'long_mean': float(pm[sm > 0].mean()) if (sm > 0).any() else np.nan, 'long_n': int((sm > 0).sum()),
                     'short_mean': float(pm[sm < 0].mean()) if (sm < 0).any() else np.nan, 'short_n': int((sm < 0).sum())}
    return out


def backtest(df, preds, cfg):
    st, g = cfg['straddle'], cfg['gate']
    valid = preds.notna().all(axis=1).to_numpy()
    d = df[valid]
    P = preds[valid]
    T = d['tau_h'].to_numpy(float) / 8760
    args = (d['s0'].to_numpy(float), d['K'].to_numpy(float), d['sT'].to_numpy(float), T,
            d['iv_ask'].to_numpy(float), d['iv_bid'].to_numpy(float), st['fee_rate'], st['fee_cap'])
    out = []

    def add(rule, fam, var, theta, side):
        p, prem = pnl(side, *args)
        out.append({'rule': rule, 'family': fam, 'variant': var, 'theta': theta,
                    'groups': metrics(p, side, prem, d.index, cfg['groups'], g)})

    add('always_buy', None, None, None, np.ones(len(d), int))
    add('always_sell', None, None, None, -np.ones(len(d), int))
    for fam in cfg['families']:
        for var in st['variants']:
            z = P[f'{fam}:{var}'].to_numpy(float) - d['mk_iv'].to_numpy(float)
            for theta in st['thetas']:
                s = sides(z, theta)
                add('signal', fam, var, theta, s)
                add('flip', fam, var, theta, -s)
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_straddle.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b5/straddle.py tests/research/onchain_b5/test_straddle.py
git commit -m "feat(onchain-b5): Black-76 straddle pricing, Deribit fees and cost-aware backtest

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Event study (Q4)

**Files:**
- Create: `tradingagents/research/onchain_b5/events.py`
- Test: `tests/research/onchain_b5/test_events.py`

**Interfaces:**
- Consumes: B4 `features/hourly.parquet` (transformed) and `features/hourly_raw.parquet`; `dataset4.zscore`, `dataset4.price_features`; `decisions.px_features`; `implied.prepare`, `implied.wmedian`; `fit_predict`, `folds`, `interval`.
- Produces: `events.first_per_window(times, spacing_h) -> list[Timestamp]`; `events.flow_events(raw, trans, kind, cfg) -> list`; `events.placebo_events(bars, n, cfg) -> list`; `events.vol_targets(bars, kmax) -> (Y, R)`; `events.surprises(bars, cfg) -> DataFrame[s1..sK]`; `events.iv_series(trades_for_day, days, cfg) -> Series`; `events.responses(evts, S, R, iv, kmax, gate) -> list[dict]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b5/test_events.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import config, events, implied

CFG = config.load()


def test_first_per_window_spacing():
    t = pd.to_datetime(['2023-01-01 00:00', '2023-01-01 05:00', '2023-01-02 00:00', '2023-01-02 01:00', '2023-01-03 02:00'])
    assert [str(x) for x in events.first_per_window(t, 24)] == ['2023-01-01 00:00:00', '2023-01-02 00:00:00', '2023-01-03 02:00:00']


def _bars(n, seed=2):
    idx = pd.date_range('2022-01-01', periods=n, freq='h')
    rng = np.random.default_rng(seed)
    return pd.DataFrame({'close': 1000 * np.exp(np.cumsum(rng.normal(0, 0.004, n))), 'qvol': rng.gamma(2.0, 1e6, n)}, index=idx)


def test_placebo_size_and_vol_targets():
    bars = _bars(24 * 120)
    pl = events.placebo_events(bars, 5, CFG)
    assert len(pl) <= 5 and pl == sorted(pl)
    Y, R = events.vol_targets(bars, 3)
    lc = np.log(bars['close'])
    b = bars.index[100]
    r = lc.diff()
    assert np.isclose(Y.loc[b, 'y3'], np.log(np.sqrt((r.iloc[101:104] ** 2).sum() * 8760 / 3)))
    assert np.isclose(R.loc[b, 'r3'], lc.iloc[103] - lc.iloc[100])


def test_responses_detect_injected_jump():
    idx = pd.date_range('2022-01-01', periods=2000, freq='h')
    S = pd.DataFrame({f's{k}': 0.0 for k in (1, 2)}, index=idx)
    R = pd.DataFrame({f'r{k}': 0.0 for k in (1, 2)}, index=idx)
    ev = list(idx[200::100][:15])
    for e in ev:
        S.loc[e, 's1'] = 1.0 + 0.01 * ev.index(e)
        S.loc[e, 's2'] = 0.5
    iv = pd.Series(50.0, index=idx)
    out = events.responses(ev, S, R, iv, 2, {**CFG['gate'], 'block': 1})
    k1 = [o for o in out if o['k'] == 1][0]
    assert k1['post_vol']['mean'] > 0.9 and k1['post_vol']['lo'] > 0.9 and k1['pre_vol']['mean'] == 0.0
    assert k1['d_iv']['mean'] == 0.0 and k1['n'] == 15


def test_iv_series_uses_nearest_live_expiry():
    ts0 = int(pd.Timestamp('2023-06-01', tz='UTC').timestamp() * 1000)
    rows = [(6.5, 'ETH-1JUN23-1900-C', 99.0),      # expires 08:00, bin 06:00 ends 07:00 < 08:00 + 2h rule: excluded
            (6.6, 'ETH-2JUN23-1900-C', 55.0), (6.7, 'ETH-2JUN23-1900-P', 57.0), (6.8, 'ETH-9JUN23-1900-C', 70.0)]
    df = implied.prepare(pd.DataFrame([{'timestamp': ts0 + int(h * 3_600_000), 'trade_id': str(i), 'instrument_name': n, 'iv': iv,
                                        'price': 0.01, 'index_price': 1900.0, 'amount': 1.0, 'direction': 'buy'}
                                       for i, (h, n, iv) in enumerate(rows)]))
    s = events.iv_series(lambda d: df if d == '2023-06-01' else None, ['2023-06-01'], CFG)
    assert s.loc[pd.Timestamp('2023-06-01 06:00')] == 55.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_events.py -q`
Expected: FAIL with `ImportError: cannot import name 'events'`

- [ ] **Step 3: Implement events.py**

```python
# tradingagents/research/onchain_b5/events.py
"""Event study (spec §8): large stablecoin inflow (or outflow) hours versus placebo exchange-
activity spikes; responses k = 1..K hours: realised-volatility surprise against an out-of-fold
price-only forecast, the same before the event, change in near-expiry implied volatility, and
signed return."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2.screen import fit_predict, folds
from ..onchain_b4 import dataset4
from ..onchain_b4.screen4 import interval
from . import decisions, implied

H = pd.Timedelta(hours=1)


def first_per_window(times, spacing_h):
    kept, last = [], None
    for t in sorted(pd.DatetimeIndex(times)):
        if last is None or t - last >= pd.Timedelta(hours=spacing_h):
            kept.append(t)
            last = t
    return kept


def flow_events(raw, trans, kind, cfg):
    e = cfg['events']
    if kind == 'inflow':
        m = (trans['stable_in_val__h1z'] >= e['z']) & (raw['stable_big_in'].reindex(trans.index) >= 1)
    else:
        m = trans['stable_out_val__h1z'] >= e['z']
    return first_per_window(trans.index[m.fillna(False).to_numpy()], e['spacing_h'])


def placebo_events(bars, n, cfg):
    e = cfg['events']
    b = bars.reindex(pd.date_range(bars.index.min(), bars.index.max(), freq='h'))
    r = np.log(b['close']).diff()
    za = dataset4.zscore(r.abs(), e['z_window'], e['z_min'], 10.0)
    zv = dataset4.zscore(np.log(b['qvol']).replace([np.inf, -np.inf], np.nan), e['z_window'], e['z_min'], 10.0)
    cand = first_per_window(b.index[((za >= e['z']) | (zv >= e['z'])).fillna(False).to_numpy()], e['spacing_h'])
    if len(cand) > n:
        rng = np.random.default_rng(e['placebo_seed'])
        cand = sorted(pd.DatetimeIndex(cand)[rng.choice(len(cand), n, replace=False)])
    return list(cand)


def vol_targets(bars, kmax):
    b = bars.reindex(pd.date_range(bars.index.min(), bars.index.max(), freq='h'))
    lc = np.log(b['close'])
    r2 = lc.diff() ** 2
    Y, R = pd.DataFrame(index=b.index), pd.DataFrame(index=b.index)
    for k in range(1, kmax + 1):
        Y[f'y{k}'] = np.log(np.sqrt(r2.rolling(k, min_periods=k).sum().shift(-k) * 8760 / k).clip(lower=1e-8))
        R[f'r{k}'] = lc.shift(-k) - lc
    return Y, R


def surprises(bars, cfg):
    e = cfg['events']
    X = dataset4.price_features(bars).join(decisions.px_features(bars))
    Y, _ = vol_targets(bars, e['kmax'])
    S = pd.DataFrame(index=Y.index)
    for k in range(1, e['kmax'] + 1):
        d = X.join(Y[[f'y{k}']]).dropna()
        y = d[f'y{k}'].to_numpy(float)
        Xm = d[[c for c in X.columns]].to_numpy(float)
        p = np.full(len(d), np.nan)
        for _, tr, te in folds(d.index, e['test_years'], k / 24):
            if te.any() and tr.sum() >= 1000:
                p[te] = fit_predict('linear', 'regression', Xm[tr], y[tr], Xm[te], e['inner_len'], cfg)
        S[f's{k}'] = pd.Series(y - p, index=d.index)
    return S


def iv_series(trades_for_day, days, cfg):
    c, e = cfg['implied'], cfg['events']
    out = {}
    for day in days:
        tr = trades_for_day(day)
        if tr is None or not len(tr):
            continue
        tr = tr.assign(bin=tr['ts'].dt.floor('h'))
        tr = tr[tr['expiry'] >= tr['bin'] + H + pd.Timedelta(hours=e['iv_min_ahead_h'])]
        tr = tr[np.abs(np.log(tr['strike'] / tr['index_price'])) <= c['moneyness']]
        for b, g in tr.groupby('bin'):
            g = g[g['expiry'] == g['expiry'].min()]
            out[b] = implied.wmedian(g['iv'], g['amount'])
    return pd.Series(out, dtype=float).sort_index()


def _stat(x, gate):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return {'mean': float(x.mean()) if len(x) else np.nan, 'lo': np.nan, 'hi': np.nan, 'n': int(len(x))}
    lo, hi = interval(x, 1, gate['draws'], gate['seed'], gate['chunk'])
    return {'mean': float(x.mean()), 'lo': lo, 'hi': hi, 'n': int(len(x))}


def responses(evts, S, R, iv, kmax, gate):
    ev = pd.DatetimeIndex(evts)
    out = []
    for k in range(1, kmax + 1):
        post = S[f's{k}'].reindex(ev).to_numpy()
        pre = S[f's{k}'].reindex(ev - k * H).to_numpy()
        div = iv.reindex(ev + k * H).to_numpy() - iv.reindex(ev).to_numpy()
        ret = R[f'r{k}'].reindex(ev).to_numpy()
        out.append({'k': k, 'n': int(len(ev)), 'post_vol': _stat(post, gate), 'pre_vol': _stat(pre, gate),
                    'd_iv': _stat(div, gate), 'ret': _stat(ret, gate)})
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_events.py -q`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b5/events.py tests/research/onchain_b5/test_events.py
git commit -m "feat(onchain-b5): event study of large stablecoin flows against placebo activity spikes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: CLI stages

**Files:**
- Create: `tradingagents/research/onchain_b5/cli.py`
- Test: `tests/research/onchain_b5/test_cli5.py`

**Interfaces:**
- Consumes: everything above; `onchain_b2.market.http_get`; `onchain_b4.hourmarket.fetch/load_all`; `onchain_b.runlog.Log`.
- Produces: `cli.main(argv)`; module attributes `ARTIFACTS`, `STUDY`, `B4` (patchable); `cli.options_complete(asset) -> bool`; `cli.trades_loader(asset) -> callable(day)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b5/test_cli5.py
import copy
import json

import pandas as pd
import pytest

from tradingagents.research.onchain_b5 import cli, config, deribit


def _setup(tmp_path, monkeypatch, fail=()):
    cfg = copy.deepcopy(config.load())
    cfg['window'] = {'start': '2023-06-01', 'end': '2023-06-03'}
    cfg['deribit']['retries'] = []
    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path / 'b5')
    monkeypatch.setattr(cli.config, 'load', lambda: cfg)

    def fake(get, currency, day, c, sleep=None):
        if day in fail:
            raise OSError('net')
        return pd.DataFrame([{'timestamp': 1, 'trade_id': f'{currency}-{day}', 'instrument_name': 'ETH-2JUN23-1900-C',
                              'iv': 50.0, 'price': 0.01, 'index_price': 1900.0, 'amount': 1.0, 'direction': 'buy'}])
    monkeypatch.setattr(deribit, 'fetch_day', fake)
    return tmp_path / 'b5'


def test_fetch_options_writes_resumes_and_marks(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch, fail=('2023-06-02',))
    cli.main(['fetch-options', '--asset', 'ETH'])
    assert (art / 'options' / 'ETH' / '2023-06-01.parquet').exists()
    assert json.loads((art / 'options' / 'ETH' / '2023-06-02.unavailable.json').read_text())['day'] == '2023-06-02'
    assert cli.options_complete('ETH')                 # a marked day counts as complete
    _setup(tmp_path, monkeypatch)
    cli.main(['fetch-options', '--asset', 'ETH'])
    assert (art / 'options' / 'ETH' / '2023-06-02.parquet').exists()
    assert not (art / 'options' / 'ETH' / '2023-06-02.unavailable.json').exists()
    assert cli.options_complete('ETH')


def test_decisions_refuse_incomplete_options(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match='options incomplete'):
        cli.main(['decisions'])


def test_trades_loader_prepares_and_skips_missing(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    cli.main(['fetch-options', '--asset', 'ETH'])
    load = cli.trades_loader('ETH')
    df = load('2023-06-01')
    assert 'expiry' in df.columns and df['expiry'].iloc[0] == pd.Timestamp('2023-06-02 08:00')
    assert load('2023-07-01') is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_cli5.py -q`
Expected: FAIL with `ImportError: cannot import name 'cli'`

- [ ] **Step 3: Implement the CLI**

```python
# tradingagents/research/onchain_b5/cli.py
"""B5 stage runner: fetch option trades / DVOL / BTC bars, build decision tables, run the
forecast comparison, the straddle backtests and the event study, and write the tables."""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

from ..onchain_b.runlog import Log
from ..onchain_b2 import market
from ..onchain_b4 import hourmarket
from . import config, decisions, deribit, events, forecast, implied, straddle

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B4 = config.B4_ARTIFACTS


def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True, default=lambda o: None if o != o else str(o)))
    os.replace(tmp, path)


def _opt_dir(asset):
    return ARTIFACTS / 'options' / asset


def options_complete(asset):
    d = _opt_dir(asset)
    return all((d / f'{day}.parquet').exists() or (d / f'{day}.unavailable.json').exists() for day in config.days(config.load()))


def trades_loader(asset):
    cache = {}

    def load(day):
        if day not in cache:
            p = _opt_dir(asset) / f'{day}.parquet'
            cache.clear()
            cache[day] = implied.prepare(deribit.load_day(p)) if p.exists() else None
        return cache[day]
    return load


def stage_fetch_options(args):
    c = config.load()
    log = Log(ARTIFACTS / 'logs' / f'options-{args.asset}.jsonl')
    for day in config.days(c):
        out = _opt_dir(args.asset) / f'{day}.parquet'
        if out.exists():
            continue
        t = time.time()
        try:
            df = deribit.with_retries(lambda: deribit.fetch_day(market.http_get, args.asset, day, c), c['deribit']['retries'])
        except deribit.Unavailable as e:
            _write_json(_opt_dir(args.asset) / f'{day}.unavailable.json', {'day': day, 'errors': e.errors})
            log.event(event='day', day=day, status='unavailable')
            continue
        deribit.save_day(df, out)
        (_opt_dir(args.asset) / f'{day}.unavailable.json').unlink(missing_ok=True)
        log.event(event='day', day=day, status='done', trades=int(len(df)), seconds=round(time.time() - t, 1))


def stage_fetch_dvol(args):
    c = config.load()
    w = c['window']
    for asset in c['assets']:
        s = deribit.fetch_dvol(market.http_get, asset, w['start'], w['end'], c)
        p = ARTIFACTS / 'market' / f'dvol_{asset}.parquet'
        p.parent.mkdir(parents=True, exist_ok=True)
        s.to_frame().to_parquet(p)
        print(json.dumps({'asset': asset, 'hours': len(s), 'first': str(s.index.min()), 'last': str(s.index.max())}))


def stage_fetch_bars(args):
    c = config.load()
    b = c['binance']
    bars, _ = hourmarket.fetch(market.http_get, b['BTC'], b['start'], b['end'])
    p = ARTIFACTS / 'market' / 'btc_hourly.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(sorted(bars.items()))))
    print(json.dumps({'btc_hours': len(bars)}))


def _bars(asset):
    if asset == 'ETH':
        return hourmarket.load_all(B4 / 'market' / 'hourly_dev.json', B4 / 'sealed' / 'hourly_sealed.json')
    return decisions.load_bars(ARTIFACTS / 'market' / 'btc_hourly.json')


def _flows(cfg):
    f = pd.read_parquet(B4 / 'features' / 'hourly.parquet')
    return f[[c for c in f.columns if c.startswith(tuple(cfg['flow_prefixes']))]]


def stage_decisions(args):
    c = config.load()
    for asset in c['assets']:
        if not options_complete(asset):
            raise SystemExit(f'options incomplete for {asset}: fetch or mark every day first')
    flows, counts = _flows(c), {}
    for asset in c['assets']:
        bars = _bars(asset)
        dvol = pd.read_parquet(ARTIFACTS / 'market' / f'dvol_{asset}.parquet')['dvol']
        for sched in c['schedules']:
            df = decisions.build(sched, bars, dvol, flows, trades_loader(asset), c)
            p = ARTIFACTS / 'decisions' / f'{asset}_{sched}.parquet'
            p.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(p)
            counts[f'{asset}_{sched}'] = {'rows': len(df), 'by_year': df.index.year.value_counts().sort_index().to_dict()}
    _write_json(ARTIFACTS / 'decisions' / 'counts.json', counts)
    print(json.dumps(counts, default=str))


def _tables(c):
    return {f'{a}_{s}': pd.read_parquet(ARTIFACTS / 'decisions' / f'{a}_{s}.parquet') for a in c['assets'] for s in c['schedules']}


def stage_forecast(args):
    c = config.load()
    allres = {}
    (ARTIFACTS / 'forecast').mkdir(parents=True, exist_ok=True)
    for key, df in _tables(c).items():
        preds, res = forecast.run(df, c)
        preds.to_parquet(ARTIFACTS / 'forecast' / f'{key}_preds.parquet')
        allres[key] = res
    _write_json(ARTIFACTS / 'forecast' / 'results.json', allres)


def stage_backtest(args):
    c = config.load()
    out = {}
    for key, df in _tables(c).items():
        preds = pd.read_parquet(ARTIFACTS / 'forecast' / f'{key}_preds.parquet')
        cols = [f'{f}:{v}' for f in c['families'] for v in c['straddle']['variants']]
        out[key] = straddle.backtest(df, preds[cols], c)
    _write_json(ARTIFACTS / 'backtest' / 'results.json', out)


def stage_events(args):
    c = config.load()
    trans = pd.read_parquet(B4 / 'features' / 'hourly.parquet')
    raw = pd.read_parquet(B4 / 'features' / 'hourly_raw.parquet')
    groups = {'2019-24': list(range(2019, 2025)), '2025-26': [2025, 2026]}
    out = {}
    for asset in c['assets']:
        bars = _bars(asset)
        S = events.surprises(bars, c)
        _, R = events.vol_targets(bars, c['events']['kmax'])
        iv = events.iv_series(trades_loader(asset), config.days(c), c)
        sets = {'inflow': events.flow_events(raw, trans, 'inflow', c), 'outflow': events.flow_events(raw, trans, 'outflow', c)}
        sets['placebo'] = events.placebo_events(bars, len(sets['inflow']), c)
        out[asset] = {}
        for name, ev in sets.items():
            ev = pd.DatetimeIndex(ev)
            out[asset][name] = {g: events.responses([e for e in ev if e.year in yrs], S, R, iv, c['events']['kmax'], c['gate'])
                                for g, yrs in groups.items()}
    _write_json(ARTIFACTS / 'events' / 'results.json', out)


def _fmt(x, d=4):
    return '—' if x is None or x != x else f'{x:+.{d}f}'


def stage_report(args):
    c = config.load()
    lines = ['# B5 tables (generated; interpretation in RESULTS.md)', '', '## Q1 forecast comparison', '',
             '| table | family | comparison | group | n | mean diff | 95 % CI | years better |', '|---|---|---|---|---|---|---|---|']
    for key, res in json.loads((ARTIFACTS / 'forecast' / 'results.json').read_text()).items():
        for r in res:
            lines.append(f"| {key} | {r['family']} | {r['set']} vs {r['comparator']} | {r['group']} | {r['n']} | "
                         f"{_fmt(r['mean_diff'], 5)} | [{_fmt(r['lo'], 5)}, {_fmt(r['hi'], 5)}] | {r['wins']}/{len(r['years'])} |")
    lines += ['', '## Q2 straddle backtest (USD per coin)', '',
              '| table | rule | family | variant | θ | group | trades | mean/trade | 95 % CI | total | hit | Sharpe | max DD | long mean (n) | short mean (n) |',
              '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for key, res in json.loads((ARTIFACTS / 'backtest' / 'results.json').read_text()).items():
        for r in res:
            for g, m in r['groups'].items():
                lines.append(f"| {key} | {r['rule']} | {r['family'] or '—'} | {r['variant'] or '—'} | {r['theta'] if r['theta'] is not None else '—'} | {g} | "
                             f"{m['trades']} | {_fmt(m['mean_trade'], 2)} | [{_fmt(m['lo'], 2)}, {_fmt(m['hi'], 2)}] | {_fmt(m['total'], 0)} | "
                             f"{_fmt(m['hit'], 2)} | {_fmt(m['sharpe'], 2)} | {_fmt(m['maxdd'], 0)} | {_fmt(m['long_mean'], 2)} ({m['long_n']}) | "
                             f"{_fmt(m['short_mean'], 2)} ({m['short_n']}) |")
    ev_path = ARTIFACTS / 'events' / 'results.json'
    if ev_path.exists():
        lines += ['', '## Q4 event study (k = 1, 3, 6, 12 h)', '',
                  '| asset | events | group | k | n | post vol surprise | pre vol surprise | Δ implied vol | signed return |', '|---|---|---|---|---|---|---|---|---|']
        for asset, sets in json.loads(ev_path.read_text()).items():
            for name, groups in sets.items():
                for g, rows in groups.items():
                    for r in rows:
                        if r['k'] in (1, 3, 6, 12):
                            cell = lambda s: f"{_fmt(s['mean'], 3)} [{_fmt(s['lo'], 3)}, {_fmt(s['hi'], 3)}]"
                            lines.append(f"| {asset} | {name} | {g} | {r['k']} | {r['n']} | {cell(r['post_vol'])} | {cell(r['pre_vol'])} | "
                                         f"{cell(r['d_iv'])} | {cell(r['ret'])} |")
    (STUDY / 'TABLES.md').write_text('\n'.join(lines) + '\n')
    print(f'{len(lines)} lines')


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b5')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('fetch-options')
    a.add_argument('--asset', required=True, choices=['ETH', 'BTC'])
    a.set_defaults(fn=stage_fetch_options)
    for name, fn in (('fetch-dvol', stage_fetch_dvol), ('fetch-bars', stage_fetch_bars), ('decisions', stage_decisions),
                     ('forecast', stage_forecast), ('backtest', stage_backtest), ('events', stage_events), ('report', stage_report)):
        sub.add_parser(name).set_defaults(fn=fn)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests to verify they pass, then the package suite**

Run: `.venv/bin/python -m pytest tests/research/onchain_b5/test_cli5.py -q`
Expected: `3 passed`

Run: `.venv/bin/python -m pytest tests/research/onchain_b5 tests/research/onchain_b4 -q`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b5/cli.py tests/research/onchain_b5/test_cli5.py
git commit -m "feat(onchain-b5): stage runner for fetches, decision tables, forecasts, backtests, events and tables

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Data (B5-CP1) and decision tables (B5-CP2)

Operational.

- [ ] **Step 1: Fetch option trades (two units in parallel) and the small series**

```bash
P=$PWD; for A in ETH BTC; do systemd-run --user --unit onchain-b5-opt-$A -p MemoryMax=3G -p WorkingDirectory=$P \
  $P/.venv/bin/python -m tradingagents.research.onchain_b5.cli fetch-options --asset $A; done
.venv/bin/python -m tradingagents.research.onchain_b5.cli fetch-dvol
.venv/bin/python -m tradingagents.research.onchain_b5.cli fetch-bars
```
Expected: 2,029 day files (or markers) per asset in ≈ 1–2 h; DVOL ≈ 48,000 hours per asset from 2021-03-24; BTC ≈ 80,000 hours. Relaunch a unit if it dies (finished days are skipped; marked days are retried).

- [ ] **Step 2: Record B5-CP1 in `STATE.md`** (days, unavailable days, trades per year, DVOL and BTC coverage) and commit (`docs(onchain-b5): B5-CP1 data stored`).

- [ ] **Step 3: Decision tables**

Run: `.venv/bin/python -m tradingagents.research.onchain_b5.cli decisions`
Expected: four tables; eligible decisions per year printed. Record B5-CP2 counts in `STATE.md` and commit (`docs(onchain-b5): B5-CP2 decision tables`).

---

### Task 10: Analyses (B5-CP3, B5-CP4)

Operational. Every item of `PLAN.md` is reported.

- [ ] **Step 1:** `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b5.cli forecast` then `… backtest` then `… events` then `… report`; commit `TABLES.md` with `STATE.md` (`research(onchain-b5): B5-CP3 forecasts, backtests and events`).
- [ ] **Step 2:** Tron probe: request SQD's public portal (and any other free source found) for one day of USDT TRC-20 `Transfer` logs (contract `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t`), time it, extrapolate to full history; check Dune Spellbook for Tron CEX address lists. Write `research/onchain-b5-2026-10-19/TRON_PROBE.md` (go or no-go, cost).
- [ ] **Step 3:** Write `research/onchain-b5-2026-10-19/RESULTS.md`: Q1–Q5 answers from `TABLES.md`, the pre-declared positive reading for Q2 applied as written, caveats; update `STATE.md`, memory note and the audit page; commit (`research(onchain-b5): B5-CP4 results`).

---

## Self-review

**Spec coverage:** §3 data → Tasks 2, 8, 9; §4 schedules and implied → Tasks 3, 4; §5 forecast → Task 5; §6 straddle → Task 6; §7 BTC → Tasks 8–10 (assets loop); §8 events → Task 7; §9 Tron → Task 10; §10 PLAN.md → Task 1; §11 compute → Task 9; §12 layout → as listed; §13 testing → Tasks 2–8; §14 checkpoints → Tasks 9–10.

**Type consistency:** `deribit.COLUMNS` day frames → `implied.prepare` → `decisions.build(sched, bars, dvol, flows, trades_for_day, cfg)` → `forecast.run(df, cfg)` → preds columns `f'{family}:{set}'` → `straddle.backtest(df, preds, cfg)`; `events.responses(evts, S, R, iv, kmax, gate)` with `S` columns `s{k}`, `R` columns `r{k}`.

**Review Focus coverage:** 1 → Task 4 `test_build_skips_ineligible_and_is_causal`; 2 → Task 4 `test_fill_spread_uses_only_earlier_rows`; 3 → Task 2 `test_fetch_day_paginates_and_dedupes`; 4 → Task 6 `test_black76_values_parity_and_extremes`; 5 → Task 7 `test_iv_series_uses_nearest_live_expiry`.
