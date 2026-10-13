# Onchain B2 Weekly Screen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stream ETH transactions 2017–2026, build weekly activity, exchange/whale-flow and motif features, screen them with simple models for five targets on 2017–2024, and confirm the best configurations once on a sealed 2025–26 window.

**Architecture:** New subpackage `tradingagents/research/onchain_b2/` with one module per stage (source, labels, week build, market, targets, motif features, dataset, screen, holdout, CLI). Graph, matching, dictionary and MCM code is reused unchanged from `tradingagents/research/onchain_b/`. Every stage is idempotent per week or per run and writes JSON-lines logs; network access goes through injectable functions so tests never touch the network.

**Tech Stack:** Python 3.13 `.venv`, pyarrow 23 (S3 anonymous filesystem, compute), pandas 2.3, NumPy, scikit-learn 1.7 (Ridge, LogisticRegression, HistGradientBoosting), PyTorch CPU (MCM via onchain_b), pytest.

**Spec:** `docs/superpowers/specs/2026-10-13-onchain-b2-weekly-screen-design.md`

## Global Constraints

- Worktree `/home/malecada/master_thesis/TradingAgents-onchain-b`, branch `research/onchain-replication-b-2026-10-12`. Never modify Branch A paths (`research/onchain-paper-replication-2026-09-24/`, `tradingagents/research/onchain_replication/`) or Branch B's sealed results (`research/onchain-replication-b-2026-10-12/RESULT.md`, `FORENSICS.md`). `tradingagents/research/onchain_b/` is reused, not edited.
- Weeks: Monday-anchored UTC, `2017-01-02` … `2026-10-05` (510). Graph lag 1 day: a week is usable on day *d* iff its end (next Monday) ≤ *d*.
- Development: weekly decisions 2017-10-02 ≤ *m*, *m*+7 ≤ 2024-12-31 (378); daily 2017-10-02 ≤ *d*, *d*+1 ≤ 2024-12-31. Embargo decision 2024-12-30. Holdout: weekly 2025-01-06 ≤ *m*, *m*+7 ≤ 2026-10-12 (92); daily 2025-01-01 ≤ *d*, *d*+1 ≤ 2026-10-12.
- Dev code must never read prices or volumes after 2024-12-31; the holdout stage runs only with a committed, unmodified `research/onchain-b2-2026-10-13/selection.json`.
- K = 5,000, n_max = 32, dictionary seed 11 from weeks 2017-01-02 … 2018-12-24, 512 samples, 32 motifs; matching config from `onchain_b.config.load('matching')`.
- Deposit-like share 0.9 (inclusive); whales = 100 non-exchange addresses by ETH moved, ties by address ascending; top-share n = 100.
- Transforms: log1p / signed log1p / unchanged; z-score vs previous 8 weeks (≥ 6 present, ddof 0, zero std → 0) and one-week change; no raw levels.
- Screen: test years 2019–2024, purge 7 days weekly / 1 day daily; linear L2 grid {0.1, 1, 10, 100, 1000}, inner validation last 52 weeks / 365 days; HistGradientBoosting max_iter 300, learning_rate 0.03, max_leaf_nodes 7, min_samples_leaf 20, l2_regularization 1.0, random_state 11.
- Gate: pooled loss difference with 95 % circular block bootstrap (block 4 weekly / 14 daily, 2,000 draws, seed 20261013) entirely below 0 and lower loss in ≥ 4 of 6 years; ≤ 3 selected, ranked by interval upper end, ties prefer S3/S4. Holdout: one-sided bootstrap p, Holm at α = 0.05.
- Streaming retries: waits of 30 s then 120 s, then the day is unavailable. Units: `systemd-run --user -p MemoryMax=10G`; torch threads 2.
- Documentation impersonal (no "we/our"). Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Test command: `cd /home/malecada/master_thesis/TradingAgents-onchain-b && OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2 -q`.

## Review Focus

1. A date partition with several parquet part files → all parts read and concatenated, rows summed in the receipt (Task 2 `test_multiple_parts_concatenated`).
2. An address that only receives, never sends, in a week → present in the address table with zero outgoing (Task 4 `test_receive_only_address_has_zero_out`).
3. A 2025 date reaching the development loader → `ValueError`, never silently used (Task 5 `test_load_dev_refuses_sealed_dates`).
4. A week with no exchange-related transfers (or an empty label set) → role flows are 0.0, never `None`/NaN (Task 4 `test_role_flows_without_exchanges_are_zero`).
5. An unavailable day → week marker written, later weeks still built, samples needing that week excluded with a reason (Task 11 `test_unavailable_day_marks_week_and_continues`, Task 8 `test_unavailable_week_excluded_with_reason`).

---

### Task 1: Skeleton, configuration, research directory, periods

**Files:**
- Create: `tradingagents/research/onchain_b2/__init__.py`, `tradingagents/research/onchain_b2/config.py`, `tradingagents/research/onchain_b2/periods.py`
- Create: `research/onchain-b2-2026-10-13/config/b2.json`, `research/onchain-b2-2026-10-13/gates.json`, `research/onchain-b2-2026-10-13/CHARTER.md`, `research/onchain-b2-2026-10-13/STATE.md`
- Modify: `.gitignore` (append `/research_artifacts/onchain-b2/`)
- Test: `tests/research/onchain_b2/__init__.py`, `tests/research/onchain_b2/test_periods.py`

**Interfaces:**
- Produces: `config.ROOT`, `config.STUDY`, `config.ARTIFACTS` (Paths), `config.load() -> dict`; `periods.all_weeks() -> list[str]`, `periods.week_days(week) -> list[str]`, `periods.week_end(week) -> date`, `periods.latest_week_for(day: date, weeks: list[str]) -> str | None`, `periods.weekly_window(m: date) -> 'dev' | 'holdout' | None`, `periods.daily_window(d: date) -> 'dev' | 'holdout' | None`, `periods.dictionary_weeks() -> list[str]`, `periods.DEV_END: date`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b2/test_periods.py
from datetime import date, timedelta

from tradingagents.research.onchain_b2 import config, periods


def test_week_denominators():
    w = periods.all_weeks()
    assert len(w) == 510 and w[0] == '2017-01-02' and w[-1] == '2026-10-05'
    d = periods.dictionary_weeks()
    assert len(d) == 104 and d[-1] == '2018-12-24'


def test_lag_rule():
    weeks = periods.all_weeks()
    assert periods.latest_week_for(date(2017, 1, 8), weeks) is None
    assert periods.latest_week_for(date(2017, 1, 9), weeks) == '2017-01-02'
    assert periods.latest_week_for(date(2017, 1, 15), weeks) == '2017-01-02'
    assert periods.latest_week_for(date(2017, 1, 16), weeks) == '2017-01-09'


def test_windows_and_embargo():
    ms = [periods.week_end(w) for w in periods.all_weeks()]
    dev = [m for m in ms if periods.weekly_window(m) == 'dev']
    hold = [m for m in ms if periods.weekly_window(m) == 'holdout']
    assert len(dev) == 378 and dev[0] == date(2017, 10, 2) and dev[-1] == date(2024, 12, 23)
    assert len(hold) == 92 and hold[0] == date(2025, 1, 6) and hold[-1] == date(2026, 10, 5)
    assert periods.weekly_window(date(2024, 12, 30)) is None
    assert periods.daily_window(date(2024, 12, 30)) == 'dev' and periods.daily_window(date(2024, 12, 31)) is None
    assert periods.daily_window(date(2025, 1, 1)) == 'holdout' and periods.daily_window(date(2026, 10, 12)) is None


def test_frozen_numbers_and_ignore():
    c = config.load()
    assert c['k'] == 5000 and c['n_max'] == 32 and c['dictionary']['seed'] == 11
    assert c['gate']['draws'] == 2000 and c['gate']['min_year_wins'] == 4 and c['gate']['max_selected'] == 3
    assert '/research_artifacts/onchain-b2/' in (config.ROOT / '.gitignore').read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_periods.py -q`
Expected: collection error, `ModuleNotFoundError: tradingagents.research.onchain_b2`

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b2/__init__.py
"""Branch B2: weekly on-chain graph screen with a sealed 2025–26 holdout.

Design: docs/superpowers/specs/2026-10-13-onchain-b2-weekly-screen-design.md
"""
```

```python
# tradingagents/research/onchain_b2/config.py
"""Frozen B2 configuration (research/onchain-b2-2026-10-13/config/b2.json)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b2-2026-10-13'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b2'


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b2.json').read_text())
```

```python
# tradingagents/research/onchain_b2/periods.py
"""Weeks, the one-day graph lag and the development / holdout windows (spec §4.2)."""
from __future__ import annotations

import bisect
from datetime import date, timedelta
from functools import lru_cache

from .config import load

_C = load()
LAG = timedelta(days=_C['graph_lag_days'])
DEV_START = date.fromisoformat(_C['windows']['dev_start'])
DEV_END = date.fromisoformat(_C['windows']['dev_end'])
HOLD_START = date.fromisoformat(_C['windows']['holdout_start'])
HOLD_END = date.fromisoformat(_C['windows']['holdout_end'])


def mondays(first: str, last: str) -> list[str]:
    d, end, out = date.fromisoformat(first), date.fromisoformat(last), []
    assert d.weekday() == 0 and end.weekday() == 0
    while d <= end:
        out.append(d.isoformat())
        d += timedelta(days=7)
    return out


@lru_cache(maxsize=None)
def _all():
    return tuple(mondays(_C['weeks']['first'], _C['weeks']['last']))


def all_weeks() -> list[str]:
    return list(_all())


def dictionary_weeks() -> list[str]:
    return mondays(_C['dictionary']['first_week'], _C['dictionary']['last_week'])


def week_days(week: str) -> list[str]:
    start = date.fromisoformat(week)
    return [(start + timedelta(days=k)).isoformat() for k in range(7)]


def week_end(week: str) -> date:
    return date.fromisoformat(week) + timedelta(days=7)


def latest_week_for(day: date, weeks: list[str]) -> str | None:
    """Latest week whose end plus the lag is no later than the start of day+1."""
    ends = [week_end(w) + LAG for w in weeks]
    i = bisect.bisect_right(ends, day + timedelta(days=1))
    return weeks[i - 1] if i else None


def weekly_window(m: date) -> str | None:
    if DEV_START <= m and m + timedelta(days=7) <= DEV_END:
        return 'dev'
    if HOLD_START <= m and m + timedelta(days=7) <= HOLD_END:
        return 'holdout'
    return None


def daily_window(d: date) -> str | None:
    if DEV_START <= d and d + timedelta(days=1) <= DEV_END:
        return 'dev'
    if HOLD_START <= d and d + timedelta(days=1) <= HOLD_END:
        return 'holdout'
    return None
```

`research/onchain-b2-2026-10-13/config/b2.json`:

```json
{
 "k": 5000,
 "n_max": 32,
 "dictionary": {"seed": 11, "first_week": "2017-01-02", "last_week": "2018-12-24", "sample_count": 512, "size": 32},
 "weeks": {"first": "2017-01-02", "last": "2026-10-05"},
 "graph_lag_days": 1,
 "local_span_days": {"first": "2022-01-01", "last": "2024-12-31"},
 "windows": {"dev_start": "2017-10-02", "dev_end": "2024-12-31", "holdout_start": "2025-01-01", "holdout_end": "2026-10-12"},
 "s3": {"bucket": "aws-public-blockchain", "prefix": "v1.0/eth/transactions/date=", "region": "us-east-2",
        "https": "https://aws-public-blockchain.s3.us-east-2.amazonaws.com/", "retries": [30, 120]},
 "roles": {"deposit_share": 0.9, "whales": 100, "top_share_n": 100},
 "transforms": {"z_window": 8, "z_min": 6},
 "folds": {"test_years": [2019, 2020, 2021, 2022, 2023, 2024], "purge_days": {"weekly": 7, "daily": 1},
           "inner_len": {"weekly": 52, "daily": 365}},
 "models": {"alphas": [0.1, 1, 10, 100, 1000],
            "trees": {"max_iter": 300, "learning_rate": 0.03, "max_leaf_nodes": 7, "min_samples_leaf": 20,
                      "l2_regularization": 1.0, "random_state": 11}},
 "gate": {"block": {"weekly": 4, "daily": 14}, "draws": 2000, "seed": 20261013, "min_year_wins": 4,
          "max_selected": 3, "alpha": 0.05},
 "market": {"price_start": "2016-12-01", "volume_start": "2017-08-17", "end": "2026-10-12"},
 "labels": {"spellbook": {"repo": "duneanalytics/spellbook", "branch": "main",
                          "path": "dbt_subprojects/hourly_spellbook/models/_sector/cex/addresses/chains/cex_evms_addresses.sql"},
            "ethlabels": {"repo": "dawsbot/eth-labels", "branch": "master", "path": "src/mainnet/exchange/all.json"}}
}
```

`research/onchain-b2-2026-10-13/gates.json`:

