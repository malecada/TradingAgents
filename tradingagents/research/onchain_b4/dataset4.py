# tradingagents/research/onchain_b4/dataset4.py
"""B4 features, targets and samples (spec §4.6–4.7, §5.2–5.3). Every feature at time t uses data
up to the end of t only; a sample enters a target only if the label window lies in its window."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2 import targets as T
from . import flows

HOURLY_FEATURES = ('h0_', 'eth_', 'stable_', 'act_')
HOURLY_TARGETS = ('R1', 'R6', 'R24', 'V6', 'V24')


def zscore(x, window, min_periods, clip):
    prev = x.shift(1)
    mean = prev.rolling(window, min_periods=min_periods).mean()
    std = prev.rolling(window, min_periods=min_periods).std(ddof=0)
    z = (x - mean) / std
    z[(std == 0) & x.notna()] = 0.0
    return z.clip(-clip, clip)


def hourly_table(hours_dir, days):
    frames = [pd.read_parquet(hours_dir / f'{d}.parquet') for d in days if (hours_dir / f'{d}.parquet').exists()]
    raw = pd.concat(frames).sort_index()
    return raw.reindex(pd.date_range(days[0], periods=24 * len(days), freq='h'))


def transform_hourly(raw, c):
    out = {}
    for name in flows.SERIES + flows.LAB:
        out[f'{name}__h1z'] = zscore(np.log1p(raw[name]), c['h1_window'], c['h1_min'], c['clip'])
        s24 = raw[name].rolling(24, min_periods=24).sum()
        out[f'{name}__d24z'] = zscore(np.log1p(s24), c['d24_window'], c['d24_min'], c['clip'])
    for prefix in ('', 'lab_'):
        for a in ('eth', 'stable'):
            i24 = raw[f'{prefix}{a}_in_val'].rolling(24, min_periods=24).sum()
            o24 = raw[f'{prefix}{a}_out_val'].rolling(24, min_periods=24).sum()
            out[f'{prefix}{a}_net24__z'] = zscore(np.log1p(i24) - np.log1p(o24), c['d24_window'], c['d24_min'], c['clip'])
    return pd.DataFrame(out, index=raw.index)


def _full(bars):
    return bars.reindex(pd.date_range(bars.index.min(), bars.index.max(), freq='h'))


def price_features(bars):
    b = _full(bars)
    lc = np.log(b['close'])
    r = lc.diff()
    f = pd.DataFrame(index=b.index)
    for k in (1, 4, 24, 168):
        f[f'h0_r{k}'] = lc - lc.shift(k)
    for k in (24, 168):
        f[f'h0_rv{k}'] = np.sqrt((r ** 2).rolling(k, min_periods=k).sum())
    v24 = b['qvol'].rolling(24, min_periods=24).sum()
    v168 = b['qvol'].rolling(168, min_periods=168).sum()
    f['h0_lvol24'] = np.log(v24)
    f['h0_volratio'] = np.log(v24 / (v168 / 7))
    return f.replace([np.inf, -np.inf], np.nan)


def hourly_targets(bars):
    b = _full(bars)
    lc = np.log(b['close'])
    r2 = lc.diff() ** 2
    t = pd.DataFrame(index=b.index)
    for k in (1, 6, 24):
        t[f'R{k}'] = lc.shift(-k) - lc
    for k in (6, 24):
        fut = r2.rolling(k, min_periods=k).sum().shift(-k)
        t[f'V{k}'] = np.log(np.sqrt(fut).clip(lower=1e-8))
    return t


def window_mask(index, horizon_hours, unit_hours, window, cfg):
    w = {k: pd.Timestamp(v) for k, v in cfg['windows'].items()}
    start, end = (w['dev_start'], w['dev_end']) if window == 'dev' else (w['holdout_start'], w['holdout_end'])
    t = pd.DatetimeIndex(index)
    return np.asarray((t >= start) & (t + pd.Timedelta(hours=horizon_hours + unit_hours) <= end + pd.Timedelta(days=1)))


def hourly_samples(trans, bars, window, cfg):
    df = trans.join(price_features(bars), how='inner').join(hourly_targets(bars), how='left')
    df = df[window_mask(df.index, 0, 1, window, cfg)]
    req = [c for c in df.columns if c.startswith(HOURLY_FEATURES)]
    ok = df[req].notna().all(axis=1)
    excluded = {'features_incomplete': int((~ok).sum())}
    df = df[ok].copy()
    for name, tc in cfg['targets'].items():
        if tc['kind'] == 'hourly':
            df.loc[~window_mask(df.index, tc['horizon_hours'], 1, window, cfg), name] = np.nan
    return df, excluded


def cm_values(cm, prices):
    idx = pd.date_range(cm.index.min(), cm.index.max(), freq='D')
    cm = cm.reindex(idx)
    p = pd.Series({pd.Timestamp(d): v for d, v in prices.items()}, dtype=float).reindex(idx)
    stable = (cm['usdt'].fillna(0) + cm['usdc'].fillna(0) + cm['dai'].fillna(0)).where(cm['usdt'].notna())
    v = pd.DataFrame(index=idx)
    v['cmf_in'] = np.log1p(cm['FlowInExNtv'])
    v['cmf_out'] = np.log1p(cm['FlowOutExNtv'])
    v['cmf_net'] = (cm['FlowInExNtv'] - cm['FlowOutExNtv']) / cm['SplyExNtv']
    v['cmf_sply_chg7'] = np.log(cm['SplyExNtv'] / cm['SplyExNtv'].shift(7))
    v['cmf_ex_share'] = cm['SplyExNtv'] / cm['SplyCur']
    v['cmo_mvrv'] = np.log(cm['CapMVRVCur'])
    v['cmo_adr'] = np.log(cm['AdrActCnt'])
    v['cmo_fee'] = np.log1p(cm['FeeTotNtv'])
    v['cmo_stable_chg7'] = np.log(stable / stable.shift(7))
    v['cmo_ssr'] = np.log(stable / (p * cm['SplyCur']))
    return v.replace([np.inf, -np.inf], np.nan)


def transform_daily(values, c):
    x = values.shift(c['lag_days'])
    out = {}
    for name in x.columns:
        out[f'{name}__z28'] = zscore(x[name], c['z_window'], c['z_min'], c['clip'])
        out[f'{name}__d1'] = x[name] - x[name].shift(1)
    return pd.DataFrame(out, index=x.index)


def daily_samples(trans, prices, volumes, window, cfg):
    rows, excluded = {}, {'features_incomplete': 0, 'f0_unavailable': 0}
    for t in trans.index[window_mask(trans.index, 0, 24, window, cfg)]:
        feats = trans.loc[t]
        if feats.isna().any():
            excluded['features_incomplete'] += 1
            continue
        d = t.date()
        f0 = T.f0(prices, volumes, d)
        if f0 is None:
            excluded['f0_unavailable'] += 1
            continue
        rows[t] = {**feats.to_dict(), **f0, 'T1': T.t1(prices, d), 'R7': T.t3(prices, d), 'V7': T.t4(prices, d)}
    df = pd.DataFrame.from_dict(rows, orient='index').sort_index().astype(float)
    for name, tc in cfg['targets'].items():
        if tc['kind'] == 'daily':
            df.loc[~window_mask(df.index, tc['horizon_hours'], 24, window, cfg), name] = np.nan
    return df, excluded
