# tradingagents/research/onchain_b8/hourly8.py
"""One day of admitted transfers -> 24 × n_tokens rows of the seven token-hour series
(spec §3). USD values use the token's hourly close of the block's hour; a token-hour without a
price has NaN USD series, counts unaffected and big_cnt 0."""
from __future__ import annotations

import numpy as np
import pandas as pd

SERIES = ['dep_usd', 'wd_usd', 'dep_cnt', 'wd_cnt', 'tx_cnt', 'active', 'big_cnt']


def price_matrix(bars_by_index, hours, multipliers=None):
    """Per-token USD price of one token per hour: the perp close divided by the symbol's
    multiplier (1,000 for "1000X" perps)."""
    m = np.full((len(hours), len(bars_by_index)), np.nan)
    for j, b in enumerate(bars_by_index):
        mult = 1 if multipliers is None else multipliers[j]
        m[:, j] = b['close'].reindex(hours).to_numpy(float) / mult
    return m


def day_rows(day, d, state, prices, big_usd):
    n_tok = prices.shape[1]
    start = int(pd.Timestamp(day, tz='UTC').timestamp())
    hour = ((d.ts - start) // 3600).astype(np.int64)
    tok = d.token.astype(np.int64)
    key = hour * n_tok + tok
    ex_s, ex_d = state.is_exchange(d.src), state.is_exchange(d.dst)
    dep, wd = ex_d & ~ex_s, ex_s & ~ex_d
    usd = d.amount * prices[hour, tok]
    out = np.zeros((24 * n_tok, len(SERIES)))
    np.add.at(out[:, 0], key[dep], np.nan_to_num(usd[dep]))
    np.add.at(out[:, 1], key[wd], np.nan_to_num(usd[wd]))
    np.add.at(out[:, 2], key[dep], 1.0)
    np.add.at(out[:, 3], key[wd], 1.0)
    np.add.at(out[:, 4], key, 1.0)
    pairs = np.empty(2 * len(key), dtype=[('k', np.int64), ('a', np.uint64)])
    pairs['k'] = np.concatenate([key, key])
    pairs['a'] = np.concatenate([d.src, d.dst])
    uniq = np.unique(pairs)
    np.add.at(out[:, 5], uniq['k'], 1.0)
    big = usd >= big_usd
    np.add.at(out[:, 6], key[big], 1.0)
    nop = ~np.isfinite(prices).reshape(-1)
    out[nop, 0] = np.nan
    out[nop, 1] = np.nan
    df = pd.DataFrame(out, columns=SERIES)
    df.insert(0, 'token', np.tile(np.arange(n_tok, dtype=np.int16), 24))
    df.insert(0, 'hour', pd.Timestamp(day) + pd.to_timedelta(np.repeat(np.arange(24), n_tok), unit='h'))
    return df
