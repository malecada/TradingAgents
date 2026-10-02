"""Finite scheduling observations; these tests never launch a workload."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PREP = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-successor-preparation-2026-10-02'


def module():
    path = PREP / 'readiness.py'
    assert path.is_file(), 'finite prelaunch observer is missing'
    spec = importlib.util.spec_from_file_location('neural_launch_readiness_fixture', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def policy():
    return json.loads((PREP / 'launch_scheduling.json').read_text())


class Clock:
    def __init__(self):
        self.seconds = 100.0

    def now(self):
        return self.seconds

    def sleep(self, seconds):
        self.seconds += seconds


def test_exact_margin_requires_all_sixteen_reads_and_thirty_seconds():
    clock = Clock()
    reads = []
    def memory():
        reads.append(clock.now())
        return policy()['minimum_available_bytes']
    result = module().observe(policy(), mem_available=memory, clock=clock.now, sleep=clock.sleep)
    assert result['status'] == 'ready'
    assert len(reads) == 16
    assert reads == [100.0 + 2*i for i in range(16)]
    assert result['elapsed_seconds'] == 30.0
    assert module().fresh(result, policy(), clock.now())


@pytest.mark.parametrize('failed_index', [0, 7, 15])
def test_one_low_read_refuses_without_waiting_for_recovery(failed_index):
    clock = Clock()
    reads = []
    def memory():
        index = len(reads)
        reads.append(index)
        return policy()['minimum_available_bytes'] - (index == failed_index)
    result = module().observe(policy(), mem_available=memory, clock=clock.now, sleep=clock.sleep)
    assert result['status'] == 'deferred'
    assert result['reason'] == 'available RAM below scheduling margin'
    assert len(reads) == failed_index + 1
    assert not module().fresh(result, policy(), clock.now())


def test_slow_read_cannot_make_the_window_pass():
    clock = Clock()
    def memory():
        clock.seconds += 61
        return policy()['minimum_available_bytes']
    result = module().observe(policy(), mem_available=memory, clock=clock.now, sleep=clock.sleep)
    assert result['status'] == 'deferred'
    assert result['reason'] == 'readiness observation window expired'
    assert not module().fresh(result, policy(), clock.now())


def test_observation_expires_before_a_delayed_launch():
    clock = Clock()
    result = module().observe(policy(), mem_available=lambda: policy()['minimum_available_bytes'],
                              clock=clock.now, sleep=clock.sleep)
    assert module().fresh(result, policy(), clock.now() + 1)
    assert not module().fresh(result, policy(), clock.now() + 1.001)
    assert not module().fresh(result, policy(), clock.now() - 1)


def test_truncated_or_altered_observations_are_not_ready():
    clock = Clock()
    result = module().observe(policy(), mem_available=lambda: policy()['minimum_available_bytes'],
                              clock=clock.now, sleep=clock.sleep)
    result['observations'].pop()
    assert not module().fresh(result, policy(), clock.now())
    result = module().observe(policy(), mem_available=lambda: policy()['minimum_available_bytes'],
                              clock=clock.now, sleep=clock.sleep)
    result['observations'][5]['available_bytes'] -= 1
    assert not module().fresh(result, policy(), clock.now())


@pytest.mark.parametrize('value', [True, -1, 1.5])
def test_invalid_memory_readback_never_passes(value):
    clock = Clock()
    with pytest.raises(ValueError, match='memory readback'):
        module().observe(policy(), mem_available=lambda: value, clock=clock.now, sleep=clock.sleep)


def test_original_fatal_from_observation_is_preserved():
    clock = Clock()
    original = MemoryError('readback unavailable')
    def memory():
        raise original
    with pytest.raises(MemoryError) as caught:
        module().observe(policy(), mem_available=memory, clock=clock.now, sleep=clock.sleep)
    assert caught.value is original


def test_weaker_or_unbounded_policy_is_refused():
    clock = Clock()
    for name, value in [('minimum_available_bytes', 9663676416),
                        ('observation_count', 1), ('maximum_window_seconds', float('inf')),
                        ('automatic_launch_retry', True)]:
        changed = policy()
        changed[name] = value
        with pytest.raises(ValueError, match='scheduling policy'):
            module().observe(changed, mem_available=lambda: 10**12, clock=clock.now, sleep=clock.sleep)
