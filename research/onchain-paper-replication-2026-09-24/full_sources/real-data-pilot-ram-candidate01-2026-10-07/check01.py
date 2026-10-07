"""Runs explicitly reviewed synthetic module in the repository offline profile."""
import importlib.util,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3];sys.path.insert(0,str(R))
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';os.environ['RUN_ONLINE_TESTS']='0';os.environ.pop('PYTEST_ADDOPTS',None)
def audit(event,args):
 if event=='import' and args[0].split('.')[0] in {'numpy','torch','pandas','scipy'}:raise RuntimeError('numerical imports prohibited')
sys.addaudithook(audit)
import tradingagents.research.onchain_replication as package
S=H/'baseline' if os.environ.get('RAM_BASELINE')=='1' else H
for name in ('resources','real_pilot_import_caller','job'):
 full=package.__name__+'.'+name;spec=importlib.util.spec_from_file_location(full,S/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[full]=m;setattr(package,name,m);spec.loader.exec_module(m)
from scripts import verify_offline
path=str((H/'test_ram01.py').relative_to(R));verify_offline.OFFLINE_FILES=verify_offline.OFFLINE_FILES|{path}
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','--import-mode=importlib',path,*sys.argv[1:]]))
