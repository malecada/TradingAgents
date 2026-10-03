"""Independent R1 source review; no genuine capsule/claim or numerical imports."""
import ast,copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent;ROOT=BASE.parents[2]
A=BASE/'neural-cold-feature-handoff-engineering-registration-preparation03-2026-10-03';OLD=BASE/'neural-cold-feature-handoff-engineering-registration-preparation02-2026-10-03';OUT=BASE/'neural-cold-feature-handoff-proof-outer-preparation03-2026-10-03'
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load(A/'generate03.py','review_generator03');old=load(OLD/'generate02.py','review_generator02')
rows=json.loads((OUT/'source_inventory03.json').read_text())['source_inventory'];r=next(r for r in rows if r['target']=='tradingagents/research/onchain_replication/resources.py');RAW=(ROOT/r['snapshot']).read_bytes()
class Review(unittest.TestCase):
 def test_manifest_dependency_pins_and_preservation(self):
  doc=json.loads((A/'MANIFEST03.json').read_text());self.assertEqual(len(doc['files']),11)
  for x in doc['files']:
   raw=(A/x['path']).read_bytes();self.assertEqual(len(raw),x['bytes']);self.assertEqual(m.digest(raw),x['sha256'])
  paths={'accepted_inventory':OUT/'source_inventory03.json','outer03_review':OUT/'REVIEW_OUTER03.md','review02':BASE/'neural-cold-feature-handoff-engineering-registration-review02-2026-10-03/REVIEW_REGISTRATION02.md','withheld_generator02':OLD/'MANIFEST02.json'}
  for k,p in paths.items():self.assertEqual(m.digest(p.read_bytes()),doc['dependencies'][k])
  self.assertEqual(m.digest(RAW),r['sha256']);self.assertEqual((A/'generate02.baseline.py').read_bytes(),(OLD/'generate02.py').read_bytes())
  for n in ('CHARTER_COMPARE02.md','CHARTER_MATERIALIZE02.md','HISTORY02.md','request-compare02.json'):self.assertEqual((A/n).read_bytes(),(OLD/n).read_bytes())
 def test_whole_module_inverse_AST_parity(self):
  source=(A/'generate03.py').read_text();before=ast.parse((OLD/'generate02.py').read_text());after=ast.parse(source)
  after.body=[n for n in after.body if not(isinstance(n,ast.FunctionDef) and n.name=='native_environment')]
  for n in after.body:
   if isinstance(n,ast.Import):n.names=[a for a in n.names if a.name!='ast']
   if isinstance(n,ast.FunctionDef) and n.name=='validate':
    n.body=[s for s in n.body if not(isinstance(s,ast.Expr) and isinstance(s.value,ast.Call) and isinstance(s.value.func,ast.Name) and s.value.func.id=='native_environment')]
    for s in n.body:
     if isinstance(s,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='keys' for t in s.targets):s.value.elts=[e for e in s.value.elts if e.value!='native_environment']
   if isinstance(n,ast.FunctionDef) and n.name=='render':
    for d in ast.walk(n):
     if isinstance(d,ast.Dict):
      for k,v in zip(d.keys,d.values):
       if isinstance(k,ast.Constant) and k.value=='native_environment':v.slice.value='environment'
  self.assertEqual(ast.dump(before),ast.dump(after))
 def test_actual_native_helper_reference_and_corruption(self):
  with tempfile.TemporaryDirectory(prefix='review-cold03-') as name:
   root=Path(name).resolve();p=root/r['target'];p.parent.mkdir(parents=True);p.write_bytes(RAW)
   f=next(n for n in ast.parse(RAW).body if isinstance(n,ast.FunctionDef) and n.name=='_native_owned_env');ns={'Path':Path};exec(compile(ast.Module(body=[f],type_ignores=[]),'selected-helper','exec'),ns)
   native=ns['_native_owned_env'](root);sources={r['target']:r['sha256']};body=root/'native.json'
   def request(value):
    body.write_bytes(m.canonical(value));return {'native_environment':{'path':'native.json','sha256':m.digest(body.read_bytes())}}
   self.assertEqual(m.native_environment(root,request(native),sources),native)
   for value in ({'python':'3.13.13','packages':{}},native|{'OMP_NUM_THREADS':'3'},{k:v for k,v in native.items() if k!='TMPDIR'},native|{'extra':'x'}):
    with self.assertRaises(ValueError):m.native_environment(root,request(value),sources)
   req=request(native);body.write_bytes(b'{}')
   with self.assertRaises(ValueError):m.native_environment(root,req,sources)
   req=request(native);p.write_bytes(RAW+b'\n')
   with self.assertRaises(ValueError):m.native_environment(root,req,sources)
   with self.assertRaises(KeyError):m.native_environment(root,{},sources)
 def test_actual_old_to_new_template_boundary(self):
  req={'runtime':{'path':'runtime'},'environment':{'path':'inventory','sha256':m.digest(b'inventory')},'native_environment':{'path':'native','sha256':m.digest(b'native')},'cpus':[0,1],'inputs':{n:{'path':n} for n in ('recipe','configs','model','training','anchor','future_resources','environment','cold_proof','execution_job')}}
  req['inputs']['environment']=req['environment']|{'dataset':'synthetic-cold'}
  outputs=[]
  for module in (old,m):
   v,ref=module.validate,module.reference
   module.validate=lambda *a:({},{});module.reference=lambda root,x:(A/x['path']).read_bytes()
   try:outputs.append(module.render(Path('/fixture'),req,{'path':'CHARTER_MATERIALIZE02.md'},{'path':'HISTORY02.md'}))
   finally:module.validate=v;module.reference=ref
  previous,current=outputs;self.assertEqual(previous['gate_template']['native_environment'],req['environment']);self.assertEqual(current['gate_template']['native_environment'],req['native_environment'])
  self.assertEqual(previous['registration'],current['registration']);self.assertEqual(len(current['registration']['experiments'][m.IDS['materialize']]['inputs']),9)
  previous['gate_template']['native_environment']=req['native_environment'];self.assertEqual(previous,current)
 def test_no_numerical_imports(self):self.assertFalse(any(k.split('.')[0] in {'numpy','torch','scipy','tradingagents','pandas','pyarrow'} for k in sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
