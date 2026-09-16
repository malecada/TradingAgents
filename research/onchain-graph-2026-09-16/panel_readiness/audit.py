"""Frozen metadata-only multi-year archive inventory; never read data columns."""
import argparse
import base64
from datetime import date, timedelta
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import struct
import urllib.parse

import pyarrow.parquet as pq
from tradingagents.research import ResearchRun

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENT = 'eth-panel-readiness-20260916'
REGISTRATION = 'research/onchain-graph-2026-09-16/panel_readiness/gates.json'
module_spec = importlib.util.spec_from_file_location('retained_archive_transport', HERE.parent/'source_probe.py')
transport = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(transport)
COLUMNS = {
    'blocks': ['number', 'hash', 'parent_hash', 'timestamp', 'transaction_count'],
    'transactions': ['hash', 'block_hash', 'block_number', 'block_timestamp',
                     'transaction_index', 'from_address', 'to_address', 'value', 'receipt_status']}


def dates(year):
    current = date(year, 1, 1)
    while current.year == year:
        yield current.isoformat()
        current += timedelta(days=1)


def inventory(body, table, year):
    prefix = f'v1.0/eth/{table}/date={year}-'
    parsed = transport.listing(body, prefix)
    grouped = {day: [] for day in dates(year)}
    unexpected = []
    for obj in parsed['objects']:
        match = re.fullmatch(re.escape(prefix) + r'(\d{2}-\d{2})/[^/]+\.parquet', obj['key'])
        day = f'{year}-{match[1]}' if match else None
        if day not in grouped:
            unexpected.append(obj)
        else:
            grouped[day].append(obj)
    rows = []
    for day, objects in grouped.items():
        reason = ('truncated annual listing' if parsed['truncated'] else
                  'unexpected object path in annual listing' if unexpected else
                  'missing object' if not objects else
                  'multiple objects: unsupported partition layout' if len(objects) != 1 else
                  'empty or invalid Parquet object size' if objects[0]['size'] < 12 else None)
        rows.append({'date': day, 'table': table, 'status': 'unavailable' if reason else 'complete',
                     'reason': reason, 'objects': objects})
    return {'table': table, 'year': year, 'truncated': parsed['truncated'],
            'unexpected_objects': unexpected, 'listed_objects': len(parsed['objects']),
            'listed_bytes': parsed['listed_bytes'], 'dates': rows}


def receipt_body(record):
    raw = base64.b64decode(record['body_base64'], validate=True)
    if len(raw) != record['bytes'] or hashlib.sha256(raw).hexdigest() != record['sha256']:
        raise ValueError('retained receipt bytes differ')
    return raw


def projected_metadata(tail, footer, obj, table):
    metadata = transport.footer_metadata(tail, footer, obj['size'])
    meta = pq.read_metadata(io.BytesIO(b'PAR1' + footer))
    required = COLUMNS[table]
    missing = sorted(set(required) - metadata['schema'].keys())
    spans, group_sizes = [], []
    for i in range(meta.num_row_groups):
        group = meta.row_group(i); selected = 0
        for j in range(group.num_columns):
            column = group.column(j)
            if column.path_in_schema not in required:
                continue
            positions = [n for n in (column.dictionary_page_offset, column.data_page_offset) if n is not None and n >= 4]
            if not positions or column.total_compressed_size <= 0:
                raise ValueError('invalid projected column offsets')
            start = min(positions); end = start + column.total_compressed_size
            if end > obj['size'] - len(footer):
                raise ValueError('projected column overlaps footer')
            spans.append((start, end)); selected += column.total_compressed_size
        group_sizes.append(selected)
    ordered = sorted(spans)
    if any(left[1] > right[0] for left, right in zip(ordered, ordered[1:])):
        raise ValueError('overlapping projected columns')
    return {**metadata, 'missing_columns': missing, 'projected_compressed_bytes': sum(group_sizes),
            'max_projected_row_group_bytes': max(group_sizes, default=0),
            'projected_range_count': len(spans), 'required_columns': required,
            'qualification': 'Footer-reported sizes and schema only; no column rows decoded.'}


