"""Independent per-date raw check, using the previously reviewed archive checker.

No acquisition, graph event decoding or price parsing occurs. This module does
not import bulk_graph, storage, numerical projection or the capture runner.
"""
import argparse
import json
from pathlib import Path

from check_capture import blob, check_graph, digest, inside, load, receipts, require

PREFIX = 'research/onchain-graph-2026-09-16/comparison'


def check_day(root, date, cell):
    root = Path(root).resolve()
    own = root/PREFIX
    directory = own/'bulk-artifacts'/date
    require(date in load(own/'bulk-cohort.json')['dates'], 'date not in frozen cohort')
    require(cell['date'] == date, 'cell date binding')
    require(cell['manifest_sha256'] is not None, 'day manifest absent')
    manifest_path = directory/'manifest.json'
    require(digest(manifest_path.read_bytes()) == cell['manifest_sha256'], 'day manifest hash')
    manifest = load(manifest_path)
    paths = [inside(directory, f['path']) for f in manifest['files']]
    require(len(paths) == len(set(paths)), 'manifest duplicate paths')
    require(set(paths) | {manifest_path.resolve()} == {p.resolve() for p in directory.iterdir()}, 'manifest file denominator')
    for path, entry in zip(paths, manifest['files']):
        require(path.is_file() and not path.is_symlink(), 'non-regular source member')
        require(path.stat().st_size == entry['bytes'] and digest(path.read_bytes()) == entry['sha256'], 'manifest member hash/size')
    for key, value in manifest['result'].items():
        require(cell[key] == value, 'manifest/result binding: '+key)
    records = receipts(directory)
    require(len(records) == cell['requests'] <= 291, 'request denominator')
    received = sum(r['bytes'] for r, _ in records)
    require(received == cell['received_bytes'] <= 272*1024**2, 'received byte denominator')
    if cell['status'] == 'complete':
        if date == '2024-01-09':
            reference = load(own/'bulk-reuse.json')['jan9_blocks']
            receipt_path = inside(root, reference['receipt_path'])
            require(digest(receipt_path.read_bytes()) == reference['receipt_sha256'], 'reused block receipt hash')
            record = load(receipt_path)
            path, raw = blob(receipt_path, record)
            require(path == inside(root, reference['blob_path']), 'reused block path')
            require(record['blob']['stored_sha256'] == reference['stored_sha256'], 'reused stored hash')
            require(digest(raw) == reference['raw_sha256'], 'reused raw hash')
            records.insert(0, (record, raw))
        check_graph(date, cell, records, directory,
                    load(root/'research_runs/eth-panel-readiness-20260916/outputs/inventory.json'),
                    load(own/'capture-plan.json'))
    return dict(status='verified', source_status=cell['status'], date=date,
                received_bytes=received, files=len(paths)+1,
                graph_rows_decoded=False, price_fields_parsed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--date', required=True)
    args = parser.parse_args()
    cell = load(args.root/'research_runs/eth-remaining-graph-capture-20260916/outputs'/('graph-'+args.date+'.json'))
    # A checker failure is preserved separately in the lifecycle cell; never
    # change original acquisition fields merely to make a recheck succeed.
    print(json.dumps(check_day(args.root, args.date, cell.get('capture', cell)), sort_keys=True))
