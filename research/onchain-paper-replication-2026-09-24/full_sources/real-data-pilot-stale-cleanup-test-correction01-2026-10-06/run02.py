"""Admit only the authorized copied cleanup module; keep offline guards intact."""
import os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
os.environ.update(PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT),PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',RUN_ONLINE_TESTS='0')
os.environ.pop('PYTEST_ADDOPTS',None)
sys.path.insert(0,str(ROOT))
from scripts import verify_offline
name=(HERE/'test_score_cleanup.py').relative_to(ROOT).as_posix()
verify_offline.OFFLINE_FILES=verify_offline.OFFLINE_FILES|{name}
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','--import-mode=importlib','--basetemp',str(HERE/'synthetic-tmp02'),name]))
