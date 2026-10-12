# Onchain Replication Branch B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lean, test-covered package that turns the retained ETH transaction store into paper-scale weekly graphs, motif dictionaries, MCM features and a jointly trained GAT→attention-LSTM predictor, and evaluates the initial ETH fold (train 2022–2023, test 2024) under a pre-registered protocol.

**Architecture:** Stage pipeline with idempotent per-week / per-arm-seed outputs under `research_artifacts/onchain-replication-b/`. Science code is new (`tradingagents/research/onchain_b/`); only the hash-verified span reader is copied from Branch A. Two matching solvers share one contract: a readable reference solver and a bucketed batched solver that must agree to 1e-9.

**Tech Stack:** Python 3.13 (`.venv` via `uv sync --all-extras --python 3.13.13`), NumPy 2.3, SciPy 1.17, PyArrow, zstandard, PyTorch 2.10 CPU, scikit-learn, pytest.

**Spec:** `docs/superpowers/specs/2026-10-12-onchain-replication-b-design.md`

## Global Constraints

- Never modify `research/onchain-paper-replication-2026-09-24/` or `tradingagents/research/onchain_replication/` (Branch A). Raw stores under `/home/malecada/Data/onchain-research/` are read-only.
- Resident memory ≤ 12 GiB for any stage; no GPU; no network; no paid resources; artifacts ≤ 6 GB under `research_artifacts/onchain-replication-b/` (gitignored).
- Documentation in impersonal prose; no "we/our". Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Frozen numbers: 512 samples, 32 motifs, hop depth 1, α=1, β₀=1, β_f=30, β_rate=0.075, max 50 iterations, seeds 11/23/37/51/71, Adam 1e-3, batch 16, 100 epochs, lookback 28, MLP 32→64→32, GAT 4×16 then 1×32, LSTM 64, attention 32.
- Test command: `cd /home/malecada/master_thesis/TradingAgents-onchain-b && .venv/bin/python -m pytest tests/research/onchain_b -q`.
- No 2024 graph, close or label may be read by dictionary, calibration or scaling code paths.

## Review Focus

1. A day whose parquet contains two rows with the same transaction hash → `weekly.admitted_events` must raise, never double count (Task 5 test `test_duplicate_hash_rejected`).
2. A week in which fewer than K addresses are active → `top_k_subgraph` returns all of them with K_effective recorded, no padding (Task 5 test `test_fewer_than_k_nodes`).
3. A neighborhood or motif with zero edges → solver uses node term only, score finite, no NaN from `sqrt(l1*l2)=0` (Task 7 test `test_zero_edge_graph`).
4. A decision date whose 28-day window starts before the first available week → example excluded and listed, never filled with a later week (Task 3 test `test_warmup_exclusion`).
5. Two pairs in one batched bucket with different edge counts → product offsets must not bleed across pairs (Task 8 test `test_batched_mixed_edge_counts`).

---

### Task 1: Package skeleton, research directory, protocol configs

**Files:**
- Create: `tradingagents/research/onchain_b/__init__.py`
- Create: `tradingagents/research/onchain_b/config.py`
- Create: `tests/research/onchain_b/__init__.py`
- Create: `tests/research/onchain_b/test_config.py`
- Create: `research/onchain-replication-b-2026-10-12/PROTOCOL.md`
- Create: `research/onchain-replication-b-2026-10-12/config/{graph,dictionary,matching,model,training,calendar}.json`
- Create: `research/onchain-replication-b-2026-10-12/gates.json`
- Create: `research/onchain-replication-b-2026-10-12/STATE.md`
- Modify: `.gitignore` (append `/research_artifacts/onchain-replication-b/`)

**Interfaces:**
- Produces: `config.load(name) -> dict` reading `research/onchain-replication-b-2026-10-12/config/<name>.json`; `config.ROOT` (repo root Path); `config.STUDY` (research dir Path); `config.ARTIFACTS` (`ROOT/'research_artifacts/onchain-replication-b'`).

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b/test_config.py
from tradingagents.research.onchain_b import config

def test_frozen_matching_numbers():
    m = config.load('matching')
    assert (m['alpha'], m['beta0'], m['beta_final'], m['beta_rate'], m['max_iterations']) == (1.0, 1.0, 30.0, 0.075, 50)

def test_frozen_dictionary_numbers():
    d = config.load('dictionary')
    assert d['sample_count'] == 512 and d['size'] == 32 and d['hop_depth'] == 1
    assert d['n_max'] in (32, 64)

def test_artifacts_dir_is_ignored():
    text = (config.ROOT / '.gitignore').read_text()
    assert '/research_artifacts/onchain-replication-b/' in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_config.py -q`
Expected: FAIL with `ModuleNotFoundError: tradingagents.research.onchain_b`

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/__init__.py
"""Branch B paper-scale replication of Çelik & Sefer (2026). See docs/superpowers/specs/2026-10-12-onchain-replication-b-design.md."""
```

```python
# tradingagents/research/onchain_b/config.py
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-replication-b-2026-10-12'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-replication-b'


def load(name: str) -> dict:
    return json.loads((STUDY / 'config' / f'{name}.json').read_text())
```

Config files (exact contents):

```json
// config/matching.json
{"alpha": 1.0, "beta0": 1.0, "beta_final": 30.0, "beta_rate": 0.075, "max_iterations": 50,
 "normalization": "row then column, one pass each, log-domain",
 "hardening": "greedy global maximum, row-major ties, remove row and column, min(n1,n2) picks",
 "s1": "exp(-mean squared edge feature difference); 0 if either edge absent",
 "s2": "exp(-mean squared node feature difference)",
 "objective": "Eq.1 literal: edge term /(2 sqrt(l1 l2)), node term /sqrt(n1 n2), total /(1+alpha); zero-edge graphs contribute 0 to edge term",
 "reference_tolerance": {"atol": 1e-9, "rtol": 1e-9}}
```

```json
// config/dictionary.json
{"sample_count": 512, "size": 32, "hop_depth": 1, "n_max": 32,
 "neighborhood": "weak one-hop induced; center plus up to n_max-1 neighbors with largest interaction count with center, ties by node index",
 "sampling": "without replacement over (training week, center); equal initial weights; halve weights of remaining centers inside the drawn neighborhood in that week",
 "linkage": "average", "representative": "medoid: minimum within-cluster distance sum, ties by sample index",
 "rng": "numpy PCG64(seed)", "distance": "1 - (S(A,B)+S(B,A))/2"}
```

```json
// config/graph.json
{"asset": "ETH", "week_anchor": "MON", "timezone": "UTC",
 "first_week": "2022-01-03", "last_week": "2024-12-23", "expected_weeks": 156,
 "admitted_event": "receipt_status==1 and value>0 and to_address matches 0x[0-9a-f]{40}",
 "duplicates": "reject day on duplicate transaction hash",
 "aggregation": "ordered (from,to) pair: count, value_eth=sum(value/1e18)",
 "paper_scale": {"rule": "induced subgraph on K most active addresses; activity=in_count+out_count of admitted transactions; ties lexicographic address", "K": null,
                 "calibration": "K chosen label-free on weeks 2022-03-07, 2022-09-05, 2023-03-06, 2023-09-04 to match paper density 0.003 in log space; cap 50000"},
 "node_features": ["log1p(in_count)", "log1p(out_count)", "log1p(in_volume_eth)", "log1p(out_volume_eth)"],
 "edge_features": ["log1p(count)", "log1p(value_eth)"],
 "self_loops": "retained"}
```

```json
// config/model.json
{"mcm_input": 32, "mlp_widths": [64, 32], "mlp_activation": "relu",
 "gat_layers": 2, "gat_heads": [4, 1], "gat_widths": [16, 32], "gat_concat": [true, false],
 "gat_activation": ["elu", "identity"], "leaky_relu_slope": 0.2, "gat_neighbors": "incoming edges plus self once",
 "pooling": "mean", "graph_vector_width": 32, "lookback_days": 28, "lstm_width": 64, "attention_width": 32,
 "heads": {"regression": 1, "classification": 2},
 "baselines": {"lstm": {"width": 64}, "gru": {"width": 64}, "hlstm": {"lower": 128, "upper": 128, "chunks": 4, "chunk_len": 7}, "svm": {"kernel": "rbf", "C": 1.0, "gamma": "scale"}}}
```

```json
// config/training.json
{"optimizer": "adam", "lr": 0.001, "betas": [0.9, 0.999], "batch_size": 16, "epochs": 100, "grad_clip_norm": 1.0,
 "seeds": [11, 23, 37, 51, 71], "validation": "none", "early_stopping": false, "best_seed_selection": false,
 "regression_target": "next-day close scaled by training mean/std; reported in USD",
 "direction_target": "close[d+1] > close[d]; ties 0; cross-entropy",
 "diagnostics": ["constant_graph", "label_permutation"], "label_permutation_seed": 20260924}
```

```json
// config/calendar.json
{"fold": "initial_eth", "train_label_end_exclusive": "2024-01-01", "test_decision_start": "2024-01-01", "test_decision_end": "2024-12-30",
 "graph_lag_days": 1, "price_availability": "close[d] available at start of d+1", "lookback_days": 28}
```

```json
// gates.json
{"registered": "2026-10-12", "fold": "initial_eth", "sealed_test_year": 2024, "one_shot": true,
 "primary": {"metric": "direction_accuracy_full_model_mean_over_seeds", "paper_value": 0.804,
             "close_if_abs_diff_le": 0.02, "bootstrap": {"draws": 2000, "block_days": 14, "seed": 20260924}},
 "secondary": ["full_minus_lstm_accuracy_with_bootstrap", "regression_mae_rmse_mape_usd"],
 "chance_control": "label_permutation accuracy within bootstrap interval of majority-class rate",
 "no_tuning": "no setting changes after any 2024 evaluation; failed cells retained"}
```

`PROTOCOL.md`: one page restating spec §4–§11 as the executable protocol, naming each config file and the calibration rule; `STATE.md`: "Design frozen 2026-10-12; CP1 pending."

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_config.py -q`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b tests/research/onchain_b research/onchain-replication-b-2026-10-12 .gitignore
git commit -m "feat(onchain-b): package skeleton and frozen protocol configs"
```

---

### Task 2: Source reader (day mapping + span reassembly)

**Files:**
- Create: `tradingagents/research/onchain_b/sources.py`
- Test: `tests/research/onchain_b/test_sources.py`

**Interfaces:**
- Produces: `load_plan() -> dict`; `day_manifest(plan, day: str) -> dict` with keys `size, spans, object`; `read_day(manifest, scratch: Path, columns: tuple[str,...]) -> pyarrow.Table`; `projected_table(manifest, scratch, columns)` (same, used by tests with synthetic manifests); constant `COLUMNS = ('hash','block_timestamp','from_address','to_address','value','receipt_status')`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b/test_sources.py
import hashlib, io, json
import pyarrow as pa, pyarrow.parquet as pq, zstandard
from tradingagents.research.onchain_b import sources

