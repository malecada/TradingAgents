# tradingagents/research/onchain_b4/cmdaily.py
"""Coin Metrics community daily metrics (spec §5.1). Dates after the development cutoff are
written only to the sealed directory: MVRV and the stablecoin ratio carry the price."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

URL = ('https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets={assets}&metrics={metrics}'
       '&frequency=1d&start_time={start}&end_time={end}&page_size=10000&paging_from=start')


def fetch(get, assets, metrics, start, end):
    url = URL.format(assets=','.join(assets), metrics=','.join(metrics), start=start, end=end)
    out, pages = {}, []
    while url:
        raw = get(url)
        pages.append(raw)
        doc = json.loads(raw)
        for r in doc['data']:
            for m in metrics:
                if r.get(m) is not None:
                    out.setdefault(r['asset'], {}).setdefault(m, {})[r['time'][:10]] = float(r[m])
        url = doc.get('next_page_url')
    return out, pages


def _frame(cols):
    df = pd.DataFrame({c: pd.Series({pd.Timestamp(d): v for d, v in s.items()}, dtype=float) for c, s in cols.items()})
    return df.sort_index()


def to_frame(data, eth_metrics, stables):
    cols = {m: data.get('eth', {}).get(m, {}) for m in eth_metrics}
    cols.update({a: data.get(a, {}).get('SplyCur', {}) for a in stables})
    return _frame(cols)


def _doc(frame):
    return {c: {d.strftime('%Y-%m-%d'): float(v) for d, v in frame[c].dropna().items()} for c in frame.columns}


def store(frame, pages, out_dir, cutoff):
    out_dir, cut = Path(out_dir), pd.Timestamp(cutoff)
    (out_dir / 'market').mkdir(parents=True, exist_ok=True)
    (out_dir / 'sealed' / 'raw').mkdir(parents=True, exist_ok=True)
    dev, sealed = frame[frame.index <= cut], frame[frame.index > cut]
    (out_dir / 'market' / 'cm_dev.json').write_text(json.dumps(_doc(dev)))
    (out_dir / 'sealed' / 'cm_sealed.json').write_text(json.dumps(_doc(sealed)))
    for raw in pages:
        (out_dir / 'sealed' / 'raw' / f'cm-{hashlib.sha256(raw).hexdigest()}.json').write_bytes(raw)
    meta = {'cutoff': str(cut.date()), 'dev_days': len(dev), 'sealed_days': len(sealed), 'columns': list(frame.columns)}
    (out_dir / 'market' / 'cm_meta.json').write_text(json.dumps(meta, indent=1))
    return meta


def load_dev(path, cutoff):
    df = _frame(json.loads(Path(path).read_text()))
    if len(df) and df.index.max() > pd.Timestamp(cutoff):
        raise ValueError('development Coin Metrics file contains sealed dates')
    return df


def load_all(dev_path, sealed_path):
    return pd.concat([_frame(json.loads(Path(dev_path).read_text())),
                      _frame(json.loads(Path(sealed_path).read_text()))]).sort_index()
