# tradingagents/research/onchain_b5/events.py
"""Event study (spec §8): large stablecoin inflow (or outflow) hours versus placebo exchange-
activity spikes; responses k = 1..K hours: realised-volatility surprise against an out-of-fold
price-only forecast, the same before the event, change in near-expiry implied volatility, and
signed return."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2.screen import fit_predict, folds
from ..onchain_b4 import dataset4
from ..onchain_b4.screen4 import interval
from . import decisions, implied

H = pd.Timedelta(hours=1)


def first_per_window(times, spacing_h):
    kept, last = [], None
    for t in sorted(pd.DatetimeIndex(times)):
        if last is None or t - last >= pd.Timedelta(hours=spacing_h):
            kept.append(t)
            last = t
    return kept


def flow_events(raw, trans, kind, cfg):
    e = cfg['events']
    if kind == 'inflow':
        m = (trans['stable_in_val__h1z'] >= e['z']) & (raw['stable_big_in'].reindex(trans.index) >= 1)
    else:
        m = trans['stable_out_val__h1z'] >= e['z']
    return first_per_window(trans.index[m.fillna(False).to_numpy()], e['spacing_h'])


def placebo_events(bars, n, cfg):
    e = cfg['events']
    b = bars.reindex(pd.date_range(bars.index.min(), bars.index.max(), freq='h'))
    r = np.log(b['close']).diff()
    za = dataset4.zscore(r.abs(), e['z_window'], e['z_min'], 10.0)
    zv = dataset4.zscore(np.log(b['qvol']).replace([np.inf, -np.inf], np.nan), e['z_window'], e['z_min'], 10.0)
    cand = first_per_window(b.index[((za >= e['z']) | (zv >= e['z'])).fillna(False).to_numpy()], e['spacing_h'])
    if len(cand) > n:
        rng = np.random.default_rng(e['placebo_seed'])
        cand = sorted(pd.DatetimeIndex(cand)[rng.choice(len(cand), n, replace=False)])
    return list(cand)


def vol_targets(bars, kmax):
    b = bars.reindex(pd.date_range(bars.index.min(), bars.index.max(), freq='h'))
    lc = np.log(b['close'])
    r2 = lc.diff() ** 2
    Y, R = pd.DataFrame(index=b.index), pd.DataFrame(index=b.index)
    for k in range(1, kmax + 1):
        Y[f'y{k}'] = np.log(np.sqrt(r2.rolling(k, min_periods=k).sum().shift(-k) * 8760 / k).clip(lower=1e-8))
        R[f'r{k}'] = lc.shift(-k) - lc
    return Y, R


def surprises(bars, cfg):
    e = cfg['events']
    X = dataset4.price_features(bars).join(decisions.px_features(bars))
    Y, _ = vol_targets(bars, e['kmax'])
    S = pd.DataFrame(index=Y.index)
    for k in range(1, e['kmax'] + 1):
        d = X.join(Y[[f'y{k}']]).dropna()
        y = d[f'y{k}'].to_numpy(float)
        Xm = d[[c for c in X.columns]].to_numpy(float)
        p = np.full(len(d), np.nan)
        for _, tr, te in folds(d.index, e['test_years'], k / 24):
            if te.any() and tr.sum() >= 1000:
                p[te] = fit_predict('linear', 'regression', Xm[tr], y[tr], Xm[te], e['inner_len'], cfg)
        S[f's{k}'] = pd.Series(y - p, index=d.index)
    return S


def iv_series(trades_for_day, days, cfg):
    c, e = cfg['implied'], cfg['events']
    out = {}
    for day in days:
        tr = trades_for_day(day)
        if tr is None or not len(tr):
            continue
        tr = tr.assign(bin=tr['ts'].dt.floor('h'))
        tr = tr[tr['expiry'] >= tr['bin'] + H + pd.Timedelta(hours=e['iv_min_ahead_h'])]
        tr = tr[np.abs(np.log(tr['strike'] / tr['index_price'])) <= c['moneyness']]
        for b, g in tr.groupby('bin'):
            g = g[g['expiry'] == g['expiry'].min()]
            out[b] = implied.wmedian(g['iv'], g['amount'])
    return pd.Series(out, dtype=float).sort_index()


def _stat(x, gate):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return {'mean': float(x.mean()) if len(x) else np.nan, 'lo': np.nan, 'hi': np.nan, 'n': int(len(x))}
    lo, hi = interval(x, 1, gate['draws'], gate['seed'], gate['chunk'])
    return {'mean': float(x.mean()), 'lo': lo, 'hi': hi, 'n': int(len(x))}


def responses(evts, S, R, iv, kmax, gate):
    ev = pd.DatetimeIndex(evts)
    out = []
    for k in range(1, kmax + 1):
        post = S[f's{k}'].reindex(ev).to_numpy()
        pre = S[f's{k}'].reindex(ev - k * H).to_numpy()
        div = iv.reindex(ev + k * H).to_numpy() - iv.reindex(ev).to_numpy()
        ret = R[f'r{k}'].reindex(ev).to_numpy()
        out.append({'k': k, 'n': int(len(ev)), 'post_vol': _stat(post, gate), 'pre_vol': _stat(pre, gate),
                    'd_iv': _stat(div, gate), 'ret': _stat(ret, gate)})
    return out
