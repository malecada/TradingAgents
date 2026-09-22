"""Frozen full-panel compute under the unchanged sampled8GiB/two-CPU guard."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
from admission import admit_panel

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--review',action='store_true');args=parser.parse_args()
    here=Path(__file__).resolve().parent;root=here.parents[2]
    if not args.review:admit_panel(root,args.source)
    receipt=here/('independent-resource.json' if args.review else 'resource.json')
    if receipt.exists():raise FileExistsError('guard receipt already exists')
    scratch=here/'sparse-scratch';scratch.mkdir(exist_ok=args.review);os.environ['TMPDIR']=str(scratch)
    guard=load('fullpanel_cpu_guard',root/'research/strategy-search-2026-09-11/resource_guard_v2.py')
    memory=load('fullpanel_memory_guard',here.parent/'motifs8gib/launch.py')
    command=([sys.executable,'-B',str(here/'check_final.py'),'--root',str(root),'--source',args.source,'--report',str(here/'independent-report.json')]
             if args.review else [sys.executable,'-B',str(here/'run.py'),'--source',args.source])
    with receipt.open('x') as stream:
        result=memory.run_with_limit(command,guard,root);result['source']=args.source
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result),flush=True)
    return int(result['child_exit_code']!=0 or result['limit_reason'] is not None)
if __name__=='__main__':raise SystemExit(main())
