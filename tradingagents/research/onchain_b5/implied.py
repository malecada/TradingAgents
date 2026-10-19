# tradingagents/research/onchain_b5/implied.py
"""Instrument parsing and decision-time implied volatility (spec §4): near-ATM trades on the
target expiry in [t - lookback, t), amount-weighted medians over all, taker-buy (ask) and
taker-sell (bid) trades."""
from __future__ import annotations

import numpy as np
import pandas as pd

MONTHS = {m: i + 1 for i, m in enumerate(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'])}


def parse(names):
    parts = pd.Series(list(names)).str.split('-', expand=True)
    m = parts[1].str.extract(r'^(\d{1,2})([A-Z]{3})(\d{2})$')
    expiry = pd.to_datetime(pd.DataFrame({'year': 2000 + m[2].astype(int), 'month': m[1].map(MONTHS),
                                          'day': m[0].astype(int)})) + pd.Timedelta(hours=8)
    return pd.DataFrame({'expiry': expiry, 'strike': parts[2].astype(float), 'kind': parts[3]})


def prepare(day_df):
    df = day_df.reset_index(drop=True).copy()
    df['ts'] = pd.to_datetime(df['timestamp'], unit='ms')
    if len(df):
        p = parse(df['instrument_name'])
        df[['expiry', 'strike', 'kind']] = p[['expiry', 'strike', 'kind']].to_numpy()
        df['expiry'] = pd.to_datetime(df['expiry'])
        df['strike'] = df['strike'].astype(float)
    else:
        df['expiry'], df['strike'], df['kind'] = pd.Series(dtype='datetime64[ns]'), pd.Series(dtype=float), pd.Series(dtype=object)
    return df


def wmedian(values, weights):
    v, w = np.asarray(values, float), np.asarray(weights, float)
    o = np.argsort(v, kind='stable')
    c = np.cumsum(w[o])
    return float(v[o][np.searchsorted(c, 0.5 * c[-1])])


def decision_iv(trades, t, expiry, c):
    lo = t - pd.Timedelta(hours=c['lookback_h'])
    win = trades[(trades['ts'] >= lo) & (trades['ts'] < t) & (trades['expiry'] == expiry)]
    atm = win[np.abs(np.log(win['strike'] / win['index_price'])) <= c['moneyness']]
    if len(atm) < c['min_trades']:
        return None
    buy, sell = atm[atm['direction'] == 'buy'], atm[atm['direction'] == 'sell']
    return {'iv_mid': wmedian(atm['iv'], atm['amount']),
            'iv_ask': wmedian(buy['iv'], buy['amount']) if len(buy) else float('nan'),
            'iv_bid': wmedian(sell['iv'], sell['amount']) if len(sell) else float('nan'),
            'n_trades': int(len(atm)), 'strikes': sorted(float(k) for k in atm['strike'].unique())}
