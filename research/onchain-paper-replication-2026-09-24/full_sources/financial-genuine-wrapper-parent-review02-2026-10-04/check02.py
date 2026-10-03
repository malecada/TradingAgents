"""Exact-source scalar policy controls and first-fatal prelaunch counterexample."""
import ast,hashlib,json,os,sys
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;C=H.parent/'financial-genuine-wrapper-parent-preparation02-2026-10-04'
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source')
checks=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def require(v,m):
 if not v:raise ValueError(m)
def extract(raw,names):
 tree=ast.parse(raw);nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
 assert len(nodes)==len(names)
 return ast.Module(body=nodes,type_ignores=[])
raw=(C/'parent01.py').read_text();tree=ast.parse(raw);launch=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='launch')
seam=next(n for n in launch.body if isinstance(n,ast.Try) and any(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and c.func.attr=='fsync' for c in ast.walk(n)))
ok('counterexample exact plain fsync/close seam',ast.get_source_segment(raw,seam)=='try:os.fsync(fd)\n finally:os.close(fd)')
primary=KeyboardInterrupt('original fsync fatal');secondary=OSError('later close error');events=[]
fd=os.open(H,os.O_RDONLY|os.O_DIRECTORY)
def fsync(n):os.fsync(n);events.append('actual fsync then primary fatal');raise primary
def close(n):os.close(n);events.append('actual close then secondary ordinary');raise secondary
observed=None
try:exec(compile(ast.Module(body=[seam],type_ignores=[]),str(C/'parent01.py'),'exec'),{'os':SimpleNamespace(fsync=fsync,close=close),'fd':fd})
except BaseException as e:observed=e
ok('PF1 original primary fatal replaced',observed is secondary and observed.__context__ is primary)
try:os.fstat(fd)
except OSError:checks.append('owned counterexample fd actually closed')
else:raise AssertionError('owned fd remains')
witness={'id':'PF1','file':str(C/'parent01.py'),'line':seam.lineno,'end_line':seam.end_lineno,'source_segment':ast.get_source_segment(raw,seam),'source_sha256':hashlib.sha256(raw.encode()).hexdigest(),'events':events,'primary_type':type(primary).__name__,'observed_type':type(observed).__name__,'same_primary_observed':observed is primary,'secondary_is_observed':observed is secondary,'primary_retained_only_as_context':observed.__context__ is primary,'real_native_commands':False,'real_research_claims':False}
(H/'PF1_WITNESS01.json').write_text(json.dumps(witness,sort_keys=True,indent=2)+'\n')
# Actual original command builder; plain argument record, not a ResearchRun/Owner/Binding.
job=(C/'original-job.py').read_text();ns={'sys':sys,'Path':Path,'MODULE':'tradingagents.research.onchain_replication.job'}
exec(compile(extract(job,{'_command'}),'original-job.py','exec'),ns)
args=SimpleNamespace(root=str(CAP),registration='opaque-registration.json',experiment='opaque-unreserved-scalar',source='0'*40)
cmd=ns['_command'](args,'launch')
ok('original command exactly forwards source and fixed mode',cmd==[sys.executable,'-B','-m',ns['MODULE'],'--mode','launch','--root',str(CAP),'--registration',args.registration,'--experiment',args.experiment,'--source',args.source])
ok('no invented design argument','--design-source' not in cmd)
fw=(CAP/'tradingagents/research/onchain_replication/financial_wrapper_fixture.py').read_text();ns={'require':require,'GIB':1024**3,'FILE':4*1024**2}
exec(compile(extract(fw,{'schema'}),'financial_wrapper_fixture.py','exec'),ns)
# Genuine prepared initial job supplies exact policy; this control does not decode samples.
pre=H.parent/'financial-genuine-wrapper-registration-preparation01-2026-10-04'
paths=sorted((pre/'generated03').rglob('*.json'))
jobs=[]
for p in paths:
 v=json.loads(p.read_bytes())
 if isinstance(v,dict) and v.get('kind')=='financial_wrapper':jobs.append((p,v))
ok('ten genuine prepared initial job bodies',len(jobs)==10)
for p,v in jobs:ns['schema'](v);checks.append('genuine schema '+p.name)
base=jobs[0][1]
for key,value in [('memory_max_bytes',4*1024**3),('memory_high_bytes',2*1024**3),('reserve_bytes',2*1024**3),('start_reserve_bytes',5*1024**3),('disk_floor_bytes',9*1024**3),('wall_seconds',1801)]:
 v=json.loads(json.dumps(base));v['resources'][key]=value
 try:ns['schema'](v)
 except ValueError:checks.append('actual schema refuses '+key)
 else:raise AssertionError('widened policy '+key)
v=json.loads(json.dumps(base));v['resources']['native_unit_limits']['file_size_bytes']=8*1024**2
try:ns['schema'](v)
except ValueError:checks.append('actual schema refuses larger file bound')
else:raise AssertionError('file bound accepted')
v=json.loads(json.dumps(base));v['resources']['storage_budget']['limits']['max_logical_bytes']=2*1024**3
try:ns['schema'](v)
except ValueError:checks.append('actual schema refuses larger storage bound')
else:raise AssertionError('storage bound accepted')
ok('outer deadline fixed1840 source',"supervise(command,CAP,env,directory,1840,checked,spawned)" in raw)
ok('planned interruption not success',"'planned_interrupt_requested':q['expected_phase']=='interrupt1','outcome_semantics_accepted':False" in raw)
ok('no numeric imports',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
(H/'CHECKS02.json').write_text(json.dumps({'checks':checks,'count':len(checks),'counterexample':witness,'actual_native_commands':False,'actual_run_start':False,'policy_source_sha256':hashlib.sha256(fw.encode()).hexdigest(),'original_job_sha256':hashlib.sha256(job.encode()).hexdigest()},sort_keys=True,indent=2)+'\n')
print(len(checks),'source controls passed; PF1 independently reproduced')
