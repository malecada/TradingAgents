"""One finite capture under unchanged 8 GiB/two-CPU resource supervision."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

from tradingagents.research import admit


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    admit(root=root, registration='research/onchain-graph-2026-09-16/comparison/bulk-gates.json',
          experiment='eth-remaining-graph-capture-20260916', source=args.source)
    launcher = load('bulk_memory_guard', here.parent/'motifs8gib/launch.py')
    guard = load('bulk_cpu_guard', root/'research/strategy-search-2026-09-11/resource_guard_v2.py')
    with (here/'bulk-resource.json').open('x') as handle:
        result = launcher.run_with_limit([sys.executable, '-B', str(here/'bulk_run.py'),
                                         '--source', args.source], guard, root)
        result['source'] = args.source
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps(result), flush=True)
    return int(result['child_exit_code'] != 0 or result['limit_reason'] is not None)


if __name__ == '__main__':
    raise SystemExit(main())
