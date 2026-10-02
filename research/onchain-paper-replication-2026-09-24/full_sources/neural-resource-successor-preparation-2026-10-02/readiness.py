"""Finite coordinator RAM observations, never a workload launcher or admission.

Use a new in-process observation after actual metadata admission. A ready result
expires after one second; retained receipts cannot be used as a later permit.
The registered job's independent hard resource checks still apply.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time


_POLICY = {
    'schema_version': 1,
    'minimum_available_bytes': 9932111872,
    'observation_count': 16,
    'observation_interval_seconds': 2,
    'maximum_window_seconds': 60,
    'hard_guard_start_reserve_bytes_unchanged': 9663676416,
    'hard_guard_reserve_bytes_unchanged': 3221225472,
    'failed_observation_reserves_namespace': False,
    'automatic_launch_retry': False,
}


def validate(policy):
    if (type(policy) is not dict or set(policy) != set(_POLICY) | {'qualification'}
            or type(policy['qualification']) is not str or not policy['qualification'].strip()
            or any(type(policy[k]) is not type(v) or policy[k] != v for k, v in _POLICY.items())):
        raise ValueError('scheduling policy differs from the frozen successor')


def _fingerprint(policy):
    return hashlib.sha256((json.dumps(policy, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()).hexdigest()


def read_mem_available():
    with Path('/proc/meminfo').open('rb') as source:
        raw = source.read(65537)
    if len(raw) > 65536:
        raise ValueError('memory readback exceeds its bound')
    values = [line.split() for line in raw.decode('ascii').splitlines() if line.startswith('MemAvailable:')]
    if len(values) != 1 or len(values[0]) != 3 or values[0][2] != 'kB' or not values[0][1].isdecimal():
        raise ValueError('memory readback is unavailable or malformed')
    return int(values[0][1]) * 1024


def _clock(clock):
    value = clock()
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('readiness monotonic clock is invalid')
    return value


def observe(policy, *, mem_available=read_mem_available, clock=time.monotonic, sleep=time.sleep):
    validate(policy)
    start = _clock(clock)
    result = {'schema_version': 1, 'status': 'deferred', 'reason': None,
              'policy_sha256': _fingerprint(policy), 'start_monotonic': start,
              'observations': [], 'elapsed_seconds': 0.0}
    previous = None
    for _ in range(policy['observation_count']):
        if previous is not None:
            remaining = previous + policy['observation_interval_seconds'] - _clock(clock)
            if remaining > 0:
                sleep(remaining)
        before = _clock(clock)
        if before < start or before - start > policy['maximum_window_seconds']:
            result['reason'] = 'readiness observation window expired'
            result['elapsed_seconds'] = before - start
            return result
        available = mem_available()
        if type(available) is not int or available < 0:
            raise ValueError('memory readback is not a nonnegative integer byte count')
        now = _clock(clock)
        if now < before or (previous is not None and now - previous < policy['observation_interval_seconds']):
            raise ValueError('readiness observations did not preserve monotonic spacing')
        result['observations'].append({'monotonic': now, 'available_bytes': available})
        result['elapsed_seconds'] = now - start
        if result['elapsed_seconds'] > policy['maximum_window_seconds']:
            result['reason'] = 'readiness observation window expired'
            return result
        if available < policy['minimum_available_bytes']:
            result['reason'] = 'available RAM below scheduling margin'
            return result
        previous = now
    result['status'] = 'ready'
    result['reason'] = 'all finite scheduling observations passed; hard job admission still required'
    return result


def fresh(result, policy, now):
    """Check the full observation, including expiry, before invoking the job."""
    validate(policy)
    try:
        rows = result['observations']
        times = [row['monotonic'] for row in rows]
        return (type(result) is dict and result['schema_version'] == 1
                and result['status'] == 'ready' and result['policy_sha256'] == _fingerprint(policy)
                and type(rows) is list and len(rows) == policy['observation_count']
                and type(now) in (int, float) and math.isfinite(now)
                and all(type(t) in (int, float) and math.isfinite(t) for t in times)
                and all(type(row['available_bytes']) is int
                        and row['available_bytes'] >= policy['minimum_available_bytes'] for row in rows)
                and all(b - a >= policy['observation_interval_seconds'] for a, b in zip(times, times[1:]))
                and times[0] >= result['start_monotonic']
                and result['elapsed_seconds'] == times[-1] - result['start_monotonic']
                and 30 <= result['elapsed_seconds'] <= policy['maximum_window_seconds']
                and 0 <= now - times[-1] <= 1.0)
    except (KeyError, IndexError, TypeError, ValueError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, required=True)
    args = parser.parse_args()
    raw = args.policy.read_bytes()
    if len(raw) > 262144:
        raise ValueError('scheduling policy exceeds bounded metadata size')
    policy = json.loads(raw)
    result = observe(policy)
    result['policy_file_sha256'] = hashlib.sha256(raw).hexdigest()
    result['qualification'] = 'RAM observations only. No workload, admission, empirical claim or namespace reservation.'
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0 if result['status'] == 'ready' else 3


if __name__ == '__main__':
    raise SystemExit(main())
