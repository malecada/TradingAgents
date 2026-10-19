# tradingagents/research/onchain_b5/decisions.py
"""Decision tables (spec §§4–6): one row per daily decision time with price, option-market and
B4 flow features taken at the last complete hour before t, realised log volatility to expiry,
the index at t and at expiry, the straddle strike, and implied volatilities."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..onchain_b4 import dataset4
from . import implied

H = pd.Timedelta(hours=1)


def load_bars(path):
    doc = json.loads(Path(path).read_text())
    idx = pd.to_datetime(list(doc), format='%Y-%m-%dT%H')
    v = list(doc.values())
    return pd.DataFrame({'close': [float(x[0]) for x in v], 'qvol': [float(x[1]) for x in v]}, index=idx).sort_index()


def _full(bars):
    return bars.reindex(pd.date_range(bars.index.min(), bars.index.max(), freq='h'))


def px_features(bars):
    b = _full(bars)
    lc = np.log(b['close'])
    r = lc.diff()
    f = pd.DataFrame(index=b.index)
    f['px_abs_r1'] = r.abs()
    f['px_rv4'] = np.sqrt((r ** 2).rolling(4, min_periods=4).sum())
    f['px_rv6'] = np.sqrt((r ** 2).rolling(6, min_periods=6).sum())
    f['px_lvol1'] = np.log(b['qvol'])
    f['px_lvol4'] = np.log(b['qvol'].rolling(4, min_periods=4).sum())
    return f.replace([np.inf, -np.inf], np.nan)


def realized_logvol(closes, t, tau_h):
    seg = closes.reindex(pd.date_range(t - H, periods=tau_h + 1, freq='h'))
    if seg.isna().any():
        return float('nan')
    r = np.diff(np.log(seg.to_numpy(float)))
    return float(np.log(max(np.sqrt((r ** 2).sum() * 8760 / tau_h), 1e-8)))


def fill_spread(df, window):
    # amendment 2: half-spread = max(0, (ask - bid) / 2); a missing side takes the median of the previous
    # rows' half-spreads; execution IVs are symmetric around the mid
    df = df.copy()
    df['hs_raw'] = (df['iv_ask'] - df['iv_bid']) / 2
    hs = df['hs_raw'].clip(lower=0)
    hs = hs.fillna(hs.shift(1).rolling(window, min_periods=1).median())
    df['iv_ask'] = df['iv_mid'] + hs
    df['iv_bid'] = df['iv_mid'] - hs
    return df


def build(sched, bars, dvol, flows, trades_for_day, cfg, settle=None):
    s = cfg['schedules'][sched]
    tau = s['tau_h']
    full = _full(bars)
    closes = full['close']
    pf = dataset4.price_features(bars).join(px_features(bars))
    w = cfg['window']
    times = pd.date_range(pd.Timestamp(w['start']) + pd.Timedelta(hours=s['hour']),
                          pd.Timestamp(w['end']) + pd.Timedelta(hours=s['hour']), freq='D')
    rows = {}
    for t in times:
        tr = trades_for_day(t.date().isoformat())
        if tr is None or not len(tr):
            continue
        expiry = t.normalize() + pd.Timedelta(days=s['expiry_days'], hours=8)
        iv = implied.decision_iv(tr, t, expiry, cfg['implied'])
        bar = t - H
        if iv is None or bar not in pf.index:
            continue
        s0 = closes.get(bar)
        s_t = closes.get(expiry - H) if settle is None else settle.get(expiry.date().isoformat())
        dv, dv24 = dvol.get(bar), dvol.get(bar - 24 * H)
        frow = flows.loc[bar].to_dict() if bar in flows.index else {c: np.nan for c in flows.columns}
        rows[t] = {**pf.loc[bar].to_dict(), **frow,
                   'mk_dvol': np.log(dv) if dv else np.nan,
                   'mk_dvol_chg24': np.log(dv) - np.log(dv24) if dv and dv24 else np.nan,
                   'mk_iv': np.log(iv['iv_mid'] / 100.0),
                   'y': realized_logvol(closes, t, tau), 's0': s0, 'sT': s_t,
                   'K': min(iv['strikes'], key=lambda k: abs(k - s0)) if s0 is not None and s0 == s0 else np.nan,
                   'tau_h': float(tau), 'iv_mid': iv['iv_mid'], 'iv_ask': iv['iv_ask'], 'iv_bid': iv['iv_bid'],
                   'n_trades': iv['n_trades']}
    df = pd.DataFrame.from_dict(rows, orient='index').sort_index()
    if not len(df):
        return df
    df = fill_spread(df, cfg['implied']['spread_window'])
    need = [c for c in df.columns if c.startswith(('h0_', 'px_', 'mk_', 'eth_', 'stable_'))] + ['y', 's0', 'sT', 'K', 'iv_ask', 'iv_bid']
    return df[np.isfinite(df[need].astype(float).to_numpy()).all(axis=1)]