```json
{
 "registered": "2026-10-13",
 "spec": "docs/superpowers/specs/2026-10-13-onchain-b2-weekly-screen-design.md",
 "targets": {"T1": "daily next-day direction", "T2": "weekly next-week direction", "T3": "weekly next-week log return",
             "T4": "weekly next-week log realised volatility", "T5": "weekly next-week log Binance quote volume"},
 "comparisons": [["S1", "S0"], ["S2", "S1"], ["S3", "S1"], ["S4", "S2"]],
 "families": ["linear", "trees"],
 "screen_gate": "pooled loss difference 95% circular block-bootstrap interval entirely below 0 AND lower loss in >= 4 of 6 test years (2019-2024)",
 "selection": "at most 3 passing configurations by interval upper end; ties prefer S3/S4; selection.json committed before any holdout read",
 "holdout_gate": "refit on all development samples; one-sided bootstrap p of loss difference; Holm-adjusted p < 0.05",
 "sealed_window": "weekly decisions 2025-01-06..2026-10-05; daily decisions 2025-01-01..2026-10-11",
 "no_tuning": "no feature, model or threshold change after any holdout read"
}
```

`research/onchain-b2-2026-10-13/CHARTER.md`:

```markdown
# Branch B2 charter — weekly on-chain graph screen

Registered 2026-10-13 before any B2 capture or outcome. Spec:
`docs/superpowers/specs/2026-10-13-onchain-b2-weekly-screen-design.md`; frozen
numbers in `config/b2.json`; decision rules in `gates.json`.

Questions: does on-chain activity (F1), exchange/whale role flow (F3a) or
motif structure (F2, F3b) improve price-only (F0) forecasts of next-day and
next-week ETH direction, next-week return, realised volatility and volume?

Development 2017-10 → 2024 with yearly walk-forward (2019–2024); sealed holdout
2025-01-06 → 2026-10-05 (92 weekly decisions), opened once, only for the
configurations committed in `selection.json`. Branch B's spent 2024 year is
development data here. No raw transaction storage; free public sources only.
```

`research/onchain-b2-2026-10-13/STATE.md`:

```markdown
# Branch B2 state

2026-10-13 — Charter, configuration and gates registered. No capture, no feature,
no fit. Next: implement `tradingagents/research/onchain_b2` per
`docs/superpowers/plans/2026-10-13-onchain-b2-weekly-screen.md`.
```

Append to `.gitignore`:

```
# Branch B2 artifacts (weeks, graphs, MCM, features, sealed market data, logs)
/research_artifacts/onchain-b2/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_periods.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b2 tests/research/onchain_b2 research/onchain-b2-2026-10-13 .gitignore
git commit -m "feat(onchain-b2): register B2 charter, config, gates and window calendar"
```

---

### Task 2: Day source (S3 streaming, local spans, receipts, retries)

**Files:**
- Create: `tradingagents/research/onchain_b2/s3source.py`
- Test: `tests/research/onchain_b2/test_s3source.py`

**Interfaces:**
- Consumes: `config.load()`; `onchain_b.sources.{load_plan, day_manifest, read_day, COLUMNS}`.
- Produces: `COLUMNS` (tuple of 6 column names), `DayUnavailable(RuntimeError)` with `.day`, `.errors`; `read_s3_day(day, *, filesystem, root, https, head_fn) -> (pa.Table, dict)`; `read_day(day, *, scratch, filesystem=None, head_fn=None, sleep=time.sleep, cfg=None) -> (pa.Table, dict)`; `check_timestamps(table, day) -> None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b2/test_s3source.py
import numpy as np
import pyarrow as pa
import pyarrow.fs as pafs
import pyarrow.parquet as pq
import pytest

from tradingagents.research.onchain_b2 import s3source as S

PREFIX = 'v1.0/eth/transactions/date='


def _table(day, n, offset=0):
    base = int(np.datetime64(day, 'ns').astype('int64'))
    return pa.table({'hash': ['0x' + f'{i + offset:064x}' for i in range(n)],
                     'block_timestamp': pa.array([base + i * 10**9 for i in range(n)], pa.timestamp('ns')),
                     'from_address': ['0x' + 'a' * 40] * n, 'to_address': ['0x' + 'b' * 40] * n,
                     'value': [1e18] * n, 'receipt_status': [1] * n})


def _write(root, day, parts):
    d = root / f'{PREFIX}{day}'
    d.mkdir(parents=True)
    for k, t in enumerate(parts):
        pq.write_table(t, d / f'part-{k:05d}.parquet')


def _head(url):
    return {'etag': '"e"', 'size': None}


def test_reads_projected_columns_with_receipt(tmp_path):
    _write(tmp_path, '2019-06-03', [_table('2019-06-03', 5)])
    t, r = S.read_s3_day('2019-06-03', filesystem=pafs.LocalFileSystem(), root=str(tmp_path), https='https://x/', head_fn=_head)
    assert t.num_rows == 5 and t.column_names == list(S.COLUMNS)
    assert r['day'] == '2019-06-03' and r['source'] == 's3' and r['rows'] == 5
    assert r['files'][0]['key'].endswith('date=2019-06-03/part-00000.parquet') and r['files'][0]['etag'] == '"e"'


def test_multiple_parts_concatenated(tmp_path):
    _write(tmp_path, '2019-06-03', [_table('2019-06-03', 3), _table('2019-06-03', 4, offset=100)])
    t, r = S.read_s3_day('2019-06-03', filesystem=pafs.LocalFileSystem(), root=str(tmp_path), https='https://x/', head_fn=_head)
    assert t.num_rows == 7 and r['rows'] == 7 and len(r['files']) == 2


def test_timestamp_outside_day_rejected(tmp_path):
    _write(tmp_path, '2019-06-03', [_table('2019-06-04', 2)])
    with pytest.raises(ValueError, match='outside'):
        S.read_s3_day('2019-06-03', filesystem=pafs.LocalFileSystem(), root=str(tmp_path), https='https://x/', head_fn=_head)


def test_retries_then_unavailable(monkeypatch):
    waits, calls = [], []

    def boom(*a, **k):
        calls.append(1)
        raise OSError('network down')

    monkeypatch.setattr(S, 'read_s3_day', boom)
    with pytest.raises(S.DayUnavailable) as e:
        S.read_day('2019-06-03', scratch='.', filesystem=object(), head_fn=_head, sleep=waits.append)
    assert waits == [30, 120] and len(calls) == 3 and e.value.day == '2019-06-03' and len(e.value.errors) == 3


def test_retry_recovers(monkeypatch):
    seq = iter([OSError('x'), ('table', {'rows': 1})])

    def flaky(*a, **k):
        v = next(seq)
        if isinstance(v, Exception):
            raise v
        return v

    monkeypatch.setattr(S, 'read_s3_day', flaky)
    waits = []
    assert S.read_day('2019-06-03', scratch='.', filesystem=object(), head_fn=_head, sleep=waits.append) == ('table', {'rows': 1})
    assert waits == [30]


def test_local_window_dispatches_to_retained_spans(monkeypatch):
    monkeypatch.setattr(S, 'read_local_day', lambda day, scratch: ('local', {'day': day}))
    monkeypatch.setattr(S, 'read_s3_day', lambda *a, **k: pytest.fail('S3 used for a local-span day'))
    assert S.read_day('2023-06-05', scratch='.', sleep=lambda s: None)[0] == 'local'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_s3source.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b2/s3source.py
"""One UTC day of ETH transactions: streamed from the AWS public bucket, or read from
Branch B's retained hash-verified spans for 2022–2024. Only six columns are read;
nothing raw is written to disk."""
from __future__ import annotations

import time
import urllib.request

import numpy as np
import pyarrow as pa
import pyarrow.fs as pafs
import pyarrow.parquet as pq

from . import config

COLUMNS = ('hash', 'block_timestamp', 'from_address', 'to_address', 'value', 'receipt_status')


class DayUnavailable(RuntimeError):
    def __init__(self, day, errors):
        super().__init__(f'{day} unavailable after {len(errors)} attempts: {errors[-1] if errors else ""}')
        self.day, self.errors = day, errors


def https_head(url, timeout=30):
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'onchain-b2-research'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        size = r.headers.get('Content-Length')
        return {'etag': r.headers.get('ETag'), 'size': int(size) if size is not None else None}


def check_timestamps(table, day):
    start = np.datetime64(day, 'ns')
    ts = table.column('block_timestamp').to_numpy().astype('datetime64[ns]')
    if len(ts) and ((ts < start).any() or (ts >= start + np.timedelta64(1, 'D')).any()):
        raise ValueError(f'block_timestamp outside {day}')


def read_s3_day(day, *, filesystem, root, https, head_fn):
    prefix = config.load()['s3']['prefix']
    infos = [f for f in filesystem.get_file_info(pafs.FileSelector(f'{root}/{prefix}{day}'))
             if f.path.endswith('.parquet')]
    if not infos:
        raise FileNotFoundError(f'no parquet parts for {day}')
    tables, files = [], []
    for info in sorted(infos, key=lambda f: f.path):
        with filesystem.open_input_file(info.path) as fh:
            t = pq.ParquetFile(fh).read(columns=list(COLUMNS))
        key = info.path[len(root):].lstrip('/')
        head = head_fn(https + key)
        if head.get('size') is not None and head['size'] != info.size:
            raise ValueError(f'size mismatch for {key}')
        files.append({'key': key, 'size': info.size, 'etag': head.get('etag'), 'rows': t.num_rows})
        tables.append(t.select(list(COLUMNS)))
    table = pa.concat_tables(tables)
    check_timestamps(table, day)
    return table, {'day': day, 'source': 's3', 'rows': table.num_rows, 'files': files}


def read_local_day(day, scratch):
    from ..onchain_b import sources
    manifest = sources.day_manifest(sources.load_plan(), day)
    table = sources.read_day(manifest, scratch, sources.COLUMNS)
    check_timestamps(table, day)
    return table, {'day': day, 'source': 'local', 'rows': table.num_rows, 'object': manifest['object'].get('key')}


def _s3(cfg):
    return pafs.S3FileSystem(anonymous=True, region=cfg['region'])


def read_day(day, *, scratch, filesystem=None, head_fn=None, sleep=time.sleep, cfg=None):
    c = cfg or config.load()
    s = c['s3']
    local = c['local_span_days']['first'] <= day <= c['local_span_days']['last']

    def once():
        if local:
            return read_local_day(day, scratch)
        return read_s3_day(day, filesystem=filesystem or _s3(s), root=s['bucket'], https=s['https'],
                           head_fn=head_fn or https_head)

    waits, errors = list(s['retries']), []
    for attempt in range(len(waits) + 1):
        try:
            return once()
        except Exception as e:        # network, decode or integrity failure: retry, then mark unavailable
            errors.append(repr(e))
            if attempt < len(waits):
                sleep(waits[attempt])
    raise DayUnavailable(day, errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_s3source.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b2/s3source.py tests/research/onchain_b2/test_s3source.py
git commit -m "feat(onchain-b2): stream one day from S3 or retained spans with receipts and retries"
```

---

### Task 3: Exchange labels

**Files:**
- Create: `tradingagents/research/onchain_b2/labels.py`
- Test: `tests/research/onchain_b2/test_labels.py`

**Interfaces:**
- Produces: `parse_spellbook(text) -> (dict[str, dict], int unparsed)`; `parse_ethlabels(text) -> dict[str, dict]`; `union(spell, eth) -> dict[str, dict]` (keys lowercase `0x…`, values `{'name', 'added', 'sources'}`); `fetch_and_store(get, out_dir, cfg=None) -> dict meta`; `load(path) -> dict`; `exchange_array(path) -> pa.Array` (sorted lowercase strings).

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b2/test_labels.py
import json

from tradingagents.research.onchain_b2 import labels as L

SPELL = """
SELECT address, cex_name, distinct_name, added_by, added_date
FROM (VALUES
    -- Binance
    (0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be, 'Binance', 'Binance 1', 'hildobby', date '2022-08-28')
    , (0xD551234AE421E3BCBA99A0DA6D736074F22192FF, 'Binance', 'Binance 2', 'hildobby', date '2022-08-28')
    , (0x71660c4005ba85c37ccec55d0c4493e66fe775d3, 'Coinbase', 'Coinbase 1', 'hildobby', date '2022-11-14')
    , (0x1234, 'Broken', 'x', 'y', date '2022-01-01')
    ) AS x (address, cex_name, distinct_name, added_by, added_date)
"""
ETH = json.dumps([{'address': '0x71660c4005ba85c37ccec55d0c4493e66fe775d3', 'nameTag': 'Coinbase 1'},
                  {'address': '0xABCDEFabcdefABCDEFabcdefABCDEFabcdefABCD', 'nameTag': ''}])


def test_parse_spellbook_lowercases_and_counts_unparsed():
    rows, unparsed = L.parse_spellbook(SPELL)
    assert set(rows) == {'0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be', '0xd551234ae421e3bcba99a0da6d736074f22192ff',
                         '0x71660c4005ba85c37ccec55d0c4493e66fe775d3'}
    assert rows['0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be'] == {'name': 'Binance', 'added': '2022-08-28'}
    assert unparsed == 1


def test_union_keeps_sources():
    u = L.union(L.parse_spellbook(SPELL)[0], L.parse_ethlabels(ETH))
    assert len(u) == 4
    assert u['0x71660c4005ba85c37ccec55d0c4493e66fe775d3']['sources'] == ['ethlabels', 'spellbook']
    assert u['0xabcdefabcdefabcdefabcdefabcdefabcdefabcd']['sources'] == ['ethlabels']


