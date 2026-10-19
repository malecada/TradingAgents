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
