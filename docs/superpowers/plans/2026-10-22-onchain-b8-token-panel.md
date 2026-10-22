# B8 Per-Token Hourly Panel — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A frozen universe of 148 perp-listed ERC-20 tokens, one `token_transfers` pass (2020-06-01 … 2026-07-29) writing seven token-hour series per day, a panel with B7's feature engineering per token plus cross-sectional z-scores and volatility targets, and pooled walk-forward comparisons with hour-block bootstrap intervals.

**Architecture:** New package `tradingagents/research/onchain_b8/` importing B2 (`folds`, `row_loss`, `DayUnavailable`, `check_timestamps`), B4 (`reader` helpers, `price_features`, `hourly_targets`, `interval`, cli constants), B5 (`px_features`), B6 (`_read_table`, `labels6.LabelState` + activation table from `state.npz`) and B7 (`features7.multiscale`, `models7.fit_predict7`, `forecast7.columns/detail_report`). Day files are the pass state (resumable by file existence); the forecast stage is resumable per target.

**Tech Stack:** Python 3.13, numpy, pandas, pyarrow (S3 anonymous), scikit-learn, pytest; systemd user units.

**Spec:** `docs/superpowers/specs/2026-10-22-onchain-b8-token-panel-design.md`

## Global Constraints

- Exploratory with a pre-declared plan: `research/onchain-b8-2026-10-22/PLAN.md` and the frozen `config/universe.json` committed before any day is read.
- Universe rule: token map `address` present, ≥ 17,520 hourly bars (2 years) in the 1-hour kline store, one symbol per contract (longer history wins).
- Series per token-hour: `dep_usd`, `wd_usd`, `dep_cnt`, `wd_cnt`, `tx_cnt`, `active`, `big_cnt` (≥ $100k). USD = amount × the token's hourly close of the block's hour; hours without a bar have NaN USD series.
- Exchange activation = B6's first-seen table (`research_artifacts/onchain-b6/state/state.npz`, `ex_first`, day ordinals from 2017-01-01); an address is an exchange from the day after its first observed transfer.
- Features: B7 `multiscale` per token (prefix `n_`), `h0_` (8), `px_` (5), cross-sectional `xs_` z-scores per hour (≥ 20 tokens) of the `__s24z` and `__ex1` columns and of `h0_rv24`, `h0_lvol24`; a token enters 30 days after its first bar.
- Targets V6, V24 (B4), XV24 = V24 − hour mean over tokens (≥ 20 tokens). Sets P0 = `h0_`, `px_`, `xs_h0_`; P1 = P0 + `n_`; P2 = P1 + `xs_n_`. Comparisons P1 vs P0, P2 vs P1, P2 vs P0; families ridge, trees_es (B7 settings incl. `min_tail_pos`); test years 2022–2026; purge = horizon; min_train 50,000; inner window 175,200.
- Statistics: per-row loss differences averaged per hour, circular block bootstrap over hours (block 168, 2,000 draws, seed 20261023), per-year means; criterion upper < 0 and ≥ 3 of 5 years.
- `onchain_b` … `onchain_b7` imported, not edited. Docs impersonal. Commits end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Package test command: `.venv/bin/python -m pytest tests/research/onchain_b8 -q`.

## Review Focus

1. A transfer between two active exchange addresses is neither a deposit nor a withdrawal, and an address first seen today is not an exchange today (Task 4 `test_day_rows_flows_activation_and_prices`).
2. A token-hour without a price gives NaN USD series but correct counts, and never a zero that looks like "no flow" (Task 4 same test).
3. Cross-sectional z-scores and XV24 are NaN in hours with fewer than 20 tokens and never use other hours (Task 5 `test_cross_section_min_tokens_and_xv24`).
4. The bootstrap and the per-year criterion weight hours, not rows: an hour with 148 tokens and one with 25 count once each (Task 6 `test_compare_weights_hours_not_rows`).
5. A pass killed mid-day leaves no partial day file and resumes at the missing day; an unavailable day is marked and skipped (Task 7 `test_pass_resumes_and_marks_unavailable`).

---

### Task 1: Skeleton, configuration, universe freeze, registration

**Files:**
- Create: `tradingagents/research/onchain_b8/__init__.py` (empty), `config.py`, `universe8.py`
- Create: `research/onchain-b8-2026-10-22/config/b8.json`, `CHARTER.md`, `PLAN.md`, `STATE.md`
- Modify: `.gitignore` (add `/research_artifacts/onchain-b8/`)
- Test: `tests/research/onchain_b8/__init__.py` (empty), `tests/research/onchain_b8/test_config.py`, `tests/research/onchain_b8/test_universe8.py`

**Interfaces:**
- Produces: `config.ROOT/STUDY/ARTIFACTS/B6_ARTIFACTS/KLINES/TOKEN_MAP/EPOCH`, `config.load()`, `config.universe() -> list[dict]`, `config.days(cfg=None)`, `config.day_ord(day)`; `universe8.build(token_map_path, klines_dir, min_rows) -> list[dict(symbol, address, decimals, rows, how)]`, `universe8.load_bars(klines_dir, symbol) -> DataFrame[close, qvol]` (naive UTC hourly index).

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b8/test_config.py
from tradingagents.research.onchain_b8 import config


def test_config_window_sets_and_models():
    c = config.load()
    assert config.days(c)[0] == '2020-06-01' and config.days(c)[-1] == '2026-07-29'
    assert config.day_ord('2017-01-02') == 1 and config.EPOCH.isoformat() == '2017-01-01'
    assert c['series'] == ['dep_usd', 'wd_usd', 'dep_cnt', 'wd_cnt', 'tx_cnt', 'active', 'big_cnt']
    assert c['sets'] == {'P0': [], 'P1': ['N'], 'P2': ['N', 'XN']} and c['comparisons'] == [['P1', 'P0'], ['P2', 'P1'], ['P2', 'P0']]
    assert c['folds']['test_years'] == [2022, 2023, 2024, 2025, 2026] and c['folds']['min_train'] == 50000
    assert c['models']['trees_es']['min_tail_pos'] == 10 and c['gate']['seed'] == 20261023
    assert set(c['targets']) == {'V6', 'V24', 'XV24'}


def test_registration_files_exist():
    for name in ('CHARTER.md', 'PLAN.md', 'STATE.md'):
        assert (config.STUDY / name).exists()
```

```python
# tests/research/onchain_b8/test_universe8.py
import json

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b8 import universe8 as U


def _klines(path, symbol, n, tz=True):
    idx = pd.date_range('2021-01-01', periods=n, freq='h', tz='UTC' if tz else None)
    df = pd.DataFrame({'open': 1.0, 'high': 1.0, 'low': 1.0, 'close': np.linspace(1, 2, n), 'volume': 1.0,
                       'quote_volume': 5.0, 'taker_buy_quote_volume': 2.0}, index=pd.Index(idx, name='ts'))
    df.to_parquet(path / f'{symbol}.parquet')


def test_build_filters_dedupes_and_sorts(tmp_path):
    k = tmp_path / 'k'
    k.mkdir()
    for sym, n in (('AAAUSDT', 20000), ('BBBUSDT', 100), ('1000CCCUSDT', 30000), ('CCCUSDT', 25000), ('EEEUSDT', 20000)):
        _klines(k, sym, n)
    tm = {'map': {'AAAUSDT': {'address': '0xAAAA', 'decimals': 18, 'how': 'binance_spot'},
                  'BBBUSDT': {'address': '0xbbbb', 'decimals': 6, 'how': 'binance_spot'},
                  '1000CCCUSDT': {'address': '0xcccc', 'decimals': 9, 'how': 'binance_spot'},
                  'CCCUSDT': {'address': '0xcccc', 'decimals': 9, 'how': 'fallback_single_ranked'},
                  'DDDUSDT': {'address': '0xdddd', 'decimals': 18, 'how': 'binance_spot'},
                  'EEEUSDT': {'how': 'fallback_no_candidate'}}}
    (tmp_path / 'map.json').write_text(json.dumps(tm))
    u = U.build(tmp_path / 'map.json', k, 17520)
    assert [r['symbol'] for r in u] == ['1000CCCUSDT', 'AAAUSDT']               # BBB too short, DDD no bars, EEE no address, CCC duplicate contract
    assert u[1]['address'] == '0xaaaa' and u[1]['decimals'] == 18 and u[1]['rows'] == 20000 and u[0]['how'] == 'binance_spot'


