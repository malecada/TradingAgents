"""Reuse the accepted twelve behavioral tests against only the new fixed policy."""
from pathlib import Path
import sys
import pytest
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
TARGET=ROOT/'tests/research/onchain_replication/test_neural_launch_readiness_5gib.py'
class BindPolicy:
    def pytest_collection_modifyitems(self,session,config,items):
        for item in items:
            if Path(item.module.__file__).resolve()!=TARGET:raise ValueError('unexpected test scope')
            item.module.PREP=HERE
if __name__=='__main__':
    sys.path.insert(0,str(ROOT))
    raise SystemExit(pytest.main(['-q',str(TARGET)],plugins=[BindPolicy()]))
