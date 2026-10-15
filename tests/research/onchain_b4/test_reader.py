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


def test_token_address_is_normalised(tmp_path):
    _fixture(tmp_path)
    d = tmp_path / 'v1.0' / 'eth' / 'token_transfers' / 'date=2025-06-02'
    pq.write_table(pa.table({
        'token_address': [pad(USDT).upper().replace('0X', '0x')], 'from_address': [pad(A)], 'to_address': [pad(C)],
        'value': [7e6], 'block_number': [14], 'block_timestamp': pa.array([TS(6)], pa.timestamp('ns'))}), d / 'part-1.parquet')
    day = reader.read_day('2025-06-02', filesystem=pafs.LocalFileSystem(), root=str(tmp_path),
                          tokens=config.load()['tokens'], retries=[])
    assert 7.0 in np.round(day.amount, 6).tolist()


def test_malformed_address_is_rejected(tmp_path):
    _fixture(tmp_path)
    d = tmp_path / 'v1.0' / 'eth' / 'transactions' / 'date=2025-06-02'
    t = pq.read_table(d / 'part-0.parquet')
    t = t.set_column(0, 'from_address', pa.array([A[2:]] + t['from_address'].to_pylist()[1:]))
    pq.write_table(t, d / 'part-0.parquet')
    with pytest.raises(DayUnavailable, match='address length'):
        reader.read_day('2025-06-02', filesystem=pafs.LocalFileSystem(), root=str(tmp_path),
                        tokens=config.load()['tokens'], retries=[])
