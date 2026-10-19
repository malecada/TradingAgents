# B6 Hourly Structure, Entity Detail and Minute Events — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One labels-only day pass over 2017–2026 that writes hourly graph-structure, token-split, counterparty-class and issuance series plus large-transfer records; a forecast comparison of those blocks against intraday price and option-market baselines on two tracks; a minute-level event study of very large deposits; and an optional Tron USDT block.

**Architecture:** New package `tradingagents/research/onchain_b6/` importing B2–B5 primitives. Frozen label sets with day-after activation; a B6 admission that keeps mint/burn rows and token codes; per-hour structure and flow blocks with a Bloom filter of all addresses seen; B5's forecast runner wrapped per track and target; a minute module over Binance 1-minute closes; an SQD stream for Tron.

**Tech Stack:** Python 3.13, numpy, pandas, pyarrow, scipy, scikit-learn via B2 `fit_predict`, pytest; systemd user units.

**Spec:** `docs/superpowers/specs/2026-10-19-onchain-b6-structure-entities-design.md`

## Global Constraints

- Exploratory with a pre-declared plan: `research/onchain-b6-2026-10-19/PLAN.md` committed before any pass output is read; every item reported.
- Pass window 2017-01-01 … 2026-10-11 (3,571 days), sequential; labels-only entities; activation = day after first observed transfer; Bloom 2³³ bits, 5 hashes.
- Blocks F (`eth_`, `stable_`), S (`gs_`), E (`tk_`, `cl_`, `is_`), T (`tron_`); bases P0 (`h0_`, `px_`) and K0 (P0 + `mk_`); sets X0 … X4 (X5 with Tron); comparisons X1 vs X0, X2 vs X1, X3 vs X1, X4 vs X1 (X5 vs X4 with Tron); targets V6, V24; families linear, trees.
- Track A 2017-10-02 → 2024-12-31, test years 2019–2024, criterion upper < 0 and ≥ 4/6 years; track B 2021-04-01 → 2026-10-12, test years 2022–2026, criterion upper < 0 in 2022–24 and mean < 0 in 2025–26. Bootstrap block 168, draws 2,000, seed 20261020.
- Minute events: deposits ≥ $10M stablecoin or ≥ 5,000 ETH (tier 2: ≥ $50M / ≥ 20,000 ETH), withdrawals likewise, first per 30 minutes per direction and tier; responses from m + 1.
- `onchain_b` … `onchain_b5` imported, not edited. Docs impersonal. Commits end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Package test command: `.venv/bin/python -m pytest tests/research/onchain_b6 -q`.

## Review Focus

1. A labelled address first seen today must not count as labelled today, only from tomorrow (Task 2 `test_activation_is_day_after_first_observation`).
2. Hours with no transfers or a single transfer → structure features finite, no division by zero (Task 4 `test_structure_degenerate_hours`).
3. Mint/burn rows must never enter the transfer graph, flows or large-transfer records, only issuance (Task 5 `test_mint_burn_only_in_issuance`).
4. Event responses must start the minute after the block minute, and placebo minutes must stay ≥ 60 minutes from every event (Task 6 `test_response_alignment_and_placebo_gap`).
5. A Tron stream that returns a partial block range must be continued, and HTTP 529 must back off, not mark the day (Task 7 `test_stream_continues_partial_and_backs_off`).

---

### Task 1: Skeleton, configuration, registration

**Files:**
- Create: `tradingagents/research/onchain_b6/__init__.py` (empty), `tradingagents/research/onchain_b6/config.py`
- Create: `research/onchain-b6-2026-10-19/config/b6.json`, `CHARTER.md`, `PLAN.md`, `STATE.md`
- Modify: `.gitignore` (add `/research_artifacts/onchain-b6/`)
- Test: `tests/research/onchain_b6/__init__.py` (empty), `tests/research/onchain_b6/test_config.py`

**Interfaces:**
- Produces: `config.ROOT/STUDY/ARTIFACTS/B2_ARTIFACTS/B4_ARTIFACTS/B5_ARTIFACTS`; `config.load()`; `config.days(cfg=None) -> list[str]`; `config.day_ord(day) -> int`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b6/test_config.py
from tradingagents.research.onchain_b6 import config


def test_config_window_sets_and_tracks():
    c = config.load()
    d = config.days(c)
    assert len(d) == 3571 and d[0] == '2017-01-01' and d[-1] == '2026-10-11'
    assert config.day_ord('2017-01-01') == 0 and config.day_ord('2017-01-02') == 1
    assert c['set_blocks']['X4'] == ['F', 'S', 'E'] and c['set_blocks']['X5'] == ['F', 'S', 'E', 'T']
    assert len(c['comparisons']) == 4 and c['tron_comparison'] == ['X5', 'X4']
    assert c['tracks']['A']['test_years'] == [2019, 2020, 2021, 2022, 2023, 2024]
    assert c['tracks']['B']['groups'] == {'2022-24': [2022, 2023, 2024], '2025-26': [2025, 2026]}
    assert c['targets'] == {'V6': 6, 'V24': 24}


def test_registration_files_exist():
    for name in ('CHARTER.md', 'PLAN.md', 'STATE.md'):
        assert (config.STUDY / name).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_config.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.research.onchain_b6'`

- [ ] **Step 3: Write config module and registration files**

```python
# tradingagents/research/onchain_b6/config.py
"""Frozen B6 configuration (research/onchain-b6-2026-10-19/config/b6.json)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b6-2026-10-19'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b6'
B2_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b2'
B4_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b4'
B5_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b5'
EPOCH = date(2017, 1, 1)


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b6.json').read_text())


def days(cfg=None) -> list:
    w = (cfg or load())['window']
    return [d.date().isoformat() for d in pd.date_range(w['first_day'], w['last_day'], freq='D')]


def day_ord(day) -> int:
    return (date.fromisoformat(day) - EPOCH).days
```

`research/onchain-b6-2026-10-19/config/b6.json`:

```json
{
 "window": {"first_day": "2017-01-01", "last_day": "2026-10-11"},
 "pass": {"snapshot_every": 30, "prefetch": 2, "max_consecutive_unavailable": 3},
 "s3": {"bucket": "aws-public-blockchain", "region": "us-east-2", "retries": [30, 120]},
 "tokens": {
  "0xdac17f958d2ee523a2206206994597c13d831ec7": {"name": "USDT", "decimals": 6, "code": 1},
  "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"name": "USDC", "decimals": 6, "code": 2},
  "0x6b175474e89094c44da98b954eedeac495271d0f": {"name": "DAI", "decimals": 18, "code": 3}},
 "issuer": {"usdt_treasury": "0x5754284f345afc66a98fbb0a0afe71e0f007b949"},
 "labels": {
  "ethlabels": {"repo": "dawsbot/eth-labels", "branch": "v1", "path": "data/csv/accounts.csv"},
  "spellbook": {"repo": "duneanalytics/spellbook", "branch": "main",
   "bridges": "dbt_subprojects/daily_spellbook/models/_sector/labels/addresses/bridge/identifiers/labels_bridges_ethereum.sql",
   "funds": "dbt_subprojects/daily_spellbook/models/_sector/labels/addresses/institution/identifier/funds/labels_funds_ethereum.sql",
   "tron": "dbt_subprojects/hourly_spellbook/models/_sector/cex/addresses/chains/tron/cex_tron_addresses.sql"},
  "exchange_labels": ["binance", "coinbase", "kraken", "okx", "bitget", "deribit", "bilaxy", "bybit", "kucoin", "htx", "huobi", "gate-io", "mexc", "bitfinex", "bitstamp", "gemini", "bithumb", "upbit", "crypto-com", "ftx", "celsius-network", "nexo", "coindcx", "bitmart", "bittrex", "poloniex", "hitbtc", "bitvavo", "coinex", "ascendex", "bingx", "phemex", "lbank", "bitrue", "bitflyer", "coincheck", "bitbank", "luno", "paxos", "bitpanda", "bitpay", "blockfi", "cex-io", "btcturk", "wazirx", "bitkub", "changenow", "shapeshift", "cobo", "bitgo", "anchorage-digital", "bullish", "robinhood", "bitso", "bitbuy", "okcoin", "bitmex"],
  "mev_labels": ["mev-bot", "mev-builder"],
  "fund_keywords": ["wintermute", "jump trading", "cumberland", "galaxy digital", "amber group", "b2c2", "dwf labs", "gsr", "flow traders", "genesis trading", "falconx"]},
 "structure": {"bloom_bits_log2": 33, "bloom_hashes": 5, "top_n": 10},
 "large": {"stable_usd": 1000000.0, "eth": 500.0},
 "transforms": {"h1_window": 168, "h1_min": 120, "d24_window": 720, "d24_min": 480, "clip": 10.0},
 "iv": {"min_trades": 3, "ffill_hours": 3},
 "targets": {"V6": 6, "V24": 24},
 "blocks": {"F": ["eth_", "stable_"], "S": ["gs_"], "E": ["tk_", "cl_", "is_"], "T": ["tron_"]},
 "set_blocks": {"X0": [], "X1": ["F"], "X2": ["F", "S"], "X3": ["F", "E"], "X4": ["F", "S", "E"], "X5": ["F", "S", "E", "T"]},
 "comparisons": [["X1", "X0"], ["X2", "X1"], ["X3", "X1"], ["X4", "X1"]],
 "tron_comparison": ["X5", "X4"],
 "tracks": {
  "A": {"start": "2017-10-02", "end": "2024-12-31", "test_years": [2019, 2020, 2021, 2022, 2023, 2024],
        "groups": {"2019-24": [2019, 2020, 2021, 2022, 2023, 2024]}, "base": ["h0_", "px_"], "criterion": "years"},
  "B": {"start": "2021-04-01", "end": "2026-10-12", "test_years": [2022, 2023, 2024, 2025, 2026],
        "groups": {"2022-24": [2022, 2023, 2024], "2025-26": [2025, 2026]}, "base": ["h0_", "px_", "mk_"], "criterion": "groups"}},
 "families": ["linear", "trees"],
 "folds": {"inner_len": 8760, "min_train": 2000, "min_year_wins": 4},
 "models": {"alphas": [0.1, 1, 10, 100, 1000, 10000, 100000], "fallback_alpha": 100.0,
            "trees": {"max_iter": 100, "learning_rate": 0.05, "max_leaf_nodes": 7, "min_samples_leaf": 30,
                      "l2_regularization": 1.0, "random_state": 11}},
 "gate": {"draws": 2000, "seed": 20261020, "block": 168, "chunk": 100},
 "minutes": {"symbols": {"ETH": "ETHUSDT", "BTC": "BTCUSDT"}, "start": "2019-01-01", "end": "2026-10-13",
             "tiers": {"stable_usd": [10000000.0, 50000000.0], "eth": [5000.0, 20000.0]},
             "spacing_min": 30, "k_vol": [5, 15, 30, 60], "k_ret": [1, 5, 15, 30, 60], "pre_ret_min": 15,
             "pre_vol_min": 60, "placebo_gap_min": 60, "seed": 20261020, "block": 10,
             "groups": {"2019-24": [2019, 2020, 2021, 2022, 2023, 2024], "2025-26": [2025, 2026]}},
 "tron": {"url": "https://portal.sqd.dev/datasets/tron-mainnet/stream",
          "usdt": "a614f803b6fd780986a42c78ec9c7f77e6ded13c",
          "topic0": "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
          "start_block": 20000000, "end": "2026-10-13", "chunk_blocks": 28800,
          "backoff": [30, 120, 600], "big_usd": 1000000.0}
}
```

`research/onchain-b6-2026-10-19/CHARTER.md`:

```markdown
# B6 charter — hourly graph structure, entity detail and minute-level events

Registered 2026-10-19 before any B6 pass output is read. Spec:
`docs/superpowers/specs/2026-10-19-onchain-b6-structure-entities-design.md`.

## Questions

Q1 Does hourly transfer-graph structure add volatility information beyond price history,
option-market information and B4's flow intensity? Q2 Do token-split flows, DEX / bridge /
MEV / fund flows and stablecoin issuance add beyond B4's flows? Q3 Do very large exchange
deposits or withdrawals move volatility or price within 5–60 minutes of their block, and
does the market move first? Q4 (side) Does Tron USDT exchange flow add beyond Ethereum flows?

## Framing

Exploratory with a pre-declared plan (`PLAN.md`); the ETH and BTC 2025–26 windows were
opened in B4 and B5. Targets are realised volatility only.

## Disclosures

- Exchange and class labels are a 2026 snapshot; each address counts as labelled only from
  the day after its first observed transfer, which removes the "label before existence"
  look-ahead but not the identity look-ahead.
- Exchange entities are labels only (no deposit inference); eth-labels' exchange set is
  dominated by three exchanges' deposit addresses (Bitget, Deribit, Bilaxy).
- USDT issuance is proxied by Tether Treasury transfers; USDC and DAI by mint/burn events.
- Binance 1-minute closes stand in for the market; the block timestamp has 12-second
  resolution; responses start at the next full minute.
```

`research/onchain-b6-2026-10-19/PLAN.md`:

