"""Candidate-only reviewed offline tiny synthetic tests; no real-data execution."""
import os,resource,sys
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]))
resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
import importlib.util
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3];sys.path.insert(0,str(R))
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';os.environ['RUN_ONLINE_TESTS']='0';os.environ.pop('PYTEST_ADDOPTS',None)
def audit(event,args):
 if event=='import' and args[0].split('.')[0]=='torch':raise RuntimeError('Torch prohibited')
 if event in ('socket.connect','socket.getaddrinfo'):raise RuntimeError('network prohibited')
 if event=='open' and isinstance(args[0],str):
  p=Path(args[0])
  if p.is_absolute() and p.is_relative_to(R) and any(x in p.relative_to(R).parts for x in ('research_runs','research_artifacts','keys','apis','data')):raise RuntimeError('original data prohibited')
sys.addaudithook(audit)
import tradingagents.research.onchain_replication as package
for name in ('matching_pair','compact_matcher'):
 full=package.__name__+'.'+name
 spec=importlib.util.spec_from_file_location(full,H/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[full]=m;setattr(package,name,m);spec.loader.exec_module(m)
from scripts import verify_offline
paths=[str((H/name).relative_to(R)) for name in ('test_matching_pair_checkpoints.py','test_compact_matcher.py')]
verify_offline.OFFLINE_FILES=verify_offline.OFFLINE_FILES|set(paths)
paths.append('tests/research/onchain_replication/test_compact_policy.py')
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','--import-mode=importlib',*paths]))
