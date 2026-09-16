"""Pinned foreground resource envelope for the single registered source audit."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

from tradingagents.research.admission import admit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    admit(root=root, registration='research/onchain-graph-2026-09-16/gates-source.json',
          experiment='eth-graph-source-20260916', source=args.source)
    spec = importlib.util.spec_from_file_location('onchain_source_guard',
        root / 'research/strategy-search-2026-09-11/resource_guard_v2.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    report_path = Path(__file__).with_name('source-resource.json')
    with report_path.open('x') as stream:
        result = guard.run_guard([sys.executable, '-B', str(Path(__file__).with_name('source_probe.py')),
            '--root', str(root), '--source', args.source], rss_limit_bytes=2 * 1024**3, wall_seconds=360)
        result['source'] = args.source
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))
    return 0 if result['child_exit_code'] == 0 and result['limit_reason'] is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