```markdown
# B6 pre-declared analysis plan (committed before any pass output is read)

All items run once and are reported in `RESULTS.md`, including negatives.

## Q1, Q2, Q4 — forecast comparisons
Tracks A (2017-10 → 2024-12; test years 2019–2024) and B (2021-04 → 2026-10-12; test
years 2022–2026, groups 2022–24 and 2025–26). Targets V6, V24. Families linear, trees.
Sets X0 = base, X1 = X0 + F, X2 = X1 + S, X3 = X1 + E, X4 = X1 + S + E; with Tron
X5 = X4 + T. Comparisons X1 vs X0, X2 vs X1, X3 vs X1, X4 vs X1 (X5 vs X4 if Tron ran):
mean squared-error difference, 95 % circular block-bootstrap interval (block 168),
per-year differences. Positive reading: track A — upper end < 0 and better in ≥ 4 of 6
years; track B — upper end < 0 in 2022–24 and mean difference < 0 in 2025–26.

## Q3 — minute-level events
ETH primary, BTC cross-check. Events: deposits and withdrawals of ≥ $10M stablecoin or
≥ 5,000 ETH (tier 1) and ≥ $50M or ≥ 20,000 ETH (tier 2), first per 30 minutes per
direction and tier. Responses from m + 1: log realised volatility over the next 5, 15,
30, 60 minutes minus the previous 60 minutes; signed log return over the next 1, 5, 15,
30, 60 minutes; signed return over the 15 minutes before m. Placebo minutes matched by
year and hour of day, ≥ 60 minutes from any event. Means with block-bootstrap intervals
(block 10 events), groups 2019–24 and 2025–26.

## Reporting
`TABLES.md` (generated) holds every row; `RESULTS.md` reads them. Post hoc additions
are labelled.
```

`research/onchain-b6-2026-10-19/STATE.md`:

```markdown
# Branch B6 state

2026-10-19 — Registered (charter, config, pre-declared plan). No B6 pass output read yet.

Next safe action: implement plan tasks 2–9; freeze labels and fetch 1-minute bars
(B6-CP1); run the pass and the Tron stream (B6-CP2); forecasts (B6-CP3); events and
`RESULTS.md` (B6-CP4).
```

Add to `.gitignore` after the B5 line:

```
# B6 hourly structure/entity tables, large transfers, minute bars, state
/research_artifacts/onchain-b6/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_config.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add .gitignore tradingagents/research/onchain_b6 tests/research/onchain_b6 research/onchain-b6-2026-10-19
git commit -m "feat(onchain-b6): register structure/entity study, config and pre-declared plan

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Labels — fetch, classify, freeze; activation state

**Files:**
- Create: `tradingagents/research/onchain_b6/labels6.py`
- Test: `tests/research/onchain_b6/test_labels6.py`

**Interfaces:**
- Consumes: `onchain_b2.labels.load(path)`, `onchain_b2.labels._commit(get, repo, branch)`; `onchain_b4.reader.addr_keys`; `onchain_b4.entities.member`.
- Produces: `labels6.classify(b2, eth_rows, spell_bridges, spell_funds, cfg) -> dict` with keys `exchange` ({addr: name}), `dex`, `bridge`, `mev`, `funds` (sorted lists), `issuer`; `labels6.build(get, b2_path, cfg) -> dict` (adds `sources`); `labels6.save(doc, path)`, `labels6.load(path)`; `labels6.parse_sql_addresses(text) -> list[(addr, name)]`; class `labels6.LabelState(doc, usdt_treasury)` with `.classes` (`['dex','bridge','mev','funds']`), `.begin_day(day_ord)`, `.is_exchange(keys)`, `.entity_of(keys)` (int32, −1 if none), `.in_class(name, keys)`, `.observe(keys, day_ord)`, `.save(path)`, `LabelState.load(path, doc, usdt_treasury)`, `.treasury_key`, `.entity_names`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b6/test_labels6.py
import numpy as np

from tradingagents.research.onchain_b4.reader import addr_keys
from tradingagents.research.onchain_b6 import config, labels6

A, B, C, D, E, F, G = ('0x' + c * 40 for c in 'abcdef1')
CFG = config.load()


def _rows():
    return [{'address': A, 'chainId': '1', 'label': 'binance', 'nameTag': 'Binance 14'},
            {'address': B, 'chainId': '1', 'label': 'dex', 'nameTag': 'Uniswap V3: Router 2'},
            {'address': C, 'chainId': '1', 'label': 'mev-bot', 'nameTag': 'MEV Bot: 0x…'},
            {'address': D, 'chainId': '1', 'label': 'take-action', 'nameTag': 'Wintermute Trading 3'},
            {'address': E, 'chainId': '1', 'label': 'bridge', 'nameTag': 'Arbitrum: L1 Gateway'},
            {'address': B, 'chainId': '1', 'label': 'coinbase', 'nameTag': 'Coinbase 9'},      # exchange wins
            {'address': F, 'chainId': '56', 'label': 'dex', 'nameTag': 'PancakeSwap Router'}]  # other chain


def test_classify_precedence_and_sources():
    b2 = {G: {'name': 'Kraken 4', 'added': None, 'sources': ['spellbook']}}
    doc = labels6.classify(b2, _rows(), [(E, 'Arbitrum: Bridge'), (F, 'Other: Bridge')], [(D, 'Wintermute Trading')], CFG)
    assert doc['exchange'] == {G: 'Kraken 4', A: 'binance', B: 'coinbase'}
    assert doc['dex'] == [] and doc['mev'] == [C] and doc['funds'] == [D]
    assert doc['bridge'] == [E, F]                                 # spellbook bridge on another chain still an address
    assert doc['issuer']['usdt_treasury'] == CFG['issuer']['usdt_treasury']


def test_parse_sql_addresses():
    t = "values\n  (0xAbC0000000000000000000000000000000000001, 'Across Protocol: Bridge', 'bridge')\n"
    assert labels6.parse_sql_addresses(t) == [('0xabc0000000000000000000000000000000000001', 'Across Protocol: Bridge')]


def test_activation_is_day_after_first_observation(tmp_path):
    doc = labels6.classify({}, _rows(), [], [], CFG)
    st = labels6.LabelState(doc, CFG['issuer']['usdt_treasury'])
    ka, kb, kc = addr_keys(np.array([A, B, C], object))
    st.begin_day(10)
    assert st.is_exchange(np.array([ka, kb, kc], np.uint64)).tolist() == [False, False, False]
    st.observe(np.array([ka, kc], np.uint64), 10)
    st.begin_day(10)
    assert st.is_exchange(np.array([ka], np.uint64)).tolist() == [False]          # same day: not yet
    st.begin_day(11)
    assert st.is_exchange(np.array([ka, kb], np.uint64)).tolist() == [True, False]
    assert st.in_class('mev', np.array([kc, ka], np.uint64)).tolist() == [True, False]
    assert st.entity_of(np.array([ka, kc], np.uint64)).tolist() == [st.entity_names.index('binance'), -1]
    st.save(tmp_path / 'labels_state.npz')
    st2 = labels6.LabelState.load(tmp_path / 'labels_state.npz', doc, CFG['issuer']['usdt_treasury'])
    st2.begin_day(11)
    assert st2.is_exchange(np.array([ka], np.uint64)).tolist() == [True]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_labels6.py -q`
Expected: FAIL with `ImportError: cannot import name 'labels6'`

- [ ] **Step 3: Implement labels6.py**

```python
# tradingagents/research/onchain_b6/labels6.py
"""Label sets (spec §3): exchanges from B2 and eth-labels, classes from eth-labels and
Spellbook; frozen with source commits. LabelState applies day-after activation."""
from __future__ import annotations

import csv
import io
import json
import os
import re
from pathlib import Path

import numpy as np

from ..onchain_b2.labels import _commit
from ..onchain_b2.labels import load as load_b2
from ..onchain_b4.entities import member
from ..onchain_b4.reader import addr_keys

CLASSES = ['dex', 'bridge', 'mev', 'funds']
ADDR = re.compile(r'^0x[0-9a-f]{40}$')


def _stem(name):
    return (name or '').split(':')[0].split(' ')[0].strip().lower()


def parse_sql_addresses(text):
    return [(a.lower(), n) for a, n in re.findall(r"(0x[0-9a-fA-F]{40})\s*,\s*'([^']+)'", text)]


def classify(b2, eth_rows, spell_bridges, spell_funds, cfg):
    L = cfg['labels']
    stems = ({_stem(v.get('name')) for v in b2.values()} - {''}) | set(L['exchange_labels'])
    exchange = {a.lower(): v.get('name') or '' for a, v in b2.items()}
    cls = {c: set() for c in CLASSES}
    for r in eth_rows:
        if r.get('chainId', '1') != '1':
            continue
        a, lab, tag = r['address'].lower(), r.get('label', ''), (r.get('nameTag') or '')
        if not ADDR.match(a):
            continue
        tl = tag.lower()
        if lab in stems or lab.replace('-', ' ') in stems or lab.replace('-', '.') in stems:
            exchange.setdefault(a, lab)
        elif lab == 'dex' or 'router' in tl:
            cls['dex'].add(a)
        elif lab == 'bridge' or 'bridge' in tl:
            cls['bridge'].add(a)
        elif lab in L['mev_labels']:
            cls['mev'].add(a)
        elif any(k in tl for k in L['fund_keywords']):
            cls['funds'].add(a)
    cls['bridge'] |= {a for a, _ in spell_bridges}
    cls['funds'] |= {a for a, _ in spell_funds}
    for c in CLASSES:
        cls[c] -= set(exchange)
    return {'exchange': dict(sorted(exchange.items())), **{c: sorted(cls[c]) for c in CLASSES},
            'issuer': {'usdt_treasury': cfg['issuer']['usdt_treasury']}}


def build(get, b2_path, cfg):
    L = cfg['labels']
    e, s = L['ethlabels'], L['spellbook']
    raw = get(f"https://raw.githubusercontent.com/{e['repo']}/{e['branch']}/{e['path']}").decode(errors='replace')
    rows = list(csv.DictReader(io.StringIO(raw)))
    sb = lambda p: get(f"https://raw.githubusercontent.com/{s['repo']}/{s['branch']}/{p}").decode()
    doc = classify(load_b2(b2_path), rows, parse_sql_addresses(sb(s['bridges'])), parse_sql_addresses(sb(s['funds'])), cfg)
    doc['sources'] = {'b2_labels': str(b2_path), 'ethlabels_commit': _commit(get, e['repo'], e['branch']),
                      'spellbook_commit': _commit(get, s['repo'], s['branch']),
                      'counts': {'exchange': len(doc['exchange']), **{c: len(doc[c]) for c in CLASSES}}}
    return doc


def save(doc, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=0, sort_keys=True))


def load(path):
    return json.loads(Path(path).read_text())


class LabelState:
    def __init__(self, doc, usdt_treasury):
        ex = doc['exchange']
        self.entity_names = sorted({v for v in ex.values()})
        addrs = np.array(sorted(ex), object)
        k = addr_keys(addrs) if len(addrs) else np.empty(0, np.uint64)
        order = np.argsort(k)
        self.ex_keys = k[order]
        self.ex_entity = np.array([self.entity_names.index(ex[a]) for a in addrs[order]], np.int32) if len(addrs) else np.empty(0, np.int32)
        self.ex_first = np.full(len(self.ex_keys), -1, np.int32)
        self.cls_keys, self.cls_first = {}, {}
        for c in CLASSES:
            kk = np.unique(addr_keys(np.array(doc[c], object))) if doc[c] else np.empty(0, np.uint64)
            self.cls_keys[c], self.cls_first[c] = kk, np.full(len(kk), -1, np.int32)
        self.treasury_key = int(addr_keys(np.array([usdt_treasury], object))[0])
        self.classes = CLASSES
        self._day = None

    def begin_day(self, day_ord):
        self._day = int(day_ord)
        self._ex_active = (self.ex_first >= 0) & (self.ex_first < self._day)
        self._cls_active = {c: (self.cls_first[c] >= 0) & (self.cls_first[c] < self._day) for c in CLASSES}

    def _lookup(self, sorted_keys, keys):
        keys = np.asarray(keys, np.uint64)
        if len(sorted_keys) == 0 or len(keys) == 0:
            return np.zeros(len(keys), bool), np.zeros(len(keys), np.int64)
        pos = np.searchsorted(sorted_keys, keys)
        pos[pos == len(sorted_keys)] = 0
        return sorted_keys[pos] == keys, pos

    def is_exchange(self, keys):
        hit, pos = self._lookup(self.ex_keys, keys)
        return hit & self._ex_active[pos]

    def entity_of(self, keys):
        hit, pos = self._lookup(self.ex_keys, keys)
        out = np.full(len(hit), -1, np.int32)
        m = hit & self._ex_active[pos]
        out[m] = self.ex_entity[pos[m]]
        return out

    def in_class(self, name, keys):
        hit, pos = self._lookup(self.cls_keys[name], keys)
        return hit & self._cls_active[name][pos]

    def observe(self, keys, day_ord):
        keys = np.unique(np.asarray(keys, np.uint64))
        for sorted_keys, first in [(self.ex_keys, self.ex_first)] + [(self.cls_keys[c], self.cls_first[c]) for c in CLASSES]:
            if len(sorted_keys) == 0 or len(keys) == 0:
                continue
            hit = member(sorted_keys, keys)
            pos = np.searchsorted(sorted_keys, keys[hit])
            fresh = first[pos] < 0
            first[pos[fresh]] = int(day_ord)

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.stem + '.tmp.npz')
        np.savez(tmp, ex_first=self.ex_first, **{f'cls_first_{c}': self.cls_first[c] for c in CLASSES})
        os.replace(tmp, path)

    @classmethod
    def load(cls, path, doc, usdt_treasury):
        st = cls(doc, usdt_treasury)
        z = np.load(path)
        st.ex_first = z['ex_first'].copy()
        for c in CLASSES:
            st.cls_first[c] = z[f'cls_first_{c}'].copy()
        return st
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_labels6.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b6/labels6.py tests/research/onchain_b6/test_labels6.py
git commit -m "feat(onchain-b6): frozen label sets with classes and day-after activation

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Reader with mint/burn and token codes

**Files:**
- Create: `tradingagents/research/onchain_b6/reader6.py`
- Test: `tests/research/onchain_b6/test_reader6.py`

**Interfaces:**
- Consumes: `onchain_b4.reader` helpers `_arr, _strs, _floats, _ints, _secs, _unpad, _check42, addr_keys, ZERO`; `onchain_b2.s3source.DayUnavailable, check_timestamps`.
- Produces: `reader6.Day6` dataclass (`src, dst, token` int8 0 ETH/1 USDT/2 USDC/3 DAI, `amount, ts, mint, burn` bool, `rows` dict); `reader6.admit6(tx, tt, tokens) -> Day6`; `reader6.read_day6(day, *, filesystem, root, tokens, retries, sleep)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b6/test_reader6.py
import numpy as np
import pyarrow as pa
import pyarrow.fs as pafs
import pyarrow.parquet as pq

