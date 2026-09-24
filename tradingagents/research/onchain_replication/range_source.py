"""Finite, conditional selected-column acquisition behind an admitted claim.

This stage retains bytes and schema membership, not canonical-chain/value
admission. Each response, including denial or oversized responses, is immutable.
A failed/partial object is never retried here. Any continuation needs a new
registration that explicitly reconciles retained bytes. An outer resource guard
is required: blob limits exclude bounded JSON receipts and temporary memory.
"""
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.parse import quote

import zstandard

from ..lifecycle import ResearchRun, _immutable
from .parquet_ranges import plan_ranges
from .provenance import digest, file_hash, durable_mkdir, sync_directory
from .source_inventory import HOST, http_transport


def range_policy(asset, dates, catalogues, *, maximum_span_bytes,
                 max_requests, max_received_bytes, max_blob_bytes):
    """Construct a registration input; construction grants no execution permit."""
    dates = list(dates)
    if asset not in ('BTC', 'ETH') or not dates or dates != sorted(set(dates)):
        raise ValueError('source asset/date population')
    if any(date.fromisoformat(d).isoformat() != d or not 2016 <= date.fromisoformat(d).year <= 2024 for d in dates):
        raise ValueError('source calendar bounds')
    years = {d[:4] for d in dates}
    if set(catalogues) != years or any(not isinstance(x, str) or not x for x in catalogues.values()):
        raise ValueError('registered catalogue year membership')
    for value, upper in ((maximum_span_bytes, 64*1024**2), (max_requests, 500_000),
                         (max_received_bytes, 2*1024**4), (max_blob_bytes, 2*1024**4)):
        if type(value) is not int or not 0 < value <= upper:
            raise ValueError('source resource bounds')
    return {'schema_version': 1, 'asset': asset, 'dates': dates, 'catalogue_inputs': dict(catalogues),
            'host': HOST, 'timeout_seconds': 30, 'retries': 0,
            'maximum_span_bytes': maximum_span_bytes, 'maximum_footer_bytes': 2*1024**2,
            'maximum_object_bytes': 8*1024**3, 'maximum_objects_per_date': 128,
            'max_requests': max_requests, 'max_received_bytes': max_received_bytes,
            'max_blob_bytes': max_blob_bytes, 'blob_limit_scope': 'compressed response bodies only',
            'footer_requests': 'trailer then footer; selected spans reacquire metadata with same ETag',
            'decode_transaction_pages': False}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _write_blob(path, body):
    with path.open('xb') as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(path.parent)