def test_fetch_and_store_pins_commits_and_hashes(tmp_path):
    def get(url):
        if url.endswith('/commits/main'):
            return json.dumps({'sha': 's' * 40}).encode()
        if url.endswith('/commits/master'):
            return json.dumps({'sha': 'e' * 40}).encode()
        if 'spellbook/' + 's' * 40 in url:
            return SPELL.encode()
        if 'eth-labels/' + 'e' * 40 in url:
            return ETH.encode()
        raise AssertionError(url)

    meta = L.fetch_and_store(get, tmp_path)
    assert meta['count'] == 4 and meta['sources']['spellbook']['commit'] == 's' * 40 and meta['sources']['spellbook']['unparsed'] == 1
    assert len(meta['sources']['ethlabels']['sha256']) == 64
    arr = L.exchange_array(tmp_path / 'labels.json')
    assert arr.to_pylist() == sorted(arr.to_pylist()) and len(arr) == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_labels.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b2/labels.py
"""Exchange-address labels: union of Dune Spellbook `cex_evms_addresses` (BSL 1.1,
research use) and dawsbot/eth-labels `mainnet/exchange` (MIT), pinned to commits.
The list itself stays in gitignored artifacts; commits record sources and hashes."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pyarrow as pa

from . import config

_ROW = re.compile(r"\(\s*(0x[0-9a-fA-F]{40})\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*date\s*'(\d{4}-\d{2}-\d{2})'\s*\)")


def parse_spellbook(text):
    rows = {}
    for m in _ROW.finditer(text):
        rows[m.group(1).lower()] = {'name': m.group(2), 'added': m.group(5)}
    candidates = len(re.findall(r'\(\s*0x', text))
    return rows, candidates - len(_ROW.findall(text))


def parse_ethlabels(text):
    out = {}
    for r in json.loads(text):
        a = r['address'].lower()
        if re.fullmatch(r'0x[0-9a-f]{40}', a):
            out[a] = {'name': r.get('nameTag') or ''}
    return out


def union(spell, eth):
    out = {}
    for src, rows in (('ethlabels', eth), ('spellbook', spell)):
        for a, v in rows.items():
            e = out.setdefault(a, {'name': '', 'added': None, 'sources': []})
            e['sources'].append(src)
            e['name'] = e['name'] or v.get('name', '')
            e['added'] = e['added'] or v.get('added')
    for e in out.values():
        e['sources'] = sorted(e['sources'])
    return out


def _commit(get, repo, branch):
    return json.loads(get(f'https://api.github.com/repos/{repo}/commits/{branch}'))['sha']


def fetch_and_store(get, out_dir, cfg=None):
    c = (cfg or config.load())['labels']
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta, raw = {'sources': {}}, {}
    for name in ('spellbook', 'ethlabels'):
        s = c[name]
        sha = _commit(get, s['repo'], s['branch'])
        url = f"https://raw.githubusercontent.com/{s['repo']}/{sha}/{s['path']}"
        body = get(url)
        raw[name] = body.decode()
        (out_dir / f'{name}.raw').write_bytes(body)
        meta['sources'][name] = {'repo': s['repo'], 'commit': sha, 'path': s['path'], 'url': url,
                                 'sha256': hashlib.sha256(body).hexdigest()}
    spell, unparsed = parse_spellbook(raw['spellbook'])
    eth = parse_ethlabels(raw['ethlabels'])
    meta['sources']['spellbook'].update(count=len(spell), unparsed=unparsed)
    meta['sources']['ethlabels'].update(count=len(eth))
    u = union(spell, eth)
    body = json.dumps(u, sort_keys=True, indent=0).encode()
    (out_dir / 'labels.json').write_bytes(body)
    meta.update(count=len(u), sha256=hashlib.sha256(body).hexdigest())
    (out_dir / 'meta.json').write_text(json.dumps(meta, indent=1, sort_keys=True))
    return meta


def load(path):
    return json.loads(Path(path).read_text())


def exchange_array(path):
    return pa.array(sorted(load(path)), pa.string())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_labels.py -q`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b2/labels.py tests/research/onchain_b2/test_labels.py
git commit -m "feat(onchain-b2): pinned union of public exchange-address labels"
```

---

### Task 4: Week build (activity F1, role flows F3a, whales, top-K graph)

**Files:**
- Create: `tradingagents/research/onchain_b2/weekbuild.py`
- Test: `tests/research/onchain_b2/test_weekbuild.py`

**Interfaces:**
- Consumes: `onchain_b.weekly.{admitted_events, aggregate_pairs, top_k_subgraph, WeekGraph}`; `config.load()`.
- Produces: `address_table(pairs) -> pa.Table[address, out_value, out_count, in_value, in_count]`; `f1_features(events, pairs, addr, counters, top_n) -> dict` (keys `f1_*`); `role_flows(pairs, addr, exchanges, deposit_share, n_whales) -> (dict f3a_*, list[str] whales)`; `build_week(week, day_tables, exchanges, cfg=None) -> (summary: dict, graph: WeekGraph)`. F1 keys: `f1_transfers, f1_failed_share, f1_zero_share, f1_null_share, f1_active, f1_senders, f1_receivers, f1_eth_moved, f1_median_size, f1_p90_size, f1_top_share, f1_self_share, f1_edges, f1_mean_degree`. F3a keys: `f3a_ex_in_value, f3a_ex_in_count, f3a_ex_out_value, f3a_ex_out_count, f3a_ex_net_value, f3a_dep_count, f3a_dep_received_value, f3a_whale_net_to_ex, f3a_whale_share, f3a_ex_senders`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b2/test_weekbuild.py
import pyarrow as pa
import pytest

from tradingagents.research.onchain_b.weekly import admitted_events, aggregate_pairs
from tradingagents.research.onchain_b2 import weekbuild as WB

A, B, C, D, E1, E2 = ('0x' + c * 40 for c in 'abcdef')
EX = pa.array(sorted([E1, E2]))
ROWS = [(A, E1, 9.0, 1), (A, C, 1.0, 1), (B, E1, 8.9, 1), (B, C, 1.1, 1), (C, A, 5.0, 1),
        (E1, D, 4.0, 1), (E1, E2, 100.0, 1), (D, D, 2.0, 1), (A, B, 3.0, 0), (B, A, 0.0, 1)]


def _day(rows):
    return pa.table({'hash': ['0x' + f'{i:064x}' for i in range(len(rows))],
                     'block_timestamp': pa.array([0] * len(rows), pa.timestamp('ns')),
                     'from_address': [r[0] for r in rows], 'to_address': [r[1] for r in rows],
                     'value': [r[2] * 1e18 for r in rows], 'receipt_status': [r[3] for r in rows]})


def _week():
    ev, c = admitted_events(_day(ROWS))
    pairs = aggregate_pairs([ev])
    return ev, pairs, WB.address_table(pairs), [c]


def test_f1_activity():
    ev, pairs, addr, counters = _week()
    f = WB.f1_features(ev, pairs, addr, counters, top_n=2)
    assert f['f1_transfers'] == 8 and f['f1_failed_share'] == pytest.approx(0.1) and f['f1_zero_share'] == pytest.approx(0.1)
    assert f['f1_null_share'] == 0 and f['f1_active'] == 6 and f['f1_senders'] == 5 and f['f1_receivers'] == 5
    assert f['f1_eth_moved'] == pytest.approx(131.0) and f['f1_median_size'] == pytest.approx(4.5)
    assert f['f1_p90_size'] == pytest.approx(36.3) and f['f1_self_share'] == pytest.approx(1 / 8)
    assert f['f1_top_share'] == pytest.approx(221.9 / 262) and f['f1_edges'] == 8 and f['f1_mean_degree'] == pytest.approx(8 / 6)


def test_role_flows_deposit_boundary_and_whales():
    ev, pairs, addr, _ = _week()
    f, whales = WB.role_flows(pairs, addr, EX, deposit_share=0.9, n_whales=2)
    assert f['f3a_ex_in_value'] == pytest.approx(17.9) and f['f3a_ex_in_count'] == 2
    assert f['f3a_ex_out_value'] == pytest.approx(4.0) and f['f3a_ex_out_count'] == 1
    assert f['f3a_ex_net_value'] == pytest.approx(13.9)
    assert f['f3a_dep_count'] == 1                          # A sends exactly 90 % to E (inclusive); B sends 89 %
    assert f['f3a_dep_received_value'] == pytest.approx(5.0)  # C -> A
    assert f['f3a_ex_senders'] == 2                         # B -> E1, C -> A (A itself is deposit-like)
    assert whales == [A, B]
    assert f['f3a_whale_net_to_ex'] == pytest.approx(17.9) and f['f3a_whale_share'] == pytest.approx(25 / 262)


def test_receive_only_address_has_zero_out():
    _, _, addr, _ = _week()
    row = {r['address']: r for r in addr.to_pylist()}[E2]
    assert row['out_value'] == 0 and row['out_count'] == 0 and row['in_value'] == pytest.approx(100.0)


def test_role_flows_without_exchanges_are_zero():
    ev, pairs, addr, _ = _week()
    f, whales = WB.role_flows(pairs, addr, pa.array([], pa.string()), deposit_share=0.9, n_whales=2)
    assert all(isinstance(v, (int, float)) and v == v for v in f.values())
    assert f['f3a_ex_in_value'] == 0.0 and f['f3a_dep_count'] == 0 and f['f3a_whale_net_to_ex'] == 0.0
    assert whales == [E1, E2]                                # with no labels, every address is non-exchange


def test_whale_ties_break_by_address():
    rows = [(B, C, 5.0, 1), (A, C, 5.0, 1)]
    ev, _ = admitted_events(_day(rows))
    pairs = aggregate_pairs([ev])
    _, whales = WB.role_flows(pairs, WB.address_table(pairs), EX, 0.9, 2)
    assert whales == [C, A]                                  # C 10; A and B tie at 5 → A first


def test_build_week_summary_and_graph():
    summary, g = WB.build_week('2019-06-03', [_day(ROWS)], EX, {'k': 3, 'roles': {'deposit_share': 0.9, 'whales': 2, 'top_share_n': 2}})
    assert summary['week'] == '2019-06-03' and summary['f1']['f1_transfers'] == 8 and summary['whales'] == [A, B]
    assert g.n == 3 and summary['graph']['k_effective'] == 3 and summary['counters'][0]['rows'] == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_weekbuild.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b2/weekbuild.py
"""One week: admitted events → ordered-pair aggregates → activity (F1), exchange/whale
role flows (F3a) and the top-K graph used for motifs (spec §5.2–5.3)."""
from __future__ import annotations

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

from ..onchain_b.weekly import admitted_events, aggregate_pairs, top_k_subgraph
from . import config


def _sum(x):
    v = pc.sum(x).as_py()
    return float(v) if v is not None else 0.0


def _sums(pairs, key, prefix):
    g = pairs.group_by(key).aggregate([('value_eth', 'sum'), ('count', 'sum')])
    return pa.table({'address': g[key], f'{prefix}_value': g['value_eth_sum'], f'{prefix}_count': g['count_sum']})


def address_table(pairs):
    t = _sums(pairs, 'src', 'out').join(_sums(pairs, 'dst', 'in'), keys='address', join_type='full outer')
    cols = {'address': t['address']}
    for name in ('out_value', 'out_count', 'in_value', 'in_count'):
        cols[name] = pc.fill_null(t[name], 0)
    return pa.table(cols)


def f1_features(events, pairs, addr, counters, top_n):
    rows = sum(c['rows'] for c in counters)
    n = events.num_rows
    vol = addr['out_value'].to_numpy() + addr['in_value'].to_numpy()
    q = pc.quantile(events['value_eth'], q=[0.5, 0.9], interpolation='linear').to_pylist()
    selfs = int(pc.sum(pc.cast(pc.equal(events['from_address'], events['to_address']), pa.int64())).as_py() or 0)
    active = addr.num_rows
    return {'f1_transfers': n,
            'f1_failed_share': sum(c['failed'] for c in counters) / rows,
            'f1_zero_share': sum(c['zero_value'] for c in counters) / rows,
            'f1_null_share': sum(c['null_recipient'] for c in counters) / rows,
            'f1_active': active,
            'f1_senders': int(pc.count_distinct(pairs['src']).as_py()),
            'f1_receivers': int(pc.count_distinct(pairs['dst']).as_py()),
            'f1_eth_moved': _sum(events['value_eth']),
            'f1_median_size': float(q[0]), 'f1_p90_size': float(q[1]),
            'f1_top_share': float(np.sort(vol)[::-1][:top_n].sum() / vol.sum()),
            'f1_self_share': selfs / n,
            'f1_edges': pairs.num_rows,
            'f1_mean_degree': pairs.num_rows / active}


def role_flows(pairs, addr, exchanges, deposit_share, n_whales):
    src_ex = pc.is_in(pairs['src'], value_set=exchanges)
    dst_ex = pc.is_in(pairs['dst'], value_set=exchanges)
    val, cnt = pairs['value_eth'], pairs['count']
    inflow = pc.and_(pc.invert(src_ex), dst_ex)
    outflow = pc.and_(src_ex, pc.invert(dst_ex))
    f = {'f3a_ex_in_value': _sum(pc.filter(val, inflow)), 'f3a_ex_in_count': int(_sum(pc.filter(cnt, inflow))),
         'f3a_ex_out_value': _sum(pc.filter(val, outflow)), 'f3a_ex_out_count': int(_sum(pc.filter(cnt, outflow)))}
    f['f3a_ex_net_value'] = f['f3a_ex_in_value'] - f['f3a_ex_out_value']

    # deposit-like: non-exchange, >= 1 transfer to E, >= deposit_share of outgoing ETH sent to E
    to_ex = pairs.filter(inflow).group_by('src').aggregate([('value_eth', 'sum')])
    to_ex = pa.table({'address': to_ex['src'], 'to_ex': to_ex['value_eth_sum']})
    a = addr.join(to_ex, keys='address', join_type='left outer')
    a_addr = np.asarray(a['address'].to_pylist(), dtype=object)
    a_out = a['out_value'].to_numpy()
    a_vol = a_out + a['in_value'].to_numpy()
    a_to_ex = pc.fill_null(a['to_ex'], 0.0).to_numpy()
    a_is_ex = np.asarray(pc.is_in(a['address'], value_set=exchanges).to_pylist(), dtype=bool)
    dep_mask = (~a_is_ex) & (a_to_ex > 0) & (a_to_ex >= deposit_share * a_out)
    deposits = pa.array(sorted(a_addr[dep_mask].tolist()), pa.string())
    src_dep = pc.is_in(pairs['src'], value_set=deposits)
    dst_dep = pc.is_in(pairs['dst'], value_set=deposits)
    src_other = pc.and_(pc.invert(src_ex), pc.invert(src_dep))
    f['f3a_dep_count'] = int(dep_mask.sum())
    f['f3a_dep_received_value'] = _sum(pc.filter(val, pc.and_(dst_dep, src_other)))
    to_e_or_d = pc.and_(pc.or_(dst_ex, dst_dep), src_other)
    f['f3a_ex_senders'] = int(pc.count_distinct(pc.filter(pairs['src'], to_e_or_d)).as_py())

    # whales: largest ETH moved among non-exchange addresses, ties by address
    cand = np.flatnonzero(~a_is_ex)
    order = cand[np.lexsort((a_addr[cand].astype(str), -a_vol[cand]))][:n_whales]
    whales = a_addr[order].tolist()
    w = pa.array(whales, pa.string())
    src_w, dst_w = pc.is_in(pairs['src'], value_set=w), pc.is_in(pairs['dst'], value_set=w)
    f['f3a_whale_net_to_ex'] = _sum(pc.filter(val, pc.and_(src_w, dst_ex))) - _sum(pc.filter(val, pc.and_(src_ex, dst_w)))
    f['f3a_whale_share'] = float(a_vol[order].sum() / a_vol.sum()) if a_vol.sum() > 0 else 0.0
    return f, whales


def build_week(week, day_tables, exchanges, cfg=None):
    c = cfg or config.load()
    r = c['roles']
    evs, counters = zip(*(admitted_events(t) for t in day_tables))
    events = pa.concat_tables(evs)
    pairs = aggregate_pairs(list(evs))
    addr = address_table(pairs)
    f1 = f1_features(events, pairs, addr, list(counters), r['top_share_n'])
    f3a, whales = role_flows(pairs, addr, exchanges, r['deposit_share'], r['whales'])
    graph = top_k_subgraph(pairs, c['k'], week)
    summary = {'week': week, 'counters': list(counters), 'f1': f1, 'f3a': f3a, 'whales': whales,
               'graph': dict(graph.summary)}
    return summary, graph
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_weekbuild.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b2/weekbuild.py tests/research/onchain_b2/test_weekbuild.py
git commit -m "feat(onchain-b2): weekly activity, exchange/whale role flows and top-K graph"
```

---

### Task 5: Market data (Coin Metrics close, Binance volume, sealed split)

**Files:**
- Create: `tradingagents/research/onchain_b2/market.py`
- Test: `tests/research/onchain_b2/test_market.py`

**Interfaces:**
- Produces: `http_get(url, timeout=60) -> bytes`; `fetch_coinmetrics(get, start: date, end: date) -> (dict[date, float], list[bytes])`; `fetch_binance(get, start: date, end: date) -> (dict[date, float], list[bytes])`; `store(prices, volumes, pages: dict[str, list[bytes]], out_dir, cutoff: date) -> dict`; `load_dev(path, cutoff: date) -> (prices, volumes)`; `load_all(dev_path, sealed_path) -> (prices, volumes)`. Paths: `out_dir/market/dev.json`, `out_dir/sealed/market_sealed.json`, `out_dir/sealed/raw/<sha256>.json`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b2/test_market.py
import json
from datetime import date, datetime, timezone

import pytest

from tradingagents.research.onchain_b2 import market as Mk


def _ms(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)


def test_coinmetrics_pages():
    p1 = {'data': [{'time': '2024-12-30T00:00:00.000000000Z', 'PriceUSD': '3400.5'}], 'next_page_url': 'NEXT'}
    p2 = {'data': [{'time': '2025-01-02T00:00:00.000000000Z', 'PriceUSD': '3500.0'}]}
    pages = {'NEXT': json.dumps(p2).encode()}
    prices, raw = Mk.fetch_coinmetrics(lambda u: pages.get(u, json.dumps(p1).encode()), date(2024, 12, 30), date(2025, 1, 2))
    assert prices == {date(2024, 12, 30): 3400.5, date(2025, 1, 2): 3500.0} and len(raw) == 2


def test_binance_quote_volume_and_range():
    rows = [[_ms(date(2024, 12, 31)), '1', '1', '1', '1', '9', 0, '1000.5', 1, '0', '0', '0'],
            [_ms(date(2025, 1, 1)), '1', '1', '1', '1', '9', 0, '2000.0', 1, '0', '0', '0']]
    vols, raw = Mk.fetch_binance(lambda u: json.dumps(rows).encode(), date(2024, 12, 31), date(2025, 1, 1))
    assert vols == {date(2024, 12, 31): 1000.5, date(2025, 1, 1): 2000.0} and len(raw) == 1


def test_store_splits_at_cutoff(tmp_path):
    prices = {date(2024, 12, 31): 1.0, date(2025, 1, 1): 2.0}
    vols = {date(2024, 12, 31): 10.0, date(2025, 1, 1): 20.0}
    Mk.store(prices, vols, {'coinmetrics': [b'{}'], 'binance': [b'[]']}, tmp_path, date(2024, 12, 31))
    p, v = Mk.load_dev(tmp_path / 'market' / 'dev.json', date(2024, 12, 31))
    assert p == {date(2024, 12, 31): 1.0} and v == {date(2024, 12, 31): 10.0}
    pa_, va = Mk.load_all(tmp_path / 'market' / 'dev.json', tmp_path / 'sealed' / 'market_sealed.json')
    assert pa_[date(2025, 1, 1)] == 2.0 and va[date(2025, 1, 1)] == 20.0
    assert '2025-01-01' not in (tmp_path / 'market' / 'dev.json').read_text()


def test_load_dev_refuses_sealed_dates(tmp_path):
    f = tmp_path / 'dev.json'
    f.write_text(json.dumps({'prices': {'2025-01-01': 1.0}, 'volumes': {}}))
    with pytest.raises(ValueError, match='sealed'):
        Mk.load_dev(f, date(2024, 12, 31))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_market.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b2/market.py
"""Daily ETH close (Coin Metrics community PriceUSD) and volume (Binance ETHUSDT quote
volume). Dates after the development cutoff are written only to the sealed directory."""
from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

CM = ('https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets=eth&metrics=PriceUSD'
      '&frequency=1d&start_time={start}&end_time={end}&page_size=10000')
BN = 'https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1d&startTime={ms}&limit=1000'
DAY_MS = 86_400_000


def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers={'User-Agent': 'onchain-b2-research'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_coinmetrics(get, start, end):
    url, out, pages = CM.format(start=start.isoformat(), end=end.isoformat()), {}, []
    while url:
        raw = get(url)
        pages.append(raw)
        doc = json.loads(raw)
        for r in doc['data']:
            out[date.fromisoformat(r['time'][:10])] = float(r['PriceUSD'])
        url = doc.get('next_page_url')
    return out, pages


def fetch_binance(get, start, end):
    ms = int(datetime(start.year, start.month, start.day, tzinfo=timezone.utc).timestamp() * 1000)
    out, pages = {}, []
    while True:
        raw = get(BN.format(ms=ms))
        pages.append(raw)
        rows = json.loads(raw)
        for k in rows:
            d = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).date()
            if start <= d <= end:
                out[d] = float(k[7])
        if len(rows) < 1000 or datetime.fromtimestamp(rows[-1][0] / 1000, tz=timezone.utc).date() >= end:
            break
        ms = rows[-1][0] + DAY_MS
    return out, pages


def _iso(d):
    return {k.isoformat(): v for k, v in sorted(d.items())}


def store(prices, volumes, pages, out_dir, cutoff):
    out_dir = Path(out_dir)
    (out_dir / 'market').mkdir(parents=True, exist_ok=True)
    (out_dir / 'sealed' / 'raw').mkdir(parents=True, exist_ok=True)
    dev = {'prices': _iso({d: v for d, v in prices.items() if d <= cutoff}),
           'volumes': _iso({d: v for d, v in volumes.items() if d <= cutoff})}
    sealed = {'prices': _iso({d: v for d, v in prices.items() if d > cutoff}),
              'volumes': _iso({d: v for d, v in volumes.items() if d > cutoff})}
    (out_dir / 'market' / 'dev.json').write_text(json.dumps(dev))
    (out_dir / 'sealed' / 'market_sealed.json').write_text(json.dumps(sealed))
    index = {}
    for source, raws in pages.items():
        for raw in raws:            # raw responses span both windows, so they stay sealed
            h = hashlib.sha256(raw).hexdigest()
            (out_dir / 'sealed' / 'raw' / f'{h}.json').write_bytes(raw)
            index.setdefault(source, []).append(h)
    meta = {'cutoff': cutoff.isoformat(), 'dev_prices': len(dev['prices']), 'dev_volumes': len(dev['volumes']),
            'sealed_prices': len(sealed['prices']), 'sealed_volumes': len(sealed['volumes']), 'raw': index}
    (out_dir / 'market' / 'meta.json').write_text(json.dumps(meta, indent=1))
    return meta


def _parse(doc):
    return ({date.fromisoformat(k): float(v) for k, v in doc['prices'].items()},
            {date.fromisoformat(k): float(v) for k, v in doc['volumes'].items()})


def load_dev(path, cutoff):
    prices, volumes = _parse(json.loads(Path(path).read_text()))
    if any(d > cutoff for d in list(prices) + list(volumes)):
        raise ValueError('development market file contains sealed dates')
    return prices, volumes


def load_all(dev_path, sealed_path):
    p1, v1 = _parse(json.loads(Path(dev_path).read_text()))
    p2, v2 = _parse(json.loads(Path(sealed_path).read_text()))
    return {**p1, **p2}, {**v1, **v2}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_market.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b2/market.py tests/research/onchain_b2/test_market.py
git commit -m "feat(onchain-b2): Coin Metrics close and Binance volume with a sealed split"
```

---

### Task 6: Targets T1–T5 and price/volume features F0

**Files:**
- Create: `tradingagents/research/onchain_b2/targets.py`
- Test: `tests/research/onchain_b2/test_targets.py`

**Interfaces:**
- Produces: `f0(prices, volumes, d: date) -> dict | None` (keys `f0_r1, f0_r7, f0_r28, f0_rv7, f0_rv28, f0_lvol7, f0_volratio`); `t1(prices, d)`, `t2(prices, m)` → `int | None`; `t3(prices, m)`, `t4(prices, m)`, `t5(volumes, m)` → `float | None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b2/test_targets.py
import math
from datetime import date, timedelta

import pytest

from tradingagents.research.onchain_b2 import targets as T

D0 = date(2020, 1, 1)


def _series(f, n=80):
    return {D0 + timedelta(days=i): f(i) for i in range(n)}


def test_directions_and_return():
    p = _series(lambda i: 100.0 * 1.01 ** i)
    m = D0 + timedelta(days=40)
    assert T.t1(p, m) == 1 and T.t2(p, m) == 1
    assert T.t3(p, m) == pytest.approx(7 * math.log(1.01))
    flat = _series(lambda i: 100.0)
    assert T.t1(flat, m) == 0 and T.t2(flat, m) == 0


def test_realised_volatility():
    p = _series(lambda i: 100.0 * (1.02 if i % 2 else 1.0))     # alternating ±log(1.02)
    m = D0 + timedelta(days=40)
    assert T.t4(p, m) == pytest.approx(math.log(math.sqrt(7) * math.log(1.02)))


def test_volume_target_and_missing():
    v = _series(lambda i: 10.0)
    m = D0 + timedelta(days=40)
    assert T.t5(v, m) == pytest.approx(math.log(70.0))
    assert T.t5(v, D0 + timedelta(days=75)) is None


def test_f0_values_and_missing_history():
    p = _series(lambda i: 100.0 * 1.01 ** i)
    v = _series(lambda i: 10.0 if i < 60 else 20.0)
    d = D0 + timedelta(days=66)
    f = T.f0(p, v, d)
    assert f['f0_r1'] == pytest.approx(math.log(1.01)) and f['f0_r7'] == pytest.approx(7 * math.log(1.01))
    assert f['f0_rv7'] == pytest.approx(math.sqrt(7) * math.log(1.01))
    assert f['f0_lvol7'] == pytest.approx(math.log(140.0))
    assert f['f0_volratio'] == pytest.approx(math.log(140.0 / ((7 * 20 + 21 * 10) * 7 / 28)))
    assert T.f0(p, v, D0 + timedelta(days=20)) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_targets.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b2/targets.py
"""Targets T1–T5 and price/volume features F0 (spec §5.1, §6). Decision at the close of
day d (or Monday m); every input is a close or volume at or before d."""
from __future__ import annotations

import math
from datetime import timedelta


def _c(p, d, k=0):
    return p.get(d + timedelta(days=k))


def _rets(p, d, start, n):
    """Daily log returns for days d+start … d+start+n-1 (each relative to the previous day)."""
    out = []
    for k in range(start, start + n):
        a, b = _c(p, d, k - 1), _c(p, d, k)
        if a is None or b is None:
            return None
        out.append(math.log(b / a))
    return out


def t1(p, d):
    a, b = _c(p, d), _c(p, d, 1)
    return None if a is None or b is None else int(b > a)


def t2(p, m):
    a, b = _c(p, m), _c(p, m, 7)
    return None if a is None or b is None else int(b > a)


def t3(p, m):
    a, b = _c(p, m), _c(p, m, 7)
    return None if a is None or b is None else math.log(b / a)


def t4(p, m):
    r = _rets(p, m, 1, 7)
    return None if r is None else math.log(max(math.sqrt(sum(x * x for x in r)), 1e-8))


def t5(v, m):
    xs = [v.get(m + timedelta(days=k)) for k in range(1, 8)]
    return None if any(x is None for x in xs) or sum(xs) <= 0 else math.log(sum(xs))


def f0(p, v, d):
    r = _rets(p, d, -27, 28)            # returns ending at d: days d-27 … d
    c, c1, c7, c28 = _c(p, d), _c(p, d, -1), _c(p, d, -7), _c(p, d, -28)
    vols = [v.get(d - timedelta(days=k)) for k in range(28)]
    if r is None or None in (c, c1, c7, c28) or any(x is None for x in vols) or sum(vols[:7]) <= 0:
        return None
    v7, v28 = sum(vols[:7]), sum(vols)
    return {'f0_r1': math.log(c / c1), 'f0_r7': math.log(c / c7), 'f0_r28': math.log(c / c28),
            'f0_rv7': math.sqrt(sum(x * x for x in r[-7:])), 'f0_rv28': math.sqrt(sum(x * x for x in r)),
            'f0_lvol7': math.log(v7), 'f0_volratio': math.log(v7 / (v28 * 7 / 28))}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_targets.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b2/targets.py tests/research/onchain_b2/test_targets.py
git commit -m "feat(onchain-b2): targets T1-T5 and price/volume features"
```

---

### Task 7: Motif features F2 and role-split motifs F3b

**Files:**
- Create: `tradingagents/research/onchain_b2/motiffeat.py`
- Test: `tests/research/onchain_b2/test_motiffeat.py`

**Interfaces:**
- Consumes: `onchain_b.weekly.WeekGraph` (fields `addresses` S42, `x` float32[K,4] with columns log1p in_count, out_count, in_volume, out_volume).
- Produces: `motif_features(F: np.ndarray[K, m], graph, exchanges: set[str], whales: set[str]) -> dict` with keys `f2_hist_{k}`, `f2_mean_{k}`, `f2_vw_{k}`, `f3b_ex_{k}`, `f3b_wh_{k}` for k in 0…m-1, plus `f3b_ex_n`, `f3b_wh_n`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b2/test_motiffeat.py
import numpy as np
import pytest

from tradingagents.research.onchain_b.weekly import WeekGraph
from tradingagents.research.onchain_b2.motiffeat import motif_features

A, B, C = ('0x' + c * 40 for c in 'abc')


def _graph():
    x = np.zeros((3, 4), np.float32)
    x[0, 2] = np.log1p(1.0)          # node 0: 1 ETH in
    x[1, 3] = np.log1p(3.0)          # node 1: 3 ETH out
    return WeekGraph('2019-06-03', np.array([A, B, C], dtype='S42'), x, np.zeros((2, 0), np.int32),
                     np.zeros((0, 2), np.float32), np.zeros(0, np.int64), {})


def test_motif_features():
    F = np.array([[0.1, 0.9], [0.8, 0.2], [0.5, 0.5]], np.float32)
    f = motif_features(F, _graph(), exchanges={B}, whales={A, C})
    assert f['f2_hist_0'] == pytest.approx(2 / 3) and f['f2_hist_1'] == pytest.approx(1 / 3)   # tie → motif 0
    assert f['f2_mean_0'] == pytest.approx(1.4 / 3) and f['f2_mean_1'] == pytest.approx(1.6 / 3)
    assert f['f2_vw_0'] == pytest.approx(0.625, abs=1e-6) and f['f2_vw_1'] == pytest.approx(0.375, abs=1e-6)
    assert f['f3b_ex_0'] == pytest.approx(0.8) and f['f3b_ex_n'] == 1
    assert f['f3b_wh_0'] == pytest.approx(0.3) and f['f3b_wh_1'] == pytest.approx(0.7) and f['f3b_wh_n'] == 2


def test_absent_roles_give_zeros():
    F = np.array([[0.1, 0.9], [0.8, 0.2], [0.5, 0.5]], np.float32)
    f = motif_features(F, _graph(), exchanges=set(), whales=set())
    assert f['f3b_ex_n'] == 0 and f['f3b_ex_0'] == 0.0 and f['f3b_wh_1'] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_motiffeat.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b2/motiffeat.py
"""Motif features that keep the distribution instead of one mean (spec §5.3):
best-motif histogram, mean and ETH-volume-weighted mean score per motif (F2), and
mean score per motif over exchange and whale nodes of the top-K graph (F3b)."""
from __future__ import annotations

import numpy as np


def motif_features(F, graph, exchanges, whales):
    K, m = F.shape
    F = F.astype(np.float64)
    out = {}
    hist = np.bincount(F.argmax(1), minlength=m) / K
    mean = F.mean(0)
    w = np.expm1(graph.x[:, 2].astype(np.float64)) + np.expm1(graph.x[:, 3].astype(np.float64))
    vw = (w[:, None] * F).sum(0) / w.sum() if w.sum() > 0 else mean
    addrs = [a.decode() if isinstance(a, bytes) else str(a) for a in graph.addresses]
    for name, members in (('ex', exchanges), ('wh', whales)):
        mask = np.array([a in members for a in addrs], bool)
        role = F[mask].mean(0) if mask.any() else np.zeros(m)
        out[f'f3b_{name}_n'] = int(mask.sum())
        for k in range(m):
            out[f'f3b_{name}_{k}'] = float(role[k])
    for k in range(m):
        out[f'f2_hist_{k}'] = float(hist[k])
        out[f'f2_mean_{k}'] = float(mean[k])
        out[f'f2_vw_{k}'] = float(vw[k])
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_motiffeat.py -q`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b2/motiffeat.py tests/research/onchain_b2/test_motiffeat.py
git commit -m "feat(onchain-b2): motif histogram, weighted and role-split motif features"
```

---

### Task 8: Dataset (raw table, causal transforms, samples, feature sets)

**Files:**
- Create: `tradingagents/research/onchain_b2/dataset.py`
- Test: `tests/research/onchain_b2/test_dataset.py`

**Interfaces:**
- Consumes: `periods.{all_weeks, week_end, latest_week_for, weekly_window, daily_window}`; `targets.{f0, t1, t2, t3, t4, t5}`.
- Produces: `raw_table(rows: dict[str week, dict | None]) -> pd.DataFrame` (index = all weeks, NaN for missing); `transform(raw, z_window=8, z_min=6) -> pd.DataFrame` (columns `<name>__z8`, `<name>__d1`); `weekly_samples(trans, prices, volumes, window) -> (pd.DataFrame, list[tuple[str, str]])` (index decision date, columns features + `f0_*` + `T2…T5`); `daily_samples(trans, prices, volumes, window) -> (pd.DataFrame, list)` (`T1`); `FEATURE_SETS: dict[str, tuple[str, ...]]`; `columns(df, set_name) -> list[str]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b2/test_dataset.py
import math
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2 import dataset as DS
from tradingagents.research.onchain_b2 import periods


def test_transform_is_causal_and_correct():
    weeks = [f'w{i:02d}' for i in range(12)]
    raw = pd.DataFrame({'f2_mean_0': np.arange(1.0, 13.0)}, index=weeks)
    t = DS.transform(raw)
    assert math.isnan(t.loc['w05', 'f2_mean_0__z8'])                         # only 5 previous values
    assert t.loc['w06', 'f2_mean_0__z8'] == pytest.approx((7 - 3.5) / np.std(np.arange(1.0, 7.0)))
    assert t.loc['w08', 'f2_mean_0__z8'] == pytest.approx((9 - 4.5) / np.std(np.arange(1.0, 9.0)))
    assert t.loc['w08', 'f2_mean_0__d1'] == pytest.approx(1.0)
    raw2 = raw.copy()
    raw2.loc['w09', 'f2_mean_0'] = 1000.0
    assert DS.transform(raw2).loc['w08', 'f2_mean_0__z8'] == t.loc['w08', 'f2_mean_0__z8']   # no future leak


def test_value_transforms():
    raw = pd.DataFrame({'f1_transfers': [np.e - 1] * 10, 'f3a_ex_net_value': [-(np.e - 1)] * 10,
                        'f1_top_share': [0.5] * 10}, index=[f'w{i}' for i in range(10)])
    t = DS.transform(raw)
    assert t['f1_transfers__z8'].iloc[-1] == 0.0                              # constant series → zero std → 0
    assert DS._value('f1_transfers', np.e - 1) == pytest.approx(1.0)
    assert DS._value('f3a_ex_net_value', -(np.e - 1)) == pytest.approx(-1.0)
    assert DS._value('f1_top_share', 0.5) == 0.5 and DS._value('f3b_ex_n', np.e - 1) == pytest.approx(1.0)


def _market():
    d0 = date(2016, 12, 1)
    days = [d0 + timedelta(days=i) for i in range((date(2025, 1, 31) - d0).days)]
    rng = np.random.default_rng(0)
    p = dict(zip(days, 1000 * np.exp(np.cumsum(rng.normal(0, 0.02, len(days))))))
    v = dict(zip(days, np.full(len(days), 5e8)))
    return {d: x for d, x in p.items() if d <= periods.DEV_END}, {d: x for d, x in v.items() if d <= periods.DEV_END}


def _trans(missing=()):
    weeks = periods.all_weeks()
    rows = {w: (None if w in missing else {'f1_transfers': 1000.0 + i, 'f2_mean_0': 0.1 + 0.001 * (i % 7)})
            for i, w in enumerate(weeks)}
    return DS.transform(DS.raw_table(rows))


def test_weekly_dev_samples():
    p, v = _market()
    df, excluded = DS.weekly_samples(_trans(), p, v, 'dev')
    assert len(df) + len(excluded) == 378 and df.index.min() >= pd.Timestamp('2017-10-02')
    assert df.index.max() <= pd.Timestamp('2024-12-23') and {'T2', 'T3', 'T4', 'T5', 'f0_r1'} <= set(df.columns)
    assert DS.columns(df, 'S0') == sorted(c for c in df.columns if c.startswith('f0_'))
    assert set(DS.columns(df, 'S3')) == set(DS.columns(df, 'S1')) | {c for c in df.columns if c.startswith('f2_')}


def test_unavailable_week_excluded_with_reason():
    p, v = _market()
    df, excluded = DS.weekly_samples(_trans(missing={'2020-03-02'}), p, v, 'dev')
    assert (pd.Timestamp('2020-03-09') not in df.index) and ('2020-03-09', 'week_unavailable') in excluded


def test_daily_samples_use_latest_completed_week():
    p, v = _market()
    df, _ = DS.daily_samples(_trans(), p, v, 'dev')
    assert 'T1' in df.columns and df.index.max() == pd.Timestamp('2024-12-30')
    row = df.loc[pd.Timestamp('2020-03-08')]
    assert row['week'] == '2020-02-24'                                        # week 2020-03-02 not finished on 03-08
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_dataset.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b2/dataset.py
"""Weekly raw features → causal transforms → weekly and daily samples (spec §5.4, §6, §7)."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import periods
from . import targets as T

