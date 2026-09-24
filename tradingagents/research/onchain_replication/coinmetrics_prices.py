"""Explicit alternative source; pinned daily PriceUSD, never a silent fallback."""
import csv
import io
import json
import math
import http.client
from pathlib import Path
from dataclasses import asdict
from datetime import date, datetime, timezone
from ..lifecycle import ResearchRun, _immutable
from .contracts import PricePanel
from .prices import _fetch
from .cache import cache_key, publish
from .provenance import digest, utc, file_hash, canonical_bytes, durable_mkdir, sync_directory
from .source_inventory import required_dates

REVISION = 'f1a36afb962731c387bb03982758ab0103063da5'


def price_policy(asset):
    if asset not in ('BTC', 'ETH'):
        raise ValueError('unsupported price asset')
    return {'asset': asset, 'symbol': asset+'-USD', 'provider': 'Coin Metrics',
        'revision': REVISION, 'field': 'PriceUSD', 'frequency': '1d',
        'start': '2016-01-01', 'end_exclusive': '2025-01-01',
        'url': f'https://raw.githubusercontent.com/coinmetrics/data/{REVISION}/csv/{asset.lower()}.csv',
        'timeout_seconds': 30, 'max_bytes': 32*1024**2, 'max_rows': 10000, 'max_columns': 512,
        'requests': 1, 'retries': 0, 'license': 'CC BY-NC 4.0',
        'qualification': 'retrospective Coin Metrics daily UTC closing PriceUSD; date denotes represented day; availability assumed next midnight; historical publication and original paper identity unverified'}


def _policy(policy):
    if not isinstance(policy, dict) or policy != price_policy(policy.get('asset')):
        raise ValueError('registered Coin Metrics policy differs')


def parse_prices(raw, *, expected_dates, policy, sha256, retrieved_at):
    _policy(policy)
    if digest(raw) != sha256:
        raise ValueError('price source hash mismatch')
    utc(retrieved_at)
    if len(raw) > policy['max_bytes']:
        raise ValueError('price response byte limit')
    expected = list(expected_dates)
    if expected != sorted(set(expected)) or any(date.fromisoformat(d).isoformat() != d for d in expected):
        raise ValueError('invalid price denominator')
    values = {}; first = last = None; rows = outside = 0; required = set(expected)
    try:
        reader = csv.reader(io.StringIO(raw.decode('utf-8'), newline=''), strict=True)
        header = next(reader)
        if not 2 <= len(header) <= policy['max_columns'] or len(set(header)) != len(header) or any(not s for s in header):
            raise ValueError('invalid CSV header')
        if 'time' not in header or 'PriceUSD' not in header:
            raise ValueError('required time/PriceUSD absent; no metric fallback')
        ti, pi = header.index('time'), header.index('PriceUSD')
        for row in reader:
            rows += 1
            if rows > policy['max_rows'] or len(row) != len(header):
                raise ValueError('CSV row bound/width differs')
            day = row[ti]
            if date.fromisoformat(day).isoformat() != day or (last is not None and day <= last):
                raise ValueError('invalid or duplicate/unsorted daily date')
            if first is None: first = day
            last = day
            value = None if row[pi] == '' else float(row[pi])
            if value is not None and (not math.isfinite(value) or value <= 0):
                raise ValueError('invalid PriceUSD')
            if day in required: values[day] = value
            else: outside += 1
    except (csv.Error, UnicodeError, StopIteration, OverflowError) as error:
        raise ValueError('invalid price CSV: '+type(error).__name__) from error
    if not rows: raise ValueError('empty price CSV')
    dates = tuple(d for d in expected if values.get(d) is not None)
    panel = PricePanel(policy['symbol'], dates, tuple(values[d] for d in dates),
        tuple(d for d in expected if values.get(d) is None), sha256, retrieved_at)
    return panel, {'rows': rows, 'first_date': first, 'last_date': last, 'outside_required_dates': outside}


