"""Finite continued extraction or independent check in isolated memory cgroup."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--review',action='store_true');args=p.parse_args()
    admission=module('resume_launch_admission',HERE/'admission.py')
    admission.admit_resume(ROOT,args.source,review=args.review)
    plan=json.loads((HERE/'plan.json').read_bytes());guard=module('resume_memory_guard',HERE/'memory_guard.py')
    phase='review' if args.review else 'compute';directory=HERE/'resources'/phase
    if args.review:
        run=ROOT/'research_runs'/admission.EXPERIMENT
        if sum((run/n).exists() for n in ('complete.json','failed.json'))!=1:raise ValueError('unique terminal required before review')
        if not (HERE/'resources/compute/final.json').exists():raise ValueError('compute guard must be terminal')
        command=[sys.executable,'-B',str(HERE/'check_final.py'),'--root',str(ROOT),'--source',args.source,'--report',str(HERE/'independent-report.json')]
    else:command=[sys.executable,'-B',str(HERE/'run.py'),'--source',args.source]
    result=guard.guarded_run(command,cwd=ROOT,receipt_dir=directory,**plan['memory'])
    print(json.dumps(result),flush=True)
    return int(result['phase']!='complete')

if __name__=='__main__':raise SystemExit(main())