from tradingagents.research.onchain_b4.reader import addr_keys
from tradingagents.research.onchain_b6 import config, reader6

A, B, C = ('0x' + c * 40 for c in 'abc')
ZERO = '0x' + '0' * 40
USDT, USDC, DAI = (k for k in config.load()['tokens'])
pad = lambda a: '0x' + '0' * 24 + a[2:]
TS = lambda h: np.datetime64('2025-06-02T00:00:00', 'ns') + np.timedelta64(h, 'h')


def _write(root, table, day, t):
    d = root / 'v1.0' / 'eth' / table / f'date={day}'
    d.mkdir(parents=True)
    pq.write_table(t, d / 'part-0.parquet')


def test_admit6_tokens_mint_burn_and_exclusions(tmp_path):
    _write(tmp_path, 'transactions', '2025-06-02', pa.table({
        'from_address': [A, B, C], 'to_address': [B, 'None', C], 'value': [2e18, 1e18, 1e18], 'receipt_status': [1, 1, 1],
        'block_number': [1, 2, 3], 'block_timestamp': pa.array([TS(1), TS(2), TS(2)], pa.timestamp('ns'))}))
    _write(tmp_path, 'token_transfers', '2025-06-02', pa.table({
        'token_address': [USDT, pad(USDC), DAI, USDC, USDT],
        'from_address': [pad(A), pad(ZERO), pad(B), pad(C), pad(A)],
        'to_address': [pad(B), pad(A), pad(ZERO), pad(C), pad(B)],
        'value': [5e6, 9e6, 3e18, 1e6, 0.0], 'block_number': [1, 2, 3, 4, 5],
        'block_timestamp': pa.array([TS(1), TS(2), TS(3), TS(4), TS(5)], pa.timestamp('ns'))}))
    d = reader6.read_day6('2025-06-02', filesystem=pafs.LocalFileSystem(), root=str(tmp_path),
                          tokens=config.load()['tokens'], retries=[])
    k = {x: addr_keys(np.array([x], object))[0] for x in (A, B, C)}
    rows = sorted(zip(d.src.tolist(), d.dst.tolist(), d.token.tolist(), np.round(d.amount, 6).tolist(), d.mint.tolist(), d.burn.tolist()))
    assert rows == sorted([(k[A], k[B], 0, 2.0, False, False), (k[A], k[B], 1, 5.0, False, False),
                           (0, k[A], 2, 9.0, True, False), (k[B], 0, 3, 3.0, False, True)])
    assert d.rows == {'eth_transfers': 1, 'stable_transfers': 1, 'mint': 1, 'burn': 1}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_reader6.py -q`
Expected: FAIL with `ImportError: cannot import name 'reader6'`

- [ ] **Step 3: Implement reader6.py**

```python
# tradingagents/research/onchain_b6/reader6.py
"""One UTC day for B6 (spec §4): ETH and stablecoin transfers with a token code, plus
stablecoin mint/burn rows (from/to the zero address) kept for issuance."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.fs as pafs
import pyarrow.parquet as pq

from ..onchain_b2.s3source import DayUnavailable, check_timestamps
from ..onchain_b4.reader import ZERO, _arr, _check42, _floats, _ints, _secs, _strs, _unpad, addr_keys

TABLES6 = {
    'transactions': ['from_address', 'to_address', 'value', 'receipt_status', 'block_number', 'block_timestamp'],
    'token_transfers': ['token_address', 'from_address', 'to_address', 'value', 'block_number', 'block_timestamp'],
}


@dataclass
class Day6:
    src: np.ndarray
    dst: np.ndarray
    token: np.ndarray
    amount: np.ndarray
    ts: np.ndarray
    mint: np.ndarray
    burn: np.ndarray
    rows: dict = field(default_factory=dict)


def admit6(tx, tt, tokens):
    tx = tx.filter(pc.equal(_arr(tx['receipt_status']), 1))
    frm_e, to_e = _arr(tx['from_address']), _arr(tx['to_address'])
    has_to = pc.and_(pc.is_valid(to_e), pc.invert(pc.is_in(to_e, value_set=pa.array(['None', '']))))
    e = tx.filter(pc.and_(pc.and_(pc.greater(_arr(tx['value']), 0.0), has_to), pc.not_equal(frm_e, to_e)))
    _check42(_arr(e['from_address']), 'transactions.from_address')
    _check42(_arr(e['to_address']), 'transactions.to_address')
    tok_all = _unpad(tt['token_address'])
    m = pc.is_in(tok_all, value_set=pa.array(sorted(tokens)))
    tt, tok_all = tt.filter(m), pc.filter(tok_all, m)
    frm, to = _unpad(tt['from_address']), _unpad(tt['to_address'])
    keep = pc.and_(pc.greater(_arr(tt['value']), 0.0), pc.not_equal(frm, to))
    tt, frm, to, tok_all = tt.filter(keep), pc.filter(frm, keep), pc.filter(to, keep), pc.filter(tok_all, keep)
    _check42(frm, 'token_transfers.from_address')
    _check42(to, 'token_transfers.to_address')
    frm_s, to_s, tok = _strs(frm), _strs(to), tok_all.to_numpy(zero_copy_only=False)
    raw = _floats(tt['value'])
    amt, code = np.zeros(len(raw)), np.zeros(len(raw), np.int8)
    for addr, meta in tokens.items():
        mm = tok == addr
        amt[mm] = raw[mm] / 10.0 ** meta['decimals']
        code[mm] = meta['code']
    mint, burn = frm_s == ZERO, to_s == ZERO
    n_e = e.num_rows
    src_t, dst_t = addr_keys(frm_s), addr_keys(to_s)
    src_t[mint], dst_t[burn] = 0, 0
    return Day6(src=np.concatenate([addr_keys(_strs(e['from_address'])), src_t]),
                dst=np.concatenate([addr_keys(_strs(e['to_address'])), dst_t]),
                token=np.concatenate([np.zeros(n_e, np.int8), code]),
                amount=np.concatenate([_floats(e['value']) / 1e18, amt]),
                ts=np.concatenate([_secs(e['block_timestamp']), _secs(tt['block_timestamp'])]).astype(np.int64),
                mint=np.concatenate([np.zeros(n_e, bool), mint]), burn=np.concatenate([np.zeros(n_e, bool), burn]),
                rows={'eth_transfers': int(n_e), 'stable_transfers': int((~mint & ~burn).sum()),
                      'mint': int(mint.sum()), 'burn': int(burn.sum())})


def _read_table(filesystem, root, table, day):
    sel = pafs.FileSelector(f'{root}/v1.0/eth/{table}/date={day}')
    infos = sorted((f for f in filesystem.get_file_info(sel) if f.path.endswith('.parquet')), key=lambda f: f.path)
    if not infos:
        raise FileNotFoundError(f'no {table} parts for {day}')
    parts = []
    for info in infos:
        with filesystem.open_input_file(info.path) as fh:
            parts.append(pq.ParquetFile(fh).read(columns=TABLES6[table]))
    return pa.concat_tables(parts)


def read_day6(day, *, filesystem, root, tokens, retries, sleep=time.sleep):
    errors = []
    for attempt in range(len(retries) + 1):
        try:
            tx = _read_table(filesystem, root, 'transactions', day)
            tt = _read_table(filesystem, root, 'token_transfers', day)
            check_timestamps(tx, day)
            check_timestamps(tt, day)
            return admit6(tx, tt, tokens)
        except Exception as e:        # network, decode or integrity failure: retry, then mark unavailable
            errors.append(repr(e))
            if attempt < len(retries):
                sleep(retries[attempt])
    raise DayUnavailable(day, errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_reader6.py -q`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b6/reader6.py tests/research/onchain_b6/test_reader6.py
git commit -m "feat(onchain-b6): day reader with token codes and mint/burn rows

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Hourly structure features

**Files:**
- Create: `tradingagents/research/onchain_b6/structure6.py`
- Test: `tests/research/onchain_b6/test_structure6.py`

**Interfaces:**
- Consumes: `onchain_b3.structure.gini, undirected_edges, kcore_alive`; `scipy.sparse.csgraph.connected_components`.
- Produces: `structure6.NAMES` (11 names, prefix `gs_`); `structure6.hour_structure(src, dst, usd, is_ex_src, is_ex_dst, ent_src, ent_dst, bloom_contains, top_n) -> dict`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b6/test_structure6.py
import numpy as np

from tradingagents.research.onchain_b6 import structure6 as S

u = lambda *x: np.array(x, np.uint64)


def test_structure_on_hand_built_hour():
    # exchanges 100 (entity 0), 101 (entity 1); users 1..6; triangle 1-2-3 (2-core), 4 pendant on 1, 5-6 isolated pair
    src = u(1, 2, 3, 4, 5, 1, 2, 100, 100)
    dst = u(2, 3, 1, 1, 6, 100, 101, 1, 101)
    usd = np.array([10.0, 20.0, 0.0, 5.0, 1.0, 40.0, 0.0, 4.0, 20.0])
    ex = lambda k: np.isin(k, [100, 101])
    ent = lambda k: np.where(k == 100, 0, np.where(k == 101, 1, -1))
    seen = lambda k: np.isin(k, [1, 2, 3, 100, 101])          # 4, 5, 6 are new
    r = S.hour_structure(src, dst, usd, ex(src), ex(dst), ent(src), ent(dst), seen, 10)
    assert r['gs_active'] == 8 and r['gs_edges'] == 9 and np.isclose(r['gs_edges_per_node'], 9 / 8)
    assert np.isclose(r['gs_new_share'], 3 / 8)
    out = {1: 50.0, 2: 20.0, 4: 5.0, 5: 1.0, 100: 24.0}                 # outgoing USD per address
    assert np.isclose(r['gs_top10_share'], 1.0) and r['gs_value_gini'] > 0.3
    assert np.isclose(r['gs_core2_share'], 3 / 8) and np.isclose(r['gs_giant_share'], 6 / 8)
    assert r['gs_ex_cp'] == 2 and np.isclose(r['gs_ex_cp_new_share'], 0.0)   # users 1 and 2 touch exchanges
    assert np.isclose(r['gs_cex_cex_usd'], 20.0)


def test_structure_degenerate_hours():
    empty = S.hour_structure(u(), u(), np.array([]), np.array([], bool), np.array([], bool),
                             np.array([], np.int32), np.array([], np.int32), lambda k: np.zeros(len(k), bool), 10)
    assert all(np.isfinite(v) for v in empty.values()) and empty['gs_active'] == 0
    one = S.hour_structure(u(1), u(2), np.array([3.0]), np.array([False]), np.array([False]),
                           np.array([-1]), np.array([-1]), lambda k: np.zeros(len(k), bool), 10)
    assert one['gs_active'] == 2 and one['gs_core2_share'] == 0.0 and one['gs_giant_share'] == 1.0
    assert set(empty) == set(S.NAMES)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_structure6.py -q`
Expected: FAIL with `ImportError: cannot import name 'structure6'`

- [ ] **Step 3: Implement structure6.py**

```python
# tradingagents/research/onchain_b6/structure6.py
"""Hourly graph structure (spec §4.1) on the hour's non-self transfers."""
from __future__ import annotations

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from ..onchain_b3.structure import gini, kcore_alive, undirected_edges