class _Budget:
    def __init__(self, run, policy, transport):
        self.run, self.policy, self.transport = run, policy, transport
        self.requests = self.received = self.charged = self.stored = 0
        self.unknown_transport_bytes = 0

    def request(self, directory, name, item, a, b):
        """Half-open range, including a reserved one-byte overflow observation."""
        self.run._active()
        self.run._check_source()
        maximum = b-a
        if not 0 <= a < b <= item['bytes']:
            raise ValueError('range outside catalogued object')
        if self.requests >= self.policy['max_requests'] or self.charged + maximum + 1 > self.policy['max_received_bytes']:
            raise ValueError('registered request/received-byte budget exhausted')
        # Conservative reservation also retains a bounded erroneous response.
        if self.stored + 2*(maximum+1) + 1024 > self.policy['max_blob_bytes']:
            raise ValueError('registered compressed-blob budget exhausted')
        headers = {'Range': f'bytes={a}-{b-1}', 'If-Match': item['etag'], 'Accept-Encoding': 'identity'}
        url = HOST + quote(item['key'], safe='/=')
        _immutable(directory / (name+'-intent.json'), {
            'url': url, 'headers': headers, 'maximum_bytes': maximum, 'overflow_observation_bytes': 1,
            'requested_at': _now(), 'retry': False, 'source_commit': self.run.admission.source})
        self.requests += 1  # A transport failure consumes its request attempt.
        self.charged += maximum + 1
        try:
            status, reply, body = self.transport(url, headers, maximum)
        except Exception as error:
            # A short read may expose a prefix even though transport did not
            # return. Preserve it, and conservatively charge the entire reserved
            # bound: the exception cannot prove that no other bytes arrived.
            partial = getattr(error, 'partial', b'')
            if not isinstance(partial, bytes) or len(partial) > maximum+1:
                partial = b''
            self.received += len(partial)
            self.unknown_transport_bytes += 1
            stored = zstandard.ZstdCompressor(level=3).compress(partial)
            blob = directory / (name+'-partial.zst')
            _write_blob(blob, stored)
            self.stored += len(stored)
            _immutable(directory / (name+'-transport-error.json'), {
                'reason': type(error).__name__+': '+str(error), 'finished_at': _now(),
                'partial_body': {'path': str(blob), 'raw_bytes': len(partial),
                                 'raw_sha256': digest(partial), 'stored_bytes': len(stored),
                                 'stored_sha256': digest(stored), 'codec': 'zstd'},
                'received_bytes_unknown': True, 'charged_bytes': maximum+1,
                'cumulative_charged_bytes': self.charged})
            raise
        if not isinstance(body, bytes) or len(body) > maximum+1:
            raise ValueError('transport violated bounded response contract')
        self.received += len(body)
        self.charged -= maximum + 1 - len(body)
        stored = zstandard.ZstdCompressor(level=3).compress(body)
        if self.stored + len(stored) > self.policy['max_blob_bytes']:
            raise ValueError('compression bound violated')
        blob = directory / (name+'.zst')
        _write_blob(blob, stored)
        self.stored += len(stored)
        span = {'start': a, 'end': b, 'path': str(blob), 'codec': 'zstd',
                'raw_bytes': len(body), 'raw_sha256': digest(body),
                'stored_bytes': len(stored), 'stored_sha256': digest(stored)}
        _immutable(directory / (name+'-response.json'), {
            'status': status, 'headers': reply, 'body': span, 'received_at': _now(),
            'cumulative_requests': self.requests, 'cumulative_received_bytes': self.received,
            'cumulative_charged_bytes': self.charged,
            'cumulative_blob_bytes': self.stored})
        lower = {k.lower(): v for k, v in reply.items()}
        if len(lower) != len(reply):
            raise ValueError('ambiguous response headers')
        if status != 206 or lower.get('content-range') != f'bytes {a}-{b-1}/{item["bytes"]}' or len(body) != maximum:
            raise ValueError('range response differs from registered extent')
        if lower.get('etag') != item['etag']:
            raise ValueError('source ETag changed')
        if lower.get('content-encoding', 'identity').lower() != 'identity':
            raise ValueError('unexpected response content encoding')
        if 'content-length' in lower and lower['content-length'] != str(len(body)):
            raise ValueError('response Content-Length differs')
        return body, span


def _object(budget, directory, asset, item, catalogue_hash):
    directory.mkdir(exist_ok=False)
    sync_directory(directory.parent)
    result = {'asset': asset, 'date': item['date'], 'object': item,
              'catalogue_sha256': catalogue_hash, 'status': 'unavailable',
              'transaction_data_admitted': False}
    try:
        size = item['bytes']
        trailer, _ = budget.request(directory, 'trailer', item, size-8, size)
        length = int.from_bytes(trailer[:4], 'little')
        if trailer[4:] != b'PAR1' or not 0 < length <= 2*1024**2 or length > size-12:
            raise ValueError('footer framing/byte bound')
        footer, _ = budget.request(directory, 'footer', item, size-8-length, size-8)
        plan = plan_ranges(footer, trailer, size, asset,
                           maximum_span_bytes=budget.policy['maximum_span_bytes'])
        _immutable(directory / 'column-plan.json', plan)
        spans = []
        for number, extent in enumerate(plan['spans']):
            body, span = budget.request(directory, f'span-{number:06d}', item,
                                        extent['start'], extent['end'])
            if extent['start'] < 4 and body[:min(extent['end'], 4)-extent['start']] != b'PAR1'[extent['start']:min(extent['end'], 4)]:
                raise ValueError('invalid acquired Parquet header')
            # A same-ETag server inconsistency must not change planning metadata.
            start, end = extent['start'], extent['end']
            metadata_start = size-8-length
            if end > metadata_start:
                x = max(start, metadata_start)
                if body[x-start:] != (footer+trailer)[x-metadata_start:end-metadata_start]:
                    raise ValueError('reacquired footer differs from planning bytes')
            spans.append(span)
        projected = directory / 'projected.json'
        _immutable(projected, {'schema_version': 1, 'size': size, 'spans': spans,
                              'column_plan': plan, 'object': item, 'catalogue_sha256': catalogue_hash,
                              'transaction_data_admitted': False})
        result.update(status='complete', path=str(projected), sha256=file_hash(projected),
                      expected_rows=plan['rows'], selected_bytes=plan['selected_bytes'],
                      reason='all required column bytes retained; value/chain verification pending')
    except Exception as error:
        result['reason'] = type(error).__name__+': '+str(error)
    _immutable(directory / 'result.json', result)
    return result


