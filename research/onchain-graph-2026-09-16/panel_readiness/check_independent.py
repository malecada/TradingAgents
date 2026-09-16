"""Offline independent XML/footer reconciliation; never decode data columns."""
import argparse
import base64
import calendar
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET

import pyarrow.parquet as pq
from tradingagents.research.verify import verify_run, verify_claim


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def body(receipt):
    raw = base64.b64decode(receipt['body_base64'], validate=True)
    assert len(raw) == receipt['bytes'] and sha(raw) == receipt['sha256']
    return raw


def utc(value):
    parsed = datetime.fromisoformat(value)
    assert parsed.utcoffset() == timedelta(0)
    return parsed


def year_days(year):
    return [(date(year, 1, 1) + timedelta(days=i)).isoformat()
            for i in range(366 if calendar.isleap(year) else 365)]


def parse_inventory(raw, table, year):
    root = ET.fromstring(raw)
    tag = '{http://s3.amazonaws.com/doc/2006-03-01/}'
    prefix = f'v1.0/eth/{table}/date={year}-'
    if (root.tag != tag + 'ListBucketResult' or root.findtext(tag + 'Prefix') != prefix
            or root.findtext(tag + 'IsTruncated') not in ('true', 'false')):
        raise ValueError('invalid listing identity/truncation')
    objects = []
    for item in root.findall(tag + 'Contents'):
        key, size, etag = item.findtext(tag+'Key'), int(item.findtext(tag+'Size')), item.findtext(tag+'ETag')
        if not key or not key.startswith(prefix) or size < 0 or not etag:
            raise ValueError('invalid object identity')
        objects.append({'key': key, 'size': size, 'etag': etag,
                        'last_modified': item.findtext(tag+'LastModified')})
    if len({o['key'] for o in objects}) != len(objects):
        raise ValueError('duplicate keys')
    objects.sort(key=lambda o: o['key'])
    grouped = {day: [] for day in year_days(year)}
    unexpected = []
    for obj in objects:
        match = re.fullmatch(re.escape(prefix) + r'(\d{2}-\d{2})/[^/]+\.parquet', obj['key'])
        day = f'{year}-{match[1]}' if match else None
        (grouped[day] if day in grouped else unexpected).append(obj)
    truncated = root.findtext(tag+'IsTruncated') == 'true'
    rows = {day: {'objects': items, 'status': 'complete' if (
        not truncated and not unexpected and len(items) == 1 and items[0]['size'] >= 12)
        else 'unavailable'} for day, items in grouped.items()}
    return {'objects': objects, 'rows': rows, 'truncated': truncated,
            'unexpected_objects': unexpected, 'listed_bytes': sum(o['size'] for o in objects)}


def validate_range(receipt, raw, start, end, obj):
    headers = receipt.get('response_headers', {})
    if (raw is None or receipt.get('status') != 206
            or headers.get('content-range') != f'bytes {start}-{end}/{obj["size"]}'
            or headers.get('etag') != obj['etag'] or len(raw) != end-start+1):
        raise ValueError('conditional range unavailable or inconsistent')


def parse_footer(tail, footer, obj, columns):
    if len(tail) != 8 or tail[4:] != b'PAR1':
        raise ValueError('footer magic')
    length = struct.unpack('<I', tail[:4])[0]
    if not 0 < length or length+12 > obj['size'] or len(footer) != length+8 or footer[-8:] != tail:
        raise ValueError('footer length/tail')
    meta = pq.read_metadata(io.BytesIO(b'PAR1' + footer))
    schema = {field.name: str(field.type) for field in meta.schema.to_arrow_schema()}
    spans, groups = [], []
    for i in range(meta.num_row_groups):
        rg = meta.row_group(i)
        size = 0
        for j in range(rg.num_columns):
            col = rg.column(j)
            if col.path_in_schema not in columns:
                continue
            offsets = [x for x in (col.dictionary_page_offset, col.data_page_offset) if x is not None and x >= 4]
            if not offsets or col.total_compressed_size <= 0:
                raise ValueError('column offset/size')
            start = min(offsets); end = start + col.total_compressed_size
            if end > obj['size'] - len(footer):
                raise ValueError('column overlaps footer')
            spans.append((start, end)); size += col.total_compressed_size
        groups.append(size)
    spans.sort()
    if any(a[1] > b[0] for a, b in zip(spans, spans[1:])):
        raise ValueError('columns overlap')
    return {'rows': meta.num_rows, 'row_groups': meta.num_row_groups, 'schema': schema,
            'uncompressed_bytes': sum(meta.row_group(i).total_byte_size for i in range(meta.num_row_groups)),
            'created_by': meta.created_by, 'missing_columns': sorted(set(columns)-set(schema)),
            'projected_compressed_bytes': sum(groups), 'max_projected_row_group_bytes': max(groups, default=0),
            'projected_range_count': len(spans), 'required_columns': list(columns)}


