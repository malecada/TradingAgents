"""Offline schema and mocked native readbacks, no process-limit changes or claim."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,resource,sys,types,unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
D=Path(__file__).resolve().parent;M=D.parents[3];P=Path('tradingagents/research/onchain_replication');T=D/'candidate'/P
pkg=types.ModuleType('policy_offline');pkg.__path__=[str(T),str(M/P)];sys.modules['policy_offline']=pkg

def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m

def funcs(path,names,env):
 nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
 assert {n.name for n in nodes}==set(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env)
 return env
caller=load('policy_offline.real_pilot_import_caller',T/'real_pilot_import_caller.py')
original=load('policy_offline.baseline_caller',D/'baseline/real_pilot_import_caller.py')
fixture=load('policy_offline.resource_fixture',T/'resource_fixture.py')
res=load('policy_offline.resources',T/'resources.py')
job=types.ModuleType('policy_offline.job');job.__dict__.update(__package__='policy_offline',Path=Path,resources=res,os=os);sys.modules[job.__name__]=job
funcs(T/'job.py',['resource_policy','_resource_worker_limits','_resource_limit_receipt'],job.__dict__)
GIB=1024**3

def resources(root,large=False):
 return {'memory_max_bytes':(4 if large else 3)*GIB,'memory_high_bytes':3*GIB,'reserve_bytes':3*GIB,'start_reserve_bytes':(7 if large else 6)*GIB,'disk_floor_bytes':10*GIB,'disk_paths':[str(root)],'wall_seconds':3600 if large else 1800,'native_unit_limits':{'file_size_bytes':16*1024**2 if large else 4*1024**2},'storage_budget':{'root':str(root),'limits':{'max_allocated_bytes':2*GIB if large else GIB,'max_logical_bytes':2*GIB if large else GIB,'max_entries':65536 if large else 32768,'max_depth':32,'max_scan_seconds':5}}}

def make_job(root,large=False):
 selected={k:'synthetic-'+k for k in caller.KEYS-{'descriptor','operation'}}
 selected.update(operation='produce',descriptor={'arm':'proposed','dictionary_origin':'imported-original-v1'})
 return {'schema_version':1,'kind':'compact_resource','resources':resources(root,large),'environment_input':'synthetic-environment','payload':{'representation_jobs':{'test':selected}}}

def plan(j,version):
 hashes=[f'{i:064x}' for i in range(7)]
 p={'schema_version':version,'kind':caller.KIND,'asset':'ETH','seed':11,'batch_size':16,'lookback_days':28,'cell_id':'synthetic-policy-only','graph_inputs':{h:'role'+str(i) for i,h in enumerate(hashes)},'indices':list(range(16)),'decisions':[f'2022-06-{i:02}' for i in range(1,17)],'graph_sequences':[hashes*4 for _ in range(16)],'population_plan_input':'population','model_input':'model','training_input':'training','model_execution':None,'max_checkpoint_bytes':4*1024**2,'outputs':dict(summary='summary.json',ledger='ledger.json',binding='binding.json',journal='journal.json')}
 if version==2:p['resource_policy']=copy.deepcopy(j['resources'])
 return p

def ast_functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}

class Checks(unittest.TestCase):
 def test_01_exact_inverse_and_legacy_controls(self):
  d=json.loads((D/'SOURCE_DELTA01.json').read_text())
  for r in d['files']:
   raw=(D/'candidate'/r['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),r['candidate_sha256']);lines=raw.decode().splitlines(True)
   for e in reversed(r['edits']):self.assertEqual(lines[e['new_start']:e['new_end']],e['new']);lines[e['new_start']:e['new_end']]=e['old']
   self.assertEqual(''.join(lines).encode(),(D/'baseline'/Path(r['path']).name).read_bytes())
   self.assertEqual(hashlib.sha256((M/r['path']).read_bytes()).hexdigest(),r['baseline_sha256'])
  for n,changed in [('resources.py',{'_native_policy'}),('resource_fixture.py',{'publication_boundary'}),('job.py',{'_resource_worker_limits','_resource_limit_receipt','worker'}),('real_pilot_import_caller.py',{'validate_plan','schema','admitted','_tiny_resources','_finite_resources','_bind_resources','worker_limits','publication_boundary'})]:
   old=ast_functions(D/'baseline'/n);new=ast_functions(T/n)
   for name,value in old.items():
    if name not in changed:self.assertEqual(value,new[name],(n,name))
 def test_02_schema1_original_small_policy(self):
  j=make_job(D);p=plan(j,1)
  self.assertEqual(original.validate_plan(p),caller.validate_plan(p));original.schema(j);caller.schema(j)
  with TemporaryDirectory(dir=D) as td:
   j=make_job(Path(td));caller._bind_resources(types.SimpleNamespace(root=Path(td)),j,plan(j,1))
   large=make_job(Path(td),True)
   with self.assertRaises(ValueError):original.schema(large)
   with self.assertRaises(ValueError):caller._bind_resources(types.SimpleNamespace(root=Path(td)),large,plan(large,1))
 def test_03_schema2_exact_registered_resources(self):
  with TemporaryDirectory(dir=D) as td:
   root=Path(td);j=make_job(root,True);p=plan(j,2)
   caller.schema(j);caller.validate_plan(p);caller._bind_resources(types.SimpleNamespace(root=root),j,p)
   p['resource_policy']['wall_seconds']-=1
   with self.assertRaisesRegex(ValueError,'plan/job'):caller._bind_resources(types.SimpleNamespace(root=root),j,p)
 def test_04_finite_existing_authority_refusals(self):
  p=resources(D,True)
  for key,value in [('memory_max_bytes',7*GIB),('memory_max_bytes',True),('reserve_bytes',2*GIB),('start_reserve_bytes',1),('disk_floor_bytes',9*GIB),('wall_seconds',28801)]:
   q=copy.deepcopy(p);q[key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):caller._finite_resources(q)
  for value in [True,0,-1,2**63,2.5,3*GIB]:
   q=copy.deepcopy(p);q['native_unit_limits']['file_size_bytes']=value
   with self.subTest(file=value),self.assertRaises(ValueError):caller._finite_resources(q)
  for key,value in [('max_depth',65),('max_scan_seconds',6),('max_entries',2**63),('max_logical_bytes',0)]:
   q=copy.deepcopy(p);q['storage_budget']['limits'][key]=value
   with self.subTest(storage=key),self.assertRaises(ValueError):caller._finite_resources(q)
 def test_05_physical_capacity_refuses_impossible_tree(self):
  with TemporaryDirectory(dir=D) as td:
   root=Path(td);j=make_job(root,True);p=plan(j,2)
   with patch('os.statvfs',return_value=types.SimpleNamespace(f_blocks=11*GIB,f_frsize=1)):
    with self.assertRaisesRegex(ValueError,'physical volume'):caller._bind_resources(types.SimpleNamespace(root=root),j,p)
 def test_06_exact_native_ready_large_and_legacy(self):
  self.assertIsNone(res._native_policy(None))
  for n in [4*1024**2,16*1024**2]:
   p={'file_size_bytes':n};ready={'native_unit_limits':p,'file_size_limit':[n,n],'native_environment':res._native_owned_env(D)}
   props={'LimitFSIZE':str(n),'LimitFSIZESoft':str(n),'RuntimeMaxUSec':'3600s'}
   res._native_ready(p,ready,props,3600,D)
   with self.assertRaises(ValueError):res._native_ready(p,ready,dict(props,LimitFSIZESoft=str(n-1)),3600,D)
   with self.assertRaises(ValueError):res._native_ready(p,dict(ready,file_size_limit=[n-1,n]),props,3600,D)
  for v in [True,0,-1,2**63,float('inf')]:
   with self.assertRaises(ValueError):res._native_policy({'file_size_bytes':v})
 def test_07_selected_monitor_worker_and_tiny_file_limit(self):
  j=make_job(D,True);limit=j['resources']['native_unit_limits']['file_size_bytes']
  with patch.object(resource,'setrlimit') as setter,patch.object(resource,'getrlimit',return_value=(limit,limit)):
   self.assertEqual(job._resource_worker_limits(j)['rlimit_fsize'],limit);setter.assert_called_once_with(resource.RLIMIT_FSIZE,(limit,limit))
  with patch.object(resource,'setrlimit'),patch.object(resource,'getrlimit',return_value=(limit-1,limit)):
   with self.assertRaises(ValueError):job._resource_worker_limits(j)
  unselected=copy.deepcopy(j);del unselected['payload']['representation_jobs']['test']['real_pilot_input']
  with patch.object(fixture,'worker_limits',return_value={'rlimit_fsize':4*1024**2}) as legacy:
   self.assertEqual(job._resource_worker_limits(unselected)['rlimit_fsize'],4*1024**2);legacy.assert_called_once_with()
  # Actual receipt function, mocked publication and RLIMIT only. No guard/claim.
  args=types.SimpleNamespace(experiment='synthetic',source='a'*40,root=D)
  job._base=lambda args:D;published=[]
  with patch.object(resource,'setrlimit'),patch.object(resource,'getrlimit',return_value=(limit,limit)),patch.dict(os.environ,res._native_owned_env(D)),patch.object(res,'_native_receipt',side_effect=lambda *v:published.append(v)):
   job._resource_limit_receipt(args,j,'monitor')
   job._resource_limit_receipt(args,j,'worker',{'native_unit_limits':j['resources']['native_unit_limits'],'unit':'mock','cgroup':'mock'})
   with self.assertRaises(ValueError):job._resource_limit_receipt(args,j,'worker',{'native_unit_limits':{'file_size_bytes':4*1024**2}})
  self.assertEqual(len(published),2)
 def test_08_publication_selection_and_no_duck_owner(self):
  j=make_job(D,True)
  owner=types.SimpleNamespace(bound=types.SimpleNamespace(record={'resource_only':True,'job_input':'execution_job'},_run=types.SimpleNamespace(read_input=lambda name:json.dumps(j).encode())))
  marker=object()
  with patch.object(caller,'publication_boundary',return_value=marker) as call:
   self.assertIs(fixture.publication_boundary(owner,object()),marker);call.assert_called_once()
  # Load only the type-check front of actual function: no actual Owner constructed.
  fake=types.ModuleType('policy_offline.compact_owner');fake.Owner=type('UnusedOwnerType',(),{});fake.Stage=type('UnusedStageType',(),{})
  with patch.dict(sys.modules,{'policy_offline.compact_owner':fake}):
   with self.assertRaisesRegex(ValueError,'same-owner'):caller.publication_boundary(owner,object(),j)
 def test_09_science_and_checkpoint_unchanged(self):
  p=plan(make_job(D,True),2)
  for key,value in [('seed',12),('batch_size',15),('lookback_days',27),('asset','BTC'),('max_checkpoint_bytes',4*1024**2+1),('indices',list(range(15))+[16])]:
   q=copy.deepcopy(p);q[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):caller.validate_plan(q)
  self.assertFalse({'numpy','torch','scipy','networkx'}&set(sys.modules))

if __name__=='__main__':unittest.main(verbosity=2)
