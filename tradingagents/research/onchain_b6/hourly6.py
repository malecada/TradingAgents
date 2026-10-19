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