SIGNED = {'f3a_ex_net_value', 'f3a_whale_net_to_ex'}
FEATURE_SETS = {'S0': ('f0_',), 'S1': ('f0_', 'f1_'), 'S2': ('f0_', 'f1_', 'f3a_'),
                'S3': ('f0_', 'f1_', 'f2_'), 'S4': ('f0_', 'f1_', 'f3a_', 'f2_', 'f3b_')}


def _value(name, x):
    if name in SIGNED:
        return np.sign(x) * np.log1p(np.abs(x))
    unchanged = (name.endswith('_share') or name == 'f1_mean_degree' or name.startswith('f2_')
                 or (name.startswith('f3b_') and not name.endswith('_n')))
    return x if unchanged else np.log1p(x)


def raw_table(rows):
    weeks = periods.all_weeks() if not rows or set(rows) <= set(periods.all_weeks()) else sorted(rows)
    data = {w: (rows.get(w) or {}) for w in weeks}
    return pd.DataFrame.from_dict(data, orient='index').reindex(weeks)


def transform(raw, z_window=8, z_min=6):
    out = {}
    for name in raw.columns:
        x = _value(name, raw[name].astype(float))
        prev = x.shift(1)
        mean = prev.rolling(z_window, min_periods=z_min).mean()
        std = prev.rolling(z_window, min_periods=z_min).std(ddof=0)
        z = (x - mean) / std
        z[(std == 0) & x.notna()] = 0.0
        out[f'{name}__z8'] = z
        out[f'{name}__d1'] = x - prev
    return pd.DataFrame(out, index=raw.index)


