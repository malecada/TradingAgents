"""Read-only independent capture closure check; never parse prices or graph rows.

Uses standard archive readers directly, without capture/model/ResearchRun imports.
Prints one JSON report; does not write evidence, registrations or ledgers.
"""
import argparse
import calendar
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import urllib.parse
import zipfile

import pyarrow.parquet as pq
import zstandard


EXPERIMENT = 'eth-matched-input-capture-20260916'
PREFIX = 'research/onchain-graph-2026-09-16/comparison'
DAYS = [f'2022-01-{i:02d}' for i in range(1, 8)]
MONTHS = ['2021-12'] + [f'{y}-{m:02d}' for y in range(2022, 2025) for m in range(1, 13)] + ['2025-01']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def inside(root, relative):
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    return path


def blob(path, record):
    meta = record['blob']
    require(Path(meta['path']).name == meta['path'], 'blob path is not a basename')
    target = inside(path.parent, meta['path'])
    require(target.stat().st_size <= 65 * 1024**2, 'stored blob exceeds reader bound')
    stored = target.read_bytes()
    require(len(stored) == meta['stored_bytes'] and digest(stored) == meta['stored_sha256'], 'stored hash/size')
    require(type(meta['raw_bytes']) is int and 0 <= meta['raw_bytes'] <= 64 * 1024**2, 'raw size bound')
    require(zstandard.frame_content_size(stored) == meta['raw_bytes'], 'zstd declared size')
    raw = zstandard.ZstdDecompressor().decompress(stored, max_output_size=max(1, meta['raw_bytes']), allow_extra_data=False)
    require(len(raw) == record['bytes'] == meta['raw_bytes'], 'raw size binding')
    require(digest(raw) == record['sha256'] == meta['raw_sha256'], 'raw hash binding')
    return target, raw


def receipts(directory):
    records, bound = [], set()
    paths = sorted(p for p in directory.glob('request-*.json') if not p.name.endswith('-intent.json'))
    intents = sorted(directory.glob('request-*-intent.json'))
    require(len(paths) == len(intents), 'request intent denominator')
    for number, path in enumerate(paths, 1):
        require(path.name == f'request-{number:04d}.json', 'request sequence')
        record = load(path)
        intent = load(path.with_name(f'request-{number:04d}-intent.json'))
        require(record['request_number'] == number and intent['method'] == 'GET', 'request identity')
        for key in ('url', 'request_headers', 'requested_at', 'request_number'):
            require(record[key] == intent[key], 'intent differs from receipt')
        target, raw = blob(path, record)
        require(target not in bound, 'raw body reused by two requests')
        bound.add(target)
        records.append((record, raw if len(raw) <= 16 * 1024**2 else None))
    require(bound == {p.resolve() for p in directory.glob('*.zst')}, 'orphan/missing raw body')
    return records


def successful(record, url, obj=None, span=None):
    require(record['url'] == url and not record.get('error'), 'successful request URL/error')
    headers = record['response_headers']
    if obj is None:
        require(record['status'] == 200 and record['request_headers'] == {}, 'spot HTTP contract')
        return
    expected = {'If-Match': obj['etag']}
    require(headers.get('etag') == obj['etag'], 'object ETag changed')
    if span is None:
        require(record['status'] == 200 and record['bytes'] == obj['size'], 'full object status/size')
    else:
        start, end = span
        expected['Range'] = f'bytes={start}-{end}'
        require(record['status'] == 206 and record['bytes'] == end-start+1, 'range status/size')
        require(headers.get('content-range') == f'bytes {start}-{end}/{obj["size"]}', 'content-range')
    require(record['request_headers'] == expected, 'request conditional/range headers')