def capture_response(policy, root, *, fetch=_fetch):
    """Exclusive durable intent and one bounded HTTP attempt; retain known prefix."""
    _policy(policy)
    root = Path(root); durable_mkdir(root)
    identity = cache_key(policy)
    intent = {'policy': policy, 'started_at': datetime.now(timezone.utc).isoformat()}
    _immutable(root/(identity+'.intent.json'), intent)
    result = dict(intent, status='unavailable', http_status=None, response_headers={})
    body = b''
    try:
        status, headers, body = fetch(policy['url'], policy['timeout_seconds'], policy['max_bytes'])
        result.update(http_status=status, response_headers=headers)
        if len(body) > policy['max_bytes']:
            raise ValueError('response byte limit exceeded; retained prefix')
        if status != 200: raise ValueError(f'HTTP {status}')
        result['status'] = 'complete'
    except Exception as error:
        if isinstance(error, http.client.IncompleteRead): body = error.partial[:policy['max_bytes']+1]
        result['reason'] = f'{type(error).__name__}: {error}'
    result['finished_at'] = datetime.now(timezone.utc).isoformat()
    publish(root, identity, {'response.bin': body, 'receipt.json': canonical_bytes(result)}, policy)
    return result, root/identity/'response.bin'


def capture_admitted_prices(run, asset, *, fetch=_fetch):
    if not isinstance(run, ResearchRun): raise ValueError('admitted price source run required')
    run._active(); run._check_source()
    policy = json.loads(run.read_input('price_policy'))
    if policy != price_policy(asset): raise ValueError('registered price policy differs')
    dates = [d for y in range(2016, 2025) for d in required_dates(y)]
    if run.admission.experiment['cells'] != ['capture', *('price-'+d for d in dates)]:
        raise ValueError('registered price denominator differs')
    directory = run.admission.root/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/run.admission.experiment_id
    durable_mkdir(directory.parent); directory.mkdir(exist_ok=False); sync_directory(directory.parent)
    result, body = capture_response(policy, directory/'capture', fetch=fetch)
    manifest = {'path': str(body), 'sha256': file_hash(body), 'retrieved_at': result['finished_at'],
        'expected_dates': dates, 'status': result['status'], 'policy': policy,
        'capture_manifest_sha256': file_hash(body.parent/'manifest.json')}
    panel = None; extent = None; reason = result.get('reason')
    if result['status'] == 'complete':
        try:
            panel, extent = parse_prices(body.read_bytes(), expected_dates=dates, policy=policy,
                sha256=manifest['sha256'], retrieved_at=manifest['retrieved_at'])
        except (ValueError, TypeError, KeyError) as error:
            reason = 'source schema unavailable: '+type(error).__name__+': '+str(error)
    rows = [{'id': 'capture', 'status': result['status'],
        'reason': result.get('reason') or 'bounded HTTP response retained; daily schema/coverage is separate'}]
    values = {} if panel is None else dict(zip(panel.dates, panel.closes, strict=True))
    for day in dates:
        row = {'id': 'price-'+day, 'date': day, 'status': 'complete' if day in values else 'unavailable',
            'reason': policy['qualification'] if day in values else reason or 'missing daily PriceUSD; not filled'}
        _immutable(directory/(row['id']+'.json'), row); rows.append(row)
    _immutable(directory/'capture.json', rows[0]); _immutable(directory/'price-manifest.json', manifest)
    _immutable(directory/'price-panel.json', None if panel is None else asdict(panel))
    summary = {'asset': asset, 'provider': policy['provider'], 'required_dates': len(dates),
        'admitted_dates': len(values), 'missing_dates': [d for d in dates if d not in values],
        'schema_accepted': panel is not None, 'all_dates_available': len(values)==len(dates),
        'archive_extent': extent, 'reason': reason, 'qualification': policy['qualification'],
        'financial_run_admitted': False, 'source_manifest_sha256': file_hash(directory/'price-manifest.json')}
    return rows, summary, directory