def columns(df, set_name):
    return sorted(c for c in df.columns if c.startswith(FEATURE_SETS[set_name]))


def _row(trans, week, f0, extra):
    feats = trans.loc[week]
    if feats.isna().any():
        return None, 'features_incomplete'
    if f0 is None:
        return None, 'f0_unavailable'
    return {**feats.to_dict(), **f0, **extra}, None


def weekly_samples(trans, prices, volumes, window):
    rows, excluded = {}, []
    available = set(trans.index[trans.notna().any(axis=1)])
    for w in trans.index:
        m = periods.week_end(w)
        if periods.weekly_window(m) != window:
            continue
        if w not in available:
            excluded.append((m.isoformat(), 'week_unavailable'))
            continue
        row, why = _row(trans, w, T.f0(prices, volumes, m),
                        {'week': w, 'T2': T.t2(prices, m), 'T3': T.t3(prices, m), 'T4': T.t4(prices, m),
                         'T5': T.t5(volumes, m)})
        if why:
            excluded.append((m.isoformat(), why))
        else:
            rows[pd.Timestamp(m)] = row
    df = pd.DataFrame.from_dict(rows, orient='index').sort_index()
    return df.astype({c: float for c in df.columns if c != 'week'}), excluded


def daily_samples(trans, prices, volumes, window):
    weeks = list(trans.index)
    available = set(trans.index[trans.notna().any(axis=1)])
    rows, excluded = {}, []
    start = periods.DEV_START if window == 'dev' else periods.HOLD_START
    end = periods.DEV_END if window == 'dev' else periods.HOLD_END
    d = start
    while d <= end:
        if periods.daily_window(d) == window:
            w = periods.latest_week_for(d, weeks)
            if w is None or w not in available:
                excluded.append((d.isoformat(), 'week_unavailable'))
            else:
                row, why = _row(trans, w, T.f0(prices, volumes, d), {'week': w, 'T1': T.t1(prices, d)})
                if why:
                    excluded.append((d.isoformat(), why))
                else:
                    rows[pd.Timestamp(d)] = row
        d += timedelta(days=1)
    df = pd.DataFrame.from_dict(rows, orient='index').sort_index()
    return df.astype({c: float for c in df.columns if c != 'week'}), excluded
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_dataset.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b2/dataset.py tests/research/onchain_b2/test_dataset.py
git commit -m "feat(onchain-b2): causal feature transforms and weekly/daily sample assembly"
```

---

### Task 9: Screen (walk-forward, models, losses, gate, selection, report)

**Files:**
- Create: `tradingagents/research/onchain_b2/screen.py`
- Test: `tests/research/onchain_b2/test_screen.py`

**Interfaces:**
- Consumes: `dataset.columns`; `onchain_b.evaluate.block_bootstrap(values, block, draws, seed) -> (lo, hi)`; `config.load()`.
- Produces: `TARGETS: dict[str, (kind, task)]`, `COMPARISONS: list[(str, str)]`, `FAMILIES`; `folds(dates, test_years, purge_days) -> list[(year, train_mask, test_mask)]`; `fit_predict(family, task, Xtr, ytr, Xte, inner_len, cfg) -> np.ndarray`; `row_loss(task, y, pred) -> np.ndarray`; `run_screen(samples: dict[str, DataFrame], cfg) -> list[dict]` (each: `target, kind, task, family, set, comparator, n, mean_diff, lo, hi, wins, years, passed, loss_set, loss_comparator, extra`); `select(results, cfg) -> list[dict]` (`target, family, set, comparator, dev_mean_diff, dev_hi`); `report(results, selection) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b2/test_screen.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b2 import config, screen as SC