class Receipts:
    def __init__(self, output, plan, started, ended):
        self.output, self.plan, self.started, self.ended = output, plan, started, ended
        self.count = self.total = 0
        self.denied = False
        self.statuses = {}

    def take(self, url, headers=None):
        if self.denied or self.count >= self.plan['max_requests']:
            return None, {}
        self.count += 1
        headers = headers or {}
        intent = self.output(f'request-{self.count:02d}-intent.json')
        receipt = self.output(f'request-{self.count:02d}.json')
        assert intent['status'] == 'intent' and intent['method'] == 'GET'
        for record in (intent, receipt):
            assert record['url'] == url and record['request_headers'] == headers
            assert record['request_number'] == self.count
        assert intent['requested_at'] == receipt['requested_at']
        assert self.started <= utc(receipt['requested_at']) <= utc(receipt['retrieved_at']) <= self.ended
        raw = body(receipt)
        cap = min(self.plan['max_response_bytes'], self.plan['max_total_bytes']-self.total)
        assert len(raw) <= max(cap, 0)+1
        self.total += len(raw)
        status = receipt['status']; self.statuses[str(status)] = self.statuses.get(str(status), 0)+1
        if status in (401, 403, 429):
            self.denied = True
        if 'error' not in receipt:
            assert cap > 0 and len(raw) <= cap and status in (200, 206)
            length = receipt.get('response_headers', {}).get('content-length')
            assert length is None or int(length) == len(raw)
        return (None if 'error' in receipt else raw), receipt

    def finish(self):
        for i in range(self.count+1, self.plan['max_requests']+1):
            assert self.output(f'request-{i:02d}-intent.json')['status'] == 'not_attempted'
            assert self.output(f'request-{i:02d}.json')['status'] == 'not_attempted'
        assert self.total <= self.plan['max_total_bytes']+1


