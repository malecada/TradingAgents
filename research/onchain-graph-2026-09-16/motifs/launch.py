"""Two-CPU sampled2GiB memory-only envelope; no elapsed-time kill."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
from tradingagents.research.admission import admit


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True)
    args=parser.parse_args();here=Path(__file__).resolve().parent;root=here.parents[2]
    admit(root=root,registration='research/onchain-graph-2026-09-16/motifs/gates.json',
          experiment='eth-temporal-motifs-20260916',source=args.source)
    launcher=load('motif_memory_launcher',here.parent/'launch_source.py')
    guard=load('motif_guard',root/'research/strategy-search-2026-09-11/resource_guard_v2.py')
    with (here/'resource.json').open('x') as stream:
        result=launcher.run_without_elapsed_kill([sys.executable,'-B',str(here/'benchmark.py'),'--source',args.source],guard,root)
        result['source']=args.source;json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result))
    return int(result['child_exit_code'] != 0 or result['limit_reason'] is not None)


if __name__ == '__main__':raise SystemExit(main())