def _weekly(rng):
    idx = pd.date_range('2017-10-02', '2024-12-23', freq='7D')
    n = len(idx)
    sig = rng.normal(size=n)
    df = pd.DataFrame({'f0_r1__x': rng.normal(size=n), 'f1_sig__z8': sig, 'f3a_noise__z8': rng.normal(size=n),
                       'f2_noise__z8': rng.normal(size=n), 'f3b_noise__z8': rng.normal(size=n)}, index=idx)
    df['T2'] = (sig + 0.3 * rng.normal(size=n) > 0).astype(float)
    df['T3'] = 2 * sig + 0.3 * rng.normal(size=n)
    df['T4'] = rng.normal(size=n)
    df['T5'] = rng.normal(size=n)
    return df


def _daily(rng):
    idx = pd.date_range('2017-10-02', '2024-12-30', freq='D')
    n = len(idx)
    df = pd.DataFrame({'f0_r1__x': rng.normal(size=n), 'f1_sig__z8': rng.normal(size=n),
                       'f3a_noise__z8': rng.normal(size=n), 'f2_noise__z8': rng.normal(size=n),
                       'f3b_noise__z8': rng.normal(size=n)}, index=idx)
    df['T1'] = (rng.random(n) > 0.5).astype(float)
    return df


def test_folds_purge_and_years():
    idx = pd.date_range('2017-10-02', '2024-12-23', freq='7D')
    f = SC.folds(idx, [2019], purge_days=7)
    year, train, test = f[0]
    assert year == 2019 and idx[train].max() == pd.Timestamp('2018-12-24') and idx[test].min() == pd.Timestamp('2019-01-07')
    assert (idx[test].year == 2019).all()


def test_screen_finds_real_signal_and_rejects_noise():
    rng = np.random.default_rng(1)
    cfg = config.load()
    res = SC.run_screen({'weekly': _weekly(rng), 'daily': _daily(rng)}, cfg)
    get = {(r['target'], r['family'], r['set']): r for r in res}
    assert len(res) == 5 * 2 * 4
    assert get[('T3', 'linear', 'S1')]['passed'] and get[('T3', 'linear', 'S1')]['wins'] >= 4
    assert get[('T2', 'linear', 'S1')]['passed']
    assert not get[('T3', 'linear', 'S2')]['passed'] and not get[('T1', 'linear', 'S1')]['passed']
    sel = SC.select(res, cfg)
    assert 1 <= len(sel) <= 3 and all(s['set'] == 'S1' for s in sel)
    text = SC.report(res, sel)
    assert '| T3 | linear | S1 vs S0 |' in text and 'Selected for the holdout' in text


def test_row_loss():
    assert np.allclose(SC.row_loss('regression', np.array([1.0, 2.0]), np.array([0.0, 2.0])), [1.0, 0.0])
    ll = SC.row_loss('classification', np.array([1.0, 0.0]), np.array([0.5, 0.5]))
    assert np.allclose(ll, [np.log(2), np.log(2)])


def test_select_prefers_graph_sets_on_ties():
    base = dict(target='T4', family='linear', passed=True, mean_diff=-0.1, hi=-0.05)
    res = [{**base, 'set': 'S1', 'comparator': 'S0'}, {**base, 'set': 'S3', 'comparator': 'S1'}]
    assert SC.select(res, {'gate': {'max_selected': 1}})[0]['set'] == 'S3'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_screen.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b2/screen.py
"""Development-window screen (spec §8): expanding walk-forward 2019–2024, fixed linear and
tree models, nested feature-set comparisons, pre-registered gate and holdout selection."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ..onchain_b.evaluate import block_bootstrap
from .dataset import columns

TARGETS = {'T1': ('daily', 'classification'), 'T2': ('weekly', 'classification'),
           'T3': ('weekly', 'regression'), 'T4': ('weekly', 'regression'), 'T5': ('weekly', 'regression')}
COMPARISONS = [('S1', 'S0'), ('S2', 'S1'), ('S3', 'S1'), ('S4', 'S2')]
FAMILIES = ('linear', 'trees')


def folds(dates, test_years, purge_days):
    d = pd.DatetimeIndex(dates)
    out = []
    for y in test_years:
        start, end = pd.Timestamp(f'{y}-01-01'), pd.Timestamp(f'{y + 1}-01-01')
        train = np.asarray(d + pd.Timedelta(days=purge_days) <= start)
        test = np.asarray((d >= start) & (d < end))
        out.append((y, train, test))
    return out


def row_loss(task, y, pred):
    if task == 'classification':
        p = np.clip(pred, 1e-6, 1 - 1e-6)
        return -(y * np.log(p) + (1 - y) * np.log(1 - p))
    return (y - pred) ** 2


def _model(family, task, alpha, cfg):
    if family == 'trees':
        params = cfg['models']['trees']
        return (HistGradientBoostingClassifier if task == 'classification' else HistGradientBoostingRegressor)(**params)
    if task == 'classification':
        return make_pipeline(StandardScaler(), LogisticRegression(C=1.0 / alpha, max_iter=5000))
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def _fit(family, task, alpha, X, y, cfg):
    if task == 'classification' and len(np.unique(y)) < 2:
        return None
    return _model(family, task, alpha, cfg).fit(X, y)


def _predict(model, task, X, fallback):
    if model is None:
        return np.full(len(X), fallback)
    return model.predict_proba(X)[:, 1] if task == 'classification' else model.predict(X)


def fit_predict(family, task, Xtr, ytr, Xte, inner_len, cfg):
    alpha = 10.0
    if family == 'linear' and len(Xtr) > inner_len + 52:
        best = None
        for a in cfg['models']['alphas']:
            m = _fit(family, task, a, Xtr[:-inner_len], ytr[:-inner_len], cfg)
            loss = row_loss(task, ytr[-inner_len:], _predict(m, task, Xtr[-inner_len:], ytr[:-inner_len].mean())).mean()
            if best is None or loss < best[0]:
                best = (loss, a)
        alpha = best[1]
    model = _fit(family, task, alpha, Xtr, ytr, cfg)
    return _predict(model, task, Xte, ytr.mean())


def run_screen(samples, cfg):
    g, f = cfg['gate'], cfg['folds']
    results = []
    for target, (kind, task) in TARGETS.items():
        df = samples[kind]
        df = df[df[target].notna()].sort_index()
        y = df[target].to_numpy(float)
        fl = folds(df.index, f['test_years'], f['purge_days'][kind])
        tested = np.zeros(len(df), bool)
        for _, _, te in fl:
            tested |= te
        years = df.index.year.to_numpy()
        for family in FAMILIES:
            preds = {}
            for s in ('S0', 'S1', 'S2', 'S3', 'S4'):
                X = df[columns(df, s)].to_numpy(float)
                p = np.full(len(df), np.nan)
                for _, tr, te in fl:
                    p[te] = fit_predict(family, task, X[tr], y[tr], X[te], f['inner_len'][kind], cfg)
                preds[s] = p
            loss = {s: row_loss(task, y[tested], preds[s][tested]) for s in preds}
            for a, b in COMPARISONS:
                diff = loss[a] - loss[b]
                lo, hi = block_bootstrap(diff, block=g['block'][kind], draws=g['draws'], seed=g['seed'])
                per_year = {int(yr): float(diff[years[tested] == yr].mean()) for yr in f['test_years']}
                wins = sum(v < 0 for v in per_year.values())
                extra = {}
                if task == 'classification':
                    extra = {f'accuracy_{s}': float(((preds[s][tested] > 0.5) == (y[tested] > 0.5)).mean()) for s in (a, b)}
                else:
                    extra = {f'r2_vs_S0_{s}': float(1 - loss[s].mean() / loss['S0'].mean()) for s in (a, b)}
                results.append({'target': target, 'kind': kind, 'task': task, 'family': family, 'set': a, 'comparator': b,
                                'n': int(len(diff)), 'mean_diff': float(diff.mean()), 'lo': lo, 'hi': hi,
                                'wins': int(wins), 'years': per_year,
                                'passed': bool(hi < 0 and wins >= g['min_year_wins']),
                                'loss_set': float(loss[a].mean()), 'loss_comparator': float(loss[b].mean()), 'extra': extra})
    return results


def select(results, cfg):
    passing = [r for r in results if r['passed']]
    passing.sort(key=lambda r: (r['hi'], 0 if r['set'] in ('S3', 'S4') else 1))
    return [{'target': r['target'], 'family': r['family'], 'set': r['set'], 'comparator': r['comparator'],
             'dev_mean_diff': r['mean_diff'], 'dev_hi': r['hi']} for r in passing[:cfg['gate']['max_selected']]]


def report(results, selection):
    lines = ['| target | family | comparison | n | mean loss diff | 95 % CI | years better | pass | detail |',
             '|---|---|---|---|---|---|---|---|---|']
    for r in results:
        detail = ', '.join(f'{k} {v:.4f}' for k, v in r['extra'].items())
        lines.append(f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n']} | "
                     f"{r['mean_diff']:+.5f} | [{r['lo']:+.5f}, {r['hi']:+.5f}] | {r['wins']}/6 | "
                     f"{'PASS' if r['passed'] else '—'} | {detail} |")
    lines += ['', '## Selected for the holdout', '']
    lines += [f"- {s['target']} · {s['family']} · {s['set']} vs {s['comparator']} (dev upper bound {s['dev_hi']:+.5f})"
              for s in selection] or ['- none: screen negative, holdout stays unused']
    return '\n'.join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_screen.py -q`
Expected: 4 passed (the synthetic screen takes about a minute)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b2/screen.py tests/research/onchain_b2/test_screen.py
git commit -m "feat(onchain-b2): walk-forward screen with registered gate and selection"
```

---

### Task 10: Holdout (committed-selection guard, one-shot evaluation, Holm)

**Files:**
- Create: `tradingagents/research/onchain_b2/holdout.py`
- Test: `tests/research/onchain_b2/test_holdout.py`

**Interfaces:**
- Consumes: `screen.{TARGETS, fit_predict, row_loss}`; `dataset.columns`; `onchain_b.evaluate._bootstrap_means(values, block, draws, seed)`.
- Produces: `committed_selection(path, repo) -> dict` (raises `PermissionError` if untracked or modified); `holm(pvalues) -> list[float]`; `evaluate(dev: dict[str, DataFrame], hold: dict[str, DataFrame], selection: dict, cfg) -> list[dict]` (`target, family, set, comparator, n, mean_diff, p, p_holm, passed`).

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b2/test_holdout.py
import json
import subprocess

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2 import config, holdout as H


def _git(repo, *args):
    subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)


def test_committed_selection_guard(tmp_path):
    _git(tmp_path, 'init', '-q')
    _git(tmp_path, 'config', 'user.email', 't@t')
    _git(tmp_path, 'config', 'user.name', 't')
    sel = tmp_path / 'selection.json'
    sel.write_text(json.dumps({'selected': []}))
    with pytest.raises(PermissionError, match='not committed'):
        H.committed_selection(sel, tmp_path)
    _git(tmp_path, 'add', 'selection.json')
    _git(tmp_path, 'commit', '-qm', 'sel')
    assert H.committed_selection(sel, tmp_path) == {'selected': []}
    sel.write_text(json.dumps({'selected': [1]}))
    with pytest.raises(PermissionError, match='uncommitted'):
        H.committed_selection(sel, tmp_path)


def test_holm():
    assert np.allclose(H.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


def test_evaluate_detects_signal_once():
    rng = np.random.default_rng(3)
    def frame(start, end):
        idx = pd.date_range(start, end, freq='7D')
        sig = rng.normal(size=len(idx))
        return pd.DataFrame({'f0_a__x': rng.normal(size=len(idx)), 'f1_sig__z8': sig,
                             'T3': 2 * sig + 0.3 * rng.normal(size=len(idx))}, index=idx)
    dev, hold = {'weekly': frame('2017-10-02', '2024-12-23')}, {'weekly': frame('2025-01-06', '2026-10-05')}
    sel = {'selected': [{'target': 'T3', 'family': 'linear', 'set': 'S1', 'comparator': 'S0'}]}
    res = H.evaluate(dev, hold, sel, config.load())
    assert res[0]['n'] == 92 and res[0]['mean_diff'] < 0 and res[0]['passed'] and res[0]['p_holm'] < 0.05
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_holdout.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b2/holdout.py
"""Sealed-window confirmation (spec §9): runs only for a committed, unmodified selection;
each configuration is refitted once on all development samples and scored once."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