NAMES = ['gs_active', 'gs_new_share', 'gs_edges', 'gs_edges_per_node', 'gs_value_gini', 'gs_top10_share',
         'gs_core2_share', 'gs_giant_share', 'gs_ex_cp', 'gs_ex_cp_new_share', 'gs_cex_cex_usd']


def hour_structure(src, dst, usd, is_ex_src, is_ex_dst, ent_src, ent_dst, bloom_contains, top_n):
    src, dst, usd = np.asarray(src, np.uint64), np.asarray(dst, np.uint64), np.asarray(usd, float)
    m = src != dst
    src, dst, usd = src[m], dst[m], usd[m]
    is_ex_src, is_ex_dst, ent_src, ent_dst = (np.asarray(x)[m] for x in (is_ex_src, is_ex_dst, ent_src, ent_dst))
    if len(src) == 0:
        return {k: 0.0 for k in NAMES}
    keys, inv = np.unique(np.concatenate([src, dst]), return_inverse=True)
    n = len(keys)
    a, b = inv[:len(src)], inv[len(src):]
    edges = len(np.unique(a.astype(np.int64) * n + b))
    known = bloom_contains(keys)
    out_usd = np.bincount(a, weights=usd, minlength=n)
    pos = np.sort(out_usd[out_usd > 0])[::-1]
    ua, ub = undirected_edges(a, b, n)
    core2 = float(kcore_alive(ua, ub, n, 2).mean()) if len(ua) else 0.0
    _, lab = connected_components(coo_matrix((np.ones(len(ua)), (ua, ub)), shape=(n, n)), directed=False)
    giant = float(np.bincount(lab).max() / n)
    one_ex = is_ex_src ^ is_ex_dst
    cp = np.unique(np.concatenate([a[one_ex & ~is_ex_src], b[one_ex & ~is_ex_dst]]))
    cross = is_ex_src & is_ex_dst & (ent_src != ent_dst)
    return {'gs_active': float(n), 'gs_new_share': float((~known).mean()), 'gs_edges': float(edges),
            'gs_edges_per_node': float(edges / n), 'gs_value_gini': gini(pos),
            'gs_top10_share': float(pos[:top_n].sum() / pos.sum()) if len(pos) else 0.0,
            'gs_core2_share': core2, 'gs_giant_share': giant, 'gs_ex_cp': float(len(cp)),
            'gs_ex_cp_new_share': float((~known[cp]).mean()) if len(cp) else 0.0,
            'gs_cex_cex_usd': float(usd[cross].sum())}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_structure6.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b6/structure6.py tests/research/onchain_b6/test_structure6.py
git commit -m "feat(onchain-b6): hourly graph-structure features

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: One day → hourly rows and large transfers

**Files:**
- Create: `tradingagents/research/onchain_b6/hourly6.py`
- Test: `tests/research/onchain_b6/test_hourly6.py`

**Interfaces:**
- Consumes: `reader6.Day6`; `labels6.LabelState`; `onchain_b3.history.Bloom`; `structure6.hour_structure`.
- Produces: `hourly6.COLUMNS` (39 = 11 gs + 6 tk + 16 cl + 6 is); `hourly6.day_rows(day, d, state, bloom, cfg) -> (DataFrame 24 rows, DataFrame large)`; large columns `ts, token, amount, direction (1 deposit / -1 withdrawal), entity, cp_new`. Side effects: `bloom.add` per hour; `state.observe` at the end of the day.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b6/test_hourly6.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b3.history import Bloom
from tradingagents.research.onchain_b4.reader import addr_keys
from tradingagents.research.onchain_b6 import config, hourly6, labels6
from tradingagents.research.onchain_b6.reader6 import Day6

CFG = config.load()
A, B, C, X, Y, R, M, T = ('0x' + c * 40 for c in 'abcxyr12')
TREAS = CFG['issuer']['usdt_treasury']
K = {n: int(addr_keys(np.array([a], object))[0]) for n, a in {'A': A, 'B': B, 'C': C, 'X': X, 'Y': Y, 'R': R, 'M': M, 'T': TREAS}.items()}
T0 = int(pd.Timestamp('2023-06-01', tz='UTC').timestamp())


def _state(day_ord=100):
    doc = {'exchange': {X: 'okx', Y: 'kraken'}, 'dex': [R], 'bridge': [], 'mev': [M], 'funds': [], 'issuer': {'usdt_treasury': TREAS}}
    st = labels6.LabelState(doc, TREAS)
    st.observe(np.array([K['X'], K['Y'], K['R'], K['M']], np.uint64), day_ord - 1)
    st.begin_day(day_ord)
    return st


def _day(rows):
    a = np.array(rows, dtype=object)
    return Day6(src=np.array(a[:, 0], np.uint64), dst=np.array(a[:, 1], np.uint64), token=np.array(a[:, 2], np.int8),
                amount=np.array(a[:, 3], float), ts=np.array([T0 + 3600 * int(h) + 7 for h in a[:, 4]], np.int64),
                mint=np.array(a[:, 5], bool), burn=np.array(a[:, 6], bool))


def test_day_rows_flows_issuance_large_and_bloom():
    rows = [(K['A'], K['X'], 1, 2e6, 0, 0, 0),       # USDT deposit 2M -> large, tk_usdt_in
            (K['X'], K['B'], 2, 5e5, 0, 0, 0),        # USDC withdrawal
            (K['A'], K['R'], 0, 3.0, 0, 0, 0),        # ETH into DEX
            (K['M'], K['C'], 1, 100.0, 0, 0, 0),      # stable out of MEV
            (0, K['A'], 2, 7e6, 1, 1, 0),             # USDC mint (hour 1)
            (K['B'], 0, 3, 1e6, 1, 0, 1),             # DAI burn
            (K['T'], K['X'], 1, 3e7, 1, 0, 0),        # treasury out, also a deposit of 30M (treasury is not an exchange)
            (K['A'], K['X'], 0, 600.0, 2, 0, 0),      # ETH deposit 600 -> large
            (K['X'], K['Y'], 1, 50.0, 2, 0, 0)]       # cross-entity exchange transfer
    st, bloom = _state(), Bloom(16, 3)
    bloom.add(np.array([K['A']], np.uint64))
    h, large = hourly6.day_rows('2023-06-01', _day(rows), st, bloom, CFG)
    assert len(h) == 24 and list(h.columns) == hourly6.COLUMNS
    assert h['tk_usdt_in'].iloc[0] == 2e6 and h['tk_usdc_out'].iloc[0] == 5e5
    assert h['cl_dex_eth_in'].iloc[0] == 3.0 and h['cl_mev_stable_out'].iloc[0] == 100.0
    assert h['is_usdc_mint'].iloc[1] == 7e6 and h['is_dai_burn'].iloc[1] == 1e6 and h['is_usdt_treasury_out'].iloc[1] == 3e7
    assert h['tk_usdt_in'].iloc[1] == 3e7 and h['gs_cex_cex_usd'].iloc[2] == 50.0
    assert h['gs_active'].iloc[1] == 2.0                                   # mint/burn rows are not graph edges
    assert sorted(zip(large['direction'], large['amount'])) == [(1, 600.0), (1, 2e6), (1, 3e7)]
    assert large['entity'].tolist() == [st.entity_names.index('okx')] * 3 and large['cp_new'].tolist()[0] == False
    assert h['gs_new_share'].iloc[0] > 0 and bloom.contains(np.array([K['B']], np.uint64)).all()


def test_mint_burn_only_in_issuance():
    st, bloom = _state(), Bloom(16, 3)
    h, large = hourly6.day_rows('2023-06-01', _day([(0, K['X'], 2, 9e6, 0, 1, 0), (K['X'], 0, 2, 9e6, 0, 0, 1)]), st, bloom, CFG)
    assert h['is_usdc_mint'].iloc[0] == 9e6 and h['is_usdc_burn'].iloc[0] == 9e6
    assert h['tk_usdc_in'].iloc[0] == 0.0 and h['tk_usdc_out'].iloc[0] == 0.0 and h['gs_active'].iloc[0] == 0.0 and len(large) == 0