def check_spot(month, cell, records):
    require(len(records) == 2, 'complete spot pair denominator')
    name = f'ETHUSDT-1d-{month}.zip'
    url = 'https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1d/' + name
    successful(records[0][0], url)
    successful(records[1][0], url+'.CHECKSUM')
    raw, checksum = records[0][1], records[1][1]
    match = re.fullmatch(r'([0-9a-fA-F]{64})[ \t]+\*?'+re.escape(name)+r'[\r\n]*', checksum.decode('ascii'))
    require(match is not None and digest(raw) == match[1].lower(), 'archive checksum')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        require(len(members) == 1 and members[0].filename == name[:-4]+'.csv', 'CSV member identity')
        require(0 < members[0].file_size <= 1024**2 and not members[0].flag_bits & 1, 'CSV size/encryption')
        with archive.open(members[0]) as source:
            csv_raw = source.read(1024**2+1)
        require(len(csv_raw) == members[0].file_size <= 1024**2, 'CSV actual expansion')
    year, number = map(int, month.split('-'))
    unit = 10**6 if year >= 2025 else 1000
    beginning = int(datetime(year, number, 1, tzinfo=timezone.utc).timestamp()) * unit
    rows = list(csv.reader(io.StringIO(csv_raw.decode('utf-8')), strict=True))
    require(len(rows) == calendar.monthrange(year, number)[1] == cell['rows'], 'spot daily denominator')
    for day, row in enumerate(rows):
        require(len(row) == 12, 'spot field count')
        opening = beginning + day * 86400 * unit
        require(int(row[0]) == opening and int(row[6]) == opening+86400*unit-1, 'spot daily timestamps')
    require(digest(csv_raw) == cell['csv_sha256'], 'CSV manifest hash')


def check_graph(date, cell, records, directory, inventory, plan):
    def obj(table):
        matches = [r for group in inventory['inventories'] for r in group['dates'] if r['table'] == table and r['date'] == date]
        require(len(matches) == 1 and matches[0]['status'] == 'complete' and len(matches[0]['objects']) == 1, 'inventory denominator')
        return matches[0]['objects'][0]
    blocks, tx = obj('blocks'), obj('transactions')
    url = lambda o: plan['base_url']+urllib.parse.quote(o['key'], safe='/=')
    require(len(records) >= 3, 'graph initial requests')
    successful(records[0][0], url(blocks), blocks)
    schema = pq.read_metadata(io.BytesIO(records[0][1])).schema.to_arrow_schema()
    require(all(str(schema.field(k).type) == v for k, v in plan['block_required_types'].items()), 'block schema')
    successful(records[1][0], url(tx), tx, (tx['size']-8, tx['size']-1))
    tail = records[1][1]
    require(tail[4:] == b'PAR1', 'footer signature')
    length = struct.unpack('<I', tail[:4])[0]
    require(0 < length <= 4*1024**2, 'footer size bound')
    successful(records[2][0], url(tx), tx, (tx['size']-length-8, tx['size']-1))
    footer = records[2][1]
    require(footer[-8:] == tail, 'footer trailer equality')
    metadata = pq.read_metadata(io.BytesIO(b'PAR1'+footer))
    schema = metadata.schema.to_arrow_schema()
    require(all(str(schema.field(k).type) == v for k, v in plan['required_types'].items()), 'transaction schema')
    expected = []
    for group in range(metadata.num_row_groups):
        row_group = metadata.row_group(group)
        for column in range(row_group.num_columns):
            col = row_group.column(column)
            if col.path_in_schema not in plan['required_types']:
                continue
            require(not col.file_path, 'external column')
            offsets = [n for n in (col.dictionary_page_offset, col.data_page_offset) if n is not None and n >= 4]
            start = min(offsets)
            expected.append(dict(group=group, column=col.path_in_schema, start=start,
                                 end=start+col.total_compressed_size-1, bytes=col.total_compressed_size))
    projection = load(directory/'projection.json')
    require(projection['object'] == tx and projection['ranges'] == expected, 'projection/raw footer mismatch')
    require(0 < metadata.num_rows <= 2_000_000 and 0 < metadata.num_row_groups <= 32, 'graph row bounds')
    require(len(expected) == metadata.num_row_groups*9 and len(records) == len(expected)+3, 'graph range denominator')
    for (record, _), span in zip(records[3:], expected):
        successful(record, url(tx), tx, (span['start'], span['end']))
    require(cell['projected_rows'] == projection['rows'] == metadata.num_rows, 'projected row count')
    require(cell['selected_bytes'] == sum(s['bytes'] for s in expected) <= 256*1024**2, 'selected byte count')


