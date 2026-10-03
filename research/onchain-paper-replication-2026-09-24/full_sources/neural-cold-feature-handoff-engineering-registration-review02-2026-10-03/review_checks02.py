"""Independent stdlib source checks. Synthetic metadata is NOT release authority."""
import ast,copy,hashlib,importlib.util,json,sys,types,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
AUTHOR=BASE/'neural-cold-feature-handoff-engineering-registration-preparation02-2026-10-03'
OUT=BASE/'neural-cold-feature-handoff-proof-outer-preparation03-2026-10-03'
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
g=load(AUTHOR/'generate02.py','reviewed_generator02')
def require(ok,msg):
 if not ok:raise ValueError(msg)
def extract(path,name,env):
 fn=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
 exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path)+'::'+name,'exec'),env);return env[name]
def fixture():
 inputs={n:{'path':'fixture/'+n,'sha256':hashlib.sha256(n.encode()).hexdigest(),'dataset':'synthetic-cold'} for n in g.MATERIAL_INPUTS}
 sources={str(i):hashlib.sha256(str(i).encode()).hexdigest() for i in range(195)}
 first={'family':g.FAMILY,'parent':None,'question':'fixture','stage':'development','reuse':'exploratory','runtime_hashes':{'x':'fixed'},'source_files':sources,'inputs':{'environment':{'path':'inventory','sha256':g.digest(b'fixture'),'dataset':'synthetic-cold'}},'charter':{'path':'original-charter','sha256':g.digest(b'original')},'cells':[g.CELL['materialize']],'outputs':['proof-materialize.json'],'windows':[]}
 old={'schema_version':1,'program_id':g.PROGRAM,'families':{g.FAMILY:{'mechanism_id':g.FAMILY,'attempt_budget':2,'prior_attempts':0,'history_reference':'history'}},'datasets':{'synthetic-cold':{'identity':'fixture','exposures':[]}},'experiments':{g.IDS['materialize']:first}}
 release={'source':'1234567890'*4,'registration':{'path':'old','sha256':g.digest(b'old'),'bytes':3,'kind':'document'},'root':'/fixture','sources':{},'runtime':{},'native_environment':{},'cpus':[0,1]}
 retained={'context':{'release':release},'registration':old,'material':{'inputs':inputs}}
 paths={k:'new/'+k for k in ('registration','charter','evolution','phase_contract')}
 return retained,paths
