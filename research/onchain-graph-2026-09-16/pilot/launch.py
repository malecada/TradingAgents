"""Same reviewed 8 GiB/two-CPU/no-elapsed-kill guard, new seven-day engineering identity."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
from tradingagents.research import admit


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
    here=Path(__file__).resolve().parent;root=here.parents[2]
    admit(root=root,registration='research/onchain-graph-2026-09-16/pilot/gates.json',
          experiment='eth-seven-day-pilot-20260916',source=args.source)
    launcher=load('reviewed_memory_guard',here.parent/'motifs8gib/launch.py')
    guard=load('reviewed_cpu_limits',root/'research/strategy-search-2026-09-11/resource_guard_v2.py')
    with (here/'resource.json').open('x') as stream:
        result=launcher.run_with_limit([sys.executable,'-B',str(here/'run.py'),'--source',args.source],guard,root)
        result['source']=args.source;json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result));return int(result['child_exit_code']!=0 or result['limit_reason'] is not None)


if __name__=='__main__':raise SystemExit(main())