def test_load_bars_naive_utc_close_and_qvol(tmp_path):
    _klines(tmp_path, 'AAAUSDT', 50)
    b = U.load_bars(tmp_path, 'AAAUSDT')
    assert list(b.columns) == ['close', 'qvol'] and b.index.tz is None and b.index[0] == pd.Timestamp('2021-01-01')
    assert b['qvol'].iloc[0] == 5.0 and np.isclose(b['close'].iloc[-1], 2.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8 -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.research.onchain_b8'`

- [ ] **Step 3: Write the modules, config, docs and gitignore entry**

```python
# tradingagents/research/onchain_b8/config.py
"""Frozen B8 configuration (research/onchain-b8-2026-10-22/config/b8.json) and the frozen
universe (config/universe.json)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b8-2026-10-22'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b8'
B6_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b6'
KLINES = ROOT.parent / 'TradingAgents' / 'data' / 'xsect' / 'klines_1h'
TOKEN_MAP = ROOT.parent / 'TradingAgents-predlab' / 'data' / 'predlab' / 'smw' / 'token_map.json'
EPOCH = date(2017, 1, 1)             # B6's day-ordinal epoch: the activation table is B6's


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b8.json').read_text())


def universe() -> list:
    return json.loads((STUDY / 'config' / 'universe.json').read_text())['tokens']


def days(cfg=None) -> list:
    w = (cfg or load())['window']
    return [d.date().isoformat() for d in pd.date_range(w['first_day'], w['last_day'], freq='D')]


def day_ord(day) -> int:
    return (date.fromisoformat(day) - EPOCH).days
```

```python
# tradingagents/research/onchain_b8/universe8.py
"""Frozen token universe (spec §1.2): perp symbols with a mainnet ERC-20 contract in the smw
token map and at least `min_rows` hourly bars, one symbol per contract (the longer history
wins). Hourly bars as close / quote volume on a naive UTC index."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


def build(token_map_path, klines_dir, min_rows):
    tm = json.loads(Path(token_map_path).read_text())['map']
    rows = []
    for sym, v in sorted(tm.items()):
        addr = v.get('address')
        p = Path(klines_dir) / f'{sym}.parquet'
        if not addr or not p.exists():
            continue
        n = pq.read_metadata(p).num_rows
        if n < min_rows:
            continue
        rows.append({'symbol': sym, 'address': addr.lower(), 'decimals': int(v['decimals']), 'rows': int(n), 'how': v.get('how')})
    best = {}
    for r in rows:
        if r['address'] not in best or r['rows'] > best[r['address']]['rows']:
            best[r['address']] = r
    return sorted(best.values(), key=lambda r: r['symbol'])


def load_bars(klines_dir, symbol):
    df = pd.read_parquet(Path(klines_dir) / f'{symbol}.parquet', columns=['close', 'quote_volume'])
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_convert('UTC').tz_localize(None)
    out = pd.DataFrame({'close': df['close'].to_numpy(float), 'qvol': df['quote_volume'].to_numpy(float)}, index=idx).sort_index()
    return out[~out.index.duplicated()]
```

`research/onchain-b8-2026-10-22/config/b8.json`:

```json
{
 "window": {"first_day": "2020-06-01", "last_day": "2026-07-29"},
 "universe": {"min_rows": 17520},
 "pass": {"prefetch": 1, "max_consecutive_unavailable": 3},
 "s3": {"bucket": "aws-public-blockchain", "region": "us-east-2", "retries": [30, 120]},
 "big_usd": 100000.0,
 "series": ["dep_usd", "wd_usd", "dep_cnt", "wd_cnt", "tx_cnt", "active", "big_cnt"],
 "engineering": {"profile_weeks": 8, "profile_min": 4, "z1_window": 168, "z1_min": 120,
                 "s6_window": 720, "s6_min": 480, "s24_window": 720, "s24_min": 480,
                 "s168_window": 2160, "s168_min": 1440, "burst_window": 24, "clip": 10.0},
 "panel": {"entry_days": 30, "min_tokens_hour": 20, "xs_series": ["__s24z", "__ex1"], "xs_price": ["h0_rv24", "h0_lvol24"]},
 "targets": {"V6": {"h": 6}, "V24": {"h": 24}, "XV24": {"h": 24}},
 "blocks": {"base": ["h0_", "px_", "xs_h0_"], "N": ["n_"], "XN": ["xs_n_"]},
 "sets": {"P0": [], "P1": ["N"], "P2": ["N", "XN"]},
 "comparisons": [["P1", "P0"], ["P2", "P1"], ["P2", "P0"]],
 "families": ["ridge", "trees_es"],
 "folds": {"test_years": [2022, 2023, 2024, 2025, 2026], "inner_len": 175200, "min_train": 50000, "min_year_wins": 3},
 "models": {"alphas": [0.1, 1, 10, 100, 1000, 10000, 100000], "fallback_alpha": 100.0,
            "trees": {"max_iter": 100, "learning_rate": 0.05, "max_leaf_nodes": 7, "min_samples_leaf": 30,
                      "l2_regularization": 1.0, "random_state": 11},
            "trees_es": {"max_iter": 600, "learning_rate": 0.05, "max_leaf_nodes": 15, "min_samples_leaf": 50,
                         "l2_regularization": 1.0, "random_state": 11, "tail_frac": 0.1, "min_iter": 20, "min_tail_pos": 10}},
 "gate": {"draws": 2000, "seed": 20261023, "block": 168, "chunk": 100}
}
```

`research/onchain-b8-2026-10-22/CHARTER.md`:

```markdown
# B8 charter — hourly per-token on-chain panel for perp-listed ERC-20 tokens

Registered 2026-10-22 before any day of the pass is read. Spec:
`docs/superpowers/specs/2026-10-22-onchain-b8-token-panel-design.md`.

## Questions

Q1 Across tokens, do hourly exchange-flow and transfer-activity features improve next-6 /
24-hour volatility forecasts beyond the token's own price and volume history? Q2 Do they
forecast which tokens will be more volatile than the others over the next 24 hours? Q3
(reading) Is a per-token effect, if any, of the same kind as ETH's activity proxy?

## Framing

Exploratory with a pre-declared plan (`PLAN.md`); no sealed window; volatility targets
only, no return or direction claim.

## Disclosures

- Universe and token map are 2026 snapshots (148 tokens with ≥ 2 years of hourly perp bars
  and a mainnet contract; delisted tokens kept where the kline store kept them).
- Exchange labels and activation are B6's (identity look-ahead disclosed there).
- USD values use the perp close of the block's hour; token-hours without a bar have missing
  USD series and `big_cnt` 0.
- §82 (smw_xs) tested DEX-swap smart-money features for next-day returns on this kind of
  universe and closed; B8 uses exchange transfers and volatility targets only.
```

`research/onchain-b8-2026-10-22/PLAN.md`:

```markdown
# B8 pre-declared analysis plan (committed before any day is read)

All items run once; `RESULTS.md` reports every row, including negatives.

## Comparisons

Pooled panel, one model across tokens per fold; test years 2022–2026 (window 2020-06-01 →
2026-07-29), purge = horizon, expanding training, min_train 50,000 rows. Targets V6, V24 (log
realised volatility of the token's hourly returns over the next 6 / 24 h), XV24 (V24 minus the
hour's mean V24 over tokens, ≥ 20 tokens). Sets P0 = price (`h0_`), intraday (`px_`) and the
cross-sectional z-scores of `h0_rv24`, `h0_lvol24`; P1 = P0 + B7's six transforms of the seven
token-hour series (42); P2 = P1 + cross-sectional z-scores of the `__s24z` and `__ex1`
columns (14). Families ridge and trees_es (B7 rules, min_tail_pos irrelevant for regression).
Comparisons P1 vs P0, P2 vs P1, P2 vs P0 → 3 × 2 families × 3 targets = 18 rows.

Statistics: per-row squared-error differences averaged per hour across tokens (one value per
hour), the mean over hours, a 95 % circular block-bootstrap interval over hours (block 168,
2,000 draws, seed 20261023), per-year means, the loss of the training-mean constant.
Criterion: upper end < 0 and better in ≥ 3 of 5 years. About one chance pass is expected
among 18 rows; a finding needs both families.

Post hoc (labelled): per-token mean differences for every comparison (CSV), read by
liquidity tercile of mean quote volume.

## Reporting

`TABLES.md` (generated) holds every row with per-year rows, hours and tokens; `RESULTS.md`
reads it. Post hoc additions are labelled.
```

`research/onchain-b8-2026-10-22/STATE.md`:

```markdown
# Branch B8 state

2026-10-22 — Registered (charter, config, pre-declared plan). Universe not frozen yet; no day read.
```

Append to `.gitignore`:

```
# B8 artifacts (day files, panel, predictions)
/research_artifacts/onchain-b8/
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8 -q`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b8 research/onchain-b8-2026-10-22 tests/research/onchain_b8 .gitignore
git commit -m "feat(onchain-b8): skeleton, configuration, universe builder and registration"
```

---

### Task 2: reader8 — one day of token_transfers for the universe

**Files:**
- Create: `tradingagents/research/onchain_b8/reader8.py`
- Test: `tests/research/onchain_b8/test_reader8.py`

**Interfaces:**
- Consumes: `onchain_b4.reader` helpers (`ZERO, _arr, _check42, _floats, _secs, _strs, _unpad, addr_keys`), `onchain_b6.reader6._read_table`, `onchain_b2.s3source.{DayUnavailable, check_timestamps}`.
- Produces: `Day8(src, dst, token: int16 index, amount: token units, ts: unix s, rows)`, `admit8(tt, contracts: dict[address -> (index, decimals)]) -> Day8`, `read_day8(day, *, filesystem, root, contracts, retries, sleep) -> Day8`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b8/test_reader8.py
import numpy as np
import pandas as pd
import pyarrow as pa
import pytest

from tradingagents.research.onchain_b2.s3source import DayUnavailable
from tradingagents.research.onchain_b4.reader import ZERO, addr_keys
from tradingagents.research.onchain_b8 import reader8 as R

A, B, C = ('0x' + ch * 40 for ch in 'abc')
TOK1, TOK2, TOK9 = ('0x' + ch * 40 for ch in '129')


def _table(day='2023-05-01'):
    t0 = pd.Timestamp(day, tz='UTC')
    rows = [(TOK1, A, B, 5e18, 1), (TOK1.upper(), B, C, 2e18, 2), (TOK2, A, C, 7e6, 3), (TOK9, A, B, 1e18, 4),
            (TOK1, A, A, 1e18, 5), (TOK1, ZERO, A, 1e18, 6), (TOK1, A, B, 0.0, 7)]
    return pa.table({'token_address': [r[0] for r in rows], 'from_address': [r[1] for r in rows], 'to_address': [r[2] for r in rows],
                     'value': pa.array([r[3] for r in rows], pa.float64()), 'block_number': [r[4] for r in rows],
                     'block_timestamp': pa.array([(t0 + pd.Timedelta(minutes=r[4])).to_datetime64() for r in rows], pa.timestamp('ns'))})


def test_admit8_filters_scales_and_indexes():
    d = R.admit8(_table(), {TOK1: (0, 18), TOK2: (1, 6)})
    assert d.rows == {'transfers': 3} and d.token.tolist() == [0, 0, 1] and d.token.dtype == np.int16
    assert np.allclose(d.amount, [5.0, 2.0, 7.0])
    ka, kb, kc = addr_keys(np.array([A, B, C], object))
    assert d.src.tolist() == [ka, kb, ka] and d.dst.tolist() == [kb, kc, kc]
    assert d.ts.tolist() == [int(pd.Timestamp('2023-05-01 00:01', tz='UTC').timestamp()) + 60 * k for k in (0, 1, 2)]


def test_read_day8_retries_then_unavailable(monkeypatch):
    calls = []

    def fake_read(filesystem, root, table, day):
        calls.append(table)
        if len(calls) < 3 or day == '2023-05-02':
            raise OSError('timeout')
        return _table(day)
    monkeypatch.setattr(R, '_read_table', fake_read)
    d = R.read_day8('2023-05-01', filesystem=None, root='r', contracts={TOK1: (0, 18)}, retries=[0, 0], sleep=lambda s: None)
    assert d.rows['transfers'] == 2 and calls == ['token_transfers'] * 3
    with pytest.raises(DayUnavailable):
        R.read_day8('2023-05-02', filesystem=None, root='r', contracts={TOK1: (0, 18)}, retries=[0], sleep=lambda s: None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8/test_reader8.py -q`
Expected: FAIL with `ImportError: cannot import name 'reader8'`

- [ ] **Step 3: Write the module**

```python
# tradingagents/research/onchain_b8/reader8.py
"""One UTC day of token_transfers restricted to the universe contracts (spec §3): sender and
receiver keys, token index, amount in token units and block timestamp. Mint and burn rows
(zero address), self-transfers and zero values are excluded."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

from ..onchain_b2.s3source import DayUnavailable, check_timestamps
from ..onchain_b4.reader import ZERO, _arr, _check42, _floats, _secs, _strs, _unpad, addr_keys
from ..onchain_b6.reader6 import _read_table


@dataclass
class Day8:
    src: np.ndarray
    dst: np.ndarray
    token: np.ndarray
    amount: np.ndarray
    ts: np.ndarray
    rows: dict = field(default_factory=dict)


def admit8(tt, contracts):
    tok_all = _unpad(tt['token_address'])
    m = pc.is_in(tok_all, value_set=pa.array(sorted(contracts)))
    tt, tok_all = tt.filter(m), pc.filter(tok_all, m)
    frm, to = _unpad(tt['from_address']), _unpad(tt['to_address'])
    keep = pc.and_(pc.and_(pc.greater(_arr(tt['value']), 0.0), pc.not_equal(frm, to)),
                   pc.and_(pc.not_equal(frm, ZERO), pc.not_equal(to, ZERO)))
    tt, frm, to, tok_all = tt.filter(keep), pc.filter(frm, keep), pc.filter(to, keep), pc.filter(tok_all, keep)
    _check42(frm, 'token_transfers.from_address')
    _check42(to, 'token_transfers.to_address')
    tok, raw = tok_all.to_numpy(zero_copy_only=False), _floats(tt['value'])
    amt, code = np.zeros(len(raw)), np.full(len(raw), -1, np.int16)
    for addr, (i, dec) in contracts.items():
        mm = tok == addr
        amt[mm] = raw[mm] / 10.0 ** dec
        code[mm] = i
    return Day8(src=addr_keys(_strs(frm)), dst=addr_keys(_strs(to)), token=code, amount=amt,
                ts=_secs(tt['block_timestamp']).astype(np.int64), rows={'transfers': int(tt.num_rows)})


def read_day8(day, *, filesystem, root, contracts, retries, sleep=time.sleep):
    errors = []
    for attempt in range(len(retries) + 1):
        try:
            tt = _read_table(filesystem, root, 'token_transfers', day)
            check_timestamps(tt, day)
            return admit8(tt, contracts)
        except Exception as e:        # network, decode or integrity failure: retry, then mark unavailable
            errors.append(repr(e))
            if attempt < len(retries):
                sleep(retries[attempt])
    raise DayUnavailable(day, errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8/test_reader8.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b8/reader8.py tests/research/onchain_b8/test_reader8.py
git commit -m "feat(onchain-b8): day reader for universe token transfers"
```

---

### Task 3: hourly8 — token-hour series with exchange activation and prices

**Files:**
- Create: `tradingagents/research/onchain_b8/hourly8.py`
- Test: `tests/research/onchain_b8/test_hourly8.py`

**Interfaces:**
- Consumes: `reader8.Day8`, `onchain_b6.labels6.LabelState` (`begin_day(day_ord)`, `is_exchange(keys)`).
- Produces: `SERIES` (7 names), `price_matrix(bars_by_index: list[DataFrame], hours: DatetimeIndex) -> ndarray (n_hours, n_tokens)`, `day_rows(day, d: Day8, state, prices_day: ndarray (24, n_tokens), big_usd) -> DataFrame[hour, token, 7 series]` with 24 × n_tokens rows.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b8/test_hourly8.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b4.reader import addr_keys
from tradingagents.research.onchain_b6.labels6 import LabelState
from tradingagents.research.onchain_b8 import config, hourly8 as Hh
from tradingagents.research.onchain_b8.reader8 import Day8

A, B, X, Y, Z = ('0x' + ch * 40 for ch in 'abxyc')


def _state(first_seen):
    doc = {'exchange': {X: 'okx', Y: 'binance', Z: 'bybit'}, 'dex': [], 'bridge': [], 'mev': [], 'funds': []}
    st = LabelState(doc, '0x5754284f345afc66a98fbb0a0afe71e0f007b949')
    keys = addr_keys(np.array([X, Y, Z], object))
    for k, day in zip(keys, first_seen):
        st.ex_first[np.searchsorted(st.ex_keys, k)] = day
    return st


def test_day_rows_flows_activation_and_prices():
    day = '2023-05-01'
    t0 = int(pd.Timestamp(day, tz='UTC').timestamp())
    ka, kb, kx, ky, kz = addr_keys(np.array([A, B, X, Y, Z], object))
    #            A->X dep   X->B wd    X->Y ex-ex   A->B plain  B->Z (Z seen today: not an exchange)  A->X tok1 no price
    src = np.array([ka, kx, kx, ka, kb, ka], np.uint64)
    dst = np.array([kx, kb, ky, kb, kz, kx], np.uint64)
    d = Day8(src=src, dst=dst, token=np.array([0, 0, 0, 0, 0, 1], np.int16), amount=np.array([10.0, 4.0, 100.0, 1.0, 50.0, 3.0]),
             ts=np.array([t0 + 60, t0 + 120, t0 + 3700, t0 + 3800, t0 + 7300, t0 + 60], np.int64))
    st = _state([config.day_ord('2023-01-01'), config.day_ord('2023-01-01'), config.day_ord(day)])
    st.begin_day(config.day_ord(day))
    prices = np.full((24, 2), np.nan)
    prices[:, 0] = 2.0                                                          # token 0 priced at 2 all day; token 1 unpriced
    rows = Hh.day_rows(day, d, st, prices, big_usd=15.0)
    assert len(rows) == 48 and list(rows.columns) == ['hour', 'token'] + Hh.SERIES
    r = rows.set_index(['hour', 'token'])
    h = lambda k: pd.Timestamp(day) + pd.Timedelta(hours=k)
    assert r.loc[(h(0), 0), 'dep_usd'] == 20.0 and r.loc[(h(0), 0), 'wd_usd'] == 8.0
    assert r.loc[(h(0), 0), 'dep_cnt'] == 1 and r.loc[(h(0), 0), 'wd_cnt'] == 1 and r.loc[(h(0), 0), 'tx_cnt'] == 2
    assert r.loc[(h(0), 0), 'active'] == 3 and r.loc[(h(0), 0), 'big_cnt'] == 1    # A, X, B; only the $20 deposit is big
    assert r.loc[(h(1), 0), 'dep_usd'] == 0.0 and r.loc[(h(1), 0), 'wd_usd'] == 0.0 and r.loc[(h(1), 0), 'tx_cnt'] == 2   # ex→ex and plain
    assert r.loc[(h(2), 0), 'dep_usd'] == 0.0 and r.loc[(h(2), 0), 'tx_cnt'] == 1   # Z first seen today: not yet an exchange
    assert np.isnan(r.loc[(h(0), 1), 'dep_usd']) and r.loc[(h(0), 1), 'dep_cnt'] == 1 and r.loc[(h(0), 1), 'big_cnt'] == 0
    assert np.isnan(r.loc[(h(5), 1), 'dep_usd']) and r.loc[(h(5), 1), 'tx_cnt'] == 0 and r.loc[(h(5), 0), 'dep_usd'] == 0.0
    st.begin_day(config.day_ord('2023-05-02'))
    rows2 = Hh.day_rows('2023-05-02', Day8(src=src[4:5], dst=dst[4:5], token=np.array([0], np.int16), amount=np.array([50.0]),
                                          ts=np.array([t0 + 86400 + 10], np.int64)), st, prices, big_usd=15.0)
    assert rows2.set_index(['hour', 'token']).loc[(pd.Timestamp('2023-05-02'), 0), 'dep_usd'] == 100.0   # active from the next day


def test_price_matrix_aligns_tokens_and_hours():
    hours = pd.date_range('2023-05-01', periods=48, freq='h')
    b0 = pd.DataFrame({'close': np.arange(1, 25, dtype=float), 'qvol': 1.0}, index=pd.date_range('2023-05-01', periods=24, freq='h'))
    b1 = pd.DataFrame({'close': [7.0, 8.0], 'qvol': 1.0}, index=pd.DatetimeIndex(['2023-05-02 03:00', '2023-05-02 05:00']))
    m = Hh.price_matrix([b0, b1], hours)
    assert m.shape == (48, 2) and m[0, 0] == 1.0 and m[23, 0] == 24.0 and np.isnan(m[24, 0])
    assert np.isnan(m[26, 1]) and m[27, 1] == 7.0 and np.isnan(m[28, 1]) and m[29, 1] == 8.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8/test_hourly8.py -q`
Expected: FAIL with `ImportError: cannot import name 'hourly8'`

- [ ] **Step 3: Write the module**

```python
# tradingagents/research/onchain_b8/hourly8.py
"""One day of admitted transfers -> 24 × n_tokens rows of the seven token-hour series
(spec §3). USD values use the token's hourly close of the block's hour; a token-hour without a
price has NaN USD series, counts unaffected and big_cnt 0."""
from __future__ import annotations

import numpy as np
import pandas as pd

SERIES = ['dep_usd', 'wd_usd', 'dep_cnt', 'wd_cnt', 'tx_cnt', 'active', 'big_cnt']


def price_matrix(bars_by_index, hours):
    m = np.full((len(hours), len(bars_by_index)), np.nan)
    for j, b in enumerate(bars_by_index):
        m[:, j] = b['close'].reindex(hours).to_numpy(float)
    return m


def day_rows(day, d, state, prices, big_usd):
    n_tok = prices.shape[1]
    start = int(pd.Timestamp(day, tz='UTC').timestamp())
    hour = ((d.ts - start) // 3600).astype(np.int64)
    tok = d.token.astype(np.int64)
    key = hour * n_tok + tok
    ex_s, ex_d = state.is_exchange(d.src), state.is_exchange(d.dst)
    dep, wd = ex_d & ~ex_s, ex_s & ~ex_d
    usd = d.amount * prices[hour, tok]
    out = np.zeros((24 * n_tok, len(SERIES)))
    np.add.at(out[:, 0], key[dep], np.nan_to_num(usd[dep]))
    np.add.at(out[:, 1], key[wd], np.nan_to_num(usd[wd]))
    np.add.at(out[:, 2], key[dep], 1.0)
    np.add.at(out[:, 3], key[wd], 1.0)
    np.add.at(out[:, 4], key, 1.0)
    pairs = np.empty(2 * len(key), dtype=[('k', np.int64), ('a', np.uint64)])
    pairs['k'] = np.concatenate([key, key])
    pairs['a'] = np.concatenate([d.src, d.dst])
    uniq = np.unique(pairs)
    np.add.at(out[:, 5], uniq['k'], 1.0)
    big = usd >= big_usd
    np.add.at(out[:, 6], key[big], 1.0)
    nop = ~np.isfinite(prices).reshape(-1)
    out[nop, 0] = np.nan
    out[nop, 1] = np.nan
    df = pd.DataFrame(out, columns=SERIES)
    df.insert(0, 'token', np.tile(np.arange(n_tok, dtype=np.int16), 24))
    df.insert(0, 'hour', pd.Timestamp(day) + pd.to_timedelta(np.repeat(np.arange(24), n_tok), unit='h'))
    return df
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8/test_hourly8.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b8/hourly8.py tests/research/onchain_b8/test_hourly8.py
git commit -m "feat(onchain-b8): token-hour flow and activity series"
```

---

### Task 4: panel8 — per-token features, cross-section, targets

**Files:**
- Create: `tradingagents/research/onchain_b8/panel8.py`
- Test: `tests/research/onchain_b8/test_panel8.py`

**Interfaces:**
- Consumes: `onchain_b7.features7.multiscale`, `onchain_b4.dataset4.{price_features, hourly_targets}`, `onchain_b5.decisions.px_features`.
- Produces: `token_series(day_frames: list[DataFrame], hours, token_index) -> DataFrame[7 series on hours]`, `token_frame(series, bars, c) -> DataFrame[n_*, h0_*, px_*, V6, V24]` (rows from first bar + entry_days), `cross_section(panel, c) -> DataFrame` (adds `xs_*` and `XV24`), where `panel` is the long frame (index hour, column `token`).

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b8/test_panel8.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b8 import config, hourly8 as Hh, panel8 as P

CFG = config.load()


def _panel(n_tok, hours, rng):
    frames = []
    for j in range(n_tok):
        f = pd.DataFrame({'n_dep_usd__s24z': rng.normal(size=len(hours)), 'n_dep_usd__ex1': rng.normal(size=len(hours)),
                          'n_dep_usd__z1': rng.normal(size=len(hours)), 'h0_rv24': rng.gamma(2, 1, len(hours)),
                          'h0_lvol24': rng.normal(size=len(hours)), 'px_rv6': rng.gamma(2, 1, len(hours)),
                          'V6': rng.normal(size=len(hours)), 'V24': rng.normal(size=len(hours)) + j}, index=hours)
        f['token'] = np.int16(j)
        frames.append(f)
    return pd.concat(frames)


def test_token_series_and_frame_entry():
    rng = np.random.default_rng(21)
    hours = pd.date_range('2023-01-01', periods=24 * 200, freq='h')
    days = [pd.DataFrame({'hour': np.repeat(hours[k * 24:(k + 1) * 24], 2), 'token': np.tile(np.array([0, 1], np.int16), 24),
                          **{s: rng.gamma(2, 3, 48) for s in Hh.SERIES}}) for k in range(200) if k != 50]   # day 50 missing
    s = P.token_series(days, hours, 1)
    assert s.shape == (4800, 7) and list(s.columns) == Hh.SERIES and s.iloc[50 * 24:51 * 24].isna().all().all()
    assert s.iloc[0, 0] == days[0].loc[1, 'dep_usd']
    bars = pd.DataFrame({'close': 10 * np.exp(np.cumsum(rng.normal(0, 0.01, 4000))), 'qvol': rng.gamma(2, 1e5, 4000)},
                        index=hours[400:4400])
    f = P.token_frame(s, bars, CFG)
    assert f.index.min() == hours[400] + pd.Timedelta(days=30) and f.index.max() == hours[4399]
    assert len([c for c in f.columns if c.startswith('n_')]) == 42 and {'h0_rv24', 'px_rv6', 'V6', 'V24'} <= set(f.columns)
    assert 'token' not in f.columns


def test_cross_section_min_tokens_and_xv24():
    rng = np.random.default_rng(22)
    hours = pd.date_range('2023-01-01', periods=10, freq='h')
    cfg = {**CFG, 'panel': {**CFG['panel'], 'min_tokens_hour': 3}}
    p = _panel(4, hours, rng)
    p = p[~((p.index == hours[2]) & (p['token'] >= 2))]                                 # hour 2 has 2 tokens
    x = P.cross_section(p, cfg)
    cols = ['xs_n_dep_usd__s24z', 'xs_n_dep_usd__ex1', 'xs_h0_rv24', 'xs_h0_lvol24']
    assert set(c for c in x.columns if c.startswith('xs_')) == set(cols) and 'XV24' in x.columns
    h0 = x.loc[hours[0]]
    assert np.isclose(h0['xs_h0_rv24'].mean(), 0) and np.isclose(h0['xs_h0_rv24'].std(ddof=1), 1)
    assert np.allclose(h0['XV24'], h0['V24'] - h0['V24'].mean())
    assert x.loc[hours[2], cols + ['XV24']].isna().all().all() and x.loc[hours[3], cols].notna().all().all()
    assert len(x) == len(p) and (x['token'] == p['token']).all()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8/test_panel8.py -q`
Expected: FAIL with `ImportError: cannot import name 'panel8'`

- [ ] **Step 3: Write the module**

```python
# tradingagents/research/onchain_b8/panel8.py
"""Panel rows (spec §4): per token, B7's engineering of the seven series plus price and
intraday features and the V6 / V24 targets; per hour, cross-sectional z-scores and the
relative target XV24. A token enters `entry_days` after its first bar."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b4 import dataset4
from ..onchain_b5.decisions import px_features
from ..onchain_b7.features7 import multiscale
from .hourly8 import SERIES


def token_series(day_frames, hours, token_index):
    parts = [f[f['token'] == token_index].set_index('hour')[SERIES] for f in day_frames]
    s = pd.concat(parts).sort_index() if parts else pd.DataFrame(columns=SERIES)
    return s.reindex(hours)


def token_frame(series, bars, c):
    f = multiscale(series, c['engineering'])
    m = dataset4.price_features(bars).join(px_features(bars))
    t = dataset4.hourly_targets(bars)[['V6', 'V24']]
    df = f.join(m, how='inner').join(t, how='left')
    start = bars.index.min() + pd.Timedelta(days=c['panel']['entry_days'])
    return df[df.index >= start]


def cross_section(panel, c):
    pc = c['panel']
    cols = [col for col in panel.columns if col.startswith('n_') and col.endswith(tuple(pc['xs_series']))] + list(pc['xs_price'])
    g = panel.groupby(level=0)
    mean, std, cnt = g[cols].transform('mean'), g[cols].transform('std'), g[cols].transform('count')
    z = (panel[cols] - mean) / std
    z = z.where((cnt >= pc['min_tokens_hour']) & (std > 0))
    vm, vc = g['V24'].transform('mean'), g['V24'].transform('count')
    out = panel.copy()
    for col in cols:                     # positional assignment: the hour index is not unique, so no join
        out[f'xs_{col}'] = z[col].to_numpy()
    out['XV24'] = (panel['V24'] - vm).where(vc >= pc['min_tokens_hour']).to_numpy()
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8/test_panel8.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b8/panel8.py tests/research/onchain_b8/test_panel8.py
git commit -m "feat(onchain-b8): per-token panel features, cross-section and targets"
```

---

### Task 5: forecast8 — pooled folds, hour-block bootstrap, criteria, tables

**Files:**
- Create: `tradingagents/research/onchain_b8/forecast8.py`
- Test: `tests/research/onchain_b8/test_forecast8.py`

**Interfaces:**
- Consumes: `onchain_b7.models7.fit_predict7`, `onchain_b7.forecast7.{columns, detail_report}`, `onchain_b2.screen.{folds, row_loss}`, `onchain_b4.screen4.interval`.
- Produces: `set_prefixes(name, cfg)`, `samples(panel, cfg) -> DataFrame`, `predict_all(df, target, cfg, log=None) -> (P, meta)` (P has `fam:set` columns, `token`, `y`, `const`, `tested`), `compare(P, target, cfg) -> list[dict]` (keys as B7 plus `n_rows`, `n_hours`), `per_token(P, target, cfg) -> DataFrame[target, family, set, comparator, token, n, mean_diff]`, `report(results) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b8/test_forecast8.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b8 import config, forecast8 as F

CFG = config.load()
SMALL = {**CFG, 'folds': {'test_years': [2022, 2023], 'inner_len': 200, 'min_train': 100, 'min_year_wins': 2},
         'models': {**CFG['models'], 'trees_es': {**CFG['models']['trees_es'], 'max_iter': 30, 'min_iter': 5}},
         'gate': {**CFG['gate'], 'draws': 200, 'block': 24}, 'window': {'first_day': '2021-01-01', 'last_day': '2023-12-31'}}


def _panel(rng, n_tok=6, start='2021-01-01', end='2023-12-31'):
    hours = pd.date_range(start, end, freq='12h')
    frames = []
    for j in range(n_tok):
        sig = rng.normal(size=len(hours))
        f = pd.DataFrame({'h0_r1': rng.normal(size=len(hours)), 'px_rv6': rng.normal(size=len(hours)), 'xs_h0_rv24': rng.normal(size=len(hours)),
                          'n_dep_usd__z1': rng.normal(size=len(hours)), 'xs_n_dep_usd__ex1': sig, 'other': 1.0,
                          'V6': 2 * sig + 0.3 * rng.normal(size=len(hours)), 'V24': rng.normal(size=len(hours)), 'XV24': rng.normal(size=len(hours))},
                         index=hours)
        f['token'] = np.int16(j)
        frames.append(f)
    return pd.concat(frames).sort_index(kind='stable')


def test_samples_and_prefixes():
    assert F.set_prefixes('P2', CFG) == ['h0_', 'px_', 'xs_h0_', 'n_', 'xs_n_']
    rng = np.random.default_rng(31)
    p = _panel(rng)
    p.iloc[10, p.columns.get_loc('n_dep_usd__z1')] = np.nan
    s = F.samples(p, SMALL)
    assert 'other' not in s.columns and 'token' in s.columns and len(s) == len(p) - 1
    assert s.loc[pd.Timestamp('2023-12-31 00:00'), 'V24'].isna().all() and s.loc[pd.Timestamp('2023-12-31 00:00'), 'V6'].notna().all()   # the 12-hourly range ends at 00:00


def test_compare_weights_hours_not_rows():
    rng = np.random.default_rng(32)
    p = _panel(rng)
    s = F.samples(p, SMALL)
    P, meta = F.predict_all(s, 'V6', SMALL)
    assert {'ridge:P0', 'trees_es:P2', 'token', 'y', 'const', 'tested'} <= set(P.columns) and set(meta['ridge:P2']) == {2022, 2023}
    res = F.compare(P, 'V6', SMALL)
    assert len(res) == 6
    get = {(r['family'], r['set'], r['comparator']): r for r in res}
    r = get[('ridge', 'P2', 'P1')]
    assert r['passed'] and r['criterion'] == 'interval+years' and r['n_hours'] == P['tested'].sum() // 6 and r['n_rows'] == P['tested'].sum()
    assert not get[('ridge', 'P1', 'P0')]['passed'] and get[('ridge', 'P2', 'P0')]['gain_set'] > 0.5
    # hour weighting: duplicate every row of one hour 50 times -> the per-hour mean is unchanged, so the statistics are too
    h = P.index[P['tested'].to_numpy()][0]
    dup = pd.concat([P] + [P.loc[[h]]] * 50).sort_index(kind='stable')
    r2 = {(x['family'], x['set'], x['comparator']): x for x in F.compare(dup, 'V6', SMALL)}[('ridge', 'P2', 'P1')]
    assert r2['n_hours'] == r['n_hours'] and np.isclose(r2['mean_diff'], r['mean_diff']) and r2['n_rows'] == r['n_rows'] + 300
    t = F.per_token(P, 'V6', SMALL)
    assert set(t['token']) == set(range(6)) and len(t) == 6 * 6 and (t['n'] > 0).all()
    text = F.report(res)
    assert '| V6 | ridge | P2 vs P1 |' in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8/test_forecast8.py -q`
Expected: FAIL with `ImportError: cannot import name 'forecast8'`

- [ ] **Step 3: Write the module**

```python
# tradingagents/research/onchain_b8/forecast8.py
"""Pooled walk-forward comparisons on the token panel (spec §5): one model across tokens per
fold, per-row losses averaged per hour, a block bootstrap over hours, a per-year criterion."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2.screen import folds, row_loss
from ..onchain_b4.screen4 import interval
from ..onchain_b7.forecast7 import columns
from ..onchain_b7.models7 import fit_predict7

H = pd.Timedelta(hours=1)


def set_prefixes(name, cfg):
    out = list(cfg['blocks']['base'])
    for b in cfg['sets'][name]:
        out += cfg['blocks'][b]
    return out


def samples(panel, cfg):
    end = pd.Timestamp(cfg['window']['last_day']) + pd.Timedelta(days=1)
    pre = sorted({p for s in cfg['sets'] for p in set_prefixes(s, cfg)})
    tcols = list(cfg['targets'])
    feat = columns(panel, pre)
    df = panel[['token'] + feat + tcols]
    df = df[np.isfinite(df[feat].to_numpy(np.float32)).all(axis=1)].copy()
    for name, t in cfg['targets'].items():
        df.loc[df.index + pd.Timedelta(hours=t['h']) > end - H, name] = np.nan
    return df


def predict_all(df, target, cfg, log=None):
    fc = cfg['folds']
    h = cfg['targets'][target]['h']
    d = df[df[target].notna()].sort_index(kind='stable')
    y = d[target].to_numpy(float)
    fl = [(yr, tr, te) for yr, tr, te in folds(d.index, fc['test_years'], h / 24) if te.any() and tr.sum() >= fc['min_train']]
    tested, const = np.zeros(len(d), bool), np.full(len(d), np.nan)
    for _, tr, te in fl:
        tested |= te
        const[te] = y[tr].mean()
    preds, meta = {}, {}
    for fam in cfg['families']:
        for s in cfg['sets']:
            key = f'{fam}:{s}'
            X = d[columns(d, set_prefixes(s, cfg))].to_numpy(np.float32)
            p, meta[key] = np.full(len(d), np.nan), {}
            for yr, tr, te in fl:
                info = {}
                p[te] = fit_predict7(fam, 'regression', X[tr], y[tr], X[te], cfg, info)
                meta[key][int(yr)] = info
                if log is not None:
                    log(event='fit', target=target, fit=key, year=int(yr), n_train=int(tr.sum()), **info)
            preds[key] = p
    P = pd.DataFrame(preds, index=d.index)
    P['token'] = d['token'].to_numpy()
    P['y'], P['const'], P['tested'] = y, const, tested
    return P, meta


def _gain(loss, const):
    return float(1 - loss / const) if np.isfinite(loss) and np.isfinite(const) and const > 0 else np.nan


def compare(P, target, cfg):
    g, fc = cfg['gate'], cfg['folds']
    y, const, tested = P['y'].to_numpy(float), P['const'].to_numpy(float), P['tested'].to_numpy(bool)
    results = []
    for a, b in cfg['comparisons']:
        for fam in cfg['families']:
            la = row_loss('regression', y, P[f'{fam}:{a}'].to_numpy(float))
            lb = row_loss('regression', y, P[f'{fam}:{b}'].to_numpy(float))
            m = tested & np.isfinite(la) & np.isfinite(lb)
            per_hour = pd.Series((la - lb)[m], index=P.index[m]).groupby(level=0).mean()
            yrs = per_hour.index.year.to_numpy()
            v = per_hour.to_numpy()
            lo, hi = interval(v, g['block'], g['draws'], g['seed'], g['chunk']) if len(v) >= g['block'] else (np.nan, np.nan)
            per_year = {int(yr): float(v[yrs == yr].mean()) for yr in fc['test_years'] if (yrs == yr).any()}
            wins = int(sum(x < 0 for x in per_year.values()))
            lc = float(row_loss('regression', y[m], const[m]).mean()) if m.any() else np.nan
            ls, lcomp = (float(la[m].mean()), float(lb[m].mean())) if m.any() else (np.nan, np.nan)
            results.append({'target': target, 'family': fam, 'set': a, 'comparator': b, 'n_rows': int(m.sum()), 'n_hours': int(len(v)),
                            'mean_diff': float(v.mean()) if len(v) else np.nan, 'lo': lo, 'hi': hi, 'wins': wins, 'years': per_year,
                            'loss_set': ls, 'loss_comparator': lcomp, 'loss_constant': lc,
                            'gain_set': _gain(ls, lc), 'gain_comparator': _gain(lcomp, lc),
                            'passed': bool(hi < 0 and wins >= fc['min_year_wins']), 'criterion': 'interval+years'})
    return results


def per_token(P, target, cfg):
    y, tested = P['y'].to_numpy(float), P['tested'].to_numpy(bool)
    rows = []
    for a, b in cfg['comparisons']:
        for fam in cfg['families']:
            la = row_loss('regression', y, P[f'{fam}:{a}'].to_numpy(float))
            lb = row_loss('regression', y, P[f'{fam}:{b}'].to_numpy(float))
            m = tested & np.isfinite(la) & np.isfinite(lb)
            d = pd.DataFrame({'token': P['token'].to_numpy()[m], 'diff': (la - lb)[m]}).groupby('token')['diff'].agg(['count', 'mean'])
            for tok, r in d.iterrows():
                rows.append({'target': target, 'family': fam, 'set': a, 'comparator': b, 'token': int(tok), 'n': int(r['count']), 'mean_diff': float(r['mean'])})
    return pd.DataFrame(rows, columns=['target', 'family', 'set', 'comparator', 'token', 'n', 'mean_diff'])


def report(results):
    lines = ['| target | family | comparison | rows | hours | mean diff | 95 % CI | years better | pass | gain vs constant (set / comparator) |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for r in results:
        lines.append(f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n_rows']} | {r['n_hours']} | "
                     f"{r['mean_diff']:+.5f} | [{r['lo']:+.5f}, {r['hi']:+.5f}] | {r['wins']}/{len(r['years'])} | "
                     f"{'PASS' if r['passed'] else '—'} | {r['gain_set']:+.4f} / {r['gain_comparator']:+.4f} |")
    return '\n'.join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8/test_forecast8.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b8/forecast8.py tests/research/onchain_b8/test_forecast8.py
git commit -m "feat(onchain-b8): pooled comparisons with hour-block bootstrap"
```

---

### Task 6: cli — universe, pass (resumable, watchdog), panel, forecast, report

**Files:**
- Create: `tradingagents/research/onchain_b8/cli.py`
- Test: `tests/research/onchain_b8/test_cli8.py`

**Interfaces:**
- Consumes: everything above; `onchain_b.runlog.Log`; `onchain_b4.cli.{MIN_FREE_LAUNCH, READ_TIMEOUT, STALL_EXIT, _write_json, _peak_rss_mb}`; `onchain_b6.labels6.{LabelState, load}`; `onchain_b7.forecast7.detail_report`.
- Produces: stages `universe`, `pass [--end]`, `panel`, `forecast [--only V6,...]`, `report`; files `research/onchain-b8-2026-10-22/config/universe.json`, `research_artifacts/onchain-b8/days/<day>.parquet | <day>.unavailable.json`, `panel/panel.parquet` (float32 features, `token` column), `forecast/<target>.json`, `forecast/pred_<target>.parquet`, `forecast/per_token.csv`, `forecast/results.json`, `research/onchain-b8-2026-10-22/TABLES.md`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b8/test_cli8.py
import copy
import json

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2.s3source import DayUnavailable
from tradingagents.research.onchain_b4.reader import addr_keys
from tradingagents.research.onchain_b6 import labels6
from tradingagents.research.onchain_b6.labels6 import LabelState
from tradingagents.research.onchain_b8 import cli, config, reader8
from tradingagents.research.onchain_b8.reader8 import Day8

A, B, X = ('0x' + ch * 40 for ch in 'abx')
T0, T1 = '2020-06-01', '2021-12-31'


def _klines(path, symbol, n, rng, start=T0):
    idx = pd.date_range(start, periods=n, freq='h', tz='UTC')
    close = 10 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    pd.DataFrame({'open': close, 'high': close, 'low': close, 'close': close, 'volume': 1.0, 'quote_volume': rng.gamma(2, 1e5, n),
                  'taker_buy_quote_volume': 1.0}, index=pd.Index(idx, name='ts')).to_parquet(path / f'{symbol}.parquet')


def _setup(tmp_path, monkeypatch, unavailable=()):
    rng = np.random.default_rng(41)
    cfg = copy.deepcopy(config.load())
    cfg['window'] = {'first_day': T0, 'last_day': T1}
    cfg['universe']['min_rows'] = 1000
    cfg['s3']['retries'] = []
    cfg['panel']['min_tokens_hour'] = 2
    cfg['folds'] = {'test_years': [2021], 'inner_len': 300, 'min_train': 100, 'min_year_wins': 1}
    cfg['models']['trees_es'].update({'max_iter': 20, 'min_iter': 5})
    cfg['gate'].update({'draws': 100, 'block': 24})
    k, b6, art, study = tmp_path / 'k', tmp_path / 'b6', tmp_path / 'b8', tmp_path / 'study'
    for p in (k, b6 / 'labels', b6 / 'state', study / 'config'):
        p.mkdir(parents=True)
    n = 24 * 579
    for sym in ('AAAUSDT', 'BBBUSDT', 'CCCUSDT'):
        _klines(k, sym, n, rng)
    tm = {'map': {'AAAUSDT': {'address': '0x' + '1' * 40, 'decimals': 18, 'how': 'binance_spot'},
                  'BBBUSDT': {'address': '0x' + '2' * 40, 'decimals': 6, 'how': 'binance_spot'},
                  'CCCUSDT': {'address': '0x' + '3' * 40, 'decimals': 18, 'how': 'binance_spot'}}}
    (tmp_path / 'map.json').write_text(json.dumps(tm))
    doc = {'exchange': {X: 'okx'}, 'dex': [], 'bridge': [], 'mev': [], 'funds': [], 'issuer': {'usdt_treasury': '0x5754284f345afc66a98fbb0a0afe71e0f007b949'}}
    labels6.save(doc, b6 / 'labels' / 'labels6.json')
    st = LabelState(doc, doc['issuer']['usdt_treasury'])
    st.ex_first[:] = config.day_ord('2020-01-01')
    np.savez(b6 / 'state' / 'state.npz', ex_first=st.ex_first, **{f'cls_first_{c}': st.cls_first[c] for c in labels6.CLASSES},
             bits=np.zeros(8, np.uint8), last_day=np.array(['2026-10-11']))
    monkeypatch.setattr(config, 'KLINES', k)
    monkeypatch.setattr(config, 'TOKEN_MAP', tmp_path / 'map.json')
    monkeypatch.setattr(cli, 'B6', b6)
    monkeypatch.setattr(cli, 'ARTIFACTS', art)
    monkeypatch.setattr(cli, 'STUDY', study)
    monkeypatch.setattr(cli.config, 'load', lambda: cfg)
    monkeypatch.setattr(cli.config, 'universe', lambda: json.loads((study / 'config' / 'universe.json').read_text())['tokens'])
    monkeypatch.setattr(cli, 'filesystem', lambda: None)
    monkeypatch.setattr(cli.shutil, 'disk_usage', lambda p: type('U', (), {'free': 10**12})())
    ka, kb, kx = addr_keys(np.array([A, B, X], object))

    def fake(day, **kw):
        if day in unavailable:
            raise DayUnavailable(day, ['boom'])
        t0 = int(pd.Timestamp(day, tz='UTC').timestamp())
        r = np.random.default_rng(int(day.replace('-', '')))
        n_tr = 40
        src = r.choice([ka, kb, kx], n_tr)
        dst = r.choice([ka, kb, kx], n_tr)
        return Day8(src=src.astype(np.uint64), dst=dst.astype(np.uint64), token=r.integers(0, 3, n_tr).astype(np.int16),
                    amount=r.gamma(2, 1000, n_tr), ts=np.sort(t0 + r.integers(0, 86400, n_tr)).astype(np.int64), rows={'transfers': n_tr})
    monkeypatch.setattr(reader8, 'read_day8', fake)
    return cfg, art, study


def test_universe_stage_freezes_once(tmp_path, monkeypatch):
    cfg, art, study = _setup(tmp_path, monkeypatch)
    cli.main(['universe'])
    u = json.loads((study / 'config' / 'universe.json').read_text())
    assert [t['symbol'] for t in u['tokens']] == ['AAAUSDT', 'BBBUSDT', 'CCCUSDT'] and u['min_rows'] == 1000
    with pytest.raises(SystemExit):
        cli.main(['universe'])


def test_pass_resumes_and_marks_unavailable(tmp_path, monkeypatch):
    cfg, art, study = _setup(tmp_path, monkeypatch, unavailable=('2020-06-03',))
    cli.main(['universe'])
    cli.main(['pass', '--end', '2020-06-05'])
    d = pd.read_parquet(art / 'days' / '2020-06-02.parquet')
    assert len(d) == 72 and list(d.columns) == ['hour', 'token'] + cli.hourly8.SERIES and d['dep_usd'].notna().all()
    assert (art / 'days' / '2020-06-03.unavailable.json').exists() and not (art / 'days' / '2020-06-03.parquet').exists()
    stamp = (art / 'days' / '2020-06-02.parquet').stat().st_mtime_ns
    cli.main(['pass', '--end', '2020-06-07'])
    assert (art / 'days' / '2020-06-02.parquet').stat().st_mtime_ns == stamp and (art / 'days' / '2020-06-07.parquet').exists()
    assert not cli.pass_complete() and cli.day_status('2020-06-03') == 'unavailable'


def test_panel_forecast_report(tmp_path, monkeypatch):
    cfg, art, study = _setup(tmp_path, monkeypatch, unavailable=('2021-06-15',))
    cli.main(['universe'])
    cli.main(['pass'])
    assert cli.pass_complete()
    cli.main(['panel'])
    p = pd.read_parquet(art / 'panel' / 'panel.parquet')
    assert p['token'].nunique() == 3 and p.index.min() >= pd.Timestamp(T0) + pd.Timedelta(days=30)
    assert {'n_dep_usd__ex1', 'xs_n_dep_usd__s24z', 'xs_h0_rv24', 'h0_rv24', 'px_rv6', 'V6', 'V24', 'XV24'} <= set(p.columns)
    assert p['n_dep_usd__ex1'].dtype == np.float32
    assert p.loc['2021-06-15':'2021-06-16 22:00', 'n_dep_usd__s24z'].isna().all() and p.loc['2021-06-16 23:00':'2021-06-17', 'n_dep_usd__s24z'].notna().all()
    cli.main(['forecast', '--only', 'V6'])
    assert (art / 'forecast' / 'V6.json').exists()
    cli.main(['forecast'])
    res = json.loads((art / 'forecast' / 'results.json').read_text())
    assert len(res['results']) == 18 and set(res['meta']) == {'V6', 'V24', 'XV24'} and res['n']['V6']['years']['2021']['hours'] > 1000
    assert (art / 'forecast' / 'per_token.csv').exists()
    cli.main(['report'])
    text = (study / 'TABLES.md').read_text()
    assert '| XV24 | trees_es | P2 vs P0 |' in text and 'V6 | trees_es:P2' in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8/test_cli8.py -q`
Expected: FAIL with `ImportError: cannot import name 'cli'`

- [ ] **Step 3: Write the module**

```python
# tradingagents/research/onchain_b8/cli.py
"""B8 stage runner: universe freeze, the sequential token_transfers pass (resumable by day
file, read watchdog), the panel, pooled forecasts (resumable per target) and the tables."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

import numpy as np
import pandas as pd

from ..onchain_b.runlog import Log
from ..onchain_b2.s3source import DayUnavailable
from ..onchain_b4.cli import MIN_FREE_LAUNCH, READ_TIMEOUT, STALL_EXIT, _peak_rss_mb, _write_json
from ..onchain_b6 import labels6
from ..onchain_b6.labels6 import LabelState
from ..onchain_b7.forecast7 import detail_report
from . import config, forecast8, hourly8, panel8, reader8, universe8

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B6 = config.B6_ARTIFACTS
_hard_exit = os._exit


def _require_disk(min_bytes, what):
    p = ARTIFACTS
    while not p.exists():
        p = p.parent
    free = shutil.disk_usage(p).free
    if free < min_bytes:
        raise SystemExit(f'only {free / 1e9:.1f} GB disk free; {what} needs {min_bytes / 1e9:.1f} GB')


def filesystem():
    import pyarrow.fs as pafs
    return pafs.S3FileSystem(anonymous=True, region=config.load()['s3']['region'])


def stage_universe(args):
    c = config.load()
    out = STUDY / 'config' / 'universe.json'
    if out.exists():
        raise SystemExit('universe already frozen')
    tokens = universe8.build(config.TOKEN_MAP, config.KLINES, c['universe']['min_rows'])
    _write_json(out, {'tokens': tokens, 'min_rows': c['universe']['min_rows'], 'token_map': str(config.TOKEN_MAP), 'klines': str(config.KLINES)})
    print(json.dumps({'tokens': len(tokens)}))


def day_status(day):
    if (ARTIFACTS / 'days' / f'{day}.parquet').exists():
        return 'done'
    if (ARTIFACTS / 'days' / f'{day}.unavailable.json').exists():
        return 'unavailable'
    return None


def pass_complete():
    return all(day_status(d) is not None for d in config.days(config.load()))


def _state():
    doc = labels6.load(B6 / 'labels' / 'labels6.json')
    st = LabelState(doc, doc.get('issuer', {}).get('usdt_treasury', '0x5754284f345afc66a98fbb0a0afe71e0f007b949'))
    z = np.load(B6 / 'state' / 'state.npz')
    st.ex_first = z['ex_first'].copy()
    return st


def _bars_all(tokens):
    return [universe8.load_bars(config.KLINES, t['symbol']) for t in tokens]


def stage_pass(args):
    c = config.load()
    _require_disk(MIN_FREE_LAUNCH, 'pass launch')
    tokens = config.universe()
    contracts = {t['address']: (i, t['decimals']) for i, t in enumerate(tokens)}
    days = [d for d in config.days(c) if args.end is None or d <= args.end]
    hours = pd.date_range(days[0], periods=24 * len(days), freq='h')
    prices = hourly8.price_matrix(_bars_all(tokens), hours)
    st = _state()
    log = Log(ARTIFACTS / 'logs' / 'pass.jsonl')
    fs, p = filesystem(), c['pass']
    out = ARTIFACTS / 'days'
    out.mkdir(parents=True, exist_ok=True)
    todo = [d for d in days if day_status(d) is None]

    def fetch(day):
        return reader8.read_day8(day, filesystem=fs, root=c['s3']['bucket'], contracts=contracts, retries=c['s3']['retries'])

    consecutive = 0
    pool = ThreadPoolExecutor(max_workers=max(1, p['prefetch']))
    try:
        futures = {}
        for i, day in enumerate(todo):
            for nxt in todo[i:i + p['prefetch'] + 1]:
                if nxt not in futures:
                    futures[nxt] = pool.submit(fetch, nxt)
            t = time.time()
            try:
                d = futures.pop(day).result(timeout=READ_TIMEOUT)
            except FuturesTimeout:
                log.event(event='stall', day=day, after_seconds=READ_TIMEOUT)
                pool.shutdown(wait=False, cancel_futures=True)
                _hard_exit(STALL_EXIT)
            except DayUnavailable as e:
                _write_json(out / f'{day}.unavailable.json', {'day': day, 'errors': e.errors})
                log.event(event='day', day=day, status='unavailable')
                consecutive += 1
                if consecutive >= p['max_consecutive_unavailable']:
                    raise SystemExit(f'{consecutive} consecutive unavailable days up to {day}: stopping the pass')
                continue
            consecutive = 0
            st.begin_day(config.day_ord(day))
            k = days.index(day)
            rows = hourly8.day_rows(day, d, st, prices[24 * k:24 * (k + 1)], c['big_usd'])
            tmp = out / f'.{day}.parquet.tmp'
            rows.to_parquet(tmp)
            os.replace(tmp, out / f'{day}.parquet')
            log.event(event='day', day=day, status='done', seconds=round(time.time() - t, 1), transfers=int(len(d.src)), peak_rss_mb=_peak_rss_mb())
            del d
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def stage_panel(args):
    if not pass_complete():
        raise SystemExit('pass incomplete: build or mark every day first')
    c = config.load()
    tokens = config.universe()
    days = config.days(c)
    hours = pd.date_range(days[0], periods=24 * len(days), freq='h')
    frames = [pd.read_parquet(ARTIFACTS / 'days' / f'{d}.parquet') for d in days if day_status(d) == 'done']
    bars = _bars_all(tokens)
    parts = []
    for i, t in enumerate(tokens):
        f = panel8.token_frame(panel8.token_series(frames, hours, i), bars[i], c)
        f['token'] = np.int16(i)
        parts.append(f)
    panel = pd.concat(parts).sort_index(kind='stable')
    panel = panel8.cross_section(panel, c)
    feat = [col for col in panel.columns if col not in ('token', 'V6', 'V24', 'XV24')]
    panel[feat] = panel[feat].astype(np.float32)
    (ARTIFACTS / 'panel').mkdir(parents=True, exist_ok=True)
    panel.to_parquet(ARTIFACTS / 'panel' / 'panel.parquet')
    print(json.dumps({'rows': len(panel), 'tokens': int(panel['token'].nunique()), 'columns': panel.shape[1],
                      'first': str(panel.index.min()), 'last': str(panel.index.max())}))


def _support(df, target):
    s = df[target]
    ok, yrs, tok = s.notna().to_numpy(), df.index.year.to_numpy(), df['token'].to_numpy()
    years = {}
    for yr in np.unique(yrs):
        m = ok & (yrs == yr)
        years[int(yr)] = {'rows': int(m.sum()), 'hours': int(df.index[m].nunique()), 'tokens': int(np.unique(tok[m]).size)}
    return {'n': int(ok.sum()), 'mean': float(s.mean()), 'years': years}


def stage_forecast(args):
    c = config.load()
    only = set(args.only.split(',')) if args.only else None
    panel = pd.read_parquet(ARTIFACTS / 'panel' / 'panel.parquet')
    df = forecast8.samples(panel, c)
    out = ARTIFACTS / 'forecast'
    out.mkdir(parents=True, exist_ok=True)
    log = Log(ARTIFACTS / 'logs' / 'forecast.jsonl')
    n = {t: _support(df, t) for t in c['targets']}
    for target in c['targets']:
        unit = out / f'{target}.json'
        if (only is not None and target not in only) or unit.exists():
            continue
        t0 = time.time()
        P, meta = forecast8.predict_all(df, target, c, log=log.event)
        res = forecast8.compare(P, target, c)
        P.to_parquet(out / f'pred_{target}.parquet')
        forecast8.per_token(P, target, c).to_csv(out / f'per_token_{target}.csv', index=False)
        _write_json(unit, {'results': res, 'meta': meta, 'seconds': round(time.time() - t0, 1)})
        log.event(event='unit', target=target, seconds=round(time.time() - t0, 1), passed=sum(r['passed'] for r in res))
    units = [out / f'{t}.json' for t in c['targets'] if (out / f'{t}.json').exists()]
    docs = {u.stem: json.loads(u.read_text()) for u in units}
    results = [r for d in docs.values() for r in d['results']]
    pt = [out / f'per_token_{t}.csv' for t in c['targets'] if (out / f'per_token_{t}.csv').exists()]
    if pt:
        pd.concat([pd.read_csv(p) for p in pt]).to_csv(out / 'per_token.csv', index=False)
    _write_json(out / 'results.json', {'results': results, 'meta': {k: d['meta'] for k, d in docs.items()}, 'n': n,
                                       'seconds': {k: d['seconds'] for k, d in docs.items()}})
    print(json.dumps({'units': len(units), 'rows': len(results), 'passed': sum(r['passed'] for r in results)}))


def stage_report(args):
    res = json.loads((ARTIFACTS / 'forecast' / 'results.json').read_text())
    lines = ['# B8 tables (generated; interpretation in RESULTS.md)', '', '## Samples', '',
             '| target | rows | mean | per year rows / hours / tokens |', '|---|---|---|---|']
    for t, v in res['n'].items():
        per = ', '.join(f"{yr} {d['rows']} / {d['hours']} / {d['tokens']}" for yr, d in sorted(v['years'].items(), key=lambda kv: int(kv[0])))
        lines.append(f"| {t} | {v['n']} | {v['mean']:.4f} | {per} |")
    lines += ['', '## Comparisons', '', forecast8.report(res['results']), '', '## Model detail', '', detail_report(res['meta']),
              '', 'Per-token differences (post hoc): `research_artifacts/onchain-b8/forecast/per_token.csv`.']
    STUDY.mkdir(parents=True, exist_ok=True)
    (STUDY / 'TABLES.md').write_text('\n'.join(lines) + '\n')
    print(f'{len(lines)} lines')


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b8')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('universe').set_defaults(fn=stage_universe)
    a = sub.add_parser('pass')
    a.add_argument('--end', default=None)
    a.set_defaults(fn=stage_pass)
    sub.add_parser('panel').set_defaults(fn=stage_panel)
    f = sub.add_parser('forecast')
    f.add_argument('--only', default=None, help='comma-separated targets')
    f.set_defaults(fn=stage_forecast)
    sub.add_parser('report').set_defaults(fn=stage_report)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8/test_cli8.py -q`
Expected: `3 passed`

- [ ] **Step 5: Run the whole package suite and commit**

Run: `.venv/bin/python -m pytest tests/research/onchain_b8 -q`
Expected: `15 passed`

```bash
git add tradingagents/research/onchain_b8/cli.py tests/research/onchain_b8/test_cli8.py
git commit -m "feat(onchain-b8): stage runner with resumable pass and forecasts"
```

---

### Task 7: Freeze, review, run, report

- [ ] **Step 1: Freeze the universe and commit it with STATE (B8-CP1)**

Run: `.venv/bin/python -m tradingagents.research.onchain_b8.cli universe`
Expected: `{"tokens": 148}` (or the deduplicated count); commit `research/onchain-b8-2026-10-22/config/universe.json`.

- [ ] **Step 2: Fresh whole-branch review**; fix Critical/Important with tests.

- [ ] **Step 3: Probe one day, then launch the pass as a systemd unit after the B7 forecast unit has finished**

```bash
P=$PWD; systemd-run --user --unit onchain-b8-pass -p MemoryMax=6G -p Restart=no -p RestartForceExitStatus=75 -p RestartSec=60 -p WorkingDirectory=$P $P/.venv/bin/python -m tradingagents.research.onchain_b8.cli pass
```
Expected: ≈ 2,250 day files over 6–12 h; stalls exit 75 and restart; reboots resume by relaunching.

- [ ] **Step 4: Panel, forecast, report, results**

Run: `cli panel` (minutes), `cli forecast` (systemd unit, ≈ 2–3 h), `cli report`; write `RESULTS.md`; update STATE (B8-CP2…CP4); commit.
