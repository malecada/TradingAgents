"""Pinned foreground resource envelope for the single registered source audit."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from tradingagents.research.admission import admit


def run_without_elapsed_kill(command, guard, root):
    env = dict(os.environ, PYTHONPATH=str(root), OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2',
               MKL_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2')
    begin = time.monotonic()
    try:
        process = subprocess.Popen(command, cwd=root, env=env, preexec_fn=guard._limits,
                                   start_new_session=True)
    except (OSError, subprocess.SubprocessError) as exc:
        return {'child_exit_code': None, 'limit_reason': 'launch/setup failed: ' + str(exc),
                'elapsed_seconds': time.monotonic() - begin, 'elapsed_time_kill': False,
                'peak_sampled_tree_rss_bytes': None, 'rss_limit_bytes': 2 * 1024**3,
                'retry': False, 'qualification': 'Child launch/resource setup was not confirmed.'}
    peak, reason = 0, None
    while process.poll() is None:
        try:
            peak = max(peak, guard.tree_rss(process.pid))
            if peak > 2 * 1024**3:
                reason = 'sampled aggregate RSS limit exceeded'
        except (OSError, RuntimeError, ValueError) as exc:
            reason = 'resource monitor failed: ' + str(exc)
        if reason:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            break
        time.sleep(.02)
    return {'child_exit_code': process.wait(), 'limit_reason': reason,
            'elapsed_seconds': time.monotonic() - begin, 'elapsed_time_kill': False,
            'peak_sampled_tree_rss_bytes': peak, 'rss_limit_bytes': 2 * 1024**3,
            'sample_interval_seconds': .02,
            'qualification': 'Sampled RSS can miss brief peaks. Per-request socket timeout and finite request/byte budgets remain.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    admit(root=root, registration='research/onchain-graph-2026-09-16/gates-source-v2.json',
          experiment='eth-graph-source-20260916', source=args.source)
    spec = importlib.util.spec_from_file_location('onchain_source_guard',
        root / 'research/strategy-search-2026-09-11/resource_guard_v2.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    report_path = Path(__file__).with_name('source-resource.json')
    with report_path.open('x') as stream:
        result = run_without_elapsed_kill([sys.executable, '-B', str(Path(__file__).with_name('source_probe.py')),
            '--root', str(root), '--source', args.source], guard, root)
        result['source'] = args.source
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))
    return 0 if result['child_exit_code'] == 0 and result['limit_reason'] is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
