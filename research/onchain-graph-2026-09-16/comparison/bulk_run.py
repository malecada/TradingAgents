"""Finite remaining-cohort raw capture; one immutable checkpoint per date."""
import argparse
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path

from tradingagents.research import ResearchRun
from bulk_graph import Budget, capture_day
from check_bulk import check_day
from graph_capture import storage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENT = 'eth-remaining-graph-capture-20260916'
REGISTRATION = 'research/onchain-graph-2026-09-16/comparison/bulk-gates.json'


def dates():
    reused = {f'2022-01-{d:02d}' for d in range(1, 8)} | {f'2024-01-{d:02d}' for d in range(1, 6)}
    day, stop = date(2022, 1, 1), date(2025, 1, 1)
    result = []
    while day < stop:
        if day.isoformat() not in reused:
            result.append(day.isoformat())
        day += timedelta(days=1)
    return result


def bounded(value, maximum):
    if len((json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()) > maximum:
        raise ValueError('lifecycle output exceeds dedicated metadata reserve')
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=ROOT, registration=REGISTRATION,
                           experiment=EXPERIMENT, source=args.source) as run:
        plan = json.loads(run.read_input('source_plan'))
        inventory = json.loads(run.read_input('inventory'))
        cohort = json.loads(run.read_input('cohort'))
        reuse = json.loads(run.read_input('reuse'))
        run.read_input('history')
        if cohort['dates'] != dates() or len(cohort['dates']) != 1084:
            raise ValueError('remaining acquisition calendar differs')
        block_receipt_raw = run.read_input('jan9_block_receipt')
        block_receipt = json.loads(block_receipt_raw)
        block_path = ROOT/reuse['jan9_blocks']['blob_path']
        if hashlib.sha256(run.read_input('jan9_block_blob')).hexdigest() != block_receipt['blob']['stored_sha256']:
            raise ValueError('reused block blob binding differs')
        block_body = storage.read_blob(block_path, block_receipt['blob'])
        reused_block = dict(body=block_body, receipt=block_receipt,
                            provenance={k: reuse['jan9_blocks'][k] for k in
                                ('receipt_path', 'receipt_sha256', 'blob_path', 'stored_sha256')})
        directory = HERE/'bulk-artifacts'
        directory.mkdir(exist_ok=False)
        # 128 MiB prior metadata plus 128 MiB dedicated lifecycle/log reserve.
        budget = Budget(existing_raw_bytes=2*1024**3,
                        existing_metadata_bytes=256*1024**2)
        cells, rows = [], []
        for current in cohort['dates']:
            result = capture_day(current, directory/current, inventory, plan, budget,
                                 reused_blocks=reused_block if current == '2024-01-09' else None)
            try:
                checked = check_day(ROOT, current, result)
                result = dict(result, independent_check=checked)
            except Exception as exc:
                result = dict(date=current, status='unavailable', capture=result,
                              reason='independent raw check: '+str(exc)[:4096],
                              independent_check=dict(status='failed', error_type=type(exc).__name__))
            ident = 'graph-'+current
            run.write_json(ident+'.json', bounded(result, 16*1024))
            cells.append(dict(id=ident, status=result['status'], **(
                {'reason':result['reason']} if result['status'] != 'complete' else {})))
            rows.append(result)
            print(json.dumps(dict(phase='remaining_graph_capture', **result)), flush=True)
        index = dict(source=args.source, days=rows, reused_source_manifest_sha256=
                     hashlib.sha256((HERE/'bulk-reuse.json').read_bytes()).hexdigest(),
                     raw_only=True, numerical_integrity_admitted=False)
        run.write_json('index.json', bounded(index, 32*1024**2))
        cells.append(dict(id='index', status='complete'))
        run.write_json('summary.json', bounded(dict(cells=cells,
            complete_days=sum(r['status']=='complete' for r in rows), scheduled_days=len(rows),
            raw_only=True, numerical_integrity_admitted=False,
            external_raw_backup_verified=False, automatic_restart=False), 1024**2))
        run.finish(cells)


if __name__ == '__main__':
    main()