def inspect(capture, obj, table, day, retained):
    url = capture.spec['base_url'] + urllib.parse.quote(obj['key'], safe='/=')
    end = obj['size']-1
    if day == '2024-01-01':
        tail_receipt, footer_receipt = retained[table]
        if any(r['url'] != url or r['request_headers'].get('If-Match') != obj['etag'] for r in retained[table]):
            raise ValueError('retained Jan1 object identity changed; no substitute acquisition')
        tail = receipt_body(tail_receipt); footer = receipt_body(footer_receipt)
        transport.validate_range(tail_receipt, tail, end-7, end, obj)
        transport.validate_range(footer_receipt, footer, obj['size']-len(footer), end, obj)
        acquisition = 'reused exact prior receipts; no new request'
    else:
        tail, record = capture.get(url, {'Range': f'bytes={end-7}-{end}', 'If-Match': obj['etag']})
        transport.validate_range(record, tail, end-7, end, obj)
        if tail[4:] != b'PAR1':
            raise ValueError('unsupported Parquet magic')
        length = struct.unpack('<I', tail[:4])[0]
        if not 0 < length <= capture.spec['max_footer_bytes'] or length + 12 > obj['size']:
            raise ValueError('invalid or excessive footer size')
        start = obj['size']-length-8
        footer, record = capture.get(url, {'Range': f'bytes={start}-{end}', 'If-Match': obj['etag']})
        transport.validate_range(record, footer, start, end, obj)
        acquisition = 'two bounded conditional range reads'
    return {'date': day, 'table': table, 'object': obj, 'acquisition': acquisition,
            'footer_sha256': hashlib.sha256(footer).hexdigest(),
            'metadata': projected_metadata(tail, footer, obj, table)}


def execute(spec, retained, publish):
    capture = transport.Capture(spec, publish)
    inventories, samples, cells = [], [], []
    for year in spec['years']:
        for table in spec['tables']:
            cell_id = f'inventory-{table}-{year}'
            prefix = f'v1.0/eth/{table}/date={year}-'
            try:
                body, record = capture.get(spec['base_url']+'?'+urllib.parse.urlencode({
                    'list-type': '2', 'prefix': prefix, 'max-keys': spec['max_keys']}))
                if body is None:
                    raise ValueError(record.get('error', 'request unavailable'))
                item = inventory(body, table, year)
                inventories.append(item)
                absent = sum(r['status'] != 'complete' for r in item['dates'])
                if absent:
                    raise ValueError(f'{absent} dates unavailable in current object inventory')
                cells.append({'id': cell_id, 'status': 'complete'})
            except Exception as exc:
                if not any(i['year'] == year and i['table'] == table for i in inventories):
                    inventories.append({'year': year, 'table': table, 'error': str(exc),
                        'dates': [{'date': d, 'table': table, 'status': 'unavailable',
                                   'reason': str(exc), 'objects': []} for d in dates(year)]})
                cells.append({'id': cell_id, 'status': 'unavailable', 'reason': str(exc)})
    by_date = {(r['table'],r['date']):r for item in inventories for r in item['dates']}
    for day in spec['sample_dates']:
        for table in spec['tables']:
            cell_id = f'schema-{table}-{day}'
            try:
                row = by_date[table,day]
                if row['status'] != 'complete':
                    raise ValueError(row['reason'])
                sample = inspect(capture, row['objects'][0], table, day, retained)
                samples.append(sample)
                drift = {name:sample['metadata']['schema'].get(name) for name,kind in spec['required_types'][table].items()
                         if sample['metadata']['schema'].get(name) != kind}
                if sample['metadata']['missing_columns'] or drift or sample['metadata']['rows'] <= 0:
                    sample.update(status='unavailable',reason='missing columns, type drift or empty object',type_drift=drift)
                    raise ValueError(sample['reason'])
                sample['status'] = 'complete'
                cells.append({'id': cell_id, 'status': 'complete'})
            except Exception as exc:
                if not any(s['date']==day and s['table']==table for s in samples):
                    samples.append({'date':day,'table':table,'status':'unavailable','reason':str(exc)})
                cells.append({'id':cell_id,'status':'unavailable','reason':str(exc)})
    for number in range(capture.count+1,spec['max_requests']+1):
        for suffix in ('-intent',''):
            publish(f'request-{number:02d}{suffix}.json', {'status':'not_attempted',
                'reason':'fixed request sequence ended, reuse or prerequisite unavailable; no substitutions'})
    publish('inventory.json', {'expected_date_table_cells':2192,'inventories':inventories,
        'current_inventory_only':True,'chain_completeness_verified':False})
    publish('schemas.json', {'expected_samples':24,'samples':samples,'all_day_schema_verified':False})
    publish('summary.json', {'requests':capture.count,'response_bytes':capture.total,
        'expected_date_table_cells':2192,'complete_date_table_cells':sum(r['status']=='complete' for r in by_date.values()),
        'expected_schema_cells':24,'complete_schema_cells':sum(r['status']=='complete' for r in samples),
        'first_day_prior_overlap_audited':False,'historical_publication_verified':False,
        'transaction_rows_decoded':0,'financial_outcomes_opened':False,
        'cells':cells,'qualification':'Inventory and sampled footer readiness only; no full panel admitted.'})
    return cells


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
    with ResearchRun.start(root=ROOT,registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        spec=json.loads(run.read_input('plan'))
        retained={table:[json.loads(run.read_input(f'{table}-{part}')) for part in ['tail','footer']]
                  for table in spec['tables']}
        run.finish(execute(spec,retained,run.write_json))


if __name__=='__main__': main()
