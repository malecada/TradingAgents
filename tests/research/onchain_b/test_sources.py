import hashlib
import io

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import zstandard

from tradingagents.research.onchain_b import sources


def _synthetic_manifest(tmp_path, table, n_spans=3):
    buf = io.BytesIO()
    pq.write_table(table, buf)
    raw = buf.getvalue()
    size = len(raw)
    bounds = [0] + [size * k // n_spans for k in range(1, n_spans)] + [size]
    spans = []
    for k, (a, b) in enumerate(zip(bounds, bounds[1:])):
        chunk = raw[a:b]
        stored = zstandard.ZstdCompressor().compress(chunk)
        p = tmp_path / f'span{k}.zst'
        p.write_bytes(stored)
        spans.append({'path': str(p), 'start': a, 'end': b, 'codec': 'zstd', 'raw_bytes': b - a,
                      'raw_sha256': hashlib.sha256(chunk).hexdigest(), 'stored_bytes': len(stored),
                      'stored_sha256': hashlib.sha256(stored).hexdigest()})
    return {'size': size, 'spans': spans, 'object': {'key': 'synthetic'}}


def _table():
    return pa.table({'hash': ['0x' + f'{i:064x}' for i in range(5)],
                     'block_timestamp': pa.array([1_700_000_000_000_000_000 + i for i in range(5)], pa.timestamp('ns')),
                     'from_address': ['0x' + f'{i:040x}' for i in range(5)],
                     'to_address': ['0x' + f'{i + 1:040x}' for i in range(5)],
                     'value': [1e18 * (i + 1) for i in range(5)],
                     'receipt_status': [1, 1, 0, 1, 1]})


def test_projected_table_roundtrip(tmp_path):
    table = _table()
    manifest = _synthetic_manifest(tmp_path, table)
    out = sources.projected_table(manifest, tmp_path, sources.COLUMNS)
    assert out.num_rows == 5 and out.column_names == list(sources.COLUMNS)
    assert out.column('value').to_pylist() == table.column('value').to_pylist()


def test_corrupted_span_rejected(tmp_path):
    manifest = _synthetic_manifest(tmp_path, _table())
    manifest['spans'][1]['stored_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='stored range hash'):
        sources.projected_table(manifest, tmp_path, sources.COLUMNS)


def test_special_day_resolves_from_retained_checkout():
    # 2024-01-01 uses untracked prototype captures that live only in the original data checkout
    from pathlib import Path
    m = sources.day_manifest(sources.load_plan(), '2024-01-01')
    assert len(m['spans']) == 118 and all(Path(s['path']).exists() for s in m['spans'])
    assert m['spans'][-1]['codec'] == 'receipt_base64'


def test_real_plan_resolves_all_days():
    plan = sources.load_plan()
    days = sorted(plan['expected_rows'])
    assert len(days) == 1096 and days[0] == '2022-01-01' and days[-1] == '2024-12-31'
    m = sources.day_manifest(plan, '2023-06-05')
    assert m['size'] > 0 and len(m['spans']) > 0 and all(span['codec'] == 'zstd' for span in m['spans'])
