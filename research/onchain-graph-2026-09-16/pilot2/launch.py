"""One frozen compute or independent-check invocation under the reviewed guard."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
from admission import admit_pilot

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--review',action='store_true');args=p.parse_args()
    here=Path(__file__).resolve().parent;root=here.parents[2]
    # Compute admission before claim; independent review verifies terminal through its own verifier.
    if not args.review:admit_pilot(root,args.source)
    guard=load('pilot2_cpu_guard',root/'research/strategy-search-2026-09-11/resource_guard_v2.py')
    memory=load('pilot2_memory_guard',here.parent/'motifs8gib/launch.py')
    scratch=here/'scratch';scratch.mkdir(exist_ok=True);os.environ['TMPDIR']=str(scratch)
    if args.review:
        command=[sys.executable,'-B',str(here/'check_independent.py'),'--root',str(root),'--source',args.source,'--report',str(here/'independent-report.json')]
        receipt=here/'independent-resource.json'
    else:
        command=[sys.executable,'-B',str(here/'run.py'),'--source',args.source];receipt=here/'resource.json'
    with receipt.open('x') as handle:
        result=memory.run_with_limit(command,guard,root);result['source']=args.source
        json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps(result),flush=True)
    return int(result['child_exit_code']!=0 or result['limit_reason'] is not None)
if __name__=='__main__':raise SystemExit(main())
