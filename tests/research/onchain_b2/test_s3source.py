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