class Review(unittest.TestCase):
 def test_manifest_origins_and_all195_snapshots(self):
  manifest=json.loads((AUTHOR/'MANIFEST02.json').read_text());self.assertEqual(manifest['file_count'],11)
  for item in manifest['files']:
   b=(AUTHOR/item['path']).read_bytes();self.assertEqual(len(b),item['bytes']);self.assertEqual(g.digest(b),item['sha256'])
  for item in json.loads((AUTHOR/'source-origins02.json').read_text())['files']:
   b=(ROOT/item['path']).read_bytes();self.assertEqual(len(b),item['bytes']);self.assertEqual(g.digest(b),item['sha256'])
  b=(OUT/'source_inventory03.json').read_bytes();self.assertEqual(g.digest(b),g.PINNED_INVENTORY)
  rows=json.loads(b)['source_inventory'];self.assertEqual(len(rows),195)
  for row in rows:
   b=(ROOT/row['snapshot']).read_bytes();self.assertEqual(len(b),row['bytes']);self.assertEqual(g.digest(b),row['sha256'])
 def test_materialization_environment_collision_reproduced(self):
  rows=json.loads((OUT/'source_inventory03.json').read_text())['source_inventory']
  selected={Path(r['target']).name:ROOT/r['snapshot'] for r in rows if r['target'].endswith(('/environment.py','/resources.py','/job.py'))}
  native=extract(selected['resources.py'],'_native_owned_env',{'Path':Path})(Path('/fixture'))
  tree=ast.parse(selected['environment.py'].read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inventory')
  initial=next(n.value for n in fn.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict))
  inventory_keys={k.value for k in initial.keys};self.assertTrue({'python','cpu_count','lock_sha256','packages'}<=inventory_keys);self.assertTrue(inventory_keys.isdisjoint(native))
  text=selected['job.py'].read_text();self.assertIn("inventory(root, include_torch=job['kind']",text);self.assertIn("json.loads(run.read_input(job['environment_input']))",text)
  # Extract actual render, explicitly substituting authentication only for pure template inspection.
  env={'validate':lambda root,req:({},{}),'require':require,'reference':lambda root,ref:(AUTHOR/ref['path']).read_bytes(),'HERE':AUTHOR,'FAMILY':g.FAMILY,'IDS':g.IDS,'CELL':g.CELL,'PROGRAM':g.PROGRAM,'Path':Path}
  render=extract(AUTHOR/'generate02.py','render',env)
  reference={'path':'inventory.json','sha256':g.digest(b'inventory')};request={'runtime':{},'environment':reference,'cpus':[0,1],'inputs':{'environment':reference|{'dataset':'synthetic-cold'}}}
  result=render(Path('/fixture'),request,{'path':'CHARTER_MATERIALIZE02.md'},{'path':'HISTORY02.md'})
  self.assertEqual(result['gate_template']['native_environment'],reference)
  self.assertEqual(result['registration']['experiments'][g.IDS['materialize']]['inputs']['environment']['path'],reference['path'])
  self.assertIn("require(environment==ctx['environment'],'selected owned environment differs')",(OUT/'proof_outer01.py').read_text())
  print('REPRODUCED: same reference must equal incompatible inventory keys and native variable keys; no launch performed')
 def test_real_reducer_accepts_full43_to44_and_rejects_drift(self):
  r,p=fixture();o=g.compare_documents(r,p,{'path':'accepted'},{'path':'wait'},(AUTHOR/'CHARTER_COMPARE02.md').read_bytes())
  reducer=extract(OUT/'proof_release01.py','_registration_evolution',{'require':require,'IDENTITIES':g.IDS,'MATERIAL_INPUTS':g.MATERIAL_INPUTS})
  old=r['registration'];new=o['registration'];cmp=g.IDS['compare'];mat=g.IDS['materialize']
  reducer(old,new,new['experiments'][cmp],r['material']);self.assertEqual(len(new['experiments'][cmp]['inputs']),44)
  changes=[lambda x:x['families'][g.FAMILY].update(attempt_budget=3),lambda x:x['families'][g.FAMILY].update(prior_attempts=1),lambda x:x['datasets']['synthetic-cold']['exposures'].append('changed'),lambda x:x['experiments'][mat].update(question='changed'),lambda x:x['experiments'][cmp].update(parent=None),lambda x:x['experiments'][cmp]['source_files'].update({'0':'changed'}),lambda x:x['experiments'][cmp]['runtime_hashes'].update(x='changed'),lambda x:x['experiments'][cmp]['inputs']['graph-00'].update(sha256='changed'),lambda x:x['experiments'][cmp]['inputs']['environment'].update(sha256='changed'),lambda x:x['experiments'].update(extra={})]
  for change in changes:
   n=copy.deepcopy(new);change(n)
   with self.assertRaises(ValueError):reducer(old,n,n['experiments'][cmp],r['material'])
  evolution=json.loads(o['files'][p['evolution']]);self.assertEqual(len(evolution['additions']),3);self.assertEqual(len(o['files']),4)
  for row in evolution['additions']:self.assertEqual(row['sha256'],g.digest(o['files'][row['path']]))
  self.assertNotIn(p['evolution'],[row['path'] for row in evolution['additions']]);self.assertIsNone(o['gate_template']['source'])
 def test_actual_head_helper_sole_direct_parent(self):
  A='1234567890'*4;B='abcdef0123'*4;state={'head':B,'parents':B+' '+A}
  def call(cmd,**kwargs):return state['head'] if cmd[1]=='rev-parse' else state['parents']
  fn=extract(OUT/'proof_release01.py','_source_head',{'require':require,'subprocess':types.SimpleNamespace(check_output=call)})
  self.assertEqual(fn(None,A,'retained-materialization'),B)
  for parents in (B+' '+'9876543210'*4,B+' '+A+' '+'9876543210'*4):
   state['parents']=parents
   with self.assertRaises(ValueError):fn(None,A,'retained-materialization')
 def test_no_numerical_imports(self):self.assertFalse(any(k.split('.')[0] in {'numpy','torch','scipy','tradingagents','pandas','pyarrow'} for k in sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