from ..onchain_b.evaluate import _bootstrap_means
from .dataset import columns
from .screen import TARGETS, fit_predict, row_loss


def committed_selection(path, repo):
    path, repo = Path(path), Path(repo)
    rel = str(path.resolve().relative_to(repo.resolve()))
    if subprocess.run(['git', '-C', str(repo), 'ls-files', '--error-unmatch', rel], capture_output=True).returncode:
        raise PermissionError('selection.json is not committed')
    if subprocess.run(['git', '-C', str(repo), 'diff', '--quiet', 'HEAD', '--', rel]).returncode:
        raise PermissionError('selection.json has uncommitted changes')
    return json.loads(path.read_text())


def holm(pvalues):
    p = np.asarray(pvalues, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    return adj.tolist()


def evaluate(dev, hold, selection, cfg):
    g, f = cfg['gate'], cfg['folds']
    out = []
    for s in selection['selected']:
        kind, task = TARGETS[s['target']]
        d = dev[kind][dev[kind][s['target']].notna()].sort_index()
        h = hold[kind][hold[kind][s['target']].notna()].sort_index()
        yd, yh = d[s['target']].to_numpy(float), h[s['target']].to_numpy(float)
        loss = {}
        for name in (s['set'], s['comparator']):
            cols = columns(d, name)
            pred = fit_predict(s['family'], task, d[cols].to_numpy(float), yd, h[cols].to_numpy(float),
                               f['inner_len'][kind], cfg)
            loss[name] = row_loss(task, yh, pred)
        diff = loss[s['set']] - loss[s['comparator']]
        means = _bootstrap_means(diff, block=g['block'][kind], draws=g['draws'], seed=g['seed'])
        out.append({**{k: s[k] for k in ('target', 'family', 'set', 'comparator')}, 'n': int(len(diff)),
                    'mean_diff': float(diff.mean()), 'p': float((means >= 0).mean())})
    for r, adj in zip(out, holm([r['p'] for r in out]) if out else []):
        r['p_holm'] = adj
        r['passed'] = bool(adj < g['alpha'] and r['mean_diff'] < 0)
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_holdout.py -q`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b2/holdout.py tests/research/onchain_b2/test_holdout.py
git commit -m "feat(onchain-b2): committed-selection holdout with Holm correction"
```

---

### Task 11: CLI stages

**Files:**
- Create: `tradingagents/research/onchain_b2/cli.py`
- Test: `tests/research/onchain_b2/test_cli.py`

**Interfaces:**
- Consumes: every module above; `onchain_b.{weekly.save, weekly.load, dictionary.build/save/load, mcm.compute_week, matching.agreement.MatchConfig, config.load, runlog.Log}`.
- Produces: `main(argv)` with subcommands `labels`, `market`, `weeks [--start W] [--end W] [--workers N]`, `dictionary`, `mcm [--shard I/N]`, `features`, `screen`, `holdout`; `build_one(week, scratch) -> dict status`; module attribute `ARTIFACTS` (patchable). Artifact layout under `ARTIFACTS`: `labels/`, `market/`, `sealed/`, `weeks/<week>.json` or `weeks/<week>.unavailable.json`, `graphs/<week>/`, `dictionary/`, `mcm/<week>.npy`, `features/weekly_raw.parquet`, `screen/`, `logs/`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b2/test_cli.py
import json

import pyarrow as pa

from tradingagents.research.onchain_b2 import cli, s3source

A, B, E = '0x' + 'a' * 40, '0x' + 'b' * 40, '0x' + 'e' * 40


def _day(day):
    return pa.table({'hash': ['0x' + f'{hash(day) % 10**10:064x}'], 'block_timestamp': pa.array([0], pa.timestamp('ns')),
                     'from_address': [A], 'to_address': [B], 'value': [1e18], 'receipt_status': [1]})


def _setup(tmp_path, monkeypatch, fail_day=None):
    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path)
    (tmp_path / 'labels').mkdir()
    (tmp_path / 'labels' / 'labels.json').write_text(json.dumps({E: {'name': 'X', 'added': None, 'sources': ['spellbook']}}))

    def fake_read(day, *, scratch, **kw):
        if day == fail_day:
            raise s3source.DayUnavailable(day, ['boom'])
        return _day(day), {'day': day, 'source': 'test', 'rows': 1}

    monkeypatch.setattr(s3source, 'read_day', fake_read)


