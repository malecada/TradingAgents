"""Linux sampled process-tree RSS/wall guard; no virtual-address-space cap."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time


def tree_rss(pid):
    """Leader-thread descendants only; tolerate a confirmed process-exit transition."""
    for observation in range(2):
        try:
            status = Path(f'/proc/{pid}/status').read_text()
            children = Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
        except (FileNotFoundError, ProcessLookupError):
            return 0
        values = [line.split()[1] for line in status.splitlines() if line.startswith('VmRSS:')]
        if values:
            rss = int(values[0])
            if rss < 0:
                raise RuntimeError(f'negative VmRSS for PID {pid}')
            return rss * 1024 + sum(tree_rss(int(child)) for child in children)
        state = next((line for line in status.splitlines() if line.startswith('State:')), 'State: missing')
        if state.split()[1:2] in (['Z'], ['X']):
            return 0
        if observation == 0:
            time.sleep(.02)  # mm may be released before the exiting state is published.
        else:
            raise RuntimeError(f'PID {pid} still has no VmRSS after exit-transition retry; {state}')


def _limits():
    resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])


def run_guard(command, *, rss_limit_bytes=512*1024**2, wall_seconds=120, interval=.02):
    env = dict(os.environ)
    env.update(OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2')
    begin = time.monotonic()
    try:
        process = subprocess.Popen(command, env=env, preexec_fn=_limits, start_new_session=True)
    except (OSError, subprocess.SubprocessError) as exc:
        return {'child_exit_code': None, 'limit_reason': 'launch/setup failed: '+str(exc),
                'elapsed_seconds': time.monotonic()-begin, 'peak_sampled_tree_rss_bytes': None,
                'linux_children_ru_maxrss_kib': None, 'rss_limit_bytes': rss_limit_bytes,
                'wall_limit_seconds': wall_seconds, 'sample_interval_seconds': interval,
                'virtual_address_space_limit': 'setup not confirmed', 'retry': False}
    peak, reason = 0, None
    while process.poll() is None:
        try:
            rss = tree_rss(process.pid)
            peak = max(peak, rss)
            if rss > rss_limit_bytes:
                reason = 'sampled aggregate RSS limit exceeded'
            elif time.monotonic() - begin > wall_seconds:
                reason = 'wall-clock limit exceeded'
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
        time.sleep(interval)
    return {'child_exit_code': process.wait(), 'limit_reason': reason,
            'elapsed_seconds': time.monotonic()-begin, 'peak_sampled_tree_rss_bytes': peak,
            'linux_children_ru_maxrss_kib': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
            'rss_limit_bytes': rss_limit_bytes, 'wall_limit_seconds': wall_seconds,
            'sample_interval_seconds': interval, 'virtual_address_space_limit': 'unlimited',
            'qualification': 'Nominal 20 ms sampled aggregate RSS with one 20 ms process-exit retry; brief overshoot can occur. No detached/background or secondary-thread subprocesses admitted. Shared pages may be counted twice. ru_maxrss is the largest individual child peak, not aggregate.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('child command required')
    # Exclusive reservation prevents accidentally overwriting a prior monitor log.
    with open(args.report, 'x') as report:
        result = run_guard(command)
        json.dump(result, report, indent=2); report.write('\n')
    print(json.dumps(result))
    raise SystemExit(0 if result['child_exit_code'] == 0 and result['limit_reason'] is None else 1)


if __name__ == '__main__':
    main()
