"""Reuse unchanged reviewed 8 GiB/two-CPU/no-duration-kill resource guard."""
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
    admit(root=root, registration='research/onchain-graph-2026-09-16/comparison/capture-gates.json',
          experiment='eth-matched-input-capture-20260916', source=args.source)
    launcher = load('capture_reviewed_memory_guard', here.parent/'motifs8gib/launch.py')
    guard = load('capture_reviewed_cpu_guard', root/'research/strategy-search-2026-09-11/resource_guard_v2.py')
    with (here/'capture-resource.json').open('x') as stream:
        result = launcher.run_with_limit([sys.executable, '-B', str(here/'capture_run.py'),
                                         '--source', args.source], guard, root)
        result['source'] = args.source
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))
    return int(result['child_exit_code'] != 0 or result['limit_reason'] is not None)


if __name__ == '__main__':
    raise SystemExit(main())
