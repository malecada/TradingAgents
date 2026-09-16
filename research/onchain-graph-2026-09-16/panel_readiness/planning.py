"""Read terminal metadata only; estimate storage without claiming panel admission."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import shutil


def summarize(inventory, schemas):
    exact = []
    for annual in inventory['inventories']:
        rows = annual['dates']
        exact.append({'year':annual['year'],'table':annual['table'],
            'expected_dates':len(rows),'usable_inventory_dates':sum(r['status']=='complete' for r in rows),
            'listed_full_object_bytes':annual.get('listed_bytes'),
            'inventory_complete':all(r['status']=='complete' for r in rows)})
    quarters = []
    for sample in schemas['samples']:
        day=date.fromisoformat(sample['date'])
        next_quarter=date(day.year+1,1,1) if day.month==10 else date(day.year,day.month+3,1)
        days=(next_quarter-day).days
        size=sample.get('metadata',{}).get('projected_compressed_bytes') if sample['status']=='complete' else None
        quarters.append({'date':sample['date'],'table':sample['table'],'quarter_days':days,
            'sample_projected_bytes':size,'extrapolated_quarter_projected_bytes':None if size is None else size*days})
    complete=len(quarters)==24 and all(q['sample_projected_bytes'] is not None for q in quarters)
    estimate=sum(q['extrapolated_quarter_projected_bytes'] for q in quarters) if complete else None
    return {'exact_listed_full_objects':exact,'quarter_start_extrapolation':quarters,
        'estimated_three_year_projected_bytes':estimate,
        'estimated_base64_receipt_payload_bytes':None if estimate is None else (estimate+2)//3*4,
        'qualification':'Quarter-start daily compressed column sizes multiplied by days in each calendar quarter. Not measured all-day projection cost, a confidence bound, or a RAM/runtime forecast. Base64 estimate excludes JSON, footers, outputs, Git and additional worktrees. Listed full-object bytes are a different, directly observed metadata quantity.',
        'full_panel_admitted':False,'historical_publication_verified':False}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--report',required=True)
    args=parser.parse_args();root=Path(args.root).resolve();run=root/'research_runs/eth-panel-readiness-20260916'
    assert (run/'complete.json').exists() and not (run/'failed.json').exists()
    sources=[run/'outputs'/name for name in ['inventory.json','schemas.json']]
    result=summarize(*(json.loads(p.read_bytes()) for p in sources))
    result['input_sha256']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    result['planning_script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    usage=shutil.disk_usage(root)
    result['local_disk_snapshot']={'root':str(root),'total_bytes':usage.total,'free_bytes':usage.free,
        'qualification':'Current filesystem observation; no deletion, reservation or external storage availability assumed.'}
    with Path(args.report).open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['quarter_start_extrapolation','input_sha256']},indent=2))


if __name__=='__main__':main()