def check(root):
    root = root.resolve()
    own = root/PREFIX
    gate = load(own/'capture-gates.json')['experiments'][EXPERIMENT]
    for spec in gate['inputs'].values():
        require(digest(inside(root, spec['path']).read_bytes()) == spec['sha256'], 'registered input hash')
    inventory = load(inside(root, gate['inputs']['inventory']['path']))
    plan = load(own/'capture-plan.json')
    outputs = root/'research_runs'/EXPERIMENT/'outputs'
    directory = own/'capture-artifacts'
    manifest = load(outputs/'manifest.json')
    files = manifest['files']
    paths = [inside(root, f['path']) for f in files]
    require(len(paths) == len(set(paths)), 'manifest duplicate members')
    require(set(paths) == {p.resolve() for p in directory.rglob('*') if p.is_file()}, 'manifest file denominator')
    for path, entry in zip(paths, files):
        require(path.stat().st_size == entry['bytes'] and digest(path.read_bytes()) == entry['sha256'], 'manifest hash/size')
    require(manifest['bytes'] == sum(f['bytes'] for f in files), 'manifest total bytes')
    summary = load(outputs/'summary.json')
    cells = summary['cells']
    require(len(cells) == 46 and {c['id'] for c in cells} == set(gate['cells']), 'lifecycle cell denominator')
    indexed = {c['id']: c for c in cells}
    spot_manifest = load(directory/'spot/manifest.json')
    raw_spot = receipts(directory/'spot')
    by_number = {r['request_number']: (r, raw) for r, raw in raw_spot}
    for month in MONTHS:
        cell = load(outputs/f'spot-{month}.json')
        require(cell == load(directory/f'spot/month-{month}.json'), 'spot cell differs from raw result')
        require(indexed['spot-'+month]['status'] == cell['status'], 'spot lifecycle status')
        records = [by_number[r['request_number']] for r in cell['receipts']]
        if cell['status'] == 'complete':
            check_spot(month, cell, records)
    require(sum(r['bytes'] for r, _ in raw_spot) == spot_manifest['raw_bytes'] <= 16*1024**2, 'spot byte ceiling')
    graph_bytes = 0
    for date in DAYS:
        cell = load(outputs/f'graph-{date}.json')
        folder = directory/'graph'/date
        require(cell == load(folder/'result.json'), 'graph cell differs from raw result')
        require(indexed['graph-'+date]['status'] == cell['status'], 'graph lifecycle status')
        records = receipts(folder)
        require(sum(r['bytes'] for r, _ in records) == cell['received_bytes'] <= 272*1024**2, 'graph byte ceiling')
        require(cell['requests'] <= 291, 'graph request ceiling')
        graph_bytes += cell['received_bytes']
        if cell['status'] == 'complete':
            check_graph(date, cell, records, folder, inventory, plan)
    require(summary['received_bytes'] == graph_bytes+spot_manifest['raw_bytes'], 'aggregate byte denominator')
    return dict(status='verified', cells=46, complete_cells=sum(c['status']=='complete' for c in cells),
                files=len(files), received_bytes=summary['received_bytes'], price_fields_parsed=False,
                graph_rows_decoded=False, qualification='Capture integrity only; no historical availability, graph numerical or predictive admission.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    print(json.dumps(check(parser.parse_args().root), sort_keys=True))