def test_weeks_stage_builds_and_skips(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-10', '--workers', '1'])
    s = json.loads((tmp_path / 'weeks' / '2019-06-03.json').read_text())
    assert s['f1']['f1_transfers'] == 7 and len(s['receipts']) == 7 and (tmp_path / 'graphs' / '2019-06-03' / 'summary.json').exists()
    m = (tmp_path / 'weeks' / '2019-06-03.json').stat().st_mtime
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-03', '--workers', '1'])
    assert (tmp_path / 'weeks' / '2019-06-03.json').stat().st_mtime == m


def test_unavailable_day_marks_week_and_continues(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, fail_day='2019-06-05')
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-10', '--workers', '1'])
    bad = json.loads((tmp_path / 'weeks' / '2019-06-03.unavailable.json').read_text())
    assert bad['day'] == '2019-06-05' and not (tmp_path / 'weeks' / '2019-06-03.json').exists()
    assert (tmp_path / 'weeks' / '2019-06-10.json').exists()


def test_stale_graph_without_summary_is_rebuilt(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    (tmp_path / 'graphs' / '2019-06-03').mkdir(parents=True)
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-03', '--workers', '1'])
    assert (tmp_path / 'weeks' / '2019-06-03.json').exists() and (tmp_path / 'graphs' / '2019-06-03' / 'x.npy').exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_cli.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b2/cli.py
"""B2 stage runner. Each stage is idempotent at week / run granularity and logs JSON lines."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from ..onchain_b import config as b_config
from ..onchain_b import dictionary as D
from ..onchain_b import mcm
from ..onchain_b import weekly as W
from ..onchain_b.matching.agreement import MatchConfig
from ..onchain_b.runlog import Log
from . import config, dataset, holdout, labels, market, motiffeat, periods, s3source, screen, weekbuild

ARTIFACTS = config.ARTIFACTS


def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))
    os.replace(tmp, path)


def build_one(week, scratch):
    cfg = config.load()
    out = ARTIFACTS / 'weeks' / f'{week}.json'
    if out.exists():
        return {'week': week, 'status': 'skip'}
    tables, receipts = [], []
    for day in periods.week_days(week):
        try:
            t, r = s3source.read_day(day, scratch=scratch)
        except s3source.DayUnavailable as e:
            _write_json(ARTIFACTS / 'weeks' / f'{week}.unavailable.json', {'week': week, 'day': e.day, 'errors': e.errors})
            return {'week': week, 'status': 'unavailable', 'day': e.day}
        tables.append(t)
        receipts.append(r)
    summary, graph = weekbuild.build_week(week, tables, labels.exchange_array(ARTIFACTS / 'labels' / 'labels.json'), cfg)
    summary['receipts'] = receipts
    gdir = ARTIFACTS / 'graphs' / week
    if gdir.exists():
        shutil.rmtree(gdir)            # a graph without its summary marker is from an interrupted run
    W.save(graph, gdir)
    _write_json(out, summary)          # summary last: it is the completion marker
    return {'week': week, 'status': 'done', 'rows': sum(r['rows'] for r in receipts)}


def _build_job(args):
    week, scratch = args
    t = time.time()
    res = build_one(week, scratch)
    res['seconds'] = round(time.time() - t, 1)
    return res


def stage_weeks(args):
    log = Log(ARTIFACTS / 'logs' / 'weeks.jsonl')
    weeks = [w for w in periods.all_weeks() if (args.start or '0') <= w <= (args.end or '9')]
    todo = [w for w in weeks if not (ARTIFACTS / 'weeks' / f'{w}.json').exists()]
    log.event(event='start', weeks=len(weeks), todo=len(todo))
    (ARTIFACTS / 'scratch').mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ARTIFACTS / 'scratch') as scratch:
        jobs = [(w, scratch) for w in todo]
        if args.workers == 1:
            results = map(_build_job, jobs)
            for r in results:
                log.event(event='week', **r)
        else:
            with ProcessPoolExecutor(args.workers) as ex:
                for r in ex.map(_build_job, jobs):
                    log.event(event='week', **r)


def stage_labels(args):
    print(json.dumps(labels.fetch_and_store(market.http_get, ARTIFACTS / 'labels'), indent=1))


def stage_market(args):
    from datetime import date
    m = config.load()['market']
    prices, p_raw = market.fetch_coinmetrics(market.http_get, date.fromisoformat(m['price_start']), date.fromisoformat(m['end']))
    vols, v_raw = market.fetch_binance(market.http_get, date.fromisoformat(m['volume_start']), date.fromisoformat(m['end']))
    print(json.dumps(market.store(prices, vols, {'coinmetrics': p_raw, 'binance': v_raw}, ARTIFACTS, periods.DEV_END), indent=1))


def _done_weeks():
    return [w for w in periods.all_weeks() if (ARTIFACTS / 'weeks' / f'{w}.json').exists()]


def stage_dictionary(args):
    c = config.load()['dictionary']
    log = Log(ARTIFACTS / 'logs' / 'dictionary.jsonl')
    out = ARTIFACTS / 'dictionary'
    if (out / 'dictionary.json').exists():
        log.event(event='skip')
        return
    done = set(_done_weeks())
    weeks = {w: W.load(ARTIFACTS / 'graphs' / w) for w in periods.dictionary_weeks() if w in done}
    t = time.time()
    d = D.build(weeks, MatchConfig.from_json(b_config.load('matching')), c['sample_count'], c['size'],
                config.load()['n_max'], c['seed'])
    D.save(d, out)
    log.event(event='done', weeks=len(weeks), seconds=round(time.time() - t, 1))


def stage_mcm(args):
    i, n = map(int, args.shard.split('/'))
    log = Log(ARTIFACTS / 'logs' / f'mcm-{i}of{n}.jsonl')
    d = D.load(ARTIFACTS / 'dictionary')
    cfg = MatchConfig.from_json(b_config.load('matching'))
    out = ARTIFACTS / 'mcm'
    out.mkdir(parents=True, exist_ok=True)
    for w in _done_weeks()[i::n]:
        target = out / f'{w}.npy'
        if target.exists():
            continue
        t = time.time()
        F = mcm.compute_week(W.load(ARTIFACTS / 'graphs' / w), d, cfg, config.load()['n_max'])
        tmp = out / f'.{w}.tmp.npy'
        np.save(tmp, F)
        os.replace(tmp, target)
        log.event(event='week', week=w, seconds=round(time.time() - t, 1), cells=int(F.size))


def stage_features(args):
    import pyarrow as pa
    import pyarrow.parquet as pq
    exchanges = set(labels.load(ARTIFACTS / 'labels' / 'labels.json'))
    rows, missing = {}, []
    for w in periods.all_weeks():
        s_path, m_path = ARTIFACTS / 'weeks' / f'{w}.json', ARTIFACTS / 'mcm' / f'{w}.npy'
        if not (s_path.exists() and m_path.exists()):
            missing.append(w)
            continue
        s = json.loads(s_path.read_text())
        mf = motiffeat.motif_features(np.load(m_path), W.load(ARTIFACTS / 'graphs' / w), exchanges, set(s['whales']))
        rows[w] = {**s['f1'], **s['f3a'], **mf}
    raw = dataset.raw_table(rows)
    (ARTIFACTS / 'features').mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(raw, preserve_index=True), ARTIFACTS / 'features' / 'weekly_raw.parquet')
    _write_json(ARTIFACTS / 'features' / 'missing.json', missing)
    print(json.dumps({'weeks': len(rows), 'missing': len(missing), 'columns': raw.shape[1]}))


def _transformed():
    import pyarrow.parquet as pq
    raw = pq.read_table(ARTIFACTS / 'features' / 'weekly_raw.parquet').to_pandas()
    t = config.load()['transforms']
    return dataset.transform(raw, t['z_window'], t['z_min'])


def _samples(trans, prices, volumes, window):
    weekly, ex_w = dataset.weekly_samples(trans, prices, volumes, window)
    daily, ex_d = dataset.daily_samples(trans, prices, volumes, window)
    return {'weekly': weekly, 'daily': daily}, {'weekly': ex_w, 'daily': ex_d}


def stage_screen(args):
    cfg = config.load()
    prices, volumes = market.load_dev(ARTIFACTS / 'market' / 'dev.json', periods.DEV_END)
    samples, excluded = _samples(_transformed(), prices, volumes, 'dev')
    results = screen.run_screen(samples, cfg)
    selection = screen.select(results, cfg)
    _write_json(ARTIFACTS / 'screen' / 'screen.json', {'results': results, 'excluded': excluded,
                                                     'n': {k: len(v) for k, v in samples.items()}})
    head = (f"# B2 screen — development 2017-10 → 2024 (walk-forward 2019–2024)\n\n"
            f"Samples: weekly {len(samples['weekly'])} (excluded {len(excluded['weekly'])}), "
            f"daily {len(samples['daily'])} (excluded {len(excluded['daily'])}).\n\n")
    (config.STUDY / 'SCREEN.md').write_text(head + screen.report(results, selection) + '\n')
    _write_json(config.STUDY / 'selection.json', {'registered_from': 'screen.json', 'selected': selection})
    print(screen.report(results, selection))


def stage_holdout(args):
    cfg = config.load()
    selection = holdout.committed_selection(config.STUDY / 'selection.json', config.ROOT)
    if not selection['selected']:
        print('screen negative: holdout not opened')
        return
    trans = _transformed()
    p_dev, v_dev = market.load_dev(ARTIFACTS / 'market' / 'dev.json', periods.DEV_END)
    p_all, v_all = market.load_all(ARTIFACTS / 'market' / 'dev.json', ARTIFACTS / 'sealed' / 'market_sealed.json')
    dev, _ = _samples(trans, p_dev, v_dev, 'dev')
    hold, excluded = _samples(trans, p_all, v_all, 'holdout')
    res = holdout.evaluate(dev, hold, selection, cfg)
    _write_json(ARTIFACTS / 'screen' / 'holdout.json', {'results': res, 'excluded': excluded})
    lines = ['# B2 holdout — sealed 2025-01-06 → 2026-10-05', '',
             '| target | family | comparison | n | mean loss diff | p (one-sided) | p Holm | pass |', '|---|---|---|---|---|---|---|---|']
    lines += [f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n']} | {r['mean_diff']:+.5f} | "
              f"{r['p']:.4f} | {r['p_holm']:.4f} | {'PASS' if r['passed'] else '—'} |" for r in res]
    (config.STUDY / 'HOLDOUT.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b2')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('labels').set_defaults(fn=stage_labels)
    sub.add_parser('market').set_defaults(fn=stage_market)
    a = sub.add_parser('weeks')
    a.add_argument('--start')
    a.add_argument('--end')
    a.add_argument('--workers', type=int, default=2)
    a.set_defaults(fn=stage_weeks)
    sub.add_parser('dictionary').set_defaults(fn=stage_dictionary)
    a = sub.add_parser('mcm')
    a.add_argument('--shard', default='0/1')
    a.set_defaults(fn=stage_mcm)
    sub.add_parser('features').set_defaults(fn=stage_features)
    sub.add_parser('screen').set_defaults(fn=stage_screen)
    sub.add_parser('holdout').set_defaults(fn=stage_holdout)
    args = p.parse_args(argv)
    import torch
    torch.set_num_threads(2)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    args.fn(args)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2/test_cli.py -q`
Expected: 3 passed

- [ ] **Step 5: Run the whole B2 suite and commit**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b2 -q`
Expected: all pass (≈ 38 tests)

```bash
git add tradingagents/research/onchain_b2/cli.py tests/research/onchain_b2/test_cli.py
git commit -m "feat(onchain-b2): stage runner for capture, features, screen and holdout"
```

---

### Task 12: Capture — labels, market, smoke reads, all weeks (B2-CP1)

Operational. Commit docs only; artifacts stay gitignored.

- [ ] **Step 1: Labels and market**

Run:
```bash
OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b2.cli labels
OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b2.cli market
```
Expected: labels `count` ≈ 5,300 with `unparsed` small (record the number); market `dev_prices` ≈ 2,953, `sealed_prices` 650, `dev_volumes` ≈ 2,694, `sealed_volumes` 650.

- [ ] **Step 2: Smoke-read one streamed day from each period**

Run:
```bash
OMP_NUM_THREADS=2 .venv/bin/python -c "
import time; from tradingagents.research.onchain_b2 import s3source as S
for d in ('2017-03-06', '2025-06-02'):
    t0 = time.time(); t, r = S.read_day(d, scratch='research_artifacts/onchain-b2'); print(d, r['rows'], round(time.time() - t0, 1), 's')"
```
Expected: two lines with row counts > 0 and ≈ 3–15 s each.

- [ ] **Step 3: Launch the 510-week build**

Run:
```bash
P=$PWD; systemd-run --user --unit onchain-b2-weeks -p MemoryMax=10G -p WorkingDirectory=$P \
  $P/.venv/bin/python -m tradingagents.research.onchain_b2.cli weeks --workers 2
```
Expected: `research_artifacts/onchain-b2/logs/weeks.jsonl` gains one `week` event per week; ≈ 3–4 h total. Monitor with `tail`; the stage resumes on restart.

- [ ] **Step 4: Record B2-CP1 and commit**

Count `weeks/*.json` and `weeks/*.unavailable.json`; write `research/onchain-b2-2026-10-13/DATA.md` with: label counts, source commits and sha256 (from `labels/meta.json`), market counts and raw hashes (from `market/meta.json`), weeks built / unavailable (with the failing days), streamed vs local day counts, total rows. Update `STATE.md`.

```bash
git add research/onchain-b2-2026-10-13/DATA.md research/onchain-b2-2026-10-13/STATE.md
git commit -m "docs(onchain-b2): B2-CP1 data capture record"
```

---

### Task 13: Dictionary, MCM, features (B2-CP2)

Operational.

- [ ] **Step 1: Dictionary from 2017–2018**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b2.cli dictionary`
Expected: `logs/dictionary.jsonl` `done` with `weeks` = 104 (or fewer if unavailable weeks, recorded), ≈ 30 s.

- [ ] **Step 2: MCM in two shards**

Run:
```bash
P=$PWD; for s in 0 1; do systemd-run --user --unit onchain-b2-mcm$s -p MemoryMax=5G -p WorkingDirectory=$P \
  $P/.venv/bin/python -m tradingagents.research.onchain_b2.cli mcm --shard $s/2; done
```
Expected: `mcm/*.npy` count reaches the number of built weeks; ≈ 2 h.

- [ ] **Step 3: Feature table**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b2.cli features`
Expected: `{"weeks": <built>, "missing": <unavailable>, "columns": 14 + 10 + 96 + 66}` = 186 columns.

- [ ] **Step 4: Record B2-CP2 and commit**

Append to `STATE.md`: dictionary motif sizes, MCM cells/s, feature columns, missing weeks.

```bash
git add research/onchain-b2-2026-10-13/STATE.md
git commit -m "docs(onchain-b2): B2-CP2 dictionary, MCM and feature table"
```

---

### Task 14: Screen, selection commit, holdout (B2-CP3, B2-CP4)

Operational. The selection commit must precede the holdout run.

- [ ] **Step 1: Screen**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b2.cli screen`
Expected: `SCREEN.md` with 40 rows and a selection section; `selection.json` written. ≈ 10–20 min.

- [ ] **Step 2: Commit the screen and selection (B2-CP3) before any holdout read**

```bash
git add research/onchain-b2-2026-10-13/SCREEN.md research/onchain-b2-2026-10-13/selection.json research/onchain-b2-2026-10-13/STATE.md
git commit -m "research(onchain-b2): B2-CP3 development screen and committed holdout selection"
```

- [ ] **Step 3: Holdout (B2-CP4)**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b2.cli holdout`
Expected: either `screen negative: holdout not opened`, or `HOLDOUT.md` with one row per selected configuration.

- [ ] **Step 4: Record and commit**

Update `STATE.md` with the outcome; commit `HOLDOUT.md` (if written) and `STATE.md`. Update the memory note `project_onchain_replication_branch_b_status.md` and the audit artifact's checkpoint section.

```bash
git add research/onchain-b2-2026-10-13/HOLDOUT.md research/onchain-b2-2026-10-13/STATE.md
git commit -m "research(onchain-b2): B2-CP4 sealed holdout result"
```

---

## Self-review

**Spec coverage:** §1 decisions → Tasks 1, 12; §2 questions → Task 9 comparisons; §4.1 sources → Tasks 2, 3, 5; receipts and retries → Task 2; static-label caveat → Task 3 (added_date kept) and DATA.md (Task 12); §4.2 windows and sealing → Tasks 1, 5, 10, 11; §5.1 F0 → Task 6; §5.2 F1 → Task 4; §5.3 F3a, top-K, dictionary, F2, F3b → Tasks 4, 7, 11, 13; §5.4 transforms → Task 8; §6 targets → Task 6; §7 sets → Task 8; §8 screen, gate, selection → Task 9, 11, 14; §9 holdout → Task 10, 14; §10 step 4 → gated on the screen outcome, separate spec (no task here by design); §11 compute and failure handling → Tasks 2, 11, 12, 13; §12 layout → as listed; §13 testing → each task; §14 checkpoints → Tasks 12–14.

**Placeholder scan:** none; all code steps are complete.

**Type consistency:** `read_day(...) -> (pa.Table, dict)` used by `cli.build_one`; `build_week(week, tables, exchanges, cfg) -> (summary, WeekGraph)`; summary keys `f1`, `f3a`, `whales`, `receipts` consumed by `stage_features`; `motif_features(F, graph, exchanges: set, whales: set)`; `dataset.columns(df, set)` used by `screen` and `holdout`; `TARGETS` shared; market `load_dev/load_all` return `(prices, volumes)` dicts keyed by `date`.

**Review Focus coverage:** 1 → Task 2 `test_multiple_parts_concatenated`; 2 → Task 4 `test_receive_only_address_has_zero_out`; 3 → Task 5 `test_load_dev_refuses_sealed_dates`; 4 → Task 4 `test_role_flows_without_exchanges_are_zero`; 5 → Task 11 `test_unavailable_day_marks_week_and_continues` and Task 8 `test_unavailable_week_excluded_with_reason`.
