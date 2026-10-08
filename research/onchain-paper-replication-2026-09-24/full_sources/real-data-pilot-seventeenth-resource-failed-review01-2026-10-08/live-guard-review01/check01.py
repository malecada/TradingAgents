"""Reviewed synthetic delta profile only; no numerical imports or empirical run."""
import os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[4]
sys.path.insert(0,str(R))
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';os.environ['RUN_ONLINE_TESTS']='0';os.environ.pop('PYTEST_ADDOPTS',None)
os.environ['OWNER_SOURCE']=str(H.parent.parent/'real-data-pilot-live-guard-correction01-2026-10-08/matching_owner.py')
def audit(event,args):
    if event=='import' and args[0].split('.')[0] in {'numpy','torch','pandas','scipy'}:raise RuntimeError('numerical import prohibited')
sys.addaudithook(audit)
from scripts import verify_offline
path=str((H/'test_review01.py').relative_to(R));verify_offline.OFFLINE_FILES=verify_offline.OFFLINE_FILES|{path}
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','--import-mode=importlib',path]))