def reconcile(plan, retained, output, started, ended):
    receipts = Receipts(output, plan, started, ended)
    actual_inventory = output('inventory.json')
    actual_schemas = output('schemas.json')
    summary = output('summary.json')
    assert actual_inventory['expected_date_table_cells'] == 2192
    assert actual_inventory['current_inventory_only'] and not actual_inventory['chain_completeness_verified']
    assert actual_schemas['expected_samples'] == 24 and not actual_schemas['all_day_schema_verified']
    assert len(actual_inventory['inventories']) == 6 and len(actual_schemas['samples']) == 24
    by_date, cell_status, exact_listed_bytes = {}, {}, {'blocks': 0, 'transactions': 0}
    for index, (year, table) in enumerate((y,t) for y in plan['years'] for t in plan['tables']):
        prefix = f'v1.0/eth/{table}/date={year}-'
        url = plan['base_url']+'?'+urllib.parse.urlencode({'list-type':'2','prefix':prefix,'max-keys':1000})
        raw, _ = receipts.take(url)
        reported = actual_inventory['inventories'][index]
        assert (reported['year'], reported['table']) == (year, table)
        try:
            if raw is None:
                raise ValueError('response unavailable')
            parsed = parse_inventory(raw, table, year)
        except (ValueError, TypeError, ET.ParseError):
            parsed = None
            assert 'error' in reported
        if parsed:
            for name in ('truncated', 'unexpected_objects', 'listed_bytes'):
                assert reported[name] == parsed[name]
            assert reported['listed_objects'] == len(parsed['objects'])
            exact_listed_bytes[table] += parsed['listed_bytes']
        assert [r['date'] for r in reported['dates']] == year_days(year)
        complete = True
        for row in reported['dates']:
            assert row['table'] == table
            expected = parsed['rows'][row['date']] if parsed else {'objects': [], 'status':'unavailable'}
            assert row['objects'] == expected['objects'] and row['status'] == expected['status']
            if expected['status'] != 'complete':
                complete = False; assert row.get('reason')
            by_date[table,row['date']] = expected
        cell_status[f'inventory-{table}-{year}'] = 'complete' if complete else 'unavailable'
    estimates = {'blocks': 0, 'transactions': 0}
    quarter_evidence = []
    reused = 0
    for index, (day, table) in enumerate((d,t) for d in plan['sample_dates'] for t in plan['tables']):
        reported = actual_schemas['samples'][index]
        assert (reported['date'], reported['table']) == (day, table)
        row = by_date[table,day]
        meta, footer = None, None
        try:
            if row['status'] != 'complete':
                raise ValueError('inventory unavailable')
            obj, = row['objects']
            url = plan['base_url']+urllib.parse.quote(obj['key'],safe='/=')
            end = obj['size']-1
            if day == '2024-01-01':
                tr, fr = retained[table]
                if any(r['url'] != url or r['request_headers'].get('If-Match') != obj['etag'] for r in (tr,fr)):
                    raise ValueError('retained January identity differs')
                tail, footer = body(tr), body(fr)
                validate_range(tr,tail,end-7,end,obj)
                validate_range(fr,footer,obj['size']-len(footer),end,obj)
                reused += 2
            else:
                tail, tr = receipts.take(url,{'Range':f'bytes={end-7}-{end}','If-Match':obj['etag']})
                validate_range(tr,tail,end-7,end,obj)
                if tail[4:] != b'PAR1':
                    raise ValueError('footer magic')
                length = struct.unpack('<I',tail[:4])[0]
                if not 0 < length <= plan['max_footer_bytes'] or length+12 > obj['size']:
                    raise ValueError('footer bound')
                start = obj['size']-length-8
                footer, fr = receipts.take(url,{'Range':f'bytes={start}-{end}','If-Match':obj['etag']})
                validate_range(fr,footer,start,end,obj)
            meta = parse_footer(tail,footer,obj,plan['required_types'][table])
        except (ValueError, TypeError, KeyError, OSError):
            assert reported['status'] == 'unavailable' and reported.get('reason')
        if meta is not None:
            assert reported['object'] == obj and reported['footer_sha256'] == sha(footer)
            for name, value in meta.items():
                assert reported['metadata'][name] == value, (day,table,name)
            drift = {k:meta['schema'].get(k) for k,v in plan['required_types'][table].items() if meta['schema'].get(k) != v}
            status = 'unavailable' if meta['missing_columns'] or drift or meta['rows'] <= 0 else 'complete'
            assert reported['status'] == status
            if status == 'unavailable':
                assert reported['type_drift'] == drift
            else:
                d = date.fromisoformat(day)
                days = sum(calendar.monthrange(d.year,m)[1] for m in range(d.month,d.month+3))
                estimate = days*meta['projected_compressed_bytes']
                estimates[table] += estimate
                quarter_evidence.append({'date':day,'table':table,'calendar_quarter_days':days,
                    'sample_projected_compressed_bytes':meta['projected_compressed_bytes'],
                    'weighted_projected_byte_estimate':estimate,
                    'sample_rows':meta['rows'],'sample_row_groups':meta['row_groups'],
                    'sample_max_projected_row_group_bytes':meta['max_projected_row_group_bytes']})
        cell_status[f'schema-{table}-{day}'] = reported['status']
    receipts.finish()
    assert len(by_date) == 2192 and len(cell_status) == 30
    assert {c['id']:c['status'] for c in summary['cells']} == cell_status
    assert summary['requests'] == receipts.count and summary['response_bytes'] == receipts.total
    assert summary['expected_date_table_cells'] == 2192 and summary['expected_schema_cells'] == 24
    assert summary['complete_date_table_cells'] == sum(r['status']=='complete' for r in by_date.values())
    assert summary['complete_schema_cells'] == sum(r['status']=='complete' for r in actual_schemas['samples'])
    assert summary['transaction_rows_decoded'] == 0 and not summary['financial_outcomes_opened']
    assert not summary['first_day_prior_overlap_audited'] and not summary['historical_publication_verified']
    return {'requests':receipts.count,'response_bytes':receipts.total,'http_statuses':receipts.statuses,
        'reused_receipts':reused,'date_table_cells':2192,'complete_date_table_cells':summary['complete_date_table_cells'],
        'schema_cells':24,'complete_schema_cells':summary['complete_schema_cells'],'cell_status':cell_status,
        'listed_full_object_bytes_by_table':exact_listed_bytes,
        'listed_full_object_bytes_qualification':'Exact sum of objects in parsed current listings; incomplete listings do not imply full archive coverage.',
        'quarter_start_projection_evidence':quarter_evidence,
        'quarter_weighted_projected_bytes_by_table':estimates if len(quarter_evidence)==24 else None,
        'projection_qualification':'Extrapolation: each fixed quarter-start sample represents its calendar quarter, not measured daily transfers. No memory or runtime extrapolation.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',required=True); parser.add_argument('--report',required=True)
    args = parser.parse_args(); root = Path(args.root)
    here = root/'research/onchain-graph-2026-09-16/panel_readiness'
    run = root/'research_runs/eth-panel-readiness-20260916'
    assert len(os.sched_getaffinity(0)) <= 2
    # No response inspection before a unique successful terminal exists.
    assert (run/'complete.json').exists() and not (run/'failed.json').exists()
    load = lambda p: json.loads(p.read_bytes())
    structural = verify_run(run); claim = verify_claim(run); terminal = load(run/'complete.json')
    assert structural['status']=='complete' and structural['cell_count']==30 and structural['output_count']==111
    source = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    assert source == claim['source'] == terminal['source']
    assert claim['family']['prior_attempts']==4 and claim['family']['attempt_budget']==5
    exp = claim['experiment']; assert len(exp['inputs'])==16 and len(exp['source_files'])==17
    for name, digest in exp['source_files'].items():
        assert file_sha(root/name)==digest
    for name, digest in exp['runtime_hashes'].items():
        assert file_sha(root/'tradingagents/research'/name)==digest
    for item in claim['inputs'].values():
        assert file_sha(root/item['path'])==item['sha256']
    inputs = lambda name: load(root/claim['inputs'][name]['path'])
    history = inputs('history')
    assert history['local_claim_count']==41 and len(history['metadata_hashes'])==81
    for name,digest in history['metadata_hashes'].items():
        assert file_sha(root/name)==digest
    assert len(list((root/'research_runs').glob('*/claim.json')))==42
    resource = load(here/'resource.json')
    assert resource['source']==source and resource['child_exit_code']==0 and resource['limit_reason'] is None
    assert not resource['elapsed_time_kill'] and resource['rss_limit_bytes']==8*1024**3
    assert resource['peak_sampled_tree_rss_bytes'] <= resource['rss_limit_bytes']
    retained = {table:[inputs(f'{table}-{part}') for part in ('tail','footer')] for table in ('blocks','transactions')}
    output = lambda name: load(run/'outputs'/name)
    result = reconcile(inputs('plan'),retained,output,utc(claim['started_at']),utc(terminal['ended_at']))
    assert {c['id']:c['status'] for c in terminal['cells']}==result['cell_status']
    result.update(passed=True,source=source,reviewed_at=datetime.now(timezone.utc).isoformat(),
        structural_verification=structural,execution_resource=resource,
        reviewer_script_sha256=file_sha(Path(__file__)),claim_sha256=file_sha(run/'claim.json'),
        terminal_sha256=file_sha(run/'complete.json'),gate_sha256=file_sha(here/'gates.json'),
        retained_output_sha256={p.name:file_sha(p) for p in sorted((run/'outputs').iterdir())},
        new_network_requests=0,transaction_rows_decoded=0,financial_admission=False,
        historical_feature_panel_admitted=False,
        qualification='Independent raw XML/calendar/footer reconciliation only; sampled metadata and planning extrapolation, not all-day integrity, historical availability, canonicality, scalability or financial validation.')
    with Path(args.report).open('x') as stream:
        json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({k:result[k] for k in ('passed','requests','response_bytes','complete_date_table_cells','complete_schema_cells')}))


if __name__=='__main__':
    main()
