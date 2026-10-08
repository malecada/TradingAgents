"""Independent fail-closed deferred-import boundaries; no graph operations."""
import os,resource,sys
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
from pathlib import Path
import hashlib,importlib.abc,importlib.util,inspect,json
H=Path(__file__).resolve().parent;R=H.parents[4];D=H.parent.parent/'real-data-pilot-startup-lazy-engine-correction01-2026-10-08';sys.path.insert(0,str(R))
def audit(event,args):
 if event=='import' and args[0].split('.')[0]=='torch':raise RuntimeError('torch forbidden')
 if event in ('socket.connect','socket.getaddrinfo'):raise RuntimeError('network forbidden')
 if event=='open' and isinstance(args[0],str):
  p=Path(args[0])
  if any(x in p.parts for x in ('research_artifacts','research_runs','keys','apis')) or p.name in ('.env','hf_token.txt') or p.suffix in ('.npy','.npz','.parquet'):raise RuntimeError('private/scientific input forbidden')
sys.addaudithook(audit)
import tradingagents.research.onchain_replication as package
fullname=package.__name__+'.matching_checkpoint'
class ExpectedImportRefusal(ImportError):pass
class RefuseEngine(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname_,path=None,target=None):
  if fullname_==fullname:raise ExpectedImportRefusal('deliberate engine import refusal')
blocker=RefuseEngine();sys.meta_path.insert(0,blocker)
def candidate(name):
 full=package.__name__+'.'+name;p=D/(name+'.py');spec=importlib.util.spec_from_file_location(full,p);m=importlib.util.module_from_spec(spec);sys.modules[full]=m;setattr(package,name,m);spec.loader.exec_module(m);return m
pair=candidate('matching_pair')
from tradingagents.research.onchain_replication import real_pilot_reservations,compact_policy
assert fullname not in sys.modules and 'scipy.special' not in sys.modules and not hasattr(pair,'engine')
assert compact_policy.pair is pair
# Each moved import must fail before the first engine use or other function work.
instance=pair.PairSession.__new__(pair.PairSession)
functions=[('write',pair.write),('identity',pair.identity),('policy_check',pair.policy_check),('_reserve',pair.PairSession._reserve),('create',pair.PairSession.create),('resume',pair.PairSession.resume),('step',instance.step),('save',instance.save),('close',instance.close)]
refused=[]
for label,fn in functions:
 kwargs={k:None for k,v in inspect.signature(fn).parameters.items() if v.default is inspect.Parameter.empty}
 try:fn(**kwargs)
 except ExpectedImportRefusal:refused.append(label)
 else:raise AssertionError('engine refusal lost at '+label)
 assert fullname not in sys.modules
sys.meta_path.remove(blocker)
matcher=candidate('compact_matcher');engine=sys.modules[fullname]
assert matcher.engine is engine and not hasattr(pair,'engine')
path=Path(engine.__file__).resolve();expected=R/'tradingagents/research/onchain_replication/matching_checkpoint.py'
assert path==expected and hashlib.sha256(path.read_bytes()).hexdigest()=='de8f7077e513105719fffcf6ea13e96bfb0199056acf0227ecf744df189ee35c'
# Invalid workflow context still refuses through the genuine pair function after real import.
try:pair.identity(None,None,None,{})
except ValueError as error:assert 'explicit workflow/source/runtime context required' in str(error)
else:raise AssertionError('missing context accepted')
assert 'torch' not in sys.modules
print(json.dumps({'decision':'passed','metadata_import_succeeded_with_engine_import_forbidden':True,'all_nine_deferred_engine_refusals':refused,'genuine_engine_source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'compact_matcher_engine_identity_exact':True,'missing_context_refused':True,'scientific_operations_executed':False,'private_or_empirical_inputs_read':False},sort_keys=True))
