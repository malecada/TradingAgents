"""Registered first input tranche; metadata-only source checks, never model fitting."""
import argparse
import json
from pathlib import Path

from tradingagents.research import ResearchRun
from graph_capture import capture_graph, DATES, day, storage
from spot_capture import capture_spot, MONTHS, registered_url

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENT = 'eth-matched-input-capture-20260916'
REGISTRATION = 'research/onchain-graph-2026-09-16/comparison/capture-gates.json'


def manifest(root, directory):
    bound = set()
    for intent in directory.rglob('request-*-intent.json'):
        if not intent.with_name(intent.name.replace('-intent.json', '.json')).is_file():
            raise ValueError('unresolved request intent')
    for receipt in directory.rglob('request-*.json'):
        if receipt.name.endswith('-intent.json'):
            continue
        value = json.loads(receipt.read_bytes())
        meta = value['blob']
        path = (receipt.parent/meta['path']).resolve()
        path.relative_to(directory.resolve())
        raw = storage.read_blob(path, meta)
        if len(raw) != value['bytes'] or storage.sha(raw) != value['sha256']:
            raise ValueError('receipt/raw binding differs')
        bound.add(path)
    if bound != {p.resolve() for p in directory.rglob('*.zst')}:
        raise ValueError('orphan or missing raw blob')
    return day.artifact_manifest(root, directory)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=ROOT, registration=REGISTRATION,
                           experiment=EXPERIMENT, source=args.source) as run:
        plan = json.loads(run.read_input('capture_plan'))
        inventory = json.loads(run.read_input('inventory'))
        run.read_input('history')
        spot_plan = json.loads(run.read_input('spot_plan'))
        if spot_plan['months'] != list(MONTHS) or spot_plan['urls'] != [
                registered_url(month, checksum) for month in MONTHS for checksum in (False, True)]:
            raise ValueError('spot acquisition plan differs from frozen source cohort')
        directory = HERE/'capture-artifacts'
        directory.mkdir(exist_ok=False)
        spot = capture_spot(directory/'spot')
        cells = []
        for row in spot['cells']:
            ident = 'spot-'+row['month']
            run.write_json(ident+'.json', row)
            cells.append(dict(id=ident, status=row['status'], **(
                {'reason':row['reason']} if row['status'] != 'complete' else {})))
        graph = capture_graph(directory/'graph', inventory, plan)
        for row in graph['days']:
            ident = 'graph-'+row['date']
            run.write_json(ident+'.json', row)
            cells.append(dict(id=ident, status=row['status'], **(
                {'reason':row['reason']} if row['status'] != 'complete' else {})))
        files = manifest(ROOT, directory)
        run.write_json('manifest.json', dict(files=files, bytes=sum(r['bytes'] for r in files)))
        cells.append(dict(id='manifest', status='complete'))
        run.write_json('summary.json', dict(cells=cells,
            spot_requests=spot['requests'], graph_requests=graph['requests'],
            received_bytes=spot['raw_bytes']+graph['received_bytes'],
            complete_spot_months=spot['complete_months'],
            complete_graph_days=sum(r['status']=='complete' for r in graph['days']),
            graph_numerical_integrity_admitted=False, price_fields_parsed=False,
            predictions_or_financial_outcomes=False))
        run.finish(cells)


if __name__ == '__main__':
    main()
