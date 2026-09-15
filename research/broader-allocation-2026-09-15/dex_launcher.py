"""Exact240second/512MiB/twoCPU wrapper; no modification to the existing guard."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
loader = importlib.util.spec_from_file_location('broader_existing_guard_v2', HERE.parent/'strategy-search-2026-09-11/resource_guard_v2.py')
guard = importlib.util.module_from_spec(loader)
loader.loader.exec_module(guard)


def launch(command):
    return guard.run_guard(command, wall_seconds=240, rss_limit_bytes=512*1024**2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    with open(args.report, 'x') as stream:
        result = launch([sys.executable, '-B', str(HERE/'dex_source.py'), '--source', args.source])
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))
    raise SystemExit(0 if result['child_exit_code'] == 0 and result['limit_reason'] is None else 1)


if __name__ == '__main__':
    main()