def test_observe_marks_first_seen_labels():
    doc = {'exchange': {X: 'okx'}, 'dex': [], 'bridge': [], 'mev': [], 'funds': [], 'issuer': {'usdt_treasury': TREAS}}
    st = labels6.LabelState(doc, TREAS)
    st.begin_day(5)
    h, _ = hourly6.day_rows('2017-01-06', _day([(K['A'], K['X'], 1, 5e6, 0, 0, 0)]), st, Bloom(16, 3), CFG)
    assert h['tk_usdt_in'].iloc[0] == 0.0                                  # not active on its first day
    assert st.ex_first[0] == 5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_hourly6.py -q`
Expected: FAIL with `ImportError: cannot import name 'hourly6'`

- [ ] **Step 3: Implement hourly6.py**

```python
# tradingagents/research/onchain_b6/hourly6.py
"""One day of admitted transfers -> 24 hourly rows of structure, token-split, class and
issuance series (spec §4.1–4.2) and the day's large transfers (§4.3)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import structure6
from .config import day_ord
from .labels6 import CLASSES

TOKENS = {1: 'usdt', 2: 'usdc', 3: 'dai'}
TK = [f'tk_{t}_{d}' for t in TOKENS.values() for d in ('in', 'out')]
CL = [f'cl_{c}_{k}' for c in CLASSES for k in ('stable_in', 'stable_out', 'eth_in', 'eth_out')]
IS = ['is_usdc_mint', 'is_usdc_burn', 'is_dai_mint', 'is_dai_burn', 'is_usdt_treasury_out', 'is_usdt_treasury_in']
COLUMNS = structure6.NAMES + TK + CL + IS


def day_rows(day, d, state, bloom, cfg):
    start = int(pd.Timestamp(day, tz='UTC').timestamp())
    hr = ((d.ts - start) // 3600).astype(int)
    lg_s, lg_e = cfg['large']['stable_usd'], cfg['large']['eth']
    out = np.zeros((24, len(COLUMNS)))
    col = {c: i for i, c in enumerate(COLUMNS)}
    large = []
    seen_today = []
    for h in range(24):
        m = hr == h
        if not m.any():
            continue
        src, dst, tok, amt, mint, burn = d.src[m], d.dst[m], d.token[m], d.amount[m], d.mint[m], d.burn[m]
        row = out[h]
        row[col['is_usdc_mint']] = amt[mint & (tok == 2)].sum()
        row[col['is_usdc_burn']] = amt[burn & (tok == 2)].sum()
        row[col['is_dai_mint']] = amt[mint & (tok == 3)].sum()
        row[col['is_dai_burn']] = amt[burn & (tok == 3)].sum()
        tr = ~mint & ~burn
        src, dst, tok, amt = src[tr], dst[tr], tok[tr], amt[tr]
        if len(src) == 0:
            continue
        stable = tok > 0
        usd = np.where(stable, amt, 0.0)
        row[col['is_usdt_treasury_out']] = amt[(src == state.treasury_key) & (tok == 1)].sum()
        row[col['is_usdt_treasury_in']] = amt[(dst == state.treasury_key) & (tok == 1)].sum()
        ex_s, ex_d = state.is_exchange(src), state.is_exchange(dst)
        dep, wd = ~ex_s & ex_d, ex_s & ~ex_d
        for code, name in TOKENS.items():
            row[col[f'tk_{name}_in']] = amt[dep & (tok == code)].sum()
            row[col[f'tk_{name}_out']] = amt[wd & (tok == code)].sum()
        for c in CLASSES:
            in_s, in_d = state.in_class(c, src), state.in_class(c, dst)
            ci, co = ~in_s & in_d, in_s & ~in_d
            row[col[f'cl_{c}_stable_in']] = amt[ci & stable].sum()
            row[col[f'cl_{c}_stable_out']] = amt[co & stable].sum()
            row[col[f'cl_{c}_eth_in']] = amt[ci & ~stable].sum()
            row[col[f'cl_{c}_eth_out']] = amt[co & ~stable].sum()
        ent_s, ent_d = state.entity_of(src), state.entity_of(dst)
        s = structure6.hour_structure(src, dst, usd, ex_s, ex_d, ent_s, ent_d, bloom.contains, cfg['structure']['top_n'])
        for k, v in s.items():
            row[col[k]] = v
        big = (stable & (amt >= lg_s)) | (~stable & (amt >= lg_e))
        for mask, direction, cp in ((dep & big, 1, src), (wd & big, -1, dst)):
            idx = np.flatnonzero(mask)
            if len(idx):
                new = ~bloom.contains(cp[idx])
                ent = np.where(direction == 1, ent_d[idx], ent_s[idx])
                large += [{'ts': int(d.ts[m][tr][i]), 'token': int(tok[i]), 'amount': float(amt[i]), 'direction': direction,
                           'entity': int(ent[j]), 'cp_new': bool(new[j])} for j, i in enumerate(idx)]
        keys = np.unique(np.concatenate([src, dst]))
        bloom.add(keys)
        seen_today.append(keys)
    if seen_today:
        state.observe(np.concatenate(seen_today), day_ord(day))
    rows = pd.DataFrame(out, columns=COLUMNS, index=pd.date_range(day, periods=24, freq='h'))
    cols = ['ts', 'token', 'amount', 'direction', 'entity', 'cp_new']
    types = ('int64', 'int64', 'float64', 'int64', 'int64', 'bool')
    lg = pd.DataFrame(large, columns=cols) if large else pd.DataFrame({c: pd.Series(dtype=t) for c, t in zip(cols, types)})
    return rows, lg.astype(dict(zip(cols, types)))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_hourly6.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b6/hourly6.py tests/research/onchain_b6/test_hourly6.py
git commit -m "feat(onchain-b6): hourly structure, token, class and issuance rows with large-transfer records

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Minute bars and the event study

**Files:**
- Create: `tradingagents/research/onchain_b6/minutes.py`
- Test: `tests/research/onchain_b6/test_minutes.py`

**Interfaces:**
- Consumes: `onchain_b4.screen4.interval`.
- Produces: `minutes.fetch(get, symbol, start, end, sleep) -> Series` (minute closes, naive UTC); `minutes.select_events(large, cfg) -> DataFrame[minute, direction, tier, token]`; `minutes.placebo(events, closes, cfg) -> DatetimeIndex`; `minutes.responses(minutes_idx, closes, cfg) -> dict` with keys `n, vol{k}, ret{k}, pre_ret` each `{mean, lo, hi}`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b6/test_minutes.py
import json

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b6 import config, minutes

CFG = config.load()


def test_fetch_minute_pages():
    stop = int(pd.Timestamp('2023-01-01 02:00', tz='UTC').timestamp() * 1000)

    def get(url):
        ms = int(url.split('startTime=')[1].split('&')[0])
        rows = [[t, '0', '0', '0', str(100 + (t - ms) / 60000), '0', 0, '0'] for t in range(ms, min(stop, ms + 1000 * 60000), 60000)]
        return json.dumps(rows).encode()
    s = minutes.fetch(get, 'ETHUSDT', '2022-12-31', '2023-01-01 02:00', sleep=lambda x: None)
    assert len(s) == 26 * 60 and s.index[0] == pd.Timestamp('2022-12-31 00:00') and s.index[-1] == pd.Timestamp('2023-01-01 01:59')


def _large():
    t0 = int(pd.Timestamp('2023-06-01 10:00:07', tz='UTC').timestamp())
    return pd.DataFrame({'ts': [t0, t0 + 600, t0 + 1900, t0 + 3700, t0 + 3800], 'token': [1, 1, 0, 2, 0],
                         'amount': [1.2e7, 6e7, 6000.0, 2e7, 100.0], 'direction': [1, 1, -1, 1, 1],
                         'entity': [0, 0, 0, 0, 0], 'cp_new': [False] * 5})


def test_select_events_tiers_and_spacing():
    ev = minutes.select_events(_large(), CFG)
    rows = sorted(zip(ev['minute'].astype(str), ev['direction'], ev['tier']))
    assert rows == [('2023-06-01 10:00:00', 1, 1), ('2023-06-01 10:10:00', 1, 2), ('2023-06-01 10:31:00', -1, 1),
                    ('2023-06-01 11:01:00', 1, 1)]                       # 10:10 tier-1 event suppressed by 30-min spacing


def test_response_alignment_and_placebo_gap():
    idx = pd.date_range('2023-06-01', periods=3 * 24 * 60, freq='min')
    closes = pd.Series(100.0, index=idx)
    e = pd.Timestamp('2023-06-01 10:00')
    closes.loc[e + pd.Timedelta(minutes=1):] = 110.0            # jump in the first minute after the event minute
    r = minutes.responses(pd.DatetimeIndex([e]), closes, {**CFG['minutes'], 'block': 1})
    assert np.isclose(r['ret1']['mean'], np.log(1.1)) and np.isclose(r['pre_ret']['mean'], 0.0)
    noisy = pd.Series(100 * np.exp(np.cumsum(np.random.default_rng(3).normal(0, 1e-4, len(idx)))), index=idx)
    noisy.loc[e + pd.Timedelta(minutes=1):] *= 1.1
    assert minutes.responses(pd.DatetimeIndex([e]), noisy, {**CFG['minutes'], 'block': 1})['vol5']['mean'] > 0
    ev = pd.DataFrame({'minute': [e], 'direction': [1], 'tier': [1], 'token': [1]})
    pl = minutes.placebo(ev, closes, CFG['minutes'])
    assert len(pl) == 1 and pl[0].hour == 10 and abs((pl[0] - e).total_seconds()) >= 3600
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_minutes.py -q`
Expected: FAIL with `ImportError: cannot import name 'minutes'`

- [ ] **Step 3: Implement minutes.py**

```python
# tradingagents/research/onchain_b6/minutes.py
"""Minute-level event study (spec §6): Binance 1-minute closes, very large deposit and
withdrawal events from the large-transfer records, responses from the next full minute,
placebo minutes matched by year and hour of day."""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from ..onchain_b4.screen4 import interval

URL = 'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&startTime={ms}&limit=1000'
MIN_MS = 60_000


def fetch(get, symbol, start, end, sleep=time.sleep, pause=0.05):
    ms, stop = int(pd.Timestamp(start, tz='UTC').timestamp() * 1000), int(pd.Timestamp(end, tz='UTC').timestamp() * 1000)
    vals = {}
    while ms < stop:
        rows = json.loads(get(URL.format(symbol=symbol, ms=ms)))
        for k in rows:
            if k[0] < stop:
                vals[int(k[0])] = float(k[4])
        if len(rows) < 1000:
            break
        ms = rows[-1][0] + MIN_MS
        sleep(pause)
    keys = sorted(vals)
    return pd.Series([vals[k] for k in keys], index=pd.to_datetime(keys, unit='ms'), name='close')


def select_events(large, cfg):
    m = cfg['minutes']
    tiers = m['tiers']
    df = large.copy()
    stable = df['token'] > 0
    thr = lambda i: np.where(stable, tiers['stable_usd'][i], tiers['eth'][i])
    df['minute'] = pd.to_datetime(df['ts'], unit='s').dt.floor('min')
    out = []
    for tier in (1, 2):                                            # nested: tier 1 holds every event of tier 2
        sub = df[df['amount'] >= thr(tier - 1)]
        for direction, g in sub.sort_values('ts').groupby('direction'):
            last = None
            for _, r in g.iterrows():
                if last is None or (r['minute'] - last) >= pd.Timedelta(minutes=m['spacing_min']):
                    out.append({'minute': r['minute'], 'direction': int(direction), 'tier': int(tier), 'token': int(r['token'])})
                    last = r['minute']
    return pd.DataFrame(out, columns=['minute', 'direction', 'tier', 'token']).sort_values('minute').reset_index(drop=True)


def _stat(x, block, gate_draws=2000, seed=20261020):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < max(2, block):
        return {'mean': float(x.mean()) if len(x) else np.nan, 'lo': np.nan, 'hi': np.nan}
    lo, hi = interval(x, block, gate_draws, seed, 100)
    return {'mean': float(x.mean()), 'lo': lo, 'hi': hi}


def responses(minutes_idx, closes, m):
    full = closes.reindex(pd.date_range(closes.index.min(), closes.index.max(), freq='min'))
    lc = np.log(full)
    r2 = lc.diff() ** 2
    ev = pd.DatetimeIndex(minutes_idx)
    out = {'n': int(len(ev))}
    pre = r2.rolling(m['pre_vol_min'], min_periods=m['pre_vol_min']).sum()
    for k in m['k_vol']:
        post = r2.rolling(k, min_periods=k).sum().shift(-k)             # sum over minutes t+1 .. t+k at index t
        val = np.log(post.reindex(ev).to_numpy() / k) - np.log(pre.reindex(ev).to_numpy() / m['pre_vol_min'])
        out[f'vol{k}'] = _stat(val, m['block'])
    for k in m['k_ret']:
        out[f'ret{k}'] = _stat((lc.shift(-k) - lc).reindex(ev).to_numpy(), m['block'])
    out['pre_ret'] = _stat((lc - lc.shift(m['pre_ret_min'])).reindex(ev).to_numpy(), m['block'])
    return out


def placebo(events, closes, m):
    rng = np.random.default_rng(m['seed'])
    ev = pd.DatetimeIndex(events['minute']).sort_values()
    taken = ev.to_numpy().astype('datetime64[m]').astype(np.int64)
    gap = m['placebo_gap_min']
    idx = closes.index
    out = []
    for e in ev:
        pool = idx[(idx.year == e.year) & (idx.hour == e.hour)].to_numpy().astype('datetime64[m]').astype(np.int64)
        ok = pool[np.min(np.abs(pool[:, None] - taken[None, :]), axis=1) >= gap] if len(pool) else pool
        if len(ok):
            out.append(pd.Timestamp(int(rng.choice(ok)), unit='m'))
    return pd.DatetimeIndex(out)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_minutes.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b6/minutes.py tests/research/onchain_b6/test_minutes.py
git commit -m "feat(onchain-b6): minute bars, very-large-transfer events, responses and placebo

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Tron USDT stream

**Files:**
- Create: `tradingagents/research/onchain_b6/tron.py`
- Test: `tests/research/onchain_b6/test_tron.py`

**Interfaces:**
- Produces: `tron.b58_to_hex(addr) -> str` (40 hex chars); `tron.topics(addrs) -> list[str]` (64-hex); `tron.parse_lines(raw_bytes) -> list[dict]`; `tron.aggregate(blocks, label_set, big_usd, direction) -> dict[hour -> dict]`; `tron.Backoff(waits, sleep)`; `tron.run(post, labels_hex, state_path, out_path, cfg, sleep)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b6/test_tron.py
import json

import pandas as pd
import pytest

from tradingagents.research.onchain_b6 import config, tron

CFG = config.load()
L = ['TXFBqBbqJommqZf7BV8NNYzePh97UmJodJ']            # a Tron base58 address


def test_b58_to_hex_and_topics():
    h = tron.b58_to_hex(L[0])
    assert len(h) == 40 and tron.topics(L)[0] == '0' * 24 + h


def _block(num, ts, logs):
    return json.dumps({'header': {'number': num, 'timestamp': ts}, 'logs': logs}).encode()


def _log(frm, to, usd):
    pad = lambda h: '0' * 24 + h
    return {'topics': ['dd', pad(frm), pad(to)], 'data': hex(int(usd * 1e6))[2:].rjust(64, '0')}


def test_aggregate_in_out_and_big():
    lab = tron.b58_to_hex(L[0])
    other, third = 'a' * 40, 'b' * 40
    ts = int(pd.Timestamp('2023-06-01 10:30', tz='UTC').timestamp() * 1000)
    blocks = [{'header': {'number': 1, 'timestamp': ts}, 'logs': [_log(other, lab, 2e6), _log(lab, third, 5.0), _log(lab, lab, 9e6)]}]
    agg = tron.aggregate(blocks, {lab}, 1e6)
    row = agg[pd.Timestamp('2023-06-01 10:00')]
    assert row == {'tron_in_val': 2e6, 'tron_out_val': 5.0, 'tron_in_cnt': 1, 'tron_out_cnt': 1, 'tron_big_in': 1}


def test_stream_continues_partial_and_backs_off(tmp_path):
    lab = tron.b58_to_hex(L[0])
    calls, slept = [], []
    t0 = int(pd.Timestamp('2020-05-23', tz='UTC').timestamp() * 1000)

    def post(body):
        calls.append(body)
        if len(calls) == 2:
            raise tron.Overloaded(529)
        frm, to = body['fromBlock'], body['toBlock']
        last = min(to, frm + 1)                                     # the server returns only two blocks per call
        lines = [_block(n, t0 + (n - 20000000) * 3000, [_log('a' * 40, lab, 1.0)] if 'topic2' in body['logs'][0] else []) for n in range(frm, last + 1)]
        return b'\n'.join(lines)
    cfg = json.loads(json.dumps(CFG))
    cfg['tron'].update({'start_block': 20000000, 'chunk_blocks': 4, 'backoff': [1, 2]})
    tron.run(post, [lab], tmp_path / 'state.json', tmp_path / 'hourly.parquet', cfg, sleep=slept.append, stop_block=20000007)
    out = pd.read_parquet(tmp_path / 'hourly.parquet')
    assert out['tron_in_cnt'].sum() == 8 and slept[0] == 1
    assert json.loads((tmp_path / 'state.json').read_text())['next_block'] == 20000008
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_tron.py -q`
Expected: FAIL with `ImportError: cannot import name 'tron'`

- [ ] **Step 3: Implement tron.py**

```python
# tradingagents/research/onchain_b6/tron.py
"""Tron USDT exchange flows (spec §7) from the SQD portal: server-side topic filters on the
labelled exchange addresses, hourly aggregation on the fly, resumable by block."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd

ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
COLS = ['tron_in_val', 'tron_out_val', 'tron_in_cnt', 'tron_out_cnt', 'tron_big_in']


class Overloaded(RuntimeError):
    def __init__(self, status):
        super().__init__(f'HTTP {status}')
        self.status = status


def b58_to_hex(addr):
    n = 0
    for ch in addr:
        n = n * 58 + ALPHABET.index(ch)
    return n.to_bytes(25, 'big')[1:21].hex()


