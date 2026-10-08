"""Own focused synthetic checks; installed numerical modules forbidden."""
from pathlib import Path
import importlib.util,os,sys,resource
H=Path(__file__).resolve().parent;R=H.parents[4];C=H.parent.parent/'real-data-pilot-startup-reserve-correction01-2026-10-08';sys.path.insert(0,str(R))
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';os.environ['RUN_ONLINE_TESTS']='0';os.environ.pop('PYTEST_ADDOPTS',None)
def audit(event,args):
 if event=='import' and args[0].split('.')[0] in {'numpy','torch','scipy','pandas'}:raise RuntimeError('numerical imports forbidden')
 if event in ('socket.connect','socket.getaddrinfo'):raise RuntimeError('network forbidden')
sys.addaudithook(audit)
import tradingagents.research.onchain_replication as package
for name in ('resources','real_pilot_import_caller','job'):
 full=package.__name__+'.'+name;spec=importlib.util.spec_from_file_location(full,C/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[full]=m;setattr(package,name,m);spec.loader.exec_module(m)
from scripts import verify_offline
path=str((H/'test_boundaries01.py').relative_to(R));verify_offline.OFFLINE_FILES=verify_offline.OFFLINE_FILES|{path}
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','--import-mode=importlib','--basetemp',str(H/'synthetic01'),path]))
