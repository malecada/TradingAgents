"""Offline Yahoo response adapter. Acquisition requires a separate source gate."""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import json
import math
from .contracts import PricePanel
from .provenance import file_hash,utc


def read_prices(manifest: dict,price_config: dict) -> PricePanel:
    if manifest.get('status')!='complete':raise ValueError('unavailable price source cell')
    path=Path(manifest['path'])
    if file_hash(path)!=manifest['sha256']:raise ValueError('price source hash mismatch')
    utc(manifest['retrieved_at'])
    body=json.loads(path.read_bytes())
    chart=body['chart']
    if chart.get('error') is not None or not chart.get('result'):raise ValueError('unavailable Yahoo response')
    if len(chart['result'])!=1:raise ValueError('ambiguous price response')
    data=chart['result'][0];meta=data['meta']
    if meta['symbol']!=price_config['symbol'] or meta.get('currency')!='USD':raise ValueError('price instrument mismatch')
    if meta.get('exchangeTimezoneName') not in ('UTC','Etc/UTC'):raise ValueError('price timezone not admitted')
    if price_config['field']!='unadjusted daily Close':raise ValueError('unsupported price field')
    timestamps=data['timestamp'];closes=data['indicators']['quote'][0]['close']
    if len(timestamps)!=len(closes):raise ValueError('price length mismatch')
    values={}
    for ts,close in zip(timestamps,closes,strict=True):
        t=datetime.fromtimestamp(ts,timezone.utc)
        if (t.hour,t.minute,t.second,t.microsecond)!=(0,0,0,0):raise ValueError('nonmidnight daily bar')
        date=t.date().isoformat()
        if date in values:raise ValueError('duplicate price date')
        if close is not None and (not math.isfinite(close) or close<=0):raise ValueError('invalid close')
        values[date]=close
    expected=manifest['expected_dates']
    if len(expected)!=len(set(expected)) or expected!=sorted(expected):raise ValueError('invalid price denominator')
    if set(values)-set(expected):raise ValueError('unexpected price dates')
    dates=tuple(d for d in expected if values.get(d) is not None)
    missing=tuple(d for d in expected if values.get(d) is None)
    return PricePanel(price_config['symbol'],dates,tuple(values[d] for d in dates),missing,manifest['sha256'],manifest['retrieved_at'])


def _fetch(url,timeout,maximum):
    import urllib.request
    import urllib.error
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    try:response=opener.open(url,timeout=timeout)
    except urllib.error.HTTPError as error:response=error
    with response:
        return response.status,{k.lower():v for k,v in response.headers.items() if k.lower() in {'content-type','date','etag','last-modified'}},response.read(maximum+1)


def capture_prices(contract,root,identity,*,fetch=_fetch):
    """One bounded public request. Caller must admit its source claim beforehand.

    The exclusive intent is persisted before the request, including failed or
    interrupted attempts. Existing intents/results are never retried here.
    """
    from urllib.parse import urlsplit,parse_qs
    import os
    from .cache import publish
    from .provenance import canonical_bytes,require_hash,durable_mkdir,sync_directory
    require_hash(identity)
    url=contract['url'];target=urlsplit(url);query=parse_qs(target.query)
    if (target.scheme!='https' or target.netloc!='query1.finance.yahoo.com'
        or target.path not in ('/v8/finance/chart/ETH-USD','/v8/finance/chart/BTC-USD')
        or set(query)!={'period1','period2','interval'} or query['interval']!=['1d']
        or target.fragment):raise ValueError('unregistered public price endpoint')
    if not 0<contract['timeout_seconds']<=30 or not 0<contract['max_bytes']<=8*1024**2:raise ValueError('capture bounds')
    root=Path(root);durable_mkdir(root)
    intent={'contract':contract,'started_at':datetime.now(timezone.utc).isoformat()}
    with (root/(identity+'.intent.json')).open('xb') as stream:
        stream.write(canonical_bytes(intent));stream.flush();os.fsync(stream.fileno())
    sync_directory(root)
    result=dict(intent,status='unavailable',http_status=None,response_headers={})
    body=b''
    try:
        status,headers,body=fetch(url,contract['timeout_seconds'],contract['max_bytes'])
        result.update(http_status=status,response_headers=headers)
        if len(body)>contract['max_bytes']:raise ValueError('response byte limit exceeded; retained prefix')
        if status!=200:raise ValueError(f'HTTP {status}')
        result['status']='complete'
    except Exception as error:
        result['reason']=f'{type(error).__name__}: {error}'
    result['finished_at']=datetime.now(timezone.utc).isoformat()
    publish(root,identity,{'response.bin':body,'receipt.json':canonical_bytes(result)},contract)
    return result
