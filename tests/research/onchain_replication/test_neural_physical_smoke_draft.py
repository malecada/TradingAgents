"""Pure exception-order checks; never execute the draft OS smoke."""
from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest


def draft():
    root = Path(__file__).resolve().parents[3]
    return runpy.run_path(str(root/'research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-physical-implementation-2026-10-02/os-smoke-preparation/smoke.candidate02.py.draft'))


@pytest.mark.parametrize('fatal_type', [SystemExit, MemoryError])
def test_terminal_fatal_promotes_over_ordinary_and_retains_first_fatal(fatal_type):
    reduce = draft()['terminal_primary']
    ordinary = ValueError('original terminal write')
    fatal = fatal_type('first fatal')
    later = SystemExit('later fatal')
    assert reduce([ordinary, fatal, later]) is fatal
    assert fatal.__cause__ is ordinary
    assert any('later fatal' in note for note in fatal.__notes__)


def test_failed_claim_observation_does_not_skip_observer_or_finish():
    calls = []
    primary = ValueError('claim observation unavailable')
    fatal = SystemExit('finish fatal')
    def check(**kwargs):
        calls.append('check')
        raise primary
    def publish(path, value):
        calls.append(path.name)
    def finish():
        calls.append('finish')
        raise fatal
    scope = SimpleNamespace(check=check, base=Path('synthetic'), finish=finish)
    with pytest.raises(SystemExit) as caught:
        draft()['terminal_publications'](scope, publish, {'status': 'failed'})
    assert caught.value is fatal and fatal.__cause__ is primary
    assert calls == ['check', 'observer.json', 'finish']
