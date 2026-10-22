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
