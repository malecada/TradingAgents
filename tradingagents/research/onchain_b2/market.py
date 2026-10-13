"""Daily ETH close (Coin Metrics community PriceUSD) and volume (Binance ETHUSDT quote
volume). Dates after the development cutoff are written only to the sealed directory."""
from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

CM = ('https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets=eth&metrics=PriceUSD'
      '&frequency=1d&start_time={start}&end_time={end}&page_size=10000')
BN = 'https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1d&startTime={ms}&limit=1000'
DAY_MS = 86_400_000


def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers={'User-Agent': 'onchain-b2-research'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_coinmetrics(get, start, end):
    url, out, pages = CM.format(start=start.isoformat(), end=end.isoformat()), {}, []
    while url:
        raw = get(url)
        pages.append(raw)
        doc = json.loads(raw)
        for r in doc['data']:
            out[date.fromisoformat(r['time'][:10])] = float(r['PriceUSD'])
        url = doc.get('next_page_url')
    return out, pages


def fetch_binance(get, start, end):
    ms = int(datetime(start.year, start.month, start.day, tzinfo=timezone.utc).timestamp() * 1000)
    out, pages = {}, []
    while True:
        raw = get(BN.format(ms=ms))
        pages.append(raw)
        rows = json.loads(raw)
        for k in rows:
            d = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).date()
            if start <= d <= end:
                out[d] = float(k[7])
        if len(rows) < 1000 or datetime.fromtimestamp(rows[-1][0] / 1000, tz=timezone.utc).date() >= end:
            break
        ms = rows[-1][0] + DAY_MS
    return out, pages


def _iso(d):
    return {k.isoformat(): v for k, v in sorted(d.items())}


def store(prices, volumes, pages, out_dir, cutoff):
    out_dir = Path(out_dir)
    (out_dir / 'market').mkdir(parents=True, exist_ok=True)
    (out_dir / 'sealed' / 'raw').mkdir(parents=True, exist_ok=True)
    dev = {'prices': _iso({d: v for d, v in prices.items() if d <= cutoff}),
           'volumes': _iso({d: v for d, v in volumes.items() if d <= cutoff})}
    sealed = {'prices': _iso({d: v for d, v in prices.items() if d > cutoff}),
              'volumes': _iso({d: v for d, v in volumes.items() if d > cutoff})}
    (out_dir / 'market' / 'dev.json').write_text(json.dumps(dev))
    (out_dir / 'sealed' / 'market_sealed.json').write_text(json.dumps(sealed))
    index = {}
    for source, raws in pages.items():
        for raw in raws:            # raw responses span both windows, so they stay sealed
            h = hashlib.sha256(raw).hexdigest()
            (out_dir / 'sealed' / 'raw' / f'{h}.json').write_bytes(raw)
            index.setdefault(source, []).append(h)
    meta = {'cutoff': cutoff.isoformat(), 'dev_prices': len(dev['prices']), 'dev_volumes': len(dev['volumes']),
            'sealed_prices': len(sealed['prices']), 'sealed_volumes': len(sealed['volumes']), 'raw': index}
    (out_dir / 'market' / 'meta.json').write_text(json.dumps(meta, indent=1))
    return meta


def _parse(doc):
    return ({date.fromisoformat(k): float(v) for k, v in doc['prices'].items()},
            {date.fromisoformat(k): float(v) for k, v in doc['volumes'].items()})


def load_dev(path, cutoff):
    prices, volumes = _parse(json.loads(Path(path).read_text()))
    if any(d > cutoff for d in list(prices) + list(volumes)):
        raise ValueError('development market file contains sealed dates')
    return prices, volumes


def load_all(dev_path, sealed_path):
    p1, v1 = _parse(json.loads(Path(dev_path).read_text()))
    p2, v2 = _parse(json.loads(Path(sealed_path).read_text()))
    return {**p1, **p2}, {**v1, **v2}