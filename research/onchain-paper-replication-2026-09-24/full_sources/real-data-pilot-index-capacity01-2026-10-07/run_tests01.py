"""Admit only this reviewed synthetic candidate module to the offline profile.

No persistent inventory edit: parent owns live integration. The normal root
conftest installs network/store guards; legacy tests remain withheld.
"""
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));os.chdir(ROOT)
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';os.environ['RUN_ONLINE_TESTS']='0';os.environ.pop('PYTEST_ADDOPTS',None)
from scripts import verify_offline
path=str(Path(__file__).with_name('test_capacity01.py').relative_to(ROOT))
verify_offline.OFFLINE_FILES=verify_offline.OFFLINE_FILES|{path}
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','--import-mode=importlib',path,'tests/research/onchain_replication/test_array_neighborhoods.py']))
