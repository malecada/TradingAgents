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
