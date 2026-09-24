"""Once-only registered comparison or independent review under the kernel guard."""
import argparse
import json
from pathlib import Path
import sys

from admission import BASE,EXPERIMENT,admit_execution,guard_module

ROOT=Path(__file__).resolve().parents[4]


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--review',action='store_true');a=p.parse_args()
    admit_execution(ROOT,a.source,review=a.review,require_guard=False)
    ns=ROOT/BASE;phase='review' if a.review else 'compute'
    command=[sys.executable,'-B',str(ns/('check_final.py' if a.review else 'run.py'))]
    if a.review:
        run=ROOT/'research_runs'/EXPERIMENT
        if sum((run/name).exists() for name in ['complete.json','failed.json'])!=1:
            raise ValueError('unique comparison terminal required')
        if not (ns/'resources/compute/final.json').is_file():raise ValueError('compute guard terminal required')
        command+=['--root',str(ROOT)]
    command+=['--source',a.source]
    if a.review:command+=['--report',str(ns/'independent-report.json')]
    result=guard_module(ROOT).guarded_run(command,cwd=ROOT,receipt_dir=ns/'resources'/phase,
        memory_max_bytes=6*2**30,memory_high_bytes=6*2**30,memory_swap_max_bytes=2**29,
        reserve_bytes=3*2**30,start_reserve_bytes=9*2**30)
    print(json.dumps(result),flush=True)
    return int(result['phase']!='complete')


if __name__=='__main__':raise SystemExit(main())