def _synthetic_manifest(tmp_path, table, n_spans=3):
    buf = io.BytesIO(); pq.write_table(table, buf); raw = buf.getvalue(); size = len(raw)
    bounds = [0] + [size * k // n_spans for k in range(1, n_spans)] + [size]
    spans = []
    for k, (a, b) in enumerate(zip(bounds, bounds[1:])):
        chunk = raw[a:b]; stored = zstandard.ZstdCompressor().compress(chunk)
        p = tmp_path / f'span{k}.zst'; p.write_bytes(stored)
        spans.append({'path': str(p), 'start': a, 'end': b, 'codec': 'zstd', 'raw_bytes': b - a,
                      'raw_sha256': hashlib.sha256(chunk).hexdigest(), 'stored_bytes': len(stored),
                      'stored_sha256': hashlib.sha256(stored).hexdigest()})
    return {'size': size, 'spans': spans, 'object': {'key': 'synthetic'}}

def _table():
    return pa.table({'hash': ['0x' + f'{i:064x}' for i in range(5)],
                     'block_timestamp': pa.array([1_700_000_000_000_000_000 + i for i in range(5)], pa.timestamp('ns')),
                     'from_address': ['0x' + f'{i:040x}' for i in range(5)],
                     'to_address': ['0x' + f'{i+1:040x}' for i in range(5)],
                     'value': [1e18 * (i + 1) for i in range(5)], 'receipt_status': [1, 1, 0, 1, 1]})

def test_projected_table_roundtrip(tmp_path):
    table = _table(); manifest = _synthetic_manifest(tmp_path, table)
    out = sources.projected_table(manifest, tmp_path, sources.COLUMNS)
    assert out.num_rows == 5 and out.column_names == list(sources.COLUMNS)
    assert out.column('value').to_pylist() == table.column('value').to_pylist()

def test_corrupted_span_rejected(tmp_path):
    manifest = _synthetic_manifest(tmp_path, _table())
    manifest['spans'][1]['stored_sha256'] = '0' * 64
    import pytest
    with pytest.raises(ValueError, match='stored range hash'):
        sources.projected_table(manifest, tmp_path, sources.COLUMNS)

def test_real_plan_resolves_all_days():
    plan = sources.load_plan()
    days = sorted(plan['expected_rows'])
    assert len(days) == 1096 and days[0] == '2022-01-01' and days[-1] == '2024-12-31'
    m = sources.day_manifest(plan, '2023-06-05')
    assert m['size'] > 0 and len(m['spans']) > 0 and all(span['codec'] == 'zstd' for span in m['spans'])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_sources.py -q`
Expected: FAIL with `ModuleNotFoundError` / `AttributeError`

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/sources.py
"""Day → retained-span mapping and hash-verified parquet reassembly.

`projected_table`, `AcquiredReader` and the span-verification logic are ported
from Branch A's `tradingagents/research/onchain_replication/eth_source.py`
(Codex, 2026-09/10) with simplifications; the metadata mapping follows
`research/onchain-paper-replication-2026-09-24/prepare_pilot_sources.py`.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, io, json, re, tempfile
import pyarrow.parquet as pq
import zstandard
from .config import ROOT

COLUMNS = ('hash', 'block_timestamp', 'from_address', 'to_address', 'value', 'receipt_status')
PLAN_PATH = ROOT / 'research/onchain-graph-2026-09-16/fullpanel/plan.json'
PLAN_SHA = '19f3716454216afc172aec2939a9908ba3b57921e99249951e1860b995d1d691'


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _load(path, expected=None):
    raw = Path(path).read_bytes()
    if expected is not None and digest(raw) != expected:
        raise ValueError(f'metadata hash mismatch {path}')
    return json.loads(raw)


def load_plan() -> dict:
    return _load(PLAN_PATH, PLAN_SHA)


def _span(blob, start, end, base):
    path = Path(base) / blob['path']
    if path.stat().st_size != blob['stored_bytes']:
        raise ValueError('stored size differs')
    if blob['raw_bytes'] != end - start or blob['codec'] != 'zstd':
        raise ValueError('range framing differs')
    return {'path': str(path), 'start': start, 'end': end,
            **{k: blob[k] for k in ('raw_bytes', 'raw_sha256', 'stored_bytes', 'stored_sha256', 'codec')}}


def _ordinary(entry, day, expected_rows):
    manifest = _load(ROOT / entry['manifest']['path'], entry['manifest']['sha256'])
    if manifest['status'] != 'complete' or manifest['date'] != day:
        raise ValueError('incomplete source')
    directory = Path(entry['directory']); files = {f['path']: f for f in manifest['files']}
    def read(name): return _load(directory / name, files[name]['sha256'])
    projection = read('projection.json'); obj = projection['object']
    requests = {}
    for name in files:
        if re.fullmatch(r'request-\d+\.json', name):
            receipt = read(name)
            if receipt['url'].endswith(obj['key']) and receipt['status'] == 206:
                a, b = map(int, receipt['request_headers']['Range'].removeprefix('bytes=').split('-'))
                if receipt['request_headers'].get('If-Match') != obj['etag'] or receipt['response_headers']['etag'] != obj['etag']:
                    raise ValueError('object ETag differs')
                requests[(a, b + 1)] = receipt
    ranges = [(r['start'], r['end'] + 1) for r in projection['ranges']] + [(projection['footer_start'], obj['size'])]
    spans = []
    for a, b in ranges:
        blob = requests[(a, b)]['blob']; registered = files[blob['path']]
        if registered['sha256'] != blob['stored_sha256'] or registered['bytes'] != blob['stored_bytes']:
            raise ValueError('blob inventory differs')
        spans.append(_span(blob, a, b, directory))
    if sum(projection['groups']) != expected_rows:
        raise ValueError('row denominator differs')
    return {'size': obj['size'], 'spans': spans, 'object': obj}


def _special_2024_01_01(expected_rows):
    prefix = ROOT / 'research/onchain-graph-2026-09-16'
    plan = _load(prefix / 'prototype/plan.json', '4e3716ad928b43902b111e0c4a1e849bfd7c9b35cdbc32993dcc887ddcf07800')
    receipt = _load(prefix / 'pilot/artifacts/results/context-2024-01-01.json')
    if plan['rows'] != expected_rows:
        raise ValueError('context rows differ')
    spans = [_span(b, r['start'], r['end'] + 1, ROOT) for r, b in zip(plan['ranges'], receipt['benchmark']['blobs'], strict=True)]
    footer_path = ROOT / 'research_runs/eth-graph-source-20260916/outputs/request-11.json'
    footer = _load(footer_path, '4b568e9995a4d7cb234c6103dda1b4be55389b49e4252c6e8b65c8e007dec16e')
    spans.append({'path': str(footer_path), 'start': plan['footer_start'], 'end': plan['object']['size'],
                  'raw_bytes': footer['bytes'], 'raw_sha256': footer['sha256'], 'stored_bytes': footer_path.stat().st_size,
                  'stored_sha256': digest(footer_path.read_bytes()), 'codec': 'receipt_base64'})
    return {'size': plan['object']['size'], 'spans': spans, 'object': plan['object']}


def day_manifest(plan: dict, day: str) -> dict:
    rows = plan['expected_rows'][day]
    return _special_2024_01_01(rows) if day == '2024-01-01' else _ordinary(plan['captures'][day], day, rows)


class AcquiredReader(io.RawIOBase):
    """Random-access view over a sparse temp file; reads outside acquired intervals are errors."""
    def __init__(self, file, intervals, size):
        self.file, self.intervals, self.size = file, intervals, size
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.file.tell()
    def seek(self, offset, whence=0): return self.file.seek(offset, whence)
    def read(self, size=-1):
        pos = self.tell(); end = self.size if size is None or size < 0 else min(self.size, pos + size)
        if pos < end and not any(a <= pos and end <= b for a, b in self.intervals):
            raise ValueError(f'read outside acquired ranges [{pos},{end})')
        return self.file.read(end - pos)
    def readinto(self, buffer):
        data = self.read(len(buffer)); buffer[:len(data)] = data; return len(data)


def _decompress(span, stored):
    if span['codec'] == 'zstd':
        n = span['end'] - span['start']
        if zstandard.frame_content_size(stored) != n:
            raise ValueError('range decompression length')
        return zstandard.ZstdDecompressor().decompress(stored, max_output_size=n, allow_extra_data=False)
    if span['codec'] == 'receipt_base64':
        import base64
        receipt = json.loads(stored); raw = base64.b64decode(receipt['body_base64'], validate=True)
        if len(raw) != span['end'] - span['start'] or receipt['sha256'] != span['raw_sha256']:
            raise ValueError('receipt body framing')
        return raw
    raise ValueError('unregistered range codec')


def projected_table(manifest: dict, scratch: Path, columns=COLUMNS):
    size = manifest['size']
    if not isinstance(size, int) or not 12 <= size <= 8 * 1024 ** 3:
        raise ValueError('logical parquet size limit')
    intervals = []
    with tempfile.TemporaryFile(dir=scratch) as file:
        file.truncate(size)
        for span in sorted(manifest['spans'], key=lambda s: s['start']):
            a, b = span['start'], span['end']
            if not 0 <= a < b <= size or (intervals and a < intervals[-1][1]):
                raise ValueError('invalid/overlapping ranges')
            stored = Path(span['path']).read_bytes()
            if len(stored) != span['stored_bytes'] or digest(stored) != span['stored_sha256']:
                raise ValueError('stored range hash')
            raw = _decompress(span, stored)
            if digest(raw) != span['raw_sha256']:
                raise ValueError('raw range hash')
            file.seek(a); file.write(raw); intervals.append((a, b))
        file.flush(); file.seek(size - 8); trailer = file.read(8)
        if trailer[4:] != b'PAR1':
            raise ValueError('invalid parquet trailer')
        length = int.from_bytes(trailer[:4], 'little')
        file.seek(size - length - 8); footer = file.read(length + 8)
        metadata = pq.read_metadata(io.BytesIO(b'PAR1' + footer))
        reader = AcquiredReader(file, intervals, size); reader.seek(0)
        parquet = pq.ParquetFile(reader, metadata=metadata, pre_buffer=False)
        return parquet.read(columns=list(columns), use_threads=False)


def read_day(manifest: dict, scratch: Path, columns=COLUMNS):
    return projected_table(manifest, scratch, columns)
```

Note: the synthetic-test spans cover the whole file, so `AcquiredReader` never refuses; real manifests only cover projected columns plus footer, which is why `columns` must be a subset of the projected ones.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_sources.py -q`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/sources.py tests/research/onchain_b/test_sources.py
git commit -m "feat(onchain-b): hash-verified day reader over retained spans"
```

---

### Task 3: Calendar (weeks, availability, fold, warm-up)

**Files:**
- Create: `tradingagents/research/onchain_b/calendar.py`
- Test: `tests/research/onchain_b/test_calendar.py`

**Interfaces:**
- Produces: `weeks() -> list[str]` (156 Monday ISO dates); `week_days(week) -> list[str]` (7 ISO dates); `week_end(week) -> date` (next Monday); `available_week(day: date) -> str | None`; `decision_dates(split: 'train'|'test') -> list[date]`; `window(d: date) -> list[date]` (28 step days ending at d); `LOOKBACK = 28`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b/test_calendar.py
from datetime import date
from tradingagents.research.onchain_b import calendar as cal

def test_week_denominator():
    w = cal.weeks(); assert len(w) == 156 and w[0] == '2022-01-03' and w[-1] == '2024-12-23'
    assert cal.week_days('2022-01-03') == [f'2022-01-0{k}' for k in range(3, 10)]

def test_availability_lag():
    assert cal.available_week(date(2022, 1, 9)) is None
    assert cal.available_week(date(2022, 1, 10)) == '2022-01-03'
    assert cal.available_week(date(2022, 1, 16)) == '2022-01-03'
    assert cal.available_week(date(2022, 1, 17)) == '2022-01-10'
    assert cal.available_week(date(2024, 12, 31)) == '2024-12-23'

def test_fold_membership_and_warmup():
    train, test = cal.decision_dates('train'), cal.decision_dates('test')
    assert train[0] == date(2022, 2, 6) and train[-1] == date(2023, 12, 30) and len(train) == 693
    assert test[0] == date(2024, 1, 1) and test[-1] == date(2024, 12, 30) and len(test) == 365
    assert all(d + __import__('datetime').timedelta(days=1) < date(2024, 1, 1) for d in train)

def test_warmup_exclusion():
    # 2022-02-05 has a step (2022-01-09) with no available week → not a training decision date
    assert date(2022, 2, 5) not in cal.decision_dates('train')
    assert all(cal.available_week(t) is not None for t in cal.window(date(2022, 2, 6)))

def test_window_length():
    w = cal.window(date(2023, 3, 1)); assert len(w) == 28 and w[-1] == date(2023, 3, 1) and w[0] == date(2023, 2, 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_calendar.py -q`
Expected: FAIL (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/calendar.py
"""Monday-anchored UTC weeks, one-day graph lag, initial-ETH fold membership."""
from __future__ import annotations
from datetime import date, timedelta
from functools import lru_cache
from .config import load

LOOKBACK = 28
_G = load('graph'); _C = load('calendar')
FIRST_WEEK = date.fromisoformat(_G['first_week']); LAST_WEEK = date.fromisoformat(_G['last_week'])
LAG = timedelta(days=_C['graph_lag_days'])


@lru_cache(maxsize=None)
def weeks() -> list[str]:
    out, d = [], FIRST_WEEK
    while d <= LAST_WEEK:
        out.append(d.isoformat()); d += timedelta(days=7)
    assert len(out) == _G['expected_weeks']
    return out


def week_days(week: str) -> list[str]:
    start = date.fromisoformat(week)
    return [(start + timedelta(days=k)).isoformat() for k in range(7)]


def week_end(week: str) -> date:
    return date.fromisoformat(week) + timedelta(days=7)


def available_week(day: date) -> str | None:
    """Latest week whose end (next Monday) + lag <= start of day+1, i.e. end <= day."""
    best = None
    for w in weeks():
        if week_end(w) + LAG <= day + timedelta(days=1):
            best = w
        else:
            break
    return best


def window(d: date) -> list[date]:
    return [d - timedelta(days=LOOKBACK - 1 - k) for k in range(LOOKBACK)]


def _complete(d: date) -> bool:
    return all(available_week(t) is not None for t in window(d))


@lru_cache(maxsize=None)
def decision_dates(split: str) -> list[date]:
    label_end = date.fromisoformat(_C['train_label_end_exclusive'])
    if split == 'train':
        start = FIRST_WEEK; end = label_end - timedelta(days=2)  # label day d+1 < label_end
    elif split == 'test':
        start = date.fromisoformat(_C['test_decision_start']); end = date.fromisoformat(_C['test_decision_end'])
    else:
        raise ValueError(split)
    out, d = [], start
    while d <= end:
        if _complete(d):
            out.append(d)
        d += timedelta(days=1)
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_calendar.py -q`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/calendar.py tests/research/onchain_b/test_calendar.py
git commit -m "feat(onchain-b): calendar with graph lag and fold membership"
```

---

### Task 4: Prices (Coin Metrics reader, labels, training-only scaling)

**Files:**
- Create: `tradingagents/research/onchain_b/prices.py`
- Test: `tests/research/onchain_b/test_prices.py`

**Interfaces:**
- Produces: `load_prices(path=DEFAULT) -> dict[date, float]`; `direction(prices, d) -> int` (1 if close[d+1] > close[d] else 0); `target_usd(prices, d) -> float` (close[d+1]); `Scaler(mean, std)` with `.fit(prices, days: list[date])`, `.transform(x)`, `.inverse(x)`; `DEFAULT` path constant.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b/test_prices.py
from datetime import date
from tradingagents.research.onchain_b import prices as P

def test_csv_parse(tmp_path):
    p = tmp_path / 'r.bin'
    p.write_text('time,AdrActCnt,PriceUSD\n2022-01-03T00:00:00.000000000Z,1,3700.5\n2022-01-04T00:00:00.000000000Z,1,3800.25\n')
    px = P.load_prices(p)
    assert px[date(2022, 1, 3)] == 3700.5 and px[date(2022, 1, 4)] == 3800.25
    assert P.direction(px, date(2022, 1, 3)) == 1 and P.target_usd(px, date(2022, 1, 3)) == 3800.25

def test_direction_tie_is_zero():
    px = {date(2022, 1, 3): 1.0, date(2022, 1, 4): 1.0}
    assert P.direction(px, date(2022, 1, 3)) == 0

def test_scaler_roundtrip():
    px = {date(2022, 1, k): float(k) for k in range(1, 11)}
    s = P.Scaler().fit(px, [date(2022, 1, k) for k in range(1, 11)])
    assert abs(s.inverse(s.transform(7.0)) - 7.0) < 1e-12 and abs(s.mean - 5.5) < 1e-12

def test_real_file_covers_study():
    px = P.load_prices()
    assert date(2022, 1, 1) in px and date(2024, 12, 31) in px and all(v > 0 for v in px.values())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_prices.py -q`
Expected: FAIL (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/prices.py
"""Coin Metrics daily PriceUSD (declared deviation from the paper's Yahoo source)."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import csv, math
from .config import ROOT

DEFAULT = ROOT / ('research_artifacts/onchain-paper-replication-2026-09-24/sources/paper-prices-coinmetrics-eth-20260924/'
                  'capture/da30555fdfc60ac1d51a62b598421a339e5ab417bceb9e7f8bf29a4d19630f9e/response.bin')


def load_prices(path: Path = DEFAULT) -> dict[date, float]:
    out = {}
    with open(path, newline='') as fh:
        for row in csv.DictReader(fh):
            v = row.get('PriceUSD', '')
            if v == '':
                continue
            d = date.fromisoformat(row['time'][:10]); x = float(v)
            if not math.isfinite(x) or x <= 0 or d in out:
                raise ValueError(f'bad price row {row}')
            out[d] = x
    return out


def target_usd(prices, d: date) -> float:
    return prices[d + timedelta(days=1)]


def direction(prices, d: date) -> int:
    return int(prices[d + timedelta(days=1)] > prices[d])


@dataclass
class Scaler:
    mean: float = 0.0
    std: float = 1.0
    def fit(self, prices, days):
        xs = [prices[t] for t in days]; n = len(xs)
        self.mean = sum(xs) / n
        var = sum((x - self.mean) ** 2 for x in xs) / n
        self.std = math.sqrt(var) if var > 0 else 1.0
        return self
    def transform(self, x): return (x - self.mean) / self.std
    def inverse(self, z): return z * self.std + self.mean
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_prices.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/prices.py tests/research/onchain_b/test_prices.py
git commit -m "feat(onchain-b): price reader, labels and training-only scaler"
```

---

### Task 5: Weekly graphs (admission, aggregation, top-K subgraph, storage)

**Files:**
- Create: `tradingagents/research/onchain_b/weekly.py`
- Test: `tests/research/onchain_b/test_weekly.py`

**Interfaces:**
- Produces: `admitted_events(table) -> (pa.Table[from_address,to_address,value_eth], counters: dict)`; `aggregate_pairs(tables) -> pa.Table[src,dst,count,value_eth]`; `WeekGraph` dataclass (`week: str`, `addresses: np.ndarray[S42]` lexicographically sorted, `x: float32[K,4]`, `edge_index: int32[2,E]` (src,dst local), `edge_attr: float32[E,2]`, `edge_count: int64[E]`, `summary: dict`); `top_k_subgraph(pairs, k, week) -> WeekGraph`; `save(graph, dir)`, `load(dir) -> WeekGraph`; `full_summary(pairs) -> dict` (nodes, edges, density).

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b/test_weekly.py
import numpy as np, pyarrow as pa, pytest
from tradingagents.research.onchain_b import weekly as W

A, B, C, D = ('0x' + c * 40 for c in 'abcd')

def _day(rows):
    return pa.table({'hash': ['0x' + f'{i:064x}' for i, _ in enumerate(rows)],
                     'block_timestamp': pa.array([0] * len(rows), pa.timestamp('ns')),
                     'from_address': [r[0] for r in rows], 'to_address': [r[1] for r in rows],
                     'value': [r[2] for r in rows], 'receipt_status': [r[3] for r in rows]})

def test_admission_filters_and_counters():
    t = _day([(A, B, 3e18, 1), (A, B, 2e18, 1), (B, C, 1e18, 0), (A, None, 1e18, 1), (C, A, 0.0, 1), (A, A, 1e18, 1)])
    events, counters = W.admitted_events(t)
    assert events.num_rows == 3 and counters == {'rows': 6, 'admitted': 3, 'failed': 1, 'null_recipient': 1, 'zero_value': 1}

def test_duplicate_hash_rejected():
    t = _day([(A, B, 1e18, 1), (A, B, 1e18, 1)]); t = t.set_column(0, 'hash', pa.array(['0x' + '1' * 64] * 2))
    with pytest.raises(ValueError, match='duplicate'):
        W.admitted_events(t)

def test_aggregation_and_subgraph():
    ev1, _ = W.admitted_events(_day([(A, B, 3e18, 1), (A, B, 2e18, 1), (A, A, 1e18, 1)]))
    ev2, _ = W.admitted_events(_day([(B, C, 1e18, 1), (D, C, 1e18, 1)]))
    pairs = W.aggregate_pairs([ev1, ev2])
    rows = {(r['src'], r['dst']): (r['count'], r['value_eth']) for r in pairs.to_pylist()}
    assert rows[(A, B)] == (2, 5.0) and rows[(A, A)] == (1, 1.0) and rows[(B, C)] == (1, 1.0)
    g = W.top_k_subgraph(pairs, 3, '2022-01-03')   # activity: A=2+1+1(self twice)=4? see rule below
    assert list(g.addresses.astype(str)) == sorted([A, B, C])   # D dropped (activity 1 < C's 2)
    e = {(int(s), int(d)) for s, d in g.edge_index.T}
    assert e == {(0, 1), (0, 0), (1, 2)}
    assert g.summary['k_effective'] == 3 and g.summary['full_nodes'] == 4
    # node features recomputed on induced graph: B has in_count 2 (A→B count 2), out_count 1
    xb = g.x[1]; assert np.isclose(xb[0], np.log1p(2)) and np.isclose(xb[1], np.log1p(1))

def test_fewer_than_k_nodes():
    ev, _ = W.admitted_events(_day([(A, B, 1e18, 1)]))
    g = W.top_k_subgraph(W.aggregate_pairs([ev]), 50, '2022-01-03')
    assert g.summary['k_effective'] == 2 and g.x.shape == (2, 4)

def test_save_load_roundtrip(tmp_path):
    ev, _ = W.admitted_events(_day([(A, B, 1e18, 1), (B, A, 2e18, 1)]))
    g = W.top_k_subgraph(W.aggregate_pairs([ev]), 2, '2022-01-03'); W.save(g, tmp_path)
    h = W.load(tmp_path)
    assert (h.addresses == g.addresses).all() and np.array_equal(h.edge_index, g.edge_index) and h.summary == g.summary
```

Activity rule for the test: activity(addr) = Σ count of admitted transactions where addr is sender + Σ where addr is recipient (a self-transfer counts twice). In `test_aggregation_and_subgraph`: A: out 2+1, in 1 → 4; B: in 2, out 1 → 3; C: in 2 → 2; D: out 1 → 1. Top-3 = A, B, C.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_weekly.py -q`
Expected: FAIL (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/weekly.py
"""Admitted events → ordered-pair aggregates → paper-scale top-K induced subgraph."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import json, os, tempfile
import numpy as np
import pyarrow as pa, pyarrow.compute as pc

ADDR = r'^0x[0-9a-f]{40}$'


def admitted_events(table: pa.Table):
    n = table.num_rows
    hashes = table.column('hash')
    if pc.count_distinct(hashes).as_py() != n:
        raise ValueError('duplicate transaction hash in day')
    status_ok = pc.equal(table.column('receipt_status'), 1)
    to_lower = pc.utf8_lower(table.column('to_address')); from_lower = pc.utf8_lower(table.column('from_address'))
    recipient_ok = pc.fill_null(pc.match_substring_regex(to_lower, ADDR), False)
    value_ok = pc.greater(table.column('value'), 0.0)
    counters = {'rows': n,
                'failed': int(pc.sum(pc.invert(status_ok)).as_py() or 0),
                'null_recipient': int(pc.sum(pc.and_(status_ok, pc.invert(recipient_ok))).as_py() or 0),
                'zero_value': int(pc.sum(pc.and_(pc.and_(status_ok, recipient_ok), pc.invert(value_ok))).as_py() or 0)}
    mask = pc.and_(pc.and_(status_ok, recipient_ok), value_ok)
    if not pc.all(pc.fill_null(pc.match_substring_regex(from_lower, ADDR), False)).as_py():
        raise ValueError('malformed sender address')
    out = pa.table({'from_address': from_lower, 'to_address': to_lower,
                    'value_eth': pc.divide(table.column('value'), 1e18)}).filter(mask)
    counters['admitted'] = out.num_rows
    return out, counters


def aggregate_pairs(tables) -> pa.Table:
    t = pa.concat_tables(tables)
    g = t.group_by(['from_address', 'to_address']).aggregate([('value_eth', 'sum'), ('value_eth', 'count')])
    return g.rename_columns(['src', 'dst', 'value_eth', 'count']).select(['src', 'dst', 'count', 'value_eth'])


@dataclass
class WeekGraph:
    week: str
    addresses: np.ndarray
    x: np.ndarray
    edge_index: np.ndarray
    edge_attr: np.ndarray
    edge_count: np.ndarray
    summary: dict = field(default_factory=dict)
    @property
    def n(self): return len(self.addresses)
    @property
    def e(self): return self.edge_index.shape[1]


def _index(pairs):
    src = np.asarray(pairs.column('src').to_numpy(zero_copy_only=False)).astype('S42')
    dst = np.asarray(pairs.column('dst').to_numpy(zero_copy_only=False)).astype('S42')
    count = pairs.column('count').to_numpy().astype(np.int64); value = pairs.column('value_eth').to_numpy().astype(np.float64)
    addresses, inverse = np.unique(np.concatenate([src, dst]), return_inverse=True)
    return addresses, inverse[:len(src)], inverse[len(src):], count, value


def full_summary(pairs) -> dict:
    addresses, s, d, count, value = _index(pairs); n = len(addresses); e = len(s)
    return {'full_nodes': int(n), 'full_edges': int(e), 'full_density': float(e / (n * (n - 1))) if n > 1 else 0.0,
            'full_transactions': int(count.sum())}


def top_k_subgraph(pairs: pa.Table, k: int, week: str) -> WeekGraph:
    addresses, s, d, count, value = _index(pairs); n = len(addresses)
    activity = np.bincount(s, weights=count, minlength=n) + np.bincount(d, weights=count, minlength=n)
    order = np.lexsort((np.arange(n), -activity))          # activity desc, then address (index) asc
    keep = np.zeros(n, bool); keep[order[:min(k, n)]] = True
    sel = np.flatnonzero(keep)                              # already lexicographic
    local = -np.ones(n, np.int64); local[sel] = np.arange(len(sel))
    m = keep[s] & keep[d]
    ls, ld, lc, lv = local[s[m]], local[d[m]], count[m], value[m]
    eo = np.lexsort((ld, ls)); ls, ld, lc, lv = ls[eo], ld[eo], lc[eo], lv[eo]
    kk = len(sel)
    x = np.stack([np.log1p(np.bincount(ld, weights=lc, minlength=kk)), np.log1p(np.bincount(ls, weights=lc, minlength=kk)),
                  np.log1p(np.bincount(ld, weights=lv, minlength=kk)), np.log1p(np.bincount(ls, weights=lv, minlength=kk))], 1).astype(np.float32)
    edge_attr = np.stack([np.log1p(lc), np.log1p(lv)], 1).astype(np.float32)
    summary = {**full_summary(pairs), 'k_requested': int(k), 'k_effective': int(kk), 'edges': int(len(ls)),
               'density': float(len(ls) / (kk * (kk - 1))) if kk > 1 else 0.0,
               'min_activity_kept': float(activity[sel].min()) if kk else 0.0}
    return WeekGraph(week, addresses[sel], x, np.stack([ls, ld]).astype(np.int32), edge_attr, lc.astype(np.int64), summary)


def save(g: WeekGraph, directory: Path):
    directory = Path(directory); tmp = Path(tempfile.mkdtemp(dir=directory.parent, prefix='.tmp-'))
    np.save(tmp / 'addresses.npy', g.addresses); np.save(tmp / 'x.npy', g.x); np.save(tmp / 'edge_index.npy', g.edge_index)
    np.save(tmp / 'edge_attr.npy', g.edge_attr); np.save(tmp / 'edge_count.npy', g.edge_count)
    (tmp / 'summary.json').write_text(json.dumps({'week': g.week, **g.summary}, indent=1, sort_keys=True))
    os.replace(tmp, directory)


def load(directory: Path) -> WeekGraph:
    directory = Path(directory); s = json.loads((directory / 'summary.json').read_text()); week = s.pop('week')
    return WeekGraph(week, np.load(directory / 'addresses.npy'), np.load(directory / 'x.npy'), np.load(directory / 'edge_index.npy'),
                     np.load(directory / 'edge_attr.npy'), np.load(directory / 'edge_count.npy'), s)
```

If `os.replace` of a directory onto an existing directory fails on this filesystem, `save` must first check `directory.exists()` and raise (outputs are immutable; the CLI skips existing weeks).

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_weekly.py -q`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/weekly.py tests/research/onchain_b/test_weekly.py
git commit -m "feat(onchain-b): admitted events, pair aggregation, top-K weekly subgraph"
```

---

### Task 6: Neighborhoods (CSR, weak one-hop with N_max)

**Files:**
- Create: `tradingagents/research/onchain_b/neighborhoods.py`
- Test: `tests/research/onchain_b/test_neighborhoods.py`

**Interfaces:**
- Produces: `Graph` NamedTuple (`x: float64[n,4]`, `edge_index: int64[2,l]`, `edge_attr: float64[l,2]`, `nodes: int64[n]` global ids, `center: int` local index); `Adjacency.from_week(week: WeekGraph)` with `.neighborhood(center: int, n_max: int) -> Graph`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b/test_neighborhoods.py
import numpy as np
from tradingagents.research.onchain_b.weekly import WeekGraph
from tradingagents.research.onchain_b.neighborhoods import Adjacency

def _week():
    # 0→1 (c3), 1→0 (c1), 0→2 (c1), 2→3 (c5), 3→0 (c2), 0→0 (c1)
    ei = np.array([[0, 1, 0, 2, 3, 0], [1, 0, 2, 3, 0, 0]], np.int32)
    cnt = np.array([3, 1, 1, 5, 2, 1]); ea = np.stack([np.log1p(cnt), np.log1p(cnt * 1.5)], 1).astype(np.float32)
    x = np.arange(16, dtype=np.float32).reshape(4, 4)
    return WeekGraph('2022-01-03', np.array([b'a', b'b', b'c', b'd']), x, ei, ea, cnt, {})

def test_full_neighborhood_of_hub():
    g = Adjacency.from_week(_week()).neighborhood(0, 32)
    assert list(g.nodes) == [0, 1, 2, 3] and g.center == 0
    e = {(int(s), int(d)) for s, d in g.edge_index.T}
    assert e == {(0, 1), (1, 0), (0, 2), (2, 3), (3, 0), (0, 0)}   # induced, self loop kept, global order kept
    assert g.x.dtype == np.float64 and g.edge_attr.dtype == np.float64

def test_n_max_keeps_strongest_neighbors():
    g = Adjacency.from_week(_week()).neighborhood(0, 3)
    # interaction with 0: node1 = 3+1 = 4, node3 = 2, node2 = 1 → keep {0,1,3}
    assert list(g.nodes) == [0, 1, 3]
    e = {(int(s), int(d)) for s, d in g.edge_index.T}; assert e == {(0, 1), (1, 0), (2, 0), (0, 0)}

def test_isolated_center():
    w = _week(); g = Adjacency.from_week(w).neighborhood(3, 2)
    assert list(g.nodes) == [0, 3] or list(g.nodes) == [2, 3]   # tie 2 vs 0? counts: 3→0 is 2, 2→3 is 5 → {2,3}
    assert list(g.nodes) == [2, 3]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_neighborhoods.py -q`
Expected: FAIL (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/neighborhoods.py
"""Weak one-hop induced neighborhoods with the declared N_max cap (spec §5.3)."""
from __future__ import annotations
from typing import NamedTuple
import numpy as np
from .weekly import WeekGraph


class Graph(NamedTuple):
    x: np.ndarray
    edge_index: np.ndarray
    edge_attr: np.ndarray
    nodes: np.ndarray
    center: int


class Adjacency:
    def __init__(self, week: WeekGraph):
        self.w = week; n = week.n; src, dst = week.edge_index[0].astype(np.int64), week.edge_index[1].astype(np.int64)
        self.src, self.dst = src, dst
        o = np.argsort(src, kind='stable'); self.out_eid = o; self.out_ptr = np.searchsorted(src[o], np.arange(n + 1))
        i = np.argsort(dst, kind='stable'); self.in_eid = i; self.in_ptr = np.searchsorted(dst[i], np.arange(n + 1))
        self._mask = np.zeros(n, bool); self._local = np.full(n, -1, np.int64)

    @classmethod
    def from_week(cls, week): return cls(week)

    def _incident(self, c):
        return np.concatenate([self.out_eid[self.out_ptr[c]:self.out_ptr[c + 1]], self.in_eid[self.in_ptr[c]:self.in_ptr[c + 1]]])

    def neighborhood(self, center: int, n_max: int) -> Graph:
        w = self.w; eids = self._incident(center)
        other = np.where(self.src[eids] == center, self.dst[eids], self.src[eids])
        keep = other != center
        nbr, inv = np.unique(other[keep], return_inverse=True)
        strength = np.bincount(inv, weights=w.edge_count[eids[keep]], minlength=len(nbr)) if len(nbr) else np.zeros(0)
        order = np.lexsort((nbr, -strength))[:max(n_max - 1, 0)]
        nodes = np.sort(np.concatenate([[center], nbr[order]]).astype(np.int64))
        self._mask[nodes] = True; self._local[nodes] = np.arange(len(nodes))
        cand = np.unique(np.concatenate([self.out_eid[self.out_ptr[v]:self.out_ptr[v + 1]] for v in nodes]))
        sel = cand[self._mask[self.dst[cand]]]
        ls, ld = self._local[self.src[sel]], self._local[self.dst[sel]]
        eo = np.lexsort((ld, ls)); sel = sel[eo]
        self._mask[nodes] = False; self._local[nodes] = -1
        return Graph(w.x[nodes].astype(np.float64), np.stack([ls[eo], ld[eo]]).astype(np.int64),
                     w.edge_attr[sel].astype(np.float64), nodes, int(np.searchsorted(nodes, center)))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_neighborhoods.py -q`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/neighborhoods.py tests/research/onchain_b/test_neighborhoods.py
git commit -m "feat(onchain-b): capped weak one-hop neighborhoods"
```

---

### Task 7: Agreement functions and reference solver (literal Algorithm 1)

**Files:**
- Create: `tradingagents/research/onchain_b/matching/__init__.py`
- Create: `tradingagents/research/onchain_b/matching/agreement.py`
- Create: `tradingagents/research/onchain_b/matching/reference.py`
- Test: `tests/research/onchain_b/test_matching_reference.py`

**Interfaces:**
- Produces: `agreement.node_agreement(x1, x2) -> float64[n1,n2]`; `agreement.edge_agreement(f1, f2) -> float64[l1,l2]`; `agreement.score(g1, g2, hard: bool[n1,n2], alpha) -> float`; `agreement.MatchConfig` dataclass (`alpha, beta0, beta_final, beta_rate, max_iterations`) with `.from_json()`; `reference.match(g1: Graph, g2: Graph, cfg) -> Result(hard: bool[n1,n2], score: float, iterations: int, soft: float64[n1,n2])`; `reference.harden(soft) -> bool[n1,n2]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b/test_matching_reference.py
import itertools, math
import numpy as np
from tradingagents.research.onchain_b.neighborhoods import Graph
from tradingagents.research.onchain_b.matching import agreement as A, reference as R

def G(x, edges, ea=None):
    x = np.asarray(x, float); edges = np.asarray(edges, np.int64).reshape(2, -1)
    ea = np.zeros((edges.shape[1], 2)) if ea is None else np.asarray(ea, float)
    return Graph(x, edges, ea, np.arange(len(x)), 0)

CFG = A.MatchConfig(alpha=1.0, beta0=1.0, beta_final=30.0, beta_rate=0.075, max_iterations=50)

def test_agreement_values():
    assert A.node_agreement(np.zeros((1, 4)), np.zeros((1, 4)))[0, 0] == 1.0
    assert math.isclose(A.node_agreement(np.zeros((1, 4)), np.full((1, 4), 2.0))[0, 0], math.exp(-4.0))
    assert math.isclose(A.edge_agreement(np.array([[1.0, 3.0]]), np.array([[2.0, 1.0]]))[0, 0], math.exp(-2.5))

def test_score_identical_one_edge_graph_is_three_quarters():
    g = G([[0, 0, 0, 0], [1, 1, 1, 1]], [[0], [1]])
    hard = np.eye(2, dtype=bool)
    # edge term: 1/(2*sqrt(1*1)) = 0.5; node term: 2/sqrt(4) = 1; (0.5+1)/2 = 0.75  (paper Eq.1 literal)
    assert math.isclose(A.score(g, g, hard, 1.0), 0.75)

def test_zero_edge_graph():
    g1 = G([[0, 0, 0, 0]], np.zeros((2, 0))); g2 = G([[0, 0, 0, 0], [5, 5, 5, 5]], [[0], [1]])
    r = R.match(g1, g2, CFG)
    assert math.isfinite(r.score) and r.hard.sum() == 1 and r.hard[0, 0]

def test_schedule_has_48_temperatures():
    g = G([[0, 0, 0, 0]], np.zeros((2, 0)))
    assert R.match(g, g, CFG).iterations == 48

def test_reference_within_brute_force_bound():
    rng = np.random.default_rng(0)
    for _ in range(20):
        n1, n2 = rng.integers(2, 5), rng.integers(2, 5)
        x1, x2 = rng.normal(size=(n1, 4)), rng.normal(size=(n2, 4))
        e1 = rng.permutation(n1 * n1)[: rng.integers(1, n1 * n1 + 1)]; e2 = rng.permutation(n2 * n2)[: rng.integers(1, n2 * n2 + 1)]
        g1 = G(x1, [e1 // n1, e1 % n1], rng.normal(size=(len(e1), 2))); g2 = G(x2, [e2 // n2, e2 % n2], rng.normal(size=(len(e2), 2)))
        r = R.match(g1, g2, CFG)
        assert r.hard.sum() == min(n1, n2) and r.hard.sum(0).max() <= 1 and r.hard.sum(1).max() <= 1
        best = -1.0
        for perm in itertools.permutations(range(n2), min(n1, n2)):
            for rows in itertools.combinations(range(n1), min(n1, n2)):
                h = np.zeros((n1, n2), bool); h[list(rows), list(perm)] = True
                best = max(best, A.score(g1, g2, h, 1.0))
        assert r.score <= best + 1e-12
        assert math.isclose(r.score, A.score(g1, g2, r.hard, 1.0))

def test_relabeling_invariance():
    rng = np.random.default_rng(1); n1, n2 = 5, 4
    x1, x2 = rng.normal(size=(n1, 4)), rng.normal(size=(n2, 4)); e1 = np.array([[0, 1, 2, 3, 4, 0], [1, 2, 3, 4, 0, 2]]); e2 = np.array([[0, 1, 2, 3], [1, 2, 3, 0]])
    g1 = G(x1, e1, rng.normal(size=(6, 2))); g2 = G(x2, e2, rng.normal(size=(4, 2)))
    p = rng.permutation(n1); inv = np.argsort(p)
    g1p = G(x1[p], inv[e1], g1.edge_attr)   # node k of g1 becomes node inv[k]
    a, b = R.match(g1, g2, CFG), R.match(g1p, g2, CFG)
    assert math.isclose(a.score, b.score, rel_tol=1e-9) and np.array_equal(a.hard[p], b.hard)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_matching_reference.py -q`
Expected: FAIL (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/matching/__init__.py
```

```python
# tradingagents/research/onchain_b/matching/agreement.py
"""Eq. 1 agreement functions and objective (paper §2.2, literal)."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class MatchConfig:
    alpha: float
    beta0: float
    beta_final: float
    beta_rate: float
    max_iterations: int
    @classmethod
    def from_json(cls, d):
        return cls(float(d['alpha']), float(d['beta0']), float(d['beta_final']), float(d['beta_rate']), int(d['max_iterations']))


def node_agreement(x1, x2):
    d = x1[:, None, :] - x2[None, :, :]
    return np.exp(-np.mean(d * d, axis=2))


def edge_agreement(f1, f2):
    if len(f1) == 0 or len(f2) == 0:
        return np.zeros((len(f1), len(f2)))
    d = f1[:, None, :] - f2[None, :, :]
    return np.exp(-np.mean(d * d, axis=2))


def score(g1, g2, hard, alpha: float) -> float:
    n1, n2 = g1.x.shape[0], g2.x.shape[0]; l1, l2 = g1.edge_index.shape[1], g2.edge_index.shape[1]
    node = float((node_agreement(g1.x, g2.x) * hard).sum()) / np.sqrt(n1 * n2)
    edge = 0.0
    if l1 and l2:
        s1 = edge_agreement(g1.edge_attr, g2.edge_attr)
        u, v = g1.edge_index; i, j = g2.edge_index
        both = hard[u[:, None], i[None, :]] & hard[v[:, None], j[None, :]]
        edge = float((s1 * both).sum()) / (2.0 * np.sqrt(l1 * l2))
    return (edge + alpha * node) / (1.0 + alpha)
```

```python
# tradingagents/research/onchain_b/matching/reference.py
"""Per-pair literal Algorithm 1 (paper §2.2.3) with greedy hardening. Readable, not fast."""
from __future__ import annotations
from typing import NamedTuple
import numpy as np
from scipy.special import logsumexp
from .agreement import node_agreement, edge_agreement, score


class Result(NamedTuple):
    hard: np.ndarray
    score: float
    iterations: int
    soft: np.ndarray


def harden(soft: np.ndarray) -> np.ndarray:
    n1, n2 = soft.shape; work = soft.copy(); hard = np.zeros((n1, n2), bool)
    for _ in range(min(n1, n2)):
        k = int(np.argmax(work))          # first occurrence → row-major ties
        u, i = divmod(k, n2); hard[u, i] = True
        work[u, :] = -np.inf; work[:, i] = -np.inf
    return hard


def match(g1, g2, cfg) -> Result:
    V = node_agreement(g1.x, g2.x); n1, n2 = V.shape
    u, v = g1.edge_index; i, j = g2.edge_index
    W = 0.5 * edge_agreement(g1.edge_attr, g2.edge_attr)      # (l1, l2); the literal half coefficient
    M = V.copy(); beta = cfg.beta0; iterations = 0
    while beta <= cfg.beta_final and iterations < cfg.max_iterations:
        Q = cfg.alpha * V.copy()
        for a in range(len(u)):
            for b in range(len(i)):
                Q[u[a], i[b]] += W[a, b] * M[v[a], j[b]]
        L = beta * Q
        L = L - logsumexp(L, axis=1, keepdims=True)
        L = L - logsumexp(L, axis=0, keepdims=True)
        M = np.exp(L)
        beta *= 1.0 + cfg.beta_rate; iterations += 1
    hard = harden(M)
    return Result(hard, score(g1, g2, hard, cfg.alpha), iterations, M)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_matching_reference.py -q`
Expected: 6 passed (the brute-force test loops ≤ 4!·C(4,4) combos; fast)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/matching tests/research/onchain_b/test_matching_reference.py
git commit -m "feat(onchain-b): Eq.1 agreement and literal Algorithm 1 reference solver"
```

---

### Task 8: Batched solver (bucketed multi-pair, torch CPU float64)

**Files:**
- Create: `tradingagents/research/onchain_b/matching/batched.py`
- Test: `tests/research/onchain_b/test_matching_batched.py`

**Interfaces:**
- Consumes: `Graph`, `MatchConfig`, `agreement.node_agreement/edge_agreement`, `reference.match` (tests only).
- Produces: `match_many(pairs: list[tuple[Graph, Graph]], cfg, max_products=20_000_000) -> tuple[np.ndarray scores float64[P], list[np.ndarray hard]]`; `score_matrix(lefts: list[Graph], rights: list[Graph], cfg) -> float64[len(lefts), len(rights)]` (all left×right pairs, S(left, right)).

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b/test_matching_batched.py
import numpy as np
from tradingagents.research.onchain_b.neighborhoods import Graph
from tradingagents.research.onchain_b.matching import agreement as A, reference as R, batched as B

CFG = A.MatchConfig(1.0, 1.0, 30.0, 0.075, 50)

def rand_graph(rng, n, l):
    e = rng.integers(0, n, size=(2, l)) if l else np.zeros((2, 0), np.int64)
    return Graph(rng.normal(size=(n, 4)), e.astype(np.int64), rng.normal(size=(l, 2)), np.arange(n), 0)

def test_batched_matches_reference_single_bucket():
    rng = np.random.default_rng(2); pairs = [(rand_graph(rng, 4, 5), rand_graph(rng, 3, 4)) for _ in range(6)]
    scores, hards = B.match_many(pairs, CFG)
    for (g1, g2), s, h in zip(pairs, scores, hards):
        r = R.match(g1, g2, CFG); assert abs(s - r.score) <= 1e-9 and np.array_equal(h, r.hard)

def test_batched_mixed_edge_counts():
    rng = np.random.default_rng(3)
    pairs = [(rand_graph(rng, 5, l1), rand_graph(rng, 5, l2)) for l1, l2 in [(0, 3), (7, 0), (12, 9), (1, 1), (20, 20)]]
    scores, hards = B.match_many(pairs, CFG)
    for (g1, g2), s, h in zip(pairs, scores, hards):
        r = R.match(g1, g2, CFG); assert abs(s - r.score) <= 1e-9 and np.array_equal(h, r.hard)

def test_many_buckets_and_chunking():
    rng = np.random.default_rng(4)
    pairs = [(rand_graph(rng, rng.integers(1, 7), rng.integers(0, 10)), rand_graph(rng, rng.integers(1, 7), rng.integers(0, 10))) for _ in range(60)]
    scores, hards = B.match_many(pairs, CFG, max_products=50)   # forces many tiny chunks
    for (g1, g2), s, h in zip(pairs, scores, hards):
        r = R.match(g1, g2, CFG); assert abs(s - r.score) <= 1e-9 and np.array_equal(h, r.hard)

def test_score_matrix_shape_and_values():
    rng = np.random.default_rng(5); L = [rand_graph(rng, 3, 2) for _ in range(3)]; Rr = [rand_graph(rng, 4, 3) for _ in range(2)]
    S = B.score_matrix(L, Rr, CFG); assert S.shape == (3, 2)
    assert abs(S[1, 0] - R.match(L[1], Rr[0], CFG).score) <= 1e-9
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_matching_batched.py -q`
Expected: FAIL (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/matching/batched.py
"""Many (G1, G2) pairs at once: same arithmetic as reference.match, bucketed by (n1, n2).

Per temperature: one gather of M[v,j], one multiply by the fixed 0.5*s1 weights,
one index_add into Q, then log-domain row and column normalization. Hardening is
vectorized across the bucket. float64 throughout.
"""
from __future__ import annotations
from collections import defaultdict
import numpy as np
import torch
from .agreement import node_agreement, edge_agreement

torch.set_default_dtype(torch.float64)


def _products(g1, g2, n1, n2, offset):
    u, v = g1.edge_index; i, j = g2.edge_index; l1, l2 = len(u), len(i)
    if l1 == 0 or l2 == 0:
        return (np.zeros(0), np.zeros(0, np.int64), np.zeros(0, np.int64), l1, l2)
    w = 0.5 * edge_agreement(g1.edge_attr, g2.edge_attr)                 # (l1, l2)
    gi = (offset + v[:, None] * n2 + j[None, :]).ravel()                   # read M[v, j]
    si = (offset + u[:, None] * n2 + i[None, :]).ravel()                   # add into Q[u, i]
    return (w.ravel(), gi, si, l1, l2)


def _solve_chunk(pairs, n1, n2, cfg):
    B = len(pairs); nm = n1 * n2
    V = torch.from_numpy(np.stack([node_agreement(g1.x, g2.x) for g1, g2 in pairs]).reshape(B, nm))
    ws, gis, sis, l1s, l2s, seg = [], [], [], [], [], []
    for p, (g1, g2) in enumerate(pairs):
        w, gi, si, l1, l2 = _products(g1, g2, n1, n2, p * nm)
        ws.append(w); gis.append(gi); sis.append(si); l1s.append(l1); l2s.append(l2); seg.append(np.full(len(w), p, np.int64))
    w = torch.from_numpy(np.concatenate(ws)); gi = torch.from_numpy(np.concatenate(gis)); si = torch.from_numpy(np.concatenate(sis))
    seg = torch.from_numpy(np.concatenate(seg))
    M = V.clone(); beta = cfg.beta0; it = 0
    while beta <= cfg.beta_final and it < cfg.max_iterations:
        Q = cfg.alpha * V
        if len(w):
            Q = Q.reshape(-1).index_add(0, si, w * M.reshape(-1)[gi]).reshape(B, nm)
        L = (beta * Q).reshape(B, n1, n2)
        L = L - torch.logsumexp(L, dim=2, keepdim=True)
        L = L - torch.logsumexp(L, dim=1, keepdim=True)
        M = torch.exp(L).reshape(B, nm)
        beta *= 1.0 + cfg.beta_rate; it += 1
    # greedy hardening, vectorized over pairs
    work = M.reshape(B, n1, n2).clone(); hard = torch.zeros(B, n1, n2, dtype=torch.bool)
    ar = torch.arange(B)
    for _ in range(min(n1, n2)):
        k = torch.argmax(work.reshape(B, nm), dim=1); u, i = k // n2, k % n2
        hard[ar, u, i] = True; work[ar, u, :] = -np.inf; work[ar, :, i] = -np.inf
    hard_flat = hard.reshape(-1).to(torch.float64)
    node = (V * hard.reshape(B, nm)).sum(1) / np.sqrt(n1 * n2)
    edge = torch.zeros(B)
    if len(w):
        both = hard_flat[si] * hard_flat[gi]
        edge = edge.index_add(0, seg, 2.0 * w * both)
    denom = torch.tensor([2.0 * np.sqrt(l1 * l2) if l1 and l2 else 1.0 for l1, l2 in zip(l1s, l2s)])
    scores = ((edge / denom) + cfg.alpha * node) / (1.0 + cfg.alpha)
    return scores.numpy(), [h.numpy() for h in hard]


def match_many(pairs, cfg, max_products=20_000_000):
    buckets = defaultdict(list)
    for p, (g1, g2) in enumerate(pairs):
        buckets[(g1.x.shape[0], g2.x.shape[0])].append(p)
    scores = np.zeros(len(pairs)); hards = [None] * len(pairs)
    for (n1, n2), idx in buckets.items():
        chunk, load = [], 0
        def flush():
            s, h = _solve_chunk([pairs[q] for q in chunk], n1, n2, cfg)
            for q, sq, hq in zip(chunk, s, h):
                scores[q] = sq; hards[q] = hq
        for q in idx:
            g1, g2 = pairs[q]; cost = g1.edge_index.shape[1] * g2.edge_index.shape[1]
            if chunk and load + cost > max_products:
                flush(); chunk, load = [], 0
            chunk.append(q); load += cost
        if chunk:
            flush()
    return scores, hards


def score_matrix(lefts, rights, cfg):
    pairs = [(a, b) for a in lefts for b in rights]
    s, _ = match_many(pairs, cfg)
    return s.reshape(len(lefts), len(rights))
```

Note on tie-breaking: `torch.argmax` returns the first maximal index on CPU, matching `np.argmax` row-major; the test fixtures are continuous random values so ties do not arise, and the relabeling test in Task 7 covers tie-free invariance.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_matching_batched.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/matching/batched.py tests/research/onchain_b/test_matching_batched.py
git commit -m "feat(onchain-b): bucketed batched graduated-assignment solver"
```

---

### Task 9: Motif dictionary (sampling, pairwise distance, average linkage, medoids)

**Files:**
- Create: `tradingagents/research/onchain_b/dictionary.py`
- Test: `tests/research/onchain_b/test_dictionary.py`

**Interfaces:**
- Consumes: `WeekGraph`, `Adjacency`, `Graph`, `batched.score_matrix`, `MatchConfig`.
- Produces: `sample_centers(weeks: dict[str, WeekGraph], n_samples, n_max, seed) -> list[tuple[str, int]]`; `pairwise_distance(graphs, cfg) -> float64[S,S]`; `cluster_medoids(D, n_clusters) -> list[int]`; `Dictionary` dataclass (`motifs: list[Graph]`, `centers: list[tuple[str,int]]`, `medoids: list[int]`, `seed: int`, `n_max: int`); `build(weeks, cfg, n_samples, n_clusters, n_max, seed) -> Dictionary`; `save(dictionary, path)`, `load(path) -> Dictionary` (npz + json).

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b/test_dictionary.py
import numpy as np
from tradingagents.research.onchain_b import dictionary as D
from tradingagents.research.onchain_b.weekly import WeekGraph
from tradingagents.research.onchain_b.matching.agreement import MatchConfig

CFG = MatchConfig(1.0, 1.0, 30.0, 0.075, 50)

def _week(week, n, rng):
    ei = np.stack([rng.integers(0, n, 3 * n), rng.integers(0, n, 3 * n)]).astype(np.int32)
    cnt = rng.integers(1, 5, 3 * n); ea = np.stack([np.log1p(cnt), np.log1p(cnt)], 1).astype(np.float32)
    return WeekGraph(week, np.array([f'{k:042x}'.encode() for k in range(n)]), rng.normal(size=(n, 4)).astype(np.float32), ei, ea, cnt, {})

def test_sampling_reproducible_and_without_replacement():
    rng = np.random.default_rng(0); weeks = {'2022-01-03': _week('2022-01-03', 30, rng), '2022-01-10': _week('2022-01-10', 30, rng)}
    a = D.sample_centers(weeks, 12, 8, seed=11); b = D.sample_centers(weeks, 12, 8, seed=11); c = D.sample_centers(weeks, 12, 8, seed=23)
    assert a == b and a != c and len(set(a)) == 12

def test_overlap_halving_changes_weights():
    # two-node week: drawing node 0 (neighborhood {0,1}) must halve node 1's weight
    ei = np.array([[0], [1]], np.int32); w = WeekGraph('2022-01-03', np.array([b'0', b'1']), np.zeros((2, 4), np.float32), ei, np.zeros((1, 2), np.float32), np.array([1]), {})
    weights = D._initial_weights({'2022-01-03': w}); D._halve_inside({'2022-01-03': w}, weights, ('2022-01-03', 0), 8)
    assert weights[1] == 0.5 and weights[0] == 0.0

def test_cluster_medoids_exact_count_and_rule():
    D_ = np.array([[0, .1, .9, .95], [.1, 0, .9, .95], [.9, .9, 0, .2], [.95, .95, .2, 0]])
    med = D.cluster_medoids(D_, 2); assert sorted(med) == [0, 2]      # ties by smallest index inside cluster

def test_build_small_dictionary():
    rng = np.random.default_rng(1); weeks = {'2022-01-03': _week('2022-01-03', 40, rng)}
    d = D.build(weeks, CFG, n_samples=10, n_clusters=3, n_max=6, seed=11)
    assert len(d.motifs) == 3 and all(m.x.shape[0] <= 6 for m in d.motifs) and len(d.centers) == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_dictionary.py -q`
Expected: FAIL (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/dictionary.py
"""Paper §2.1: sampled neighborhoods → average-linkage clusters → medoid motifs."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import numpy as np
from scipy.cluster.hierarchy import linkage, cut_tree
from scipy.spatial.distance import squareform
from .neighborhoods import Adjacency, Graph
from .matching.batched import score_matrix


def _initial_weights(weeks):
    return np.ones(sum(w.n for w in weeks.values()), np.float64)


def _layout(weeks):
    keys = sorted(weeks); offsets = {}; o = 0
    for k in keys:
        offsets[k] = o; o += weeks[k].n
    return keys, offsets


def _halve_inside(weeks, weights, drawn, n_max, adjacency=None):
    keys, offsets = _layout(weeks); week, center = drawn
    adj = adjacency[week] if adjacency else Adjacency.from_week(weeks[week])
    g = adj.neighborhood(center, n_max)
    idx = offsets[week] + g.nodes
    weights[idx] *= 0.5
    weights[offsets[week] + center] = 0.0


def sample_centers(weeks, n_samples, n_max, seed):
    keys, offsets = _layout(weeks); weights = _initial_weights(weeks)
    adjacency = {k: Adjacency.from_week(weeks[k]) for k in keys}
    owner = np.concatenate([[k] * weeks[k].n for k in keys]); local = np.concatenate([np.arange(weeks[k].n) for k in keys])
    rng = np.random.Generator(np.random.PCG64(seed)); out = []
    for _ in range(n_samples):
        total = weights.sum()
        if total <= 0:
            raise ValueError('insufficient candidates')
        k = int(rng.choice(len(weights), p=weights / total))
        drawn = (str(owner[k]), int(local[k])); out.append(drawn)
        _halve_inside(weeks, weights, drawn, n_max, adjacency)
    return out


def pairwise_distance(graphs, cfg):
    S = score_matrix(graphs, graphs, cfg)
    D = 1.0 - 0.5 * (S + S.T); np.fill_diagonal(D, 0.0)
    return D


def cluster_medoids(D, n_clusters):
    Z = linkage(squareform(D, checks=False), method='average')
    labels = cut_tree(Z, n_clusters=n_clusters).ravel()
    medoids = []
    for c in range(n_clusters):
        members = np.flatnonzero(labels == c)
        sums = D[np.ix_(members, members)].sum(1)
        medoids.append(int(members[int(np.argmin(sums))]))      # argmin → first index on ties
    return medoids


@dataclass
class Dictionary:
    motifs: list
    centers: list
    medoids: list
    seed: int
    n_max: int


def build(weeks, cfg, n_samples, n_clusters, n_max, seed) -> Dictionary:
    centers = sample_centers(weeks, n_samples, n_max, seed)
    adjacency = {k: Adjacency.from_week(weeks[k]) for k in weeks}
    graphs = [adjacency[w].neighborhood(c, n_max) for w, c in centers]
    if len(graphs) < n_clusters:
        raise ValueError('fewer samples than clusters')
    D = pairwise_distance(graphs, cfg); med = cluster_medoids(D, n_clusters)
    return Dictionary([graphs[m] for m in med], centers, med, seed, n_max)


def save(d: Dictionary, path: Path):
    path = Path(path); path.mkdir(parents=True, exist_ok=True)
    arrays = {}
    for k, g in enumerate(d.motifs):
        arrays[f'x{k}'] = g.x; arrays[f'ei{k}'] = g.edge_index; arrays[f'ea{k}'] = g.edge_attr; arrays[f'nodes{k}'] = g.nodes
    np.savez(path / 'motifs.npz', **arrays)
    (path / 'dictionary.json').write_text(json.dumps({'centers': d.centers, 'medoids': d.medoids, 'seed': d.seed, 'n_max': d.n_max,
                                                      'centers_of_motifs': [list(d.centers[m]) for m in d.medoids]}, indent=1))


def load(path: Path) -> Dictionary:
    path = Path(path); meta = json.loads((path / 'dictionary.json').read_text()); z = np.load(path / 'motifs.npz')
    motifs = [Graph(z[f'x{k}'], z[f'ei{k}'], z[f'ea{k}'], z[f'nodes{k}'], 0) for k in range(len(meta['medoids']))]
    return Dictionary(motifs, [tuple(c) for c in meta['centers']], meta['medoids'], meta['seed'], meta['n_max'])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_dictionary.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/dictionary.py tests/research/onchain_b/test_dictionary.py
git commit -m "feat(onchain-b): seeded sampling, average-linkage dictionary, medoid motifs"
```

---

### Task 10: MCM features and the data-stage CLI (build-graphs, calibrate, dictionary, mcm)

**Files:**
- Create: `tradingagents/research/onchain_b/mcm.py`
- Create: `tradingagents/research/onchain_b/cli.py`
- Create: `tradingagents/research/onchain_b/runlog.py`
- Test: `tests/research/onchain_b/test_mcm.py`
- Test: `tests/research/onchain_b/test_cli_stages.py`

**Interfaces:**
- Produces: `mcm.compute_week(week: WeekGraph, dictionary: Dictionary, cfg, n_max, chunk=4096, log=None) -> float32[K, 32]`; `cli.main(argv)` with subcommands `build-graphs [--weeks W..] [--k K]`, `calibrate`, `dictionary --seed S`, `mcm --seed S [--weeks ..]`; `runlog.Log(path)` with `.event(**kv)` writing JSON lines including `rss_mb` and elapsed; artifact layout `ARTIFACTS/graphs/<week>/`, `ARTIFACTS/calibration/density.json`, `ARTIFACTS/dictionary/seed<S>/`, `ARTIFACTS/mcm/seed<S>/<week>.npy`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b/test_mcm.py
import numpy as np
from tradingagents.research.onchain_b import mcm, dictionary as D
from tradingagents.research.onchain_b.weekly import WeekGraph
from tradingagents.research.onchain_b.neighborhoods import Adjacency
from tradingagents.research.onchain_b.matching import reference as R
from tradingagents.research.onchain_b.matching.agreement import MatchConfig

CFG = MatchConfig(1.0, 1.0, 30.0, 0.075, 50)

def _week(n, rng):
    ei = np.stack([rng.integers(0, n, 2 * n), rng.integers(0, n, 2 * n)]).astype(np.int32); cnt = rng.integers(1, 4, 2 * n)
    return WeekGraph('2022-01-03', np.array([f'{k:042x}'.encode() for k in range(n)]), rng.normal(size=(n, 4)).astype(np.float32), ei,
                     np.stack([np.log1p(cnt), np.log1p(cnt)], 1).astype(np.float32), cnt, {})

def test_compute_week_matches_reference_per_cell():
    rng = np.random.default_rng(7); w = _week(25, rng)
    d = D.build({'2022-01-03': w}, CFG, n_samples=6, n_clusters=3, n_max=5, seed=11)
    F = mcm.compute_week(w, d, CFG, n_max=5, chunk=7)
    assert F.shape == (25, 3) and F.dtype == np.float32
    adj = Adjacency.from_week(w)
    for c in (0, 13, 24):
        for m, motif in enumerate(d.motifs):
            assert abs(float(F[c, m]) - R.match(adj.neighborhood(c, 5), motif, CFG).score) < 1e-6
```

```python
# tests/research/onchain_b/test_cli_stages.py
import json, numpy as np
from tradingagents.research.onchain_b import cli, weekly as W, config
import pyarrow as pa

def test_build_graphs_writes_week_and_skips_existing(tmp_path, monkeypatch):
    A, B = '0x' + 'a' * 40, '0x' + 'b' * 40
    day = pa.table({'hash': ['0x' + '1' * 64], 'block_timestamp': pa.array([0], pa.timestamp('ns')), 'from_address': [A], 'to_address': [B],
                    'value': [1e18], 'receipt_status': [1]})
    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path)
    monkeypatch.setattr(cli, '_read_day_tables', lambda week, scratch: [day] * 7)
    cli.main(['build-graphs', '--weeks', '2022-01-03', '--k', '10'])
    g = W.load(tmp_path / 'graphs' / '2022-01-03'); assert g.n == 2 and g.summary['k_effective'] == 2
    mtime = (tmp_path / 'graphs' / '2022-01-03' / 'summary.json').stat().st_mtime
    cli.main(['build-graphs', '--weeks', '2022-01-03', '--k', '10'])       # second run must skip
    assert (tmp_path / 'graphs' / '2022-01-03' / 'summary.json').stat().st_mtime == mtime
    log = [json.loads(l) for l in (tmp_path / 'logs' / 'build-graphs.jsonl').read_text().splitlines()]
    assert any(e.get('event') == 'week_done' for e in log) and all('rss_mb' in e for e in log)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_mcm.py tests/research/onchain_b/test_cli_stages.py -q`
Expected: FAIL (modules missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/runlog.py
from __future__ import annotations
from pathlib import Path
import json, resource, time


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


class Log:
    def __init__(self, path: Path):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True); self.t0 = time.time()
    def event(self, **kv):
        rec = {'t': round(time.time() - self.t0, 3), 'rss_mb': round(rss_mb(), 1), **kv}
        with open(self.path, 'a') as fh:
            fh.write(json.dumps(rec, sort_keys=True) + '\n')
        return rec
```

```python
# tradingagents/research/onchain_b/mcm.py
"""Per-week motif convolution: similarity of every node neighborhood to every motif (paper §2.3)."""
from __future__ import annotations
import numpy as np
from .neighborhoods import Adjacency
from .matching.batched import match_many


def compute_week(week, dictionary, cfg, n_max, chunk=4096, log=None):
    adj = Adjacency.from_week(week); motifs = dictionary.motifs; K = week.n; m = len(motifs)
    out = np.zeros((K, m), np.float32)
    for start in range(0, K, chunk):
        centers = range(start, min(K, start + chunk))
        hoods = [adj.neighborhood(c, n_max) for c in centers]
        pairs = [(h, mo) for h in hoods for mo in motifs]
        scores, _ = match_many(pairs, cfg)
        out[start:start + len(hoods)] = scores.reshape(len(hoods), m)
        if log:
            log.event(event='mcm_chunk', week=week.week, done=start + len(hoods), total=K)
    return out
```

```python
# tradingagents/research/onchain_b/cli.py
"""Stage runner. Every stage is idempotent at week / seed granularity and logs JSON lines."""
from __future__ import annotations
from pathlib import Path
import argparse, json, os, tempfile, time
import numpy as np
from . import calendar as cal, config, dictionary as D, mcm, sources, weekly as W
from .matching.agreement import MatchConfig
from .runlog import Log

ARTIFACTS = config.ARTIFACTS
CALIBRATION_WEEKS = ['2022-03-07', '2022-09-05', '2023-03-06', '2023-09-04']
CALIBRATION_K = [5000, 10000, 20000, 34000, 50000]


def _read_day_tables(week, scratch):
    plan = sources.load_plan()
    return [sources.read_day(sources.day_manifest(plan, day), scratch, sources.COLUMNS) for day in cal.week_days(week)]


def _week_pairs(week, scratch, log):
    tables, counters = [], []
    for table in _read_day_tables(week, scratch):
        ev, c = W.admitted_events(table); tables.append(ev); counters.append(c)
    pairs = W.aggregate_pairs(tables)
    log.event(event='week_aggregated', week=week, rows=sum(c['rows'] for c in counters), admitted=sum(c['admitted'] for c in counters))
    return pairs, counters


def _k():
    k = config.load('graph')['paper_scale']['K']
    if k is None:
        raise SystemExit('graph.json paper_scale.K is not frozen; run calibrate and commit CALIBRATION.md first')
    return int(k)


def build_graphs(args):
    log = Log(ARTIFACTS / 'logs' / 'build-graphs.jsonl'); k = args.k or _k(); weeks = args.weeks or cal.weeks()
    with tempfile.TemporaryDirectory(dir=ARTIFACTS) as scratch:
        for week in weeks:
            out = ARTIFACTS / 'graphs' / week
            if (out / 'summary.json').exists():
                log.event(event='week_skip', week=week); continue
            t = time.time(); pairs, counters = _week_pairs(week, Path(scratch), log)
            g = W.top_k_subgraph(pairs, k, week); g.summary['day_counters'] = counters
            W.save(g, out); log.event(event='week_done', week=week, seconds=round(time.time() - t, 1), **{kk: v for kk, v in g.summary.items() if kk != 'day_counters'})


def calibrate(args):
    """Label-free: density of top-K induced subgraphs on four training weeks vs the paper's 0.003."""
    log = Log(ARTIFACTS / 'logs' / 'calibrate.jsonl'); rows = []
    with tempfile.TemporaryDirectory(dir=ARTIFACTS) as scratch:
        for week in CALIBRATION_WEEKS:
            pairs, _ = _week_pairs(week, Path(scratch), log); full = W.full_summary(pairs)
            for k in CALIBRATION_K:
                g = W.top_k_subgraph(pairs, k, week)
                rows.append({'week': week, 'K': k, 'nodes': g.n, 'edges': g.e, 'density': g.summary['density'], **full})
                log.event(event='calibration_point', **rows[-1])
            rng = np.random.Generator(np.random.PCG64(20261012)); n = full['full_nodes']
            # random-50k alternative for the record: expected induced edges = E * (50000/n)^2
            rows.append({'week': week, 'K': 'random50000_expected', 'edges_expected': full['full_edges'] * (min(50000, n) / n) ** 2, **full})
    target = 0.003; summary = {}
    for k in CALIBRATION_K:
        dens = [r['density'] for r in rows if r.get('K') == k]
        summary[k] = {'mean_density': float(np.mean(dens)), 'log_gap': float(abs(np.log(np.mean(dens)) - np.log(target)))}
    chosen = min(summary, key=lambda k: summary[k]['log_gap'])
    out = ARTIFACTS / 'calibration'; out.mkdir(parents=True, exist_ok=True)
    (out / 'density.json').write_text(json.dumps({'rows': rows, 'summary': summary, 'chosen_K': chosen, 'target_density': target}, indent=1))
    print(json.dumps({'summary': summary, 'chosen_K': chosen}, indent=1))


def _training_weeks():
    first_test = cal.decision_dates('test')[0]
    return [w for w in cal.weeks() if cal.week_end(w) + cal.LAG <= first_test]   # weeks available before any test decision


def _load_weeks(weeks):
    return {w: W.load(ARTIFACTS / 'graphs' / w) for w in weeks}


def dictionary(args):
    log = Log(ARTIFACTS / 'logs' / f'dictionary-seed{args.seed}.jsonl'); dcfg = config.load('dictionary'); mcfg = MatchConfig.from_json(config.load('matching'))
    out = ARTIFACTS / 'dictionary' / f'seed{args.seed}'
    if (out / 'dictionary.json').exists():
        log.event(event='skip'); return
    weeks = _load_weeks(_training_weeks()); assert all(w < '2024' for w in weeks)
    t = time.time(); d = D.build(weeks, mcfg, dcfg['sample_count'], dcfg['size'], dcfg['n_max'], args.seed)
    D.save(d, out); log.event(event='done', seconds=round(time.time() - t, 1), motif_sizes=[int(m.x.shape[0]) for m in d.motifs], motif_edges=[int(m.edge_index.shape[1]) for m in d.motifs])


def mcm_stage(args):
    log = Log(ARTIFACTS / 'logs' / f'mcm-seed{args.seed}.jsonl'); dcfg = config.load('dictionary'); mcfg = MatchConfig.from_json(config.load('matching'))
    d = D.load(ARTIFACTS / 'dictionary' / f'seed{args.seed}'); out = ARTIFACTS / 'mcm' / f'seed{args.seed}'; out.mkdir(parents=True, exist_ok=True)
    for week in (args.weeks or cal.weeks()):
        target = out / f'{week}.npy'
        if target.exists():
            log.event(event='week_skip', week=week); continue
        g = W.load(ARTIFACTS / 'graphs' / week); t = time.time()
        F = mcm.compute_week(g, d, mcfg, dcfg['n_max'], log=log)
        tmp = target.with_suffix('.tmp.npy'); np.save(tmp, F); os.replace(tmp, target)
        log.event(event='week_done', week=week, seconds=round(time.time() - t, 1), cells=int(F.size), cells_per_s=round(F.size / max(time.time() - t, 1e-9), 1))


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b'); sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('build-graphs'); a.add_argument('--weeks', nargs='*'); a.add_argument('--k', type=int); a.set_defaults(fn=build_graphs)
    a = sub.add_parser('calibrate'); a.set_defaults(fn=calibrate)
    a = sub.add_parser('dictionary'); a.add_argument('--seed', type=int, required=True); a.set_defaults(fn=dictionary)
    a = sub.add_parser('mcm'); a.add_argument('--seed', type=int, required=True); a.add_argument('--weeks', nargs='*'); a.set_defaults(fn=mcm_stage)
    args = p.parse_args(argv); ARTIFACTS.mkdir(parents=True, exist_ok=True); args.fn(args)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_mcm.py tests/research/onchain_b/test_cli_stages.py -q`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/{mcm,cli,runlog}.py tests/research/onchain_b/test_mcm.py tests/research/onchain_b/test_cli_stages.py
git commit -m "feat(onchain-b): MCM features and data-stage CLI with JSON-lines logs"
```

- [ ] **Step 6: Operational: smoke-read one real day and record timing**

Run: `.venv/bin/python -c "from tradingagents.research.onchain_b import sources, weekly; import tempfile, time; p=sources.load_plan(); t=time.time(); tab=sources.read_day(sources.day_manifest(p,'2023-06-05'), tempfile.gettempdir()); ev,c=weekly.admitted_events(tab); print(tab.num_rows, c, round(time.time()-t,1),'s')"`
Expected: `1151611 {...} <60 s`. Record the number in `STATE.md` (no commit of data).

---

### Task 11: Calibration run and protocol freeze (CP1)

**Files:**
- Create: `research/onchain-replication-b-2026-10-12/CALIBRATION.md`
- Modify: `research/onchain-replication-b-2026-10-12/config/graph.json` (set `paper_scale.K`)
- Modify: `research/onchain-replication-b-2026-10-12/config/dictionary.json` (`n_max`, after Task 13's compute check if it changes)
- Modify: `research/onchain-replication-b-2026-10-12/STATE.md`

This task is operational; its "test" is the committed calibration note with the numbers.

- [ ] **Step 1: Run the density calibration**

Run: `nohup .venv/bin/python -m tradingagents.research.onchain_b.cli calibrate > research_artifacts/onchain-replication-b/logs/calibrate.out 2>&1 &`
Expected: four weeks × five K rows in `research_artifacts/onchain-replication-b/calibration/density.json`; wall ≈ 4 × (7 days × ~30 s) ≈ 15 min.

- [ ] **Step 2: Write CALIBRATION.md**

Table: week × K → nodes, edges, density; the random-50k expected edges row; mean density per K; chosen K with its log gap to 0.003; a sentence on the cap (K ≤ 50,000) and on the consequence if wrong ("a different K changes the node population; the paper's K is unknown"). Set `paper_scale.K` in `graph.json` to the chosen value.

- [ ] **Step 3: Launch the full graph build (156 weeks) under a memory cap**

Run: `systemd-run --user --unit onchain-b-graphs -p MemoryMax=12G -p WorkingDirectory=/home/malecada/master_thesis/TradingAgents-onchain-b /home/malecada/master_thesis/TradingAgents-onchain-b/.venv/bin/python -m tradingagents.research.onchain_b.cli build-graphs`
Expected: `week_done` events accumulate in `logs/build-graphs.jsonl`; ≈ 156 × 3–4 min ≈ 8–10 h. Monitor with `tail -f`; the stage resumes on restart.

- [ ] **Step 4: Commit the freeze**

```bash
git add research/onchain-replication-b-2026-10-12
git commit -m "docs(onchain-b): freeze paper-scale K from label-free density calibration (CP1 start)"
```

---

### Task 12: Model (MLP, GAT, pooling, attention LSTM, heads, price baselines)

**Files:**
- Create: `tradingagents/research/onchain_b/model.py`
- Test: `tests/research/onchain_b/test_model.py`

**Interfaces:**
- Produces: `GraphEncoder(cfg)` with `forward(mcm: float32[K,32], edge_index: int64[2,E]) -> float32[32]`; `AttentionLSTM(input_width, lstm_width, attention_width)` with `forward(seq: float32[B,T,F], lengths=None) -> float32[B,lstm_width]`; `FullModel(task: 'regression'|'classification', cfg)` with `forward(prices: float32[B,T], graph_vectors: float32[B,T,32]) -> float32[B,out]` and `.encoder`; `PriceModel(kind: 'lstm'|'gru'|'hlstm', task, cfg)` with `forward(prices: float32[B,T]) -> float32[B,out]`; `output_width(task) -> int`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b/test_model.py
import numpy as np, torch
from tradingagents.research.onchain_b import model as M, config

CFG = config.load('model')

def test_encoder_permutation_invariant():
    torch.manual_seed(0); enc = M.GraphEncoder(CFG); K, E = 30, 80
    mcm = torch.randn(K, 32); ei = torch.randint(0, K, (2, E))
    v = enc(mcm, ei)
    p = torch.randperm(K); inv = torch.argsort(p)
    v2 = enc(mcm[p], inv[ei])
    assert v.shape == (32,) and torch.allclose(v, v2, atol=1e-5)

def test_isolated_nodes_get_self_only():
    enc = M.GraphEncoder(CFG); mcm = torch.randn(5, 32); ei = torch.zeros((2, 0), dtype=torch.long)
    assert torch.isfinite(enc(mcm, ei)).all()

def test_full_model_gradients_everywhere():
    torch.manual_seed(1); m = M.FullModel('classification', CFG)
    prices = torch.randn(4, 28); gv = torch.randn(4, 28, 32, requires_grad=True)
    out = m(prices, gv); assert out.shape == (4, 2)
    out.sum().backward()
    for name, p in m.named_parameters():
        assert p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0, name
    assert gv.grad.abs().sum() > 0

def test_attention_ignores_padding():
    torch.manual_seed(2); att = M.AttentionLSTM(3, 8, 4); x = torch.randn(2, 6, 3)
    a = att(x, lengths=torch.tensor([6, 4])); x2 = x.clone(); x2[1, 4:] = 99.0
    b = att(x2, lengths=torch.tensor([6, 4])); assert torch.allclose(a[1], b[1], atol=1e-6)

def test_price_baselines_shapes():
    for kind in ('lstm', 'gru', 'hlstm'):
        m = M.PriceModel(kind, 'regression', CFG); assert m(torch.randn(3, 28)).shape == (3, 1)

def test_synthetic_learning():
    torch.manual_seed(3); m = M.PriceModel('lstm', 'regression', CFG); opt = torch.optim.Adam(m.parameters(), 1e-2)
    x = torch.randn(64, 28); y = x[:, -1:] * 2 + 1; first = None
    for step in range(500):
        opt.zero_grad(); loss = ((m(x) - y) ** 2).mean(); loss.backward(); opt.step()
        first = first or loss.item()
    assert loss.item() < 0.2 * first
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_model.py -q`
Expected: FAIL (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/model.py
"""MCM-MLP → directed GAT → mean pool → price join → LSTM → additive attention → head (spec §8)."""
from __future__ import annotations
import torch, torch.nn as nn, torch.nn.functional as F


def output_width(task): return 2 if task == 'classification' else 1


class GATLayer(nn.Module):
    def __init__(self, inp, width, heads, concat, slope):
        super().__init__(); self.W = nn.Linear(inp, heads * width, bias=False); self.a_src = nn.Parameter(torch.empty(heads, width)); self.a_dst = nn.Parameter(torch.empty(heads, width))
        self.heads, self.width, self.concat, self.slope = heads, width, concat, slope
        nn.init.xavier_uniform_(self.W.weight); bound = (6.0 / (2 * width + 1)) ** 0.5
        nn.init.uniform_(self.a_src, -bound, bound); nn.init.uniform_(self.a_dst, -bound, bound)
        self.bias = nn.Parameter(torch.zeros(heads * width if concat else width))

    def forward(self, h, edge_index):
        K = h.shape[0]; src, dst = edge_index
        loop = torch.arange(K, device=h.device); src = torch.cat([src, loop]); dst = torch.cat([dst, loop])   # incoming edges + self once
        Wh = self.W(h).view(K, self.heads, self.width)
        e = F.leaky_relu((Wh[src] * self.a_src).sum(-1) + (Wh[dst] * self.a_dst).sum(-1), self.slope)     # (E, heads)
        e_max = torch.full((K, self.heads), -1e30, dtype=e.dtype).index_reduce_(0, dst, e, 'amax', include_self=True)
        ex = torch.exp(e - e_max[dst]); denom = torch.zeros(K, self.heads, dtype=e.dtype).index_add_(0, dst, ex)
        alpha = ex / denom[dst]
        out = torch.zeros(K, self.heads, self.width, dtype=h.dtype).index_add_(0, dst, alpha.unsqueeze(-1) * Wh[src])
        out = out.reshape(K, -1) if self.concat else out.mean(1)
        return out + self.bias


class GraphEncoder(nn.Module):
    def __init__(self, cfg):
        super().__init__(); w = cfg['mlp_widths']
        self.mlp = nn.Sequential(nn.Linear(cfg['mcm_input'], w[0]), nn.ReLU(), nn.Linear(w[0], w[1]), nn.ReLU())
        self.gat1 = GATLayer(w[1], cfg['gat_widths'][0], cfg['gat_heads'][0], cfg['gat_concat'][0], cfg['leaky_relu_slope'])
        self.gat2 = GATLayer(cfg['gat_widths'][0] * cfg['gat_heads'][0], cfg['gat_widths'][1], cfg['gat_heads'][1], cfg['gat_concat'][1], cfg['leaky_relu_slope'])

    def forward(self, mcm, edge_index):
        h = self.mlp(mcm); h = F.elu(self.gat1(h, edge_index)); h = self.gat2(h, edge_index)
        return h.mean(0)


class AttentionLSTM(nn.Module):
    def __init__(self, input_width, lstm_width, attention_width):
        super().__init__(); self.lstm = nn.LSTM(input_width, lstm_width, batch_first=True)
        self.Wq = nn.Linear(lstm_width, attention_width); self.Wk = nn.Linear(lstm_width, attention_width); self.v = nn.Linear(attention_width, 1, bias=False)
        for name, p in self.lstm.named_parameters():
            nn.init.uniform_(p, -1 / lstm_width ** 0.5, 1 / lstm_width ** 0.5) if 'weight' in name else nn.init.zeros_(p)

    def forward(self, seq, lengths=None):
        B, T, _ = seq.shape; H, _ = self.lstm(seq)
        if lengths is None:
            lengths = torch.full((B,), T, dtype=torch.long)
        last = H[torch.arange(B), lengths - 1]
        score = self.v(torch.tanh(self.Wq(last).unsqueeze(1) + self.Wk(H))).squeeze(-1)         # (B, T)
        mask = torch.arange(T).unsqueeze(0) < lengths.unsqueeze(1)
        score = score.masked_fill(~mask, -1e30); w = torch.softmax(score, 1)
        return (w.unsqueeze(-1) * H).sum(1)


class FullModel(nn.Module):
    def __init__(self, task, cfg):
        super().__init__(); self.encoder = GraphEncoder(cfg)
        self.seq = AttentionLSTM(cfg['graph_vector_width'] + 1, cfg['lstm_width'], cfg['attention_width'])
        self.head = nn.Linear(cfg['lstm_width'], output_width(task))

    def forward(self, prices, graph_vectors):
        x = torch.cat([prices.unsqueeze(-1), graph_vectors], -1)
        return self.head(self.seq(x))


class PriceModel(nn.Module):
    def __init__(self, kind, task, cfg):
        super().__init__(); b = cfg['baselines']; self.kind = kind
        if kind == 'lstm':
            self.rnn = nn.LSTM(1, b['lstm']['width'], batch_first=True); width = b['lstm']['width']
        elif kind == 'gru':
            self.rnn = nn.GRU(1, b['gru']['width'], batch_first=True); width = b['gru']['width']
        elif kind == 'hlstm':
            h = b['hlstm']; self.lower = nn.LSTM(1, h['lower'], batch_first=True); self.upper = nn.LSTM(h['lower'], h['upper'], batch_first=True)
            self.chunks, self.chunk_len, width = h['chunks'], h['chunk_len'], h['upper']
        else:
            raise ValueError(kind)
        self.head = nn.Linear(width, output_width(task))

    def forward(self, prices):
        x = prices.unsqueeze(-1)
        if self.kind == 'hlstm':
            B = x.shape[0]; chunks = x.view(B * self.chunks, self.chunk_len, 1)
            _, (h, _) = self.lower(chunks); _, (h2, _) = self.upper(h[-1].view(B, self.chunks, -1))
            return self.head(h2[-1])
        _, h = self.rnn(x); h = h[0] if isinstance(h, tuple) else h
        return self.head(h[-1])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_model.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/model.py tests/research/onchain_b/test_model.py
git commit -m "feat(onchain-b): GAT encoder, attention LSTM, heads and price baselines"
```

---

### Task 13: Data pipeline and training (examples, week cache with checkpointing, fit loop, SVM)

**Files:**
- Create: `tradingagents/research/onchain_b/data.py`
- Create: `tradingagents/research/onchain_b/train.py`
- Test: `tests/research/onchain_b/test_data.py`
- Test: `tests/research/onchain_b/test_train.py`

**Interfaces:**
- Produces: `data.Example(decision: date, step_days: list[date], step_weeks: list[str], closes: float32[28], target: float)`; `data.examples(split, prices, scaler, task) -> list[Example]`; `data.WeekStore(graph_dir, mcm_dir)` with `.tensors(week) -> (mcm: float32[K,32], edge_index: int64[2,E])` (LRU 16); `data.Batch` with `.prices float32[B,28]`, `.weeks list[list[str]]`, `.targets`; `data.batches(examples, batch_size) -> iterator[Batch]` (chronological, no shuffle); `train.fit(arm, task, seed, out_dir, store=None, epochs=None, diag=None) -> dict` writing `predictions.json` (`{"decision": ..., "pred": ..., "target": ...}` per test day) and `checkpoint.pt` each epoch; `train.encode_weeks(model, store, weeks) -> dict[str, Tensor]` using `torch.utils.checkpoint`; `train.set_seed(seed)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/onchain_b/test_data.py
from datetime import date
from tradingagents.research.onchain_b import data as Dt, prices as P, calendar as cal

def _prices():
    d0 = date(2021, 12, 1); out = {}
    for k in range(1200):
        out[d0 + __import__('datetime').timedelta(days=k)] = 1000.0 + k
    return out

def test_train_examples_never_touch_2024():
    px = _prices(); sc = P.Scaler().fit(px, [date(2022, 2, 6)]); ex = Dt.examples('train', px, sc, 'classification')
    assert len(ex) == 693 and all(w < '2024' for e in ex for w in e.step_weeks)
    assert all(max(e.step_days) + __import__('datetime').timedelta(days=1) < date(2024, 1, 1) for e in ex)

def test_test_examples_use_available_weeks_only():
    px = _prices(); sc = P.Scaler().fit(px, [date(2022, 2, 6)]); ex = Dt.examples('test', px, sc, 'regression')
    assert len(ex) == 365
    for e in ex:
        for t, w in zip(e.step_days, e.step_weeks):
            assert cal.week_end(w) <= t

def test_batches_are_chronological_and_sized():
    px = _prices(); sc = P.Scaler().fit(px, [date(2022, 2, 6)]); ex = Dt.examples('train', px, sc, 'regression')
    bs = list(Dt.batches(ex, 16)); assert len(bs) == 44 and bs[0].prices.shape == (16, 28) and bs[-1].prices.shape[0] == 693 - 43 * 16
    assert bs[0].decisions[0] < bs[1].decisions[0]
```

```python
# tests/research/onchain_b/test_train.py
import json, numpy as np, torch
from datetime import date
from tradingagents.research.onchain_b import train as T, data as Dt, config

class FakeStore:
    def __init__(self, K=12, E=30):
        self.K, self.E = K, E; self.calls = 0
    def tensors(self, week):
        self.calls += 1; g = torch.Generator().manual_seed(abs(hash(week)) % 2**31)
        return torch.randn(self.K, 32, generator=g), torch.randint(0, self.K, (2, self.E), generator=g)

def test_fit_full_model_one_epoch_writes_outputs(tmp_path):
    px = {date(2021, 12, 1) + __import__('datetime').timedelta(days=k): 1000.0 + (k % 7) for k in range(1200)}
    res = T.fit('full', 'classification', 11, tmp_path, store=FakeStore(), epochs=1, prices=px)
    pred = json.loads((tmp_path / 'predictions.json').read_text())
    assert len(pred) == 365 and set(pred[0]) == {'decision', 'pred', 'target'} and (tmp_path / 'checkpoint.pt').exists()
    assert res['epochs_done'] == 1 and np.isfinite(res['final_train_loss'])

def test_fit_is_deterministic(tmp_path):
    px = {date(2021, 12, 1) + __import__('datetime').timedelta(days=k): 1000.0 + (k % 5) for k in range(1200)}
    a = T.fit('lstm', 'regression', 23, tmp_path / 'a', epochs=1, prices=px); b = T.fit('lstm', 'regression', 23, tmp_path / 'b', epochs=1, prices=px)
    pa_ = json.loads((tmp_path / 'a' / 'predictions.json').read_text()); pb = json.loads((tmp_path / 'b' / 'predictions.json').read_text())
    assert [r['pred'] for r in pa_] == [r['pred'] for r in pb]

def test_svm_arm(tmp_path):
    px = {date(2021, 12, 1) + __import__('datetime').timedelta(days=k): 1000.0 + (k % 5) for k in range(1200)}
    res = T.fit('svm', 'classification', 11, tmp_path, prices=px)
    assert len(json.loads((tmp_path / 'predictions.json').read_text())) == 365 and res['arm'] == 'svm'

def test_label_permutation_diag_changes_targets(tmp_path):
    px = {date(2021, 12, 1) + __import__('datetime').timedelta(days=k): 1000.0 + (k % 3) for k in range(1200)}
    ex = Dt.examples('train', px, __import__('tradingagents.research.onchain_b.prices', fromlist=['Scaler']).Scaler().fit(px, [date(2022, 2, 6)]), 'classification')
    perm = T.permute_labels(ex, 20260924)
    assert [e.target for e in perm] != [e.target for e in ex] and sorted(e.target for e in perm) == sorted(e.target for e in ex)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_data.py tests/research/onchain_b/test_train.py -q`
Expected: FAIL (modules missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/data.py
"""Daily examples with 28-step windows; each step carries its latest available week."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
import numpy as np, torch
from . import calendar as cal, prices as P, weekly as W


@dataclass
class Example:
    decision: date
    step_days: list
    step_weeks: list
    closes: np.ndarray
    target: float


def examples(split, prices, scaler, task):
    out = []
    for d in cal.decision_dates(split):
        days = cal.window(d); weeks = [cal.available_week(t) for t in days]
        if any(w is None for w in weeks):
            continue
        closes = np.array([scaler.transform(prices[t]) for t in days], np.float32)
        target = float(P.direction(prices, d)) if task == 'classification' else float(scaler.transform(P.target_usd(prices, d)))
        out.append(Example(d, days, weeks, closes, target))
    return out


class WeekStore:
    def __init__(self, graph_dir: Path, mcm_dir: Path):
        self.graph_dir, self.mcm_dir = Path(graph_dir), Path(mcm_dir); self._tensors = lru_cache(maxsize=16)(self._load)
    def _load(self, week):
        g = W.load(self.graph_dir / week); mcm = np.load(self.mcm_dir / f'{week}.npy')
        return torch.from_numpy(mcm.astype(np.float32)), torch.from_numpy(g.edge_index.astype(np.int64))
    def tensors(self, week): return self._tensors(week)


@dataclass
class Batch:
    decisions: list
    prices: torch.Tensor
    weeks: list
    targets: torch.Tensor


def batches(examples_, batch_size):
    for s in range(0, len(examples_), batch_size):
        chunk = examples_[s:s + batch_size]
        yield Batch([e.decision for e in chunk], torch.from_numpy(np.stack([e.closes for e in chunk])), [e.step_weeks for e in chunk],
                    torch.tensor([e.target for e in chunk]))
```

```python
# tradingagents/research/onchain_b/train.py
"""One arm-seed fit: deterministic, chronological batches, per-epoch checkpoints, one-shot test predictions."""
from __future__ import annotations
from pathlib import Path
import json, random, time
import numpy as np, torch
from torch.utils.checkpoint import checkpoint
from . import config, data as Dt, prices as P, calendar as cal, model as M
from .runlog import Log

ARMS = ('full', 'lstm', 'gru', 'hlstm', 'svm')


def set_seed(seed):
    random.seed(seed); np.random.seed(seed % 2**32); torch.manual_seed(seed); torch.use_deterministic_algorithms(True, warn_only=True)


def permute_labels(examples_, seed):
    rng = np.random.Generator(np.random.PCG64(seed)); order = sorted(range(len(examples_)), key=lambda k: examples_[k].decision)
    targets = [examples_[k].target for k in order]; perm = rng.permutation(len(targets))
    out = []
    for k, e in zip(order, [examples_[k] for k in order]):
        out.append(Dt.Example(e.decision, e.step_days, e.step_weeks, e.closes, targets[perm[len(out)]]))
    return out


def encode_weeks(model, store, weeks, constant=False):
    vectors = {}
    for w in sorted(set(weeks)):
        if constant:
            vectors[w] = torch.zeros(32); continue
        mcm, ei = store.tensors(w)
        vectors[w] = checkpoint(model.encoder, mcm, ei, use_reentrant=False)
    return vectors


def _graph_tensor(vectors, batch_weeks):
    return torch.stack([torch.stack([vectors[w] for w in ws]) for ws in batch_weeks])


def _loss(task, out, targets):
    return torch.nn.functional.cross_entropy(out, targets.long()) if task == 'classification' else ((out.squeeze(-1) - targets) ** 2).mean()


def _predict(task, out):
    return out.argmax(1).tolist() if task == 'classification' else out.squeeze(-1).tolist()


def fit(arm, task, seed, out_dir, store=None, epochs=None, diag=None, prices=None):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True); log = Log(out_dir / 'fit.jsonl')
    tcfg, mcfg = config.load('training'), config.load('model'); epochs = tcfg['epochs'] if epochs is None else epochs
    prices = P.load_prices() if prices is None else prices
    train_days = cal.decision_dates('train'); scaler = P.Scaler().fit(prices, sorted({t for d in train_days for t in cal.window(d)}))
    train = Dt.examples('train', prices, scaler, task); test = Dt.examples('test', prices, scaler, task)
    if diag == 'label_permutation':
        train = permute_labels(train, tcfg['label_permutation_seed'])
    constant = diag == 'constant_graph'
    set_seed(seed)
    if arm == 'svm':
        from sklearn.svm import SVC, SVR
        X = np.stack([e.closes for e in train]); y = np.array([e.target for e in train]); Xt = np.stack([e.closes for e in test])
        svm_cfg = mcfg['baselines']['svm']
        m = (SVC if task == 'classification' else SVR)(kernel=svm_cfg['kernel'], C=svm_cfg['C'], gamma=svm_cfg['gamma']).fit(X, y)
        preds = m.predict(Xt).tolist(); result = {'arm': arm, 'task': task, 'seed': seed, 'epochs_done': 0, 'final_train_loss': float('nan')}
    else:
        model = M.FullModel(task, mcfg) if arm == 'full' else M.PriceModel(arm, task, mcfg)
        opt = torch.optim.Adam(model.parameters(), lr=tcfg['lr'], betas=tuple(tcfg['betas'])); start = 0
        ck = out_dir / 'checkpoint.pt'
        if ck.exists():
            state = torch.load(ck, weights_only=False); model.load_state_dict(state['model']); opt.load_state_dict(state['opt']); start = state['epoch']
            torch.set_rng_state(state['rng']); np.random.set_state(state['np_rng']); random.setstate(state['py_rng'])
        loss_value = float('nan')
        for epoch in range(start, epochs):
            model.train(); t = time.time(); total = 0.0; n = 0
            for b in Dt.batches(train, tcfg['batch_size']):
                opt.zero_grad()
                if arm == 'full':
                    vec = encode_weeks(model, store, [w for ws in b.weeks for w in ws], constant); out = model(b.prices, _graph_tensor(vec, b.weeks))
                else:
                    out = model(b.prices)
                loss = _loss(task, out, b.targets); loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), tcfg['grad_clip_norm']); opt.step()
                total += loss.item() * len(b.decisions); n += len(b.decisions)
            loss_value = total / n
            torch.save({'model': model.state_dict(), 'opt': opt.state_dict(), 'epoch': epoch + 1, 'rng': torch.get_rng_state(),
                        'np_rng': np.random.get_state(), 'py_rng': random.getstate()}, ck)
            log.event(event='epoch', epoch=epoch + 1, train_loss=loss_value, seconds=round(time.time() - t, 1))
        model.eval(); preds = []
        with torch.no_grad():
            for b in Dt.batches(test, tcfg['batch_size']):
                if arm == 'full':
                    vec = encode_weeks(model, store, [w for ws in b.weeks for w in ws], constant); out = model(b.prices, _graph_tensor(vec, b.weeks))
                else:
                    out = model(b.prices)
                preds += _predict(task, out)
        result = {'arm': arm, 'task': task, 'seed': seed, 'epochs_done': epochs, 'final_train_loss': loss_value}
    records = []
    for e, p in zip(test, preds):
        target = e.target if task == 'classification' else scaler.inverse(e.target)
        pred = p if task == 'classification' else scaler.inverse(p)
        records.append({'decision': e.decision.isoformat(), 'pred': float(pred), 'target': float(target)})
    (out_dir / 'predictions.json').write_text(json.dumps(records))
    (out_dir / 'result.json').write_text(json.dumps({**result, 'diag': diag, 'n_train': len(train), 'n_test': len(test)}, indent=1))
    return result
```

Note: `encode_weeks` with `checkpoint` recomputes each graph encoding during backward, bounding memory to one graph at a time. The test `FakeStore` exercises the full path on tiny graphs.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_data.py tests/research/onchain_b/test_train.py -q`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/{data,train}.py tests/research/onchain_b/test_data.py tests/research/onchain_b/test_train.py
git commit -m "feat(onchain-b): daily examples, week cache with checkpointed encoding, fit loop"
```

---

### Task 14: Evaluation, bootstrap, report, fit CLI

**Files:**
- Create: `tradingagents/research/onchain_b/evaluate.py`
- Modify: `tradingagents/research/onchain_b/cli.py` (add `fit`, `evaluate`, `report`)
- Test: `tests/research/onchain_b/test_evaluate.py`

**Interfaces:**
- Produces: `evaluate.direction_metrics(pred: list[int], target: list[int]) -> dict(accuracy, precision, recall, f1, n, majority_rate)`; `evaluate.regression_metrics(pred, target) -> dict(mae, mse, rmse, mape)`; `evaluate.block_bootstrap(values: np.ndarray[bool|float], block=14, draws=2000, seed=20260924) -> (lo, hi)` on the mean; `evaluate.paired_block_bootstrap(a, b, ...) -> (lo, hi)` on mean(a−b); `evaluate.report(fits_dir) -> str` (Markdown table) written to `research/onchain-replication-b-2026-10-12/RESULT.md` by `cli report`; CLI `fit --arm A --task T --seed S [--diag D] [--epochs N]` writes to `ARTIFACTS/fits/<task>/<arm>[-<diag>]/seed<S>/`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b/test_evaluate.py
import numpy as np
from tradingagents.research.onchain_b import evaluate as E

def test_direction_metrics():
    m = E.direction_metrics([1, 1, 0, 0, 1], [1, 0, 0, 1, 1])
    assert m['accuracy'] == 0.6 and abs(m['precision'] - 2 / 3) < 1e-12 and abs(m['recall'] - 2 / 3) < 1e-12 and m['n'] == 5 and m['majority_rate'] == 0.6

def test_regression_metrics():
    m = E.regression_metrics([1.0, 2.0], [2.0, 2.0]); assert m['mae'] == 0.5 and m['rmse'] == 0.5 ** 0.5 and abs(m['mape'] - 25.0) < 1e-12

def test_bootstrap_deterministic_and_contains_mean():
    x = np.random.default_rng(0).random(365) < 0.55
    lo, hi = E.block_bootstrap(x); lo2, hi2 = E.block_bootstrap(x)
    assert (lo, hi) == (lo2, hi2) and lo <= x.mean() <= hi and 0.4 < lo < hi < 0.7

def test_paired_bootstrap_zero_for_identical():
    x = np.random.default_rng(1).random(100) < 0.5; lo, hi = E.paired_block_bootstrap(x, x); assert lo == 0.0 == hi
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/research/onchain_b/test_evaluate.py -q`
Expected: FAIL (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b/evaluate.py
"""Metrics (paper Eqs. 12–19, binary-up convention), moving-block bootstrap, result table."""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np


def direction_metrics(pred, target):
    p, t = np.asarray(pred, int), np.asarray(target, int); tp = int(((p == 1) & (t == 1)).sum()); fp = int(((p == 1) & (t == 0)).sum()); fn = int(((p == 0) & (t == 1)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0; recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {'accuracy': float((p == t).mean()), 'precision': precision, 'recall': recall, 'f1': f1, 'n': int(len(t)), 'majority_rate': float(max(t.mean(), 1 - t.mean()))}


def regression_metrics(pred, target):
    p, t = np.asarray(pred, float), np.asarray(target, float); err = p - t
    return {'mae': float(np.abs(err).mean()), 'mse': float((err ** 2).mean()), 'rmse': float(np.sqrt((err ** 2).mean())), 'mape': float((np.abs(err / t)).mean() * 100)}


def _blocks(n, block, draws, seed):
    rng = np.random.Generator(np.random.PCG64(seed)); k = int(np.ceil(n / block))
    starts = rng.integers(0, max(n - block + 1, 1), size=(draws, k))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(draws, -1)[:, :n]
    return idx


def block_bootstrap(values, block=14, draws=2000, seed=20260924):
    x = np.asarray(values, float); idx = _blocks(len(x), block, draws, seed); means = x[idx].mean(1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def paired_block_bootstrap(a, b, block=14, draws=2000, seed=20260924):
    return block_bootstrap(np.asarray(a, float) - np.asarray(b, float), block, draws, seed)


def _load(fit_dir):
    rec = json.loads((Path(fit_dir) / 'predictions.json').read_text())
    return [r['pred'] for r in rec], [r['target'] for r in rec]


def report(fits_dir, paper_direction=0.804):
    fits_dir = Path(fits_dir); lines = ['| task | arm | seeds | accuracy / MAE mean | range | vs paper | vs LSTM (95 % CI) |', '|---|---|---|---|---|---|---|']
    for task in ('classification', 'regression'):
        tdir = fits_dir / task
        if not tdir.exists():
            continue
        per_arm = {}
        for arm_dir in sorted(tdir.iterdir()):
            vals, hits = [], []
            for seed_dir in sorted(arm_dir.glob('seed*')):
                if not (seed_dir / 'predictions.json').exists():
                    continue
                p, t = _load(seed_dir)
                if task == 'classification':
                    vals.append(direction_metrics(p, t)['accuracy']); hits.append(np.asarray(p, int) == np.asarray(t, int))
                else:
                    vals.append(regression_metrics(p, t)['mae'])
            if vals:
                per_arm[arm_dir.name] = (vals, hits)
        for arm, (vals, hits) in per_arm.items():
            mean = float(np.mean(vals)); vs_paper = f'{(mean - paper_direction) * 100:+.1f} pp' if task == 'classification' else '—'
            vs_lstm = '—'
            if task == 'classification' and arm != 'lstm' and 'lstm' in per_arm and hits and per_arm['lstm'][1]:
                a = np.mean([h for h in hits], 0); b = np.mean([h for h in per_arm['lstm'][1]], 0)
                lo, hi = paired_block_bootstrap(a, b); vs_lstm = f'{(a.mean() - b.mean()) * 100:+.1f} pp [{lo * 100:+.1f}, {hi * 100:+.1f}]'
            lines.append(f'| {task} | {arm} | {len(vals)} | {mean:.4f} | {min(vals):.4f}–{max(vals):.4f} | {vs_paper} | {vs_lstm} |')
    return '\n'.join(lines)
```

CLI additions in `cli.py` (append before `main`, and register the subcommands):

```python
def fit_stage(args):
    from . import train as T, data as Dt
    name = args.arm + (f'-{args.diag}' if args.diag else ''); out = ARTIFACTS / 'fits' / args.task / name / f'seed{args.seed}'
    if (out / 'predictions.json').exists():
        print('exists', out); return
    store = Dt.WeekStore(ARTIFACTS / 'graphs', ARTIFACTS / 'mcm' / f'seed{args.seed}') if args.arm == 'full' else None
    torch_threads = max(1, (os.cpu_count() or 2) - 2); __import__('torch').set_num_threads(torch_threads)
    print(json.dumps(T.fit(args.arm, args.task, args.seed, out, store=store, epochs=args.epochs, diag=args.diag)))


def report_stage(args):
    from . import evaluate as E
    text = E.report(ARTIFACTS / 'fits'); path = config.STUDY / 'RESULT.md'
    path.write_text('# Branch B results — initial ETH fold (sealed 2024)\n\nGenerated by `cli report`; every fit is one-shot.\n\n' + text + '\n'); print(text)
```

```python
    a = sub.add_parser('fit'); a.add_argument('--arm', required=True, choices=('full', 'lstm', 'gru', 'hlstm', 'svm')); a.add_argument('--task', required=True, choices=('classification', 'regression'))
    a.add_argument('--seed', type=int, required=True); a.add_argument('--diag', choices=('constant_graph', 'label_permutation')); a.add_argument('--epochs', type=int); a.set_defaults(fn=fit_stage)
    a = sub.add_parser('report'); a.set_defaults(fn=report_stage)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/research/onchain_b -q`
Expected: all passed (≈ 40 tests)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b/evaluate.py tradingagents/research/onchain_b/cli.py tests/research/onchain_b/test_evaluate.py
git commit -m "feat(onchain-b): metrics, block bootstrap, result report and fit CLI"
```

---

### Task 15: Compute calibration, dictionary, MCM (CP2) and training launch (CP3 → CP4)

Operational task; each step records numbers in `STATE.md` / `CALIBRATION.md` and commits docs only.

- [ ] **Step 1: Throughput and memory check on one training week (freeze N_max)**

Run (after `build-graphs` has produced `2022-03-07`):
```bash
.venv/bin/python - <<'EOF'
import time, numpy as np, resource
from tradingagents.research.onchain_b import weekly as W, dictionary as D, mcm, config
from tradingagents.research.onchain_b.matching.agreement import MatchConfig
cfg = MatchConfig.from_json(config.load('matching')); g = W.load(config.ARTIFACTS/'graphs'/'2022-03-07')
for n_max in (32, 64):
    d = D.build({'2022-03-07': g}, cfg, 64, 8, n_max, 11)          # small throwaway dictionary for timing only
    sub = W.WeekGraph(g.week, g.addresses[:2000], g.x[:2000], g.edge_index[:, (g.edge_index < 2000).all(0)], g.edge_attr[(g.edge_index < 2000).all(0)], g.edge_count[(g.edge_index < 2000).all(0)], {})
    t = time.time(); F = mcm.compute_week(sub, d, cfg, n_max); dt = time.time() - t
    print(n_max, 'cells/s', round(F.size/dt), 'proj_hours_156w', round(156 * g.n * 32 / (F.size/dt) / 3600, 1), 'rss_mb', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024)
EOF
```
Expected: a cells/s figure per `N_max`; choose the largest `N_max` whose projected 156-week MCM time ≤ 48 h and RSS ≤ 12 GiB; write both rows to `CALIBRATION.md`, set `dictionary.json n_max`, commit `docs(onchain-b): freeze N_max from measured throughput`.

- [ ] **Step 2: GAT forward/backward check on one real week**

```bash
.venv/bin/python - <<'EOF'
import time, torch, numpy as np, resource
from tradingagents.research.onchain_b import weekly as W, model as M, config
g = W.load(config.ARTIFACTS/'graphs'/'2022-03-07'); enc = M.GraphEncoder(config.load('model'))
mcm = torch.randn(g.n, 32); ei = torch.from_numpy(g.edge_index.astype(np.int64))
t = time.time(); v = enc(mcm, ei); v.sum().backward(); print('fwd+bwd s', round(time.time()-t, 2), 'nodes', g.n, 'edges', g.e, 'rss_mb', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024)
EOF
```
Expected: seconds and RSS; projected arm-seed time = epochs × batches × ~8 graphs × 2 × fwd+bwd. Record in `CALIBRATION.md`; if > 6 h per arm-seed, record and continue (the gate is on completion, not speed), but note it in `STATE.md`.

- [ ] **Step 3: Dictionaries and MCM for all seeds (CP2)**

```bash
for s in 11 23 37 51 71; do systemd-run --user --unit onchain-b-dict-$s -p MemoryMax=12G -p WorkingDirectory=$PWD $PWD/.venv/bin/python -m tradingagents.research.onchain_b.cli dictionary --seed $s; done
# after all dictionaries exist:
for s in 11 23 37 51 71; do systemd-run --user --unit onchain-b-mcm-$s -p MemoryMax=12G -p WorkingDirectory=$PWD $PWD/.venv/bin/python -m tradingagents.research.onchain_b.cli mcm --seed $s; done
```
Run the five MCM units sequentially, not concurrently (each uses all cores). Record `cells_per_s` and total hours in `STATE.md`; commit `docs(onchain-b): CP2 dictionaries and MCM features complete`.

- [ ] **Step 4: One full-model arm-seed, then all arms (CP3 → CP4)**

```bash
systemd-run --user --unit onchain-b-fit-full-cls-11 -p MemoryMax=12G -p WorkingDirectory=$PWD $PWD/.venv/bin/python -m tradingagents.research.onchain_b.cli fit --arm full --task classification --seed 11
```
After it completes, record epoch seconds and RSS from `fit.jsonl` (CP3). Then queue, sequentially: `full` × 5 seeds × 2 tasks; `lstm`, `gru`, `hlstm` × 5 seeds × 2 tasks; `svm` × 1 × 2 tasks; diagnostics `full --diag constant_graph` and `full --diag label_permutation` × 5 seeds (classification). Then `cli report`; commit `RESULT.md` and `STATE.md` (`CP4`).

- [ ] **Step 5: Publish checkpoint comparison**

Update the audit artifact's "Next: two independent branches" section with CP1–CP4 numbers from both branches; update memory file `project_onchain_replication_branch_b.md`.

---

## Self-review

**Spec coverage:** §4 data → Tasks 2, 4; §5 graphs/calibration/neighborhoods → Tasks 5, 6, 10, 11; §6 dictionary → Task 9; §7 solvers → Tasks 7, 8; §8 model/training/baselines/diagnostics → Tasks 12, 13; §9 compute calibration → Task 15 steps 1–2; §10 chronology → Task 3 (+ data tests); §11 gates → Task 1 (`gates.json`) and Task 14 report; §12 checkpoints → Task 15; §13 layout → as listed; §15 `fidelity-b.json` → written in Task 11 step 2 alongside `CALIBRATION.md` (copy Branch A's F01–F14 dispositions with F01b/F04b replacements; no code).

**Placeholders:** none; every code step is complete. The `PROTOCOL.md` content in Task 1 is described, not pasted, because it restates spec §4–§11; write it by copying those sections.

**Type consistency:** `Graph` (neighborhoods) fields `x, edge_index, edge_attr, nodes, center` used identically in Tasks 7–10; `WeekGraph` fields in Tasks 5, 6, 9, 10, 13; `MatchConfig` signature `(alpha, beta0, beta_final, beta_rate, max_iterations)` everywhere; `match_many` returns `(scores, hards)`; `WeekStore.tensors(week) -> (mcm, edge_index)` matches `FakeStore` in Task 13 tests and `encode_weeks`.

**Review Focus coverage:** 1 → `test_duplicate_hash_rejected` (Task 5); 2 → `test_fewer_than_k_nodes` (Task 5); 3 → `test_zero_edge_graph` (Task 7) and mixed zero-edge pairs (Task 8); 4 → `test_warmup_exclusion` (Task 3); 5 → `test_batched_mixed_edge_counts` (Task 8).