def topics(addrs):
    return ['0' * 24 + b58_to_hex(a) for a in addrs]


def parse_lines(raw):
    return [json.loads(x) for x in raw.splitlines() if x.strip()]


def aggregate(blocks, label_set, big_usd):
    out = {}
    for b in blocks:
        hour = pd.Timestamp(int(b['header']['timestamp']), unit='ms').floor('h')
        row = out.setdefault(hour, {c: 0.0 for c in COLS})
        for lg in b.get('logs', []):
            t = lg['topics']
            if len(t) < 3:
                continue
            frm, to = t[1][-40:], t[2][-40:]
            usd = int(lg['data'], 16) / 1e6 if lg.get('data') else 0.0
            fi, ti = frm in label_set, to in label_set
            if ti and not fi:
                row['tron_in_val'] += usd
                row['tron_in_cnt'] += 1
                row['tron_big_in'] += usd >= big_usd
            elif fi and not ti:
                row['tron_out_val'] += usd
                row['tron_out_cnt'] += 1
    return out


class Backoff:
    def __init__(self, waits, sleep):
        self.waits, self.sleep, self.i = list(waits), sleep, 0

    def wait(self):
        if self.i >= len(self.waits):
            raise SystemExit('tron stream: back-off exhausted')
        self.sleep(self.waits[self.i])
        self.i += 1

    def reset(self):
        self.i = 0


def _body(cfg, frm, to, key, tops):
    t = cfg['tron']
    return {'type': 'tron', 'fromBlock': frm, 'toBlock': to,
            'logs': [{'address': [t['usdt']], 'topic0': [t['topic0']], key: tops}],
            'fields': {'block': {'number': True, 'timestamp': True}, 'log': {'topics': True, 'data': True}}}


def run(post, labels_hex, state_path, out_path, cfg, sleep=time.sleep, stop_block=None):
    t = cfg['tron']
    tops = ['0' * 24 + h for h in labels_hex]
    label_set = set(labels_hex)
    end_ms = int(pd.Timestamp(t['end'], tz='UTC').timestamp() * 1000)
    state_path, out_path = Path(state_path), Path(out_path)
    state = json.loads(state_path.read_text()) if state_path.exists() else {'next_block': t['start_block']}
    rows = pd.read_parquet(out_path).to_dict('index') if out_path.exists() else {}
    rows = {pd.Timestamp(k): v for k, v in rows.items()}
    back = Backoff(t['backoff'], sleep)
    nxt = state['next_block']
    done = False
    while not done:
        frm, to = nxt, nxt + t['chunk_blocks'] - 1
        if stop_block is not None:
            to = min(to, stop_block)
        for key in ('topic2', 'topic1'):
            cur = frm
            while cur <= to:
                try:
                    blocks = parse_lines(post(_body(cfg, cur, to, key, tops)))
                except Overloaded:
                    back.wait()
                    continue
                back.reset()
                if not blocks:
                    cur = to + 1
                    break
                for hour, agg in aggregate(blocks, label_set, t['big_usd']).items():
                    r = rows.setdefault(hour, {c: 0.0 for c in COLS})
                    if key == 'topic2':
                        for c in ('tron_in_val', 'tron_in_cnt', 'tron_big_in'):
                            r[c] += agg[c]
                    else:
                        for c in ('tron_out_val', 'tron_out_cnt'):
                            r[c] += agg[c]
                last = blocks[-1]['header']
                if int(last['timestamp']) >= end_ms:
                    done = True
                cur = int(last['number']) + 1
        nxt = to + 1
        if stop_block is not None and nxt > stop_block:
            done = True
        df = pd.DataFrame.from_dict(rows, orient='index').sort_index()[COLS] if rows else pd.DataFrame(columns=COLS)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = out_path.with_name('.' + out_path.name + '.tmp')
        df.to_parquet(tmp)
        os.replace(tmp, out_path)
        state_path.write_text(json.dumps({'next_block': nxt}))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_tron.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b6/tron.py tests/research/onchain_b6/test_tron.py
git commit -m "feat(onchain-b6): resumable Tron USDT exchange-flow stream with hourly aggregation

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Dataset and forecast comparison

**Files:**
- Create: `tradingagents/research/onchain_b6/dataset6.py`, `tradingagents/research/onchain_b6/forecast6.py`
- Test: `tests/research/onchain_b6/test_dataset6.py`, `tests/research/onchain_b6/test_forecast6.py`

**Interfaces:**
- Consumes: `onchain_b4.dataset4.zscore, price_features, hourly_targets`; `onchain_b5.decisions.px_features`; `onchain_b5.implied.prepare`; `onchain_b5.forecast.run`.
- Produces: `dataset6.transform_raw(raw, c) -> DataFrame` (`__h1z`, `__d24z` per column); `dataset6.iv_hourly(trades_for_day, days, min_trades, ffill_hours, implied_cfg) -> Series` (log IV, hourly); `dataset6.market_hourly(bars, dvol, iv) -> DataFrame` (`h0_`, `px_`, `mk_`); `dataset6.samples(track, feats, bars, cfg) -> DataFrame` (features + V6, V24 within the track window, finite features required); `forecast6.set_prefixes(name, track, cfg, with_tron) -> list`; `forecast6.run_all(samples_by_track, cfg, with_tron) -> list[dict]` (keys `track, target, family, set, comparator, group, n, mean_diff, lo, hi, wins, years, passed`); `forecast6.report(results) -> str`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b6/test_dataset6.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import implied
from tradingagents.research.onchain_b6 import config, dataset6 as D

CFG = config.load()


def test_transform_raw_is_causal_and_named():
    idx = pd.date_range('2024-01-01', periods=1500, freq='h')
    raw = pd.DataFrame({'gs_active': np.random.default_rng(1).gamma(2, 3, 1500), 'tk_usdt_in': 1.0}, index=idx)
    a = D.transform_raw(raw, CFG['transforms'])
    b = D.transform_raw(raw.assign(gs_active=raw['gs_active'].where(raw.index < idx[1200], 99.0)), CFG['transforms'])
    pd.testing.assert_frame_equal(a.iloc[:1200], b.iloc[:1200])
    assert set(a.columns) == {'gs_active__h1z', 'gs_active__d24z', 'tk_usdt_in__h1z', 'tk_usdt_in__d24z'}
    assert (a['tk_usdt_in__h1z'].dropna() == 0).all()


def test_iv_hourly_min_trades_and_ffill_limit():
    ts0 = int(pd.Timestamp('2023-06-01', tz='UTC').timestamp() * 1000)
    rows = [(0.2, 50.0), (0.3, 52.0), (0.4, 54.0), (5.5, 60.0)]      # 3 trades in hour 0, one in hour 5
    df = implied.prepare(pd.DataFrame([{'timestamp': ts0 + int(h * 3.6e6), 'trade_id': str(i), 'instrument_name': 'ETH-2JUN23-1900-C',
                                        'iv': iv, 'price': 0.01, 'index_price': 1900.0, 'amount': 1.0, 'direction': 'buy'}
                                       for i, (h, iv) in enumerate(rows)]))
    s = D.iv_hourly(lambda d: df if d == '2023-06-01' else None, ['2023-06-01'], 3, 3, {'moneyness': 0.02, 'iv_min_ahead_h': 2})
    h = lambda k: pd.Timestamp('2023-06-01') + pd.Timedelta(hours=k)
    assert np.isclose(s[h(0)], np.log(0.52)) and np.isclose(s[h(3)], np.log(0.52)) and np.isnan(s.get(h(4), np.nan))
    assert h(5) not in s.dropna().index                                  # one trade: ineligible, not filled


def test_samples_windows_and_targets():
    idx = pd.date_range('2021-01-01', periods=24 * 400, freq='h')
    rng = np.random.default_rng(2)
    bars = pd.DataFrame({'close': 1000 * np.exp(np.cumsum(rng.normal(0, 0.004, len(idx)))), 'qvol': rng.gamma(2.0, 1e6, len(idx))}, index=idx)
    feats = pd.DataFrame({'gs_active__h1z': rng.normal(size=len(idx)), 'eth_in_val__h1z': rng.normal(size=len(idx)),
                          'mk_iv': rng.normal(size=len(idx))}, index=idx)
    cfg = {**CFG, 'tracks': {'B': {**CFG['tracks']['B'], 'start': '2021-04-01', 'end': '2022-01-31'}}}
    s = D.samples('B', feats, bars, cfg)
    assert s.index.min() >= pd.Timestamp('2021-04-01') and s['V24'].last_valid_index() == pd.Timestamp('2022-01-30 23:00')
    assert s['V6'].last_valid_index() == pd.Timestamp('2022-01-31 17:00') and {'V6', 'V24', 'h0_r1', 'px_rv6'} <= set(s.columns)
```

```python
# tests/research/onchain_b6/test_forecast6.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b6 import config, forecast6 as F

CFG = config.load()


def _samples(start, end, rng):
    idx = pd.date_range(start, end, freq='6h')
    n = len(idx)
    sig = rng.normal(size=n)
    df = pd.DataFrame({'h0_r1': rng.normal(size=n), 'px_rv6': rng.normal(size=n), 'mk_iv': rng.normal(size=n),
                       'eth_in_val__h1z': rng.normal(size=n), 'gs_core2_share__h1z': sig, 'tk_usdt_in__h1z': rng.normal(size=n),
                       'tron_in_val__h1z': rng.normal(size=n)}, index=idx)
    df['V6'] = 2 * sig + 0.3 * rng.normal(size=n)
    df['V24'] = rng.normal(size=n)
    return df


def test_set_prefixes_and_run_all_criteria():
    cfg = {**CFG, 'families': ['linear']}
    assert F.set_prefixes('X2', 'B', cfg, False) == ['h0_', 'px_', 'mk_', 'eth_', 'stable_', 'gs_']
    assert F.set_prefixes('X5', 'A', cfg, True)[-1] == 'tron_'
    rng = np.random.default_rng(5)
    res = F.run_all({'A': _samples('2017-10-02', '2024-12-31', rng), 'B': _samples('2021-04-01', '2026-10-12', rng)}, cfg, with_tron=True)
    assert len(res) == 10 + 20                        # track A: 5 comparisons x 1 group x 2 targets; track B: x 2 groups
    get = {(r['track'], r['target'], r['set'], r['group']): r for r in res}
    assert get[('A', 'V6', 'X2', '2019-24')]['passed'] and not get[('A', 'V6', 'X3', '2019-24')]['passed']
    assert get[('B', 'V6', 'X2', '2022-24')]['passed'] and 'passed' in get[('B', 'V6', 'X2', '2025-26')]
    assert not get[('A', 'V24', 'X2', '2019-24')]['passed']
    text = F.report(res)
    assert '| A | V6 | linear | X2 vs X1 | 2019-24 |' in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_dataset6.py tests/research/onchain_b6/test_forecast6.py -q`
Expected: FAIL with `ImportError: cannot import name 'dataset6'`

- [ ] **Step 3: Implement dataset6.py and forecast6.py**

```python
# tradingagents/research/onchain_b6/dataset6.py
"""B6 features and samples (spec §5): causal transforms of the hourly blocks, an hourly
near-expiry implied-volatility series, market features, and per-track samples."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b4 import dataset4
from ..onchain_b5 import implied
from ..onchain_b5.decisions import px_features

H = pd.Timedelta(hours=1)


def transform_raw(raw, c):
    out = {}
    for name in raw.columns:
        x = np.log1p(raw[name].clip(lower=0))
        out[f'{name}__h1z'] = dataset4.zscore(x, c['h1_window'], c['h1_min'], c['clip'])
        s24 = raw[name].rolling(24, min_periods=24).sum()
        out[f'{name}__d24z'] = dataset4.zscore(np.log1p(s24.clip(lower=0)), c['d24_window'], c['d24_min'], c['clip'])
    return pd.DataFrame(out, index=raw.index)


def iv_hourly(trades_for_day, days, min_trades, ffill_hours, implied_cfg):
    vals = {}
    for day in days:
        tr = trades_for_day(day)
        if tr is None or not len(tr):
            continue
        tr = tr[np.isfinite(tr['iv']) & (tr['iv'] > 0)].assign(bin=lambda x: x['ts'].dt.floor('h'))
        tr = tr[tr['expiry'] >= tr['bin'] + H + pd.Timedelta(hours=implied_cfg['iv_min_ahead_h'])]
        tr = tr[np.abs(np.log(tr['strike'] / tr['index_price'])) <= implied_cfg['moneyness']]
        for b, g in tr.groupby('bin'):
            g = g[g['expiry'] == g['expiry'].min()]
            if len(g) >= min_trades:
                vals[b] = np.log(implied.wmedian(g['iv'], g['amount']) / 100.0)
    s = pd.Series(vals, dtype=float).sort_index()
    if not len(s):
        return s
    full = s.reindex(pd.date_range(s.index.min(), pd.Timestamp(days[-1]) + 23 * H, freq='h'))
    return full.ffill(limit=ffill_hours)


def market_hourly(bars, dvol, iv):
    f = dataset4.price_features(bars).join(px_features(bars))
    if dvol is not None:
        d = dvol.reindex(f.index)
        f['mk_dvol'] = np.log(d)
        f['mk_dvol_chg24'] = np.log(d) - np.log(d.shift(24))
    if iv is not None:
        f['mk_iv'] = iv.reindex(f.index)
    return f.replace([np.inf, -np.inf], np.nan)


def samples(track, feats, bars, cfg):
    tc = cfg['tracks'][track]
    market = dataset4.price_features(bars).join(px_features(bars))
    df = feats.join(market, how='inner').join(dataset4.hourly_targets(bars)[['V6', 'V24']], how='left')
    start, end = pd.Timestamp(tc['start']), pd.Timestamp(tc['end']) + pd.Timedelta(days=1)
    df = df[(df.index >= start) & (df.index < end)]
    need = [c for c in df.columns if c not in ('V6', 'V24')]
    df = df[np.isfinite(df[need].to_numpy(float)).all(axis=1)].copy()
    for name, h in cfg['targets'].items():
        df.loc[df.index + pd.Timedelta(hours=h) > end - H, name] = np.nan
    return df
```

```python
# tradingagents/research/onchain_b6/forecast6.py
"""Forecast comparisons (spec §5) on B5's walk-forward runner, one run per track and target."""
from __future__ import annotations

