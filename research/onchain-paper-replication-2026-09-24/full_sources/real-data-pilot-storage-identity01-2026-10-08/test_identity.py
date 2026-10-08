"""Real-source isolated storage/identity checks; synthetic local files, no jobs."""
import ast,copy,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def execute(path,ns,strip_relative=False):
 t=ast.parse(path.read_text())
 if strip_relative:t.body=[n for n in t.body if not isinstance(n,ast.ImportFrom) or not n.level]
 exec(compile(t,str(path),'exec'),ns)
S={};execute(ROOT/'tradingagents/research/onchain_replication/workflow_storage.py',S)
execute(HERE/'real_pilot_storage.py',S,True)
def seam(kind):
 t=ast.parse((HERE/'resources.py').read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==kind)
 if kind=='guarded_run':
  start=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='storage_watch' for x in n.targets))
  body=f.body[start:start+2]+[ast.Return(ast.Name('storage_watch',ast.Load()))]
 else:
  block=next(n for n in f.body if isinstance(n,ast.If) and ast.unparse(n.test)=="'native_unit_limits' in live")
  body=block.body[:2]
 class RemoveImports(ast.NodeTransformer):
  def visit_ImportFrom(self,n):return None
 body=[RemoveImports().visit(n) for n in body]
 fn=ast.FunctionDef(name='probe',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=k) for k in (['storage_budget','cwd','native_unit_limits','owner_identity','experiment'] if kind=='guarded_run' else ['live','pilot_context'])],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[])
 ns=dict(S);exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),kind,'exec'),ns);return ns['probe']
launch=seam('guarded_run');worker=seam('assert_guarded_worker')
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(dir=HERE);self.root=Path(self.t.name);(self.root/'research_runs').mkdir();(self.root/'research_runs/.lock').touch();(self.root/'research_artifacts').mkdir()
  self.old=S['EXPERIMENT'];self.new='eth-paper-real-data-end-to-end-resource-20261009-22'
 def tearDown(self):self.t.cleanup()
 def budget(self,name):return {'schema_version':2,'kind':S['KIND'],'authority_root':str(self.root),'experiment':name,'roots':[str(self.root/'research_artifacts'),str(self.root/'research_runs'/name)],'shared_files':[str(self.root/'research_runs/.lock')],'limits':{'max_allocated_bytes':10**8,'max_logical_bytes':10**8,'max_entries':10000,'max_depth':64,'max_scan_seconds':5}}
 def test_default_and_explicit_union_residuals(self):
  for name,kwargs in [(self.old,{}),(self.new,{'experiment':self.new})]:
   w=S['WritableUnion'](self.budget(name),self.root,**kwargs);obs=w.check()
   self.assertEqual(w.target,self.root/'research_runs'/name)
   paths=obs['residual_domains']['training_and_lifecycle']['roots'];self.assertEqual(len(paths),3)
   self.assertTrue(all(Path(x['root']).name==name for x in paths))
   w.target.mkdir();(w.target/'tiny').write_text('synthetic');self.assertGreater(w.check()['logical_file_bytes'],0)
   w.target.rename(w.target.with_name(name+'-retired'))
   with self.assertRaises(ValueError):w.check()
 def test_name_budget_and_root_refusals(self):
  b=self.budget(self.new)
  with self.assertRaises(ValueError):S['validate'](b,self.root)
  for bad in ['../x',self.new+'/x',self.new+'\n',self.new.replace('-22','-022'),self.new.replace('-22','-1000000'),True,None]:
   with self.subTest(bad=bad),self.assertRaises(ValueError):S['validate'](b,self.root,experiment=bad)
  with self.assertRaises(ValueError):S['validate'](self.budget(self.old),self.root,experiment=self.new)
  b['roots'][1]=str(self.root/'research_runs'/self.old)
  with self.assertRaises(ValueError):S['validate'](b,self.root,experiment=self.new)
 def test_actual_launch_join(self):
  self.assertIsNotNone(launch(self.budget(self.old),self.root,{}, {'experiment':self.old},None))
  self.assertIsNotNone(launch(self.budget(self.new),self.root,{}, {'experiment':self.new},self.new))
  for budget,owner,exp in [(self.budget(self.new),self.new,None),(self.budget(self.new),self.old,self.new),(self.budget(self.old),self.new,self.new)]:
   with self.assertRaises(ValueError):launch(budget,self.root,{}, {'experiment':owner},exp)
 def test_worker_admission_join(self):
  live={'storage_budget':self.budget(self.new),'owner_identity':{'experiment':self.new}}
  # Metadata fixtures only: no Admission/Owner instance or authentication claim.
  context=(SimpleNamespace(experiment_id=self.new),{})
  worker(live,context)
  with self.assertRaises(RuntimeError):worker(live,None)
  for changed in ('budget','owner','admission'):
   x=copy.deepcopy(live);ctx=context
   if changed=='budget':x['storage_budget']['experiment']=self.old
   elif changed=='owner':x['owner_identity']['experiment']=self.old
   else:ctx=(SimpleNamespace(experiment_id=self.old),{})
   with self.assertRaises(RuntimeError):worker(x,ctx)
  worker({'storage_budget':self.budget(self.old)},None)
 def test_environment_only_route_and_preparation(self):
  t=ast.parse((HERE/'resources.py').read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_native_owned_env')
  class Strip(ast.NodeTransformer):
   def visit_ImportFrom(self,n):return None
  ns=dict(S);exec(compile(ast.fix_missing_locations(ast.Module(body=[Strip().visit(f)],type_ignores=[])),'env','exec'),ns)
  env=ns['_native_owned_env'](self.root,self.budget(self.new))
  self.assertEqual(env['TMPDIR'],str(self.root/'research_artifacts/real_pilot_runtime/tmp'))
  with self.assertRaises(ValueError):S['prepare_environment'](self.root,self.budget(self.new),env)
  S['prepare_environment'](self.root,self.budget(self.new),env,experiment=self.new)
  bad=self.budget(self.new);bad['experiment']='../x'
  with self.assertRaises(ValueError):ns['_native_owned_env'](self.root,bad)
 def test_caller_and_unchanged_limits(self):
  a=(HERE/'baseline_real_pilot_import_caller.py').read_text();b=(HERE/'real_pilot_import_caller.py').read_text()
  self.assertEqual(b,a.replace('watch=WritableUnion(budget,run.admission.root)','watch=WritableUnion(budget,run.admission.root,experiment=run.admission.experiment_id)',1))
  old={};execute(ROOT/'tradingagents/research/onchain_replication/workflow_storage.py',old);execute(HERE/'baseline_real_pilot_storage.py',old,True)
  self.assertEqual(S['RESIDUAL_POLICY'],old['RESIDUAL_POLICY']);self.assertEqual(S['NATIVE_METADATA_BYTES'],old['NATIVE_METADATA_BYTES'])
  self.assertEqual(S['environment'](self.root,{}),old['environment'](self.root,{}))
  self.assertFalse('torch' in sys.modules)
if __name__=='__main__':unittest.main(verbosity=2)
