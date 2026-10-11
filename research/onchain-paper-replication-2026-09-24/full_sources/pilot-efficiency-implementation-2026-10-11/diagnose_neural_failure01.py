"""Observe one existing synthetic test's masked producer cause; no source patch."""
from pathlib import Path
import sys
import traceback

import pytest

TARGET = str(Path('tradingagents/research/onchain_replication/compact_native_producer.py').resolve())


def observe(frame, event, arg):
    if event == 'exception' and arg[0].__name__ == 'CompactProducerError':
        print('\nORIGINAL_SYNTHETIC_PRODUCER_CAUSE:', flush=True)
        traceback.print_exception(arg[1], file=sys.stdout)
    return observe


def select(frame, event, arg):
    if event == 'call' and frame.f_code.co_name == 'produce' and frame.f_code.co_filename == TARGET:
        return observe
    return None


previous = sys.gettrace()
try:
    sys.settrace(select)
    result = pytest.main([
        '-q', '-s', '-x', '-p', 'no:cacheprovider', '--import-mode=importlib',
        'tests/research/onchain_replication/test_archive_producer_integration.py::test_late_archive_mcm_mutation_preserves_spent_claims',
    ])
finally:
    sys.settrace(previous)
raise SystemExit(result)
