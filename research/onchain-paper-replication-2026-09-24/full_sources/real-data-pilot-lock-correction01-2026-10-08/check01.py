"""Explicit reviewed offline synthetic profile extension; no live integration."""
import os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3];sys.path.insert(0,str(R))
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';os.environ['RUN_ONLINE_TESTS']='0';os.environ.pop('PYTEST_ADDOPTS',None)
def audit(event,args):
 if event=='import' and args[0].split('.')[0] in {'numpy','torch','pandas','scipy'}:raise RuntimeError('numerical imports prohibited')
sys.addaudithook(audit)
from scripts import verify_offline
path=str((H/'test_lock01.py').relative_to(R));verify_offline.OFFLINE_FILES=verify_offline.OFFLINE_FILES|{path}
import pytest
raise SystemExit(pytest.main(['-q','-s','-p','no:cacheprovider','--import-mode=importlib',path,*sys.argv[1:]]))