import numpy as np

from ..onchain_b5 import forecast as F5

SETS = ['X0', 'X1', 'X2', 'X3', 'X4']


def set_prefixes(name, track, cfg, with_tron):
    blocks = cfg['set_blocks'][name]
    if 'T' in blocks and not with_tron:
        raise ValueError('Tron block not available')
    out = list(cfg['tracks'][track]['base'])
    for b in blocks:
        out += cfg['blocks'][b]
    return out


def _run_cfg(track, target, cfg, with_tron):
    tc = cfg['tracks'][track]
    sets = SETS + (['X5'] if with_tron else [])
    comps = cfg['comparisons'] + ([cfg['tron_comparison']] if with_tron else [])
    return {'sets': {s: set_prefixes(s, track, cfg, with_tron) for s in sets}, 'comparisons': comps,
            'families': cfg['families'], 'folds': {'test_years': tc['test_years'], 'inner_len': cfg['folds']['inner_len'],
                                                   'min_train': cfg['folds']['min_train']},
            'groups': tc['groups'], 'gate': cfg['gate'], 'models': cfg['models']}


def _passed(r, track_cfg, group_rows, min_wins):
    if track_cfg['criterion'] == 'years':
        return bool(r['hi'] < 0 and r['wins'] >= min_wins)
    first, second = list(track_cfg['groups'])
    if r['group'] != first:
        return bool(r['mean_diff'] < 0)
    other = group_rows.get(second)
    return bool(r['hi'] < 0 and other is not None and other['mean_diff'] < 0)


def run_all(samples_by_track, cfg, with_tron):
    results = []
    for track, df in samples_by_track.items():
        tc = cfg['tracks'][track]
        for target, h in cfg['targets'].items():
            d = df[df[target].notna()].copy()
            d['y'], d['tau_h'] = d[target], float(h)
            _, res = F5.run(d, _run_cfg(track, target, cfg, with_tron))
            for r in res:
                r['track'], r['target'] = track, target
            by = {}
            for r in res:
                by.setdefault((r['family'], r['set'], r['comparator']), {})[r['group']] = r
            for r in res:
                r['passed'] = _passed(r, tc, by[(r['family'], r['set'], r['comparator'])], cfg['folds']['min_year_wins'])
            results += res
    return results


