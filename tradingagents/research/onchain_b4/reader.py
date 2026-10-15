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


def _check42(arr, what):
    if len(arr) and not pc.all(pc.equal(pc.utf8_length(arr), 42)).as_py():
        raise ValueError(f'address length != 42 in {what}')


def admit(tx, tt, blocks, tokens):
    tx = tx.filter(pc.equal(_arr(tx['receipt_status']), 1))
    paid = pc.coalesce(_arr(tx['receipt_effective_gas_price']), _arr(tx['gas_price']))
    frm_e, to_e = _arr(tx['from_address']), _arr(tx['to_address'])
    # contract creations: the dataset writes the missing recipient as null or as the string 'None'
    has_to = pc.and_(pc.is_valid(to_e), pc.invert(pc.is_in(to_e, value_set=pa.array(['None', '']))))
    keep_e = pc.and_(pc.and_(pc.greater(_arr(tx['value']), 0.0), has_to), pc.not_equal(frm_e, to_e))
    e = tx.filter(keep_e)
    _check42(_arr(e['from_address']), 'transactions.from_address')
    _check42(_arr(e['to_address']), 'transactions.to_address')
    tok_all = _unpad(tt['token_address'])
    m = pc.is_in(tok_all, value_set=pa.array(sorted(tokens)))
    tt, tok_all = tt.filter(m), pc.filter(tok_all, m)
    frm, to = _unpad(tt['from_address']), _unpad(tt['to_address'])
    keep = pc.and_(pc.and_(pc.greater(_arr(tt['value']), 0.0), pc.not_equal(frm, to)),
                   pc.and_(pc.not_equal(frm, ZERO), pc.not_equal(to, ZERO)))
    tt, frm, to, tok_all = tt.filter(keep), pc.filter(frm, keep), pc.filter(to, keep), pc.filter(tok_all, keep)
    _check42(frm, 'token_transfers.from_address')
    _check42(to, 'token_transfers.to_address')
    tok, raw = tok_all.to_numpy(zero_copy_only=False), _floats(tt['value'])
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
