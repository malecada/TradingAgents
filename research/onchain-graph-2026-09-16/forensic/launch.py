"""Memory-only envelope for one offline forensic check; no lifecycle budget amendment."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--source', required=True)
    args = parser.parse_args(); here = Path(__file__).resolve().parent; root = here.parents[2]
    launcher = load('forensic_memory_launcher', here.parent / 'launch_source.py')
    guard = load('forensic_rss_guard', root / 'research/strategy-search-2026-09-11/resource_guard_v2.py')
    with (here / 'resource.json').open('x') as stream:
        result = launcher.run_without_elapsed_kill([sys.executable, '-B', str(here / 'reconstruct.py'), '--source', args.source], guard, root)
        result['source'] = args.source
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(result))
    return 0 if result['child_exit_code'] == 0 and result['limit_reason'] is None else 1


if __name__ == '__main__': raise SystemExit(main())