def report(results):
    lines = ['| track | target | family | comparison | group | n | mean diff | 95 % CI | years better | pass |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for r in results:
        yrs = len(r['years']) if r['years'] else 0
        lines.append(f"| {r['track']} | {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['group']} | {r['n']} | "
                     f"{r['mean_diff']:+.5f} | [{r['lo']:+.5f}, {r['hi']:+.5f}] | {r['wins']}/{yrs} | {'PASS' if r['passed'] else '—'} |")
    return '\n'.join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_dataset6.py tests/research/onchain_b6/test_forecast6.py -q`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b6/dataset6.py tradingagents/research/onchain_b6/forecast6.py tests/research/onchain_b6/test_dataset6.py tests/research/onchain_b6/test_forecast6.py
git commit -m "feat(onchain-b6): causal features, hourly implied volatility, track samples and comparisons

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: CLI stages

**Files:**
- Create: `tradingagents/research/onchain_b6/cli.py`
- Test: `tests/research/onchain_b6/test_cli6.py`

**Interfaces:**
- Consumes: everything above; `onchain_b2.market.http_get`; `onchain_b4.cli._write_json, _peak_rss_mb, _require_disk, READ_TIMEOUT, STALL_EXIT, MIN_FREE_LAUNCH, MIN_FREE_SNAPSHOT`; `onchain_b4.hourmarket.load_all`; `onchain_b5.cli.trades_loader`; `onchain_b5.decisions.load_bars`; `onchain_b.runlog.Log`.
- Produces: `cli.main(argv)`; patchable `ARTIFACTS, STUDY, B2, B4, B5, ROOT`; `cli.filesystem()`; `cli.pass_complete()`; `cli.post_json(url, body)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b6/test_cli6.py
import copy
import json

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2.s3source import DayUnavailable
from tradingagents.research.onchain_b4.reader import addr_keys
from tradingagents.research.onchain_b6 import cli, config, labels6, reader6
from tradingagents.research.onchain_b6.reader6 import Day6

A, B, X = ('0x' + c * 40 for c in 'abx')


def _day(day):
    t0 = int(pd.Timestamp(day, tz='UTC').timestamp())
    ka, kb, kx = addr_keys(np.array([A, B, X], object))
    return Day6(src=np.array([ka, kx, kb], np.uint64), dst=np.array([kx, kb, ka], np.uint64), token=np.array([1, 0, 1], np.int8),
                amount=np.array([2e6, 1.0, 3.0]), ts=np.array([t0 + 60, t0 + 7200, t0 + 9000], np.int64),
                mint=np.zeros(3, bool), burn=np.zeros(3, bool), rows={'eth_transfers': 1, 'stable_transfers': 2, 'mint': 0, 'burn': 0})


def _setup(tmp_path, monkeypatch, unavailable=()):
    art = tmp_path / 'b6'
    cfg = copy.deepcopy(config.load())
    cfg['window'] = {'first_day': '2017-01-01', 'last_day': '2017-01-05'}
    cfg['structure']['bloom_bits_log2'] = 16
    cfg['s3']['retries'] = []
    monkeypatch.setattr(cli, 'ARTIFACTS', art)
    monkeypatch.setattr(cli.config, 'load', lambda: cfg)
    monkeypatch.setattr(cli, 'filesystem', lambda: None)
    monkeypatch.setattr(cli.shutil, 'disk_usage', lambda p: type('U', (), {'free': 10**12})())
    doc = {'exchange': {X: 'okx'}, 'dex': [], 'bridge': [], 'mev': [], 'funds': [], 'issuer': {'usdt_treasury': cfg['issuer']['usdt_treasury']}}
    labels6.save(doc, art / 'labels' / 'labels6.json')

    def fake(day, **kw):
        if day in unavailable:
            raise DayUnavailable(day, ['boom'])
        return _day(day)
    monkeypatch.setattr(reader6, 'read_day6', fake)
    return art


def test_pass_writes_rows_large_and_activates(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch)
    cli.main(['pass'])
    h = pd.read_parquet(art / 'hours' / '2017-01-03.parquet')
    assert len(h) == 24 and h['tk_usdt_in'].iloc[0] == 2e6            # X active from day 2 on
    assert pd.read_parquet(art / 'hours' / '2017-01-01.parquet')['tk_usdt_in'].iloc[0] == 0.0
    assert (art / 'large' / '2017-01-03.parquet').exists() and (art / 'state' / 'labels_state.npz').exists()
    assert cli.pass_complete()


def test_resume_matches_uninterrupted(tmp_path, monkeypatch):
    art = _setup(tmp_path / 'one', monkeypatch)
    cli.main(['pass'])
    full = pd.read_parquet(art / 'hours' / '2017-01-05.parquet')
    art2 = _setup(tmp_path / 'two', monkeypatch)
    cli.main(['pass', '--end', '2017-01-02'])
    cli.main(['pass'])
    pd.testing.assert_frame_equal(full, pd.read_parquet(art2 / 'hours' / '2017-01-05.parquet'))


def test_unavailable_day_marked_and_features_refuse_incomplete(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch, unavailable=('2017-01-02',))
    cli.main(['pass', '--end', '2017-01-03'])
    assert (art / 'hours' / '2017-01-02.unavailable.json').exists()
    with pytest.raises(SystemExit, match='pass incomplete'):
        cli.main(['features'])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_cli6.py -q`
Expected: FAIL with `ImportError: cannot import name 'cli'`

- [ ] **Step 3: Implement the CLI**

```python
# tradingagents/research/onchain_b6/cli.py
"""B6 stage runner: labels, minute bars, the sequential day pass, the Tron stream, feature
tables, forecast comparisons, the event study and the tables."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from pathlib import Path

import numpy as np
import pandas as pd

from ..onchain_b.runlog import Log
from ..onchain_b2 import market
from ..onchain_b2.s3source import DayUnavailable
from ..onchain_b3.history import Bloom
from ..onchain_b4 import hourmarket
from ..onchain_b4.cli import MIN_FREE_LAUNCH, MIN_FREE_SNAPSHOT, READ_TIMEOUT, STALL_EXIT, _peak_rss_mb, _write_json
from ..onchain_b5 import cli as B5CLI
from ..onchain_b5 import config as b5config
from ..onchain_b5.decisions import load_bars
from . import config, dataset6, forecast6, hourly6, labels6, minutes, reader6, tron
from .labels6 import LabelState

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B2 = config.B2_ARTIFACTS
B4 = config.B4_ARTIFACTS
B5 = config.B5_ARTIFACTS
ROOT = config.ROOT
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


def post_json(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'User-Agent': 'onchain-b6'})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code in (429, 529, 503):
            raise tron.Overloaded(e.code)
        raise


def stage_labels(args):
    c = config.load()
    out = ARTIFACTS / 'labels' / 'labels6.json'
    if out.exists():
        raise SystemExit('labels already frozen')
    doc = labels6.build(market.http_get, B2 / 'labels' / 'labels.json', c)
    labels6.save(doc, out)
    s = c['labels']['spellbook']
    txt = market.http_get(f"https://raw.githubusercontent.com/{s['repo']}/{s['branch']}/{s['tron']}").decode()
    addrs = re.findall(r"'tron'\s*,\s*'(T[1-9A-HJ-NP-Za-km-z]{33})'", txt)
    _write_json(ARTIFACTS / 'labels' / 'tron_labels.json', {'addresses': sorted(set(addrs)), 'hex': sorted({tron.b58_to_hex(a) for a in addrs}),
                                                            'commit': doc['sources']['spellbook_commit']})
    print(json.dumps({**doc['sources']['counts'], 'tron': len(set(addrs))}))


def stage_market(args):
    c = config.load()['minutes']
    (ARTIFACTS / 'market').mkdir(parents=True, exist_ok=True)
    for asset, sym in c['symbols'].items():
        s = minutes.fetch(market.http_get, sym, c['start'], c['end'])
        s.to_frame().to_parquet(ARTIFACTS / 'market' / f'minutes_{asset}.parquet')
        print(json.dumps({'asset': asset, 'minutes': len(s), 'first': str(s.index.min()), 'last': str(s.index.max())}))


def day_status(day):
    if (ARTIFACTS / 'hours' / f'{day}.parquet').exists():
        return 'done'
    if (ARTIFACTS / 'hours' / f'{day}.unavailable.json').exists():
        return 'unavailable'
    return None


def pass_complete():
    return all(day_status(d) is not None for d in config.days(config.load()))


def _load_state(c):
    doc = labels6.load(ARTIFACTS / 'labels' / 'labels6.json')
    sp, bp, mp = ARTIFACTS / 'state' / 'labels_state.npz', ARTIFACTS / 'state' / 'bloom.npy', ARTIFACTS / 'state' / 'meta.json'
    st_c = c['structure']
    if sp.exists() and bp.exists() and mp.exists():
        st = LabelState.load(sp, doc, c['issuer']['usdt_treasury'])
        bloom = Bloom(st_c['bloom_bits_log2'], st_c['bloom_hashes'])
        bloom.bits = np.load(bp)
        return st, bloom, json.loads(mp.read_text())['last_day']
    return LabelState(doc, c['issuer']['usdt_treasury']), Bloom(st_c['bloom_bits_log2'], st_c['bloom_hashes']), None


def _save_state(st, bloom, last_day):
    d = ARTIFACTS / 'state'
    d.mkdir(parents=True, exist_ok=True)
    st.save(d / 'labels_state.npz')
    tmp = d / '.bloom.tmp.npy'
    np.save(tmp, bloom.bits)
    os.replace(tmp, d / 'bloom.npy')
    _write_json(d / 'meta.json', {'last_day': last_day})


def stage_pass(args):
    c = config.load()
    _require_disk(MIN_FREE_LAUNCH, 'pass launch')
    days = [d for d in config.days(c) if args.end is None or d <= args.end]
    st, bloom, last = _load_state(c)
    todo = [d for d in days if last is None or d > last]
    log = Log(ARTIFACTS / 'logs' / 'pass.jsonl')
    fs, p = filesystem(), c['pass']
    hours, large = ARTIFACTS / 'hours', ARTIFACTS / 'large'
    hours.mkdir(parents=True, exist_ok=True)
    large.mkdir(parents=True, exist_ok=True)

    def fetch(day):
        return reader6.read_day6(day, filesystem=fs, root=c['s3']['bucket'], tokens=c['tokens'], retries=c['s3']['retries'])

    consecutive, since = 0, 0
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
                _require_disk(MIN_FREE_SNAPSHOT, 'snapshot')
                _save_state(st, bloom, last)
                pool.shutdown(wait=False, cancel_futures=True)
                _hard_exit(STALL_EXIT)
            except DayUnavailable as e:
                _write_json(hours / f'{day}.unavailable.json', {'day': day, 'errors': e.errors})
                log.event(event='day', day=day, status='unavailable')
                consecutive += 1
                if consecutive >= p['max_consecutive_unavailable']:
                    _require_disk(MIN_FREE_SNAPSHOT, 'snapshot')
                    _save_state(st, bloom, last)
                    raise SystemExit(f'{consecutive} consecutive unavailable days up to {day}: stopping the pass')
                continue
            consecutive = 0
            st.begin_day(config.day_ord(day))
            rows, lg = hourly6.day_rows(day, d, st, bloom, c)
            for df, path in ((rows, hours / f'{day}.parquet'), (lg, large / f'{day}.parquet')):
                tmp = path.with_name('.' + path.name + '.tmp')
                df.to_parquet(tmp)
                os.replace(tmp, path)
            (hours / f'{day}.unavailable.json').unlink(missing_ok=True)
            last = day
            log.event(event='day', day=day, status='done', seconds=round(time.time() - t, 1), transfers=int(len(d.src)),
                      large=int(len(lg)), peak_rss_mb=_peak_rss_mb(), **d.rows)
            del d
            since += 1
            if since >= p['snapshot_every']:
                _require_disk(MIN_FREE_SNAPSHOT, 'snapshot')
                _save_state(st, bloom, last)
                since = 0
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    _require_disk(MIN_FREE_SNAPSHOT, 'snapshot')
    _save_state(st, bloom, last)


def stage_tron(args):
    c = config.load()
    lab = json.loads((ARTIFACTS / 'labels' / 'tron_labels.json').read_text())['hex']
    (ARTIFACTS / 'tron').mkdir(parents=True, exist_ok=True)
    tron.run(lambda body: post_json(c['tron']['url'], body), lab, ARTIFACTS / 'tron' / 'state.json',
             ARTIFACTS / 'tron' / 'hourly.parquet', c)
    print('tron stream complete')


def tron_complete():
    p = ARTIFACTS / 'tron' / 'hourly.parquet'
    if not p.exists():
        return False
    df = pd.read_parquet(p)
    return len(df) and df.index.max() >= pd.Timestamp(config.load()['tron']['end']) - pd.Timedelta(days=2)


def _require_pass():
    if not pass_complete():
        raise SystemExit('pass incomplete: build or mark every day first')


def stage_features(args):
    _require_pass()
    c = config.load()
    days = config.days(c)
    frames = [pd.read_parquet(ARTIFACTS / 'hours' / f'{d}.parquet') for d in days if day_status(d) == 'done']
    raw = pd.concat(frames).sort_index().reindex(pd.date_range(days[0], periods=24 * len(days), freq='h'))
    if tron_complete():
        t = pd.read_parquet(ARTIFACTS / 'tron' / 'hourly.parquet').reindex(raw.index)
        raw = raw.join(t)
    trans = dataset6.transform_raw(raw, c['transforms'])
    flows = pd.read_parquet(B4 / 'features' / 'hourly.parquet')
    flows = flows[[x for x in flows.columns if x.startswith(tuple(c['blocks']['F']))]]
    feats = trans.join(flows, how='left')
    bars = hourmarket.load_all(B4 / 'market' / 'hourly_dev.json', B4 / 'sealed' / 'hourly_sealed.json')
    dvol = pd.read_parquet(B5 / 'market' / 'dvol_ETH.parquet')['dvol']
    iv = dataset6.iv_hourly(B5CLI.trades_loader('ETH'), b5config.days(b5config.load()), c['iv']['min_trades'], c['iv']['ffill_hours'],
                            {**b5config.load()['implied'], 'iv_min_ahead_h': b5config.load()['events']['iv_min_ahead_h']})
    mk = dataset6.market_hourly(bars, dvol, iv)[['mk_dvol', 'mk_dvol_chg24', 'mk_iv']]
    out = ARTIFACTS / 'features'
    out.mkdir(parents=True, exist_ok=True)
    raw.to_parquet(out / 'hourly_raw.parquet')
    feats.to_parquet(out / 'features_A.parquet')
    feats.join(mk, how='left').to_parquet(out / 'features_B.parquet')
    print(json.dumps({'hours': len(raw), 'raw_columns': raw.shape[1], 'feature_columns': feats.shape[1], 'tron': bool(tron_complete())}))


def stage_forecast(args):
    c = config.load()
    bars = hourmarket.load_all(B4 / 'market' / 'hourly_dev.json', B4 / 'sealed' / 'hourly_sealed.json')
    with_tron = tron_complete()
    sb = {tr: dataset6.samples(tr, pd.read_parquet(ARTIFACTS / 'features' / f'features_{tr}.parquet'), bars, c) for tr in ('A', 'B')}
    res = forecast6.run_all(sb, c, with_tron)
    (ARTIFACTS / 'forecast').mkdir(parents=True, exist_ok=True)
    _write_json(ARTIFACTS / 'forecast' / 'results.json', {'results': res, 'with_tron': with_tron, 'n': {k: len(v) for k, v in sb.items()}})
    print(json.dumps({'rows': len(res), 'passed': sum(r['passed'] for r in res), 'with_tron': with_tron}))


def stage_events(args):
    c = config.load()
    m = c['minutes']
    large = pd.concat([pd.read_parquet(p) for p in sorted((ARTIFACTS / 'large').glob('*.parquet'))], ignore_index=True)
    ev = minutes.select_events(large, c)
    out = {'events': int(len(ev))}
    for asset in m['symbols']:
        closes = pd.read_parquet(ARTIFACTS / 'market' / f'minutes_{asset}.parquet')['close']
        out[asset] = {}
        for (direction, tier), g in ev.groupby(['direction', 'tier']):
            key = f"{'deposit' if direction == 1 else 'withdrawal'}_tier{tier}"
            pl = minutes.placebo(g, closes, m)
            out[asset][key] = {}
            for gname, yrs in m['groups'].items():
                e = pd.DatetimeIndex(g.loc[g['minute'].dt.year.isin(yrs), 'minute'])
                p = pl[np.isin(pl.year, yrs)]
                out[asset][key][gname] = {'events': minutes.responses(e, closes, m), 'placebo': minutes.responses(p, closes, m)}
    (ARTIFACTS / 'events').mkdir(parents=True, exist_ok=True)
    _write_json(ARTIFACTS / 'events' / 'results.json', out)
    print(json.dumps({'events': out['events']}))


def _cell(s):
    return f"{s['mean']:+.4f} [{s['lo']:+.4f}, {s['hi']:+.4f}]" if s and s['mean'] == s['mean'] else '—'


def stage_report(args):
    res = json.loads((ARTIFACTS / 'forecast' / 'results.json').read_text())
    lines = ['# B6 tables (generated; interpretation in RESULTS.md)', '', f"Tron block: {'included' if res['with_tron'] else 'not run'}", '',
             '## Forecast comparisons', '', forecast6.report(res['results'])]
    ep = ARTIFACTS / 'events' / 'results.json'
    if ep.exists():
        ev = json.loads(ep.read_text())
        lines += ['', f"## Minute-level events ({ev['events']} events)", '',
                  '| asset | events | group | kind | n | vol 5 | vol 15 | vol 30 | vol 60 | ret 1 | ret 5 | ret 15 | ret 30 | ret 60 | pre ret 15 |',
                  '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
        for asset, keys in ev.items():
            if asset == 'events':
                continue
            for key, groups in keys.items():
                for g, kinds in groups.items():
                    for kind, r in kinds.items():
                        lines.append(f"| {asset} | {key} | {g} | {kind} | {r['n']} | " + ' | '.join(_cell(r.get(k)) for k in
                                     ('vol5', 'vol15', 'vol30', 'vol60', 'ret1', 'ret5', 'ret15', 'ret30', 'ret60', 'pre_ret')) + ' |')
    (STUDY / 'TABLES.md').write_text('\n'.join(lines) + '\n')
    print(f'{len(lines)} lines')


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b6')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('pass')
    a.add_argument('--end', default=None)
    a.set_defaults(fn=stage_pass)
    for name, fn in (('labels', stage_labels), ('market', stage_market), ('tron', stage_tron), ('features', stage_features),
                     ('forecast', stage_forecast), ('events', stage_events), ('report', stage_report)):
        sub.add_parser(name).set_defaults(fn=fn)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests to verify they pass, then the full on-chain suite**

Run: `.venv/bin/python -m pytest tests/research/onchain_b6/test_cli6.py -q`
Expected: `3 passed`

Run: `.venv/bin/python -m pytest tests/research/onchain_b6 tests/research/onchain_b5 tests/research/onchain_b4 tests/research/onchain_b3 tests/research/onchain_b2 tests/research/onchain_b -q`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b6/cli.py tests/research/onchain_b6/test_cli6.py
git commit -m "feat(onchain-b6): stage runner with resumable labels-only pass, Tron stream and analyses

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Data, pass and analyses (B6-CP1 … CP4)

Operational.

- [ ] **Step 1 (CP1):** `cli labels` (freeze; print counts), `cli market` (1-minute bars, two assets); record counts in `STATE.md`, commit (`docs(onchain-b6): B6-CP1 labels frozen and minute bars stored`).
- [ ] **Step 2:** probe one heavy day (`reader6.read_day6` + `hourly6.day_rows` on 2025-06-02 with a fresh state) for time and peak; then launch

```bash
P=$PWD; systemd-run --user --unit onchain-b6-pass -p MemoryMax=6G -p Restart=no -p RestartForceExitStatus=75 -p RestartSec=60 \
  -p WorkingDirectory=$P -E OMP_NUM_THREADS=2 /usr/bin/systemd-inhibit --what=idle --who=onchain-b6 --why="B6 pass" --mode=block \
  $P/.venv/bin/python -m tradingagents.research.onchain_b6.cli pass
systemd-run --user --unit onchain-b6-tron -p MemoryMax=2G -p WorkingDirectory=$P $P/.venv/bin/python -m tradingagents.research.onchain_b6.cli tron
```
Expected: ≈ 25 h; relaunch on failure (resumes from the snapshot).
- [ ] **Step 3 (CP2):** when the pass ends: counts (days, unavailable, large transfers per year), Tron status; `cli features`; record and commit.
- [ ] **Step 4 (CP3):** `cli forecast` (systemd, 6 GiB), `cli events`, `cli report`; commit `TABLES.md` and `STATE.md`.
- [ ] **Step 5 (CP4):** write `RESULTS.md` (Q1–Q4 answers from `TABLES.md`, the pre-declared criteria applied as written, caveats); update `STATE.md`, memory note and the audit page; commit (`research(onchain-b6): B6-CP4 results`).

---

## Self-review

**Spec coverage:** §3 labels → Task 2; §4 pass, 4.1 → Task 4, 4.2–4.3 → Task 5, reader → Task 3, loop → Task 9; §5 features/comparison → Task 8; §6 minutes → Task 6; §7 Tron → Task 7; §8 PLAN.md → Task 1; §9 compute → Task 10; §10 layout → as listed; §11 tests → Tasks 2–9; §12 checkpoints → Task 10.

**Type consistency:** `reader6.Day6` fields used by `hourly6.day_rows`; `LabelState.begin_day/is_exchange/entity_of/in_class/observe/treasury_key/entity_names` used by `hourly6`; `structure6.hour_structure(src, dst, usd, is_ex_src, is_ex_dst, ent_src, ent_dst, bloom_contains, top_n)`; `hourly6.day_rows(day, d, state, bloom, cfg) -> (rows, large)` consumed by `cli.stage_pass`; large columns `ts, token, amount, direction, entity, cp_new` consumed by `minutes.select_events`; `forecast6.run_all(samples_by_track, cfg, with_tron)` consumes `dataset6.samples` output with `V6`, `V24`; `tron.run(post, labels_hex, state_path, out_path, cfg, sleep, stop_block)`.

**Review Focus coverage:** 1 → Task 2 `test_activation_is_day_after_first_observation` (+ Task 5 `test_observe_marks_first_seen_labels`); 2 → Task 4 `test_structure_degenerate_hours`; 3 → Task 5 `test_mint_burn_only_in_issuance`; 4 → Task 6 `test_response_alignment_and_placebo_gap`; 5 → Task 7 `test_stream_continues_partial_and_backs_off`.
