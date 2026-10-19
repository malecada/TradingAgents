# tradingagents/research/onchain_b5/straddle.py
"""At-the-money daily straddle backtest (spec §6): Black-76 at the ask (buys) or bid (sells)
implied volatility, Deribit fees capped at 12.5 % of each leg, payoff |S_T - K| at expiry."""
from __future__ import annotations

import numpy as np
from scipy.special import ndtr

from ..onchain_b4.screen4 import interval


def black76(F, K, T, sigma):
    F, K, T, sigma = (np.asarray(x, float) for x in (F, K, T, sigma))
    v = sigma * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * v ** 2) / v
    d2 = d1 - v
    call = F * ndtr(d1) - K * ndtr(d2)
    put = K * ndtr(-d2) - F * ndtr(-d1)
    return call, put


def pnl(side, s0, K, sT, T, iv_ask, iv_bid, rate, cap):
    side = np.asarray(side, int)
    sigma = np.where(side > 0, iv_ask, iv_bid) / 100.0
    c, p = black76(s0, K, T, sigma)
    fee_in = np.minimum(rate * s0, cap * c) + np.minimum(rate * s0, cap * p)
    ic, ip = np.maximum(sT - K, 0.0), np.maximum(K - sT, 0.0)
    fee_out = np.where(ic > 0, np.minimum(rate * sT, cap * ic), 0.0) + np.where(ip > 0, np.minimum(rate * sT, cap * ip), 0.0)
    premium = c + p
    gross = np.where(side > 0, ic + ip - premium, premium - ic - ip)
    out = np.where(side == 0, 0.0, gross - fee_in - fee_out)
    return out, premium


def sides(z, theta):
    z = np.asarray(z, float)
    return np.where(z > theta, 1, np.where(z < -theta, -1, 0))


def _maxdd(p):
    c = np.cumsum(p)
    return float(np.max(np.maximum.accumulate(np.concatenate([[0.0], c]))[1:] - c)) if len(c) else 0.0


def metrics(p, side, premium, index, groups, gate):
    years = index.year.to_numpy()
    out = {}
    for name, yrs in groups.items():
        m = np.isin(years, yrs)
        pm, sm, prm = p[m], side[m], premium[m]
        tr = sm != 0
        tp = pm[tr]
        lo, hi = interval(tp, gate['block'], gate['draws'], gate['seed'], gate['chunk']) if len(tp) >= gate['block'] else (np.nan, np.nan)
        sd = pm.std()
        out[name] = {'decisions': int(m.sum()), 'trades': int(tr.sum()), 'mean_trade': float(tp.mean()) if len(tp) else np.nan,
                     'lo': lo, 'hi': hi, 'total': float(pm.sum()), 'hit': float((tp > 0).mean()) if len(tp) else np.nan,
                     'sharpe': float(pm.mean() / sd * np.sqrt(365)) if sd > 0 else np.nan, 'maxdd': _maxdd(pm),
                     'per_premium': float(tp.sum() / prm[tr].sum()) if tr.any() else np.nan,
                     'long_mean': float(pm[sm > 0].mean()) if (sm > 0).any() else np.nan, 'long_n': int((sm > 0).sum()),
                     'short_mean': float(pm[sm < 0].mean()) if (sm < 0).any() else np.nan, 'short_n': int((sm < 0).sum())}
    return out


def backtest(df, preds, cfg):
    st, g = cfg['straddle'], cfg['gate']
    valid = preds.notna().all(axis=1).to_numpy()
    d = df[valid]
    P = preds[valid]
    T = d['tau_h'].to_numpy(float) / 8760
    args = (d['s0'].to_numpy(float), d['K'].to_numpy(float), d['sT'].to_numpy(float), T,
            d['iv_ask'].to_numpy(float), d['iv_bid'].to_numpy(float), st['fee_rate'], st['fee_cap'])
    out = []

    def add(rule, fam, var, theta, side):
        p, prem = pnl(side, *args)
        out.append({'rule': rule, 'family': fam, 'variant': var, 'theta': theta,
                    'groups': metrics(p, side, prem, d.index, cfg['groups'], g)})

    add('always_buy', None, None, None, np.ones(len(d), int))
    add('always_sell', None, None, None, -np.ones(len(d), int))
    for fam in cfg['families']:
        for var in st['variants']:
            z = P[f'{fam}:{var}'].to_numpy(float) - d['mk_iv'].to_numpy(float)
            for theta in st['thetas']:
                s = sides(z, theta)
                add('signal', fam, var, theta, s)
                add('flip', fam, var, theta, -s)
    return out
