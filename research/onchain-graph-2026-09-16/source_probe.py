"""One frozen anonymous archive audit. No prices, labels, models or AWS credentials."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import struct
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from tradingagents.research import ResearchRun


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(body):
    return hashlib.sha256(body).hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Capture:
    def __init__(self, spec, publish):
        self.spec, self.publish = spec, publish
        self.count, self.total, self.denied = 0, 0, False
        # No cookies, auth handlers, credential discovery, retries or redirects.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def get(self, url, headers=None):
        if not url.startswith(self.spec['base_url']):
            raise ValueError('unregistered host/path')
        if self.denied or self.count >= self.spec['max_requests']:
            return None, {'error': 'source denied or request budget exhausted'}
        self.count += 1
        remaining = self.spec['max_total_bytes'] - self.total
        cap = min(self.spec['max_response_bytes'], remaining)
        record = {'url': url, 'request_headers': headers or {}, 'requested_at': now(),
                  'request_number': self.count, 'status': None}
        self.publish(f'request-{self.count:02d}-intent.json', {
            **record, 'status': 'intent', 'method': 'GET',
            'qualification': 'Published before I/O; a missing response receipt means outcome and any received prefix are unavailable. No automatic retry.'})
        body = b''
        response = None
        try:
            if cap <= 0:
                raise ValueError('total byte budget exhausted')
            request = urllib.request.Request(url, headers=headers or {})
            try:
                response = self.opener.open(request, timeout=self.spec['timeout_seconds'])
            except urllib.error.HTTPError as exc:
                response = exc
            record['status'] = response.status
            record['response_headers'] = {k.lower(): v for k, v in response.headers.items()
                if k.lower() in {'etag', 'content-length', 'content-range', 'last-modified', 'date'}}
            if response.status in {401, 403, 429}:
                self.denied = True
            chunks = []
            length = 0
            try:
                while length <= cap:
                    chunk = response.read(min(65536, cap + 1 - length))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    length += len(chunk)
            finally:
                body = b''.join(chunks)
            if len(body) > cap:
                raise ValueError('response byte limit exceeded; retained prefix is incomplete')
            expected_length = record['response_headers'].get('content-length')
            if expected_length is not None and len(body) != int(expected_length):
                raise ValueError('response body length mismatch')
            if response.status not in {200, 206}:
                raise ValueError(f'HTTP {response.status}')
        except Exception as exc:
            record['error'] = f'{type(exc).__name__}: {exc}'
        finally:
            if response is not None:
                response.close()
        self.total += len(body)
        record.update(retrieved_at=now(), bytes=len(body), sha256=sha(body),
                      body_base64=base64.b64encode(body).decode())
        self.publish(f'request-{self.count:02d}.json', record)
        return (None if 'error' in record else body), record


def listing(body, prefix):
    root = ET.fromstring(body)
    ns = {'s': 'http://s3.amazonaws.com/doc/2006-03-01/'}
    if root.tag != '{http://s3.amazonaws.com/doc/2006-03-01/}ListBucketResult':
        raise ValueError('unexpected listing root')
    if root.findtext('s:Prefix', namespaces=ns) != prefix:
        raise ValueError('returned prefix differs')
    truncated = root.findtext('s:IsTruncated', namespaces=ns)
    if truncated not in {'true', 'false'}:
        raise ValueError('missing truncation state')
    objects = []
    for item in root.findall('s:Contents', ns):
        key = item.findtext('s:Key', namespaces=ns)
        size = int(item.findtext('s:Size', namespaces=ns))
        etag = item.findtext('s:ETag', namespaces=ns)
        if not key or not key.startswith(prefix) or size < 0 or not etag:
            raise ValueError('invalid object identity')
        objects.append({'key': key, 'size': size, 'etag': etag,
                        'last_modified': item.findtext('s:LastModified', namespaces=ns)})
    if len({x['key'] for x in objects}) != len(objects):
        raise ValueError('duplicate object keys')
    return {'objects': sorted(objects, key=lambda x: x['key']),
            'truncated': truncated == 'true', 'listed_bytes': sum(x['size'] for x in objects)}


def validate_range(record, body, start, end, obj):
    headers = record.get('response_headers', {})
    if body is None or record['status'] != 206:
        raise ValueError('range unavailable or ignored')
    if headers.get('content-range') != f'bytes {start}-{end}/{obj["size"]}':
        raise ValueError('incorrect Content-Range')
    if headers.get('etag') != obj['etag'] or len(body) != end - start + 1:
        raise ValueError('object identity/length changed')


def footer_metadata(tail, footer, size):
    import pyarrow.parquet as pq
    if len(tail) != 8 or tail[4:] != b'PAR1':
        raise ValueError('not an ordinary Parquet footer')
    footer_size = struct.unpack('<I', tail[:4])[0]
    if footer_size <= 0 or footer_size + 12 > size:
        raise ValueError('invalid footer size')
    if len(footer) != footer_size + 8 or footer[-8:] != tail:
        raise ValueError('footer does not match tail')
    # Metadata-only container; data offsets are deliberately not dereferenced.
    meta = pq.read_metadata(io.BytesIO(b'PAR1' + footer))
    return {'rows': meta.num_rows, 'row_groups': meta.num_row_groups,
            'schema': {f.name: str(f.type) for f in meta.schema.to_arrow_schema()},
            'uncompressed_bytes': sum(meta.row_group(i).total_byte_size for i in range(meta.num_row_groups)),
            'created_by': meta.created_by}


def inspect_object(capture, obj, table):
    spec = capture.spec
    if obj['size'] < 12:
        raise ValueError('object too small')
    url = spec['base_url'] + urllib.parse.quote(obj['key'], safe='/=')
    end = obj['size'] - 1
    tail, r = capture.get(url, {'Range': f'bytes={end-7}-{end}', 'If-Match': obj['etag']})
    validate_range(r, tail, end-7, end, obj)
    if tail[4:] != b'PAR1':
        raise ValueError('unsupported Parquet magic')
    length = struct.unpack('<I', tail[:4])[0]
    if not 0 < length <= spec['max_footer_bytes'] or length + 12 > obj['size']:
        raise ValueError('footer exceeds bound or invalid')
    start = obj['size'] - length - 8
    footer, r = capture.get(url, {'Range': f'bytes={start}-{end}', 'If-Match': obj['etag']})
    validate_range(r, footer, start, end, obj)
    meta = footer_metadata(tail, footer, obj['size'])
    required = {'number', 'hash', 'parent_hash', 'timestamp', 'transaction_count'} if table == 'blocks' else {
        'hash', 'block_hash', 'block_number', 'block_timestamp', 'transaction_index',
        'from_address', 'to_address', 'value', 'receipt_status'}
    meta['missing_columns'] = sorted(required - meta['schema'].keys())
    meta['exact_wei_supported'] = None if table == 'blocks' else meta['schema'].get('value') in {
        'string', 'large_string', 'decimal256(76, 0)', 'decimal128(38, 0)'}
    result = {'object': obj, 'metadata': meta, 'sample': {'status': 'unavailable'}}
    if meta['missing_columns']:
        result['sample']['reason'] = 'required columns missing'
    elif (obj['size'] > spec['max_sample_bytes'] or meta['rows'] > spec['max_sample_rows']
          or meta['uncompressed_bytes'] > spec['max_uncompressed_bytes']):
        result['sample']['reason'] = 'complete object exceeds frozen compressed/row/uncompressed sample bound'
    else:
        body, receipt = capture.get(url, {'If-Match': obj['etag']})
        if body is None or receipt.get('status') != 200 or len(body) != obj['size'] or receipt.get('response_headers', {}).get('etag') != obj['etag']:
            result['sample']['reason'] = 'complete object unavailable or identity mismatch'
        else:
            import pyarrow.parquet as pq
            frame = pq.read_table(io.BytesIO(body), columns=sorted(required), use_threads=False)
            if frame.num_rows != meta['rows']:
                raise ValueError('sample/footer row count differs')
            result['sample'] = {'status': 'complete', 'rows': frame.num_rows,
                'null_counts': {n: frame[n].null_count for n in frame.column_names},
                'body_sha256': sha(body), 'request_number': receipt['request_number'],
                'qualification': 'one object only; no day/chain completeness or canonicality admission'}
    return result


def execute(spec, publish):
    capture = Capture(spec, publish)
    cells, inventories, inspected = [], {}, {}
    for day in spec['dates']:
        for table in spec['tables']:
            cell_id = f'{table}-{day}'
            prefix = f'v1.0/eth/{table}/date={day}/'
            url = spec['base_url'] + '?' + urllib.parse.urlencode({
                'list-type': '2', 'prefix': prefix, 'max-keys': spec['max_keys']})
            try:
                body, receipt = capture.get(url)
                if body is None:
                    raise ValueError(receipt['error'])
                inv = listing(body, prefix)
                inventories[cell_id] = inv
                if inv['truncated'] or not inv['objects']:
                    raise ValueError('listing truncated or empty')
                cells.append({'id': cell_id, 'status': 'complete'})
            except Exception as exc:
                cells.append({'id': cell_id, 'status': 'unavailable', 'reason': str(exc)})
    for table in spec['tables']:
        cell_id = f'{table}-primary-schema'
        inv = inventories.get(f'{table}-{spec["primary_date"]}', {})
        candidates = [x for x in inv.get('objects', []) if x['size'] and x['key'].endswith('.parquet')]
        try:
            if not candidates or inv.get('truncated'):
                raise ValueError('complete primary listing unavailable')
            inspected[table] = inspect_object(capture, candidates[0], table)
            if inspected[table]['metadata']['missing_columns']:
                raise ValueError('required schema fields missing')
            cells.append({'id': cell_id, 'status': 'complete'})
        except Exception as exc:
            cells.append({'id': cell_id, 'status': 'unavailable', 'reason': str(exc)})
    for number in range(capture.count + 1, spec['max_requests'] + 1):
        publish(f'request-{number:02d}-intent.json', {'status': 'not_attempted',
            'reason': 'prerequisite, source denial or fixed resource condition prevented request'})
        publish(f'request-{number:02d}.json', {'status': 'not_attempted',
            'reason': 'prerequisite, source denial or fixed resource condition prevented request'})
    result = {'cells': cells, 'inventories': inventories, 'inspected': inspected,
              'requests': capture.count, 'raw_response_bytes': capture.total,
              'historical_publication_admitted': False, 'full_history_admitted': False,
              'financial_evaluation_admitted': False, 'acquired_at': now()}
    publish('source-audit.json', result)
    return cells


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=Path(args.root),
            registration='research/onchain-graph-2026-09-16/gates-source-v2.json',
            experiment='eth-graph-source-20260916', source=args.source) as run:
        spec = json.loads(run.read_input('request_spec'))
        cells = execute(spec, run.write_json)
        run.finish(cells)


if __name__ == '__main__':
    main()
