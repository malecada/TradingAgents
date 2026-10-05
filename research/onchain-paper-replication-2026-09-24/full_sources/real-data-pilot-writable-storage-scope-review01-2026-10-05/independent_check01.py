"""Three synthetic metadata refusals only; no authority or native processes."""
from pathlib import Path
import ast,importlib,json,sys,tempfile,types
D=Path(__file__).resolve().parent;M=D.parents[3];P=Path('tradingagents/research/onchain_replication');C=D.parent/'real-data-pilot-writable-storage-scope02-2026-10-05/candidate'/P
pkg=types.ModuleType('isolated_review');pkg.__path__=[str(C),str(M/P)];sys.modules[pkg.__name__]=pkg
s=importlib.import_module('isolated_review.real_pilot_storage')
limits={'max_allocated_bytes':1048576,'max_logical_bytes':1048576,'max_entries':100,'max_depth':8,'max_scan_seconds':5}
def setup(p):
 (p/'research_artifacts').mkdir();(p/'research_runs').mkdir();(p/'research_runs/.lock').write_bytes(b'lock')
 return {'schema_version':2,'kind':s.KIND,'experiment':s.EXPERIMENT,'authority_root':str(p),'roots':[str(p/'research_artifacts'),str(p/'research_runs'/s.EXPERIMENT)],'shared_files':[str(p/'research_runs/.lock')],'limits':dict(limits)}
results=[]
def refused(name,fn,message):
 try:fn()
 except ValueError as e:
  assert message in str(e);results.append({'case':name,'result':'refused','reason':str(e)})
 else:raise AssertionError(name+' unexpectedly accepted')
with tempfile.TemporaryDirectory(dir=D) as tmp:
 p=Path(tmp);budget=setup(p);w=s.WritableUnion(budget,p);w.check()
 original=s.StorageWatch._check
 def birth(watch,begin,history):
  result=original(watch,begin,history)
  if watch.root==p/'research_artifacts':w.target.mkdir()
  return result
 s.StorageWatch._check=birth
 try:refused('birth during absent observation',w.check,'born during scan')
 finally:s.StorageWatch._check=original
with tempfile.TemporaryDirectory(dir=D) as tmp:
 p=Path(tmp);budget=setup(p);w=s.WritableUnion(budget,p);w.check()
 w.lock.rename(p/'research_runs/retained-old-lock');w.lock.write_bytes(b'new')
 refused('shared lock replacement between observations',w.check,'lock type/link/identity')
with tempfile.TemporaryDirectory(dir=D) as tmp:
 p=Path(tmp);budget=setup(p)
 tree=ast.parse((C/'job.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='resource_policy')
 env={'__name__':'isolated_review.policy','__package__':'isolated_review','Path':Path,'resources':types.SimpleNamespace(GIB=1024**3)}
 exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-resource-policy','exec'),env)
 policy={'memory_max_bytes':1024**3,'memory_high_bytes':1024**3,'reserve_bytes':3*1024**3,'start_reserve_bytes':4*1024**3,'disk_floor_bytes':10*1024**3,'disk_paths':[str(p)],'wall_seconds':100,'storage_budget':budget}
 refused('selected union without admission context',lambda:env['resource_policy'](policy,p),'explicit real-pilot selection')
assert not {'numpy','torch','scipy','networkx'} & set(sys.modules)
print(json.dumps({'decision':'pass','checks':results,'numerical_imports':False,'genuine_authority_constructed':False},sort_keys=True,indent=2))