def capture_ranges(run, *, transport=http_transport):
    """Acquire the exact registered date/object population once, preserving gaps."""
    if not isinstance(run, ResearchRun):
        raise ValueError('admitted source run required')
    run._active()
    run._check_source()
    policy = json.loads(run.read_input('range_policy'))
    expected = range_policy(policy['asset'], policy['dates'], policy['catalogue_inputs'],
                            **{k: policy[k] for k in ('maximum_span_bytes', 'max_requests',
                                                     'max_received_bytes', 'max_blob_bytes')})
    if expected != policy:
        raise ValueError('registered selected-range policy differs')
    asset = policy['asset']
    if run.admission.experiment['cells'] != [asset+'-'+d for d in policy['dates']]:
        raise ValueError('registered source date denominator differs')
    catalogues = {}
    for year, name in policy['catalogue_inputs'].items():
        raw = run.read_input(name)
        catalogue = json.loads(raw)
        if catalogue['asset'] != asset or catalogue['year'] != int(year) or catalogue['listing_complete'] is not True:
            raise ValueError('catalogue identity/completeness differs')
        catalogues[year] = catalogue, digest(raw)
    # Validate all metadata before the first network request.
    population = {}
    seen = set()
    for day in policy['dates']:
        catalogue, identity = catalogues[day[:4]]
        items = catalogue['dates'].get(day, {}).get('objects', [])
        if not isinstance(items, list) or len(items) > policy['maximum_objects_per_date']:
            raise ValueError('daily object count bound')
        for item in items:
            if item['date'] != day or not re.fullmatch(r'v1\.0/'+asset.lower()+r'/transactions/date='+day+r'/[A-Za-z0-9_.-]+\.parquet', item['key']):
                raise ValueError('foreign catalogued object')
            if item['key'] in seen or type(item['bytes']) is not int or not 12 <= item['bytes'] <= policy['maximum_object_bytes']:
                raise ValueError('duplicate/invalid catalogued object')
            if not isinstance(item['etag'], str) or not re.fullmatch(r'"[A-Za-z0-9-]+"', item['etag']):
                raise ValueError('invalid catalogued ETag')
            seen.add(item['key'])
        population[day] = sorted(items, key=lambda x: x['key']), identity
    directory = run.admission.root / 'research_artifacts/onchain-paper-replication-2026-09-24/sources' / run.admission.experiment_id
    durable_mkdir(directory.parent)
    directory.mkdir(exist_ok=False)
    (directory / 'objects').mkdir()
    sync_directory(directory)
    sync_directory(directory.parent)
    budget = _Budget(run, policy, transport)
    rows = []
    for day in policy['dates']:
        items, identity = population[day]
        members = [_object(budget, directory/'objects'/digest(item['key'].encode()), asset, item, identity) for item in items]
        complete = bool(members) and all(x['status'] == 'complete' for x in members)
        failed = [x['reason'] for x in members if x['status'] != 'complete']
        row = {'id': asset+'-'+day, 'date': day, 'status': 'complete' if complete else 'unavailable',
               'reason': '; '.join(failed) if failed else ('all declared object bytes retained; decoding pending' if complete else 'no catalogued object; not filled'),
               'members': members, 'catalogue_sha256': identity, 'transaction_data_admitted': False}
        _immutable(directory / (row['id']+'.json'), row)
        rows.append(row)
    summary = {'asset': asset, 'required_dates': len(rows), 'complete_dates': sum(x['status'] == 'complete' for x in rows),
               'required_objects': len(seen), 'requests': budget.requests, 'received_bytes': budget.received,
               'charged_bytes': budget.charged, 'requests_with_unknown_received_bytes': budget.unknown_transport_bytes,
               'blob_bytes': budget.stored, 'transaction_data_admitted': False,
               'qualification': 'current ETag-bound byte retention; no transaction decode, value/chain check or historical vintage admission'}
    _immutable(directory / 'summary.json', summary)
    return rows, summary, directory
