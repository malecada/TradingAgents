"""Finite admitted Yahoo source capture; every required daily Close is retained."""
from pathlib import Path
from dataclasses import asdict
from datetime import datetime,timezone
import json
from ..lifecycle import ResearchRun,_immutable
from .prices import capture_prices,read_prices,_fetch
from .source_inventory import required_dates
from .cache import cache_key
from .provenance import file_hash,durable_mkdir,sync_directory


def price_policy(asset):
    if asset not in ('BTC','ETH'):raise ValueError('unsupported price asset')
    return {'asset':asset,'symbol':asset+'-USD','field':'unadjusted daily Close',
        'start':'2016-01-01','end_exclusive':'2025-01-01','url':'https://query1.finance.yahoo.com/v8/finance/chart/'+asset+'-USD?period1=1451606400&period2=1735689600&interval=1d',
        'timeout_seconds':30,'max_bytes':8*1024**2,'requests':1,'retries':0,
        'qualification':'current retrospective Yahoo vintage; historical publication assumed, not verified'}


def capture_admitted_prices(run,asset,*,fetch=_fetch):
    if not isinstance(run,ResearchRun):raise ValueError('admitted price source run required')
    run._active();run._check_source()
    policy=json.loads(run.read_input('price_policy'))
    if policy!=price_policy(asset):raise ValueError('registered price policy differs')
    dates=[day for year in range(2016,2025) for day in required_dates(year)]
    ids=['capture',*('price-'+day for day in dates)]
    if run.admission.experiment['cells']!=ids:raise ValueError('registered price denominator differs')
    directory=run.admission.root/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/run.admission.experiment_id
    durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)
    contract={k:policy[k] for k in ('url','timeout_seconds','max_bytes')};identity=cache_key(policy)
    result=capture_prices(contract,directory/'capture',identity,fetch=fetch)
    body=directory/'capture'/identity/'response.bin'
    manifest={'path':str(body),'sha256':file_hash(body),'retrieved_at':result['finished_at'],
        'expected_dates':dates,'status':result['status'],'symbol':policy['symbol'],'field':policy['field'],
        'capture_manifest_sha256':file_hash(body.parent/'manifest.json'),'qualification':policy['qualification']}
    panel=None;reason=result.get('reason')
    if result['status']=='complete':
        try:panel=read_prices(manifest,policy)
        except (ValueError,KeyError,TypeError,IndexError,OverflowError) as error:reason='source schema unavailable: '+type(error).__name__+': '+str(error)
    rows=[{'id':'capture','status':result['status'],'reason':result.get('reason') or 'bounded HTTP response retained; daily schema/coverage is separate'}]
    values={} if panel is None else dict(zip(panel.dates,panel.closes,strict=True))
    for day in dates:
        row={'id':'price-'+day,'date':day,'status':'complete' if day in values else 'unavailable',
            'reason':'valid daily unadjusted USD Close under retrospective clock assumption' if day in values else reason or 'missing/null daily Close; not filled'}
        _immutable(directory/(row['id']+'.json'),row);rows.append(row)
    _immutable(directory/'capture.json',rows[0]);_immutable(directory/'price-manifest.json',manifest)
    _immutable(directory/'price-panel.json',None if panel is None else asdict(panel))
    summary={'asset':asset,'required_dates':len(dates),'admitted_dates':len(values),
        'missing_dates':[d for d in dates if d not in values],'schema_accepted':panel is not None,
        'all_dates_available':len(values)==len(dates),'reason':reason,'qualification':policy['qualification'],
        'financial_run_admitted':False,'source_manifest_sha256':file_hash(directory/'price-manifest.json')}
    return rows,summary,directory
